#!/usr/bin/env python3
"""
Parse tables list from PDF pages using GPT-4 Vision.

This script extracts the complete tables catalog from a thesis by processing
each page individually to avoid token limits and truncation issues.
Results are automatically merged into a single YAML file.

Usage:
    python parse_toc_tables.py thesis.pdf 17 17 output_directory/

The script will:
1. Process each page individually to avoid API token limits
2. Extract table information from each page separately
3. Merge all results into a complete tables catalog
4. Handle tables that may span across pages

Requires:
- OpenAI API key in OPENAI_API_KEY environment variable
- poppler-utils for PDF processing (pdftoppm command)
"""

import os
import openai
import argparse
from pathlib import Path
import re

# Import common utilities
from pdf_utils import extract_pages_to_images
from progress_utils import print_progress, print_section_header, print_completion_summary
from gpt_vision_utils import (
    encode_images_for_vision,
    call_gpt_vision_api,
    cleanup_temp_directory
)
from yaml_utils import (
    clean_yaml_output,
    parse_and_validate_yaml,
    save_yaml_data,
    count_items_in_yaml
)


def extract_text_from_pdf_page(pdf_path, page_num):
    """
    Extract text from a single PDF page for guidance and validation.
    
    Args:
        pdf_path (str): Path to PDF file
        page_num (int): Page number (1-based)
        
    Returns:
        str: Extracted text from the page, or empty string if failed
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        if page_num - 1 < len(doc):
            page = doc.load_page(page_num - 1)  # Convert to 0-based
            text = page.get_text()
            doc.close()
            return text.strip()
        doc.close()
    except ImportError:
        pass
    
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            if page_num - 1 < len(pdf.pages):
                page = pdf.pages[page_num - 1]  # Convert to 0-based
                text = page.extract_text() or ""
                return text.strip()
    except ImportError:
        pass
    
    return ""


def generate_simple_text_tables(yaml_data, output_file):
    """
    Generate a simple text format of the tables list for easy validation.
    
    Args:
        yaml_data (dict): Parsed YAML tables data
        output_file (str): Output text file path
    """
    print_progress("Generating simple text tables list for validation...")
    
    lines = []
    lines.append("=" * 60)
    lines.append("TABLES LIST - SIMPLE TEXT FORMAT")
    lines.append("=" * 60)
    lines.append("")
    
    tables = yaml_data.get('tables', [])
    
    for table in tables:
        table_number = table.get('table_number', '?')
        title = table.get('title', 'NO TITLE')
        page = table.get('page', '?')
        chapter = table.get('chapter', '?')
        
        # Format with dots between title and page number
        dots_length = max(5, 50 - len(f"Table {table_number} {title}"))
        dots = "." * dots_length
        
        lines.append(f"Table {table_number} {title} {dots} {page}")
    
    # Add summary statistics
    lines.append("")
    lines.append("=" * 60)
    lines.append("SUMMARY")
    lines.append("=" * 60)
    
    # Count tables by chapter/appendix using the new chapter_name field
    chapter_counts = {}
    for table in tables:
        chapter_name = table.get('chapter_name', 'Unknown')
        chapter_counts[chapter_name] = chapter_counts.get(chapter_name, 0) + 1
    
    # Sort chapters and appendices properly using chapter_name
    def chapter_name_sort_key(ch_name):
        if ch_name.startswith('Chapter '):
            try:
                num = int(ch_name.replace('Chapter ', ''))
                return (1, num)  # Chapters first
            except ValueError:
                return (3, ch_name)  # Unknown chapters last
        elif ch_name.startswith('Appendix '):
            appendix_num_str = ch_name.replace('Appendix ', '')
            try:
                appendix_num = int(appendix_num_str)
                return (2, appendix_num)  # Appendices after chapters
            except ValueError:
                return (3, ch_name)  # Unknown appendices last
        else:
            return (3, ch_name)  # Unknown last
    
    for chapter_name in sorted(chapter_counts.keys(), key=chapter_name_sort_key):
        if chapter_name != 'Unknown':
            lines.append(f"{chapter_name}: {chapter_counts[chapter_name]} tables")
    
    if 'Unknown' in chapter_counts:
        lines.append(f"Unknown: {chapter_counts['Unknown']} tables")
    
    lines.append(f"Total tables: {len(tables)}")
    lines.append("")
    lines.append("=" * 60)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print_progress(f"+ Simple text tables list saved to {output_file}")
    return output_file


def create_single_page_tables_prompt(extracted_text=None):
    """
    Create prompt for processing individual tables pages with text guidance.
    
    Args:
        extracted_text (str, optional): Text extracted from PDF for validation
        
    Returns:
        str: Focused prompt for extracting table entries from a single page
    """
    base_prompt = """
    Extract tables list from this single page of a 1992 PhD thesis.
    Focus on accuracy and handle mathematical symbols appropriately.
    
    Return YAML format with this structure:

    page_tables:
      - table_number: "4.1"
        title: "exact table caption/title (with mathematical symbols formatted as inline markdown)"
        page: number
        chapter_name: "Chapter 4"
        chapter_id: "4"
      - table_number: "A1.1"  
        title: "appendix table title"
        page: number
        chapter_name: "Appendix 1"
        chapter_id: "A1"

    Instructions:
    1. Extract ALL tables visible on this page exactly as shown
    2. Include complete table titles/captions
    3. Extract page numbers accurately
    4. Set chapter_name and chapter_id from table numbering:
       - For chapters: "4.1" → chapter_name: "Chapter 4", chapter_id: "4"
       - For chapters: "5.2.3" → chapter_name: "Chapter 5", chapter_id: "5"
       - For appendices: "A1.1" → chapter_name: "Appendix 1", chapter_id: "A1"
       - For appendices: "A2.2" → chapter_name: "Appendix 2", chapter_id: "A2"
    5. Preserve exact capitalization and punctuation in titles
    6. Include tables with appendix numbering like "A1.1", "A2.2", etc.
    7. Format mathematical symbols SPARINGLY - only actual math symbols, NOT English words:
       - Greek letters: α, β, γ → $\\alpha$, $\\beta$, $\\gamma$
       - Subscripts/superscripts: x_i → $x_{i}$
       - DO NOT convert words like "Integral", "Function", "Distribution" to math formulas
    8. If no tables are found, return empty page_tables list"""
    
    if extracted_text:
        guidance_section = f"""
    
    GUIDANCE FROM PDF TEXT EXTRACTION:
    The following text was extracted from this page to help guide your analysis:
    
    {extracted_text[:1000]}{'...' if len(extracted_text) > 1000 else ''}
    
    Use this text as reference but rely primarily on the visual content for accurate formatting."""
        base_prompt += guidance_section
    
    base_prompt += """
    
    Return only valid YAML without explanatory text or markdown formatting.
    """
    
    return base_prompt


def parse_single_tables_page(pdf_path, page_number, api_key, page_index, total_pages, temp_dir="/tmp/toc_tables", output_dir=None, debug=False):
    """
    Parse a single tables list page using GPT-4 Vision API with text guidance.
    
    Args:
        pdf_path (str): Path to the thesis PDF file
        page_number (int): Single page number to process (1-based)
        api_key (str): OpenAI API key for GPT-4 Vision access
        page_index (int): Current page index for progress tracking (1-based)
        total_pages (int): Total number of pages to process
        temp_dir (str): Directory for temporary files
        output_dir (Path, optional): Output directory for debug files
        debug (bool): Whether to save debug files
        
    Returns:
        tuple: (dict or None, dict) - Parsed YAML data and diagnostic info
    """
    openai.api_key = api_key
    
    print_progress(f"Processing tables page {page_index}/{total_pages}: page {page_number}")
    
    # Initialize diagnostic information
    diagnostics = {
        'page_number': page_number,
        'page_index': page_index,
        'total_pages': total_pages,
        'extraction_success': False,
        'text_extraction_success': False,
        'api_success': False,
        'yaml_parsing_success': False,
        'tables_extracted': 0,
        'raw_response_length': 0,
        'cleaned_response_length': 0,
        'text_guidance_length': 0,
        'error_details': None
    }
    
    # Extract text from PDF page for guidance
    extracted_text = extract_text_from_pdf_page(pdf_path, page_number)
    if extracted_text:
        diagnostics['text_extraction_success'] = True
        diagnostics['text_guidance_length'] = len(extracted_text)
        print_progress(f"+ Extracted {len(extracted_text)} characters of text for guidance")
    else:
        print_progress("- No text extracted from PDF (will rely on vision only)")
    
    # Extract single page as image
    images = extract_pages_to_images(
        pdf_path, page_number, page_number, temp_dir,
        dpi=200, page_prefix=f"tables-page-{page_number}"
    )
    
    if not images:
        print_progress(f"- Failed to extract page {page_number}")
        diagnostics['error_details'] = "PDF page extraction failed"
        return None, diagnostics
    
    diagnostics['extraction_success'] = True
    diagnostics['images_created'] = len(images)
    
    # Encode image for Vision API
    image_contents = encode_images_for_vision(images, show_progress=False)
    
    # Create prompt with text guidance
    prompt = create_single_page_tables_prompt(extracted_text)
    
    # Call GPT-4 Vision API (tables typically need fewer tokens)
    max_tokens = 1000
    diagnostics['max_tokens_used'] = max_tokens
    
    result = call_gpt_vision_api(
        prompt, image_contents,
        model="gpt-4o", max_tokens=max_tokens
    )
    
    diagnostics['raw_response_length'] = len(result) if result else 0
    
    if result.startswith("Error:"):
        print_progress(f"- API error for page {page_number}: {result}")
        diagnostics['error_details'] = result
        return None, diagnostics
    
    diagnostics['api_success'] = True
    
    # Parse YAML response
    cleaned_result = clean_yaml_output(result)
    diagnostics['cleaned_response_length'] = len(cleaned_result)
    
    # Save raw response for debugging (only if debug flag is enabled)
    if debug:
        if output_dir:
            debug_file = output_dir / f'tables_page_{page_number}_debug.txt'
        else:
            debug_file = f'tables_page_{page_number}_debug.txt'
        try:
            with open(debug_file, 'w') as f:
                f.write(f"=== TABLES PAGE {page_number} DEBUG INFO ===\n")
                f.write(f"Page: {page_number}\n")
                f.write(f"Text guidance length: {diagnostics['text_guidance_length']}\n")
                f.write(f"Raw response length: {diagnostics['raw_response_length']}\n")
                f.write(f"Cleaned response length: {diagnostics['cleaned_response_length']}\n")
                f.write(f"Max tokens: {max_tokens}\n")
                if extracted_text:
                    f.write(f"\n=== EXTRACTED TEXT ===\n")
                    f.write(extracted_text[:2000] + ('...' if len(extracted_text) > 2000 else ''))
                f.write("\n\n=== RAW RESPONSE ===\n")
                f.write(result)
                f.write("\n\n=== CLEANED RESPONSE ===\n")
                f.write(cleaned_result)
            diagnostics['debug_file_created'] = str(debug_file)
        except Exception as e:
            diagnostics['debug_file_error'] = str(e)
    else:
        diagnostics['debug_file_created'] = None
    
    data = parse_and_validate_yaml(cleaned_result, f'tables_page_{page_number}_debug.txt')
    
    if data:
        diagnostics['yaml_parsing_success'] = True
        tables = data.get('page_tables', [])
        diagnostics['tables_extracted'] = len(tables)
        
        print_progress(f"+ Page {page_number}: extracted {diagnostics['tables_extracted']} tables")
    else:
        diagnostics['error_details'] = "YAML parsing failed"
        print_progress(f"- Page {page_number}: YAML parsing failed")
    
    return data, diagnostics


def merge_tables_pages(page_data_list, page_diagnostics_list):
    """
    Merge tables data from multiple pages into a single coherent structure.
    
    Args:
        page_data_list (list): List of parsed YAML data from each page
        page_diagnostics_list (list): List of diagnostic info from each page
        
    Returns:
        tuple: (dict, dict) - Merged YAML structure and comprehensive diagnostics
    """
    print_progress("Merging tables data from all pages...")
    
    # Create comprehensive diagnostics
    merge_diagnostics = {
        'total_pages_processed': len([d for d in page_diagnostics_list if d]),
        'successful_pages': 0,
        'failed_pages': 0,
        'page_details': page_diagnostics_list,
        'pages_processed': [],
        'tables_by_page': {}
    }
    
    # Initialize merged structure
    merged_data = {
        'thesis_title': 'PhD Thesis - Richard Jeans 1992',
        'total_pages': 215,
        'tables': []
    }
    
    # Collect all tables from all pages with detailed tracking
    all_tables = []
    
    for i, (page_data, page_diag) in enumerate(zip(page_data_list, page_diagnostics_list)):
        if not page_diag:
            merge_diagnostics['failed_pages'] += 1
            continue
            
        page_num = page_diag.get('page_number', i + 1)
        
        if page_data and 'page_tables' in page_data:
            tables = page_data['page_tables']
            if tables:  # Check if tables is not empty
                all_tables.extend(tables)
                merge_diagnostics['successful_pages'] += 1
                merge_diagnostics['tables_by_page'][page_num] = {
                    'count': len(tables),
                    'page': page_num
                }
                merge_diagnostics['pages_processed'].append(page_num)
        else:
            merge_diagnostics['failed_pages'] += 1
    
    print_progress(f"Found {len(all_tables)} total tables across {merge_diagnostics['successful_pages']} successful pages")
    
    # Sort tables by table_number for better organization
    try:
        def table_sort_key(table):
            chapter_id = table.get('chapter_id', '0')
            table_num = table.get('table_number', '0.0')
            
            # Split table number into parts for sub-sorting
            parts = table_num.split('.')
            
            # Create sort key based on chapter_id
            if isinstance(chapter_id, str) and chapter_id.startswith('A'):
                # Appendix (A1, A2, etc.) - sort after chapters
                try:
                    appendix_num = int(chapter_id[1:])  # Extract number after 'A'
                    primary_sort = 1000 + appendix_num  # Appendices sort after chapters
                except (ValueError, IndexError):
                    primary_sort = 2000  # Unknown appendices last
            else:
                # Chapter - convert to int for proper numeric sorting
                try:
                    primary_sort = int(chapter_id)
                except (ValueError, TypeError):
                    primary_sort = 0  # Default for unknown
            
            # Add sub-parts for detailed sorting (e.g., 4.1 vs 4.2)
            sub_parts = []
            for part in parts[1:]:  # Skip first part (already handled by chapter_id)
                if part.isdigit():
                    sub_parts.append(int(part))
                else:
                    sub_parts.append(0)
            
            return [primary_sort] + sub_parts
        
        all_tables.sort(key=table_sort_key)
        print_progress("+ Tables sorted by table number")
    except Exception as e:
        print_progress(f"- Could not sort tables: {e}")
    
    # Add processed tables to merged structure
    merged_data['tables'] = all_tables
    
    # Add extraction metadata
    merged_data['extraction_metadata'] = {
        'pages_processed': merge_diagnostics['successful_pages'],
        'total_tables_extracted': len(all_tables),
        'pages_covered': merge_diagnostics['pages_processed'],
        'extraction_date': __import__('datetime').datetime.now().isoformat(),
        'processing_method': 'single_page_with_text_guidance'
    }
    
    return merged_data, merge_diagnostics


def parse_tables(pdf_path, start_page, end_page, api_key, output_dir=None, debug=False):
    """
    Parse tables list by processing each page individually with text guidance.
    
    Args:
        pdf_path (str): Path to the thesis PDF file
        start_page (int): First page of tables list to process (1-based)
        end_page (int): Last page of tables list to process (1-based)
        api_key (str): OpenAI API key for GPT-4 Vision access
        output_dir (Path, optional): Output directory for debug files
        debug (bool): Whether to save debug files
        
    Returns:
        dict or None: Complete merged tables structure, or None if failed
    """
    temp_dir = "/tmp/toc_tables"
    
    total_pages = end_page - start_page + 1
    
    print_progress(f"Starting single-page tables processing with text guidance:")
    print_progress(f"  Total pages: {total_pages}")
    print_progress(f"  Processing method: One page at a time")
    print_progress(f"  Text guidance: Enabled")
    print_progress(f"  Mathematical symbol handling: Enabled")
    
    # Process pages individually
    page_data_list = []
    page_diagnostics_list = []
    
    for page_index, current_page in enumerate(range(start_page, end_page + 1), 1):
        page_data, page_diagnostics = parse_single_tables_page(
            pdf_path, current_page, api_key, 
            page_index, total_pages, temp_dir, output_dir, debug
        )
        
        page_data_list.append(page_data)
        page_diagnostics_list.append(page_diagnostics)
        
        if not page_data:
            print_progress(f"- Page {current_page}: processing failed")
            if page_diagnostics and page_diagnostics.get('error_details'):
                print_progress(f"  Error: {page_diagnostics['error_details']}")
    
    # Clean up temporary files
    cleanup_temp_directory(temp_dir)
    
    # Merge all page data into final structure
    successful_pages = [p for p in page_data_list if p is not None]
    if successful_pages:
        merged_data, merge_diagnostics = merge_tables_pages(page_data_list, page_diagnostics_list)
        print_progress(f"Successfully processed {len(successful_pages)}/{total_pages} pages")
        
        # Save comprehensive diagnostics
        if output_dir:
            diagnostics_file = output_dir / "tables_extraction_diagnostics.json"
        else:
            diagnostics_file = "tables_extraction_diagnostics.json"
        try:
            import json
            with open(diagnostics_file, 'w') as f:
                json.dump({
                    'processing_summary': {
                        'total_pages': total_pages,
                        'processing_method': 'single_page_with_text_guidance',
                        'successful_pages': len(successful_pages),
                        'failed_pages': total_pages - len(successful_pages),
                        'text_guidance_enabled': True,
                        'mathematical_formatting_enabled': True
                    },
                    'page_diagnostics': page_diagnostics_list,
                    'merge_diagnostics': merge_diagnostics
                }, f, indent=2)
            print_progress(f"+ Detailed diagnostics saved to {diagnostics_file}")
        except Exception as e:
            print_progress(f"- Could not save diagnostics: {e}")
        
        return merged_data
    else:
        print_progress("- No pages successfully processed")
        return None


def main():
    """
    Main function for page-by-page TOC tables parsing script.
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description='Parse tables list from PDF using single-page GPT-4 Vision processing with text guidance'
    )
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('start_page', type=int, help='Starting page number')
    parser.add_argument('end_page', type=int, help='Ending page number')
    parser.add_argument('output_dir', help='Output directory for all generated files')
    parser.add_argument('--debug', action='store_true', help='Enable debug output (saves per-page debug files)')
    
    args = parser.parse_args()
    
    # Validate API key availability
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: Please set your OPENAI_API_KEY environment variable")
        return 1
    
    # Validate input file exists
    if not Path(args.pdf_path).exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        return 1
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define standardized output files
    yaml_file = output_dir / "thesis_tables.yaml"
    text_file = output_dir / "thesis_tables.txt"
    diagnostics_file = output_dir / "tables_extraction_diagnostics.json"
    
    # Display processing information
    print_section_header("TABLES LIST PARSING (SINGLE-PAGE WITH TEXT GUIDANCE)")
    print(f"Input PDF: {args.pdf_path}")
    print(f"Pages: {args.start_page}-{args.end_page}")
    print(f"Output directory: {args.output_dir}")
    print(f"Files to be created:")
    print(f"  - {yaml_file}")
    print(f"  - {text_file}")
    print(f"  - {diagnostics_file}")
    print("=" * 60)
    
    # Parse the tables list with single-page processing
    result = parse_tables(args.pdf_path, args.start_page, args.end_page, api_key, output_dir, args.debug)
    
    # Check for processing errors
    if result is None:
        print("FAILED: Could not extract tables list")
        return 1
    
    # Save structured data to YAML file
    if not save_yaml_data(result, str(yaml_file)):
        return 1
    
    # Generate simple text format for validation
    try:
        generate_simple_text_tables(result, str(text_file))
    except Exception as e:
        print_progress(f"- Warning: Could not generate text format: {e}")
    
    # Display completion summary with table count
    table_count = count_items_in_yaml(result, 'tables')
    print_completion_summary(str(yaml_file), table_count, "tables")
    print(f"Text format saved to: {text_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())
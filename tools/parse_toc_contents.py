#!/usr/bin/env python3
"""
Parse table of contents (chapters and sections) from PDF pages using GPT-4 Vision.

This script extracts the main chapter and section structure from a thesis
table of contents using intelligent batching to optimize speed and cost.
Automatically determines optimal batch size based on token estimation.

Usage:
    python parse_toc_contents.py thesis.pdf 9 12 output/toc_contents.yaml

The script will:
1. Estimate optimal batch size based on token limits
2. Process pages in efficient batches to minimize API calls
3. Merge all results into a coherent YAML structure
4. Validate sequential numbering automatically

Requires:
- OpenAI API key in OPENAI_API_KEY environment variable
- poppler-utils for PDF processing (pdftoppm command)
"""

import os
import openai
import argparse
from pathlib import Path
import yaml
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
    count_items_in_yaml,
    validate_section_numbering,
    print_numbering_validation
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


def format_mathematical_symbols(text):
    """
    Format mathematical symbols in TOC entries as inline markdown.
    
    Args:
        text (str): Text that may contain mathematical symbols
        
    Returns:
        str: Text with mathematical symbols formatted as inline markdown
    """
    # Be very selective - only convert actual mathematical symbols
    # DO NOT convert common English words like "Integral", "Operators", "Function"
    math_patterns = [
        # Greek letters (only as standalone symbols, not part of words)
        (r'\b(α|β|γ|δ|ε|ζ|η|θ|ι|κ|λ|μ|ν|ξ|ο|π|ρ|σ|τ|υ|φ|χ|ψ|ω)\b', r'$\1$'),
        # Subscripts and superscripts with underscore/caret notation
        (r'([a-zA-Z])_([0-9a-zA-Z]+)', r'$\1_{\2}$'),
        (r'([a-zA-Z])\^([0-9a-zA-Z]+)', r'$\1^{\2}$'),
        # Mathematical operators (only symbols, not words)
        (r'∇', r'$\\nabla$'),
        (r'∂', r'$\\partial$'),
        (r'∫', r'$\\int$'),
        (r'∑', r'$\\sum$'),
        (r'∏', r'$\\prod$'),
        # Simple equations (single variable = expression)
        (r'\b([A-Za-z])\s*=\s*([0-9\+\-\*/\(\)]+)\b', r'$\1 = \2$')
    ]
    
    # Note: We explicitly DO NOT convert English words like:
    # - "Integral" (as in "Integral Equations") 
    # - "Operators" (as in "Integral Operators")
    # - "Function" (as in "Green's Function")
    # These should remain as regular text
    
    formatted_text = text
    for pattern, replacement in math_patterns:
        formatted_text = re.sub(pattern, replacement, formatted_text)
    
    return formatted_text


def generate_simple_text_toc(yaml_data, output_file):
    """
    Generate a simple text format of the table of contents for easy validation.
    
    Args:
        yaml_data (dict): Parsed YAML TOC data
        output_file (str): Output text file path
    """
    print_progress("Generating simple text TOC for validation...")
    
    lines = []
    lines.append("=" * 60)
    lines.append("TABLE OF CONTENTS - SIMPLE TEXT FORMAT")
    lines.append("=" * 60)
    lines.append("")
    
    sections = yaml_data.get('sections', [])
    
    for section in sections:
        section_type = section.get('type', 'unknown')
        title = section.get('title', 'NO TITLE')
        page_start = section.get('page_start', '?')
        chapter_number = section.get('chapter_number')
        
        # Format main entry
        if section_type == 'front_matter':
            lines.append(f"{title} ..................................... {page_start}")
        elif section_type == 'chapter':
            if chapter_number:
                lines.append(f"CHAPTER {chapter_number}. {title.replace(f'CHAPTER {chapter_number}. ', '')} ..................................... {page_start}")
            else:
                lines.append(f"{title} ..................................... {page_start}")
        elif section_type == 'appendix':
            lines.append(f"{title} ..................................... {page_start}")
        else:
            lines.append(f"{title} ..................................... {page_start}")
        
        lines.append("")
        
        # Format subsections with proper indentation
        subsections = section.get('subsections', [])
        for subsection in subsections:
            section_number = subsection.get('section_number', '')
            subsection_title = subsection.get('title', 'NO TITLE')
            page = subsection.get('page', '?')
            level = subsection.get('level', 1)
            
            # Create indentation based on level
            indent = "    " * level
            dots_length = max(5, 50 - len(indent + section_number + " " + subsection_title))
            dots = "." * dots_length
            
            lines.append(f"{indent}{section_number} {subsection_title} {dots} {page}")
        
        if subsections:  # Add extra spacing after chapters with subsections
            lines.append("")
    
    # Add summary statistics
    lines.append("")
    lines.append("=" * 60)
    lines.append("SUMMARY")
    lines.append("=" * 60)
    
    # Count entries by type
    type_counts = {}
    total_subsections = 0
    
    for section in sections:
        section_type = section.get('type', 'unknown')
        type_counts[section_type] = type_counts.get(section_type, 0) + 1
        total_subsections += len(section.get('subsections', []))
    
    for section_type, count in type_counts.items():
        lines.append(f"{section_type.replace('_', ' ').title()}: {count}")
    
    lines.append(f"Total subsections: {total_subsections}")
    lines.append(f"Total entries: {len(sections)}")
    
    # Add extraction metadata if available
    metadata = yaml_data.get('extraction_metadata', {})
    if metadata:
        lines.append("")
        lines.append("EXTRACTION INFO:")
        lines.append(f"Pages processed: {metadata.get('pages_processed', 'unknown')}")
        lines.append(f"Processing method: {metadata.get('processing_method', 'unknown')}")
        if metadata.get('extraction_date'):
            lines.append(f"Extracted: {metadata['extraction_date']}")
    
    lines.append("")
    lines.append("=" * 60)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print_progress(f"+ Simple text TOC saved to {output_file}")
    return output_file


def create_single_page_toc_prompt(extracted_text=None):
    """
    Create prompt for processing a single TOC page.
    
    Args:
        extracted_text (str, optional): Text extracted from PDF for validation
        
    Returns:
        str: Optimized prompt for extracting table of contents from one page
    """
    base_prompt = """
    Extract table of contents entries from this single page of a 1992 PhD thesis.
    Focus on accuracy and handle mathematical symbols appropriately.
    IMPORTANT: This page may contain continuation entries from previous pages.
    
    Return YAML format with this structure:

    page_entries:
      - type: "front_matter|chapter|appendix|back_matter|toc|continuation"
        title: "exact title from TOC (with mathematical symbols formatted as inline markdown)"
        page_start: number
        chapter_number: number (if applicable, null otherwise)
        subsections:
          - section_number: "2.1" or "3.4.2" (extracted numbering)
            title: "subsection title without number (with math symbols as inline markdown)"
            page: number
            level: 1|2|3|4 (based on numbering depth)

    Instructions:
    1. Extract ALL entries visible on this page exactly as shown
    2. Identify section types: front_matter, chapter, appendix, back_matter, toc, continuation
       - Use type: "toc" ONLY for these specific sections (case-insensitive):
         * "CONTENTS", "TABLE OF CONTENTS" 
         * "FIGURES", "LIST OF FIGURES"
         * "TABLES", "LIST OF TABLES"
       - Use type: "front_matter" for all other preliminary sections:
         * "Abstract", "Acknowledgements", "Notation", "Title Page"
         * Any section that appears before Chapter 1 and is NOT a table of contents/figures/tables
       - DECISION RULE: If the section title exactly matches "CONTENTS", "FIGURES", or "TABLES" (or their variants), use "toc". Otherwise, if it appears before chapters, use "front_matter".
    3. For CONTINUATION entries:
       - Use type: "continuation" for subsections that continue from previous pages
       - Title should be "Chapter X (continued)" where X is the chapter number
       - Include ALL subsections visible on this page, even if the chapter header isn't shown
       - Determine chapter number from the subsection numbering (e.g., "2.5" belongs to Chapter 2)
    4. For subsections, separate the numbering from the title:
       - section_number: "2.1", "3.4.2", "4.1.5.3" (extract exact numbering)
       - title: Clean title without the numbering prefix
    5. Determine level from numbering depth (2.1=level 1, 3.4.2=level 2, etc.)
    6. Preserve exact capitalization and punctuation in titles
    7. For chapters, extract chapter_number from title (e.g., "Chapter 3" -> 3)
    8. TYPE ASSIGNMENT EXAMPLES:
       - "Abstract" -> type: "front_matter"  
       - "Acknowledgements" -> type: "front_matter"
       - "Notation" -> type: "front_matter"
       - "CONTENTS" -> type: "toc"
       - "FIGURES" -> type: "toc"  
       - "TABLES" -> type: "toc"
       - "Chapter 1: Introduction" -> type: "chapter"
       - "Appendix 1" -> type: "appendix"
       - "References" -> type: "back_matter"
    10. Format mathematical symbols SPARINGLY - only actual math symbols, NOT English words:
        - Greek letters: α, β, γ → $\\alpha$, $\\beta$, $\\gamma$
        - Subscripts/superscripts: x_i → $x_{i}$
        - DO NOT convert words like "Integral", "Operators", "Function" to math formulas
    11. Maintain sequential order as they appear in the document
    12. If you see subsections like "2.5", "2.5.1" without a chapter header, create a continuation entry for Chapter 2"""
    
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


def parse_single_toc_page(pdf_path, page_num, api_key, page_index, total_pages, temp_dir="/tmp/toc_contents", output_dir=None, debug=False):
    """
    Parse a single table of contents page using GPT-4 Vision API with text guidance.
    
    Args:
        pdf_path (str): Path to the thesis PDF file
        page_num (int): Page number to process (1-based)
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
    
    print_progress(f"Processing TOC page {page_index}/{total_pages}: page {page_num}")
    
    # Initialize diagnostic information
    diagnostics = {
        'page_number': page_num,
        'page_index': page_index,
        'total_pages': total_pages,
        'extraction_success': False,
        'text_extraction_success': False,
        'api_success': False,
        'yaml_parsing_success': False,
        'entries_extracted': 0,
        'raw_response_length': 0,
        'cleaned_response_length': 0,
        'text_guidance_length': 0,
        'error_details': None
    }
    
    # Extract text from PDF page for guidance
    extracted_text = extract_text_from_pdf_page(pdf_path, page_num)
    if extracted_text:
        diagnostics['text_extraction_success'] = True
        diagnostics['text_guidance_length'] = len(extracted_text)
        print_progress(f"+ Extracted {len(extracted_text)} characters of text for guidance")
    else:
        print_progress("- No text extracted from PDF (will rely on vision only)")
    
    # Extract single page as image
    images = extract_pages_to_images(
        pdf_path, page_num, page_num, temp_dir,
        dpi=200, page_prefix=f"contents-page-{page_num}"
    )
    
    if not images:
        print_progress(f"- Failed to extract page {page_num}")
        diagnostics['error_details'] = "PDF page extraction failed"
        return None, diagnostics
    
    diagnostics['extraction_success'] = True
    diagnostics['images_created'] = len(images)
    
    # Encode images for Vision API
    image_contents = encode_images_for_vision(images, show_progress=False)
    
    # Create prompt with text guidance
    prompt = create_single_page_toc_prompt(extracted_text)
    
    # Set appropriate token limit for single page processing
    max_tokens = 2000  # More conservative for single page
    diagnostics['max_tokens_used'] = max_tokens
    
    result = call_gpt_vision_api(
        prompt, image_contents,
        model="gpt-4o", max_tokens=max_tokens
    )
    
    diagnostics['raw_response_length'] = len(result) if result else 0
    
    if result.startswith("Error:"):
        print_progress(f"- API error for page {page_num}: {result}")
        diagnostics['error_details'] = result
        return None, diagnostics
    
    diagnostics['api_success'] = True
    
    # Parse YAML response
    cleaned_result = clean_yaml_output(result)
    diagnostics['cleaned_response_length'] = len(cleaned_result)
    
    # Save raw response for debugging (only if debug flag is enabled)
    debug_file = None
    if debug:
        if output_dir:
            debug_file = output_dir / f'contents_page_{page_num}_debug.txt'
        else:
            debug_file = f'contents_page_{page_num}_debug.txt'
        try:
            with open(debug_file, 'w') as f:
                f.write(f"=== PAGE {page_num} DEBUG INFO ===\n")
                f.write(f"Page: {page_num}\n")
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
    
    data = parse_and_validate_yaml(cleaned_result, debug_file)
    
    if data:
        diagnostics['yaml_parsing_success'] = True
        entries = data.get('page_entries', [])
        diagnostics['entries_extracted'] = len(entries)
        
        # Post-process entries to format mathematical symbols
        for entry in entries:
            if entry.get('title'):
                entry['title'] = format_mathematical_symbols(entry['title'])
            
            # Process subsections too
            for subsection in entry.get('subsections', []):
                if subsection.get('title'):
                    subsection['title'] = format_mathematical_symbols(subsection['title'])
        
        # Detailed entry analysis
        diagnostics['entries_by_type'] = {}
        diagnostics['entries_details'] = []
        
        for entry in entries:
            entry_type = entry.get('type', 'unknown')
            if entry_type not in diagnostics['entries_by_type']:
                diagnostics['entries_by_type'][entry_type] = 0
            diagnostics['entries_by_type'][entry_type] += 1
            
            # Capture key details for each entry
            entry_detail = {
                'type': entry_type,
                'title': entry.get('title', 'NO TITLE'),
                'page_start': entry.get('page_start'),
                'chapter_number': entry.get('chapter_number'),
                'subsection_count': len(entry.get('subsections', []))
            }
            diagnostics['entries_details'].append(entry_detail)
        
        print_progress(f"+ Page {page_num}: extracted {diagnostics['entries_extracted']} entries")
        
        # Print detailed breakdown
        for entry_type, count in diagnostics['entries_by_type'].items():
            print_progress(f"  - {entry_type}: {count}")
    
    else:
        diagnostics['error_details'] = "YAML parsing failed"
        print_progress(f"- Page {page_num}: YAML parsing failed")
    
    return data, diagnostics


def merge_page_results(page_data_list, page_diagnostics_list):
    """
    Merge TOC data from multiple single-page results into a single coherent structure.
    
    Args:
        page_data_list (list): List of parsed YAML data from each page
        page_diagnostics_list (list): List of diagnostic info from each page
        
    Returns:
        tuple: (dict, dict) - Merged YAML structure and comprehensive diagnostics
    """
    print_progress("Merging TOC data from all pages...")
    
    # Create comprehensive diagnostics
    merge_diagnostics = {
        'total_pages_processed': len([d for d in page_diagnostics_list if d]),
        'successful_pages': 0,
        'failed_pages': 0,
        'page_details': page_diagnostics_list,
        'pages_processed': [],
        'entries_by_page': {},
        'missing_pages': [],
        'duplicate_entries': [],
        'merge_warnings': []
    }
    
    # Initialize merged structure
    merged_data = {
        'thesis_title': 'PhD Thesis - Richard Jeans 1992',
        'total_pages': 215,
        'sections': []
    }
    
    # Collect all entries from all pages with detailed tracking
    all_entries = []
    continuation_entries = []
    
    for i, (page_data, page_diag) in enumerate(zip(page_data_list, page_diagnostics_list)):
        if not page_diag:
            merge_diagnostics['failed_pages'] += 1
            continue
            
        page_num = page_diag.get('page_number', i + 1)
        
        if page_data and 'page_entries' in page_data:
            entries = page_data['page_entries']
            if entries:  # Check if entries is not empty
                # Separate continuation entries for special processing
                page_regular_entries = []
                page_continuation_entries = []
                
                for entry in entries:
                    if entry.get('type') == 'continuation':
                        page_continuation_entries.append(entry)
                    else:
                        page_regular_entries.append(entry)
                
                all_entries.extend(page_regular_entries)
                continuation_entries.extend(page_continuation_entries)
                
                merge_diagnostics['successful_pages'] += 1
                merge_diagnostics['entries_by_page'][page_num] = {
                    'count': len(entries),
                    'regular_entries': len(page_regular_entries),
                    'continuation_entries': len(page_continuation_entries),
                    'page': page_num,
                    'types': page_diag.get('entries_by_type', {}),
                    'details': page_diag.get('entries_details', [])
                }
                merge_diagnostics['pages_processed'].append(page_num)
            else:
                merge_diagnostics['merge_warnings'].append(f"Page {page_num}: no entries found")
        else:
            merge_diagnostics['failed_pages'] += 1
            merge_diagnostics['merge_warnings'].append(f"Page {page_num}: invalid data structure")
    
    print_progress(f"Found {len(all_entries)} regular entries and {len(continuation_entries)} continuation entries across {merge_diagnostics['successful_pages']} successful pages")
    
    # Merge continuation entries with their parent chapters
    print_progress("Processing continuation entries...")
    for continuation in continuation_entries:
        chapter_num = continuation.get('chapter_number')
        if chapter_num:
            # Find the corresponding chapter in all_entries
            parent_chapter = None
            for entry in all_entries:
                if entry.get('type') == 'chapter' and entry.get('chapter_number') == chapter_num:
                    parent_chapter = entry
                    break
            
            if parent_chapter:
                # Add continuation subsections to the parent chapter
                parent_subsections = parent_chapter.get('subsections', [])
                continuation_subsections = continuation.get('subsections', [])
                parent_chapter['subsections'] = parent_subsections + continuation_subsections
                print_progress(f"+ Merged {len(continuation_subsections)} subsections into Chapter {chapter_num}")
            else:
                merge_diagnostics['merge_warnings'].append(f"Could not find parent chapter {chapter_num} for continuation entry")
        else:
            merge_diagnostics['merge_warnings'].append("Continuation entry missing chapter number")
    
    # Analyze coverage
    all_expected_pages = set()
    if merge_diagnostics['page_details']:
        for diag in merge_diagnostics['page_details']:
            if diag and diag.get('page_number'):
                all_expected_pages.add(diag['page_number'])
    
    pages_with_entries = set()
    for entry in all_entries:
        if entry and entry.get('page_start'):
            pages_with_entries.add(entry['page_start'])
        subsections = entry.get('subsections', []) if entry else []
        for subsec in subsections:
            if subsec and subsec.get('page'):
                pages_with_entries.add(subsec['page'])
    
    merge_diagnostics['expected_pages'] = sorted(list(all_expected_pages))
    merge_diagnostics['pages_with_entries'] = sorted(list(pages_with_entries))
    merge_diagnostics['missing_coverage'] = sorted(list(all_expected_pages - pages_with_entries))
    
    if merge_diagnostics['missing_coverage']:
        print_progress(f"WARNING: No entries found for pages: {merge_diagnostics['missing_coverage']}")
    
    # Process entries to calculate page_end values
    for i, entry in enumerate(all_entries):
        if not entry:  # Skip None entries
            continue
            
        # Calculate page_end based on next entry's page_start
        if i < len(all_entries) - 1:
            next_entry = all_entries[i + 1]
            if next_entry and next_entry.get('page_start'):
                entry['page_end'] = next_entry.get('page_start', entry.get('page_start', 0)) - 1
            else:
                entry['page_end'] = entry.get('page_start', 0) + 20  # Default estimate
        else:
            # For last entry, estimate based on total pages or set a default
            entry['page_end'] = entry.get('page_start', 0) + 20  # Default estimate
    
    # Add processed entries to merged structure (filter out None entries)
    filtered_entries = [entry for entry in all_entries if entry is not None]
    merged_data['sections'] = filtered_entries
    
    # Add extraction metadata
    merged_data['extraction_metadata'] = {
        'pages_processed': merge_diagnostics['successful_pages'],
        'total_entries_extracted': len(filtered_entries),
        'pages_covered': merge_diagnostics['pages_processed'],
        'extraction_date': __import__('datetime').datetime.now().isoformat(),
        'processing_method': 'single_page_with_text_guidance'
    }
    
    return merged_data, merge_diagnostics


def parse_contents(pdf_path, start_page, end_page, api_key, output_dir=None, debug=False):
    """
    Parse table of contents structure processing one page at a time with text guidance.
    
    Processes each page individually with extracted text guidance for better accuracy
    and mathematical symbol handling.
    
    Args:
        pdf_path (str): Path to the thesis PDF file
        start_page (int): First page of TOC to process (1-based)
        end_page (int): Last page of TOC to process (1-based)
        api_key (str): OpenAI API key for GPT-4 Vision access
        output_dir (Path, optional): Output directory for debug files
        debug (bool): Whether to save debug files
        
    Returns:
        dict or None: Complete merged YAML structure, or None if failed
    """
    temp_dir = "/tmp/toc_contents"
    
    total_pages = end_page - start_page + 1
    
    print_progress(f"Starting single-page processing with text guidance:")
    print_progress(f"  Total pages: {total_pages}")
    print_progress(f"  Processing method: One page at a time")
    print_progress(f"  Text guidance: Enabled")
    print_progress(f"  Mathematical symbol handling: Enabled")
    
    # Process pages individually
    page_data_list = []
    page_diagnostics_list = []
    
    for page_index, page_num in enumerate(range(start_page, end_page + 1), 1):
        page_data, page_diagnostics = parse_single_toc_page(
            pdf_path, page_num, api_key, 
            page_index, total_pages, temp_dir, output_dir, debug
        )
        
        page_data_list.append(page_data)
        page_diagnostics_list.append(page_diagnostics)
        
        if not page_data:
            print_progress(f"- Page {page_num}: processing failed")
            if page_diagnostics and page_diagnostics.get('error_details'):
                print_progress(f"  Error: {page_diagnostics['error_details']}")
    
    # Clean up temporary files
    cleanup_temp_directory(temp_dir)
    
    # Merge all page data into final structure
    successful_pages = [p for p in page_data_list if p is not None]
    if successful_pages:
        merged_data, merge_diagnostics = merge_page_results(page_data_list, page_diagnostics_list)
        print_progress(f"Successfully processed {len(successful_pages)}/{total_pages} pages")
        
        # Save comprehensive diagnostics  
        if output_dir:
            diagnostics_file = output_dir / "toc_extraction_diagnostics.json"
        else:
            diagnostics_file = "toc_extraction_diagnostics.json"
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
    Main function for single-page TOC contents parsing script with text guidance.
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description='Parse table of contents structure from PDF using single-page GPT-4 Vision processing with text guidance'
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
    yaml_file = output_dir / "thesis_contents.yaml"
    text_file = output_dir / "thesis_contents.txt"
    diagnostics_file = output_dir / "toc_extraction_diagnostics.json"
    
    # Display processing information
    print_section_header("TABLE OF CONTENTS STRUCTURE PARSING (SINGLE-PAGE WITH TEXT GUIDANCE)")
    print(f"Input PDF: {args.pdf_path}")
    print(f"Pages: {args.start_page}-{args.end_page}")
    print(f"Output directory: {args.output_dir}")
    print(f"Files to be created:")
    print(f"  - {yaml_file}")
    print(f"  - {text_file}")
    print(f"  - {diagnostics_file}")
    print("=" * 60)
    
    # Parse the table of contents structure with single-page processing
    result = parse_contents(args.pdf_path, args.start_page, args.end_page, api_key, output_dir, args.debug)
    
    # Check for processing errors
    if result is None:
        print("FAILED: Could not extract table of contents structure")
        return 1
    
    # Save structured data to YAML file
    if not save_yaml_data(result, str(yaml_file)):
        return 1
    
    # Generate simple text format for validation
    try:
        generate_simple_text_toc(result, str(text_file))
    except Exception as e:
        print_progress(f"- Warning: Could not generate text format: {e}")
    
    # Display completion summary with statistics
    sections = result.get('sections', [])
    chapters = [s for s in sections if s.get('type') == 'chapter']
    
    print_completion_summary(str(yaml_file), len(sections), "total entries")
    print(f"Including {len(chapters)} chapters")
    print(f"Text format saved to: {text_file}")
    
    # Validate section numbering
    print_progress("Validating section numbering...")
    validation_results = validate_section_numbering(sections)
    print_numbering_validation(validation_results)
    
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())
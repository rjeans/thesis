#!/usr/bin/env python3
"""
Shared utilities for TOC parsing scripts.

This module contains common functions and patterns used across all TOC parsing
scripts (contents, figures, tables) to eliminate code duplication.
"""

import argparse
import json
import tempfile
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

from gpt_vision_utils import call_gpt_vision_api, encode_images_for_vision
from prompt_utils import create_toc_parsing_prompt
from pdf_utils import extract_pages_to_pdf, pdf_to_images, extract_text_from_pdf_page
from progress_utils import print_progress, print_completion_summary, print_section_header


def save_debug_files(
    output_path: Path,
    page_num: int,
    content_type: str,
    prompt: str,
    text_context: str,
    raw_output: str,
    cleaned_output: str
) -> None:
    """
    Save debug files for a single page processing operation.
    
    Args:
        output_path: Base output directory path
        page_num: Page number being processed
        content_type: Type of content ('contents', 'figures', 'tables')
        prompt: The prompt sent to GPT-4 Vision
        text_context: Extracted text context from PDF
        raw_output: Raw response from GPT-4 Vision
        cleaned_output: Cleaned/processed response
    """
    prefix = f"toc_{content_type}_page_{page_num}" if content_type != "contents" else f"toc_page_{page_num}"
    
    # Save prompt
    prompt_path = output_path / f"{prefix}_prompt.txt"
    with open(prompt_path, 'w', encoding='utf-8') as f:
        f.write(prompt)
    print_progress(f"  Prompt saved to: {prompt_path}")
    
    # Save text context
    text_context_path = output_path / f"{prefix}_text_context.txt"
    with open(text_context_path, 'w', encoding='utf-8') as f:
        f.write(text_context)
    print_progress(f"  Text context saved to: {text_context_path}")
    
    # Save raw GPT output
    raw_output_path = output_path / f"{prefix}_raw_output.txt"
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        f.write(raw_output)
    print_progress(f"  Raw GPT output saved to: {raw_output_path}")
    
    # Save cleaned output
    cleaned_output_path = output_path / f"{prefix}_cleaned_output.txt"
    with open(cleaned_output_path, 'w', encoding='utf-8') as f:
        f.write(cleaned_output)
    print_progress(f"  Cleaned output saved to: {cleaned_output_path}")


def process_single_page(
    pdf_path: str,
    page_num: int,
    temp_dir: str,
    output_path: Path,
    content_type: str,
    yaml_structure: str,
    debug: bool = False
) -> Optional[Dict]:
    """
    Process a single page through the complete GPT-4 Vision pipeline.
    
    Args:
        pdf_path: Path to source PDF file
        page_num: Page number to process (1-based)
        temp_dir: Temporary directory for intermediate files
        output_path: Output directory for debug files
        content_type: Type of content ('contents', 'figures', 'tables')
        yaml_structure: YAML structure template for prompts
        debug: Whether to save debug files
        
    Returns:
        Parsed YAML data from GPT-4 Vision, or None if processing failed
    """
    print_progress(f"\nProcessing page {page_num}...")
    
    # Extract single page to PDF
    page_pdf_path = Path(temp_dir) / f"page_{page_num}.pdf"
    if not extract_pages_to_pdf(pdf_path, str(page_pdf_path), page_num, page_num):
        print_progress(f"- Failed to extract page {page_num}")
        return None

    # Convert page to images
    image_paths = pdf_to_images(str(page_pdf_path), temp_dir)
    if not image_paths:
        print_progress(f"- Failed to convert page {page_num} to image")
        return None

    # Prepare for GPT-4 Vision API call
    image_contents = encode_images_for_vision(image_paths)
    prompt = create_toc_parsing_prompt(content_type, yaml_structure)
    
    # Extract text context for debug
    text_context = ""
    if debug:
        text_context = extract_text_from_pdf_page(pdf_path, page_num, page_num)

    print_progress(f"  Sending to GPT-4 Vision API for {content_type} extraction...")
    result = call_gpt_vision_api(prompt, image_contents)
    
    if not result or result.startswith("Error:"):
        print_progress(f"- GPT-4 Vision API error on page {page_num}: {result}")
        return None
    
    # Clean the result
    cleaned_result = result.strip().removeprefix('```yaml').removeprefix('```').removesuffix('```')
    
    # Save debug files if requested
    if debug:
        save_debug_files(
            output_path, page_num, content_type,
            prompt, text_context, result, cleaned_result
        )
    
    # Parse YAML
    try:
        page_data = yaml.safe_load(cleaned_result.strip())
        return page_data
    except yaml.YAMLError as e:
        print_progress(f"- YAML parsing error for page {page_num}: {e}")
        return None


def process_pages_batch(
    pdf_path: str,
    start_page: int,
    end_page: int,
    output_path: Path,
    content_type: str,
    yaml_structure: str,
    debug: bool = False,
    page_processor: Optional[Callable] = None
) -> List[Dict]:
    """
    Process a batch of pages using the standard page-by-page pipeline.
    
    Args:
        pdf_path: Path to source PDF file
        start_page: Starting page number (1-based)
        end_page: Ending page number (1-based)
        output_path: Output directory for debug files
        content_type: Type of content ('contents', 'figures', 'tables')
        yaml_structure: YAML structure template for prompts
        debug: Whether to save debug files
        page_processor: Optional custom processor for page results
        
    Returns:
        List of successfully parsed page data dictionaries
    """
    all_pages_data = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for page_num in range(start_page, end_page + 1):
            page_data = process_single_page(
                pdf_path, page_num, temp_dir, output_path,
                content_type, yaml_structure, debug
            )
            
            if page_data:
                # Apply custom processing if provided
                if page_processor:
                    page_data = page_processor(page_data, page_num)
                
                all_pages_data.append(page_data)
                
                # Report success based on content type
                if content_type == "contents" and 'sections' in page_data:
                    print_progress(f"+ Successfully parsed {len(page_data['sections'])} sections from page {page_num}")
                elif content_type == "figures" and 'figures' in page_data:
                    print_progress(f"+ Successfully parsed {len(page_data['figures'])} figures from page {page_num}")
                elif content_type == "tables" and 'tables' in page_data:
                    print_progress(f"+ Successfully parsed {len(page_data['tables'])} tables from page {page_num}")
                else:
                    print_progress(f"+ No {content_type} found on page {page_num}")
    
    return all_pages_data


def save_diagnostics(
    output_path: Path,
    content_type: str,
    start_page: int,
    end_page: int,
    final_structure: Dict,
    all_pages_data: List[Dict]
) -> None:
    """
    Save comprehensive diagnostics for TOC parsing operation.
    
    Args:
        output_path: Output directory path
        content_type: Type of content ('contents', 'figures', 'tables')
        start_page: Starting page number processed
        end_page: Ending page number processed
        final_structure: Final processed structure
        all_pages_data: Raw page processing results
    """
    if content_type == "contents":
        diagnostics_data = {
            'processing_summary': {
                'pages_processed': end_page - start_page + 1,
                'total_sections': len(final_structure.get('sections', [])),
                'front_matter_sections': len([s for s in final_structure.get('sections', []) if s.get('type') == 'front_matter']),
                'chapters': len([s for s in final_structure.get('sections', []) if s.get('type') == 'chapter']),
                'back_matter_sections': len([s for s in final_structure.get('sections', []) if s.get('type') == 'back_matter']),
                'appendices': len([s for s in final_structure.get('sections', []) if s.get('type') == 'appendix']),
            },
            'page_processing_results': all_pages_data,
            'section_analysis': [
                {
                    'section_number': section.get('section_number'),
                    'title': section.get('title'),
                    'type': section.get('type'),
                    'page_range': f"{section.get('page_start')}-{section.get('page_end')}",
                    'subsection_count': len(section.get('subsections', []))
                }
                for section in final_structure.get('sections', [])
            ]
        }
        filename = "toc_extraction_diagnostics.json"
        
    elif content_type == "figures":
        diagnostics_data = {
            'processing_summary': {
                'pages_processed': end_page - start_page + 1,
                'total_figures': len(final_structure.get('figures', [])),
                'page_range': f"{start_page}-{end_page}",
            },
            'figures_analysis': [
                {
                    'figure_number': fig.get('figure_number'),
                    'title': fig.get('title'),
                    'page': fig.get('page'),
                    'chapter': fig.get('chapter')
                }
                for fig in final_structure.get('figures', [])
            ]
        }
        filename = "figures_extraction_diagnostics.json"
        
    elif content_type == "tables":
        diagnostics_data = {
            'processing_summary': {
                'pages_processed': end_page - start_page + 1,
                'total_tables': len(final_structure.get('tables', [])),
                'page_range': f"{start_page}-{end_page}",
            },
            'tables_analysis': [
                {
                    'table_number': table.get('table_number'),
                    'title': table.get('title'),
                    'page': table.get('page'),
                    'chapter': table.get('chapter')
                }
                for table in final_structure.get('tables', [])
            ]
        }
        filename = "tables_extraction_diagnostics.json"
    
    else:
        print_progress(f"- Unknown content type for diagnostics: {content_type}")
        return
    
    diagnostics_path = output_path / filename
    with open(diagnostics_path, 'w', encoding='utf-8') as f:
        json.dump(diagnostics_data, f, indent=2, ensure_ascii=False)
    print_progress(f"Diagnostics saved to: {diagnostics_path}")


def save_yaml_output(
    output_path: Path,
    content_type: str,
    final_structure: Dict,
    start_page: int,
    end_page: int
) -> str:
    """
    Save final YAML output and return the output file path.
    
    Args:
        output_path: Output directory path
        content_type: Type of content ('contents', 'figures', 'tables')
        final_structure: Final processed structure to save
        start_page: Starting page number processed
        end_page: Ending page number processed
        
    Returns:
        Path to the saved YAML file
    """
    # Generate YAML content
    enhanced_yaml = yaml.dump(final_structure, default_flow_style=False, sort_keys=False)
    
    # Determine output filename
    if content_type == "contents":
        filename = "thesis_contents.yaml"
    elif content_type == "figures":
        filename = "thesis_figures.yaml"
    elif content_type == "tables":
        filename = "thesis_tables.yaml"
    else:
        filename = f"thesis_{content_type}.yaml"
    
    # Save to file
    yaml_output_path = output_path / filename
    with open(yaml_output_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_yaml)
    
    # Print completion summary
    print_completion_summary(str(yaml_output_path), end_page - start_page + 1, "pages processed")
    
    return str(yaml_output_path)


def create_standard_argument_parser(
    description: str,
    example_usage: str,
    default_pages: str = "9 12"
) -> argparse.ArgumentParser:
    """
    Create standardized argument parser for TOC parsing scripts.
    
    Args:
        description: Description for the script
        example_usage: Example usage string
        default_pages: Default page range for example
        
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Example:
  python parse_toc_{{script}}.py --input thesis.pdf --start-page {default_pages.split()[0]} --end-page {default_pages.split()[1]} --output structure/
  
{example_usage}
"""
    )
    
    parser.add_argument('--input', required=True, help='Path to source PDF file')
    parser.add_argument('--start-page', type=int, required=True, help='Starting page number (1-based)')
    parser.add_argument('--end-page', type=int, required=True, help='Ending page number (1-based)')
    parser.add_argument('--output', required=True, help='Output directory for structure files')
    parser.add_argument('--debug', action='store_true', help='Write prompt and text context files for debugging')
    parser.add_argument('--diagnostics', action='store_true', help='Write detailed diagnostics and analysis files')
    
    return parser


def validate_and_setup(args: argparse.Namespace, content_type: str) -> Path:
    """
    Validate arguments and setup output directory.
    
    Args:
        args: Parsed command line arguments
        content_type: Type of content being processed
        
    Returns:
        Path object for output directory
        
    Raises:
        SystemExit: If validation fails
    """
    # Validate input file
    if not Path(args.input).exists():
        print(f"ERROR: PDF file not found: {args.input}")
        exit(1)
    
    # Create output directory
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Print header
    print_section_header(f"TOC {content_type.upper()} PARSING")
    print_progress(f"Processing pages {args.start_page}-{args.end_page} from {args.input}")
    
    return output_path


def run_standard_toc_parser(
    content_type: str,
    yaml_structure_func: Callable[[], str],
    content_processor: Callable[[List[Dict]], Any],
    description: str,
    example_usage: str,
    default_pages: str = "9 12"
) -> bool:
    """
    Standard main function for TOC parsing scripts.
    
    Args:
        content_type: Type of content ('contents', 'figures', 'tables')
        yaml_structure_func: Function that returns YAML structure template
        content_processor: Function to process collected content
        description: Script description for argument parser
        example_usage: Example usage text
        default_pages: Default page range for examples
        
    Returns:
        True if parsing succeeded, False otherwise
    """
    # Parse arguments
    parser = create_standard_argument_parser(description, example_usage, default_pages)
    args = parser.parse_args()
    
    # Validate and setup
    output_path = validate_and_setup(args, content_type)
    
    # Get YAML structure
    yaml_structure = yaml_structure_func()
    
    # Process pages
    all_pages_data = process_pages_batch(
        args.input,
        args.start_page,
        args.end_page,
        output_path,
        content_type,
        yaml_structure,
        debug=args.debug
    )
    
    if not all_pages_data:
        print_progress(f"- No {content_type} were extracted from any page.")
        return False
    
    # Process the collected data
    try:
        final_structure = content_processor(all_pages_data)
    except Exception as e:
        print_progress(f"- Error processing {content_type} data: {e}")
        return False
    
    # Generate diagnostics if requested
    if args.diagnostics:
        save_diagnostics(
            output_path, content_type, 
            args.start_page, args.end_page,
            final_structure, all_pages_data
        )
    
    # Save YAML output
    save_yaml_output(
        output_path, content_type, final_structure,
        args.start_page, args.end_page
    )
    
    return True
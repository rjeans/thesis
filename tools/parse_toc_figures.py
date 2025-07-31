#!/usr/bin/env python3
"""
Parse figures list from thesis PDF to extract figure catalog.

This tool extracts figure information including titles, page numbers,
and chapter associations from the figures list pages of a PDF thesis.
"""

import argparse
import yaml
from pathlib import Path
import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gpt_vision_utils import call_gpt_vision_api, encode_images_for_vision
from prompt_utils import create_toc_parsing_prompt
from pdf_utils import extract_pages_to_pdf, pdf_to_images, extract_text_from_pdf_page
from progress_utils import print_progress, print_completion_summary, print_section_header


def create_figures_yaml_structure():
    """Create YAML structure template for figures parsing."""
    return """figures:
- figure_number: "2.1"
  title: "Figure title from the figures list"
  page: 45
  chapter: 2
- figure_number: "3.5.6"
  title: "Complex numbered figure title"
  page: 78
  chapter: 3
extraction_metadata:
  pages_processed: 3
  extraction_date: "2024-01-01"
  tool_version: "simplified"
"""


def parse_toc_figures(pdf_path, start_page, end_page, output_dir):
    """
    Parse figures list from PDF pages to extract figure catalog.
    
    Args:
        pdf_path (str): Path to the source PDF file
        start_page (int): Starting page number (1-based)
        end_page (int): Ending page number (1-based)
        output_dir (str): Directory to save output files
    
    Returns:
        bool: True if parsing succeeded, False otherwise
    """
    print_section_header("TOC FIGURES PARSING")
    print_progress(f"Processing pages {start_page}-{end_page} from {pdf_path}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Extract figures list pages to temporary PDF
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        figures_pdf_path = Path(temp_dir) / "toc_figures.pdf"
        
        print_progress(f"Extracting pages {start_page}-{end_page}...")
        success = extract_pages_to_pdf(pdf_path, str(figures_pdf_path), start_page, end_page)
        if not success:
            print_progress("- Failed to extract figures list pages")
            return False
        
        # Convert to images
        print_progress("Converting PDF to images...")
        image_paths = pdf_to_images(str(figures_pdf_path), temp_dir)
        if not image_paths:
            print_progress("- Failed to convert PDF to images")
            return False
        
        # Extract text context for guidance
        text_context = ""
        for page_num in range(start_page, end_page + 1):
            page_text = extract_text_from_pdf_page(pdf_path, page_num)
            if page_text:
                text_context += f"\n--- Page {page_num} ---\n{page_text}"
        
        # Encode images for Vision API
        image_contents = encode_images_for_vision(image_paths)
        
        # Create parsing prompt
        yaml_structure = create_figures_yaml_structure()
        prompt = create_toc_parsing_prompt("figures", yaml_structure)
        
        # Add text guidance to prompt
        if text_context:
            prompt += f"\n\nEXTRACTED TEXT FOR REFERENCE:\n{text_context[:2000]}..."
        
        print_progress("Sending to GPT-4 Vision API for figures extraction...")
        
        # Call GPT-4 Vision API
        result = call_gpt_vision_api(prompt, image_contents)
        
        if result and not result.startswith("Error:"):
            # Clean the result
            cleaned_result = result.strip()
            if cleaned_result.startswith('```yaml'):
                cleaned_result = cleaned_result[7:]
            elif cleaned_result.startswith('```'):
                cleaned_result = cleaned_result[3:]
            if cleaned_result.endswith('```'):
                cleaned_result = cleaned_result[:-3]
            
            # Save YAML output
            yaml_output_path = output_path / "thesis_figures.yaml"
            with open(yaml_output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_result.strip())
            
            # Save text output for reference
            text_output_path = output_path / "thesis_figures.txt"
            with open(text_output_path, 'w', encoding='utf-8') as f:
                f.write(f"Figures List Extraction\n")
                f.write(f"Pages: {start_page}-{end_page}\n")
                f.write(f"Source: {pdf_path}\n\n")
                f.write("Extracted Text Context:\n")
                f.write(text_context)
            
            print_completion_summary(str(yaml_output_path), end_page - start_page + 1, "pages processed")
            print_progress(f"Text reference saved to: {text_output_path}")
            return True
        else:
            print_progress(f"- GPT-4 Vision API error: {result}")
            return False


def main():
    """Main function for TOC figures parsing."""
    parser = argparse.ArgumentParser(
        description='Parse figures list to extract figure catalog',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python parse_toc_figures.py thesis.pdf 13 15 structure/
  
This will extract the figure catalog from pages 13-15 and save it to structure/thesis_figures.yaml
"""
    )
    
    parser.add_argument('pdf_path', help='Path to source PDF file')
    parser.add_argument('start_page', type=int, help='Starting page number (1-based)')
    parser.add_argument('end_page', type=int, help='Ending page number (1-based)')
    parser.add_argument('output_dir', help='Output directory for structure files')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.pdf_path).exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        return 1
    
    # Parse TOC figures
    success = parse_toc_figures(
        args.pdf_path,
        args.start_page,
        args.end_page,
        args.output_dir
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
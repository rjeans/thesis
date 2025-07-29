#!/usr/bin/env python3
"""
Parse table of contents from thesis PDF to extract chapter/section structure.

This tool extracts the hierarchical structure of chapters and sections from
the table of contents pages of a PDF thesis document.
"""

import argparse
import yaml
from pathlib import Path
import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gpt_vision_utils import call_gpt_vision_api, encode_images_for_vision, create_toc_parsing_prompt
from pdf_utils import extract_pages_to_pdf, pdf_to_images, extract_text_from_pdf_page
from progress_utils import print_progress, print_completion_summary, print_section_header


def create_contents_yaml_structure():
    """Create YAML structure template for contents parsing."""
    return """thesis_title: "PhD Thesis Title"
total_pages: 215
sections:
- type: front_matter|chapter|appendix|back_matter
  title: "Section Title"
  page_start: 1
  chapter_number: 1  # Only for chapters, null for others
  subsections:
  - section_number: "1.1"
    title: "Subsection Title"
    page: 25
    level: 1  # 1 for main sections, 2 for subsections, etc.
  page_end: 10
extraction_metadata:
  pages_processed: 4
  extraction_date: "2024-01-01"
  tool_version: "simplified"
"""


def parse_toc_contents(pdf_path, start_page, end_page, output_dir):
    """
    Parse table of contents from PDF pages to extract chapter structure.
    
    Args:
        pdf_path (str): Path to the source PDF file
        start_page (int): Starting page number (1-based)
        end_page (int): Ending page number (1-based)
        output_dir (str): Directory to save output files
    
    Returns:
        bool: True if parsing succeeded, False otherwise
    """
    print_section_header("TOC CONTENTS PARSING")
    print_progress(f"Processing pages {start_page}-{end_page} from {pdf_path}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Extract TOC pages to temporary PDF
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        toc_pdf_path = Path(temp_dir) / "toc_contents.pdf"
        
        print_progress(f"Extracting pages {start_page}-{end_page}...")
        success = extract_pages_to_pdf(pdf_path, str(toc_pdf_path), start_page, end_page)
        if not success:
            print_progress("- Failed to extract TOC pages")
            return False
        
        # Convert to images
        print_progress("Converting PDF to images...")
        image_paths = pdf_to_images(str(toc_pdf_path), temp_dir)
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
        yaml_structure = create_contents_yaml_structure()
        prompt = create_toc_parsing_prompt("contents", yaml_structure)
        
        # Add text guidance to prompt
        if text_context:
            prompt += f"\n\nEXTRACTED TEXT FOR REFERENCE:\n{text_context[:2000]}..."
        
        print_progress("Sending to GPT-4 Vision API for structure extraction...")
        
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
            yaml_output_path = output_path / "thesis_contents.yaml"
            with open(yaml_output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_result.strip())
            
            # Save text output for reference
            text_output_path = output_path / "thesis_contents.txt"
            with open(text_output_path, 'w', encoding='utf-8') as f:
                f.write(f"Table of Contents Extraction\n")
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
    """Main function for TOC contents parsing."""
    parser = argparse.ArgumentParser(
        description='Parse table of contents to extract chapter structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python parse_toc_contents.py thesis.pdf 9 12 structure/
  
This will extract the chapter/section structure from pages 9-12 and save it to structure/thesis_contents.yaml
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
    
    # Parse TOC contents
    success = parse_toc_contents(
        args.pdf_path,
        args.start_page,
        args.end_page,
        args.output_dir
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
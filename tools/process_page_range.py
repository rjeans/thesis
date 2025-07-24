#!/usr/bin/env python3
"""
Process specific page ranges directly to markdown for testing and figure processing.

This script allows direct conversion of arbitrary page ranges to markdown,
useful for testing figure captions, anchor points, and specific content processing.

Usage:
    python process_page_range.py thesis.pdf 13 16 figures_test.md --content-type toc
    python process_page_range.py thesis.pdf 60 65 chapter3_figures.md --content-type chapter
    python process_page_range.py thesis.pdf 25 25 single_page_test.md --content-type chapter

Features:
- Direct page range to markdown conversion
- Content-type specific processing with anchor generation
- Figure and table caption testing
- Single page or multi-page processing
- Context-enhanced conversion with PDF text guidance

Requires:
- OpenAI API key in OPENAI_API_KEY environment variable
- PDF processing tools and poppler-utils
"""

import os
import argparse
import tempfile
from pathlib import Path
import sys

# Import our enhanced tools
from pdf_utils import extract_pages_to_pdf
from convert_with_context import convert_pdf_with_context
from progress_utils import print_progress, print_section_header, print_completion_summary


def process_page_range_to_markdown(pdf_path, start_page, end_page, output_path, 
                                 content_type="generic", structure_dir="structure/", 
                                 chapter_name=None):
    """
    Process a specific page range directly to markdown.
    
    Args:
        pdf_path (str): Path to source PDF file
        start_page (int): Starting page number
        end_page (int): Ending page number  
        output_path (str): Output markdown file path
        content_type (str): Type of content being processed
        structure_dir (str): Directory containing YAML structure files
        chapter_name (str, optional): Content identifier for context
        
    Returns:
        bool: True if processing succeeded, False otherwise
    """
    # Validate API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print_progress("ERROR: Please set your OPENAI_API_KEY environment variable")
        return False
    
    # Validate input file
    if not Path(pdf_path).exists():
        print_progress(f"ERROR: PDF file not found: {pdf_path}")
        return False
    
    # Create output directory
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    print_progress(f"Processing pages {start_page}-{end_page} from {pdf_path}")
    print_progress(f"Content type: {content_type}")
    print_progress(f"Output: {output_path}")
    
    # Step 1: Extract page range to temporary PDF
    with tempfile.TemporaryDirectory(prefix="page_range_processing_") as temp_dir:
        temp_pdf = Path(temp_dir) / f"pages_{start_page}_{end_page}.pdf"
        
        print_progress(f"Extracting pages {start_page}-{end_page}...")
        extraction_success = extract_pages_to_pdf(pdf_path, str(temp_pdf), start_page, end_page)
        
        if not extraction_success:
            print_progress(f"- Failed to extract pages {start_page}-{end_page}")
            return False
        
        print_progress(f"+ Successfully extracted pages to {temp_pdf}")
        
        # Step 2: Convert to markdown with context-enhanced processing
        print_progress("Converting to markdown with context enhancement...")
        
        # Generate content name if not provided
        if not chapter_name:
            if start_page == end_page:
                chapter_name = f"Page {start_page}"
            else:
                chapter_name = f"Pages {start_page}-{end_page}"
        
        conversion_success = convert_pdf_with_context(
            str(temp_pdf),
            output_path,
            structure_dir=structure_dir,
            chapter_name=chapter_name,
            content_type=content_type
        )
        
        if conversion_success:
            print_progress(f"+ Successfully converted to {output_path}")
            return True
        else:
            print_progress(f"- Failed to convert pages {start_page}-{end_page}")
            return False


def main():
    """Main function for page range processing."""
    parser = argparse.ArgumentParser(
        description='Process specific page ranges directly to markdown for testing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process figures list pages (13-16) with TOC content type
  python process_page_range.py thesis.pdf 13 16 figures_test.md --content-type toc

  # Process specific chapter pages with figure testing
  python process_page_range.py thesis.pdf 60 65 chapter3_figures.md --content-type chapter

  # Process single page for detailed testing
  python process_page_range.py thesis.pdf 25 25 single_page_test.md --content-type chapter

  # Process with custom structure directory and content name
  python process_page_range.py thesis.pdf 200 204 appendix1.md \\
      --content-type appendix \\
      --structure-dir custom/structure/ \\
      --chapter-name "Appendix 1"

  # Test front matter page
  python process_page_range.py thesis.pdf 5 8 notation_test.md --content-type front_matter
        """
    )
    
    parser.add_argument('pdf_path', help='Path to source PDF file')
    parser.add_argument('start_page', type=int, help='Starting page number')
    parser.add_argument('end_page', type=int, help='Ending page number')
    parser.add_argument('output_path', help='Output markdown file path')
    
    parser.add_argument('--content-type', 
                       choices=['chapter', 'front_matter', 'appendix', 'references', 'toc', 'generic'],
                       default='generic',
                       help='Type of content being processed (affects prompt and anchor generation)')
    parser.add_argument('--structure-dir', 
                       required=True,
                       help='Directory containing YAML structure files')
    parser.add_argument('--chapter-name',
                       help='Content identifier for context (e.g., "Chapter 3", "Figures List")')
    
    args = parser.parse_args()
    
    # Validate page range
    if args.start_page < 1:
        print("ERROR: Start page must be >= 1")
        return 1
    
    if args.end_page < args.start_page:
        print("ERROR: End page must be >= start page")
        return 1
    
    # Display processing information
    print_section_header("PAGE RANGE TO MARKDOWN PROCESSING")
    print(f"PDF: {args.pdf_path}")
    print(f"Page range: {args.start_page}-{args.end_page}")
    print(f"Output: {args.output_path}")
    print(f"Content type: {args.content_type}")
    print(f"Structure directory: {args.structure_dir}")
    if args.chapter_name:
        print(f"Content name: {args.chapter_name}")
    print("=" * 60)
    
    # Process the page range
    success = process_page_range_to_markdown(
        args.pdf_path,
        args.start_page,
        args.end_page,
        args.output_path,
        args.content_type,
        args.structure_dir,
        args.chapter_name
    )
    
    if success:
        print_completion_summary(args.output_path, 1, f"page range processed ({args.start_page}-{args.end_page})")
        return 0
    else:
        print("FAILED: Page range processing unsuccessful")
        return 1


if __name__ == "__main__":
    exit(main())
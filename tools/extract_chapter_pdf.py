#!/usr/bin/env python3
"""
Extract specific page ranges from PDF to create chapter PDFs.

This script creates individual chapter PDF files from a larger thesis PDF
by extracting specific page ranges. It supports multiple PDF extraction
tools for maximum compatibility across different systems.

Usage:
    python extract_chapter_pdf.py thesis.pdf chapter1.pdf 25 45

The script will:
1. Try pdftk first (fastest and most reliable)
2. Fall back to qpdf if pdftk is unavailable
3. Fall back to ghostscript as universal option
4. Create output directory if needed

Requires at least one of:
- pdftk (recommended)
- qpdf 
- ghostscript

This script is typically used after parsing the table of contents
to create individual chapter files for conversion to markdown.
"""

import argparse
from pathlib import Path

# Import common utilities
from pdf_utils import extract_pages_to_pdf
from progress_utils import print_progress, print_section_header


def main():
    """
    Main function for chapter PDF extraction script.
    
    Handles command line arguments, file validation, and coordinates
    the PDF page extraction process using the most appropriate tool
    available on the system.
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description='Extract page range from PDF to create chapter PDF'
    )
    parser.add_argument('input_pdf', help='Input PDF file')
    parser.add_argument('output_pdf', help='Output PDF file') 
    parser.add_argument('start_page', type=int, help='Starting page number')
    parser.add_argument('end_page', type=int, help='Ending page number')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input_pdf).exists():
        print(f"ERROR: PDF file not found: {args.input_pdf}")
        return 1
    
    # Validate page range
    if args.start_page < 1 or args.end_page < args.start_page:
        print(f"ERROR: Invalid page range: {args.start_page}-{args.end_page}")
        return 1
    
    # Display extraction information
    print_section_header("CHAPTER PDF EXTRACTION")
    print(f"Source PDF: {args.input_pdf}")
    print(f"Chapter PDF: {args.output_pdf}")
    print(f"Page range: {args.start_page}-{args.end_page}")
    print("=" * 60)
    
    # Extract the specified page range
    success = extract_pages_to_pdf(
        args.input_pdf, 
        args.output_pdf, 
        args.start_page, 
        args.end_page
    )
    
    if success:
        print_progress("Chapter PDF extraction completed successfully")
        return 0
    else:
        print_progress("Chapter PDF extraction failed")
        return 1


if __name__ == "__main__":
    exit(main())
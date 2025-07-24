#!/usr/bin/env python3
"""
Convert chapter PDF to markdown using GPT-4 Vision.

This script converts a complete academic chapter from PDF format to markdown,
preserving mathematical equations, section structure, and academic formatting.
It uses GPT-4 Vision API to process the entire chapter as a collection of
high-resolution images.

Usage:
    python convert_chapter_pdf.py chapter1.pdf chapter1.md --chapter-name "Introduction"

The script will:
1. Convert the chapter PDF to high-resolution PNG images
2. Send all images to GPT-4 Vision API in a single request
3. Parse the markdown response and clean formatting
4. Save the complete chapter as a markdown file

Requires:
- OpenAI API key in OPENAI_API_KEY environment variable
- poppler-utils for PDF processing (pdftoppm command)

This script is optimized for academic content with:
- LaTeX mathematical notation preservation
- Section and subsection hierarchy
- Figure and equation cross-references
- Academic writing conventions from 1992
"""

import os
import openai
import argparse
from pathlib import Path

# Import common utilities
from pdf_utils import pdf_to_images
from progress_utils import print_progress, print_section_header, print_completion_summary
from gpt_vision_utils import (
    encode_images_for_vision,
    call_gpt_vision_api,
    create_chapter_conversion_prompt,
    cleanup_temp_directory,
    clean_markdown_output
)


def convert_chapter_to_markdown(pdf_path, api_key, chapter_name="Chapter"):
    """
    Convert entire chapter PDF to markdown using GPT-4 Vision API.
    
    Processes all pages of a chapter PDF through GPT-4 Vision to create
    a complete markdown document with preserved mathematical notation,
    academic structure, and proper formatting.
    
    Args:
        pdf_path (str): Path to the chapter PDF file
        api_key (str): OpenAI API key for GPT-4 Vision access
        chapter_name (str): Name/title of the chapter for context
        
    Returns:
        str: Markdown content from GPT-4 Vision API, or error message
    """
    openai.api_key = api_key
    
    print_progress(f"Converting {Path(pdf_path).name} to markdown...")
    
    # Convert chapter PDF to images for Vision API processing
    temp_dir = "/tmp/chapter_conversion"
    images = pdf_to_images(pdf_path, temp_dir, dpi=200, page_prefix="page")
    
    if not images:
        cleanup_temp_directory(temp_dir)
        return "Error: Failed to convert PDF to images"
    
    # Encode images for GPT-4 Vision API
    image_contents = encode_images_for_vision(images)
    
    # Create specialized prompt for chapter conversion
    prompt = create_chapter_conversion_prompt(chapter_name)
    
    # Call GPT-4 Vision API with higher token limit for full chapter
    print_progress(f"Processing {len(images)} pages in single request...")
    result = call_gpt_vision_api(
        prompt, image_contents,
        model="gpt-4o", max_tokens=4000
    )
    
    # Clean up temporary files
    cleanup_temp_directory(temp_dir)
    
    return result


def main():
    """
    Main function for chapter PDF to markdown conversion script.
    
    Handles command line arguments, API key validation, file checking,
    and coordinates the complete chapter conversion workflow with proper
    error handling and output statistics.
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description='Convert chapter PDF to markdown using GPT-4 Vision'
    )
    parser.add_argument('pdf_path', help='Path to chapter PDF file')
    parser.add_argument('output_file', help='Output markdown file')
    parser.add_argument(
        '--chapter-name', 
        default='Chapter', 
        help='Name of chapter for context (default: Chapter)'
    )
    
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
    
    # Display conversion information
    print_section_header("CHAPTER PDF TO MARKDOWN CONVERSION")
    print(f"Input PDF: {args.pdf_path}")
    print(f"Output file: {args.output_file}")
    print(f"Chapter name: {args.chapter_name}")
    print("=" * 60)
    
    # Convert the chapter to markdown
    result = convert_chapter_to_markdown(args.pdf_path, api_key, args.chapter_name)
    
    # Check for API errors
    if result.startswith("Error:"):
        print(f"FAILED: {result}")
        return 1
    
    # Clean and save markdown result
    cleaned_result = clean_markdown_output(result)
    
    try:
        print_progress("Saving markdown content to file...")
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_result)
        
        # Display completion summary with content statistics
        print_completion_summary(str(output_path))
        print(f"Content length: {len(cleaned_result)} characters")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print_progress(f"- Error saving file: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
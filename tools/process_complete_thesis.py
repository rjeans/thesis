#!/usr/bin/env python3
"""
Complete thesis processing workflow using structure-driven extraction and context-enhanced conversion.

This script orchestrates the entire thesis conversion process:
1. Structure-driven content extraction
2. Context-enhanced markdown conversion
3. Cross-reference validation and reporting

Usage:
    # Process all chapters with full context
    python process_complete_thesis.py --all-chapters
    
    # Process specific content
    python process_complete_thesis.py --content "Chapter 2"
    
    # Process front matter only
    python process_complete_thesis.py --front-matter
    
    # Interactive mode
    python process_complete_thesis.py --interactive

Features:
- Intelligent content discovery from YAML structure
- Context-aware conversion with figure/table expectations
- Cross-reference validation and reporting
- Batch processing with progress tracking
- Content-type specific handling

Requires:
- YAML structure files from TOC parsing
- OpenAI API key in OPENAI_API_KEY environment variable
- PDF processing tools and poppler-utils
"""

import os
import argparse
from pathlib import Path
import tempfile
import time

# Import our enhanced tools
from extract_by_structure import load_structure_files, extract_content_by_structure, extract_all_chapters
from convert_with_context import convert_pdf_with_context
from progress_utils import print_progress, print_section_header, print_completion_summary


def process_content_item(pdf_path, content_name, structure_data, temp_dir, output_dir, content_type="chapter", structure_dir="structure/"):
    """
    Process a single content item: extract and convert.
    
    Args:
        pdf_path (str): Source PDF path
        content_name (str): Content identifier
        structure_data (dict): YAML structure data
        temp_dir (str): Temporary directory for extracted PDFs
        output_dir (str): Final output directory
        content_type (str): Type of content
        
    Returns:
        bool: True if processing succeeded
    """
    print_progress(f"Processing {content_name}...")
    
    # Step 1: Extract content to temporary PDF
    extraction_success = extract_content_by_structure(
        pdf_path, content_name, structure_data, temp_dir
    )
    
    if not extraction_success:
        print_progress(f"- Failed to extract {content_name}")
        return False
    
    # Find the extracted PDF file
    temp_dir_path = Path(temp_dir)
    extracted_pdfs = list(temp_dir_path.glob("*.pdf"))
    
    if not extracted_pdfs:
        print_progress(f"- No extracted PDF found for {content_name}")
        return False
    
    # Use the most recently created PDF
    extracted_pdf = max(extracted_pdfs, key=lambda p: p.stat().st_mtime)
    
    # Step 2: Convert to markdown with context
    output_md = Path(output_dir) / f"{extracted_pdf.stem}.md"
    
    conversion_success = convert_pdf_with_context(
        str(extracted_pdf),
        str(output_md),
        structure_dir=structure_dir,
        chapter_name=content_name,
        content_type=content_type
    )
    
    if conversion_success:
        print_progress(f"+ Successfully processed {content_name} -> {output_md}")
        return True
    else:
        print_progress(f"- Failed to convert {content_name}")
        return False


def process_all_chapters(pdf_path, structure_data, output_dir, structure_dir="structure/"):
    """
    Process all chapters in the thesis.
    
    Args:
        pdf_path (str): Source PDF path
        structure_data (dict): YAML structure data
        output_dir (str): Output directory
        
    Returns:
        tuple: (successful_count, total_count)
    """
    if not structure_data.get('contents'):
        print_progress("- No contents structure available")
        return 0, 0
    
    sections = structure_data['contents']['sections']
    chapters = [s for s in sections if s.get('type') == 'chapter']
    
    if not chapters:
        print_progress("- No chapters found in structure")
        return 0, 0
    
    print_progress(f"Processing {len(chapters)} chapters...")
    
    successful = 0
    
    with tempfile.TemporaryDirectory(prefix="thesis_processing_") as temp_dir:
        for i, chapter in enumerate(chapters, 1):
            chapter_num = chapter.get('chapter_number', i)
            content_name = f"Chapter {chapter_num}"
            
            print_progress(f"[{i}/{len(chapters)}] {content_name}...")
            
            success = process_content_item(
                pdf_path, content_name, structure_data, 
                temp_dir, output_dir, "chapter", structure_dir
            )
            
            if success:
                successful += 1
            
            # Small delay between chapters to avoid API rate limits
            if i < len(chapters):
                time.sleep(1)
    
    return successful, len(chapters)


def process_front_matter(pdf_path, structure_data, output_dir, structure_dir="structure/"):
    """
    Process all front matter sections.
    
    Args:
        pdf_path (str): Source PDF path
        structure_data (dict): YAML structure data  
        output_dir (str): Output directory
        
    Returns:
        tuple: (successful_count, total_count)
    """
    if not structure_data.get('contents'):
        print_progress("- No contents structure available")
        return 0, 0
    
    sections = structure_data['contents']['sections']
    front_matter = [s for s in sections if s.get('type') == 'front_matter']
    
    # Now that TOC content has type "toc", we don't need to filter front matter
    convertible_front_matter = front_matter
    
    if not convertible_front_matter:
        print_progress("- No convertible front matter found")
        return 0, 0
    
    print_progress(f"Processing {len(convertible_front_matter)} front matter sections...")
    
    successful = 0
    
    with tempfile.TemporaryDirectory(prefix="thesis_front_matter_") as temp_dir:
        for i, section in enumerate(convertible_front_matter, 1):
            content_name = section['title']
            
            print_progress(f"[{i}/{len(convertible_front_matter)}] {content_name}...")
            
            success = process_content_item(
                pdf_path, content_name, structure_data,
                temp_dir, output_dir, "front_matter", structure_dir
            )
            
            if success:
                successful += 1
            
            time.sleep(1)  # API rate limiting
    
    return successful, len(convertible_front_matter)


def process_appendices(pdf_path, structure_data, output_dir, structure_dir="structure/"):
    """
    Process all appendices.
    
    Args:
        pdf_path (str): Source PDF path
        structure_data (dict): YAML structure data
        output_dir (str): Output directory
        
    Returns:
        tuple: (successful_count, total_count)
    """
    if not structure_data.get('contents'):
        print_progress("- No contents structure available")
        return 0, 0
    
    sections = structure_data['contents']['sections']
    appendices = [s for s in sections if s.get('type') == 'appendix']
    
    if not appendices:
        print_progress("- No appendices found in structure")
        return 0, 0
    
    print_progress(f"Processing {len(appendices)} appendices...")
    
    successful = 0
    
    with tempfile.TemporaryDirectory(prefix="thesis_appendices_") as temp_dir:
        for i, appendix in enumerate(appendices, 1):
            content_name = appendix['title']
            
            print_progress(f"[{i}/{len(appendices)}] {content_name}...")
            
            success = process_content_item(
                pdf_path, content_name, structure_data,
                temp_dir, output_dir, "appendix", structure_dir
            )
            
            if success:
                successful += 1
            
            time.sleep(1)  # API rate limiting
    
    return successful, len(appendices)


def process_toc_content(pdf_path, structure_data, output_dir, structure_dir="structure/"):
    """
    Process all table of contents sections (TOC, figures list, tables list).
    
    Args:
        pdf_path (str): Source PDF path
        structure_data (dict): YAML structure data
        output_dir (str): Output directory
        structure_dir (str): Structure directory path
        
    Returns:
        tuple: (successful_count, total_count)
    """
    if not structure_data.get('contents'):
        print_progress("- No contents structure available")
        return 0, 0
    
    sections = structure_data['contents']['sections']
    toc_sections = [s for s in sections if s.get('type') == 'toc']
    
    if not toc_sections:
        print_progress("- No TOC sections found in structure")
        return 0, 0
    
    print_progress(f"Processing {len(toc_sections)} TOC sections...")
    
    successful = 0
    
    with tempfile.TemporaryDirectory(prefix="thesis_toc_") as temp_dir:
        for i, section in enumerate(toc_sections, 1):
            content_name = section['title']
            
            print_progress(f"[{i}/{len(toc_sections)}] {content_name}...")
            
            success = process_content_item(
                pdf_path, content_name, structure_data,
                temp_dir, output_dir, "toc", structure_dir
            )
            
            if success:
                successful += 1
            
            time.sleep(1)  # API rate limiting
    
    return successful, len(toc_sections)


def interactive_processing_menu(pdf_path, structure_data, output_dir, structure_dir="structure/"):
    """
    Interactive menu for thesis processing.
    
    Args:
        pdf_path (str): Source PDF path
        structure_data (dict): YAML structure data
        output_dir (str): Output directory
    """
    if not structure_data.get('contents'):
        print("No structure data available for processing")
        return
    
    while True:
        print("\n" + "=" * 60)
        print("THESIS PROCESSING MENU")
        print("=" * 60)
        print("[1] Process all chapters")
        print("[2] Process all front matter")
        print("[3] Process all appendices")
        print("[4] Process TOC content (table of contents, figures, tables)")
        print("[5] Process specific content")
        print("[6] Show available content")
        print("[0] Exit")
        
        try:
            choice = input("\nSelect option [0-6]: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                successful, total = process_all_chapters(pdf_path, structure_data, output_dir, structure_dir)
                print_progress(f"Chapters processed: {successful}/{total} successful")
            elif choice == '2':
                successful, total = process_front_matter(pdf_path, structure_data, output_dir, structure_dir)
                print_progress(f"Front matter processed: {successful}/{total} successful")
            elif choice == '3':
                successful, total = process_appendices(pdf_path, structure_data, output_dir, structure_dir)
                print_progress(f"Appendices processed: {successful}/{total} successful")
            elif choice == '4':
                successful, total = process_toc_content(pdf_path, structure_data, output_dir, structure_dir)
                print_progress(f"TOC content processed: {successful}/{total} successful")
            elif choice == '5':
                content_name = input("Enter content name (e.g., 'Chapter 2', 'Abstract'): ").strip()
                if content_name:
                    with tempfile.TemporaryDirectory(prefix="thesis_specific_") as temp_dir:
                        success = process_content_item(
                            pdf_path, content_name, structure_data,
                            temp_dir, output_dir, "generic", structure_dir
                        )
                        if success:
                            print_progress(f"Successfully processed: {content_name}")
                        else:
                            print_progress(f"Failed to process: {content_name}")
            elif choice == '6':
                show_available_content(structure_data)
            else:
                print("Invalid choice")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def show_available_content(structure_data):
    """Display available content for processing."""
    if not structure_data.get('contents'):
        print("No structure data available")
        return
    
    sections = structure_data['contents']['sections']
    
    # Group by type
    front_matter = [s for s in sections if s.get('type') == 'front_matter']
    chapters = [s for s in sections if s.get('type') == 'chapter']  
    appendices = [s for s in sections if s.get('type') == 'appendix']
    toc_sections = [s for s in sections if s.get('type') == 'toc']
    
    print("\nAVAILABLE CONTENT:")
    
    if front_matter:
        print("\nFRONT MATTER:")
        for section in front_matter:
            pages = f"{section['page_start']}-{section.get('page_end', section['page_start'])}"
            print(f"  - {section['title']} (pages {pages})")
    
    if chapters:
        print("\nCHAPTERS:")
        for section in chapters:
            pages = f"{section['page_start']}-{section.get('page_end', '?')}"
            chapter_num = section.get('chapter_number', '?')
            print(f"  - Chapter {chapter_num}: {section['title']} (pages {pages})")
    
    if appendices:
        print("\nAPPENDICES:")
        for section in appendices:
            pages = f"{section['page_start']}-{section.get('page_end', '?')}"
            print(f"  - {section['title']} (pages {pages})")
    
    if toc_sections:
        print("\nTOC CONTENT:")
        for section in toc_sections:
            pages = f"{section['page_start']}-{section.get('page_end', section['page_start'])}"
            print(f"  - {section['title']} (pages {pages})")


def main():
    """Main function for complete thesis processing."""
    parser = argparse.ArgumentParser(
        description='Complete thesis processing with structure-driven extraction and context-enhanced conversion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all chapters
  python process_complete_thesis.py thesis.pdf --all-chapters

  # Process specific content
  python process_complete_thesis.py thesis.pdf --content "Chapter 2"

  # Process front matter only  
  python process_complete_thesis.py thesis.pdf --front-matter

  # Process TOC content (table of contents, figures list, tables list)
  python process_complete_thesis.py thesis.pdf --toc

  # Interactive processing
  python process_complete_thesis.py thesis.pdf --interactive

  # Custom paths
  python process_complete_thesis.py custom/thesis.pdf --all-chapters \\
      --structure-dir custom/structure/ \\
      --output-dir custom/markdown/
        """
    )
    
    parser.add_argument('pdf_path', 
                       help='Path to source PDF file')
    parser.add_argument('--structure-dir', 
                       required=True,
                       help='Directory containing YAML structure files')
    parser.add_argument('--output-dir', 
                       required=True,
                       help='Output directory for markdown files')
    
    # Processing modes
    parser.add_argument('--all-chapters', action='store_true',
                       help='Process all chapters')
    parser.add_argument('--front-matter', action='store_true',
                       help='Process front matter sections')
    parser.add_argument('--appendices', action='store_true',
                       help='Process appendices')
    parser.add_argument('--toc', action='store_true',
                       help='Process TOC content (table of contents, figures list, tables list)')
    parser.add_argument('--content',
                       help='Process specific content (e.g., "Chapter 2", "Abstract")')
    parser.add_argument('--interactive', action='store_true',
                       help='Interactive processing menu')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.pdf_path).exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        return 1
    
    # Validate API key
    if not os.getenv('OPENAI_API_KEY'):
        print("ERROR: Please set your OPENAI_API_KEY environment variable")
        return 1
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Display processing information
    print_section_header("COMPLETE THESIS PROCESSING")
    print(f"PDF: {args.pdf_path}")
    print(f"Structure directory: {args.structure_dir}")
    print(f"Output directory: {args.output_dir}")
    print("=" * 60)
    
    # Load structure data
    structure_data = load_structure_files(args.structure_dir)
    if not structure_data.get('contents'):
        print("ERROR: No contents structure found")
        print("Run the TOC parsing scripts first to generate structure files")
        return 1
    
    # Process based on arguments
    total_processed = 0
    total_successful = 0
    
    if args.interactive:
        interactive_processing_menu(args.pdf_path, structure_data, args.output_dir, args.structure_dir)
        return 0
    
    if args.all_chapters:
        print_progress("Processing all chapters...")
        successful, total = process_all_chapters(args.pdf_path, structure_data, args.output_dir, args.structure_dir)
        total_successful += successful
        total_processed += total
        print_progress(f"Chapters: {successful}/{total} successful")
    
    if args.front_matter:
        print_progress("Processing front matter...")
        successful, total = process_front_matter(args.pdf_path, structure_data, args.output_dir, args.structure_dir)
        total_successful += successful
        total_processed += total
        print_progress(f"Front matter: {successful}/{total} successful")
    
    if args.appendices:
        print_progress("Processing appendices...")
        successful, total = process_appendices(args.pdf_path, structure_data, args.output_dir, args.structure_dir)
        total_successful += successful
        total_processed += total
        print_progress(f"Appendices: {successful}/{total} successful")
    
    if args.toc:
        print_progress("Processing TOC content...")
        successful, total = process_toc_content(args.pdf_path, structure_data, args.output_dir, args.structure_dir)
        total_successful += successful
        total_processed += total
        print_progress(f"TOC content: {successful}/{total} successful")
    
    if args.content:
        print_progress(f"Processing specific content: {args.content}")
        with tempfile.TemporaryDirectory(prefix="thesis_specific_") as temp_dir:
            success = process_content_item(
                args.pdf_path, args.content, structure_data,
                temp_dir, args.output_dir, "generic", structure_dir=args.structure_dir
            )
            total_processed = 1
            total_successful = 1 if success else 0
    
    if not any([args.all_chapters, args.front_matter, args.appendices, args.toc, args.content]):
        print("No processing mode specified")
        show_available_content(structure_data)
        print("\nSpecify --all-chapters, --front-matter, --appendices, --toc, --content, or --interactive")
        return 1
    
    # Final summary
    if total_processed > 0:
        print_completion_summary(args.output_dir, total_successful, 
                               f"items processed ({total_successful}/{total_processed} successful)")
        return 0 if total_successful > 0 else 1
    else:
        return 1


if __name__ == "__main__":
    exit(main())
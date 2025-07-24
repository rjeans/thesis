#!/usr/bin/env python3
"""
Extract thesis content using YAML structure metadata instead of manual page ranges.

This script leverages the comprehensive structure files created by the TOC parsers
to enable intelligent content extraction by content name rather than page numbers.

Usage:
    python extract_by_structure.py --content "Chapter 2" --output chapters/
    python extract_by_structure.py --content "2.3" --output sections/
    python extract_by_structure.py --content "Abstract" --output front_matter/
    python extract_by_structure.py --all-chapters --output chapters/
    python extract_by_structure.py --interactive

Features:
- Intelligent content matching with fuzzy search
- Automatic page range lookup from YAML structure
- Batch processing capabilities
- Interactive content selection
- Comprehensive error handling and suggestions

Requires:
- YAML structure files from TOC parsing
- PDF processing tools (pdftk, qpdf, or ghostscript)
"""

import os
import argparse
import yaml
from pathlib import Path
from difflib import SequenceMatcher, get_close_matches

# Import common utilities
from pdf_utils import extract_pages_to_pdf
from progress_utils import print_progress, print_section_header, print_completion_summary


def load_structure_files(structure_dir):
    """
    Load all YAML structure files from the specified directory.
    
    Args:
        structure_dir (Path): Directory containing YAML structure files
        
    Returns:
        dict: Dictionary with 'contents', 'figures', 'tables' data
    """
    structure_dir = Path(structure_dir)
    
    structure_data = {}
    
    # Load contents structure
    contents_file = structure_dir / "thesis_contents.yaml"
    if contents_file.exists():
        with open(contents_file, 'r', encoding='utf-8') as f:
            structure_data['contents'] = yaml.safe_load(f)
        print_progress(f"+ Loaded contents structure: {len(structure_data['contents']['sections'])} sections")
    else:
        print_progress(f"- Contents file not found: {contents_file}")
        structure_data['contents'] = None
    
    # Load figures structure
    figures_file = structure_dir / "thesis_figures.yaml"
    if figures_file.exists():
        with open(figures_file, 'r', encoding='utf-8') as f:
            structure_data['figures'] = yaml.safe_load(f)
        print_progress(f"+ Loaded figures structure: {len(structure_data['figures']['figures'])} figures")
    else:
        print_progress(f"- Figures file not found: {figures_file}")
        structure_data['figures'] = None
    
    # Load tables structure
    tables_file = structure_dir / "thesis_tables.yaml"
    if tables_file.exists():
        with open(tables_file, 'r', encoding='utf-8') as f:
            structure_data['tables'] = yaml.safe_load(f)
        print_progress(f"+ Loaded tables structure: {len(structure_data['tables']['tables'])} tables")
    else:
        print_progress(f"- Tables file not found: {tables_file}")
        structure_data['tables'] = None
    
    return structure_data


def find_content_in_structure(structure_data, target_content):
    """
    Find target content in the structure using intelligent matching.
    
    Args:
        structure_data (dict): Loaded structure data
        target_content (str): Content identifier to find
        
    Returns:
        dict or None: Found content entry with metadata, or None if not found
    """
    if not structure_data['contents']:
        print_progress("- No contents structure available")
        return None
    
    sections = structure_data['contents']['sections']
    target_lower = target_content.lower()
    
    # Direct matches
    for section in sections:
        # Match by chapter number (e.g., "1", "Chapter 1")
        if section.get('chapter_number'):
            chapter_num = str(section['chapter_number'])
            if target_lower in [chapter_num, f"chapter {chapter_num}", f"ch {chapter_num}"]:
                return section
        
        # Match by title (case-insensitive, partial)
        title = section['title'].lower()
        if target_lower in title or title in target_lower:
            return section
        
        # Match by section number (e.g., "2.3", "2.1.1")
        for subsection in section.get('subsections', []):
            section_num = subsection.get('section_number', '')
            if target_content == section_num:
                # For subsections, we need to determine page range
                # This is complex - for now return the parent chapter
                subsection['parent_chapter'] = section
                subsection['type'] = 'subsection'
                return subsection
    
    # Fuzzy matching for better user experience
    all_titles = []
    for section in sections:
        all_titles.append(section['title'])
        for subsection in section.get('subsections', []):
            if 'title' in subsection:
                all_titles.append(f"{subsection.get('section_number', '')}: {subsection['title']}")
    
    matches = get_close_matches(target_content, all_titles, n=3, cutoff=0.6)
    if matches:
        print_progress(f"- '{target_content}' not found exactly. Did you mean:")
        for i, match in enumerate(matches, 1):
            print_progress(f"  {i}. {match}")
        return None
    
    print_progress(f"- Content '{target_content}' not found in structure")
    return None


def get_section_page_range(section, next_section=None):
    """
    Determine the page range for a section, handling subsections intelligently.
    
    Args:
        section (dict): Section data from YAML
        next_section (dict, optional): Next section for range calculation
        
    Returns:
        tuple: (start_page, end_page)
    """
    start_page = section['page_start']
    
    # If section has explicit page_end, use it
    if 'page_end' in section:
        end_page = section['page_end']
    elif next_section:
        # End just before next section starts
        end_page = next_section['page_start'] - 1
    else:
        # Last section - use some heuristic or require manual specification
        print_progress(f"- Warning: No end page for {section['title']}, using start page")
        end_page = start_page
    
    return start_page, end_page


def suggest_available_content(structure_data):
    """
    Display available content options to help users.
    
    Args:
        structure_data (dict): Loaded structure data
    """
    if not structure_data['contents']:
        print_progress("- No structure data available for suggestions")
        return
    
    sections = structure_data['contents']['sections']
    
    print_section_header("AVAILABLE CONTENT")
    
    # Group by type
    front_matter = [s for s in sections if s.get('type') == 'front_matter']
    chapters = [s for s in sections if s.get('type') == 'chapter']
    appendices = [s for s in sections if s.get('type') == 'appendix']
    references = [s for s in sections if s.get('type') == 'references']
    toc_sections = [s for s in sections if s.get('type') == 'toc']
    
    if front_matter:
        print("FRONT MATTER:")
        for section in front_matter:
            pages = f"{section['page_start']}-{section.get('page_end', section['page_start'])}"
            print(f"  '{section['title']}' (pages {pages})")
    
    if chapters:
        print("\nCHAPTERS:")
        for section in chapters:
            pages = f"{section['page_start']}-{section.get('page_end', '?')}"
            chapter_num = section.get('chapter_number', '?')
            print(f"  'Chapter {chapter_num}' or '{chapter_num}': {section['title']} (pages {pages})")
            
            # Show subsections
            for subsection in section.get('subsections', []):
                subsection_title = f"{subsection.get('section_number', '?')}: {subsection.get('title', '?')}"
                print(f"    '{subsection.get('section_number', '?')}': {subsection.get('title', '?')} (page {subsection.get('page', '?')})")
    
    if appendices:
        print("\nAPPENDICES:")
        for section in appendices:
            pages = f"{section['page_start']}-{section.get('page_end', '?')}"
            print(f"  '{section['title']}' (pages {pages})")
    
    if references:
        print("\nREFERENCES:")
        for section in references:
            pages = f"{section['page_start']}-{section.get('page_end', '?')}"
            print(f"  '{section['title']}' (pages {pages})")
    
    if toc_sections:
        print("\nTOC CONTENT:")
        for section in toc_sections:
            pages = f"{section['page_start']}-{section.get('page_end', section['page_start'])}"
            print(f"  '{section['title']}' (pages {pages})")
    
    print("=" * 60)
    print("\nUSAGE EXAMPLES:")
    print("  --content 'Chapter 2'")
    print("  --content '2'")
    print("  --content '2.3'")
    print("  --content 'Abstract'")
    print("  --content 'References'")
    print("  --content 'CONTENTS'")
    print("  --content 'FIGURES'")


def create_output_filename(section, output_dir):
    """
    Create a standardized output filename for extracted content.
    
    Args:
        section (dict): Section metadata
        output_dir (Path): Output directory
        
    Returns:
        Path: Output file path
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename based on content type
    if section.get('type') == 'chapter':
        chapter_num = section.get('chapter_number', 'X')
        filename = f"chapter_{chapter_num}.pdf"
    elif section.get('type') == 'front_matter':
        title = section['title'].lower().replace(' ', '_')
        filename = f"{title}.pdf"
    elif section.get('type') == 'appendix':
        title = section['title'].lower().replace(' ', '_').replace('.', '')
        filename = f"{title}.pdf"
    elif section.get('type') == 'subsection':
        section_num = section.get('section_number', '').replace('.', '_')
        filename = f"section_{section_num}.pdf"
    elif section.get('type') == 'toc':
        title = section['title'].lower().replace(' ', '_').replace('.', '')
        filename = f"toc_{title}.pdf"
    else:
        # Generic fallback
        title = section['title'].lower().replace(' ', '_').replace('.', '')
        filename = f"{title}.pdf"
    
    return output_dir / filename


def extract_content_by_structure(pdf_path, target_content, structure_data, output_dir):
    """
    Extract specific content using structure metadata.
    
    Args:
        pdf_path (str): Path to source PDF
        target_content (str): Content identifier
        structure_data (dict): Structure metadata
        output_dir (str): Output directory
        
    Returns:
        bool: True if extraction succeeded, False otherwise
    """
    # Find content in structure
    section = find_content_in_structure(structure_data, target_content)
    if not section:
        print_progress(f"- Could not find '{target_content}' in structure")
        suggest_available_content(structure_data)
        return False
    
    # Determine page range
    if section.get('type') == 'subsection':
        print_progress("- Subsection extraction not fully implemented yet")
        print_progress("- Using parent chapter instead")
        section = section.get('parent_chapter', section)
    
    start_page = section['page_start']
    end_page = section.get('page_end')
    
    if not end_page:
        print_progress(f"- Warning: No end page specified for '{section['title']}'")
        print_progress("- Using start page only (single page extraction)")
        end_page = start_page
    
    # Create output filename
    output_file = create_output_filename(section, output_dir)
    
    # Extract content
    print_progress(f"Extracting '{section['title']}' (pages {start_page}-{end_page})")
    print_progress(f"Output: {output_file}")
    
    success = extract_pages_to_pdf(pdf_path, str(output_file), start_page, end_page)
    
    if success:
        print_progress(f"+ Successfully extracted to {output_file}")
        return True
    else:
        print_progress(f"- Failed to extract {target_content}")
        return False


def extract_all_chapters(pdf_path, structure_data, output_dir):
    """
    Extract all chapters in batch mode.
    
    Args:
        pdf_path (str): Path to source PDF
        structure_data (dict): Structure metadata
        output_dir (str): Output directory
        
    Returns:
        int: Number of chapters successfully extracted
    """
    if not structure_data['contents']:
        print_progress("- No contents structure available for batch extraction")
        return 0
    
    sections = structure_data['contents']['sections']
    chapters = [s for s in sections if s.get('type') == 'chapter']
    
    if not chapters:
        print_progress("- No chapters found in structure")
        return 0
    
    print_progress(f"Starting batch extraction of {len(chapters)} chapters...")
    
    successful_extractions = 0
    
    for i, chapter in enumerate(chapters, 1):
        chapter_num = chapter.get('chapter_number', i)
        print_progress(f"[{i}/{len(chapters)}] Processing Chapter {chapter_num}...")
        
        if extract_content_by_structure(pdf_path, f"Chapter {chapter_num}", structure_data, output_dir):
            successful_extractions += 1
        else:
            print_progress(f"- Failed to extract Chapter {chapter_num}")
    
    print_progress(f"Batch extraction completed: {successful_extractions}/{len(chapters)} chapters extracted")
    return successful_extractions


def interactive_content_selector(structure_data):
    """
    Interactive menu for content selection.
    
    Args:
        structure_data (dict): Structure metadata
        
    Returns:
        str or None: Selected content identifier, or None if cancelled
    """
    if not structure_data['contents']:
        print("No structure data available for interactive selection")
        return None
    
    sections = structure_data['contents']['sections']
    
    # Group content by type
    front_matter = [s for s in sections if s.get('type') == 'front_matter']
    chapters = [s for s in sections if s.get('type') == 'chapter']
    appendices = [s for s in sections if s.get('type') == 'appendix']
    toc_sections = [s for s in sections if s.get('type') == 'toc']
    
    print("\n" + "=" * 60)
    print("INTERACTIVE CONTENT SELECTOR")
    print("=" * 60)
    
    menu_items = []
    menu_index = 1
    
    if front_matter:
        print(f"\nFRONT MATTER:")
        for section in front_matter:
            pages = f"{section['page_start']}-{section.get('page_end', section['page_start'])}"
            print(f"[{menu_index}] {section['title']} (pages {pages})")
            menu_items.append(section['title'])
            menu_index += 1
    
    if chapters:
        print(f"\nCHAPTERS:")
        for section in chapters:
            pages = f"{section['page_start']}-{section.get('page_end', '?')}"
            chapter_num = section.get('chapter_number', '?')
            title = f"Chapter {chapter_num}: {section['title']}"
            print(f"[{menu_index}] {title} (pages {pages})")
            menu_items.append(f"Chapter {chapter_num}")
            menu_index += 1
    
    if appendices:
        print(f"\nAPPENDICES:")
        for section in appendices:
            pages = f"{section['page_start']}-{section.get('page_end', '?')}"
            print(f"[{menu_index}] {section['title']} (pages {pages})")
            menu_items.append(section['title'])
            menu_index += 1
    
    if toc_sections:
        print(f"\nTOC CONTENT:")
        for section in toc_sections:
            pages = f"{section['page_start']}-{section.get('page_end', section['page_start'])}"
            print(f"[{menu_index}] {section['title']} (pages {pages})")
            menu_items.append(section['title'])
            menu_index += 1
    
    # Special options
    print(f"\nSPECIAL OPTIONS:")
    print(f"[{menu_index}] Extract all chapters")
    menu_items.append("ALL_CHAPTERS")
    menu_index += 1
    
    print(f"[0] Cancel")
    
    # Get user selection
    try:
        choice = input(f"\nSelect content to extract [0-{len(menu_items)}]: ").strip()
        choice_num = int(choice)
        
        if choice_num == 0:
            return None
        elif 1 <= choice_num <= len(menu_items):
            selected = menu_items[choice_num - 1]
            if selected == "ALL_CHAPTERS":
                return "ALL_CHAPTERS"
            else:
                return selected
        else:
            print(f"Invalid choice: {choice_num}")
            return None
            
    except (ValueError, KeyboardInterrupt):
        print("\nCancelled by user")
        return None


def main():
    """Main function for structure-driven content extraction."""
    parser = argparse.ArgumentParser(
        description='Extract thesis content using YAML structure metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_by_structure.py thesis.pdf --content "Chapter 2" --output-dir chapters/
  python extract_by_structure.py thesis.pdf --content "Abstract" --output-dir front_matter/
  python extract_by_structure.py thesis.pdf --content "2.3" --output-dir sections/
  python extract_by_structure.py thesis.pdf --all-chapters --output-dir chapters/
  python extract_by_structure.py thesis.pdf --interactive

The script looks for structure files in these locations:
  structure/thesis_contents.yaml
  structure/thesis_figures.yaml  
  structure/thesis_tables.yaml
        """
    )
    
    parser.add_argument('pdf_path', 
                       help='Path to source PDF file')
    parser.add_argument('--structure-dir', 
                       required=True,
                       help='Directory containing YAML structure files')
    parser.add_argument('--content',
                       help='Content identifier to extract (e.g., "Chapter 2", "Abstract", "2.3")')
    parser.add_argument('--output-dir', 
                       required=True,
                       help='Output directory for extracted files')
    parser.add_argument('--all-chapters', action='store_true',
                       help='Extract all chapters in batch mode')
    parser.add_argument('--interactive', action='store_true',
                       help='Interactive content selection menu')
    parser.add_argument('--list-content', action='store_true',
                       help='List available content without extracting')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.pdf_path).exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        return 1
    
    # Load structure files
    print_section_header("STRUCTURE-DRIVEN CONTENT EXTRACTION")
    print(f"PDF: {args.pdf_path}")
    print(f"Structure directory: {args.structure_dir}")
    print(f"Output directory: {args.output_dir}")
    print("=" * 60)
    
    structure_data = load_structure_files(args.structure_dir)
    
    if not structure_data['contents']:
        print("ERROR: No contents structure file found")
        print("Run the TOC parsing scripts first to generate structure files")
        return 1
    
    # Handle different modes
    if args.list_content:
        suggest_available_content(structure_data)
        return 0
    
    if args.interactive:
        selected_content = interactive_content_selector(structure_data)
        if not selected_content:
            print("No content selected")
            return 0
        if selected_content == "ALL_CHAPTERS":
            args.all_chapters = True
        else:
            args.content = selected_content
    
    if args.all_chapters:
        successful = extract_all_chapters(args.pdf_path, structure_data, args.output_dir)
        if successful > 0:
            print_completion_summary(args.output_dir, successful, "chapters extracted")
            return 0
        else:
            return 1
    
    if not args.content:
        print("ERROR: No content specified")
        print("Use --content, --all-chapters, --interactive, or --list-content")
        return 1
    
    # Extract specific content
    success = extract_content_by_structure(args.pdf_path, args.content, structure_data, args.output_dir)
    
    if success:
        print_completion_summary(args.output_dir, 1, f"content extracted ({args.content})")
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
"""
Generate individual section markdown files and stitch them into a complete thesis.

This script iterates over the thesis structure to create individual markdown files
for each major section, then combines them into a complete thesis document.
"""

import argparse
import yaml
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from progress_utils import print_progress, print_completion_summary, print_section_header
from section_processor import SectionProcessor


def get_section_filename(section: Dict) -> str:
    """
    Generate filename for a section based on its type and content.
    
    Args:
        section (dict): Section data from structure YAML
        
    Returns:
        str: Filename for the section (e.g., "Chapter_2.md", "Title.md")
    """
    section_type = section.get('type', 'unknown')
    title = section.get('title', 'Unknown')
    section_number = section.get('section_number', '')
    chapter_number = section.get('chapter_number')
    
    if section_type == 'front_matter':
        # Front matter: use title directly (Title.md, Abstract.md, etc.)
        clean_title = title.replace('CHAPTER ', '').replace('Chapter ', '').strip()
        filename = clean_title.title().replace(' ', '_').replace('.', '').replace(',', '')
        return f"{filename}.md"
        
    elif section_type == 'chapter':
        # Chapters: Chapter_X.md format
        if chapter_number:
            return f"Chapter_{chapter_number}.md"
        else:
            # Fallback to section number if no chapter number
            return f"Chapter_{section_number}.md"
            
    elif section_type == 'back_matter':
        # Back matter: use title (References.md, etc.)
        clean_title = title.replace('CHAPTER ', '').replace('Chapter ', '').strip()
        filename = clean_title.title().replace(' ', '_').replace('.', '').replace(',', '')
        return f"{filename}.md"
        
    elif section_type == 'appendix':
        # Appendices: Appendix_X.md format
        if 'APPENDIX' in title:
            # Extract appendix number/identifier
            parts = title.split(' ', 2)
            if len(parts) >= 2:
                appendix_id = parts[1]  # "1", "2", "A", etc.
                return f"Appendix_{appendix_id}.md"
        
        # Fallback
        return f"Appendix_{section_number}.md"
    
    else:
        # Unknown type fallback
        return f"Section_{section_number}.md"


def get_section_identifier(section: Dict) -> str:
    """
    Generate section identifier for the section_processor.py script.
    
    Args:
        section (dict): Section data from structure YAML
        
    Returns:
        str: Section identifier (e.g., "F1", "2", "A1")
    """
    section_type = section.get('type', 'unknown')
    section_number = section.get('section_number', '')
    chapter_number = section.get('chapter_number')
    
    if section_type == 'front_matter':
        # Use section number for front matter (F1, F2, etc.)
        return section_number
        
    elif section_type == 'chapter':
        # Use chapter number for chapters (1, 2, etc.)
        if chapter_number:
            return str(chapter_number)
        else:
            return section_number
            
    elif section_type == 'back_matter':
        # Use section number for back matter (B1, etc.)
        return section_number
        
    elif section_type == 'appendix':
        # Use section number for appendices (A1, A2, etc.)
        return section_number
    
    else:
        return section_number




def get_main_section_identifier(section: Dict) -> str:
    """
    Get the main section identifier that section_processor.py can handle.
    
    Args:
        section (dict): Section data from structure YAML
        
    Returns:
        str: Main section identifier (e.g., "F1", "2", "A1")
    """
    return section.get('section_number', '')




def process_section(
    section: Dict, 
    input_pdf: str, 
    output_dir: str, 
    structure_file: str,
    dry_run: bool = False,
    debug: bool = False
) -> Optional[str]:
    """
    Process a high-level section using SectionProcessor class directly.
    
    Args:
        section (dict): Section data from structure YAML
        input_pdf (str): Path to input PDF file
        output_dir (str): Directory for output files
        structure_file (str): Path to thesis structure YAML file
        dry_run (bool): If True, only show what would be done
        debug (bool): Whether to enable debug output
        
    Returns:
        str: Path to generated markdown file, or None if failed
    """
    section_filename = get_section_filename(section)
    main_section_id = get_main_section_identifier(section)
    subsections = section.get('subsections', [])
    
    print_progress(f"Processing high-level section: {section.get('title', 'Unknown')} -> {section_filename}")
    if subsections:
        print_progress(f"  Section {main_section_id} includes {len(subsections)} subsections (processed automatically)")
    
    if dry_run:
        print_progress(f"  [DRY RUN] Would process section {main_section_id} with SectionProcessor")
        print_progress(f"  [DRY RUN] Would save output as: {section_filename}")
        return str(Path(output_dir) / section_filename)
    
    try:
        # Initialize SectionProcessor
        processor = SectionProcessor(
            pdf_path=input_pdf,
            structure_file=structure_file,
            debug=debug
        )
        
        # Create the complete output file path
        output_file_path = str(Path(output_dir) / section_filename)
        
        # Process the section
        success = processor.process_section(main_section_id, output_file_path)
        
        if success:
            print_progress(f"  ✓ Generated: {section_filename}")
            return output_file_path
        else:
            print_progress(f"  ✗ Failed to generate {section_filename}")
            return None
            
    except Exception as e:
        print_progress(f"  ✗ Exception processing {main_section_id}: {e}")
        return None


# Note: stitch_thesis_sections function removed - now copying individual files instead


def generate_thesis_sections(
    input_pdf: str,
    structure_file: str,
    output_dir: str,
    thesis_dir: str,
    sections_filter: Optional[List[str]] = None,
    section_numbers: Optional[List[str]] = None,
    dry_run: bool = False,
    debug: bool = False
) -> bool:
    """
    Generate all thesis sections and create complete thesis document.
    
    Args:
        input_pdf (str): Path to input PDF file
        structure_file (str): Path to thesis structure YAML file
        output_dir (str): Directory for individual section files
        thesis_dir (str): Directory for complete thesis file
        sections_filter (list, optional): List of section types to process
        section_numbers (list, optional): List of specific section numbers to process (e.g., ['F1', '2', 'A1'])
        dry_run (bool): If True, only show what would be done
        debug (bool): If True, enable debug output from SectionProcessor
        
    Returns:
        bool: True if generation succeeded, False otherwise
    """
    print_section_header("THESIS SECTIONS GENERATION")
    print_progress(f"Input PDF: {input_pdf}")
    print_progress(f"Structure file: {structure_file}")
    print_progress(f"Output directory: {output_dir}")
    print_progress(f"Thesis directory: {thesis_dir}")
    
    # Load structure data
    contents_file = Path(structure_file)
    if not contents_file.exists():
        print_progress(f"✗ Structure file not found: {contents_file}")
        return False
    
    try:
        with open(contents_file, 'r', encoding='utf-8') as f:
            structure_data = yaml.safe_load(f)
    except Exception as e:
        print_progress(f"✗ Error loading structure file: {e}")
        return False
    
    sections = structure_data.get('sections', [])
    if not sections:
        print_progress("✗ No sections found in structure file")
        return False
    
    # Filter sections if requested
    if sections_filter:
        sections = [s for s in sections if s.get('type') in sections_filter]
        print_progress(f"Filtered by type to {len(sections)} sections: {sections_filter}")
    
    # Filter by section numbers if requested
    if section_numbers:
        sections = [s for s in sections if s.get('section_number') in section_numbers]
        print_progress(f"Filtered by section number to {len(sections)} sections: {section_numbers}")
    
    print_progress(f"Found {len(sections)} sections to process")
    
    # Validate output directories exist
    if not Path(output_dir).exists():
        print_progress(f"✗ Output directory does not exist: {output_dir}")
        return False
    
    if not Path(thesis_dir).exists():
        print_progress(f"✗ Thesis directory does not exist: {thesis_dir}")
        return False
    
    # Process each section
    successful_files = []
    failed_sections = []
    
    for i, section in enumerate(sections, 1):
        section_title = section.get('title', 'Unknown')
        print_progress(f"\n[{i}/{len(sections)}] Processing: {section_title}")
        
        result_file = process_section(
            section, input_pdf, output_dir, structure_file, dry_run, debug
        )
        
        if result_file:
            successful_files.append(result_file)
        else:
            failed_sections.append(section_title)
    
    # Report processing results
    print_progress(f"\nProcessing complete:")
    print_progress(f"  ✓ Successful: {len(successful_files)} sections")
    print_progress(f"  ✗ Failed: {len(failed_sections)} sections")
    
    if failed_sections:
        print_progress("Failed sections:")
        for failed in failed_sections:
            print_progress(f"  - {failed}")
    
    # Copy individual section files to thesis directory
    if successful_files and not dry_run:
        import shutil
        print_progress(f"Copying {len(successful_files)} section files to thesis directory...")
        
        copied_files = []
        for section_file in successful_files:
            source_path = Path(section_file)
            dest_path = Path(thesis_dir) / source_path.name
            
            try:
                shutil.copy2(source_path, dest_path)
                copied_files.append(str(dest_path))
                print_progress(f"  ✓ Copied: {source_path.name}")
            except Exception as e:
                print_progress(f"  ✗ Failed to copy {source_path.name}: {e}")
        
        if copied_files:
            print_completion_summary(
                thesis_dir, 
                len(copied_files), 
                "section files copied"
            )
        
        return len(copied_files) > 0
    
    return len(successful_files) > 0


def main():
    """Main function for thesis sections generation."""
    parser = argparse.ArgumentParser(
        description='Generate individual section markdown files in output and thesis directories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all sections
  python generate_thesis_sections.py --input thesis.pdf --structure structure/thesis_contents.yaml --output sections/ --thesis thesis/
  
  # Generate only chapters
  python generate_thesis_sections.py --input thesis.pdf --structure structure/thesis_contents.yaml --output sections/ --thesis thesis/ --sections chapter
  
  # Generate specific sections by number
  python generate_thesis_sections.py --input thesis.pdf --structure structure/thesis_contents.yaml --output sections/ --thesis thesis/ --section-numbers F1 F2 1 2 3
  
  # Generate front matter and specific chapters
  python generate_thesis_sections.py --input thesis.pdf --structure structure/thesis_contents.yaml --output sections/ --thesis thesis/ --section-numbers F1 F2 F3 1 2
  
  # Dry run (show what would be done)
  python generate_thesis_sections.py --input thesis.pdf --structure structure/thesis_contents.yaml --output sections/ --thesis thesis/ --dry-run

File naming conventions:
  - Front matter: Title.md, Abstract.md, Acknowledgements.md
  - Chapters: Chapter_1.md, Chapter_2.md, etc.
  - Back matter: References.md
  - Appendices: Appendix_1.md, Appendix_2.md, etc.
"""
    )
    
    parser.add_argument('--input', required=True, help='Path to input PDF file')
    parser.add_argument('--structure', required=True, help='Path to thesis structure YAML file (e.g., structure/thesis_contents.yaml)')
    parser.add_argument('--output', required=True, help='Directory for individual section markdown files')
    parser.add_argument('--thesis', required=True, help='Directory to copy individual section markdown files')
    parser.add_argument('--sections', nargs='+', 
                       choices=['front_matter', 'chapter', 'back_matter', 'appendix'],
                       help='Section types to process (default: all)')
    parser.add_argument('--section-numbers', nargs='+',
                       help='Specific section numbers to process (e.g., F1 F2 1 2 3 A1 A2)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be done without actually processing')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug output from SectionProcessor (saves prompts and context)')
    
    args = parser.parse_args()
    
    # Validate input files
    if not Path(args.input).exists():
        print(f"ERROR: PDF file not found: {args.input}")
        return 1
    
    if not Path(args.structure).exists():
        print(f"ERROR: Structure file not found: {args.structure}")
        return 1
    
    # Generate thesis sections
    success = generate_thesis_sections(
        args.input,
        args.structure,
        args.output,
        args.thesis,
        sections_filter=args.sections,
        section_numbers=args.section_numbers,
        dry_run=args.dry_run,
        debug=args.debug
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
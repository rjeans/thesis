#!/usr/bin/env python3
"""
Generate markdown table of contents from structured YAML thesis data.

This script converts the parsed thesis structure YAML into a well-formatted
markdown table of contents with working hyperlinks to chapter files and
section anchors.

Usage:
    python generate_toc_markdown.py thesis_contents.yaml README.md

The script will:
1. Parse the structured YAML thesis data
2. Generate hierarchical markdown TOC with proper indentation
3. Create hyperlinks to chapter files and section anchors
4. Handle different section types (chapters, front matter, appendices)

Output format follows standard markdown documentation patterns with
chapter-based file organization for optimal navigation.
"""

import argparse
import yaml
import re
from pathlib import Path
from progress_utils import print_progress, print_section_header


def create_anchor_from_title(section_number, title):
    """
    Create a markdown anchor from section number and title.
    
    Converts section info like "2.1" + "Background Studies" into 
    a clean anchor like "#21-background-studies".
    
    Args:
        section_number (str): Section number like "2.1", "3.4.2"
        title (str): Section title
        
    Returns:
        str: Clean anchor for markdown linking
    """
    # Clean the section number (remove dots)
    clean_number = section_number.replace('.', '') if section_number else ""
    
    # Clean the title (lowercase, replace spaces/special chars with hyphens)
    clean_title = re.sub(r'[^\w\s-]', '', title.lower())
    clean_title = re.sub(r'[-\s]+', '-', clean_title).strip('-')
    
    # Combine number and title
    if clean_number and clean_title:
        return f"#{clean_number}-{clean_title}"
    elif clean_title:
        return f"#{clean_title}"
    else:
        return f"#{clean_number}" if clean_number else "#section"


def determine_chapter_filename(section):
    """
    Determine the appropriate filename for a section.
    
    Creates consistent filenames based on section type and number.
    
    Args:
        section (dict): Section data from YAML
        
    Returns:
        str: Filename like "chapter1.md", "appendixA.md", etc.
    """
    section_type = section.get('type', 'chapter')
    chapter_number = section.get('chapter_number')
    
    if section_type == 'front_matter':
        # Use title-based filename for front matter
        title = section.get('title', 'front-matter')
        clean_title = re.sub(r'[^\w-]', '', title.lower().replace(' ', '-'))
        return f"{clean_title}.md"
    
    elif section_type == 'chapter' and chapter_number:
        return f"chapter{chapter_number}.md"
    
    elif section_type == 'appendix':
        # Use letter-based naming for appendices (A, B, C, etc.)
        if chapter_number:
            appendix_letter = chr(ord('A') + chapter_number - 1)
            return f"appendix{appendix_letter}.md"
        else:
            return "appendix.md"
    
    elif section_type == 'back_matter':
        title = section.get('title', 'back-matter')
        clean_title = re.sub(r'[^\w-]', '', title.lower().replace(' ', '-'))
        return f"{clean_title}.md"
    
    else:
        # Fallback
        return f"section{chapter_number or 'unknown'}.md"


def format_subsection_line(subsection, chapter_filename, level_indent):
    """
    Format a single subsection line with proper indentation and linking.
    
    Args:
        subsection (dict): Subsection data with number, title, level
        chapter_filename (str): Target chapter file
        level_indent (str): Indentation string for this level
        
    Returns:
        str: Formatted markdown line
    """
    section_number = subsection.get('section_number', '')
    title = subsection.get('title', 'Untitled')
    page = subsection.get('page', '')
    
    # Create anchor for this subsection
    anchor = create_anchor_from_title(section_number, title)
    
    # Format the display title
    if section_number:
        display_title = f"{section_number} {title}"
    else:
        display_title = title
    
    # Create the link
    link = f"[{display_title}]({chapter_filename}{anchor})"
    
    # Add page reference if available
    page_ref = f" (p. {page})" if page else ""
    
    return f"{level_indent}- {link}{page_ref}"


def generate_markdown_toc(thesis_data):
    """
    Generate complete markdown table of contents from thesis YAML data.
    
    Args:
        thesis_data (dict): Parsed YAML thesis structure
        
    Returns:
        str: Complete markdown table of contents
    """
    lines = []
    
    # Header
    thesis_title = thesis_data.get('thesis_title', 'PhD Thesis')
    lines.append(f"# {thesis_title}")
    lines.append("")
    lines.append("## Table of Contents")
    lines.append("")
    
    # Process each main section
    sections = thesis_data.get('sections', [])
    
    for section in sections:
        section_type = section.get('type', 'chapter')
        title = section.get('title', 'Untitled')
        chapter_number = section.get('chapter_number')
        page_start = section.get('page_start', '')
        
        # Determine filename for this section
        filename = determine_chapter_filename(section)
        
        # Format main section header
        if section_type == 'chapter' and chapter_number:
            section_header = f"## {chapter_number}. [{title}]({filename})"
        elif section_type in ['front_matter', 'back_matter']:
            section_header = f"## [{title}]({filename})"
        else:
            section_header = f"## [{title}]({filename})"
        
        # Add page reference
        if page_start:
            section_header += f" (p. {page_start})"
        
        lines.append(section_header)
        
        # Process subsections
        subsections = section.get('subsections', [])
        if subsections:
            lines.append("")  # Blank line before subsections
            
            for subsection in subsections:
                level = subsection.get('level', 1)
                
                # Create appropriate indentation (2 spaces per level)
                level_indent = "  " * level
                
                # Format subsection line
                subsection_line = format_subsection_line(subsection, filename, level_indent)
                lines.append(subsection_line)
        
        lines.append("")  # Blank line after each main section
    
    # Add metadata section
    lines.append("---")
    lines.append("")
    lines.append("## Document Information")
    lines.append("")
    total_pages = thesis_data.get('total_pages', 'Unknown')
    lines.append(f"- **Total Pages**: {total_pages}")
    
    # Count sections by type
    chapter_count = len([s for s in sections if s.get('type') == 'chapter'])
    lines.append(f"- **Chapters**: {chapter_count}")
    
    total_subsections = sum(len(s.get('subsections', [])) for s in sections)
    lines.append(f"- **Total Sections**: {total_subsections}")
    
    lines.append("")
    lines.append("*Generated from thesis structure analysis*")
    
    return "\n".join(lines)


def generate_file_list(thesis_data):
    """
    Generate a list of expected markdown files based on thesis structure.
    
    Args:
        thesis_data (dict): Parsed YAML thesis structure
        
    Returns:
        list: List of expected markdown filenames
    """
    files = []
    sections = thesis_data.get('sections', [])
    
    for section in sections:
        filename = determine_chapter_filename(section)
        if filename not in files:
            files.append(filename)
    
    return sorted(files)


def main():
    """
    Main function for TOC markdown generation script.
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description='Generate markdown table of contents from structured thesis YAML'
    )
    parser.add_argument('yaml_file', help='Input YAML file with thesis structure')
    parser.add_argument('output_file', help='Output markdown file for table of contents')
    parser.add_argument('--file-list', help='Optional file to write expected markdown filenames')
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.yaml_file).exists():
        print(f"ERROR: YAML file not found: {args.yaml_file}")
        return 1
    
    print_section_header("MARKDOWN TABLE OF CONTENTS GENERATION")
    print(f"Input YAML: {args.yaml_file}")
    print(f"Output markdown: {args.output_file}")
    if args.file_list:
        print(f"File list: {args.file_list}")
    print("=" * 60)
    
    try:
        # Load thesis structure data
        print_progress("Loading thesis structure YAML...")
        with open(args.yaml_file, 'r', encoding='utf-8') as f:
            thesis_data = yaml.safe_load(f)
        
        sections_count = len(thesis_data.get('sections', []))
        print_progress(f"+ Loaded {sections_count} sections")
        
        # Generate markdown TOC
        print_progress("Generating markdown table of contents...")
        markdown_content = generate_markdown_toc(thesis_data)
        
        # Count generated lines and links
        lines_count = len(markdown_content.split('\n'))
        links_count = markdown_content.count('](')
        print_progress(f"+ Generated {lines_count} lines with {links_count} hyperlinks")
        
        # Save markdown file
        print_progress("Saving markdown table of contents...")
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print_progress(f"+ TOC saved to {output_path}")
        
        # Generate file list if requested
        if args.file_list:
            print_progress("Generating expected file list...")
            expected_files = generate_file_list(thesis_data)
            
            with open(args.file_list, 'w', encoding='utf-8') as f:
                f.write("# Expected Markdown Files\n\n")
                f.write("Based on thesis structure analysis:\n\n")
                for filename in expected_files:
                    f.write(f"- {filename}\n")
            
            print_progress(f"+ File list saved to {args.file_list} ({len(expected_files)} files)")
        
        print("=" * 60)
        print("MARKDOWN TOC GENERATION COMPLETE")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print_progress(f"- Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
"""
Generate a complete thesis document by combining individual markdown sections.

This script uses the YAML structure metadata to combine individual markdown files
in the correct order, creating a complete thesis document with proper navigation.

Usage:
    python generate_complete_document.py thesis_structure.yaml markdown_dir/ complete_thesis.md
    
    # With custom options
    python generate_complete_document.py thesis_structure.yaml markdown_dir/ complete_thesis.md \
        --add-toc \
        --add-page-breaks \
        --include-front-matter
        
Features:
- Automatic section ordering based on YAML structure
- Table of contents generation with hyperlinks
- Page break insertion for print formatting
- Cross-reference validation and linking
- Missing section reporting

Requires:
- YAML structure files from TOC parsing
- Individual markdown files from conversion process
"""

import argparse
import yaml
from pathlib import Path
import re
from collections import defaultdict

from progress_utils import print_progress, print_section_header, print_completion_summary


def load_structure_data(structure_file):
    """Load the complete thesis structure from YAML file."""
    try:
        with open(structure_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print_progress(f"- Failed to load structure file: {e}")
        return None


def find_markdown_files(markdown_dir):
    """Find all markdown files in the directory and map them to content."""
    markdown_dir = Path(markdown_dir)
    
    if not markdown_dir.exists():
        print_progress(f"- Markdown directory not found: {markdown_dir}")
        return {}
    
    # Map different naming patterns to markdown files
    file_mapping = {}
    
    for md_file in markdown_dir.glob("*.md"):
        name = md_file.stem.lower()
        
        # Map various filename patterns
        if name.startswith('chapter_'):
            chapter_num = name.replace('chapter_', '')
            file_mapping[f"chapter_{chapter_num}"] = md_file
            file_mapping[f"chapter {chapter_num}"] = md_file
        elif name.startswith('appendix'):
            file_mapping[name] = md_file
        elif name in ['abstract', 'acknowledgements', 'notation', 'title', 'references']:
            file_mapping[name] = md_file
        else:
            # Generic mapping
            file_mapping[name] = md_file
    
    print_progress(f"+ Found {len(file_mapping)} markdown files")
    return file_mapping


def find_matching_markdown_file(section, file_mapping):
    """Find the markdown file corresponding to a structure section."""
    title = section.get('title', '').lower()
    section_type = section.get('type', '')
    chapter_number = section.get('chapter_number')
    
    # Try various matching strategies
    possible_keys = []
    
    if section_type == 'chapter' and chapter_number:
        possible_keys.extend([
            f"chapter_{chapter_number}",
            f"chapter {chapter_number}",
            f"ch_{chapter_number}",
            f"ch{chapter_number}"
        ])
    
    # Try direct title matching
    clean_title = re.sub(r'[^\w\s]', '', title).strip()
    possible_keys.extend([
        clean_title,
        clean_title.replace(' ', '_'),
        title.split('.')[0].strip().lower() if '.' in title else title,
    ])
    
    # Try section-specific patterns
    if 'abstract' in title:
        possible_keys.append('abstract')
    elif 'acknowledgement' in title:
        possible_keys.extend(['acknowledgements', 'acknowledgment'])
    elif 'notation' in title:
        possible_keys.append('notation')
    elif 'reference' in title:
        possible_keys.extend(['references', 'bibliography'])
    elif 'appendix' in title:
        appendix_match = re.search(r'appendix\s+(\d+)', title)
        if appendix_match:
            num = appendix_match.group(1)
            possible_keys.extend([
                f"appendix_{num}",
                f"appendix {num}",
                f"appendix{num}"
            ])
    
    # Find the first matching file
    for key in possible_keys:
        if key in file_mapping:
            return file_mapping[key]
    
    return None


def generate_table_of_contents(structure_data, add_links=True):
    """Generate a table of contents with optional hyperlinks."""
    if not structure_data or 'sections' not in structure_data:
        return ""
    
    toc_lines = []
    toc_lines.append("# Table of Contents\n")
    
    for section in structure_data['sections']:
        title = section.get('title', 'Unknown Section')
        section_type = section.get('type', '')
        chapter_number = section.get('chapter_number')
        page_start = section.get('page_start', '?')
        
        # Create anchor link if requested
        if add_links:
            # Generate anchor from title
            anchor = re.sub(r'[^\w\s-]', '', title).strip().lower().replace(' ', '-')
            anchor = re.sub(r'-+', '-', anchor).strip('-')
            link_text = f"[{title}](#{anchor})"
        else:
            link_text = title
        
        # Format based on section type
        if section_type == 'front_matter':
            toc_lines.append(f"- {link_text}")
        elif section_type == 'chapter':
            if chapter_number:
                toc_lines.append(f"- **Chapter {chapter_number}:** {link_text}")
            else:
                toc_lines.append(f"- **{link_text}**")
            
            # Add subsections
            for subsection in section.get('subsections', []):
                sub_title = subsection.get('title', 'Unknown Subsection')
                sub_number = subsection.get('section_number', '')
                if add_links:
                    sub_anchor = re.sub(r'[^\w\s-]', '', f"{sub_number} {sub_title}").strip().lower().replace(' ', '-')
                    sub_anchor = re.sub(r'-+', '-', sub_anchor).strip('-')
                    sub_link_text = f"[{sub_number} {sub_title}](#{sub_anchor})"
                else:
                    sub_link_text = f"{sub_number} {sub_title}"
                
                level = subsection.get('level', 1)
                indent = "  " * level
                toc_lines.append(f"{indent}- {sub_link_text}")
        
        elif section_type == 'appendix':
            toc_lines.append(f"- **{link_text}**")
        else:
            toc_lines.append(f"- {link_text}")
    
    toc_lines.append("\n---\n")  # Separator after TOC
    return '\n'.join(toc_lines)


def read_markdown_file(file_path):
    """Read and return the content of a markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        print_progress(f"- Failed to read {file_path}: {e}")
        return None


def add_section_anchor(content, section):
    """Add an anchor to the beginning of a section for navigation."""
    title = section.get('title', 'Unknown Section')
    anchor = re.sub(r'[^\w\s-]', '', title).strip().lower().replace(' ', '-')
    anchor = re.sub(r'-+', '-', anchor).strip('-')
    
    # If content already starts with a header, add anchor to it
    lines = content.split('\n')
    if lines and lines[0].startswith('#'):
        # Extract header text and level
        header_match = re.match(r'^(#+)\s*(.*)$', lines[0])
        if header_match:
            level, header_text = header_match.groups()
            # Add anchor to existing header
            lines[0] = f'{level} {header_text} {{#{anchor}}}'
            return '\n'.join(lines)
    
    # If no header, add one with anchor
    section_type = section.get('type', '')
    chapter_number = section.get('chapter_number')
    
    if section_type == 'chapter' and chapter_number:
        header = f"# Chapter {chapter_number}: {title} {{#{anchor}}}\n\n"
    else:
        header = f"# {title} {{#{anchor}}}\n\n"
    
    return header + content


def combine_markdown_sections(structure_data, file_mapping, add_toc=True, add_page_breaks=False, 
                            include_front_matter=True, add_anchors=True):
    """Combine individual markdown files into a complete document."""
    if not structure_data or 'sections' not in structure_data:
        print_progress("- No structure data available")
        return None
    
    document_parts = []
    found_sections = 0
    missing_sections = []
    
    # Add title and metadata
    thesis_title = structure_data.get('thesis_title', 'PhD Thesis')
    document_parts.append(f"# {thesis_title}\n")
    
    # Add table of contents if requested
    if add_toc:
        toc = generate_table_of_contents(structure_data, add_links=add_anchors)
        document_parts.append(toc)
    
    # Process sections in order
    for i, section in enumerate(structure_data['sections']):
        section_type = section.get('type', '')
        title = section.get('title', 'Unknown Section')
        
        # Skip front matter if not requested
        if not include_front_matter and section_type == 'front_matter':
            continue
        
        # Find corresponding markdown file
        md_file = find_matching_markdown_file(section, file_mapping)
        
        if md_file:
            print_progress(f"+ Found: {title} -> {md_file.name}")
            content = read_markdown_file(md_file)
            
            if content:
                # Add anchors if requested
                if add_anchors:
                    content = add_section_anchor(content, section)
                
                # Add page break if requested
                if add_page_breaks and i > 0:
                    document_parts.append("\n<div style=\"page-break-before: always;\"></div>\n")
                
                document_parts.append(content + "\n")
                found_sections += 1
            else:
                missing_sections.append(f"{title} (file exists but couldn't read)")
        else:
            print_progress(f"- Missing: {title}")
            missing_sections.append(f"{title} (file not found)")
            # Add placeholder
            if add_anchors:
                anchor = re.sub(r'[^\w\s-]', '', title).strip().lower().replace(' ', '-')
                placeholder = f"\n# {title} {{#{anchor}}}\n\n*[Content not available - markdown file not found]*\n"
            else:
                placeholder = f"\n# {title}\n\n*[Content not available - markdown file not found]*\n"
            document_parts.append(placeholder)
    
    # Report results
    total_sections = len(structure_data['sections'])
    if not include_front_matter:
        front_matter_count = len([s for s in structure_data['sections'] if s.get('type') == 'front_matter'])
        total_sections -= front_matter_count
    
    print_progress(f"Document assembly: {found_sections}/{total_sections} sections found")
    
    if missing_sections:
        print_progress(f"Missing sections ({len(missing_sections)}):")
        for missing in missing_sections:
            print_progress(f"  - {missing}")
    
    return '\n'.join(document_parts)


def main():
    """Main function for complete document generation."""
    parser = argparse.ArgumentParser(
        description='Generate complete thesis document from individual markdown sections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic document generation
  python generate_complete_document.py structure/thesis_contents.yaml markdown_output/ complete_thesis.md
  
  # With table of contents and page breaks
  python generate_complete_document.py structure/thesis_contents.yaml markdown_output/ complete_thesis.md \\
      --add-toc --add-page-breaks
  
  # Chapters only (no front matter)
  python generate_complete_document.py structure/thesis_contents.yaml markdown_output/ complete_thesis.md \\
      --no-front-matter
        """
    )
    
    parser.add_argument('structure_file', help='YAML structure file (thesis_contents.yaml)')
    parser.add_argument('markdown_dir', help='Directory containing individual markdown files')
    parser.add_argument('output_file', help='Output file for complete document')
    parser.add_argument('--add-toc', action='store_true', 
                       help='Add table of contents with hyperlinks')
    parser.add_argument('--add-page-breaks', action='store_true',
                       help='Add page breaks between sections for printing')
    parser.add_argument('--no-front-matter', action='store_true',
                       help='Exclude front matter sections')
    parser.add_argument('--no-anchors', action='store_true',
                       help='Do not add navigation anchors to sections')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.structure_file).exists():
        print(f"ERROR: Structure file not found: {args.structure_file}")
        return 1
    
    if not Path(args.markdown_dir).exists():
        print(f"ERROR: Markdown directory not found: {args.markdown_dir}")
        return 1
    
    # Display processing information
    print_section_header("COMPLETE DOCUMENT GENERATION")
    print(f"Structure file: {args.structure_file}")
    print(f"Markdown directory: {args.markdown_dir}")
    print(f"Output file: {args.output_file}")
    print(f"Include TOC: {args.add_toc}")
    print(f"Add page breaks: {args.add_page_breaks}")
    print(f"Include front matter: {not args.no_front_matter}")
    print(f"Add anchors: {not args.no_anchors}")
    print("=" * 60)
    
    # Load structure data
    structure_data = load_structure_data(args.structure_file)
    if not structure_data:
        print("ERROR: Failed to load structure data")
        return 1
    
    # Find markdown files
    file_mapping = find_markdown_files(args.markdown_dir)
    if not file_mapping:
        print("ERROR: No markdown files found")
        return 1
    
    # Generate complete document
    complete_document = combine_markdown_sections(
        structure_data, 
        file_mapping,
        add_toc=args.add_toc,
        add_page_breaks=args.add_page_breaks,
        include_front_matter=not args.no_front_matter,
        add_anchors=not args.no_anchors
    )
    
    if not complete_document:
        print("ERROR: Failed to generate document")
        return 1
    
    # Save complete document
    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(complete_document)
        
        # Display results
        line_count = len(complete_document.split('\n'))
        word_count = len(complete_document.split())
        
        print_completion_summary(str(output_file), 1, "complete document generated")
        print(f"Document statistics: {line_count:,} lines, {word_count:,} words")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: Failed to save complete document: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
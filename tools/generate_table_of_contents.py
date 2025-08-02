#!/usr/bin/env python3
"""
Generate table of contents for sections, figures, and tables from YAML structure files.

This tool creates markdown table of contents with proper anchor links that match
the thesis format for cross-referencing between documents.
"""

import argparse
import yaml
from pathlib import Path
import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from progress_utils import print_progress, print_completion_summary, print_section_header


def generate_section_anchor(section_number):
    """
    Generate anchor ID for sections matching thesis format.
    
    Args:
        section_number (str): Section number (e.g., "2.1", "2.1.1")
        
    Returns:
        str: Anchor ID (e.g., "section-2-1", "section-2-1-1")
    """
    return f"section-{section_number.replace('.', '-')}"


def generate_figure_anchor(figure_number):
    """
    Generate anchor ID for figures matching thesis format.
    
    Args:
        figure_number (str): Figure number (e.g., "2.1", "3.5")
        
    Returns:
        str: Anchor ID (e.g., "figure-2-1", "figure-3-5")
    """
    return f"figure-{figure_number.replace('.', '-')}"


def generate_table_anchor(table_number):
    """
    Generate anchor ID for tables matching thesis format.
    
    Args:
        table_number (str): Table number (e.g., "4.1", "5.2")
        
    Returns:
        str: Anchor ID (e.g., "table-4-1", "table-5-2")
    """
    return f"table-{table_number.replace('.', '-')}"


def format_section_entry(section, level=0):
    """
    Format a section entry for the table of contents.
    
    Args:
        section (dict): Section data from YAML
        level (int): Indentation level
        
    Returns:
        list: List of formatted markdown lines
    """
    section_number = section.get('section_number', '')
    title = section.get('title', 'Unknown Section')
    section_type = section.get('type', 'chapter')
    
    # Clean up title
    title = title.replace('CHAPTER ', '').replace('Chapter ', '')
    if title.startswith(f"{section_number}. "):
        title = title[len(f"{section_number}. "):]
    elif title.startswith(f"{section_number} "):
        title = title[len(f"{section_number} "):]
    
    # Generate anchor link
    if section_type in ['front_matter', 'back_matter', 'appendix']:
        # For non-chapter sections, use the title-based anchor
        anchor_id = title.lower().replace(' ', '-').replace('.', '').replace(',', '')
        anchor_id = ''.join(c for c in anchor_id if c.isalnum() or c == '-')
        link_text = title
    else:
        # For chapter sections, use section number
        anchor_id = generate_section_anchor(section_number)
        link_text = f"{section_number} {title}" if section_number else title
    
    # Format with appropriate indentation
    indent = "  " * level
    
    lines = [f"{indent}- [{link_text}](#{anchor_id})"]
    
    # Add subsections
    subsections = section.get('subsections', [])
    if subsections:
        for subsection in subsections:
            sub_number = subsection.get('section_number', '')
            sub_title = subsection.get('title', 'Unknown Subsection')
            sub_anchor = generate_section_anchor(sub_number)
            
            sub_indent = "  " * (level + 1)
            lines.append(f"{sub_indent}- [{sub_number} {sub_title}](#{sub_anchor})")
    
    return lines


def generate_sections_toc(contents_yaml):
    """
    Generate table of contents for sections from contents YAML.
    
    Args:
        contents_yaml (str): Path to thesis_contents.yaml
        
    Returns:
        list: List of markdown lines for sections TOC
    """
    try:
        with open(contents_yaml, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print_progress(f"- Error loading contents YAML: {e}")
        return []
    
    sections = data.get('sections', [])
    if not sections:
        return []
    
    lines = [
        "# Table of Contents",
        "",
        "## Sections",
        ""
    ]
    
    for section in sections:
        section_lines = format_section_entry(section)
        lines.extend(section_lines)
        lines.append("")  # Add spacing between major sections
    
    return lines


def generate_figures_toc(figures_yaml):
    """
    Generate table of contents for figures from figures YAML.
    
    Args:
        figures_yaml (str): Path to thesis_figures.yaml
        
    Returns:
        list: List of markdown lines for figures TOC
    """
    try:
        with open(figures_yaml, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print_progress(f"- Error loading figures YAML: {e}")
        return []
    
    figures = data.get('figures', [])
    if not figures:
        return []
    
    lines = [
        "## Figures",
        ""
    ]
    
    # Group figures by chapter
    chapters = {}
    for figure in figures:
        chapter = figure.get('chapter', 'Unknown')
        if chapter not in chapters:
            chapters[chapter] = []
        chapters[chapter].append(figure)
    
    # Sort chapters numerically
    sorted_chapters = sorted(chapters.keys(), key=lambda x: int(x) if str(x).isdigit() else 999)
    
    for chapter in sorted_chapters:
        chapter_figures = sorted(chapters[chapter], key=lambda x: x.get('figure_number', ''))
        
        if chapter != 'Unknown':
            lines.append(f"### Chapter {chapter}")
            lines.append("")
        
        for figure in chapter_figures:
            fig_number = figure.get('figure_number', '')
            title = figure.get('title', 'Untitled Figure')
            
            # Clean up title - remove figure number prefix if present
            if title.startswith(f"Figure {fig_number}"):
                title = title[len(f"Figure {fig_number}"):].strip()
                if title.startswith('.') or title.startswith(':'):
                    title = title[1:].strip()
            elif title.startswith(f"{fig_number}"):
                title = title[len(f"{fig_number}"):].strip()
                if title.startswith('.') or title.startswith(':'):
                    title = title[1:].strip()
            
            anchor_id = generate_figure_anchor(fig_number)
            
            lines.append(f"- [Figure {fig_number}: {title}](#{anchor_id})")
        
        lines.append("")
    
    return lines


def generate_tables_toc(tables_yaml):
    """
    Generate table of contents for tables from tables YAML.
    
    Args:
        tables_yaml (str): Path to thesis_tables.yaml
        
    Returns:
        list: List of markdown lines for tables TOC
    """
    try:
        with open(tables_yaml, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print_progress(f"- Error loading tables YAML: {e}")
        return []
    
    tables = data.get('tables', [])
    if not tables:
        return []
    
    lines = [
        "## Tables",
        ""
    ]
    
    # Group tables by chapter
    chapters = {}
    for table in tables:
        chapter = table.get('chapter', 'Unknown')
        if chapter not in chapters:
            chapters[chapter] = []
        chapters[chapter].append(table)
    
    # Sort chapters numerically
    sorted_chapters = sorted(chapters.keys(), key=lambda x: int(x) if str(x).isdigit() else 999)
    
    for chapter in sorted_chapters:
        chapter_tables = sorted(chapters[chapter], key=lambda x: x.get('table_number', ''))
        
        if chapter != 'Unknown':
            lines.append(f"### Chapter {chapter}")
            lines.append("")
        
        for table in chapter_tables:
            table_number = table.get('table_number', '')
            title = table.get('title', 'Untitled Table')
            
            # Clean up title - remove table number prefix if present
            if title.startswith(f"Table {table_number}"):
                title = title[len(f"Table {table_number}"):].strip()
                if title.startswith('.') or title.startswith(':'):
                    title = title[1:].strip()
            elif title.startswith(f"{table_number}"):
                title = title[len(f"{table_number}"):].strip()
                if title.startswith('.') or title.startswith(':'):
                    title = title[1:].strip()
            
            anchor_id = generate_table_anchor(table_number)
            
            lines.append(f"- [Table {table_number}: {title}](#{anchor_id})")
        
        lines.append("")
    
    return lines


def generate_complete_toc(structure_dir, output_file, include_sections=True, include_figures=True, include_tables=True):
    """
    Generate complete table of contents from structure YAML files.
    
    Args:
        structure_dir (str): Path to directory containing YAML structure files
        output_file (str): Path to output markdown file
        include_sections (bool): Whether to include sections TOC
        include_figures (bool): Whether to include figures TOC
        include_tables (bool): Whether to include tables TOC
        
    Returns:
        bool: True if generation succeeded, False otherwise
    """
    print_section_header("TABLE OF CONTENTS GENERATION")
    print_progress(f"Generating TOC from {structure_dir} to {output_file}")
    
    structure_path = Path(structure_dir)
    all_lines = []
    
    # Generate sections TOC
    if include_sections:
        contents_file = structure_path / "thesis_contents.yaml"
        if contents_file.exists():
            print_progress("Processing sections from thesis_contents.yaml")
            section_lines = generate_sections_toc(str(contents_file))
            all_lines.extend(section_lines)
        else:
            print_progress("- thesis_contents.yaml not found, skipping sections")
    
    # Generate figures TOC
    if include_figures:
        figures_file = structure_path / "thesis_figures.yaml"
        if figures_file.exists():
            print_progress("Processing figures from thesis_figures.yaml")
            figure_lines = generate_figures_toc(str(figures_file))
            all_lines.extend(figure_lines)
        else:
            print_progress("- thesis_figures.yaml not found, skipping figures")
    
    # Generate tables TOC
    if include_tables:
        tables_file = structure_path / "thesis_tables.yaml"
        if tables_file.exists():
            print_progress("Processing tables from thesis_tables.yaml")
            table_lines = generate_tables_toc(str(tables_file))
            all_lines.extend(table_lines)
        else:
            print_progress("- thesis_tables.yaml not found, skipping tables")
    
    if not all_lines:
        print_progress("- No content generated for table of contents")
        return False
    
    # Add footer
    all_lines.extend([
        "---",
        "",
        "*Table of contents generated from thesis structure files.*",
        "*Links correspond to anchors in the converted markdown chapters.*"
    ])
    
    # Write output file
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_lines))
        
        total_items = len([line for line in all_lines if line.strip().startswith('- [')])
        print_completion_summary(str(output_path), total_items, "TOC entries generated")
        return True
        
    except Exception as e:
        print_progress(f"- Error writing TOC file: {e}")
        return False


def main():
    """Main function for table of contents generation."""
    parser = argparse.ArgumentParser(
        description='Generate table of contents for sections, figures, and tables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python generate_table_of_contents.py --structure-dir structure/ --output markdown_output/table_of_contents.md
  
  # Generate only specific TOCs:
  python generate_table_of_contents.py --structure-dir structure/ --output toc.md --no-tables --no-figures
  
This will generate a complete table of contents with anchor links matching the thesis format.
"""
    )
    
    parser.add_argument('--structure-dir', required=True, help='Path to directory containing YAML structure files')
    parser.add_argument('--output', required=True, help='Path to output markdown file')
    parser.add_argument('--no-sections', action='store_true', help='Exclude sections from TOC')
    parser.add_argument('--no-figures', action='store_true', help='Exclude figures from TOC')
    parser.add_argument('--no-tables', action='store_true', help='Exclude tables from TOC')
    
    args = parser.parse_args()
    
    # Validate structure directory
    if not Path(args.structure_dir).exists():
        print(f"ERROR: Structure directory not found: {args.structure_dir}")
        return 1
    
    # Generate table of contents
    success = generate_complete_toc(
        args.structure_dir,
        args.output,
        include_sections=not args.no_sections,
        include_figures=not args.no_figures,
        include_tables=not args.no_tables
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
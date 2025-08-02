#!/usr/bin/env python3
"""
Convert YAML references to markdown format with proper anchors.

This tool converts the extracted references from YAML format to markdown
with anchor IDs that match the citation links used in the thesis sections.
"""

import argparse
import yaml
import re
from pathlib import Path
import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from progress_utils import print_progress, print_completion_summary, print_section_header


def generate_anchor_id(ref_id):
    """
    Generate anchor ID matching thesis citation format.
    
    Converts reference ID (e.g., "jennings-1977") to anchor format ("bib-jennings-1977")
    to match links like [Jennings [1977]](#bib-jennings-1977)
    
    Args:
        ref_id (str): Reference ID from YAML
        
    Returns:
        str: Anchor ID for markdown
    """
    return f"bib-{ref_id}"


def format_authors(author_string):
    """
    Format authors for citation display.
    
    Args:
        author_string (str): Author string from BibTeX format
        
    Returns:
        str: Formatted author string for display
    """
    if not author_string:
        return "Unknown Author"
    
    # Handle multiple authors separated by "and"
    authors = [author.strip() for author in author_string.split(' and ')]
    
    if len(authors) == 1:
        # Single author: "Last, First M." -> "Last, F. M."
        return authors[0]
    elif len(authors) == 2:
        # Two authors: "Author1 and Author2"
        return f"{authors[0]} and {authors[1]}"
    elif len(authors) > 2:
        # Multiple authors: "Author1 et al."
        return f"{authors[0]} et al."
    
    return author_string


def format_reference_citation(ref):
    """
    Format a single reference into academic citation style.
    
    Args:
        ref (dict): Reference data from YAML
        
    Returns:
        str: Formatted citation string
    """
    ref_type = ref.get('type', 'misc')
    author = format_authors(ref.get('author', 'Unknown Author'))
    title = ref.get('title', 'Untitled')
    year = ref.get('year', 'n.d.')
    
    # Remove quotes from title if present
    title = title.strip('"')
    
    if ref_type == 'article':
        journal = ref.get('journal', 'Unknown Journal')
        volume = ref.get('volume', '')
        number = ref.get('number', '')
        pages = ref.get('pages', '')
        
        citation = f"{author}. {title}. *{journal}*"
        
        if volume:
            citation += f", {volume}"
            if number:
                citation += f"({number})"
        
        if pages:
            citation += f":{pages}"
            
        citation += f", {year}."
        
    elif ref_type == 'book':
        publisher = ref.get('publisher', 'Unknown Publisher')
        address = ref.get('address', '')
        edition = ref.get('edition', '')
        
        citation = f"{author}. *{title}*"
        
        if edition:
            citation += f", {edition}"
            
        citation += f". {publisher}"
        
        if address:
            citation += f", {address}"
            
        citation += f", {year}."
        
    elif ref_type in ['inproceedings', 'incollection']:
        booktitle = ref.get('booktitle', 'Unknown Proceedings')
        publisher = ref.get('publisher', '')
        address = ref.get('address', '')
        pages = ref.get('pages', '')
        editor = ref.get('editor', '')
        
        citation = f"{author}. {title}. In "
        
        if editor:
            citation += f"{editor}, editors, "
            
        citation += f"*{booktitle}*"
        
        if pages:
            citation += f", pages {pages}"
            
        if publisher:
            citation += f". {publisher}"
            
        if address:
            citation += f", {address}"
            
        citation += f", {year}."
        
    elif ref_type in ['techreport', 'misc']:
        institution = ref.get('institution', ref.get('publisher', 'Unknown Institution'))
        number = ref.get('number', '')
        address = ref.get('address', '')
        
        citation = f"{author}. {title}."
        
        if number:
            citation += f" {number}."
            
        citation += f" {institution}"
        
        if address:
            citation += f", {address}"
            
        citation += f", {year}."
        
    elif ref_type in ['phdthesis', 'mastersthesis']:
        school = ref.get('school', ref.get('institution', 'Unknown University'))
        address = ref.get('address', '')
        
        thesis_type = "PhD thesis" if ref_type == 'phdthesis' else "Master's thesis"
        citation = f"{author}. {title}. {thesis_type}, {school}"
        
        if address:
            citation += f", {address}"
            
        citation += f", {year}."
        
    else:
        # Fallback for unknown types
        citation = f"{author}. {title}, {year}."
        
        # Add any additional info available
        for field in ['journal', 'publisher', 'institution', 'school']:
            value = ref.get(field)
            if value:
                citation = citation.rstrip('.') + f". {value}, {year}."
                break
    
    return citation


def convert_references_to_markdown(yaml_file, output_file):
    """
    Convert YAML references to markdown format.
    
    Args:
        yaml_file (str): Path to input YAML file
        output_file (str): Path to output markdown file
        
    Returns:
        bool: True if conversion succeeded, False otherwise
    """
    print_section_header("REFERENCES YAML TO MARKDOWN CONVERSION")
    print_progress(f"Converting {yaml_file} to {output_file}")
    
    # Load YAML data
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print_progress(f"- Error loading YAML file: {e}")
        return False
    
    references = data.get('references', [])
    if not references:
        print_progress("- No references found in YAML file")
        return False
    
    print_progress(f"Found {len(references)} references to convert")
    
    # Sort references by first author's last name, then by year
    def sort_key(ref):
        author = ref.get('author', 'zzz')
        # Extract first author's last name
        if ' and ' in author:
            author = author.split(' and ')[0]
        if ',' in author:
            last_name = author.split(',')[0].strip()
        else:
            # Assume "First Last" format
            parts = author.strip().split()
            last_name = parts[-1] if parts else 'zzz'
        
        year = ref.get('year', 9999)
        return (last_name.lower(), year)
    
    sorted_references = sorted(references, key=sort_key)
    print_progress("References sorted alphabetically by first author")
    
    # Generate markdown content
    markdown_lines = [
        "# References <a id=\"references\"></a>",
        "",
        "This bibliography contains all references cited in the thesis, formatted in academic citation style.",
        "",
    ]
    
    current_letter = None
    
    for ref in sorted_references:
        ref_id = ref.get('id', 'unknown')
        anchor_id = generate_anchor_id(ref_id)
        citation = format_reference_citation(ref)
        
        # Get first letter of first author's last name for grouping
        author = ref.get('author', 'Unknown')
        if ' and ' in author:
            author = author.split(' and ')[0]
        if ',' in author:
            first_letter = author.split(',')[0].strip()[0].upper()
        else:
            parts = author.strip().split()
            first_letter = parts[-1][0].upper() if parts else 'U'
        
        # Add letter header if starting new letter group
        if first_letter != current_letter:
            if current_letter is not None:
                markdown_lines.append("")  # Add space between letter groups
            markdown_lines.extend([
                f"## {first_letter}",
                ""
            ])
            current_letter = first_letter
        
        # Add the reference with anchor
        markdown_lines.extend([
            f"<a id=\"{anchor_id}\"></a>",
            f"{citation}",
            ""
        ])
    
    # Add metadata footer
    metadata = data.get('extraction_metadata', {})
    total_refs = metadata.get('total_references', len(references))
    pages_processed = metadata.get('pages_processed', 'unknown')
    
    markdown_lines.extend([
        "---",
        "",
        f"*Bibliography extracted from {pages_processed} pages containing {total_refs} references.*",
        f"*Converted from YAML to markdown format with anchor links for cross-referencing.*"
    ])
    
    # Write markdown file
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_lines))
        
        print_completion_summary(str(output_path), len(references), "references converted")
        return True
        
    except Exception as e:
        print_progress(f"- Error writing markdown file: {e}")
        return False


def generate_bibtex_file(yaml_file, output_file):
    """
    Generate a standalone BibTeX file from the YAML references.
    
    Args:
        yaml_file (str): Path to input YAML file
        output_file (str): Path to output .bib file
        
    Returns:
        bool: True if generation succeeded, False otherwise
    """
    print_progress(f"Generating BibTeX file: {output_file}")
    
    try:
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print_progress(f"- Error loading YAML file: {e}")
        return False
    
    # Extract BibTeX content if available
    bibtex_content = data.get('bibtex_content', '')
    
    if not bibtex_content:
        print_progress("- No BibTeX content found in YAML file")
        return False
    
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(bibtex_content)
        
        print_progress(f"+ BibTeX file saved: {output_path}")
        return True
        
    except Exception as e:
        print_progress(f"- Error writing BibTeX file: {e}")
        return False


def main():
    """Main function for references conversion."""
    parser = argparse.ArgumentParser(
        description='Convert YAML references to markdown format with proper anchors',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python convert_references_to_markdown.py --input structure/thesis_references.yaml --output markdown_output/references.md
  
This will convert the YAML references to markdown with anchor IDs that match thesis citation links.
You can also generate a standalone BibTeX file using --bibtex-output.
"""
    )
    
    parser.add_argument('--input', required=True, help='Path to input YAML references file')
    parser.add_argument('--output', required=True, help='Path to output markdown file')
    parser.add_argument('--bibtex-output', help='Optional path to output standalone BibTeX (.bib) file')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input).exists():
        print(f"ERROR: YAML file not found: {args.input}")
        return 1
    
    # Convert to markdown
    success = convert_references_to_markdown(args.input, args.output)
    
    # Generate BibTeX file if requested
    if args.bibtex_output and success:
        generate_bibtex_file(args.input, args.bibtex_output)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
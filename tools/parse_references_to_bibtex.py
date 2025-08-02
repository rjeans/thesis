#!/usr/bin/env python3
"""
Parse references from thesis PDF to extract and convert to BibTeX format.

This tool extracts academic references from the References section of a PDF thesis
document and converts them to properly formatted BibTeX entries.
"""

import argparse
import yaml
from pathlib import Path
import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from toc_parsing_utils import (
    process_pages_batch, save_diagnostics, save_yaml_output,
    create_standard_argument_parser, validate_and_setup, run_standard_toc_parser
)
from prompt_utils import create_toc_parsing_prompt
from progress_utils import print_progress, print_completion_summary, print_section_header


def create_references_yaml_structure():
    """Create YAML structure template for references parsing."""
    return """references:
- id: "author-year"  # BibTeX key (lowercase, hyphenated)
  type: "article|book|inproceedings|incollection|techreport|phdthesis|mastersthesis|misc"
  author: "Last, First M. and Other, Second P."  # Author names in BibTeX format
  title: "Complete Title of the Work"
  journal: "Journal Name"  # For articles
  booktitle: "Book or Conference Title"  # For inproceedings/incollection
  publisher: "Publisher Name"  # For books/reports
  institution: "Institution Name"  # For techreports/theses
  school: "University Name"  # For theses
  year: 1992
  volume: "15"  # String format for special volumes
  number: "3"  # Issue number
  pages: "123-456"  # Page range
  edition: "2nd"  # For books
  address: "City, Country"  # Publication location
  note: "Additional notes"  # Optional notes
  doi: "10.1000/journal.1992.123"  # Digital Object Identifier
  url: "https://example.com/paper"  # Web URL if available
  isbn: "978-0-123456-78-9"  # For books
  issn: "1234-5678"  # For journals
  original_text: "Original reference text as it appears in the PDF"

extraction_metadata:
  pages_processed: 5
  extraction_date: "2024-01-01"
  total_references: 0
  tool_version: "bibtex_converter_v1"
"""




def process_references_data(all_pages_data):
    """
    Process collected references data from multiple pages.
    
    Args:
        all_pages_data (list): List of page data dictionaries from GPT-4 Vision
        
    Returns:
        dict: Final structure with consolidated references
    """
    print_progress("Consolidating references from all pages...")
    
    all_references = []
    
    # Collect all references from all pages
    for page_idx, page_data in enumerate(all_pages_data):
        page_references = page_data.get('references', [])
        if page_references:
            print_progress(f"  Page {page_idx + 1}: Found {len(page_references)} references")
            all_references.extend(page_references)
        else:
            print_progress(f"  Page {page_idx + 1}: No references found")
    
    # Remove duplicates based on ID
    unique_references = []
    seen_ids = set()
    
    for ref in all_references:
        ref_id = ref.get('id', 'unknown')
        if ref_id not in seen_ids:
            unique_references.append(ref)
            seen_ids.add(ref_id)
        else:
            print_progress(f"  [DUPLICATE] Removed duplicate reference: {ref_id}")
    
    # Sort references by year, then by first author
    def sort_key(ref):
        year = ref.get('year', 9999)
        author = ref.get('author', 'zzz').split(' and ')[0].split(',')[0].lower()
        return (year, author)
    
    unique_references.sort(key=sort_key)
    
    # Generate BibTeX content
    bibtex_entries = []
    for ref in unique_references:
        bibtex_entry = generate_bibtex_entry(ref)
        if bibtex_entry:
            bibtex_entries.append(bibtex_entry)
    
    final_structure = {
        'references': unique_references,
        'bibtex_content': '\n\n'.join(bibtex_entries),
        'extraction_metadata': {
            'pages_processed': len(all_pages_data),
            'total_references': len(unique_references),
            'extraction_date': '2024-01-01',
            'tool_version': 'bibtex_converter_v1'
        }
    }
    
    print_progress(f"Final reference count: {len(unique_references)} unique references")
    return final_structure


def generate_bibtex_entry(ref):
    """
    Generate a BibTeX entry string from reference data.
    
    Args:
        ref (dict): Reference data dictionary
        
    Returns:
        str: Formatted BibTeX entry
    """
    ref_type = ref.get('type', 'misc')
    ref_id = ref.get('id', 'unknown')
    
    entry_lines = [f"@{ref_type}{{{ref_id},"]
    
    # Required and optional fields by type
    field_mapping = {
        'author': 'author',
        'title': 'title', 
        'journal': 'journal',
        'booktitle': 'booktitle',
        'publisher': 'publisher',
        'institution': 'institution',
        'school': 'school',
        'year': 'year',
        'volume': 'volume',
        'number': 'number',
        'pages': 'pages',
        'edition': 'edition',
        'address': 'address',
        'note': 'note',
        'doi': 'doi',
        'url': 'url',
        'isbn': 'isbn',
        'issn': 'issn'
    }
    
    # Add fields that exist in the reference
    for yaml_field, bibtex_field in field_mapping.items():
        value = ref.get(yaml_field)
        if value and str(value).strip():
            if yaml_field in ['title', 'journal', 'booktitle', 'publisher', 'institution', 'school', 'note', 'address']:
                # String fields need quotes
                entry_lines.append(f"  {bibtex_field} = \"{value}\",")
            else:
                # Numeric or special fields
                entry_lines.append(f"  {bibtex_field} = {{{value}}},")
    
    entry_lines.append("}")
    
    return '\n'.join(entry_lines)


def main():
    """Main function for references parsing."""
    
    def yaml_structure_func():
        return create_references_yaml_structure()
    
    def content_processor(all_pages_data):
        return process_references_data(all_pages_data)
    
    success = run_standard_toc_parser(
        content_type="references",
        yaml_structure_func=yaml_structure_func,
        content_processor=content_processor,
        description='Parse academic references and convert to BibTeX format',
        example_usage='This will extract references from pages 195-199 and save them to structure/thesis_references.yaml with BibTeX conversion',
        default_pages="195 199"
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
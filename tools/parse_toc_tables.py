#!/usr/bin/env python3
"""
Parse tables list from thesis PDF to extract table catalog.

This tool extracts table information including titles, page numbers,
and chapter associations from the tables list pages of a PDF thesis.
"""

import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from toc_parsing_utils import run_standard_toc_parser
from progress_utils import print_progress


def create_tables_yaml_structure():
    """Create YAML structure template for tables parsing."""
    return """tables:
- table_number: "4.1"
  title: "Table title from the tables list"
  page: 67
  chapter: 4
- table_number: "5.2"
  title: "Another table title"
  page: 89
  chapter: 5
extraction_metadata:
  pages_processed: 1
  extraction_date: "2024-01-01"
  tool_version: "simplified"
"""


def process_tables_data(all_pages_data):
    """
    Process collected tables data from all pages.
    
    Args:
        all_pages_data: List of page data dictionaries from GPT-4 Vision
        
    Returns:
        Final structure dictionary with tables list
    """
    all_tables = []
    
    # Collect all tables from all pages
    for page_data in all_pages_data:
        if page_data and 'tables' in page_data:
            page_tables = page_data['tables']
            all_tables.extend(page_tables)
    
    # Always return a structure (even if empty)
    if all_tables:
        print_progress(f"+ Successfully collected {len(all_tables)} tables total")
    else:
        print_progress("+ No tables found, but created empty structure")
        
    return {'tables': all_tables}


def main():
    """Main function for TOC tables parsing."""
    success = run_standard_toc_parser(
        content_type="tables",
        yaml_structure_func=create_tables_yaml_structure,
        content_processor=process_tables_data,
        description='Parse tables list to extract table catalog',
        example_usage='This will extract the table catalog from page 17 and save it to structure/thesis_tables.yaml',
        default_pages="17 17"
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
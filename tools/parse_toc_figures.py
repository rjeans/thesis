#!/usr/bin/env python3
"""
Parse figures list from thesis PDF to extract figure catalog.

This tool extracts figure information including titles, page numbers,
and chapter associations from the figures list pages of a PDF thesis.
"""

import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from toc_parsing_utils import run_standard_toc_parser
from progress_utils import print_progress


def create_figures_yaml_structure():
    """Create YAML structure template for figures parsing."""
    return """figures:
- figure_number: "2.1"
  title: "Figure title from the figures list"
  page: 45
  chapter: 2
- figure_number: "3.5.6"
  title: "Complex numbered figure title"
  page: 78
  chapter: 3
extraction_metadata:
  pages_processed: 3
  extraction_date: "2024-01-01"
  tool_version: "simplified"
"""


def process_figures_data(all_pages_data):
    """
    Process collected figures data from all pages.
    
    Args:
        all_pages_data: List of page data dictionaries from GPT-4 Vision
        
    Returns:
        Final structure dictionary with figures list
    """
    all_figures = []
    
    # Collect all figures from all pages
    for page_data in all_pages_data:
        if page_data and 'figures' in page_data:
            page_figures = page_data['figures']
            all_figures.extend(page_figures)
    
    if not all_figures:
        print_progress("- No figures were extracted from any page.")
        # Return empty structure instead of failing
        return {'figures': []}
    
    print_progress(f"+ Successfully collected {len(all_figures)} figures total")
    return {'figures': all_figures}


def main():
    """Main function for TOC figures parsing."""
    success = run_standard_toc_parser(
        content_type="figures",
        yaml_structure_func=create_figures_yaml_structure,
        content_processor=process_figures_data,
        description='Parse figures list to extract figure catalog',
        example_usage='This will extract the figure catalog from pages 13-15 and save it to structure/thesis_figures.yaml',
        default_pages="13 15"
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
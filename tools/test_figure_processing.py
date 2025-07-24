#!/usr/bin/env python3
"""
Test figure processing and anchor generation on specific pages.

This script helps test figure caption processing, anchor generation, and 
GitBook/Pandoc compatibility by processing pages known to contain figures.

Usage:
    python test_figure_processing.py thesis.pdf --test-figures-list
    python test_figure_processing.py thesis.pdf --test-chapter-figures 3
    python test_figure_processing.py thesis.pdf --test-page 62
    python test_figure_processing.py thesis.pdf --test-all-figures

Features:
- Process figures list (pages 13-16) with TOC content type and anchor generation
- Process specific chapter pages containing figures
- Test individual pages with figures for detailed validation
- Validate anchor generation format for GitBook/Pandoc compatibility
- Generate test reports showing anchor usage

Requires:
- YAML structure files from TOC parsing
- OpenAI API key in OPENAI_API_KEY environment variable
"""

import os
import argparse
import yaml
from pathlib import Path
import re

# Import our tools
from process_page_range import process_page_range_to_markdown
from progress_utils import print_progress, print_section_header, print_completion_summary


def load_figure_metadata(structure_dir):
    """
    Load figure metadata from YAML structure files.
    
    Args:
        structure_dir (str): Directory containing YAML structure files
        
    Returns:
        dict: Figure metadata or None if not found
    """
    figures_file = Path(structure_dir) / "thesis_figures.yaml"
    
    if not figures_file.exists():
        print_progress(f"- Figures metadata not found: {figures_file}")
        return None
    
    try:
        with open(figures_file, 'r', encoding='utf-8') as f:
            figures_data = yaml.safe_load(f)
        print_progress(f"+ Loaded {len(figures_data.get('figures', []))} figures from metadata")
        return figures_data
    except Exception as e:
        print_progress(f"- Failed to load figures metadata: {e}")
        return None


def analyze_anchors_in_markdown(markdown_path):
    """
    Analyze anchor generation in a markdown file.
    
    Args:
        markdown_path (str): Path to markdown file
        
    Returns:
        dict: Analysis results
    """
    if not Path(markdown_path).exists():
        return {"error": "File not found"}
    
    try:
        with open(markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {"error": f"Failed to read file: {e}"}
    
    # Find different types of anchors
    header_anchors = re.findall(r'#+\s+.*?\{#([^}]+)\}', content)
    figure_anchors = re.findall(r'\{#(figure-[^}]+)\}', content)
    table_anchors = re.findall(r'\{#(table-[^}]+)\}', content)
    equation_anchors = re.findall(r'\{#(equation-[^}]+)\}', content)
    
    # Count markdown elements
    headers = re.findall(r'^#+\s+', content, re.MULTILINE)
    figures = re.findall(r'!\[.*?\]\(.*?\)', content)
    tables = re.findall(r'^\|.*\|', content, re.MULTILINE)
    equations = re.findall(r'\$\$.*?\$\$', content, re.DOTALL)
    
    return {
        "anchors": {
            "headers": header_anchors,
            "figures": figure_anchors, 
            "tables": table_anchors,
            "equations": equation_anchors,
            "total": len(header_anchors) + len(figure_anchors) + len(table_anchors) + len(equation_anchors)
        },
        "elements": {
            "headers": len(headers),
            "figures": len(figures),
            "tables": len(tables),
            "equations": len(equations)
        },
        "content_length": len(content),
        "line_count": len(content.split('\n'))
    }


def test_figures_list_processing(pdf_path, structure_dir, output_dir):
    """
    Test processing of the figures list (TOC) pages.
    
    Args:
        pdf_path (str): Path to source PDF
        structure_dir (str): Structure directory
        output_dir (str): Output directory
        
    Returns:
        bool: Success status
    """
    print_section_header("TESTING FIGURES LIST PROCESSING")
    
    output_path = Path(output_dir) / "test_figures_list.md"
    
    # Process figures list pages (13-16) with TOC content type
    success = process_page_range_to_markdown(
        pdf_path, 13, 16, str(output_path),
        content_type="toc",
        structure_dir=structure_dir,
        chapter_name="Figures List"
    )
    
    if success:
        # Analyze the output
        analysis = analyze_anchors_in_markdown(str(output_path))
        
        print_progress("\nFIGURES LIST ANALYSIS:")
        print_progress(f"  Output file: {output_path}")
        print_progress(f"  Content length: {analysis['content_length']} characters")
        print_progress(f"  Lines: {analysis['line_count']}")
        print_progress(f"  Total anchors generated: {analysis['anchors']['total']}")
        print_progress(f"    - Header anchors: {len(analysis['anchors']['headers'])}")
        print_progress(f"    - Figure anchors: {len(analysis['anchors']['figures'])}")
        print_progress(f"    - Table anchors: {len(analysis['anchors']['tables'])}")
        print_progress(f"    - Equation anchors: {len(analysis['anchors']['equations'])}")
        
        if analysis['anchors']['figures']:
            print_progress(f"  Figure anchors found: {analysis['anchors']['figures'][:5]}...")
        
        return True
    else:
        print_progress("- Failed to process figures list")
        return False


def test_chapter_figures(pdf_path, chapter_num, structure_dir, output_dir):
    """
    Test processing of pages from a specific chapter containing figures.
    
    Args:
        pdf_path (str): Path to source PDF
        chapter_num (int): Chapter number to test
        structure_dir (str): Structure directory
        output_dir (str): Output directory
        
    Returns:
        bool: Success status
    """
    print_section_header(f"TESTING CHAPTER {chapter_num} FIGURE PROCESSING")
    
    # Load chapter structure to find page ranges
    contents_file = Path(structure_dir) / "thesis_contents.yaml"
    if not contents_file.exists():
        print_progress(f"- Contents structure not found: {contents_file}")
        return False
    
    try:
        with open(contents_file, 'r', encoding='utf-8') as f:
            contents_data = yaml.safe_load(f)
    except Exception as e:
        print_progress(f"- Failed to load contents: {e}")
        return False
    
    # Find the specified chapter
    chapter_info = None
    for section in contents_data.get('sections', []):
        if section.get('type') == 'chapter' and section.get('chapter_number') == chapter_num:
            chapter_info = section
            break
    
    if not chapter_info:
        print_progress(f"- Chapter {chapter_num} not found in structure")
        return False
    
    start_page = chapter_info['page_start']
    end_page = chapter_info.get('page_end', start_page + 10)  # Default range if not specified
    
    # Process a subset of the chapter (first 5 pages to keep manageable)
    test_end_page = min(end_page, start_page + 4)
    
    output_path = Path(output_dir) / f"test_chapter_{chapter_num}_figures.md"
    
    print_progress(f"Processing Chapter {chapter_num} pages {start_page}-{test_end_page}")
    
    success = process_page_range_to_markdown(
        pdf_path, start_page, test_end_page, str(output_path),
        content_type="chapter",
        structure_dir=structure_dir,
        chapter_name=f"Chapter {chapter_num}"
    )
    
    if success:
        # Analyze the output
        analysis = analyze_anchors_in_markdown(str(output_path))
        
        print_progress(f"\nCHAPTER {chapter_num} ANALYSIS:")
        print_progress(f"  Output file: {output_path}")
        print_progress(f"  Pages processed: {start_page}-{test_end_page}")
        print_progress(f"  Content length: {analysis['content_length']} characters")
        print_progress(f"  Total anchors generated: {analysis['anchors']['total']}")
        print_progress(f"  Elements found:")
        print_progress(f"    - Headers: {analysis['elements']['headers']}")
        print_progress(f"    - Figures: {analysis['elements']['figures']}")
        print_progress(f"    - Tables: {analysis['elements']['tables']}")
        print_progress(f"    - Equations: {analysis['elements']['equations']}")
        
        return True
    else:
        print_progress(f"- Failed to process Chapter {chapter_num} figures")
        return False


def test_single_page(pdf_path, page_num, structure_dir, output_dir):
    """
    Test processing of a single page for detailed analysis.
    
    Args:
        pdf_path (str): Path to source PDF
        page_num (int): Page number to test
        structure_dir (str): Structure directory
        output_dir (str): Output directory
        
    Returns:
        bool: Success status
    """
    print_section_header(f"TESTING SINGLE PAGE {page_num} PROCESSING")
    
    output_path = Path(output_dir) / f"test_page_{page_num}.md"
    
    success = process_page_range_to_markdown(
        pdf_path, page_num, page_num, str(output_path),
        content_type="chapter",  # Assume chapter content for single page tests
        structure_dir=structure_dir,
        chapter_name=f"Page {page_num} Test"
    )
    
    if success:
        # Detailed analysis for single page
        analysis = analyze_anchors_in_markdown(str(output_path))
        
        print_progress(f"\nSINGLE PAGE {page_num} DETAILED ANALYSIS:")
        print_progress(f"  Output file: {output_path}")
        print_progress(f"  Content length: {analysis['content_length']} characters")
        print_progress(f"  Lines: {analysis['line_count']}")
        
        print_progress(f"\nANCHOR ANALYSIS:")
        for anchor_type, anchors in analysis['anchors'].items():
            if anchors and anchor_type != 'total':
                print_progress(f"  {anchor_type.title()} anchors ({len(anchors)}):")
                for anchor in anchors:
                    print_progress(f"    - {anchor}")
        
        print_progress(f"\nELEMENT COUNTS:")
        for element_type, count in analysis['elements'].items():
            print_progress(f"  {element_type.title()}: {count}")
        
        # Show first few lines of content for validation
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:10]
            print_progress(f"\nFIRST 10 LINES OF OUTPUT:")
            for i, line in enumerate(lines, 1):
                print_progress(f"  {i:2d}: {line.rstrip()}")
        except Exception as e:
            print_progress(f"- Could not preview content: {e}")
        
        return True
    else:
        print_progress(f"- Failed to process page {page_num}")
        return False


def main():
    """Main function for figure processing tests."""
    parser = argparse.ArgumentParser(
        description='Test figure processing and anchor generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test figures list processing with TOC content type
  python test_figure_processing.py thesis.pdf --test-figures-list

  # Test figure processing in Chapter 3
  python test_figure_processing.py thesis.pdf --test-chapter-figures 3

  # Test detailed processing of page 62
  python test_figure_processing.py thesis.pdf --test-page 62

  # Test multiple scenarios
  python test_figure_processing.py thesis.pdf --test-figures-list --test-chapter-figures 2

  # Custom output directory
  python test_figure_processing.py thesis.pdf --test-figures-list \\
      --output-dir custom_test_output/
        """
    )
    
    parser.add_argument('pdf_path', help='Path to source PDF file')
    
    # Test options
    parser.add_argument('--test-figures-list', action='store_true',
                       help='Test processing of figures list (pages 13-16)')
    parser.add_argument('--test-chapter-figures', type=int, metavar='N',
                       help='Test figure processing in Chapter N')
    parser.add_argument('--test-page', type=int, metavar='N',
                       help='Test detailed processing of page N')
    
    # Configuration options
    parser.add_argument('--structure-dir', required=True,
                       help='Directory containing YAML structure files')
    parser.add_argument('--output-dir', required=True,
                       help='Output directory for test files')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.pdf_path).exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        return 1
    
    if not any([args.test_figures_list, args.test_chapter_figures, args.test_page]):
        print("ERROR: No test specified. Use --test-figures-list, --test-chapter-figures N, or --test-page N")
        return 1
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Display test information
    print_section_header("FIGURE PROCESSING AND ANCHOR GENERATION TESTS")
    print(f"PDF: {args.pdf_path}")
    print(f"Structure directory: {args.structure_dir}")
    print(f"Output directory: {args.output_dir}")
    print("=" * 60)
    
    # Run requested tests
    total_tests = 0
    successful_tests = 0
    
    if args.test_figures_list:
        total_tests += 1
        if test_figures_list_processing(args.pdf_path, args.structure_dir, args.output_dir):
            successful_tests += 1
    
    if args.test_chapter_figures:
        total_tests += 1
        if test_chapter_figures(args.pdf_path, args.test_chapter_figures, 
                               args.structure_dir, args.output_dir):
            successful_tests += 1
    
    if args.test_page:
        total_tests += 1
        if test_single_page(args.pdf_path, args.test_page, 
                           args.structure_dir, args.output_dir):
            successful_tests += 1
    
    # Final summary
    print_section_header("TEST RESULTS SUMMARY")
    print_completion_summary(args.output_dir, successful_tests, 
                           f"figure processing tests completed ({successful_tests}/{total_tests} successful)")
    
    if successful_tests == total_tests:
        print_progress("✅ All tests passed!")
        return 0
    else:
        print_progress(f"⚠️  {total_tests - successful_tests} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
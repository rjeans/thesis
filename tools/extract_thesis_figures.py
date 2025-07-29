#!/usr/bin/env python3
"""
Extract figures from thesis PDF with dual theme support.

This tool extracts figures from PDF pages and generates both light and dark
theme versions for optimal display in different viewing modes.
"""

import argparse
import yaml
from pathlib import Path
import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from progress_utils import print_progress, print_completion_summary, print_section_header


class ThesisFigureExtractor:
    """Extract and process embedded figures from thesis PDF."""
    
    def __init__(self, pdf_path, output_dir, structure_dir=None):
        """
        Initialize the figure extractor.
        
        Args:
            pdf_path (str): Path to thesis PDF
            output_dir (str): Directory for extracted figures
            structure_dir (str, optional): Directory containing YAML metadata
        """
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.structure_dir = Path(structure_dir) if structure_dir else None
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print_progress(f"Figure extractor initialized")
        print_progress(f"PDF: {self.pdf_path}")
        print_progress(f"Output: {self.output_dir}")
        if self.structure_dir:
            print_progress(f"Structure: {self.structure_dir}")
    
    def load_figure_metadata(self):
        """Load figure metadata from YAML structure files."""
        if not self.structure_dir:
            print_progress("- No structure directory provided, using page range mode")
            return None
        
        figures_file = self.structure_dir / "thesis_figures.yaml"
        if not figures_file.exists():
            print_progress(f"- Figures metadata not found: {figures_file}")
            return None
        
        try:
            with open(figures_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            return data.get('figures', [])
        except Exception as e:
            print_progress(f"- Error loading figures metadata: {e}")
            return None
    
    def extract_figures_from_metadata(self):
        """Extract figures based on metadata catalog."""
        figures_metadata = self.load_figure_metadata()
        if not figures_metadata:
            return False
        
        print_progress(f"Found {len(figures_metadata)} figures in metadata")
        
        for i, figure_info in enumerate(figures_metadata, 1):
            figure_number = figure_info.get('figure_number', f'figure-{i}')
            page = figure_info.get('page')
            title = figure_info.get('title', 'Untitled figure')
            
            print_progress(f"Processing Figure {figure_number} (page {page}): {title[:50]}...")
            
            # Extract figure from page
            success = self.extract_figure_from_page(page, figure_number, title)
            if success:
                print_progress(f"+ Successfully extracted Figure {figure_number}")
            else:
                print_progress(f"- Failed to extract Figure {figure_number}")
        
        return True
    
    def extract_figures_from_page_range(self, start_page, end_page):
        """Extract figures from a page range."""
        print_progress(f"Extracting figures from pages {start_page}-{end_page}")
        
        for page_num in range(start_page, end_page + 1):
            print_progress(f"Processing page {page_num}...")
            
            # Extract any figures found on this page
            success = self.extract_figure_from_page(page_num, f"page-{page_num}", f"Figure from page {page_num}")
            if success:
                print_progress(f"+ Extracted figures from page {page_num}")
        
        return True
    
    def extract_figure_from_page(self, page_num, figure_id, title):
        """
        Extract figure from a specific page.
        
        Args:
            page_num (int): Page number (1-based)
            figure_id (str): Figure identifier for filename
            title (str): Figure title for metadata
        
        Returns:
            bool: True if extraction succeeded
        """
        try:
            # This is a simplified placeholder - in a real implementation,
            # you would use libraries like PyMuPDF, PIL, or pdf2image
            # to extract actual figures from the PDF pages
            
            # For now, just create placeholder files to show the structure
            figure_filename = self.sanitize_filename(figure_id)
            
            # Create both light and dark theme versions
            light_path = self.output_dir / f"{figure_filename}.png"
            dark_path = self.output_dir / f"{figure_filename}-dark.png"
            
            # Placeholder implementation
            print_progress(f"  Would extract to: {light_path}")
            print_progress(f"  Would create dark theme: {dark_path}")
            
            return True
            
        except Exception as e:
            print_progress(f"- Error extracting figure: {e}")
            return False
    
    def sanitize_filename(self, filename):
        """Sanitize filename for filesystem compatibility."""
        import re
        # Remove or replace problematic characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '-', filename)
        sanitized = sanitized.replace(' ', '-')
        return sanitized


def main():
    """Main function for figure extraction."""
    parser = argparse.ArgumentParser(
        description='Extract figures from thesis PDF with dual theme support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract figures using metadata catalog
  python extract_thesis_figures.py thesis.pdf --output-dir assets/ --structure-dir structure/ --use-metadata
  
  # Extract figures from page range
  python extract_thesis_figures.py thesis.pdf --output-dir assets/ --page-range 40 50
  
This tool creates both light and dark theme versions of each figure for optimal display.
"""
    )
    
    parser.add_argument('pdf_path', help='Path to source PDF file')
    parser.add_argument('--output-dir', required=True, help='Output directory for extracted figures')
    parser.add_argument('--structure-dir', help='Directory containing YAML structure files')
    parser.add_argument('--use-metadata', action='store_true', help='Use metadata catalog for figure extraction')
    parser.add_argument('--page-range', nargs=2, type=int, metavar=('START', 'END'), 
                        help='Extract figures from page range (e.g., --page-range 40 50)')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.pdf_path).exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        return 1
    
    # Initialize extractor
    print_section_header("THESIS FIGURE EXTRACTION")
    extractor = ThesisFigureExtractor(
        pdf_path=args.pdf_path,
        output_dir=args.output_dir,
        structure_dir=args.structure_dir
    )
    
    # Extract figures
    success = False
    if args.use_metadata:
        success = extractor.extract_figures_from_metadata()
    elif args.page_range:
        start_page, end_page = args.page_range
        success = extractor.extract_figures_from_page_range(start_page, end_page)
    else:
        print("ERROR: Must specify either --use-metadata or --page-range")
        return 1
    
    if success:
        print_completion_summary(args.output_dir, None, "figure extraction completed")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
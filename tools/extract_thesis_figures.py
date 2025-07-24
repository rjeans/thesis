#!/usr/bin/env python3
"""
Extract embedded figures from PhD thesis PDF with dual theme support.

This script extracts high-resolution embedded images from the PDF and generates
both light and dark theme versions with transparent backgrounds, optimized
for black-and-white line art and technical diagrams.

Usage:
    python extract_thesis_figures.py thesis.pdf --output-dir assets/ --structure-dir structure/
    python extract_thesis_figures.py thesis.pdf --output-dir assets/ --page-range 41 45
    python extract_thesis_figures.py thesis.pdf --output-dir assets/ --all-figures

Features:
- Direct embedded image extraction at original resolution
- Dual theme generation (light/dark) with transparency
- Integration with YAML figure metadata for intelligent naming
- Quality optimization for line art and technical diagrams
- Batch processing with progress tracking
"""

import os
import sys
import argparse
from pathlib import Path
import tempfile
import io
import yaml
from PIL import Image, ImageOps
import numpy as np

# Import our utilities
from progress_utils import print_progress, print_section_header, print_completion_summary
import yaml

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF (fitz) is required for embedded image extraction")
    print("Install with: pip install PyMuPDF")
    sys.exit(1)


class ThesisFigureExtractor:
    """Extract and process embedded figures from thesis PDF."""
    
    def __init__(self, pdf_path, output_dir, structure_dir=None):
        """Initialize the figure extractor.
        
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
        
        # Load figure metadata if available
        self.figure_metadata = {}
        if self.structure_dir:
            self.load_figure_metadata()
        
        # Open PDF document
        try: 
            self.doc = fitz.open(str(self.pdf_path))
            print_progress(f"+ Opened PDF: {len(self.doc)} pages")
        except Exception as e:
            raise Exception(f"Failed to open PDF: {e}")
    
    def load_figure_metadata(self):
        """Load figure metadata from YAML structure files."""
        figures_file = self.structure_dir / "thesis_figures.yaml"
        
        if figures_file.exists():
            try:
                with open(figures_file, 'r', encoding='utf-8') as f:
                    figures_data = yaml.safe_load(f)
                if figures_data and 'figures' in figures_data:
                    # Create lookup by page number
                    for fig in figures_data['figures']:
                        page_num = fig.get('page')
                        if page_num:
                            # Ensure page_num is an integer
                            try:
                                page_num = int(page_num)
                                if page_num not in self.figure_metadata:
                                    self.figure_metadata[page_num] = []
                                self.figure_metadata[page_num].append(fig)
                            except (ValueError, TypeError):
                                print_progress(f"- Skipping invalid page number: {page_num}")
                                continue
                    
                    print_progress(f"+ Loaded metadata for {len(figures_data['figures'])} figures")
                else:
                    print_progress("- No figure data found in YAML file")
            except Exception as e:
                print_progress(f"- Failed to load figure metadata: {e}")
        else:
            print_progress("- No figure metadata file found")
    
    def get_figure_name(self, page_num, img_index=0):
        """Generate figure name based on metadata or page number.
        
        Args:
            page_num (int): PDF page number (1-based)
            img_index (int): Image index on page
            
        Returns:
            str: Figure name (e.g., "figure-2-5")
        """
        # Try to get name from metadata
        if page_num in self.figure_metadata:
            figures_on_page = self.figure_metadata[page_num]
            if img_index < len(figures_on_page):
                fig_data = figures_on_page[img_index]
                fig_number = fig_data.get('figure_number', '')
                if fig_number:
                    # Convert "2.5" to "figure-2-5"
                    return f"figure-{fig_number.replace('.', '-')}"
        
        # Fallback to page-based naming
        if img_index == 0:
            return f"figure-page-{page_num}"
        else:
            return f"figure-page-{page_num}-{img_index + 1}"
    
    def process_line_art_image(self, pix, figure_name):
        """Process embedded image for line art optimization - light version only.
        
        Args:
            pix (fitz.Pixmap): Image data from PDF
            figure_name (str): Base name for figure files
            
        Returns:
            str: light_theme_path or None if failed
        """
        try:
            # Convert fitz pixmap to PIL Image
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            
            # Ensure grayscale for line art processing
            if img.mode != 'L':
                img = img.convert('L')
            
            print_progress(f"  Processing {img.size[0]}x{img.size[1]} grayscale image")
            
            # Convert to numpy array for processing
            img_array = np.array(img)
            
            # Analyze image characteristics
            unique_values = len(np.unique(img_array))
            white_pixels = np.sum(img_array > 240)  # Near-white pixels
            total_pixels = img_array.size
            white_ratio = white_pixels / total_pixels
            
            print_progress(f"  Image analysis: {unique_values} unique values, {white_ratio:.1%} white pixels")
            
            # Optimize for line art (clean up gray values)
            # Threshold to ensure pure black/white for better processing
            threshold = 128
            if white_ratio > 0.8:  # Mostly white background (typical for line art)
                # More aggressive thresholding for line art
                threshold = 200
            
            # Create binary mask
            binary_mask = img_array > threshold
            
            # Light theme: black lines on transparent background
            light_img = Image.new('RGBA', img.size, (0, 0, 0, 0))  # Transparent
            light_array = np.array(light_img)
            
            # Set non-white pixels to black, white pixels to transparent
            light_array[~binary_mask] = [0, 0, 0, 255]      # Black lines
            light_array[binary_mask] = [255, 255, 255, 0]    # Transparent background
            
            light_img = Image.fromarray(light_array, 'RGBA')
            
            # Save light version only
            light_path = self.output_dir / f"{figure_name}.png"
            
            # Optimize PNG compression while maintaining quality
            light_img.save(str(light_path), 'PNG', optimize=True, compress_level=6)
            
            print_progress(f"  + Saved: {light_path.name} ({light_img.size[0]}x{light_img.size[1]})")
            print_progress(f"  + Note: Dark version will be generated by auto_crop_figures.py")
            
            return str(light_path)
            
        except Exception as e:
            print_progress(f"  - Failed to process image: {e}")
            return None
    
    def extract_page_figures(self, page_num):
        """Extract full page images for pages containing figures.
        
        Since embedded images are full pages, extract the page image and create
        separate files for each figure that should be on this page according to metadata.
        
        Args:
            page_num (int): Page number (1-based)
            
        Returns:
            list: List of (light_path, dark_path) tuples for extracted page images
        """
        page = self.doc[page_num - 1]  # fitz uses 0-based indexing
        image_list = page.get_images()
        
        extracted_figures = []
        
        if not image_list:
            print_progress(f"  No embedded images found on page {page_num}")
            return extracted_figures
        
        # Get expected figures on this page from metadata
        expected_figures = self.figure_metadata.get(page_num, [])
        print_progress(f"  Found {len(image_list)} embedded image(s)")
        print_progress(f"  Expected figures on page: {len(expected_figures)}")
        
        for fig in expected_figures:
            fig_num = fig.get('figure_number', '?')
            fig_title = fig.get('title', 'No title')
            print_progress(f"    - Figure {fig_num}: {fig_title}")
        
        # Extract the page image (should be the first/only image for full page images)
        if image_list:
            try:
                # Extract the page image data
                xref = image_list[0][0]  # Use first image (should be the full page)
                pix = fitz.Pixmap(self.doc, xref)
                
                # Skip if not grayscale (unexpected for line art)
                if pix.colorspace and pix.colorspace.name != "DeviceGray":
                    print_progress(f"  - Skipping non-grayscale page image")
                    pix = None
                    return extracted_figures
                
                print_progress(f"  Processing full page image:")
                print_progress(f"    Size: {pix.width}x{pix.height}")
                print_progress(f"    Colorspace: {pix.colorspace.name if pix.colorspace else 'Unknown'}")
                
                # Create page images for each expected figure on this page
                if expected_figures:
                    # Create separate files for each figure that should be on this page
                    for fig_index, fig_data in enumerate(expected_figures):
                        fig_number = fig_data.get('figure_number', '')
                        if fig_number:
                            figure_name = f"figure-{fig_number.replace('.', '-')}"
                        else:
                            figure_name = f"figure-page-{page_num}-{fig_index + 1}"
                        
                        # Process the same page image with different figure names
                        light_path = self.process_line_art_image(pix, figure_name)
                        
                        if light_path:
                            extracted_figures.append(light_path)
                else:
                    # No metadata, create single page image
                    figure_name = f"figure-page-{page_num}"
                    light_path = self.process_line_art_image(pix, figure_name)
                    
                    if light_path:
                        extracted_figures.append(light_path)
                
                # Clean up
                pix = None
                
            except Exception as e:
                print_progress(f"  - Failed to extract page image: {e}")
        
        return extracted_figures
    
    def extract_figures_by_page_range(self, start_page, end_page):
        """Extract figures from a range of pages.
        
        Args:
            start_page (int): Starting page number (1-based)
            end_page (int): Ending page number (1-based, inclusive)
            
        Returns:
            list: List of light_path strings for all extracted figures
        """
        print_section_header(f"EXTRACTING FIGURES FROM PAGES {start_page}-{end_page}")
        
        all_figures = []
        pages_with_figures = 0
        
        for page_num in range(start_page, end_page + 1):
            if page_num > len(self.doc):
                print_progress(f"- Page {page_num} exceeds document length ({len(self.doc)})")
                continue
            
            print_progress(f"\n=== PAGE {page_num} ===")
            
            page_figures = self.extract_page_figures(page_num)
            
            if page_figures:
                all_figures.extend(page_figures)
                pages_with_figures += 1
                print_progress(f"+ Extracted {len(page_figures)} figure(s) from page {page_num}")
            else:
                print_progress(f"  No figures extracted from page {page_num}")
        
        print_section_header("EXTRACTION SUMMARY")
        print_progress(f"Pages processed: {end_page - start_page + 1}")
        print_progress(f"Pages with figures: {pages_with_figures}")
        print_progress(f"Total figures extracted: {len(all_figures)}")
        print_progress(f"Output directory: {self.output_dir}")
        
        return all_figures
    
    def extract_all_figures(self):
        """Extract all embedded figures from the entire document.
        
        Returns:
            list: List of light_path strings for all extracted figures
        """
        return self.extract_figures_by_page_range(1, len(self.doc))
    
    def extract_figures_from_metadata(self):
        """Extract page images for all pages containing figures according to TOC metadata.
        
        This extracts full page images for every page that contains figures according
        to the YAML metadata. If multiple figures are on the same page, multiple files
        are created (one for each figure) that can then be manually cropped.
        
        Returns:
            list: List of light_path strings for extracted page images
        """
        if not self.figure_metadata:
            print_progress("- No figure metadata available, cannot extract by metadata")
            return []
        
        print_section_header("EXTRACTING PAGE IMAGES FOR ALL FIGURES FROM TOC METADATA")
        
        # Get unique pages with figures
        pages_with_figures = sorted(self.figure_metadata.keys())
        
        print_progress(f"Found {len(pages_with_figures)} pages containing figures")
        
        # Count total expected figures
        total_expected_figures = sum(len(self.figure_metadata[page]) for page in pages_with_figures)
        print_progress(f"Total expected figures: {total_expected_figures}")
        print_progress("")
        
        all_figures = []
        
        for page_num in pages_with_figures:
            figures_on_page = self.figure_metadata[page_num]
            print_progress(f"=== PAGE {page_num} ===")
            print_progress(f"Expected figures on this page: {len(figures_on_page)}")
            for fig in figures_on_page:
                fig_num = fig.get('figure_number', '?')
                fig_title = fig.get('title', 'No title')
                print_progress(f"  - Figure {fig_num}: {fig_title}")
            
            # Extract page image(s) - creates one file per expected figure
            page_figures = self.extract_page_figures(page_num)
            all_figures.extend(page_figures)
            
            if page_figures:
                print_progress(f"+ Created {len(page_figures)} page image file(s) for manual cropping")
            else:
                print_progress(f"- No page images extracted from page {page_num}")
            print_progress("")
        
        print_section_header("METADATA-BASED EXTRACTION SUMMARY")
        print_progress(f"Pages processed: {len(pages_with_figures)}")
        print_progress(f"Expected figures: {total_expected_figures}")
        print_progress(f"Page image files created: {len(all_figures)}")
        print_progress(f"Output directory: {self.output_dir}")
        print_progress("")
        print_progress("NEXT STEPS:")
        print_progress("1. Each page image file contains the full page")
        print_progress("2. Manually crop each file to extract the specific figure")
        print_progress("3. Both light and dark theme versions are available")
        print_progress("4. Files are named according to figure numbers from TOC")
        
        return all_figures
    
    def close(self):
        """Clean up resources."""
        if hasattr(self, 'doc'):
            self.doc.close()


def main():
    """Main function for thesis figure extraction."""
    parser = argparse.ArgumentParser(
        description='Extract embedded figures from PhD thesis PDF with dual theme support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract figures from specific page range
  python extract_thesis_figures.py thesis.pdf --output-dir assets/ --page-range 40 50

  # Extract all figures from entire document
  python extract_thesis_figures.py thesis.pdf --output-dir assets/ --all-figures

  # Extract figures using YAML metadata locations
  python extract_thesis_figures.py thesis.pdf --output-dir assets/ --structure-dir structure/ --use-metadata

  # Extract with custom naming and quality settings
  python extract_thesis_figures.py thesis.pdf --output-dir assets/ --page-range 41 45 --structure-dir structure/

Output:
  Each figure generates two files:
  - figure-2-5.png      (light theme: black on transparent)
  - figure-2-5-dark.png (dark theme: white on transparent)
        """
    )
    
    parser.add_argument('pdf_path', help='Path to thesis PDF file')
    parser.add_argument('--output-dir', required=True,
                       help='Output directory for extracted figures')
    
    # Extraction modes
    extraction_group = parser.add_mutually_exclusive_group(required=True)
    extraction_group.add_argument('--page-range', nargs=2, type=int, metavar=('START', 'END'),
                                 help='Extract figures from page range (e.g., --page-range 40 50)')
    extraction_group.add_argument('--all-figures', action='store_true',
                                 help='Extract all embedded figures from entire document')
    extraction_group.add_argument('--use-metadata', action='store_true',
                                 help='Extract figures from locations specified in YAML metadata')
    
    # Optional parameters
    parser.add_argument('--structure-dir',
                       help='Directory containing YAML structure files (for metadata and naming)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.pdf_path).exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        return 1
    
    if args.use_metadata and not args.structure_dir:
        print("ERROR: --structure-dir is required when using --use-metadata")
        return 1
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Display extraction information
    print_section_header("THESIS FIGURE EXTRACTION")
    print(f"PDF: {args.pdf_path}")
    print(f"Output directory: {args.output_dir}")
    if args.structure_dir:
        print(f"Structure directory: {args.structure_dir}")
    
    if args.page_range:
        print(f"Mode: Page range ({args.page_range[0]}-{args.page_range[1]})")
    elif args.all_figures:
        print(f"Mode: All figures")
    elif args.use_metadata:
        print(f"Mode: YAML metadata locations")
    
    print("=" * 60)
    
    try:
        # Initialize extractor
        extractor = ThesisFigureExtractor(
            args.pdf_path,
            args.output_dir,
            args.structure_dir
        )
        
        # Extract figures based on mode
        if args.page_range:
            figures = extractor.extract_figures_by_page_range(args.page_range[0], args.page_range[1])
        elif args.all_figures:
            figures = extractor.extract_all_figures()
        elif args.use_metadata:
            figures = extractor.extract_figures_from_metadata()
        
        # Final summary
        if figures:
            print_completion_summary(
                args.output_dir,
                len(figures),
                f"figure(s) extracted (light theme only)"
            )
            
            print("\nGenerated files (light theme only):")
            for light_path in figures:
                light_name = Path(light_path).name
                print(f"  {light_name} (light theme)")
            print("\nNote: Run auto_crop_figures.py to generate dark theme versions and crop figures")
        else:
            print("No figures were extracted.")
        
        # Clean up
        extractor.close()
        
        return 0 if figures else 1
        
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
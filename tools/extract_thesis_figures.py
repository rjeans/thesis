#!/usr/bin/env python3
"""
Extract figures from thesis PDF using structure metadata.

This tool reads the figures YAML structure file and extracts a full page image
for each figure. Both light and dark theme versions are generated for optimal
display in different viewing modes.
"""

import argparse
import yaml
from pathlib import Path
import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf_utils import pdf_to_images, extract_pages_to_pdf
from progress_utils import print_progress, print_completion_summary, print_section_header


def load_figures_metadata(figures_yaml_path):
    """
    Load figures metadata from YAML file.
    
    Args:
        figures_yaml_path (Path): Path to thesis_figures.yaml file
        
    Returns:
        list: List of figure dictionaries from YAML
    """
    try:
        with open(figures_yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        figures = data.get('figures', [])
        print_progress(f"Loaded {len(figures)} figures from metadata")
        return figures
        
    except Exception as e:
        print_progress(f"ERROR: Could not load figures metadata: {e}")
        return []


def create_transparent_background_image(source_image_path, output_image_path):
    """
    Convert white background to transparent in the extracted PDF page image.
    
    Args:
        source_image_path (Path): Path to source image (from PDF)
        output_image_path (Path): Path to save processed image with transparency
        
    Returns:
        bool: True if processing succeeded
    """
    try:
        from PIL import Image
        
        # Increase PIL decompression bomb limit for large PDF pages
        Image.MAX_IMAGE_PIXELS = None  # Remove limit entirely
        
        # Open the source image
        with Image.open(source_image_path) as img:
            # Convert to RGBA for transparency support
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Get image data as array
            data = img.getdata()
            
            # Define what we consider "white" (with some tolerance for slight variations)
            # PDF backgrounds might not be pure white due to compression
            white_threshold = 240  # RGB values above this are considered "white"
            
            # Replace white/near-white pixels with transparent
            new_data = []
            for item in data:
                # If pixel is close to white (high R, G, B values), make it transparent
                if (item[0] > white_threshold and 
                    item[1] > white_threshold and 
                    item[2] > white_threshold):
                    # Make transparent (R, G, B, Alpha=0)
                    new_data.append((item[0], item[1], item[2], 0))
                else:
                    # Keep original pixel with full opacity
                    new_data.append((item[0], item[1], item[2], 255))
            
            # Apply the new data
            img.putdata(new_data)
            
            # Save with transparency
            img.save(output_image_path, format='PNG', optimize=True)
            
        return True
        
    except ImportError:
        print_progress(f"    WARNING: PIL not available, copying image without transparency")
        # Fallback: just copy the original image
        import shutil
        shutil.copy2(source_image_path, output_image_path)
        return True
    except Exception as e:
        print_progress(f"    ERROR: Could not create transparent background: {e}")
        return False


def create_dark_theme_image(light_image_path, dark_image_path):
    """
    Create dark theme version of an image by inverting colors while preserving transparency.
    
    Args:
        light_image_path (Path): Path to light theme image with transparency
        dark_image_path (Path): Path to save dark theme image
    """
    try:
        from PIL import Image, ImageOps
        
        # Increase PIL decompression bomb limit for large PDF pages
        Image.MAX_IMAGE_PIXELS = None  # Remove limit entirely
        
        # Open the light image (should have RGBA with transparency)
        with Image.open(light_image_path) as img:
            # Ensure we're working with RGBA mode
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Separate the color channels from alpha channel
            # We want to invert colors but preserve transparency
            r, g, b, a = img.split()
            
            # Combine RGB channels and invert them
            rgb_img = Image.merge('RGB', (r, g, b))
            inverted_rgb = ImageOps.invert(rgb_img)
            
            # Split the inverted RGB back into channels
            inv_r, inv_g, inv_b = inverted_rgb.split()
            
            # Recombine with original alpha channel to preserve transparency
            dark_img = Image.merge('RGBA', (inv_r, inv_g, inv_b, a))
            
            # Save dark theme version with transparency preserved
            dark_img.save(dark_image_path, format='PNG', optimize=True)
            
        print_progress(f"  Created dark theme with transparency: {dark_image_path.name}")
        
    except ImportError:
        print_progress(f"  WARNING: PIL not available, skipping dark theme generation")
    except Exception as e:
        print_progress(f"  WARNING: Could not create dark theme for {light_image_path.name}: {e}")


def extract_figure_page(pdf_path, page_num, figure_number, output_dir):
    """
    Extract a full page image for a figure.
    
    Args:
        pdf_path (Path): Path to source PDF
        page_num (int): Page number containing the figure
        figure_number (str): Figure number (e.g., "2.1")
        output_dir (Path): Output directory for images
        
    Returns:
        bool: True if extraction succeeded
    """
    import tempfile
    
    # Sanitize figure number for filename
    safe_figure_num = figure_number.replace('.', '-')
    light_filename = f"figure-{safe_figure_num}.png"
    dark_filename = f"figure-{safe_figure_num}-dark.png"
    
    light_path = output_dir / light_filename
    dark_path = output_dir / dark_filename
    
    print_progress(f"  Extracting Figure {figure_number} from page {page_num}")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract single page to PDF
            page_pdf_path = Path(temp_dir) / f"page_{page_num}.pdf"
            if not extract_pages_to_pdf(str(pdf_path), str(page_pdf_path), page_num, page_num):
                print_progress(f"    ERROR: Could not extract page {page_num}")
                return False
            
            # Convert page to image
            image_paths = pdf_to_images(str(page_pdf_path), temp_dir)
            if not image_paths:
                print_progress(f"    ERROR: Could not convert page {page_num} to image")
                return False
            
            # Process the image to add transparent background
            source_image = Path(image_paths[0])
            if create_transparent_background_image(source_image, light_path):
                print_progress(f"    Created light theme with transparency: {light_filename}")
                
                # Create dark theme version
                create_dark_theme_image(light_path, dark_path)
            else:
                print_progress(f"    ERROR: Could not process image for transparency")
                return False
            
            return True
            
    except Exception as e:
        print_progress(f"    ERROR: Failed to extract Figure {figure_number}: {e}")
        return False


def extract_figures(pdf_path, figures_yaml_path, output_dir, target_figure=None):
    """
    Extract figures from PDF based on metadata.
    
    Args:
        pdf_path (Path): Path to source PDF
        figures_yaml_path (Path): Path to figures YAML metadata
        output_dir (Path): Output directory for extracted figures
        target_figure (str, optional): Specific figure number to extract
        
    Returns:
        bool: True if extraction succeeded
    """
    print_section_header("THESIS FIGURE EXTRACTION")
    print_progress(f"PDF: {pdf_path}")
    print_progress(f"Figures metadata: {figures_yaml_path}")
    print_progress(f"Output directory: {output_dir}")
    if target_figure:
        print_progress(f"Target figure: {target_figure}")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load figures metadata
    figures = load_figures_metadata(figures_yaml_path)
    if not figures:
        return False
    
    # Filter for target figure if specified
    if target_figure:
        figures = [f for f in figures if f.get('figure_number') == target_figure]
        if not figures:
            print_progress(f"ERROR: Figure {target_figure} not found in metadata")
            return False
        print_progress(f"Found target figure: {target_figure}")
    
    # Extract each figure
    successful_extractions = 0
    total_figures = len(figures)
    
    for figure in figures:
        figure_number = figure.get('figure_number', 'unknown')
        page_num = figure.get('page')
        title = figure.get('title', 'No title')
        
        if not page_num:
            print_progress(f"  WARNING: No page number for Figure {figure_number}, skipping")
            continue
        
        print_progress(f"\nFigure {figure_number}: {title}")
        
        if extract_figure_page(pdf_path, page_num, figure_number, output_dir):
            successful_extractions += 1
    
    # Summary
    if successful_extractions > 0:
        print_progress(f"\n+ Successfully extracted {successful_extractions}/{total_figures} figures")
        print_progress(f"+ Light theme images: figure-X-Y.png")
        print_progress(f"+ Dark theme images: figure-X-Y-dark.png")
        print_completion_summary(str(output_dir), successful_extractions, "figures extracted")
        return True
    else:
        print_progress(f"\n- No figures were successfully extracted")
        return False


def main():
    """Main function for figure extraction."""
    parser = argparse.ArgumentParser(
        description='Extract figures from thesis PDF using structure metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all figures
  python extract_thesis_figures.py --input thesis.pdf --figures structure/thesis_figures.yaml --output assets/
  
  # Extract specific figure
  python extract_thesis_figures.py --input thesis.pdf --figures structure/thesis_figures.yaml --output assets/ --figure 2.1
  
This tool generates both light theme (figure-X-Y.png) and dark theme (figure-X-Y-dark.png) versions of each figure.
"""
    )
    
    parser.add_argument('--input', required=True, help='Path to source PDF file')
    parser.add_argument('--figures', required=True, help='Path to thesis_figures.yaml metadata file')
    parser.add_argument('--output', required=True, help='Output directory for extracted figures')
    parser.add_argument('--figure', help='Extract only this specific figure number (e.g., "2.1")')
    
    args = parser.parse_args()
    
    # Validate input files
    pdf_path = Path(args.input)
    if not pdf_path.exists():
        print(f"ERROR: PDF file not found: {pdf_path}")
        return 1
    
    figures_yaml_path = Path(args.figures)
    if not figures_yaml_path.exists():
        print(f"ERROR: Figures YAML file not found: {figures_yaml_path}")
        return 1
    
    output_dir = Path(args.output)
    
    # Extract figures
    success = extract_figures(pdf_path, figures_yaml_path, output_dir, args.figure)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
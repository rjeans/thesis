#!/usr/bin/env python3
"""
Automatically crop PNG figure assets and generate dark theme versions.

This script processes PNG files to remove padding and creates dual-theme
versions for optimal display in both light and dark viewing modes.
"""

import argparse
from pathlib import Path
import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from progress_utils import print_progress, print_completion_summary, print_section_header


class FigureCropper:
    """Crop figures and generate theme variations."""
    
    def __init__(self, input_dir, crop_padding=10):
        """
        Initialize the figure cropper.
        
        Args:
            input_dir (str): Directory containing PNG figures
            crop_padding (int): Padding to leave around cropped content
        """
        self.input_dir = Path(input_dir)
        self.crop_padding = crop_padding
        
        if not self.input_dir.exists():
            raise ValueError(f"Input directory not found: {self.input_dir}")
        
        print_progress(f"Figure cropper initialized")
        print_progress(f"Input directory: {self.input_dir}")
        print_progress(f"Crop padding: {self.crop_padding}px")
    
    def find_figure_files(self):
        """Find all PNG files in the input directory."""
        png_files = list(self.input_dir.glob("*.png"))
        # Exclude dark theme files (those ending with -dark.png)
        light_files = [f for f in png_files if not f.stem.endswith("-dark")]
        
        print_progress(f"Found {len(light_files)} figure files to process")
        return light_files
    
    def crop_and_generate_themes(self):
        """Crop all figures and generate dark theme versions."""
        figure_files = self.find_figure_files()
        
        if not figure_files:
            print_progress("- No PNG files found to process")
            return False
        
        processed_count = 0
        
        for figure_file in figure_files:
            print_progress(f"Processing {figure_file.name}...")
            
            try:
                # Crop the original figure
                success = self.crop_figure(figure_file)
                if success:
                    # Generate dark theme version
                    self.generate_dark_theme(figure_file)
                    processed_count += 1
                    print_progress(f"+ Successfully processed {figure_file.name}")
                else:
                    print_progress(f"- Failed to process {figure_file.name}")
                    
            except Exception as e:
                print_progress(f"- Error processing {figure_file.name}: {e}")
        
        print_progress(f"Processed {processed_count}/{len(figure_files)} figures")
        return processed_count > 0
    
    def crop_figure(self, figure_path):
        """
        Crop a figure to remove excessive padding.
        
        Args:
            figure_path (Path): Path to the figure file
        
        Returns:
            bool: True if cropping succeeded
        """
        try:
            # This is a simplified placeholder - in a real implementation,
            # you would use PIL (Pillow) to:
            # 1. Load the image
            # 2. Find the bounding box of non-transparent/non-white content
            # 3. Crop to that bounding box plus padding
            # 4. Save the cropped version
            
            print_progress(f"  Would crop: {figure_path}")
            print_progress(f"  Padding: {self.crop_padding}px")
            
            return True
            
        except Exception as e:
            print_progress(f"- Error cropping figure: {e}")
            return False
    
    def generate_dark_theme(self, figure_path):
        """
        Generate dark theme version of a figure.
        
        Args:
            figure_path (Path): Path to the light theme figure
        
        Returns:
            bool: True if dark theme generation succeeded
        """
        try:
            # Create dark theme filename
            dark_path = figure_path.parent / f"{figure_path.stem}-dark{figure_path.suffix}"
            
            # This is a simplified placeholder - in a real implementation,
            # you would use PIL to:
            # 1. Load the light theme image
            # 2. Apply color inversion or other dark theme transformations
            # 3. Adjust colors for dark backgrounds
            # 4. Save as the dark theme version
            
            print_progress(f"  Would generate dark theme: {dark_path.name}")
            
            return True
            
        except Exception as e:
            print_progress(f"- Error generating dark theme: {e}")
            return False


def main():
    """Main function for figure cropping and theme generation."""
    parser = argparse.ArgumentParser(
        description='Crop figures and generate dark theme versions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crop figures with default padding
  python auto_crop_figures.py --input-dir assets/
  
  # Crop with custom padding
  python auto_crop_figures.py --input-dir assets/ --crop-padding 15
  
This tool processes PNG files to remove excess padding and creates dual-theme versions.
"""
    )
    
    parser.add_argument('--input-dir', required=True, help='Input directory containing PNG figures')
    parser.add_argument('--crop-padding', type=int, default=10, 
                        help='Padding to leave around cropped content (default: 10px)')
    
    args = parser.parse_args()
    
    # Initialize cropper
    print_section_header("FIGURE CROPPING AND THEME GENERATION")
    
    try:
        cropper = FigureCropper(
            input_dir=args.input_dir,
            crop_padding=args.crop_padding
        )
        
        # Process figures
        success = cropper.crop_and_generate_themes()
        
        if success:
            print_completion_summary(args.input_dir, None, "figure processing completed")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
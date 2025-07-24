#!/usr/bin/env python3
"""
Automatically crop PNG figure assets to remove transparent/white background padding and generate dark theme versions.

This script processes all PNG files in a directory and crops them to the smallest
rectangle that contains the actual figure content, removing any transparent or
white background padding around the edges. It also generates dark theme versions
by inverting the RGB channels while preserving transparency.

Usage:
    python auto_crop_figures.py assets/ --backup
    python auto_crop_figures.py assets/ --dry-run
    python auto_crop_figures.py assets/ --threshold 240 --padding 10
    python auto_crop_figures.py assets/ --no-dark  # Skip dark version generation

Features:
- Intelligent edge detection for both transparent and white backgrounds
- Automatic dark theme generation from light versions
- Configurable threshold for background detection
- Optional padding around cropped content
- Backup creation before processing
- Dry run mode for testing
- Progress tracking for batch operations
- Preserves original file format and quality
- Figure pair validation for consistency checking
"""

import os
import sys
import argparse
from pathlib import Path
import shutil
from PIL import Image, ImageOps
import numpy as np

# Import our utilities
from progress_utils import print_progress, print_section_header, print_completion_summary


class AutoCropper:
    """Automatically crop PNG images to remove background padding and generate dark versions."""
    
    def __init__(self, threshold=240, padding=5, backup=False, dry_run=False, generate_dark=True):
        """Initialize the auto cropper.
        
        Args:
            threshold (int): Threshold for background detection (0-255)
            padding (int): Pixels to add around cropped content
            backup (bool): Create backup copies before processing
            dry_run (bool): Show what would be done without making changes
            generate_dark (bool): Generate dark theme versions from light versions
        """
        self.threshold = threshold
        self.padding = padding
        self.backup = backup
        self.dry_run = dry_run
        self.generate_dark = generate_dark
        
    def detect_content_bounds(self, img):
        """Detect the bounding box of actual content in the image.
        
        Args:
            img (PIL.Image): Image to analyze
            
        Returns:
            tuple: (left, top, right, bottom) bounding box or None if no content
        """
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Convert to numpy array for analysis
        img_array = np.array(img)
        
        # Get alpha channel
        alpha = img_array[:, :, 3]
        
        # For images with transparency, use alpha channel
        if np.any(alpha < 255):
            # Find non-transparent pixels
            non_transparent = alpha > 0
        else:
            # For images without transparency, detect background by color
            # Convert to grayscale for analysis
            gray = np.array(img.convert('L'))
            
            # Consider pixels darker than threshold as content
            non_transparent = gray < self.threshold
        
        # Find bounding box of content
        if not np.any(non_transparent):
            print_progress("  - No content detected in image")
            return None
        
        # Get coordinates of content pixels
        coords = np.where(non_transparent)
        
        if len(coords[0]) == 0:
            print_progress("  - No content pixels found")
            return None
        
        top = int(np.min(coords[0]))
        bottom = int(np.max(coords[0])) + 1
        left = int(np.min(coords[1]))
        right = int(np.max(coords[1])) + 1
        
        return (left, top, right, bottom)
    
    def calculate_crop_box(self, bounds, img_size):
        """Calculate final crop box with padding.
        
        Args:
            bounds (tuple): (left, top, right, bottom) content bounds
            img_size (tuple): (width, height) of original image
            
        Returns:
            tuple: (left, top, right, bottom) crop box
        """
        if not bounds:
            return None
        
        left, top, right, bottom = bounds
        width, height = img_size
        
        # Add padding
        left = max(0, left - self.padding)
        top = max(0, top - self.padding)
        right = min(width, right + self.padding)
        bottom = min(height, bottom + self.padding)
        
        return (left, top, right, bottom)
    
    def generate_dark_version(self, light_img):
        """Generate dark theme version from light theme image.
        
        Args:
            light_img (PIL.Image): Light theme image with transparent background
            
        Returns:
            PIL.Image: Dark theme version with white content on transparent background
        """
        # Convert to RGBA if not already
        if light_img.mode != 'RGBA':
            light_img = light_img.convert('RGBA')
        
        # Create dark version by inverting the RGB channels while preserving alpha
        img_array = np.array(light_img)
        dark_array = img_array.copy()
        
        # Invert RGB channels for pixels that are not fully transparent
        mask = img_array[:, :, 3] > 0  # Non-transparent pixels
        
        # Invert RGB values: black (0) -> white (255), white (255) -> black (0)
        dark_array[mask, 0] = 255 - img_array[mask, 0]  # R
        dark_array[mask, 1] = 255 - img_array[mask, 1]  # G
        dark_array[mask, 2] = 255 - img_array[mask, 2]  # B
        # Alpha channel stays the same
        
        return Image.fromarray(dark_array, 'RGBA')
    
    def crop_image(self, image_path):
        """Crop a single image file and optionally generate dark version.
        
        Args:
            image_path (Path): Path to image file
            
        Returns:
            dict: Results of cropping operation
        """
        try:
            # Load image
            img = Image.open(image_path)
            original_size = img.size
            
            print_progress(f"  Processing {image_path.name} ({original_size[0]}x{original_size[1]})")
            
            # Detect content bounds
            bounds = self.detect_content_bounds(img)
            if not bounds:
                return {
                    'success': False,
                    'reason': 'No content detected',
                    'original_size': original_size,
                    'cropped_size': None
                }
            
            # Calculate crop box with padding
            crop_box = self.calculate_crop_box(bounds, img.size)
            if not crop_box:
                return {
                    'success': False,
                    'reason': 'Invalid crop box',
                    'original_size': original_size,
                    'cropped_size': None
                }
            
            left, top, right, bottom = crop_box
            cropped_size = (right - left, bottom - top)
            
            # Check if cropping would actually change the image
            if (left == 0 and top == 0 and right == original_size[0] and bottom == original_size[1]):
                print_progress(f"    No cropping needed")
                
                # Still generate dark version if requested and this is a light image
                if self.generate_dark and not image_path.stem.endswith('-dark') and not self.dry_run:
                    dark_path = image_path.parent / f"{image_path.stem}-dark.png"
                    if not dark_path.exists():
                        dark_img = self.generate_dark_version(img)
                        dark_img.save(str(dark_path), 'PNG', optimize=True)
                        print_progress(f"    + Generated dark version: {dark_path.name}")
                
                return {
                    'success': True,
                    'reason': 'No cropping needed',
                    'original_size': original_size,
                    'cropped_size': original_size
                }
            
            print_progress(f"    Content bounds: {bounds}")
            print_progress(f"    Crop box: {crop_box}")
            print_progress(f"    New size: {cropped_size[0]}x{cropped_size[1]}")
            
            if self.dry_run:
                print_progress(f"    [DRY RUN] Would crop to {cropped_size[0]}x{cropped_size[1]}")
                if self.generate_dark and not image_path.stem.endswith('-dark'):
                    print_progress(f"    [DRY RUN] Would generate dark version")
                return {
                    'success': True,
                    'reason': 'Dry run - no changes made',
                    'original_size': original_size,
                    'cropped_size': cropped_size
                }
            
            # Create backup if requested
            if self.backup:
                backup_path = image_path.with_suffix('.backup.png')
                shutil.copy2(image_path, backup_path)
                print_progress(f"    Created backup: {backup_path.name}")
            
            # Crop the image
            cropped_img = img.crop(crop_box)
            
            # Save cropped light image
            cropped_img.save(image_path, 'PNG', optimize=True)
            print_progress(f"    + Cropped and saved light version")
            
            # Generate dark version if requested and this is not already a dark image
            if self.generate_dark and not image_path.stem.endswith('-dark'):
                dark_path = image_path.parent / f"{image_path.stem}-dark.png"
                dark_img = self.generate_dark_version(cropped_img)
                dark_img.save(str(dark_path), 'PNG', optimize=True)
                print_progress(f"    + Generated dark version: {dark_path.name}")
            
            return {
                'success': True,
                'reason': 'Successfully cropped',
                'original_size': original_size,
                'cropped_size': cropped_size
            }
            
        except Exception as e:
            print_progress(f"    - Error processing {image_path.name}: {e}")
            return {
                'success': False,
                'reason': f'Error: {e}',
                'original_size': None,
                'cropped_size': None
            }
    
    def validate_figure_pairs(self, directory):
        """Validate that figure pairs exist and have matching dimensions.
        
        Args:
            directory (Path): Directory containing PNG files
            
        Returns:
            dict: Validation results with any issues found
        """
        directory = Path(directory)
        png_files = list(directory.glob("*.png"))
        
        # Group figures by base name (without -dark suffix)
        figure_groups = {}
        for png_file in png_files:
            name = png_file.stem
            if name.endswith('-dark'):
                base_name = name[:-5]  # Remove '-dark'
                if base_name not in figure_groups:
                    figure_groups[base_name] = {}
                figure_groups[base_name]['dark'] = png_file
            else:
                base_name = name
                if base_name not in figure_groups:
                    figure_groups[base_name] = {}
                figure_groups[base_name]['light'] = png_file
        
        validation_results = {
            'missing_pairs': [],
            'size_mismatches': [],
            'valid_pairs': [],
            'total_figures': len(figure_groups)
        }
        
        print_section_header("FIGURE PAIR VALIDATION")
        
        for base_name, files in sorted(figure_groups.items()):
            light_file = files.get('light')
            dark_file = files.get('dark')
            
            # Check 1: Both light and dark versions exist
            if not light_file or not dark_file:
                missing = []
                if not light_file:
                    missing.append('light')
                if not dark_file:
                    missing.append('dark')
                
                validation_results['missing_pairs'].append({
                    'figure': base_name,
                    'missing': missing
                })
                print_progress(f"- {base_name}: Missing {', '.join(missing)} version(s)")
                continue
            
            # Check 2: Both versions have exactly the same dimensions
            try:
                light_img = Image.open(light_file)
                dark_img = Image.open(dark_file)
                
                light_size = light_img.size
                dark_size = dark_img.size
                
                if light_size != dark_size:
                    validation_results['size_mismatches'].append({
                        'figure': base_name,
                        'light_size': light_size,
                        'dark_size': dark_size,
                        'light_file': light_file.name,
                        'dark_file': dark_file.name
                    })
                    print_progress(f"- {base_name}: Size mismatch - light: {light_size[0]}x{light_size[1]}, dark: {dark_size[0]}x{dark_size[1]}")
                else:
                    validation_results['valid_pairs'].append({
                        'figure': base_name,
                        'size': light_size,
                        'light_file': light_file.name,
                        'dark_file': dark_file.name
                    })
                    print_progress(f"+ {base_name}: Valid pair ({light_size[0]}x{light_size[1]})")
                
                light_img.close()
                dark_img.close()
                
            except Exception as e:
                print_progress(f"- {base_name}: Error reading images - {e}")
                validation_results['missing_pairs'].append({
                    'figure': base_name,
                    'error': str(e)
                })
        
        return validation_results
    
    def process_directory(self, directory):
        """Process all PNG files in a directory with validation checks.
        
        Args:
            directory (Path): Directory containing PNG files
            
        Returns:
            dict: Summary of processing results
        """
        directory = Path(directory)
        
        if not directory.exists():
            print_progress(f"ERROR: Directory not found: {directory}")
            return {'success': False, 'reason': 'Directory not found'}
        
        # Find all PNG files
        png_files = list(directory.glob("*.png"))
        
        if not png_files:
            print_progress(f"No PNG files found in {directory}")
            return {'success': False, 'reason': 'No PNG files found'}
        
        # Run validation checks first
        validation = self.validate_figure_pairs(directory)
        
        # Report validation summary
        print_section_header("VALIDATION SUMMARY")
        print_progress(f"Total figure groups: {validation['total_figures']}")
        print_progress(f"Valid pairs: {len(validation['valid_pairs'])}")
        print_progress(f"Missing pairs: {len(validation['missing_pairs'])}")
        print_progress(f"Size mismatches: {len(validation['size_mismatches'])}")
        
        if validation['missing_pairs']:
            print_progress("")
            print_progress("MISSING PAIRS:")
            for missing in validation['missing_pairs']:
                if 'error' in missing:
                    print_progress(f"  {missing['figure']}: {missing['error']}")
                else:
                    print_progress(f"  {missing['figure']}: Missing {', '.join(missing['missing'])} version(s)")
        
        if validation['size_mismatches']:
            print_progress("")
            print_progress("SIZE MISMATCHES:")
            for mismatch in validation['size_mismatches']:
                print_progress(f"  {mismatch['figure']}:")
                print_progress(f"    Light: {mismatch['light_size'][0]}x{mismatch['light_size'][1]} ({mismatch['light_file']})")
                print_progress(f"    Dark:  {mismatch['dark_size'][0]}x{mismatch['dark_size'][1]} ({mismatch['dark_file']})")
        
        # If there are validation issues, ask user if they want to continue
        if validation['missing_pairs'] or validation['size_mismatches']:
            print_progress("")
            print_progress("VALIDATION ISSUES FOUND!")
            if not self.dry_run:
                print_progress("Consider fixing these issues before proceeding with cropping.")
                print_progress("You can still continue, but mismatched figures may have different final sizes.")
                print_progress("")
        
        print_section_header(f"AUTO-CROPPING {len(png_files)} PNG FILES")
        print_progress(f"Directory: {directory}")
        print_progress(f"Threshold: {self.threshold}")
        print_progress(f"Padding: {self.padding} pixels")
        print_progress(f"Backup: {'Yes' if self.backup else 'No'}")
        print_progress(f"Generate dark versions: {'Yes' if self.generate_dark else 'No'}")
        print_progress(f"Dry run: {'Yes' if self.dry_run else 'No'}")
        print_progress("")
        
        results = []
        successful_crops = 0
        total_size_reduction = 0
        
        for png_file in sorted(png_files):
            result = self.crop_image(png_file)
            results.append({
                'file': png_file.name,
                **result
            })
            
            if result['success'] and result['original_size'] and result['cropped_size']:
                if result['original_size'] != result['cropped_size']:
                    successful_crops += 1
                    original_area = result['original_size'][0] * result['original_size'][1]
                    cropped_area = result['cropped_size'][0] * result['cropped_size'][1]
                    size_reduction = original_area - cropped_area
                    total_size_reduction += size_reduction
        
        # Summary
        print_section_header("PROCESSING SUMMARY")
        print_progress(f"Files processed: {len(png_files)}")
        print_progress(f"Successfully cropped: {successful_crops}")
        print_progress(f"No changes needed: {len([r for r in results if r.get('reason') == 'No cropping needed'])}")
        print_progress(f"Errors: {len([r for r in results if not r['success']])}")
        
        if total_size_reduction > 0:
            avg_reduction = (total_size_reduction / len(png_files)) if png_files else 0
            print_progress(f"Average pixel reduction per file: {avg_reduction:.0f}")
        
        if self.dry_run:
            print_progress("")
            print_progress("This was a dry run - no files were modified")
            print_progress("Run without --dry-run to apply changes")
        
        # Final validation check after processing
        if not self.dry_run and (validation['missing_pairs'] or validation['size_mismatches']):
            print_progress("")
            print_progress("Running post-processing validation...")
            final_validation = self.validate_figure_pairs(directory)
            
            if final_validation['size_mismatches']:
                print_progress("")
                print_progress("WARNING: Size mismatches still exist after processing!")
                for mismatch in final_validation['size_mismatches']:
                    print_progress(f"  {mismatch['figure']}: light {mismatch['light_size']} vs dark {mismatch['dark_size']}")
        
        return {
            'success': True,
            'processed': len(png_files),
            'cropped': successful_crops,
            'results': results,
            'validation': validation
        }


def main():
    """Main function for auto-cropping PNG assets."""
    parser = argparse.ArgumentParser(
        description='Automatically crop PNG figure assets to remove background padding',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crop all PNG files and generate dark versions with backup
  python auto_crop_figures.py assets/ --backup
  
  # Test run without making changes
  python auto_crop_figures.py assets/ --dry-run
  
  # Custom threshold and padding
  python auto_crop_figures.py assets/ --threshold 250 --padding 10
  
  # Process with minimal padding for tight crops
  python auto_crop_figures.py assets/ --padding 2
  
  # Only crop light versions without generating dark themes
  python auto_crop_figures.py assets/ --no-dark
  
  # Validate figure pairs without processing
  python auto_crop_figures.py assets/ --validate-only

Background Detection:
  - For transparent images: Uses alpha channel to detect content
  - For opaque images: Uses threshold to detect background vs content
  - Threshold 240 works well for white/light gray backgrounds
  - Lower threshold (200) for darker backgrounds

Dark Theme Generation:
  - Automatically creates dark versions by inverting RGB channels
  - Preserves alpha transparency in both light and dark versions
  - Ensures matching dimensions between light and dark versions
  - Skips generation if dark version already exists
        """
    )
    
    parser.add_argument('directory', help='Directory containing PNG files to crop')
    
    parser.add_argument('--threshold', type=int, default=240,
                       help='Background detection threshold (0-255, default: 240)')
    parser.add_argument('--padding', type=int, default=5,
                       help='Pixels to add around cropped content (default: 5)')
    parser.add_argument('--backup', action='store_true',
                       help='Create backup copies before cropping')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without making changes')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate figure pairs without cropping')
    parser.add_argument('--no-dark', action='store_true',
                       help='Skip dark version generation (only crop light versions)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not 0 <= args.threshold <= 255:
        print("ERROR: Threshold must be between 0 and 255")
        return 1
    
    if args.padding < 0:
        print("ERROR: Padding must be non-negative")
        return 1
    
    # Initialize cropper
    cropper = AutoCropper(
        threshold=args.threshold,
        padding=args.padding,
        backup=args.backup,
        dry_run=args.dry_run,
        generate_dark=not args.no_dark
    )
    
    # Handle validation-only mode
    if args.validate_only:
        try:
            directory = Path(args.directory)
            if not directory.exists():
                print(f"ERROR: Directory not found: {args.directory}")
                return 1
            
            validation = cropper.validate_figure_pairs(directory)
            
            # Report validation summary
            print_section_header("VALIDATION SUMMARY")
            print_progress(f"Total figure groups: {validation['total_figures']}")
            print_progress(f"Valid pairs: {len(validation['valid_pairs'])}")
            print_progress(f"Missing pairs: {len(validation['missing_pairs'])}")
            print_progress(f"Size mismatches: {len(validation['size_mismatches'])}")
            
            if validation['missing_pairs'] or validation['size_mismatches']:
                print_progress("")
                print_progress("ISSUES FOUND - see details above")
                return 1
            else:
                print_progress("")
                print_progress("All figure pairs are valid!")
                return 0
                
        except Exception as e:
            print(f"ERROR: {e}")
            return 1
    
    # Process directory
    try:
        result = cropper.process_directory(args.directory)
        
        if result['success']:
            if not args.dry_run:
                print_completion_summary(
                    args.directory,
                    result['cropped'],
                    f"PNG file(s) auto-cropped successfully"
                )
            return 0
        else:
            print(f"FAILED: {result.get('reason', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
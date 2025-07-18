#!/usr/bin/env python3
"""
Figure extraction using ImageMagick - practical approach for thesis conversion
"""

import subprocess
import json
from pathlib import Path
import sys
import re

class FigureExtractor:
    def __init__(self, output_dir="../images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def resize_page(self, input_path, max_width=2000):
        """Resize page to manageable size for processing"""
        input_path = Path(input_path)
        resized_path = input_path.parent / f"{input_path.stem}_resized.png"
        
        cmd = ["magick", str(input_path), "-resize", f"{max_width}x", str(resized_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Resized {input_path.name} -> {resized_path.name}")
            return resized_path
        else:
            print(f"Failed to resize: {result.stderr}")
            return None
    
    def detect_figure_regions(self, image_path):
        """
        Use ImageMagick to detect potential figure regions
        Strategy: Look for connected components that are likely figures
        """
        # Get image dimensions
        cmd = ["magick", "identify", "-format", "%w %h", str(image_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return []
        
        width, height = map(int, result.stdout.strip().split())
        
        # Define potential figure regions based on typical academic paper layout
        # These are educated guesses that can be refined
        potential_regions = [
            {
                "name": "top_figure",
                "box": (int(width*0.1), int(height*0.15), int(width*0.9), int(height*0.45)),
                "description": "Top half figure region"
            },
            {
                "name": "middle_figure", 
                "box": (int(width*0.1), int(height*0.3), int(width*0.9), int(height*0.7)),
                "description": "Middle figure region"
            },
            {
                "name": "bottom_figure",
                "box": (int(width*0.1), int(height*0.55), int(width*0.9), int(height*0.85)),
                "description": "Bottom figure region"
            }
        ]
        
        return potential_regions
    
    def extract_region(self, image_path, region_box, output_name):
        """Extract a specific region from the image"""
        x, y, x2, y2 = region_box
        width = x2 - x
        height = y2 - y
        
        output_path = self.output_dir / f"{output_name}.png"
        
        # ImageMagick crop format: widthxheight+x+y
        crop_spec = f"{width}x{height}+{x}+{y}"
        
        cmd = ["magick", str(image_path), "-crop", crop_spec, str(output_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Extracted region to: {output_path}")
            return output_path
        else:
            print(f"Failed to extract: {result.stderr}")
            return None
    
    def manual_crop_interactive(self, image_path):
        """Guide user through manual cropping process"""
        print(f"\nManual cropping for: {image_path}")
        print("1. Open the image in an image viewer")
        print("2. Note the coordinates of the figure you want to extract")
        print("3. Enter the coordinates when prompted")
        print()
        
        try:
            x = int(input("Left edge (x): "))
            y = int(input("Top edge (y): "))
            x2 = int(input("Right edge (x2): "))
            y2 = int(input("Bottom edge (y2): "))
            
            name = input("Figure name (e.g., figure-2-5): ")
            
            return self.extract_region(image_path, (x, y, x2, y2), name)
            
        except ValueError:
            print("Invalid coordinates entered")
            return None
    
    def create_markdown_link(self, figure_path, caption=""):
        """Generate markdown link for figure"""
        # Create relative path from thesis root
        rel_path = f"images/{figure_path.name}"
        if caption:
            return f"![{caption}]({rel_path})"
        else:
            return f"![]({rel_path})"
    
    def update_markdown_links(self, markdown_path, replacements):
        """Update markdown file with actual figure links"""
        content = Path(markdown_path).read_text()
        
        for old_link, new_link in replacements.items():
            content = content.replace(old_link, new_link)
            print(f"Updated: {old_link} -> {new_link}")
        
        Path(markdown_path).write_text(content)

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python extract_figures_imagemagick.py resize <image>")
        print("  python extract_figures_imagemagick.py auto <image>")
        print("  python extract_figures_imagemagick.py manual <image>")
        print("  python extract_figures_imagemagick.py crop <image> <x> <y> <x2> <y2> <name>")
        print("  python extract_figures_imagemagick.py update-md <markdown> <old> <new>")
        return
    
    extractor = FigureExtractor()
    command = sys.argv[1]
    
    if command == "resize":
        image_path = Path(sys.argv[2])
        resized = extractor.resize_page(image_path)
        if resized:
            print(f"Use resized image for further processing: {resized}")
    
    elif command == "auto":
        image_path = Path(sys.argv[2])
        print(f"Auto-detecting regions in: {image_path}")
        
        regions = extractor.detect_figure_regions(image_path)
        for i, region in enumerate(regions):
            print(f"{i+1}. {region['description']}: {region['box']}")
        
        print("\nTo extract a region, use:")
        print("python extract_figures_imagemagick.py crop <image> <x> <y> <x2> <y2> <name>")
    
    elif command == "manual":
        image_path = Path(sys.argv[2])
        extractor.manual_crop_interactive(image_path)
    
    elif command == "crop":
        if len(sys.argv) != 8:
            print("Usage: crop <image> <x> <y> <x2> <y2> <name>")
            return
        
        image_path = Path(sys.argv[2])
        x, y, x2, y2 = map(int, sys.argv[3:7])
        name = sys.argv[7]
        
        result = extractor.extract_region(image_path, (x, y, x2, y2), name)
        if result:
            link = extractor.create_markdown_link(result, f"Figure {name}")
            print(f"Markdown link: {link}")
    
    elif command == "update-md":
        if len(sys.argv) != 5:
            print("Usage: update-md <markdown> <old_link> <new_link>")
            return
        
        markdown_path = Path(sys.argv[2])
        old_link = sys.argv[3]
        new_link = sys.argv[4]
        
        extractor.update_markdown_links(markdown_path, {old_link: new_link})
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
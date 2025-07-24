#!/usr/bin/env python3
"""
Fix figure caption hyperlinks in markdown files.

Figure captions should be plain text since we already have HTML anchors.
This script converts [Figure X.Y.](#figure-x-y-) Caption → Figure X.Y. Caption

Usage:
    python fix_figure_captions.py input.md
"""

import re
import sys
from pathlib import Path


def fix_figure_captions(content):
    """Fix figure caption hyperlinks to plain text."""
    
    # Pattern: [Figure X.Y.](#figure-x-y-) Caption text → Figure X.Y. Caption text
    def fix_caption(match):
        figure_text = match.group(1)  # e.g., "Figure 2.5."
        caption_text = match.group(2)  # e.g., " The thin shell geometry."
        return f"{figure_text}{caption_text}"
    
    # Fix figure captions that are incorrectly hyperlinked
    fixed_content = re.sub(r'\[(\bFigure\s+\d+\.\d+\.)\]\(#[^)]+\)([^\n]*)', fix_caption, content)
    
    # Count fixes made
    original_captions = len(re.findall(r'\[(\bFigure\s+\d+\.\d+\.)\]\(#[^)]+\)', content))
    remaining_captions = len(re.findall(r'\[(\bFigure\s+\d+\.\d+\.)\]\(#[^)]+\)', fixed_content))
    fixes_made = original_captions - remaining_captions
    
    return fixed_content, fixes_made


def main():
    if len(sys.argv) != 2:
        print("Usage: python fix_figure_captions.py input.md")
        return 1
    
    input_file = Path(sys.argv[1])
    
    if not input_file.exists():
        print(f"Error: File {input_file} not found")
        return 1
    
    print(f"Processing {input_file}...")
    
    # Read the file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix figure captions
    print("Fixing figure caption hyperlinks...")
    fixed_content, fixes_made = fix_figure_captions(content)
    
    if fixes_made > 0:
        # Write the fixed content back
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"✅ Fixed {fixes_made} figure caption hyperlinks in {input_file}")
    else:
        print(f"✅ No figure caption hyperlinks found to fix in {input_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())
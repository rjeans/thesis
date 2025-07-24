#!/usr/bin/env python3
"""
Fix mathematical delimiters in markdown files.

This script converts \[...\] and \(...\) delimiters to $$...$$ and $...$ respectively,
and also adds hyperlinks to equation and figure references.

Usage:
    python fix_math_delimiters.py input.md
"""

import re
import sys
from pathlib import Path


def fix_math_delimiters(content):
    """Fix LaTeX delimiters to markdown format."""
    
    # First, let's fix any numeric codes that may have appeared
    content = re.sub(r'^\d{5,}$', '$$', content, flags=re.MULTILINE)
    
    # Fix display math delimiters \[ and \]
    content = re.sub(r'\\\\\[', '$$', content)
    content = re.sub(r'\\\\\]', '$$', content)
    content = re.sub(r'\\\[', '$$', content)
    content = re.sub(r'\\\]', '$$', content)
    
    # Fix inline math delimiters \( and \)
    content = re.sub(r'\\\\\(', '$', content)
    content = re.sub(r'\\\\\)', '$', content)
    content = re.sub(r'\\\(', '$', content)
    content = re.sub(r'\\\)', '$', content)
    
    return content


def add_hyperlinks_to_references(content):
    """Add hyperlinks to equation and figure references."""
    
    # Add hyperlinks to equation references
    # Match patterns like "Eq. (2.1.4)", "equation (2.1.4)", "Eq. 2.1.4", etc.
    def equation_link_replacer(match):
        full_match = match.group(0)
        eq_num = match.group(1) if match.group(1) else match.group(2)
        anchor_id = f"equation-{eq_num.replace('.', '-')}"
        return f"[{full_match}](#{anchor_id})"
    
    # Pattern for equation references
    eq_patterns = [
        r'\bEq\.\s*\(([0-9.]+)\)',
        r'\bequation\s*\(([0-9.]+)\)',
        r'\bEq\.\s*([0-9.]+)',
        r'\bequation\s*([0-9.]+)',
    ]
    
    for pattern in eq_patterns:
        content = re.sub(pattern, equation_link_replacer, content, flags=re.IGNORECASE)
    
    # Add hyperlinks to figure references
    # Match patterns like "Figure 2.1", "Fig. 2.1", "figure 2.1", etc.
    def figure_link_replacer(match):
        full_match = match.group(0)
        fig_num = match.group(1)
        anchor_id = f"figure-{fig_num.replace('.', '-')}"
        return f"[{full_match}](#{anchor_id})"
    
    # Pattern for figure references (not followed by a period and title)
    fig_patterns = [
        r'\bFigure\s+([0-9.]+)(?!\s*\.)',
        r'\bFig\.\s*([0-9.]+)(?!\s*\.)',
        r'\bfigure\s+([0-9.]+)(?!\s*\.)',
    ]
    
    for pattern in fig_patterns:
        content = re.sub(pattern, figure_link_replacer, content)
    
    # Add hyperlinks to table references
    def table_link_replacer(match):
        full_match = match.group(0)
        table_num = match.group(1)
        anchor_id = f"table-{table_num.replace('.', '-')}"
        return f"[{full_match}](#{anchor_id})"
    
    # Pattern for table references
    table_patterns = [
        r'\bTable\s+([0-9.]+)(?!\s*\.)',
        r'\btable\s+([0-9.]+)(?!\s*\.)',
    ]
    
    for pattern in table_patterns:
        content = re.sub(pattern, table_link_replacer, content)
    
    return content


def clean_duplicate_links(content):
    """Remove duplicate links that may have been created."""
    # Fix cases where we created nested links
    content = re.sub(r'\[(\[[^\]]+\]\([^)]+\))\]\([^)]+\)', r'\1', content)
    return content


def main():
    if len(sys.argv) != 2:
        print("Usage: python fix_math_delimiters.py input.md")
        return 1
    
    input_file = Path(sys.argv[1])
    
    if not input_file.exists():
        print(f"Error: File {input_file} not found")
        return 1
    
    print(f"Processing {input_file}...")
    
    # Read the file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix mathematical delimiters
    print("Fixing mathematical delimiters...")
    content = fix_math_delimiters(content)
    
    # Add hyperlinks to references
    print("Adding hyperlinks to equation and figure references...")
    content = add_hyperlinks_to_references(content)
    
    # Clean up any duplicate links
    content = clean_duplicate_links(content)
    
    # Write the fixed content back
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed mathematical delimiters and added hyperlinks in {input_file}")
    return 0


if __name__ == "__main__":
    exit(main())
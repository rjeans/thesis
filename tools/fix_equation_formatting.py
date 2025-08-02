#!/usr/bin/env python3
"""
Fix equation formatting in markdown files.

This script corrects malformed LaTeX equations that have line breaks inside $$ blocks.
It converts multi-line equations to single-line format as required by the formatting standards.
"""

import argparse
import re
from pathlib import Path
import sys

def fix_equation_formatting(content):
    """
    Fix equation formatting by converting multi-line $$ blocks to single-line format
    and fixing inline equation delimiters.
    
    Args:
        content (str): Markdown content to fix
        
    Returns:
        str: Fixed markdown content
    """
    # Fix 1: Convert multi-line equation blocks to single-line format
    # Pattern to match multi-line equation blocks: $$ (content with potential newlines) $$
    pattern = r'\$\$\s*\n*(.*?)\n*\s*\$\$'
    
    def fix_equation_block(match):
        equation_content = match.group(1)
        
        # Remove internal newlines and excessive whitespace
        # But preserve single spaces between elements
        fixed_equation = re.sub(r'\s*\n\s*', ' ', equation_content)
        # Clean up multiple spaces
        fixed_equation = re.sub(r'\s+', ' ', fixed_equation)
        # Remove leading/trailing whitespace
        fixed_equation = fixed_equation.strip()
        
        # Return as single-line equation
        return f'$${fixed_equation}$$'
    
    # Apply the display equation fix
    fixed_content = re.sub(pattern, fix_equation_block, content, flags=re.DOTALL)
    
    # Fix 2: Convert \(...\) inline equations to $...$ format
    inline_pattern = r'\\?\\\((.*?)\\?\\\)'
    
    def fix_inline_equation(match):
        equation_content = match.group(1)
        return f'${equation_content}$'
    
    # Apply the inline equation fix
    fixed_content = re.sub(inline_pattern, fix_inline_equation, fixed_content)
    
    # Fix 3: Convert \[...\] display equations to $$...$$ format (just in case)
    display_bracket_pattern = r'\\?\\\[(.*?)\\?\\\]'
    
    def fix_display_bracket_equation(match):
        equation_content = match.group(1)
        return f'$${equation_content}$$'
    
    # Apply the display bracket equation fix
    fixed_content = re.sub(display_bracket_pattern, fix_display_bracket_equation, fixed_content, flags=re.DOTALL)
    
    return fixed_content

def count_equation_issues(content):
    """
    Count the number of malformed equation blocks and inline equations in the content.
    
    Args:
        content (str): Markdown content to analyze
        
    Returns:
        int: Total number of equation formatting issues found
    """
    # Find equation blocks that span multiple lines
    display_pattern = r'\$\$\s*\n.*?\n.*?\$\$'
    display_matches = re.findall(display_pattern, content, re.DOTALL)
    
    # Find \(...\) inline equations
    inline_pattern = r'\\?\\\((.*?)\\?\\\)'
    inline_matches = re.findall(inline_pattern, content)
    
    # Find \[...\] display equations
    bracket_pattern = r'\\?\\\[(.*?)\\?\\\]'
    bracket_matches = re.findall(bracket_pattern, content, re.DOTALL)
    
    return len(display_matches) + len(inline_matches) + len(bracket_matches)

def fix_markdown_file(file_path, dry_run=False):
    """
    Fix equation formatting in a markdown file.
    
    Args:
        file_path (Path): Path to markdown file
        dry_run (bool): If True, only report issues without fixing
        
    Returns:
        bool: True if fixes were applied or issues found
    """
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        return False
    
    if not file_path.suffix.lower() == '.md':
        print(f"WARNING: Not a markdown file: {file_path}")
        return False
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Count issues before fixing
        issues_found = count_equation_issues(original_content)
        
        if issues_found == 0:
            print(f"✓ {file_path.name}: No equation formatting issues found")
            return False
        
        print(f"⚠ {file_path.name}: Found {issues_found} malformed equation block(s)")
        
        if dry_run:
            print(f"  (Dry run - no changes made)")
            return True
        
        # Fix the content
        fixed_content = fix_equation_formatting(original_content)
        
        # Verify the fix worked
        remaining_issues = count_equation_issues(fixed_content)
        
        if remaining_issues > 0:
            print(f"  WARNING: {remaining_issues} issues remain after fixing")
        
        # Write the fixed content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"  ✓ Fixed {issues_found - remaining_issues} equation formatting issues")
        return True
        
    except Exception as e:
        print(f"ERROR: Could not process {file_path}: {e}")
        return False

def main():
    """Main function for equation formatting fixes."""
    parser = argparse.ArgumentParser(
        description='Fix equation formatting in markdown files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fix specific file
  python fix_equation_formatting.py --input chapter_2.md
  
  # Check all markdown files in directory (dry run)
  python fix_equation_formatting.py --input markdown_output/ --dry-run
  
  # Fix all markdown files in directory
  python fix_equation_formatting.py --input markdown_output/
  
This tool converts multi-line equation blocks like:
  $$
  equation content
  \\tag{2.1}
  $$
  
To single-line format:
  $$equation content \\tag{2.1}$$
"""
    )
    
    parser.add_argument('--input', required=True, 
                       help='Input markdown file or directory containing markdown files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Only report issues without making changes')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"ERROR: Input path not found: {input_path}")
        return 1
    
    files_processed = 0
    files_fixed = 0
    
    if input_path.is_file():
        # Process single file
        if fix_markdown_file(input_path, args.dry_run):
            files_fixed += 1
        files_processed += 1
    elif input_path.is_dir():
        # Process all markdown files in directory
        markdown_files = list(input_path.glob('*.md'))
        
        if not markdown_files:
            print(f"No markdown files found in: {input_path}")
            return 1
        
        print(f"Processing {len(markdown_files)} markdown files...")
        print()
        
        for md_file in sorted(markdown_files):
            if fix_markdown_file(md_file, args.dry_run):
                files_fixed += 1
            files_processed += 1
    else:
        print(f"ERROR: Input path is neither file nor directory: {input_path}")
        return 1
    
    # Summary
    print()
    if args.dry_run:
        print(f"Dry run completed: {files_fixed}/{files_processed} files have equation formatting issues")
    else:
        print(f"Processing completed: {files_fixed}/{files_processed} files were fixed")
    
    return 0

if __name__ == "__main__":
    exit(main())
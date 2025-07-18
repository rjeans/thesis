#!/usr/bin/env python3
"""
Simple markdown validation script to check for KaTeX rendering issues
"""

import re
import sys
from pathlib import Path

def validate_math_blocks(content):
    """Check for common KaTeX issues in markdown content"""
    issues = []
    
    # Check for inline math with proper delimiters
    inline_math = re.findall(r'\$([^$]+)\$', content)
    for i, match in enumerate(inline_math):
        if match.strip() == '':
            issues.append(f"Empty inline math block: ${match}$")
        if '$' in match:
            issues.append(f"Nested $ in inline math: ${match}$")
    
    # Check for display math blocks
    display_math = re.findall(r'\$\$(.*?)\$\$', content, re.DOTALL)
    for i, match in enumerate(display_math):
        if match.strip() == '':
            issues.append(f"Empty display math block: $${match}$$")
        if '$' in match:
            issues.append(f"Nested $ in display math block {i+1}: $${match}$$")
    
    # Check for unmatched $ symbols
    dollar_count = content.count('$')
    if dollar_count % 2 != 0:
        issues.append(f"Unmatched $ symbols (count: {dollar_count})")
    
    return issues

def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_markdown.py <markdown_file>")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    content = file_path.read_text()
    issues = validate_math_blocks(content)
    
    if issues:
        print(f"Found {len(issues)} potential KaTeX issues:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
    else:
        print("No obvious KaTeX issues found!")
    
    # Show math block summary
    inline_count = len(re.findall(r'\$[^$]+\$', content))
    display_count = len(re.findall(r'\$\$.*?\$\$', content, re.DOTALL))
    print(f"\nMath blocks summary:")
    print(f"  Inline math: {inline_count}")
    print(f"  Display math: {display_count}")
    print(f"  Total $ symbols: {content.count('$')}")

if __name__ == "__main__":
    main()
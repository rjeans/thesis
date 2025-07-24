#!/usr/bin/env python3
"""
Extract table of contents from PDF text for initial structure analysis.

This script extracts text from TOC pages and attempts to parse the structure
without using GPT-4 Vision. Useful for quick validation and debugging.

Usage:
    python extract_toc_text.py thesis.pdf 9 12 toc_text_analysis.txt

The script will:
1. Extract raw text from specified PDF pages
2. Analyze text patterns for TOC structure
3. Generate a preliminary structure estimate
4. Compare with vision-based results

Requires:
- PyMuPDF (fitz) or pdfplumber for text extraction
"""

import argparse
import re
from pathlib import Path
from progress_utils import print_progress, print_section_header

def extract_text_from_pdf(pdf_path, start_page, end_page):
    """
    Extract text from PDF pages using multiple methods.
    
    Args:
        pdf_path (str): Path to PDF file
        start_page (int): First page (1-based)
        end_page (int): Last page (1-based)
        
    Returns:
        dict: Text content by page number
    """
    print_progress("Attempting PDF text extraction...")
    
    extracted_text = {}
    
    # Try PyMuPDF first
    try:
        import fitz  # PyMuPDF
        print_progress("Using PyMuPDF for text extraction")
        
        doc = fitz.open(pdf_path)
        for page_num in range(start_page - 1, end_page):  # Convert to 0-based
            if page_num < len(doc):
                page = doc.load_page(page_num)
                text = page.get_text()
                extracted_text[page_num + 1] = text  # Store with 1-based page numbers
                print_progress(f"+ Page {page_num + 1}: {len(text)} characters")
        doc.close()
        return extracted_text
        
    except ImportError:
        print_progress("PyMuPDF not available, trying pdfplumber...")
    
    # Try pdfplumber as fallback
    try:
        import pdfplumber
        print_progress("Using pdfplumber for text extraction")
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in range(start_page - 1, end_page):  # Convert to 0-based
                if page_num < len(pdf.pages):
                    page = pdf.pages[page_num]
                    text = page.extract_text() or ""
                    extracted_text[page_num + 1] = text
                    print_progress(f"+ Page {page_num + 1}: {len(text)} characters")
        return extracted_text
        
    except ImportError:
        print_progress("pdfplumber not available, trying pypdf...")
    
    # Try pypdf as last resort
    try:
        import pypdf
        print_progress("Using pypdf for text extraction")
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            for page_num in range(start_page - 1, min(end_page, len(pdf_reader.pages))):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                extracted_text[page_num + 1] = text
                print_progress(f"+ Page {page_num + 1}: {len(text)} characters")
        return extracted_text
        
    except ImportError:
        print_progress("- No PDF text extraction libraries available")
        print_progress("  Install: pip install PyMuPDF pdfplumber")
        return {}


def analyze_toc_patterns(text_by_page):
    """
    Analyze extracted text for TOC patterns and structure.
    
    Args:
        text_by_page (dict): Text content by page number
        
    Returns:
        dict: Analyzed TOC structure
    """
    print_progress("Analyzing TOC patterns in extracted text...")
    
    analysis = {
        'pages_processed': list(text_by_page.keys()),
        'total_lines': 0,
        'potential_entries': [],
        'patterns_found': {
            'chapters': [],
            'sections': [],
            'appendices': [],
            'front_matter': []
        },
        'numbering_styles': set(),
        'page_references': []
    }
    
    # Common TOC patterns
    chapter_patterns = [
        r'(?i)^chapter\s+(\d+)[.\s]+(.+?)\s+(\d+)$',  # Chapter 1. Title 25
        r'^(\d+)\.\s+(.+?)\s+(\d+)$',                 # 1. Title 25
        r'^(\d+)\s+(.+?)\s+(\d+)$'                    # 1 Title 25
    ]
    
    section_patterns = [
        r'^(\d+\.\d+)\s+(.+?)\s+(\d+)$',              # 1.1 Title 27
        r'^(\d+\.\d+\.\d+)\s+(.+?)\s+(\d+)$',         # 1.1.1 Title 28
        r'^\s+(\d+\.\d+)\s+(.+?)\s+(\d+)$',           # Indented sections
    ]
    
    appendix_patterns = [
        r'(?i)^appendix\s+([A-Z])[.\s]+(.+?)\s+(\d+)$', # Appendix A. Title 200
        r'^([A-Z])\.\s+(.+?)\s+(\d+)$',                # A. Title 200
    ]
    
    front_matter_patterns = [
        r'(?i)^(abstract|acknowledgments?|preface|contents|list of figures|list of tables)\s+(\d+)$',
        r'(?i)^(.+?)\s+([ivx]+)$',  # Roman numerals for front matter
    ]
    
    for page_num, text in text_by_page.items():
        if not text.strip():
            print_progress(f"- Page {page_num}: No text extracted")
            continue
            
        lines = text.strip().split('\n')
        analysis['total_lines'] += len(lines)
        
        print_progress(f"Analyzing page {page_num}: {len(lines)} lines")
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if len(line) < 3:  # Skip very short lines
                continue
                
            # Try to match chapter patterns
            for pattern in chapter_patterns:
                match = re.match(pattern, line)
                if match:
                    if len(match.groups()) >= 3:
                        chapter_num, title, page = match.groups()
                        analysis['patterns_found']['chapters'].append({
                            'source_page': page_num,
                            'source_line': line_num + 1,
                            'number': chapter_num,
                            'title': title.strip(),
                            'page': page,
                            'raw_line': line
                        })
                        analysis['numbering_styles'].add(f"chapter_{pattern}")
                        break
            
            # Try to match section patterns
            for pattern in section_patterns:
                match = re.match(pattern, line)
                if match:
                    if len(match.groups()) >= 3:
                        section_num, title, page = match.groups()
                        level = len(section_num.split('.')) - 1
                        analysis['patterns_found']['sections'].append({
                            'source_page': page_num,
                            'source_line': line_num + 1,
                            'number': section_num,
                            'title': title.strip(),
                            'page': page,
                            'level': level,
                            'raw_line': line
                        })
                        analysis['numbering_styles'].add(f"section_{pattern}")
                        break
            
            # Try to match appendix patterns
            for pattern in appendix_patterns:
                match = re.match(pattern, line)
                if match:
                    if len(match.groups()) >= 3:
                        app_letter, title, page = match.groups()
                        analysis['patterns_found']['appendices'].append({
                            'source_page': page_num,
                            'source_line': line_num + 1,
                            'letter': app_letter,
                            'title': title.strip(),
                            'page': page,
                            'raw_line': line
                        })
                        analysis['numbering_styles'].add(f"appendix_{pattern}")
                        break
            
            # Try to match front matter patterns
            for pattern in front_matter_patterns:
                match = re.match(pattern, line)
                if match:
                    groups = match.groups()
                    if len(groups) >= 2:
                        title, page = groups
                        analysis['patterns_found']['front_matter'].append({
                            'source_page': page_num,
                            'source_line': line_num + 1,
                            'title': title.strip(),
                            'page': page,
                            'raw_line': line
                        })
                        break
            
            # Collect page references (any number at end of line)
            page_ref_match = re.search(r'\s+(\d+)$', line)
            if page_ref_match:
                analysis['page_references'].append({
                    'source_page': page_num,
                    'line': line,
                    'page_ref': page_ref_match.group(1)
                })
    
    # Summary statistics
    for category, entries in analysis['patterns_found'].items():
        count = len(entries)
        if count > 0:
            print_progress(f"+ Found {count} {category} entries")
    
    return analysis


def generate_text_analysis_report(analysis, output_file):
    """
    Generate a comprehensive text analysis report.
    
    Args:
        analysis (dict): Analysis results
        output_file (str): Output file path
    """
    print_progress("Generating text analysis report...")
    
    lines = []
    lines.append("# TOC Text Extraction Analysis")
    lines.append("")
    lines.append(f"**Pages processed:** {analysis['pages_processed']}")
    lines.append(f"**Total lines analyzed:** {analysis['total_lines']}")
    lines.append("")
    
    # Summary by category
    lines.append("## Summary by Category")
    lines.append("")
    for category, entries in analysis['patterns_found'].items():
        count = len(entries)
        lines.append(f"- **{category.title()}:** {count} entries")
    lines.append("")
    
    # Detailed entries
    for category, entries in analysis['patterns_found'].items():
        if not entries:
            continue
            
        lines.append(f"## {category.title()}")
        lines.append("")
        
        for entry in entries:
            if category == 'chapters':
                lines.append(f"- **Chapter {entry['number']}**: {entry['title']} (page {entry['page']})")
            elif category == 'sections':
                indent = "  " * entry.get('level', 1)
                lines.append(f"{indent}- **{entry['number']}** {entry['title']} (page {entry['page']})")
            elif category == 'appendices':
                lines.append(f"- **Appendix {entry['letter']}**: {entry['title']} (page {entry['page']})")
            elif category == 'front_matter':
                lines.append(f"- **{entry['title']}** (page {entry['page']})")
            
            lines.append(f"  - *Source: Page {entry['source_page']}, Line {entry['source_line']}*")
            lines.append(f"  - *Raw: `{entry['raw_line']}`*")
            lines.append("")
    
    # Pattern analysis
    lines.append("## Pattern Analysis")
    lines.append("")
    lines.append("**Numbering styles detected:**")
    for style in sorted(analysis['numbering_styles']):
        lines.append(f"- {style}")
    lines.append("")
    
    lines.append(f"**Total page references found:** {len(analysis['page_references'])}")
    lines.append("")
    
    # Raw text samples
    lines.append("## Sample Page References")
    lines.append("")
    for ref in analysis['page_references'][:10]:  # Show first 10
        lines.append(f"- Page {ref['source_page']}: `{ref['line']}` → Page {ref['page_ref']}")
    
    if len(analysis['page_references']) > 10:
        remaining = len(analysis['page_references']) - 10
        lines.append(f"- ... and {remaining} more references")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by text-based TOC extraction*")
    
    # Save report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print_progress(f"+ Report saved to {output_file}")


def main():
    """
    Main function for text-based TOC extraction.
    """
    parser = argparse.ArgumentParser(
        description='Extract and analyze TOC structure from PDF text'
    )
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('start_page', type=int, help='Starting page number')
    parser.add_argument('end_page', type=int, help='Ending page number')
    parser.add_argument('output_file', help='Output analysis file')
    
    args = parser.parse_args()
    
    if not Path(args.pdf_path).exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        return 1
    
    print_section_header("TEXT-BASED TOC EXTRACTION")
    print(f"Input PDF: {args.pdf_path}")
    print(f"Pages: {args.start_page}-{args.end_page}")
    print(f"Output file: {args.output_file}")
    print("=" * 60)
    
    try:
        # Extract text from PDF
        text_by_page = extract_text_from_pdf(args.pdf_path, args.start_page, args.end_page)
        
        if not text_by_page:
            print("ERROR: Could not extract text from PDF")
            print("Make sure you have: pip install PyMuPDF pdfplumber")
            return 1
        
        # Analyze TOC patterns
        analysis = analyze_toc_patterns(text_by_page)
        
        # Generate report
        generate_text_analysis_report(analysis, args.output_file)
        
        print("=" * 60)
        print("TEXT ANALYSIS COMPLETE")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print_progress(f"- Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
#!/usr/bin/env python3
"""
Debug script to test PDF text extraction and see exactly what text is captured.
"""

import sys
import os
from pathlib import Path

# Import the text extraction functions from convert_with_context
from convert_with_context import extract_pdf_text_by_pages
from pdf_utils import extract_text_from_pdf_page

def debug_text_extraction(pdf_path, start_page=41, end_page=42):
    """Debug text extraction for specific pages."""
    
    print("="*60)
    print("PDF TEXT EXTRACTION DEBUG")
    print("="*60)
    print(f"PDF: {pdf_path}")
    print(f"Testing pages: {start_page}-{end_page}")
    print()
    
    # Test individual page extraction
    for page_num in range(start_page, end_page + 1):
        print(f"=== PAGE {page_num} INDIVIDUAL EXTRACTION ===")
        page_text = extract_text_from_pdf_page(pdf_path, page_num)
        if page_text:
            print(f"Text length: {len(page_text)} characters")
            print("First 500 characters:")
            print("-" * 40)
            print(page_text[:500])
            print("-" * 40)
            print("Last 500 characters:")
            print("-" * 40)
            print(page_text[-500:] if len(page_text) > 500 else page_text)
            print("-" * 40)
            
            # Look for the specific missing sentence
            missing_sentence = "As the boundary layer formulation are related to the SHIE and the DSHIE"
            if missing_sentence.lower() in page_text.lower():
                print("✅ FOUND: Missing sentence is present in extracted text!")
                # Find the context around it
                text_lower = page_text.lower()
                pos = text_lower.find(missing_sentence.lower())
                context_start = max(0, pos - 100)
                context_end = min(len(page_text), pos + len(missing_sentence) + 100)
                print("Context around missing sentence:")
                print(">" * 40)
                print(page_text[context_start:context_end])
                print("<" * 40)
            else:
                print("❌ NOT FOUND: Missing sentence not in extracted text")
                
            # Look for keywords
            keywords = ["SHIE", "DSHIE", "Burton", "Miller", "hybrid formulation", "boundary layer"]
            found_keywords = []
            for keyword in keywords:
                if keyword.lower() in page_text.lower():
                    found_keywords.append(keyword)
            print(f"Keywords found: {found_keywords}")
            
        else:
            print("❌ No text extracted from this page")
        print()
    
    # Test the full extraction function used by the system
    print("=== FULL SYSTEM EXTRACTION (extract_pdf_text_by_pages) ===")
    full_text = extract_pdf_text_by_pages(pdf_path)
    if full_text:
        print(f"Total text length: {len(full_text)} characters")
        
        # Check if our missing sentence is in the full extraction
        missing_sentence = "As the boundary layer formulation are related to the SHIE and the DSHIE"
        if missing_sentence.lower() in full_text.lower():
            print("✅ FOUND: Missing sentence is in full system extraction!")
        else:
            print("❌ NOT FOUND: Missing sentence not in full system extraction")
            
        # Show what text appears around pages 41-42
        page_41_marker = "=== PAGE 41 ==="
        page_42_marker = "=== PAGE 42 ==="
        
        if page_41_marker in full_text:
            pos_41 = full_text.find(page_41_marker)
            if page_42_marker in full_text:
                pos_42 = full_text.find(page_42_marker)
                pages_41_42_text = full_text[pos_41:pos_42 + 500]
            else:
                pages_41_42_text = full_text[pos_41:pos_41 + 1000]
            
            print("Text from pages 41-42 section:")
            print(">" * 60)
            print(pages_41_42_text)
            print("<" * 60)
        else:
            print("Could not find page 41 marker in full text")
    else:
        print("❌ Full system extraction returned no text")

def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_text_extraction.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    debug_text_extraction(pdf_path)

if __name__ == "__main__":
    main()
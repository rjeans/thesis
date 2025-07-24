#!/usr/bin/env python3
"""
Debug script to check if images are embedded in the PDF and how they can be extracted.
"""

import sys
from pathlib import Path

def check_pdf_images(pdf_path):
    """Check what images are available in the PDF for extraction."""
    
    print("="*60)
    print("PDF IMAGE EXTRACTION DEBUG")
    print("="*60)
    print(f"PDF: {pdf_path}")
    print()
    
    # Try PyMuPDF (fitz) first
    try:
        import fitz
        print("✅ PyMuPDF (fitz) available")
        
        doc = fitz.open(pdf_path)
        total_images = 0
        
        print(f"Total pages: {len(doc)}")
        print()
        
        # Check pages around figures (based on your test - pages 41-42 area)
        test_pages = [41, 42, 43, 44, 45]  # Around where figures should be
        
        for page_num in test_pages:
            if page_num <= len(doc):
                page = doc[page_num - 1]  # fitz uses 0-based indexing
                image_list = page.get_images()
                
                print(f"=== PAGE {page_num} ===")
                print(f"Number of embedded images: {len(image_list)}")
                
                if image_list:
                    for img_index, img in enumerate(image_list):
                        # img is a tuple: (xref, smask, width, height, bpc, colorspace, alt, name, filter, bbox)
                        xref = img[0]
                        width = img[2]
                        height = img[3]
                        bbox = img[9] if len(img) > 9 else None
                        
                        print(f"  Image {img_index + 1}:")
                        print(f"    Size: {width}x{height}")
                        print(f"    XRef: {xref}")
                        if bbox:
                            print(f"    BBox: {bbox}")
                        
                        # Try to get more details about the image
                        try:
                            pix = fitz.Pixmap(doc, xref)
                            print(f"    Colorspace: {pix.colorspace}")
                            print(f"    Has alpha: {pix.alpha}")
                            print(f"    Samples: {pix.samples}")
                            pix = None  # Clean up
                        except Exception as e:
                            print(f"    Could not get pixmap details: {e}")
                        
                        total_images += 1
                else:
                    print("  No embedded images found")
                print()
        
        print(f"SUMMARY: Found {total_images} embedded images in test pages")
        doc.close()
        
    except ImportError:
        print("❌ PyMuPDF (fitz) not available")
        
    # Try alternative approach with PDF2Image + PIL
    try:
        from pdf2image import convert_from_path
        from PIL import Image
        import numpy as np
        
        print("\n" + "="*40)
        print("ALTERNATIVE: PAGE RENDERING APPROACH")
        print("="*40)
        
        # Convert a test page to see what we get
        test_page = 42  # Page with figure 2.5
        print(f"Rendering page {test_page} to analyze...")
        
        pages = convert_from_path(pdf_path, first_page=test_page, last_page=test_page, dpi=200)
        if pages:
            page_img = pages[0]
            print(f"Page rendered as: {page_img.size[0]}x{page_img.size[1]} image")
            print(f"Mode: {page_img.mode}")
            
            # Convert to numpy for analysis
            img_array = np.array(page_img)
            print(f"Image array shape: {img_array.shape}")
            
            # Basic analysis of the image
            if len(img_array.shape) == 3:
                # Color image
                print("Color channels detected")
                # Check if it's mostly black/white (good for line art)
                gray = np.mean(img_array, axis=2)
                unique_values = len(np.unique(gray))
                print(f"Unique gray values: {unique_values}")
                if unique_values < 20:
                    print("→ Looks like mostly black/white content (good for line art)")
                else:
                    print("→ Has gradual tones")
            
    except ImportError as e:
        print(f"❌ pdf2image/PIL not available: {e}")
    
    print("\n" + "="*60)
    print("RECOMMENDATIONS:")
    
    if total_images > 0:
        print("✅ PDF contains embedded images - can extract directly")
        print("→ Use fitz image extraction for high quality")
        print("→ Images are likely the original figure sources")
    else:
        print("❌ No embedded images found - figures are probably vector/text")
        print("→ Use page rendering + crop approach")
        print("→ Need to detect figure boundaries programmatically")
    
    print("="*60)

def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_pdf_images.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    check_pdf_images(pdf_path)

if __name__ == "__main__":
    main()
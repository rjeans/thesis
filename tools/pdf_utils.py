#!/usr/bin/env python3
"""
PDF processing utilities for thesis conversion workflow.

This module provides common PDF manipulation functions including:
- Page extraction to create chapter PDFs
- PDF to PNG image conversion for GPT-4 Vision API
- Support for multiple PDF tools (pdftk, qpdf, ghostscript)
"""

import subprocess
from pathlib import Path
import time
from progress_utils import print_progress


def extract_pages_to_pdf(input_pdf, output_pdf, start_page, end_page):
    """
    Extract a page range from PDF to create a new PDF file.
    
    Tries multiple PDF tools in order of preference:
    1. pdftk (fastest, most reliable)
    2. qpdf (good alternative)
    3. ghostscript (universal fallback)
    
    Args:
        input_pdf (str): Path to source PDF file
        output_pdf (str): Path for output PDF file
        start_page (int): First page to extract (1-based)
        end_page (int): Last page to extract (1-based)
        
    Returns:
        bool: True if extraction succeeded, False otherwise
    """
    input_path = Path(input_pdf).resolve()
    output_path = Path(output_pdf).resolve()
    
    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print_progress(f"Extracting pages {start_page}-{end_page} from {input_path.name}")
    print_progress(f"Output: {output_path}")
    
    # Try pdftk first (fastest and most reliable)
    if _try_pdftk_extract(input_path, output_path, start_page, end_page):
        return True
    
    # Fallback to qpdf
    if _try_qpdf_extract(input_path, output_path, start_page, end_page):
        return True
    
    # Fallback to ghostscript
    if _try_ghostscript_extract(input_path, output_path, start_page, end_page):
        return True
    
    print_progress("- No PDF extraction tool found (tried pdftk, qpdf, ghostscript)")
    return False


def pdf_to_images(pdf_path, temp_dir="/tmp/chapter_conversion", dpi=200, page_prefix="page"):
    """
    Convert PDF pages to PNG images for GPT-4 Vision processing.
    
    Uses pdftoppm to create high-quality PNG images from PDF pages.
    Each page becomes a separate PNG file with sequential numbering.
    
    Args:
        pdf_path (str): Path to input PDF file
        temp_dir (str): Directory for temporary image files
        dpi (int): Resolution for image conversion (default 200)
        page_prefix (str): Prefix for generated image filenames
        
    Returns:
        list: Sorted list of Path objects for generated PNG files
    """
    print_progress(f"Converting PDF to images (DPI: {dpi})...")
    
    temp_path = Path(temp_dir)
    temp_path.mkdir(parents=True, exist_ok=True)
    
    # Build pdftoppm command
    cmd = [
        'pdftoppm',
        '-png',              # Output format
        '-r', str(dpi),      # Resolution
        str(pdf_path),       # Input PDF
        str(temp_path / page_prefix)  # Output prefix
    ]
    
    try:
        start_time = time.time()
        subprocess.run(cmd, check=True, capture_output=True)
        convert_time = time.time() - start_time
        
        # Find all generated images
        images = sorted(temp_path.glob(f"{page_prefix}-*.png"))
        print_progress(f"+ Converted to {len(images)} images in {convert_time:.1f}s")
        return images
        
    except subprocess.CalledProcessError as e:
        print_progress(f"- PDF to image conversion failed: {e}")
        return []
    except FileNotFoundError:
        print_progress("- pdftoppm not found - install poppler-utils")
        return []


def extract_pages_to_images(pdf_path, start_page, end_page, temp_dir, dpi=200, page_prefix="page"):
    """
    Extract specific page range from PDF and convert to images.
    
    Combines page extraction with image conversion for TOC parsing workflows.
    
    Args:
        pdf_path (str): Path to source PDF file
        start_page (int): First page to extract (1-based)
        end_page (int): Last page to extract (1-based)
        temp_dir (str): Directory for temporary image files
        dpi (int): Image resolution (default 200)
        page_prefix (str): Prefix for generated image filenames
        
    Returns:
        list: Sorted list of Path objects for generated PNG files
    """
    print_progress(f"Extracting pages {start_page}-{end_page} from PDF...")
    
    temp_path = Path(temp_dir)
    temp_path.mkdir(parents=True, exist_ok=True)
    
    # Build pdftoppm command with page range
    cmd = [
        'pdftoppm',
        '-png',
        '-r', str(dpi),
        '-f', str(start_page),  # First page
        '-l', str(end_page),    # Last page
        str(pdf_path),
        str(temp_path / page_prefix)
    ]
    
    try:
        start_time = time.time()
        subprocess.run(cmd, check=True, capture_output=True)
        extract_time = time.time() - start_time
        
        images = sorted(temp_path.glob(f"{page_prefix}-*.png"))
        print_progress(f"+ Extracted {len(images)} pages in {extract_time:.1f}s")
        return images
        
    except subprocess.CalledProcessError as e:
        print_progress(f"- Error extracting pages: {e}")
        return []


def _try_pdftk_extract(input_path, output_path, start_page, end_page):
    """Try extracting pages using pdftk."""
    try:
        cmd = ['pdftk', str(input_path), 'cat', f'{start_page}-{end_page}', 'output', str(output_path)]
        subprocess.run(cmd, check=True, capture_output=True)
        print_progress("+ Pages extracted using pdftk")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _try_qpdf_extract(input_path, output_path, start_page, end_page):
    """Try extracting pages using qpdf."""
    try:
        cmd = ['qpdf', '--pages', str(input_path), f'{start_page}-{end_page}', '--', str(output_path)]
        subprocess.run(cmd, check=True, capture_output=True)
        print_progress("+ Pages extracted using qpdf")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _try_ghostscript_extract(input_path, output_path, start_page, end_page):
    """Try extracting pages using ghostscript."""
    try:
        cmd = [
            'gs', '-sDEVICE=pdfwrite', '-dNOPAUSE', '-dBATCH', '-dSAFER',
            f'-dFirstPage={start_page}', f'-dLastPage={end_page}',
            f'-sOutputFile={output_path}', str(input_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print_progress("+ Pages extracted using ghostscript")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def extract_text_from_pdf_page(pdf_path, page_num):
    """
    Extract text from a single PDF page for guidance and validation.
    
    Uses multiple PDF text extraction libraries as fallbacks:
    1. PyMuPDF (fitz) - fastest and most accurate
    2. pdfplumber - good fallback with table support
    3. pypdf - universal fallback
    
    Args:
        pdf_path (str): Path to PDF file
        page_num (int): Page number (1-based)
        
    Returns:
        str: Extracted text from the page, or empty string if failed
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        if page_num - 1 < len(doc):
            page = doc.load_page(page_num - 1)  # Convert to 0-based
            text = page.get_text()
            doc.close()
            return text.strip()
        doc.close()
    except ImportError:
        pass
    
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            if page_num - 1 < len(pdf.pages):
                page = pdf.pages[page_num - 1]  # Convert to 0-based
                text = page.extract_text() or ""
                return text.strip()
    except ImportError:
        pass
    
    try:
        import pypdf
        with open(pdf_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            if page_num - 1 < len(pdf_reader.pages):
                page = pdf_reader.pages[page_num - 1]
                text = page.extract_text()
                return text.strip()
    except ImportError:
        pass
    
    return ""
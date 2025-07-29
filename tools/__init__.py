"""
Thesis Conversion Tools Package

This package provides utilities for converting a 1992 PhD thesis PDF
to markdown format using GPT-4 Vision API.

Main modules:
- pdf_utils: PDF extraction and image conversion
- progress_utils: Progress tracking and reporting 
- gpt_vision_utils: GPT-4 Vision API interfaces
- yaml_utils: YAML processing and validation

Main scripts:
- extract_chapter_pdf.py: Extract page ranges to create chapter PDFs
- convert_chapter_pdf.py: Convert chapter PDFs to markdown
- parse_toc_contents.py: Parse table of contents structure
- parse_toc_figures.py: Parse figures list
- parse_toc_tables.py: Parse tables list
"""

__version__ = "1.0.0"
__author__ = "Thesis Conversion Project"
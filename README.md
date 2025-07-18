# PhD Thesis Conversion Project

Converting my 1992 PhD thesis from PDF to Markdown using modern AI tools.

## Overview

This project converts a scanned PDF thesis into clean, readable Markdown format suitable for modern publishing platforms. The thesis contains complex mathematical equations, technical diagrams, and 1990s LaTeX typesetting that requires specialized handling.

## Project Structure

- `original/` - Original PDF thesis (Richard_Jeans-1992-PhD-Thesis.pdf)
- `chapters/` - Converted markdown chapters
- `images/` - Extracted figures and diagrams  
- `tools/` - Conversion scripts and utilities

## Tools

### Core Conversion Tools
- `test_gpt4_vision.py` - **Primary tool**: GPT-4 Vision for text and equation extraction
- `validate_markdown.py` - KaTeX math validation for markdown output
- `extract_figures_imagemagick.py` - Figure extraction using ImageMagick
- `gpt_figure_locator_percentage.py` - Experimental AI-powered figure location

### Test Files
- `tools/test_samples/test_page-042.png` - Sample page for testing
- `tools/test_samples/gpt4_vision_result.md` - Example GPT-4 Vision output

## Workflow

1. **Text Extraction**: Use GPT-4 Vision to convert page images to markdown with proper LaTeX math
2. **Figure Extraction**: Manual extraction of diagrams and figures (AI approaches tested but manual proved most reliable)
3. **Validation**: Use validation tools to check KaTeX math rendering
4. **Assembly**: Combine chapters into complete thesis

## Key Findings

- **GPT-4 Vision** excels at converting mathematical content and preserving document structure
- **Manual figure extraction** is more reliable than automated approaches for 1992 LaTeX documents
- **Proper equation formatting** requires specific attention to KaTeX compatibility

## Status

- [x] Text extraction workflow established
- [x] Math equation formatting solved
- [x] Validation tools created
- [ ] Figure extraction approach finalized
- [ ] Batch processing of full thesis
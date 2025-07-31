# PhD Thesis Conversion Project

Converting my 1992 PhD thesis from PDF to Markdown using a sophisticated, AI-powered workflow that combines vision-based parsing with robust, deterministic code for 100% accurate table of contents (TOC) extraction and document structuring.

## Overview

This project converts a scanned 215-page PDF thesis into clean, readable Markdown. The core challenge is accurately parsing the TOC to reconstruct the document's hierarchical structure, which is essential for all subsequent processing steps.

**Key Innovation**: A hybrid approach that uses GPT-4 Vision for what it excels at—visual pattern recognition—and robust Python code for what it does best: deterministic logic and calculation. This ensures a complete and accurate TOC structure, which is the foundation of the entire conversion process.

**Production Status**: The TOC parsing and document structuring workflow is now considered complete and production-ready. The system correctly handles all edge cases, including sections that span page boundaries and complex hierarchical relationships.

## Project Structure

- `original/` - Original PDF thesis (Richard_Jeans-1992-PhD-Thesis.pdf)
- `structure/` - YAML structure files generated from TOC parsing
- `markdown_output/` - Final markdown files with modern HTML anchors
 - `assets/` - Dual-theme figure assets (light/dark with transparency)
- `tools/` - Conversion scripts and utilities with abstract base class architecture

## The TOC Parsing Solution: A Hybrid Approach

The key to successfully parsing the TOC is a sophisticated, multi-stage process that intelligently divides the labor between AI and code:

1.  **AI for Visual Extraction (Per-Page):**
    *   The `parse_toc_contents.py` script processes each page of the TOC individually.
    *   For each page, it uses GPT-4 Vision to extract the raw TOC entries exactly as they appear. The AI's task is kept simple and focused: recognize text and its basic hierarchy on a single page. This has proven to be the most reliable way to handle the visual layout of the TOC.

2.  **Intelligent Code for Stitching and Merging:**
    *   After collecting the raw data from all pages, a new, context-aware Python function intelligently stitches the sections together.
    *   It keeps track of the last "active" chapter and correctly appends subsections to it, even if they appear on a different page. This solves the problem of missing or duplicated sections at page boundaries.

3.  **Deterministic Code for Page Range Calculation:**
    *   Once the complete, correct hierarchy is reassembled, a final Python function, `calculate_section_page_ranges`, calculates the `end_page` for every entry.
    *   It does this by creating a flat list of all sections and subsections, sorted by their `start_page`, and then sets the `end_page` of each entry to be the `start_page` of the next entry, minus one. This is a deterministic and 100% reliable method.

This hybrid approach is the key to the success of the project. It leverages the strengths of both AI and traditional code, resulting in a robust and accurate solution.

## Installation

### Prerequisites
- Python 3.x with packages: `openai`, `pyyaml`, `Pillow`, `numpy`, `PyMuPDF`
- OpenAI API key: `export OPENAI_API_KEY='your-api-key'`
- PDF processing tools (install at least one):
 - `pdftk` (recommended - fastest)
 - `qpdf` (good alternative)
 - `ghostscript` (universal fallback)
- Image processing: `poppler-utils` (for pdftoppm command)
- Figure extraction: `PyMuPDF` (fitz) for embedded image processing

### Setup
```bash
# Install Python dependencies
pip install openai pyyaml Pillow numpy PyMuPDF

# Install PDF tools (macOS with Homebrew)
brew install pdftk poppler

# Install PDF tools (Ubuntu/Debian)
sudo apt-get install pdftk poppler-utils qpdf ghostscript

# Set OpenAI API key
export OPENAI_API_KEY='your-api-key'
```

## Production Workflow 

### Phase 1: Structure Generation (One-time setup)

Extract the complete thesis structure to enable intelligent content discovery:

```bash
cd tools

# Parse main chapter/section structure
python3 parse_toc_contents.py "../original/Richard_Jeans-1992-PhD-Thesis.pdf" 9 12 "../structure/"

# Parse figures catalog
python3 parse_toc_figures.py "../original/Richard_Jeans-1992-PhD-Thesis.pdf" 13 15 "../structure/"

# Parse tables catalog
python3 parse_toc_tables.py "../original/Richard_Jeans-1992-PhD-Thesis.pdf" 17 17 "../structure/"
```

**Generated Structure Files:**
- `structure/thesis_contents.yaml` - Complete chapter hierarchy and page ranges
- `structure/thesis_figures.yaml` - Figure catalog with cross-references
- `structure/thesis_tables.yaml` - Table catalog with cross-references

### Phase 2: Content Processing

Process all content using the generated structure files:

```bash
# Process main chapters
python3 chapter_processor.py "../original/Richard_Jeans-1992-PhD-Thesis.pdf" "Chapter 1" \
 "../markdown_output/chapter_1.md" --structure-dir "../structure/"

# ... and so on for all chapters, appendices, etc.
```

## Conclusion

The successful implementation of the TOC parsing workflow is a major milestone for this project. By combining the strengths of AI and deterministic code, we have created a robust and reliable solution that can accurately reconstruct the structure of a complex academic document. This provides a solid foundation for the next phases of the project, which will focus on content extraction and conversion.

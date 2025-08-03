# PhD Thesis Conversion Project

Converting my 1992 PhD thesis from PDF to Markdown using a sophisticated, AI-powered workflow that combines vision-based parsing with robust, deterministic code for 100% accurate table of contents (TOC) extraction and document structuring.

## Overview

This project converts a scanned 215-page PDF thesis into clean, readable Markdown. The core challenge is accurately parsing the TOC to reconstruct the document's hierarchical structure, which is essential for all subsequent processing steps.

**Key Innovation**: A hybrid approach that uses GPT-4 Vision for what it excels at—visual pattern recognition—and robust Python code for what it does best: deterministic logic and calculation. This ensures a complete and accurate TOC structure, which is the foundation of the entire conversion process.

**Production Status**: The entire thesis conversion workflow is now production-ready with simplified architecture, enhanced token capacity, and comprehensive automation. The system includes automated post-processing to fix common GPT-4 formatting issues, making it fully autonomous and reliable.

## Major Architectural Improvements

### ✅ Simplified Architecture
- **Removed complex batch processing** - each section now processed as a complete logical unit
- **Single-responsibility tools** - clean separation between individual processing and batch orchestration
- **Enhanced token capacity** - increased from 3,000 to 16,000 tokens for complete section processing
- **Unified prompt system** - all prompts consolidated in `prompt_utils.py` for consistency

### ✅ Enhanced Quality Assurance
- **Automated equation formatting** - fixes multi-line equations and incorrect delimiters
- **Prompt leakage detection** - automatic removal of processing instructions from output
- **Table structure preservation** - maintains original table orientation and column/row relationships  
- **Section-aware naming** - figures and tables use correct prefixes (A2-1.png for appendices)

### ✅ Production-Ready Workflow
- **Individual file processing** - each section creates separate files for editing
- **File management** - copies individual files to thesis directory for publication
- **Debug transparency** - saves prompts, text context, and processing diagnostics
- **Comprehensive error handling** - robust error recovery and detailed progress reporting

## Project Structure

- `original/` - Original PDF thesis (Richard_Jeans-1992-PhD-Thesis.pdf)
- `structure/` - YAML structure files generated from TOC parsing
- `markdown/` - Individual section markdown files with modern HTML anchors
- `thesis/` - Final concatenated thesis files (one per high-level section)
- `tools/` - Conversion scripts with unified prompt architecture and section-aware processing

## Installation

### Prerequisites
- Python 3.x with packages: `openai`, `pyyaml`, `Pillow`, `numpy`, `PyMuPDF`
- OpenAI API key: `export OPENAI_API_KEY='your-api-key'`
- PDF processing tools (install at least one):
  - `pdftk` (recommended - fastest)
  - `qpdf` (good alternative)  
  - `ghostscript` (universal fallback)
- Image processing: `poppler-utils` (for pdftoppm command)

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
python3 parse_toc_contents.py --input "../original/Richard_Jeans-1992-PhD-Thesis.pdf" --start-page 9 --end-page 12 --output "../structure/"

# Parse figures catalog
python3 parse_toc_figures.py --input "../original/Richard_Jeans-1992-PhD-Thesis.pdf" --start-page 13 --end-page 15 --output "../structure/"

# Parse tables catalog
python3 parse_toc_tables.py --input "../original/Richard_Jeans-1992-PhD-Thesis.pdf" --start-page 17 --end-page 17 --output "../structure/"
```

**Generated Structure Files:**
- `structure/thesis_contents.yaml` - Complete chapter hierarchy and page ranges
- `structure/thesis_figures.yaml` - Figure catalog with cross-references  
- `structure/thesis_tables.yaml` - Table catalog with cross-references

### Phase 2: Hierarchical Content Processing

#### Option 1: Individual Section Processing (Recommended)
```bash
# Process complete section 
python3 section_processor.py \
  --input "../original/Richard_Jeans-1992-PhD-Thesis.pdf" \
  --section "A2" \
  --output "../markdown/Appendix_2.md" \
  --structure "../structure/thesis_contents.yaml" \
  --debug

# Process specific subsection only
python3 section_processor.py \
  --input "../original/Richard_Jeans-1992-PhD-Thesis.pdf" \
  --section "A2.1" \
  --output "../markdown/Section_A2_1.md" \
  --structure "../structure/thesis_contents.yaml"

# Process main chapter
python3 section_processor.py \
  --input "../original/Richard_Jeans-1992-PhD-Thesis.pdf" \
  --section "2" \
  --output "../markdown/Chapter_2.md" \
  --structure "../structure/thesis_contents.yaml"
```

#### Option 2: Batch Processing with File Management
```bash
# Generate all sections with individual + copied output
python3 generate_thesis_sections.py \
  --input "../original/Richard_Jeans-1992-PhD-Thesis.pdf" \
  --structure "../structure/thesis_contents.yaml" \
  --output "../markdown/" \
  --thesis "../thesis/" \
  --debug

# Generate specific sections only
python3 generate_thesis_sections.py \
  --input "../original/Richard_Jeans-1992-PhD-Thesis.pdf" \
  --structure "../structure/thesis_contents.yaml" \
  --output "../markdown/" \
  --thesis "../thesis/" \
  --section-numbers A1 A2 \
  --debug
```

### Phase 3: Figure Extraction
```bash
# Extract all figures with dual-theme support
python3 extract_thesis_figures.py \
  --input "../original/Richard_Jeans-1992-PhD-Thesis.pdf" \
  --figures "../structure/thesis_figures.yaml" \
  --output "../markdown/assets/"

# Extract specific figure
python3 extract_thesis_figures.py \
  --input "../original/Richard_Jeans-1992-PhD-Thesis.pdf" \
  --figures "../structure/thesis_figures.yaml" \
  --output "../markdown/assets/" \
  --figure "A2.1"
```

## Key Features

### Simplified Section Processing
- **Complete section processing**: Each section processed as single logical unit
- **Enhanced token capacity**: 16,000 tokens to handle complete sections without truncation
- **Intelligent mode detection**: Automatically handles parent sections vs. complete sections
- **Section-aware naming**: Ensures correct figure/table prefixes (A2-1.png for appendices)

### Enhanced Quality Assurance
- **Automated equation formatting**: Converts multi-line equations to single-line format
- **Prompt leakage detection**: Automatic removal of processing instructions from output
- **Table structure preservation**: Maintains original table orientation and relationships
- **Comprehensive validation**: Real-time detection and correction of formatting issues

### Production-Ready Architecture
- **Unified prompt system**: All prompts consolidated in `prompt_utils.py` for consistency
- **Debug transparency**: Saves prompts, text context, and processing diagnostics
- **Clean architecture**: Single-responsibility tools with clear separation of concerns
- **Error recovery**: Robust handling of API failures and processing errors

## Output Structure

The workflow generates two sets of files:

### Individual Section Files (`markdown/`)
- Each section as separate file (e.g., `Appendix_2.md`, `Section_A2_1.md`)
- Useful for individual editing and review
- Contains complete debug information when `--debug` enabled

### Thesis Directory Files (`thesis/`)  
- Copies of individual section files for publication workflow
- Organized for final document assembly
- Maintains proper section hierarchy and cross-references

## Troubleshooting

### Common Issues
1. **Token limits exceeded**: Use section-specific processing instead of entire chapters
2. **Missing figures**: Ensure figure YAML structure is correctly generated
3. **Equation formatting**: Enable debug mode to inspect equation post-processing
4. **Table structure**: Check that original table orientation is preserved

### Debug Mode
Enable `--debug` flag for comprehensive diagnostics:
- Saves processing prompts for each section
- Exports text context used for guidance  
- Provides detailed concatenation logging
- Shows equation formatting corrections

## The TOC Parsing Solution: A Hybrid Approach

The key to successfully parsing the TOC is a sophisticated, multi-stage process that intelligently divides the labor between AI and code:

1. **AI for Visual Extraction (Per-Page):**
   - The `parse_toc_contents.py` script processes each page of the TOC individually
   - GPT-4 Vision extracts raw TOC entries exactly as they appear
   - Focused task: recognize text and basic hierarchy on a single page

2. **Intelligent Code for Stitching and Merging:**
   - Context-aware Python function intelligently stitches sections together
   - Tracks the last "active" chapter and correctly appends subsections
   - Solves missing or duplicated sections at page boundaries

3. **Deterministic Code for Page Range Calculation:**
   - Final Python function calculates `end_page` for every entry
   - Creates flat list sorted by `start_page` and calculates ranges
   - 100% reliable and deterministic method

This hybrid approach leverages the strengths of both AI and traditional code, resulting in a robust and accurate solution that serves as the foundation for the entire conversion process.
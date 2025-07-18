# Converting a 1992 PhD Thesis to Markdown: An AI-Powered Journey

I recently decided to convert my 1992 PhD thesis from its original scanned PDF format into clean, searchable Markdown. What started as a simple digitization project became an interesting exploration of modern AI tools for document conversion.

## The Challenge

The thesis exists as a scanned PDF - a 200+ page document with:
- Complex mathematical equations in 1990s LaTeX formatting
- Technical diagrams and figures
- High-resolution scans (17089×25139 pixels per page)
- Varying scan quality and typography quirks

Traditional OCR tools struggle with mathematical notation and fail to preserve the semantic structure of academic documents.

## The Approach

### Phase 1: Text Extraction
I experimented with several approaches:

1. **Traditional OCR** (Tesseract) - Poor results with mathematical notation
2. **Nougat** (Meta's academic paper OCR) - Better but still inconsistent  
3. **GPT-4 Vision** - Game changer for mathematical content

GPT-4 Vision proved exceptional at:
- Converting mathematical expressions to proper LaTeX markdown
- Preserving document structure (headings, sections, equation numbering)
- Understanding context and fixing OCR errors
- Handling complex equation formatting with proper KaTeX compatibility

### Phase 2: Figure Extraction - Lessons Learned

I initially tried several AI-powered approaches:
- GPT-4 Vision for figure location and cropping
- Automated bounding box detection
- Percentage-based coordinate systems

**Key Finding**: For 1992 LaTeX documents, **manual figure extraction proved most reliable**. The predictable document structure and high image quality make manual coordinate identification faster and more accurate than complex AI approaches.

### Phase 3: Validation and Quality Control

Created validation tools to ensure:
- KaTeX math rendering compatibility
- Proper equation formatting (avoiding newlines after `$$`)
- Correct equation numbering with `align*` and `\tag{}`

## Technical Solutions

### Math Formatting
- Use `$$equation$$` format (content on same line as delimiters)
- Numbered equations: `$$\begin{align*} equation \tag{2.5.1} \end{align*}$$`
- Validation script catches common KaTeX parsing errors

### Figure Extraction
- Convert high-res pages to workable resolution (1200px wide)
- Manual coordinate identification in image viewer
- Scale coordinates back to original resolution for extraction
- ImageMagick for precise cropping

### Document Structure
- Preserve exact academic formatting
- Maintain LaTeX equation structure
- Keep figure references and captions

## Results

The GPT-4 Vision approach has produced remarkably clean conversions with:
- Properly formatted mathematical equations compatible with modern renderers
- Preserved section structure and academic formatting  
- Minimal manual cleanup required
- High-quality figure extraction workflow established

## Key Takeaways

1. **GPT-4 Vision excels at mathematical content** - far superior to traditional OCR for academic documents
2. **Manual approaches can be optimal** - sometimes simpler is better than complex AI automation
3. **Validation is crucial** - small formatting issues can break math rendering
4. **Document-specific approaches work** - 1992 LaTeX has predictable patterns worth exploiting

## Tools Created

- `test_gpt4_vision.py` - Core GPT-4 Vision text extraction
- `validate_markdown.py` - KaTeX compatibility validation
- `extract_figures_imagemagick.py` - Manual figure extraction workflow

## Next Steps

- Batch process entire thesis using established workflow
- Create chapter-by-chapter conversion pipeline
- Publish as searchable, modern markdown thesis

The project demonstrates how combining AI tools with traditional approaches can solve complex document conversion challenges that neither could handle alone.

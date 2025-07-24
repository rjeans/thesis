#!/usr/bin/env python3
"""
Convert PDF chapters to markdown with enhanced context and PDF text guidance.

This script leverages YAML structure metadata to provide GPT-4 Vision with:
- Chapter structure and subsection hierarchy
- Expected figures and tables for cross-reference validation
- PDF text extraction for improved accuracy
- Content-type specific prompts for optimal conversion

Usage:
    python convert_with_context.py chapter2.pdf chapter2.md \
        --structure-dir structure/ \
        --chapter-name "Chapter 2"
        
    python convert_with_context.py abstract.pdf abstract.md \
        --structure-dir structure/ \
        --content-type front_matter
        
    python convert_with_context.py appendix_1.pdf appendix_1.md \
        --structure-dir structure/ \
        --content-type appendix

Features:
- Context-aware prompts with figure/table expectations
- PDF text guidance for better GPT-4 Vision accuracy
- Cross-reference validation and suggestions
- Content-type specific processing (chapters, front matter, appendices)
- Mathematical symbol formatting with selective approach
- Section structure preservation

Requires:
- YAML structure files from TOC parsing
- OpenAI API key in OPENAI_API_KEY environment variable
- poppler-utils for PDF processing
"""

import os
import openai
import argparse
import yaml
from pathlib import Path
import json

# Import common utilities
from pdf_utils import pdf_to_images, extract_text_from_pdf_page
from progress_utils import print_progress, print_section_header, print_completion_summary
from gpt_vision_utils import (
    encode_images_for_vision,
    call_gpt_vision_api,
    cleanup_temp_directory
)


def load_structure_data(structure_dir, chapter_name=None):
    """
    Load YAML structure files and extract relevant context.
    
    Args:
        structure_dir (Path): Directory containing YAML structure files
        chapter_name (str, optional): Specific chapter to find context for
        
    Returns:
        dict: Structure data with contents, figures, tables
    """
    structure_dir = Path(structure_dir)
    
    structure_data = {
        'contents': None,
        'figures': None,
        'tables': None,
        'chapter_info': None,
        'chapter_figures': [],
        'chapter_tables': []
    }
    
    # Load contents structure
    contents_file = structure_dir / "thesis_contents.yaml"
    if contents_file.exists():
        with open(contents_file, 'r', encoding='utf-8') as f:
            structure_data['contents'] = yaml.safe_load(f)
        print_progress(f"+ Loaded contents structure")
    
    # Load figures structure
    figures_file = structure_dir / "thesis_figures.yaml"
    if figures_file.exists():
        with open(figures_file, 'r', encoding='utf-8') as f:
            structure_data['figures'] = yaml.safe_load(f)
        print_progress(f"+ Loaded figures structure")
    
    # Load tables structure
    tables_file = structure_dir / "thesis_tables.yaml"
    if tables_file.exists():
        with open(tables_file, 'r', encoding='utf-8') as f:
            structure_data['tables'] = yaml.safe_load(f)
        print_progress(f"+ Loaded tables structure")
    
    # Find chapter-specific context
    if chapter_name and structure_data['contents']:
        structure_data['chapter_info'] = find_chapter_info(structure_data['contents'], chapter_name)
        
        if structure_data['chapter_info']:
            chapter_id = str(structure_data['chapter_info'].get('chapter_number', ''))
            
            # Find chapter-specific figures
            if structure_data['figures']:
                structure_data['chapter_figures'] = [
                    fig for fig in structure_data['figures']['figures']
                    if fig.get('chapter_id') == chapter_id
                ]
            
            # Find chapter-specific tables
            if structure_data['tables']:
                structure_data['chapter_tables'] = [
                    table for table in structure_data['tables']['tables']
                    if table.get('chapter_id') == chapter_id
                ]
            
            print_progress(f"+ Found context: {len(structure_data['chapter_figures'])} figures, {len(structure_data['chapter_tables'])} tables")
    
    return structure_data


def find_chapter_info(contents_data, chapter_name):
    """
    Find chapter information from contents structure.
    
    Args:
        contents_data (dict): Contents YAML data
        chapter_name (str): Chapter identifier
        
    Returns:
        dict or None: Chapter information if found
    """
    if not contents_data or 'sections' not in contents_data:
        return None
    
    chapter_lower = chapter_name.lower()
    
    for section in contents_data['sections']:
        # Match by chapter number
        if section.get('chapter_number'):
            chapter_num = str(section['chapter_number'])
            if chapter_lower in [chapter_num, f"chapter {chapter_num}", f"ch {chapter_num}"]:
                return section
        
        # Match by title
        title = section['title'].lower()
        if chapter_lower in title or title.replace('chapter ', '') in chapter_lower:
            return section
    
    return None


def extract_pdf_text_by_pages(pdf_path):
    """
    Extract text from all pages of a PDF for context guidance.
    
    Args:
        pdf_path (str): Path to PDF file
        
    Returns:
        str: Combined text from all pages
    """
    print_progress("Extracting text from PDF for guidance...")
    
    # Try to determine number of pages first
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        num_pages = len(doc)
        doc.close()
    except ImportError:
        # Fallback - try a reasonable range
        num_pages = 20
    
    all_text = []
    pages_with_text = 0
    
    for page_num in range(1, min(num_pages + 1, 21)):  # Limit to 20 pages max
        text = extract_text_from_pdf_page(pdf_path, page_num)
        if text:
            all_text.append(f"=== PAGE {page_num} ===\n{text}")
            pages_with_text += 1
    
    combined_text = '\n\n'.join(all_text)
    print_progress(f"+ Extracted text from {pages_with_text} pages ({len(combined_text)} characters)")
    
    return combined_text


def create_context_enhanced_prompt(pdf_text, structure_data, content_type="chapter"):
    """
    Create enhanced conversion prompt with context and PDF text guidance.
    
    Args:
        pdf_text (str): Extracted PDF text for guidance
        structure_data (dict): Structure metadata
        content_type (str): Type of content being converted
        
    Returns:
        str: Enhanced prompt for GPT-4 Vision
    """
    chapter_info = structure_data.get('chapter_info')
    chapter_figures = structure_data.get('chapter_figures', [])
    chapter_tables = structure_data.get('chapter_tables', [])
    
    if content_type == "chapter" and chapter_info:
        base_prompt = create_chapter_prompt(chapter_info, chapter_figures, chapter_tables)
    elif content_type == "front_matter":
        base_prompt = create_front_matter_prompt()
    elif content_type == "appendix":
        base_prompt = create_appendix_prompt(chapter_figures, chapter_tables)
    elif content_type == "references":
        base_prompt = create_references_prompt()
    elif content_type == "toc":
        base_prompt = create_toc_prompt()
    else:
        base_prompt = create_generic_prompt()
    
    # Add PDF text guidance section
    if pdf_text:
        guidance_section = f"""

GUIDANCE FROM PDF TEXT EXTRACTION:
The following text was extracted from the PDF pages to help guide your conversion:

{pdf_text[:3000]}{'...' if len(pdf_text) > 3000 else ''}

Use this text as reference for:
1. Verifying mathematical equations and symbols
2. Cross-checking figure and table references  
3. Understanding section structure and hierarchy
4. Ensuring accurate content conversion
5. Validating technical terminology and notation
6. CRITICAL: Identifying transitional sentences that may be missed visually
   - Look for sentences about "boundary layer formulation", "SHIE and DSHIE", "Burton and Miller"
   - Include ANY sentence that connects or compares different formulations or methods

The extracted text may contain OCR artifacts and line breaks - rely primarily on the visual content but MUST include transitional text found in the extracted text.
"""
        base_prompt += guidance_section
    
    base_prompt += """

IMPORTANT FORMATTING REQUIREMENTS:
1. CRITICAL: Read the entire PDF content from top to bottom without missing any text
   - Include ALL sentences and paragraphs, especially transitional text between sections
   - Pay attention to continuation text that may appear before section headers
   - Do NOT skip connector sentences that provide context or bridge between topics
   - SPECIFICALLY INCLUDE: Any sentences that reference technical methods, formulations, or comparisons
     Examples: "As the boundary layer formulation...", "This hybrid formulation is analogous to...", 
     "Similar to the Burton and Miller...", references to "SHIE", "DSHIE", etc.
2. Return ONLY the converted markdown content (no ```markdown delimiters)
3. Do not include explanatory text before or after the markdown
4. CRITICAL: Preserve the original visual layout and structure
   - Do NOT add bullet points unless the original document has bullet points
   - If you see two-column layouts (like notation definitions), use proper markdown format:
     
     PREFERRED - Definition list format:
     $\\mathbf{Q}$
     : Description here
     
     ALTERNATIVE - Table format:
     | Symbol | Description |
     |--------|-------------|
     | $\\mathbf{Q}$ | Description here |
     
   - Do NOT use single-line format "$\\mathbf{Q}$ : Description" as it renders poorly
   - If you see tables, preserve table structure
   - If you see definition lists, maintain definition format
5. Use proper markdown formatting with headers, equations, and appropriate structure
6. Ensure mathematical symbols are formatted correctly (only actual math expressions)
7. Do NOT convert standalone numbers to math format (page numbers, years, references, etc.)
8. Preserve academic writing style and technical precision
9. CRITICAL ANCHOR GENERATION for markdown viewer compatibility:
   - All headers must include section numbers and HTML anchors: ## 2.5 Section Title <a id="section-2-5"></a>
   - Chapter headers: # Chapter 2: Title <a id="chapter-2"></a>
   - Section headers: ## 2.1 Section Title <a id="section-2-1"></a>
   - Subsection headers: ### 2.1.1 Subsection Title <a id="section-2-1-1"></a>
   - Figures: Add <a id="figure-N-M"></a> anchors BEFORE figure images
   - Tables: Add <a id="table-N-M"></a> anchors BEFORE table content
   - Equations: Add <a id="equation-N-M"></a> anchors BEFORE numbered equations (multiline format)
     CORRECT FORMAT: <a id="equation-2-1-1"></a>
     $$
     \\begin{align*} \\rho \\frac{\\partial v}{\\partial t} = -\\nabla p \\tag{2.1.1} \\end{align*}
     $$
   - Figure images: Use picture element with dual theme support based on figure reference
     EXAMPLE: <a id="figure-2-5"></a>
     <picture>
       <source media="(prefers-color-scheme: dark)" srcset="assets/figure-2-5-dark.png">
       <source media="(prefers-color-scheme: light)" srcset="assets/figure-2-5.png">
       <img alt="Figure 2.5. Caption text" src="assets/figure-2-5.png">
     </picture>
     Figure 2.5. Caption text
   - Anchor IDs use section numbers, not titles: section-2-5, not thin-shell-formulation
   - This enables proper cross-referencing across markdown viewers
"""
    
    return base_prompt


def create_chapter_prompt(chapter_info, figures, tables):
    """Create chapter-specific conversion prompt."""
    
    chapter_num = chapter_info.get('chapter_number', '?')
    chapter_title = chapter_info.get('title', 'Unknown Chapter')
    subsections = chapter_info.get('subsections', [])
    
    prompt = f"""Convert this PDF chapter to clean, academic markdown format.

CHAPTER CONTEXT:
- Chapter {chapter_num}: {chapter_title}
- Pages {chapter_info.get('page_start', '?')}-{chapter_info.get('page_end', '?')}

EXPECTED SECTION STRUCTURE:"""
    
    if subsections:
        prompt += "\nThis chapter should contain the following sections:"
        for subsection in subsections:
            section_num = subsection.get('section_number', '?')
            section_title = subsection.get('title', 'Unknown Section')
            section_page = subsection.get('page', '?')
            level = subsection.get('level', 1)
            indent = "  " * (level - 1)
            prompt += f"\n{indent}- {section_num}: {section_title} (page {section_page})"
    
    if figures:
        prompt += f"\n\nEXPECTED FIGURES IN THIS CHAPTER ({len(figures)} total):"
        for fig in figures:
            prompt += f"\n- Figure {fig.get('figure_number', '?')}: {fig.get('title', 'No title')} (page {fig.get('page', '?')})"
    
    if tables:
        prompt += f"\n\nEXPECTED TABLES IN THIS CHAPTER ({len(tables)} total):"
        for table in tables:
            prompt += f"\n- Table {table.get('table_number', '?')}: {table.get('title', 'No title')} (page {table.get('page', '?')})"
    
    prompt += """

CONVERSION INSTRUCTIONS:
1. CRITICAL: Read the entire PDF content carefully from top to bottom
   - Include ALL text content, especially continuation sentences and transitional text
   - Pay special attention to text that appears before major section headers
   - Do NOT skip any paragraphs or sentences, even if they seem like connectors
   - Look for text that bridges content from previous sections or provides context
   - MANDATORY: Include sentences that reference technical formulations, methods, or comparisons
     Key patterns: "As the [method] formulation...", "analogous to the [Name] formulation", 
     "related to the SHIE and DSHIE", "Burton and Miller", "hybrid formulation"
2. Create proper markdown headers matching the section hierarchy
3. Convert mathematical equations using MARKDOWN LaTeX format (NOT LaTeX document format):
   - Inline equations: $equation$ (use single dollar signs, NOT \\(equation\\))
   - Display equations: $$equation$$ (use double dollar signs, NOT \\[equation\\])
   - Numbered equations: $$\\begin{align*} equation \\tag{2.1} \\end{align*}$$
   - Mathematical variables: $x$, $\\alpha$, $\\mathbf{Q}$ (use dollar signs, NOT \\(x\\))
4. IMPORTANT MATHEMATICAL FORMATTING RULES:
   - ALWAYS use $...$ for inline math, NEVER use \\(...\\)
   - ALWAYS use $$...$$ for display math, NEVER use \\[...\\]
   - For matrices: $\\mathbf{Q}$, not \\(\\mathbf{Q}\\)
   - For Greek letters: $\\alpha$, $\\beta$, not \\(\\alpha\\), \\(\\beta\\)
   - For subscripts: $x_i$, not \\(x_i\\)
5. IMPORTANT - Do NOT convert standalone numbers to math format:
   - "page 24" should remain "page 24", NOT "page $24$"
   - "year 1992" should remain "year 1992", NOT "year $1992$"
   - "equation 2.5" should remain "equation 2.5", NOT "equation $2.5$"
   - Only use math formatting for actual mathematical expressions and variables
6. Preserve figure and table references (e.g., "see Figure 2.1", "Table 2.3 shows")
7. Maintain academic writing style and technical precision
8. Include all mathematical derivations and technical details
9. Format mathematical symbols correctly using markdown format (Greek letters, subscripts, superscripts)
10. Preserve equation numbering and cross-references
11. CRITICAL LAYOUT PRESERVATION:
    - Preserve the original document layout and structure
    - Do NOT add bullet points (-) unless the original document has bullet points
    - If content is in two columns (like symbol definitions), use proper markdown format:
      
      OPTION 1 - Definition list:
      $\\alpha$
      : Description here
      
      $\\beta$
      : Another description
      
      OPTION 2 - Table format:
      | Symbol | Description |
      |--------|-------------|
      | $\\alpha$ | Description here |
      | $\\beta$ | Another description |
    - Do NOT use single-line format "$\\alpha$ : description" as it renders poorly
    - If content is in a table, preserve table structure
    - Look at the visual layout carefully before choosing markdown formatting
12. Use proper markdown formatting for lists, emphasis, and structure
13. CRITICAL ANCHOR GENERATION for markdown viewer compatibility:
    - Chapter headers: # Chapter 2: Title <a id="chapter-2"></a>
    - Section headers: ## 2.1 Section Title <a id="section-2-1"></a>
    - Subsection headers: ### 2.1.1 Subsection Title <a id="section-2-1-1"></a>
    - Figures: <a id="figure-2-1"></a>
      <picture>
        <source media="(prefers-color-scheme: dark)" srcset="assets/figure-2-1-dark.png">
        <source media="(prefers-color-scheme: light)" srcset="assets/figure-2-1.png">
        <img alt="Figure 2.1. Caption" src="assets/figure-2-1.png">
      </picture>
      Figure 2.1. Caption
    - Tables: <a id="table-2-1"></a> before table content
    - Equations: <a id="equation-2-1"></a>
      $$
      \\begin{align*} equation \\tag{2.1} \\end{align*}
      $$
    - Figure and equation formatting: Use picture elements for figures, multiline format for equations
    - IMPORTANT: Include section numbers in headings and use section-based anchor IDs
    - Anchor IDs use numbers: section-2-1, not descriptive names"""
    
    return prompt


def create_front_matter_prompt():
    """Create front matter-specific conversion prompt."""
    return """Convert this PDF front matter to clean markdown format.

FRONT MATTER CONVERSION INSTRUCTIONS:
1. Preserve academic formatting and style
2. Handle different front matter types appropriately:
   - Abstract: Academic summary format
   - Acknowledgements: Personal/professional recognition format
   - Notation: Mathematical symbol definitions with MARKDOWN LaTeX formatting
   - Table of contents: Clean hierarchical structure (if needed)
3. CRITICAL MATHEMATICAL FORMATTING for notation sections:
   - Use MARKDOWN format: $\\mathbf{Q}$, $\\alpha$, $x_i$ (with dollar signs)
   - NEVER use LaTeX format: \\(\\mathbf{Q}\\), \\(\\alpha\\), \\(x_i\\)
   - For matrices: $\\mathbf{Q}$, $\\mathbf{Q}^{-1}$, $\\mathbf{Q}^T$
   - For Greek letters: $\\alpha$, $\\beta$, $\\gamma$
   - For vectors: $\\{x\\}$, $\\{x\\}^T$
4. CRITICAL LAYOUT PRESERVATION for notation sections:
   - If the original shows mathematical symbols with descriptions in two columns, use markdown definition list format:
     $\\mathbf{Q}$
     : A square or rectangular matrix
     
     $\\mathbf{Q}^{-1}$
     : Matrix inverse
   - Alternative: Use table format for better alignment:
     | Symbol | Description |
     |--------|-------------|
     | $\\mathbf{Q}$ | A square or rectangular matrix |
     | $\\mathbf{Q}^{-1}$ | Matrix inverse |
   - Do NOT use bullet points (-) unless the original document actually has bullet points
   - Do NOT use single-line format like "$\\mathbf{Q}$ : description" as it renders poorly
   - Look carefully at the visual layout: two-column format needs proper markdown structure
5. IMPORTANT - Do NOT convert standalone numbers, dates, or references to math format
6. Maintain formal academic tone
7. Preserve any special formatting or emphasis
8. Use appropriate markdown headers and structure
9. CRITICAL ANCHOR GENERATION for GitBook/Pandoc linking:
   - Section headers: # Section Title {#section-title}
   - Subsection headers: ## Subsection Title {#subsection-title}
   - For notation sections, add anchors: ## Notation {#notation}
   - Use lowercase, hyphenated anchors for compatibility"""


def create_appendix_prompt(figures, tables):
    """Create appendix-specific conversion prompt."""
    prompt = """Convert this PDF appendix to clean markdown format.

APPENDIX CONVERSION INSTRUCTIONS:
1. Use appendix-appropriate formatting with A1, A2, etc. numbering
2. Convert mathematical content using MARKDOWN LaTeX formatting (only actual math expressions):
   - Use $...$ for inline math, NOT \\(...\\)
   - Use $$...$$ for display math, NOT \\[...\\]
   - Mathematical variables: $x$, $\\alpha$, $\\mathbf{Q}$ (use dollar signs)
3. IMPORTANT - Do NOT convert standalone numbers, page references, or appendix numbers to math format
4. Preserve technical details and derivations
5. Handle appendix-specific figure and table numbering (A1.1, A2.1, etc.)
6. Maintain cross-references to main document sections
7. CRITICAL LAYOUT PRESERVATION:
   - Preserve the original document layout and structure
   - Do NOT add bullet points (-) unless the original document has bullet points
   - If content is in definition format (symbol with description), use proper markdown:
     
     OPTION 1 - Definition list:
     $\\mathbf{Q}$
     : Description here
     
     OPTION 2 - Table format:
     | Symbol | Description |
     |--------|-------------|
     | $\\mathbf{Q}$ | Description here |
   - Do NOT use single-line format "$\\mathbf{Q}$ : description" as it renders poorly
   - Look at the visual layout carefully before choosing markdown formatting
8. Include all technical details and supplementary material
9. CRITICAL ANCHOR GENERATION for GitBook/Pandoc linking:
   - Appendix headers: # Appendix 1: Title {#appendix-1}
   - Section headers: ## A1.1 Section Title {#section-a1-1}
   - Figures: Caption with {#figure-a1-1} after figure references
   - Tables: Caption with {#table-a1-1} after table references
   - Equations: Add {#equation-a1-1} AFTER numbered equations (never inside \\tag{})
   - Use lowercase, hyphenated anchors for compatibility"""
    
    if figures:
        prompt += f"\n\nEXPECTED APPENDIX FIGURES ({len(figures)} total):"
        for fig in figures:
            prompt += f"\n- Figure {fig.get('figure_number', '?')}: {fig.get('title', 'No title')}"
    
    if tables:
        prompt += f"\n\nEXPECTED APPENDIX TABLES ({len(tables)} total):"
        for table in tables:
            prompt += f"\n- Table {table.get('table_number', '?')}: {table.get('title', 'No title')}"
    
    return prompt


def create_references_prompt():
    """Create references-specific conversion prompt."""
    return """Convert this PDF references section to clean markdown format.

REFERENCES CONVERSION INSTRUCTIONS:
1. Maintain bibliographic formatting and academic style
2. Preserve author names, titles, publication details
3. Convert to consistent citation format
4. Handle different reference types (journals, books, conferences, etc.)
5. Maintain alphabetical or numerical ordering as appropriate
6. For mathematical references, use MARKDOWN format ($...$) NOT LaTeX format (\\(...\\))
7. Use appropriate markdown formatting for references list
8. Add anchors for reference items: {#ref-author-year} for GitBook/Pandoc linking"""


def create_toc_prompt():
    """Create table of contents-specific conversion prompt."""
    return """Convert this PDF table of contents section to clean markdown format.

TOC CONVERSION INSTRUCTIONS:
1. This is a TABLE OF CONTENTS, FIGURES LIST, or TABLES LIST - preserve the list structure
2. Convert to proper markdown with appropriate hierarchy:
   - Main chapters: ## Chapter 1: Title <a id="chapter-1"></a>
   - Subsections: ### 1.1 Subsection Title <a id="section-1-1"></a>
   - Figures: #### Figure 2.1: Caption <a id="figure-2-1"></a>
     Format: <a id="figure-2-1"></a>
     <picture>
       <source media="(prefers-color-scheme: dark)" srcset="assets/figure-2-1-dark.png">
       <source media="(prefers-color-scheme: light)" srcset="assets/figure-2-1.png">
       <img alt="Figure 2.1. Caption" src="assets/figure-2-1.png">
     </picture>
     Figure 2.1. Caption
   - Tables: #### Table 3.2: Caption <a id="table-3-2"></a>
3. CRITICAL ANCHOR GENERATION for markdown viewer compatibility:
   - Chapters: <a id="chapter-N"></a> where N is chapter number
   - Sections: <a id="section-N-M"></a> where N.M is section number  
   - Figures: <a id="figure-N-M"></a> where N.M is figure number
   - Tables: <a id="table-N-M"></a> where N.M is table number
   - Equations: <a id="equation-N-M"></a> where N.M is equation number (BEFORE equation)
   - IMPORTANT: Include section numbers in all headings, not just titles
4. Preserve page numbers in format: "....... 24"
5. Maintain hierarchical indentation for subsections
6. Use MARKDOWN format ($...$) for any mathematical symbols in titles
7. Do NOT add bullet points unless the original uses them
8. For multi-level TOCs, use appropriate header levels (##, ###, ####)
9. Create clickable cross-references that work across markdown viewers"""


def create_generic_prompt():
    """Create generic conversion prompt for unknown content types."""
    return """Convert this PDF content to clean markdown format.

GENERAL CONVERSION INSTRUCTIONS:
1. Preserve document structure and hierarchy
2. Convert mathematical content using MARKDOWN LaTeX format where appropriate:
   - Use $...$ for inline math, NOT \\(...\\)
   - Use $$...$$ for display math, NOT \\[...\\]
3. Maintain academic writing style and formatting
4. Handle figures and tables appropriately
5. CRITICAL LAYOUT PRESERVATION:
   - Preserve the original document layout and structure
   - Do NOT add bullet points (-) unless the original document has bullet points
   - If content is in definition format (term with description), use proper markdown:
     
     OPTION 1 - Definition list:
     Term
     : Description here
     
     OPTION 2 - Table format:
     | Term | Description |
     |------|-------------|
     | Term | Description here |
   - Do NOT use single-line format "Term : description" as it renders poorly
   - Look at the visual layout carefully before choosing markdown formatting
6. Use proper markdown formatting throughout
7. Preserve technical precision and details
8. CRITICAL ANCHOR GENERATION for GitBook/Pandoc linking:
   - Headers: # Title {#title} or ## Section {#section}
   - Figures: Caption with {#figure-N-M} after figure references
   - Tables: Caption with {#table-N-M} after table references
   - Equations: Add {#equation-N-M} AFTER numbered equations (never inside \\tag{})
   - Use lowercase, hyphenated anchors for compatibility"""


def clean_markdown_output(text):
    """
    Clean up GPT-4 Vision markdown output by removing delimiters and fixing common issues.
    
    Args:
        text (str): Raw markdown text from GPT-4 Vision
        
    Returns:
        str: Cleaned markdown text
    """
    # Remove markdown code block delimiters
    text = text.strip()
    
    # Remove markdown delimiters at start and end
    if text.startswith('```markdown'):
        text = text[11:].strip()
    elif text.startswith('```'):
        text = text[3:].strip()
    
    if text.endswith('```'):
        text = text[:-3].strip()
    
    # Remove any remaining code block markers that might be in the middle
    text = text.replace('```markdown\n', '')
    text = text.replace('\n```markdown', '')
    text = text.replace('\n```', '')
    
    # Fix standalone numbers that were incorrectly converted to equations
    # Pattern: standalone numbers wrapped in $$ that should be plain text
    import re
    
    # Find patterns like "text $$24$$ text" where 24 is just a standalone number
    # This should not be converted to equations
    def fix_standalone_numbers(match):
        number = match.group(1)
        # Check if this looks like a standalone number (not a mathematical expression)
        if re.match(r'^\d+(\.\d+)?$', number):
            return f' {number} '
        else:
            return match.group(0)  # Keep original if it's a real equation
    
    # Fix standalone numbers incorrectly wrapped in $$
    text = re.sub(r'\s\$\$(\d+(?:\.\d+)?)\$\$\s', fix_standalone_numbers, text)
    
    # Fix single $ around standalone numbers as well
    text = re.sub(r'\s\$(\d+(?:\.\d+)?)\$\s', fix_standalone_numbers, text)
    
    # Fix numbers at start/end of sentences
    text = re.sub(r'^\$\$(\d+(?:\.\d+)?)\$\$\s', r'\1 ', text, flags=re.MULTILINE)
    text = re.sub(r'\s\$\$(\d+(?:\.\d+)?)\$\$$', r' \1', text, flags=re.MULTILINE)
    text = re.sub(r'^\$(\d+(?:\.\d+)?)\$\s', r'\1 ', text, flags=re.MULTILINE)
    text = re.sub(r'\s\$(\d+(?:\.\d+)?)\$$', r' \1', text, flags=re.MULTILINE)
    
    # Clean up any double spaces created by the fixes
    text = re.sub(r'  +', ' ', text)
    
    # Clean up spacing around periods and commas
    text = re.sub(r' +\.', '.', text)
    text = re.sub(r' +,', ',', text)
    
    # Fix LaTeX format to markdown format (in case GPT-4 still uses wrong format)
    # Convert \(equation\) to $equation$
    text = re.sub(r'\\?\\\((.*?)\\\)', r'$\1$', text)
    
    # Convert \[equation\] to $$equation$$
    text = re.sub(r'\\?\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    
    # Fix any double conversions (like $$$ or $$$$ that might occur)
    text = re.sub(r'\$\$\$+', '$$', text)
    text = re.sub(r'(?<!\$)\$(?!\$)(?:\$(?!\$))+', '$', text)  # Fix multiple single $
    
    return text.strip()


def convert_pdf_with_context(pdf_path, output_path, structure_dir=None, 
                           chapter_name=None, content_type="chapter"):
    """
    Convert PDF to markdown with enhanced context and PDF text guidance.
    
    Args:
        pdf_path (str): Path to input PDF file
        output_path (str): Path for output markdown file
        structure_dir (str): Directory containing YAML structure files
        chapter_name (str, optional): Chapter identifier for context
        content_type (str): Type of content being converted
        
    Returns:
        bool: True if conversion succeeded, False otherwise
    """
    # Validate API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print_progress("ERROR: Please set your OPENAI_API_KEY environment variable")
        return False
    
    openai.api_key = api_key
    
    # Load structure data for context
    structure_data = {}
    if structure_dir:
        structure_data = load_structure_data(structure_dir, chapter_name)
    
    # Extract PDF text for guidance
    pdf_text = extract_pdf_text_by_pages(pdf_path)
    
    # Convert PDF to images
    temp_dir = "/tmp/context_conversion"
    images = pdf_to_images(pdf_path, temp_dir, dpi=200, page_prefix="convert")
    
    if not images:
        print_progress("- Failed to convert PDF to images")
        return False
    
    # Encode images for Vision API
    print_progress("Preparing images for GPT-4 Vision...")
    image_contents = encode_images_for_vision(images)
    
    # Create context-enhanced prompt
    prompt = create_context_enhanced_prompt(pdf_text, structure_data, content_type)
    
    # Call GPT-4 Vision API with higher token limit for context
    print_progress("Converting content with GPT-4 Vision (enhanced context)...")
    max_tokens = 4000  # Higher limit for context-aware conversion
    
    result = call_gpt_vision_api(
        prompt, image_contents,
        model="gpt-4o", max_tokens=max_tokens
    )
    
    # Clean up temporary files
    cleanup_temp_directory(temp_dir)
    
    if result.startswith("Error:"):
        print_progress(f"- GPT-4 Vision API error: {result}")
        return False
    
    # Clean the markdown output
    print_progress("Cleaning markdown output...")
    cleaned_result = clean_markdown_output(result)
    
    # Save converted content
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_result)
        print_progress(f"+ Conversion completed: {output_file}")
        
        # Display conversion statistics
        line_count = len(cleaned_result.split('\n'))
        word_count = len(cleaned_result.split())
        print_progress(f"+ Output: {line_count} lines, {word_count} words")
        
        # Report cleaning statistics
        if cleaned_result != result:
            print_progress(f"+ Cleaned markdown formatting and fixed standalone numbers")
        
        return True
        
    except Exception as e:
        print_progress(f"- Failed to save output: {e}")
        return False


def main():
    """Main function for context-enhanced PDF to markdown conversion."""
    parser = argparse.ArgumentParser(
        description='Convert PDF to markdown with enhanced context and PDF text guidance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a chapter with full context
  python convert_with_context.py chapter2.pdf \\
      --output-dir markdown_output/ \\
      --structure-dir structure/ \\
      --chapter-name "Chapter 2"
  
  # Convert front matter
  python convert_with_context.py abstract.pdf \\
      --output-dir markdown_output/ \\
      --structure-dir structure/ \\
      --content-type front_matter
  
  # Convert with custom directories
  python convert_with_context.py chapter1.pdf \\
      --output-dir custom/markdown/ \\
      --structure-dir custom/structure/
        """
    )
    
    parser.add_argument('input_pdf', help='Input PDF file path')
    parser.add_argument('--output-dir', required=True,
                       help='Output directory for markdown files')
    parser.add_argument('--structure-dir', required=True,
                       help='Directory containing YAML structure files')
    parser.add_argument('--chapter-name',
                       help='Chapter identifier for context (e.g., "Chapter 2", "2")')
    parser.add_argument('--content-type', 
                       choices=['chapter', 'front_matter', 'appendix', 'references', 'toc', 'generic'],
                       default='chapter',
                       help='Type of content being converted')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input_pdf).exists():
        print(f"ERROR: Input PDF not found: {args.input_pdf}")
        return 1
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output markdown filename
    input_pdf_path = Path(args.input_pdf)
    output_md = output_dir / f"{input_pdf_path.stem}.md"
    
    # Display processing information
    print_section_header("CONTEXT-ENHANCED PDF TO MARKDOWN CONVERSION")
    print(f"Input PDF: {args.input_pdf}")
    print(f"Output markdown: {output_md}")
    print(f"Output directory: {args.output_dir}")
    print(f"Structure directory: {args.structure_dir}")
    print(f"Content type: {args.content_type}")
    if args.chapter_name:
        print(f"Chapter context: {args.chapter_name}")
    print("=" * 60)
    
    # Perform conversion
    success = convert_pdf_with_context(
        args.input_pdf, 
        str(output_md),
        args.structure_dir,
        args.chapter_name,
        args.content_type
    )
    
    if success:
        print_completion_summary(str(output_md), 1, "document converted")
        return 0
    else:
        print("FAILED: Conversion unsuccessful")
        return 1


if __name__ == "__main__":
    exit(main())
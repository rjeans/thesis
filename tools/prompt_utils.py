#!/usr/bin/env python3
"""
Simplified prompt utilities for thesis conversion.
"""


def get_content_transcription_requirements():
    """Get content transcription requirements section."""
    return """**COMPLETE TEXT TRANSCRIPTION**: Read entire PDF content without missing any text
   - Include ALL sentences and paragraphs, especially transitional text between sections
   - Pay attention to continuation text that may appear before section headers
   - Do NOT skip connector sentences that provide context or bridge between topics
   - SPECIFICALLY INCLUDE: Any sentences that reference technical methods, formulations, or comparisons
   - Look for partial sentences or paragraphs that continue from the previous page"""


def get_mathematical_formatting_section():
    """Get mathematical formatting requirements section."""
    return """**MATHEMATICAL FORMATTING**:
   - **CRITICAL**: Inline equations: $variable$ (NOT \\(variable\\))
   - **CRITICAL**: Display equations (unnumbered): $$equation$$ (NOT \\[equation\\])
   - **CRITICAL**: Display equations (numbered): $$equation \\tag{2.5.1}$$ or $$\\begin{align*} equation \\tag{2.5.1} \\end{align*}$$
   - **CRITICAL**: ALL numbered equations MUST use \\tag{} inside the $$ block
   - **CRITICAL**: NEVER put equation numbers outside $$ like: $$equation$$ (2.5.1)
   - **CRITICAL**: NEVER use \\(variable\\) or \\[equation\\] - these are forbidden
   - **CRITICAL**: Complex superscripts/subscripts must use braces: $\\lambda_N^{{e_p}}$ NOT $\\lambda_N^e_p$
   - Use proper LaTeX notation for mathematical symbols and operators

**EXAMPLES:**
- Correct inline: The $N_i^k$ operator can be...
- Wrong inline: The \\(N_i^k\\) operator can be...
- Correct display: $$equation content \\tag{4.4.1}$$
- Wrong display: \\[equation content\\]
- Correct complex subscript/superscript: $\\lambda_N^{{e_p}}$
- Wrong complex subscript/superscript: $\\lambda_N^e_p$"""


def get_figure_formatting_section():
    """Get figure formatting requirements section."""
    return """**FIGURE FORMATTING**: Use HTML picture element format with correct section-based naming:

<a id="figure-x-y"></a>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/figure-x-y-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="assets/figure-x-y.png">
  <img alt="Figure X.Y. Caption text here." src="assets/figure-x-y.png">
</picture>
Figure X.Y. Caption text here.

**CRITICAL NAMING**: Use the actual section prefix in figure names:
- For Chapter 2: figure-2-1.png, figure-2-2.png
- For Appendix A2: figure-A2-1.png, figure-A2-2.png  
- For Appendix A1: figure-A1-1.png, figure-A1-2.png
**Requirements**: Anchor BEFORE picture element, both themes, full alt text, plain caption below"""


def get_table_formatting_section():
    """Get table formatting requirements section."""
    return """**TABLE FORMATTING**:
   - **CRITICAL**: Convert ALL tables to proper Markdown table format
   - **PRESERVE ORIGINAL STRUCTURE**: Maintain the exact layout and orientation from the PDF
   - Add anchor before table: `<a id="table-a2-1"></a>`
   - Use pipe-separated format with proper alignment:
     ```
     <a id="table-2-1"></a>
     
     | Column 1 | Column 2 | Column 3 |
     |----------|----------|----------|
     | Value 1  | Value 2  | Value 3  |
     | Value 4  | Value 5  | Value 6  |
     
     **Table 2.1**: Caption text describing the table contents
     ```
   - **CRITICAL**: If the table has column headers (like n=0, n=1, n=2...), use them as column headers
   - **CRITICAL**: If the table has row labels, include them in the first column
   - Preserve all table data accurately, including numerical values and units
   - Maintain proper column alignment (left, center, right as appropriate)
   - Include complete table captions below the table
   - **DO NOT SKIP TABLES** - they contain important data that must be preserved
   - **DO NOT TRANSPOSE**: Keep rows as rows and columns as columns as shown in the original"""


def get_anchor_generation_section():
    """Get anchor generation requirements section."""
    return """**ANCHOR GENERATION AND HEADING HIERARCHY**:
   - **Chapter headers (level 1)**: # Chapter Title <a id="chapter-X"></a>
   - **Main sections (level 1)**: ## 2.1 Section Title <a id="section-2-1"></a>
   - **Subsections (level 2)**: ### 2.1.1 Subsection Title <a id="section-2-1-1"></a>
   - **Sub-subsections (level 3)**: #### 2.1.1.1 Sub-subsection Title <a id="section-2-1-1-1"></a>
   - **CRITICAL**: Use correct heading depth based on section numbering depth
   - Figures: <a id="figure-2-1"></a> before figure elements
   - Equations: <a id="equation-2-1"></a> before equation blocks
   - Tables: <a id="table-2-1"></a> before table content"""


def get_cross_reference_section():
    """Get cross-reference requirements section."""
    return """**CROSS-REFERENCES**:
   - Figures: [Figure 2.1](#figure-2-1), [Fig. 2.1](#figure-2-1)
   - Equations: [equation (2.1)](#equation-2-1), [Eq. (2.1)](#equation-2-1)
   - Tables: [Table 2.1](#table-2-1), [Tab. 2.1](#table-2-1)
   - Sections: [Section 2.1](#section-2-1), [Sec. 2.1](#section-2-1)
   - **Literature References**: Convert ALL citation patterns to markdown links:
     * "Author [Year]" → [Author [Year]](#bib-author-year) e.g., [Jennings [1977]](#bib-jennings-1977)
     * "Author (Year)" → [Author (Year)](#bib-author-year) e.g., [Smith (1990)](#bib-smith-1990)
     * "Author et al. [Year]" → [Author et al. [Year]](#bib-author-et-al-year) e.g., [Jones et al. [1985]](#bib-jones-et-al-1985)
     * "Author and Author [Year]" → [Author and Author [Year]](#bib-author-author-year) e.g., [Burton and Miller [1971]](#bib-burton-miller-1971)"""


def get_pdf_text_guidance_section(text_context):
    """Get PDF text guidance section."""
    if not text_context:
        return "**PDF TEXT GUIDANCE**: No text context available."
    
    return f"""**PDF TEXT GUIDANCE**: Use this extracted text to verify accuracy and completeness:

{text_context}

This text should help you understand the content structure and ensure nothing is missed."""


def get_output_requirements_section():
    """Get output requirements section."""
    return """**OUTPUT REQUIREMENTS**:
- Provide clean markdown without code block markers
- Focus on creating complete, coherent content
- Skip page headers, footers, or page numbers
- Maintain academic writing conventions and technical precision"""


def create_toc_parsing_prompt(content_type, yaml_structure):
    """
    Generate standardized prompts for table of contents parsing.

    Creates consistent prompts for parsing different TOC sections
    (contents, figures, tables) with proper YAML output format.

    Args:
        content_type (str): Type of content ("contents", "figures", "tables")
        yaml_structure (str): YAML structure example for the output

    Returns:
        str: Formatted prompt for GPT-4 Vision API
    """
    content_descriptions = {
        "contents": "table of contents from this 1992 PhD thesis and extract the chapter/section structure",
        "figures": "figures list from this 1992 PhD thesis and extract all figure information",
        "tables": "tables list from this 1992 PhD thesis and extract all table information",
        "references": "academic references from this 1992 PhD thesis and convert them to BibTeX format"
    }

    instructions = {
        "contents": [
            "Extract ALL table of contents entries visible on the page provided.",
            "CRITICAL: Look for BOTH complete chapters AND individual sections/subsections that may be continuations from previous pages.",
            "CRITICAL: If you see sections numbered like '2.5', '2.6' etc. without a chapter header, create a chapter entry for the parent chapter (e.g., for '2.5' create 'CHAPTER 2' entry with chapter_number: 2).",
            "CRITICAL: For orphaned sections like '2.5 Thin shell formulation', determine the parent chapter number from the section number and create a chapter entry.",
            "Do not infer or guess any content that is not explicitly visible.",
            "Identify section types: front_matter, chapter, appendix, back_matter",
            "Include complete subsection hierarchies with proper level numbering as seen on the page.",
            "Preserve exact capitalization and punctuation",
            "CRITICAL: If a title contains mathematical notation, enclose it in inline LaTeX delimiters (e.g., $...$)",
            "For chapters, extract chapter_number from title (e.g., 'CHAPTER 3' -> chapter_number: 3)",
            "CRITICAL: Extract only the start_page for each section/subsection. Do NOT include or calculate end_page.",
            "IMPORTANT: If this page shows sections from multiple chapters, create separate chapter entries for each.",
            "EXAMPLE: If you see '2.5 Thin shell formulation' without 'CHAPTER 2' header, create an entry: type: chapter, title: 'CHAPTER 2 (continued)', chapter_number: 2, subsections: [{section_number: '2.5', title: 'Thin shell formulation', ...}]"
        ],
        "figures": [
            "**CRITICAL: Process ALL pages provided - examine every single page image for figures**",
            "Extract ALL figures listed exactly as shown across ALL pages",
            "Include complete figure titles/captions from ALL pages",
            "Extract page numbers accurately from ALL pages",
            "Determine chapter number from figure numbering (e.g., \"2.1\" = chapter 2)",
            "Preserve exact capitalization and punctuation in titles",
            "Include figures with complex numbering like \"3.5.6\"",
            "**CRITICAL: Do not stop after the first page - continue through all provided pages**"
        ],
        "tables": [
            "**CRITICAL: Process ALL pages provided - examine every single page image for tables**",
            "Extract ALL tables listed exactly as shown across ALL pages",
            "Include complete table titles/captions from ALL pages",
            "Extract page numbers accurately from ALL pages",
            "Determine chapter number from table numbering (e.g., \"4.1\" = chapter 4)",
            "**CRITICAL: Do not stop after the first page - continue through all provided pages**",
            "Preserve exact capitalization and punctuation in titles",
            "If no tables are found, return an empty tables list"
        ],
        "references": [
            "**CRITICAL: Process ALL pages provided - examine every single page image for references**",
            "Extract ALL academic references exactly as they appear across ALL pages",
            "Parse each reference into proper BibTeX format with correct field identification",
            "Generate unique BibTeX keys using format: first-author-lastname-year (lowercase, hyphenated)",
            "Identify reference types: article, book, inproceedings, incollection, techreport, phdthesis, mastersthesis, misc",
            "Extract complete bibliographic data: authors, titles, journals/books, years, volumes, pages",
            "Handle various 1992 citation formats and incomplete references appropriately",
            "Include original_text field with exact reference as it appears in PDF",
            "**CRITICAL: Do not stop after the first page - continue through all provided pages**",
            "Preserve author name formatting and handle 'et al.' appropriately"
        ]
    }

    description = content_descriptions.get(content_type, f"{content_type} from this document")
    instruction_list = instructions.get(content_type, [])

    # Adjust the prompt based on content type
    if content_type in ["figures", "tables", "references"]:
        page_description = "from ALL page images provided (process every page completely)"
    else:
        page_description = "from the single page image provided"
    
    prompt = f"""
Parse the {description} {page_description}.

Return YAML format with this structure:

{yaml_structure}

Instructions:
"""

    for i, instruction in enumerate(instruction_list, 1):
        prompt += f" {i}. {instruction}\n"

    prompt += " \nReturn only valid YAML without explanatory text or markdown formatting.\n"

    return prompt


def create_chapter_conversion_prompt(chapter_name="Chapter"):
    """
    Generate standardized prompt for chapter PDF to markdown conversion.

    Creates detailed prompt for converting academic PDF chapters to markdown
    with proper LaTeX equation handling and academic formatting.

    Args:
        chapter_name (str): Name/title of the chapter being converted

    Returns:
        str: Formatted prompt for GPT-4 Vision API
    """
    return f"""
Convert this complete {chapter_name} from a 1992 LaTeX academic thesis PDF to markdown format. This is a multi-page chapter, so please:

**Content Requirements:**
1. **CRITICAL - Complete Text Transcription**: Read the entire PDF content from top to bottom without missing any text
   - Include ALL sentences and paragraphs, especially transitional text between sections
   - Pay attention to continuation text that may appear before section headers
   - Do NOT skip connector sentences that provide context or bridge between topics
   - SPECIFICALLY INCLUDE: Any sentences that reference technical methods, formulations, or comparisons
   Examples: "As the boundary layer formulation...", "This hybrid formulation is analogous to...",
   "Similar to the Burton and Miller...", references to "SHIE", "DSHIE", etc.
   - Look for partial sentences or paragraphs that continue from the previous page
2. **Preserve Structure**: Maintain all section headers, subsection numbering, and hierarchical organization
3. **Mathematical Content**: Convert all equations to proper LaTeX format:
   - Inline math: $variable$ or $equation$
   - Display equations (unnumbered): $$equation$$
   - Display equations (numbered): $$equation \\tag{{number}}$$ or $$\\begin{{align*}} equation \\tag{{number}} \\end{{align*}}$$
   - **CRITICAL**: ALL numbered equations MUST use \\tag{{}} inside the $$ block
   - **CRITICAL**: NEVER put equation numbers outside $$ like: $$equation$$ (number)
   - **CRITICAL**: Opening $$ must NOT have newline after it
   - **CRITICAL**: Closing $$ must NOT have newline before it
   - **CRITICAL**: NO line breaks anywhere within $$...$$

**CORRECT FORMAT EXAMPLES:**
<a id="equation-2-1-15"></a>
$$\\tilde{{u}} = \\nabla \\phi, \\quad \\tilde{{p}} = i \\omega \\rho \\phi. \\tag{{2.1.15}}$$

**WRONG FORMAT (DO NOT USE):**
$$
\\tilde{{u}} = \\nabla \\phi \\tag{{2.1.15}} <a id="equation-2-1-15"></a>
$$
4. **Cross-References**: Preserve all figure references, equation references, and citations
5. **Figure Formatting**: Use HTML picture element format for dual theme support:

<a id="figure-x-y"></a>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/figure-x-y-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="assets/figure-x-y.png">
  <img alt="Figure X.Y. Caption text here." src="assets/figure-x-y.png">
</picture>
Figure X.Y. Caption text here.

**Requirements**: Anchor BEFORE picture element, both themes, full alt text, plain caption below
6. **Page Continuity**: Merge content that spans across pages seamlessly

**Formatting Standards:**
- Use ## for main sections, ### for subsections with section numbers and HTML anchors: ## 2.1 Section Title <a id="section-2-1"></a>
- Preserve paragraph structure and academic writing flow
- Keep mathematical notation as LaTeX (Greek letters, operators, etc.)
- Maintain proper spacing around equations and sections
- **Add HTML anchors for equations BEFORE the equation block**: <a id="equation-x-y"></a>
$$equation$$
- Use assets/figure-x-y.png format for figure paths
- IMPORTANT: Include section numbers in headings, anchor IDs use numbers not titles

**Chapter Context:**
This appears to be from a PhD thesis on fluid-structure interaction and acoustics. Pay attention to:
- Technical terminology and mathematical notation
- Equation numbering schemes
- Academic writing conventions from 1992

**Output Format:**
Provide clean markdown without code block markers. Focus on creating a complete, coherent chapter that flows naturally from page to page.

**CRITICAL TEXT COMPLETENESS**:
- MUST transcribe ALL text content, including transitional sentences that bridge concepts
- Do NOT skip any explanatory text, especially technical method descriptions
- Include connector phrases like "This approach...", "Similarly...", "In contrast...", etc.
- Ensure mathematical derivations and their explanatory text are complete
- Pay special attention to sentences that continue across page boundaries

Skip any page headers, footers, or page numbers. Focus only on the main academic content.

**Critical Linking Requirements:**
- Create links to figures: [Figure 2.1](#figure-2-1), [Fig. 2.1](#figure-2-1)
- Create links to equations: [equation (2.1)](#equation-2-1), [Eq. (2.1)](#equation-2-1)
- Create links to tables: [Table 2.1](#table-2-1), [Tab. 2.1](#table-2-1)
- Create links to sections: [Section 2.1](#section-2-1), [Sec. 2.1](#section-2-1)
- **CRITICAL - Literature References**: Convert ALL citation patterns to markdown links:
  * "Author [Year]" → [Author [Year]](#bib-author-year) e.g., [Jennings [1977]](#bib-jennings-1977)
  * "Author (Year)" → [Author (Year)](#bib-author-year) e.g., [Smith (1990)](#bib-smith-1990)
  * "Author et al. [Year]" → [Author et al. [Year]](#bib-author-et-al-year) e.g., [Jones et al. [1985]](#bib-jones-et-al-1985)
  * "Author and Author [Year]" → [Author and Author [Year]](#bib-author-author-year) e.g., [Burton and Miller [1971]](#bib-burton-miller-1971)
- Use lowercase, hyphenated anchor references matching the anchor IDs
"""
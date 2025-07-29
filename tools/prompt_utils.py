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
   - Inline equations: $variable$ (NOT \\(variable\\))
   - Display equations: $$equation$$ (NOT \\[equation\\])
   - **CRITICAL**: Opening $$ must NOT have newline after it
   - **CRITICAL**: Closing $$ must NOT have newline before it
   - Numbered equations: $$\\begin{align*} equation \\tag{2.5.1} \\end{align*}$$"""


def get_figure_formatting_section():
    """Get figure formatting requirements section."""
    return """**FIGURE FORMATTING**: Use HTML picture element format for dual theme support:

<a id="figure-x-y"></a>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/figure-x-y-dark.png">
  <source media="(prefers-color-scheme: light)" srcset="assets/figure-x-y.png">
  <img alt="Figure X.Y. Caption text here." src="assets/figure-x-y.png">
</picture>
Figure X.Y. Caption text here.

**Requirements**: Anchor BEFORE picture element, both themes, full alt text, plain caption below"""


def get_anchor_generation_section():
    """Get anchor generation requirements section."""
    return """**ANCHOR GENERATION**:
   - Headers: ## 2.1 Section Title <a id="section-2-1"></a>
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
   - References: [Author (Year)](#bib-author-year)"""


def get_pdf_text_guidance_section(text_context):
    """Get PDF text guidance section."""
    if not text_context:
        return "**PDF TEXT GUIDANCE**: No text context available."
    
    return f"""**PDF TEXT GUIDANCE**: Use this extracted text to verify accuracy and completeness:

{text_context[:1000]}{'...' if len(text_context) > 1000 else ''}

This text should help you understand the content structure and ensure nothing is missed."""


def get_output_requirements_section():
    """Get output requirements section."""
    return """**OUTPUT REQUIREMENTS**:
- Provide clean markdown without code block markers
- Focus on creating complete, coherent content
- Skip page headers, footers, or page numbers
- Maintain academic writing conventions and technical precision"""
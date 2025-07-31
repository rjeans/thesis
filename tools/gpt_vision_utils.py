#!/usr/bin/env python3
"""
GPT-4 Vision API utilities for thesis conversion workflow.

This module provides standardized interfaces for GPT-4 Vision API calls
including image encoding, prompt templates, and response handling.
"""

import base64
import openai
import time
import shutil
from pathlib import Path
from progress_utils import print_progress, time_operation


def encode_images_for_vision(image_paths, show_progress=True):
    """
    Encode PNG images as base64 for GPT-4 Vision API.

    Converts local image files to the base64 format required by the
    OpenAI Vision API. Handles multiple images for multi-page processing.

    Args:
        image_paths (list): List of Path objects pointing to PNG files
        show_progress (bool): Whether to show encoding progress

    Returns:
        list: List of image content dictionaries for Vision API
    """
    if show_progress:
        print_progress("Encoding images for GPT-4 Vision...")

    image_contents = []

    for i, image_path in enumerate(image_paths):
        if show_progress:
            print_progress(f"Encoding page image", i+1, len(image_paths))

        try:
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                image_contents.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                })
        except Exception as e:
            print_progress(f"- Error encoding {image_path}: {e}")

    return image_contents


def call_gpt_vision_api(prompt, image_contents, model="gpt-4o", max_tokens=3000, api_key=None):
    """
    Make a GPT-4 Vision API call with proper error handling and timing.

    Standardized interface for all GPT-4 Vision API calls in the thesis
    conversion workflow. Includes timing, error handling, and progress reporting.

    Args:
        prompt (str): Text prompt for the Vision API
        image_contents (list): List of encoded image dictionaries
        model (str): OpenAI model to use (default "gpt-4o")
        max_tokens (int): Maximum tokens in response (default 3000)
        api_key (str, optional): OpenAI API key (uses openai.api_key if None)

    Returns:
        str: API response content, or error message starting with "Error:"
    """
    if api_key:
        openai.api_key = api_key

    # Prepare message content
    content = [{"type": "text", "text": prompt}] + image_contents

    print_progress("Sending to GPT-4 Vision API...")
    print_progress("Processing with AI (estimated 30-60 seconds)...")

    try:
        with time_operation("GPT-4 Vision API call"):
            response = openai.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user",
                    "content": content
                }],
                max_tokens=max_tokens
            )

        return response.choices[0].message.content

    except Exception as e:
        print_progress(f"- GPT-4 Vision API error: {str(e)}")
        return f"Error: {str(e)}"


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
        "tables": "tables list from this 1992 PhD thesis and extract all table information"
    }

    instructions = {
        "contents": [
            "Extract ALL table of contents entries visible on the page provided.",
            "Do not infer or guess any content that is not explicitly visible.",
            "Identify section types: front_matter, chapter, appendix, back_matter",
            "Include complete subsection hierarchies with proper level numbering as seen on the page.",
            "Preserve exact capitalization and punctuation",
            "CRITICAL: If a title contains mathematical notation, enclose it in inline LaTeX delimiters (e.g., $...$)",
            "For chapters, extract chapter_number from title",
            "CRITICAL: Extract only the start_page for each section/subsection. Do NOT include or calculate end_page."
        ],
        "figures": [
            "Extract ALL figures listed exactly as shown",
            "Include complete figure titles/captions",
            "Extract page numbers accurately",
            "Determine chapter number from figure numbering (e.g., \"2.1\" = chapter 2)",
            "Preserve exact capitalization and punctuation in titles",
            "Include figures with complex numbering like \"3.5.6\""
        ],
        "tables": [
            "Extract ALL tables listed exactly as shown",
            "Include complete table titles/captions",
            "Extract page numbers accurately",
            "Determine chapter number from table numbering (e.g., \"4.1\" = chapter 4)",
            "Preserve exact capitalization and punctuation in titles",
            "If no tables are found, return an empty tables list"
        ]
    }

    description = content_descriptions.get(content_type, f"{content_type} from this document")
    instruction_list = instructions.get(content_type, [])

    prompt = f"""
Parse the {description} from the single page image provided.

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
   - Display equations: $$equation$$ or $$\\begin{{align*}} equation \\tag{{number}} \\end{{align*}}$$
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
- Bibliographic references: [Author (Year)](#bib-author-year), e.g., [Smith (1990)](#bib-smith-1990)
- Reference format: [Burton and Miller (1971)](#bib-burton-miller-1971)
- Multiple authors: [Jones et al. (1985)](#bib-jones-et-al-1985)
- Use lowercase, hyphenated anchor references matching the anchor IDs
"""


def cleanup_temp_directory(temp_dir):
    """
    Clean up temporary directory used for image processing.

    Safely removes temporary directories created during PDF to image
    conversion, with error handling for cleanup failures.

    Args:
        temp_dir (str): Path to temporary directory to remove
    """
    try:
        print_progress("Cleaning up temporary files...")
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception as e:
        print_progress(f"- Warning: Could not clean up {temp_dir}: {e}")


def clean_markdown_output(result):
    """
    Clean markdown output from GPT-4 Vision API responses.

    Removes common markdown code block markers that the API sometimes
    includes in responses, ensuring clean markdown content.

    Args:
        result (str): Raw response from GPT-4 Vision API

    Returns:
        str: Cleaned markdown content
    """
    cleaned_result = result.strip()

    # Remove markdown code block markers
    if cleaned_result.startswith('```markdown'):
        cleaned_result = cleaned_result[11:]
    elif cleaned_result.startswith('```'):
        cleaned_result = cleaned_result[3:]

    if cleaned_result.endswith('```'):
        cleaned_result = cleaned_result[:-3]

    return cleaned_result.strip()
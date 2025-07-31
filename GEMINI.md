# Project Overview

This project converts a 1992 PhD thesis from PDF to Markdown. The core of the project is a sophisticated workflow that uses GPT-4 Vision to parse the document's structure and content, and then uses a suite of Python tools to process and assemble the final Markdown output.

## Current Status

The project is in a mature state. The most critical and complex part of the workflow—parsing the table of contents (TOC) to create a structural representation of the document—is complete and robust. The system can now accurately extract the full hierarchy of the thesis, including chapters, sections, and subsections, and correctly calculate the page ranges for each entry.

## Key Technical Solution: TOC Parsing

The successful TOC parsing solution is a hybrid, multi-stage approach that combines AI and deterministic code:

1.  **AI for Visual Extraction:** GPT-4 Vision is used to process each page of the TOC individually. The AI's task is to extract the raw text and basic hierarchical information from each page.
2.  **Intelligent Code for Stitching and Merging:** A Python script then takes the raw data from all pages and intelligently merges the sections together, correctly handling entries that span page boundaries.
3.  **Deterministic Code for Page Range Calculation:** Once the complete TOC is reassembled, a final Python function calculates the `end_page` for every entry by comparing it to the `start_page` of the next entry.

This approach has proven to be highly reliable and accurate.

## Next Steps

With the document structure now accurately parsed, the next steps will focus on:

*   **Content Extraction:** Using the generated `thesis_contents.yaml` file to extract the content of each chapter and section.
*   **Markdown Conversion:** Converting the extracted content into clean, well-formatted Markdown.
*   **Figure and Table Extraction:** Extracting all figures and tables and inserting them into the Markdown files.
*   **Final Assembly:** Assembling the complete thesis in Markdown, with all cross-references and links correctly resolved.

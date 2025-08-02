# Project Overview

This project converts a 1992 PhD thesis from PDF to Markdown. The core of the project is a sophisticated workflow that uses GPT-4 Vision to parse the document's structure and content, and then uses a suite of Python tools to process and assemble the final Markdown output.

## Current Status

The project is now production-ready with comprehensive automation. The most critical part—parsing the table of contents (TOC)—is complete and robust. The system features an advanced section-aware processor with automated post-processing that fixes common GPT-4 formatting issues (equations, delimiters, LaTeX syntax), making the entire workflow fully autonomous and reliable.

## Key Technical Solution: TOC Parsing

The successful TOC parsing solution is a hybrid, multi-stage approach that combines AI and deterministic code:

1.  **AI for Visual Extraction:** GPT-4 Vision is used to process each page of the TOC individually. The AI's task is to extract the raw text and basic hierarchical information from each page.
2.  **Intelligent Code for Stitching and Merging:** A Python script then takes the raw data from all pages and intelligently merges the sections together, correctly handling entries that span page boundaries.
3.  **Deterministic Code for Page Range Calculation:** Once the complete TOC is reassembled, a final Python function calculates the `end_page` for every entry by comparing it to the `start_page` of the next entry.

This approach has proven to be highly reliable and accurate.

## Recent Improvements

The system now includes several major enhancements:

*   **Section-Aware Processing:** Intelligent handling of hierarchical content at any level (2.1, 2.1.1, 2.1.2.1)
*   **Automated Post-Processing:** Built-in correction of GPT-4 equation formatting issues (multi-line equations, inline delimiters)
*   **Incremental Output:** Files are written as each section completes, providing real-time progress feedback
*   **Token Optimization:** Each section uses minimal page ranges to avoid API limits and improve efficiency
*   **Automatic Subsection Discovery:** Parent sections automatically process all child sections
*   **Debug Transparency:** Saves prompts, text context, and individual outputs for inspection
*   **Quality Assurance:** Real-time detection and correction of formatting issues
*   **Rationalized Architecture:** Clean, simplified codebase with focused functionality

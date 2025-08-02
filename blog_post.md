# Converting a 1992 PhD Thesis to Markdown: The Final, Robust Solution for TOC Parsing

After a series of trials and errors, I've finally arrived at a robust and reliable solution for parsing the table of contents (TOC) of my 1992 PhD thesis. This is a critical step, as the TOC provides the structural backbone for the entire conversion process. My journey highlights a key lesson: the most effective solutions often combine the strengths of AI with the precision of deterministic code.

## The Challenge: Why TOC Parsing is So Hard

The TOC of a scanned PDF is a minefield of potential errors:

*   **Visual Layout:** The hierarchical structure is conveyed through indentation and formatting, which is difficult for traditional text extraction to understand.
*   **Continuity:** Chapters and sections often span multiple pages, requiring context to be correctly stitched together.
*   **Token Limits:** Passing the entire TOC to a language model can exceed token limits, leading to incomplete or truncated results.
*   **Mathematical Notation:** Section titles can contain mathematical expressions that need to be correctly formatted.

My initial attempts to solve this problem with a single, all-encompassing AI prompt proved to be unreliable. The AI struggled with the combination of visual layout, continuity, and the need for precise calculations.

## The Solution: A Hybrid, Multi-Stage Approach

The final, successful solution is a multi-stage process that intelligently divides the labor between AI and code:

1.  **AI for Visual Extraction (Per-Page):**
    *   I use GPT-4 Vision to process each page of the TOC individually. The AI's task is simple and focused: extract the raw text and basic hierarchical information that it sees on that single page. This leverages the AI's strength in visual pattern recognition without asking it to make complex logical leaps.

2.  **Intelligent Code for Stitching and Merging:**
    *   Once I have the raw data from each page, a Python script takes over. It uses a context-aware function to intelligently merge the sections from consecutive pages. By keeping track of the last "active" chapter, it can correctly append subsections, even if they appear on a different page. This solves the problem of missing or duplicated sections at page boundaries.

3.  **Deterministic Code for Page Range Calculation:**
    *   With the complete and correct hierarchy reassembled, a final Python function calculates the `end_page` for every entry. It does this by creating a flat list of all sections and subsections, sorted by their `start_page`, and then setting the `end_page` of each entry to be the `start_page` of the next entry, minus one. This is a deterministic and 100% reliable method.

## The Result: A Solid Foundation

This hybrid approach has proven to be extremely effective. It produces a complete and accurate `thesis_contents.yaml` file that serves as the foundation for the rest of the conversion process. By using the right tool for the right job—AI for visual extraction, and code for logic and calculation—I've been able to create a solution that is both robust and reliable.

This experience has been a powerful reminder that the most effective AI-powered workflows are often those that don't try to do everything with a single prompt. By breaking down the problem into smaller, more manageable steps, and by using code to handle the deterministic parts of the process, we can build solutions that are far more powerful and reliable than what either AI or code could achieve on their own.

## Technical Architecture: Lessons Learned

Building this workflow taught me several crucial lessons about maintainable AI-powered systems:

### Unified Prompt Architecture
Initially, I had prompts scattered across multiple files, which led to inconsistencies and made updates difficult. The solution was to consolidate all prompts into a single `prompt_utils.py` file, creating a unified source of truth for all AI instructions. This architectural improvement eliminated prompt duplication and made the system much more maintainable.

### Section-Aware Processing
The breakthrough came with implementing hierarchical section processing. Instead of processing entire chapters at once (which hit token limits), I developed a system that intelligently handles any section level (2.1, 2.1.1, etc.) with automatic parent-child discovery. Parent sections process their intro content, then automatically continue with all subsections.

### Incremental Output for Real-Time Feedback
A key improvement was implementing incremental file writing. As each section completes processing, its output is immediately written to disk. This provides real-time progress feedback and allows you to see results without waiting for the entire run to finish—crucial for long-running AI processing tasks.

### Token Optimization
By processing sections in logical chunks rather than arbitrary page ranges, I achieved much better token efficiency. Each section uses only the pages it actually needs, avoiding the token capacity issues that plagued earlier approaches.

### Automated Post-Processing: The Final Piece
The last critical breakthrough was implementing automated post-processing within the conversion pipeline. Despite extremely detailed prompts, GPT-4 Vision would occasionally generate equations with line breaks inside `$$` blocks, violating LaTeX formatting requirements. Rather than fighting this inconsistency, I implemented intelligent post-processing that automatically detects and fixes these issues during the conversion process.

The system now includes:
- Real-time equation formatting correction (multi-line → single-line)
- Inline equation delimiter standardization (\(...\) → $...$)
- LaTeX bracket notation conversion (\[...\] → $$...$$)
- Enhanced LaTeX syntax guidance (complex superscripts with braces)
- Quality assurance reporting with detailed fix statistics
- Comprehensive formatting validation

This automated correction layer makes the entire workflow truly autonomous—no manual cleanup required.

## The Bottom Line

These architectural decisions transformed a brittle, hard-to-debug system into a robust, production-ready workflow that handles complex hierarchical content intelligently. The key lesson: successful AI workflows combine the strengths of AI (visual pattern recognition, content understanding) with the reliability of deterministic code (logic, validation, post-processing). The automated post-processing layer handles common GPT-4 formatting inconsistencies (equation delimiters, LaTeX syntax) while enhanced prompts guide proper mathematical notation. The result is a system that's both powerful and predictable.

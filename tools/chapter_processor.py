#!/usr/bin/env python3
"""
Chapter processor implementation using batching strategy to avoid token limits.

This module provides a concrete implementation of ChapterProcessorBase for
processing thesis chapters with context-enhanced conversion and proper
content merging across page batches.

Usage:
    python chapter_processor.py thesis.pdf "Chapter 2" chapter_2.md --structure-dir structure/
    python chapter_processor.py thesis.pdf "2" chapter_2.md --structure-dir structure/ --batch-size 3
"""

import sys
import argparse
import json
from pathlib import Path
import re
import tempfile
import openai
import os

# Import base class and utilities
from chapter_processor_base import ChapterProcessorBase
from progress_utils import print_progress, print_completion_summary, print_section_header
from convert_with_context import create_chapter_prompt, create_context_enhanced_prompt
from pdf_utils import extract_pages_to_pdf, pdf_to_images, extract_text_from_pdf_page
from gpt_vision_utils import encode_images_for_vision


class ChapterProcessor(ChapterProcessorBase):
    """
    Concrete implementation of chapter processing with batching strategy.
    
    This class handles the conversion of thesis chapters to markdown using
    page-by-page processing to avoid token limits while maintaining content
    continuity and academic formatting standards.
    """
    
    def __init__(self, pdf_path, structure_dir=None, batch_size=2, content_type="chapter", enable_diagnostics=False):
        """
        Initialize the chapter processor.
        
        Args:
            pdf_path (str): Path to source PDF file
            structure_dir (str, optional): Directory containing YAML structure files
            batch_size (int): Number of pages to process in each batch
            content_type (str): Type of content being processed
            enable_diagnostics (bool): Enable comprehensive page-by-page diagnostics
        """
        super().__init__(pdf_path, structure_dir, batch_size)
        self.content_type = content_type
        self.enable_diagnostics = enable_diagnostics
        
        # Initialize diagnostics tracking
        if self.enable_diagnostics:
            # Force single-page processing for diagnostics
            self.batch_size = 1
            self.diagnostics = {
                'pages': {},
                'structure_validation': {},
                'content_metrics': {},
                'errors': []
            }
    
    def create_batch_prompt(self, chapter_info, start_page, end_page, batch_index, total_batches, text_context):
        """
        Create a processing prompt for a specific batch of pages.
        
        Args:
            chapter_info (dict): Chapter information from structure
            start_page (int): Starting page number for batch
            end_page (int): Ending page number for batch
            batch_index (int): Current batch index (0-based)
            total_batches (int): Total number batches
            text_context (str): Extracted text context for guidance
            
        Returns:
            str: Formatted prompt for GPT-4 Vision
        """
        chapter_num = chapter_info.get('chapter_number', '?')
        chapter_title = chapter_info.get('title', 'Unknown Chapter')
        
        # Build context about the batch position
        batch_context = ""
        if total_batches > 1:
            if batch_index == 0:
                batch_context = f"This is the FIRST batch of {total_batches} batches for this chapter. Focus on the chapter introduction and early content."
            elif batch_index == total_batches - 1:
                batch_context = f"This is the FINAL batch ({batch_index + 1} of {total_batches}) for this chapter. Focus on conclusions and chapter wrap-up."
            else:
                batch_context = f"This is batch {batch_index + 1} of {total_batches} for this chapter. Focus on continuing the chapter content flow."
        
        # Create the prompt
        prompt = f"""Convert this batch of PDF pages from Chapter {chapter_num} to clean, academic markdown format.

CHAPTER CONTEXT:
- Chapter {chapter_num}: {chapter_title}
- Pages {start_page}-{end_page} (batch {batch_index + 1} of {total_batches})
- {batch_context}

BATCH PROCESSING INSTRUCTIONS:
1. CRITICAL: Read the entire PDF content from top to bottom without missing any text
   - Include ALL sentences and paragraphs, especially transitional text between sections
   - Pay attention to continuation text that may appear before section headers
   - Do NOT skip connector sentences that provide context or bridge between topics
   - SPECIFICALLY INCLUDE: Any sentences that reference technical methods, formulations, or comparisons
     Examples: "As the boundary layer formulation...", "This hybrid formulation is analogous to...", 
     "Similar to the Burton and Miller...", references to "SHIE", "DSHIE", etc.

2. CONTENT CONTINUITY:
   - If this is a middle or final batch, content may continue from previous pages
   - Do NOT repeat chapter title or major section headers if they appeared in previous batches
   - Focus on the new content while maintaining flow from previous sections
   - Look for partial sentences or paragraphs that continue from the previous page

3. MATHEMATICAL FORMATTING (CRITICAL - STRICTLY ENFORCE):
   - Inline equations: $equation$ (use single dollar signs)
   - Display equations: $$equation$$ (use double dollar signs)
   - Numbered equations: $$\\begin{{align*}} equation \\tag{{2.1}} \\end{{align*}}$$
   - **FORBIDDEN DELIMITERS**: NEVER use \\(...\\) or \\[...\\] - these are incorrect
   - **REQUIRED DELIMITERS**: ALWAYS use $...$ for inline math and $$...$$ for display math
   - **VALIDATION**: Every equation must use $ or $$ delimiters, no exceptions

4. CRITICAL ANCHOR GENERATION for markdown viewer compatibility:
   - Section headers: ## 2.1 Section Title <a id="section-2-1"></a>
   - Subsection headers: ### 2.1.1 Subsection Title <a id="section-2-1-1"></a>
   - Figures: <a id="figure-2-1"></a>
     <picture>
       <source media="(prefers-color-scheme: dark)" srcset="assets/figure-2-1-dark.png">
       <source media="(prefers-color-scheme: light)" srcset="assets/figure-2-1.png">
       <img alt="Figure 2.1. Caption" src="assets/figure-2-1.png">
     </picture>
     Figure 2.1. Caption
   - Equations: <a id="equation-2-1"></a>
     $$
     \\begin{{align*}} equation \\tag{{2.1}} \\end{{align*}}
     $$
   - Tables: <a id="table-2-1"></a> before table content

5. CONTENT-SPECIFIC PROCESSING:
   - Preserve figure and table references (e.g., "see Figure 2.1", "Table 2.3 shows")
   - Maintain academic writing style and technical precision
   - Include all mathematical derivations and technical details
   - Do NOT convert standalone numbers to math format (page numbers, years, references, etc.)
   - Use proper markdown formatting for lists, emphasis, and structure

6. IMPORTANT - PDF text guidance:
   The following text was extracted from these pages to help guide your conversion:
   
   {text_context[:2000]}{'...' if len(text_context) > 2000 else ''}
   
   Use this text as reference for:
   - Verifying mathematical equations and symbols
   - Cross-checking figure and table references  
   - Understanding section structure and hierarchy
   - Ensuring accurate content conversion
   - CRITICAL: Identifying transitional sentences that may be missed visually
   - **MATHEMATICAL FORMAT VERIFICATION**: Ensure all equations use $$...$$ not \\[...\\]
   
   The extracted text may contain OCR artifacts and line breaks - rely primarily on the visual content but MUST include transitional text found in the extracted text.
   
   **MATHEMATICAL FORMATTING REMINDER**: If you see any LaTeX equations in the source, convert them using:
   - Display equations: $$equation$$ (NOT \\[equation\\])
   - Inline equations: $equation$ (NOT \\(equation\\))

FORMATTING REQUIREMENTS:
- Return ONLY the converted markdown content (no ```markdown delimiters)
- Do not include explanatory text before or after the markdown
- Preserve the original visual layout and structure
- Ensure mathematical symbols are formatted correctly (only actual math expressions)
- Preserve academic writing style and technical precision

**FINAL VALIDATION BEFORE RESPONDING**:
- Check that ALL mathematical expressions use $ or $$ delimiters
- Verify NO equations use \\[...\\] or \\(...\\) delimiters
- Confirm all anchors are properly formatted with HTML <a id="..."></a> tags

Convert the pages shown in the images to clean, well-structured markdown following these requirements exactly."""
        
        return prompt
    
    def clean_batch_result(self, result, start_page, end_page):
        """
        Clean and validate the result from a batch processing.
        
        Args:
            result (str): Raw result from GPT-4 Vision
            start_page (int): Starting page number for batch
            end_page (int): Ending page number for batch
            
        Returns:
            str: Cleaned and validated result
        """
        if not result:
            return ""
        
        # Clean the result
        cleaned = result.strip()
        
        # Remove markdown code block delimiters if present
        if cleaned.startswith('```markdown'):
            cleaned = cleaned[11:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        
        # Clean up extra whitespace
        cleaned = cleaned.strip()
        
        # CRITICAL: Fix any LaTeX delimiters that may have been generated
        # This is our safety net against incorrect mathematical formatting
        print_progress(f"  Checking mathematical formatting...")
        original_length = len(cleaned)
        
        # Fix display math delimiters
        cleaned = re.sub(r'\\\\?\[', '$$', cleaned)
        cleaned = re.sub(r'\\\\?\]', '$$', cleaned)
        
        # Fix inline math delimiters  
        cleaned = re.sub(r'\\\\?\(', '$', cleaned)
        cleaned = re.sub(r'\\\\?\)', '$', cleaned)
        
        # Count fixes made
        fixes_made = original_length != len(cleaned)
        if fixes_made:
            print_progress(f"  ! Fixed LaTeX delimiters in batch result")
        
        # Basic validation
        if len(cleaned) < 50:  # Too short, likely an error
            print_progress(f"- Warning: Very short result for pages {start_page}-{end_page} ({len(cleaned)} chars)")
        
        return cleaned
    
    def post_process_merged_content(self, content, chapter_info):
        """
        Post-process the merged content from all batches.
        
        Args:
            content (str): Merged content from all batches
            chapter_info (dict): Chapter information from structure
            
        Returns:
            str: Final processed content
        """
        if not content:
            return ""
        
        # Clean up multiple consecutive blank lines
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        # Ensure proper spacing around headers
        content = re.sub(r'\n(#+\s+)', r'\n\n\1', content)
        content = re.sub(r'(</a>)\n([^#\n])', r'\1\n\n\2', content)
        content = re.sub(r'(>\s*)\n\n(#+\s+)', r'\1\n\n\2', content)
        
        # Clean up spacing around equations
        content = re.sub(r'\n\$\$\n\s*\n', '\n$$\n', content)
        content = re.sub(r'\n\s*\n\$\$\n', '\n$$\n', content)
        
        # Ensure the content starts cleanly
        content = content.lstrip('\n')
        
        # Add chapter header if not present and this is a chapter
        chapter_num = chapter_info.get('chapter_number')
        chapter_title = chapter_info.get('title', '')
        
        if (self.content_type == "chapter" and chapter_num and 
            not content.startswith(f"# Chapter {chapter_num}") and
            not content.startswith(f"# {chapter_num}")):
            
            chapter_header = f"# Chapter {chapter_num}: {chapter_title} <a id=\"chapter-{chapter_num}\"></a>\n\n"
            content = chapter_header + content
        
        # FINAL MATHEMATICAL FORMATTING VALIDATION
        # This is our ultimate safety check to ensure no LaTeX delimiters remain
        print_progress("Performing final mathematical formatting validation...")
        original_content = content
        
        # Fix any remaining LaTeX delimiters
        content = re.sub(r'\\\\?\[', '$$', content)
        content = re.sub(r'\\\\?\]', '$$', content)
        content = re.sub(r'\\\\?\(', '$', content)
        content = re.sub(r'\\\\?\)', '$', content)
        
        # CRITICAL: Fix incorrect figure caption hyperlinks
        # Figure captions should be plain text, not hyperlinks, since we have HTML anchors
        print_progress("Fixing figure caption formatting...")
        caption_fixes = 0
        
        # Pattern: [Figure X.Y.](#figure-x-y-) Caption text → Figure X.Y. Caption text
        # This occurs after </picture> tags
        def fix_figure_caption(match):
            nonlocal caption_fixes
            caption_fixes += 1
            figure_text = match.group(1)  # e.g., "Figure 2.5."
            caption_text = match.group(2)  # e.g., " The thin shell geometry."
            return f"{figure_text}{caption_text}"
        
        # Fix figure captions that are incorrectly hyperlinked
        content = re.sub(r'\[(\bFigure\s+\d+\.\d+\.)\]\(#[^)]+\)([^\n]*)', fix_figure_caption, content)
        
        if caption_fixes > 0:
            print_progress(f"  Fixed {caption_fixes} figure caption hyperlinks")
        
        # Report if LaTeX delimiter fixes were made
        if content != original_content:
            latex_fixes = original_content != content.replace(r'\\\\?\[', '$$').replace(r'\\\\?\]', '$$').replace(r'\\\\?\(', '$').replace(r'\\\\?\)', '$')
            if latex_fixes:
                print_progress("! Fixed LaTeX delimiters in final content")
                # Count the fixes
                latex_brackets = original_content.count('\\[') + original_content.count('\\]')
                latex_parens = original_content.count('\\(') + original_content.count('\\)')
                if latex_brackets > 0:
                    print_progress(f"  Fixed {latex_brackets} LaTeX bracket delimiters")
                if latex_parens > 0:
                    print_progress(f"  Fixed {latex_parens} LaTeX parenthesis delimiters")
            
            if caption_fixes == 0 and not latex_fixes:
                print_progress("+ Mathematical formatting validation passed")
        else:
            print_progress("+ Mathematical formatting validation passed")
        
        return content
    
    def remove_duplicate_headers(self, new_content, previous_content):
        """
        Enhanced duplicate header removal for chapter content.
        
        Args:
            new_content (str): New batch content
            previous_content (str): Previously processed content
            
        Returns:
            str: Cleaned new content without duplicates
        """
        if not new_content or not previous_content:
            return new_content
        
        lines = new_content.split('\n')
        previous_lines = previous_content.split('\n')
        
        # Get headers and their anchors from previous content
        previous_headers = set()
        previous_anchors = set()
        
        for line in previous_lines:
            line_stripped = line.strip()
            # Headers with anchors
            if line_stripped.startswith('#') and '<a id=' in line_stripped:
                previous_headers.add(line_stripped)
                # Extract anchor ID
                anchor_match = re.search(r'<a id="([^"]+)">', line_stripped)
                if anchor_match:
                    previous_anchors.add(anchor_match.group(1))
        
        # Filter out duplicate headers and their anchors from new content
        filtered_lines = []
        skip_next = False
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            if skip_next:
                skip_next = False
                continue
            
            # Check for duplicate headers
            if line_stripped.startswith('#') and '<a id=' in line_stripped:
                if line_stripped in previous_headers:
                    print_progress(f"  Removing duplicate header: {line_stripped[:50]}...")
                    continue
                
                # Check for duplicate anchor IDs
                anchor_match = re.search(r'<a id="([^"]+)">', line_stripped)
                if anchor_match and anchor_match.group(1) in previous_anchors:
                    print_progress(f"  Removing duplicate anchor: {anchor_match.group(1)}")
                    continue
            
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def diagnose_page_content(self, page_num, content, chapter_info):
        """
        Comprehensive diagnostic analysis of a single page's content.
        
        Args:
            page_num (int): Page number being analyzed
            content (str): Generated markdown content for the page
            chapter_info (dict): Chapter information from structure
            
        Returns:
            dict: Detailed diagnostic information
        """
        if not content:
            return {
                'status': 'ERROR',
                'content_length': 0,
                'word_count': 0,
                'elements': {},
                'issues': ['No content generated']
            }
        
        # Basic content metrics
        content_length = len(content)
        word_count = len(content.split())
        line_count = len(content.split('\n'))
        
        # Analyze content elements
        elements = {
            'headers': len(re.findall(r'^#+\s+', content, re.MULTILINE)),
            'anchors': len(re.findall(r'<a id="[^"]+"></a>', content)),
            'equations': {
                'inline': len(re.findall(r'\$[^$]+\$', content)),
                'display': len(re.findall(r'\$\$[^$]+\$\$', content)),
                'numbered': len(re.findall(r'\\tag\{[^}]+\}', content))
            },
            'figures': len(re.findall(r'<picture>', content)),
            'figure_references': len(re.findall(r'[Ff]igure\s+\d+\.\d+', content)),
            'tables': len(re.findall(r'<a id="table-[^"]+"></a>', content)),
            'citations': len(re.findall(r'\[[0-9,\s-]+\]', content))
        }
        
        # Check for expected structure elements based on chapter metadata
        expected_elements = self.get_expected_elements_for_page(page_num, chapter_info)
        structure_match = self.validate_against_expected_structure(page_num, content, expected_elements)
        
        # Identify potential issues
        issues = []
        if content_length < 100:
            issues.append(f"Very short content ({content_length} chars)")
        if word_count < 20:
            issues.append(f"Very few words ({word_count} words)")
        if not any(elements['equations'].values()) and 'chapter' in self.content_type.lower():
            issues.append("No mathematical content found (unusual for technical chapter)")
        if elements['headers'] == 0 and page_num > 1:
            issues.append("No section headers found")
        
        # Validate mathematical formatting
        math_issues = self.validate_math_formatting(content)
        issues.extend(math_issues)
        
        # Determine overall status
        if not content.strip():
            status = 'ERROR'
        elif len(issues) > 2:
            status = 'WARNING'
        elif content_length < 200:
            status = 'SUSPECT'
        else:
            status = 'OK'
        
        return {
            'status': status,
            'content_length': content_length,
            'word_count': word_count,
            'line_count': line_count,
            'elements': elements,
            'structure_match': structure_match,
            'issues': issues,
            'sample_content': content[:200] + '...' if len(content) > 200 else content
        }
    
    def get_expected_elements_for_page(self, page_num, chapter_info):
        """
        Get expected structural elements for a specific page based on metadata.
        
        Args:
            page_num (int): Page number
            chapter_info (dict): Chapter information
            
        Returns:
            dict: Expected elements for this page
        """
        expected = {
            'figures': [],
            'tables': [],
            'sections': []
        }
        
        # Check for figures on this page
        if 'figures' in self.structure_data:
            figures_data = self.structure_data['figures']
            if figures_data and 'figures' in figures_data:
                for fig in figures_data['figures']:
                    if fig.get('page') == page_num:
                        expected['figures'].append(fig)
        
        # Check for tables on this page
        if 'tables' in self.structure_data:
            tables_data = self.structure_data['tables']
            if tables_data and 'tables' in tables_data:
                for table in tables_data['tables']:
                    if table.get('page') == page_num:
                        expected['tables'].append(table)
        
        return expected
    
    def validate_against_expected_structure(self, page_num, content, expected_elements):
        """
        Validate generated content against expected structural elements.
        
        Args:
            page_num (int): Page number
            content (str): Generated content
            expected_elements (dict): Expected elements from metadata
            
        Returns:
            dict: Validation results
        """
        validation = {
            'figures': {'expected': 0, 'found': 0, 'missing': [], 'status': 'OK'},
            'tables': {'expected': 0, 'found': 0, 'missing': [], 'status': 'OK'},
            'overall_status': 'OK'
        }
        
        # Validate figures
        expected_figures = expected_elements.get('figures', [])
        validation['figures']['expected'] = len(expected_figures)
        
        found_figures = re.findall(r'figure-(\d+-\d+)', content, re.IGNORECASE)
        validation['figures']['found'] = len(found_figures)
        
        for fig in expected_figures:
            fig_num = fig.get('figure_number', '').replace('.', '-')
            if f"figure-{fig_num}" not in content.lower():
                validation['figures']['missing'].append(fig_num)
        
        if validation['figures']['missing']:
            validation['figures']['status'] = 'MISSING'
            validation['overall_status'] = 'WARNING'
        
        # Validate tables
        expected_tables = expected_elements.get('tables', [])
        validation['tables']['expected'] = len(expected_tables)
        
        found_tables = re.findall(r'table-(\d+-\d+)', content, re.IGNORECASE)
        validation['tables']['found'] = len(found_tables)
        
        for table in expected_tables:
            table_num = table.get('table_number', '').replace('.', '-')
            if f"table-{table_num}" not in content.lower():
                validation['tables']['missing'].append(table_num)
        
        if validation['tables']['missing']:
            validation['tables']['status'] = 'MISSING'
            validation['overall_status'] = 'WARNING'
        
        return validation
    
    def validate_math_formatting(self, content):
        """
        Validate mathematical formatting in content.
        
        Args:
            content (str): Content to validate
            
        Returns:
            list: List of math formatting issues
        """
        issues = []
        
        # Check for incorrect LaTeX delimiters (these should be automatically fixed)
        latex_brackets = content.count('\\[') + content.count('\\]')
        latex_parens = content.count('\\(') + content.count('\\)')
        
        if latex_brackets > 0:
            issues.append(f"Found {latex_brackets} LaTeX bracket delimiters (\\[...\\]) - these should be automatically fixed to $$...$$")
        if latex_parens > 0:
            issues.append(f"Found {latex_parens} LaTeX parenthesis delimiters (\\(...\\)) - these should be automatically fixed to $...$")
        
        # Check for unmatched dollar signs
        single_dollars = content.count('$')
        if single_dollars % 2 != 0:
            issues.append(f"Unmatched single dollar signs in math formatting (found {single_dollars} total)")
        
        # Check for empty math expressions
        empty_inline = re.findall(r'\$\s*\$', content)
        if empty_inline:
            issues.append(f"Found {len(empty_inline)} empty inline math expressions")
        
        empty_display = re.findall(r'\$\$\s*\$\$', content)
        if empty_display:
            issues.append(f"Found {len(empty_display)} empty display math expressions")
        
        # Check for common LaTeX commands that might need attention
        latex_commands = re.findall(r'\\[a-zA-Z]+\{[^}]*\}', content)
        if len(latex_commands) > 10:  # Threshold for potentially problematic LaTeX
            issues.append(f"High number of LaTeX commands detected ({len(latex_commands)}) - verify proper markdown conversion")
        
        return issues
    
    def report_page_diagnostics(self, page_num, diagnostics):
        """
        Report diagnostic results for a single page.
        
        Args:
            page_num (int): Page number
            diagnostics (dict): Diagnostic results
        """
        status = diagnostics['status']
        status_symbols = {'OK': '+', 'WARNING': '!', 'SUSPECT': '?', 'ERROR': '-'}
        symbol = status_symbols.get(status, '?')
        
        print_progress(f"  {symbol} Page {page_num} Status: {status}")
        print_progress(f"    Content: {diagnostics['content_length']} chars, {diagnostics['word_count']} words")
        
        elements = diagnostics['elements']
        print_progress(f"    Elements: {elements['headers']} headers, {sum(elements['equations'].values())} equations, {elements['figures']} figures")
        
        if diagnostics['issues']:
            print_progress(f"    Issues: {len(diagnostics['issues'])}")
            for issue in diagnostics['issues'][:3]:  # Show first 3 issues
                print_progress(f"      - {issue}")
            if len(diagnostics['issues']) > 3:
                print_progress(f"      ... and {len(diagnostics['issues']) - 3} more")
        
        # Show structure validation
        structure = diagnostics.get('structure_match', {})
        if structure.get('overall_status') == 'WARNING':
            print_progress(f"    Structure: Missing expected elements")
            if structure['figures']['missing']:
                print_progress(f"      Missing figures: {', '.join(structure['figures']['missing'])}")
            if structure['tables']['missing']:
                print_progress(f"      Missing tables: {', '.join(structure['tables']['missing'])}")
    
    def save_diagnostics(self, diagnostics_path, final_analysis):
        """
        Save comprehensive diagnostics to JSON file.
        
        Args:
            diagnostics_path (Path): Path for diagnostics file
            final_analysis (dict): Final content analysis
        """
        if not self.enable_diagnostics:
            return
            
        full_diagnostics = {
            'page_diagnostics': self.diagnostics['pages'],
            'processing_errors': self.diagnostics['errors'],
            'final_analysis': final_analysis,
            'structure_data_loaded': {
                'contents': 'contents' in self.structure_data,
                'figures': 'figures' in self.structure_data,
                'tables': 'tables' in self.structure_data
            }
        }
        
        try:
            with open(diagnostics_path, 'w', encoding='utf-8') as f:
                json.dump(full_diagnostics, f, indent=2, ensure_ascii=False)
            print_progress(f"+ Diagnostics written to: {diagnostics_path}")
        except Exception as e:
            print_progress(f"- Failed to save diagnostics: {e}")
    
    def analyze_final_content(self, content, chapter_info, start_page, end_page):
        """
        Analyze the final merged content for comprehensive validation.
        
        Args:
            content (str): Final merged content
            chapter_info (dict): Chapter information
            start_page (int): Starting page number
            end_page (int): Ending page number
            
        Returns:
            dict: Final content analysis
        """
        if not self.enable_diagnostics:
            return {}
            
        analysis = {
            'total_length': len(content),
            'total_words': len(content.split()),
            'total_lines': len(content.split('\n')),
            'elements_found': {},
            'page_coverage': {},
            'quality_score': 0
        }
        
        # Analyze content elements
        analysis['elements_found'] = {
            'headers': len(re.findall(r'^#+\s+', content, re.MULTILINE)),
            'anchors': len(re.findall(r'<a id="[^"]+"></a>', content)),
            'equations_inline': len(re.findall(r'\$[^$]+\$', content)),
            'equations_display': len(re.findall(r'\$\$[^$]+\$\$', content)),
            'figures': len(re.findall(r'<picture>', content)),
            'tables': len(re.findall(r'<a id="table-[^"]+"></a>', content)),
            'references': len(re.findall(r'[Ff]igure\s+\d+\.\d+|\[(\d+,?\s*)+\]', content))
        }
        
        # Analyze page coverage
        for page_num in range(start_page, end_page + 1):
            page_diag = self.diagnostics['pages'].get(page_num, {})
            analysis['page_coverage'][page_num] = {
                'status': page_diag.get('status', 'UNKNOWN'),
                'content_length': page_diag.get('content_length', 0),
                'word_count': page_diag.get('word_count', 0)
            }
        
        # Calculate quality score (0-100)
        quality_factors = []
        
        # Content completeness (40 points max)
        successful_pages = sum(1 for p in analysis['page_coverage'].values() if p['status'] == 'OK')
        total_pages = len(analysis['page_coverage'])
        quality_factors.append((successful_pages / total_pages) * 40)
        
        # Content richness (30 points max)
        avg_words_per_page = analysis['total_words'] / total_pages if total_pages > 0 else 0
        richness_score = min(avg_words_per_page / 200, 1.0) * 30  # 200 words per page as baseline
        quality_factors.append(richness_score)
        
        # Structural elements (30 points max)
        has_headers = min(analysis['elements_found']['headers'] / total_pages, 1.0) * 10
        has_equations = min((analysis['elements_found']['equations_inline'] + analysis['elements_found']['equations_display']) / total_pages, 1.0) * 10
        has_anchors = min(analysis['elements_found']['anchors'] / (total_pages * 2), 1.0) * 10
        quality_factors.extend([has_headers, has_equations, has_anchors])
        
        analysis['quality_score'] = int(sum(quality_factors))
        
        print_progress(f"Content quality score: {analysis['quality_score']}/100")
        print_progress(f"Total content: {analysis['total_length']} chars, {analysis['total_words']} words")
        print_progress(f"Elements: {analysis['elements_found']['headers']} headers, {analysis['elements_found']['equations_inline'] + analysis['elements_found']['equations_display']} equations")
        
        return analysis
    
    def process_page_batch(self, start_page, end_page, chapter_info, batch_index, total_batches):
        """
        Override base class method to add diagnostic capabilities.
        
        Args:
            start_page (int): Starting page number for batch
            end_page (int): Ending page number for batch
            chapter_info (dict): Chapter information from structure
            batch_index (int): Current batch index (0-based)
            total_batches (int): Total number of batches
            
        Returns:
            str: Processed markdown content for this batch
        """
        if self.enable_diagnostics:
            print_progress(f"=== PROCESSING PAGE {start_page} ===")
        else:
            print_progress(f"Processing batch {batch_index + 1}/{total_batches}: pages {start_page}-{end_page}")
        
        # Extract pages to temporary PDF
        with tempfile.TemporaryDirectory(prefix="chapter_batch_") as temp_dir:
            temp_pdf = Path(temp_dir) / f"batch_{batch_index}_{start_page}_{end_page}.pdf"
            
            if not extract_pages_to_pdf(str(self.pdf_path), str(temp_pdf), start_page, end_page):
                error_msg = f"Failed to extract pages {start_page}-{end_page}"
                print_progress(f"- {error_msg}")
                if self.enable_diagnostics:
                    self.diagnostics['errors'].append(error_msg)
                return ""
            
            # Convert to images
            images = pdf_to_images(str(temp_pdf), temp_dir, dpi=200, page_prefix=f"batch_{batch_index}")
            if not images:
                error_msg = f"Failed to convert pages {start_page}-{end_page} to images"
                print_progress(f"- {error_msg}")
                if self.enable_diagnostics:
                    self.diagnostics['errors'].append(error_msg)
                return ""
            
            # Encode for Vision API
            image_contents = encode_images_for_vision(images, show_progress=not self.enable_diagnostics)
            if not image_contents:
                error_msg = f"Failed to encode images for pages {start_page}-{end_page}"
                print_progress(f"- {error_msg}")
                if self.enable_diagnostics:
                    self.diagnostics['errors'].append(error_msg)
                return ""
            
            # Extract text context for this batch
            text_context = self.extract_chapter_text_context(start_page, end_page)
            if self.enable_diagnostics:
                print_progress(f"  Text context: {len(text_context)} characters")
            
            # Create batch-specific prompt
            prompt = self.create_batch_prompt(
                chapter_info, 
                start_page, 
                end_page, 
                batch_index, 
                total_batches,
                text_context
            )
            
            # Process with GPT-4 Vision
            try:
                if self.enable_diagnostics:
                    print_progress(f"  Sending page {start_page} to GPT-4 Vision...")
                
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt}
                        ] + image_contents
                    }],
                    max_tokens=4096,
                    temperature=0.1
                )
                
                if response.choices and response.choices[0].message:
                    result = response.choices[0].message.content
                    if result:
                        # Clean and validate result
                        cleaned_result = self.clean_batch_result(result, start_page, end_page)
                        
                        # Run diagnostics if enabled (for single-page processing)
                        if self.enable_diagnostics and start_page == end_page:
                            page_diagnostics = self.diagnose_page_content(start_page, cleaned_result, chapter_info)
                            self.report_page_diagnostics(start_page, page_diagnostics)
                            self.diagnostics['pages'][start_page] = page_diagnostics
                            
                            # Track errors
                            if page_diagnostics['status'] == 'ERROR':
                                error_msg = f"Page {start_page} failed diagnostics: {', '.join(page_diagnostics['issues'])}"
                                self.diagnostics['errors'].append(error_msg)
                        
                        print_progress(f"+ Successfully processed batch {batch_index + 1}")
                        return cleaned_result
                
                error_msg = f"Empty response for batch {batch_index + 1}"
                print_progress(f"- {error_msg}")
                if self.enable_diagnostics:
                    self.diagnostics['errors'].append(error_msg)
                return ""
                
            except Exception as e:
                error_msg = f"API error for batch {batch_index + 1}: {e}"
                print_progress(f"- {error_msg}")
                if self.enable_diagnostics:
                    self.diagnostics['errors'].append(error_msg)
                return ""
    
    def process_chapter(self, chapter_name, output_path):
        """
        Override base class method to add diagnostic reporting.
        
        Args:
            chapter_name (str): Chapter identifier
            output_path (str): Output file path for markdown
            
        Returns:
            bool: True if processing succeeded, False otherwise
        """
        if self.enable_diagnostics:
            print_section_header(f"DIAGNOSTIC CHAPTER PROCESSING: {chapter_name}")
        else:
            print_section_header(f"PROCESSING CHAPTER: {chapter_name}")
        
        # Find chapter information
        chapter_info = self.find_chapter_info(chapter_name)
        if not chapter_info:
            print_progress(f"- Chapter '{chapter_name}' not found in structure data")
            return False
        
        start_page = chapter_info.get('page_start')
        end_page = chapter_info.get('page_end')
        
        if not start_page or not end_page:
            print_progress(f"- Invalid page range for chapter '{chapter_name}'")
            return False
        
        print_progress(f"Chapter: {chapter_info.get('title', 'Unknown')}")
        print_progress(f"Pages: {start_page}-{end_page}")
        
        if self.enable_diagnostics:
            print_progress(f"Processing mode: Single page with comprehensive diagnostics")
        else:
            print_progress(f"Processing in {(end_page - start_page + self.batch_size) // self.batch_size} batch(es) of {self.batch_size} pages each")
        
        print_progress("")
        
        # Create page batches
        batches = self.create_batch_pages(start_page, end_page)
        
        # Process each batch
        batch_results = []
        successful_pages = 0
        warning_pages = 0
        error_pages = 0
        
        for i, (batch_start, batch_end) in enumerate(batches):
            result = self.process_page_batch(
                batch_start, batch_end, chapter_info, i, len(batches)
            )
            batch_results.append(result)
            
            # Count page statuses for diagnostics
            if self.enable_diagnostics and batch_start == batch_end:  # Single page
                page_diag = self.diagnostics['pages'].get(batch_start, {})
                status = page_diag.get('status', 'ERROR')
                if status == 'OK':
                    successful_pages += 1
                elif status in ['WARNING', 'SUSPECT']:
                    warning_pages += 1
                else:
                    error_pages += 1
            
            if self.enable_diagnostics:
                print_progress("")  # Space between pages
        
        # Report statistics for diagnostics mode
        if self.enable_diagnostics:
            print_section_header("PROCESSING STATISTICS")
            total_pages = end_page - start_page + 1
            print_progress(f"Total pages: {total_pages}")
            print_progress(f"Successful pages: {successful_pages}")
            print_progress(f"Warning pages: {warning_pages}")
            print_progress(f"Error pages: {error_pages}")
            print_progress("")
        
        # Merge batch results
        print_progress("Merging batch results...")
        merged_content = self.merge_batch_results(batch_results, chapter_info)
        
        if not merged_content:
            print_progress("- No content generated from batches")
            return False
        
        # Final content analysis for diagnostics
        final_analysis = {}
        if self.enable_diagnostics:
            print_section_header("FINAL CONTENT ANALYSIS")
            final_analysis = self.analyze_final_content(merged_content, chapter_info, start_page, end_page)
        
        # Save to output file
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(merged_content)
            
            print_progress(f"+ Chapter saved to: {output_path}")
            print_progress(f"+ Content length: {len(merged_content)} characters")
            
            # Save diagnostics if enabled
            if self.enable_diagnostics:
                diagnostics_path = Path(output_path).with_suffix('.diagnostics.json')
                self.save_diagnostics(diagnostics_path, final_analysis)
            
            return True
            
        except Exception as e:
            print_progress(f"- Failed to save chapter: {e}")
            return False


def main():
    """Main function for chapter processing."""
    parser = argparse.ArgumentParser(
        description='Process thesis chapters using batching strategy to avoid token limits',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process Chapter 2 with default settings
  python chapter_processor.py thesis.pdf "Chapter 2" chapter_2.md --structure-dir structure/

  # Process chapter by number with custom batch size
  python chapter_processor.py thesis.pdf "2" chapter_2.md --structure-dir structure/ --batch-size 3

  # Process front matter with smaller batches
  python chapter_processor.py thesis.pdf "Abstract" abstract.md --structure-dir structure/ --batch-size 1
  
  # Process with comprehensive diagnostics (single-page mode)
  python chapter_processor.py thesis.pdf "Chapter 2" chapter_2_diag.md --structure-dir structure/ --diagnostics

Features:
  - Standard mode: Batch processing for speed
  - Diagnostic mode: Page-by-page processing with comprehensive validation
  - Structure validation against YAML metadata
  - Quality scoring and detailed reporting
  - JSON diagnostics output for analysis
        """
    )
    
    parser.add_argument('pdf_path', help='Path to source PDF file')
    parser.add_argument('chapter_name', help='Chapter identifier (e.g., "Chapter 2", "2", "Abstract")')
    parser.add_argument('output_path', help='Output markdown file path')
    
    parser.add_argument('--structure-dir', required=True,
                       help='Directory containing YAML structure files')
    parser.add_argument('--batch-size', type=int, default=2,
                       help='Number of pages to process in each batch (default: 2)')
    parser.add_argument('--content-type', default='chapter',
                       choices=['chapter', 'front_matter', 'appendix', 'references'],
                       help='Type of content being processed (default: chapter)')
    parser.add_argument('--diagnostics', action='store_true',
                       help='Enable comprehensive page-by-page diagnostics (forces single-page processing)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.pdf_path).exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        return 1
    
    if not Path(args.structure_dir).exists():
        print(f"ERROR: Structure directory not found: {args.structure_dir}")
        return 1
    
    if args.batch_size < 1 or args.batch_size > 10:
        print(f"ERROR: Batch size must be between 1 and 10")
        return 1
    
    # Display processing information
    mode = "Diagnostic Mode" if args.diagnostics else "Batch Processing Mode"
    print(f"Chapter Processor - {mode}")
    print(f"PDF: {args.pdf_path}")
    print(f"Chapter: {args.chapter_name}")
    print(f"Output: {args.output_path}")
    print(f"Structure directory: {args.structure_dir}")
    if args.diagnostics:
        print(f"Processing: Page-by-page with comprehensive diagnostics")
    else:
        print(f"Batch size: {args.batch_size} pages")
    print(f"Content type: {args.content_type}")
    print("=" * 60)
    
    try:
        # Initialize processor
        processor = ChapterProcessor(
            args.pdf_path,
            args.structure_dir,
            args.batch_size,
            args.content_type,
            args.diagnostics
        )
        
        # Process the chapter
        success = processor.process_chapter(args.chapter_name, args.output_path)
        
        if success:
            print_completion_summary(
                args.output_path,
                1,
                f"chapter processed using {args.batch_size}-page batches"
            )
            return 0
        else:
            print("FAILED: Chapter processing unsuccessful")
            return 1
            
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
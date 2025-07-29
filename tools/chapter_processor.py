#!/usr/bin/env python3
"""
Simplified chapter processor focused on section-based processing.

This processor focuses on the subsection-aware approach which is the way forward
for the workflow, processing complete logical content units rather than arbitrary pages.
"""

import sys
import argparse
import json
from pathlib import Path
import tempfile
import openai
import os

# Import utilities
from progress_utils import print_progress, print_completion_summary, print_section_header
from pdf_utils import extract_pages_to_pdf, pdf_to_images, extract_text_from_pdf_page
from gpt_vision_utils import encode_images_for_vision, call_gpt_vision_api
from prompt_utils import (
    get_mathematical_formatting_section,
    get_anchor_generation_section, 
    get_cross_reference_section,
    get_output_requirements_section,
    get_pdf_text_guidance_section,
    get_content_transcription_requirements,
    get_figure_formatting_section
)
from subsection_utils import (
    load_chapter_subsections, 
    calculate_subsection_page_ranges,
    group_subsections_by_hierarchy,
    create_batch_info,
    print_subsection_batching_plan
)


class ChapterProcessor:
    """
    Simplified chapter processor focused on section-based processing.
    
    This processor uses subsection-aware processing to handle complete logical
    content units rather than arbitrary page breaks.
    """

    def __init__(self, pdf_path, structure_dir=None, max_pages_per_batch=3, 
                 enable_diagnostics=False):
        """
        Initialize the chapter processor.
        
        Args:
            pdf_path (str): Path to source PDF file
            structure_dir (str): Directory containing YAML structure files
            max_pages_per_batch (int): Maximum pages per subsection batch
            enable_diagnostics (bool): Enable comprehensive diagnostics
        """
        self.pdf_path = Path(pdf_path)
        self.structure_dir = Path(structure_dir) if structure_dir else None
        self.max_pages_per_batch = max_pages_per_batch
        self.enable_diagnostics = enable_diagnostics
        
        # Initialize diagnostics tracking
        if self.enable_diagnostics:
            self.diagnostics = {
                'batches': {},
                'processing_errors': [],
                'content_metrics': {}
            }
        
        print_progress(f"Processor initialized with max {max_pages_per_batch} pages per batch")
        if enable_diagnostics:
            print_progress("+ Comprehensive diagnostics ENABLED")

    def process_chapter(self, chapter_identifier, output_path):
        """
        Process a chapter using subsection-aware processing.
        
        Args:
            chapter_identifier (str): Chapter identifier (e.g., "2", "Chapter 2")
            output_path (str): Output markdown file path
        
        Returns:
            bool: True if processing succeeded, False otherwise
        """
        print_progress(f"Processing chapter: {chapter_identifier}")
        
        # Load chapter subsections
        if not self.structure_dir or not self.structure_dir.exists():
            print_progress("- No structure directory provided or found")
            return False
            
        chapter_data = load_chapter_subsections(str(self.structure_dir), chapter_identifier)
        if not chapter_data:
            print_progress(f"- Could not load chapter data for '{chapter_identifier}'")
            return False

        # Calculate subsection page ranges
        subsection_ranges = calculate_subsection_page_ranges(chapter_data)
        if not subsection_ranges:
            print_progress(f"- No subsections found for chapter '{chapter_identifier}'")
            return False

        # Group subsections into batches
        batches = group_subsections_by_hierarchy(subsection_ranges, self.max_pages_per_batch)
        if not batches:
            print_progress(f"- Could not create subsection batches")
            return False

        # Print batching plan
        print_subsection_batching_plan(batches, chapter_data)

        # Process each batch
        batch_results = []
        
        for batch_index, subsection_batch in enumerate(batches, 1):
            batch_info = create_batch_info(subsection_batch, chapter_data)
            if not batch_info:
                continue
                
            print_progress(f"Processing batch {batch_index}/{len(batches)}: {batch_info['batch_description']}")
            
            # Extract PDF text context for this batch
            text_context = self._extract_batch_text_context(
                batch_info['start_page'], batch_info['end_page']
            )
            
            # Create batch prompt
            prompt = self._create_subsection_batch_prompt(batch_info, text_context)
            
            # Process the batch
            result = self._process_batch(batch_info, prompt, batch_index)
            
            if result and not result.startswith("Error:"):
                cleaned_result = self._clean_batch_result(result)
                batch_results.append({
                    'batch_index': batch_index,
                    'batch_info': batch_info,
                    'content': cleaned_result,
                    'success': True
                })
                print_progress(f"+ Successfully processed batch {batch_index}")
            else:
                error_msg = f"Failed to process batch {batch_index}: {result}"
                print_progress(f"- {error_msg}")
                if self.enable_diagnostics:
                    self.diagnostics['processing_errors'].append(error_msg)

        # Merge batch results
        if batch_results:
            merged_content = self._merge_subsection_batches(batch_results, chapter_data)
            
            # Write to output file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(merged_content)
                
            # Save diagnostics if enabled
            if self.enable_diagnostics:
                diagnostics_path = Path(output_path).with_suffix('.diagnostics.json')
                self._save_diagnostics(diagnostics_path)
                
            print_completion_summary(output_path, len(batch_results), "subsection batches processed")
            return True
        
        return False

    def _extract_batch_text_context(self, start_page, end_page):
        """Extract text context from a page range for guidance."""
        text_context = ""
        
        for page_num in range(start_page, end_page + 1):
            page_text = extract_text_from_pdf_page(str(self.pdf_path), page_num)
            if page_text:
                text_context += f"\n--- Page {page_num} ---\n{page_text}"
        
        return text_context

    def _create_subsection_batch_prompt(self, batch_info, text_context):
        """Create a subsection-aware prompt for processing complete logical units."""
        section_titles = "\n".join(batch_info['section_titles'])
        batch_description = batch_info['batch_description']
        chapter_title = batch_info['chapter_title']
        
        prompt = f"""Convert this subsection content from a 1992 LaTeX academic thesis PDF to markdown format.

SUBSECTION BATCH INFORMATION:
- Chapter: {chapter_title}
- Processing: {batch_description} (pages {batch_info['start_page']}-{batch_info['end_page']})
- Content Type: Complete subsection(s) with logical boundaries

EXPECTED SECTION STRUCTURE:
{section_titles}

CRITICAL CONTENT REQUIREMENTS:
1. {get_content_transcription_requirements()}

2. **LOGICAL BOUNDARY AWARENESS**:
   - This batch contains complete subsection(s) with natural content boundaries
   - **IMPORTANT**: Include any parent section content that appears before the first subsection on the same page
   - Process the full logical flow from subsection introduction to conclusion
   - Maintain academic narrative structure within each subsection
   - Ensure mathematical derivations are complete with their explanatory context

3. {get_mathematical_formatting_section()}

4. {get_figure_formatting_section()}

5. {get_anchor_generation_section()}

6. {get_cross_reference_section()}

7. {get_pdf_text_guidance_section(text_context)}

8. **SUBSECTION PROCESSING GUIDELINES**:
   - Focus on complete logical units rather than arbitrary page breaks
   - Ensure smooth narrative flow within each subsection
   - Include complete mathematical derivations with their explanatory context
   - Maintain academic writing conventions and technical precision
   - Preserve figure and table references within subsection context

{get_output_requirements_section()}
"""
        
        return prompt

    def _process_batch(self, batch_info, prompt, batch_index):
        """Process a single batch of pages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            batch_pdf_path = Path(temp_dir) / f"batch_{batch_index}.pdf"
            
            # Extract pages for this batch
            success = extract_pages_to_pdf(
                str(self.pdf_path),
                str(batch_pdf_path),
                batch_info['start_page'],
                batch_info['end_page']
            )
            
            if not success:
                return f"Error: Failed to extract pages {batch_info['start_page']}-{batch_info['end_page']}"
            
            # Convert to images
            image_paths = pdf_to_images(str(batch_pdf_path), temp_dir)
            if not image_paths:
                return "Error: Failed to convert batch to images"
            
            # Encode images
            image_contents = encode_images_for_vision(image_paths)
            
            # Call GPT-4 Vision API
            result = call_gpt_vision_api(prompt, image_contents)
            
            return result

    def _clean_batch_result(self, result):
        """Clean and validate batch processing result."""
        if not result or result.startswith("Error:"):
            return result
        
        # Basic cleaning
        cleaned_result = result.strip()
        
        # Remove any markdown code block markers
        lines = cleaned_result.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            
            # Skip lines that are just code block markers
            if stripped_line in ["```", "```markdown", "```md"]:
                continue
                
            # Skip introductory text before code blocks
            if "converted content" in line.lower() or "markdown content" in line.lower():
                continue
                
            cleaned_lines.append(line)
        
        cleaned_result = '\n'.join(cleaned_lines)
        
        # Remove potential prompt leakage phrases
        prompt_leakage_patterns = [
            "Focus on maintaining the academic and technical precision",
            "ensuring coherence and completeness in the content delivery",
            "Focus on creating complete, coherent subsections",
            "within their logical boundaries",
            "Maintain academic writing conventions and technical precision",
            "Provide clean markdown without code block markers"
        ]
        
        for pattern in prompt_leakage_patterns:
            lines = cleaned_result.split('\n')
            cleaned_lines = []
            for line in lines:
                if pattern not in line:
                    cleaned_lines.append(line)
                else:
                    print_progress(f"- Removed prompt leakage: {line[:60]}...")
            cleaned_result = '\n'.join(cleaned_lines)
        
        return cleaned_result

    def _merge_subsection_batches(self, batch_results, chapter_data):
        """Merge subsection batch results into a coherent chapter."""
        chapter_title = chapter_data.get('title', 'Chapter')
        chapter_number = chapter_data.get('chapter_number', '')
        
        # Start with chapter header
        merged_content = f"# {chapter_title} <a id=\"chapter-{chapter_number}\"></a>\n\n"
        
        # Add each batch content
        for result in batch_results:
            if result['success'] and result['content']:
                # Clean and add batch content
                batch_content = result['content'].strip()
                
                # Remove any redundant chapter headers from individual batches
                import re
                batch_content = re.sub(r'^#\s+.*\n\n?', '', batch_content, flags=re.MULTILINE)
                
                merged_content += batch_content + "\n\n"
            else:
                # Add error placeholder
                batch_info = result['batch_info']
                merged_content += f"<!-- ERROR: Could not process {batch_info['batch_description']} -->\n\n"
        
        return merged_content

    def _save_diagnostics(self, diagnostics_path):
        """Save comprehensive diagnostics to JSON file."""
        if not self.enable_diagnostics:
            return
        
        try:
            with open(diagnostics_path, 'w', encoding='utf-8') as f:
                json.dump(self.diagnostics, f, indent=2, ensure_ascii=False)
            print_progress(f"+ Diagnostics saved to: {diagnostics_path}")
        except Exception as e:
            print_progress(f"- Failed to save diagnostics: {e}")


def main():
    """Main function for simplified chapter processing."""
    parser = argparse.ArgumentParser(
        description='Process thesis chapters with section-based processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process chapter 2 with section-aware batching
  python chapter_processor.py thesis.pdf "2" chapter_2.md --structure-dir structure/
  
  # Enable diagnostics for detailed analysis
  python chapter_processor.py thesis.pdf "Chapter 2" chapter_2.md --structure-dir structure/ --diagnostics
  
  # Custom batch size (pages per subsection batch)
  python chapter_processor.py thesis.pdf "2" chapter_2.md --structure-dir structure/ --max-pages 2

This processor focuses on subsection-aware processing for optimal content quality.
"""
    )
    
    parser.add_argument('pdf_path', help='Path to source PDF file')
    parser.add_argument('chapter_identifier', help='Chapter identifier (e.g., "2", "Chapter 2")')
    parser.add_argument('output_path', help='Output markdown file path')
    parser.add_argument('--structure-dir', required=True, help='Directory containing YAML structure files')
    parser.add_argument('--max-pages', type=int, default=3, help='Maximum pages per subsection batch (default: 3)')
    parser.add_argument('--diagnostics', action='store_true', help='Enable comprehensive diagnostics')
    
    args = parser.parse_args()

    # Validate input file
    if not Path(args.pdf_path).exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        return 1

    # Initialize processor
    print_section_header("SECTION-AWARE CHAPTER PROCESSING")
    print(f"PDF: {args.pdf_path}")
    print(f"Chapter: {args.chapter_identifier}")
    print(f"Output: {args.output_path}")
    print(f"Structure directory: {args.structure_dir}")
    print(f"Max pages per batch: {args.max_pages}")
    if args.diagnostics:
        print("Diagnostics: ENABLED")
    print("=" * 60)
    
    processor = ChapterProcessor(
        pdf_path=args.pdf_path,
        structure_dir=args.structure_dir,
        max_pages_per_batch=args.max_pages,
        enable_diagnostics=args.diagnostics
    )
    
    # Process chapter
    success = processor.process_chapter(
        args.chapter_identifier,
        args.output_path
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
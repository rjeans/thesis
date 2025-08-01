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
    load_individual_section,
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
        Process a chapter or individual section using subsection-aware processing.
        
        Args:
            chapter_identifier (str): Chapter identifier (e.g., "2", "Chapter 2") or section (e.g., "2.1", "2.1.1")
            output_path (str): Output markdown file path
        
        Returns:
            bool: True if processing succeeded, False otherwise
        """
        print_progress(f"Processing identifier: {chapter_identifier}")
        
        # Check if structure directory exists
        if not self.structure_dir or not self.structure_dir.exists():
            print_progress("- No structure directory provided or found")
            return False
        
        # Try to load as individual section first (if contains dots)
        if '.' in chapter_identifier and chapter_identifier.replace('.', '').isdigit():
            print_progress(f"Attempting to load as individual section: {chapter_identifier}")
            section_data = load_individual_section(str(self.structure_dir), chapter_identifier)
            if section_data:
                print_progress(f"+ Found individual section: {section_data['title']}")
                return self.process_individual_section(section_data, output_path)
        
        # Try to load as full chapter
        print_progress(f"Attempting to load as chapter: {chapter_identifier}")
        chapter_data = load_chapter_subsections(str(self.structure_dir), chapter_identifier)
        if not chapter_data:
            print_progress(f"- Could not load data for '{chapter_identifier}' as chapter or section")
            return False
        
        print_progress(f"+ Found chapter: {chapter_data.get('title', 'Unknown')}")

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
            text_context_path = Path(output_path).parent / f"batch_{batch_index}_text_context.txt"
            with open(text_context_path, 'w', encoding='utf-8') as f:
                f.write(text_context)
            
            # Create batch prompt
            prompt = self._create_subsection_batch_prompt(batch_info, text_context)
            prompt_path = Path(output_path).parent / f"batch_{batch_index}_prompt.txt"
            with open(prompt_path, 'w', encoding='utf-8') as f:
                f.write(prompt)
            print_progress(f"  Batch prompt saved to: {prompt_path}")
            
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
                
                # Store detailed diagnostics
                if self.enable_diagnostics:
                    self.diagnostics['batches'][f'batch_{batch_index}'] = {
                        'batch_description': batch_info['batch_description'],
                        'page_range': f"{batch_info['start_page']}-{batch_info['end_page']}",
                        'page_count': batch_info['page_count'],
                        'section_count': batch_info['subsection_count'],
                        'success': True,
                        'raw_content_length': len(result) if result else 0,
                        'cleaned_content_length': len(cleaned_result)
                    }
                
                print_progress(f"+ Successfully processed batch {batch_index}")
                batch_output_path = Path(output_path).parent / f"batch_{batch_index}.md"
                with open(batch_output_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_result)
                print_progress(f"  Batch content written to: {batch_output_path}")
            else:
                error_msg = f"Failed to process batch {batch_index}: {result}"
                print_progress(f"- {error_msg}")
                if self.enable_diagnostics:
                    self.diagnostics['processing_errors'].append(error_msg)
                    self.diagnostics['batches'][f'batch_{batch_index}'] = {
                        'batch_description': batch_info['batch_description'],
                        'page_range': f"{batch_info['start_page']}-{batch_info['end_page']}",
                        'page_count': batch_info['page_count'],
                        'section_count': batch_info['subsection_count'],
                        'success': False,
                        'error': error_msg
                    }


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

    def process_individual_section(self, section_data, output_path):
        """
        Process an individual section (e.g., 2.1, 2.1.1) rather than a full chapter.
        
        Args:
            section_data (dict): Section data with parent chapter context
            output_path (str): Output markdown file path
        
        Returns:
            bool: True if processing succeeded, False otherwise
        """
        section_info = section_data['section_data']
        chapter_title = section_data['chapter_title']
        section_number = section_info.get('section_number', '')
        section_title = section_info.get('title', '')
        
        print_progress(f"Processing individual section: {section_number} {section_title}")
        
        # Get page range for this section - use calculated range if available
        if 'calculated_page_range' in section_data:
            start_page = section_data['calculated_page_range']['start_page']
            end_page = section_data['calculated_page_range']['end_page']
            print_progress(f"+ Using calculated page range: {start_page}-{end_page}")
        else:
            # Fallback to single page
            start_page = section_info.get('start_page') or section_info.get('page')
            if start_page is None:
                print_progress(f"- No page information found for section {section_number}")
                return False
            end_page = section_info.get('end_page', start_page)
        
        print_progress(f"Section page range: {start_page}-{end_page}")
        
        # Create a simplified batch for this section
        batch_info = {
            'start_page': start_page,
            'end_page': end_page,
            'page_count': end_page - start_page + 1,
            'section_titles': [f"{section_number} {section_title}"],
            'batch_description': f"Section {section_number}",
            'chapter_title': chapter_title,
            'subsection_count': 1
        }
        
        # Extract PDF text context
        text_context = self._extract_batch_text_context(start_page, end_page)

        text_context_path = Path(output_path).parent / f"section_{section_number}_text_context.txt"
        with open(text_context_path, 'w', encoding='utf-8') as f:
            f.write(text_context)
        print_progress(f"  Text context saved to: {text_context_path}")
        
        if self.enable_diagnostics:
            print_progress(f"+ Diagnostic mode: Processing individual section")
            print_progress(f"  Section: {section_number} - {section_title}")
            print_progress(f"  Pages: {start_page}-{end_page} ({batch_info['page_count']} pages)")
            print_progress(f"  Text context: {len(text_context)} characters")
        
        # Create section-specific prompt
        prompt = self._create_individual_section_prompt(batch_info, text_context, section_data)
        prompt_path = Path(output_path).parent / f"section_{section_number}_prompt.txt"
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print_progress(f"  Prompt saved to: {prompt_path}")

        # Process the section
        result = self._process_batch(batch_info, prompt, 1)
        
        if result and not result.startswith("Error:"):
            cleaned_result = self._clean_batch_result(result)
            
            # Start with parent section content
            final_content = cleaned_result
            
            # Check if this is a parent section with child subsections
            all_subsections = section_data.get('all_subsections', [])
            child_subsections = [s for s in all_subsections if s.get('section_number', '') != section_number and s.get('section_number', '').startswith(section_number + '.')]
            
            if child_subsections:
                print_progress(f"+ Parent section processed, continuing with {len(child_subsections)} child subsections...")
                
                # Process each child subsection
                for child in child_subsections:
                    child_number = child.get('section_number', '')
                    child_title = child.get('title', '')
                    print_progress(f"  Processing child subsection: {child_number} {child_title}")
                    
                    # Create child section data structure
                    child_section_data = {
                        'type': 'individual_section',
                        'title': f"Section {child_number}: {child_title}",
                        'chapter_number': section_data.get('chapter_number'),
                        'chapter_title': section_data.get('chapter_title'),
                        'section_data': child,
                        'parent_chapter': section_data.get('parent_chapter'),
                        'all_subsections': [child],  # Only this child for processing
                        'calculated_page_range': {
                            'start_page': child.get('start_page', child.get('page', 0)),
                            'end_page': child.get('end_page', child.get('start_page', child.get('page', 0)))
                        }
                    }
                    
                    # Process the child subsection
                    child_result = self._process_child_subsection(child_section_data)
                    if child_result:
                        # Append child content to final content
                        final_content += "\n\n" + child_result
                        print_progress(f"  + Child subsection {child_number} processed successfully")
                    else:
                        print_progress(f"  - Failed to process child subsection {child_number}")
            
            # Write complete content to output file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            # Save diagnostics if enabled
            if self.enable_diagnostics:
                diagnostics_path = Path(output_path).with_suffix('.diagnostics.json')
                section_diagnostics = {
                    'processing_mode': 'individual_section',
                    'section_number': section_number,
                    'section_title': section_title,
                    'chapter_context': chapter_title,
                    'page_range': f"{start_page}-{end_page}",
                    'page_count': batch_info['page_count'],
                    'success': True,
                    'content_analysis': {
                        'character_count': len(final_content),
                        'line_count': len(final_content.split('\n')),
                        'equation_count': final_content.count('$$'),
                        'figure_references': final_content.count('[Figure ') + final_content.count('[Fig. '),
                        'section_headers': final_content.count('##') + final_content.count('###') + final_content.count('####'),
                        'anchor_count': final_content.count('<a id='),
                        'heading_level_used': '###' if len(section_number.split('.')) == 3 else '##'
                    },
                    'processing_details': {
                        'text_context_length': len(text_context),
                        'raw_result_length': len(result) if result else 0,
                        'cleaned_result_length': len(cleaned_result),
                        'prompt_used': 'individual_section_prompt'
                    }
                }
                self._save_section_diagnostics(diagnostics_path, section_diagnostics)
            
            print_completion_summary(output_path, 1, f"individual section processed")
            return True
        else:
            print_progress(f"- Failed to process individual section: {result}")
            return False

    def _extract_batch_text_context(self, start_page, end_page):
        """Extract text context from a page range for guidance."""
        text_context = ""

        text_context = extract_text_from_pdf_page(str(self.pdf_path), start_page, end_page)
 
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

    def _create_individual_section_prompt(self, batch_info, text_context, section_data):
        """
        Create a prompt for processing an individual section.
        
        Args:
            batch_info (dict): Information about the section batch
            text_context (str): Extracted PDF text for guidance
            section_data (dict): Section data with chapter context
        
        Returns:
            str: Formatted prompt for GPT-4 Vision API
        """
        section_info = section_data['section_data']
        section_number = section_info.get('section_number', '')
        section_title = section_info.get('title', '')
        chapter_title = section_data['chapter_title']
        all_subsections = section_data.get('all_subsections', [])
        
        # Determine correct heading level based on section numbering
        section_parts = section_number.split('.')
        if len(section_parts) == 2:  # e.g., "2.1"
            heading_level = "##"
            heading_type = "main section"
        elif len(section_parts) == 3:  # e.g., "2.1.1"
            heading_level = "###"
            heading_type = "subsection"
        elif len(section_parts) == 4:  # e.g., "2.1.1.1"
            heading_level = "####"
            heading_type = "sub-subsection"
        else:
            heading_level = "##"
            heading_type = "section"
        
        # Determine if this is a parent section with child subsections
        child_subsections = [s for s in all_subsections if s.get('section_number', '') != section_number and s.get('section_number', '').startswith(section_number + '.')]
        is_parent_section = len(child_subsections) > 0
        
        if is_parent_section:
            expected_structure = f"{section_number} {section_title} (parent section content only)"
            processing_mode = "PARENT_SECTION_ONLY"
        else:
            # Create expected subsection structure list for leaf sections
            expected_subsections = []
            for subsection in all_subsections:
                sub_number = subsection.get('section_number', '')
                sub_title = subsection.get('title', '')
                if sub_number and sub_title:
                    expected_subsections.append(f"{sub_number} {sub_title}")
            
            expected_structure = "\n".join(expected_subsections) if expected_subsections else f"{section_number} {section_title}"
            processing_mode = "COMPLETE_SECTION"
        
        prompt = f"""Convert this individual section from a 1992 LaTeX academic thesis PDF to markdown format.

INDIVIDUAL SECTION INFORMATION:
- Chapter Context: {chapter_title}
- Section: {section_number} {section_title}
- Processing: Individual {heading_type} (pages {batch_info['start_page']}-{batch_info['end_page']})
- Content Type: Complete {heading_type} with logical boundaries

EXPECTED SECTION STRUCTURE:
{expected_structure}

CRITICAL CONTENT REQUIREMENTS:
1. {get_content_transcription_requirements()}

2. **INDIVIDUAL SECTION PROCESSING** ({processing_mode}):
   - This is a single {heading_type} from a larger chapter
   - **CRITICAL HEADING LEVEL**: Use {heading_level} for the main section header
   - Start with: {heading_level} {section_number} {section_title} <a id="section-{section_number.replace('.', '-')}"></a>
   - **PROCESSING SCOPE**: {"Process ONLY the parent section content - extract the section heading and any introductory text that belongs directly to " + section_number + " but do NOT include any subsection content" if is_parent_section else "Process the complete section including ALL content from pages " + str(batch_info['start_page']) + "-" + str(batch_info['end_page'])}
   - {"CRITICAL: Stop processing when you encounter the first subsection heading (e.g., " + child_subsections[0].get('section_number', '') + ")" if is_parent_section and child_subsections else "Process complete logical flow from section introduction through conclusion"}
   - {"Focus on introductory material that sets up the overall section before diving into specific subsections" if is_parent_section else "Ensure comprehensive coverage of all section content"}

3. {get_mathematical_formatting_section()}

4. {get_figure_formatting_section()}

5. {get_anchor_generation_section()}

6. {get_cross_reference_section()}

7. {get_pdf_text_guidance_section(text_context)}

8. **SECTION PROCESSING GUIDELINES**:
   - Focus on this specific section's content only
   - Ensure the heading level matches the section numbering depth
   - Include complete mathematical derivations with explanatory context
   - Maintain academic writing conventions and technical precision
   - Preserve figure and table references within section context

{get_output_requirements_section()}
"""
        
        return prompt

    def _process_child_subsection(self, child_section_data):
        """
        Process a child subsection as part of parent section processing.
        
        Args:
            child_section_data (dict): Child section data structure
            
        Returns:
            str: Processed markdown content or None if failed
        """
        section_info = child_section_data['section_data']
        section_number = section_info.get('section_number', '')
        section_title = section_info.get('title', '')
        
        # Get page range for this child section
        if 'calculated_page_range' in child_section_data:
            start_page = child_section_data['calculated_page_range']['start_page']
            end_page = child_section_data['calculated_page_range']['end_page']
        else:
            start_page = section_info.get('start_page') or section_info.get('page')
            end_page = section_info.get('end_page', start_page)
        
        if start_page is None:
            return None
        
        # Create batch info for child
        batch_info = {
            'start_page': start_page,
            'end_page': end_page,
            'page_count': end_page - start_page + 1,
            'section_titles': [f"{section_number} {section_title}"],
            'batch_description': f"Child Section {section_number}",
            'chapter_title': child_section_data['chapter_title'],
            'subsection_count': 1
        }
        
        # Extract PDF text context
        text_context = self._extract_batch_text_context(start_page, end_page)
        text_context_path = f"child_section_{section_number}_text_context.txt"
        with open(text_context_path, 'w', encoding='utf-8') as f:
            f.write(text_context)
        print_progress(f"  Text context saved to: {text_context_path}")
        
        if self.enable_diagnostics:
            print_progress(f"    Pages: {start_page}-{end_page} ({batch_info['page_count']} pages)")
            print_progress(f"    Text context: {len(text_context)} characters")
        
        # Create child section prompt
        prompt = self._create_individual_section_prompt(batch_info, text_context, child_section_data)
        
        # Process the child section
        result = self._process_batch(batch_info, prompt, 1)
        
        if result and not result.startswith("Error:"):
            return self._clean_batch_result(result)
        else:
            print_progress(f"    - Error processing child section: {result}")
            return None

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
        
        # Calculate comprehensive metrics
        total_batches = len(self.diagnostics.get('batches', {}))
        successful_batches = sum(1 for batch in self.diagnostics.get('batches', {}).values() 
                               if batch.get('success', False))
        total_errors = len(self.diagnostics.get('processing_errors', []))
        
        # Add summary metrics
        self.diagnostics['summary'] = {
            'total_batches_processed': total_batches,
            'successful_batches': successful_batches,
            'failed_batches': total_batches - successful_batches,
            'success_rate': (successful_batches / total_batches * 100) if total_batches > 0 else 0,
            'total_processing_errors': total_errors,
            'processing_mode': 'subsection-aware',
            'timestamp': str(Path(diagnostics_path).stem)
        }
        
        # Add batch-by-batch analysis
        if 'batches' in self.diagnostics:
            for batch_id, batch_data in self.diagnostics['batches'].items():
                if 'content' in batch_data:
                    content = batch_data['content']
                    batch_data['content_analysis'] = {
                        'character_count': len(content),
                        'line_count': len(content.split('\n')),
                        'equation_count': content.count('$$'),
                        'figure_references': content.count('[Figure ') + content.count('[Fig. '),
                        'section_headers': content.count('##') + content.count('###') + content.count('####'),
                        'anchor_count': content.count('<a id=')
                    }
        
        try:
            with open(diagnostics_path, 'w', encoding='utf-8') as f:
                json.dump(self.diagnostics, f, indent=2, ensure_ascii=False)
            print_progress(f"+ Comprehensive diagnostics saved to: {diagnostics_path}")
            print_progress(f"  Summary: {successful_batches}/{total_batches} batches successful ({self.diagnostics['summary']['success_rate']:.1f}%)")
        except Exception as e:
            print_progress(f"- Failed to save diagnostics: {e}")

    def _save_section_diagnostics(self, diagnostics_path, section_diagnostics):
        """Save diagnostics for individual section processing."""
        try:
            with open(diagnostics_path, 'w', encoding='utf-8') as f:
                json.dump(section_diagnostics, f, indent=2, ensure_ascii=False)
            print_progress(f"+ Section diagnostics saved to: {diagnostics_path}")
        except Exception as e:
            print_progress(f"- Failed to save section diagnostics: {e}")


def main():
    """Main function for simplified chapter processing."""
    parser = argparse.ArgumentParser(
        description='Process thesis chapters or individual sections with section-based processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process full chapter 2 with section-aware batching
  python chapter_processor.py thesis.pdf "2" chapter_2.md --structure-dir structure/
  
  # Process individual section 2.1 (main section)
  python chapter_processor.py thesis.pdf "2.1" section_2_1.md --structure-dir structure/
  
  # Process individual subsection 2.1.1 (subsection level)
  python chapter_processor.py thesis.pdf "2.1.1" section_2_1_1.md --structure-dir structure/
  
  # Enable comprehensive diagnostics for detailed analysis
  python chapter_processor.py thesis.pdf "2" chapter_2.md --structure-dir structure/ --diagnostics
  
  # Custom batch size (pages per subsection batch)
  python chapter_processor.py thesis.pdf "2" chapter_2.md --structure-dir structure/ --max-pages 2

This processor supports both full chapters and individual sections with proper heading levels.
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
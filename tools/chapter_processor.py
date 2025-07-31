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

    def __init__(self, pdf_path, structure_dir=None, max_pages_per_batch=3):
        """
        Initialize the chapter processor.
        
        Args:
            pdf_path (str): Path to source PDF file
            structure_dir (str): Directory containing YAML structure files
            max_pages_per_batch (int): Maximum pages per subsection batch

        """
        self.pdf_path = Path(pdf_path)
        self.structure_dir = Path(structure_dir) if structure_dir else None
        self.max_pages_per_batch = max_pages_per_batch
   
        
    
        
        print_progress(f"Processor initialized with max {max_pages_per_batch} pages per batch")
     
    def process_section(self, section_identifier, output_path):
        """
        Process a chapter or individual section using subsection-aware processing.
        
        Args:
            section_identifier (str): Section identifier (e.g., "2.1", "2.1.1")
            output_path (str): Output markdown file path
        
        Returns:
            bool: True if processing succeeded, False otherwise
        """
        print_progress(f"Processing identifier: {section_identifier}")

        # Check if structure directory exists
        if not self.structure_dir or not self.structure_dir.exists():
            print_progress("- No structure directory provided or found")
            return False
        section_data = load_individual_section(str(self.structure_dir), section_identifier)
        if section_data:
            print_progress(f"+ Found individual section: {section_data['title']}")
            return self.process_individual_section(section_data, output_path)
        
    

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
        section_number = section_data['section_data'].get('section_number')
        section_title = section_info.get('title', '')
        chapter_title = section_data.get('chapter_title')

        print_progress(f"Processing individual section: {section_number} {section_title}")
        print_progress(f"Chapter: {chapter_title}")

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
        text_context = self._extract_batch_text_context(start_page, end_page,section_info,output_path)

    
        
       
        print_progress(f"+ Diagnostic mode: Processing individual section")
        print_progress(f"  Section: {section_number} - {section_title}")
        print_progress(f"  Pages: {start_page}-{end_page} ({batch_info['page_count']} pages)")
        print_progress(f"  Text context: {len(text_context)} characters")
        
        # Create section-specific prompt
        prompt = self._create_individual_section_prompt(batch_info, text_context, section_data, output_path)
 
        # Process the section
        result = self._process_batch(batch_info, prompt, 1)
        
        if result and not result.startswith("Error:"):
            cleaned_result = self._clean_batch_result(result)
            
            # Start with parent section content
            section_content = cleaned_result

            section_output_path = Path(output_path) / f"{section_number}_{section_title.replace(' ', '_')}.md"
            with open(section_output_path, 'w', encoding='utf-8') as f:
                f.write(section_content)

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
                    child_result = self._process_child_subsection(child_section_data,output_path)
                    if child_result:
                        print_progress(f"  + Child subsection {child_number} processed successfully")
                    else:
                        print_progress(f"  - Failed to process child subsection {child_number}")
            
   
            
 
            
            print_completion_summary(output_path, 1, f"individual section processed")
            return True
        else:
            print_progress(f"- Failed to process individual section: {result}")
            return False

    def _extract_batch_text_context(self, start_page, end_page, section_data,output_path):
        """Extract text context from a page range for guidance."""
        section_number = section_data.get('section_number')
 
        text_context = ""

        text_context = extract_text_from_pdf_page(str(self.pdf_path), start_page, end_page)

        text_context_path = Path(output_path) / f"section_{section_number}_text_context.txt"
        with open(text_context_path, 'w', encoding='utf-8') as f:
            f.write(text_context)
        print_progress(f"  Text context saved to: {text_context_path}")
 
        return text_context

   

        
        return prompt

    def _create_individual_section_prompt(self, batch_info, text_context, section_data, output_path):
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
        section_number = section_info.get('section_number')
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
        
        prompt_path = Path(output_path) / f"section_{section_number}_prompt.txt"
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        print_progress(f"  Prompt saved to: {prompt_path}")
        return prompt

    def _process_child_subsection(self, child_section_data,output_path):
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
        text_context = self._extract_batch_text_context(start_page, end_page,section_info,output_path)
    
        
 
        print_progress(f"    Pages: {start_page}-{end_page} ({batch_info['page_count']} pages)")
        print_progress(f"    Text context: {len(text_context)} characters")
        
        # Create child section prompt
        prompt = self._create_individual_section_prompt(batch_info, text_context, child_section_data, output_path)

        # Process the child section
        result = self._process_batch(batch_info, prompt, 1)
        
        if result and not result.startswith("Error:"):
            output =  self._clean_batch_result(result)
            result_output_path = Path(output_path) / f"{section_number}_{section_title.replace(' ', '_')}.md"
            with open(result_output_path, 'w', encoding='utf-8') as f:
                f.write(output)
            print_progress(f"    - Child section processed successfully: {result_output_path}")
            return output
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
  
  
  # Custom batch size (pages per subsection batch)
  python chapter_processor.py thesis.pdf "2" chapter_2.md --structure-dir structure/ --max-pages 2

This processor supports both full chapters and individual sections with proper heading levels.
"""
    )

    parser.add_argument('--input', required=True, help='Path to source PDF file')
    parser.add_argument('--section', required=True, help='Section identifier (e.g., "2", "2.1")')
    parser.add_argument('--output', required=True, help='Output markdown directory')
    parser.add_argument('--structure-dir', required=True, help='Directory containing YAML structure files')
    parser.add_argument('--max-pages', type=int, default=3, help='Maximum pages per subsection batch (default: 3)')
    
    args = parser.parse_args()

    # Validate input file
    if not Path(args.input).exists():
        print(f"ERROR: PDF file not found: {args.input}")
        return 1
    if not Path(args.structure_dir).is_dir():
        print(f"ERROR: Structure directory not found or is not a directory: {args.structure_dir}")
        return 1
    if not Path(args.output).is_dir():
        print(f"ERROR: Output directory does not exist or is not a directory: {Path(args.output)}")
        return 1

    # Initialize processor
    print_section_header("SECTION-AWARE CHAPTER PROCESSING")
    print(f"PDF: {args.input}")
    print(f"Chapter: {args.section}")
    print(f"Output: {args.output}")
    print(f"Structure directory: {args.structure_dir}")
    print(f"Max pages per batch: {args.max_pages}")
    print("=" * 60)
    
    processor = ChapterProcessor(
        pdf_path=args.input,
        structure_dir=args.structure_dir,
        max_pages_per_batch=args.max_pages,
    )
    
    # Process chapter
    success = processor.process_section(
        args.section,
        args.output
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
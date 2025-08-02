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
from enum import Enum

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

class ProcessingMode(Enum):
    PARENT_SECTION_ONLY = "PARENT_SECTION_ONLY"
    COMPLETE_SECTION = "COMPLETE_SECTION"


class SectionProcessor:
    """
    Simplified section processor focused on section-based processing.
    
    This processor uses subsection-aware processing to handle complete logical
    content units rather than arbitrary page breaks.
    """

    def __init__(self, pdf_path, structure_dir=None, max_pages_per_batch=3, debug=False):
        """
        Initialize the section processor.

        Args:
            pdf_path (str): Path to source PDF file
            structure_dir (str): Directory containing YAML structure files
            max_pages_per_batch (int): Maximum pages per subsection batch
            debug (bool): Whether to write debug files (prompt and text context)

        """
        self.pdf_path = Path(pdf_path)
        self.structure_dir = Path(structure_dir) if structure_dir else None
        self.max_pages_per_batch = max_pages_per_batch
        self.debug = debug
   
        
    
        
        print_progress(f"Processor initialized with max {max_pages_per_batch} pages per batch")
     
    def process_section(self, section_identifier, output_path):
        """
        Process a section or individual section using subsection-aware processing.
        
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
        chapter_title = section_data.get('chapter_title', '')
        section_number = section_info.get('section_number')
        section_title = section_info.get('title', '')
        result=False

        print_progress(f"Processing individual section: {section_number} {section_title}")
        if chapter_title:
            print_progress(f"Chapter: {chapter_title}")
        else:
            print_progress(f"Section type: {section_data.get('section_type', 'unknown')}")

        # Get page range and batch info
        start_page, end_page = self._get_page_range(section_info)
        batch_info = self._create_batch_info(section_info, start_page, end_page)

        print_progress(f"Section page range: {start_page}-{end_page}")

        # Extract PDF text context
        text_context = self._extract_batch_text_context(start_page, end_page, section_info, output_path)

        print_progress(f"+ Diagnostic mode: Processing individual section")
        print_progress(f"  Section: {section_number} - {section_title}")
        print_progress(f"  Pages: {start_page}-{end_page} ({batch_info['page_count']} pages)")
        print_progress(f"  Text context: {len(text_context)} characters")

        # Create section-specific prompt
        prompt = self._create_individual_section_prompt(batch_info, text_context, section_data, output_path)

        # Process the section
        result = self._process_batch(batch_info, prompt, 1)

        if result and not result.startswith("Error:"):
            # Save raw GPT output if debug mode is enabled
            if self.debug:
                raw_output_path = Path(output_path) / f"section_{section_number}_raw_output.txt"
                with open(raw_output_path, 'w', encoding='utf-8') as f:
                    f.write(result)
                print_progress(f"  Raw GPT output saved to: {raw_output_path}")
            
            cleaned_result = self._clean_batch_result(result)
            
            # Save cleaned output if debug mode is enabled
            if self.debug:
                cleaned_output_path = Path(output_path) / f"section_{section_number}_cleaned_output.txt"
                with open(cleaned_output_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_result)
                print_progress(f"  Cleaned output saved to: {cleaned_output_path}")

            # Start with parent section content
            section_content = cleaned_result

            section_output_path = Path(output_path) / f"{section_number}_{section_title.replace(' ', '_')}.md"
            with open(section_output_path, 'w', encoding='utf-8') as f:
                f.write(section_content)

 

            print_completion_summary(output_path, 1, f"individual section processed")
            result=True
        else:
            print_progress(f"- Failed to process individual section")
            result=False
        return result

    def _extract_batch_text_context(self, start_page, end_page, section_data, output_path):
        """Extract text context from a page range for guidance."""
        section_number = section_data.get('section_number')
 
        text_context = ""

        text_context = extract_text_from_pdf_page(str(self.pdf_path), start_page, end_page)

        if self.debug:
            text_context_path = Path(output_path) / f"section_{section_number}_text_context.txt"
            with open(text_context_path, 'w', encoding='utf-8') as f:
                f.write(text_context)
            print_progress(f"  Text context saved to: {text_context_path}")
 
        return text_context

    def _determine_heading_level(self, section_number: str) -> tuple[str, str]:
        """Determine the heading level and type based on section numbering."""
        # Handle universal section numbers (F1, F2, 1, 2, B1, A1, etc.)
        if section_number.isdigit() or section_number.startswith(('F', 'B', 'A')):
            return "#", "chapter"
        
        # Handle traditional dotted section numbers
        section_parts = section_number.split('.')
        if len(section_parts) == 2:
            return "##", "main section"
        elif len(section_parts) == 3:
            return "###", "subsection"
        elif len(section_parts) == 4:
            return "####", "sub-subsection"
        return "##", "section"

    def _format_section_heading(self, section_number: str, section_title: str, heading_level: str) -> str:
        """Format the section heading properly based on section type."""
        # For top-level sections (F1, B1, A1, etc.), don't include the universal identifier in the title
        if section_number.startswith(('F', 'B', 'A')):
            return f"{heading_level} {section_title} <a id=\"section-{section_number.lower()}\"></a>"
        # For chapters and regular sections, include the number
        else:
            return f"{heading_level} {section_number} {section_title} <a id=\"section-{section_number.replace('.', '-')}\"></a>"

    def _determine_processing_mode_and_structure(self, section_number: str, section_title: str, all_subsections: list) -> tuple[str, str]:
        """Determine the processing mode and expected structure for the section."""
        child_subsections = [s for s in all_subsections if s.get('section_number', '').startswith(section_number + '.')]
        if child_subsections:
            expected_structure = f"{section_number} {section_title} (parent section content only)"
            return ProcessingMode.PARENT_SECTION_ONLY.value, expected_structure
        else:
            expected_structure = "\n".join(
                f"{s.get('section_number', '')} {s.get('title', '')}" for s in all_subsections
            ) or f"{section_number} {section_title}"
            return ProcessingMode.COMPLETE_SECTION.value, expected_structure

    def _build_prompt(self, batch_info: dict, text_context: str, section_number: str, section_title: str, chapter_title: str, heading_level: str, heading_type: str, processing_mode: str, expected_structure: str) -> str:
        """Build the prompt string for the section."""
        formatted_heading = self._format_section_heading(section_number, section_title, heading_level)
        
        return f"""Convert this individual section from a 1992 LaTeX academic thesis PDF to markdown format.

INDIVIDUAL SECTION INFORMATION:
- Context: {chapter_title if chapter_title else f"Top-level {heading_type}"}
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
   - Start with: {formatted_heading}
   - {"**PARENT SECTION ONLY**: Extract ONLY the section heading. Do NOT include any content from subsections that follow. Stop immediately after the section heading." if processing_mode == ProcessingMode.PARENT_SECTION_ONLY.value else "Process the complete section including all content"}

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

    def _create_individual_section_prompt(self, batch_info: dict, text_context: str, section_data: dict, output_path: str) -> str:
        """
        Create a prompt for processing an individual section.
        
        Args:
            batch_info (dict): Information about the section batch
            text_context (str): Extracted PDF text for guidance
            section_data (dict): Section data with chapter context
            output_path (str): Path to save the generated prompt
    
        Returns:
            str: Formatted prompt for GPT-4 Vision API
        """
        section_info = section_data['section_data']
        section_number = section_info.get('section_number')
        section_title = section_info.get('title', '')
        chapter_title = section_data.get('chapter_title', '')
        all_subsections = section_data.get('all_subsections', [])

        # Determine heading level and type
        heading_level, heading_type = self._determine_heading_level(section_number)

        # Determine processing mode and expected structure
        processing_mode, expected_structure = self._determine_processing_mode_and_structure(section_number, section_title, all_subsections)

        # Build the prompt
        prompt = self._build_prompt(
            batch_info, text_context, section_number, section_title, chapter_title,
            heading_level, heading_type, processing_mode, expected_structure
        )

        # Save the prompt to a file (if debug mode is enabled)
        if self.debug:
            prompt_path = Path(output_path) / f"section_{section_number}_prompt.txt"
            with open(prompt_path, 'w', encoding='utf-8') as f:
                f.write(prompt)
            print_progress(f"  Prompt saved to: {prompt_path}")
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
        
        # Fix equation formatting - convert multi-line equations to single-line format
        cleaned_result = self._fix_equation_formatting(cleaned_result)
        
        return cleaned_result

    def _fix_equation_formatting(self, content):
        """
        Fix equation formatting by converting multi-line $$ blocks to single-line format.
        
        Args:
            content (str): Markdown content to fix
            
        Returns:
            str: Fixed markdown content
        """
        import re
        
        # Count issues before fixing
        issues_found = self._count_equation_issues(content)
        if issues_found > 0:
            print_progress(f"- Post-processing: Fixing {issues_found} malformed equation block(s)")
        
        # Pattern to match multi-line equation blocks
        # This matches: $$ (content with potential newlines) $$
        pattern = r'\$\$\s*\n*(.*?)\n*\s*\$\$'
        
        def fix_equation_block(match):
            equation_content = match.group(1)
            
            # Remove internal newlines and excessive whitespace
            # But preserve single spaces between elements
            fixed_equation = re.sub(r'\s*\n\s*', ' ', equation_content)
            # Clean up multiple spaces
            fixed_equation = re.sub(r'\s+', ' ', fixed_equation)
            # Remove leading/trailing whitespace
            fixed_equation = fixed_equation.strip()
            
            # Return as single-line equation
            return f'$${fixed_equation}$$'
        
        # Apply the fix to all equation blocks
        fixed_content = re.sub(pattern, fix_equation_block, content, flags=re.DOTALL)
        
        # Verify the fix worked
        remaining_issues = self._count_equation_issues(fixed_content)
        if issues_found > 0:
            fixed_count = issues_found - remaining_issues
            print_progress(f"- Post-processing: Fixed {fixed_count} equation formatting issue(s)")
            if remaining_issues > 0:
                print_progress(f"- Post-processing: {remaining_issues} issues remain (may need manual review)")
        
        return fixed_content
    
    def _count_equation_issues(self, content):
        """
        Count the number of malformed equation blocks in the content.
        
        Args:
            content (str): Markdown content to analyze
            
        Returns:
            int: Number of malformed equation blocks found
        """
        import re
        # Find equation blocks that span multiple lines
        pattern = r'\$\$\s*\n.*?\n.*?\$\$'
        matches = re.findall(pattern, content, re.DOTALL)
        return len(matches)

    def _get_page_range(self, section_data: dict) -> tuple[int, int]:
        """Get the start and end page for a section."""
        if 'calculated_page_range' in section_data:
            return section_data['calculated_page_range']['start_page'], section_data['calculated_page_range']['end_page']
        start_page = section_data.get('start_page') or section_data.get('page')
        end_page = section_data.get('end_page', start_page)
        return start_page, end_page

    def _create_batch_info(self, section_data: dict, start_page: int, end_page: int) -> dict:
        """Create batch info for a section."""
        section_number = section_data.get('section_number', '')
        section_title = section_data.get('title', '')
        return {
            'start_page': start_page,
            'end_page': end_page,
            'page_count': end_page - start_page + 1,
            'section_titles': [f"{section_number} {section_title}"],
            'batch_description': f"Section {section_number}",
            'chapter_title': section_data.get('chapter_title', ''),
            'subsection_count': 1
        }


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
    parser.add_argument('--debug', action='store_true', help='Write prompt and text context files for debugging')
    
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
    print(f"Debug mode: {'Enabled' if args.debug else 'Disabled'}")
    print("=" * 60)
    
    processor = SectionProcessor(
        pdf_path=args.input,
        structure_dir=args.structure_dir,
        max_pages_per_batch=args.max_pages,
        debug=args.debug,
    )
    
    # Process chapter
    success = processor.process_section(
        args.section,
        args.output
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
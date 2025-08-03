#!/usr/bin/env python3
"""
Simplified section processor for complete section processing.

This processor processes complete sections as single units for optimal quality,
focusing on logical content boundaries rather than arbitrary page batches.
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
    get_figure_formatting_section,
    get_table_formatting_section
)
from subsection_utils import (
    load_chapter_subsections, 
    load_individual_section
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

    def __init__(self, pdf_path, structure_file=None, debug=False):
        """
        Initialize the section processor.

        Args:
            pdf_path (str): Path to source PDF file
            structure_file (str): Path to thesis structure YAML file
            debug (bool): Whether to write debug files (prompt and text context)

        """
        self.pdf_path = Path(pdf_path)
        self.structure_file = Path(structure_file) if structure_file else None
        self.debug = debug
        
        print_progress(f"Processor initialized")
     
    def process_section(self, section_identifier, output_file_path):
        """
        Process a section or individual section using subsection-aware processing.
        
        Args:
            section_identifier (str): Section identifier (e.g., "2.1", "2.1.1")
            output_file_path (str): Complete path to output markdown file (including filename)
        
        Returns:
            bool: True if processing succeeded, False otherwise
        """
        print_progress(f"Processing identifier: {section_identifier}")

        # Check if structure file exists
        if not self.structure_file or not self.structure_file.exists():
            print_progress("- No structure file provided or found")
            return False
        section_data = load_individual_section(str(self.structure_file), section_identifier)
        if section_data:
            print_progress(f"+ Found individual section: {section_data['title']}")
            return self.process_individual_section(section_data, output_file_path)
        
    

    def process_individual_section(self, section_data, output_file_path):
        """
        Process an individual section (e.g., 2.1, 2.1.1) rather than a full chapter.
        
        Args:
            section_data (dict): Section data with parent chapter context
            output_file_path (str): Complete path to output markdown file (including filename)
        
        Returns:
            bool: True if processing succeeded, False otherwise
        """
        section_info = section_data['section_data']
        chapter_title = section_data.get('chapter_title', '')
        section_number = section_info.get('section_number')
        section_title = section_info.get('title', '')

        print_progress(f"Processing individual section: {section_number} {section_title}")
        if chapter_title:
            print_progress(f"Chapter: {chapter_title}")
        else:
            print_progress(f"Section type: {section_data.get('section_type', 'unknown')}")

        # Get page range (use full section_data which contains calculated_page_range)
        start_page, end_page = self._get_page_range(section_data)
        total_pages = end_page - start_page + 1

        print_progress(f"Section page range: {start_page}-{end_page} ({total_pages} pages)")

        # Get output directory for debug files
        output_dir = Path(output_file_path).parent
        
        # Extract section text context
        text_context = self._extract_section_text_context(
            start_page, end_page, section_info, output_dir, output_file_path
        )
        
        print_progress(f"Processing section as single unit with {len(text_context)} characters text context")

        # Create section prompt
        prompt = self._create_individual_section_prompt(section_data, text_context, output_dir, output_file_path)

        # Process the entire section
        result = self._process_section(start_page, end_page, prompt, output_dir, output_file_path)
        
        if result and not result.startswith("Error:"):
            # Clean the result
            cleaned_result = self._clean_section_result(result)
            
            # Save debug output if debug mode is enabled
            if self.debug:
                base_name = Path(output_file_path).stem
                debug_output_path = output_dir / f"{base_name}_output.txt"
                with open(debug_output_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_result)
                print_progress(f"  Debug output saved to: {debug_output_path}")
        else:
            print_progress(f"  ✗ Section processing failed: {result}")
            return False

        # Write the section content to the specified output file
        output_file = Path(output_file_path)
        
        # Ensure the output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_result)

        print_completion_summary(str(output_file), total_pages, f"pages processed")
        return True


    def _extract_section_text_context(self, start_page, end_page, section_data, output_path, output_file_path=None):
        """Extract text context from the section for guidance."""
        section_number = section_data.get('section_number')
 
        text_context = extract_text_from_pdf_page(str(self.pdf_path), start_page, end_page)

        # Save debug file if debug mode enabled
        if self.debug:
            # Use output filename stem for debug files
            if output_file_path:
                base_name = Path(output_file_path).stem
            else:
                base_name = f"section_{section_number}"
                
            text_context_path = Path(output_path) / f"{base_name}_text_context.txt"
            with open(text_context_path, 'w', encoding='utf-8') as f:
                f.write(text_context)
            print_progress(f"  Text context saved to: {text_context_path}")
 
        return text_context

    def _save_debug_images(self, image_paths, output_dir, output_file_path):
        """Save page images in debug mode for inspection."""
        import shutil
        
        base_name = Path(output_file_path).stem
        
        for i, image_path in enumerate(image_paths, 1):
            # Create descriptive filename for the debug image
            debug_image_name = f"{base_name}_page_{i}.png"
            debug_image_path = Path(output_dir) / debug_image_name
            
            # Copy the image from temp directory to output directory
            shutil.copy2(image_path, debug_image_path)
            print_progress(f"  Debug image saved: {debug_image_name}")

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
        # For top-level sections without dots (F1, B1, A1, A2, etc.), use only the title
        # For subsections with dots (A2.1, A2.2, etc.), include the section number
        if section_number.startswith(('F', 'B', 'A')) and '.' not in section_number:
            return f"{heading_level} {section_title} <a id=\"section-{section_number.lower()}\"></a>"
        # For all other sections (chapters and subsections), include the number
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

    def _build_prompt(self, section_data: dict, text_context: str, section_number: str, section_title: str, chapter_title: str, heading_level: str, heading_type: str, processing_mode: str, expected_structure: str, start_page: int, end_page: int) -> str:
        """Build the prompt string for the section."""
        formatted_heading = self._format_section_heading(section_number, section_title, heading_level)
        
        processing_info = f"individual {heading_type} (pages {start_page}-{end_page})"

        return f"""Convert this individual section from a 1992 LaTeX academic thesis PDF to markdown format.

INDIVIDUAL SECTION INFORMATION:
- Context: {chapter_title if chapter_title else f"Top-level {heading_type}"}
- Section: {section_number} {section_title}
- Processing: {processing_info}
- Content Type: Complete {heading_type} with logical boundaries

EXPECTED SECTION STRUCTURE:
{expected_structure}

CRITICAL CONTENT REQUIREMENTS:
1. {get_content_transcription_requirements()}

2. **INDIVIDUAL SECTION PROCESSING** ({processing_mode}):
   - This is a complete {heading_type} from a larger chapter
   - **CRITICAL HEADING LEVEL**: Use {heading_level} for the main section header
   - Start with: {formatted_heading}
   - {"**PARENT SECTION CONTENT**: Extract only the main section heading (e.g., # APPENDIX 2 Analytical Solutions <a id=\"section-a2\"></a>), and do not include any surrounding or subsequent paragraph text, unless it clearly precedes any subsection heading. If the very next content after the heading is a subsection (e.g., A2.1), then treat the parent section as heading only, with no body content." if processing_mode == ProcessingMode.PARENT_SECTION_ONLY.value else "Process the complete section content"}

3. {get_mathematical_formatting_section()}

4. {get_figure_formatting_section()}

5. {get_table_formatting_section()}

6. {get_anchor_generation_section()}

7. {get_cross_reference_section()}

8. {get_pdf_text_guidance_section(text_context)}

9. **SECTION PROCESSING GUIDELINES**:
   - Focus on this specific section's content only
   - Ensure the heading level matches the section numbering depth
   - Include complete mathematical derivations with explanatory context
   - Maintain academic writing conventions and technical precision
   - Preserve figure and table references within section context
   - **SECTION-AWARE NAMING**: Use the correct section prefix for figures and tables:
     * For Appendix A2: figure-A2-1.png, table-A2-1, etc.
     * For Chapter 2: figure-2-1.png, table-2-1, etc.
   - **HEADING FORMAT**: Include section numbers in subsection headings:
     * Top-level: "# APPENDIX 2 Analytical Solutions" (no A2 prefix)
     * Subsections: "## A2.1 Rigid Sphere", "## A2.2 Asymptotic Solutions" (include A2.1, A2.2 prefix)
   - **FOR PARENT SECTIONS ONLY**: Include introductory text that applies to the whole section, but stop before subsection headings or equations/content tagged with subsection numbers (e.g., stop before equations tagged A2.1.1, A2.1.2, or headings like "A2.1 Rigid Sphere")

{get_output_requirements_section()}
"""

    def _create_individual_section_prompt(self, section_data: dict, text_context: str, output_path: str, output_file_path: str = None) -> str:
        """
        Create a prompt for processing an individual section.
        
        Args:
            section_data (dict): Section data with chapter context
            text_context (str): Extracted PDF text for guidance
            output_path (str): Path to save the generated prompt
            output_file_path (str): Path to output markdown file
    
        Returns:
            str: Formatted prompt for GPT-4 Vision API
        """
        section_info = section_data['section_data']
        section_number = section_info.get('section_number')
        section_title = section_info.get('title', '')
        chapter_title = section_data.get('chapter_title', '')
        all_subsections = section_data.get('all_subsections', [])
        
        # Get page range
        start_page, end_page = self._get_page_range(section_data)

        # Determine heading level and type
        heading_level, heading_type = self._determine_heading_level(section_number)

        # Determine processing mode and expected structure
        processing_mode, expected_structure = self._determine_processing_mode_and_structure(section_number, section_title, all_subsections)

        # Build the prompt
        prompt = self._build_prompt(
            section_data, text_context, section_number, section_title, chapter_title,
            heading_level, heading_type, processing_mode, expected_structure, start_page, end_page
        )

        # Save the prompt to a file (if debug mode is enabled)
        if self.debug:
            # Use output filename stem for debug files
            if output_file_path:
                base_name = Path(output_file_path).stem
            else:
                base_name = f"section_{section_number}"
                
            prompt_path = Path(output_path) / f"{base_name}_prompt.txt"
            with open(prompt_path, 'w', encoding='utf-8') as f:
                f.write(prompt)
            print_progress(f"  Prompt saved to: {prompt_path}")
        return prompt



    def _process_section(self, start_page, end_page, prompt, output_dir=None, output_file_path=None):
        """Process a complete section as a single unit."""
        with tempfile.TemporaryDirectory() as temp_dir:
            section_pdf_path = Path(temp_dir) / "section.pdf"
            
            # Extract pages for this section
            success = extract_pages_to_pdf(
                str(self.pdf_path),
                str(section_pdf_path),
                start_page,
                end_page
            )
            
            if not success:
                return f"Error: Failed to extract pages {start_page}-{end_page}"
            
            # Convert to images
            image_paths = pdf_to_images(str(section_pdf_path), temp_dir)
            if not image_paths:
                return "Error: Failed to convert section to images"
            
            # Save page images in debug mode
            if self.debug and output_dir and output_file_path:
                self._save_debug_images(image_paths, output_dir, output_file_path)
            
            # Encode images
            image_contents = encode_images_for_vision(image_paths)
            
            # Call GPT-4 Vision API
            result = call_gpt_vision_api(prompt, image_contents)
            
            return result

    def _clean_section_result(self, result):
        """Clean and validate section processing result."""
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
        
        # Fix inline equations that were incorrectly formatted as display equations
        cleaned_result = self._fix_inline_display_equations(cleaned_result)
        
        return cleaned_result

    def _fix_equation_formatting(self, content):
        """
        Fix equation formatting by converting multi-line $$ blocks to single-line format
        and fixing inline equation delimiters.
        
        Args:
            content (str): Markdown content to fix
            
        Returns:
            str: Fixed markdown content
        """
        import re
        
        # Count issues before fixing
        display_issues = self._count_equation_issues(content)
        inline_issues = self._count_inline_equation_issues(content)
        total_issues = display_issues + inline_issues
        
        if total_issues > 0:
            print_progress(f"- Post-processing: Fixing {display_issues} display + {inline_issues} inline equation issue(s)")
        
        # Fix 1: Convert multi-line equation blocks to single-line format
        # Pattern to match multi-line equation blocks: $$ (content with potential newlines) $$
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
        
        # Apply the display equation fix
        fixed_content = re.sub(pattern, fix_equation_block, content, flags=re.DOTALL)
        
        # Fix 2: Convert \(...\) inline equations to $...$ format
        inline_pattern = r'\\?\\\((.*?)\\?\\\)'
        
        def fix_inline_equation(match):
            equation_content = match.group(1)
            return f'${equation_content}$'
        
        # Apply the inline equation fix
        fixed_content = re.sub(inline_pattern, fix_inline_equation, fixed_content)
        
        # Fix 3: Convert \[...\] display equations to $$...$$ format (just in case)
        display_bracket_pattern = r'\\?\\\[(.*?)\\?\\\]'
        
        def fix_display_bracket_equation(match):
            equation_content = match.group(1)
            return f'$${equation_content}$$'
        
        # Apply the display bracket equation fix
        fixed_content = re.sub(display_bracket_pattern, fix_display_bracket_equation, fixed_content, flags=re.DOTALL)
        
        # Verify the fixes worked
        remaining_display_issues = self._count_equation_issues(fixed_content)
        remaining_inline_issues = self._count_inline_equation_issues(fixed_content)
        
        if total_issues > 0:
            display_fixed = display_issues - remaining_display_issues
            inline_fixed = inline_issues - remaining_inline_issues
            total_fixed = display_fixed + inline_fixed
            print_progress(f"- Post-processing: Fixed {total_fixed} equation formatting issue(s) ({display_fixed} display, {inline_fixed} inline)")
            
            remaining_total = remaining_display_issues + remaining_inline_issues
            if remaining_total > 0:
                print_progress(f"- Post-processing: {remaining_total} issues remain (may need manual review)")
        
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
    
    def _count_inline_equation_issues(self, content):
        """
        Count the number of \\(...\\) inline equations that should be $...$.
        
        Args:
            content (str): Markdown content to analyze
            
        Returns:
            int: Number of inline equation issues found
        """
        import re
        # Find \(...\) patterns
        pattern = r'\\?\\\((.*?)\\?\\\)'
        matches = re.findall(pattern, content)
        return len(matches)

    def _fix_inline_display_equations(self, content):
        """
        Fix inline equations that were incorrectly formatted as display equations.
        
        Converts patterns like: "text $$equation$$ text" to "text $equation$ text"
        Only when it's clearly an inline context (text before and after on same line).
        
        Args:
            content (str): Markdown content to fix
            
        Returns:
            str: Fixed markdown content
        """
        import re
        
        # Count issues before fixing
        inline_display_issues = self._count_inline_display_equation_issues(content)
        
        if inline_display_issues > 0:
            print_progress(f"- Post-processing: Fixing {inline_display_issues} inline display equation issue(s)")
        
        # Pattern to match display equations that appear inline
        # Look for: word/text $$equation$$ word/text (all on same line)
        pattern = r'(\S.*?)\s*\$\$([^$\n]+?)\$\$\s*(\S.*?)(?=\n|$)'
        
        def fix_inline_display_equation(match):
            before_text = match.group(1).strip()
            equation_content = match.group(2).strip()
            after_text = match.group(3).strip()
            
            # Safety checks - only convert if it looks like inline context
            if (len(before_text) > 0 and len(after_text) > 0 and
                not before_text.endswith('.') and  # Not end of sentence
                not equation_content.startswith('\\begin') and  # Not complex equation
                not equation_content.endswith('\\tag{') and  # Not numbered equation
                len(equation_content) < 50):  # Not too long
                
                return f"{before_text} ${equation_content}$ {after_text}"
            else:
                # Keep as display equation
                return match.group(0)
        
        # Apply the fix
        fixed_content = re.sub(pattern, fix_inline_display_equation, content)
        
        # Verify the fixes worked
        remaining_issues = self._count_inline_display_equation_issues(fixed_content)
        
        if inline_display_issues > 0:
            fixed_count = inline_display_issues - remaining_issues
            print_progress(f"- Post-processing: Fixed {fixed_count} inline display equation issue(s)")
            
            if remaining_issues > 0:
                print_progress(f"- Post-processing: {remaining_issues} display equations remain (likely intentional)")
        
        return fixed_content
    
    def _count_inline_display_equation_issues(self, content):
        """
        Count potential inline display equation issues.
        
        Args:
            content (str): Markdown content to analyze
            
        Returns:
            int: Number of potential issues found
        """
        import re
        # Find display equations that appear to be inline (text before and after on same line)
        pattern = r'\S.*?\s*\$\$[^$\n]+?\$\$\s*\S.*?(?=\n|$)'
        matches = re.findall(pattern, content)
        return len(matches)
    

    def _get_page_range(self, section_data: dict) -> tuple[int, int]:
        """Get the start and end page for a section."""
        # Check if calculated_page_range is at the top level (new format)
        if 'calculated_page_range' in section_data:
            return section_data['calculated_page_range']['start_page'], section_data['calculated_page_range']['end_page']
        
        # Check if we have section_data nested (old format)
        if 'section_data' in section_data:
            section_info = section_data['section_data']
            if 'calculated_page_range' in section_info:
                return section_info['calculated_page_range']['start_page'], section_info['calculated_page_range']['end_page']
            start_page = section_info.get('start_page') or section_info.get('page')
            end_page = section_info.get('end_page', start_page)
            return start_page, end_page
        
        # Fallback to direct properties
        start_page = section_data.get('start_page') or section_data.get('page')
        end_page = section_data.get('end_page', start_page)
        return start_page, end_page



def main():
    """Main function for simplified section processing."""
    parser = argparse.ArgumentParser(
        description='Process thesis sections with single-unit processing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process full chapter 2
  python section_processor.py --input thesis.pdf --section "2" --output chapter_2.md --structure structure/thesis_contents.yaml
  
  # Process individual section 2.1 (main section)
  python section_processor.py --input thesis.pdf --section "2.1" --output section_2_1.md --structure structure/thesis_contents.yaml
  
  # Process individual subsection 2.1.1 (subsection level)
  python section_processor.py --input thesis.pdf --section "2.1.1" --output section_2_1_1.md --structure structure/thesis_contents.yaml
  
  # Process appendix section with custom filename
  python section_processor.py --input thesis.pdf --section "A1" --output "Appendix_1.md" --structure structure/thesis_contents.yaml

This processor supports both full chapters and individual sections with proper heading levels.
Each section is processed as a complete unit for optimal quality.
"""
    )

    parser.add_argument('--input', required=True, help='Path to source PDF file')
    parser.add_argument('--section', required=True, help='Section identifier (e.g., "2", "2.1")')
    parser.add_argument('--output', required=True, help='Complete path to output markdown file (including filename)')
    parser.add_argument('--structure', required=True, help='Path to thesis structure YAML file (e.g., structure/thesis_contents.yaml)')
    parser.add_argument('--debug', action='store_true', help='Write prompt and text context files for debugging')
    
    args = parser.parse_args()

    # Validate input file
    if not Path(args.input).exists():
        print(f"ERROR: PDF file not found: {args.input}")
        return 1
    if not Path(args.structure).exists():
        print(f"ERROR: Structure file not found: {args.structure}")
        return 1
    
    # Check if output is a directory (old interface) or file path (new interface)
    output_path = Path(args.output)
    if output_path.is_dir():
        print(f"ERROR: --output must be a complete file path (including filename), not a directory.")
        print(f"Example: --output ../markdown/section_A2_1.md")
        print(f"You provided: {args.output} (which is a directory)")
        return 1
    
    # Validate that output file's parent directory exists
    output_dir = output_path.parent
    if not output_dir.exists():
        print(f"ERROR: Output directory does not exist: {output_dir}")
        return 1

    # Initialize processor
    print_section_header("SIMPLIFIED SECTION PROCESSING")
    print(f"PDF: {args.input}")
    print(f"Section: {args.section}")
    print(f"Output: {args.output}")
    print(f"Structure file: {args.structure}")
    print(f"Debug mode: {'Enabled' if args.debug else 'Disabled'}")
    print("=" * 60)
    
    processor = SectionProcessor(
        pdf_path=args.input,
        structure_file=args.structure,
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
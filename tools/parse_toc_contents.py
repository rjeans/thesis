#!/usr/bin/env python3
"""
Parse table of contents from thesis PDF to extract chapter/section structure.

This tool extracts the hierarchical structure of chapters and sections from
the table of contents pages of a PDF thesis document.
"""

import argparse
import yaml
from pathlib import Path
import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gpt_vision_utils import call_gpt_vision_api, encode_images_for_vision, create_toc_parsing_prompt
from pdf_utils import extract_pages_to_pdf, pdf_to_images, extract_text_from_pdf_page
from progress_utils import print_progress, print_completion_summary, print_section_header

def calculate_section_page_ranges(structure_data):
    """
    Calculate end_page for each section and subsection, handling AI parsing errors
    and correctly calculating ranges for items on the same page.
    
    Args:
        structure_data (dict): Parsed YAML structure data from AI
        
    Returns:
        dict: Enhanced structure data with calculated page ranges
    """
    if 'sections' not in structure_data or not structure_data['sections']:
        print_progress("  [AI PARSING WARNING] No sections found in the structure data.")
        return structure_data
    
    sections = structure_data['sections']
    total_pages = structure_data.get('total_pages', 999)
    
    print_progress("Calculating section page ranges...")
    
    # First pass: Filter out invalid top-level sections
    valid_sections = []
    for i, section in enumerate(sections):
        if not isinstance(section, dict) or 'page_start' not in section:
            title = section.get('title', f"Unknown Section at index {i}") if isinstance(section, dict) else f"Invalid section data at index {i}"
            print_progress(f"  [AI PARSING WARNING] Skipping top-level section missing 'page_start': {title}")
            continue
        valid_sections.append(section)

    # Calculate end pages for valid sections
    for i, section in enumerate(valid_sections):
        next_section_start_page = None
        if i + 1 < len(valid_sections):
            next_section_start_page = valid_sections[i+1].get('page_start')
        
        if next_section_start_page is not None:
            section['page_end'] = next_section_start_page - 1
        else:
            section['page_end'] = total_pages
        
        section['page_end'] = max(section.get('page_start', 0), section.get('page_end', section.get('page_start', 0)))

        print_progress(f"  {section.get('title', 'Unknown')}: pages {section.get('page_start', 'N/A')}-{section.get('page_end', 'N/A')}")

        # Second pass: Process subsections for the current valid section
        if 'subsections' in section and section['subsections']:
            
            valid_subsections = []
            for sub in section['subsections']:
                if not isinstance(sub, dict):
                    print_progress(f"    [AI PARSING WARNING] Skipping invalid subsection data: {sub}")
                    continue
                if 'page' in sub and 'start_page' not in sub:
                    sub['start_page'] = sub['page']
                    del sub['page']
                
                if 'start_page' in sub:
                    valid_subsections.append(sub)
                else:
                    title = sub.get('title', sub.get('section_number', 'Unknown subsection'))
                    print_progress(f"    [AI PARSING WARNING] Skipping subsection missing 'page_start': {title}")

            valid_subsections.sort(key=lambda x: x.get('start_page', 0))
            section['subsections'] = valid_subsections

            for j, subsection in enumerate(valid_subsections):
                current_start = subsection.get('start_page', 0)
                current_level = subsection.get('level')

                if current_level is None:
                    if 'end_page' not in subsection:
                        subsection['end_page'] = current_start
                    continue

                next_section_start = None
                # Find the start page of the next section at the same or higher level
                for k in range(j + 1, len(valid_subsections)):
                    next_subsection = valid_subsections[k]
                    next_level = next_subsection.get('level')
                    if next_level is not None and next_level <= current_level:
                        next_section_start = next_subsection.get('start_page')
                        break
                
                if next_section_start is not None:
                    subsection['end_page'] = next_section_start - 1
                else:
                    # If no next subsection, it ends at the chapter's end page
                    subsection['end_page'] = section.get('page_end', current_start)
                
                subsection['end_page'] = max(current_start, subsection.get('end_page', current_start))
                    
                print_progress(f"    {subsection.get('section_number', 'Unknown')}: pages {subsection.get('start_page', 'N/A')}-{subsection.get('end_page', 'N/A')}")
    
    structure_data['sections'] = valid_sections
    return structure_data

def create_contents_yaml_structure():
    """Create YAML structure template for contents parsing with start/end pages."""
    return """thesis_title: "PhD Thesis Title"
total_pages: 215
sections:
- type: front_matter|chapter|appendix|back_matter
  title: "Section Title"
  page_start: 1
  page_end: 10
  chapter_number: 1  # Only for chapters, null for others
  subsections:
  - section_number: "1.1"
    title: "Subsection Title"
    start_page: 25
    end_page: 27
    level: 1  # 1 for main sections, 2 for subsections, etc.
  - section_number: "1.1.1"
    title: "Sub-subsection Title"  
    start_page: 25
    end_page: 26
    level: 2
  - section_number: "1.1.2"
    title: "Another Sub-subsection"
    start_page: 27
    end_page: 27
    level: 2
extraction_metadata:
  pages_processed: 4
  extraction_date: "2024-01-01"
  tool_version: "enhanced_with_page_ranges"
"""


def parse_toc_contents(pdf_path, start_page, end_page, output_dir):
    """
    Parse table of contents from PDF pages to extract chapter structure.
    
    Args:
        pdf_path (str): Path to the source PDF file
        start_page (int): Starting page number (1-based)
        end_page (int): Ending page number (1-based)
        output_dir (str): Directory to save output files
    
    Returns:
        bool: True if parsing succeeded, False otherwise
    """
    print_section_header("TOC CONTENTS PARSING")
    print_progress(f"Processing pages {start_page}-{end_page} from {pdf_path}")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    all_pages_data = []
    
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        for page_num in range(start_page, end_page + 1):
            print_progress(f"\nProcessing page {page_num}...")
            
            page_pdf_path = Path(temp_dir) / f"page_{page_num}.pdf"
            if not extract_pages_to_pdf(pdf_path, str(page_pdf_path), page_num, page_num):
                print_progress(f"- Failed to extract page {page_num}")
                continue

            image_paths = pdf_to_images(str(page_pdf_path), temp_dir)
            if not image_paths:
                print_progress(f"- Failed to convert page {page_num} to image")
                continue

            image_contents = encode_images_for_vision(image_paths)
            
            yaml_structure = create_contents_yaml_structure()
            prompt = create_toc_parsing_prompt("contents", yaml_structure)

            print_progress("  Sending to GPT-4 Vision API for structure extraction...")
            result = call_gpt_vision_api(prompt, image_contents)
            
            if result and not result.startswith("Error:"):
                cleaned_result = result.strip().removeprefix('```yaml').removeprefix('```').removesuffix('```')
                try:
                    page_data = yaml.safe_load(cleaned_result.strip())
                    if page_data and 'sections' in page_data:
                        for section in page_data['sections']:
                            section['source_page'] = page_num
                        all_pages_data.append(page_data)
                        print_progress(f"+ Successfully parsed {len(page_data['sections'])} sections from page {page_num}")
                except yaml.YAMLError as e:
                    print_progress(f"- YAML parsing error for page {page_num}: {e}")
            else:
                print_progress(f"- GPT-4 Vision API error on page {page_num}: {result}")

    if not all_pages_data:
        print_progress("- No sections were extracted from any page.")
        return False

    # Intelligent merging of sections
    all_sections = []
    for page_data in all_pages_data:
        all_sections.extend(page_data.get('sections', []))

    final_structure = {
        'thesis_title': 'PhD Thesis Title',
        'total_pages': 215,
        'sections': all_sections
    }
    
    print_progress("\nConsolidating all extracted sections...")
    enhanced_structure = calculate_section_page_ranges(final_structure)
    
    enhanced_yaml = yaml.dump(enhanced_structure, default_flow_style=False, sort_keys=False)
    
    yaml_output_path = output_path / "thesis_contents.yaml"
    with open(yaml_output_path, 'w', encoding='utf-8') as f:
        f.write(enhanced_yaml)

    print_completion_summary(str(yaml_output_path), end_page - start_page + 1, "pages processed")
    return True




def main():
    """Main function for TOC contents parsing."""
    parser = argparse.ArgumentParser(
        description='Parse table of contents to extract chapter structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python parse_toc_contents.py thesis.pdf 9 12 structure/
  
This will extract the chapter/section structure from pages 9-12 and save it to structure/thesis_contents.yaml
"""
    )
    
    parser.add_argument('pdf_path', help='Path to source PDF file')
    parser.add_argument('start_page', type=int, help='Starting page number (1-based)')
    parser.add_argument('end_page', type=int, help='Ending page number (1-based)')
    parser.add_argument('output_dir', help='Output directory for structure files')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.pdf_path).exists():
        print(f"ERROR: PDF file not found: {args.pdf_path}")
        return 1
    
    # Parse TOC contents
    success = parse_toc_contents(
        args.pdf_path,
        args.start_page,
        args.end_page,
        args.output_dir
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
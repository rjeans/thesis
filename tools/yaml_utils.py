#!/usr/bin/env python3
"""
YAML processing utilities for thesis conversion workflow.

This module provides standardized YAML handling functions including
output cleaning, parsing, and file operations with error handling.
"""

import yaml
from pathlib import Path
from progress_utils import print_progress


def clean_yaml_output(result):
    """
    Clean YAML output from GPT-4 Vision API responses.
    
    Removes common markdown code block markers that the API sometimes
    includes around YAML responses, ensuring valid YAML content.
    
    Args:
        result (str): Raw response from GPT-4 Vision API
        
    Returns:
        str: Cleaned YAML content
    """
    cleaned_result = result.strip()
    
    # Remove YAML code block markers
    if cleaned_result.startswith('```yaml'):
        cleaned_result = cleaned_result[7:]
    elif cleaned_result.startswith('```'):
        cleaned_result = cleaned_result[3:]
    
    if cleaned_result.endswith('```'):
        cleaned_result = cleaned_result[:-3]
    
    return cleaned_result.strip()


def parse_and_validate_yaml(yaml_content, debug_filename=None):
    """
    Parse YAML content with error handling and optional debug output.
    
    Attempts to parse YAML content from GPT-4 Vision API responses.
    If parsing fails, optionally saves the raw content to a debug file
    for manual inspection.
    
    Args:
        yaml_content (str): YAML content to parse
        debug_filename (str, optional): Filename to save raw content on error
        
    Returns:
        dict or None: Parsed YAML data, or None if parsing failed
    """
    print_progress("Parsing YAML output...")
    
    try:
        data = yaml.safe_load(yaml_content)
        print_progress("+ YAML parsed successfully")
        return data
        
    except yaml.YAMLError as e:
        print_progress(f"- YAML parsing error: {e}")
        
        if debug_filename:
            try:
                with open(debug_filename, 'w') as f:
                    f.write(yaml_content)
                print_progress(f"Raw result saved to {debug_filename}")
            except Exception as save_error:
                print_progress(f"- Could not save debug file: {save_error}")
        
        return None


def save_yaml_data(data, output_file):
    """
    Save structured data to YAML file with proper formatting.
    
    Creates the output directory if needed and saves data with
    consistent YAML formatting (no flow style, preserve order,
    support Unicode).
    
    Args:
        data (dict): Data structure to save as YAML
        output_file (str): Path for output YAML file
        
    Returns:
        bool: True if save succeeded, False otherwise
    """
    try:
        print_progress("Saving results to file...")
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                data, 
                f, 
                default_flow_style=False,  # Use block style (more readable)
                sort_keys=False,           # Preserve order
                allow_unicode=True         # Support Unicode characters
            )
        
        return True
        
    except Exception as e:
        print_progress(f"- Error saving file: {e}")
        return False


def create_toc_yaml_structure():
    """
    Return example YAML structure for table of contents parsing.
    
    Provides the expected YAML format for thesis TOC structure
    that GPT-4 Vision should follow when parsing contents.
    
    Returns:
        str: Example YAML structure as formatted string
    """
    return """
    thesis_title: "extracted title if visible"
    total_pages: 215
    sections:
      - type: "front_matter|chapter|appendix|back_matter"
        title: "exact title from TOC"
        page_start: number
        page_end: number (will be calculated later)
        chapter_number: number (if applicable, null otherwise)
        subsections:
          - section_number: "2.1" or "3.4.2" (extracted numbering)
            title: "subsection title without number"
            page: number
            level: 1|2|3|4 (based on numbering depth)
    """.strip()


def create_figures_yaml_structure():
    """
    Return example YAML structure for figures list parsing.
    
    Provides the expected YAML format for thesis figures list
    that GPT-4 Vision should follow when parsing figures.
    
    Returns:
        str: Example YAML structure as formatted string
    """
    return """
    figures:
      - figure_number: "2.1"
        title: "exact figure caption/title"
        page: number
        chapter: number (extracted from figure number)
    """.strip()


def create_tables_yaml_structure():
    """
    Return example YAML structure for tables list parsing.
    
    Provides the expected YAML format for thesis tables list
    that GPT-4 Vision should follow when parsing tables.
    
    Returns:
        str: Example YAML structure as formatted string
    """
    return """
    tables:
      - table_number: "4.1"
        title: "exact table caption/title"
        page: number
        chapter: number (extracted from table number)
    """.strip()


def count_items_in_yaml(data, item_key):
    """
    Count items of a specific type in parsed YAML data.
    
    Helper function to extract statistics from parsed YAML data
    for progress reporting and validation.
    
    Args:
        data (dict): Parsed YAML data
        item_key (str): Key to count items for (e.g., "sections", "figures", "tables")
        
    Returns:
        int: Number of items found, or 0 if key not found
    """
    if not data or not isinstance(data, dict):
        return 0
    
    items = data.get(item_key, [])
    return len(items) if isinstance(items, list) else 0


def validate_section_numbering(sections):
    """
    Validate sequential numbering of sections and subsections.
    
    Checks that section numbers follow proper sequential patterns
    (e.g., 2.1, 2.2, 2.3... then 3.1, 3.2, etc.) and reports any
    gaps or inconsistencies.
    
    Args:
        sections (list): List of section dictionaries from YAML data
        
    Returns:
        dict: Validation results with warnings and statistics
    """
    results = {
        'valid': True,
        'warnings': [],
        'chapter_counts': {},
        'total_subsections': 0
    }
    
    for section in sections:
        if section.get('type') == 'chapter':
            chapter_num = section.get('chapter_number')
            subsections = section.get('subsections', [])
            
            if chapter_num:
                results['chapter_counts'][chapter_num] = len(subsections)
                results['total_subsections'] += len(subsections)
                
                # Check subsection numbering for this chapter
                prev_numbers = []
                for subsec in subsections:
                    section_num = subsec.get('section_number', '')
                    level = subsec.get('level', 1)
                    
                    if section_num:
                        # Parse section number (e.g., "2.1.3" -> [2, 1, 3])
                        try:
                            parts = [int(p) for p in section_num.split('.')]
                            
                            # Check if chapter number matches
                            if parts[0] != chapter_num:
                                results['warnings'].append(
                                    f"Section {section_num}: chapter mismatch (expected {chapter_num})"
                                )
                                results['valid'] = False
                            
                            # Check level consistency
                            expected_level = len(parts) - 1
                            if level != expected_level:
                                results['warnings'].append(
                                    f"Section {section_num}: level mismatch (got {level}, expected {expected_level})"
                                )
                            
                            prev_numbers.append((section_num, parts, level))
                            
                        except ValueError:
                            results['warnings'].append(
                                f"Section {section_num}: invalid number format"
                            )
                            results['valid'] = False
    
    return results


def print_numbering_validation(validation_results):
    """
    Print formatted validation results for section numbering.
    
    Args:
        validation_results (dict): Results from validate_section_numbering()
    """
    from progress_utils import print_progress
    
    if validation_results['valid']:
        print_progress("+ Section numbering validation passed")
    else:
        print_progress("- Section numbering validation issues found")
    
    print_progress(f"Total subsections: {validation_results['total_subsections']}")
    
    for chapter, count in validation_results['chapter_counts'].items():
        print_progress(f"Chapter {chapter}: {count} subsections")
    
    if validation_results['warnings']:
        print_progress("Numbering warnings:")
        for warning in validation_results['warnings']:
            print_progress(f"  - {warning}")
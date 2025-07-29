#!/usr/bin/env python3
"""
YAML processing utilities for thesis conversion workflow.

This module provides standardized YAML handling functions for
loading and processing thesis structure metadata.
"""

import yaml
from pathlib import Path


def load_yaml_file(file_path):
    """
    Load and parse a YAML file.
    
    Args:
        file_path (str or Path): Path to YAML file
    
    Returns:
        dict: Parsed YAML data, or None if loading failed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading YAML file {file_path}: {e}")
        return None


def save_yaml_file(data, file_path):
    """
    Save data to a YAML file.
    
    Args:
        data (dict): Data to save
        file_path (str or Path): Output file path
    
    Returns:
        bool: True if saving succeeded
    """
    try:
        # Ensure parent directories exist
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
        return True
    except Exception as e:
        print(f"Error saving YAML file {file_path}: {e}")
        return False


def validate_thesis_structure(structure_data):
    """
    Validate thesis structure YAML data.
    
    Args:
        structure_data (dict): Structure data to validate
    
    Returns:
        bool: True if structure is valid
    """
    if not isinstance(structure_data, dict):
        return False
    
    # Check for required top-level fields
    required_fields = ['thesis_title', 'sections']
    for field in required_fields:
        if field not in structure_data:
            print(f"Missing required field: {field}")
            return False
    
    # Check sections structure
    sections = structure_data.get('sections', [])
    if not isinstance(sections, list):
        print("Sections must be a list")
        return False
    
    for i, section in enumerate(sections):
        if not isinstance(section, dict):
            print(f"Section {i} must be a dictionary")
            return False
        
        # Check required section fields
        if 'title' not in section:
            print(f"Section {i} missing title")
            return False
    
    return True


def find_chapter_by_identifier(structure_data, chapter_id):
    """
    Find a chapter in the structure by identifier.
    
    Args:
        structure_data (dict): Thesis structure data
        chapter_id (str): Chapter identifier (number or title)
    
    Returns:
        dict: Chapter data, or None if not found
    """
    if not structure_data or 'sections' not in structure_data:
        return None
    
    for section in structure_data['sections']:
        if section.get('type') != 'chapter':
            continue
        
        chapter_number = section.get('chapter_number')
        title = section.get('title', '')
        
        # Match by chapter number
        if str(chapter_number) == str(chapter_id):
            return section
        
        # Match by title
        if title.lower() == chapter_id.lower():
            return section
        
        # Match by "Chapter X" format
        if f"chapter {chapter_number}" == chapter_id.lower():
            return section
    
    return None


def get_chapter_page_range(chapter_data):
    """
    Get the page range for a chapter.
    
    Args:
        chapter_data (dict): Chapter data
    
    Returns:
        tuple: (start_page, end_page) or None if not available
    """
    if not chapter_data:
        return None
    
    start_page = chapter_data.get('page_start')
    end_page = chapter_data.get('page_end')
    
    if start_page is not None and end_page is not None:
        return (start_page, end_page)
    
    return None
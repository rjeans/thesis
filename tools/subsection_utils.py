#!/usr/bin/env python3
"""
Simplified subsection utilities for section-based processing.
"""

import yaml
from pathlib import Path
from progress_utils import print_progress


def find_leaf_sections(structure_dir, chapter_identifier=None):
    """
    Find all leaf sections (lowest-level sections without subsections) for processing.
    
    Args:
        structure_dir (str): Directory containing YAML structure files
        chapter_identifier (str, optional): Specific chapter to analyze, or None for all chapters
    
    Returns:
        list: List of leaf section identifiers suitable for individual processing
    """
    structure_file = Path(structure_dir) / "thesis_contents.yaml"
    
    if not structure_file.exists():
        print_progress(f"- Structure file not found: {structure_file}")
        return []
    
    try:
        with open(structure_file, 'r', encoding='utf-8') as f:
            structure_data = yaml.safe_load(f)
        
        if 'sections' not in structure_data:
            return []
        
        leaf_sections = []
        
        # Look through all chapters or specific chapter
        for chapter in structure_data['sections']:
            if chapter.get('type') != 'chapter':
                continue
                
            # Skip if looking for specific chapter and this isn't it
            if chapter_identifier and str(chapter.get('chapter_number', '')) != str(chapter_identifier):
                continue
                
            subsections = chapter.get('subsections', [])
            
            # Build hierarchy map to identify leaf nodes
            section_hierarchy = {}
            for subsection in subsections:
                section_number = str(subsection.get('section_number', ''))
                if section_number:
                    section_hierarchy[section_number] = subsection
            
            # Find leaf sections (sections that don't have any subsections under them)
            for section_number, section_data in section_hierarchy.items():
                is_leaf = True
                
                # Check if any other section starts with this section number + "."
                for other_section in section_hierarchy.keys():
                    if (other_section != section_number and 
                        other_section.startswith(section_number + '.') and
                        len(other_section.split('.')) == len(section_number.split('.')) + 1):
                        is_leaf = False
                        break
                
                if is_leaf:
                    leaf_sections.append({
                        'section_number': section_number,
                        'title': section_data.get('title', ''),
                        'chapter_title': chapter.get('title', ''),
                        'start_page': section_data.get('start_page', section_data.get('page')),
                        'end_page': section_data.get('end_page'),
                        'level': section_data.get('level', 0)
                    })
        
        # Sort by section number for consistent processing order
        leaf_sections.sort(key=lambda x: [int(n) for n in x['section_number'].split('.')])
        
        return leaf_sections
        
    except Exception as e:
        print_progress(f"- Error loading structure file: {e}")
        return []


def load_chapter_subsections(structure_dir, chapter_identifier):
    """Load chapter subsections from YAML structure files."""
    structure_file = Path(structure_dir) / "thesis_contents.yaml"
    
    if not structure_file.exists():
        print_progress(f"- Structure file not found: {structure_file}")
        return None
    
    try:
        with open(structure_file, 'r', encoding='utf-8') as f:
            structure_data = yaml.safe_load(f)
        
        # Find the chapter by identifier
        if 'sections' not in structure_data:
            return None
            
        for chapter in structure_data['sections']:
            if (str(chapter.get('chapter_number', '')) == str(chapter_identifier) or
                chapter.get('title', '').lower() == chapter_identifier.lower() or
                f"chapter {chapter.get('chapter_number', '')}" == chapter_identifier.lower()):
                return chapter
                
        print_progress(f"- Chapter '{chapter_identifier}' not found in structure")
        return None
        
    except Exception as e:
        print_progress(f"- Error loading structure file: {e}")
        return None


def load_individual_section(structure_dir, section_identifier):
    """
    Load a specific section (e.g., 2.1, 2.1.1) from YAML structure files.
    
    Args:
        structure_dir (str): Directory containing YAML structure files
        section_identifier (str): Section identifier (e.g., "2.1", "2.1.1")
    
    Returns:
        dict: Section data with parent chapter context and all subsections, or None if not found
    """
    structure_file = Path(structure_dir) / "thesis_contents.yaml"
    
    if not structure_file.exists():
        print_progress(f"- Structure file not found: {structure_file}")
        return None
    
    try:
        with open(structure_file, 'r', encoding='utf-8') as f:
            structure_data = yaml.safe_load(f)
        
        if 'sections' not in structure_data:
            return None
        
        # First, check if this is a top-level section by universal section number
        for section in structure_data['sections']:
            section_number = section.get('section_number', '')
            if section_number == section_identifier:
                print_progress(f"+ Found top-level section by universal number: {section_number}")
                
                # Calculate optimal page range based on subsections
                subsections = section.get('subsections', [])
                start_page = section.get('page_start', 1)
                
                if subsections:
                    # Has subsections - process only the parent section page (usually just the section heading)
                    # For parent sections, we only want the section heading, not subsection content
                    end_page = start_page  # Process only the page where the section starts
                    
                    print_progress(f"+ Parent section with {len(subsections)} subsections - processing only section heading (page {start_page})")
                else:
                    # No subsections - process full range
                    end_page = section.get('page_end', start_page)
                    print_progress(f"+ Leaf section with no subsections - processing full range (pages {start_page}-{end_page})")
                
                # Create enhanced section data with proper field mapping
                enhanced_section = section.copy()
                enhanced_section['start_page'] = start_page
                enhanced_section['end_page'] = end_page
                
                return {
                    'type': 'top_level_section',
                    'title': section.get('title', ''),
                    'section_type': section.get('type', 'unknown'),
                    'section_number': section_number,
                    'section_data': enhanced_section,
                    'parent_chapter': None,
                    'all_subsections': subsections,
                    'calculated_page_range': {
                        'start_page': start_page,
                        'end_page': end_page
                    }
                }
        
        # Look for the section within all chapters (existing logic for subsections)
        for chapter in structure_data['sections']:
            if chapter.get('type') != 'chapter':
                continue
                
            subsections = chapter.get('subsections', [])
            
            # Find the target section and collect all its subsections
            target_section = None
            section_subsections = []
            
            for subsection in subsections:
                section_number = str(subsection.get('section_number', ''))
                
                # Found the main section (e.g., "2.1")
                if section_number == section_identifier:
                    target_section = subsection
                    section_subsections.append(subsection)
                # Found a subsection that belongs to this section (e.g., "2.1.1", "2.1.2")
                elif section_number.startswith(section_identifier + '.') and len(section_number.split('.')) == len(section_identifier.split('.')) + 1:
                    section_subsections.append(subsection)
            
            if target_section:
                # Enhanced YAML structure already has start_page and end_page calculated
                # Sort subsections by start_page
                section_subsections.sort(key=lambda x: x.get('start_page', x.get('page', 0)))
                
                # Calculate section range based on whether it's a parent or leaf section
                # For token efficiency, parent sections only process their direct content
                child_subsections = [s for s in section_subsections if s.get('section_number', '') != section_identifier]
                
                if len(child_subsections) > 0:  # Parent section with subsections
                    # For parent sections, only process from start until first subsection starts
                    overall_start = target_section.get('start_page', target_section.get('page', 0))
                    
                    # Find first child subsection
                    child_subsections.sort(key=lambda x: x.get('start_page', x.get('page', 0)))
                    first_child_start = child_subsections[0].get('start_page', child_subsections[0].get('page', overall_start))
                    
                    # If first child starts on same page as parent, process only that page
                    # If first child starts on later page, process up to (but not including) that page
                    if first_child_start == overall_start:
                        overall_end = overall_start  # Same page - process only parent content on that page
                    else:
                        overall_end = first_child_start - 1  # Different page - process up to child start
                        
                    print_progress(f"+ Parent section detected - processing only parent content")
                else:  # Leaf section - use full range
                    overall_start = target_section.get('start_page', target_section.get('page', 0))
                    overall_end = target_section.get('end_page', overall_start)
                
                print_progress(f"+ Section {section_identifier} spans pages {overall_start}-{overall_end}")
                print_progress(f"+ Found {len(section_subsections)} subsections:")
                for subsection in section_subsections:
                    start_p = subsection.get('start_page', subsection.get('page', 'Unknown'))
                    end_p = subsection.get('end_page', start_p)
                    print_progress(f"  - {subsection.get('section_number')}: {start_p}-{end_p}")
                
                # Return section with complete context
                return {
                    'type': 'individual_section',
                    'title': f"Section {section_identifier}: {target_section.get('title', '')}",
                    'chapter_number': chapter.get('chapter_number'),
                    'chapter_title': chapter.get('title', ''),
                    'section_data': target_section,
                    'parent_chapter': chapter,
                    'all_subsections': section_subsections,
                    'calculated_page_range': {
                        'start_page': overall_start,
                        'end_page': overall_end
                    }
                }
        
        print_progress(f"- Section '{section_identifier}' not found in structure")
        return None
        
    except Exception as e:
        print_progress(f"- Error loading structure file: {e}")
        return None


def calculate_subsection_page_ranges(chapter_data):
    """Calculate page ranges for each subsection using enhanced YAML structure."""
    if not chapter_data or 'subsections' not in chapter_data:
        return []
    
    subsections = chapter_data['subsections']
    ranges = []
    
    for subsection in subsections:
        # Enhanced structure should already have start_page and end_page
        start_page = subsection.get('start_page') or subsection.get('page')
        end_page = subsection.get('end_page', start_page)
        
        if start_page is None:
            continue
        
        ranges.append({
            **subsection,
            'start_page': start_page,
            'end_page': end_page,
            'page_count': max(1, end_page - start_page + 1)  # Ensure at least 1 page
        })
    
    return ranges


def group_subsections_by_hierarchy(subsection_ranges, max_pages_per_batch):
    """Group subsections into processing batches."""
    if not subsection_ranges:
        return []
    
    batches = []
    current_batch = []
    current_pages = 0
    
    for subsection in subsection_ranges:
        page_count = subsection.get('page_count', 1)
        
        # If adding this subsection would exceed max pages, start new batch
        if current_batch and current_pages + page_count > max_pages_per_batch:
            batches.append(current_batch)
            current_batch = [subsection]
            current_pages = page_count
        else:
            current_batch.append(subsection)
            current_pages += page_count
    
    # Add the last batch if it has content
    if current_batch:
        batches.append(current_batch)
    
    return batches


def create_batch_info(subsection_batch, chapter_data):
    """Create batch information dictionary."""
    if not subsection_batch:
        return None
    
    start_page = min(s.get('start_page', 0) for s in subsection_batch)
    end_page = max(s.get('end_page', 0) for s in subsection_batch)
    page_count = end_page - start_page + 1
    
    section_titles = []
    for subsection in subsection_batch:
        section_num = subsection.get('section_number', '')
        title = subsection.get('title', '')
        if section_num and title:
            section_titles.append(f"{section_num} {title}")
        elif title:
            section_titles.append(title)
    
    # Create batch description
    if len(subsection_batch) == 1:
        batch_description = f"Section {subsection_batch[0].get('section_number', '')}"
    else:
        first_section = subsection_batch[0].get('section_number', '')
        last_section = subsection_batch[-1].get('section_number', '')
        batch_description = f"Sections {first_section}-{last_section}"
    
    return {
        'start_page': start_page,
        'end_page': end_page,
        'page_count': page_count,
        'section_titles': section_titles,
        'batch_description': batch_description,
        'chapter_title': chapter_data.get('title', 'Chapter'),
        'subsection_count': len(subsection_batch)
    }


def print_subsection_batching_plan(batches, chapter_data):
    """Print the batching plan for subsections."""
    chapter_title = chapter_data.get('title', 'Chapter')
    print_progress(f"Processing plan for {chapter_title}:")
    print_progress(f"Total batches: {len(batches)}")
    
    for i, batch in enumerate(batches, 1):
        batch_info = create_batch_info(batch, chapter_data)
        if batch_info:
            print_progress(f"  Batch {i}: {batch_info['batch_description']} "
                         f"(pages {batch_info['start_page']}-{batch_info['end_page']})")
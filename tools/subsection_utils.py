#!/usr/bin/env python3
"""
Simplified subsection utilities for section-based processing.
"""

import yaml
from pathlib import Path
from progress_utils import print_progress


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


def calculate_subsection_page_ranges(chapter_data):
    """Calculate page ranges for each subsection."""
    if not chapter_data or 'subsections' not in chapter_data:
        return []
    
    subsections = chapter_data['subsections']
    ranges = []
    
    for i, subsection in enumerate(subsections):
        start_page = subsection.get('start_page') or subsection.get('page')
        if start_page is None:
            continue
            
        # End page is either the next subsection's start page - 1, or chapter end
        if i + 1 < len(subsections):
            next_start = subsections[i + 1].get('start_page') or subsections[i + 1].get('page')
            end_page = next_start - 1 if next_start else start_page
        else:
            end_page = chapter_data.get('page_end') or chapter_data.get('end_page', start_page)
        
        ranges.append({
            **subsection,
            'start_page': start_page,
            'end_page': end_page,
            'page_count': end_page - start_page + 1
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
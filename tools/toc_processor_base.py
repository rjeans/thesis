#!/usr/bin/env python3
"""
Base class for TOC processing across different content types.

This module provides a common framework for processing table of contents,
figures lists, and tables lists from PDF files using GPT-4 Vision.

Classes:
- TOCProcessorBase: Abstract base class with common processing logic
- ContentConfig: Configuration container for content-specific settings
"""

import os
import openai
import argparse
from pathlib import Path
import json
from abc import ABC, abstractmethod

# Import common utilities
from pdf_utils import extract_pages_to_images, extract_text_from_pdf_page
from progress_utils import print_progress, print_section_header, print_completion_summary
from gpt_vision_utils import (
    encode_images_for_vision,
    call_gpt_vision_api,
    cleanup_temp_directory
)
from yaml_utils import (
    clean_yaml_output,
    parse_and_validate_yaml,
    save_yaml_data,
    count_items_in_yaml
)


class ContentConfig:
    """Configuration container for content-specific settings."""
    
    def __init__(self, content_type, yaml_key, max_tokens, temp_dir_suffix, 
                 file_prefix, debug_prefix, item_name_singular, item_name_plural):
        self.content_type = content_type           # "contents", "figures", "tables"
        self.yaml_key = yaml_key                   # "page_entries", "page_figures", "page_tables"
        self.max_tokens = max_tokens               # Token limit for API calls
        self.temp_dir_suffix = temp_dir_suffix     # For temp directory names
        self.file_prefix = file_prefix             # For generated filenames
        self.debug_prefix = debug_prefix           # For debug file names
        self.item_name_singular = item_name_singular # "entry", "figure", "table"
        self.item_name_plural = item_name_plural   # "entries", "figures", "tables"


class TOCProcessorBase(ABC):
    """
    Abstract base class for TOC processing.
    
    Provides common functionality for processing different types of TOC content
    while allowing content-specific customization through abstract methods.
    """
    
    def __init__(self, config: ContentConfig):
        self.config = config
        self.temp_dir = f"/tmp/toc_{config.temp_dir_suffix}"
    
    @abstractmethod
    def create_prompt(self, extracted_text=None):
        """Create content-specific prompt for GPT-4 Vision."""
        pass
    
    @abstractmethod
    def generate_simple_text_output(self, yaml_data, output_file):
        """Generate human-readable text format for validation."""
        pass
    
    @abstractmethod
    def get_sort_key_function(self):
        """Return a function for sorting extracted items."""
        pass
    
    def parse_single_page(self, pdf_path, page_num, api_key, page_index, total_pages, 
                         temp_dir, output_dir=None, debug=False):
        """
        Parse a single page using GPT-4 Vision API with text guidance.
        
        Args:
            pdf_path (str): Path to the thesis PDF file
            page_num (int): Page number to process (1-based)
            api_key (str): OpenAI API key for GPT-4 Vision access
            page_index (int): Current page index for progress tracking (1-based)
            total_pages (int): Total number of pages to process
            temp_dir (str): Directory for temporary files
            output_dir (Path, optional): Output directory for debug files
            debug (bool): Whether to save debug files
            
        Returns:
            tuple: (dict or None, dict) - Parsed YAML data and diagnostic info
        """
        openai.api_key = api_key
        
        print_progress(f"Processing {self.config.content_type} page {page_index}/{total_pages}: page {page_num}")
        
        # Initialize diagnostic information
        diagnostics = {
            'page_number': page_num,
            'page_index': page_index,
            'total_pages': total_pages,
            'extraction_success': False,
            'text_extraction_success': False,
            'api_success': False,
            'yaml_parsing_success': False,
            f'{self.config.item_name_plural}_extracted': 0,
            'raw_response_length': 0,
            'cleaned_response_length': 0,
            'text_guidance_length': 0,
            'error_details': None
        }
        
        # Extract text from PDF page for guidance
        extracted_text = extract_text_from_pdf_page(pdf_path, page_num)
        if extracted_text:
            diagnostics['text_extraction_success'] = True
            diagnostics['text_guidance_length'] = len(extracted_text)
            print_progress(f"+ Extracted {len(extracted_text)} characters of text for guidance")
        else:
            print_progress("- No text extracted from PDF (will rely on vision only)")
        
        # Extract single page as image
        images = extract_pages_to_images(
            pdf_path, page_num, page_num, temp_dir,
            dpi=200, page_prefix=f"{self.config.file_prefix}-page-{page_num}"
        )
        
        if not images:
            print_progress(f"- Failed to extract page {page_num}")
            diagnostics['error_details'] = "PDF page extraction failed"
            return None, diagnostics
        
        diagnostics['extraction_success'] = True
        diagnostics['images_created'] = len(images)
        
        # Encode images for Vision API
        image_contents = encode_images_for_vision(images, show_progress=False)
        
        # Create prompt with text guidance
        prompt = self.create_prompt(extracted_text)
        
        # Call GPT-4 Vision API
        max_tokens = self.config.max_tokens
        diagnostics['max_tokens_used'] = max_tokens
        
        result = call_gpt_vision_api(
            prompt, image_contents,
            model="gpt-4o", max_tokens=max_tokens
        )
        
        diagnostics['raw_response_length'] = len(result) if result else 0
        
        if result.startswith("Error:"):
            print_progress(f"- API error for page {page_num}: {result}")
            diagnostics['error_details'] = result
            return None, diagnostics
        
        diagnostics['api_success'] = True
        
        # Parse YAML response
        cleaned_result = clean_yaml_output(result)
        diagnostics['cleaned_response_length'] = len(cleaned_result)
        
        # Save raw response for debugging (only if debug flag is enabled)
        if debug:
            if output_dir:
                debug_file = output_dir / f'{self.config.debug_prefix}_page_{page_num}_debug.txt'
            else:
                debug_file = f'{self.config.debug_prefix}_page_{page_num}_debug.txt'
            try:
                with open(debug_file, 'w') as f:
                    f.write(f"=== {self.config.content_type.upper()} PAGE {page_num} DEBUG INFO ===\n")
                    f.write(f"Page: {page_num}\n")
                    f.write(f"Text guidance length: {diagnostics['text_guidance_length']}\n")
                    f.write(f"Raw response length: {diagnostics['raw_response_length']}\n")
                    f.write(f"Cleaned response length: {diagnostics['cleaned_response_length']}\n")
                    f.write(f"Max tokens: {max_tokens}\n")
                    if extracted_text:
                        f.write(f"\n=== EXTRACTED TEXT ===\n")
                        f.write(extracted_text[:2000] + ('...' if len(extracted_text) > 2000 else ''))
                    f.write("\n\n=== RAW RESPONSE ===\n")
                    f.write(result)
                    f.write("\n\n=== CLEANED RESPONSE ===\n")
                    f.write(cleaned_result)
                diagnostics['debug_file_created'] = str(debug_file)
            except Exception as e:
                diagnostics['debug_file_error'] = str(e)
        else:
            diagnostics['debug_file_created'] = None
        
        data = parse_and_validate_yaml(cleaned_result, f'{self.config.debug_prefix}_page_{page_num}_debug.txt')
        
        if data:
            diagnostics['yaml_parsing_success'] = True
            items = data.get(self.config.yaml_key, [])
            diagnostics[f'{self.config.item_name_plural}_extracted'] = len(items)
            
            print_progress(f"+ Page {page_num}: extracted {len(items)} {self.config.item_name_plural}")
        else:
            diagnostics['error_details'] = "YAML parsing failed"
            print_progress(f"- Page {page_num}: YAML parsing failed")
        
        return data, diagnostics
    
    def merge_pages(self, page_data_list, page_diagnostics_list):
        """
        Merge data from multiple pages into a single coherent structure.
        
        Args:
            page_data_list (list): List of parsed YAML data from each page
            page_diagnostics_list (list): List of diagnostic info from each page
            
        Returns:
            tuple: (dict, dict) - Merged YAML structure and comprehensive diagnostics
        """
        print_progress(f"Merging {self.config.content_type} data from all pages...")
        
        # Create comprehensive diagnostics
        merge_diagnostics = {
            'total_pages_processed': len([d for d in page_diagnostics_list if d]),
            'successful_pages': 0,
            'failed_pages': 0,
            'page_details': page_diagnostics_list,
            'pages_processed': [],
            f'{self.config.item_name_plural}_by_page': {}
        }
        
        # Initialize merged structure
        merged_data = {
            'thesis_title': 'PhD Thesis - Richard Jeans 1992',
            'total_pages': 215,
            self.config.item_name_plural: []
        }
        
        # Collect all items from all pages with detailed tracking
        all_items = []
        
        for i, (page_data, page_diag) in enumerate(zip(page_data_list, page_diagnostics_list)):
            if not page_diag:
                merge_diagnostics['failed_pages'] += 1
                continue
                
            page_num = page_diag.get('page_number', i + 1)
            
            if page_data and self.config.yaml_key in page_data:
                items = page_data[self.config.yaml_key]
                if items:  # Check if items is not empty
                    all_items.extend(items)
                    merge_diagnostics['successful_pages'] += 1
                    merge_diagnostics[f'{self.config.item_name_plural}_by_page'][page_num] = {
                        'count': len(items),
                        'page': page_num
                    }
                    merge_diagnostics['pages_processed'].append(page_num)
            else:
                merge_diagnostics['failed_pages'] += 1
        
        print_progress(f"Found {len(all_items)} total {self.config.item_name_plural} across {merge_diagnostics['successful_pages']} successful pages")
        
        # Sort items if sorting function is available
        try:
            sort_key_func = self.get_sort_key_function()
            if sort_key_func:
                all_items.sort(key=sort_key_func)
                print_progress(f"+ {self.config.item_name_plural.title()} sorted")
        except Exception as e:
            print_progress(f"- Could not sort {self.config.item_name_plural}: {e}")
        
        # Add processed items to merged structure
        merged_data[self.config.item_name_plural] = all_items
        
        # Add extraction metadata
        merged_data['extraction_metadata'] = {
            'pages_processed': merge_diagnostics['successful_pages'],
            f'total_{self.config.item_name_plural}_extracted': len(all_items),
            'pages_covered': merge_diagnostics['pages_processed'],
            'extraction_date': __import__('datetime').datetime.now().isoformat(),
            'processing_method': 'single_page_with_text_guidance'
        }
        
        return merged_data, merge_diagnostics
    
    def process_pages(self, pdf_path, start_page, end_page, api_key, output_dir=None, debug=False):
        """
        Process pages individually with text guidance.
        
        Args:
            pdf_path (str): Path to the thesis PDF file
            start_page (int): First page to process (1-based)
            end_page (int): Last page to process (1-based)
            api_key (str): OpenAI API key for GPT-4 Vision access
            output_dir (Path, optional): Output directory for debug files
            debug (bool): Whether to save debug files
            
        Returns:
            dict or None: Complete merged structure, or None if failed
        """
        total_pages = end_page - start_page + 1
        
        print_progress(f"Starting single-page {self.config.content_type} processing with text guidance:")
        print_progress(f"  Total pages: {total_pages}")
        print_progress(f"  Processing method: One page at a time")
        print_progress(f"  Text guidance: Enabled")
        print_progress(f"  Mathematical symbol handling: Enabled")
        
        # Process pages individually
        page_data_list = []
        page_diagnostics_list = []
        
        for page_index, current_page in enumerate(range(start_page, end_page + 1), 1):
            page_data, page_diagnostics = self.parse_single_page(
                pdf_path, current_page, api_key, 
                page_index, total_pages, self.temp_dir, output_dir, debug
            )
            
            page_data_list.append(page_data)
            page_diagnostics_list.append(page_diagnostics)
            
            if not page_data:
                print_progress(f"- Page {current_page}: processing failed")
                if page_diagnostics and page_diagnostics.get('error_details'):
                    print_progress(f"  Error: {page_diagnostics['error_details']}")
        
        # Clean up temporary files
        cleanup_temp_directory(self.temp_dir)
        
        # Merge all page data into final structure
        successful_pages = [p for p in page_data_list if p is not None]
        if successful_pages:
            merged_data, merge_diagnostics = self.merge_pages(page_data_list, page_diagnostics_list)
            print_progress(f"Successfully processed {len(successful_pages)}/{total_pages} pages")
            
            # Save comprehensive diagnostics
            if output_dir:
                diagnostics_file = output_dir / f"{self.config.content_type}_extraction_diagnostics.json"
            else:
                diagnostics_file = f"{self.config.content_type}_extraction_diagnostics.json"
            try:
                with open(diagnostics_file, 'w') as f:
                    json.dump({
                        'processing_summary': {
                            'total_pages': total_pages,
                            'processing_method': 'single_page_with_text_guidance',
                            'successful_pages': len(successful_pages),
                            'failed_pages': total_pages - len(successful_pages),
                            'text_guidance_enabled': True,
                            'mathematical_formatting_enabled': True
                        },
                        'page_diagnostics': page_diagnostics_list,
                        'merge_diagnostics': merge_diagnostics
                    }, f, indent=2)
                print_progress(f"+ Detailed diagnostics saved to {diagnostics_file}")
            except Exception as e:
                print_progress(f"- Could not save diagnostics: {e}")
            
            return merged_data
        else:
            print_progress("- No pages successfully processed")
            return None
    
    def main(self, args):
        """
        Main processing function with standardized argument handling.
        
        Args:
            args: Parsed command line arguments
            
        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        # Validate API key availability
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("ERROR: Please set your OPENAI_API_KEY environment variable")
            return 1
        
        # Validate input file exists
        if not Path(args.pdf_path).exists():
            print(f"ERROR: PDF file not found: {args.pdf_path}")
            return 1
        
        # Create output directory if it doesn't exist
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define standardized output files
        yaml_file = output_dir / f"thesis_{self.config.content_type}.yaml"
        text_file = output_dir / f"thesis_{self.config.content_type}.txt"
        diagnostics_file = output_dir / f"{self.config.content_type}_extraction_diagnostics.json"
        
        # Display processing information
        print_section_header(f"{self.config.content_type.upper()} PARSING (SINGLE-PAGE WITH TEXT GUIDANCE)")
        print(f"Input PDF: {args.pdf_path}")
        print(f"Pages: {args.start_page}-{args.end_page}")
        print(f"Output directory: {args.output_dir}")
        print(f"Files to be created:")
        print(f"  - {yaml_file}")
        print(f"  - {text_file}")
        print(f"  - {diagnostics_file}")
        print("=" * 60)
        
        # Process the pages
        result = self.process_pages(args.pdf_path, args.start_page, args.end_page, api_key, output_dir, args.debug)
        
        # Check for processing errors
        if result is None:
            print(f"FAILED: Could not extract {self.config.content_type}")
            return 1
        
        # Save structured data to YAML file
        if not save_yaml_data(result, str(yaml_file)):
            return 1
        
        # Generate simple text format for validation
        try:
            self.generate_simple_text_output(result, str(text_file))
        except Exception as e:
            print_progress(f"- Warning: Could not generate text format: {e}")
        
        # Display completion summary
        item_count = count_items_in_yaml(result, self.config.item_name_plural)
        print_completion_summary(str(yaml_file), item_count, self.config.item_name_plural)
        print(f"Text format saved to: {text_file}")
        
        # Validate if needed (can be overridden in subclasses)
        print("=" * 60)
        
        return 0


def create_argument_parser(content_type_name):
    """Create standardized argument parser for TOC processors."""
    parser = argparse.ArgumentParser(
        description=f'Parse {content_type_name} from PDF using single-page GPT-4 Vision processing with text guidance'
    )
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('start_page', type=int, help='Starting page number')
    parser.add_argument('end_page', type=int, help='Ending page number')
    parser.add_argument('output_dir', help='Output directory for all generated files')
    parser.add_argument('--debug', action='store_true', help='Enable debug output (saves per-page debug files)')
    
    return parser
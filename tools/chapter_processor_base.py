#!/usr/bin/env python3
"""
Base class for chapter processing with page-by-page batching strategy.

This module provides a consistent architecture for processing thesis chapters
in manageable batches to avoid token limits, following the same pattern as
TOCProcessorBase for architectural consistency.

Features:
- Page-by-page or small batch processing to avoid token limits
- Intelligent content merging with cross-page continuity
- Context-enhanced conversion with PDF text guidance
- Progress tracking and error handling
- Consistent error recovery and validation
"""

import os
import tempfile
from pathlib import Path
from abc import ABC, abstractmethod
import openai

# Import our utilities
from pdf_utils import extract_pages_to_pdf, pdf_to_images
from gpt_vision_utils import encode_images_for_vision
from progress_utils import print_progress, print_section_header
from yaml_utils import clean_yaml_output


class ChapterProcessorBase(ABC):
    """
    Abstract base class for chapter processing with batching strategy.
    
    This class provides the common infrastructure for processing thesis chapters
    in manageable batches while maintaining content continuity and avoiding
    token limits. Concrete implementations handle specific content types.
    """
    
    def __init__(self, pdf_path, structure_dir=None, batch_size=2):
        """
        Initialize the chapter processor.
        
        Args:
            pdf_path (str): Path to source PDF file
            structure_dir (str, optional): Directory containing YAML structure files
            batch_size (int): Number of pages to process in each batch
        """
        self.pdf_path = Path(pdf_path)
        self.structure_dir = Path(structure_dir) if structure_dir else None
        self.batch_size = batch_size
        
        # Validate API key
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("Please set your OPENAI_API_KEY environment variable")
        
        openai.api_key = self.api_key
        
        # Load structure data if available
        self.structure_data = {}
        if self.structure_dir:
            self.load_structure_data()
    
    def load_structure_data(self):
        """Load chapter structure data from YAML files."""
        # Load contents structure
        contents_file = self.structure_dir / "thesis_contents.yaml"
        if contents_file.exists():
            try:
                import yaml
                with open(contents_file, 'r', encoding='utf-8') as f:
                    self.structure_data['contents'] = yaml.safe_load(f)
                print_progress("+ Loaded chapter contents structure")
            except Exception as e:
                print_progress(f"- Failed to load contents structure: {e}")
        
        # Load figures structure
        figures_file = self.structure_dir / "thesis_figures.yaml"
        if figures_file.exists():
            try:
                import yaml
                with open(figures_file, 'r', encoding='utf-8') as f:
                    self.structure_data['figures'] = yaml.safe_load(f)
                print_progress("+ Loaded figures structure")
            except Exception as e:
                print_progress(f"- Failed to load figures structure: {e}")
        
        # Load tables structure
        tables_file = self.structure_dir / "thesis_tables.yaml"
        if tables_file.exists():
            try:
                import yaml
                with open(tables_file, 'r', encoding='utf-8') as f:
                    self.structure_data['tables'] = yaml.safe_load(f)
                print_progress("+ Loaded tables structure")
            except Exception as e:
                print_progress(f"- Failed to load tables structure: {e}")
    
    def find_chapter_info(self, chapter_name):
        """
        Find chapter information from structure data.
        
        Args:
            chapter_name (str): Chapter identifier (e.g., "Chapter 2", "2")
            
        Returns:
            dict: Chapter information or None if not found
        """
        if not self.structure_data.get('contents'):
            return None
        
        # Normalize chapter name for comparison
        chapter_name_lower = chapter_name.lower().strip()
        
        for section in self.structure_data['contents'].get('sections', []):
            if section.get('type') == 'chapter':
                # Try multiple matching strategies
                title = section.get('title', '').lower()
                chapter_num = str(section.get('chapter_number', ''))
                
                # Match by title, chapter number, or "Chapter X" format
                if (chapter_name_lower in title or 
                    chapter_name_lower == chapter_num or
                    chapter_name_lower == f"chapter {chapter_num}"):
                    return section
        
        return None
    
    def extract_chapter_text_context(self, start_page, end_page):
        """
        Extract text context from chapter pages for guidance.
        
        Args:
            start_page (int): Starting page number
            end_page (int): Ending page number
            
        Returns:
            str: Combined text content for context
        """
        try:
            from pdf_utils import extract_text_from_pdf_page
            
            text_parts = []
            for page_num in range(start_page, end_page + 1):
                page_text = extract_text_from_pdf_page(str(self.pdf_path), page_num)
                if page_text:
                    text_parts.append(f"=== PAGE {page_num} ===\n{page_text}")
            
            return "\n\n".join(text_parts)
        except Exception as e:
            print_progress(f"- Could not extract text context: {e}")
            return ""
    
    def create_batch_pages(self, start_page, end_page):
        """
        Create page batches for processing.
        
        Args:
            start_page (int): Starting page number
            end_page (int): Ending page number
            
        Returns:
            list: List of (batch_start, batch_end) tuples
        """
        batches = []
        current_page = start_page
        
        while current_page <= end_page:
            batch_end = min(current_page + self.batch_size - 1, end_page)
            batches.append((current_page, batch_end))
            current_page = batch_end + 1
        
        return batches
    
    def process_page_batch(self, start_page, end_page, chapter_info, batch_index, total_batches):
        """
        Process a batch of pages.
        
        Args:
            start_page (int): Starting page number for batch
            end_page (int): Ending page number for batch
            chapter_info (dict): Chapter information from structure
            batch_index (int): Current batch index (0-based)
            total_batches (int): Total number of batches
            
        Returns:
            str: Processed markdown content for this batch
        """
        print_progress(f"Processing batch {batch_index + 1}/{total_batches}: pages {start_page}-{end_page}")
        
        # Extract pages to temporary PDF
        with tempfile.TemporaryDirectory(prefix="chapter_batch_") as temp_dir:
            temp_pdf = Path(temp_dir) / f"batch_{batch_index}_{start_page}_{end_page}.pdf"
            
            if not extract_pages_to_pdf(str(self.pdf_path), str(temp_pdf), start_page, end_page):
                print_progress(f"- Failed to extract pages {start_page}-{end_page}")
                return ""
            
            # Convert to images
            images = pdf_to_images(str(temp_pdf), temp_dir, dpi=200, page_prefix=f"batch_{batch_index}")
            if not images:
                print_progress(f"- Failed to convert pages {start_page}-{end_page} to images")
                return ""
            
            # Encode for Vision API
            image_contents = encode_images_for_vision(images)
            if not image_contents:
                print_progress(f"- Failed to encode images for pages {start_page}-{end_page}")
                return ""
            
            # Extract text context for this batch
            text_context = self.extract_chapter_text_context(start_page, end_page)
            
            # Create batch-specific prompt
            prompt = self.create_batch_prompt(
                chapter_info, 
                start_page, 
                end_page, 
                batch_index, 
                total_batches,
                text_context
            )
            
            # Process with GPT-4 Vision
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt}
                        ] + image_contents
                    }],
                    max_tokens=4096,
                    temperature=0.1
                )
                
                if response.choices and response.choices[0].message:
                    result = response.choices[0].message.content
                    if result:
                        # Clean and validate result
                        cleaned_result = self.clean_batch_result(result, start_page, end_page)
                        print_progress(f"+ Successfully processed batch {batch_index + 1}")
                        return cleaned_result
                
                print_progress(f"- Empty response for batch {batch_index + 1}")
                return ""
                
            except Exception as e:
                print_progress(f"- API error for batch {batch_index + 1}: {e}")
                return ""
    
    def merge_batch_results(self, batch_results, chapter_info):
        """
        Merge results from multiple batches into coherent chapter content.
        
        Args:
            batch_results (list): List of markdown content from each batch
            chapter_info (dict): Chapter information from structure
            
        Returns:
            str: Merged chapter content
        """
        if not batch_results:
            return ""
        
        # Filter out empty results
        valid_results = [result.strip() for result in batch_results if result.strip()]
        
        if not valid_results:
            return ""
        
        if len(valid_results) == 1:
            return valid_results[0]
        
        # Merge multiple batches
        merged_content = []
        
        for i, batch_content in enumerate(valid_results):
            if i == 0:
                # First batch: use as-is
                merged_content.append(batch_content)
            else:
                # Subsequent batches: remove duplicate headers and merge
                cleaned_batch = self.remove_duplicate_headers(batch_content, merged_content[-1])
                if cleaned_batch.strip():
                    merged_content.append(cleaned_batch)
        
        # Join with appropriate spacing
        final_content = "\n\n".join(merged_content)
        
        # Post-process the merged content
        return self.post_process_merged_content(final_content, chapter_info)
    
    def remove_duplicate_headers(self, new_content, previous_content):
        """
        Remove duplicate headers from new content that already exist in previous content.
        
        Args:
            new_content (str): New batch content
            previous_content (str): Previously processed content
            
        Returns:
            str: Cleaned new content without duplicates
        """
        # Simple implementation - can be enhanced based on specific needs
        lines = new_content.split('\n')
        previous_lines = previous_content.split('\n')
        
        # Get headers from previous content
        previous_headers = set()
        for line in previous_lines:
            line = line.strip()
            if line.startswith('#') and line.endswith('>'):  # Headers with anchors
                previous_headers.add(line)
        
        # Filter out duplicate headers from new content
        filtered_lines = []
        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith('#') and line_stripped.endswith('>'):
                if line_stripped not in previous_headers:
                    filtered_lines.append(line)
            else:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def process_chapter(self, chapter_name, output_path):
        """
        Process a complete chapter using batching strategy.
        
        Args:
            chapter_name (str): Chapter identifier
            output_path (str): Output file path for markdown
            
        Returns:
            bool: True if processing succeeded, False otherwise
        """
        print_section_header(f"PROCESSING CHAPTER: {chapter_name}")
        
        # Find chapter information
        chapter_info = self.find_chapter_info(chapter_name)
        if not chapter_info:
            print_progress(f"- Chapter '{chapter_name}' not found in structure data")
            return False
        
        start_page = chapter_info.get('page_start')
        end_page = chapter_info.get('page_end')
        
        if not start_page or not end_page:
            print_progress(f"- Invalid page range for chapter '{chapter_name}'")
            return False
        
        print_progress(f"Chapter: {chapter_info.get('title', 'Unknown')}")
        print_progress(f"Pages: {start_page}-{end_page}")
        
        # Create page batches
        batches = self.create_batch_pages(start_page, end_page)
        print_progress(f"Processing in {len(batches)} batch(es) of {self.batch_size} pages each")
        
        # Process each batch
        batch_results = []
        for i, (batch_start, batch_end) in enumerate(batches):
            result = self.process_page_batch(
                batch_start, batch_end, chapter_info, i, len(batches)
            )
            batch_results.append(result)
        
        # Merge batch results
        print_progress("Merging batch results...")
        merged_content = self.merge_batch_results(batch_results, chapter_info)
        
        if not merged_content:
            print_progress("- No content generated from batches")
            return False
        
        # Save to output file
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(merged_content)
            
            print_progress(f"+ Chapter saved to: {output_path}")
            print_progress(f"+ Content length: {len(merged_content)} characters")
            
            return True
            
        except Exception as e:
            print_progress(f"- Failed to save chapter: {e}")
            return False
    
    # Abstract methods that concrete implementations must provide
    
    @abstractmethod
    def create_batch_prompt(self, chapter_info, start_page, end_page, batch_index, total_batches, text_context):
        """
        Create a processing prompt for a specific batch of pages.
        
        Args:
            chapter_info (dict): Chapter information from structure
            start_page (int): Starting page number for batch
            end_page (int): Ending page number for batch
            batch_index (int): Current batch index (0-based)
            total_batches (int): Total number of batches
            text_context (str): Extracted text context for guidance
            
        Returns:
            str: Formatted prompt for GPT-4 Vision
        """
        pass
    
    @abstractmethod
    def clean_batch_result(self, result, start_page, end_page):
        """
        Clean and validate the result from a batch processing.
        
        Args:
            result (str): Raw result from GPT-4 Vision
            start_page (int): Starting page number for batch
            end_page (int): Ending page number for batch
            
        Returns:
            str: Cleaned and validated result
        """
        pass
    
    @abstractmethod
    def post_process_merged_content(self, content, chapter_info):
        """
        Post-process the merged content from all batches.
        
        Args:
            content (str): Merged content from all batches
            chapter_info (dict): Chapter information from structure
            
        Returns:
            str: Final processed content
        """
        pass
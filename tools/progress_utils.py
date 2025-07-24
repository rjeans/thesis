#!/usr/bin/env python3
"""
Progress tracking utilities for thesis conversion workflow.

This module provides consistent progress reporting across all scripts
with timestamps, step counters, and visual indicators.
"""

import time
import sys


def print_progress(message, step=None, total=None):
    """
    Print progress message with timestamp and optional step counter.
    
    Provides consistent progress reporting across all thesis conversion scripts.
    Messages are flushed immediately to ensure real-time feedback during
    long-running operations like GPT-4 Vision API calls.
    
    Args:
        message (str): Progress message to display
        step (int, optional): Current step number (1-based)
        total (int, optional): Total number of steps
        
    Example:
        print_progress("Processing files...")
        print_progress("Converting page", 3, 10)  # Shows [3/10]
    """
    timestamp = time.strftime("%H:%M:%S")
    
    if step and total:
        print(f"[{timestamp}] [{step}/{total}] {message}")
    else:
        print(f"[{timestamp}] {message}")
    
    # Flush output for real-time feedback
    sys.stdout.flush()


def print_section_header(title, width=60):
    """
    Print a formatted section header for script output.
    
    Creates visually consistent section separators across all scripts
    to improve readability of console output.
    
    Args:
        title (str): Section title to display
        width (int): Width of the header line (default 60)
    """
    separator = "=" * width
    print(separator)
    print(title)
    print(separator)


def print_completion_summary(output_file, item_count=None, item_type="items"):
    """
    Print standardized completion summary for thesis conversion scripts.
    
    Provides consistent completion reporting with file paths and statistics.
    
    Args:
        output_file (str): Path to the generated output file
        item_count (int, optional): Number of items processed
        item_type (str): Type of items (e.g., "chapters", "figures", "tables")
    """
    print_progress("PARSING COMPLETE")
    print("=" * 60)
    print(f"Output saved to: {output_file}")
    
    if item_count is not None:
        print(f"Found {item_count} {item_type}")
    
    print("=" * 60)


def time_operation(operation_name):
    """
    Context manager for timing operations with progress reporting.
    
    Automatically reports the start and completion time of operations.
    
    Args:
        operation_name (str): Name of the operation being timed
        
    Returns:
        TimedOperation: Context manager for timing
        
    Example:
        with time_operation("GPT-4 Vision API call"):
            # ... perform operation ...
            pass
    """
    return TimedOperation(operation_name)


class TimedOperation:
    """Context manager for timing operations with automatic progress reporting."""
    
    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        print_progress(f"Starting {self.operation_name}...")
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed_time = time.time() - self.start_time
        
        if exc_type is None:
            print_progress(f"+ {self.operation_name} completed in {elapsed_time:.1f}s")
        else:
            print_progress(f"- {self.operation_name} failed after {elapsed_time:.1f}s")
        
        return False  # Don't suppress exceptions
#!/usr/bin/env python3
"""Minimal progress utilities - temporary fix for indentation issues."""

import time
import sys
from contextlib import contextmanager

def print_progress(message, step=None, total=None):
    """Print progress message with timestamp."""
    timestamp = time.strftime("%H:%M:%S")
    
    if step and total:
        print(f"[{timestamp}] [{step}/{total}] {message}")
    else:
        print(f"[{timestamp}] {message}")
    
    sys.stdout.flush()

def print_section_header(title, width=60):
    """Print a formatted section header."""
    separator = "=" * width
    print(separator)
    print(title)
    print(separator)

def print_completion_summary(output_file, item_count=None, item_type="items"):
    """Print completion summary."""
    print_progress("PARSING COMPLETE")
    print("=" * 60)
    print(f"Output saved to: {output_file}")
    
    if item_count is not None:
        print(f"Found {item_count} {item_type}")
    
    print("=" * 60)

@contextmanager
def time_operation(description):
    """Context manager to time operations."""
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        print_progress(f"{description} completed in {elapsed:.1f}s")

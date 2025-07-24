#!/usr/bin/env python3
"""
Analyze TOC extraction diagnostics to identify missing or problematic sections.

This script provides detailed analysis of the TOC extraction process,
helping identify where the extraction may have failed or missed content.

Usage:
    python analyze_toc_diagnostics.py toc_extraction_diagnostics.json

The script will:
1. Analyze batch-by-batch extraction results
2. Identify pages with no extracted content
3. Highlight potential vision analysis issues
4. Compare expected vs actual extraction coverage
"""

import argparse
import json
from pathlib import Path
from progress_utils import print_progress, print_section_header


def analyze_batch_performance(diagnostics_data):
    """
    Analyze the performance of each batch in the extraction process.
    
    Args:
        diagnostics_data (dict): Full diagnostics from TOC extraction
    """
    print_section_header("BATCH-BY-BATCH ANALYSIS")
    
    batch_diags = diagnostics_data.get('batch_diagnostics', [])
    
    for i, batch_diag in enumerate(batch_diags):
        if not batch_diag:
            print_progress(f"Batch {i+1}: NO DIAGNOSTIC DATA")
            continue
            
        batch_num = batch_diag.get('batch_number', i+1)
        pages = batch_diag.get('page_range', 'unknown')
        
        print(f"\n--- Batch {batch_num} (pages {pages}) ---")
        
        # Extraction pipeline status
        extraction_ok = batch_diag.get('extraction_success', False)
        api_ok = batch_diag.get('api_success', False) 
        yaml_ok = batch_diag.get('yaml_parsing_success', False)
        entries_count = batch_diag.get('entries_extracted', 0)
        
        print(f"  PDF Extraction: {'✓' if extraction_ok else '✗'}")
        print(f"  API Call:       {'✓' if api_ok else '✗'}")
        print(f"  YAML Parsing:   {'✓' if yaml_ok else '✗'}")
        print(f"  Entries Found:  {entries_count}")
        
        # Token usage
        raw_len = batch_diag.get('raw_response_length', 0)
        cleaned_len = batch_diag.get('cleaned_response_length', 0)
        max_tokens = batch_diag.get('max_tokens_used', 0)
        
        print(f"  Response Size:  {raw_len} chars (cleaned: {cleaned_len})")
        print(f"  Token Limit:    {max_tokens}")
        
        if raw_len > 0 and max_tokens > 0:
            # Rough estimate of token usage vs limit
            estimated_tokens = raw_len // 3  # Very rough estimate
            usage_pct = (estimated_tokens / max_tokens) * 100 if max_tokens > 0 else 0
            print(f"  Est. Usage:     ~{usage_pct:.1f}% of limit")
        
        # Entry breakdown
        if batch_diag.get('entries_by_type'):
            print(f"  Entry Types:")
            for entry_type, count in batch_diag['entries_by_type'].items():
                print(f"    - {entry_type}: {count}")
        
        # Error details
        if batch_diag.get('error_details'):
            print(f"  ⚠️  ERROR: {batch_diag['error_details']}")
        
        # Detailed entry analysis
        if batch_diag.get('entries_details'):
            print(f"  Detailed Entries:")
            for entry_detail in batch_diag['entries_details'][:3]:  # Show first 3
                title = entry_detail.get('title', 'NO TITLE')[:50]
                page = entry_detail.get('page_start', 'no page')
                subsec_count = entry_detail.get('subsection_count', 0)
                print(f"    - \"{title}\" (p.{page}, {subsec_count} subsections)")
            
            if len(batch_diag['entries_details']) > 3:
                remaining = len(batch_diag['entries_details']) - 3
                print(f"    ... and {remaining} more entries")


def analyze_coverage_gaps(diagnostics_data):
    """
    Analyze coverage gaps in the extraction process.
    """
    print_section_header("COVERAGE ANALYSIS")
    
    merge_diag = diagnostics_data.get('merge_diagnostics', {})
    
    expected_pages = merge_diag.get('expected_pages', [])
    pages_with_entries = merge_diag.get('pages_with_entries', [])
    missing_coverage = merge_diag.get('missing_coverage', [])
    
    print(f"Expected pages to process: {expected_pages}")
    print(f"Pages with extracted entries: {pages_with_entries}")
    
    if missing_coverage:
        print(f"\n⚠️  MISSING COVERAGE:")
        print(f"  Pages with no extracted entries: {missing_coverage}")
        print(f"  This could indicate:")
        print(f"    - Pages contain only continuation text (no new sections)")
        print(f"    - Vision API failed to recognize TOC structure")
        print(f"    - Pages contain non-standard formatting")
    else:
        print(f"✓ All processed pages have extracted entries")
    
    # Batch success analysis
    total_batches = merge_diag.get('total_batches_processed', 0)
    successful_batches = merge_diag.get('successful_batches', 0)
    failed_batches = merge_diag.get('failed_batches', 0)
    
    print(f"\nBatch Success Rate:")
    print(f"  Successful: {successful_batches}/{total_batches}")
    print(f"  Failed: {failed_batches}/{total_batches}")
    
    if failed_batches > 0:
        success_rate = (successful_batches / total_batches) * 100 if total_batches > 0 else 0
        print(f"  Success Rate: {success_rate:.1f}%")
    
    # Merge warnings
    warnings = merge_diag.get('merge_warnings', [])
    if warnings:
        print(f"\n⚠️  MERGE WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")


def analyze_entry_distribution(diagnostics_data):
    """
    Analyze the distribution of extracted entries.
    """
    print_section_header("ENTRY DISTRIBUTION ANALYSIS")
    
    merge_diag = diagnostics_data.get('merge_diagnostics', {})
    entries_by_batch = merge_diag.get('entries_by_batch', {})
    
    print("Entries extracted per batch:")
    total_entries = 0
    
    for batch_num, batch_info in entries_by_batch.items():
        count = batch_info.get('count', 0)
        pages = batch_info.get('pages', [])
        types = batch_info.get('types', {})
        
        total_entries += count
        
        print(f"\n  Batch {batch_num} (pages {pages[0]}-{pages[-1]} if pages else 'unknown'):")
        print(f"    Total entries: {count}")
        
        if types:
            print(f"    By type:")
            for entry_type, type_count in types.items():
                print(f"      - {entry_type}: {type_count}")
        
        # Show some example entries
        details = batch_info.get('details', [])
        if details:
            print(f"    Examples:")
            for detail in details[:2]:  # Show first 2
                title = detail.get('title', 'NO TITLE')[:40]
                entry_type = detail.get('type', 'unknown')
                print(f"      - {entry_type}: \"{title}...\"")
    
    print(f"\nTotal entries extracted: {total_entries}")


def provide_recommendations(diagnostics_data):
    """
    Provide recommendations based on diagnostic analysis.
    """
    print_section_header("RECOMMENDATIONS")
    
    merge_diag = diagnostics_data.get('merge_diagnostics', {})
    batch_diags = diagnostics_data.get('batch_diagnostics', [])
    
    recommendations = []
    
    # Check for failed batches
    failed_batches = merge_diag.get('failed_batches', 0)
    if failed_batches > 0:
        recommendations.append(
            f"🔄 {failed_batches} batches failed completely - consider re-running with single-page processing"
        )
    
    # Check for missing coverage
    missing_coverage = merge_diag.get('missing_coverage', [])
    if missing_coverage:
        recommendations.append(
            f"🔍 Pages {missing_coverage} have no extracted entries - manually verify these pages contain TOC content"
        )
    
    # Check for truncated responses
    for i, batch_diag in enumerate(batch_diags):
        if not batch_diag:
            continue
        
        raw_len = batch_diag.get('raw_response_length', 0)
        max_tokens = batch_diag.get('max_tokens_used', 0)
        
        if raw_len > 0 and max_tokens > 0:
            estimated_tokens = raw_len // 3
            if estimated_tokens > max_tokens * 0.9:  # Using >90% of tokens
                batch_num = batch_diag.get('batch_number', i+1)
                recommendations.append(
                    f"⚠️  Batch {batch_num} may be hitting token limits - consider smaller batches"
                )
    
    # Check YAML parsing issues
    yaml_failures = sum(1 for d in batch_diags if d and not d.get('yaml_parsing_success', False))
    if yaml_failures > 0:
        recommendations.append(
            f"🔧 {yaml_failures} batches had YAML parsing issues - check debug files for malformed output"
        )
    
    if not recommendations:
        recommendations.append("✓ Extraction appears to be working well!")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")


def main():
    """
    Main function for diagnostic analysis script.
    """
    parser = argparse.ArgumentParser(
        description='Analyze TOC extraction diagnostics to identify issues'
    )
    parser.add_argument('diagnostics_file', help='JSON diagnostics file from TOC extraction')
    
    args = parser.parse_args()
    
    if not Path(args.diagnostics_file).exists():
        print(f"ERROR: Diagnostics file not found: {args.diagnostics_file}")
        return 1
    
    try:
        # Load diagnostics data
        with open(args.diagnostics_file, 'r') as f:
            diagnostics_data = json.load(f)
        
        print_section_header("TOC EXTRACTION DIAGNOSTICS ANALYSIS")
        print(f"Diagnostics file: {args.diagnostics_file}")
        print("=" * 60)
        
        # Run analysis
        analyze_batch_performance(diagnostics_data)
        analyze_coverage_gaps(diagnostics_data)
        analyze_entry_distribution(diagnostics_data)
        provide_recommendations(diagnostics_data)
        
        return 0
        
    except Exception as e:
        print_progress(f"- Error analyzing diagnostics: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
# ASCII-Only Coding Standard

## MANDATORY PRACTICE

All code, documentation, and output files in this project MUST use only standard ASCII characters (0-127). This is now a mandatory working practice to ensure maximum compatibility and readability.

## Prohibited Characters

### Emojis and Unicode Symbols
- NO emojis: [OK] [ERROR] [TOOL] [TARGET] [READY] [NOTE] [ANALYZING] [STATS] [SMART] [PROCESS] [CLEAN] [GUIDE] [WARNING] [SAVE] [FILE] [SUCCESS] [NEW] [STAR]
- NO special Unicode symbols: <- -> ^ v 
- NO decorative characters: 

### Replacement Guidelines

#### Status Indicators
- Instead of [OK] use: "PASS", "OK", "SUCCESS", "[OK]" 
- Instead of [ERROR] use: "FAIL", "ERROR", "FAILED", "[ERROR]"
- Instead of [WARNING] use: "WARNING", "WARN", "CAUTION", "[WARN]"
- Instead of [ANALYZING] use: "ANALYZING", "CHECKING", "REVIEWING"

#### Progress and Process
- Instead of [READY] use: "STARTING", "LAUNCHING", "READY"
- Instead of [TARGET] use: "TARGET", "GOAL", "OBJECTIVE"
- Instead of [TOOL] use: "TOOL", "UTILITY", "PROCESSING"
- Instead of [SAVE] use: "SAVING", "EXPORT", "WRITING"

#### Documentation
- Instead of [NOTE] use: "NOTE", "DOCS", "DOCUMENTATION"
- Instead of [GUIDE] use: "GUIDE", "MANUAL", "REFERENCE"
- Instead of [STATS] use: "STATS", "METRICS", "ANALYSIS"
- Instead of [FILE] use: "FILE", "DOCUMENT", "OUTPUT"

#### Lists and Bullets
- Use standard ASCII: `-`, `*`, `+` for bullet points
- Use numbers: `1.`, `2.`, `3.` for ordered lists
- Use `[x]` and `[ ]` for checkboxes

## Enforcement

### Code Files (.py)
- All Python files must contain only ASCII characters
- Comments and docstrings must use ASCII only
- Print statements and error messages must use ASCII only

### Documentation (.md)
- All Markdown files must use ASCII characters only
- Headers, lists, and formatting must use standard ASCII
- Code blocks and examples must use ASCII only

### Output Files
- All generated files must contain ASCII characters only
- Log files, diagnostic files, and reports must use ASCII
- Configuration files must use ASCII only

## Examples

### CORRECT (ASCII-only)
```python
print("Processing complete - analysis successful")
print("WARNING: Content may be incomplete")
print("ERROR: Failed to process batch")

# Status indicators
status = "OK" if success else "FAILED"
print(f"Batch status: {status}")

# Lists in documentation
- Primary processing mode
- Fallback processing mode 
- Diagnostic analysis mode
```

### INCORRECT (Contains non-ASCII)
```python
print("Processing complete [OK] - analysis successful [SUCCESS]")
print("[WARNING] WARNING: Content may be incomplete")
print("[ERROR] ERROR: Failed to process batch")

# Contains emojis
status = "[OK]" if success else "[ERROR]"
print(f"Batch status: {status}")

# Unicode bullets in documentation 
- Primary processing mode
- Fallback processing mode
- Diagnostic analysis mode
```

## Validation

### Pre-commit Checks
Before committing any changes, verify ASCII compliance:

```bash
# Check for non-ASCII characters in Python files
find . -name "*.py" -exec grep -P '[^\x00-\x7F]' {} + || echo "All Python files are ASCII-clean"

# Check for non-ASCII characters in Markdown files 
find . -name "*.md" -exec grep -P '[^\x00-\x7F]' {} + || echo "All Markdown files are ASCII-clean"
```

### Automated Cleaning
Use the provided cleaning script to remove non-ASCII characters:

```bash
python3 clean_emojis.py
```

## Benefits of ASCII-Only

1. **Universal Compatibility**: Works across all systems, terminals, and editors
2. **Version Control**: Clean diffs without encoding issues
3. **Debugging**: Easier to debug without character encoding complications 
4. **Professional Appearance**: Clean, professional look across all platforms
5. **Search and Replace**: Reliable text processing without Unicode complications
6. **Legacy System Support**: Compatible with older systems and tools

## Migration Complete

As of this standard, all files in the codebase have been cleaned to comply with ASCII-only requirements:

### Files Cleaned
- `/CLAUDE.md` - Removed emojis from headers and status indicators
- `/README.md` - Removed emojis from status markers and section headers
- `tools/test_diagnostics.py` - Replaced emoji status indicators with text
- `tools/fix_figure_captions.py` - Cleaned all non-ASCII characters
- `tools/analyze_toc_diagnostics.py` - Removed emoji markers
- `tools/test_subsection_batching.py` - Replaced emoji indicators
- `tools/debug_pdf_images.py` - Cleaned decorative characters
- `tools/fix_math_delimiters.py` - Removed status emojis
- `tools/DIAGNOSTICS_USAGE.md` - Cleaned all documentation emojis

### Tools Available
- `tools/clean_emojis.py` - Automated cleaning script for future use

## Mandatory Compliance

This ASCII-only standard is now MANDATORY for all:
- New code development
- Documentation updates 
- Bug fixes and modifications
- Tool outputs and logging
- Configuration files
- Test files and examples

Any code submission that violates this standard will be rejected until cleaned to ASCII-only compliance.
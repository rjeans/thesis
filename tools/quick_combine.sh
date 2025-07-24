#!/bin/bash
# Quick script to combine markdown files in order
# Usage: ./quick_combine.sh markdown_dir/ output.md

MARKDOWN_DIR=${1:-"markdown_output"}
OUTPUT_FILE=${2:-"complete_thesis.md"}

echo "Combining markdown files from $MARKDOWN_DIR into $OUTPUT_FILE"

# Create output file with title
echo "# PhD Thesis - Complete Document" > "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Add files in logical order
files=(
    "title.md"
    "abstract.md" 
    "acknowledgements.md"
    "notation.md"
    "chapter_1.md"
    "chapter_2.md"
    "chapter_3.md"
    "chapter_4.md"
    "appendix_1.md"
    "appendix_2.md"
    "references.md"
)

for file in "${files[@]}"; do
    filepath="$MARKDOWN_DIR/$file"
    if [[ -f "$filepath" ]]; then
        echo "Adding $file..."
        echo "" >> "$OUTPUT_FILE"
        echo "---" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        cat "$filepath" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
    else
        echo "Skipping $file (not found)"
    fi
done

echo "Complete document saved to: $OUTPUT_FILE"
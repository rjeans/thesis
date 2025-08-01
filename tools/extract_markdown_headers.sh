#!/bin/bash

FILE="$1"

if [[ ! -f "$FILE" ]]; then
  echo "Usage: $0 <markdown_file>"
  exit 1
fi

echo "| Line | Level | Section  | Title                                | Issues |"
echo "|------|-------|----------|----------------------------------------|--------|"

gawk '
BEGIN {
  IGNORECASE = 1
  OFS = " | "
}

function count_dots(str) {
  return gsub(/\./, ".", str)
}

function print_row() {
  printf "| %4d | %5s | %-8s | %-40s | %s|\n", line_num, level, section, title, issues
}

/^#{1,6}[ \t]/ {
  line_num = NR
  line = $0
  match(line, /^#+/, level_match)
  level = length(level_match[0])
  sub(/^#+[ \t]+/, "", line)

  # Extract anchor inline if present
  anchor = ""
  if (match(line, /<a[ \t]+id="([^"]+)"/, m)) {
    anchor = m[1]
    sub(/[ \t]*<a[ \t]+id="[^"]+">[ \t]*<\/a>[ \t]*$/, "", line)
  }

  section = ""
  title = line
  issues = ""

  # Match "Chapter N. Title"
  if (match(line, /^(chapter)[ \t]+([0-9]+)\.[ \t]+(.+)$/, chap)) {
    section = chap[2]
    title = chap[3]
  }
  # Match "N.N" or "N.N.N" section formats
  else if (match(line, /^([0-9]+\.[0-9]+(\.[0-9]+)*)\s+/, sec)) {
    section = sec[1]
    title = substr(line, RLENGTH + 1)
  }

  # Check level correctness
  if (section != "") {
    expected_level = count_dots(section) + 1
    if (level != expected_level) {
      issues = issues "wrong-level (expected " expected_level "); "
    }
  }

  # Check for duplicate section numbers
  if (section != "" && seen[section]++) {
    issues = issues "duplicate; "
  }

  # Check if anchor is missing
  if (anchor == "") {
    issues = issues "missing-anchor; "
  }

  print_row()
}
' "$FILE"

#!/bin/bash

set -e

echo "Publishing podcast to Dropbox..."

INPUT_FILE="data/podcast/voice_memo_mix.mp3"
OUTPUT_DIR="dropbox-output"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file $INPUT_FILE not found"
    exit 1
fi

# Create output directory if it doesn't exist (should already be mounted)
mkdir -p "$OUTPUT_DIR"

# Find the latest file in the output directory
LATEST_FILE=$(find "$OUTPUT_DIR" -maxdepth 1 -name "*.mp3" -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n1 | cut -d' ' -f2-)

# Create file prefix (e.g. "0001-April 30, 2025"), default to "0001" if no files found
PREVIOUS_PREFIX=$(if [ -n "$LATEST_FILE" ]; then basename "$LATEST_FILE" .mp3 | cut -d' ' -f 1; else echo "0000"; fi)
PREVIOUS_PREFIX=$((10#$PREVIOUS_PREFIX)) # force decimal conversion
NEW_PREFIX=$(printf "%04d" $((PREVIOUS_PREFIX + 1)))

# Rename our file to include the prefix and today's date (e.g. "0002-April 31, 2025")
NEW_FILE="$NEW_PREFIX-$(date +"%B %d, %Y").mp3"
echo "Uploading $NEW_FILE"
cp "$INPUT_FILE" "$OUTPUT_DIR/$NEW_FILE"

echo "Podcast published successfully to Dropbox!"

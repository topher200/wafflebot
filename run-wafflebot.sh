#!/bin/bash

set -e

echo "Building Docker images..."
docker compose build

echo "Running file downloader..."
docker compose run --rm file-downloader

echo "Running audio mixer..."
docker compose run --rm audio-mixer

echo "Uploading podcast..."
INPUT_FILE="data/podcast/voice_memo_mix.mp3"
OUTPUT_DIR="/home/topher/Dropbox/Apps/PushPod/Haotic Waffles"

# find the latest file in the output directory
mkdir -p "$OUTPUT_DIR"
LATEST_FILE=$(find "$OUTPUT_DIR" -maxdepth 1 -name "*.mp3" -type f -printf '%T@ %p\n' | sort -nr | head -n1 | cut -d' ' -f2-)

# create file prefix (e.g. "0001-April 30, 2025"), default to "0001" if no files found
PREVIOUS_PREFIX=$(if [ -n "$LATEST_FILE" ]; then basename "$LATEST_FILE" .mp3 | cut -d '-' -f 1; else echo "0000"; fi)
PREVIOUS_PREFIX=$((10#$PREVIOUS_PREFIX))  # Force base-10
NEW_PREFIX=$(printf "%04d" $((PREVIOUS_PREFIX + 1)))

# rename our file to include the prefix and today's date (e.g. "0002-April 31, 2025")
NEW_FILE="$NEW_PREFIX-$(date +"%B %d, %Y").mp3"
echo "Uploading $NEW_FILE"
mv "$INPUT_FILE" "$OUTPUT_DIR/$NEW_FILE"

echo "Cleaning up intermediate volumes..."
docker compose down -v

echo "Done!"

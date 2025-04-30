#!/bin/bash

set -e

echo "Download latest git version..."
git fetch && git checkout origin/master

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
LATEST_FILE=$(ls -t "$OUTPUT_DIR"/*.mp3 | head -n 1)

# get its prefix (e.g. "1-April 30, 2025")
PREFIX=$(basename "$LATEST_FILE" .mp3 | cut -d '-' -f 1)

# rename our file to include that prefix, +1, plus today's date (e.g. "2-April 30, 2025")
NEW_FILE="$PREFIX-$(date +"%B %d, %Y").mp3"
echo "Uploading $NEW_FILE"
mv "$INPUT_FILE" "$OUTPUT_DIR/$NEW_FILE"

echo "Cleaning up intermediate volumes..."
docker compose down -v

echo "Done!"

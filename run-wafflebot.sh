#!/bin/bash

set -e

echo "Building Docker images..."
docker compose build

echo "Running file downloader..."
docker compose run --rm file-downloader

if [ ! -d "data/voice-memos" ]; then
    echo "No voice memos were downloaded. Exiting."
    exit 0
fi

echo "Running audio mixer..."
docker compose run --rm audio-mixer

echo "Uploading podcast..."
OUTPUT_DIR="/home/topher/Dropbox/Apps/PushPod/Haotic Waffles"

# find the latest file in the output directory
LATEST_FILE=$(ls -t "$OUTPUT_DIR"/*.mp3 | head -n 1)

# get its prefix (e.g. "1-April 30, 2025")
PREFIX=$(basename "$LATEST_FILE" .mp3 | cut -d '-' -f 1)

# rename our file to include that prefix, +1, plus today's date
NEW_FILE="$PREFIX-$(date +%d).mp3"
mv "$LATEST_FILE" "$OUTPUT_DIR/$NEW_FILE"

echo "Cleaning up voice memos..."
rm -rf data/voice-memos

echo "Done!"

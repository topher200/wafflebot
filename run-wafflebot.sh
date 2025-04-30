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
chown -R topher:topher data/podcast
cp data/podcast/* "/home/topher/Dropbox/Apps/PushPod/Haotic Waffles"

echo "Cleaning up voice memos..."
rm -rf data/voice-memos
echo "Cleaning up generated podcast..."
rm -rf data/podcast

echo "Done!"

#!/bin/bash

set -e

echo "Building Docker images..."
docker compose build

echo "Running file downloader..."
docker compose run --rm file-downloader

echo "Running audio mixer..."
docker compose run --rm audio-mixer

echo "Publishing podcast to Dropbox..."
docker compose run --rm publish-to-dropbox

echo "Publishing podcast to S3..."
docker compose run --rm publish-podcast-to-s3

echo "Updating RSS feed..."
docker compose run --rm update-rss-feed

echo "Cleaning up intermediate volumes..."
docker compose down -v

echo "Done!"

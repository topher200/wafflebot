#!/bin/bash
set -e

SERVICE_NAME="$1"

if [ -z "$SERVICE_NAME" ]; then
    echo "Error: Service name is required"
    echo "Usage: $0 <service-name>"
    echo "Available services: file-downloader, audio-mixer, publish-to-dropbox, publish-podcast-to-s3, update-rss-feed"
    exit 1
fi

case "$SERVICE_NAME" in
    "file-downloader")
        echo "Starting file-downloader service..."
        exec uv run --no-dev python src/file_downloader/download.py
        ;;
    "audio-mixer")
        echo "Starting audio-mixer service..."
        exec uv run --no-dev python src/mixer/generate_audio.py
        ;;
    "publish-to-dropbox")
        echo "Starting publish-to-dropbox service..."
        exec bash src/publish-podcast-to-dropbox/publish.sh
        ;;
    "publish-podcast-to-s3")
        echo "Starting publish-podcast-to-s3 service..."
        exec bash src/publish-podcast-to-s3/publish.sh
        ;;
    "update-rss-feed")
        echo "Starting update-rss-feed service..."
        exec uv run --no-dev python src/update_rss_feed/generate_rss.py
        ;;
    *)
        echo "Error: Unknown service '$SERVICE_NAME'"
        echo "Available services: file-downloader, audio-mixer, publish-to-dropbox, publish-podcast-to-s3, update-rss-feed"
        exit 1
        ;;
esac

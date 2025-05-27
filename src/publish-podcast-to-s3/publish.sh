#!/bin/bash

set -e

echo "Publishing podcast to S3..."

INPUT_FILE="data/podcast/voice_memo_mix.mp3"

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file $INPUT_FILE not found"
    exit 1
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check if required environment variables are set
if [ -z "$S3_BUCKET_NAME" ]; then
    echo "Error: S3_BUCKET_NAME environment variable not set"
    exit 1
fi

if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "Error: AWS_ACCESS_KEY_ID environment variable not set"
    exit 1
fi

if [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Error: AWS_SECRET_ACCESS_KEY environment variable not set"
    exit 1
fi

# Set AWS region (default to us-east-1 if not specified)
export AWS_DEFAULT_REGION="${AWS_REGION:-us-east-1}"

# Create filename with ISO 8601 timestamp
# Format: YYYY-MM-DDTHHMMSS.mp3 (e.g., "2025-01-15T143022.mp3")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H%M%S")
NEW_FILE="$TIMESTAMP.mp3"
S3_DESTINATION="s3://${S3_BUCKET_NAME}/podcasts/$NEW_FILE"

echo "Uploading $NEW_FILE to S3..."

# Upload the file to S3 using AWS CLI with environment credentials
aws s3 cp "$INPUT_FILE" "$S3_DESTINATION"

echo "Podcast published successfully to S3: $S3_DESTINATION"

# Publish Podcast to S3 Service

This service handles publishing the generated podcast audio file to an AWS S3 bucket with ISO 8601 timestamp naming.

## Purpose

The `publish-podcast-to-s3` service takes the generated podcast audio file from the `audio-mixer` service and uploads it to an S3 bucket with a timestamp-based filename.

## How it Works

1. **Input**: Reads the generated podcast file from the `podcast-audio` Docker volume (mounted as read-only)
2. **Processing**: Generates a filename with ISO 8601 timestamp format: `YYYY-MM-DDTHHMMSS.mp3`
3. **Output**: Uploads the file to the S3 bucket using AWS CLI

## Environment Variables

- `S3_BUCKET_NAME`: The name of the S3 bucket where podcasts will be stored
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region (optional, defaults to us-east-1)

## Docker Integration

The service is configured in `docker-compose.yml` as:

```yaml
publish-podcast-to-s3:
  build:
    context: .
  volumes:
    - podcast-audio:/app/data/podcast:ro # Read-only access to generated audio
  command: bash src/publish-podcast-to-s3/publish.sh
```

## S3 Bucket Structure

Files are uploaded to the S3 bucket with the following structure:

```
s3://your-bucket-name/
└── podcasts/
    ├── 2025-01-15T143022.mp3
    ├── 2025-01-16T091545.mp3
    └── ...
```

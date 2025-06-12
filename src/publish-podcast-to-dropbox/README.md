# Publish Podcast to Dropbox Service

This service handles publishing the generated podcast audio file to a Dropbox folder with proper naming and versioning.

## Purpose

The `publish-to-dropbox` service takes the generated podcast audio file from the `audio-mixer` service and copies it to a Dropbox folder with an incremented filename that includes the current date.

## How it Works

1. **Input**: Reads the generated podcast file from the `podcast-audio` Docker volume (mounted as read-only)
2. **Processing**:
   - Finds existing podcast files in the Dropbox directory
   - Determines the next sequential number NNNN (e.g., 0001, 0002, etc.)
   - Generates a filename with format: `NNNN-Month DD, YYYY.mp3`
3. **Output**: Copies the file to the mounted Dropbox directory

## Usage

The service is automatically called by `run-wafflebot.sh`:

```bash
# Run as part of the full pipeline
./run-wafflebot.sh

# Or run individually
docker compose run --rm publish-to-dropbox
```

## Testing

```bash
# Run all publish tests
uv run pytest src/publish-podcast-to-dropbox/test_publish.py -v
```

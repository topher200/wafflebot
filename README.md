# WaffleBot

WaffleBot is a Discord bot that collects voice memos from a channel, combines
them into a single audio file with intro, outro, and interlude music, and
uploads the result to Dropbox/PushPod.

## Overview

![WaffleBot Architecture](static/wafflebot.excalidraw.png)

- **file-downloader**: Downloads voice memos from Discord
- **audio-mixer**: Combines memos with music into a podcast audio file
- **publish-to-dropbox**: Publishes the podcast audio to Dropbox with versioned naming ([details](src/publish-podcast-to-dropbox/README.md))

## Development

1. **Run unit tests:**

   ```bash
   uv run pytest src/ -v
   ```

2. **Run end-to-end tests:**

   ```bash
   ./run-e2e-tests.sh
   ```

   Or manually:

   ```bash
   uv run pytest tests/e2e/ -v
   ```

   The e2e tests will:
   - Download test audio files from URLs (cached locally)
   - Run the complete audio processing pipeline in Docker
   - Verify that files are correctly processed and published

3. **Run all tests:**

   ```bash
   uv run pytest -v
   ```

## Deployment

WaffleBot can be deployed as a daily automated service using Docker Compose and systemd.

### Prerequisites

- Docker and Docker Compose installed
- systemd (standard on most Linux distributions)
- sudo access for systemd service installation

### Installation

1. **Update the environment variables:**  

   ```bash
   cp .env.example .env
   ```

2. **Install the systemd service and timer:**

   ```bash
   ./install-systemd-scripts.sh
   ```

   This will:
   - Copy the systemd service and timer files to `/etc/systemd/system/`
   - Enable and start the timer
   - Set up daily automated runs overnight

### Manual Control

- **Run manually:**

  ```bash
  docker compose run --build --rm file-downloader
  docker compose run --build --rm audio-mixer
  docker compose run --build --rm publish-to-dropbox
  ```

  or

  ```bash
  ./run-wafflebot.sh
  ```

- **Check service status:**

  ```bash
  systemctl status homelab-run-wafflebot.timer
  ```

- **View logs:**

  ```bash
  journalctl -u homelab-run-wafflebot
  ```

- **Stop the service from running:**

  ```bash
  systemctl stop homelab-run-wafflebot.timer
  ```

## Testing Architecture

The project includes comprehensive end-to-end tests that validate the complete audio processing pipeline:

### Test Structure

```
tests/
├── e2e/                           # End-to-end tests
│   ├── conftest.py               # pytest fixtures
│   ├── test_full_pipeline.py     # main e2e tests
│   ├── fixtures/
│   │   └── test_audio_urls.json  # URLs for test audio files
│   └── utils/
│       ├── audio_downloader.py   # download & cache test audio
│       └── docker_helpers.py     # docker compose test helpers
├── cache/                        # cached test audio files (gitignored)
└── .env.test                     # test environment configuration
```

### Docker Configuration

The project uses Docker Compose override files to avoid duplication:

- `docker-compose.yml` - Base service definitions
- `docker-compose.override.yml` - Production volume mounts (auto-loaded)
- `docker-compose.test.yml` - Test-specific volume mounts

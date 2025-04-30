# WaffleBot

WaffleBot is a Discord bot that collects voice memos from a channel, combines
them into a single audio file with intro, outro, and interlude music, and
uploads the result to Dropbox/PushPod.

## Overview

![WaffleBot Architecture](static/wafflebot.excalidraw.png)

## Development

1. **Run tests:**

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
   - Set up daily automated runs at midnight Eastern Time

### Manual Control

- **Run manually:**

  ```bash
  systemctl start homelab-run-wafflebot
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

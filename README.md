# WaffleBot

WaffleBot is a Discord bot that collects voice memos from a channel, combines them into a single audio file with intro, outro, and interlude music, and prepares it for podcast hosting.

## Setup

1. **Build the Docker image:**

   ```bash
   docker build -t wafflebot .
   ```

2. **Run the Docker container:**

   ```bash
   docker run -it --rm wafflebot
   ```

## Actions

- **Download files from Discord:**

  This action will download audio files from a specified Discord channel.

- **Generate audio file:**

  This action will combine the downloaded audio files into a single audio file with music.

## Requirements

- Docker
- Python 3.9
- `uv` for packaging

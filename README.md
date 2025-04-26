# WaffleBot

WaffleBot is a Discord bot that collects voice memos from a channel, combines
them into a single audio file with intro, outro, and interlude music, and
prepares it for podcast hosting.

## Setup

1. **Build the Docker image:**

   ```bash
   docker build -t wafflebot .
   ```

2. **Run the Docker container for different services:**

   - **Download files from Discord:**

     ```bash
     docker run -it --rm wafflebot python src/file_downloader/main.py
     ```

   - **Generate audio file:**

     ```bash
     docker run -it --rm wafflebot python src/mixer/main.py
     ```

   - **Upload podcast:**

     ```bash
     docker run -it --rm wafflebot python src/podcast_uploader/main.py
     ```
   ```

## Requirements

- Docker
- Python 3.13
- `uv` for packaging

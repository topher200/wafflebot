# syntax=docker/dockerfile:1.4
FROM python:3.13-slim AS base

# Create group and user that match host's UID/GID
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} topher && \
    useradd -u ${USER_ID} -g ${GROUP_ID} -m topher

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y ffmpeg curl unzip && \
    rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip aws/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install uv

USER topher
WORKDIR /app

COPY --chown=topher:topher pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --locked

COPY --chown=topher:topher . .

# Create and set permissions for intermediate directories
RUN mkdir -p /app/data/voice-memos && \
    chown -R topher:topher /app/data/voice-memos
RUN mkdir -p /app/data/podcast && \
    chown -R topher:topher /app/data/podcast
RUN mkdir -p /app/dropbox-output && \
    chown -R topher:topher /app/dropbox-output

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/.venv/lib/python3.13/site-packages:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1

FROM base AS file-downloader
CMD ["uv", "run", "--no-dev", "python", "src/file_downloader/download.py"]

FROM base AS audio-mixer
CMD ["uv", "run", "--no-dev", "python", "src/mixer/generate_audio.py"]

FROM base AS publish-to-dropbox
CMD ["bash", "src/publish-podcast-to-dropbox/publish.sh"]

FROM base AS publish-podcast-to-s3
CMD ["bash", "src/publish-podcast-to-s3/publish.sh"]

FROM base AS update-rss-feed
CMD ["uv", "run", "--no-dev", "python", "src/update_rss_feed/generate_rss.py"]

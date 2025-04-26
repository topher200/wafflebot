# syntax=docker/dockerfile:1.4
FROM python:3.13-slim

WORKDIR /app

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y ffmpeg

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync

COPY . .

CMD ["python", "src/file_downloader/main.py"]

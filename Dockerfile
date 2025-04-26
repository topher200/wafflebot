FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync

COPY . .

CMD ["python", "src/file_downloader/main.py"]

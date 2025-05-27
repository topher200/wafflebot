# syntax=docker/dockerfile:1.4
FROM python:3.13-slim

# Create group and user that match host's UID/GID
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} topher && \
    useradd -u ${USER_ID} -g ${GROUP_ID} -m topher

WORKDIR /app

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    apt-get install -y ffmpeg curl unzip

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip aws/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --locked

COPY . .

# Create and set permissions for intermediate directories
RUN mkdir -p /app/data/voice-memos && \
    chown -R topher:topher /app/data/voice-memos
RUN mkdir -p /app/data/podcast && \
    chown -R topher:topher /app/data/podcast
RUN mkdir -p /app/dropbox-output && \
    chown -R topher:topher /app/dropbox-output

# Set ownership of the entire app directory
RUN chown -R topher:topher /app

# Switch to non-root user
USER topher

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/.venv/lib/python3.13/site-packages:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "src/mixer/generate_audio.py"]

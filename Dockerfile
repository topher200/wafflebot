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

# install uv's python deps
COPY --chown=topher:topher pyproject.toml uv.lock ./
RUN mkdir -p /home/topher/.cache/uv
RUN --mount=type=cache,target=/home/topher/.cache/uv,uid=${USER_ID},gid=${GROUP_ID} \
    uv sync --no-dev --locked

COPY --chown=topher:topher . .

# Create intermediate directories for mounts
RUN mkdir -p /app/data/voice-memos /app/data/podcast /app/data/dropbox-output

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/.venv/lib/python3.13/site-packages:$PYTHONPATH"
ENV PYTHONUNBUFFERED=1

RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]

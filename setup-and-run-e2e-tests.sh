#!/bin/bash

set -e

echo "Setting up E2E test environment..."

# Clean up any existing test containers/volumes
echo "Cleaning up existing test environment..."
docker compose -f docker-compose.yml -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true

# Install dependencies
echo "Installing dependencies..."
uv sync --group dev

# Build Docker images
echo "Building Docker images..."
./build.sh

export DOCKER_UID=$(id -u)
export DOCKER_GID=$(id -g)

# Run the tests
echo "Running E2E tests..."
uv run pytest tests/e2e/ -v

# Clean up after tests
echo "Cleaning up test environment..."
docker compose -f docker-compose.yml -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true

echo "E2E tests completed!"

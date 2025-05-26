#!/bin/bash

set -e

echo "Setting up E2E test environment..."

# Create test environment file if it doesn't exist
if [ ! -f "tests/.env.test" ]; then
    echo "Creating tests/.env.test..."
    cat >tests/.env.test <<EOF
# Test environment configuration
TEST_MODE=true
EOF
fi

# Clean up any existing test containers/volumes
echo "Cleaning up existing test environment..."
docker compose -f docker-compose.yml -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true

# Install dependencies
echo "Installing dependencies..."
uv sync --group dev

# Run the tests
echo "Running E2E tests..."
uv run pytest tests/e2e/ -v

# Clean up after tests
echo "Cleaning up test environment..."
docker compose -f docker-compose.yml -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true

echo "E2E tests completed!"

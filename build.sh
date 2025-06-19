#!/bin/bash
set -euo pipefail

echo "Building base image..."
docker buildx bake wafflebot-base

echo "Building service images..."
docker buildx bake --load all

echo "Build completed successfully!"

echo "Built images:"
docker images --filter "reference=*wafflebot*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

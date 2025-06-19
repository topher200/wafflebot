#!/bin/bash
set -euo pipefail

echo "Building unified wafflebot image..."
docker buildx bake --load wafflebot

echo "Build completed successfully!"

echo "Built images:"
docker images --filter "reference=*wafflebot*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

#!/bin/bash

set -e

# Function to show usage
show_usage() {
    echo "Usage: $0 [staging|prod]"
    echo ""
    echo "Examples:"
    echo "  $0            # Run with default environment (production)"
    echo "  $0 staging    # Run with staging environment configuration"
    echo "  $0 prod       # Run with production environment configuration"
    echo ""
    exit 1
}

# Default to production if no environment specified
ENVIRONMENT="${1:-prod}"

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "prod" ]]; then
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "   Valid environments: staging, prod"
    show_usage
fi

# Environment-specific configuration
ENV_FILE=".env"
if [ "$ENVIRONMENT" = "staging" ]; then
    ENV_FILE=".env.staging"
    echo "🔧 Running WaffleBot in STAGING environment..."
else
    echo "🚀 Running WaffleBot in PRODUCTION environment..."
fi

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Environment file $ENV_FILE not found!"
    if [ "$ENVIRONMENT" = "staging" ]; then
        echo "📝 Please create .env.staging with your staging configuration"
        echo "   You can copy .env as a starting point and modify the S3_BUCKET_NAME"
    else
        echo "📝 Please create .env with your production configuration"
    fi
    exit 1
fi

echo "📁 Using environment file: $ENV_FILE"

# Build Docker images
./build.sh

# Run the pipeline with environment-specific configuration
export COMPOSE_ENV_FILE="$ENV_FILE"

echo "Running file downloader..."
docker compose --env-file "$ENV_FILE" run --rm file-downloader

echo "Running audio mixer..."
docker compose --env-file "$ENV_FILE" run --rm audio-mixer

echo "Publishing podcast to Dropbox..."
docker compose --env-file "$ENV_FILE" run --rm publish-to-dropbox

# echo "Publishing podcast to S3..."
# docker compose --env-file "$ENV_FILE" run --rm publish-podcast-to-s3

# echo "Updating RSS feed..."
# docker compose --env-file "$ENV_FILE" run --rm update-rss-feed

echo "Cleaning up intermediate volumes..."
docker compose --env-file "$ENV_FILE" down -v

echo "✅ WaffleBot pipeline completed successfully in $ENVIRONMENT environment!"

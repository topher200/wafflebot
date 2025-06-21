#!/bin/bash

set -ex

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

# Check if environment-specific files exist
if [ "$ENVIRONMENT" = "staging" ]; then
    echo "🔧 Running WaffleBot in STAGING environment..."

    if [ ! -f ".env.staging" ]; then
        echo "❌ Environment file .env.staging not found!"
        echo "   Please create .env.staging with your configuration; copy .env.example as a starting point"
        exit 1
    fi
    echo "📁 Using environment file: .env.staging"

    if [ ! -f ".env.aws.staging" ]; then
        echo "❌ AWS environment file .env.aws.staging not found!"
        echo "   Please create .env.aws.staging with your AWS credentials"
        echo "   You can use aws-vault to generate temporary credentials"
        echo "   aws-vault exec <your-profile> -- env | grep AWS_ > .env.aws.staging"
        exit 1
    fi
    echo "📁 Using AWS environment file: .env.aws.staging"
else
    echo "🚀 Running WaffleBot in PRODUCTION environment..."

    if [ ! -f ".env" ]; then
        echo "❌ Environment file .env not found!"
        echo "   Please create .env with your configuration; copy .env.example as a starting point"
        exit 1
    fi
    echo "📁 Using environment file: .env"

    if [ ! -f ".env.aws" ]; then
        echo "❌ AWS environment file .env.aws not found!"
        echo "   Please create .env.aws with your AWS credentials"
        echo "   You can use aws-vault to generate temporary credentials"
        echo "   aws-vault exec <your-profile> -- env | grep AWS_ > .env.aws"
        exit 1
    fi
    echo "📁 Using AWS environment file: .env.aws"
fi

# Build Docker images
./build.sh

# Set up Docker Compose file arguments based on environment.
# We export environment variables for substitution in docker-compose.yml files.
if [ "$ENVIRONMENT" = "staging" ]; then
    COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.volumes.yml -f docker-compose.staging.yml)
    set -a
    source .env.staging
    set +a
else
    COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.volumes.yml -f docker-compose.prod.yml)
    set -a
    source .env
    set +a
fi

echo "Running file downloader..."
docker compose "${COMPOSE_FILES[@]}" run --rm file-downloader

echo "Running audio mixer..."
docker compose "${COMPOSE_FILES[@]}" run --rm audio-mixer

echo "Publishing podcast to Dropbox..."
docker compose "${COMPOSE_FILES[@]}" run --rm publish-to-dropbox

echo "Publishing podcast to S3..."
docker compose "${COMPOSE_FILES[@]}" run --rm publish-podcast-to-s3

# echo "Updating RSS feed..."
# docker compose "${COMPOSE_FILES[@]}" run --rm update-rss-feed

echo "Cleaning up intermediate volumes..."
docker compose "${COMPOSE_FILES[@]}" down -v

echo "✅ WaffleBot pipeline completed successfully in $ENVIRONMENT environment!"

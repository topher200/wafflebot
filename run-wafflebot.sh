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

# Environment-specific configuration
ENV_FILE=".env"
AWS_ENV_FILE=".env.aws"
if [ "$ENVIRONMENT" = "staging" ]; then
    ENV_FILE=".env.staging"
    AWS_ENV_FILE=".env.aws.staging"
    echo "🔧 Running WaffleBot in STAGING environment..."
else
    echo "🚀 Running WaffleBot in PRODUCTION environment..."
fi

# Check if environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Environment file $ENV_FILE not found!"
    echo "   Please create $ENV_FILE with your configuration; copy .env.example as a starting point"
    exit 1
fi
echo "📁 Using environment file: $ENV_FILE"

if [ ! -f "$AWS_ENV_FILE" ]; then
    echo "❌ AWS environment file $AWS_ENV_FILE not found!"
    echo "   Please create $AWS_ENV_FILE with your AWS credentials"
    echo "   You can use aws-vault to generate temporary credentials"
    echo "   aws-vault exec <your-profile> -- env | grep AWS_ > $AWS_ENV_FILE"
    exit 1
fi
echo "📁 Using AWS environment file: $AWS_ENV_FILE"

# Build Docker images
./build.sh

# Run the pipeline with environment-specific configuration
export COMPOSE_ENV_FILE="$ENV_FILE"
export COMPOSE_AWS_ENV_FILE="$AWS_ENV_FILE"

echo "Running file downloader..."
docker compose run --rm file-downloader

echo "Running audio mixer..."
docker compose run --rm audio-mixer

echo "Publishing podcast to Dropbox..."
docker compose run --rm publish-to-dropbox

echo "Publishing podcast to S3..."
docker compose run --rm publish-podcast-to-s3

# echo "Updating RSS feed..."
# docker compose run --rm update-rss-feed

echo "Cleaning up intermediate volumes..."
docker compose down -v

echo "✅ WaffleBot pipeline completed successfully in $ENVIRONMENT environment!"

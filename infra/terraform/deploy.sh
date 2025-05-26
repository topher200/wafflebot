#!/bin/bash

# Podcast Infrastructure Deployment Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to show usage
show_usage() {
    echo "Usage: $0 [staging|prod]"
    echo ""
    echo "Examples:"
    echo "  $0 staging    # Deploy to staging environment"
    echo "  $0 prod       # Deploy to production environment"
    echo ""
    exit 1
}

# Check if environment argument is provided
if [ $# -eq 0 ]; then
    echo "❌ No environment specified!"
    show_usage
fi

ENVIRONMENT="$1"
TFVARS_FILE="$SCRIPT_DIR/environments/${ENVIRONMENT}.tfvars"

# Validate environment
if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "prod" ]]; then
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "   Valid environments: staging, prod"
    show_usage
fi

echo "🎙️  Deploying Podcast Infrastructure - ${ENVIRONMENT^^} Environment..."

# Check if environment tfvars file exists
if [ ! -f "$TFVARS_FILE" ]; then
    echo "❌ $TFVARS_FILE not found!"
    echo "📝 Please create the $ENVIRONMENT environment file with your values"
    exit 1
fi

echo "🔧 Initializing Terraform for ${ENVIRONMENT}..."
terraform -chdir="$SCRIPT_DIR" init

echo "🏗️  Selecting/creating ${ENVIRONMENT} workspace..."
terraform -chdir="$SCRIPT_DIR" workspace select ${ENVIRONMENT} 2>/dev/null || terraform -chdir="$SCRIPT_DIR" workspace new ${ENVIRONMENT}

echo ""
# Add extra warning for production
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "⚠️  WARNING: You are about to deploy to PRODUCTION!"
    echo ""
fi

echo "🚀 Deploying ${ENVIRONMENT}..."
terraform -chdir="$SCRIPT_DIR" apply -var-file="$TFVARS_FILE"

echo ""
echo "✅ ${ENVIRONMENT^^} deployment complete!"
echo "⏰ Note: CloudFront deployment can take 10-20 minutes to fully propagate"

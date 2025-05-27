#!/bin/bash

# Podcast Infrastructure Deployment Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../podcast"

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
TFVARS_FILE="$TERRAFORM_DIR/${ENVIRONMENT}.tfvars"

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

echo "🔧 Initializing Terraform..."
terraform -chdir="$TERRAFORM_DIR" init

echo "🏗️  Selecting/creating podcast-${ENVIRONMENT} workspace..."
terraform -chdir="$TERRAFORM_DIR" workspace select podcast-${ENVIRONMENT} 2>/dev/null || terraform -chdir="$TERRAFORM_DIR" workspace new podcast-${ENVIRONMENT}

echo ""
# Add extra warning for production
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "⚠️  WARNING: You are about to deploy to PRODUCTION!"
    echo ""
fi

echo "🚀 Deploying podcast ${ENVIRONMENT}..."
terraform -chdir="$TERRAFORM_DIR" apply -var-file="$TFVARS_FILE"

echo ""
echo "✅ Podcast ${ENVIRONMENT^^} deployment complete!"
echo "⏰ Note: CloudFront deployment can take 10-20 minutes to fully propagate"

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
terraform init "$SCRIPT_DIR"

echo "🏗️  Selecting/creating ${ENVIRONMENT} workspace..."
terraform workspace select ${ENVIRONMENT} 2>/dev/null || terraform workspace new ${ENVIRONMENT}

echo "📋 Planning ${ENVIRONMENT} deployment..."
terraform plan -var-file="$TFVARS_FILE"

echo ""
# Add extra warning for production
if [ "$ENVIRONMENT" = "prod" ]; then
    echo "⚠️  WARNING: You are about to deploy to PRODUCTION!"
    echo ""
fi

read -p "🚀 Deploy ${ENVIRONMENT} infrastructure? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Deploying ${ENVIRONMENT}..."
    terraform apply -var-file="$TFVARS_FILE"

    echo ""
    echo "✅ ${ENVIRONMENT^^} deployment complete!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Upload your RSS feed: aws s3 cp rss s3://\$(terraform output -raw s3_bucket_name)/rss"
    echo "2. Upload audio files: aws s3 cp episode1.mp3 s3://\$(terraform output -raw s3_bucket_name)/episode1.mp3"
    echo "3. Your ${ENVIRONMENT} podcast will be available at: \$(terraform output -raw custom_domain_url)"
    echo ""
    echo "⏰ Note: CloudFront deployment can take 10-20 minutes to fully propagate"
else
    echo "❌ ${ENVIRONMENT} deployment cancelled"
fi

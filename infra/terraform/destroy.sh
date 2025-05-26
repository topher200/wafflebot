#!/bin/bash

# Infrastructure Destruction Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to show usage
show_usage() {
    echo "Usage: $0 [staging|prod]"
    echo ""
    echo "Examples:"
    echo "  $0 staging    # Destroy staging environment"
    echo "  $0 prod       # Destroy production environment"
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

echo "💥 Destroying Podcast Infrastructure - ${ENVIRONMENT^^} Environment..."

# Check if environment tfvars file exists
if [ ! -f "$TFVARS_FILE" ]; then
    echo "❌ $TFVARS_FILE not found!"
    echo "📝 Cannot destroy without environment configuration"
    exit 1
fi

echo "🔧 Initializing Terraform for ${ENVIRONMENT}..."
terraform -chdir="$SCRIPT_DIR" init

echo "🏗️  Selecting ${ENVIRONMENT} workspace..."
terraform -chdir="$SCRIPT_DIR" workspace select ${ENVIRONMENT} 2>/dev/null || {
    echo "❌ Workspace ${ENVIRONMENT} does not exist!"
    exit 1
}

echo "📋 Planning ${ENVIRONMENT} destruction..."
terraform -chdir="$SCRIPT_DIR" plan -destroy -var-file="$TFVARS_FILE"

echo ""
echo "⚠️  WARNING: This will PERMANENTLY DELETE all ${ENVIRONMENT^^} infrastructure!"
echo "   - S3 bucket and all files"
echo "   - CloudFront distribution"
echo "   - SSL certificate"
echo "   - DNS records"
echo ""
read -p "💥 Are you SURE you want to destroy ${ENVIRONMENT}? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "💥 Destroying ${ENVIRONMENT}..."
    terraform -chdir="$SCRIPT_DIR" destroy -var-file="$TFVARS_FILE"

    echo ""
    echo "✅ ${ENVIRONMENT^^} infrastructure destroyed!"
else
    echo "❌ ${ENVIRONMENT} destruction cancelled"
fi

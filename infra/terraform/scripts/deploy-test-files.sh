#!/bin/bash

# Test Files Infrastructure Deployment Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../test-files"

TFVARS_FILE="$TERRAFORM_DIR/main.tfvars"

echo "🧪 Deploying Test Files Infrastructure..."

# Check if environment tfvars file exists
if [ ! -f "$TFVARS_FILE" ]; then
    echo "❌ $TFVARS_FILE not found!"
    echo "📝 Please create the test-files environment file with your values"
    exit 1
fi

echo "🔧 Initializing Terraform..."
terraform -chdir="$TERRAFORM_DIR" init

echo "🏗️  Selecting/creating test-files workspace..."
terraform -chdir="$TERRAFORM_DIR" workspace select test-files 2>/dev/null || terraform -chdir="$TERRAFORM_DIR" workspace new test-files

echo ""
echo "🚀 Deploying test files infrastructure..."
terraform -chdir="$TERRAFORM_DIR" apply -var-file="$TFVARS_FILE"

echo ""
echo "✅ Test Files deployment complete!"
echo "📁 Your public S3 bucket is ready for test files"

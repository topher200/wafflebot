#!/bin/bash

# Multi-Environment Infrastructure Status Script

set -e

# Function to show usage
show_usage() {
    echo "Usage: $0 [staging|prod|all]"
    echo ""
    echo "Examples:"
    echo "  $0 staging    # Show staging environment status"
    echo "  $0 prod       # Show production environment status"
    echo "  $0 all        # Show all environments status"
    echo ""
    exit 1
}

# Function to show environment status
show_env_status() {
    local env="$1"
    local tfvars_file="environments/${env}.tfvars"

    echo "📊 ${env^^} Environment Status:"
    echo "================================"

    if [ ! -f "$tfvars_file" ]; then
        echo "❌ Configuration file not found: $tfvars_file"
        echo ""
        return
    fi

    # Check if workspace exists
    if terraform workspace list | grep -q "^\*\?\s*${env}$"; then
        terraform workspace select ${env} >/dev/null 2>&1

        echo "✅ Workspace: ${env}"
        echo "📁 Config file: ${tfvars_file}"

        # Show key outputs if they exist
        if terraform output >/dev/null 2>&1; then
            echo "🌐 Domain: $(terraform output -raw custom_domain_url 2>/dev/null || echo 'Not deployed')"
            echo "🪣 S3 Bucket: $(terraform output -raw s3_bucket_name 2>/dev/null || echo 'Not deployed')"
            echo "☁️  CloudFront: $(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo 'Not deployed')"
        else
            echo "⚠️  Status: Not deployed or no outputs available"
        fi
    else
        echo "❌ Workspace '${env}' does not exist"
        echo "📁 Config file: ${tfvars_file}"
        echo "⚠️  Status: Not deployed"
    fi

    echo ""
}

# Check if environment argument is provided
if [ $# -eq 0 ]; then
    echo "❌ No environment specified!"
    show_usage
fi

ENVIRONMENT="$1"

echo "🔧 Initializing Terraform..."
terraform init >/dev/null

if [ "$ENVIRONMENT" = "all" ]; then
    show_env_status "staging"
    show_env_status "prod"
elif [[ "$ENVIRONMENT" = "staging" || "$ENVIRONMENT" = "prod" ]]; then
    show_env_status "$ENVIRONMENT"
else
    echo "❌ Invalid environment: $ENVIRONMENT"
    echo "   Valid options: staging, prod, all"
    show_usage
fi

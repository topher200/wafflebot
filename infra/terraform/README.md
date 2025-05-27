# WaffleBot Infrastructure

This directory contains the Terraform infrastructure for WaffleBot, organized into separate root modules for clean isolation.

## Architecture

The infrastructure uses a **split root architecture** with separate Terraform roots for each environment:

1. **Podcast Root** (`podcast/`) - Deploys podcast infrastructure using the podcast module
2. **Test Files Root** (`test-files/`) - Deploys test files infrastructure using the test-files module

Each root calls its respective module from the shared `modules/` directory, ensuring code reuse while maintaining environment isolation.

## Directory Structure

```
infra/terraform/
├── modules/                        # Reusable Terraform modules
│   ├── podcast/                    # Podcast infrastructure module
│   │   ├── main.tf                 # AWS caller identity
│   │   ├── variables.tf            # Module variables
│   │   ├── outputs.tf              # Module outputs
│   │   ├── s3.tf                   # S3 bucket configuration
│   │   ├── cloudfront.tf           # CloudFront distribution
│   │   ├── acm.tf                  # SSL certificate
│   │   └── dns.tf                  # Route53 DNS records
│   └── test-files/                 # Test files module
│       ├── main.tf                 # AWS caller identity
│       ├── variables.tf            # Module variables
│       ├── outputs.tf              # Module outputs
│       └── s3.tf                   # Public S3 bucket
├── podcast/                        # Podcast deployment root
│   ├── main.tf                     # Calls ../modules/podcast
│   ├── variables.tf                # Root variables
│   ├── outputs.tf                  # Root outputs
│   ├── provider.tf                 # AWS providers (including us-east-1)
│   ├── staging.tfvars              # Staging config (gitignored)
│   ├── prod.tfvars                 # Production config (gitignored)
│   └── podcast.tfvars.example      # Config template
├── test-files/                     # Test files deployment root
│   ├── main.tf                     # Calls ../modules/test-files
│   ├── variables.tf                # Root variables
│   ├── outputs.tf                  # Root outputs
│   ├── provider.tf                 # AWS provider
│   ├── test-files.tfvars           # Config (gitignored)
│   └── test-files.tfvars.example   # Config template
├── scripts/                        # Deployment scripts
│   ├── deploy-podcast.sh           # Deploy podcast (staging/prod)
│   ├── deploy-test-files.sh        # Deploy test files
│   └── deploy-all.sh               # Deploy everything
```

## Setup

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform installed (version 1.0+)
3. `aws-vault` for secure credential management (recommended)

### Environment Configuration

Each deployment root has its own configuration files:

#### 1. Create Podcast Environment Files

```bash
# Copy example file to create your configurations
cp podcast/podcast.tfvars.example podcast/staging.tfvars
cp podcast/podcast.tfvars.example podcast/prod.tfvars

# Edit with your actual values
vim podcast/staging.tfvars
vim podcast/prod.tfvars
```

#### 2. Create Test Files Environment File

```bash
# Copy example file to create your configuration
cp test-files/test-files.tfvars.example test-files/test-files.tfvars

# Edit with your actual values
vim test-files/test-files.tfvars
```

#### 3. Required Values

You'll need to provide:

- **S3 bucket names**: Must be globally unique
- **Domain names**: Your actual domain names (podcast only)
- **Route53 zone ID**: Found in AWS Console under Route53 > Hosted zones (podcast only)

**Note**: The `.tfvars` files are gitignored to keep your configuration private.

## Deployment

### Deploy Podcast Infrastructure

```bash
# Deploy to staging
./scripts/deploy-podcast.sh staging

# Deploy to production
./scripts/deploy-podcast.sh prod
```

### Deploy Test Files Infrastructure

```bash
# Deploy test files bucket
./scripts/deploy-test-files.sh
```

### Deploy Everything

```bash
# Deploy all infrastructure
./scripts/deploy-all.sh
```

## Modules

### Podcast Module

**Purpose**: Complete podcast hosting infrastructure with custom domain and CDN.

**Resources**:

- Private S3 bucket for podcast files
- CloudFront distribution with custom domain
- ACM SSL certificate
- Route53 DNS records
- Origin Access Control (OAC) for security

**Environments**: `staging`, `prod`

**Workspaces**: `podcast-staging`, `podcast-prod`

### Test Files Module

**Purpose**: Simple public S3 bucket for hosting test files.

**Resources**:

- Public S3 bucket with read access
- Bucket versioning enabled
- Public access policy

**Environments**: Single shared environment

**Workspaces**: `test-files`

## Workspaces

Each deployment root uses Terraform workspaces for environment isolation:

- **Podcast root**: `podcast-staging`, `podcast-prod`
- **Test files root**: `test-files`

## Outputs

### Podcast Outputs

- `s3_bucket_name` - S3 bucket name
- `cloudfront_distribution_id` - CloudFront distribution ID
- `custom_domain_url` - Custom domain URL

### Test Files Outputs

- `bucket_name` - S3 bucket name
- `bucket_domain_name` - S3 bucket domain
- `bucket_regional_domain_name` - Regional S3 domain

## Security

- **Podcast S3 bucket**: Completely private, only accessible via CloudFront
- **Test files S3 bucket**: Public read access for test file hosting
- **SSL/TLS**: Enforced with minimum TLS 1.2
- **Access Control**: Origin Access Control (OAC) for CloudFront → S3

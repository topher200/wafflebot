# Podcast Infrastructure

This Terraform configuration creates a secure podcast hosting infrastructure on AWS with:

- **Private S3 bucket** for storing podcast files and RSS feed
- **CloudFront CDN** for fast, global content delivery
- **Custom domain** with HTTPS via ACM certificate
- **Origin Access Control (OAC)** to block direct S3 access
- **Route53 DNS** configuration
- **Multi-environment support** (staging and production)

## Architecture

```
Internet → podcast.yourdomain.com → CloudFront → Private S3 Bucket
```

- ✅ `https://podcast.yourdomain.com/rss` - Works
- ✅ `https://podcast.yourdomain.com/episode1.mp3` - Works  
- ❌ `https://bucket.s3.amazonaws.com/episode1.mp3` - Blocked

## Prerequisites

1. **AWS CLI configured** with appropriate credentials
2. **Terraform installed** (>= 1.0)
3. **Domain registered** and hosted zone in Route53
4. **Route53 hosted zone ID** for your domain

## Environment Configuration

The infrastructure uses environment-specific configuration files that you create from the example:

### Setup Environment Files

1. **Create environment configurations from the example:**
   ```bash
   # Copy the example to create your environment files
   cp terraform.tfvars.example environments/staging.tfvars
   cp terraform.tfvars.example environments/prod.tfvars
   ```

2. **Edit each file with environment-specific values:**

**Staging** (`environments/staging.tfvars`):
```hcl
bucket_name = "my-podcast-staging"
domain_name = "staging-podcast.mydomain.com"
route53_zone_id = "Z1234567890ABC"
environment = "staging"
```

**Production** (`environments/prod.tfvars`):
```hcl
bucket_name = "my-podcast-prod"
domain_name = "podcast.mydomain.com"
route53_zone_id = "Z1234567890ABC"
environment = "prod"
```

**Note:** The environment files (`environments/*.tfvars`) are gitignored to keep your credentials safe.

## Deployment

### Deploy to Staging
```bash
./deploy.sh staging
```

### Deploy to Production
```bash
./deploy.sh prod
```

### Check Environment Status
```bash
./status.sh staging    # Check staging
./status.sh prod       # Check production
./status.sh all        # Check both environments
```

### Destroy Environment
```bash
./destroy.sh staging   # Destroy staging
./destroy.sh prod      # Destroy production
```

## Manual Deployment Steps

If you prefer manual control:

1. **Initialize Terraform:**
   ```bash
   terraform init
   ```

2. **Select environment workspace:**
   ```bash
   terraform workspace select staging
   # or
   terraform workspace new staging
   ```

3. **Plan deployment:**
   ```bash
   terraform plan -var-file="environments/staging.tfvars"
   ```

4. **Apply configuration:**
   ```bash
   terraform apply -var-file="environments/staging.tfvars"
   ```

## Deployment Process

The deployment will:
1. Create the S3 bucket with private access
2. Create ACM certificate and validate via DNS
3. Create CloudFront distribution with OAC
4. Set up Route53 DNS records
5. Configure S3 bucket policy to allow only CloudFront

**Note:** Certificate validation and CloudFront deployment can take 10-20 minutes.

## Usage

After deployment:

1. **Upload your files to S3:**
   ```bash
   # Get bucket name from Terraform output
   BUCKET=$(terraform output -raw s3_bucket_name)
   
   # Upload files
   aws s3 cp rss s3://$BUCKET/rss
   aws s3 cp episode1.mp3 s3://$BUCKET/episode1.mp3
   ```

2. **Your RSS feed should reference your custom domain:**
   ```xml
   <enclosure url="https://podcast.yourdomain.com/episode1.mp3" type="audio/mpeg" length="12345678"/>
   ```

3. **Test access:**
   - ✅ `https://podcast.yourdomain.com/rss`
   - ✅ `https://podcast.yourdomain.com/episode1.mp3`

## Environment Separation

| Aspect | Staging | Production |
|--------|---------|------------|
| **Domain** | `staging-podcast.domain.com` | `podcast.domain.com` |
| **S3 Bucket** | `project-staging` | `project-prod` |
| **Terraform Workspace** | `staging` | `prod` |
| **State File** | Separate | Separate |
| **Resources** | Isolated | Isolated |

## Outputs

After deployment, Terraform will output:
- S3 bucket name and ARN
- CloudFront distribution ID
- Custom domain URL
- RSS feed URL

## Cache Behavior

- **RSS feed** (`rss*`): 5 minutes cache (for quick updates)
- **Audio files** (`*.mp3`): 1 week cache (for bandwidth efficiency)
- **Other files**: 1 day cache

## Security Features

- ✅ S3 bucket is completely private
- ✅ Only CloudFront can access S3 (via OAC)
- ✅ HTTPS enforced via CloudFront
- ✅ TLS 1.2+ minimum
- ✅ Server-side encryption enabled
- ✅ Environment isolation

## Workflow Examples

### Typical Development Workflow

1. **Test changes in staging:**
   ```bash
   ./deploy.sh staging
   # Test your changes at staging-podcast.domain.com
   ```

2. **Deploy to production:**
   ```bash
   ./deploy.sh prod
   # Go live at podcast.domain.com
   ```

### Check what's deployed:
```bash
./status.sh all
```

## Cleanup

To destroy an environment:
```bash
./destroy.sh staging  # Remove staging
./destroy.sh prod     # Remove production
```

## Troubleshooting

**Certificate validation stuck?**

- Check that your domain's nameservers point to Route53
- Verify the hosted zone ID is correct

**CloudFront not serving files?**

- Wait 10-15 minutes for distribution to deploy
- Check S3 bucket policy was applied correctly

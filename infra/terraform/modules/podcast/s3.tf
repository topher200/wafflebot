# S3 bucket for podcast files
resource "aws_s3_bucket" "podcast" {
  bucket        = var.bucket_name
  force_destroy = true

  tags = {
    Name        = "${var.project_name}-${var.environment}-bucket"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Block all public access to the S3 bucket
resource "aws_s3_bucket_public_access_block" "podcast" {
  bucket = aws_s3_bucket.podcast.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "podcast" {
  bucket = aws_s3_bucket.podcast.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "podcast" {
  bucket = aws_s3_bucket.podcast.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}


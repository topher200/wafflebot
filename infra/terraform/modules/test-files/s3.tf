resource "aws_s3_bucket" "test_files" {
  bucket = var.bucket_name

  tags = {
    Name        = var.bucket_name
    Project     = var.project_name
    Environment = "shared"
    Purpose     = "public-test-files"
  }
}

resource "aws_s3_bucket_public_access_block" "test_files" {
  bucket = aws_s3_bucket.test_files.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "test_files_public_read" {
  bucket = aws_s3_bucket.test_files.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.test_files.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.test_files]
}

resource "aws_s3_bucket_versioning" "test_files" {
  bucket = aws_s3_bucket.test_files.id
  versioning_configuration {
    status = "Enabled"
  }
} 

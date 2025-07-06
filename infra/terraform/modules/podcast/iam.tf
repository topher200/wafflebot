# IAM user for podcast generation
resource "aws_iam_user" "podcast" {
  name = "${var.project_name}-${var.environment}-podcast-generator"

  tags = {
    Name        = "${var.project_name}-${var.environment}-podcast-generator-user"
    Environment = var.environment
    Project     = var.project_name
  }
}

# IAM policy for S3 write access
resource "aws_iam_policy" "podcast" {
  name        = "${var.project_name}-${var.environment}-podcast-generator"
  description = "Policy for writing to the podcast S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:GetObject",
          "s3:GetObjectAcl",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.podcast.arn,
          "${aws_s3_bucket.podcast.arn}/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-podcast-generator-policy"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Attach the policy directly to the user
resource "aws_iam_user_policy_attachment" "podcast" {
  user       = aws_iam_user.podcast.name
  policy_arn = aws_iam_policy.podcast.arn
}

# Create access keys for the user.
# WARNING: This will store the secret key in terraform state
resource "aws_iam_access_key" "podcast" {
  user = aws_iam_user.podcast.name
}

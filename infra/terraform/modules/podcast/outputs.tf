output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.podcast.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.podcast.arn
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.podcast.id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.podcast.domain_name
}

output "custom_domain_url" {
  description = "Custom domain URL for the podcast"
  value       = "https://${var.domain_name}"
}

output "acm_certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = aws_acm_certificate.podcast.arn
}

output "iam_user_arn" {
  description = "ARN of the IAM user for podcast generation"
  value       = aws_iam_user.podcast.arn
}

output "iam_user_name" {
  description = "Name of the IAM user for podcast generation"
  value       = aws_iam_user.podcast.name
}

output "iam_access_key_id" {
  description = "Access key ID for the IAM user"
  value       = aws_iam_access_key.podcast.id
}

output "iam_secret_access_key" {
  description = "Secret access key for the IAM user"
  value       = aws_iam_access_key.podcast.secret
  sensitive   = true
}

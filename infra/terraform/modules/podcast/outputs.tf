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

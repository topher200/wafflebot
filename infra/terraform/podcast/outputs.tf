output "s3_bucket_name" {
  description = "Name of the podcast S3 bucket"
  value       = module.podcast.s3_bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the podcast S3 bucket"
  value       = module.podcast.s3_bucket_arn
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.podcast.cloudfront_distribution_id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.podcast.cloudfront_domain_name
}

output "custom_domain_url" {
  description = "Custom domain URL for the podcast"
  value       = module.podcast.custom_domain_url
}

output "acm_certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = module.podcast.acm_certificate_arn
}

output "iam_user_arn" {
  description = "ARN of the IAM user for podcast generation"
  value       = module.podcast.iam_user_arn
}

output "iam_user_name" {
  description = "Name of the IAM user for podcast generation"
  value       = module.podcast.iam_user_name
}

output "iam_access_key_id" {
  description = "Access key ID for the IAM user"
  value       = module.podcast.iam_access_key_id
}

output "iam_secret_access_key" {
  description = "Secret access key for the IAM user"
  value       = module.podcast.iam_secret_access_key
  sensitive   = true
}

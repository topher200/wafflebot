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

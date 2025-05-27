output "bucket_name" {
  description = "Name of the test files S3 bucket"
  value       = module.test_files.bucket_name
}

output "bucket_arn" {
  description = "ARN of the test files S3 bucket"
  value       = module.test_files.bucket_arn
}

output "bucket_domain_name" {
  description = "Domain name of the test files S3 bucket"
  value       = module.test_files.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "Regional domain name of the test files S3 bucket"
  value       = module.test_files.bucket_regional_domain_name
}

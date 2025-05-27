variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "test_files_bucket_name" {
  description = "The name of the S3 bucket for test files"
  type        = string
}

variable "test_files_project_name" {
  description = "Name of the test files project for resource tagging"
  type        = string
  default     = "wafflebot-test-files"
}

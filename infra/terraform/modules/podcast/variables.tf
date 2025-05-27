variable "aws_region" {
  description = "AWS region for resources"
  type        = string
}

variable "bucket_name" {
  description = "The name of the S3 bucket for podcast files"
  type        = string
}

variable "domain_name" {
  description = "The custom domain name for the podcast"
  type        = string
}

variable "route53_zone_id" {
  description = "The Route53 hosted zone ID for the domain"
  type        = string
}

variable "environment" {
  description = "Environment name (e.g., prod, staging)"
  type        = string
}

variable "project_name" {
  description = "Name of the project for resource tagging"
  type        = string
  default     = "podcast"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "podcast_bucket_name" {
  description = "The name of the S3 bucket for podcast files"
  type        = string
  default     = ""
}

variable "podcast_domain_name" {
  description = "The custom domain name for the podcast"
  type        = string
  default     = ""
}

variable "podcast_route53_zone_id" {
  description = "The Route53 hosted zone ID for the domain"
  type        = string
  default     = ""
}

variable "podcast_environment" {
  description = "Environment name for podcast (e.g., prod, staging)"
  type        = string
  default     = ""
}

variable "podcast_project_name" {
  description = "Name of the podcast project for resource tagging"
  type        = string
  default     = "waffles-podcast"
}

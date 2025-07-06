# Root Terraform for Podcast Infrastructure

module "podcast" {
  source = "../modules/podcast"

  aws_region      = var.aws_region
  bucket_name     = var.podcast_bucket_name
  domain_name     = var.podcast_domain_name
  route53_zone_id = var.podcast_route53_zone_id
  environment     = var.podcast_environment
  project_name    = var.podcast_project_name
}

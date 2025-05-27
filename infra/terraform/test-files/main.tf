# Root Terraform for Test Files Infrastructure
# Get current AWS account ID
data "aws_caller_identity" "current" {}

module "test_files" {
  source = "../modules/test-files"

  aws_region   = var.aws_region
  bucket_name  = var.test_files_bucket_name
  project_name = var.test_files_project_name
}

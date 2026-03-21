terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      CreatedBy   = "Aasrith"
      Environment = "Dev"
      Purpose     = "POC"
      Project     = "Codepipeline"
    }
  }
}

# Use existing S3 Bucket (data source instead of creating new)
data "aws_s3_bucket" "app_bucket" {
  bucket = "pipeline-artifacts-${data.aws_caller_identity.current.account_id}"
}

# Note: Using existing bucket, so versioning and public access block
# should already be configured. If you need to manage these settings,
# ensure the CodeBuild role has appropriate permissions.

# Get current AWS account ID
data "aws_caller_identity" "current" {}

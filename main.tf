terraform {
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

# Create an IAM role for demonstration (doesn't require S3 permissions)
resource "aws_iam_role" "demo_role" {
  name = "terraform-demo-role-${data.aws_caller_identity.current.account_id}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# Create an IAM policy
resource "aws_iam_policy" "demo_policy" {
  name        = "terraform-demo-policy-${data.aws_caller_identity.current.account_id}"
  description = "Demo policy created by Terraform"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "demo_attachment" {
  role       = aws_iam_role.demo_role.name
  policy_arn = aws_iam_policy.demo_policy.arn
}

# Create S3 bucket
resource "aws_s3_bucket" "demo_bucket" {
  bucket = "terraform-demo-bucket-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name = "Demo Bucket"
  }
}

# Enable versioning on the bucket
resource "aws_s3_bucket_versioning" "demo_bucket_versioning" {
  bucket = aws_s3_bucket.demo_bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "demo_bucket_public_access" {
  bucket = aws_s3_bucket.demo_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

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

# Create DynamoDB table
resource "aws_dynamodb_table" "demo_table" {
  name           = "terraform-demo-table-${data.aws_caller_identity.current.account_id}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name = "Demo DynamoDB Table"
  }
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# NOTE: S3 bucket creation is blocked by Service Control Policy (SCP)
# Contact your AWS administrator to allow s3:CreateBucket action

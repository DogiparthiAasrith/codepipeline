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

# Get default VPC
data "aws_vpc" "default" {
  default = true
}

# Get default subnets
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Create security group for FSx Windows
resource "aws_security_group" "fsx_sg" {
  name        = "fsx-windows-sg-${data.aws_caller_identity.current.account_id}"
  description = "Security group for FSx Windows File Server"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 445
    to_port     = 445
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
    description = "SMB/CIFS"
  }

  ingress {
    from_port   = 5985
    to_port     = 5985
    protocol    = "tcp"
    cidr_blocks = [data.aws_vpc.default.cidr_block]
    description = "WinRM HTTP"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "FSx Windows Security Group"
  }
}

# Create AWS Managed Microsoft AD (Simple AD would be cheaper but FSx requires Managed AD)
resource "aws_directory_service_directory" "demo_ad" {
  name     = "corp.demo.local"
  password = var.ad_password
  edition  = "Standard"
  type     = "MicrosoftAD"

  vpc_settings {
    vpc_id     = data.aws_vpc.default.id
    subnet_ids = slice(data.aws_subnets.default.ids, 0, 2)
  }

  tags = {
    Name = "Demo Managed AD for FSx"
  }
}

# Create FSx for Windows File Server with AWS Managed AD
resource "aws_fsx_windows_file_system" "demo_fsx" {
  storage_capacity    = 32
  subnet_ids          = [data.aws_subnets.default.ids[0]]
  throughput_capacity = 8
  security_group_ids  = [aws_security_group.fsx_sg.id]
  active_directory_id = aws_directory_service_directory.demo_ad.id

  tags = {
    Name = "Demo FSx Windows"
  }
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

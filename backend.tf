terraform {
  required_version = ">= 1.14.3"
  
  backend "s3" {
    bucket = "codepipeline-terraform-state-230399361410"
    key    = "environments/prod/terraform.tfstate"
    region = "us-east-1"
    
    # NEW: Enables native S3 locking without DynamoDB
    use_lockfile = true
    
    # Optional: Encrypt the state file
    encrypt = true
  }
}

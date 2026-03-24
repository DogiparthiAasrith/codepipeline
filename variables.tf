variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "ad_password" {
  description = "Active Directory administrator password for FSx"
  type        = string
  sensitive   = true
  default     = "TempPassword123!"
}

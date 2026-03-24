output "fsx_id" {
  description = "ID of the FSx file system"
  value       = aws_fsx_windows_file_system.demo_fsx.id
}

output "fsx_arn" {
  description = "ARN of the FSx file system"
  value       = aws_fsx_windows_file_system.demo_fsx.arn
}

output "fsx_dns_name" {
  description = "DNS name of the FSx file system"
  value       = aws_fsx_windows_file_system.demo_fsx.dns_name
}

output "account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

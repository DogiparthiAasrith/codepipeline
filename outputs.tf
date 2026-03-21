output "demo_role_name" {
  description = "Name of the IAM role"
  value       = aws_iam_role.demo_role.name
}

output "demo_role_arn" {
  description = "ARN of the IAM role"
  value       = aws_iam_role.demo_role.arn
}

output "demo_policy_arn" {
  description = "ARN of the IAM policy"
  value       = aws_iam_policy.demo_policy.arn
}

output "demo_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.demo_table.name
}

output "demo_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.demo_table.arn
}

output "account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}

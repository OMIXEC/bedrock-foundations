output "connections_table_name" {
  description = "Connections table name"
  value       = aws_dynamodb_table.connections.name
}

output "connections_table_arn" {
  description = "Connections table ARN"
  value       = aws_dynamodb_table.connections.arn
}

output "conversations_table_name" {
  description = "Conversations table name"
  value       = aws_dynamodb_table.conversations.name
}

output "conversations_table_arn" {
  description = "Conversations table ARN"
  value       = aws_dynamodb_table.conversations.arn
}

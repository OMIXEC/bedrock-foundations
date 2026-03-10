output "websocket_url" {
  description = "WebSocket API URL"
  value       = module.websocket_api.websocket_url
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain"
  value       = module.s3_frontend.cloudfront_domain
}

output "frontend_bucket" {
  description = "S3 bucket for frontend"
  value       = module.s3_frontend.bucket_name
}

output "connections_table" {
  description = "DynamoDB connections table"
  value       = module.dynamodb.connections_table_name
}

output "conversations_table" {
  description = "DynamoDB conversations table"
  value       = module.dynamodb.conversations_table_name
}

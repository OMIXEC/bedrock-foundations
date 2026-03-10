output "websocket_url" {
  description = "WebSocket API URL"
  value       = "${aws_apigatewayv2_api.websocket_api.api_endpoint}/${var.environment}"
}

output "websocket_api_id" {
  description = "WebSocket API ID"
  value       = aws_apigatewayv2_api.websocket_api.id
}

output "websocket_api_execution_arn" {
  description = "WebSocket API execution ARN"
  value       = aws_apigatewayv2_api.websocket_api.execution_arn
}

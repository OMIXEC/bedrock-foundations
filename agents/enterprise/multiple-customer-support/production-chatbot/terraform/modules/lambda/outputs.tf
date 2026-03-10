output "connect_lambda_arn" {
  description = "Connect Lambda ARN"
  value       = aws_lambda_function.connect.invoke_arn
}

output "disconnect_lambda_arn" {
  description = "Disconnect Lambda ARN"
  value       = aws_lambda_function.disconnect.invoke_arn
}

output "send_message_lambda_arn" {
  description = "Send message Lambda ARN"
  value       = aws_lambda_function.send_message.invoke_arn
}

output "connect_lambda_name" {
  description = "Connect Lambda function name"
  value       = aws_lambda_function.connect.function_name
}

output "disconnect_lambda_name" {
  description = "Disconnect Lambda function name"
  value       = aws_lambda_function.disconnect.function_name
}

output "send_message_lambda_name" {
  description = "Send message Lambda function name"
  value       = aws_lambda_function.send_message.function_name
}

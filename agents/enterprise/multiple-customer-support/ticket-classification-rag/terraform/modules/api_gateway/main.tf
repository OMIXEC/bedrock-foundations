# API Gateway Module - HTTP API with Throttling
# Rate limit: 100 RPS, Burst: 200 for customer support workload

resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.environment}-customer-support-rag-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 300
  }
}

# Throttling settings for customer support load
resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_rate_limit  = 100   # 100 requests per second
    throttling_burst_limit = 200   # Burst capacity
  }
}

variable "environment" { type = string }
variable "lambda_function_arn" { type = string }
variable "lambda_invoke_arn" { type = string }

output "api_endpoint" {
  value = aws_apigatewayv2_api.http_api.api_endpoint
}

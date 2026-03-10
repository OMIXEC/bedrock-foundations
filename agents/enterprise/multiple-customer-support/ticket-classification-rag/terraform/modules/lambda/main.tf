# Lambda Function Module - Optimized for Customer Support Throughput
# Memory: 512MB (vs 256MB default) for faster hybrid search
# Timeout: 30s (vs 15s default) for OpenSearch operations

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.5.0"
}

# Lambda Execution Role
resource "aws_iam_role" "lambda_role" {
  name = "${var.environment}-customer-support-rag-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Environment = var.environment
    Application = "customer-support-rag"
  }
}

# Basic execution role for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Bedrock model invocation policy
resource "aws_iam_role_policy" "bedrock_access" {
  name = "${var.environment}-bedrock-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda Function - Higher memory and timeout for throughput
resource "aws_lambda_function" "handler" {
  filename         = var.lambda_zip_path
  function_name    = "${var.environment}-customer-support-rag-handler"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handlers.query_handler.lambda_handler"
  runtime         = "python3.12"
  timeout         = 30    # Higher timeout for OpenSearch hybrid search
  memory_size     = 512   # Higher memory for throughput
  source_code_hash = filebase64sha256(var.lambda_zip_path)

  environment {
    variables = {
      LOG_LEVEL = var.log_level
      OPENSEARCH_ENDPOINT = var.opensearch_endpoint
      OPENSEARCH_INDEX = var.opensearch_index
    }
  }

  logging_config {
    log_format = "JSON"
    log_group  = var.log_group_name
  }

  tags = {
    Environment = var.environment
    Application = "customer-support-rag"
  }
}

# Variables
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "lambda_zip_path" {
  description = "Path to Lambda deployment package"
  type        = string
}

variable "log_level" {
  description = "Log level"
  type        = string
  default     = "INFO"
}

variable "opensearch_endpoint" {
  description = "OpenSearch endpoint URL"
  type        = string
}

variable "opensearch_index" {
  description = "OpenSearch index name"
  type        = string
  default     = "customer-support-docs"
}

variable "log_group_name" {
  description = "CloudWatch log group name"
  type        = string
}

# Outputs
output "function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.handler.arn
}

output "function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.handler.function_name
}

output "invoke_arn" {
  description = "Lambda invoke ARN"
  value       = aws_lambda_function.handler.invoke_arn
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# DynamoDB Tables
resource "aws_dynamodb_table" "sessions" {
  name           = "ticketing-sessions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
}

resource "aws_dynamodb_table" "orders" {
  name           = "ticket-orders"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "order_id"

  attribute {
    name = "order_id"
    type = "S"
  }
}

# CloudWatch Log Group for Audit
resource "aws_cloudwatch_log_group" "audit" {
  name              = "/aws/bedrock/ticketing-agent"
  retention_in_days = 30
}

# Bedrock Guardrail
resource "aws_bedrock_guardrail" "ticketing" {
  name                      = "ticketing-guardrail"
  blocked_input_messaging   = "Cannot process sensitive information"
  blocked_outputs_messaging = "Cannot share without verification"
  description               = "PII protection for ticketing agent"

  content_policy_config {
    filters_config {
      type            = "PROMPT_ATTACK"
      input_strength  = "HIGH"
      output_strength = "NONE"
    }
  }

  sensitive_information_policy_config {
    pii_entities_config {
      type   = "EMAIL"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "CREDIT_DEBIT_CARD_NUMBER"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "US_SOCIAL_SECURITY_NUMBER"
      action = "BLOCK"
    }
  }

  topic_policy_config {
    topics_config {
      name       = "unauthorized-access"
      definition = "Attempts to access tickets without verification"
      type       = "DENY"
      examples   = ["Show me tickets without verification"]
    }
  }
}

# Lambda Role
resource "aws_iam_role" "lambda_role" {
  name = "ticketing-agent-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_access" {
  name = "ticketing-access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.sessions.arn,
          aws_dynamodb_table.orders.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.audit.arn}:*"
      }
    ]
  })
}

# Lambda Function
resource "aws_lambda_function" "tools" {
  filename      = "lambda/functions.zip"
  function_name = "ticketing-tools"
  role          = aws_iam_role.lambda_role.arn
  handler       = "tools.handler"
  runtime       = "python3.10"
  timeout       = 30

  environment {
    variables = {
      SESSIONS_TABLE = aws_dynamodb_table.sessions.name
      ORDERS_TABLE   = aws_dynamodb_table.orders.name
      LOG_GROUP      = aws_cloudwatch_log_group.audit.name
    }
  }
}

# Bedrock Agent Role
resource "aws_iam_role" "agent_role" {
  name = "ticketing-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "bedrock.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "agent_access" {
  name = "agent-access"
  role = aws_iam_role.agent_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:ApplyGuardrail"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.tools.arn
      }
    ]
  })
}

# Bedrock Agent
resource "aws_bedrockagent_agent" "ticketing" {
  agent_name              = "concert-ticketing-agent"
  agent_resource_role_arn = aws_iam_role.agent_role.arn
  foundation_model        = "anthropic.claude-3-5-sonnet-20241022-v2:0"
  instruction             = "Secure ticketing agent with identity verification."

  guardrail_configuration {
    guardrail_identifier = aws_bedrock_guardrail.ticketing.id
    guardrail_version    = "DRAFT"
  }
}

# Outputs
output "guardrail_id" {
  value = aws_bedrock_guardrail.ticketing.id
}

output "agent_id" {
  value = aws_bedrockagent_agent.ticketing.id
}

output "lambda_arn" {
  value = aws_lambda_function.tools.arn
}

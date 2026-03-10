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

# DynamoDB Table for Sessions
resource "aws_dynamodb_table" "sessions" {
  name           = "ecommerce-sessions"
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

  tags = {
    Name = "E-commerce Sessions"
  }
}

# Lambda Execution Role
resource "aws_iam_role" "lambda_role" {
  name = "ecommerce-agent-lambda-role"

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

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "dynamodb-access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem"
      ]
      Resource = aws_dynamodb_table.sessions.arn
    }]
  })
}

resource "aws_iam_role_policy" "lambda_bedrock" {
  name = "bedrock-access"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "bedrock:InvokeModel"
      ]
      Resource = "*"
    }]
  })
}

# Lambda Function
resource "aws_lambda_function" "tools" {
  filename      = "lambda/functions.zip"
  function_name = "ecommerce-tools"
  role          = aws_iam_role.lambda_role.arn
  handler       = "tools.handler"
  runtime       = "python3.10"
  timeout       = 30

  environment {
    variables = {
      PINECONE_API_KEY = var.pinecone_api_key
      TABLE_NAME       = aws_dynamodb_table.sessions.name
    }
  }
}

# Bedrock Agent Role
resource "aws_iam_role" "agent_role" {
  name = "ecommerce-agent-role"

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

resource "aws_iam_role_policy" "agent_bedrock" {
  name = "bedrock-access"
  role = aws_iam_role.agent_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "bedrock:InvokeModel"
      ]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy" "agent_lambda" {
  name = "lambda-invoke"
  role = aws_iam_role.agent_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "lambda:InvokeFunction"
      ]
      Resource = aws_lambda_function.tools.arn
    }]
  })
}

# Bedrock Agent
resource "aws_bedrockagent_agent" "ecommerce" {
  agent_name              = "ecommerce-product-assistant"
  agent_resource_role_arn = aws_iam_role.agent_role.arn
  foundation_model        = "anthropic.claude-3-5-sonnet-20241022-v2:0"
  instruction             = "You are a helpful e-commerce shopping assistant."
}

# Outputs
output "dynamodb_table_name" {
  value = aws_dynamodb_table.sessions.name
}

output "lambda_function_arn" {
  value = aws_lambda_function.tools.arn
}

output "agent_id" {
  value = aws_bedrockagent_agent.ecommerce.id
}

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # S3 backend for state management (configure as needed)
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "chatbot/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-state-lock"
  # }
}

provider "aws" {
  region = var.aws_region
}

# DynamoDB tables
module "dynamodb" {
  source = "./modules/dynamodb"

  environment        = var.environment
  connections_table  = "${var.project_name}-connections-${var.environment}"
  conversations_table = "${var.project_name}-conversations-${var.environment}"
}

# Lambda functions
module "lambda" {
  source = "./modules/lambda"

  environment         = var.environment
  project_name        = var.project_name
  connections_table   = module.dynamodb.connections_table_name
  conversations_table = module.dynamodb.conversations_table_name
  lambda_role_arn     = aws_iam_role.lambda_role.arn
}

# WebSocket API Gateway
module "websocket_api" {
  source = "./modules/websocket_api"

  environment               = var.environment
  project_name              = var.project_name
  connect_lambda_arn        = module.lambda.connect_lambda_arn
  disconnect_lambda_arn     = module.lambda.disconnect_lambda_arn
  send_message_lambda_arn   = module.lambda.send_message_lambda_arn
  connect_lambda_name       = module.lambda.connect_lambda_name
  disconnect_lambda_name    = module.lambda.disconnect_lambda_name
  send_message_lambda_name  = module.lambda.send_message_lambda_name
}

# S3 + CloudFront for frontend
module "s3_frontend" {
  source = "./modules/s3_frontend"

  environment  = var.environment
  project_name = var.project_name
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${var.environment}"

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
}

# Lambda basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# DynamoDB access policy
resource "aws_iam_role_policy" "dynamodb_policy" {
  name = "${var.project_name}-dynamodb-policy-${var.environment}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          module.dynamodb.connections_table_arn,
          module.dynamodb.conversations_table_arn
        ]
      }
    ]
  })
}

# Bedrock access policy
resource "aws_iam_role_policy" "bedrock_policy" {
  name = "${var.project_name}-bedrock-policy-${var.environment}"
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
        Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0"
      }
    ]
  })
}

# API Gateway management policy for WebSocket
resource "aws_iam_role_policy" "apigateway_policy" {
  name = "${var.project_name}-apigateway-policy-${var.environment}"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "execute-api:ManageConnections"
        ]
        Resource = "${module.websocket_api.websocket_api_execution_arn}/*"
      }
    ]
  })
}

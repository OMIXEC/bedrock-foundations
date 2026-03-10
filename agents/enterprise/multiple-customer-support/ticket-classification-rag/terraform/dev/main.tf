# Customer Support RAG - Dev Environment

terraform {
  required_version = ">= 1.5.0"
}

provider "aws" {
  region = "us-east-1"
}

# Lambda Module with higher memory/timeout
module "lambda" {
  source = "../modules/lambda"

  environment         = "dev"
  lambda_zip_path     = "../../backend/lambda-package.zip"
  opensearch_endpoint = "your-opensearch-endpoint.us-east-1.aoss.amazonaws.com"
  opensearch_index    = "customer-support-docs"
  log_group_name      = "/aws/lambda/dev-customer-support-rag"
}

# API Gateway with throttling
module "api_gateway" {
  source = "../modules/api_gateway"

  environment         = "dev"
  lambda_function_arn = module.lambda.function_arn
  lambda_invoke_arn   = module.lambda.invoke_arn
}

output "api_endpoint" {
  value = module.api_gateway.api_endpoint
}

# Package backend code
data "archive_file" "backend_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../backend/src"
  output_path = "${path.root}/../backend/lambda_package.zip"
}

# Connect Lambda
resource "aws_lambda_function" "connect" {
  filename         = data.archive_file.backend_zip.output_path
  function_name    = "${var.project_name}-connect-${var.environment}"
  role             = var.lambda_role_arn
  handler          = "handlers.connect.handler"
  source_code_hash = data.archive_file.backend_zip.output_base64sha256
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      ENVIRONMENT          = var.environment
      CONNECTIONS_TABLE    = var.connections_table
      CONVERSATIONS_TABLE  = var.conversations_table
    }
  }

  logging_config {
    log_format = "JSON"
    log_group  = "/aws/lambda/${var.project_name}-connect-${var.environment}"
  }
}

# Disconnect Lambda
resource "aws_lambda_function" "disconnect" {
  filename         = data.archive_file.backend_zip.output_path
  function_name    = "${var.project_name}-disconnect-${var.environment}"
  role             = var.lambda_role_arn
  handler          = "handlers.disconnect.handler"
  source_code_hash = data.archive_file.backend_zip.output_base64sha256
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      ENVIRONMENT          = var.environment
      CONNECTIONS_TABLE    = var.connections_table
      CONVERSATIONS_TABLE  = var.conversations_table
    }
  }

  logging_config {
    log_format = "JSON"
    log_group  = "/aws/lambda/${var.project_name}-disconnect-${var.environment}"
  }
}

# Send message Lambda
resource "aws_lambda_function" "send_message" {
  filename         = data.archive_file.backend_zip.output_path
  function_name    = "${var.project_name}-send-message-${var.environment}"
  role             = var.lambda_role_arn
  handler          = "handlers.send_message.handler"
  source_code_hash = data.archive_file.backend_zip.output_base64sha256
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 1024

  environment {
    variables = {
      ENVIRONMENT          = var.environment
      CONNECTIONS_TABLE    = var.connections_table
      CONVERSATIONS_TABLE  = var.conversations_table
    }
  }

  logging_config {
    log_format = "JSON"
    log_group  = "/aws/lambda/${var.project_name}-send-message-${var.environment}"
  }
}

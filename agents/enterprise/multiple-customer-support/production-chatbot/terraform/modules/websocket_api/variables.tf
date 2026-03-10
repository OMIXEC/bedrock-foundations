variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "connect_lambda_arn" {
  description = "Connect Lambda ARN"
  type        = string
}

variable "disconnect_lambda_arn" {
  description = "Disconnect Lambda ARN"
  type        = string
}

variable "send_message_lambda_arn" {
  description = "Send message Lambda ARN"
  type        = string
}

variable "connect_lambda_name" {
  description = "Connect Lambda function name"
  type        = string
}

variable "disconnect_lambda_name" {
  description = "Disconnect Lambda function name"
  type        = string
}

variable "send_message_lambda_name" {
  description = "Send message Lambda function name"
  type        = string
}

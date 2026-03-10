variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "connections_table" {
  description = "Connections table name"
  type        = string
}

variable "conversations_table" {
  description = "Conversations table name"
  type        = string
}

variable "lambda_role_arn" {
  description = "Lambda execution role ARN"
  type        = string
}

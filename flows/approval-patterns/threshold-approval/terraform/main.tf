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

# IAM Role for Flow
resource "aws_iam_role" "flow_role" {
  name = "threshold-approval-flow-role"

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

resource "aws_iam_role_policy" "flow_bedrock" {
  name = "bedrock-access"
  role = aws_iam_role.flow_role.id

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

# Bedrock Flow
resource "aws_bedrockagent_flow" "threshold_approval" {
  name                     = "threshold-approval-flow"
  execution_role_arn       = aws_iam_role.flow_role.arn
  description              = "Auto-approve refunds <$50, escalate to manager ($50-$500) or director (>$500)"
  definition_string        = file("${path.module}/../flow.json")
}

# Flow Version
resource "aws_bedrockagent_flow_version" "v1" {
  flow_arn = aws_bedrockagent_flow.threshold_approval.arn
}

# Flow Alias
resource "aws_bedrockagent_flow_alias" "live" {
  flow_arn            = aws_bedrockagent_flow.threshold_approval.arn
  name                = "live"
  routing_configuration {
    flow_version = aws_bedrockagent_flow_version.v1.version
  }
}

# Outputs
output "flow_id" {
  value = aws_bedrockagent_flow.threshold_approval.id
}

output "flow_arn" {
  value = aws_bedrockagent_flow.threshold_approval.arn
}

output "alias_id" {
  value = aws_bedrockagent_flow_alias.live.id
}

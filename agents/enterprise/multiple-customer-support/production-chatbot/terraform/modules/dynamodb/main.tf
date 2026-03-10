resource "aws_dynamodb_table" "connections" {
  name           = var.connections_table
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "connectionId"

  attribute {
    name = "connectionId"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = var.connections_table
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "conversations" {
  name           = var.conversations_table
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "sessionId"
  range_key      = "messageId"

  attribute {
    name = "sessionId"
    type = "S"
  }

  attribute {
    name = "messageId"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = {
    Name        = var.conversations_table
    Environment = var.environment
  }
}

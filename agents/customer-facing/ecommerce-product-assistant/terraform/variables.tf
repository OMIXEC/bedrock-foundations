variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "pinecone_api_key" {
  description = "Pinecone API key"
  type        = string
  sensitive   = true
}

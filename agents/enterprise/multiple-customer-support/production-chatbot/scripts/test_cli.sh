#!/bin/bash
# Test CLI chatbot with AWS credentials

set -e

echo "🧪 Testing Bedrock CLI with AWS credentials..."

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured!"
    echo "Run: aws configure"
    exit 1
fi

echo "✅ AWS credentials found"

# Run CLI
cd backend
python -m src.cli.chat_cli "$@"

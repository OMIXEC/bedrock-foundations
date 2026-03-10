#!/bin/bash
# Deploy Customer Support RAG to AWS

set -e

ENVIRONMENT=${1:-dev}

echo "Deploying to $ENVIRONMENT environment..."

# Step 1: Run tests
./scripts/run-tests.sh all

# Step 2: Package Lambda
./scripts/package-lambda.sh

# Step 3: Deploy with Terraform
cd terraform/$ENVIRONMENT
terraform init
terraform plan
terraform apply -auto-approve

echo "Deployment complete!"

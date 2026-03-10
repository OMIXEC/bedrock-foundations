#!/bin/bash

##
# Deploy production chatbot infrastructure and application.
#
# Usage: ./deploy.sh [environment]
#   environment: dev (default), staging, or prod
##

set -e

ENVIRONMENT=${1:-dev}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🚀 Deploying production chatbot to environment: $ENVIRONMENT"

# Step 1: Install backend dependencies
echo ""
echo "📦 Step 1: Installing backend dependencies..."
cd "$PROJECT_ROOT/backend"
pip install -r requirements.txt -t src/ --upgrade

# Step 2: Run tests
echo ""
echo "🧪 Step 2: Running backend tests..."
pytest tests/ --cov=src --cov-fail-under=80

# Step 3: Deploy infrastructure with Terraform
echo ""
echo "🏗️  Step 3: Deploying infrastructure with Terraform..."
cd "$PROJECT_ROOT/terraform"
terraform init
terraform plan -var="environment=$ENVIRONMENT"
terraform apply -var="environment=$ENVIRONMENT" -auto-approve

# Get outputs
WEBSOCKET_URL=$(terraform output -raw websocket_url)
FRONTEND_BUCKET=$(terraform output -raw frontend_bucket)
CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain)
CLOUDFRONT_DIST_ID=$(terraform output -raw cloudfront_distribution_id)

echo "✅ Infrastructure deployed"
echo "   WebSocket URL: $WEBSOCKET_URL"
echo "   Frontend bucket: $FRONTEND_BUCKET"
echo "   CloudFront domain: $CLOUDFRONT_DOMAIN"

# Step 4: Build frontend
echo ""
echo "🎨 Step 4: Building frontend..."
cd "$PROJECT_ROOT/frontend"

# Set WebSocket URL in environment
export NEXT_PUBLIC_WS_URL="$WEBSOCKET_URL"

# Install dependencies and build
npm install
npm run build

# Step 5: Deploy frontend to S3
echo ""
echo "☁️  Step 5: Deploying frontend to S3..."
aws s3 sync out/ "s3://$FRONTEND_BUCKET/" --delete

# Step 6: Invalidate CloudFront cache
echo ""
echo "🔄 Step 6: Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_DIST_ID" \
  --paths "/*"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Access your chatbot at: https://$CLOUDFRONT_DOMAIN"
echo "🔌 WebSocket URL: $WEBSOCKET_URL"
echo ""

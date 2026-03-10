#!/bin/bash

##
# Teardown production chatbot infrastructure.
#
# Usage: ./teardown.sh [environment]
#   environment: dev (default), staging, or prod
##

set -e

ENVIRONMENT=${1:-dev}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🗑️  Tearing down production chatbot environment: $ENVIRONMENT"
echo ""
echo "⚠️  WARNING: This will destroy all resources and data!"
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Cancelled."
  exit 0
fi

cd "$PROJECT_ROOT/terraform"

# Get frontend bucket name before destroying
FRONTEND_BUCKET=$(terraform output -raw frontend_bucket 2>/dev/null || echo "")

# Empty S3 bucket (required before Terraform can delete it)
if [ -n "$FRONTEND_BUCKET" ]; then
  echo ""
  echo "📦 Emptying S3 bucket: $FRONTEND_BUCKET"
  aws s3 rm "s3://$FRONTEND_BUCKET/" --recursive || true
fi

# Destroy infrastructure
echo ""
echo "💥 Destroying infrastructure..."
terraform destroy -var="environment=$ENVIRONMENT" -auto-approve

echo ""
echo "✅ Teardown complete"

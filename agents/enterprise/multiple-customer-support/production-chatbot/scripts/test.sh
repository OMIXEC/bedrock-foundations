#!/bin/bash

##
# Run backend tests with coverage.
#
# Usage: ./test.sh
##

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 Running backend tests..."

cd "$PROJECT_ROOT/backend"

# Install test dependencies
pip install -r requirements-dev.txt --quiet

# Run tests with coverage
pytest tests/ \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html \
  --cov-fail-under=80 \
  -v

echo ""
echo "✅ Tests passed!"
echo "📊 Coverage report: backend/htmlcov/index.html"

#!/bin/bash
# Run tests for Customer Support RAG

set -e

TEST_TYPE=${1:-all}

case "$TEST_TYPE" in
    unit)
        echo "Running unit tests..."
        pytest -m unit --cov=src --cov-report=html -v
        ;;
    integration)
        echo "Running integration tests (requires AWS credentials)..."
        pytest -m integration -v
        ;;
    all)
        echo "Running all tests..."
        pytest -m "not load" --cov=src --cov-fail-under=80 -v
        ;;
    load)
        echo "Load testing instructions:"
        echo "  locust -f tests/load/locustfile.py --host=https://your-api-endpoint"
        ;;
    *)
        echo "Usage: ./run-tests.sh [unit|integration|all|load]"
        exit 1
        ;;
esac

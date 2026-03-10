"""
Pytest configuration and shared fixtures for Customer Support RAG testing.

WARNING: moto patches boto3 globally. Never use mock fixtures and real fixtures
in the same test or test file.

Test organization:
- tests/unit/ - Use mock fixtures (fast, no AWS costs)
- tests/integration/ - Use real fixtures (slower, incurs AWS costs)
- tests/load/ - Use locust for load testing (dedicated environment)
"""

import pytest
import boto3
from moto import mock_bedrock_runtime, mock_secretsmanager
import json


def pytest_configure(config):
    """Register custom markers for test organization."""
    config.addinivalue_line(
        "markers", "unit: Unit tests with mocked AWS services (fast, no costs)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with real AWS APIs (slower, incurs costs)"
    )
    config.addinivalue_line(
        "markers", "load: Load and performance tests (run on dedicated test environment)"
    )


# =============================================================================
# MOCK FIXTURES - Use these for unit tests (fast, no AWS costs)
# =============================================================================

@pytest.fixture
def mock_bedrock_client():
    """
    Mock Bedrock Runtime client using moto.

    WARNING: moto patches boto3 globally. Don't mix with real_bedrock_client.
    """
    with mock_bedrock_runtime():
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
        yield client


@pytest.fixture
def mock_secrets_client():
    """
    Mock Secrets Manager client using moto with a pre-created test secret.
    """
    with mock_secretsmanager():
        client = boto3.client('secretsmanager', region_name='us-east-1')
        # Create a test secret
        client.create_secret(
            Name='test-secret',
            SecretString=json.dumps({
                "OPENSEARCH_PASSWORD": "test-password"
            })
        )
        yield client


# =============================================================================
# REAL FIXTURES - Use these for integration tests (slower, incurs AWS costs)
# =============================================================================

@pytest.fixture
def real_bedrock_client():
    """
    Real Bedrock Runtime client for integration testing.

    NEVER mix this with mock fixtures in the same test file.
    """
    return boto3.client('bedrock-runtime', region_name='us-east-1')


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================

@pytest.fixture
def sample_customer_queries():
    """
    Sample customer support queries for testing ticket classification
    """
    return {
        "billing": [
            "How do I update my credit card?",
            "Can I get a refund for my subscription?",
            "What payment methods do you accept?",
            "How do I cancel my subscription?"
        ],
        "technical": [
            "My sync keeps failing with error 500",
            "The API returns 429 too many requests",
            "Files are not syncing to my other devices",
            "Application crashes when I try to upload videos"
        ],
        "account": [
            "I forgot my password",
            "How do I enable two-factor authentication?",
            "Can I change my email address?",
            "How do I add team members to my account?"
        ],
        "general": [
            "What features does CloudSync offer?",
            "Which file types are supported?",
            "Can I access files offline?",
            "What are the system requirements?"
        ]
    }


@pytest.fixture
def sample_rag_context():
    """
    Sample document chunks for testing RAG applications.
    """
    return [
        {
            "content": "CloudSync Pro subscription can be cancelled at any time through Settings > Billing. You retain access until the end of your billing period. Full refund available within first 30 days.",
            "source": "faq.txt",
            "category": "billing",
            "score": 0.92
        },
        {
            "content": "Error 500 indicates a server-side issue. Check https://status.cloudsync.com for known issues. If persistent, retry after 30 seconds and contact support with the request ID.",
            "source": "troubleshooting_guides.txt",
            "category": "technical",
            "score": 0.88
        },
        {
            "content": "To reset your password: Go to https://app.cloudsync.com/login, click 'Forgot Password?', enter your email, and check your email for reset link.",
            "source": "faq.txt",
            "category": "account",
            "score": 0.85
        }
    ]

"""
Pytest configuration and fixtures.
"""

import os
import pytest
from moto import mock_aws

# Set test environment variables
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture
def aws_credentials():
    """Set up mock AWS credentials."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"


@pytest.fixture
def config_file(tmp_path):
    """Create temporary config file."""
    config_content = """
environment: test

bedrock:
  model_id: "anthropic.claude-sonnet-4-5-20250929-v1:0"
  region: "us-east-1"
  max_tokens: 4096
  temperature: 0.7

dynamodb:
  connections_table: "test-connections"
  conversations_table: "test-conversations"
  ttl_days: 30
  region: "us-east-1"

conversation:
  max_history_messages: 20
  summarization_trigger: 15
  system_prompt: "You are a helpful assistant."

logging:
  level: "INFO"
  json_format: true

websocket:
  connection_timeout_seconds: 600
  max_message_size_bytes: 32768
"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text(config_content)
    return str(config_path)

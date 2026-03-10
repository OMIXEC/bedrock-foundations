"""
Unit tests for Pydantic models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.messages import (
    Message,
    MessageRole,
    SendMessageRequest,
    SendMessageResponse,
    ConnectionEvent,
)
from src.models.config import Config, BedrockConfig, DynamoDBConfig, ConversationConfig


class TestMessageModels:
    """Test message Pydantic models."""

    def test_message_valid(self):
        """Test valid message creation."""
        msg = Message(
            message_id="123",
            session_id="session-1",
            role=MessageRole.USER,
            content="Hello",
            timestamp=datetime.utcnow(),
        )
        assert msg.message_id == "123"
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello"

    def test_message_empty_content(self):
        """Test message with empty content fails validation."""
        with pytest.raises(ValidationError):
            Message(
                message_id="123",
                session_id="session-1",
                role=MessageRole.USER,
                content="   ",  # Only whitespace
                timestamp=datetime.utcnow(),
            )

    def test_send_message_request_valid(self):
        """Test valid send message request."""
        req = SendMessageRequest(message="Hello", session_id="session-1")
        assert req.message == "Hello"
        assert req.session_id == "session-1"

    def test_send_message_request_no_session(self):
        """Test send message request without session ID."""
        req = SendMessageRequest(message="Hello")
        assert req.message == "Hello"
        assert req.session_id is None

    def test_send_message_request_empty(self):
        """Test send message request with empty message fails."""
        with pytest.raises(ValidationError):
            SendMessageRequest(message="")

    def test_send_message_request_too_long(self):
        """Test send message request with too long message fails."""
        with pytest.raises(ValidationError):
            SendMessageRequest(message="x" * 10000)

    def test_send_message_request_suspicious_pattern(self):
        """Test send message request blocks suspicious patterns."""
        with pytest.raises(ValidationError, match="suspicious pattern"):
            SendMessageRequest(message="<script>alert('xss')</script>")

        with pytest.raises(ValidationError, match="suspicious pattern"):
            SendMessageRequest(message="javascript:alert(1)")

    def test_connection_event(self):
        """Test connection event model."""
        event = ConnectionEvent(
            connection_id="abc123",
            timestamp=datetime.utcnow(),
            event_type="CONNECT",
        )
        assert event.connection_id == "abc123"
        assert event.event_type == "CONNECT"


class TestConfigModels:
    """Test configuration models."""

    def test_bedrock_config_defaults(self):
        """Test Bedrock config with defaults."""
        config = BedrockConfig()
        assert config.model_id == "anthropic.claude-sonnet-4-5-20250929-v1:0"
        assert config.region == "us-east-1"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7

    def test_bedrock_config_custom(self):
        """Test Bedrock config with custom values."""
        config = BedrockConfig(
            model_id="custom-model", region="us-west-2", max_tokens=2048, temperature=0.5
        )
        assert config.model_id == "custom-model"
        assert config.region == "us-west-2"
        assert config.max_tokens == 2048
        assert config.temperature == 0.5

    def test_bedrock_config_validation(self):
        """Test Bedrock config validation."""
        with pytest.raises(ValidationError):
            BedrockConfig(temperature=1.5)  # Too high

        with pytest.raises(ValidationError):
            BedrockConfig(max_tokens=0)  # Too low

    def test_dynamodb_config(self):
        """Test DynamoDB config."""
        config = DynamoDBConfig(
            connections_table="connections",
            conversations_table="conversations",
            ttl_days=30,
        )
        assert config.connections_table == "connections"
        assert config.conversations_table == "conversations"
        assert config.ttl_days == 30

    def test_conversation_config(self):
        """Test conversation config."""
        config = ConversationConfig(
            max_history_messages=20,
            summarization_trigger=15,
            system_prompt="You are helpful",
        )
        assert config.max_history_messages == 20
        assert config.summarization_trigger == 15
        assert config.system_prompt == "You are helpful"

    def test_full_config(self, config_file):
        """Test full config loading."""
        from src.utils.config_loader import load_config

        config = load_config(config_file)
        assert config.environment == "test"
        assert config.bedrock.model_id == "anthropic.claude-sonnet-4-5-20250929-v1:0"
        assert config.dynamodb.connections_table == "test-connections"
        assert config.conversation.max_history_messages == 20

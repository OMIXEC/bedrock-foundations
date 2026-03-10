"""
Unit tests for ConversationService.
"""

import pytest
import boto3
from datetime import datetime
from moto import mock_aws

from src.services.conversation import ConversationService
from src.models.messages import MessageRole
from src.utils.config_loader import load_config


@mock_aws
class TestConversationService:
    """Test ConversationService with moto DynamoDB mocks."""

    @pytest.fixture
    def dynamodb_tables(self, config_file):
        """Create mock DynamoDB tables."""
        config = load_config(config_file)

        # Create DynamoDB tables
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Connections table
        dynamodb.create_table(
            TableName="test-connections",
            KeySchema=[{"AttributeName": "connectionId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "connectionId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Conversations table
        dynamodb.create_table(
            TableName="test-conversations",
            KeySchema=[
                {"AttributeName": "sessionId", "KeyType": "HASH"},
                {"AttributeName": "messageId", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "sessionId", "AttributeType": "S"},
                {"AttributeName": "messageId", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        return config

    def test_store_connection(self, dynamodb_tables):
        """Test storing WebSocket connection."""
        service = ConversationService(dynamodb_tables)

        service.store_connection("conn-123")

        # Verify connection stored
        response = service.connections_table.get_item(Key={"connectionId": "conn-123"})
        assert "Item" in response
        assert response["Item"]["connectionId"] == "conn-123"

    def test_remove_connection(self, dynamodb_tables):
        """Test removing WebSocket connection."""
        service = ConversationService(dynamodb_tables)

        # Store then remove
        service.store_connection("conn-123")
        service.remove_connection("conn-123")

        # Verify connection removed
        response = service.connections_table.get_item(Key={"connectionId": "conn-123"})
        assert "Item" not in response

    def test_store_message(self, dynamodb_tables):
        """Test storing conversation message."""
        service = ConversationService(dynamodb_tables)

        message = service.store_message(
            session_id="session-1", role=MessageRole.USER, content="Hello"
        )

        assert message.session_id == "session-1"
        assert message.role == MessageRole.USER
        assert message.content == "Hello"
        assert message.message_id is not None

        # Verify message stored in DynamoDB
        response = service.conversations_table.get_item(
            Key={"sessionId": "session-1", "messageId": message.message_id}
        )
        assert "Item" in response
        assert response["Item"]["content"] == "Hello"

    def test_get_conversation_history(self, dynamodb_tables):
        """Test retrieving conversation history."""
        service = ConversationService(dynamodb_tables)

        # Store multiple messages
        service.store_message("session-1", MessageRole.USER, "Hello")
        service.store_message("session-1", MessageRole.ASSISTANT, "Hi there!")
        service.store_message("session-1", MessageRole.USER, "How are you?")

        # Retrieve history
        history = service.get_conversation_history("session-1")

        assert len(history) == 3
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"
        assert history[1]["role"] == "assistant"
        assert history[1]["content"] == "Hi there!"

    def test_conversation_history_max_limit(self, dynamodb_tables):
        """Test conversation history respects max limit."""
        service = ConversationService(dynamodb_tables)

        # Store more messages than max_history (20)
        for i in range(25):
            role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
            service.store_message("session-1", role, f"Message {i}")

        history = service.get_conversation_history("session-1")

        # Should only return last 20
        assert len(history) == 20

    def test_conversation_summarization(self, dynamodb_tables):
        """Test conversation summarization triggers."""
        service = ConversationService(dynamodb_tables)

        # Store more than summarization_trigger (15)
        for i in range(20):
            role = MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT
            service.store_message("session-1", role, f"Message {i}")

        history = service.get_conversation_history("session-1")

        # Should trigger summarization
        # First message should be summary, followed by recent messages
        assert len(history) <= 20
        # Summary message contains "Previous conversation summary"
        if len(history) > 15:
            assert any("summary" in msg.get("content", "").lower() for msg in history)

    def test_create_session_id(self, dynamodb_tables):
        """Test session ID creation."""
        service = ConversationService(dynamodb_tables)

        session_id = service.create_session_id()

        assert session_id is not None
        assert len(session_id) > 0
        assert "-" in session_id  # UUID format

"""
Unit tests for Lambda handlers.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from moto import mock_aws
import boto3


@mock_aws
class TestConnectHandler:
    """Test WebSocket connect handler."""

    @pytest.fixture
    def setup_tables(self):
        """Set up DynamoDB tables for tests."""
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        # Create connections table
        dynamodb.create_table(
            TableName="test-connections",
            KeySchema=[{"AttributeName": "connectionId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "connectionId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        # Create conversations table
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

    @patch("src.handlers.connect.load_config")
    def test_connect_success(self, mock_load_config, setup_tables, config_file):
        """Test successful WebSocket connection."""
        from src.utils.config_loader import load_config
        from src.handlers.connect import handler

        mock_load_config.return_value = load_config(config_file)

        event = {
            "requestContext": {
                "connectionId": "test-connection-123",
                "requestId": "req-123",
            }
        }

        response = handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["message"] == "Connected"

        # Verify connection stored
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.Table("test-connections")
        result = table.get_item(Key={"connectionId": "test-connection-123"})
        assert "Item" in result


@mock_aws
class TestDisconnectHandler:
    """Test WebSocket disconnect handler."""

    @pytest.fixture
    def setup_tables(self):
        """Set up DynamoDB tables."""
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        dynamodb.create_table(
            TableName="test-connections",
            KeySchema=[{"AttributeName": "connectionId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "connectionId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )

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

    @patch("src.handlers.disconnect.load_config")
    def test_disconnect_success(self, mock_load_config, setup_tables, config_file):
        """Test successful WebSocket disconnection."""
        from src.utils.config_loader import load_config
        from src.handlers.disconnect import handler

        mock_load_config.return_value = load_config(config_file)

        # First store a connection
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.Table("test-connections")
        table.put_item(Item={"connectionId": "test-connection-123", "timestamp": "2024-01-01"})

        event = {
            "requestContext": {
                "connectionId": "test-connection-123",
                "requestId": "req-123",
            }
        }

        response = handler(event, None)

        assert response["statusCode"] == 200

        # Verify connection removed
        result = table.get_item(Key={"connectionId": "test-connection-123"})
        assert "Item" not in result


@mock_aws
class TestSendMessageHandler:
    """Test WebSocket sendMessage handler."""

    @pytest.fixture
    def setup_tables(self):
        """Set up DynamoDB tables."""
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

        dynamodb.create_table(
            TableName="test-connections",
            KeySchema=[{"AttributeName": "connectionId", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "connectionId", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )

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

    @patch("src.handlers.send_message.boto3.client")
    @patch("src.handlers.send_message.load_config")
    def test_send_message_validation_error(
        self, mock_load_config, mock_boto_client, setup_tables, config_file
    ):
        """Test send message with validation error."""
        from src.utils.config_loader import load_config
        from src.handlers.send_message import handler

        mock_load_config.return_value = load_config(config_file)

        # Mock WebSocket client
        mock_ws_client = MagicMock()
        mock_boto_client.return_value = mock_ws_client

        event = {
            "requestContext": {
                "connectionId": "test-connection-123",
                "requestId": "req-123",
                "domainName": "test.execute-api.us-east-1.amazonaws.com",
                "stage": "dev",
            },
            "body": json.dumps({"message": ""}),  # Empty message
        }

        response = handler(event, None)

        assert response["statusCode"] == 400

        # Verify error sent to client
        assert mock_ws_client.post_to_connection.called

    @patch("src.handlers.send_message.boto3.client")
    @patch("src.handlers.send_message.load_config")
    @patch("src.handlers.send_message.bedrock_client")
    def test_send_message_success(
        self,
        mock_bedrock,
        mock_load_config,
        mock_boto_client,
        setup_tables,
        config_file,
    ):
        """Test successful message send with streaming."""
        from src.utils.config_loader import load_config
        from src.handlers.send_message import handler

        mock_load_config.return_value = load_config(config_file)

        # Mock WebSocket client
        mock_ws_client = MagicMock()
        mock_boto_client.return_value = mock_ws_client

        # Mock Bedrock streaming response
        mock_bedrock.converse_stream.return_value = iter(["Hello", " ", "world", "!"])

        event = {
            "requestContext": {
                "connectionId": "test-connection-123",
                "requestId": "req-123",
                "domainName": "test.execute-api.us-east-1.amazonaws.com",
                "stage": "dev",
            },
            "body": json.dumps({"message": "Hello", "session_id": "session-1"}),
        }

        response = handler(event, None)

        assert response["statusCode"] == 200

        # Verify WebSocket messages sent
        assert mock_ws_client.post_to_connection.call_count >= 4  # ack + start + chunks + end

        # Verify messages stored in DynamoDB
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.Table("test-conversations")
        result = table.query(
            KeyConditionExpression="sessionId = :sid",
            ExpressionAttributeValues={":sid": "session-1"},
        )
        assert len(result["Items"]) == 2  # User + Assistant

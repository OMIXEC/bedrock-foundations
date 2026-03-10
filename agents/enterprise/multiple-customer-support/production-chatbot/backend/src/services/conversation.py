"""
Conversation management service with DynamoDB persistence and summarization.
"""

import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from ..models.messages import Message, MessageRole
from ..models.config import Config
from ..utils.logger import get_logger


class ConversationService:
    """
    Manages conversation history with DynamoDB storage, TTL, and summarization.

    Features:
    - Composite keys (session_id + message_id) for efficient queries
    - TTL automatic cleanup of old conversations
    - Conversation summarization before context window limits
    - Connection tracking for WebSocket management
    """

    def __init__(self, config: Config):
        """
        Initialize conversation service.

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = get_logger(__name__, config.logging.level)

        # DynamoDB clients
        self.dynamodb = boto3.resource("dynamodb", region_name=config.dynamodb.region)
        self.connections_table = self.dynamodb.Table(
            config.dynamodb.connections_table
        )
        self.conversations_table = self.dynamodb.Table(
            config.dynamodb.conversations_table
        )

        # Configuration
        self.max_history = config.conversation.max_history_messages
        self.summarization_trigger = config.conversation.summarization_trigger
        self.ttl_days = config.dynamodb.ttl_days

    def store_connection(self, connection_id: str) -> None:
        """
        Store WebSocket connection.

        Args:
            connection_id: WebSocket connection ID
        """
        try:
            ttl = int((datetime.utcnow() + timedelta(days=1)).timestamp())

            self.connections_table.put_item(
                Item={
                    "connectionId": connection_id,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "ttl": ttl,
                }
            )

            self.logger.info(
                "Connection stored",
                connection_id=connection_id,
            )

        except ClientError as e:
            self.logger.error(
                "Failed to store connection",
                connection_id=connection_id,
                error=str(e),
            )
            raise

    def remove_connection(self, connection_id: str) -> None:
        """
        Remove WebSocket connection.

        Args:
            connection_id: WebSocket connection ID
        """
        try:
            self.connections_table.delete_item(Key={"connectionId": connection_id})

            self.logger.info(
                "Connection removed",
                connection_id=connection_id,
            )

        except ClientError as e:
            self.logger.error(
                "Failed to remove connection",
                connection_id=connection_id,
                error=str(e),
            )
            raise

    def store_message(
        self, session_id: str, role: MessageRole, content: str
    ) -> Message:
        """
        Store a message in conversation history.

        Args:
            session_id: Session/conversation identifier
            role: Message role (user/assistant)
            content: Message content

        Returns:
            Stored Message object
        """
        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        ttl = int((timestamp + timedelta(days=self.ttl_days)).timestamp())

        message = Message(
            message_id=message_id,
            session_id=session_id,
            role=role,
            content=content,
            timestamp=timestamp,
        )

        try:
            self.conversations_table.put_item(
                Item={
                    "sessionId": session_id,
                    "messageId": message_id,
                    "role": role.value,
                    "content": content,
                    "timestamp": timestamp.isoformat() + "Z",
                    "ttl": ttl,
                }
            )

            self.logger.info(
                "Message stored",
                session_id=session_id,
                message_id=message_id,
                role=role.value,
            )

            return message

        except ClientError as e:
            self.logger.error(
                "Failed to store message",
                session_id=session_id,
                error=str(e),
            )
            raise

    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Retrieve conversation history for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of messages in Bedrock format: [{"role": "user", "content": "..."}]
        """
        try:
            response = self.conversations_table.query(
                KeyConditionExpression="sessionId = :sid",
                ExpressionAttributeValues={":sid": session_id},
                ScanIndexForward=True,  # Sort by timestamp ascending
            )

            messages = []
            for item in response.get("Items", []):
                # Skip system messages in history (only user/assistant)
                if item["role"] in ["user", "assistant"]:
                    messages.append({"role": item["role"], "content": item["content"]})

            self.logger.info(
                "Retrieved conversation history",
                session_id=session_id,
                message_count=len(messages),
            )

            # Apply summarization if needed
            if len(messages) > self.summarization_trigger:
                messages = self._summarize_history(messages)

            # Limit to max history
            return messages[-self.max_history :]

        except ClientError as e:
            self.logger.error(
                "Failed to retrieve conversation history",
                session_id=session_id,
                error=str(e),
            )
            raise

    def _summarize_history(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Summarize conversation history to compress long conversations.

        Args:
            messages: Full conversation history

        Returns:
            Summarized conversation with recent messages preserved
        """
        if len(messages) <= self.summarization_trigger:
            return messages

        # Keep recent messages (last 10)
        recent_messages = messages[-10:]

        # Summarize older messages
        older_messages = messages[:-10]

        # Create summary message
        summary_content = (
            "Previous conversation summary:\n"
            f"The conversation started with {len(older_messages)} messages. "
            "Key topics discussed: "
        )

        # Extract key information from older messages
        user_messages = [m for m in older_messages if m["role"] == "user"]
        if user_messages:
            first_user_msg = user_messages[0]["content"][:100]
            summary_content += f"User initially asked: {first_user_msg}... "

        summary_message = {"role": "assistant", "content": summary_content}

        self.logger.info(
            "Conversation summarized",
            original_count=len(messages),
            summarized_count=len(recent_messages) + 1,
        )

        # Return summary + recent messages
        return [summary_message] + recent_messages

    def create_session_id(self) -> str:
        """
        Create a new session ID.

        Returns:
            UUID session identifier
        """
        return str(uuid.uuid4())

"""
Message models for WebSocket communication.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class MessageRole(str, Enum):
    """Message role types."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """A single message in a conversation."""

    message_id: str = Field(..., description="Unique message identifier")
    session_id: str = Field(..., description="Session/conversation identifier")
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content", min_length=1, max_length=10000)
    timestamp: datetime = Field(..., description="Message timestamp")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate message content."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message content cannot be empty")
        return stripped


class SendMessageRequest(BaseModel):
    """Request to send a message."""

    message: str = Field(..., description="User message", min_length=1, max_length=5000)
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate and sanitize message."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message cannot be empty")

        # Check for suspicious patterns
        suspicious_patterns = ["<script", "javascript:", "onerror=", "onclick="]
        lower_message = stripped.lower()
        for pattern in suspicious_patterns:
            if pattern in lower_message:
                raise ValueError(f"Message contains suspicious pattern: {pattern}")

        return stripped


class SendMessageResponse(BaseModel):
    """Response from sending a message."""

    session_id: str = Field(..., description="Session identifier")
    message_id: str = Field(..., description="Message identifier")
    content: str = Field(..., description="Response content")
    timestamp: datetime = Field(..., description="Response timestamp")


class ConnectionEvent(BaseModel):
    """WebSocket connection event."""

    connection_id: str = Field(..., description="WebSocket connection ID")
    timestamp: datetime = Field(..., description="Connection timestamp")
    event_type: str = Field(..., description="Event type: CONNECT or DISCONNECT")

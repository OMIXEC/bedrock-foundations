"""Pydantic models for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class MessageRole(str, Enum):
    """Message role types."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """WebSocket message types."""
    CHAT = "chat"
    TYPING = "typing"
    ERROR = "error"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Chat message model."""
    session_id: str = Field(..., min_length=1, max_length=128)
    message_id: str = Field(..., min_length=1, max_length=128)
    role: MessageRole
    content: str = Field(..., min_length=1, max_length=10000)
    timestamp: datetime

    @field_validator('session_id', 'message_id')
    @classmethod
    def validate_alphanumeric(cls, v: str) -> str:
        """Validate that IDs contain only alphanumeric and hyphens."""
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('ID must contain only alphanumeric characters, hyphens, and underscores')
        return v

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate message content."""
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'eval\(',
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Message contains suspicious content')

        return v.strip()


class SendMessageRequest(BaseModel):
    """WebSocket send message request."""
    action: str = Field(default="sendmessage")
    session_id: str = Field(..., min_length=1, max_length=128)
    message: str = Field(..., min_length=1, max_length=10000)

    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session ID."""
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Session ID must contain only alphanumeric characters, hyphens, and underscores')
        return v

    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message content."""
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'eval\(',
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Message contains suspicious content')

        return v.strip()


class WebSocketResponse(BaseModel):
    """WebSocket response model."""
    type: MessageType
    content: str
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConnectionRecord(BaseModel):
    """WebSocket connection record."""
    connection_id: str
    session_id: str
    connected_at: datetime
    ttl: int  # Unix timestamp for DynamoDB TTL

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConversationRecord(BaseModel):
    """Conversation message record for DynamoDB."""
    session_id: str
    message_id: str
    role: MessageRole
    content: str
    timestamp: datetime
    ttl: int  # Unix timestamp for DynamoDB TTL

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

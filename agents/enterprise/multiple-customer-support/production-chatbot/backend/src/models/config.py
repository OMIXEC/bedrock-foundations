"""
Configuration models with Pydantic validation.
"""

from typing import Optional
from pydantic import BaseModel, Field


class BedrockConfig(BaseModel):
    """Bedrock service configuration."""

    model_id: str = Field(default="anthropic.claude-sonnet-4-5-20250929-v1:0")
    region: str = Field(default="us-east-1")
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)


class DynamoDBConfig(BaseModel):
    """DynamoDB service configuration."""

    connections_table: str = Field(..., description="Connections table name")
    conversations_table: str = Field(..., description="Conversations table name")
    ttl_days: int = Field(default=30, ge=1, le=365)
    region: str = Field(default="us-east-1")


class ConversationConfig(BaseModel):
    """Conversation management configuration."""

    max_history_messages: int = Field(default=20, ge=1, le=100)
    summarization_trigger: int = Field(default=15, ge=5, le=50)
    system_prompt: str = Field(..., min_length=10)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO")
    json_format: bool = Field(default=True)


class WebSocketConfig(BaseModel):
    """WebSocket configuration."""

    connection_timeout_seconds: int = Field(default=600, ge=60, le=3600)
    max_message_size_bytes: int = Field(default=32768, ge=1024, le=131072)


class Config(BaseModel):
    """Main application configuration."""

    environment: str = Field(default="dev")
    bedrock: BedrockConfig
    dynamodb: DynamoDBConfig
    conversation: ConversationConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    websocket: WebSocketConfig = Field(default_factory=WebSocketConfig)

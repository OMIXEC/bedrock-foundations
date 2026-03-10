"""Configuration loader with Pydantic validation."""

import os
from functools import lru_cache
from typing import Optional
import yaml
from pydantic import BaseModel, Field


class BedrockConfig(BaseModel):
    """Bedrock configuration."""
    model_id: str = Field(default="anthropic.claude-sonnet-4-5-20250929-v1:0")
    region: str = Field(default="us-east-1")
    max_tokens: int = Field(default=4096, ge=1, le=200000)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)


class DynamoDBConfig(BaseModel):
    """DynamoDB configuration."""
    connections_table: str
    conversations_table: str
    ttl_days: int = Field(default=30, ge=1)
    region: str = Field(default="us-east-1")


class ConversationConfig(BaseModel):
    """Conversation configuration."""
    max_history_messages: int = Field(default=20, ge=1)
    summarization_trigger: int = Field(default=15, ge=1)
    system_prompt: str


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO")
    json_format: bool = Field(default=True)


class WebSocketConfig(BaseModel):
    """WebSocket configuration."""
    connection_timeout_seconds: int = Field(default=600, ge=60)
    max_message_size_bytes: int = Field(default=32768, ge=1024)


class AppConfig(BaseModel):
    """Application configuration."""
    environment: str = Field(default="dev")
    bedrock: BedrockConfig
    dynamodb: DynamoDBConfig
    conversation: ConversationConfig
    logging: LoggingConfig
    websocket: WebSocketConfig


@lru_cache(maxsize=1)
def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from YAML file with environment overrides.

    Args:
        config_path: Path to config YAML file. Defaults to config.yaml in parent directory.

    Returns:
        Validated AppConfig instance.

    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If config validation fails.
    """
    if config_path is None:
        # Default to config.yaml in backend directory
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config.yaml"
        )

    # Load YAML
    with open(config_path, 'r') as f:
        config_dict = yaml.safe_load(f)

    # Apply environment variable overrides
    env = os.getenv('ENVIRONMENT')
    if env:
        config_dict['environment'] = env

    # DynamoDB table name overrides
    connections_table = os.getenv('CONNECTIONS_TABLE')
    if connections_table:
        config_dict['dynamodb']['connections_table'] = connections_table

    conversations_table = os.getenv('CONVERSATIONS_TABLE')
    if conversations_table:
        config_dict['dynamodb']['conversations_table'] = conversations_table

    # Bedrock overrides
    model_id = os.getenv('BEDROCK_MODEL_ID')
    if model_id:
        config_dict['bedrock']['model_id'] = model_id

    region = os.getenv('AWS_REGION')
    if region:
        config_dict['bedrock']['region'] = region
        config_dict['dynamodb']['region'] = region

    # Validate and return
    return AppConfig(**config_dict)


def get_config() -> AppConfig:
    """Get cached configuration instance.

    Returns:
        Validated AppConfig instance.
    """
    return load_config()

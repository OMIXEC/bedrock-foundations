"""
Application Configuration with Pydantic Validation

Type-safe configuration management with validation and environment overrides.
Prevents runtime errors from invalid config values.

Usage:
    from config.settings import load_config

    config = load_config("config/app-config.yaml")
    print(config.bedrock.model_id)
    print(config.opensearch.endpoint)

Environment overrides:
    BEDROCK_MODEL_ID=claude-3-haiku config = load_config(...)
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
import yaml


class ApplicationConfig(BaseModel):
    """Application metadata"""
    name: str = Field(default="customer-support-rag", description="Application name")
    version: str = Field(default="1.0.0", description="Semantic version")
    environment: str = Field(default="dev", description="Environment: dev, staging, prod")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ["dev", "staging", "prod"]
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}, got: {v}")
        return v


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format: json or text")
    include_correlation_id: bool = Field(default=True, description="Include correlation ID in logs")


class BedrockConfig(BaseModel):
    """Bedrock API configuration"""
    model_id: str = Field(default="anthropic.claude-sonnet-4-5-20250929-v1:0", description="Bedrock model ID")
    max_tokens: int = Field(default=1000, ge=1, le=4096, description="Max tokens to generate")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Sampling temperature")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="API timeout")
    region: str = Field(default="us-east-1", description="AWS region")


class RAGConfig(BaseModel):
    """RAG configuration"""
    chunk_size: int = Field(default=512, ge=100, le=2048, description="Chunk size in tokens")
    chunk_overlap: int = Field(default=102, ge=0, le=512, description="Chunk overlap in tokens")
    top_k_results: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")
    similarity_threshold: float = Field(default=0.75, ge=0.0, le=1.0, description="Minimum similarity score")


class OpenSearchConfig(BaseModel):
    """OpenSearch configuration"""
    endpoint: str = Field(..., description="OpenSearch endpoint URL")
    index_name: str = Field(default="customer-support-docs", description="Index name")
    vector_store_type: str = Field(default="opensearch", description="Vector store type")


class LambdaConfig(BaseModel):
    """Lambda configuration"""
    memory_size: int = Field(default=512, description="Lambda memory in MB (higher for throughput)")
    timeout: int = Field(default=30, description="Lambda timeout in seconds")


class AppConfig(BaseSettings):
    """Root configuration model"""
    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    bedrock: BedrockConfig = Field(default_factory=BedrockConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    opensearch: OpenSearchConfig
    lambda_config: LambdaConfig = Field(default_factory=LambdaConfig)

    class Config:
        env_prefix = ""
        env_nested_delimiter = "_"


def load_config(config_path: str) -> AppConfig:
    """
    Load and validate configuration from YAML file

    Args:
        config_path: Path to YAML config file

    Returns:
        Validated AppConfig object

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is invalid
        pydantic.ValidationError: If config values are invalid
    """
    with open(config_path, "r") as f:
        config_dict = yaml.safe_load(f)

    # Pydantic validates on initialization
    return AppConfig(**config_dict)

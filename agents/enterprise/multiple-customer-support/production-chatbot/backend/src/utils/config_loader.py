"""
Configuration loader with YAML and environment variable support.
"""

import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from ..models.config import Config


def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from YAML file with environment variable overrides.

    Args:
        config_path: Path to config.yaml file. Defaults to ../config.yaml

    Returns:
        Validated Config object

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValidationError: If config validation fails
    """
    if config_path is None:
        # Default to config.yaml in backend directory
        backend_dir = Path(__file__).parent.parent.parent
        config_path = str(backend_dir / "config.yaml")

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    # Environment variable overrides
    env = os.environ.get("ENVIRONMENT", config_data.get("environment", "dev"))
    config_data["environment"] = env

    # Override DynamoDB table names from environment
    if "CONNECTIONS_TABLE" in os.environ:
        config_data["dynamodb"]["connections_table"] = os.environ["CONNECTIONS_TABLE"]

    if "CONVERSATIONS_TABLE" in os.environ:
        config_data["dynamodb"]["conversations_table"] = os.environ[
            "CONVERSATIONS_TABLE"
        ]

    # Override Bedrock region from environment
    if "AWS_REGION" in os.environ:
        config_data["bedrock"]["region"] = os.environ["AWS_REGION"]
        config_data["dynamodb"]["region"] = os.environ["AWS_REGION"]

    try:
        return Config(**config_data)
    except ValidationError as e:
        raise ValidationError(f"Config validation failed: {e}") from e

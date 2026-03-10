"""
AWS Secrets Manager Integration

Secure secrets management with caching for Lambda performance.
NEVER store secrets in environment variables, config files, or logs.

Usage in Lambda handler:
    from utils.secrets import get_secrets

    def lambda_handler(event, context):
        secrets = get_secrets("customer-support-rag/prod/api-keys")
        opensearch_password = secrets["OPENSEARCH_PASSWORD"]

Cache behavior:
- Secrets are cached in Lambda container memory (@lru_cache)
- Cache persists across invocations in same container (5-15 min typical)
- New container = new cache fetch
- Call clear_secrets_cache() to force refresh (e.g., after rotation)

Security best practices:
1. NEVER log secret values
2. NEVER store secrets in Lambda environment variables
3. NEVER put secrets in config files or YAML
4. NEVER commit secrets to git
5. Use IAM roles for Lambda - grant secretsmanager:GetSecretValue permission
6. Rotate secrets regularly (30-90 days)
7. Use separate secrets per environment (dev/staging/prod)

Cost:
- $0.40 per secret per month
- $0.05 per 10,000 API calls
- Cache reduces API calls to ~1 per Lambda container
"""

import json
import logging
from functools import lru_cache
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@lru_cache(maxsize=4)
def get_secrets(secret_name: str, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Retrieve secrets from AWS Secrets Manager with caching

    Cached for Lambda container lifetime (typically 5-15 minutes).
    Use clear_secrets_cache() to force refresh after rotation.

    Args:
        secret_name: Name or ARN of the secret
        region: AWS region (default: us-east-1)

    Returns:
        Dictionary of secret key-value pairs

    Raises:
        ClientError: If secret not found or access denied
        json.JSONDecodeError: If secret value is not valid JSON
    """
    # Create Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager",
        region_name=region
    )

    try:
        # Retrieve secret value
        response = client.get_secret_value(SecretId=secret_name)

        # Parse JSON secret string
        if "SecretString" in response:
            secret = json.loads(response["SecretString"])
            logger.info(f"Successfully retrieved secret: {secret_name}")
            return secret
        else:
            # Binary secrets not supported in this helper
            raise ValueError(f"Secret {secret_name} is binary, not JSON string")

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "ResourceNotFoundException":
            logger.error(f"Secret not found: {secret_name}")
            raise
        elif error_code == "InvalidRequestException":
            logger.error(f"Invalid request for secret: {secret_name}")
            raise
        elif error_code == "InvalidParameterException":
            logger.error(f"Invalid parameter for secret: {secret_name}")
            raise
        elif error_code == "DecryptionFailure":
            logger.error(f"Cannot decrypt secret: {secret_name}")
            raise
        elif error_code == "InternalServiceError":
            logger.error(f"Secrets Manager internal error for: {secret_name}")
            raise
        else:
            logger.error(f"Unknown error retrieving secret {secret_name}: {error_code}")
            raise


def clear_secrets_cache() -> None:
    """
    Clear secrets cache - forces fresh retrieval on next get_secrets() call

    Use cases:
    1. After secret rotation (Lambda will get new value)
    2. Testing (clear cache between tests)
    3. Manual refresh (if you suspect stale cache)

    Note: This only clears cache in the current Lambda container.
    Other containers will retain their cache until they expire.
    """
    get_secrets.cache_clear()
    logger.info("Secrets cache cleared")

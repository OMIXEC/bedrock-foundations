"""
WebSocket connect handler.

Triggered when client establishes WebSocket connection.
"""

import json
from typing import Any, Dict

from ..services.conversation import ConversationService
from ..utils.config_loader import load_config
from ..utils.logger import get_logger


# Load config once at module level (Lambda container reuse)
config = load_config()
logger = get_logger(__name__, config.logging.level)
conversation_service = ConversationService(config)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket connection.

    Args:
        event: API Gateway WebSocket event
        context: Lambda context

    Returns:
        API Gateway response
    """
    connection_id = event["requestContext"]["connectionId"]
    correlation_id = event["requestContext"].get("requestId", "unknown")

    logger.info(
        "WebSocket connection initiated",
        correlation_id=correlation_id,
        connection_id=connection_id,
    )

    try:
        # Store connection in DynamoDB
        conversation_service.store_connection(connection_id)

        logger.info(
            "WebSocket connection established",
            correlation_id=correlation_id,
            connection_id=connection_id,
        )

        return {"statusCode": 200, "body": json.dumps({"message": "Connected"})}

    except Exception as e:
        logger.error(
            "Failed to establish connection",
            correlation_id=correlation_id,
            connection_id=connection_id,
            error=str(e),
        )

        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Failed to connect"}),
        }

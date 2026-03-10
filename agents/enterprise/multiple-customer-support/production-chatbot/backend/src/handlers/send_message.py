"""
WebSocket send_message handler with Bedrock streaming.

Receives user messages via WebSocket, streams Claude responses in real-time.
"""

import json
from typing import Any, Dict

import boto3
from pydantic import ValidationError

from ..models.messages import SendMessageRequest, MessageRole
from ..services.conversation import ConversationService
from ..services.bedrock_client import BedrockClient
from ..utils.config_loader import load_config
from ..utils.logger import get_logger


# Load config once at module level (Lambda container reuse)
config = load_config()
logger = get_logger(__name__, config.logging.level)
conversation_service = ConversationService(config)
bedrock_client = BedrockClient(config)

# WebSocket API Gateway Management API client
# Will be initialized per request with endpoint from event
apigateway_client = None


def _get_websocket_client(event: Dict[str, Any]):
    """Get WebSocket API Gateway Management API client."""
    domain = event["requestContext"]["domainName"]
    stage = event["requestContext"]["stage"]
    endpoint_url = f"https://{domain}/{stage}"

    return boto3.client("apigatewaymanagementapi", endpoint_url=endpoint_url)


def _send_to_connection(client, connection_id: str, data: Dict[str, Any]) -> None:
    """
    Send data to WebSocket connection.

    Args:
        client: API Gateway Management API client
        connection_id: WebSocket connection ID
        data: Data to send
    """
    try:
        client.post_to_connection(
            ConnectionId=connection_id, Data=json.dumps(data).encode("utf-8")
        )
    except client.exceptions.GoneException:
        logger.warning("Connection gone", connection_id=connection_id)
        # Clean up stale connection
        conversation_service.remove_connection(connection_id)
    except Exception as e:
        logger.error(
            "Failed to send to connection", connection_id=connection_id, error=str(e)
        )
        raise


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle WebSocket sendMessage route.

    Receives user message, retrieves conversation history, streams Claude response
    via WebSocket, and stores messages in DynamoDB.

    Args:
        event: API Gateway WebSocket event with message body
        context: Lambda context

    Returns:
        API Gateway response
    """
    connection_id = event["requestContext"]["connectionId"]
    correlation_id = event["requestContext"].get("requestId", "unknown")

    logger.info(
        "Message received",
        correlation_id=correlation_id,
        connection_id=connection_id,
    )

    # Initialize WebSocket client for this request
    ws_client = _get_websocket_client(event)

    try:
        # Parse request body
        body = json.loads(event.get("body", "{}"))

        # Validate with Pydantic
        try:
            request = SendMessageRequest(**body)
        except ValidationError as e:
            logger.warning(
                "Invalid request",
                correlation_id=correlation_id,
                validation_errors=e.errors(),
            )
            _send_to_connection(
                ws_client,
                connection_id,
                {"type": "error", "message": "Invalid request format"},
            )
            return {"statusCode": 400, "body": json.dumps({"message": "Invalid request"})}

        # Get or create session ID
        session_id = request.session_id or conversation_service.create_session_id()

        logger.info(
            "Processing message",
            correlation_id=correlation_id,
            session_id=session_id,
            message_length=len(request.message),
        )

        # Store user message
        user_message = conversation_service.store_message(
            session_id=session_id, role=MessageRole.USER, content=request.message
        )

        # Send acknowledgment
        _send_to_connection(
            ws_client,
            connection_id,
            {
                "type": "message_received",
                "session_id": session_id,
                "message_id": user_message.message_id,
            },
        )

        # Get conversation history
        history = conversation_service.get_conversation_history(session_id)

        # Add current user message to history
        history.append({"role": "user", "content": request.message})

        # Stream Claude response
        logger.info(
            "Starting Bedrock stream",
            correlation_id=correlation_id,
            session_id=session_id,
        )

        full_response = ""

        # Send stream start event
        _send_to_connection(
            ws_client,
            connection_id,
            {"type": "stream_start", "session_id": session_id},
        )

        # Stream response chunks
        for chunk in bedrock_client.converse_stream(
            messages=history, system_prompt=config.conversation.system_prompt
        ):
            full_response += chunk

            # Send chunk to client
            _send_to_connection(
                ws_client,
                connection_id,
                {"type": "stream_chunk", "content": chunk},
            )

        # Send stream end event
        _send_to_connection(
            ws_client,
            connection_id,
            {"type": "stream_end", "session_id": session_id},
        )

        # Store assistant response
        assistant_message = conversation_service.store_message(
            session_id=session_id, role=MessageRole.ASSISTANT, content=full_response
        )

        logger.info(
            "Message processed successfully",
            correlation_id=correlation_id,
            session_id=session_id,
            response_length=len(full_response),
        )

        return {"statusCode": 200, "body": json.dumps({"message": "Message processed"})}

    except ValidationError as e:
        logger.error(
            "Validation error",
            correlation_id=correlation_id,
            error=str(e),
        )
        _send_to_connection(
            ws_client,
            connection_id,
            {"type": "error", "message": "Validation failed"},
        )
        return {"statusCode": 400, "body": json.dumps({"message": "Validation error"})}

    except Exception as e:
        logger.error(
            "Message processing failed",
            correlation_id=correlation_id,
            error=str(e),
        )

        # Try to send error to client
        try:
            _send_to_connection(
                ws_client,
                connection_id,
                {"type": "error", "message": "Processing failed"},
            )
        except Exception:
            pass  # Connection might be gone

        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Internal server error"}),
        }

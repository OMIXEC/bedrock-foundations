"""REST API handler for chat with streaming support."""

import json
from typing import Any, Dict
from pydantic import ValidationError

from ..models.messages import SendMessageRequest, MessageRole
from ..services.conversation import ConversationService
from ..services.bedrock_client import BedrockClient
from ..utils.config_loader import load_config
from ..utils.logger import get_logger

config = load_config()
logger = get_logger(__name__, config.logging.level)
conversation_service = ConversationService(config)
bedrock_client = BedrockClient(config)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """REST API handler for chat messages.
    
    POST /chat - Send message and get response
    GET /chat/{session_id}/history - Get conversation history
    """
    http_method = event.get("httpMethod", "")
    path = event.get("path", "")
    correlation_id = event.get("requestContext", {}).get("requestId", "unknown")
    
    logger.info("REST request", method=http_method, path=path, correlation_id=correlation_id)
    
    try:
        if http_method == "POST" and path == "/chat":
            return handle_chat(event, correlation_id)
        elif http_method == "GET" and "/history" in path:
            return handle_history(event, correlation_id)
        else:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Not found"})
            }
    except Exception as e:
        logger.error("Request failed", error=str(e), correlation_id=correlation_id)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"})
        }


def handle_chat(event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
    """Handle chat message."""
    try:
        body = json.loads(event.get("body", "{}"))
        request = SendMessageRequest(**body)
    except ValidationError as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid request", "details": e.errors()})
        }
    
    session_id = request.session_id or conversation_service.create_session_id()
    
    # Store user message
    conversation_service.store_message(
        session_id=session_id,
        role=MessageRole.USER,
        content=request.message
    )
    
    # Get history
    history = conversation_service.get_conversation_history(session_id)
    history.append({"role": "user", "content": request.message})
    
    # Get response (non-streaming for REST)
    response_text = bedrock_client.converse(
        messages=history,
        system_prompt=config.conversation.system_prompt
    )
    
    # Store assistant response
    conversation_service.store_message(
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=response_text
    )
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "session_id": session_id,
            "response": response_text
        })
    }


def handle_history(event: Dict[str, Any], correlation_id: str) -> Dict[str, Any]:
    """Get conversation history."""
    path_params = event.get("pathParameters", {})
    session_id = path_params.get("session_id")
    
    if not session_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "session_id required"})
        }
    
    history = conversation_service.get_conversation_history(session_id)
    
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "session_id": session_id,
            "messages": history
        })
    }

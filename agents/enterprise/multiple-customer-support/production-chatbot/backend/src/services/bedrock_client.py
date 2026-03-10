"""
Bedrock client for streaming Claude responses.
"""

from typing import Dict, Iterator, List, Optional

import boto3
from botocore.exceptions import ClientError

from ..models.config import Config
from ..utils.logger import get_logger


class BedrockClient:
    """
    AWS Bedrock client for streaming Claude Sonnet 4.5 responses.

    Uses converse_stream API for real-time token streaming via WebSocket.
    """

    def __init__(self, config: Config, boto_session=None):
        """
        Initialize Bedrock client.

        Args:
            config: Application configuration
            boto_session: Optional boto3 session for custom credentials
        """
        self.config = config
        self.logger = get_logger(__name__, config.logging.level)

        if boto_session:
            self.client = boto_session.client(
                "bedrock-runtime", region_name=config.bedrock.region
            )
        else:
            self.client = boto3.client(
                "bedrock-runtime", region_name=config.bedrock.region
            )

        self.model_id = config.bedrock.model_id
        self.max_tokens = config.bedrock.max_tokens
        self.temperature = config.bedrock.temperature

    def converse_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> Iterator[str]:
        """
        Stream Claude response using converse_stream API.

        Args:
            messages: Conversation history in format [{"role": "user", "content": "..."}]
            system_prompt: Optional system prompt

        Yields:
            Text chunks as they arrive from Claude

        Raises:
            ClientError: If Bedrock API call fails
        """
        try:
            # Prepare request
            request_params = {
                "modelId": self.model_id,
                "messages": messages,
                "inferenceConfig": {
                    "maxTokens": self.max_tokens,
                    "temperature": self.temperature,
                },
            }

            if system_prompt:
                request_params["system"] = [{"text": system_prompt}]

            self.logger.info(
                "Starting Bedrock converse_stream",
                model_id=self.model_id,
                message_count=len(messages),
            )

            # Call converse_stream
            response = self.client.converse_stream(**request_params)

            # Stream response chunks
            chunk_count = 0
            total_chars = 0

            for event in response.get("stream", []):
                if "contentBlockDelta" in event:
                    delta = event["contentBlockDelta"]["delta"]
                    if "text" in delta:
                        chunk = delta["text"]
                        chunk_count += 1
                        total_chars += len(chunk)
                        yield chunk

                elif "messageStop" in event:
                    stop_reason = event["messageStop"].get("stopReason", "unknown")
                    self.logger.info(
                        "Stream completed",
                        stop_reason=stop_reason,
                        chunk_count=chunk_count,
                        total_chars=total_chars,
                    )

                elif "metadata" in event:
                    metadata = event["metadata"]
                    usage = metadata.get("usage", {})
                    self.logger.info(
                        "Stream metadata",
                        input_tokens=usage.get("inputTokens", 0),
                        output_tokens=usage.get("outputTokens", 0),
                    )

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            self.logger.error(
                "Bedrock converse_stream failed",
                error_code=error_code,
                error_message=error_message,
            )

            # Handle specific error cases
            if error_code == "ValidationException":
                raise ValueError(f"Invalid request: {error_message}") from e
            elif error_code == "ThrottlingException":
                raise RuntimeError("Bedrock API throttled, please retry") from e
            else:
                raise RuntimeError(f"Bedrock error: {error_message}") from e

    def converse(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        Non-streaming converse API for testing/summarization.

        Args:
            messages: Conversation history
            system_prompt: Optional system prompt

        Returns:
            Complete response text

        Raises:
            ClientError: If Bedrock API call fails
        """
        try:
            request_params = {
                "modelId": self.model_id,
                "messages": messages,
                "inferenceConfig": {
                    "maxTokens": self.max_tokens,
                    "temperature": self.temperature,
                },
            }

            if system_prompt:
                request_params["system"] = [{"text": system_prompt}]

            response = self.client.converse(**request_params)

            # Extract text from response
            content = response["output"]["message"]["content"]
            text = content[0]["text"] if content else ""

            self.logger.info(
                "Bedrock converse completed",
                input_tokens=response.get("usage", {}).get("inputTokens", 0),
                output_tokens=response.get("usage", {}).get("outputTokens", 0),
            )

            return text

        except ClientError as e:
            error_message = e.response.get("Error", {}).get("Message", str(e))
            self.logger.error("Bedrock converse failed", error_message=error_message)
            raise RuntimeError(f"Bedrock error: {error_message}") from e

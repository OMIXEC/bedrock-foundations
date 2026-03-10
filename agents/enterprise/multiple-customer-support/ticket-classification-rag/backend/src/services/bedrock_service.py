"""
Bedrock Service with Guardrails Integration

Provides secure Bedrock API access with optional Guardrails for:
- Prompt attack detection
- Contextual grounding validation
- Content filtering
"""

import json
import boto3
from typing import Dict, Any, Optional


class BedrockService:
    """Bedrock API client with guardrails support"""

    def __init__(self, region: str = "us-east-1", guardrail_id: Optional[str] = None, guardrail_version: str = "DRAFT"):
        """
        Initialize Bedrock service

        Args:
            region: AWS region
            guardrail_id: Guardrail ARN (optional)
            guardrail_version: Guardrail version
        """
        self.client = boto3.client('bedrock-runtime', region_name=region)
        self.guardrail_id = guardrail_id
        self.guardrail_version = guardrail_version

    def invoke_model(
        self,
        model_id: str,
        messages: list,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invoke Bedrock model with optional guardrails

        Args:
            model_id: Bedrock model ID
            messages: List of message dicts
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            Response dictionary with answer and metadata
        """

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if system_prompt:
            request_body["system"] = system_prompt

        # Add guardrails if configured
        kwargs = {
            "modelId": model_id,
            "contentType": "application/json",
            "accept": "application/json",
            "body": json.dumps(request_body)
        }

        if self.guardrail_id:
            kwargs["guardrailIdentifier"] = self.guardrail_id
            kwargs["guardrailVersion"] = self.guardrail_version

        response = self.client.invoke_model(**kwargs)

        response_body = json.loads(response['body'].read())

        return {
            "answer": response_body['content'][0]['text'],
            "stop_reason": response_body.get('stop_reason', 'unknown'),
            "usage": response_body.get('usage', {})
        }

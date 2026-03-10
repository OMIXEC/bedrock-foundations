"""
Ticket Classification Service

Classifies customer support queries into predefined categories using Claude Sonnet 4.5.
This enables category-aware RAG retrieval and routing to specialized support teams.

Categories:
- BILLING: Payment, invoice, subscription, pricing inquiries
- TECHNICAL: Bugs, errors, crashes, setup, integration issues
- ACCOUNT: Login, password, profile, permissions management
- GENERAL: Product questions, feature requests, other inquiries
"""

import json
import re
from enum import Enum
from typing import Dict


class TicketCategory(str, Enum):
    """Customer support ticket categories"""
    BILLING = "BILLING"
    TECHNICAL = "TECHNICAL"
    ACCOUNT = "ACCOUNT"
    GENERAL = "GENERAL"


def classify_ticket(query: str, bedrock_client) -> TicketCategory:
    """
    Classify customer support query using Claude Sonnet 4.5

    Args:
        query: Customer query text
        bedrock_client: boto3 bedrock-runtime client

    Returns:
        TicketCategory enum value

    Uses temperature 0.0 for deterministic classification.
    Fallback to GENERAL if classification fails.
    """

    classification_prompt = f"""Classify this customer support query into exactly one category:

BILLING - Payment, invoice, subscription, pricing, refund, cancellation
TECHNICAL - Bug, error, crash, setup, integration, API issues, sync problems
ACCOUNT - Login, password, profile, permissions, team management, authentication
GENERAL - Product features, questions, how-to, other inquiries

Query: {query}

Respond with ONLY the category name (BILLING, TECHNICAL, ACCOUNT, or GENERAL). No explanation."""

    try:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {
                    "role": "user",
                    "content": classification_prompt
                }
            ],
            "max_tokens": 50,
            "temperature": 0.0  # Deterministic classification
        }

        response = bedrock_client.invoke_model(
            modelId='anthropic.claude-sonnet-4-5-20250929-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )

        response_body = json.loads(response['body'].read())
        category_text = response_body['content'][0]['text'].strip().upper()

        # Extract category from response (handle potential extra text)
        if 'BILLING' in category_text:
            return TicketCategory.BILLING
        elif 'TECHNICAL' in category_text:
            return TicketCategory.TECHNICAL
        elif 'ACCOUNT' in category_text:
            return TicketCategory.ACCOUNT
        else:
            return TicketCategory.GENERAL

    except Exception as e:
        # Fallback to GENERAL on error
        print(f"Classification error: {str(e)}")
        return TicketCategory.GENERAL


def get_category_context(category: TicketCategory) -> str:
    """
    Get category-specific context to add to RAG prompt

    Args:
        category: Classified ticket category

    Returns:
        Additional prompt context for the category
    """

    context_map: Dict[TicketCategory, str] = {
        TicketCategory.BILLING: "Focus on pricing, payment methods, subscriptions, refunds, and billing policies.",
        TicketCategory.TECHNICAL: "Focus on troubleshooting steps, error messages, API documentation, and technical solutions.",
        TicketCategory.ACCOUNT: "Focus on account management, authentication, permissions, and user settings.",
        TicketCategory.GENERAL: "Provide comprehensive information about product features and capabilities."
    }

    return context_map.get(category, "")

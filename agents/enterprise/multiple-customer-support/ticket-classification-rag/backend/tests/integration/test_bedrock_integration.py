"""
Integration tests for Bedrock API

Tests real Bedrock API calls with Claude Sonnet 4.5.
"""

import pytest
import json


@pytest.mark.integration
def test_real_claude_classification(real_bedrock_client):
    """Test real Claude API for ticket classification"""
    from src.services.ticket_classifier import classify_ticket, TicketCategory

    # Test billing query
    billing_query = "How do I cancel my subscription?"
    category = classify_ticket(billing_query, real_bedrock_client)
    assert category == TicketCategory.BILLING

    # Test technical query
    technical_query = "My sync is failing with error 500"
    category = classify_ticket(technical_query, real_bedrock_client)
    assert category == TicketCategory.TECHNICAL


@pytest.mark.integration
def test_real_bedrock_answer_generation(real_bedrock_client):
    """Test real Bedrock API for answer generation"""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "messages": [
            {
                "role": "user",
                "content": "What is CloudSync Pro?"
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }

    response = real_bedrock_client.invoke_model(
        modelId='anthropic.claude-sonnet-4-5-20250929-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps(request_body)
    )

    response_body = json.loads(response['body'].read())
    answer = response_body['content'][0]['text']

    assert len(answer) > 10
    assert response_body['stop_reason'] in ['end_turn', 'max_tokens']

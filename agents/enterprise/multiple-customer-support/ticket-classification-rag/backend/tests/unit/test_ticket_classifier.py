"""
Unit tests for ticket classification service

Tests all 4 categories with mocked Bedrock client.
"""

import pytest
import json
from unittest.mock import Mock, MagicMock
from src.services.ticket_classifier import (
    classify_ticket,
    get_category_context,
    TicketCategory
)


@pytest.mark.unit
def test_classify_billing_query():
    """Test classification of billing-related query"""
    # Mock Bedrock client
    mock_client = Mock()
    mock_response = {
        'body': MagicMock()
    }
    mock_response['body'].read.return_value = json.dumps({
        'content': [{'text': 'BILLING'}]
    }).encode()
    mock_client.invoke_model.return_value = mock_response

    query = "How do I update my credit card?"
    category = classify_ticket(query, mock_client)

    assert category == TicketCategory.BILLING
    assert mock_client.invoke_model.called


@pytest.mark.unit
def test_classify_technical_query():
    """Test classification of technical support query"""
    mock_client = Mock()
    mock_response = {
        'body': MagicMock()
    }
    mock_response['body'].read.return_value = json.dumps({
        'content': [{'text': 'TECHNICAL'}]
    }).encode()
    mock_client.invoke_model.return_value = mock_response

    query = "My sync keeps failing with error 500"
    category = classify_ticket(query, mock_client)

    assert category == TicketCategory.TECHNICAL


@pytest.mark.unit
def test_classify_account_query():
    """Test classification of account management query"""
    mock_client = Mock()
    mock_response = {
        'body': MagicMock()
    }
    mock_response['body'].read.return_value = json.dumps({
        'content': [{'text': 'ACCOUNT'}]
    }).encode()
    mock_client.invoke_model.return_value = mock_response

    query = "I forgot my password"
    category = classify_ticket(query, mock_client)

    assert category == TicketCategory.ACCOUNT


@pytest.mark.unit
def test_classify_general_query():
    """Test classification of general product query"""
    mock_client = Mock()
    mock_response = {
        'body': MagicMock()
    }
    mock_response['body'].read.return_value = json.dumps({
        'content': [{'text': 'GENERAL'}]
    }).encode()
    mock_client.invoke_model.return_value = mock_response

    query = "What features does CloudSync offer?"
    category = classify_ticket(query, mock_client)

    assert category == TicketCategory.GENERAL


@pytest.mark.unit
def test_classify_fallback_on_error():
    """Test fallback to GENERAL category on classification error"""
    mock_client = Mock()
    mock_client.invoke_model.side_effect = Exception("API error")

    query = "Some query that causes an error"
    category = classify_ticket(query, mock_client)

    # Should fallback to GENERAL on error
    assert category == TicketCategory.GENERAL


@pytest.mark.unit
def test_get_category_context():
    """Test category-specific context retrieval"""
    billing_context = get_category_context(TicketCategory.BILLING)
    assert "pricing" in billing_context.lower() or "payment" in billing_context.lower()

    technical_context = get_category_context(TicketCategory.TECHNICAL)
    assert "troubleshoot" in technical_context.lower() or "error" in technical_context.lower()

    account_context = get_category_context(TicketCategory.ACCOUNT)
    assert "account" in account_context.lower() or "authentication" in account_context.lower()

    general_context = get_category_context(TicketCategory.GENERAL)
    assert "feature" in general_context.lower() or "product" in general_context.lower()


@pytest.mark.unit
def test_classification_uses_deterministic_temperature():
    """Test that classification uses temperature 0.0 for deterministic results"""
    mock_client = Mock()
    mock_response = {
        'body': MagicMock()
    }
    mock_response['body'].read.return_value = json.dumps({
        'content': [{'text': 'BILLING'}]
    }).encode()
    mock_client.invoke_model.return_value = mock_response

    query = "Billing question"
    classify_ticket(query, mock_client)

    # Verify temperature is 0.0 in request
    call_kwargs = mock_client.invoke_model.call_args[1]
    body = json.loads(call_kwargs['body'])
    assert body['temperature'] == 0.0

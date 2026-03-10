"""
Query Handler - Lambda Entry Point

Orchestrates ticket classification, RAG retrieval, and answer generation.
Logs category distribution metrics for monitoring.
"""

import json
import boto3
from typing import Dict, Any
from ..models.request import QueryRequest
from ..models.response import QueryResponse, SourceDocument
from ..services.ticket_classifier import classify_ticket
from ..services.rag_service import CustomerSupportRAGService
from ..utils.logger import StructuredLogger, extract_correlation_id


# Initialize logger
logger = StructuredLogger(service_name="customer-support-rag")

# Initialize AWS clients (outside handler for Lambda container reuse)
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for customer support queries

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """

    # Extract correlation ID for tracing
    correlation_id = extract_correlation_id(event)
    log = logger.with_correlation_id(correlation_id)

    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        request = QueryRequest(**body)

        log.info("Query received",
                 query_length=len(request.query),
                 max_results=request.max_results,
                 session_id=request.session_id)

        # Step 1: Classify ticket category
        category = classify_ticket(request.query, bedrock_client)

        log.info("Ticket classified",
                 category=category.value,
                 query_preview=request.query[:50])

        # Step 2: Initialize RAG service
        # In production, get these from environment variables or Secrets Manager
        opensearch_endpoint = "your-opensearch-endpoint.us-east-1.aoss.amazonaws.com"
        opensearch_index = "customer-support-docs"

        rag_service = CustomerSupportRAGService(
            bedrock_client=bedrock_client,
            opensearch_endpoint=opensearch_endpoint,
            opensearch_index=opensearch_index
        )

        # Step 3: Perform hybrid search with category awareness
        context_chunks = rag_service.hybrid_search(
            query=request.query,
            category=category,
            top_k=request.max_results
        )

        log.info("Context retrieved",
                 num_chunks=len(context_chunks),
                 category=category.value)

        # Step 4: Generate answer
        result = rag_service.generate_answer(
            query=request.query,
            context_chunks=context_chunks,
            category=category
        )

        # Step 5: Build response
        response = QueryResponse(
            answer=result["answer"],
            sources=[
                SourceDocument(content=src["content"], source=src["source"])
                for src in result["sources"]
            ],
            category=category.value,
            correlation_id=correlation_id,
            suggested_actions=_get_suggested_actions(category)
        )

        log.info("Query completed",
                 category=category.value,
                 answer_length=len(result["answer"]),
                 num_sources=len(result["sources"]))

        # Log category distribution metric (for monitoring)
        log.info("Category distribution metric",
                 metric_name="TicketCategoryCount",
                 category=category.value,
                 count=1)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "X-Correlation-Id": correlation_id
            },
            "body": response.model_dump_json()
        }

    except ValueError as e:
        log.error("Validation error",
                  error=str(e),
                  error_type="ValidationError")

        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Invalid request", "detail": str(e)})
        }

    except Exception as e:
        log.error("Query failed",
                  error=str(e),
                  error_type=type(e).__name__)

        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"})
        }


def _get_suggested_actions(category) -> list:
    """Get category-specific suggested actions"""

    actions_map = {
        "BILLING": [
            "Check your billing dashboard for detailed invoice",
            "Contact billing support if you need a refund"
        ],
        "TECHNICAL": [
            "Check our status page for known issues",
            "Try the troubleshooting steps above",
            "Contact technical support if issue persists"
        ],
        "ACCOUNT": [
            "Review your account security settings",
            "Enable two-factor authentication for better security"
        ],
        "GENERAL": [
            "Explore our documentation for more details",
            "Contact support if you have additional questions"
        ]
    }

    return actions_map.get(category, [])

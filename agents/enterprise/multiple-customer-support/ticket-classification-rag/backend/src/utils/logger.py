"""
Structured JSON Logger for AWS Lambda + CloudWatch Logs Insights

Outputs JSON-formatted logs that CloudWatch Logs Insights can easily query.
Critical for distributed tracing, debugging, and monitoring in production.

Key features:
- ISO 8601 UTC timestamps
- Correlation ID tracking across Lambda invocations
- JSON output for CloudWatch Logs Insights queries
- Service name for multi-service architectures
- Additional context via kwargs

Usage in Lambda handler:
    from utils.logger import StructuredLogger, extract_correlation_id

    logger = StructuredLogger(service_name="customer-support-rag")

    def lambda_handler(event, context):
        correlation_id = extract_correlation_id(event)
        log = logger.with_correlation_id(correlation_id)

        log.info("Query received", query=event.get("query"))
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4


class StructuredLogger:
    """JSON structured logger for CloudWatch Logs Insights"""

    def __init__(self, service_name: str):
        """
        Initialize structured logger

        Args:
            service_name: Name of the service (e.g., "customer-support-rag")
        """
        self.service_name = service_name
        self.python_logger = logging.getLogger(service_name)
        self.python_logger.setLevel(logging.INFO)
        self._bound_correlation_id: Optional[str] = None

    def _log(self, level: str, message: str, **kwargs) -> None:
        """
        Internal log method - builds JSON log entry and outputs to stdout

        Args:
            level: Log level (INFO, WARNING, ERROR, CRITICAL)
            message: Human-readable log message
            **kwargs: Additional context to include in log entry
        """
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "level": level,
            "message": message
        }

        # Add correlation_id if bound to logger
        if self._bound_correlation_id:
            log_entry["correlation_id"] = self._bound_correlation_id

        # Add correlation_id from kwargs if provided
        if "correlation_id" in kwargs:
            log_entry["correlation_id"] = kwargs.pop("correlation_id")

        # Merge additional context
        log_entry.update(kwargs)

        # Output JSON to stdout (CloudWatch captures this)
        print(json.dumps(log_entry))

    def info(self, message: str, **kwargs) -> None:
        """Log INFO level message"""
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log WARNING level message"""
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log ERROR level message"""
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log CRITICAL level message"""
        self._log("CRITICAL", message, **kwargs)

    def with_correlation_id(self, correlation_id: str) -> "StructuredLogger":
        """
        Return a logger bound to a specific correlation_id

        All logs from the returned logger will automatically include this correlation_id.
        Critical for distributed tracing across Lambda invocations, API Gateway, Step Functions.

        Args:
            correlation_id: Unique ID to track request across services

        Returns:
            New StructuredLogger instance with bound correlation_id
        """
        bound_logger = StructuredLogger(self.service_name)
        bound_logger._bound_correlation_id = correlation_id
        return bound_logger


def extract_correlation_id(event: dict) -> str:
    """
    Extract or generate correlation_id from Lambda event

    Checks in order:
    1. API Gateway custom header (x-correlation-id)
    2. API Gateway request ID
    3. Generate new UUID

    Args:
        event: Lambda event dict (API Gateway, EventBridge, etc.)

    Returns:
        Correlation ID string
    """
    # Check API Gateway headers
    headers = event.get("headers", {})
    if headers:
        # Headers can be case-insensitive in API Gateway
        for key in ["x-correlation-id", "X-Correlation-Id", "X-CORRELATION-ID"]:
            if key in headers:
                return headers[key]

    # Fallback to API Gateway request ID
    request_context = event.get("requestContext", {})
    if request_context and "requestId" in request_context:
        return request_context["requestId"]

    # Generate new correlation ID
    return str(uuid4())

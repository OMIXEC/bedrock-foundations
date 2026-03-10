"""Structured JSON logger for CloudWatch Logs Insights."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredLogger:
    """Structured logger that outputs JSON to stdout."""

    def __init__(self, name: str, level: str = "INFO"):
        """Initialize structured logger.

        Args:
            name: Logger name (typically __name__).
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Remove existing handlers
        self.logger.handlers = []

        # Create stdout handler with JSON formatter
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(self._get_formatter())
        self.logger.addHandler(handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def _get_formatter(self) -> logging.Formatter:
        """Get JSON formatter for structured logging."""

        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_data = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }

                # Add correlation ID if present
                if hasattr(record, "correlation_id"):
                    log_data["correlation_id"] = record.correlation_id

                # Add extra fields
                if hasattr(record, "extra_fields"):
                    log_data.update(record.extra_fields)

                # Add exception info if present
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)

                return json.dumps(log_data)

        return JSONFormatter()

    def _log(
        self,
        level: str,
        message: str,
        correlation_id: Optional[str] = None,
        **extra_fields: Any
    ) -> None:
        """Internal log method.

        Args:
            level: Log level.
            message: Log message.
            correlation_id: Optional correlation ID for request tracking.
            **extra_fields: Additional fields to include in log.
        """
        # Filter out sensitive data
        filtered_fields = self._filter_sensitive_data(extra_fields)

        # Create log record
        record = self.logger.makeRecord(
            self.name,
            getattr(logging, level.upper()),
            "",
            0,
            message,
            (),
            None
        )

        if correlation_id:
            record.correlation_id = correlation_id

        if filtered_fields:
            record.extra_fields = filtered_fields

        self.logger.handle(record)

    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter sensitive data from logs.

        Args:
            data: Dictionary of data to filter.

        Returns:
            Filtered dictionary with sensitive data masked.
        """
        sensitive_keys = {
            'password', 'secret', 'token', 'api_key', 'access_key',
            'private_key', 'aws_secret_access_key', 'session_token'
        }

        filtered = {}
        for key, value in data.items():
            # Check if key contains sensitive terms
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                filtered[key] = "***REDACTED***"
            elif isinstance(value, dict):
                filtered[key] = self._filter_sensitive_data(value)
            else:
                filtered[key] = value

        return filtered

    def debug(self, message: str, correlation_id: Optional[str] = None, **extra: Any) -> None:
        """Log debug message."""
        self._log("DEBUG", message, correlation_id, **extra)

    def info(self, message: str, correlation_id: Optional[str] = None, **extra: Any) -> None:
        """Log info message."""
        self._log("INFO", message, correlation_id, **extra)

    def warning(self, message: str, correlation_id: Optional[str] = None, **extra: Any) -> None:
        """Log warning message."""
        self._log("WARNING", message, correlation_id, **extra)

    def error(self, message: str, correlation_id: Optional[str] = None, **extra: Any) -> None:
        """Log error message."""
        self._log("ERROR", message, correlation_id, **extra)

    def critical(self, message: str, correlation_id: Optional[str] = None, **extra: Any) -> None:
        """Log critical message."""
        self._log("CRITICAL", message, correlation_id, **extra)


def get_logger(name: str, level: str = "INFO") -> StructuredLogger:
    """Get or create a structured logger.

    Args:
        name: Logger name (typically __name__).
        level: Log level.

    Returns:
        StructuredLogger instance.
    """
    return StructuredLogger(name, level)

"""
Request Models with Pydantic Validation

Validates all incoming Lambda requests to prevent injection attacks
and ensure data quality.
"""

from pydantic import BaseModel, Field, field_validator
import re
from typing import Optional


class QueryRequest(BaseModel):
    """Customer support query request"""

    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Customer query text"
    )

    max_results: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of context chunks to retrieve"
    )

    session_id: Optional[str] = Field(
        default=None,
        pattern=r'^[a-zA-Z0-9_-]+$',
        description="Optional session ID for conversation tracking"
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """
        Validate query to detect potential prompt injection

        Raises:
            ValueError: If suspicious patterns detected
        """

        # Strip whitespace
        v = v.strip()

        # Detect common prompt injection patterns
        suspicious_patterns = [
            r'ignore.{0,10}(previous|above|instructions)',
            r'system.{0,10}prompt',
            r'<\|.*?\|>',  # Special tokens
            r'\\n\\n',  # Escaped newlines
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Query contains suspicious patterns")

        return v

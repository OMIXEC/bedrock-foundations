"""
Response Models

Standardized API responses with proper serialization.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class SourceDocument(BaseModel):
    """Source document metadata"""
    content: str = Field(..., description="Document content snippet")
    source: str = Field(..., description="Source file name")


class QueryResponse(BaseModel):
    """Customer support query response"""

    answer: str = Field(..., description="Generated answer")

    sources: List[SourceDocument] = Field(
        default=[],
        description="Source documents used for answer"
    )

    category: str = Field(..., description="Detected ticket category")

    correlation_id: str = Field(..., description="Request correlation ID")

    suggested_actions: Optional[List[str]] = Field(
        default=None,
        description="Suggested follow-up actions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "To cancel your CloudSync Pro subscription...",
                "sources": [
                    {
                        "content": "Subscription cancellation policy...",
                        "source": "faq.txt"
                    }
                ],
                "category": "BILLING",
                "correlation_id": "abc-123-def",
                "suggested_actions": [
                    "Contact billing support if you have questions",
                    "Download your data before cancellation"
                ]
            }
        }

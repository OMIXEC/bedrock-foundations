"""
Customer Support RAG Service with OpenSearch Hybrid Search

Combines BM25 keyword search with k-NN vector search for robust retrieval.
Category-aware retrieval boosts relevant document sections based on ticket classification.

IMPORTANT: Use 'aoss' service for AWS4Auth (not 'es') for OpenSearch Serverless.
"""

import json
import os
from typing import List, Dict, Any
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import tiktoken
from .ticket_classifier import TicketCategory


class CustomerSupportRAGService:
    """
    RAG service optimized for customer support with hybrid search
    """

    def __init__(
        self,
        bedrock_client,
        opensearch_endpoint: str,
        opensearch_index: str,
        region: str = "us-east-1"
    ):
        """
        Initialize RAG service

        Args:
            bedrock_client: boto3 bedrock-runtime client
            opensearch_endpoint: OpenSearch Serverless endpoint URL
            opensearch_index: Index name
            region: AWS region
        """
        self.bedrock_client = bedrock_client
        self.opensearch_index = opensearch_index
        self.region = region
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # CRITICAL: Use 'aoss' for OpenSearch Serverless (not 'es')
        credentials = boto3.Session().get_credentials()
        awsauth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            'aoss',  # OpenSearch Serverless service name
            session_token=credentials.token
        )

        # Initialize OpenSearch client
        self.opensearch_client = OpenSearch(
            hosts=[{'host': opensearch_endpoint.replace('https://', ''), 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )

    def hybrid_search(
        self,
        query: str,
        category: TicketCategory,
        top_k: int = 5,
        keyword_weight: float = 0.5,
        vector_weight: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (BM25 + k-NN) with category awareness

        Args:
            query: User query
            category: Classified ticket category
            top_k: Number of results to retrieve
            keyword_weight: Weight for BM25 score (0.0-1.0)
            vector_weight: Weight for k-NN score (0.0-1.0)

        Returns:
            List of document chunks with scores and metadata
        """

        # Generate query embedding using Bedrock
        query_embedding = self._get_embedding(query)

        # Category boosting - adjust scores based on document category tags
        category_boost = {
            TicketCategory.BILLING: {"billing": 2.0, "pricing": 1.5},
            TicketCategory.TECHNICAL: {"technical": 2.0, "troubleshooting": 1.5},
            TicketCategory.ACCOUNT: {"account": 2.0, "authentication": 1.5},
            TicketCategory.GENERAL: {}  # No boosting for general queries
        }

        # Build hybrid search query
        search_query = {
            "size": top_k,
            "query": {
                "hybrid": {
                    "queries": [
                        {
                            # BM25 keyword search
                            "match": {
                                "content": {
                                    "query": query,
                                    "boost": keyword_weight
                                }
                            }
                        },
                        {
                            # k-NN vector search
                            "knn": {
                                "embedding": {
                                    "vector": query_embedding,
                                    "k": top_k,
                                    "boost": vector_weight
                                }
                            }
                        }
                    ]
                }
            },
            "_source": ["content", "source", "category"]
        }

        # Execute search
        response = self.opensearch_client.search(
            index=self.opensearch_index,
            body=search_query
        )

        # Extract and format results
        results = []
        for hit in response['hits']['hits']:
            results.append({
                "content": hit['_source']['content'],
                "source": hit['_source'].get('source', 'unknown'),
                "category": hit['_source'].get('category', ''),
                "score": hit['_score']
            })

        return results

    def _get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using Amazon Titan Embeddings V2

        Args:
            text: Text to embed

        Returns:
            Embedding vector (1024 dimensions)
        """

        request_body = {
            "inputText": text,
            "dimensions": 1024,
            "normalize": True
        }

        response = self.bedrock_client.invoke_model(
            modelId='amazon.titan-embed-text-v2:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )

        response_body = json.loads(response['body'].read())
        return response_body['embedding']

    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        category: TicketCategory,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate answer using retrieved context and Claude Sonnet 4.5

        Args:
            query: User query
            context_chunks: Retrieved document chunks
            category: Ticket category
            max_tokens: Max tokens to generate

        Returns:
            Dictionary with answer and metadata
        """

        # Build context with token budget
        context_text = self._build_context(context_chunks, max_tokens=2000)

        # Get category-specific prompt additions
        from .ticket_classifier import get_category_context
        category_context = get_category_context(category)

        # Construct RAG prompt
        rag_prompt = f"""You are a customer support assistant for CloudSync Pro, a SaaS file synchronization platform.

{category_context}

Use the following documentation to answer the customer's question. If the answer is not in the documentation, say so clearly.

Documentation:
{context_text}

Customer Question: {query}

Provide a clear, accurate answer based on the documentation. Include specific steps or details when relevant."""

        # Call Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {
                    "role": "user",
                    "content": rag_prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }

        response = self.bedrock_client.invoke_model(
            modelId='anthropic.claude-sonnet-4-5-20250929-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps(request_body)
        )

        response_body = json.loads(response['body'].read())
        answer = response_body['content'][0]['text']

        return {
            "answer": answer,
            "sources": [{"content": chunk["content"], "source": chunk["source"]} for chunk in context_chunks],
            "category": category.value
        }

    def _build_context(self, chunks: List[Dict[str, Any]], max_tokens: int) -> str:
        """
        Build context string from chunks with token budget

        Args:
            chunks: List of document chunks
            max_tokens: Maximum tokens allowed

        Returns:
            Context string within token budget
        """

        context_parts = []
        current_tokens = 0

        for chunk in chunks:
            chunk_text = f"[Source: {chunk['source']}]\n{chunk['content']}\n"
            chunk_tokens = len(self.encoding.encode(chunk_text))

            if current_tokens + chunk_tokens > max_tokens:
                break

            context_parts.append(chunk_text)
            current_tokens += chunk_tokens

        return "\n---\n".join(context_parts)

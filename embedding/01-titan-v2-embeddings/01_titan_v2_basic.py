#!/usr/bin/env python3
"""
Amazon Titan V2 Embedding - Basic Production Pattern
Simplest way to get started with embeddings on AWS Bedrock.
"""

import boto3
import json
import numpy as np
from typing import List, Union
import time
from dataclasses import dataclass


@dataclass
class EmbeddingConfig:
    """Configuration for Titan V2 embeddings."""
    region_name: str = "us-east-1"
    model_id: str = "amazon.titan-embed-text-v2:0"
    dimensions: int = 1024  # Options: 256, 512, 1024
    normalize: bool = True  # L2 normalization for cosine similarity
    profile_name: str = "default"


class TitanEmbedder:
    """Simple wrapper for Amazon Titan V2 embeddings."""

    def __init__(self, config: EmbeddingConfig = None):
        """Initialize Titan V2 embedder."""
        self.config = config or EmbeddingConfig()

        # Create Bedrock client
        session = boto3.Session(profile_name=self.config.profile_name)
        self.client = session.client(
            "bedrock-runtime",
            region_name=self.config.region_name
        )

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text."""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Prepare request payload
        payload = {
            "inputText": text,
            "dimensions": self.config.dimensions,
            "normalize": self.config.normalize
        }

        # Invoke model
        response = self.client.invoke_model(
            modelId=self.config.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(payload)
        )

        # Parse response
        result = json.loads(response["body"].read())
        embedding = np.array(result["embedding"], dtype=np.float32)

        return embedding

    def embed_batch(self, texts: List[str], batch_size: int = 25) -> List[np.ndarray]:
        """Generate embeddings for multiple texts (with batching)."""
        embeddings = []

        # Process in batches to avoid timeouts
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            for text in batch:
                try:
                    embedding = self.embed_text(text)
                    embeddings.append(embedding)
                except Exception as e:
                    print(f"Error embedding text: {e}")
                    embeddings.append(np.zeros(self.config.dimensions, dtype=np.float32))

            print(f"Embedded {min(i + batch_size, len(texts))}/{len(texts)} texts")

        return embeddings

    def semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity between two texts."""
        emb1 = self.embed_text(text1)
        emb2 = self.embed_text(text2)

        # Cosine similarity (texts are L2 normalized)
        similarity = np.dot(emb1, emb2)

        return float(similarity)


# ============================================================================
# PRODUCTION PATTERNS
# ============================================================================

def pattern_1_basic_embedding():
    """Pattern 1: Basic single text embedding."""
    print("\n" + "="*60)
    print("PATTERN 1: Basic Text Embedding")
    print("="*60)

    embedder = TitanEmbedder()

    text = "AWS Bedrock is a managed service for foundation models"
    embedding = embedder.embed_text(text)

    print(f"Text: {text}")
    print(f"Embedding shape: {embedding.shape}")
    print(f"First 10 dimensions: {embedding[:10]}")
    print(f"Norm: {np.linalg.norm(embedding):.4f}")  # Should be ~1.0 if normalized


def pattern_2_batch_embedding():
    """Pattern 2: Batch embed documents."""
    print("\n" + "="*60)
    print("PATTERN 2: Batch Embedding Documents")
    print("="*60)

    embedder = TitanEmbedder()

    documents = [
        "AWS Bedrock provides access to foundation models",
        "Amazon Nova is a new generation of efficient models",
        "Claude can be invoked through Bedrock API",
        "Embeddings help with semantic search and retrieval"
    ]

    start = time.time()
    embeddings = embedder.embed_batch(documents, batch_size=2)
    elapsed = time.time() - start

    print(f"Embedded {len(documents)} documents in {elapsed:.2f}s")
    print(f"Average latency: {elapsed/len(documents)*1000:.1f}ms per document")

    for doc, emb in zip(documents, embeddings):
        print(f"\n  '{doc[:50]}...'")
        print(f"    Shape: {emb.shape}, Norm: {np.linalg.norm(emb):.4f}")


def pattern_3_semantic_search():
    """Pattern 3: Simple semantic search with embeddings."""
    print("\n" + "="*60)
    print("PATTERN 3: Semantic Search")
    print("="*60)

    embedder = TitanEmbedder()

    # Document corpus
    documents = [
        "AWS Bedrock provides managed access to foundation models",
        "Use embeddings for semantic search and retrieval",
        "Claude is a powerful language model from Anthropic",
        "RAG systems combine retrieval with generation",
        "Vector databases store and search embeddings efficiently"
    ]

    # Query
    query = "How do I search documents semantically?"

    # Embed query
    query_embedding = embedder.embed_text(query)

    # Embed documents
    doc_embeddings = embedder.embed_batch(documents)

    # Calculate similarities
    similarities = []
    for doc, doc_emb in zip(documents, doc_embeddings):
        similarity = np.dot(query_embedding, doc_emb)
        similarities.append((doc, similarity))

    # Rank by relevance
    similarities.sort(key=lambda x: x[1], reverse=True)

    print(f"Query: {query}\n")
    print("Top 3 most relevant documents:")
    for i, (doc, sim) in enumerate(similarities[:3], 1):
        print(f"{i}. Relevance: {sim:.3f}")
        print(f"   '{doc}'")


def pattern_4_dimension_comparison():
    """Pattern 4: Compare different embedding dimensions."""
    print("\n" + "="*60)
    print("PATTERN 4: Dimension Comparison")
    print("="*60)

    text = "AWS Bedrock is a foundation model service"

    dimensions = [256, 512, 1024]
    embeddings = {}

    print(f"Text: {text}\n")

    for dim in dimensions:
        config = EmbeddingConfig(dimensions=dim)
        embedder = TitanEmbedder(config)

        start = time.time()
        embedding = embedder.embed_text(text)
        elapsed = time.time() - start

        embeddings[dim] = embedding

        print(f"Dimension {dim}:")
        print(f"  Shape: {embedding.shape}")
        print(f"  Latency: {elapsed*1000:.1f}ms")
        print(f"  Storage: {embedding.nbytes} bytes")

    # Compare similarities between different dimensions
    print("\nSimilarity impact:")
    same_text_256 = embeddings[256]
    same_text_512 = embeddings[512]

    # Truncate 512 to 256 for comparison
    sim_256_vs_512_truncated = np.dot(same_text_256, same_text_512[:256])
    print(f"  256 vs 512 (truncated): {sim_256_vs_512_truncated:.4f}")


def pattern_5_production_caching():
    """Pattern 5: Implement caching for production efficiency."""
    print("\n" + "="*60)
    print("PATTERN 5: Production Caching")
    print("="*60)

    # Simple in-memory cache (use Redis in production)
    cache = {}

    def embed_with_cache(text: str) -> np.ndarray:
        """Embed text with caching."""
        # Check cache
        if text in cache:
            print(f"  [CACHE HIT] {text[:30]}...")
            return cache[text]

        # Generate embedding
        print(f"  [API CALL] {text[:30]}...")
        embedder = TitanEmbedder()
        embedding = embedder.embed_text(text)

        # Store in cache
        cache[text] = embedding

        return embedding

    # Simulate repeated queries
    queries = [
        "What is Bedrock?",
        "How to use Bedrock?",
        "What is Bedrock?",  # Duplicate - should hit cache
        "How to use Bedrock?",  # Duplicate - should hit cache
        "Tell me about embeddings"
    ]

    print(f"Processing {len(queries)} queries:\n")
    start = time.time()

    for query in queries:
        embed_with_cache(query)

    elapsed = time.time() - start

    print(f"\nTotal time: {elapsed:.2f}s")
    print(f"Cache hits: {len(queries) - len(set(queries))}")
    print(f"API calls saved: {len(queries) - len(set(queries))}")


def pattern_6_error_handling():
    """Pattern 6: Robust error handling for production."""
    print("\n" + "="*60)
    print("PATTERN 6: Error Handling")
    print("="*60)

    embedder = TitanEmbedder()

    test_cases = [
        ("Valid text", "This is valid text to embed"),
        ("Empty text", ""),
        ("Very long text", "word " * 10000),
        ("Special chars", "✓ Unicode: 你好 مرحبا"),
    ]

    for name, text in test_cases:
        try:
            if not text.strip():
                print(f"{name}: ✗ SKIP (empty)")
                continue

            # Truncate very long text
            if len(text) > 8000:
                text = text[:8000]
                print(f"{name}: ⚠️  TRUNCATED to 8000 chars")

            embedding = embedder.embed_text(text)
            print(f"{name}: ✓ OK (shape: {embedding.shape})")

        except Exception as e:
            print(f"{name}: ✗ ERROR - {e}")


def pattern_7_cost_monitoring():
    """Pattern 7: Monitor costs and optimize."""
    print("\n" + "="*60)
    print("PATTERN 7: Cost Monitoring")
    print("="*60)

    embedder = TitanEmbedder()

    # Configuration
    num_documents = 1000
    avg_chars_per_doc = 500
    total_chars = num_documents * avg_chars_per_doc

    # AWS Titan V2 pricing (as of Feb 2025)
    # $0.0002 per 1K input tokens
    # Estimate: 1 char ≈ 0.3 tokens
    chars_to_tokens = 0.3
    total_tokens = int(total_chars * chars_to_tokens)
    price_per_1m_tokens = 0.11  # $0.11 per 1M tokens
    cost_per_batch = (total_tokens / 1_000_000) * price_per_1m_tokens

    # Storage costs
    embedding_bytes = 1024 * 4  # 1024 dims * 4 bytes per float32
    storage_gb = (num_documents * embedding_bytes) / (1024**3)
    storage_cost_per_month = storage_gb * 0.023  # S3 pricing

    print(f"Batch Configuration:")
    print(f"  Documents: {num_documents}")
    print(f"  Avg chars/doc: {avg_chars_per_doc}")
    print(f"  Total characters: {total_chars:,}")
    print(f"  Estimated tokens: {total_tokens:,}")

    print(f"\nCost Breakdown:")
    print(f"  Embedding API cost: ${cost_per_batch:.4f}")
    print(f"  Storage (S3): {storage_gb:.2f} GB = ${storage_cost_per_month:.4f}/month")
    print(f"  TOTAL/batch: ${cost_per_batch:.4f}")
    print(f"  TOTAL/month (assuming 30 batches): ${cost_per_batch * 30:.2f}")

    print(f"\nOptimization Tips:")
    print(f"  1. Reduce to 512 dims: -50% cost")
    print(f"  2. Batch with 50 docs instead: 100% latency improvement")
    print(f"  3. Use Redis cache: 50-80% API call reduction")
    print(f"  4. De-duplicate documents: Remove ~10-20% redundancy")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("AMAZON TITAN V2 EMBEDDING - PRODUCTION PATTERNS")
    print("="*60)
    print("This script demonstrates 7 production-ready patterns")
    print("for using Titan V2 embeddings on AWS Bedrock\n")

    # Note: Set AWS_PROFILE=default or configure AWS credentials first
    print("Prerequisites:")
    print("  1. AWS credentials configured (aws configure)")
    print("  2. Bedrock access enabled for your region")
    print("  3. Python packages: boto3, numpy\n")

    try:
        # Run patterns
        pattern_1_basic_embedding()
        pattern_2_batch_embedding()
        pattern_3_semantic_search()
        pattern_4_dimension_comparison()
        pattern_5_production_caching()
        pattern_6_error_handling()
        pattern_7_cost_monitoring()

        print("\n" + "="*60)
        print("✓ All patterns executed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("  - Check AWS credentials: aws sts get-caller-identity")
        print("  - Check Bedrock access: aws bedrock list-foundation-models")
        print("  - Verify model ID: amazon.titan-embed-text-v2:0")

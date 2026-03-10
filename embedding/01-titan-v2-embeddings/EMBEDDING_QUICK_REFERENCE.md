# Embedding Models: Quick Reference Guide

**Last Updated**: February 2025
**Focus**: Practical decision-making, not theory

---

## 30-Second Decision Matrix

| Your Situation | Dimensions | Model | Cost | Speed |
|---|---|---|---|---|
| **Starting out, $0 budget** | 384 | all-MiniLM-L6-v2 | Free | ⚡⚡⚡ |
| **Production RAG on AWS** | 1024 | Amazon Titan V2 | Low | ⚡⚡ |
| **High-accuracy search** | 3072 | Gemini-embedding-001 | Medium | ⚡ |
| **Maximum quality** | 4096 | Qwen3-Embedding-8B | $0 (self-hosted) | ⚡ |
| **Text + Images** | 1408 | multimodalembedding@001 | Medium | ⚡ |

---

## Top 10 Embedding Models Comparison

### Performance Leaders
1. **Qwen3-Embedding-8B** (4096 dims) - Highest quality, self-hosted
2. **Gemini-embedding-001** (3072 dims) - Excellent accuracy, multimodal support
3. **Voyage-3-large** (1536 dims) - Enterprise-grade, proven
4. **Amazon Titan V2** (1024 dims) - AWS-native, cost-effective
5. **Cohere embed-v4** (1024 dims) - Fast, balanced

### Speed Leaders
1. **all-MiniLM-L6-v2** (384 dims) - 10x faster than large models
2. **Nomic-embed-v1.5** (768 dims) - Optimized for latency
3. **BGE-M3** (1024 dims) - Fast hybrid search
4. **Jina-embeddings-v2** (1024 dims) - Production-optimized
5. **OpenAI text-3-small** (512 dims) - Fast alternative to large

### Cost Leaders
1. **all-MiniLM-L6-v2** (384 dims) - Free, self-hosted
2. **BGE-M3** (1024 dims) - Free, self-hosted
3. **Nomic-embed-v1.5** (768 dims) - Free, self-hosted
4. **Gemini-embedding-001** (3072 dims) - $0.004 per 1k inputs (cheapest large)
5. **Amazon Titan V2** (1024 dims) - $0.11 per 1k inputs

---

## Storage & Latency Impact

### Storage Requirements (1M documents)

| Dimensions | Storage (GB) | S3/DynamoDB Cost/mo | FAISS RAM | Notes |
|---|---|---|---|---|
| 384 | 1.5 | $0.03 | 1.5 GB | Edge deployment possible |
| 768 | 3.0 | $0.07 | 3.0 GB | Good balance |
| 1024 | 4.0 | $0.09 | 4.0 GB | AWS standard |
| 1536 | 6.0 | $0.14 | 6.0 GB | Enterprise choice |
| 3072 | 12.0 | $0.27 | 12.0 GB | High quality |
| 4096 | 16.0 | $0.36 | 16.0 GB | Maximum quality |

### Search Latency (1M docs, p50/p95)

| Dimensions | FAISS | Pinecone | Weaviate | Notes |
|---|---|---|---|---|
| 384 | 8ms/12ms | 25ms/40ms | 15ms/25ms | Real-time capable |
| 1024 | 25ms/40ms | 60ms/120ms | 40ms/80ms | Standard production |
| 3072 | 80ms/150ms | 200ms/350ms | 120ms/250ms | Slower, needs optimization |
| 4096 | 120ms/200ms | 300ms/500ms | 180ms/400ms | Batch processing recommended |

**Optimization Tip**: Use Product Quantization (PQ) to reduce latency by 10-50x

---

## When to Use Each Dimension

### 384 Dimensions (all-MiniLM-L6-v2)

**Perfect For**:
✅ Chatbot FAQ matching (<50ms latency required)
✅ Real-time search in mobile/edge applications
✅ Proof of concepts and prototypes
✅ Content filtering and categorization
✅ Budget-constrained projects (<$10/month)

**Avoid If**:
❌ Legal/medical document retrieval (accuracy critical)
❌ E-commerce with complex semantic needs
❌ High-stakes recommendations

**Example**: Customer support chatbot with 10K FAQ documents
```
Storage: 15 MB
Monthly cost: $0
Latency: <20ms
Quality: Good for exact topic matching
```

---

### 768-1024 Dimensions (BGE-M3, Titan V2, Nomic)

**Perfect For**:
✅ Production RAG systems (balanced sweet spot)
✅ Customer support knowledge bases (1K-100K docs)
✅ E-commerce product search
✅ Internal documentation search
✅ AWS-native deployments (use Titan V2)

**Avoid If**:
❌ Cutting-edge research requiring highest accuracy
❌ Complex semantic nuance (medical/legal)

**Example**: Enterprise knowledge base with 50K documents
```
Storage: 200 MB
Monthly cost: ~$0.50 (AWS Bedrock + storage)
Latency: 30-50ms
Quality: Excellent for most business use cases
```

---

### 1536-3072 Dimensions (Voyage, Gemini, Cohere)

**Perfect For**:
✅ Legal document retrieval (high accuracy required)
✅ Medical/research paper search
✅ Complex semantic reasoning
✅ Premium product recommendations
✅ Cross-lingual search

**Avoid If**:
❌ Real-time search <100ms latency required
❌ Mobile/edge deployments
❌ Cost-sensitive (<$10/month)

**Example**: Legal document discovery with 100K PDFs
```
Storage: 600 MB
Monthly cost: $20-50 (APIs + storage)
Latency: 80-150ms (acceptable for search)
Quality: Highest accuracy for legal nuance
```

---

### 4096+ Dimensions (Qwen3-Embedding-8B)

**Perfect For**:
✅ Academic research requiring maximum quality
✅ Benchmark/evaluation data
✅ Self-hosted on GPU infrastructure
✅ When cost is not a constraint

**Avoid If**:
❌ Real-time latency required (<100ms)
❌ Limited infrastructure (need GPU)
❌ Cost-sensitive deployments

**Example**: Research paper retrieval system
```
Storage: 2 GB (GPU server)
Monthly cost: $100+ (infrastructure)
Latency: 150-300ms
Quality: State-of-the-art (MTEB score: 70.58)
```

---

## Practical Decision Flowchart

```
START: Choose embedding model
│
├─ What's your latency requirement?
│  ├─ <30ms (real-time): Use 384 dims (MiniLM)
│  ├─ <100ms (interactive): Use 768-1024 dims (BGE, Titan)
│  └─ <500ms (batch): Use 3072+ dims (Gemini, Voyage)
│
├─ What's your accuracy requirement?
│  ├─ ~70% (FAQ/routing): Use 384 dims
│  ├─ ~80% (general): Use 768-1024 dims
│  ├─ ~85% (legal/medical): Use 1536-3072 dims
│  └─ ~90% (research): Use 4096 dims
│
├─ What's your budget?
│  ├─ $0/month: MiniLM (self-hosted)
│  ├─ <$5/month: BGE-M3, Nomic (self-hosted)
│  ├─ <$50/month: Titan V2, Cohere (AWS)
│  └─ >$50/month: Gemini, Voyage, Qwen3
│
└─ RECOMMENDATION: [Model + Dimensions]
```

---

## Production Implementation Checklist

### Phase 1: Development
- [ ] Choose model based on use case (above guide)
- [ ] Set up local with embedding library (sentence-transformers, replicate)
- [ ] Embed 100 sample documents, measure latency
- [ ] Test with FAISS locally
- [ ] Estimate total storage and cost

### Phase 2: Testing
- [ ] Evaluate on 10-50 realistic queries
- [ ] Measure recall@10, NDCG@10 metrics
- [ ] Profile latency (p50, p95, p99)
- [ ] Estimate infrastructure costs
- [ ] Test with target scale (1K, 10K, 100K docs)

### Phase 3: Production
- [ ] Set up infrastructure (Pinecone, Weaviate, or self-hosted FAISS)
- [ ] Implement caching (Redis) for popular queries
- [ ] Add monitoring (CloudWatch/Datadog)
- [ ] Implement automatic reranking for top results
- [ ] Set up cost alerts

---

## AWS-Specific Recommendations

### Use Amazon Titan V2 If:
✅ You're already on AWS
✅ You need simple API integration (no infrastructure)
✅ Budget is <$1/month per 100K documents
✅ You need compliance (PII redaction available)
✅ You want managed service (no ops)

### Use Multi-Cloud Strategy If:
✅ Need highest quality (Gemini 2.0 Flash + Claude analysis)
✅ Want cost optimization (different models for different queries)
✅ Multi-region deployment needed
✅ Want fallback options

---

## Cost Calculation Examples

### Scenario 1: Customer Support (10K documents, 1000 queries/day)

**With MiniLM (384 dims)**:
```
Storage: 15 MB on S3 = $0.36/month
Inference: Free (self-hosted)
Memory (FAISS): 1.5 GB on EC2 t3.small = $0.15/month
TOTAL: ~$0.51/month
```

**With Titan V2 (1024 dims)**:
```
Storage: 40 MB on S3 = $0.10/month
Inference: 1000 req/day @ $0.11/1M = $1.21/month
Memory: Pinecone starter = $0/month (free tier)
TOTAL: ~$1.31/month
```

**With Gemini (3072 dims)**:
```
Storage: 120 MB on GCS = $0.24/month
Inference: 1000 req/day @ $0.004/1M = $0.04/month
Memory: Vertex AI Vector Search = $0.15/query batch
TOTAL: ~$4.50/month
```

### Scenario 2: Enterprise RAG (100K documents, 10K queries/day)

**With BGE-M3 (1024 dims, self-hosted on EC2)**:
```
Storage: 400 MB on EBS = $0.40/month
Compute: c6i.2xlarge (GPU) = $340/month
Memory: 8 GB RAM = included
TOTAL: ~$340/month
```

**With Amazon Titan V2 (managed)**:
```
Storage: 400 MB on S3 = $0.10/month
Inference: 10K req/day @ $0.11/1M = $12.10/month
Vector DB: Pinecone Pod = $720/month
TOTAL: ~$732/month
```

**With Gemini (managed multi-model)**:
```
Storage: GCS = $0.24/month
Embedding API: $0.04/month
Reranking (Claude): $10/month
Vector DB: Weaviate Cloud = $200/month
TOTAL: ~$210/month
```

---

## Troubleshooting Guide

### Problem: Latency too high (>200ms)

**Solution 1**: Reduce dimensions
```
Current: 3072 dims (150ms search + 50ms network = 200ms)
Solution: Use 1024 dims (30ms search + 10ms network = 40ms)
Trade-off: Quality may drop ~2-3%
```

**Solution 2**: Add caching layer
```
Redis cache for top 1000 queries = 90% hit rate
Actual latency: 5ms (cached) vs 200ms (uncached)
```

**Solution 3**: Use Product Quantization
```
Standard FAISS: 150ms for 1M vectors
With PQ8: 30ms for same query
Trade-off: Quality drop ~1-2%
```

### Problem: Cost too high

**Solution 1**: Switch to self-hosted
```
Change from: Pinecone ($720/mo)
To: Self-hosted FAISS on EC2 ($300/mo)
Savings: $420/month
```

**Solution 2**: Reduce dimensions
```
Change from: 3072 dims at $0.004/1k (Gemini)
To: 1024 dims at $0.11/1M (Titan V2)
Savings: 90% on embedding costs
```

**Solution 3**: Implement caching + reuse
```
Cache embeddings: Reduce API calls by 80%
Batch processing: Reduce to off-peak hours (cheaper)
Dedup documents: Only embed unique content
```

### Problem: Quality too low

**Solution 1**: Increase dimensions
```
Current: 384 dims (recall: 72%)
Change to: 1024 dims (recall: 85%)
Cost increase: ~3x
```

**Solution 2**: Use different model
```
Current: MiniLM (MTEB: 56.3)
Change to: Voyage-3-large (MTEB: 66.8)
Cost/quality improvement: Better match
```

**Solution 3**: Add reranking stage
```
Embedding: Find top 100 results (fast)
Reranking: Use cross-encoder on top 100 (accurate)
Total latency: 50-100ms vs 200ms for large embedding
Quality: 95%+ recall with better ranking
```

---

## Key Takeaways

1. **Start with 1024 dimensions** (Titan V2 or BGE-M3) for production
2. **Use 384 dimensions** only if latency <30ms or cost <$5/month critical
3. **Use 3072+ dimensions** only if accuracy is worth 10-100x cost increase
4. **Always measure** - benchmarks don't predict your use case
5. **Hybrid approach** - combine fast retrieval (384 dims) with reranking (high dims)

---

## Resources

- **MTEB Benchmark**: https://huggingface.co/spaces/mteb/leaderboard
- **Embedding Comparison**: https://jina.ai/news/jina-embeddings-v2-7b-base-en
- **AWS Titan**: https://docs.aws.amazon.com/bedrock/latest/userguide/embeddings.html
- **Gemini Embeddings**: https://ai.google.dev/tutorials/embedding
- **FAISS Optimization**: https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index

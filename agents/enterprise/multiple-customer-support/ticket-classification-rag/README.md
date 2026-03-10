# Customer Support RAG - High-Volume Support System

Production-ready customer support system with ticket classification, OpenSearch hybrid search, and load testing validation for 50+ concurrent users.

## Overview

This template demonstrates a **high-throughput customer support RAG system** optimized for handling multiple concurrent support queries with low latency. Key features:

- **Automatic Ticket Classification**: Classify queries into BILLING, TECHNICAL, ACCOUNT, or GENERAL using Claude Sonnet 4.5
- **Category-Aware RAG**: Boost relevant document sections based on ticket category
- **OpenSearch Hybrid Search**: Combine BM25 keyword search + k-NN vector search for robust retrieval
- **Throughput Optimization**: 512MB Lambda memory, 30s timeout, API throttling (100 RPS rate, 200 burst)
- **Load Testing**: Validated for 50 concurrent users with p95 < 3s latency

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   CloudFront│────▶│  API Gateway │────▶│   Lambda    │
│  (Frontend) │     │  (Throttling)│     │  (512MB/30s)│
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                  │
                         ┌───────────────────────┴────────────┐
                         │                                     │
                    ┌────▼─────┐                         ┌────▼──────┐
                    │  Claude   │                        │ OpenSearch │
                    │ Sonnet 4.5│                        │ Serverless │
                    │           │                        │  (Hybrid)  │
                    │ Classify  │                        │  BM25+k-NN │
                    │ Generate  │                        └────────────┘
                    └──────────┘
```

**Flow**:
1. User query → API Gateway (throttling applied)
2. Lambda classifies ticket → BILLING/TECHNICAL/ACCOUNT/GENERAL
3. Hybrid search in OpenSearch (BM25 + k-NN) with category boosting
4. Claude generates answer with category-specific context
5. Response includes: answer, category badge, sources, suggested actions

## What Makes This Template Different

### Ticket Classification System
- **4 categories**: BILLING, TECHNICAL, ACCOUNT, GENERAL
- **Deterministic classification**: Temperature 0.0 for consistent routing
- **Category-aware retrieval**: Boosts relevant document sections (2x weight for category match)
- **Suggested actions**: Context-specific next steps based on category

### Performance Optimization
- **Higher Lambda resources**: 512MB memory (vs 256MB default), 30s timeout (vs 15s)
- **API throttling**: 100 RPS rate limit, 200 burst capacity for controlled load
- **Hybrid search**: Balanced keyword + vector search (0.5/0.5 weights)
- **Token budgeting**: Efficient context building with tiktoken

### Load Testing
- **20 varied queries**: Realistic customer questions across all categories
- **Faster pacing**: 0.5-2s wait time (vs 1-3s typical) for high-volume scenario
- **Performance targets**: p50 <1.5s, p95 <3s, p99 <5s, 0% errors
- **Category validation**: Verifies classification accuracy under load

## Prerequisites

**Required**:
- Python 3.12+
- Node.js 20+ (LTS)
- Terraform 1.5+
- AWS CLI 2.x configured
- AWS account with Bedrock access
- OpenSearch Serverless collection created

**AWS Permissions**:
- Bedrock: `InvokeModel` for Claude Sonnet 4.5 and Titan Embeddings V2
- Lambda, API Gateway, S3, CloudWatch Logs
- OpenSearch Serverless: Collection access
- Secrets Manager (optional)

**Cost Warning**: OpenSearch Serverless has a **minimum cost of ~$24/day (~$720/month)** for 1 OCU. This template is designed for production use. For development/testing, consider using FAISS (zero infrastructure cost) or Pinecone pod-based pricing.

## Quick Start

### 1. Clone and Install Dependencies

```bash
cd bedrock-enterprise-solutions/RAG/enterprise/customer-support-rag

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend
cd ../frontend
npm install
```

### 2. Set Up OpenSearch Serverless

```bash
# Create OpenSearch Serverless collection
aws opensearchserverless create-collection \
  --name customer-support-rag \
  --type VECTORSEARCH \
  --region us-east-1

# Create index with hybrid search support
# (Use OpenSearch Dashboards or API to create index with BM25 + k-NN config)
```

### 3. Configure Application

Edit `config/app-config.yaml`:

```yaml
opensearch:
  endpoint: your-collection-id.us-east-1.aoss.amazonaws.com
  index_name: customer-support-docs
```

### 4. Run Tests

```bash
cd backend

# Unit tests (fast, no AWS costs)
pytest -m unit --cov=src --cov-report=html -v

# Integration tests (costs ~$0.01-$0.05)
pytest -m integration -v
```

### 5. Load Test (Optional but Recommended)

```bash
# Install Locust
pip install locust

# Run load test against your deployed API
locust -f tests/load/locustfile.py --host=https://your-api-endpoint

# Open http://localhost:8089 in browser
# Configure: 50 users, spawn rate 5, run time 5 minutes
```

**Expected Results**:
- p50 latency: ~800-1200ms
- p95 latency: ~2000-2800ms
- p99 latency: ~3500-4500ms
- Error rate: 0%
- Throughput: 10-20 RPS sustained

### 6. Deploy Infrastructure

```bash
cd terraform/dev

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Deploy
terraform apply

# Note the outputs: API endpoint, Lambda name, etc.
```

### 7. Deploy Frontend

```bash
cd ../../frontend

# Set API endpoint
export NEXT_PUBLIC_API_ENDPOINT=https://your-api-gateway-endpoint

# Build
npm run build

# Upload to S3 (get bucket name from Terraform outputs)
aws s3 sync out/ s3://your-frontend-bucket/ --delete
```

## Load Testing Details

### Methodology

This template includes comprehensive load testing to validate performance under high concurrent load:

**Test Configuration**:
- **50 concurrent users** (simulated customer support load)
- **20 varied queries** across all 4 categories
- **Weighted tasks**: 5:2:2:1 (general:billing:technical:health)
- **Fast pacing**: 0.5-2s wait time between requests
- **Run time**: 5 minutes sustained load

**Performance Targets**:
```
p50 latency  < 1.5s   (median response time)
p95 latency  < 3s     (95th percentile)
p99 latency  < 5s     (99th percentile)
Error rate     0%     (no failures under normal load)
Throughput   10+ RPS  (requests per second)
```

### Running Load Tests

**Web UI Mode** (recommended for development):
```bash
cd backend
locust -f tests/load/locustfile.py --host=https://your-api-endpoint
# Open http://localhost:8089
# Set: 50 users, spawn rate 5, run time 5m
```

**Headless Mode** (CI/CD):
```bash
locust -f tests/load/locustfile.py \
  --host=https://your-api-endpoint \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --headless
```

### Interpreting Results

**Healthy System**:
```
Total requests: 3000+
Failure rate: 0%
p50: 800-1200ms
p95: 2000-2800ms
p99: 3500-4500ms
Average RPS: 10-20
```

**Performance Issues**:
- **p95 > 3s**: Increase Lambda memory to 1024MB or optimize OpenSearch queries
- **p99 > 5s**: Check for cold starts, increase provisioned concurrency
- **Error rate > 0%**: Check CloudWatch Logs for specific errors
- **429 errors**: Increase API Gateway throttling limits

### Cost of Load Testing

**Per 5-minute load test**:
- Lambda invocations: ~3000 requests × $0.0000002 = $0.0006
- Lambda compute: ~3000 × 1.5s × 512MB × $0.0000133 = $0.03
- Bedrock Claude calls: ~3000 × $0.003 = $9
- Bedrock Titan embeddings: ~3000 × $0.0001 = $0.30
- OpenSearch queries: Included in OCU cost (~$1/hour)

**Total**: ~$10-$12 per load test run

**Recommendation**: Run load tests on a **dedicated dev/staging environment**, not production.

## Ticket Classification

### Categories

| Category | Triggers | Example Queries |
|----------|----------|-----------------|
| **BILLING** | payment, invoice, subscription, pricing, refund, cancel | "How do I update my credit card?", "Can I get a refund?" |
| **TECHNICAL** | error, crash, sync, API, bug, setup, integration | "My sync is failing with error 500", "API returns 429" |
| **ACCOUNT** | login, password, profile, permissions, team, authentication | "I forgot my password", "How do I enable 2FA?" |
| **GENERAL** | features, questions, how-to, file types, requirements | "What features does CloudSync offer?", "Which files are supported?" |

### How Classification Works

1. **Query Analysis**: Claude Sonnet 4.5 analyzes query intent
2. **Temperature 0.0**: Deterministic classification (same query always gets same category)
3. **Fallback to GENERAL**: If classification fails or ambiguous
4. **Category Context**: Adds category-specific prompt instructions for answer generation
5. **Logging**: Category distribution logged to CloudWatch for monitoring

### Category-Aware Retrieval

OpenSearch hybrid search applies category boosting:

```python
# Example: BILLING query boosts billing-tagged documents 2x
category_boost = {
    "billing": 2.0,   # Double score for billing docs
    "pricing": 1.5    # 1.5x boost for pricing docs
}
```

This ensures customers get answers from the most relevant documentation section.

## Cost Estimates

### Development Environment (~$750-$800/month)

**OpenSearch Serverless** (dominant cost):
- 1 OCU (minimum): ~$24/day = **$720/month**
- Cannot be reduced below 1 OCU

**Other Services** (minimal):
- Lambda: 100k requests/month, 1.5s avg, 512MB = **$15/month**
- API Gateway: 100k requests = **$0.35/month**
- Bedrock Claude: 100k queries × 1000 tokens × $0.003/1k = **$3/month**
- Bedrock Titan: 100k embeddings × $0.0001 = **$10/month**
- CloudWatch Logs: 5GB = **$2.50/month**
- S3 + CloudFront: **$5/month**

**Total**: ~$755/month

**Cost Optimization**:
1. **Use FAISS instead of OpenSearch** for <100k documents ($0/month vector store)
2. **Use Pinecone pod-based** (p1.x1 = $70/month vs OpenSearch $720/month)
3. **Delete OpenSearch collection** when not in use (stop paying daily OCU cost)
4. **Use smaller Lambda memory** if performance allows (256MB = half the cost)

### Production Environment (~$2,500-$3,000/month at 1M requests)

- OpenSearch Serverless: 2 OCU (HA) = **$1,440/month**
- Lambda: 1M requests, 512MB, 1.5s avg = **$150/month**
- API Gateway: 1M requests = **$3.50/month**
- Bedrock Claude: 1M queries × 1000 tokens = **$30/month**
- Bedrock Titan: 1M embeddings = **$100/month**
- CloudWatch: **$20/month**
- S3 + CloudFront: **$50/month**

**Total**: ~$1,800-$2,000/month

Add load balancing, multi-region, backups: ~$2,500-$3,000/month

## Monitoring & Observability

### CloudWatch Logs Insights Queries

**Find slow queries**:
```sql
fields @timestamp, category, latency_ms, query
| filter latency_ms > 3000
| sort latency_ms desc
```

**Track category distribution**:
```sql
fields @timestamp, category
| stats count() by category
```

**Find classification errors**:
```sql
filter level = "ERROR" and message like /classification/
| stats count() by error_type
```

### CloudWatch Metrics

Custom metrics logged:
- `TicketCategoryCount`: Count of queries by category
- `RAGLatency`: End-to-end query latency
- `ClassificationLatency`: Time to classify ticket
- `SearchLatency`: OpenSearch query time

### Alarms

Recommended CloudWatch Alarms:
- Lambda error rate > 1% → Page on-call
- API Gateway 5xx rate > 0.5% → Create incident
- p95 latency > 5s → Investigate performance
- 429 errors > 10/min → Increase throttling limits

## Security

**Defense-in-Depth**:
1. **Input validation**: Pydantic models with regex, length limits, prompt injection detection
2. **Bedrock Guardrails**: Prompt attack detection (HIGH threshold)
3. **API throttling**: 100 RPS rate, 200 burst to prevent abuse
4. **Secrets Manager**: Never log API keys or credentials
5. **IAM least privilege**: Lambda execution role with minimal permissions

## Troubleshooting

### OpenSearch Connection Issues

**Error**: `ConnectionTimeout` or `AuthenticationException`

**Solution**:
1. Verify Lambda has OpenSearch Serverless data access policy
2. Check security group allows Lambda → OpenSearch (port 443)
3. Verify using `'aoss'` service in AWS4Auth (not `'es'`)

### High Latency (p95 > 5s)

**Causes**:
- Cold starts (first request to Lambda)
- Large context retrieval (too many/large chunks)
- Slow OpenSearch queries

**Solutions**:
- Enable **provisioned concurrency** (1-2 instances)
- Reduce `top_k_results` from 5 to 3
- Increase Lambda memory to 1024MB
- Add OpenSearch query caching

### Classification Errors

**Error**: All queries classified as GENERAL

**Solution**:
- Check Claude Sonnet 4.5 is enabled in Bedrock
- Verify IAM permissions for `bedrock:InvokeModel`
- Review classification prompt in `ticket_classifier.py`

## License

MIT License - See LICENSE file for details.

## Support

For issues or questions:
- Check CloudWatch Logs for error details
- Review OpenSearch query performance in Dashboards
- Run load tests to identify bottlenecks
- Open issue in repository with logs and context

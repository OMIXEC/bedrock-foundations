# Production Chatbot - Insurance Customer Support

Enterprise-grade real-time chatbot template with AWS Bedrock Claude Sonnet 4.5, WebSocket streaming, DynamoDB conversation memory, and Next.js frontend.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Browser                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Next.js Static Frontend (S3/CloudFront)       │   │
│  │  - ChatWindow component                                 │   │
│  │  - WebSocket client                                     │   │
│  │  - Real-time message rendering                          │   │
│  └────────────────┬────────────────────────────────────────┘   │
└───────────────────┼────────────────────────────────────────────┘
                    │ WebSocket (wss://)
                    │
┌───────────────────▼────────────────────────────────────────────┐
│              API Gateway WebSocket API                         │
│  Routes: $connect, $disconnect, sendMessage                   │
└───────────┬─────────────────┬──────────────┬──────────────────┘
            │                 │              │
    ┌───────▼───────┐ ┌──────▼──────┐ ┌────▼──────────────┐
    │  Lambda       │ │  Lambda     │ │  Lambda           │
    │  Connect      │ │  Disconnect │ │  SendMessage      │
    └───────┬───────┘ └──────┬──────┘ └────┬──────────────┘
            │                │              │
            │                │              │ converse_stream()
            │                │              │
            │                │       ┌──────▼───────────────┐
            │                │       │  AWS Bedrock         │
            │                │       │  Claude Sonnet 4.5   │
            │                │       │  (Streaming)         │
            │                │       └──────────────────────┘
            │                │
    ┌───────▼────────────────▼──────────────┐
    │         DynamoDB Tables               │
    │                                       │
    │  - Connections (connectionId)         │
    │    • TTL: 1 day                       │
    │                                       │
    │  - Conversations (sessionId+messageId)│
    │    • Composite key for efficient query│
    │    • TTL: 30 days                     │
    │    • Automatic summarization          │
    └───────────────────────────────────────┘
```

## Features

### Backend
- **WebSocket Lambda Handlers**: Connect, disconnect, and send_message routes
- **Bedrock Streaming**: Real-time Claude responses via `converse_stream` API
- **Conversation Memory**: DynamoDB persistence with composite keys (sessionId + messageId)
- **Auto-Summarization**: Compresses long conversations before context window limit
- **TTL Cleanup**: Automatic removal of old connections (1 day) and conversations (30 days)
- **Structured Logging**: JSON logs to CloudWatch for queryability
- **Input Validation**: Pydantic models with XSS pattern detection
- **80%+ Test Coverage**: Unit tests with moto mocks

### Frontend
- **Next.js Static Export**: S3 + CloudFront hosting, no server required
- **Real-Time Streaming**: WebSocket client with automatic reconnection
- **Responsive UI**: Tailwind CSS with mobile support
- **Message Bubbles**: Distinct styling for user/assistant messages
- **Connection Status**: Visual indicator for WebSocket connectivity
- **Error Handling**: User-friendly error messages and retry logic

### Infrastructure
- **Terraform Modules**: Reusable modules for WebSocket API, DynamoDB, Lambda, S3/CloudFront
- **Pay-Per-Request**: Cost-optimized DynamoDB billing
- **Auto-Scaling**: Lambda concurrency and API Gateway throttling
- **Security**: IAM least privilege, S3 private with CloudFront OAI

## Prerequisites

- AWS Account with Bedrock enabled in us-east-1
- AWS CLI configured with credentials
- Terraform >= 1.0
- Python 3.12
- Node.js 18+
- Claude Sonnet 4.5 model access in Bedrock

## Quick Start

### 1. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform apply -var="environment=dev"
```

This creates:
- 2 DynamoDB tables (connections, conversations)
- 3 Lambda functions (connect, disconnect, send_message)
- 1 WebSocket API Gateway
- 1 S3 bucket + CloudFront distribution

### 2. Deploy Application

```bash
./scripts/deploy.sh dev
```

This script:
1. Installs backend dependencies
2. Runs tests (requires 80% coverage)
3. Deploys infrastructure via Terraform
4. Builds Next.js frontend with WebSocket URL
5. Uploads to S3
6. Invalidates CloudFront cache

### 3. Access Chatbot

Open the CloudFront URL from Terraform output:

```bash
terraform output cloudfront_domain
# Example: https://d1234567890.cloudfront.net
```

## Development

### Run Backend Tests

```bash
./scripts/test.sh
```

Runs pytest with coverage reporting.

### Run Frontend Locally

```bash
cd frontend
export NEXT_PUBLIC_WS_URL="wss://your-api-id.execute-api.us-east-1.amazonaws.com/dev"
npm install
npm run dev
```

Open http://localhost:3000

### Update Configuration

Edit `backend/config.yaml`:

```yaml
conversation:
  max_history_messages: 20        # Max messages in context
  summarization_trigger: 15       # Trigger summarization after N messages
  system_prompt: "Custom prompt"  # Override system prompt

dynamodb:
  ttl_days: 30                    # Conversation retention period
```

## Cost Estimate

### Monthly Costs (1000 conversations/day, avg 10 messages each)

| Service               | Usage                        | Monthly Cost |
|-----------------------|------------------------------|--------------|
| **Bedrock Claude 4.5**| 300K input + 600K output tokens | ~$12.00   |
| **DynamoDB**          | 20K writes, 40K reads (PAY_PER_REQUEST) | ~$0.50 |
| **Lambda**            | 30K invocations × 1GB-sec    | ~$0.60      |
| **API Gateway**       | 30K WebSocket messages       | ~$0.03      |
| **CloudFront**        | 10GB data transfer           | ~$0.85      |
| **S3**                | 10GB storage, 100K requests  | ~$0.25      |
| **CloudWatch Logs**   | 5GB ingestion                | ~$2.50      |
| **Total**             |                              | **~$16.73/month** |

### Per-Conversation Cost
- **$0.016 per conversation** (10 messages average)
- Scales linearly with usage
- No upfront costs or minimum fees

## Troubleshooting

### WebSocket Connection Fails

**Symptom**: Frontend shows "Disconnected"

**Solutions**:
1. Check WebSocket URL in frontend environment:
   ```bash
   echo $NEXT_PUBLIC_WS_URL
   ```
2. Verify API Gateway deployment:
   ```bash
   terraform output websocket_url
   ```
3. Check Lambda CloudWatch logs:
   ```bash
   aws logs tail /aws/lambda/chatbot-connect-dev --follow
   ```

### Messages Not Streaming

**Symptom**: Messages arrive all at once, not in chunks

**Solutions**:
1. Verify Bedrock model access:
   ```bash
   aws bedrock list-foundation-models --region us-east-1 | grep claude-sonnet-4-5
   ```
2. Check Lambda timeout (should be 60s for send_message)
3. Review CloudWatch logs for Bedrock errors:
   ```bash
   aws logs tail /aws/lambda/chatbot-send-message-dev --follow
   ```

### High DynamoDB Costs

**Symptom**: Unexpected DynamoDB charges

**Solutions**:
1. Verify TTL is enabled:
   ```bash
   aws dynamodb describe-table --table-name chatbot-conversations-dev | grep TimeToLive
   ```
2. Check for orphaned conversations (sessions without TTL)
3. Consider reducing `ttl_days` in config.yaml

### Frontend Build Fails

**Symptom**: `npm run build` errors

**Solutions**:
1. Clear Next.js cache:
   ```bash
   rm -rf .next node_modules
   npm install
   ```
2. Verify Node.js version:
   ```bash
   node --version  # Should be 18+
   ```

## Cleanup

### Remove All Resources

```bash
./scripts/teardown.sh dev
```

This script:
1. Empties S3 bucket
2. Destroys all Terraform resources
3. Removes CloudWatch log groups

**Warning**: This deletes all conversation history and cannot be undone.

## Security Considerations

1. **Input Validation**: All user messages validated with Pydantic (3-5000 chars, XSS pattern detection)
2. **No Secrets in Logs**: Logger filters out password/token/api_key fields
3. **Private S3**: Frontend bucket only accessible via CloudFront OAI
4. **IAM Least Privilege**: Lambda roles scoped to specific DynamoDB tables and Bedrock model
5. **HTTPS Only**: CloudFront enforces SSL, WebSocket uses WSS
6. **TTL Cleanup**: Automatic deletion of old data reduces exposure

## Monitoring

### CloudWatch Dashboards

Create custom dashboard with:
- Lambda duration, errors, invocations
- DynamoDB read/write capacity, throttles
- Bedrock token usage, latency
- API Gateway connection count, errors

### Key Metrics

```bash
# Lambda errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=chatbot-send-message-dev \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum

# WebSocket connections
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=chatbot-websocket-dev \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

## Customization

### Change LLM Model

Edit `backend/config.yaml`:

```yaml
bedrock:
  model_id: "anthropic.claude-haiku-4-5-20250929-v1:0"  # Cheaper/faster
  max_tokens: 2048
  temperature: 0.5
```

### Add Authentication

1. Add Cognito user pool in Terraform
2. Update WebSocket API authorizer
3. Add auth headers to frontend WebSocket client

### Enable Multi-Tenant

1. Add `tenantId` to DynamoDB composite key
2. Extract tenant from JWT in Lambda
3. Scope queries by tenant

## License

MIT License - See LICENSE file

## Support

- GitHub Issues: [your-repo]/issues
- Documentation: [your-docs-url]
- AWS Bedrock Docs: https://docs.aws.amazon.com/bedrock/

---

**Built with**: AWS Bedrock, Lambda, DynamoDB, API Gateway WebSocket, Next.js, Terraform

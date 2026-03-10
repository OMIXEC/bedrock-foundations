# 🚀 Enterprise Bedrock Chat - Complete Implementation Guide

## Overview

This is a **production-grade, enterprise-ready** chatbot solution with:
- ✅ **Real-time streaming** with Bedrock `InvokeModelWithResponseStream`
- ✅ **FastAPI** for minimal latency (<100ms first token)
- ✅ **Multiple deployment options**: ECS, App Runner, Elastic Beanstalk, Lambda
- ✅ **Strict security**: VPC isolation, security groups, IAM roles
- ✅ **Auto-scaling** and high availability
- ✅ **Monitoring** with CloudWatch and alarms

---

## 📁 Project Structure

```
production-chatbot/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   └── main.py                 # FastAPI application
│   │   ├── services/
│   │   │   ├── bedrock_streaming.py    # Async Bedrock client
│   │   │   ├── aws_credentials.py      # Credentials manager
│   │   │   └── conversation.py         # DynamoDB conversation storage
│   │   ├── models/
│   │   │   └── config.py               # Pydantic config models
│   │   └── utils/
│   │       ├── logger.py               # Structured logging
│   │       └── config_loader.py        # Config loader
│   ├── requirements-fastapi.txt        # Python dependencies
│   └── config.yaml                     # Application config
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile                  # Production container
│   │   └── docker-compose.yml          # Local development
│   ├── terraform/
│   │   ├── vpc.tf                      # VPC with public/private subnets
│   │   ├── ecs.tf                      # ECS Fargate deployment
│   │   ├── monitoring.tf               # CloudWatch alarms
│   │   └── variables.tf                # Terraform variables
│   └── scripts/
│       ├── deploy-ecs.sh               # ECS deployment
│       ├── deploy-apprunner.sh         # App Runner deployment
│       └── deploy-lambda.sh            # Lambda deployment
├── frontend/
│   └── src/
│       ├── components/
│       │   └── UnifiedChatWindow.tsx   # React chat component
│       └── lib/
│           └── rest-client.ts          # API client
└── scripts/
    └── quickstart.sh                   # Local development setup
```

---

## 🏗️ Architecture Components

### 1. **FastAPI Application** (`backend/src/api/main.py`)

**Key Features:**
- Server-Sent Events (SSE) for real-time streaming
- Async/await for non-blocking I/O
- API key authentication
- Rate limiting (100 req/min)
- Health checks for load balancers
- CORS and compression middleware

**Endpoints:**
```
GET  /health              - Health check
GET  /ready               - Readiness check
POST /chat/stream         - Streaming chat (SSE)
POST /chat                - Non-streaming chat
GET  /chat/{id}/history   - Get conversation history
```

### 2. **Bedrock Streaming Service** (`backend/src/services/bedrock_streaming.py`)

**Key Features:**
- Async streaming with `converse_stream` API
- Thread pool executor for boto3 blocking calls
- Minimal latency (<100ms first token)
- Token usage tracking
- Error handling and retries

### 3. **VPC Architecture** (`deployment/terraform/vpc.tf`)

```
VPC: 10.0.0.0/16
├── Public Subnets (ALB)
│   ├── 10.0.0.0/24 (AZ-1)
│   └── 10.0.1.0/24 (AZ-2)
├── Private Subnets (ECS)
│   ├── 10.0.10.0/24 (AZ-1)
│   └── 10.0.11.0/24 (AZ-2)
├── NAT Gateways (2)
├── Internet Gateway (1)
└── VPC Endpoints
    ├── Bedrock Runtime
    ├── DynamoDB
    └── Secrets Manager
```

### 4. **Security Groups**

**ALB Security Group:**
```
Inbound:
  - 443 (HTTPS) from 0.0.0.0/0
  - 80 (HTTP) from 0.0.0.0/0
Outbound:
  - 8000 to ECS security group
```

**ECS Security Group:**
```
Inbound:
  - 8000 from ALB security group
Outbound:
  - 443 to VPC endpoints
  - 443 to 0.0.0.0/0 (Bedrock)
```

---

## 🚀 Deployment Options

### Option 1: ECS Fargate (Recommended)

**Best for:** Production workloads, high traffic, full control

**Steps:**
```bash
# 1. Set environment variables
export ENVIRONMENT=production
export AWS_REGION=us-east-1
export API_KEYS="key1,key2,key3"
export ALERT_EMAIL="ops@example.com"

# 2. Deploy infrastructure
cd deployment/terraform
terraform init
terraform apply -var="environment=production"

# 3. Build and push Docker image
docker build -f deployment/docker/Dockerfile -t bedrock-chat:latest .
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URL
docker tag bedrock-chat:latest $ECR_URL:latest
docker push $ECR_URL:latest

# 4. Update ECS service
aws ecs update-service \
  --cluster bedrock-chat-cluster-production \
  --service bedrock-chat-service-production \
  --force-new-deployment
```

**Cost:** ~$60-200/month (2 tasks, 1vCPU, 2GB RAM)

---

### Option 2: AWS App Runner

**Best for:** Simplest deployment, automatic scaling

**Steps:**
```bash
# 1. Create App Runner service
aws apprunner create-service \
  --service-name bedrock-chat \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "'$ECR_URL':latest",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "ENVIRONMENT": "production",
          "API_KEYS": "key1,key2"
        }
      }
    },
    "AutoDeploymentsEnabled": true
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }' \
  --health-check-configuration '{
    "Protocol": "HTTP",
    "Path": "/health"
  }'
```

**Cost:** ~$30-100/month

---

### Option 3: Elastic Beanstalk

**Best for:** Easy deployment, familiar interface

**Steps:**
```bash
# 1. Initialize Elastic Beanstalk
eb init -p docker bedrock-chat --region us-east-1

# 2. Create environment
eb create production \
  --instance-type t3.medium \
  --envvars ENVIRONMENT=production,API_KEYS=key1

# 3. Deploy
eb deploy
```

**Cost:** ~$40-150/month

---

### Option 4: Lambda + API Gateway

**Best for:** Low traffic, serverless, pay-per-use

**Steps:**
```bash
# 1. Package Lambda function
cd backend
pip install -r requirements-fastapi.txt -t package/
cp -r src package/
cd package && zip -r ../lambda.zip .

# 2. Create Lambda function
aws lambda create-function \
  --function-name bedrock-chat \
  --runtime python3.12 \
  --handler src.api.lambda_handler.handler \
  --zip-file fileb://lambda.zip \
  --role arn:aws:iam::ACCOUNT:role/lambda-bedrock-role \
  --timeout 60 \
  --memory-size 2048

# 3. Create API Gateway
aws apigatewayv2 create-api \
  --name bedrock-chat-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:us-east-1:ACCOUNT:function:bedrock-chat
```

**Cost:** ~$10-50/month (pay per request)

---

## 🔐 Security Configuration

### 1. IAM Role for ECS Task

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/bedrock-chat-*"
    },
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:*:*:secret:bedrock-chat-*"
    }
  ]
}
```

### 2. API Keys in Secrets Manager

```bash
# Create secret
aws secretsmanager create-secret \
  --name bedrock-chat-api-keys-production \
  --secret-string "key1,key2,key3"

# Retrieve secret
aws secretsmanager get-secret-value \
  --secret-id bedrock-chat-api-keys-production
```

### 3. VPC Endpoints (No Internet Access)

```bash
# Bedrock endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxx \
  --service-name com.amazonaws.us-east-1.bedrock-runtime \
  --subnet-ids subnet-xxx subnet-yyy

# DynamoDB endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxx \
  --service-name com.amazonaws.us-east-1.dynamodb \
  --route-table-ids rtb-xxx
```

---

## 📊 Monitoring & Alerts

### CloudWatch Alarms

```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name bedrock-chat-high-cpu \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2

# High latency alarm
aws cloudwatch put-metric-alarm \
  --alarm-name bedrock-chat-high-latency \
  --metric-name TargetResponseTime \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 300 \
  --threshold 2 \
  --comparison-operator GreaterThanThreshold
```

### View Logs

```bash
# Tail logs
aws logs tail /ecs/bedrock-chat-production --follow

# Query logs
aws logs filter-log-events \
  --log-group-name /ecs/bedrock-chat-production \
  --filter-pattern "ERROR"
```

---

## 🧪 Testing

### Local Testing

```bash
# Start with Docker
./scripts/quickstart.sh

# Test streaming endpoint
curl -N -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}' \
  http://localhost:8000/chat/stream

# Test non-streaming endpoint
curl -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}' \
  http://localhost:8000/chat
```

### Load Testing

```bash
# Install Apache Bench
brew install apache-bench

# Run load test
ab -n 1000 -c 10 \
  -H "X-API-Key: dev-key-123" \
  -H "Content-Type: application/json" \
  -p request.json \
  http://your-alb-url.com/chat
```

---

## 💰 Cost Breakdown

### Production (1000 conversations/day, 10 messages each)

| Component | Configuration | Monthly Cost |
|-----------|--------------|--------------|
| **ECS Fargate** | 2 tasks × 1vCPU × 2GB | $60 |
| **ALB** | 1 ALB + data transfer | $25 |
| **NAT Gateway** | 2 gateways | $65 |
| **VPC Endpoints** | 3 endpoints | $22 |
| **Bedrock** | 300K input + 600K output | $12 |
| **DynamoDB** | PAY_PER_REQUEST | $1 |
| **CloudWatch** | Logs + metrics | $10 |
| **Total** | | **~$195/month** |

### Cost Optimization

1. **Remove NAT Gateway** - Use VPC endpoints only (-$65/month)
2. **Use App Runner** - Simpler, cheaper (-$30/month)
3. **Use Lambda** - Pay per request (-$150/month for low traffic)

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
ENVIRONMENT=production
AWS_REGION=us-east-1
API_KEYS=key1,key2,key3

# Optional
BEDROCK_MODEL_ID=anthropic.claude-sonnet-4-5-20250929-v1:0
MAX_TOKENS=4096
TEMPERATURE=0.7
LOG_LEVEL=INFO
```

### Config File (`backend/config.yaml`)

```yaml
environment: production

bedrock:
  model_id: "anthropic.claude-sonnet-4-5-20250929-v1:0"
  region: "us-east-1"
  max_tokens: 4096
  temperature: 0.7

dynamodb:
  connections_table: "bedrock-chat-connections-production"
  conversations_table: "bedrock-chat-conversations-production"
  ttl_days: 30

conversation:
  max_history_messages: 20
  summarization_trigger: 15
  system_prompt: "You are a helpful insurance customer support assistant."

logging:
  level: "INFO"
  json_format: true
```

---

## 🚨 Troubleshooting

### Issue: Streaming not working

**Solution:**
```bash
# Check if nginx/ALB is buffering
# Add to ALB target group attributes:
aws elbv2 modify-target-group-attributes \
  --target-group-arn arn:aws:elasticloadbalancing:... \
  --attributes Key=deregistration_delay.timeout_seconds,Value=30
```

### Issue: High latency

**Solution:**
```bash
# Enable VPC endpoints for Bedrock
# Check NAT Gateway bandwidth
# Increase ECS task count
```

### Issue: Authentication failing

**Solution:**
```bash
# Verify API keys in Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id bedrock-chat-api-keys-production

# Check ECS task role permissions
```

---

## 📚 Next Steps

1. **Deploy to development** environment first
2. **Run load tests** to verify performance
3. **Set up CI/CD** pipeline (GitHub Actions)
4. **Configure custom domain** with Route 53
5. **Add SSL certificate** with ACM
6. **Enable WAF** for DDoS protection
7. **Set up backup** for DynamoDB tables

---

## 📞 Support

- **Documentation**: See `ENTERPRISE_README.md`
- **Issues**: GitHub Issues
- **Email**: support@example.com

---

**Built with**: AWS Bedrock, FastAPI, ECS Fargate, Terraform, Docker

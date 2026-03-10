# Customer Support Ticket Agent

Multi-KB agent with automatic issue resolution and escalation logic.

## Architecture
```
User → Bedrock Agent → Action Groups:
                        ├── search_solutions (Pinecone + Bedrock KB)
                        ├── create_ticket (DynamoDB)
                        ├── escalate_to_human
                        └── check_warranty
```

## Features
- **Dual Knowledge Bases**: Pinecone (product docs) + Bedrock KB (policies)
- **Auto-resolution**: Searches solutions before creating tickets
- **Smart Escalation**: Escalates complex issues with context
- **Warranty Validation**: Checks product warranty status

## Setup
```bash
# 1. Create Pinecone index with product docs
python setup_pinecone.py

# 2. Create Bedrock Knowledge Base (policies)
aws bedrock-agent create-knowledge-base \
  --name support-policies \
  --role-arn arn:aws:iam::ACCOUNT:role/bedrock-kb-role

# 3. Deploy Lambda
cd lambda && zip -r functions.zip . && cd ..
aws lambda create-function --function-name support-tools \
  --runtime python3.10 --handler tools.handler \
  --zip-file fileb://lambda/functions.zip \
  --role arn:aws:iam::ACCOUNT:role/lambda-execution

# 4. Create DynamoDB table
aws dynamodb create-table --table-name support-tickets \
  --attribute-definitions AttributeName=ticket_id,AttributeType=S \
  --key-schema AttributeName=ticket_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 5. Create agent
python create_agent.py
```

## Demo
```bash
python demo.py
```

**Sample**:
```
User: My laptop won't turn on
Agent: Let me search for solutions... Found 3 articles. Try holding power for 10 seconds.
User: That didn't work
Agent: I'll create a ticket and escalate to our technical team. Ticket #TKT-20260308...
```

## Cost
- Pinecone: Free tier
- Bedrock KB: $0.10/GB/month
- DynamoDB: $0.01/month
- Lambda: $0.20/1M requests

**Total**: <$2/month

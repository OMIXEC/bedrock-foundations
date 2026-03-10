# E-commerce Product Assistant

Customer-facing shopping assistant with Pinecone KB, session management, and cart persistence.

## Architecture
```
User → Bedrock Agent → Action Groups:
                        ├── search_products (Pinecone)
                        ├── add_to_cart (DynamoDB)
                        ├── check_inventory
                        └── get_recommendations
```

## Setup
```bash
# 1. Create Pinecone index
python setup_pinecone.py

# 2. Deploy Lambda
cd lambda && zip -r functions.zip . && cd ..
aws lambda create-function --function-name ecommerce-tools \
  --runtime python3.10 --handler tools.handler \
  --zip-file fileb://lambda/functions.zip \
  --role arn:aws:iam::ACCOUNT:role/lambda-execution

# 3. Create DynamoDB table
aws dynamodb create-table --table-name ecommerce-sessions \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 4. Create agent
python create_agent.py
```

## Demo
```bash
python demo.py
```

**Sample**:
```
User: Show me wireless headphones under $100
Agent: Found 5 headphones... Sony WH-1000XM4 at $89.99
User: Add Sony to cart
Agent: Added. Cart total: $89.99
```

## Cost
- Pinecone: Free tier
- DynamoDB: $0.01/month
- Lambda: $0.20/1M requests
- Bedrock: ~$0.003/request

**Total**: <$1/month

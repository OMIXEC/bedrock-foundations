# Order Tracking Agent

Session-based order tracking with shipping API integration.

## Features
- **Multi-Order Tracking**: Track multiple orders in single conversation
- **Real-Time Updates**: Live shipment tracking
- **Returns Management**: Initiate returns with RMA generation
- **Address Updates**: Change delivery address (if not shipped)

## Tools
- `lookup_order` - Find order by ID
- `track_shipment` - Get real-time tracking updates
- `initiate_return` - Start return process
- `update_address` - Change delivery address

## Setup
```bash
# 1. Create DynamoDB table
aws dynamodb create-table --table-name order-tracking-sessions \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 2. Deploy Lambda
cd lambda && zip -r functions.zip . && cd ..
aws lambda create-function --function-name order-tracking-tools \
  --runtime python3.10 --handler tools.handler \
  --zip-file fileb://lambda/functions.zip \
  --role arn:aws:iam::ACCOUNT:role/lambda-execution

# 3. Create agent
python create_agent.py
```

## Demo
```bash
python demo.py
```

**Sample**:
```
User: Where's my order ORD-12345?
Agent: Order ORD-12345 is in transit via UPS. Tracking: 1Z999AA10123456784. ETA: March 10

User: Track that shipment
Agent: Currently in Memphis, TN. Last update: March 8, 2:30 PM
      Recent events:
      - In transit (Memphis, TN)
      - Departed facility (Louisville, KY)

User: Also check ORD-12346
Agent: Order ORD-12346 was delivered on March 5 via FedEx

User: I need to return ORD-12345
Agent: Return approved. RMA: RMA-20260308... Return label: [link]
```

## Session Management
- Tracks all orders queried in conversation
- Maintains context across multiple order lookups
- Auto-expires after 30 minutes of inactivity

## Cost
<$1/month (DynamoDB + Lambda)

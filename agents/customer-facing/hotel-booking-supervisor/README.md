# Hotel Booking Supervisor Agent

Multi-agent supervisor pattern with search, pricing, and booking sub-agents.

## Architecture
```
User → Supervisor Agent → Search Agent (find hotels)
                        → Pricing Agent (calculate costs)
                        → Booking Agent (process reservation)
```

## Features
- **Multi-Agent Orchestration**: Supervisor delegates to specialized agents
- **Session Management**: Maintains search criteria and selections
- **Dynamic Pricing**: Calculates costs with discounts
- **Room Upgrades**: Handles room type changes

## Tools
- `search_hotels` - Delegates to search agent
- `calculate_total_cost` - Delegates to pricing agent
- `apply_discounts` - Applies customer tier discounts
- `process_booking` - Delegates to booking agent

## Setup
```bash
# 1. Create sub-agents
python create_sub_agents.py

# 2. Create DynamoDB table
aws dynamodb create-table --table-name hotel-booking-sessions \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 3. Deploy supervisor Lambda
cd lambda && zip -r functions.zip . && cd ..
aws lambda create-function --function-name hotel-supervisor \
  --runtime python3.10 --handler supervisor.handler \
  --zip-file fileb://lambda/functions.zip \
  --role arn:aws:iam::ACCOUNT:role/lambda-execution

# 4. Create supervisor agent
python create_supervisor.py
```

## Demo
```bash
python demo.py
```

**Sample**:
```
User: Find hotels in NYC for 2 guests, March 15-17
Supervisor: [Delegates to Search Agent]
Agent: Found 5 hotels... Hilton Midtown $299/night

User: Calculate cost for Hilton, deluxe room
Supervisor: [Delegates to Pricing Agent]
Agent: 2 nights × $349 = $698. With Gold discount: $628

User: Book it
Supervisor: [Delegates to Booking Agent]
Agent: ✓ Booked. Confirmation BKG-20260308
```

## Sub-Agents
1. **Search Agent**: Hotel availability and filtering
2. **Pricing Agent**: Cost calculation and discounts
3. **Booking Agent**: Reservation processing

## Cost
~$1/month (3 agents + DynamoDB)

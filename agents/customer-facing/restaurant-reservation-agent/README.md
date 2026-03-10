# Restaurant Reservation Agent

External API integration with validation rules for restaurant bookings.

## Features
- **Availability Check**: Real-time slot checking
- **Validation Rules**: Party size (max 12), business hours, blackout dates
- **Booking Management**: Create, modify, cancel reservations
- **Confirmation**: Automated email confirmations

## Tools
- `check_availability` - Check available time slots
- `create_reservation` - Book a table
- `modify_booking` - Change date/time/party size
- `send_confirmation` - Send email confirmation

## Setup
```bash
# 1. Create DynamoDB table
aws dynamodb create-table --table-name restaurant-reservations \
  --attribute-definitions AttributeName=reservation_id,AttributeType=S \
  --key-schema AttributeName=reservation_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 2. Deploy Lambda
cd lambda && zip -r functions.zip . && cd ..
aws lambda create-function --function-name restaurant-tools \
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
User: Book table for 4 tomorrow at 7pm
Agent: Checking availability... ✓ Available at Italian Bistro
User: Confirm booking
Agent: ✓ Reserved. Confirmation RES-20260308... sent to your email
```

## Validation Rules
- Party size: 1-12 guests
- Business hours: 11:00-22:00
- Advance booking: Min 1 hour, max 90 days
- Blackout dates: Major holidays

## Cost
<$1/month (DynamoDB + Lambda)

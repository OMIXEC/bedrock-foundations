# Appointment Scheduling Agent

Calendar integration with conflict detection and automated reminders.

## Features
- **Availability Check**: Real-time slot checking (9 AM - 5 PM)
- **Conflict Detection**: Prevents double-booking
- **Automated Reminders**: Email + SMS (24h and 2h before)
- **Rescheduling**: Easy appointment changes

## Tools
- `check_availability` - Find available time slots
- `book_appointment` - Schedule appointment
- `send_reminders` - Set up automated reminders
- `reschedule` - Change appointment time

## Setup
```bash
# 1. Create DynamoDB table
aws dynamodb create-table --table-name appointments \
  --attribute-definitions AttributeName=appointment_id,AttributeType=S \
  --key-schema AttributeName=appointment_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 2. Deploy Lambda
cd lambda && zip -r functions.zip . && cd ..
aws lambda create-function --function-name appointment-tools \
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
User: Schedule dentist appointment next week
Agent: Checking availability... Available slots on March 15:
       9:00 AM, 9:30 AM, 10:00 AM, 2:00 PM, 3:00 PM

User: Book 10 AM
Agent: ✓ Appointment confirmed for March 15 at 10:00 AM
       Confirmation: APT-20260308...
       Reminders scheduled: Email (24h before), SMS (2h before)

User: Actually, can we do 2 PM instead?
Agent: ✓ Rescheduled to March 15 at 2:00 PM
       Updated confirmation sent
```

## Conflict Detection
- Checks existing bookings before confirming
- Prevents overlapping appointments
- Suggests alternative slots if requested time is taken

## Cost
<$1/month (DynamoDB + Lambda)

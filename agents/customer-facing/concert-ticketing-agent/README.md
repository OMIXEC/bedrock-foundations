# Concert Ticketing Agent

Secure ticketing agent with identity verification, guardrails, and comprehensive ticket management.

## Architecture
```
User → Bedrock Agent (with Guardrail) → Action Groups:
                                         ├── verify_identity
                                         ├── retrieve_tickets
                                         ├── cancel_tickets
                                         ├── reschedule_tickets
                                         ├── transfer_tickets
                                         └── check_event_status
        ↓
    Session State (DynamoDB): verified_user, verification_attempts, active_tickets
        ↓
    Audit Log (CloudWatch): All operations logged
```

## Security Features

### Identity Verification
- **Multi-factor**: Email + Order ID or Email + Last 4 of card
- **Rate Limiting**: Max 3 verification attempts per session
- **Session Timeout**: 15 minutes of inactivity
- **Verification Required**: All ticket operations require verified identity

### Guardrails
- **PII Detection**: Automatically redacts sensitive data (SSN, credit cards)
- **Prompt Injection Prevention**: Blocks social engineering attempts
- **Content Filtering**: Prevents sharing ticket details with unverified users
- **Audit Logging**: All operations logged to CloudWatch

## Setup

```bash
# 1. Create Bedrock Guardrail
python create_guardrail.py

# 2. Deploy Lambda functions
cd lambda && zip -r functions.zip . && cd ..
aws lambda create-function --function-name ticketing-tools \
  --runtime python3.10 --handler tools.handler \
  --zip-file fileb://lambda/functions.zip \
  --role arn:aws:iam::ACCOUNT:role/lambda-execution

# 3. Create DynamoDB tables
aws dynamodb create-table --table-name ticketing-sessions \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

aws dynamodb create-table --table-name ticket-orders \
  --attribute-definitions AttributeName=order_id,AttributeType=S \
  --key-schema AttributeName=order_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# 4. Create agent with guardrail
python create_agent.py
```

## Demo

```bash
python demo.py
```

**Sample Conversation**:
```
User: I need to cancel my Taylor Swift tickets
Agent: I'll help you. Please provide your email and order ID for verification.

User: email@example.com and order ORD-12345
Agent: Verifying... ✓ Identity confirmed. I found 2 tickets for Taylor Swift on March 15.

User: Cancel both tickets
Agent: Checking cancellation policy... Full refund available (>7 days before event).
      Processing cancellation... ✓ Cancelled. Refund of $450 will arrive in 5-7 days.
      Confirmation sent to email@example.com

[Audit Log]: 2026-03-08 20:00:42 | session_abc123 | CANCEL_TICKETS | order_ORD-12345 | SUCCESS
```

## Tools

### verify_identity
Validates user identity using email + order_id or email + card_last4.
```python
verify_identity(email="user@example.com", order_id="ORD-12345")
# Returns: {"verified": True, "session_token": "abc123"}
```

### retrieve_tickets
Retrieves tickets for verified user (PII redacted by guardrail).
```python
retrieve_tickets(session_token="abc123")
# Returns: {"tickets": [...], "total": 2}
```

### cancel_tickets
Cancels tickets with refund policy check.
```python
cancel_tickets(session_token="abc123", ticket_ids=["TKT-001", "TKT-002"])
# Returns: {"status": "cancelled", "refund_amount": 450.00}
```

### reschedule_tickets
Reschedules tickets to different event date.
```python
reschedule_tickets(session_token="abc123", ticket_ids=["TKT-001"], new_event_id="EVT-456")
# Returns: {"status": "rescheduled", "price_difference": 25.00}
```

### transfer_tickets
Transfers tickets to another email (requires recipient verification).
```python
transfer_tickets(session_token="abc123", ticket_ids=["TKT-001"], recipient_email="friend@example.com")
# Returns: {"status": "transfer_initiated", "verification_sent": True}
```

### check_event_status
Checks for event cancellations or venue changes.
```python
check_event_status(event_id="EVT-123")
# Returns: {"status": "scheduled", "venue": "Madison Square Garden", "date": "2026-03-15"}
```

## Guardrail Configuration

```json
{
  "name": "ticketing-guardrail",
  "blockedInputMessaging": "I cannot process requests containing sensitive information.",
  "blockedOutputsMessaging": "I cannot share ticket details without verification.",
  "contentPolicyConfig": {
    "filtersConfig": [
      {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "NONE"}
    ]
  },
  "sensitiveInformationPolicyConfig": {
    "piiEntitiesConfig": [
      {"type": "EMAIL", "action": "ANONYMIZE"},
      {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "BLOCK"},
      {"type": "US_SOCIAL_SECURITY_NUMBER", "action": "BLOCK"}
    ]
  }
}
```

## Session Management

Sessions track:
- `verified_user`: Boolean flag
- `verification_attempts`: Counter (max 3)
- `active_tickets`: List of accessible tickets
- `last_activity`: Timestamp for timeout
- `session_token`: Unique identifier

## Audit Logging

All operations logged to CloudWatch:
```
timestamp | session_id | operation | resource_id | status | user_email
```

## Cost Estimate

- DynamoDB: $0.02/month (2 tables)
- Lambda: $0.20/1M requests
- Bedrock Guardrail: $0.75/1000 requests
- Bedrock Agent: ~$0.003/request
- CloudWatch Logs: $0.50/GB

**Total**: ~$2/month for testing

## Security Best Practices

1. **Never log PII**: Use guardrail to redact before logging
2. **Rotate session tokens**: Expire after 15 minutes
3. **Rate limit verification**: Block after 3 failed attempts
4. **Audit everything**: Log all ticket operations
5. **Validate inputs**: Check email format, order ID pattern
6. **Encrypt at rest**: Enable DynamoDB encryption
7. **Use HTTPS only**: All API calls over TLS

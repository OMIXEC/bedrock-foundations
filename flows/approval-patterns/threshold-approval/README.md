# Threshold-Based Approval Flow

Auto-approve or escalate based on amount thresholds.

## Logic
- **< $50**: Auto-approve instantly
- **$50-$500**: Escalate to manager
- **> $500**: Escalate to director

## Architecture
```
Input (amount, customer, reason)
  ↓
Condition Node (check amount)
  ├─ < $50 → Auto-Approve → Output
  ├─ $50-$500 → Manager Approval → Output
  └─ > $500 → Director Approval → Output
```

## Deploy
```bash
python deploy_flow.py
```

## Test
```bash
python test_flow.py --amount 30 --customer "CUST-001" --reason "Defective product"
# Output: "✓ Auto-approved: Refund of $30 processed for CUST-001"

python test_flow.py --amount 250 --customer "CUST-002" --reason "Wrong item shipped"
# Output: "⚠ Escalated to manager: Refund $250 requires approval"

python test_flow.py --amount 1500 --customer "CUST-003" --reason "Service failure"
# Output: "⚠ Escalated to director: High-value refund $1500 requires executive approval"
```

## Use Cases
- Refund processing
- Discount approvals
- Credit limit increases
- Expense reimbursements

## Cost
- Bedrock Flow: $0.002/invocation
- Claude Sonnet: ~$0.003/request

**Total**: ~$0.005/request

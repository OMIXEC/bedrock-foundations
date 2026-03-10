# Conditional Routing Approval Flow

Dynamic routing to appropriate approvers based on request type and department.

## Routing Logic
- **IT Requests** → IT Manager
- **Marketing Requests** → Marketing Director
- **Operations Requests** → Operations Supervisor
- **Finance Requests** → Finance Controller

## Architecture
```
Input (request_type, department, amount, details)
  ↓
Classify Request (LLM determines approver)
  ↓
Condition Node (route to appropriate approver)
  ├─ IT Manager → Approval Decision → Output
  ├─ Marketing Director → Approval Decision → Output
  ├─ Ops Supervisor → Approval Decision → Output
  └─ Finance Controller → Approval Decision → Output
```

## Deploy
```bash
python deploy_flow.py
```

## Test
```bash
python test_flow.py --type "Software purchase" --dept "IT" --amount 5000
# Output: Routed to IT Manager → APPROVED (within IT budget)

python test_flow.py --type "Ad campaign" --dept "Marketing" --amount 50000
# Output: Routed to Marketing Director → APPROVED (aligns with Q1 strategy)

python test_flow.py --type "Equipment" --dept "Operations" --amount 15000
# Output: Routed to Ops Supervisor → APPROVED (operational necessity)
```

## Use Cases
- Purchase requests by department
- Budget approvals
- Resource allocation
- Policy exceptions

## Cost
~$0.006/request (classification + approval)

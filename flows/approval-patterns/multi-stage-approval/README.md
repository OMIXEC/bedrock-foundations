# Multi-Stage Sequential Approval Flow

Sequential approval chain where each stage can approve, reject, or escalate.

## Stages
1. **L1 Support**: Initial review
2. **L2 Specialist**: Technical validation
3. **Manager**: Business approval
4. **Director**: Final executive sign-off

## Architecture
```
Input → Iterator (stages) → Decision Node → Condition:
                                            ├─ APPROVE → End
                                            ├─ REJECT → End
                                            └─ ESCALATE → Next Stage
        ↓
    Collector (all decisions) → Output
```

## Deploy
```bash
python deploy_flow.py
```

## Test
```bash
python test_flow.py --request "Server upgrade" --priority "high"
# Output:
# L1: ESCALATE - Requires technical review
# L2: ESCALATE - Budget approval needed
# Manager: APPROVE - Approved within budget
# Final: APPROVED at Manager level
```

## Use Cases
- Complex support cases
- Budget approvals
- Policy exceptions
- Contract reviews

## Cost
~$0.012/request (4 stages × $0.003)

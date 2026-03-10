# Parallel Review Approval Flow

Unanimous approval required from multiple departments simultaneously.

## Reviewers
- **Legal**: Compliance, liability, terms
- **Finance**: Budget, ROI, payment terms
- **Operations**: Feasibility, resources, timeline

## Architecture
```
Input (contract, amount)
  ├─ Legal Review ──┐
  ├─ Finance Review ─┼─ Collector → Check Unanimous → Output
  └─ Ops Review ────┘
```

## Deploy
```bash
python deploy_flow.py
```

## Test
```bash
python test_flow.py --contract "Vendor agreement" --amount 50000
# Output:
# Legal: APPROVE - Terms acceptable
# Finance: APPROVE - Within budget
# Operations: APPROVE - Resources available
# Result: ✓ APPROVED (unanimous)

python test_flow.py --contract "High-risk contract" --amount 500000
# Output:
# Legal: APPROVE - With modifications
# Finance: REJECT - Exceeds budget
# Operations: APPROVE - Feasible
# Result: ✗ REJECTED (not unanimous)
```

## Use Cases
- Contract approvals
- Major purchases
- Policy changes
- Strategic initiatives

## Cost
~$0.009/request (3 parallel reviews × $0.003)

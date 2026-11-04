---
name: ship-gate
summary: Final gate before release: verify diff matches contract, validation passed, no secrets or surprises.
---

# Ship Gate

## Purpose
Final verification before releasing code. Confirm the diff matches the task contract, validation passed, and no secrets or surprises.

## Checklist

### 1. Diff Matches Task Contract
- Use `minimalist_diff_budget` to compare planned vs. actual files
- Use `minimalist_review_change` to score the diff
- Verify scope drift is within budget (≤5%)
- Use `planner_review_task_contract` to validate

### 2. Validation Passed
- All required tests pass
- No type errors (LSP diagnostics clean)
- AOP consistency check passed
- PyRAG verification passed (for non-trivial changes)
- Oracle review passed

### 3. No Secrets
- Scan for API keys, passwords, tokens, certificates
- Check `.env` files are not committed
- Check no hardcoded credentials
- Use `grep` to search for common secret patterns

### 4. No Dependency Surprises
- Check for new dependencies not in the task contract
- Verify dependency versions are pinned
- Check for known vulnerabilities in new dependencies

### 5. No Scope Drift
- Use `planner_review_task_contract` to measure drift
- If drift > 5%, escalate to PM
- Record drift percentage

### 6. Oracle Ran
- Confirm Oracle review was completed
- Confirm Oracle verdict was PASS or CONDITIONAL (not FAIL)
- Confirm all CONDITIONAL items were resolved

## Output Format
```yaml
ship_gate:
  task_ref: <reference>
  diff_matches_contract: <true|false>
  validation_passed: <true|false>
  secrets_found: <count>
  dependency_surprises: <count>
  scope_drift_percent: <percentage>
  oracle_verdict: <PASS|CONDITIONAL|FAIL>
  verdict: <SHIP|HOLD|BLOCK>
  blockers: <list>
```

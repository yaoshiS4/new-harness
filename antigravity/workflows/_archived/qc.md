---
name: qc
summary: Independent quality control review: compare implementation against contract, check tests, and verify scope.
---

# QC (Quality Control)

## Purpose
Independent review that compares implementation against the task contract, checks tests, and verifies scope.

## Steps

### 1. Read Task Contract
- Retrieve the approved task contract
- Identify acceptance criteria, allowed files, required tests, scope drift budget

### 2. Compare Implementation
- Use `codegraph:changed_symbols` to see what changed
- Use `minimalist_review_change` to score minimalism
- Use `minimalist_diff_budget` to verify file count
- Compare changes against the contract scope

### 3. Check Tests
- Verify required tests exist and pass
- Check test coverage for new code
- Verify no regressions in existing tests
- Use `structured_validation` skill for test result summarization

### 4. Check Scope Drift
- Use `planner_review_task_contract` to measure drift
- If drift > 5%, flag for PM review
- Record drift percentage

### 5. UI-Specific Checks (if applicable)
- Confirm shared design elements were created first
- Verify UI components reuse shared primitives
- Check accessibility (keyboard nav, ARIA labels, contrast)
- Check responsive behavior (mobile, tablet, desktop)

### 6. Report Findings
```yaml
qc_review:
  task_ref: <reference>
  verdict: <approve|request_changes|escalate>
  findings:
    - severity: <critical|major|minor|informational>
      category: <scope_drift|test_gap|regression|accessibility|minimalism>
      description: <what was found>
      evidence: <specific evidence>
      recommendation: <how to fix>
  scope_drift_percent: <percentage>
  minimalism_score: <score>
  test_coverage: <percentage>
```

# Scope Lock Gate

Freezes the Story Shards, leased allowed_files, and acceptance criteria prior to Builder dispatch.

## Purpose
Freeze the atomic task list and leased file scopes after exploration and clarification. No new task or file path may be added without an explicit scope change request.

## Gate Check
1. All atomic tasks have acceptance criteria.
2. Validation target is explicit.
3. Scope drift budget is recorded.
4. PM or user approval is recorded.
5. Open uncertainties are either resolved or represented as residual risk.

## Exit Criteria
- Task list is locked.
- Later scope changes re-open this gate.

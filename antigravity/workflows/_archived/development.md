---
name: development
summary: Main development workflow that routes to new or existing development based on task type.
---

# Development

## Purpose
Route development tasks to the appropriate sub-workflow based on whether the work is new or modifies existing code.

## Decision Tree

```
Is this new code (no existing implementation)?
├── YES → new_development workflow
└── NO → existing_development workflow
```

## Steps

### 1. Read Task Contract
- Retrieve the approved task contract via `planner_review_task_contract`
- Identify: scope, allowed files, required tests, scope drift budget
- Classify complexity: atomic, medium, epic
- Read project-local SOT docs first when they exist, starting with `docs/STATUS.md`, `docs/README.md`, and workspace `AGENTS.md`
- Use `codex_knowledge` to confirm the indexed project context before broad repo scans

### 2. Determine Development Type
- **New Development**: No existing implementation for this feature
  - Route to `new_development` workflow
  - Requires full document chain (business case → atomic tasks)
- **Existing Development**: Modifying or extending existing code
  - Route to `existing_development` workflow
  - Requires baseline understanding and impact analysis

### 3. Route to Sub-Workflow
- Use `planner_suggest_topology` to determine the execution topology
- For atomic tasks: sequential pipeline with single agent
- For medium tasks: sequential pipeline with Oracle review
- For epic tasks: wave execution with multiple agents

### 4. Monitor Execution
- Track context budget per `context_budget/policy.md`
- Check progress every 5 tool calls per `monotonic_progress` guardrail
- If budget exceeded, checkpoint via `codex_knowledge_handoff_checkpoint`
- For existing codebases with a native regression gate, run `project-regression assert-fresh` before widening the edit surface

### 5. Hand Off to Verification
- After implementation, route to `verification_before_completion` skill
- Run `project-regression run` when the project exposes a native regression entrypoint
- Then route to Oracle review

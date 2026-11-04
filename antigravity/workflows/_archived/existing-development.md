---
name: existing-development
summary: Modify existing code with impact analysis, minimal diffs, and regression checks.
---

# Existing Development

## Purpose
Safely modify existing code by understanding impact, confirming scope, and validating changes.

## Steps

### 1. Read Current State
- Read the current docs, story, and baseline
- Read project-local SOT docs first when they exist, starting with `docs/STATUS.md`, `docs/README.md`, and workspace `AGENTS.md`
- Use `codex_knowledge_project_context` to load project context
- Use `codex_knowledge_graph_query` to understand dependencies
- Use `codegraph:summarize_path` on files to be modified

### 2. Impact Analysis
- Identify all files that import or reference the code to be changed
- Use `codegraph:changed_symbols` to preview symbol changes
- Estimate blast radius:
  ```yaml
  impact:
    direct_files: <files directly modified>
    dependent_files: <files that import/reference changed code>
    test_files: <test files that need updating>
    blast_radius: <small|medium|large>
  ```

### 3. Confirm Scope with PM
- If the change is not obviously atomic, confirm with PM
- Use `planner_review_task_contract` to validate scope
- If impact exceeds scope budget, escalate to PM

### 4. Implement Minimal Change
- Make the smallest possible change that achieves the goal
- Use `minimalist_review_change` to verify minimalism
- Use `minimalist_diff_budget` to verify file count is within budget

### 5. Validate
- Run `project-regression assert-fresh` before claiming the baseline is safe to extend when the project exposes that gate
- Run `project-regression run` as the default regression entrypoint when available
- Run existing tests to confirm no regressions
- Run new tests for the changed behavior
- Use `codex_knowledge_graph_query` for logical consistency
- Use `verification_before_completion` skill for full verification

### 6. Oracle Review
- Submit for Oracle review
- Address any vetoes with evidence and remediation
- Re-run validation after fixes

## Guardrails
- Update only the approved scope
- Never widen scope beyond the task contract
- Re-run tests and Oracle before release

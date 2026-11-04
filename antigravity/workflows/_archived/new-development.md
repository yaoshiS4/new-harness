---
name: new-development
summary: Build new features from scratch with full document chain, phase gates, and mandatory testing.
---

# New Development

## Purpose
Build new features from scratch with a complete document chain, phase gates, and mandatory testing.

## Steps

### 1. Build Document Chain
- Business case → PRD → architecture → atomic task list
- Use `prd_architect` skill for PRD creation
- Use `senior_architect` skill for architecture decisions
- Use `planner_review_task_contract` for task contract creation

### 2. Gate Each Phase with Oracle
- After PRD: Oracle review for scope and feasibility
- After architecture: Oracle review for technical decisions
- After task list: Oracle review for completeness
- Use `codex_knowledge_graph_query` at each gate

### 3. Define Shared Design Elements (UI Work)
- For UI work, establish shared design elements FIRST:
  - Layout grid, spacing, typography, color tokens
  - Shared components and states
  - Reuse these primitives before building screen-specific UI
- Use `visual_engineer` agent for design review

### 4. Implement from Atomic Tasks
- Pick tasks in dependency order
- Use `builder_backend` or `builder_frontend` agents
- Use `minimalist_coder` for minimal diffs
- Track scope drift per `scope_drift_control` guardrail

### 5. Run Mandatory Tests
- Unit tests for new logic
- Integration tests for new flows
- Edge case tests for critical paths
- Use `structured_validation` skill for test result summarization

### 6. Record Scope Drift
- Use `planner_review_task_contract` to check drift at each phase
- If drift exceeds 5%, escalate to PM
- Record drift in `codex_knowledge_knowledge_capture`

### 7. Model Routing
- Use the model routing catalog for agent selection:
  - Go models (Codex primary models) for primary tasks
  - Zen models (gpt-5.4-mini, etc.) for fallback
  - Mini models for cheap reads and summaries

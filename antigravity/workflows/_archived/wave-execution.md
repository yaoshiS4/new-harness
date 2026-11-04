---
name: wave-execution
summary: Execute independent work slices in parallel with one writer per branch and Oracle review after each wave.
---

# Wave Execution

## Purpose
Execute independent work slices in parallel when the task contains independent subtasks that benefit from parallel writers.

## When to Use
- Task contains independent slices (no file dependencies between slices)
- PM has approved wave execution
- Each slice can be verified independently

## Steps

### 1. Split the Epic into Independent Waves
- Identify independent work slices
- Each slice must have:
  - Clear scope and acceptance criteria
  - No file dependencies on other slices
  - Its own verification plan
- Use `planner_suggest_topology` to validate wave topology

### 2. Assign One Writer Per Branch
- Each wave agent gets exactly one git branch or worktree
- Use `worktree_isolation` skill for parallel work
- Create lock files in `.agent-locks/` for file ownership
- Each agent gets proportional context budget

### 3. Run Oracle After Each Wave
- After all agents in a wave complete, run Oracle review
- Oracle checks each slice independently
- If any slice fails, only that slice is revised
- Use `independent_ensemble/merge_policy.md` for merge decisions

### 4. Integrate After Spot Checks Pass
- Merge only validated outputs
- Do not merge speculative or unreviewed work
- Run integration tests after merge
- Use `codex_knowledge_handoff_checkpoint` to save state before merge

### 5. Sync Documentation
- Run `doc_sync_worker` through the epic closeout workflow
- Sync approved summaries to the local Obsidian SOT
- Record validated lessons in memory stores

## Guardrails
- One writer per branch remains mandatory
- No sibling-to-sibling messaging between wave agents
- Each agent returns: changed files, evidence, risks, next action
- PM manages merge order and conflict resolution

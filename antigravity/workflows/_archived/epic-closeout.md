---
name: epic-closeout
summary: Close out an epic after all phases are approved, integrated, and validated.
---

# Epic Closeout

## Purpose
Ensure an epic is fully approved, integrated, and documented before closing.

## Prerequisites
- All phases have passed Oracle review
- All tests pass
- All acceptance criteria met
- No scope drift beyond budget

## Steps

### 1. Confirm Epic Status
- Verify all task contracts are complete
- Verify all Oracle reviews passed
- Verify no outstanding vetoes or remediation items
- Check scope drift: `planner_review_task_contract` confirms drift ≤ 5%

### 2. Run Final Validation
- Run full test suite
- Run `codex_knowledge_graph_query` for final consistency check
- Run `minimalist_review_change` for final minimalism check
- Record results:
  ```yaml
  final_validation:
    tests_passing: <count>
    tests_failing: <count>
    aop_conflicts: <count>
    minimalism_score: <score>
    scope_drift_percent: <percentage>
  ```

### 3. Sync Documentation
- Run `document_sync` workflow
- Use `doc_sync_worker` agent for approved summaries
- Sync to Obsidian vault via `document-sync` skill

### 4. Capture Lessons
- Use `codex_knowledge_knowledge_capture` for durable lessons
- Use `codex_knowledge_graph_upsert` for entity updates
- Use `codex_knowledge_orchestration_lesson` for process lessons
- Use `codex_knowledge_memory_store` for KPI measurements

### 5. Record Trace
- Use `codex_knowledge_handoff_checkpoint` for the complete epic trace
- Use `codex_knowledge_handoff_checkpoint` for final state

### 6. Close Out
- Return compact closeout summary:
  ```yaml
  epic_closeout:
    epic_ref: <reference>
    phases_completed: <count>
    oracle_reviews_passed: <count>
    tests_passing: <count>
    scope_drift_final: <percentage>
    lessons_captured: <count>
    docs_synced: <true|false>
    status: <closed>
  ```

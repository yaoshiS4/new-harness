---
name: convergence-analysis
summary: Post-implementation assessment comparing delivered codebase against spec/plan/tasks. Identifies gaps and scope creep. Runs after Implementation, before Final Review.
---

# Convergence Analysis

## Purpose
Compare the delivered codebase against the original spec, plan, and tasks. Surface gaps (what was specified but not built) and scope creep (what was built but not specified). This is the final checkpoint before Final Review.

## When to Run
- After Implementation Gate (Phase 7), before Final Review Gate (Phase 9)
- After any revision cycle following Final Review feedback

## Steps

### 1. Load Baseline Artifacts
- Load the approved feature spec (all requirements, ACs, out-of-scope)
- Load the approved implementation plan (all phases, files, and tech choices)
- Load the approved task breakdown (all tasks, traceability matrix)

### 2. Inventory Delivered Code
- List all files created or modified (via `git diff --name-only` against baseline)
- List all functions/classes/symbols added (via `codegraph:changed_symbols`)
- List all tests added and their pass/fail status (via test runner output)
- List all dependencies added (via package manager diff)

### 3. Compare: Spec Requirements vs. Delivered Implementation

| Check | Method |
|-------|--------|
| Every AC is implemented | Scan codebase for each acceptance criteria from spec |
| Every user story has working code | Verify each US has corresponding implemented files |
| Every NFR is met | Check performance, accessibility, theme support |
| Out-of-scope items stay out | Verify no code exists for excluded features |

### 4. Compare: Planned Files vs. Actual Files

| Check | Method |
|-------|--------|
| All planned files were created | Compare plan's file list against `git diff --name-only` |
| No unplanned files were created | Flag files in diff not in plan |
| Unplanned files have justification | If extra files exist, verify they're needed (e.g., test files, type definitions) |

### 5. Compare: Task Completion vs. Task List

| Check | Method |
|-------|--------|
| All tasks completed or deferred | Match task status against implementation |
| Task dependencies respected | Verify dependency chain wasn't violated |
| Phase checkpoints passed | Each phase checkpoint verified |

### 6. Identify Gaps
Gaps are **spec requirements that were NOT implemented**:

```yaml
gaps:
  - requirement: <spec reference (e.g., US-1 AC-3)>
    description: <what was specified>
    severity: <critical|major|minor>
    reason: <why it was missed (e.g., "overlooked", "deferred", "technically infeasible")>
    action: <what to do (e.g., "append as new task", "update spec to remove", "escalate to PM")>
```

### 7. Identify Scope Creep
Scope creep is **code that was built but NOT specified**:

```yaml
scope_creep:
  - file: <path>
    description: <what was built that wasn't in spec>
    severity: <critical|major|minor>
    justification: <was this necessary? (e.g., "needed for test setup", "accidental overbuild")>
    action: <what to do (e.g., "remove", "update spec to include", "escalate to PM")>
```

### 8. Assess Human Continuation Readiness

| Check | Rule |
|-------|------|
| All documents are self-contained | Can a human read any document and understand it independently? |
| E2E verification steps exist and work | Run the spec's Section 7 commands — do they pass? |
| File references are accurate | Do document file paths match actual files? |
| Out-of-scope is clear | Can a human tell what was intentionally NOT built? |
| How-to-continue guide is complete | Task breakdown's Human E2E Continuation Guide is filled in |

### 9. Emit Convergence Report

```yaml
convergence_report:
  task_ref: <task contract reference>
  verdict: <PASS|GAPS_EXIST|CRITICAL_GAPS>
  
  spec_coverage:
    total_requirements: <count>
    implemented: <count>
    not_implemented: <count>
    coverage_percent: <percentage>
  
  file_alignment:
    planned_files: <count>
    actual_files: <count>
    unplanned_files: <count>
    missing_files: <count>
  
  task_completion:
    total_tasks: <count>
    completed: <count>
    deferred: <count>
    missed: <count>
  
  gaps_found: <count>
  scope_creep_found: <count>
  
  human_continuation_ready: <true|false>
  
  action:
    - if gaps: append as new tasks to roadmap
    - if scope_creep: decide remove or retro-document
    - if not human_continuation_ready: fix docs before shipping
  
  next_action: <proceed_to_final_review|fix_gaps|escalate>
```

## Transition Rules
- **PASS**: 100% spec coverage, 0 scope creep, human-ready → proceed to Final Review
- **GAPS_EXIST**: Minor gaps (≤5% coverage) → append as tasks, proceed with caveat
- **CRITICAL_GAPS**: Major gaps (>5% coverage) or scope creep → escalate to PM, may re-open Implementation

## Exit Criteria
- All critical gaps documented as new tasks in roadmap
- Scope creep items resolved (removed or spec updated)
- Human continuation readiness confirmed
- Record: `codex_knowledge_handoff_checkpoint(name=sol:<task_id>:convergence)`

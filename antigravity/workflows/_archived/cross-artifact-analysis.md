---
name: cross-artifact-analysis
summary: Automated verification that spec → plan → tasks chain is complete, consistent, and covers every requirement. Runs between Plan Review and Implementation.
---

# Cross-Artifact Consistency Analysis

## Purpose
Verify the complete document chain (spec → plan → tasks) is internally consistent before implementation begins. This gate catches gaps and orphans that would otherwise surface only after code is written.

## When to Run
- After Plan Review Gate (Phase 5), before Implementation Gate (Phase 7)
- Also triggered by any downstream artifact change (plan or task update)

## Steps

### 1. Load All Artifacts
- Load the feature spec (SPEC.md or equivalent)
- Load the implementation plan (PLAN.md or equivalent)
- Load the task breakdown (TASKS.md or equivalent)

### 2. Extract Requirement Inventory
From the spec, extract:
- Every user story ID (US-1, US-2, ...)
- Every acceptance criteria (US-1 AC-1, ...)
- Every functional requirement
- Every non-functional requirement
- Every out-of-scope declaration

### 3. Check Forward Traceability (Spec → Plan)
| Check | Rule |
|-------|------|
| Every user story has a plan item | Each US-ID must appear in the plan or be marked as deferred |
| Every NFR has a plan item | Performance, accessibility, themes must have corresponding plan sections |
| Every out-of-scope item is reaffirmed in plan | Plan must restate spec's out-of-scope items |
| No plan items have no spec origin | Every plan section must trace to a spec requirement |

### 4. Check Forward Traceability (Plan → Tasks)
| Check | Rule |
|-------|------|
| Every plan phase has tasks | Each phase in the plan must have at least one task |
| Every planned file appears in a task | Files listed in plan must be covered by tasks |
| Task dependencies match plan phases | Task phase groupings must match plan phase structure |

### 5. Check Backward Traceability (Tasks → Spec)
| Check | Rule |
|-------|------|
| Every task traces to a spec requirement | No orphan tasks without a spec origin |
| Every task has acceptance criteria coverage | Tasks that implement ACs must cite which AC they cover |
| Traceability matrix is complete | Matrix covers all spec requirements with ≥1 task each |

### 6. Check Ambiguity Resolution
| Check | Rule |
|-------|------|
| No `[NEEDS CLARIFICATION]` markers remain | All markers must be resolved before implementation |
| File paths in tasks exist or are planned | No references to non-existent directories |
| Dependency chains are acyclic | No circular dependencies in task ordering |

### 7. Check Out-of-Scope Discipline
| Check | Rule |
|-------|------|
| Spec out-of-scope is present | Section 5 is not empty |
| Plan out-of-scope is reaffirmed | Section 7 matches spec Section 5 |
| No tasks implement out-of-scope items | Flag any task that appears to implement excluded features |

### 8. Emit Consistency Report

```yaml
cross_artifact_consistency:
  task_ref: <task contract reference>
  verdict: <PASS|GAPS_FOUND|CRITICAL_GAPS>
  
  checks:
    spec_to_plan:
      stories_covered: <count>/<total>
      nfrs_covered: <count>/<total>
      status: <pass|fail>
    
    plan_to_tasks:
      phases_covered: <count>/<total>
      files_covered: <count>/<total>
      status: <pass|fail>
    
    tasks_to_spec:
      orphan_tasks: <count>
      ac_coverage: <count>/<total>
      status: <pass|fail>
    
    ambiguity:
      unresolved_clarifications: <count>
      invalid_references: <count>
      status: <pass|fail>
    
    out_of_scope:
      spec_section_present: <true|false>
      plan_reaffirmed: <true|false>
      tasks_leak_more_than_spec: <true|false>
      status: <pass|fail>
  
  gaps:
    - description: <what is missing>
      severity: <critical|major|minor>
      affected_artifacts: <list>
      remediation: <what to add/fix>
  
  overall_status: <pass|fail>
  next_action: <proceed_to_implementation|fix_gaps_and_rerun>
```

## Transition Rules
- **PASS**: All checks pass → proceed to Implementation (Phase 7)
- **GAPS_FOUND**: Minor gaps (e.g., one AC not covered) → fix and re-run
- **CRITICAL_GAPS**: Major gaps (e.g., entire story uncovered, out-of-scope violation) → escalate to PM, re-open Scope Lock if needed

## Exit Criteria
- Zero critical gaps
- Every spec requirement has ≥1 task
- Every task traces to a spec requirement
- Out-of-scope declarations are consistent across all artifacts
- Record: `codex_knowledge_handoff_checkpoint(name=sol:<task_id>:consistency)`

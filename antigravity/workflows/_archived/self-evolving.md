---
name: self-evolving
summary: Propose and apply harness improvements from validated lessons and traces.
---

# Self Evolving

## Purpose
Improve the development harness (skills, prompts, guardrails, workflows) based on validated lessons and traces.

## Prerequisites
- Lessons must be validated (post-Oracle review)
- Traces must be recorded (via `codex_knowledge_handoff_checkpoint`)
- No unapproved changes to core workflows

## Steps

### 1. Gather Validated Lessons and Traces
- Use `codex_knowledge_memory_query` to review recent traces
- Use `codex_knowledge_memory_query` to retrieve lessons
- Use `codex_knowledge_graph_query` to identify repeated failure patterns
- Use `codex_knowledge_orchestration_lesson` to consolidate patterns
- Check whether the relevant skill already has a `skillbank/optimized/<skill-id>/best_skill.md` target and the current validation baseline.

### 2. Write Proposal Manifest
- Use `codex_knowledge_knowledge_capture` to draft a proposal:
  ```yaml
  evolution_proposal:
    trigger: <what triggered this proposal>
    evidence: <list of traces, lessons, patterns>
    desired_change: <what should change>
    constraints: <what must not change>
  ```
- Add a paired `skillopt_epoch` manifest when the proposal changes a skill document:
  ```yaml
  skillopt_epoch:
    skill_id: <skill-id>
    baseline_version: <version-or-hash>
    candidate_version: <version-or-hash>
    baseline_score: <number>
    candidate_score: <number>
    edit_budget:
      max_operations: 3
      max_changed_lines_ratio: 0.2
  ```

### 3. Gate with Oracle and Human Approval
- Submit proposal to Oracle for review
- Oracle checks:
  - Does the change improve the stated metric?
  - Does it introduce new risks?
  - Is it minimal and reversible?
- Reject equal-score skill edits; only strict held-out improvement may promote a new best skill.
- If Oracle approves, submit for human approval
- Use `human_approval_interrupt` workflow for critical changes

### 4. Apply Approved Changes
- Apply only the approved harness change
- Record the change in `codex_knowledge_knowledge_capture`
- Update the relevant skill, guardrail, or workflow file
- Write promoted skill text to `skillbank/optimized/<skill-id>/best_skill.md` and store rejected edit fingerprints in memory or graph.
- Use `codex_knowledge_orchestration_lesson` to record the outcome

### 5. Monitor Results
- Track KPIs after the change:
  - `kpi:hallucination_rate:<date>`
  - `kpi:scope_drift_rate:<date>`
  - `kpi:minimalism_score:<date>`
  - `kpi:token_efficiency:<date>`
  - `kpi:harness_activation_rate:<date>`
  - `kpi:harness_adherence_score:<date>`
  - `kpi:graph_first_rate:<date>`
  - `kpi:grep_fallback_rate:<date>`
- If metrics worsen, revert the change and record the regression

### 6. Distill SkillBank Entries
- Convert validated successes into `skillbank/general` or `skillbank/task-specific` entries.
- Convert validated failures into `skillbank/failure-lessons` entries.
- Promote trainable skills into `skillbank/optimized` only after validation and Oracle review.
- Require SkillOpt and Oracle review before a SkillBank entry becomes active.
- Store evidence links in `codex_knowledge` memory or graph.

## Guardrails
- Never edit runtime files directly without an approved task contract
- Never propose more than 2 changes per evolution cycle
- Always include rollback criteria
- Require human approval for procedure changes
- Never add active SkillBank entries from unreviewed traces

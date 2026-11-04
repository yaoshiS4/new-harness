---
name: dreaming-consolidation
summary: Offline memory folding, skill distillation, and knowledge compression at session end or token budget threshold.
---

# Dreaming / Sleep Consolidation Workflow

## Overview
Dreaming is a recurrent offline consolidation pass that folds session traces into durable memory, distills failure lessons into SkillBank, and compresses knowledge for future retrieval.

## Trigger Conditions
- End of session (explicit user command or session timeout).
- Token budget > 90% (automatic trigger via context budget guardrail).
- Explicit user command: `dream`, `consolidate`, `sleep`.

## Consolidation Steps

### Step 1: Collect Traces
- Gather all traces from current session:
  - Task contracts, exploration reports, harness activations.
  - Implementation deviations, test results, Oracle verdicts.
  - Break/Resume events, scope changes.
- Record via `call_mcp_tool` on `codex_knowledge` (`ToolName: "knowledge_capture"`) with `key: session_traces_<session_id>`.

### Step 2: Fold Knowledge Graph
- Fold events -> concepts -> intents via `call_mcp_tool` on `codex_knowledge` (`ToolName: "graph_upsert"`).
- Input:
  - Subject/Predicate/Object relationships representing architectural decisions and outcomes.
- Output: Knowledge graph updated with verified entities and relations.

### Step 3: Distill Failure Lessons
- Identify failure patterns from traces:
  - Hallucination findings (from `hallucination-auditor`).
  - Scope drift events (from scope guardrail).
  - Test failures with root cause.
  - Context rot loops: Repetitive tool patterns or 3-strike file read lockouts.
- For each pattern:
  - Distill into `codex_knowledge` (`ToolName: "orchestration_lesson"`) with category `failure_lesson`.

### Step 4: Record Retrospective
- Compile session retrospective:
  - Record via `codex_knowledge` (`ToolName: "orchestration_lesson"`) or update local task documentation.

### Step 5: Persist Session KPIs (optional)
- Compile session KPIs and record to knowledge store:
  ```yaml
  session_kpis:
    hallucination_rate: <percentage>
    scope_drift_rate: <percentage>
    skill_activation_rate: <percentage>
    token_efficiency: <float>
    cache_hit_rate: <percentage>
    graph_first_rate: <percentage>
    loop_iterations: <count>
    context_rot_score: <score_0_to_100>
    file_reread_violations: <count>
    isolation_trigger_count: <count>
  ```
- Record via `codex_knowledge` (`ToolName: "orchestration_lesson"`) with `category: kpi`.

### Step 6: Autonomous Level-3 Harness & Codebase Self-Healing (`auto-harness-healer.py --auto`)
- **Severity Burn-Rate Sentinel Drainage**:
  - Drains `/tmp/.antigravity_failures_pending.jsonl` into the persistent `harness_failures` ledger in `registry.sqlite`.
  - Analyzes accumulated failure events categorized by the 4 SRE $\times$ Agent RSI severity weights ($S_0=1.00, S_1=0.25, S_2=0.05, S_3=0.01$).
  - Evaluates Burn-Rate threshold breaches ($\sum w \ge 1.0$ or $BR(W_{\text{short}}) \ge 3.0$) and pending review escalations in `settings_reviews`.
- **5-Vertex Symbolic Failure Gradients ($\nabla_{v_i} \mathcal{L}_{\text{sym}}$)**:
  - Clusters failure signatures across the 5 symbolic vertices: `hook`, `skill`, `tool_guidance`, `routing`, and `codebase`.
- **External Literature & GitHub Scouting (`external-research-scout.py`)**:
  - Integrates PaperQA2 and OpenScholar evidence grounding across arXiv, Semantic Scholar, and top open-source agent repositories with local 7-day caching.
- **Offline Counterfactual Trajectory Replay (`dream-replay-simulator.py`)**:
  - Replays high-severity historical failure trajectories offline against candidate rules and tool guardrails before promotion.
- **Harmony Harness Architecture (`arXiv:2610.15150`) & Darwin Gödel Machine 3-Gate Sandbox Verification**:
  - **CP-1 Factorized Evolution ($\mathcal{H}_{\text{gen}} \oplus \mathcal{H}_{\text{env}}$)**: Decouples prompt/skill guidance mutations ($\mathcal{H}_{\text{gen}}$) from mechanical hook/environment mutations ($\mathcal{H}_{\text{env}}$).
  - **CP-2 3-Axis Pareto Non-Dominated Gate**: Evaluates candidate mutations across `func_score`, `sec_score` (must equal `1.0`), and `token_score`, verifying against:
    1. Gate 1: `validate-harness-tree.py`
    2. Gate 2: `reflect-experience.py --self-test`
    3. Gate 3: `recursive-ppc-engine.py --self-test`
  - **CP-3 SQLite Pareto Archive**: Persists non-dominated frontier candidates in `registry.sqlite` (`pareto_archive`) for Turn-1 dynamic composition.
  - Reverts immediately to baseline (`KEEP_BASE`) if any verification gate fails or Pareto dominance is violated, recording an oscillation backoff signature in `~/.gemini/last_harness_evolution_backoff.json`.
- **Ledger Resolution & Turn-1 Notice**:
  - Stamps `resolved_at = CURRENT_TIMESTAMP` on processed rows in `harness_failures` and `settings_reviews`.
  - Emits a Turn-1 notice flag at `~/.gemini/last_harness_evolution_alert.flag` consumed on the next session invocation.

## Output Contracts

### Dreaming Report
```yaml
dreaming_report:
  session_id: <id>
  trigger: session_end | token_budget | explicit
  traces_collected: <count>
  cognifold_updates:
    events_folded: <count>
    concepts_folded: <count>
    intents_folded: <count>
    edges_updated: <count>
  failure_lessons_distilled: <count>
  retrospective_recorded: true | false
  kpi_persisted: true | false
  next_actions:
    - <action>
```

## Safety Rules
1. **No mutation during active task**: Dreaming only runs when no task is in progress.
2. **No unvalidated learning**: Only validated traces (Oracle-approved or test-verified) are folded.
3. **No unrecorded changes**: All Cognifold updates are recorded in memory store.
4. **Reversible**: Cognifold edge weights can be reset if consolidation causes retrieval degradation.

## Settings & Review Queue Gate
- Inspect pending review items via `call_mcp_tool` on `codex_knowledge` (`ToolName: "settings_review_queue"`).
- Verify each candidate against live evidence (files, git log, validator output) before promoting to durable memory or skill documents.

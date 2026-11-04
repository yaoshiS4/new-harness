---
description: Dreaming consolidation (sleep-time learning) - fold session traces into the knowledge graph, distil failure lessons, record KPIs, and run the auto-harness-healer closed loop (Harvest -> Cluster -> Scout -> Patch -> Verify) with Harmony CP-1/CP-2/CP-3 gates. Run at session end or when the user says dream / consolidate / sleep.
---

# /dreaming — consolidation

Never run during an active task; learn only from validated traces; every change reversible.

1. Collect traces: `mcp__codex_knowledge__knowledge_capture(slug, "session_traces_${CLAUDE_SESSION_ID}", <summary of mutations / verifications / decisions>)`. Source: `~/.cache/claude_harness/session_states/<session>.md` and `~/.cache/antigravity_observations/<session>.md`.
2. Fold the graph: `mcp__codex_knowledge__graph_upsert(slug, src, rel, dst)` for decisions (DECIDED_BY), dependencies (DEPENDS_ON), and session->file lineage.
3. Distil failure lessons (hallucination findings, scope drift, test root causes, loop breakers, 3-strike lockouts): `mcp__codex_knowledge__orchestration_lesson(slug, "failure_lesson", summary, severity)`.
4. Retrospective + KPIs (category `kpi`): hallucination_rate, scope_drift_rate, skill_activation_rate, token_efficiency, loop_iterations, context_rot_score, file_reread_violations.
5. Self-heal loop (ask the user first; it edits harness guidance files): `python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/auto-harness-healer.py --auto --dry-run`, review the proposed repairs, then run without `--dry-run`. Gates: `python3 scripts/validate-claude-tree.py`, `reflect-experience.py --self-test`, `recursive-ppc-engine.py --self-test`; any regression -> KEEP_BASE.
6. Check `mcp__codex_knowledge__settings_review_queue(slug)` before promoting anything; report `dreaming_report{traces_collected, graph_updates, failure_lessons_distilled, kpi_persisted, next_actions}`.

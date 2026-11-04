<!-- BEGIN CLAUDE_HARNESS_MANAGED -->

# Claude Code Global Runtime Rule (SOTA Harness)

- **Default Output Mode: ADHD Mode (Action-First)**: Active on user turns unless asked for "normal mode" (subagents exempt from Rules 3, 5, 6). Follow the `adhd-mode` skill:
  1. **Lead with Next Action / BLUF**: First line executable (action/command/path on coding; BLUF on Q&A).
  2. **Number Multi-Step Work**: Bounded numbered steps, 1 action/step.
  3. **End with ONE Concrete Action (<2 min)**: 1 micro-action on coding or 1 decision prompt on advisory (omit on "answer only"). Zero filler.
  4. **Suppress Tangents**: Primary task first; separate follow-ups.
  5. **State Anchoring**: Open with `[Step X of Y Done: <milestone>] -> Next: <immediate action>`.
  6. **Concrete Time Estimates**: Exact units (e.g., ~5 min), never vague.
  7. **Visible Wins**: Functional status + verification command.
  8. **Error Framing**: `Fail: <path:line> | Expected: <A> | Got: <B> | Cause: <C> | Fix: <D>`.
  9. **Uncapped Lists**: Full list inline `<= 30` items (never truncate); `> 30` -> file/artifact + link.
  10. **Zero Fluff**: No pleasantries, openers, recaps, or sign-offs.
- Prefer Turn-1 `[Active Knowledge Grounding]` SOT docs (`docs/STATUS.md`, `docs/README.md`, `CLAUDE.md`, `AGENTS.md`, `README.md`; verify existence first) before broad scanning.
- Tool preference: native **Grep / Glob / Read** over shell search; in Bash prefer `rg -m 50` (no `grep` when `rg` exists), `fd --max-results 50` (no `find` when `fd` exists), `jq`, `yq`, `ast-grep`. MCP servers in `.mcp.json` (`codegraph`, `codex_knowledge`, `context_health`, `context7`) take priority for symbol lookup, memory, and docs.
- Confirm before destructive commands (`rm -rf`, `git reset --hard`, `git push`), migrations, new dependencies. The PreToolUse hook converts these to permission prompts.
- Surgical, minimal, reversible diffs. Never weaken/fake assertions (`Fix-The-Code-Not-The-Test`). Require fresh execution output before claiming passes (Stop hook enforces the Causal-Past LTL verification gate).
- UI/UX: Follow `ui-apex-invariants.md` and `anti-slop-taxonomy.md` (harness `guidelines/`). Eliminate nested cards (L-01), card soup (L-13), icon fatigue (T-12), badge proliferation (D-09), ellipsis clipping (L-16), category over-expressing (W-07).
- **Terminal Diagram & Table Symmetry**: In the CLI, never emit raw ```` ```mermaid ```` — render Unicode box-drawing (`╭─╮ │ ╰─╯ ──▶`) or `mermaid-ascii`; keep pipe-table cells single-line (`<= 40 chars/cell`, no `file://` URLs; links below).

## 3-Tier Adaptive Routing & Strict Role Isolation

### Hard Role Invariant (Zero Toe-Stepping)

- **Root thread = `pm`**: Intake, SOT grounding, AskUserQuestion, `routing-thresholds`, Story Shards (`implementation_plan.md`, `task.md`), orchestration via the **Agent tool**. **NEVER** mutates application source (`apps/**`, `packages/**`, `src/**`, `*.ts`, `*.tsx`, `*.py`, `*.kt`, ...); docs, plans, configs, and `.claude/` are allowed. (Override only via `root_may_edit_code` in `.claude/harness/guardrails.json`.)
- **Explorers (`frontend-explorer`, `backend-explorer`, `research-explorer`, `Explore`)**: Read-only (`model: sonnet`); return coordinates/telemetry, never code or plans.
- **Architects (`sa`/`senior-architect`, `critical-planner`)**: Design, ADRs, adversarial plan review (`model: inherit`). Never write feature code.
- **Builders (`dev-fe`, `dev-be`, `debugger`, `designer`, `meta-evolution`)**: Edits (`model: inherit`) strictly within leased Story Shards — every builder prompt MUST contain an `allowed_files:` block (paths, globs, or `[]`). The hooks enforce the lease.
- **QC & Auditors (`frontend-qc`, `test-runner`, `oracle-review`, `hallucination-auditor`, `implementation-review`, `security-audit`)**: Read-only (**Generator-Evaluator Separation**: builders never self-certify); route `Fail: <path:line>` back to a builder.

### 3-Tier Execution Paths

- **Path 1 — Quick (`<= 3` files, 1 domain, zero schema/auth/migration risk, clear intent)**: 1) Inline Story Shard in chat (files + criteria + test; no `implementation_plan.md`). 2) 1 Builder (`Agent(subagent_type="dev-fe"|"dev-be"|"debugger")` with `allowed_files:`). 3) Fast Gate (targeted unit test + typecheck + UI anti-slop). Slash: `/fast-track`.
- **Path 2 — Normal (`4–10` files or 2 domains)**: `1. Intake → 2. Enrichment (explorers) → 3. Clarification (AskUserQuestion) → 4. PM Contract & Story Shards (implementation_plan.md + task.md) → 5. Disjoint Builders → 6. Surgical Implementation → 7. Two-Stage QC (7a frontend-qc + 7b test-runner) → 8. Independent Oracle Audit (oracle-review + hallucination-auditor)`. Slash: `/standard-dev`.
- **Path 3 — Long-Horizon (`> 10` files, `>= 3` domains, migrations, or `/goal`)**: `1. Parallel 3-Explore → 2. Architect Spec & ADR (sa) → 3. PM Depth-Tree (PLAN.md + GATES.md via unlazy) → 4. Adversarial Plan Gate (critical-planner) → 5. Wave-Isolated Builders (worktree-isolation, <= 2 concurrent) → 6. Context Checkpointing (codex_knowledge:handoff_checkpoint at 60% budget) → 7. 3-Round Zero-Bug Loop (oracle-review) → 8. Doc Sync (doc-sync-worker)`. Slash: `/goal`.

## Claude Model Routing Matrix

Subagents declare their tier in `.claude/agents/*.md`; the PreToolUse hook asks for confirmation before escalating a role above its baseline:
1. **Tier A (`model: inherit`)**: `pm`, `sa`, `senior-architect`, `critical-planner`, `security-audit`, `debugger`, `dev-fe`, `dev-be`, `designer`, `visual-engineer`, `simplifier-reviewer`, `meta-evolution`, `frontend-qc`, `oracle-review`, `hallucination-auditor`, `implementation-review`.
2. **Tier B (`model: sonnet`)**: `backend-explorer`, `frontend-explorer`, `research-explorer`, `user-tester`, `devops`, `skillopt-optimizer`, `test-runner`, `doc-sync-worker`, `librarian`.
3. **Tier C (`model: haiku`)**: `diff-helper` (telemetry).
4. **Escalation (`opus`/`fable` for a Tier B/C role)**: requires explicit user confirmation (hook emits `ask`).

## Reactive Runtime & Token Invariants

- **No Polling**: never run `sleep`/status loops; use `run_in_background` and yield for the completion notification.
- **Mechanical Read & Search Bounds (PreToolUse)**: Read `<= 200` lines whole first; for `> 400` lines run the symbol outline first (the hook returns an AST skeleton) and read slices `<= 250` lines (max 6 slices/file; `251–260` auto-clamped). Bound searches: Grep `head_limit` (auto-set to 50 in content mode), `rg -m 50`, `fd --max-results 50`.
- **External Docs (`context7`)**: `resolve-library-id` -> `query-docs` before WebSearch.
- **Zero-Tax MCP Quick-Call Signatures** — `codegraph`: `symbol_lookup(root, query, limit=20)`, `extract_symbols(root, path, symbols)`, `batch_query(root, steps)`, `summarize_path(path, limit=50)`, `callers_callees(root, symbol)`, `impact_analysis(root, changed_paths, symbols)`, `repo_map(root, max_tokens=1500)`; `codex_knowledge`: `project_context(slug, query)`, `memory_query(slug, query)`, `graph_query(slug, term)`, `memory_store(slug, key, value)`, `handoff_checkpoint(slug, name, payload)`, `batch_knowledge_query(slug, steps)`; `context_health`: `get_session_health(conversation_id)`, `check_read_budget(file_path, conversation_id)`, `compact_observations(conversation_id)`, `commit_context_ledger(milestone, goals_completed, files_modified, active_constraints, project_dir)`, `project_trajectory_toon(conversation_id, max_tokens=1200)`.
- **Zero Multimodal Poisoning**: never Read images automatically; save to artifacts.
- **Sticky Verified Decisions**: `path:line`-evidenced decisions cannot be reversed by speculative critiques without new counter-evidence (`context_health:commit_context_ledger`).
- **Zero Plan/Audit Tags in Code**: never write phase numbers, task IDs, or finding tags (`Wave 2`, `UG-01`, `F13`) in application code comments (PostToolUse warns).
- **Context Health**: at 55% (DEGRADED) compact observations + commit ledger; at 65% recommend `/compact` (PreCompact/SessionStart hooks save and restore the session snapshot); at 75% (CRITICAL) checkpoint via `handoff_checkpoint` and delegate.
- **Subagent contract**: prompts `<= 6,000` chars (write large context to a scratch file and pass the path); no nested Agent spawning (depth 1); return a summary only: changed files, evidence, risks, next action.
- **Harness surface**: hooks in `.claude/hooks/`, agents in `.claude/agents/`, skills in `.claude/skills/`, workflows as slash commands in `.claude/commands/`, policy in `.claude/harness/guardrails.json`, runtime state in `~/.cache/claude_harness/`. New project: `/harness-init` once, then `/fast-track`, `/standard-dev`, or `/goal`; `/harness-status` shows live gates; verify the harness itself with `bash scripts/verify-claude-harness.sh`.
- **Spawn governance (every Agent call)**: prompt starts with `Role: <subagent_type>` + the Story Shard (`allowed_files`, `verification_cmd`, custody lease); <= 2 concurrent builders in separate worktrees (`isolation: "worktree"`), <= 4 agents per wave; two-stage review of every return (Stage A lease/spec compliance with fresh `exit_code: 0`, then Stage B quality via `test-runner` / `frontend-qc` / `oracle-review`); returns end with a `### Telemetry Receipt`.
<!-- END CLAUDE_HARNESS_MANAGED -->

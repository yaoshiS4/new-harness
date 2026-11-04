---
name: project-documentation
description: Convert PRDs into traceable delivery documents, architecture notes, epic specifications, and task lists.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# Project Documentation & Story Shard Decomposition

## Purpose
Convert PRDs, architecture specs, and user requests into a traceable delivery document chain (`implementation_plan.md`, `task.md`, `PLAN.md`, `GATES.md`) and bite-sized, mechanically verifiable BMAD Story Shards (`allowed_files`, `verification_cmd`, `Oracle-Custody-Lease`).

---

## Workflow

### 1. Ground in Curated SOT First (`codex_knowledge:batch_knowledge_query`)
Before drafting plans or task lists, load existing requirements, architecture decisions, and story indexes in a single turn:
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "batch_knowledge_query",
  "Arguments": {
    "slug": "<project_slug>",
    "steps": [
      {"op": "project_context", "query": "<feature_or_epic>", "limit": 3},
      {"op": "memory_query", "query": "<feature_or_epic>", "limit": 10},
      {"op": "graph_query", "query": "<feature_or_epic>", "limit": 15}
    ],
    "output_format": "toon"
  }
}
```
- Anchor strictly on approved source docs: PRD, SRS, ADRs, `docs/STATUS.md`, and `AGENTS.md`.
- If the source set has unresolved ambiguities that cannot be answered by `codegraph` or SOT docs, stop and invoke `requirement-interviewer` (`AskUserQuestion` with `(Recommended)` first) before inventing scope.

### 2. Route Artifact Ceremony by Task Complexity (`routing-thresholds`)
- **Path 1 (Quick Route — `<= 3` files, 1 domain)**: Emit an **Inline Story Shard** directly in chat (target files + acceptance criteria + exact test command; zero `implementation_plan.md` file overhead).
- **Path 2 (Normal Route — `4–10` files or 2 domains)**: Produce `implementation_plan.md` and `task.md` in the session artifact directory (`<workspace>/.claude/harness/`).
- **Path 3 (Long-Horizon Route — `> 10` files, `>= 3` domains, or `/goal`)**: Produce `PLAN.md` + `GATES.md` (via `unlazy` Depth-Tree decomposition) + disjoint Wave Story Shards.

### 3. Bite-Sized Task Decomposition (`obra/superpowers` — `writing-plans`)
Write every implementation task assuming the executing Builder subagent has **zero prior conversation context** and needs exact coordinates:
1. **Atomic Granularity (2–5 Minutes per Step)**: Break work into single-action steps (*Step 1: Write failing test $\rightarrow$ Step 2: Run test to verify failure $\rightarrow$ Step 3: Implement minimal code $\rightarrow$ Step 4: Run test to verify pass*).
2. **Exact File Coordinates**: Specify exact file paths and target symbol/line ranges (`src/auth/token.py#L42-L78`), never vague module names.
3. **Deterministic Verification Command**: Every task must include the exact CLI command to run (`pytest tests/test_token.py -k test_expiry -v`) and the expected pass output.
4. **Zero Speculative Scope**: Do not add bonus endpoints, extra config flags, or unrequested abstractions.

### 4. BMAD Story Shard Contract Schema
Every delegated Builder task (`subagent_type: "dev-fe" | "dev-be" | "debugger"`) must be packaged as an explicit Story Shard lease:
```yaml
story_shard:
  shard_id: "SHARD-01"
  role: "dev-be"
  model: "inherit"
  cp1_lease_partition: "H_gen"
  oracle_custody_lease: "OCL-<wave>-<shard>"
  allowed_files:
    - "src/services/payment.py"
    - "tests/test_payment.py"
  forbidden_files:
    - "config/hooks/**"
    - "scripts/verify-claude-harness.sh"
  steps:
    - step: 1
      action: "Add failing unit test for idempotent retry token"
      verification_cmd: "pytest tests/test_payment.py -k test_idempotent_retry"
      expected_result: "FAIL (NotImplementedError)"
    - step: 2
      action: "Implement idempotent retry check in process_charge()"
      verification_cmd: "pytest tests/test_payment.py -k test_idempotent_retry"
      expected_result: "PASS (1 passed)"
  verification_cmd: "pytest tests/test_payment.py && mypy src/services/payment.py"
  scope_drift_budget: "0 out-of-lease files"
```

### 5. Traceability & Post-Approval Sync
- Keep every downstream artifact traceable back to its upstream requirement ID and forward to its verification gate in `GATES.md` or `task.md`.
- Prefer surgical delta updates over full-file rewrites.
- After `oracle-review` approval, run `document-sync` and `sot-context` to update indexes and vault summaries.

---

## Guardrails
- Do not invent epics, stories, tasks, or acceptance criteria that are not grounded in approved source docs.
- Never issue a Builder task without an explicit `allowed_files` list, `verification_cmd`, and `Oracle-Custody-Lease`.
- Never allow Builders (`H_gen`) to modify verification scripts or weaken test assertions (`Fix-The-Code-Not-The-Test`).

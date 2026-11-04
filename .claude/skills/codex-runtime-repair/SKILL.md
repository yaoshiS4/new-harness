---
name: codex-runtime-repair
description: Repair the Codex runtime or its launcher surface with minimal changes and clear evidence.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# Codex & Antigravity Runtime Repair

## Purpose
Repair the Antigravity or Codex runtime, MCP servers, lifecycle hooks, or launcher surface with minimal changes, deterministic verification, and clear evidence.

> [!IMPORTANT]
> **The Iron Law (`obra/superpowers` — `systematic-debugging`)**:
> **`NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.`**
> Never apply speculative patches, blind retries, or multi-variable edits before completing Phase 1–3 of the Root-Cause Protocol. If **3 consecutive fix attempts fail**, **STOP immediately** — do not attempt a 4th fix. Restore the shadow checkpoint (`restore-shadow-checkpoint.py --restore`) and escalate to architectural review (`subagent_type: "sa" | "debugger"`).

---

## 4-Phase Root-Cause Protocol (`obra/superpowers`)

### Phase 1: Root Cause Investigation (Observe Before Touching)
1. **Capture Exact Telemetry**: Run the failing command or hook and capture the verbatim traceback, exit code, and stderr.
2. **Verify Reproducibility**: Execute the failure trigger deterministically (at least twice if non-deterministic) and check environment invariants (`uv`, Python venv, environment variables, socket/port conflicts).
3. **Inspect Recent Changes & AST Context**:
   - Check recent mutations via `git status --short` and `git diff`.
   - Use `mcp__codegraph__summarize_path(, Arguments={"path": "<affected_file>"})` to inspect structure without blowing read budgets.
   - Query historical runtime fixes via 1-shot `mcp__codex_knowledge__memory_query(, Arguments={"slug": "<project_slug>", "query": "<error_signature>", "limit": 10})`.

### Phase 2: Pattern Analysis (Compare Against Working Baselines)
1. **Locate Working Reference**: Compare the broken hook, MCP server, or launcher configuration against working equivalents in `config/hooks/`, `config/mcp_config.json`, or `antigravity/scripts/`.
2. **Trace Data & Boundary Flow**: For multi-component failures (CLI $\rightarrow$ Hook $\rightarrow$ MCP Server $\rightarrow$ SQLite), trace the exact boundary where input payload or state diverges from expected schema.
3. **Run Mechanical Tree & Self-Healing Diagnostics**:
   ```bash
   python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/validate-claude-tree.py
   python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/auto-harness-healer.py --diagnose
   ```

### Phase 3: Hypothesis & Single-Variable Testing
1. **State Explicit Hypothesis**: Formulate a falsifiable statement: *"Failure at `<path:line>` is caused by `<root_cause>` because `<evidence>`."*
2. **Single-Variable Probe**: Test one variable at a time. Never bundle formatting changes, unrelated refactors, or multiple speculative fixes together.
3. **3-Strike Escalation Circuit Breaker**:
   - Track fix attempts (`attempt 1/3`, `attempt 2/3`, `attempt 3/3`).
   - If attempt 3 fails verification, **STOP**, roll back via `python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/restore-shadow-checkpoint.py --restore`, and report an architectural blocker.

### Phase 4: Minimal Repair & Harmony CP-2 Pareto Verification
1. **Apply Surgical Fix**: Mutate only the minimal lines required to resolve the root cause while preserving all security guardrails (`Fix-The-Code-Not-The-Test`).
2. **Run Full Verification Gate**:
   ```bash
   bash scripts/verify-claude-harness.sh
   python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/validate-claude-tree.py
   ```
3. **Verify Harmony Harness CP-2 3-Axis Pareto Non-Dominated Gate**:
   - `func_score`: 100% of targeted unit tests and harness verification checks pass.
   - `sec_score`: Zero regression in `check_security_guardrail_integrity()` (`pre_tool_use.py` & `stop.py` invariants intact).
   - `token_score`: Always-on `CLAUDE.md` byte budget (`<= 12,000` chars) and diff minimalism (`${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/clean-diff.sh`) preserved.
4. **Capture Durable Lesson**:
   Record the root cause and fix via `mcp__codex_knowledge__knowledge_capture(, Arguments={"slug": "<project_slug>", "title": "<issue>", "content": "<root_cause_and_fix>"})`.

---

## Common Antigravity & Codex Runtime Failure Modes
- **MCP Server Won't Start**: Check `config/mcp_config.json` command path, `uv run` environment, Python syntax (`py_compile`), and stdio framing.
- **Lifecycle Hook Denial / Crash**: Inspect `~/.claude/hooks/pre_tool_use.py` or `stop.py`, run `pytest tests/test_global_hooks.py`, or run `python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/auto-harness-healer.py`.
- **Corrupted Wave / Unintended Mutation**: Restore pre-wave state immediately with `python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/restore-shadow-checkpoint.py --restore`.
- **Permission or Sandbox Boundary**: Check file permissions, worktree leases, and the harness hook policies (`.claude/hooks/`, `guardrails.json`) (never bypass security checks).

---

## Output Format
```yaml
runtime_repair:
  issue: <concise failure signature>
  reproduction: <exact command>
  phase_1_evidence: <traceback and boundary where state diverged>
  root_cause_hypothesis: <falsifiable diagnosis>
  attempt_count: <1..3>
  fix: <minimal surgical change applied>
  files_changed:
    - <path>
  cp2_pareto_gate:
    func_score: pass
    sec_score: pass
    token_score: pass
  validation: <verify-harness.sh and validate-claude-tree.py output>
```

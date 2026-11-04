# Antigravity Tool Quirks & Runtime Invariants (`tool-quirks.md`)

> [!IMPORTANT]
> This document acts as the dynamic tool-quirk registry ($c^4$) and execution invariant reference for the Antigravity runtime, MCP servers, and subagent orchestration. It is strictly leased to the `INV` proposer (`meta-invariant-editor`).

---

## 1. Tool Call Slice & Flood Guards

### 1.1 `read_file` / `view_file` 250-Line Slice Cap, Fencepost `overwrite` Clamp & SOT Exemptions
- **Constraint**: `read_file` (CLI) / `view_file` (IDE) `StartLine` and `EndLine` must span **$\le 250$ lines** per invocation.
- **Enforcement & Grace-Window Auto-Clamp**: Mechanically enforced by `pre_tool_use_hook.py`. Inclusive fencepost and EOF tail slices spanning **$251\text{–}260$ lines** (`slice_cap < span <= slice_cap + 10`) are automatically clamped in-flight via native `PreToolUse` `overwrite` (`{"decision": "allow", "overwrite": {"StartLine": start_l, "EndLine": min(line_cnt, start_l + slice_cap - 1)}}`), whereas slices exceeding `slice_cap + 10` (`> 260` lines) return `{"decision": "deny"}`.
- **SOT Markdown Exemptions**: Canonical Source-of-Truth markdown basenames (`INDEX.md`, `AGENTS.md`, `GEMINI.md`, `README.md`) are exempt from false-positive duplicate-slice circuit-breaker locks, and missing optional SOT probes (`status.md`, `readme.md`, `agents.md`, `context_ledger.md`) are excluded from `burn-rate-sentinel` failure recording.
- **Resolution**: Always supply explicit slicing arguments (`StartLine: 1, EndLine: 200`). Never attempt to read whole files $> 250$ lines in a single call. Use AST symbol lookups (`codegraph:symbol_lookup`, `codegraph:summarize_path`) before detailed reads.

### 1.2 `rg -m 50` & `fd --max-results 50` Search Flood Guards
- **Constraint**: Search tools must bound stdout output to avoid massive context dumps.
- **Enforcement**: Pass `-m 50` (or `--max-count 50`) to `rg` and `--max-results 50` to `fd`.
- **Modern CLI Enforcement**: Legacy search commands (`grep`, `egrep`, `fgrep`, `rgrep`, `find`) are mechanically blocked by `pre_tool_use_hook.py`. Use modern tooling exclusively:
  - `rg` (ripgrep)
  - `fd` (fd-find)
  - `eza` (listings)
  - `bat --paging=never` (or `read_file` / `view_file`)
  - `sd` (in place of sed)
  - `sg` (`ast-grep`)
  - `jq`, `yq`

### 1.3 SWE-agent ACI Silent-Success Invariant
- **Constraint**: When standard UNIX file operations (`cp`, `mv`, `mkdir`, `chmod`, `ln`, `py_compile`) return `Exit code: 0` with empty stdout, this represents verified, authoritative completion.
- **Prohibition**: NEVER waste turns executing redundant `ls`, `stat`, or `test -f` checks solely to re-confirm that an exit-0 silent command took effect. Treat silent exit code 0 as verified success.

### 1.4 Code-Mode MCP Batching & Multi-Symbol AST Extraction (`arXiv:2402.01030`, `arXiv:2211.10435`)
- **Circuit Breaker Avoidance**: When inspecting monolithic files (> 400 lines), never attempt sequential small slices (which triggers the 6-slice loop breaker). Use `codegraph:extract_symbols(root, path, symbols, max_total_lines=250)` to retrieve 2–5 function definitions in a single call.
- **Batch Pipelining**: Use `codegraph:batch_query(root, steps)` with `"from_prev": true` or `codex_knowledge:batch_knowledge_query(slug, steps)` to execute lookup -> callers -> impact analysis in a single in-memory turn, eliminating 3-turn conversational ping-pong and token bloat.
- **Payload Spillover**: Payloads $> 6,000$ characters are automatically offloaded to `/tmp/ag_mcp_spillover_*.json` with compact TOON pointers to protect context budgets.

### 1.5 PTY Progress-Bar Suppression & Pub/Sub Sparsification
- **PTY Progress-Bar Flood Guard**: Unbounded terminal updates (`\r` carriage return redraws) saturate context windows. Always pass quiet / non-interactive flags:
  - Gradle builds: Pass `--console=plain -q` (e.g. `./gradlew assembleRelease --console=plain -q`) or `--quiet`.
  - Git push operations: Pass `-q` (`git push -q`) to suppress remote object counters.
- **Pub/Sub Sparsification Ceiling**: `send_message` content and `invoke_subagent` `Prompt` strings are capped at **6,000 characters**. For large traces, tabular dumps, or reports, write to an artifact or scratch file (`<artifactDir>/...`) and pass the concise summary (< 6,000 chars) with a file pointer.

### 1.6 Wire-Boundary `PostToolUse` `overwriteResult` & Shallow `PreToolUse` `overwrite` Invariants
- **`PostToolUse` `overwriteResult` Engine**: Antigravity's server-side hook runner (`marshalHookArgs` with `EmitUnpopulated: true`) swallows `PostToolUse` `stderr` unless the hook exits non-zero or returns `{"overwriteResult": "<string>"}`. `post_tool_use_hook.py` uses `overwriteResult` across three surfaces:
  1. **GitHub Defang & Clone Guard**: Replaces poisoned `gh` / `gh-axi` output in-flight with `[GitHub Defang Gate]` neutralized text and prepends `[SECURITY ALERT]` when `git clone` / `gh repo clone` introduces untrusted Priority #1 `.agents/` hooks or plugins.
  2. **Wire-Boundary Runaway Output Spillover (`> 16,000` chars)**: Offloads bulky `run_command`, `call_mcp_tool`, and `mcp_*` results (`> 16,000` chars) to `/tmp/ag_wire_spillover_<sha256[:10]>.txt` (`0o600`) and returns a `<= 3,800`-char envelope preserving compact JSON schemas, fatal/error lines, and head/tail previews before `transcript.jsonl` serialization.
  3. **Same-Step Edit Syntax & Quality Diagnostics**: Appends syntax and quality warnings directly to `edit_file` / `write_file` / `replace_file_content` tool results (guarded by `"result" in payload and not payload.get("error")` so `EmitUnpopulated: true` empty-result error payloads are never masked), marking `delivered_inline: true` in `syntax_error_pending.json` to prevent duplicate Turn-`N+1` warnings.
- **Shallow `PreToolUse` `overwrite` Merge Hazard**: In `PreToolUse`, returning `{"decision": "allow", "overwrite": {...}}` performs a **top-level key replacement** on the tool's argument map. Overwriting a nested object key (such as `Arguments` in `call_mcp_tool`) without preserving sibling nested keys will wipe omitted nested fields; always merge against the original nested dict (`_safe_shallow_overwrite(orig_args, updates)`).

---

## 2. SQLite Schema & Timeout Invariants

### 2.1 `registry.sqlite` Memory Schema (`ORDER BY id DESC`)
- **Constraint**: The `memory` table in `~/.local/share/codex/projects/registry.sqlite` has columns:
  `(id, slug, key, value, created_at)`
- **Schema Drift Hazard**: There is **no `updated_at` column**. Any query utilizing `ORDER BY updated_at` will fail with an SQLite operational error.
- **Query Standard**: Always query with `ORDER BY id DESC` when retrieving recent memory seeds.

### 2.2 Bounded Busy Timeout (`PRAGMA busy_timeout=500;`)
- **Constraint**: SQLite transactions inside lifecycle hooks (`pre_invocation_hook.py`, `pre_tool_use_hook.py`, `post_tool_use_hook.py`, `stop_hook.py`) must never block longer than 500ms.
- **Standard**: Always set `PRAGMA busy_timeout=500;` on connection acquisition to prevent hook timeouts.

---

## 3. Subagent Dispatch & Contract Contracts

### 3.1 Native `TypeName` vs `Role` Persona Contract
- **Constraint**: In `invoke_subagent`, the native `TypeName` parameter accepts **only** built-in subagent types:
  - `"research"`: Read-only exploration and inspection.
  - `"self"`: Full read/write/execution capabilities (inheriting parent config).
  - `"image-generator"`: Standalone image generation.
- **Contract**: Specialist personas MUST be specified in the `Role` parameter per the 11-stage matrix:
  - Stage 4 (PM Routing & Contract): `Role: "pm"` (`TypeName: "self"`, `Model: "inherit"`)
  - Stage 5a (Explorers): `Role: "backend-explorer"` | `"frontend-explorer"` | `"research-explorer"` | `"user-tester"` | `"devops"` | `"skillopt-optimizer"` (`TypeName: "research"`, `Model: "flash"`)
  - Stage 5b (Builders & Designers): `Role: "dev-fe"` | `"dev-be"` | `"frontend"` | `"designer"` | `"visual-engineer"` | `"simplifier-reviewer"` | `"meta-evolution"` (`TypeName: "self"`, `Model: "inherit"`)
  - Stage 5c (Deep Architecture, Security & Root-Cause): `Role: "sa"` | `"senior-architect"` | `"critical-planner"` | `"whitehat"` | `"security-audit"` | `"debugger"` (`TypeName: "self"`, `Model: "inherit"`)
  - Stage 5d (Docs & Telemetry Helpers): `Role: "doc-sync-worker"` | `"librarian"` | `"diff-helper"` (`TypeName: "research"`, `Model: "flash"` or `Model: "flash_lite"`)
  - Stage 6 (Fix / Implementation): `Role: "dev-fe"` | `"dev-be"` | `"debugger"` | `"meta-evolution"` (`TypeName: "self"`, `Model: "inherit"`)
  - Stage 7 (QC & Validation): `Role: "frontend-qc"` (`TypeName: "self"`, `Model: "inherit"`) and `Role: "test-runner"` (`TypeName: "research"`, `Model: "flash"`)
  - Stage 8 (Independent Audit): `Role: "oracle-review"` | `"hallucination-auditor"` | `"implementation-review"` (`TypeName: "self"`, `Model: "inherit"`)

### 3.2 6,000-Character Subagent Prompt Ceiling
- **Constraint**: The `Prompt` string passed to `invoke_subagent` must be concise and strictly **$< 6,000$ characters**.
- **Standard**: Transmit minimal Story Shards, file coordinates (`path:line`), and explicit acceptance criteria. Never paste large diffs or multi-thousand line source files into subagent prompts.

### 3.3 Gemini-Only Model Routing Matrix & Escalation Gate
- **Constraint**: Only Gemini models are permitted, pinned to each role's baseline tier:
  - `Model: "inherit"` (`gemini-4-argon-medium` default) for Builders, Architects, PM, QC, and Oracle Review (`TypeName: "self"`). Escalating to `Model: "pro"` (`gemini-4-argon-high` via CLI) triggers `force_ask` and requires explicit user confirmation.
  - `Model: "flash"` (`gemini-3.8-flash-high`) for Explorers, Test Runners, and Enrichment.
  - `Model: "flash_lite"` (`gemini-3.8-flash-low`) for Telemetry and Diff helpers.

---

## 4. Async Execution & Reactive Wakeup Protocol

### 4.1 Zero Polling Invariant
- **Rule**: NEVER poll background tasks in a loop (`while ps`, `manage_task action: 'status'` repeated in a tight loop, or `sleep`).
- **Mechanism**: The Antigravity runtime uses reactive event-driven wakeups. When a background task completes or a subagent responds via `send_message`, execution resumes automatically.
- **Standard**: After launching an asynchronous task or subagent, immediately yield your turn.

---

## 5. Proposer Isolation & Boundary Contracts

### 5.1 Level-1 Intra-Task Proposer Partitioning (`INV` vs `DOM`)
- **`INV` (`meta-invariant-editor`) Scope**:
  - `~/.gemini/antigravity/guidelines/tool-quirks.md`
  - `<workspace>/.antigravity/task_harness/tool_guidance.md`
  - `<workspace>/.antigravity/task_harness/guardrails.json`
  - *Forbidden*: `SKILL.md`, `scripts/*.py`, hooks, `GEMINI.md`, application source code.
- **`DOM` (`meta-domain-editor`) Scope**:
  - `<workspace>/.antigravity/task_harness/SKILL.md`
  - `<workspace>/.antigravity/task_harness/scripts/*.py`
  - *Forbidden*: `tool-quirks.md`, `tool_guidance.md`, `guardrails.json`, hooks, `GEMINI.md`, application source code.

### 5.2 Deterministic `KEEP_BASE` Fallback Invariant
- Candidate modifications to `.antigravity/task_harness/` are evaluated against reference telemetry $e^{(t-1)}$:
  $$\Delta_{\text{behav}} = (\text{err}_{t-1} - \text{err}_{\text{cand}}) + 2(\text{jev}_{t-1} - \text{jev}_{\text{cand}}) + (\text{strikes}_{t-1} - \text{strikes}_{\text{cand}}) + \delta_{\text{deliv}}$$
- **Rule**: If $\Delta_{\text{behav}} \le 0$ or any `.py` script in the overlay fails `py_compile`, the runtime executes `KEEP_BASE`, instantly restoring the previous verified baseline.

## Auto-Healed Tool Quirks (Level-3 Autonomous Loop)

Execution invariants automatically captured and clustered by `auto-harness-healer.py`:

- **`run_command` Quirk**: SWE-agent 50-Hit Search Flood Guard: Unbounded `rg` detected without limits. Pass `-m 50` or pipe to `head -n 50`.
- **`run_command` Quirk**: SWE-agent 50-Hit Search Flood Guard: Unbounded `fd` detected without limits. Pass `--max-results 50` or pipe to `head -n 50`.
- **`run_command` Quirk**: Modern CLI Tool Invariant: Legacy `grep` and `find` forbidden. Use `rg` or `fd`.
- **`run_command` Quirk**: The `cd` command is prohibited in `run_command` (no `Cwd` parameter). Use tool-native dir flags (e.g. `git -C`, `npm --prefix`, `make -C`, `pytest <dir>`) or absolute paths.
- **`run_command` Quirk**: Execution of `sleep` in `run_command` is strictly forbidden. Use `WaitMsBeforeAsync` or `schedule`.
- **`run_command` Quirk**: Command string length exceeds 4,000 chars. Write script or break into steps.
- **`run_command` Quirk**: Strict Targeted Test Execution (Law 22 & AGENTS.md): Untargeted runs blocked. Specify test or `PRE_SHIP=1`.
- **`run_command` Quirk**: Token Economy Invariant: Unbounded `cat` on large files blocked. Use `bat --paging=never`, `head`, or `read_file` (CLI) / `view_file` (IDE).
- **`run_command` Quirk**: Manual ADB coordinate tapping/screencap loops prohibited. Use semantic accessibility actions.
- **`view_file / read_file` Quirk**: Token Economy Invariant: Slice window exceeds 250-line maximum. Narrow the slice window (<= 250 lines).
- **`view_file / read_file` Quirk**: Slice Loop Breaker: 6-slice ceiling reached on a single file. Blocked to prevent token waste; use `rg -n`.
- **`view_file / read_file` Quirk**: Duplicate slice loop: Reading identical line ranges consecutively is blocked by circuit breaker.
- **`view_file / read_file` Quirk**: Outline-First Monolithic File Guard: Files > 400 lines require AST symbol lookup before reading.
- **`view_file / read_file` Quirk**: Pre-Verification Invariant: File does not exist on disk. Check path or use `fd` before reading.
- **`invoke_subagent` Quirk**: Pub/Sub Sparsification Invariant: Subagent `Prompt` length must not exceed 6,000 characters.
- **`manage_task` Quirk**: Token Economy & Anti-Polling Invariant: Consecutive status polling on background task blocked.
- **`agy` Terminal TUI Markdown Streaming Table Quirk**: Bare Markdown pipe tables with cells exceeding 45 characters or containing inline `file://` links cause `agy`'s streaming renderer to dynamically recalculate column widths mid-stream. Because previous lines of wrapped cells are already committed to terminal scrollback, vertical borders (`|`) shift across lines and break column symmetry. Workaround: For multi-sentence or wide cells, render tables inside ```text code blocks using pre-calculated Unicode box-drawing (`┌───┬───┐`, `│`, `├───┼───┤`, `└───┴───┘` via `format-tui-table.py`), or keep pipe tables strictly single-line (`<= 40 chars/cell`, zero inline link URLs).


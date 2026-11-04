# Claude Code SOTA Harness (Antigravity port) — Snapshot & Replication Engine

[![Harness Verification](https://img.shields.io/badge/Verification-6%2F6%20Gates-brightgreen)](scripts/verify-claude-harness.sh)
[![Hook Tests](https://img.shields.io/badge/Hook%20Tests-143%2F143-brightgreen)](.claude/hooks/tests/)
[![MCP Tests](https://img.shields.io/badge/MCP%20Tests-48%2F48-orange)](antigravity/mcp_servers/)
[![Agents](https://img.shields.io/badge/Subagents-28-blue)](.claude/agents/)
[![Skills](https://img.shields.io/badge/Skills-28%20Loaded-purple)](.claude/skills/)

A portable, deterministic, self-verifying agent harness whose **default runtime is Claude Code**. It ports the Antigravity SOTA harness (lifecycle hooks, role-isolated subagents, BMAD Story Shard leases, 3-tier routing, Oracle audit, loop breakers, context-rot prevention, local MCP servers, self-healing scripts) onto Claude Code's native extension surface: `.claude/settings.json` hooks, `.claude/agents/`, `.claude/skills/`, `.claude/commands/`, `.claude/output-styles/`, and `.mcp.json`.

The original Antigravity (Gemini) snapshot is preserved under `antigravity/`, `config/`, `antigravity-cli/`, `bin/`, `lib/` for reference and as the shared source of scripts, guidelines, skillbank, and MCP servers.

---

## Prerequisites

- macOS 13+ or Linux; `bash` 4+, `rsync`, `git`, `jq`
- `python3` 3.9+ on PATH for the hooks (no third-party packages required)
- `uv` (recommended) or `python3 -m venv` with Python 3.11+ for the three local MCP servers
- Node.js 18+ / `npx` for `context7` (and the `archify` skill)
- Optional but recommended: `rg` (ripgrep), `fd`, `ast-grep`; the Bash guard only enforces `rg`/`fd` when they are installed
- Claude Code (`claude` CLI, desktop, or IDE extension)

---

## Quick Start

```bash
git clone <this repo> && cd "Harness Agents V1"

# 1. Verify the snapshot in place (hooks are active for this repo via .claude/settings.json)
bash scripts/verify-claude-harness.sh

# 2. Deploy to ~/.claude so the harness is the default in every project (backups + merge, idempotent)
bash scripts/install-claude-harness.sh

# 3. Capture live ~/.claude changes back into the repo
bash scripts/export-claude-harness.sh
```

Inside Claude Code: `/harness-init` (once per project), `/verify-harness`, `/harness-status`, `/fast-track <task>`, `/standard-dev <request>`, `/goal <epic>`, `/oracle-review`, `/token-check`, `/system-audit`, `/runtime-handoff`, `/dreaming`.

---

## What the harness enforces (Claude Code hook events)

| Event | Hook | Invariants |
| :--- | :--- | :--- |
| `SessionStart` | `session_start.py` | Session grounding anchor (prefix-pin, SOT docs, memory keys), untrusted-customization scan, post-compaction recovery arming |
| `UserPromptSubmit` | `user_prompt_submit.py` | Turn-1 knowledge grounding (memory seeds, graph entities, agentless codegraph symbol localization, Harmony H_gen ⊕ H_env overlay, anti-patterns), syntax/stale-read/plan/context-health/recovery alerts, SOL milestones |
| `PreToolUse` | `pre_tool_use.py` | Jev loop breakers; Bash: destructive/dependency `ask` gates, sleep ban, exit-code masking, pipefail, targeted tests, search flood guard, legacy CLI nudge, role-isolation shell-write guard; Read: image/privacy/scout blocks, read-once, 250-line slice cap (auto-clamp), outline-first > 400 lines with AST skeleton, 3-strike / 6-slice breakers; Grep head_limit injection; Edit/Write: PM zero-code-write, Story Shard leases, test-assertion locks, suppression lock, Aider fuzzy `old_string` repair, in-memory syntax gate, shift-left import guard, shadow git checkpoint; Agent: lease requirement, prompt cap, nesting depth, model escalation `ask`; MCP read-only mutation lock |
| `PostToolUse` | `post_tool_use.py` | Syntax smoke guard (py/json/js/ts), anti-slop + plan-tag + stub guards, session ledgers (reads/mutations/events), structured failure feedback + fail-to-pass remedies, GitHub defang gate, clone hazard scan, wire spillover > 16k chars |
| `PostToolUseFailure` | `post_tool_use_failure.py` | Records failed verifications for the anti-bluffing and stagnation breakers |
| `SubagentStart` / `SubagentStop` | `subagent_start.py` / `subagent_stop.py` | Turn-1 subagent grounding capsule (persona bundle, lease symbol map); scope-drift guard and role trajectory contract |
| `PreCompact` | `pre_compact.py` | LOSS-02 session snapshot + observational buffer; recovery anchor on the next prompt |
| `Stop` | `stop.py` | Oracle plan gate, teardown gate, Causal-Past LTL verification gate + anti-bluffing, Simplify gate, snapshot/lineage/failure harvest, housekeeping, compaction advisory |
| status line | `statusline.py` | Model, dir, branch, context gauge, cost, active gates; mirrors context usage for the 55/65/75% alerts |

Policy knobs live in `.claude/harness/guardrails.json` (slice cap, flood limit, thresholds, `root_may_edit_code`, `ban_cd`, `require_modern_cli`, `block_image_reads`, `notify`).

---

## Repository Layout

```text
.
├── CLAUDE.md                       # Workspace guidelines (Claude Code reads this)
├── .claude/
│   ├── GLOBAL_CLAUDE.md            # Global runtime contract (installed to ~/.claude/CLAUDE.md as a managed block, <= 12,000 chars)
│   ├── settings.json               # Hook registration, statusLine, MCP enablement, deny rules
│   ├── harness/guardrails.json     # Policy knobs
│   ├── hooks/                      # 10 Claude Code hooks + harness_lib.py + tests/ (143 tests)
│   ├── agents/                     # 28 subagents (pm, explorers, sa, critical-planner, dev-fe/be, debugger, designer, QC, oracle, auditors, doc workers, ...)
│   ├── skills/                     # 28 skills ported from antigravity/skills (+ browseros-neo; axi-tools not ported)
│   ├── commands/                   # 11 slash commands (harness-init, fast-track, standard-dev, goal, oracle-review, token-check, system-audit, runtime-handoff, dreaming, verify-harness, harness-status)
│   └── output-styles/adhd-mode.md  # ADHD Mode output contract
├── .mcp.json                       # codegraph, codex_knowledge, context_health (via scripts/mcp-launch.sh), context7
├── scripts/
│   ├── install-claude-harness.sh   # Deploy to ~/.claude (+ ~/.claude/harness shared tree, MCP venvs, user-scope MCP registration)
│   ├── verify-claude-harness.sh    # 6-gate verification
│   ├── export-claude-harness.sh    # Live -> repo capture
│   ├── validate-claude-tree.py     # 5 mechanical tree invariants (incl. CP-2 security guardrails)
│   ├── mcp-launch.sh               # MCP launcher: repo venv -> ~/.claude/harness venv -> uv run
│   └── install/export/verify-harness.sh   # Legacy Antigravity (Gemini) deployment
├── antigravity/                    # Shared tree: mcp_servers/, scripts/ (self-healing, housekeeping, QC), skillbank/, guidelines/, guardrails/, contracts/, coordination/, workflows/, templates/, skills/ (original)
├── config/, antigravity-cli/, bin/, lib/   # Legacy Antigravity snapshot (hooks, TUI, builtin skills)
└── LLM_REPLICATION_GUIDE.md        # Architecture + replication specification (Claude Code section first)
```

---

## Role isolation (hook-enforced)

- **Root thread = `pm`**: intake, routing, Story Shards, orchestration via the Agent tool; never mutates application source (set `root_may_edit_code: true` only for repos where the root thread is the builder, as this harness repo does).
- **Builders** (`dev-fe`, `dev-be`, `debugger`, `designer`, `meta-evolution`): every Agent prompt must carry an `allowed_files:` block; edits outside the lease are denied; tests are immutable without `Oracle-Custody-Lease: UPDATE_ASSERTIONS`.
- **Explorers / QC / Oracle** (`backend-explorer`, `frontend-explorer`, `research-explorer`, `frontend-qc`, `test-runner`, `oracle-review`, `hallucination-auditor`, `implementation-review`, `security-audit`): read-only; mutating MCP tools are locked.
- **Model tiers**: `inherit` (Tier A), `sonnet` (explorers, test-runner, doc workers), `haiku` (diff-helper); escalating a role above its baseline triggers a permission prompt.

---

## Verification gates (`scripts/verify-claude-harness.sh`)

1. Hook unit tests: 143/143 (`.claude/hooks/tests/test_claude_hooks.py`, isolated state dir)
2. MCP pytest suites: codegraph 9, codex_knowledge 13, context_health 26 (skipped with a warning until venvs exist; `STRICT_MCP=1` to fail instead)
3. JSON integrity (`.claude`, `.mcp.json`, `config`, `antigravity-cli`, skill schemas)
4. YAML + agent/skill/command frontmatter integrity
5. Housekeeping sweeper dry-run
6. `validate-claude-tree.py`: byte budget, skill coverage/reach, template braces, hooks/agents/commands/settings compile, CP-2 security guardrail integrity (7/7)

---

## Runtime notes

- Claude Code's Bash hook payload carries stdout/stderr but no exit code, so verification commands are wrapped by PreToolUse to print `[harness] verification exit_code=N` on failure (policy `annotate_verification_exit_codes`); this is what makes the anti-bluffing gate reliable for silent failures.
- Context usage comes from the status line when it runs, otherwise from the session transcript's last `usage` block (1M window for `[1m]` models, else 200k; override with `CLAUDE_HARNESS_CONTEXT_WINDOW`).
- Project-specific test runners: add regexes to `verification_patterns` in `.claude/harness/guardrails.json`.

## Known limitations of the port

- `context_health` MCP tools that parse Antigravity transcripts (`get_session_health`, `compact_observations`, `project_trajectory_toon`) return low-information results under Claude Code; the hooks provide the equivalent read budget, observation buffer, and context alerts natively.
- `agy`-specific TUI tooling (`bin/agy-*`, `lib/agy_tui_core.py`, tmux/herdr layouts) is not ported; the status line covers the live-state mirror.
- `ensure-verification-gates.py` scaffolds `verify-oracle.sh` scripts that still call the `agy` CLI; use the `oracle-review` subagent (`/oracle-review`) instead until those scripts are re-targeted.

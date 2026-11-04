# Workspace Operating Guidelines: Claude Code SOTA Harness

This repository is the canonical, portable snapshot, deployment orchestrator, and verification gatekeeper for the **Claude Code SOTA Harness** (the Antigravity harness ported to Claude Code as the default runtime). The global runtime contract lives at `.claude/GLOBAL_CLAUDE.md` and is installed to `~/.claude/CLAUDE.md` by `scripts/install-claude-harness.sh`.

## 1. Primary Directives & Invariants

1. **Cleanliness Invariant**: never commit or leave ephemeral runtime artifacts (`.venv/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`, `*.egg-info/`, `.sqlite*`, `*.db*`, `*.log`, stray CLI outputs). Run `bash antigravity/scripts/housekeeping.sh --dry-run` before finishing work. Hook runtime state lives outside the repo in `~/.cache/claude_harness/`.
2. **100% Verification Gate Guarantee**: every edit to `.claude/hooks/`, `.claude/agents/`, `.claude/skills/`, `.claude/commands/`, or the MCP servers MUST pass `bash scripts/verify-claude-harness.sh` (hook unit tests, MCP pytest suites, JSON/YAML integrity, housekeeping dry-run, and `scripts/validate-claude-tree.py` incl. CP-2 Security Guardrail Integrity). Harmony Harness (`arXiv:2610.15150`) remains the evolution contract: CP-1 factorized evolution, CP-2 3-axis Pareto gate (`func_score`, `sec_score`, `token_score`), CP-3 SQLite Pareto archive.
3. **Deterministic Deployment**: deploy repo -> live via `bash scripts/install-claude-harness.sh`; capture live -> repo via `bash scripts/export-claude-harness.sh`. Never overwrite `~/.claude/` files without the installer's backup.
4. **Legacy tree**: `antigravity/`, `config/`, `antigravity-cli/`, `bin/`, `lib/` are the original Antigravity (Gemini) snapshot kept for reference, MCP server sources, scripts, and the legacy installer (`scripts/install-harness.sh`). New work targets `.claude/` first.

## 2. Key Architecture & SOT Pointers

- **Blueprint & Global Contract**: `LLM_REPLICATION_GUIDE.md` | `.claude/GLOBAL_CLAUDE.md`
- **Hooks (Claude Code events)**: `.claude/settings.json` -> `.claude/hooks/{session_start,user_prompt_submit,pre_tool_use,post_tool_use,post_tool_use_failure,subagent_start,subagent_stop,pre_compact,stop,statusline}.py` + `harness_lib.py`; tests in `.claude/hooks/tests/`
- **Subagents / Skills / Commands**: `.claude/agents/*.md` | `.claude/skills/*/SKILL.md` | `.claude/commands/*.md` | `.claude/output-styles/adhd-mode.md`
- **Policy & MCP**: `.claude/harness/guardrails.json` | `.mcp.json` (codegraph, codex_knowledge, context_health, context7)
- **Harness², Self-Healing & Skillbank (shared with legacy)**: `antigravity/scripts/` | `antigravity/skillbank/INDEX.md` | `antigravity/guidelines/tool-quirks.md` | `antigravity/mcp_servers/`

## 3. Subagent Leases (enforced by hooks)

- **Root thread (`pm`)**: requirements, Story Shards, verification oversight; never mutates application code (docs, plans, configs, and `.claude/` allowed).
- **`dev-be` / `dev-fe` / `debugger` / `designer`**: edits strictly within the `allowed_files:` block of their Agent prompt.
- **`oracle-review` / `hallucination-auditor` / explorers / QC**: read-only independent audit and drift detection.

## 4. Working in this repo

- Hook changes: edit, then `python3 -m unittest discover -s .claude/hooks/tests -p "test_*.py"`; keep hooks runnable on system `python3` (3.9+), fail-open on internal errors, and under the per-event timeouts in `.claude/settings.json`.
- The harness is active inside this repo (project settings): expect `deny`/`ask` decisions from your own gates (pipefail on piped verification commands, bounded `rg`, `allowed_files` leases for builder subagents, no `cat` on files > 200 lines).

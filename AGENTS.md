<!-- BEGIN HARNESS_WORKSPACE_AGENTS_MD -->
# Workspace Operating Guidelines: Claude Code SOTA Harness

Canonical portable snapshot, deployment orchestrator, and verification gatekeeper for the **Claude Code SOTA Harness** (default runtime: Claude Code; global runtime contract lives at `.claude/GLOBAL_CLAUDE.md`). `CLAUDE.md` is the primary workspace guide for Claude Code; this file mirrors it for other runtimes (Codex, OpenCode, Antigravity).

## 1. Primary Directives & Invariants

1. **Cleanliness Invariant**: never commit or leave ephemeral runtime artifacts (`.venv/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`, `*.egg-info/`, `.sqlite*`, `*.db*`, `*.log`, stray CLI outputs). Run `bash antigravity/scripts/housekeeping.sh --dry-run` before finishing work. Hook state lives in `~/.cache/claude_harness/`.
2. **100% Verification Gate Guarantee**: every edit to `.claude/hooks/`, `.claude/agents/`, `.claude/skills/`, `.claude/commands/`, or the MCP servers MUST pass all 6 gates via `bash scripts/verify-claude-harness.sh` (143 hook unit tests, 3/3 MCP pytest suites [48/48], JSON, YAML/frontmatter, housekeeping, and 5/5 `scripts/validate-claude-tree.py` checks including CP-2 Security Guardrail Integrity). Harmony Harness (`arXiv:2610.15150`) stays the evolution contract: CP-1 factorized evolution, CP-2 3-axis Pareto gate (`func_score`, `sec_score`, `token_score`), CP-3 SQLite Pareto archive.
3. **Deterministic Deployment**: deploy repo -> live via `bash scripts/install-claude-harness.sh`; capture live -> repo via `bash scripts/export-claude-harness.sh`. Never overwrite `~/.claude/` files without the installer's backup. Legacy Antigravity deployment (`~/.gemini`) remains available via `scripts/install-harness.sh`.

## 2. Key Architecture & SOT Pointers

- **Blueprint & Global Contract**: `LLM_REPLICATION_GUIDE.md` | `.claude/GLOBAL_CLAUDE.md` | `CLAUDE.md`
- **Hooks, MCP & Lifecycle**: `.claude/settings.json` | `.claude/hooks/*.py` | `.mcp.json` | `scripts/{install,export,verify}-claude-harness.sh`
- **Agents, Skills, Commands**: `.claude/agents/` | `.claude/skills/` | `.claude/commands/` | `.claude/output-styles/adhd-mode.md`
- **Harness², Self-Healing & Skillbank**: `antigravity/scripts/` | `antigravity/skillbank/INDEX.md` | `antigravity/guidelines/tool-quirks.md`

## 3. Subagent Leases

- **`pm`** (root thread): requirements, Story Shards, verification oversight; never mutates application code (this repo sets `root_may_edit_code: true` in `.claude/harness/guardrails.json` because its hooks and scripts are the product).
- **`dev-be` / `dev-fe` / `debugger` / `designer`**: hook/MCP/script/UI edits strictly within leased Story Shards (`allowed_files`).
- **`oracle-review` / `hallucination-auditor` / explorers / QC**: read-only independent audit and drift detection.
<!-- END HARNESS_WORKSPACE_AGENTS_MD -->

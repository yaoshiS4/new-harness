# Claude Code SOTA Harness: LLM Replication & Architectural Specification

> **Version**: 3.0-claude (Antigravity 2.5-SOTA ported to Claude Code)
> **Default Runtime**: Claude Code (CLI, desktop, IDE extension)
> **Canonical Tree**: `.claude/` (hooks, agents, skills, commands, output-styles) + `.mcp.json` + `scripts/*-claude-harness.sh`
> **Verification Status**: 139/143 hook unit tests | 48/48 MCP tests (codegraph 9, codex_knowledge 13, context_health 26) | 6/6 verification gates | 5/5 tree invariants (CP-2 7/7)

## Section 0: Claude Code Port (read this first)

### 0.1 One-command replication

```bash
bash scripts/verify-claude-harness.sh          # verify the snapshot in place
bash scripts/install-claude-harness.sh         # deploy to ~/.claude (backup + merge, idempotent)
bash scripts/export-claude-harness.sh          # capture live ~/.claude back into the repo

```

The installer: backs up `~/.claude/{CLAUDE.md,settings.json,agents,skills,commands,output-styles,hooks,harness}` (keeps 3), syncs the `.claude/` components, writes the managed block of `.claude/GLOBAL_CLAUDE.md` into `~/.claude/CLAUDE.md`, merges hooks/statusLine/env/deny rules into `~/.claude/settings.json` (global hooks defer to a project's own harness hooks to avoid double execution), copies the shared tree to `~/.claude/harness/` (scripts, skillbank, guidelines, guardrails, contracts, coordination, workflows, templates, docs, mcp_servers), creates MCP venvs with `uv` (Python 3.12), writes `~/.claude/harness/mcp.user.json` and registers the servers at user scope when the `claude` CLI is available, then runs the verification gate.

### 0.2 Mapping: Antigravity -> Claude Code

| Antigravity | Claude Code |
| :--- | :--- |
| `~/.gemini/GEMINI.md` (GLOBAL_AGENTS.md) | `~/.claude/CLAUDE.md` managed block from `.claude/GLOBAL_CLAUDE.md` (<= 12,000 chars) |
| `config/hooks.json` PreInvocation / SessionStart | `UserPromptSubmit` (`user_prompt_submit.py`) / `SessionStart` (`session_start.py`) |
| `pre_tool_use_hook.py` on `run_command`/`view_file`/`write_to_file`/... | `pre_tool_use.py` on `Bash`/`Read`/`Edit`/`Write`/`MultiEdit`/`Grep`/`Glob`/`Agent`/`mcp__*` |
| `post_tool_use_hook.py` (`overwriteResult`) | `post_tool_use.py` (`updatedToolOutput`, `additionalContext`, `decision: block`) + `post_tool_use_failure.py` |
| `stop_hook.py` (`decision: continue`) | `stop.py` (`decision: block` + `reason`), `subagent_stop.py`, `pre_compact.py` |
| `invoke_subagent(TypeName, Role, Model, Prompt)` | `Agent(subagent_type=<.claude/agents name>, prompt, model)`; builders need `allowed_files:` in the prompt |
| Model tiers `flash_lite` / `flash` / `inherit` / `pro` (force_ask) | `haiku` / `sonnet` / `inherit` / `opus`+`fable` (PreToolUse `ask`) |
| `call_mcp_tool(ServerName, ToolName)` | `mcp__<server>__<tool>` from `.mcp.json` |
| `antigravity/skills/*/SKILL.md` | `.claude/skills/*/SKILL.md` (28 ported, runtime notes prepended) |
| `antigravity/workflows/*.md` | `.claude/commands/*.md` (`/fast-track`, `/standard-dev`, `/goal`, `/oracle-review`, `/token-check`, `/system-audit`, `/runtime-handoff`, `/dreaming`, `/verify-harness`, `/harness-status`) |
| `agy-statusline` -> `antigravity_live_state.json` | `statusline.py` -> `~/.cache/claude_harness/live_state.json` |
| `/tmp/.antigravity_*` ledgers + transcript parsing | `~/.cache/claude_harness/sessions/<session>[/agent_<id>]/{actions,reads,events,mutations,superseded,err_sig,leases,flags}` |
| `validate-harness-tree.py` | `scripts/validate-claude-tree.py` |

### 0.3 Role detection and leases

Hooks receive `agent_type`/`agent_id` inside subagents; the main thread is the `pm`. Leases are resolved from the subagent transcript's first user message (the Agent prompt) or from the parent's recorded lease (`leases.json`, written by `PreToolUse(Agent)`). `harness_lib.ROLE_SKILL_BUNDLES`, `BUILDER_ROLES`, `READONLY_ROLES`, and the model tier tables define the matrix; `.claude/agents/*.md` frontmatter declares `tools`, `model`, `skills`, `disallowedTools: Agent, Task`.

### 0.4 Deliberate deviations (policy knobs in `.claude/harness/guardrails.json`)

`ban_cd: false` (Claude Code's Bash tool handles `cd`), `require_modern_cli: auto` (block `grep`/`find` only when `rg`/`fd` exist), destructive/dependency commands become permission prompts (`ask`), `root_may_edit_code` (false by default; true only in this harness repo), `block_image_reads` (true), `notify` (false; macOS `osascript` when enabled).

### 0.5 Verification acceptance criteria (`scripts/verify-claude-harness.sh`)

1. Hook unit tests 143/143 (`CLAUDE_HARNESS_STATE_DIR` isolated).
2. MCP pytest 48/48 (venvs at `antigravity/mcp_servers/*/.venv` or `~/.claude/harness/mcp_servers/*/.venv`; `STRICT_MCP=1` to fail when absent).
3. JSON integrity. 4. YAML + frontmatter integrity. 5. Housekeeping dry-run (Python 3.9 compatible). 6. `validate-claude-tree.py` 5/5 (byte budget, skill coverage/reach < 0.90 overlap, template braces, hooks/agents/commands/settings compile, CP-2 security guardrails 7/7).

### 0.6 Known gaps

`context_health` transcript-based MCP tools are low-value under Claude Code (hooks provide the equivalents); `ensure-verification-gates.py` still scaffolds `agy`-based oracle scripts (use `/oracle-review`); `agy` TUI tooling (`bin/agy-*`, `lib/agy_tui_core.py`) is not ported; the legacy `export-harness.sh` still writes `/home/heocop` paths.

---

# Legacy: Antigravity SOTA Harness Specification (Gemini runtime, kept for reference)

> **Version**: 2.5-SOTA  
> **Target Runtime**: Google DeepMind Antigravity & Antigravity CLI (`agy`)  
> **Source Root**: `~/.gemini`  
> **Repository**: `/home/heocop/Projects/antigravity_settings`  
> **Verification Status**: 371/371 Hook Unit Tests Passed | 3/3 Local MCP Pytest Suites (48 Tests) Passed | 6/6 Verification Gates Passed (100% Integrity)

---

## Section 1: Quick 1-Command Replication & Verification

To replicate, deploy, or restore this entire SOTA agentic harnessing environment onto any Linux system with Python 3.11+ and `uv` (or `pip`), execute:

```bash
# 1. Clone or navigate to the harness repository
cd /home/heocop/Projects/antigravity_settings

# 2. Deploy the complete harness to ~/.gemini (idempotent, automated backups included)
bash scripts/install-harness.sh

# 3. Verify 100% of the verification gates (Hooks, MCPs, JSON/YAML schemas, Housekeeping, Harness Tree)
bash scripts/verify-harness.sh
```

### Verification Gate Acceptance Criteria
When `scripts/verify-harness.sh` completes, all 6 gates must report `[PASS]`:
1. **Hook Unit Tests**: 371 unit tests passing across 11 suites (`test_e2e_review_fixes.py` [52], `test_global_hooks.py` [157], `test_harness2_upgrades.py` [49], `test_hooks.py` [10], `test_level3_self_healing.py` [20], `test_research_harmonization.py` [21], `test_rsi_shard_a.py` [9], `test_rsi_shard_b.py` [15], `test_shard_b_harmonization.py` [23], `test_tui_e2e.py` [6], `test_wave4_lifecycle_d1.py` [9]).
2. **MCP Server Pytest Suites** (48 tests across 3 local servers):
   - `codegraph`: 9/9 tests passing (RepoMap, pagerank, AST parsing, extract_symbols, batch_query, spillover resilience).
   - `codex_knowledge`: 13/13 tests passing (bi-temporal graph, hybrid search, RRF, batch_knowledge_query, settings_review_queue).
   - `context_health`: 26/26 tests passing (NeurIPS DL4Code observation masking, token budget, AST skeleton, spillover_large_payload, project_trajectory_toon).
3. **JSON Structural Integrity**: All tool schemas and configuration manifests strictly valid.
4. **YAML Structural Integrity**: All agent contracts, handoffs, and manifests strictly valid.
5. **Housekeeping Sweeper**: Cache sweeper (`housekeeping.sh --dry-run`) executing cleanly with zero errors.
6. **Mechanical Harness Tree Invariants**: `validate-harness-tree.py` verifying byte budget (<= 12,000 chars), 29/29 skill trigger coverage, template brace escaping, script compilation (all 32 validated scripts), and CP-2 security guardrail integrity (5/5 invariants).

---

## Section 2: Complete Directory Map & Host Filesystem Mapping

The harness snapshot is organized into three primary operational trees that mirror the host `~/.gemini` hierarchy:

```
/home/heocop/Projects/antigravity_settings/
├── LLM_REPLICATION_GUIDE.md        # Comprehensive LLM replication specification (this document)
├── README.md                       # Repository overview and fast-start manual
├── AGENTS.md                       # Workspace root operational guidelines and role contracts
├── scripts/
│   ├── export-harness.sh           # Idempotent exporter (captures latest live ~/.gemini settings into repo snapshot)
│   ├── install-harness.sh          # Idempotent deployer (backups, rsync, symlinks, uv venv setup)
│   └── verify-harness.sh           # Out-of-process verification gate (371 tests across 11 suites + MCPs [48] + schemas + tree validator)
├── config/                         # Maps directly to ~/.gemini/config/
│   ├── config.json                 # Core runtime user settings and plugin toggles
│   ├── hooks.json                  # Lifecycle hook registry (PreInvocation, PreToolUse, PostToolUse, Stop)
│   ├── mcp_config.json             # MCP server activation config (codegraph, codex_knowledge, browseros-neo, etc.)
│   ├── plugins.json                # Plugin registry
│   ├── skills.json                 # Custom skill root registration
│   ├── hooks/                      # Active Python hook implementations and test suite
│   │   ├── pre_invocation_hook.py  # Turn-1 SOT grounding, symbol localization, stale tombstoning, Harmony H_gen ⊕ H_env
│   │   ├── pre_tool_use_hook.py    # BMAD Story Shard leases, AST gate, search flood guard, diff hints
│   │   ├── post_tool_use_hook.py   # Syntax smoke guard, SHA-256 read ledger updater
│   │   ├── stop_hook.py            # LTL verification, Oracle watchdog, session state snapshot, pre-unlink harvest
│   │   ├── herdr-agent-state.sh    # Multi-agent state capture utility
│   │   └── tests/                  # 371 comprehensive unit tests across 11 test suites
│   │       ├── test_e2e_review_fixes.py
│   │       ├── test_global_hooks.py
│   │       ├── test_harness2_upgrades.py
│   │       ├── test_hooks.py
│   │       ├── test_level3_self_healing.py
│   │       ├── test_research_harmonization.py
│   │       ├── test_rsi_shard_a.py
│   │       ├── test_rsi_shard_b.py
│   │       ├── test_shard_b_harmonization.py
│   │       ├── test_tui_e2e.py
│   │       └── test_wave4_lifecycle_d1.py
│   ├── scripts/                    # Helper launchers for optional/sidecar MCP servers
│   │   ├── launch-open-design-mcp.sh
│   │   └── launch-stitch-mcp.sh
│   └── skills/                     # Workspace-level skills
│       └── browseros-neo/          # BrowserOS Neo dedicated agent browser integration
├── antigravity/                    # Maps directly to ~/.gemini/antigravity/
│   ├── GLOBAL_AGENTS.md            # Global Source-of-Truth agent instructions (symlinked to ~/.gemini/GEMINI.md)
│   ├── mcp_servers/                # In-repo local MCP server implementations
│   │   ├── codegraph/              # Tree-sitter + SQLite + PPR RepoMap MCP Server (9 pytest tests)
│   │   ├── codex_knowledge/        # Bi-temporal SQLite knowledge graph & hybrid BM25/Vector memory (13 pytest tests)
│   │   └── context_health/         # DL4Code observation masking, token budget & AST skeleton (26 pytest tests)
│   ├── skills/                     # 28 SOTA agent skills (+ 1 workspace skill browseros-neo in config/skills/ = 29 total)
│   ├── scripts/                    # System maintenance, self-healing, and validation scripts (32 validated scripts)
│   │   ├── auto-harness-healer.py  # Darwin Gödel Machine 5-stage closed self-healing loop
│   │   ├── burn-rate-sentinel.py   # S0-S3 severity burn-rate sentinel & escalation
│   │   ├── clean-diff.sh           # Clean git diff viewer
│   │   ├── consolidate-memory-graph.py # Dynamic memory graph consolidator
│   │   ├── dream-replay-simulator.py # Dream-RSI counterfactual replay simulator & autoresearch ratchet
│   │   ├── ensure-verification-gates.py # Automatic Oracle gate scaffolding script
│   │   ├── external-research-scout.py   # PaperQA2/OpenScholar empirical literature & repo scout (7-day cache)
│   │   ├── housekeeping.py         # Inter-session cache & SQLite WAL sweeper engine
│   │   ├── housekeeping.sh         # Wrapper for housekeeping.py
│   │   ├── recursive-ppc-engine.py # Recursive predictive processing & confidence engine
│   │   ├── reflect-experience.py   # Experience reflection and episodic memory consolidation
│   │   ├── report-schema.json      # Security audit report schema symlink
│   │   ├── restore-shadow-checkpoint.py # Shadow checkpoint restore utility
│   │   ├── run-compiled-qc.py      # Compiled language QC runner
│   │   ├── select-affected-tests.py # Risk-based affected test selector
│   │   └── validate-harness-tree.py # Mechanical harness tree validator (Harness² protocol)
│   ├── guidelines/                 # UI Apex invariants, anti-slop taxonomy, API contracts, tool-quirks.md
│   ├── guardrails/                 # Anti-hallucination rules, monotonic progress, PM constraints
│   ├── contracts/                  # Agent handoff schemas, PM task contracts, scope drift contracts
│   ├── coordination/               # Sequential pipeline, gates, context budgeting
│   ├── workflows/                  # Standard dev workflow, fast track, dreaming consolidation, runtime handoff
│   ├── docs/                       # Skill registry and system architecture documentation
│   ├── templates/                  # Implementation plan, task list, ADR, and PLAN.md templates
│   └── skillbank/                  # Curated failure lessons, optimized patterns, research cache, and INDEX.md
└── antigravity-cli/                # Maps directly to ~/.gemini/antigravity-cli/
    ├── settings.json               # IDE/CLI auto-approval, statusline, and workspace trust
    ├── mcp/                        # Lazy-loaded tool JSON schemas for all MCP servers
    │   ├── browseros-neo/          # BrowserOS Neo browser automation schemas
    │   ├── codegraph/              # Code graph exploration schemas
    │   ├── codex_knowledge/        # Knowledge graph, episodic memory, and handoff schemas
    │   ├── context7/               # External Upstash documentation query schemas
    │   ├── context_health/         # Token budgeting and observation masking schemas
    │   ├── open-design/            # OpenDesign canvas & artifact schemas
    │   └── StitchMCP/              # Stitch UI design system and screen generation schemas
    └── builtin/skills/             # Builtin CLI skills (agy-customizations, antigravity_guide, etc.)
```

### Filesystem Host Mapping Table

| Snapshot Relative Path | Host Target Path | Purpose |
| :--- | :--- | :--- |
| `config/` | `~/.gemini/config/` | Hook registration, MCP registry, core CLI settings |
| `config/hooks/` | `~/.gemini/config/hooks/` | Active lifecycle hook scripts and 371 unit tests across 11 suites |
| `config/skills/browseros-neo/` | `~/.gemini/config/skills/browseros-neo/` | BrowserOS Neo skill and configuration |
| `antigravity/` | `~/.gemini/antigravity/` | Customization engine: skills, guidelines, MCP servers, scripts |
| `antigravity/GLOBAL_AGENTS.md` | `~/.gemini/GEMINI.md` | **Symlinked canonical SOT instruction document** |
| `antigravity/mcp_servers/` | `~/.gemini/antigravity/mcp_servers/` | Source code and virtual environments for local MCP servers |
| `antigravity/guidelines/tool-quirks.md` | `~/.gemini/antigravity/guidelines/tool-quirks.md` | Documented tool quirks, limit workarounds, and CLI invariants |
| `antigravity/skillbank/INDEX.md` | `~/.gemini/antigravity/skillbank/INDEX.md` | Indexed registry of curated failure lessons and task patterns |
| `antigravity-cli/settings.json` | `~/.gemini/antigravity-cli/settings.json` | Antigravity CLI execution engine configuration |
| `antigravity-cli/mcp/` | `~/.gemini/antigravity-cli/mcp/` | Lazy tool schemas exposed to agents via `call_mcp_tool` |

---

## Section 3: Lifecycle Hooks Architecture (`config/hooks/`)

The hook pipeline executes deterministically around every model turn and tool call, enforcing SWE-agent, BMAD, and NeurIPS-validated invariants.

### 1. `pre_invocation_hook.py` (PreInvocation Gate)
Fires before the model begins its turn.
- **Turn-1 SOT Grounding**: Checks workspace documentation (`docs/STATUS.md`, `README.md`, `AGENTS.md`) and pre-populates relevant context from `codex_knowledge` and `codegraph`.
- **`UG-05` Agentless Turn-1 Hierarchical Symbol Localization**: Extracts symbols from user prompts and queries the AST symbol index before tool execution begins, eliminating initial blind `grep`/`find` searches.
- **`UG-03` Stale-Read Superseding Tombstones**: Injects warnings if an agent attempts to reason over cached file contents modified by another agent or external process.
- **`LOSS-02` Post-Compaction Recovery Anchor**: Injects a structured summary of architectural decisions and active Story Shards immediately following a `/compact` event or context trim.
- **Auto-Heal Alert Consumption**: Reads and clears Turn-1 self-healing notices generated by `auto-harness-healer.py`.
- **Oracle Plan Watchdog**: Enforces that for complex tasks, an approved plan file (`implementation_plan.md`) must exist and have been modified within 30 minutes (`st_mtime <= 1800`), preventing stale or ungrounded execution loops.

### 2. `pre_tool_use_hook.py` (PreToolUse Safety & Policy Gate)
Fires immediately before any tool call executes, inspecting arguments and environmental context.
- **Role Isolation & BMAD Story Shard Leases**:
  - Validates caller role against `allowed_files` patterns.
  - Blocks `dev-fe`, `dev-be`, or subagents from mutating files outside their leased Story Shard.
  - Enforces this invariant on both structured file tools (CLI `write_file`, `edit_file`, `read_file`; IDE `write_to_file`, `replace_file_content`, `view_file`) and shell write attempts (`cat >`, `echo >`, `sed -i`, `python3` scripts modifying files).
- **Outline-First 400-Line AST Skeleton Gate & 250-Line Slice Cap**:
  - Files larger than 400 lines cannot be viewed completely in one call (`read_file` / `view_file`); requires reading the symbol outline or AST first.
  - Slicing windows are strictly capped at 250 lines to prevent context window blowouts.
- **3-Strike Read Ledger**: Blocks repeated reading of identical file slices (max 3 reads without mutation or intermediate progress).
- **3-Strike Jev Loop Circuit Breaker**: Tracks consecutive tool error signatures; trips and halts the loop if identical tool errors recur 3 times.
- **`UG-01` SWE-agent Pre-Write In-Memory AST/Syntax Gate**:
  - Intercepts proposed writes and edits in-memory *before* touching disk.
  - Verifies syntax for Python (`ast.parse`), JSON/JSONC (`json.loads`), YAML (`yaml.safe_load`), TOML (`tomllib.loads`), and Shell (`bash -n`).
  - Blocks syntactically invalid edits and provides precise error messages to the model.
- **`UG-02` + `LOSS-01` Aider 1-Turn Fuzzy Patch Auto-Application**:
  - When `edit_file` (CLI) / `replace_file_content` (IDE) fails exact string matching due to indentation or line number drift, computes `difflib` closest matches and suggests fuzzy repair hints or applies single-turn reconciliation.
- **`UG-04` SWE-agent 50-Hit Search Flood Guard**:
  - Mechanical gate blocking unbounded `rg` (ripgrep) or `fd` calls that would saturate context tokens.
  - Mandates `--max-results 50` or explicit pipe limits (e.g., `| head -n 50`).
- **`CK-01` `scout-block` Vendor Directory Gate**: Blocks broad searches inside `node_modules`, `vendor/`, `.git/`, `.venv/`, and `__pycache__/`.
- **`CK-02` `privacy-block` Secret Gate**: Scans shell commands and file contents for accidental disclosure of API keys, credentials, and environment tokens.
- **Shift-Left TS/JS Import Verification**: Validates imports before file writes complete.

### 3. `post_tool_use_hook.py` (PostToolUse Gate)
Fires immediately after a tool finishes execution.
- **Syntax Smoke Guard**: Validates that files modified on disk remain syntactically sound.
- **`UG-03` SHA-256 Read-Ledger Mutation Recorder**:
  - Computes and records the SHA-256 hash of modified files in the session read ledger.
  - Invalidates stale cached reads across all active subagents, ensuring global consistency.

### 4. `stop_hook.py` (Stop & Teardown Gate)
Fires when the agent attempts to conclude its invocation or submit a final response.
- **`NO_TOOL_CALL` / `model_stop` Interception**: Inspects agent state before allowing completion.
- **Causal Past LTL (Linear Temporal Logic) Verification Gate**:
  - Enforces that any code mutation (CLI `write_file`, `edit_file` / IDE `write_to_file`, `replace_file_content`; read-only via CLI `read_file` / IDE `view_file`) MUST be followed in the causal past of the trajectory by an execution of the test/verification suite.
  - Halts unverified submissions with a `Fail: Code modified without fresh test execution` notice.
- **Autonomous Oracle Plan Gate**: Validates that all items declared in the implementation plan have been completed and verified.
- **Teardown Memory-Sync Gate**: Requires lessons learned or architectural changes to be persisted to `codex_knowledge` or workspace documentation.
- **Pre-Unlink Failure Log Harvest**: Collects pending failure logs for sleep-time consolidation before unlinking.
- **`LOSS-02` Session-State Snapshot Writer**: Persists active state to temporary cache so interrupted sessions can be resumed seamlessly.
- **`CK-03` `simplify-gate`**: Issues advisory warnings if single-turn changes exceed 400 LOC or modify more than 8 files.
- **65% Auto-Compact Trigger**: Evaluates token consumption and triggers proactive compaction before context degradation occurs.
- **Temporary Cache Cleanup**: Safely prunes ephemeral flags and markers.

### 5. Hook Test Suites (371 Tests Across 11 Suites)
- `test_e2e_review_fixes.py` (52 tests): End-to-end regression tests covering review fixes, gate edge-cases, and invariant preservation.
- `test_global_hooks.py` (157 tests): In-depth tests for quoting, slicing, gates, LTL, search flood guards, and syntax checks.
- `test_harness2_upgrades.py` (49 tests): Tests for Harness² protocol upgrades, outline gates, Code-Mode MCP batching, and token budgets.
- `test_hooks.py` (10 tests): Unit tests for core lifecycle hook execution.
- `test_level3_self_healing.py` (20 tests): Tests for Darwin Gödel Machine sandbox rollback, 5-stage closed loop, burn-rate sentinel, external scout caching, pre-unlink harvesting, and Harmony Harness (`arXiv:2610.15150`) CP-1 factorized evolution, CP-2 Pareto dominance/security floor, and CP-3 SQLite archive/Turn-1 composition.
- `test_research_harmonization.py` (21 tests): Tests for Research Subagent tool governance, model tier enforcement, and telemetry contracts.
- `test_rsi_shard_a.py` (9 tests): Empirical failure clustering, tool quirks canonicalization, MAP-Elites niche grid, receipt verification, and Mendelian trait crossover.
- `test_rsi_shard_b.py` (15 tests): Level-2 reflection bridge CLI, workspace experience harvesting, GEPA skill Pareto, DOM hints, Dream-RSI simulation, worktree ratchet, and dynamic guardrail promotion.
- `test_shard_b_harmonization.py` (23 tests): Harmonization, TUI table formatting, verification command detection, and prompt cache alignment.
- `test_tui_e2e.py` (6 tests): End-to-end tests for TUI state reset, multi-session tmux isolation, subagent role mapping, and Unicode box-drawing diagram formatting.
- `test_wave4_lifecycle_d1.py` (9 tests): Tests for lifecycle hook harmonization, transcript trajectory seeding, and runtime contract guards.

---

## Section 4: Level-3 Self-Healing & Harmony Harness (`arXiv:2610.15150`)

The harness incorporates Level-3 Self-Healing, Harness², and Harmony Harness (`arXiv:2610.15150`) autonomous meta-evolution mechanisms:

1. **Darwin Gödel Machine Closed Loop (`auto-harness-healer.py`)**:
   - Executes a 5-stage autonomous loop: `Harvest -> Cluster -> Scout -> Patch -> Verify`.
   - Patches are applied inside an isolated sandbox environment.
   - If verification tests degrade (pass count decreases or regressions emerge), the sandbox is rolled back immediately with zero state corruption.
2. **CP-1 Factorized Evolution ($\mathcal{H}_{\text{gen}} \oplus \mathcal{H}_{\text{env}}$)**:
   - Factorizes self-healing into global rules ($\mathcal{H}_{\text{gen}}$ in `tool-quirks.md`) and project-scoped environment overlays ($\mathcal{H}_{\text{env}}$ in `skillbank/env_overlays/<slug>.md`).
   - Prevents project-local invariant fixes from polluting or bloating the global agent harness.
3. **CP-2 3-Axis Pareto Non-Dominated Gate**:
   - Evaluates prospective repairs along 3 Pareto objectives: functional correctness (`func_score`), security integrity (`sec_score`), and token economy (`token_score`).
   - Enforces a **Hard Security Floor** (`sec_score >= 1.0` and `func_score >= 1.0`): any candidate introducing unsafe flags (`--no-verify`, `eval(`, `shell=True`) is immediately rolled back (`KEEP_BASE`).
   - Admits only Pareto non-dominated points against historical points.
4. **CP-3 SQLite Pareto Archive & Turn-1 Dynamic Composition**:
   - Persists the active Pareto frontier in `harness_pareto_archive` within SQLite.
   - Dynamically selects optimal profiles (`strict_security` for auth/migration/destructive turns vs `balanced_velocity` for standard refactors).
   - Injects composed $\mathcal{H}_{\text{gen}} \oplus \mathcal{H}_{\text{env}}$ directives at Turn-1 via `_compose_harmony_harness_overlay` in `pre_invocation_hook.py`.
5. **Burn-Rate Sentinel (`burn-rate-sentinel.py`)**:
   - Tracks operational failures weighted by severity: S0 (critical/data loss, weight 1.0), S1 (gate block/infinite loop, weight 0.25), S2 (tool error/syntax, weight 0.05), S3 (advisory/token warning, weight 0.01).
   - Triggers proactive auto-healing when the 1-hour burn-rate score exceeds configured thresholds.
6. **External Research Scout (`external-research-scout.py`)**:
   - Queries arXiv, Semantic Scholar, and GitHub Repositories for failure vertices.
   - Uses PaperQA2 empirical evidence scoring to filter non-empirical blog posts and marketing fluff.
   - 7-day local disk caching in `antigravity/skillbank/research_cache/` provides `< 5ms` instant offline lookups.
7. **Harness Tree Validator (`validate-harness-tree.py`)**:
   - Mechanical check enforcing 5 SOTA structural invariants:
     - Check 1: `GEMINI.md` always-on byte budget <= 12,000 characters.
     - Check 2: Skill trigger & index coverage ensures all 29 skills in `antigravity/skills/` and `config/skills/` are accounted for in `GEMINI.md`, `pre_invocation_hook.py`, or `skillbank/INDEX.md`.
     - Check 3: Template brace sanitizer detects unescaped `{{` or `{%` outside fenced code blocks.
     - Check 4: Script existence & compilation check verifies all 32 registered `.py` and `.sh` scripts pass `py_compile` and `bash -n`.
     - Check 5: Security Guardrail Integrity check verifies 5/5 critical invariants in `pre_tool_use_hook.py` (vendor directory block, secret/privacy block, Story Shard lease enforcement, pre-write in-memory AST gate, destructive command guard).

---

## Section 5: Active & Optional MCP Servers

All MCP servers are configured in `config/mcp_config.json` with lazy schemas defined in `antigravity-cli/mcp/`.

### 1. `codegraph` (`antigravity/mcp_servers/codegraph`)
A high-performance code graph server backed by Tree-sitter and SQLite (9 pytest tests passing).
- **RepoMap Generation**: Implements Personalized PageRank (PPR) with binary-search token budgeting to pack the most architecturally significant classes, functions, and relationships into a compact token window.
- **25-Language `summarize_path`**: Generates AST symbol summaries with a strict `limit=50` invariant across Python, TypeScript, JavaScript, Go, Rust, C++, Java, Kotlin, and more.
- **Impact Analysis & Call Graph**: Provides `callers_callees`, `symbol_lookup`, `impact_analysis`, and `changed_symbols` tools.

### 2. `codex_knowledge` (`antigravity/mcp_servers/codex_knowledge`)
The bi-temporal persistent knowledge and episodic memory engine (13 pytest tests passing).
- **Bi-temporal Graph (`graph.sqlite`)**: Records architectural decisions, entity relations, and checkpoints with valid-time and transaction-time tracking.
- **Hybrid Retrieval (`vector.sqlite` & BM25 FTS5)**: Combines dense vector similarity with sparse BM25 keyword matching via Reciprocal Rank Fusion (RRF).
- **Project Registry (`registry.sqlite`)**: Manages workspace indexing, cross-project knowledge handoffs, and session checkpoints.
- **Engine Invariants**: All databases run in SQLite `WAL` mode with path-traversal guards and automatic checkpointing.

### 3. `context_health` (`antigravity/mcp_servers/context_health`)
NeurIPS DL4Code-inspired context optimization and token economy service (26 pytest tests passing).
- **Deterministic Observation Masking**: Collapses long compiler/test outputs into actionable summaries, retaining only stack traces, failure lines, and exit codes.
- **Repeat-Read Budgeting**: Tracks file read frequencies and prevents context degradation caused by repeated full-file inspections.
- **AST Skeletonizing**: Produces compressed outline views of large files, exposing structure without source body bloat.

### 4. `context7` (External Upstash MCP)
- Provides real-time external library documentation lookup (`resolve-library-id`, `query-docs`) directly from authoritative package sources, preventing hallucinated API signatures.

### 5. `browseros-neo` (Dedicated Agent Browser)
- Dedicated browser session integration over MCP (`http://127.0.0.1:9010/mcp`) providing interactive DOM manipulation, live authentication persistence, tab grouping, screenshot capture, and PDF generation.

### 6. `open-design` & `StitchMCP` (Design System & Canvas MCPs)
- `open-design`: Full-stack UI/UX canvas integration for artifacts, design briefs, and agent collaboration.
- `StitchMCP`: Design system generator and screen modifier creating consistent, accessible design tokens and UI variants.

---

## Section 6: 3-Tier Adaptive Routing & 11-Stage Gemini Routing Matrix

Execution is governed by strict complexity routing and specialized role isolation to prevent context pollution and toe-stepping:

```text
                              ╭──────────────╮
                              │ User Request │
                              ╰──────────────╯
                                      │
                                      ▼
                      ╭──────────────────────────────╮
                      │ Stage 1: Intake & SOT Gro... │
                      ╰──────────────────────────────╯
                                      │
                                      ▼
                      ╭──────────────────────────────╮
                      │ ◇ Complexity Classificati... │
                      ╰──────────────────────────────╯
                                      │ ["<= 3 files, 1 domain"]
                                      ▼
   ╭───────────────────────╮
   │ Path 1: Quick Rout... │
   ╰───────────────────────╯
      │
      ▼
   ╭───────────────────────╮
   │ Path 2: Normal Rou... │
   ╰───────────────────────╯
      │
      ▼
   ╭───────────────────────╮
   │ Path 3: Long-Horiz... │
   ╰───────────────────────╯
      │
      ▼
   ╭───────────────────────╮
   │ Deep Architecture ... │
   ╰───────────────────────╯
      │
      ▼
   ╭───────────────────────╮
   │ Stage 2: Enrichmen... │
   ╰───────────────────────╯
      │
      ▼
   ╭────────────────────╮
   │ Inline Story Shard │
   ╰────────────────────╯
      │
      ▼
    ╭──────────────────────────────╮    ╭──────────────────────────────╮
    │ Single Builder Fix (dev-b... │    │ Stage 3: Clarification (pro) │
    ╰──────────────────────────────╯    ╰──────────────────────────────╯
                    │                                   │
                    ▼                                   ▼
   ╭───────────────────────╮
   │ Fast Verification ... │
   ╰───────────────────────╯
      │
      ▼
   ╭───────────────────────╮
   │ Stage 8: Independe... │
   ╰───────────────────────╯
      │
      ▼
   ╭───────────────────────╮
   │ Stage 4: PM Contra... │
   ╰───────────────────────╯
      │
      ▼
                      ╭──────────────────────────────╮
                      │ Stage 5-6: Disjoint Speci... │
                      ╰──────────────────────────────╯
                                      │
                                      ▼
                      ╭──────────────────────────────╮
                      │ Stage 7: Two-Stage QC (fr... │
                      ╰──────────────────────────────╯
```

### 11-Stage Gemini Model Routing Matrix

Every subagent invocation (`invoke_subagent`) and CLI delegation is restricted to Gemini models based on the cognitive requirements of the stage:

| Stage | Name | Role Persona | Native Type | Model Tier | CLI Model Target |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage 1** | Feedback Intake | Root / Orchestrator | `self` | `inherit` (`pro` via `force_ask`) | `gemini-4-argon-medium` (`gemini-4-argon-high` via `force_ask`) |
| **Stage 2** | Context Enrichment | `research-explorer` | `research` | `flash` | `gemini-3.8-flash-high` |
| **Stage 3** | Clarification & Scope | `pm` | `self` | `inherit` (`pro` via `force_ask`) | `gemini-4-argon-medium` (`gemini-4-argon-high` via `force_ask`) |
| **Stage 4** | PM Contract & Shards | `pm` | `self` | `inherit` (`pro` via `force_ask`) | `gemini-4-argon-medium` (`gemini-4-argon-high` via `force_ask`) |
| **Stage 5a** | Read-Only Explorers | `backend-explorer`, `frontend-explorer` | `research` | `flash` | `gemini-3.8-flash-high` |
| **Stage 5b** | Builders, Designers & Assets | `dev-fe`, `dev-be`, `designer`, `image-generator` | `self` / `image-generator` | `inherit` (`pro` via `force_ask`) / `image-generator` | `gemini-4-argon-medium` (`gemini-4-argon-high` via `force_ask`) / `gemini-4-argon-low` (`image-generator`) |
| **Stage 5c** | Deep Arch & Root-Cause | `sa`, `senior-architect`, `debugger` | `self` | `inherit` (`pro` via `force_ask`) | `gemini-4-argon-medium` (`gemini-4-argon-high` via `force_ask`) |
| **Stage 5d** | Docs & Telemetry | `doc-sync-worker`, `librarian`, `diff-helper` | `research` | `flash` / `flash_lite` | `gemini-3.8-flash-medium` / `gemini-3.8-flash-low` |
| **Stage 6** | Implementation | `dev-fe`, `dev-be`, `meta-evolution` | `self` | `inherit` (`pro` via `force_ask`) | `gemini-4-argon-medium` (`gemini-4-argon-high` via `force_ask`) |
| **Stage 7** | Two-Stage QC | `frontend-qc` (UI), `test-runner` (CLI) | `self` / `research` | `inherit` (`pro` via `force_ask`) / `flash` | `gemini-4-argon-medium` (`gemini-4-argon-high` via `force_ask`, `frontend-qc`) / `gemini-3.8-flash-high` (`test-runner`) |
| **Stage 8** | Independent Audit | `oracle-review`, `hallucination-auditor` | `self` | `inherit` (`pro` via `force_ask`) | `gemini-4-argon-medium` (`gemini-4-argon-high` via `force_ask`) |

---

## Section 7: Step-by-Step Instructions for an LLM Agent to Replicate or Audit This Harness

When tasked with setting up or repairing this environment in a new container, VM, or host, follow this exact sequence:

### Step 1: Pre-Flight Environment Inspection
Verify the presence of required system dependencies:
```bash
python3 --version     # Must be >= 3.11
which uv || which pip # uv is strongly recommended
which rg              # ripgrep must be available
which fd              # fd-find must be available
which rsync           # required for installer sync
```

### Step 2: Deploy Harness Files
Execute the automated installer from the repository root:
```bash
bash /home/heocop/Projects/antigravity_settings/scripts/install-harness.sh
```
*Note*: The installer automatically performs a timestamped backup of any pre-existing `~/.gemini/` configuration, syncs `config/`, `antigravity/`, and `antigravity-cli/`, establishes the `~/.gemini/GEMINI.md` symlink, creates Python virtual environments for all three local MCP servers, and triggers the verification suite.

### Step 3: Run the Verification Gate
Confirm that all 6 verification gates succeed:
```bash
bash /home/heocop/Projects/antigravity_settings/scripts/verify-harness.sh
```
If any gate reports `[FAIL]`:
- **Hook Test Failure**: Inspect `config/hooks/tests/test_*.py` output. Ensure no syntax regressions or unquoted regex patterns were introduced.
- **MCP Test Failure**: Check `.venv/bin/pytest` in the respective server directory. Reinstall dependencies with `uv pip install -e . pytest anyio`.
- **JSON/YAML Failure**: Locate the malformed file in the validator output and repair invalid syntax or trailing commas in pure JSON files.
- **Housekeeping Failure**: Run `bash antigravity/scripts/housekeeping.sh --dry-run` and inspect permission issues or missing SQLite databases.
- **Harness Tree Failure**: Run `python3 antigravity/scripts/validate-harness-tree.py` and inspect byte budget limits, unescaped template braces, or missing skill references.

### Step 4: Validate Active Configuration
Ensure `~/.gemini/config/hooks.json` points to the deployed hooks and `~/.gemini/config/mcp_config.json` correctly references Python virtualenvs in `~/.gemini/antigravity/mcp_servers/`.

### Step 5: Execute Housekeeping Check
Run the inter-session housekeeping sweeper:
```bash
bash ~/.gemini/antigravity/scripts/housekeeping.sh --dry-run
```
Ensure zero unexpected file deletions or database lock errors occur.

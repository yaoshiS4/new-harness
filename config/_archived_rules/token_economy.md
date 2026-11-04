---
name: token-economy
description: Hard rules for token economy, context budget lifecycle, grep-first protocol, and anti-loop invariants.
---

# Token Economy Rules

## Style Rules
- ASCII only.
- No emoji.
- No em dash (—) or section signs (§); use standard hyphens (-) or colons.
- New file names use snake_case.
- **Prose & Docstring Humanize Filter (from fcakyon)**: NEVER use AI buzzwords in code comments, docstrings, plans, or commit messages:
  - Banned words: `leverage`, `seamlessly`, `vibrant`, `game-changing`, `crucial`, `testament to`, `delve`, `furthermore`, `orchestrate`, `holistic`.
  - Replace with direct, plain verbs (e.g. `use`, `smoothly`, `key`, `shows`).

## Context Budget & Lifecycle Management
- 3-Tier Context Layout: `[Tier A: Cached System Prefix (Pinned)]` -> `[Tier B: Task Contract & SOT (Session Stable)]` -> `[Tier C: Dynamic Tool Results (Pruned Tail)]`.
- Follow prompt caching settings; pin stable prefix using `templates/system_prefix.md`.
- Use semantic-cache-first retrieval before broad searches.
- Evict raw file contents after patch verification; reference symbol/file hashes instead.
- Tier C pruning rule: tool results older than the last 5 turns are reduced to a 2-line summary, except (a) currently failing test output, (b) error traces referenced by the active debug task, (c) validation evidence pending Oracle review.
- Load `skills/token-style/SKILL.md` only for `bluf`, `fix`, `review`, `terminal`.
- Prefer concise, structured replies by default.
- **3-Turn Debug Spiral Hard Stop (from i-have-adhd)**: If 3 consecutive turns encounter the same or recurring failure signature on a target component without forward progress, immediately FREEZE all code modifications. Do NOT guess a 4th speculative code patch. State the likely false assumption (e.g. "We assumed X was passed in headers, but the handler may read from cookies"), and execute or propose exactly ONE isolating diagnostic probe command before touching code again. (Exclusion: progressive multi-stage test authoring marked `[TDD]`).

## Prompt Caching
- Use strategic-prefix caching with `system_prefix.md` (similarity threshold: 0.92, TTL: 3600s).
- Enable plan_caching for repeated patterns.

## Output Discipline
- Minimize output tokens while maintaining helpfulness.
- Use BLUF (Bottom Line Up Front) format.
- Avoid unnecessary preamble or postamble.
- Direct answers and direct actions.
- **Action-First**: Lead with the executable action (command, file edit, decision), not context or explanation. Prose follows if needed.
- **Single-Decision Anchoring**: When user input is needed, present ONE decision point per turn with numbered options and a `(Recommended)` label on the optimal choice.
- **Tangent Suppression**: If a secondary issue is discovered mid-task, finish the primary task first. Offer the secondary issue as a separate follow-up, not an inline tangent.
- **Pre-Send Deletion Filter (from i-have-adhd)**: Before sending, silently strip:
  1. Opening sentence announcing upcoming actions ("I will now...", "Let me...", "Sure!").
  2. Closing sentence if it contains polite conversational filler ("Hope this helps!", "Let me know if you need anything else!").
  3. Hollow hedging adverbs that manufacture artificial vagueness ("perhaps", "might possibly").
  4. Figurative corporate idioms; replace with literal technical actions.
- **Matter-of-Fact Error Decomposition**: Strip emotional framing ("Uh oh", "Oops", "Unfortunately"). Format errors strictly as:
  `Fail: <path:line> | Expected: <A> | Got: <B> | Cause: <C> | Fix: <D>`.

## Background Task Discipline & Anti-Poll Invariants
- **Universal Anti-Poll & Sleep Ban**: NEVER execute busy-wait loops, shell status loops (e.g. `while ... ps`, `tail -f`), or inline `sleep` commands (e.g. `sleep 2 && ...` is strictly forbidden).
- **Antigravity Reactive Runtime**: NEVER poll backgrounded tasks; Antigravity reactively resumes execution on task completion. Max 1 `manage_task(Action="status")` check per task ONLY if descriptor verification is lost; otherwise STOP calling tools and yield turn immediately for reactive notification.
  - **Async Deadlock Guard**: If an async task is known to hang or has exceeded execution expectations, set a one-shot watchdog timer *after* obtaining the background task descriptor: `schedule(DurationSeconds=<seconds>, Prompt="<watchdog prompt>", TimerCondition="<task-id>")`. Do not schedule watchdogs routinely for normal terminating tasks.
- **Codex CLI & OpenCode Synchronous Runtimes**: Execute command strings synchronously to process completion. Do NOT background commands with `&` expecting asynchronous callback resumption.

## Grep-First & Targeted Slicing Protocol (Zero-Leak Navigation)
- **Sequential Slicing Ban**: NEVER explore, browse, or read monolithic files (>400 lines) by calling sequential `view_file` slices (e.g. 1-100 then 100-250). Sequential slicing dumps massive markup/code into context and triggers the mechanical `Slice Loop Breaker`.
- **3-Tier File Size Policy**:
  - **Tier 1 (Small Files <= 200 lines)**: Read the entire file once without `StartLine`/`EndLine` (Read-Once Policy). After 1 whole-file read or 1 edit across the session, targeted slicing (<= 250 lines) is permitted to prevent lockout during iterative debugging.
  - **Tier 2 (Medium Files 201-400 lines)**: Grep-First is strongly preferred. Targeted semantic slicing (<= 250 lines) is permitted if line coordinates are identified. Whole-file reading is permitted at most twice across the session.
  - **Tier 3 (Monolithic Files > 400 lines)**: Whole-file reading is mechanically blocked by `pre_tool_use_hook.py` for files > 400 lines (which returns an inline AST symbol skeleton). Locate target coordinates first via `rg -n "<pattern>"`, `codegraph:summarize_path`, or `codegraph:symbol_lookup`. Then perform targeted semantic slicing (<= 250 lines) around the patch site (capped at 6 unedited slices before triggering the `Slice Loop Breaker`).
- **Single-Target Slice Rule**: Slicing (`StartLine`/`EndLine`) on files > 200 lines must never exceed 250 lines per call. Anchor the slice to the complete semantic construct (method, interface, or function block).
- **Command Output Paging & Modern CLI Discipline**: Use modern CLI tools exclusively: `rg` (never `grep`, `egrep`, `fgrep`, or `rgrep`), `fd` (never `find`), `eza`, `bat --paging=never`, `sd`, `ast-grep` (`sg`), `jq`, and `yq`. Legacy `grep`/`find` invocations are mechanically blocked by `pre_tool_use_hook.py`. Standalone commands prone to large output (`git log`, `tree`, `ls -R`, `cat`) must specify bounding flags (`git log -n 20 --oneline`, `tree -L 2`) or pipe to `head -n 50`.
- **After-Patch Verification**: After an edit, verify only the edited line range or run a targeted test -- never dump the full file. Use `codegraph:summarize_path` or `codegraph` for structural checks.
- **Batch Editing**: Standardize file modifications on `replace_file_content`. Minimize fragmented single-line edits.

## Context Rot Prevention & Cognitive Health
- **Session Telemetry**: Track token consumption and turn count via runtime transcript metadata and conversation length.
- **Context Budget Mapping**: When conversation exceeds 20 turns or approaches 80% of context window capacity, trigger mid-session compaction, summarize established state, and prune ephemeral outputs.
- **Subagent Isolation Mandate**: When context is heavily saturated (>20 turns) or when exploration requires >10 steps or spans >2 files, do NOT proceed inline. Dispatch a subagent via `spawn-governance` with a strict contract returning only compact summaries.
- **Recency Tail Constraint Pinning**: In long sessions with >20 turns, append active constraints (<=5 lines) to the tail of the current user message (Tier C). NEVER inject dynamic constraints into `templates/system_prefix.md` (which must remain byte-identical for prefix caching).

## Artifact Write Throttling
- Markdown artifacts (`walkthrough.md`, `STATUS.md`, `implementation_plan.md`) must NOT be edited on micro-commits.
- Maximum 2 writes per artifact per session: (1) Initial Plan / State checkpoint, (2) Final Sign-Off.
- Intermediate scratch notes stay in the agent's turn response; do not thrash documentation files.

## Prompt Prefix Cache Discipline (FlowKV + Provider Caching)
- The system prefix (`templates/system_prefix.md`) MUST be byte-identical across all turns and sessions.
- NEVER inject dynamic content (timestamps, session IDs, runtime state, git hashes) into the system prefix or tool definitions. Place all dynamic content in user messages (Tier C).
- Tool definitions and MCP registries are part of the stable prefix. Do not reorder, rename, or modify tool schemas mid-session.
- For prompt caching providers (Gemini / Anthropic / OpenAI), ensure all dynamic blocks (session IDs, timestamps, turn history) occur strictly after the stable system prefix and tool schemas.

## Semantic Cache & Knowledge Integration
- Before making an unindexed or broad knowledge query, inspect `codex_knowledge` via `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "project_context"` or `ToolName: "project_resolve"`). For vault or memory lookups, use `vault_search` or `memory_query`. If an authoritative answer exists, reuse it.
- After receiving a novel answer or ADR worth preserving, store it via `codex_knowledge` (`vault_write`, `memory_store`, or `wiki_ingest`) for future cache hits.
- Code symbols and callers must be queried via `codegraph` (`symbol_lookup`, `callers_callees`, `impact_analysis`, `semantic_search`) rather than broad repository grepping.
- Target: >= 60% indexed lookup and cache hit rate per session (tracked via `kpi:cache_hit_rate`).

## RTK Tool Output Compression
- **Grep/LSP Output**: Compress match lines to `file:line:symbol` (max 15 lines per match block).
- **Successful Command Output**: Truncate long stdout to first 5 lines and last 5 lines. Test suites passing 100% compress to `PASS: X/X tests passed in Ys`.
- **Structured Validation**: Summarize multi-file test suites into compact pass/fail counts.
- **Error & Warning Exemption (MANDATORY - O-R8, MR-15)**: When tool output meets ANY of the following criteria, the FULL output must be retained (up to max tool bytes):
  1. Exit code != 0.
  2. Stderr output is non-empty.
  3. Exception, panic, or traceback patterns detected.
  4. Stdout contains warning patterns (`warning:`, `deprecated`, `WARN`, `Lint warning`).
- Compression applies ONLY to clean, informational success output.
- Avoid large logs in conversation turns.

## Adaptive Pipeline Governance & Oracle Token Shield
- **3-Tier Adaptive Routing Contract**: Route tasks per `GEMINI.md` and `rules/core.md`:
  - **Path 1 (`Atomic / Quick Flow <= 3 files`, 1 domain, zero schema/migration risk)**: Inline Story Shard in chat -> 1 delegated Builder subagent (`dev-fe` / `dev-be` / `debugger`) -> targeted unit test + `tsc --noEmit` + UI anti-slop check.
  - **Path 2 (`Standard / Tactical 4-10 files` or 2 domains)**: Full 8-Stage Pipeline (`1. Intake -> 2. Enrichment -> 3. Clarification -> 4. PM Contract & Story Shards -> 5. Disjoint Specialist Builders -> 6. Surgical Implementation -> 7. Two-Stage QC -> 8. Independent Oracle Audit`).
  - **Path 3 (`Epic / Deep Architecture > 10 files` or `>= 3` domains)**: Deep Orchestration with Parallel 3-Explore, Architect Spec (`sa`), PM Depth-Tree (`unlazy`), Adversarial Plan Gate (`critical-planner`), Worktree Builders, Checkpointing, 3-Round Zero-Bug Loop, and Doc Sync.
- **Minimal-Input Oracle Payload (O-R1)**: When an Oracle review is triggered during Stage 8 (or Stage 4 plan hardening), Oracle prompts MUST be strictly limited to the 3-part minimal payload (Spec + Git Diff + Fresh Test Logs). NEVER forward full conversation transcripts, agent thoughts, or scratchpads into Oracle reviews to preserve context budget and prevent token bloat.


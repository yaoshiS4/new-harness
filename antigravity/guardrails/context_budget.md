# Context Budget Guardrails

## Mechanical Tool Bounds (pre_tool_use_hook.py)
- **File Read Bounds (`view_file` / `read_file`)**: Read files `<= 200` lines whole first. For files `> 400` lines, run AST/symbol outline first (`codegraph` or `rg`) and read targeted slices `<= 250` lines (max 6 slices/file).
- **Search Flood Bounds (`rg` / `fd`)**: Always bound search commands — `rg` with `-m 50` or `| head`, `fd` with `--max-results 50` or `--max-depth` (note: `-e` alone is NOT an output bound).
- **External Documentation (`context7`)**: For external library/SDK documentation, query `context7` (`resolve-library-id` -> `query-docs`) via `call_mcp_tool` before `search_web`.

## Token Efficiency
- Follow `../AGENTS.md` and `../skills/sot-context/SKILL.md` for cache discipline, compact outputs, and semantic-cache-first retrieval
- Keep compact response modes explicit-only
- Follow `../skills/adhd-mode/SKILL.md` for action-first, zero-fluff responses
- Prefer concise, structured replies by default

## Retrieval Strategy
- Use semantic-cache-first retrieval before broad searches
- Use curated context, indexes, and task-specific retrieval before broad scanning
- Use `call_mcp_tool` with `codex_knowledge` for local project context before broad repo or vault scanning

## Output Discipline
- Minimize output tokens while maintaining helpfulness
- Use BLUF (Bottom Line Up Front) format
- Avoid unnecessary preamble or postamble
- One-word answers are best when appropriate

## Cognitive Health & Context Pressure
- Session Telemetry: Track conversation length and token budget; trigger compaction when active token percentage reaches $\ge 65\%$ or turns since compaction reaches $\ge 25$.
- Observation Buffer Distillation & Spillover: Use `call_mcp_tool` on `context_health` (`distill_observation_buffer`, `compact_observations`, and `spillover_large_payload`) to compress verbose tool outputs and offload large payloads (>8KB) to disk artifacts before context rot degrades reasoning.
- High Context Pressure: Mandates immediate stop, state checkpointing via `task.md` or `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "handoff_checkpoint"`), and subagent isolation via `../skills/spawn-governance/SKILL.md`.
- Repeat-Read Enforcement: Mechanical pre-tool-use hook strictly enforces 3-strike limits on un-sliced file reads and identical tool repetitions.



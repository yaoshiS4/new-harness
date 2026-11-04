---
name: document-sync
description: Sync approved changes to documentation, indexes, and the local Obsidian vault. Run after every Oracle-approved implementation.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# Document Sync

## Purpose
Keep project documentation, knowledge graph relationships, skillbank indexes, and the local Obsidian vault synchronized with Oracle-approved code changes.

> [!IMPORTANT]
> **Role & One-Shot MCP Discipline**:
> - Always use `subagent_type: "doc-sync-worker"` or `subagent_type: "librarian"` (`model: sonnet`) when delegating documentation discovery/audit; both agents may edit documentation files only. Never use legacy underscore role names (`doc_sync_worker` / `doc_updater`).
> - Execute pre-flight context retrieval in a single turn via `codex_knowledge:batch_knowledge_query` rather than chaining multiple sequential MCP read calls.

---

## Steps

### 1. Post-Edit AST & Symbol Diff Discovery (`Graphify-Labs/graphify` Protocol)
1. **Extract Changed AST Symbols**:
   Run `codegraph:changed_symbols` on the approved git diff so documentation updates target exact modified functions, classes, and schemas:
   ```json
   {
     "ServerName": "codegraph",
     "ToolName": "changed_symbols",
     "Arguments": {
       "diff_text": "<git_diff_content>"
     }
   }
   ```
2. **One-Shot Knowledge Pre-Flight (`codex_knowledge:batch_knowledge_query`)**:
   Query existing project docs, memory entries, and graph nodes linked to the modified symbols in 1 turn:
   ```json
   {
     "ServerName": "codex_knowledge",
     "ToolName": "batch_knowledge_query",
     "Arguments": {
       "slug": "<project_slug>",
       "steps": [
         {"op": "project_context", "query": "<changed_symbol_or_feature>", "limit": 3},
         {"op": "memory_query", "query": "<changed_symbol_or_feature>", "limit": 10},
         {"op": "graph_query", "query": "<changed_symbol_or_feature>", "limit": 20}
       ],
       "output_format": "toon"
     }
   }
   ```

### 2. Post-Edit Graph & Index Synchronization (`Graphify-Labs/graphify`)
Whenever code or harness files change, synchronize both the structural index and the relational graph before closing the task:
- **Harness & Skillbank Index Sync**: If any skill (`SKILL.md`), script, or `CLAUDE.md` rule was modified, trigger mechanical tree validation and skillbank index regeneration:
  ```bash
  python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/validate-claude-tree.py --autotrigger
  ```
- **Relational Graph Upsert (`codex_knowledge:graph_upsert`)**: Update bi-temporal entity edges (`DEPENDS_ON`, `IMPORTS`, `EXPORTS`, `CONTAINS`, `DECIDED_BY`) for newly added or refactored symbols.
- **Wiki & Memory Sync**: Rebuild the wiki index via `mcp__codex_knowledge__wiki_ingest()` and store durable architectural facts via `mcp__codex_knowledge__memory_store()`.

### 3. Update Vault Documents & SOT Files
- Update affected project SOT docs (`docs/STATUS.md`, `docs/README.md`, `AGENTS.md`) and vault documents (`codex_knowledge:vault_write`) to reflect the new AST signatures and behavior.
- Preserve traceability links (`[symbol](file:///abs/path#L10-L20)` $\rightarrow$ doc section).

### 4. Delegate via `doc-sync-worker` | `librarian`
- For read-only doc drift detection or summary compilation, invoke `Agent(subagent_type="doc-sync-worker" | "librarian", model="sonnet")`.
- Push validated summaries to the local Obsidian vault via `codex_knowledge` (`vault_write` / `wiki_ingest`) — never sync unverified drafts or raw conversation transcripts.

### 5. Capture Lessons
- Use `mcp__codex_knowledge__knowledge_capture()` to record what was synced.
- Use `mcp__codex_knowledge__orchestration_lesson()` if the sync uncovered stale documentation or missing citation anchors.

## Guardrails
- Only sync after independent verification / `oracle-review` approval.
- Never pull in unrelated skill bundles or touch unleased files.
- Keep summaries compact, citation-anchored, and traceable.

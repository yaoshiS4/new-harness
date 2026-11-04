---
name: document-sync
description: Sync approved changes to documentation, indexes, and the local Obsidian vault. Run after every Oracle-approved implementation.
---

# Document Sync

## Purpose
Keep project documentation, knowledge graph relationships, skillbank indexes, and the local Obsidian vault synchronized with Oracle-approved code changes.

> [!IMPORTANT]
> **Role & One-Shot MCP Discipline**:
> - Always use `Role: "doc-sync-worker"` or `Role: "librarian"` (`TypeName: "research"`, `Model: "flash"`) when delegating documentation discovery/audit, or `TypeName: "self"` when writing doc updates. Never use legacy underscore role names (`doc_sync_worker` / `doc_updater`).
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
- **Harness & Skillbank Index Sync**: If any skill (`SKILL.md`), script, or `GEMINI.md` rule was modified, trigger mechanical tree validation and skillbank index regeneration:
  ```bash
  python3 ~/.gemini/antigravity/scripts/validate-harness-tree.py --autotrigger
  ```
- **Relational Graph Upsert (`codex_knowledge:graph_upsert`)**: Update bi-temporal entity edges (`DEPENDS_ON`, `IMPORTS`, `EXPORTS`, `CONTAINS`, `DECIDED_BY`) for newly added or refactored symbols.
- **Wiki & Memory Sync**: Rebuild the wiki index via `call_mcp_tool(ServerName="codex_knowledge", ToolName="wiki_ingest")` and store durable architectural facts via `call_mcp_tool(ServerName="codex_knowledge", ToolName="memory_store")`.

### 3. Update Vault Documents & SOT Files
- Update affected project SOT docs (`docs/STATUS.md`, `docs/README.md`, `AGENTS.md`) and vault documents (`codex_knowledge:vault_write`) to reflect the new AST signatures and behavior.
- Preserve traceability links (`[symbol](file:///abs/path#L10-L20)` $\rightarrow$ doc section).

### 4. Delegate via `doc-sync-worker` | `librarian`
- For read-only doc drift detection or summary compilation, invoke `invoke_subagent(TypeName="research", Role="doc-sync-worker" | "librarian", Model="flash")`.
- Push validated summaries to the local Obsidian vault via `codex_knowledge` (`vault_write` / `wiki_ingest`) — never sync unverified drafts or raw conversation transcripts.

### 5. Capture Lessons
- Use `call_mcp_tool(ServerName="codex_knowledge", ToolName="knowledge_capture")` to record what was synced.
- Use `call_mcp_tool(ServerName="codex_knowledge", ToolName="orchestration_lesson")` if the sync uncovered stale documentation or missing citation anchors.

## Guardrails
- Only sync after independent verification / `oracle-review` approval.
- Never pull in unrelated skill bundles or touch unleased files.
- Keep summaries compact, citation-anchored, and traceable.

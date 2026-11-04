---
name: sot-context
description: Load project state from curated source of truth docs. Prefer indexed retrieval over broad scanning.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# SOT Context

## Purpose
Load project context efficiently from curated source of truth documents, avoiding broad file scanning. Backed by `codex_knowledge` layered context indexing, bi-temporal graph memory, and hybrid FTS5 + Chroma Vector RRF search.

> [!IMPORTANT]
> **One-Shot MCP Execution (No 2-Turn Schema Inspection Tax)**:
> Always invoke directly using MCP tools (`mcp__<server>__<tool>`) with `ServerName: "codex_knowledge"`. Never inspect `.json` schemas before calling. Never use hallucinated legacy function names (`codex_knowledge_*`).
> The canonical project identifier parameter is `slug` (e.g., `"lich-viet-lich-only"`, `"codex_agents"`), with dual-alias `project` also fully supported. Dual aliases are also supported for `term`/`query` (`graph_query`), `entity_id`/`entity` (`graph_neighbors`), and `key`/`title` / `value`/`content` (`memory_store`).

---

## One-Shot MCP tools (`mcp__<server>__<tool>`) Invocations

### 1. Read Project Index (`project_index`)
Retrieve project overview and catalog of available curated documents:
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "project_index",
  "Arguments": {
    "slug": "<project_slug>"
  }
}
```

### 2. Retrieve Layered Context (`project_context`)
Retrieve multi-perspective context bundle (wiki, memory, graph) with grounded citation anchors and **OpenViking L0/L1/L2 Progressive Context Disclosure**:
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "project_context",
  "Arguments": {
    "slug": "<project_slug>",
    "query": "<task_or_feature_topic>",
    "limit": 3,
    "tier": "L1"
  }
}
```

#### OpenViking L0/L1/L2 Progressive Context Loading Protocol (`volcengine/OpenViking`)
Organize context retrieval across three explicit disclosure tiers (`tier: "L0" | "L1" | "L2"`) to cut input token consumption by 34–91% while preserving full fidelity when needed:
1. **`tier: "L0"` (Abstract — Instant Relevance Filter, `<= 240` chars/doc)**:
   - Returns a 1-sentence summary + top document headings (`#` / `##`).
   - Use during broad candidate triage or multi-topic sweeps to verify relevance before loading overview or body text.
2. **`tier: "L1"` (Overview — Planning & Architecture, `<= 1200` chars/doc)**:
   - Returns document headings, key bullet points, and core API/type signatures.
   - Use during intake, Story Shard planning, and dependency mapping.
3. **`tier: "L2"` (Details — Full Retrieved Context, default)**:
   - Returns the full retrieved context bundle plus additive `context_tier: "L2"` metadata.
   - Use when executing surgical implementation or verifying exact specification clauses, and follow up with `vault_read` only on anchored hits.

### 3. Read Curated Source Docs (`vault_read` & `vault_search`)
Read only the specific files cited in `project_context` hits instead of entire directory trees:
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "vault_read",
  "Arguments": {
    "slug": "<project_slug>",
    "relative_path": "docs/PRD.md"
  }
}
```
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "vault_search",
  "Arguments": {
    "slug": "<project_slug>",
    "query": "<topic_query>",
    "limit": 20
  }
}
```

### 4. Supplement with Memory & Graph (`memory_query` & `graph_query`)
Search architectural decisions, lessons, and durable invariants via hybrid FTS5 (BM25) + Chroma Vector RRF:
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "memory_query",
  "Arguments": {
    "slug": "<project_slug>",
    "query": "<symbol_or_decision_topic>",
    "limit": 20
  }
}
```

Traverse entity relationships and dependencies using PPR-ranked graph search:
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "graph_query",
  "Arguments": {
    "slug": "<project_slug>",
    "term": "<entity_or_concept>",
    "limit": 50
  }
}
```

Inspect 1-hop and 2-hop entity neighborhood:
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "graph_neighbors",
  "Arguments": {
    "slug": "<project_slug>",
    "entity_id": "<entity_name>",
    "limit": 10
  }
}
```

### 5. Durable Memory Store (`memory_store`)
Persist durable project facts, lessons learned, and semantic cache entries:
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "memory_store",
  "Arguments": {
    "slug": "<project_slug>",
    "key": "<unique_key_or_semantic_cache_id>",
    "value": "<concept_or_decision_markdown>"
  }
}
```

### 6. Persist Graph Relations (`graph_upsert`)
Record bi-temporal relationships between codebase entities, decisions, and modules:
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "graph_upsert",
  "Arguments": {
    "slug": "<project_slug>",
    "src": "<source_entity>",
    "rel": "DEPENDS_ON",
    "dst": "<target_entity>",
    "payload": "<rationale_or_evidence_markdown>"
  }
}
```
*Canonical Edge Types*: `DEPENDS_ON`, `IMPORTS`, `EXPORTS`, `CONTAINS`, `HAS_TECH_STACK`, `IS_ENGINE`, `IS_COMPONENT`, `IS_SERVICE`, `DECIDED_BY`.

### 7. Handoff Checkpoints (`handoff_checkpoint` & `handoff_read`)
Persist execution state across subagents and session phases:
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "handoff_checkpoint",
  "Arguments": {
    "slug": "<project_slug>",
    "name": "<task_id_or_phase_milestone>",
    "payload": "<folded_events_and_intent_json>"
  }
}
```
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "handoff_read",
  "Arguments": {
    "slug": "<project_slug>",
    "name": "<handoff_name>"
  }
}
```

### 8. Batch Knowledge Query (`batch_knowledge_query`)
Execute multi-perspective read operations in Python RAM in a single turn without 3-turn conversational ping-pong:
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "batch_knowledge_query",
  "Arguments": {
    "slug": "<project_slug>",
    "steps": [
      {"op": "project_context", "query": "<topic>", "limit": 3},
      {"op": "memory_query", "query": "<topic>", "limit": 10},
      {"op": "graph_query", "query": "<topic>", "limit": 10}
    ],
    "output_format": "toon"
  }
}
```

### 9. Code Mode Knowledge Bundle (`ag-mcp.py`)
Run programmatic 1-shot knowledge retrieval via CLI:
```bash
python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/ag-mcp.py knowledge bundle --slug <slug> --query <query>
```

---

## Efficiency Rules
- **Layered Context First**: Always invoke `project_context` before opening project files.
- **Inspect Citation Anchors**: Inspect `citation_status` on `top_hits` (`anchored` means the file physically exists on disk).
- **Hybrid Memory Search**: Query `memory_query` instead of scrolling or re-reading conversation transcripts.
- **Surgical Vault Reads**: Use `vault_read` exclusively for files identified through `project_context` or `vault_search`.
- **Zero Raw File Dumps**: Do not read full documentation trees when targeted SOT queries answer the question.
- **Deduplicate Before Storing**: Check `memory_query` before adding duplicate concept or decision records.

# Codex Knowledge MCP Server Instructions

## Overview
Authoritative project knowledge service providing bi-temporal graph memory with Python Personalized PageRank (PPR), zero-overhead hybrid SQLite FTS5 BM25 + Token Cosine similarity (`VectorMemory`), repository SOT document indexing, and zero-loss handoff checkpoints.

> [!IMPORTANT]
> **One-Shot MCP Execution (No 2-Turn Schema Inspection Tax)**:
> Always invoke directly using `call_mcp_tool` with `ServerName: "codex_knowledge"`. Never inspect `.json` schemas before calling. Never use hallucinated legacy function names (`codex_knowledge_*`).
> The canonical project identifier parameter is `slug` (e.g., `"lich-viet-lich-only"`, `"codex_agents"`), with dual-alias `project` also fully supported. Dual aliases are also supported for `term`/`query` (`graph_query`), `entity_id`/`entity` (`graph_neighbors`), and `key`/`title` / `value`/`content` (`memory_store`).

---

## 8 Streamlined Core Tools (`call_mcp_tool`)

### 1. `project_context`
Retrieve high-density layered context across wiki, memory, and graph stores in a single shot.
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "project_context",
  "Arguments": {
    "slug": "<project_slug>",
    "query": "<task_or_feature_topic>",
    "limit": 3
  }
}
```

### 2. `project_index`
Retrieve the full document inventory, repository SOT catalog, and recent checkpoints/handoffs.
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "project_index",
  "Arguments": {
    "slug": "<project_slug>"
  }
}
```

### 3. `memory_query`
Hybrid FTS5 (BM25) + Token Cosine RRF search for architectural decisions, lessons, and durable facts.
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "memory_query",
  "Arguments": {
    "slug": "<project_slug>",
    "query": "<semantic_or_symbol_query>",
    "limit": 20
  }
}
```

### 4. `memory_store`
Store a durable key-value memory item or semantic cache entry (<1ms latency).
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "memory_store",
  "Arguments": {
    "slug": "<project_slug>",
    "key": "<unique_key>",
    "value": "<durable_fact_or_decision>"
  }
}
```

### 5. `graph_upsert`
Persist a bi-temporal knowledge graph relationship between entities (`graph.sqlite`, 0.4ms).
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "graph_upsert",
  "Arguments": {
    "slug": "<project_slug>",
    "src": "<source_entity>",
    "rel": "EXPORTS|IMPORTS|DEPENDS_ON|CONTAINS|DECIDED_BY|HAS_TECH_STACK",
    "dst": "<target_entity>",
    "payload": "<rationale_or_evidence_markdown>"
  }
}
```

### 6. `graph_query`
PPR-ranked search over knowledge graph entities and relationship triples.
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "graph_query",
  "Arguments": {
    "slug": "<project_slug>",
    "term": "<search_term>",
    "limit": 50
  }
}
```

### 7. `graph_neighbors`
1-hop and 2-hop neighborhood traversal for an entity with strict token budget enforcement.
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "graph_neighbors",
  "Arguments": {
    "slug": "<project_slug>",
    "entity_id": "<entity_name_or_id>",
    "limit": 10
  }
}
```

### 8. `handoff_checkpoint`
Atomic dual persistence to both handoff and checkpoint stores for zero-loss phase resumption.
```json
{
  "ServerName": "codex_knowledge",
  "ToolName": "handoff_checkpoint",
  "Arguments": {
    "slug": "<project_slug>",
    "name": "<task_id_or_phase_name>",
    "payload": "<checkpoint_summary_json_or_markdown>"
  }
}
```

---

## Backward-Compatible Legacy Tools
The following 14 handlers remain active in `server.py` for backward compatibility, with schemas archived in `mcp/_disabled/codex_knowledge_legacy/`:
- **Document & Vault**: `vault_search`, `vault_read`, `vault_write`, `wiki_ingest`, `wiki_rebuild` (now reading/writing directly against repository SOT `docs/*.md` and `AGENTS.md`)
- **State Handoff & Checkpoints**: `handoff_read`, `handoff_write`, `checkpoint_save`, `checkpoint_restore`
- **Project Registration**: `project_register`, `project_resolve`
- **Orchestration**: `knowledge_capture`, `orchestration_lesson`, `settings_review_queue`

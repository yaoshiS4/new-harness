# CodeGraph MCP

Facade-first CodeGraph service for local agent exploration.

## Purpose

This MCP exposes stable CodeGraph operations without depending on an external pre-indexer:

- `symbol_lookup`
- `callers_callees`
- `impact_analysis`
- `semantic_search`

The implementation is intentionally lightweight and reversible. It scans local source structure, definitions, references, and test names, while existing `codex_knowledge`, `graphrag`, and `treesitter` remain available for project context, graph facts, and structural summaries.

## Contract

Agents call this facade before broad file reads during SOL Explore. If a query returns low confidence or no data, agents may fall back to targeted `rg`, `sed`, or runtime-native source reads and must report the fallback.

## Validation

Run:

```bash
uv run --project ~/.gemini/antigravity/mcp_servers/codegraph python -m codegraph.server
```

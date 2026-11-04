---
name: codegraph-explorer
description: Use CodeGraph-first exploration through the shared codegraph MCP facade before broad grep/read.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# CodeGraph Explorer

## Purpose
Use the shared `codegraph` MCP facade before broad file reads. Backed by persistent SQLite + Personalized PageRank (<15ms) for AST-indexed symbol resolution, caller/callee traversal, and blast radius impact analysis.

> [!IMPORTANT]
> **One-Shot MCP Execution (No 2-Turn Schema Inspection Tax)**:
> Always invoke directly using MCP tools (`mcp__<server>__<tool>`) with `ServerName: "codegraph"`. Never inspect `.json` schemas before calling. Never use hallucinated legacy function names (`codegraph_*`).

---

## One-Shot MCP tools (`mcp__<server>__<tool>`) Invocations

### 1. Symbol Resolution (`symbol_lookup`)
Find likely symbol definitions and references across the codebase in <15ms.
```json
{
  "ServerName": "codegraph",
  "ToolName": "symbol_lookup",
  "Arguments": {
    "root": "/path/to/project",
    "query": "<symbol_name>",
    "limit": 20
  }
}
```

### 2. Call Graph & References (`callers_callees`)
Traverse caller and callee hints when a symbol is known.
```json
{
  "ServerName": "codegraph",
  "ToolName": "callers_callees",
  "Arguments": {
    "root": "/path/to/project",
    "symbol": "<symbol_name>",
    "limit": 40
  }
}
```

### 3. Blast Radius & Test Impact (`impact_analysis`)
Estimate affected files and candidate tests from modified paths or symbols.
```json
{
  "ServerName": "codegraph",
  "ToolName": "impact_analysis",
  "Arguments": {
    "root": "/path/to/project",
    "changed_paths": ["src/path/to/file.ts"],
    "symbols": ["<symbol_name>"],
    "limit": 60
  }
}
```

### 4. Structural Lexical Search (`semantic_search`)
Structure-aware lexical retrieval as a fast graph fallback.
```json
{
  "ServerName": "codegraph",
  "ToolName": "semantic_search",
  "Arguments": {
    "root": "/path/to/project",
    "query": "<topic_or_code_pattern>",
    "limit": 20
  }
}
```

### 5. PageRank Repository Map (`repo_map`)
Compact structural outline ranked by Personalized PageRank under strict token budgets.
```json
{
  "ServerName": "codegraph",
  "ToolName": "repo_map",
  "Arguments": {
    "root": "/path/to/project",
    "max_tokens": 1500,
    "focus_files": ["src/index.ts"]
  }
}
```

### 6. AST Structure & Diff Symbols (`summarize_path` & `changed_symbols`)
Inspect AST-parsed outlines and symbol extraction from diffs served directly by `ServerName: "codegraph"`:
```json
{
  "ServerName": "codegraph",
  "ToolName": "summarize_path",
  "Arguments": {
    "path": "/path/to/file_or_dir"
  }
}
```
```json
{
  "ServerName": "codegraph",
  "ToolName": "changed_symbols",
  "Arguments": {
    "diff_text": "<git_diff_content>"
  }
}
```

### 7. Multi-Symbol AST Extraction (`extract_symbols`)
Extract exact code slices for multiple symbols in a file up to `max_total_lines` in a single turn without hitting read slice limits or circuit breakers:
```json
{
  "ServerName": "codegraph",
  "ToolName": "extract_symbols",
  "Arguments": {
    "root": "/path/to/project",
    "path": "src/services/api.py",
    "symbols": ["handle_request", "validate_payload"],
    "max_total_lines": 250
  }
}
```

### 8. Programmatic In-Memory Batch Query (`batch_query`)
Execute a sequential batch of queries in Python RAM in a single turn, piping outputs with `"from_prev": true` and emitting compact TOON output:
```json
{
  "ServerName": "codegraph",
  "ToolName": "batch_query",
  "Arguments": {
    "root": "/path/to/project",
    "steps": [
      {"op": "symbol_lookup", "query": "calculateAlmanac", "limit": 3},
      {"op": "callers_callees", "from_prev": true, "limit": 10},
      {"op": "impact_analysis", "from_prev": true, "limit": 20}
    ],
    "output_format": "toon"
  }
}
```

### 9. Code Mode for MCP Bridge (`ag-mcp.py`)
Run programmatic batch queries from CLI or scripts:
```bash
python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/ag-mcp.py codegraph batch --root . --symbol <sym>
python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/ag-mcp.py codegraph extract --root . --path <file> --symbols sym1,sym2
```

---

## Protocol
1. Use `symbol_lookup` for relevant names, routes, files, or concepts.
2. Use `callers_callees` for caller/callee hints when a symbol is known.
3. Use `impact_analysis` for affected files and candidate tests before modifying code.
4. Use `extract_symbols` to inspect multiple functions in a monolithic file without slice limits.
5. Use `batch_query` or `ag-mcp.py` to pipeline lookup -> callers -> impact in 1 turn.
6. Use `semantic_search` for structure-aware lexical retrieval.
7. Use `codegraph:summarize_path` to inspect file structure without blowing read budgets.
8. Fall back to targeted `rg`/reads only when the facade misses or exact implementation detail is required.

## Report Shape

```yaml
codegraph_exploration:
  facade_queries:
    - tool: symbol_lookup
      query: <symbol-or-topic>
      result_count: <number>
  fallback_reads:
    - path: <path>
      reason: graph_miss | detail_needed | validation
  impact:
    affected_files: [...]
    candidate_tests: [...]
  confidence: high | medium | low
```

## Guardrails
- Do not claim CodeGraph coverage without listing the queries used.
- Do not use broad reads when a facade query can answer the structural question.
- Record misses as evolution evidence when they block or slow the task.

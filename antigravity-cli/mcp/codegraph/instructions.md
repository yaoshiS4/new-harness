# CodeGraph MCP Server Instructions

## Overview
High-performance code graph facade backed by persistent SQLite + Personalized PageRank (<15ms) for AST-indexed symbol resolution, caller/callee traversal, and blast radius impact analysis.

> [!IMPORTANT]
> **One-Shot MCP Execution (No 2-Turn Schema Inspection Tax)**:
> Always invoke directly using `call_mcp_tool` with `ServerName: "codegraph"`. Never inspect `.json` schemas before calling. Never use hallucinated legacy function names (`codegraph_*`).

---

## One-Shot `call_mcp_tool` Tool Payloads

### 1. `symbol_lookup`
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

### 2. `callers_callees`
Traverse callers and callees for a specified function, method, or class.
```json
{
  "ServerName": "codegraph",
  "ToolName": "callers_callees",
  "Arguments": {
    "root": "/path/to/project",
    "symbol": "<target_symbol>",
    "limit": 40
  }
}
```

### 3. `impact_analysis`
Estimate files and candidate tests affected by changed files or modified symbols (blast radius).
```json
{
  "ServerName": "codegraph",
  "ToolName": "impact_analysis",
  "Arguments": {
    "root": "/path/to/project",
    "changed_paths": ["path/to/modified_file.ts"],
    "symbols": ["<symbol_name>"],
    "limit": 60
  }
}
```

### 4. `semantic_search`
Lightweight structure-aware lexical search across project source files.
```json
{
  "ServerName": "codegraph",
  "ToolName": "semantic_search",
  "Arguments": {
    "root": "/path/to/project",
    "query": "<search_expression>",
    "limit": 20
  }
}
```

### 5. `repo_map`
Generate a PageRank-ranked repository map within strict token budgets.
```json
{
  "ServerName": "codegraph",
  "ToolName": "repo_map",
  "Arguments": {
    "root": "/path/to/project",
    "max_tokens": 1500,
    "focus_files": ["path/to/key_file.ts"]
  }
}
```

### 6. `summarize_path`
Summarize structural metrics for a file or directory with fast persistent SQLite caching.
```json
{
  "ServerName": "codegraph",
  "ToolName": "summarize_path",
  "Arguments": {
    "path": "/path/to/file_or_dir"
  }
}
```

### 7. `changed_symbols`
Extract symbol-like names from a diff with fast LRU caching.
```json
{
  "ServerName": "codegraph",
  "ToolName": "changed_symbols",
  "Arguments": {
    "diff_text": "--- a/app.py\n+++ b/app.py\n@@ -10,3 +10,5 @@\n-def old_func():\n+def new_func():\n"
  }
}
```

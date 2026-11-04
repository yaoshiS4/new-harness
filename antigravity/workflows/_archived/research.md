---
name: research
summary: Research workflow for current or official source validation. Read-only — never mutate project state.
---

# Research

## Purpose
Gather information from official and primary sources without mutating project state.

## Hard Rules
- **Read-only**: Never modify any project files, memory, or graph during research
- **Source tiering**: Prefer official docs and repository source over web search
- **No assumptions**: Record what sources say, not what you infer

## Steps

### 1. Read Project Context
- Use `call_mcp_tool(ServerName="codex_knowledge", ToolName="project_context")` to load existing knowledge
- Use `call_mcp_tool(ServerName="codex_knowledge", ToolName="memory_query")` to check past research
- Use `call_mcp_tool(ServerName="codex_knowledge", ToolName="graph_query")` to find relevant entities

### 2. Gather Sources
- **Tier 1**: Repository source code (`read_file`, `fd`, `rg`)
- **Tier 2**: Official library documentation (`call_mcp_tool(ServerName="context7", ToolName="resolve-library-id")` + `call_mcp_tool(ServerName="context7", ToolName="query-docs")`)
- **Tier 3**: Project wiki and knowledge base (`call_mcp_tool(ServerName="codex_knowledge", ToolName="vault_search")`)
- **Tier 4**: Web search (only if Tier 1-3 are insufficient)

### 3. Summarize Findings
- Compile findings into a compact research contract
- Cite all sources with tier levels
- Flag any contradictions between sources
- Use `call_mcp_tool(ServerName="codex_knowledge", ToolName="graph_query")` to verify logical consistency

### 4. Output Research Contract
```yaml
research_contract:
  question: <research question>
  findings:
    - claim: <what was found>
      source_tier: <1|2|3|4>
      source: <specific reference>
      confidence: <high|medium|low>
  contradictions:
    - claim_a: <one claim>
      claim_b: <contradicting claim>
      resolution: <which is more authoritative>
  gaps:
    - <what could not be found>
  recommendation: <based on findings>
```

### 5. Do NOT Mutate
- Do not write to any project files
- Do not update memory or graph stores (that's for the implementation phase)
- Do not make implementation decisions (that's for the planning phase)

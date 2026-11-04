---
name: request-enrichment
summary: Enrich vague or underspecified requests with focused questions and context before planning.
---

# Request Enrichment

## Purpose
Transform vague requests into validated, enriched requests with clear scope before planning begins.

## Steps

### 1. Read Current Request and Context
- Parse the user's original request
- Use `codex_knowledge_project_context` to load relevant project context
- Use `codex_knowledge_memory_query` to check for related past work
- Use `codex_knowledge_graph_query` to understand relevant entities

### 2. Identify Ambiguity
- What is unclear about the request?
- What decisions need to be made?
- What scope could change based on different interpretations?
- Use `codex_knowledge_project_context` for multi-perspective research

### 3. Ask Focused Questions
- Ask the user specific questions to resolve ambiguity
- Present options when multiple interpretations exist
- Use `question` tool for structured user input
- Never assume scope — always validate

### 4. Emit Enrichment Contract
```yaml
request_enrichment:
  original_request: <user's exact words>
  enriched_request: <validated and clarified intent>
  ambiguities_resolved:
    - ambiguity: <what was unclear>
      resolution: <how it was resolved>
      user_validated: <true|false>
  scope_decisions:
    - decision: <what was decided>
      options_considered: <list>
      chosen: <chosen option>
      rationale: <why>
  needs_user_validation: <true|false>
```

### 5. Select Role Bundle
- Based on the enriched request, select the appropriate role bundle
- Use `planner_suggest_topology` for routing
- Reference `docs/project/00_project_context/role_skill_catalog.md` for role mapping

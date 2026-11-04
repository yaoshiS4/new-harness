---
name: intake-pm
summary: PM intake workflow: classify, enrich, validate, and route incoming requests.
---

# Intake PM

## Purpose
Classify the request, enrich ambiguity, validate with the user, and produce a task contract for routing.

## Steps

### 1. Read Current Context
- Use `codex_knowledge_project_context` to load project context
- Use `codex_knowledge_memory_query` to check for related past work
- Use `codex_knowledge_graph_query` to understand relevant entities

### 2. Classify Request
- Determine task type: atomic, medium, epic, exploratory, debugging, self-healing, self-evolving
- Determine complexity: simple, moderate, complex
- Use `planner_suggest_topology` to suggest routing

### 3. Enrich Ambiguity
- Identify missing information
- Ask focused questions when scope can change
- Use `request_enrichment` workflow for vague requests
- Use `codex_knowledge_project_context` for multi-perspective research

### 4. Validate with User
- Present the enriched request to the user
- Confirm scope, documents, tests, and Oracle gates
- Get explicit approval before proceeding

### 5. Produce Task Contract
- Use `planner_review_task_contract` to create the contract
- Include: validated intent, task type, complexity, topology, allowed files, required tests, scope drift budget
- Record the contract in `codex_knowledge_knowledge_capture`

### 6. Route to Next Workflow
- Atomic → `development` → single agent
- Medium → `development` → sequential pipeline
- Epic → `development` → wave execution
- Exploratory → `research`
- Debugging → `debugging`
- Self-healing → `self_healing`
- Self-evolving → `self_evolving`

## Output Format
```yaml
intake:
  original_request: <user's original words>
  validated_intent: <enriched and validated intent>
  task_type: <atomic|medium|epic|exploratory|debugging|self_healing|self_evolving>
  complexity: <simple|moderate|complex>
  topology: <sequential_pipeline|independent_ensemble>
  task_contract_ref: <reference>
  next_workflow: <workflow name>
```

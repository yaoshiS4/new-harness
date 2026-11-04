---
name: memory-capture
summary: Capture approved lessons and traceability into durable project memory after validation.
---

# Memory Capture

## Purpose
Store only validated, durable lessons into project memory — never raw logs or transcript dumps.

## Prerequisites
- Approval and validation are complete (Oracle review passed)
- Implementation is verified (tests pass, AOP clean)

## Steps

### 1. Confirm Approval
- Verify Oracle review passed
- Verify all acceptance criteria met
- Verify no outstanding vetoes

### 2. Identify Lessons
- What was learned during this task?
- What patterns emerged?
- What mistakes were made and corrected?
- What would be done differently next time?

### 3. Record Durable Lessons
- Use `codex_knowledge_knowledge_capture` with:
  - slug: project slug
  - key: descriptive key (e.g., "lesson:<topic>:<date>")
  - value: compact lesson description
  - entity_id: related entity
  - source_ref: task contract reference

### 4. Update Memory Store
- Use `codex_knowledge_memory_store` for key-value lessons
- Use `codex_knowledge_graph_upsert` for entity relationships
- Use `codex_knowledge_handoff_checkpoint` for events, concepts, and intents

### 5. Update Indexes
- Use `codex_knowledge_wiki_ingest` if documentation changed
- Use `codex_knowledge_project_index` to refresh the project index

### 6. Avoid Anti-Patterns
- Never store raw conversation logs
- Never store unvalidated claims
- Never store implementation details that may change
- Store patterns, decisions, and rationale — not code snippets

## Output Format
```yaml
memory_capture:
  lessons_captured: <count>
  graph_edges_added: <count>
  memory_entries_added: <count>
  wiki_pages_updated: <count>
  source_ref: <task contract reference>
```

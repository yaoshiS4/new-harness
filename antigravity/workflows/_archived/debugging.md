---
name: debugging
summary: Systematic debugging workflow: reproduce, trace evidence, patch minimally, validate.
---

# Debugging

## Purpose
Reproduce the smallest useful failure surface, trace evidence before patching, and validate the fix.

## Steps

### 1. Reproduce the Failure
- Identify the exact command, input, or condition that triggers the failure
- Run the command and capture the full error output
- Verify the failure is reproducible (run at least twice)
- If not reproducible, check for:
  - Race conditions (timing-dependent)
  - Environment differences (OS, dependencies, config)
  - State-dependent issues (database state, file state)

### 2. Trace Evidence
- Use `codegraph:summarize_path` on the affected file(s) to understand structure
- Use `codex_knowledge_graph_query` to check known issues with the component
- Use `codex_knowledge_memory_query` to check past debugging lessons
- Use LSP diagnostics to identify type errors or undefined references
- Record all evidence:
  ```yaml
  debug_evidence:
    failure: <error message or behavior>
    reproduction_command: <exact command>
    reproduction_rate: <always|sometimes|rare>
    affected_files: <list>
    lsp_diagnostics: <list of errors>
    known_issues: <from knowledge graph>
    past_lessons: <from memory>
  ```

### 3. Identify Root Cause
- Narrow the failure to the smallest possible code change
- Use `codegraph:changed_symbols` to understand what symbols are involved
- Check if the issue is in:
  - Logic (wrong algorithm or condition)
  - Data (wrong input, missing data, stale cache)
  - Integration (API mismatch, version conflict)
  - Environment (missing dependency, wrong config)

### 4. Patch Minimally
- Make the smallest possible change that fixes the root cause
- Do NOT refactor, optimize, or add features while fixing
- Use `minimalist_review_change` to verify the patch is minimal
- Record the patch:
  ```yaml
  patch:
    root_cause: <description>
    fix: <what was changed>
    files_changed: <list>
    lines_added: <count>
    lines_removed: <count>
  ```

### 5. Validate the Fix
- Run the reproduction command again to confirm the fix works
- Run the full test suite to confirm no regressions
- Use `codex_knowledge_graph_query` to verify no logical contradictions introduced
- Record validation:
  ```yaml
  validation:
    reproduction_fixed: <true|false>
    tests_passing: <count>
    tests_failing: <count>
    lsp_errors: <count>
    aop_conflicts: <count>
  ```

### 6. Capture Lesson
- Use `codex_knowledge_orchestration_lesson` to record the debugging lesson
- Use `codex_knowledge_knowledge_capture` to store the root cause and fix
- Use `codex_knowledge_graph_upsert` to link the bug to the component

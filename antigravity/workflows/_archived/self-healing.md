---
name: self-healing
summary: Diagnose and fix runtime issues with minimal patches and regression checks.
---

# Self Healing

## Purpose
Diagnose and fix runtime issues (crashes, errors, misconfigurations) with the smallest safe patch.

## Steps

### 1. Inspect the Failing Runtime Surface
- Identify what is failing (process, service, tool, MCP server)
- Check error messages and stack traces
- Check recent changes that may have caused the failure
- Use `codex_knowledge_memory_query` for past similar issues

### 2. Reproduce with Smallest Useful Command
- Find the minimal command that reproduces the failure
- Record the exact reproduction steps
- Verify the failure is consistent (not intermittent)

### 3. Apply the Smallest Safe Fix
- Identify the root cause
- Make the minimal change that fixes it
- Use `minimalist_review_change` to verify the patch is minimal
- Do NOT refactor, optimize, or add features while fixing

### 4. Run Doctor and Validation Checks
- Run the reproduction command to confirm the fix
- Run the full test suite to check for regressions
- Run `codex_knowledge_graph_query` for logical consistency
- Run LSP diagnostics to check for type errors

### 5. Record the Fix
- Use `codex_knowledge_knowledge_capture` to store the fix
- Use `codex_knowledge_orchestration_lesson` if this is a recurring pattern
- Use `codex_knowledge_graph_query` if the same failure has occurred before

## Output Format
```yaml
self_healing:
  failure: <description>
  reproduction: <exact command>
  root_cause: <diagnosis>
  fix: <what was changed>
  files_changed: <list>
  tests_passing: <count>
  tests_failing: <count>
  regression: <none|list of regressions>
```

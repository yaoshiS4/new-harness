---
name: self-heal-runtime
summary: Diagnose and repair runtime failures with minimal patches and validation.
---

# Self Heal Runtime

## Purpose
Diagnose and repair runtime failures (crashes, misconfigurations, dependency issues) with minimal patches.

## Steps

### 1. Inspect the Failing Runtime Surface
- Identify the failing component (server, service, tool, MCP server)
- Check logs for error messages
- Check process status and resource usage
- Use `codex_knowledge_memory_query` for past runtime issues

### 2. Reproduce the Smallest Useful Failure
- Isolate the minimal reproduction case
- Record the exact command and environment
- Verify the failure is reproducible

### 3. Route to Appropriate Workflow
- **Configuration error** → `debugging` workflow
- **Dependency issue** → `debugging` workflow (dependency resolution)
- **Resource exhaustion** → `token_check` workflow (if context-related)
- **Service crash** → `self_healing` workflow

### 4. Patch Minimally
- Make the smallest possible change that fixes the issue
- Use `minimalist_review_change` to verify minimalism
- Do NOT refactor or optimize while fixing

### 5. Validate the Fix
- Run the reproduction command again
- Run any available health checks
- Use `codex_knowledge_knowledge_capture` to record the fix
- Use `codex_knowledge_orchestration_lesson` if this is a recurring issue

## Output Format
```yaml
self_heal:
  issue: <description>
  root_cause: <diagnosis>
  fix: <what was changed>
  validation: <reproduction result after fix>
  lesson_captured: <true|false>
```

# Preflight Gate

Run before starting any implementation. Checks readiness and prevents wasted effort.

## Preflight Checklist

### 1. Task Contract Exists
- [ ] Task contract / Story Shard created (`implementation_plan.md` + `task.md` for Path 2/3, or inline Story Shard for Path 1)
- [ ] Scope, complexity, and topology defined
- [ ] Allowed files (`allowed_files`) and required tests listed

### 2. Context Available
- [ ] Project registered in `codex_knowledge`
- [ ] Relevant context retrieved via `call_mcp_tool(ServerName="codex_knowledge", ToolName="project_context")`
- [ ] No stale data (check last update timestamp)

### 3. AOP Consistency Pre-check
- [ ] Query via `call_mcp_tool(ServerName="codex_knowledge", ToolName="graph_query")` and verify (`../../skills/oracle-review/SKILL.md`):
  - claims: stated requirements and constraints
  - relations: known dependencies
  - rules: project guardrails
- [ ] No critical conflicts detected
- [ ] If conflicts found, resolve before proceeding

### 4. Budget Available
- [ ] Context budget allocated per `../context_budget/policy.md`
- [ ] Context health check passed (`call_mcp_tool(ServerName="context_health", ToolName="get_session_health")`)

### 5. Tools Available
- [ ] Required MCP servers are running
- [ ] LSP servers are responsive
- [ ] No blocking issues

## Preflight Verdict

| Verdict | Condition |
|---------|-----------|
| GO | All checks pass |
| NO-GO | Critical conflicts, missing context, or budget exceeded |
| CONDITIONAL | Minor issues that can be resolved in-flight |

## Output Format
```yaml
preflight:
  task_ref: <reference>
  verdict: <GO|NO-GO|CONDITIONAL>
  checks:
    contract: <pass|fail>
    context: <pass|fail>
    aop_consistency: <pass|fail|conflicts>
    budget: <pass|fail>
    tools: <pass|fail>
  blockers: <list>
  warnings: <list>
```

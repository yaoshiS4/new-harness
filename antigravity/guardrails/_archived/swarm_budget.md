# Swarm Budget Guardrails

## Agent Coordination
- Agents and subagents communicate through Markdown or YAML contracts only
- Medium and epic tasks record Harness Activation after Scope Lock and before implementation
- Oracle review is mandatory after each major phase

## SOL Pipeline
- Clarify Gate resolves ambiguities and emits the task contract
- 3-Explore Phase runs backend, frontend, and research exploration
- Scope Lock Gate freezes atomic tasks and validation targets
- Harness Activation Gate selects task-scoped skills, rules, workflows, and MCP tools
- Plan Review Gate requires Oracle approval before implementation
- Implementation Gate executes only the approved plan
- Final Review Gate checks tests, spec compliance, scope adherence, and harness adherence

## Delegation Rules
- Subagents are explicit, bounded, and non-overlapping
- Read-only roles stay read-only
- Summary-only returns: changed files, evidence, risks, next action
- No sibling-to-sibling messaging
- Each write-capable agent has one branch or worktree

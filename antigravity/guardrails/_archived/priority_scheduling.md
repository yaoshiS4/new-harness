# Priority Scheduling Guardrails

## Model Selection
- Default to the strongest supported model available to the runtime
- Load only the native role bundle for the current task; do not load every skill by default
- Use the mini or fast model only for cheap reads, summaries, or narrow synthesis
- If a model name is rejected, fall back to the nearest supported model rather than failing the runtime

## Task Classification
- `pm` classifies the request before implementation starts
- `pm` decides whether the work is atomic, medium, epic, exploratory, debugging, self-healing, or self-evolving
- `pm` decides whether to delegate, spawn subagents, or run a multi-agent wave

## Harness Activation
- Medium and epic tasks record Harness Activation after Scope Lock and before implementation
- Harness Activation Gate selects task-scoped skills, rules, workflows, and MCP tools
- Plan Review Gate requires Oracle approval before implementation

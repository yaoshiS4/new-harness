# Guidelines Layer

Context-triggered governance rules that activate based on task type or project state.

## Active Guidelines

| Guideline | Trigger | Purpose |
|-----------|---------|---------|
| `anti-slop-taxonomy.md` | UI/UX implementation or review turns | Catalog of anti-patterns (nested cards, card soup, badge proliferation) |
| `ui-apex-invariants.md` | UI components, layouts, or visual styling | Visual symmetry, breathability, 0px razor geometry, motion standards |
| `performance-budget.md` | Task involves UI rendering or data processing | Enforce performance limits |
| `security-checklist.md` | Task involves auth, data, or external APIs | Security review checklist |
| `api-contract-first.md` | Task creates or modifies APIs | Enforce API contract discipline |
| `observability-standards.md` | Task adds new services or workers | Ensure logging, metrics, tracing |
| `dependency-policy.md` | Task adds or updates dependencies | Enforce update cadence and review rules |
| `tool-quirks.md` | Agent tool calls and CLI invocations | Working patterns and invariants for CLI/MCP tools |

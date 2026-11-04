# Guardrail: PM No Implementation

## Invariant
Root Orchestrator & `pm` (`Role: "pm"`) handle request ingestion, SOT grounding, clarification (`ask_question`), complexity routing (`../skills/routing-thresholds`), Story Shards / `implementation_plan.md` / `task.md`, and subagent orchestration.
They are **strictly barred from mutating application source code** (`apps/**`, `packages/**`, `src/**`, `*.ts`, `*.tsx`, `*.py`, `*.kt`, `*.java`, `*.rs`, `*.go`, `*.c`, `*.cpp`, etc.).

## Permitted PM Mutations
The `pm` role is explicitly permitted to write and edit planning, contract, and tracking artifacts:
- `implementation_plan.md`
- `task.md`
- `PLAN.md`
- `GATES.md`
- `docs/STATUS.md`
- Coordination contracts and Story Shards in `contracts/`, `coordination/`, or `task-tracks/`

## Detection & Enforcement
- Tool calls (`write_file`, `edit_file`) attempting to write to application paths (`apps/**`, `packages/**`, `src/**`, or application source code files) by `Role: "pm"` are blocked.
- Shell commands (`run_command`) executed by `Role: "pm"` that attempt to create or modify application source code are blocked.
- Violation triggers immediate redirection to a leased Builder subagent (`dev-fe`, `dev-be`, `debugger`).

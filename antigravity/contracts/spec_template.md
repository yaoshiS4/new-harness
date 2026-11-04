# Spec-Driven Project Template

## Purpose
Standardise project documentation structure for spec-driven development. Projects adopting this template gain Clarify Gate alignment, Scope Lock traceability, and Oracle review readiness.

## Root Documents

### SPEC.md (Executable Specification)
```markdown
# Project Specification

## Overview
<one-paragraph description of what the project does>

## Goals
1. <goal-1>
2. <goal-2>

## Non-Goals
1. <non-goal-1>

## Architecture
<high-level architecture diagram or description>

## Key Decisions
| Decision | Rationale | Date |
|----------|-----------|------|
| <decision> | <rationale> | <date> |

## Constraints
- <constraint-1>
- <constraint-2>

## Validation Criteria
| Criterion | Measurement | Target |
|-----------|-------------|--------|
| <criterion> | <how-measured> | <target> |
```

### ARCHITECTURE.md
```markdown
# Architecture

## System Context
<diagram or description of system boundaries>

## Component Diagram
<diagram or description of major components>

## Data Flow
<description of how data flows through the system>

## Technology Stack
| Layer | Technology | Version |
|-------|-----------|---------|
| <layer> | <tech> | <version> |

## Deployment
<description of deployment topology>
```

### ROADMAP.md (Atomic Task List)
```markdown
# Roadmap

## Phase 1: <phase-name>
- [ ] <atomic-task-1> (estimate: <hours>)
- [ ] <atomic-task-2> (estimate: <hours>)

## Phase 2: <phase-name>
- [ ] <atomic-task-3> (estimate: <hours>)

## Locked After Approval
Tasks are frozen after Scope Lock Gate. Changes require re-opening the gate.
```

### CONVENTIONS.md
```markdown
# Conventions

## Code Style
- <style-rule-1>
- <style-rule-2>

## Minimalism
- Smallest valid diff that satisfies the task.
- No speculative features.
- No premature optimisation.

## Tech Debt
- Record tech debt in ROADMAP.md with estimate.
- Address tech debt in dedicated phases, not during feature work.
```

### TESTING.md
```markdown
# Testing

## Regression Gate
<command to run regression tests>

## Quality Gates
| Gate | Command | Pass Criteria |
|------|---------|---------------|
| Lint | <cmd> | 0 errors |
| Type Check | <cmd> | 0 errors |
| Unit Tests | <cmd> | 100% pass |
| Integration | <cmd> | 100% pass |

## Coverage Target
<minimum coverage percentage>
```

## Integration with 8-Stage Pipeline & 3-Tier Adaptive Routing

### Stages 1–3: Intake, Enrichment & Clarification
- Ground against project SOT docs (`docs/STATUS.md`, `AGENTS.md`, `SPEC.md`).
- Clarify requirements and constraints via targeted questioning before scope freeze.

### Stage 4: PM Contract & Story Shards
- Freeze atomic task list in `ROADMAP.md` / `task.md` with explicit file leases (`allowed_files`).
- Scope drift budget and verification criteria are recorded in task contract (`implementation_plan.md`).

### Stages 5–6: Builder Implementation
- Disjoint Builders (`dev-fe` / `dev-be`) mutate code within leased Story Shards.

### Stage 7: Two-Stage QC
- 7a Static QC (`frontend-qc` / linters / types) + 7b Dynamic QC (`test-runner` execution).

### Stage 8: Independent Oracle Audit
- Oracle verifies implementation against `SPEC.md` validation criteria and `TESTING.md` regression gates.

## Adoption
Projects may adopt this template incrementally. Minimum viable adoption:
1. `SPEC.md` with goals and validation criteria.
2. `ROADMAP.md` with atomic task list.

Full adoption adds `ARCHITECTURE.md`, `CONVENTIONS.md`, and `TESTING.md`.

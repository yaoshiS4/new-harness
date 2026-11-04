---
name: constitution-generation
summary: Generate the project constitution as Phase 0 artifact. Captures governing principles, non-negotiable rules, and development guidelines before any other work proceeds.
---

# Constitution Generation

## Purpose
Generate `.specify/constitution.md` as the foundational artifact for every project. The constitution is the root of all downstream traceability and the non-negotiable contract that governs all subsequent work.

## When to Run
- At the START of every new project
- When the user requests a new feature initiative from scratch
- When an existing project lacks a constitution
- When constitution amendments are needed (re-opens all downstream gates)

## Steps

### 1. Interview the User
- Use `requirement-interviewer` skill to ask focused questions:
  - What are the project's non-negotiable values?
  - What quality standards must be maintained?
  - What technology constraints exist?
  - What security/privacy requirements apply?
  - What performance targets are mandatory?
  - What accessibility standards must be met?
  - What is the team's working style (TDD, PR review, etc.)?
  - What documentation standards are required?

### 2. Generate Constitution
Produce `.specify/constitution.md` with at minimum these sections:

```markdown
# [Project Name] Constitution

**Date**: [DATE]
**Version**: 1.0
**Author**: [PM with user input]

## Core Principles
1. [Non-negotiable principle]
2. [Non-negotiable principle]

## Quality Standards
- Test coverage: [target]
- Lint rules: [rules]
- Review process: [process]

## Technology Constraints
- [Constraint or choice]
- [Constraint or choice]

## Security & Privacy
- [Requirement]
- [Requirement]

## Out of Scope (Project-Level)
<!-- What this project will explicitly NEVER do -->
1. [Excluded scope]
2. [Excluded scope]

## Amendment Process
<!-- How to change this constitution later -->
- Amendments require user approval
- Amendments re-open all downstream gates
```

### 3. Oracle Review
- Submit constitution for Oracle review
- Check: principles are unambiguous, measurable, and enforceable
- Check: no contradictory principles
- Check: out-of-scope declarations are clear

### 4. User Approval
- Present constitution to user
- Get explicit approval before proceeding to Phase 1
- Record approval in checkpoint

### 5. Persist
```yaml
constitution:
  project: <project name>
  file: .specify/constitution.md
  approved_by: <user>
  approved_at: <ISO-8601>
  amendment_count: 0
```

- Record: `codex_knowledge_handoff_checkpoint(name=sol:<task_id>:constitution)`

## Guardrails
- Never skip constitution generation for new projects
- Constitution is the FIRST artifact — no spec, no plan, no code before it
- Constitution changes after Phase 0 re-open ALL downstream gates
- Keep the constitution concise — ≤50 lines for principles

# Task Breakdown: [FEATURE_NAME]

> **Plan:** [link to implementation plan]
> **Spec:** [link to feature spec]
> **Control Manifest:** `contracts/control_manifest.yaml` (Mandatory for Epics/Waves)
> **Code Exclusion Zones:** [List of forbidden paths or "Inherited from AGENTS.md / pre_tool_use_hook.py"]
> **Source of Truth / Rules:** [link to `AGENTS.md`]
> **Author:** Project Manager
> **Status:** Draft | Approved | In Progress | Done
> **Superpowers TDD Standard (from obra/superpowers - MR-13):** Tasks must be clear enough for an enthusiastic junior engineer with no prior context to follow. Every functional change MUST have an explicit Red phase (failing test) before implementation (Green phase). If a task cannot meet this clarity bar, mark it `[NEEDS CLARIFICATION]` and escalate to PM before proceeding.

---

## Legend

- `[ ]` — Not started
- `[/]` — In progress
- `[x]` — Done
- `[P]` — Can run in **parallel** with other `[P]` tasks in the same group
- `[B]` — **Blocked** on a preceding task or external dependency
- `[NEEDS CLARIFICATION]` — Cannot proceed without clarification

---

## Phase 1: [Phase Name from Plan]

**Checkpoint:** [What should be independently verifiable after this phase]

### 1.1 Types & Interfaces
- [ ] Create `[path/to/types.ts]` — define [interfaces]
  - Dependencies: None

### 1.2 Tests (TDD Red)
- [ ] Create `[path/to/feature.test.ts]` — test [behavior]
  - Dependencies: 1.1
  - Expected: Tests FAIL (Red phase)

### 1.3 Implementation (TDD Green)
- [ ] [P] Implement `[path/to/service.ts]` — [purpose]
  - Dependencies: 1.1, 1.2
- [ ] [P] Implement `[path/to/util.ts]` — [purpose]
  - Dependencies: 1.1

### 1.4 Phase Checkpoint
- [ ] All Phase 1 tests pass
- [ ] Type check — zero type errors
- [ ] Lint clean

---

## Phase 2: [Phase Name from Plan]

**Checkpoint:** [...]

### 2.1 [Task Group]
- [ ] [Task description]
  - Dependencies: Phase 1
- [ ] [Task description]
  - Dependencies: 2.1.1

---

## Final Verification

- [ ] Full test suite passes
- [ ] Type check passes
- [ ] Lint passes
- [ ] Visual verification (light + dark mode, mobile viewport)
- [ ] All acceptance criteria from spec checked off
- [ ] No `[NEEDS CLARIFICATION]` markers remain

---

## Traceability Matrix

> Every task must trace to a spec requirement. Every spec requirement must have at least one task.

| Spec Requirement | Task(s) | Status |
|-----------------|---------|--------|
| US-1 AC-1 | 1.3.1 | |
| US-1 AC-2 | 1.3.2 | |
| US-2 AC-1 | 2.1.1 | |

---

## Human E2E Continuation Guide
<!-- ⚠️ MANDATORY SECTION ⚠️ -->
<!-- After LLM delivers the code, a human must be able to continue without LLM. -->
<!-- This section bridges the implementation to human understanding. -->

### What Was Built
<!-- 2-3 sentence summary a human can read to understand the feature -->

### Files Delivered
<!-- Every file created or modified, with one-line purpose -->
| File | Purpose | Status |
|------|---------|--------|
| `[path/to/file.ts]` | [what it does] | New / Modified |

### Commands to Verify
<!-- Copy-pasteable commands a human runs to prove everything works -->
```bash
# 1. Install dependencies
[command]

# 2. Run all tests
[command]

# 3. Type check
[command]

# 4. Lint
[command]

# 5. Start the app and verify manually
[command]
```

### In-Scope Checklist
<!-- What this delivery includes -- check off as verified -->
- [ ] [Feature/requirement]
- [ ] [Feature/requirement]

### Out of Scope (from spec)
<!-- What was explicitly NOT built -- for human context -->
- [ ] [Excluded item] — deferred to [phase/epic]
- [ ] [Excluded item] — not needed

### Known Gaps
<!-- From convergence analysis: what remains to be built -->
| Gap | Priority | Deferred To |
|-----|----------|-------------|
| [gap description] | High/Med/Low | [phase/epic/issue] |

### How to Continue
<!-- A human reading this should know exactly what to do next -->
1. Read `[path/to/spec]` for full requirements
2. Read `[path/to/plan]` for architecture decisions
3. The next priority tasks are: [list]
4. Run `[command]` to regenerate/rebuild if needed

---

> **Instructions for Project Manager / LLM:**
> - Derive tasks directly from the implementation plan phases
> - Enforce Superpowers Junior-Engineer standard: specify explicit file paths, line ranges, and test commands
> - Mandate TDD sequence: Phase X.2 Tests (Red) MUST precede Phase X.3 Implementation (Green)
> - Mark parallel-safe tasks with `[P]`
> - Include explicit dependencies for every task
> - Each phase MUST have a checkpoint that validates independent functionality
> - Fill in the Traceability Matrix — every spec requirement needs >=1 task
> - **The Human E2E Continuation Guide is MANDATORY — a human reading this section should be able to continue development without LLM assistance**
> - If a task cannot be defined clearly, mark it `[NEEDS CLARIFICATION]`

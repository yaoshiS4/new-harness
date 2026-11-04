# Implementation Plan: [FEATURE_NAME]

> **Spec:** [link to feature spec]
> **Source of Truth / Rules:** [link to `AGENTS.md`]
> **Author:** Senior Architect
> **Status:** Draft | Reviewed | Approved

---

## Phase -1: Pre-Implementation Gates

> These gates MUST pass before any implementation begins. If a gate fails, document the justification in the Complexity Tracking section below.

### Simplicity Gate
- [ ] Using minimal new dependencies?
- [ ] No speculative features?
- [ ] No premature abstraction?
- [ ] Simplest approach that meets acceptance criteria?

### Modularity Gate
- [ ] No circular dependencies introduced?
- [ ] New logic in service layer, not in UI components?
- [ ] Feature independently testable?

### Data Integrity Gate
- [ ] Calculation algorithms cite authoritative sources?
- [ ] Edge cases (year boundaries, leap months) explicitly handled?

### Security Gate
- [ ] No hardcoded secrets?
- [ ] All user inputs validated?
- [ ] CSP implications reviewed?

### Scope Discipline Gate
- [ ] Out of scope items from spec are respected?
- [ ] No implementation beyond spec boundaries?
- [ ] All planned files trace to spec requirements?

---

## 1. Technical Approach

### Architecture Overview
<!-- High-level description of the approach. Keep it readable. -->

### Technology Choices
| Decision | Choice | Rationale | Alternatives Considered |
|----------|--------|-----------|------------------------|
| | | | |

### Data Model Changes
<!-- New types, modified interfaces, database schema changes -->

---

## 2. Implementation Phases & BMAD Story Shards

### Section 2.0: BMAD Story Shards (Disjoint Ownership Leases)

```yaml
story_shards:
  - shard_id: "SHARD-1"
    owner_role: "dev-be | dev-fe | debugger"
    allowed_files:
      - "path/to/file.ts"
    Oracle-Custody-Lease: "NONE | UPDATE_ASSERTIONS"
    verification_cmd: "pytest -q path/to/test.py"
    immutable_acs:
      - "AC-1: Concrete testable outcome"
```

### Phase 1: [Name]
**Prerequisite:** None
**Deliverable:** [What is independently testable after this phase]
**Files:**
- `[path/to/file]` — [purpose]

### Phase 2: [Name]
**Prerequisite:** Phase 1
**Deliverable:** [...]
**Files:**
- `[path/to/file]` — [purpose]

---

## 3. File Creation Order

> Follow this order to respect dependencies and support TDD.

1. Types/interfaces (`.ts` type files)
2. Test files (TDD Red — tests that fail)
3. Service/engine implementations (TDD Green)
4. UI components (if applicable)
5. Integration wiring

---

## 4. Test Strategy

### Unit Tests
- [ ] Engine logic covered (target: 80%+)
- [ ] Edge cases from spec explicitly tested

### Integration Tests
- [ ] Component + service integration tested
- [ ] API contract tests (if applicable)

### Visual Tests
- [ ] Light/dark mode verified
- [ ] Mobile viewport verified

### Human E2E Verification Tests
- [ ] Copy-pasteable verification commands included (see spec Section 7)
- [ ] A human can run these without LLM

---

## 5. Complexity Tracking

> Document any gate failures or justified complexity here.

| Gate | Status | Justification (if failed) |
|------|--------|--------------------------|
| Simplicity | PASS/FAIL | |
| Modularity | PASS/FAIL | |
| Data Integrity | PASS/FAIL | |
| Security | PASS/FAIL | |
| Scope Discipline | PASS/FAIL | |

---

## 6. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| | | |

---

## 7. Out of Scope (Reaffirmed)
<!-- Restate the spec's out-of-scope declarations to confirm they're respected in this plan -->
1. [Excluded item from spec] — NOT implemented
2. [Excluded item from spec] — NOT implemented

---

## 8. Oracle Hardening, Directives & Sign-Off
<!-- Exclusively authored by Oracle during Stage 8 Independent Oracle Audit. Oracle does not rewrite author sections; it appends binding constraints, adversarial findings, and test mandates here. -->

### Adversarial Findings & Mitigations
| Concern / Edge Case Identified | Severity | Mandatory Mitigation | Verified By |
|---------------------------------|----------|----------------------|-------------|
| | High/Med/Low | | |

### Hardened Verification Mandates
- [ ] Explicit edge-case test cases added to `task-breakdown.md`
- [ ] Architectural & logical consistency verified
- [ ] Cross-artifact consistency verified (Spec $\leftrightarrow$ Plan $\leftrightarrow$ Tasks)

### Oracle Review Verdict
```yaml
oracle_sign_off:
  reviewer: Oracle
  verdict: PASS | CONDITIONAL | FAIL
  scope_drift_observed: 0%
  binding_directives:
    - "<directive>"
  signed_at: "<timestamp>"
```

---

## Review Checklist

- [ ] Every phase has clear prerequisites and deliverables
- [ ] All tech choices trace back to spec requirements
- [ ] File creation order supports TDD
- [ ] No over-engineering — each complexity justified
- [ ] Gates all pass (or failures documented)
- [ ] Cross-checked against spec — no orphaned or missing requirements
- [ ] Section 7 (Out of Scope Reaffirmed) matches spec Section 5
- [ ] Section 8 (Oracle Hardening & Sign-Off) completed by Oracle
- [ ] Human E2E verification tests included in test strategy

---

> **Instructions for Senior Architect & Oracle:**
> - **Senior Architect**: Authors Sections 1–7. This plan should remain high-level and readable.
> - **Oracle**: Authors Section 8 (Hardening, Directives & Sign-Off). Does not rewrite the author's architecture, but adds binding constraints, required mitigations, and synchronizes with `task-breakdown.md`.
> - A human reading this plan should understand ALL decisions without LLM assistance.

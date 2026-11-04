# Feature Specification: [FEATURE_NAME]

> **Created:** [DATE]
> **Author:** Business Analyst
> **Status:** Draft | Clarified | Approved
> **Branch:** [NNN]-[feature-slug]
> **Source of Truth / Rules:** [link to `AGENTS.md`]

---

## 0. Traceability Anchor
<!-- MANDATORY: Link this spec to its parent SOT / AGENTS.md and any upstream PRD -->
> **SOT / Rules Ref:** `AGENTS.md`  
> **Source Request:** [link to original user request / PRD]  
> **Future Human Reader:** Start here. This document is self-contained. All referenced files exist.

---

## 1. Overview

### Problem Statement
<!-- What problem does this solve? Who has this problem? -->

### Business Value
<!-- Why does this matter? What metric does it improve? -->

### Success Criteria
<!-- How do we know this feature is successful? Measurable outcomes. -->

---

## 2. User Stories

### US-1: [Story Title]
**As a** [user type], **I want** [action], **so that** [benefit].

**Acceptance Criteria:**
- [ ] Given [context], when [action], then [expected result]
- [ ] Given [context], when [action], then [expected result]

### US-2: [Story Title]
<!-- Repeat as needed -->

---

## 3. Functional Requirements

### 3.1 Core Behavior
<!-- WHAT the feature does. Focus on behavior, not implementation. -->
<!-- Use [NEEDS CLARIFICATION: specific question] for anything ambiguous -->

### 3.2 Error Handling
<!-- What happens when things go wrong? -->

### 3.3 Edge Cases
<!-- Empty data, huge data, special characters, timezone/calendar quirks, etc. -->

---

## 4. Non-Functional Requirements

- **Performance:** [e.g., renders within 200ms on mobile]
- **Accessibility:** [WCAG AA minimum]
- **Localization:** [Primary and secondary languages]
- **Theme:** [Must support light + dark mode]

---

## 5. Out of Scope
<!-- ⚠️ MANDATORY SECTION — DO NOT DELETE OR LEAVE EMPTY ⚠️ -->
<!-- Explicitly state what this feature does NOT include. -->
<!-- This is critical for human readers to understand boundaries without LLM. -->

### Explicitly NOT Included:
1. [Feature/scenario that is explicitly excluded]
2. [Another excluded item]
3. [Edge case that is intentionally deferred]

### Rationale
<!-- Why are these items out of scope? (e.g., deferred to Phase 2, separate epic, not needed) -->

---

## 6. Open Questions
<!-- Items that need clarification before planning can begin -->
<!-- Each item must use: [NEEDS CLARIFICATION: specific question] -->

---

## 7. E2E Human Verification
<!-- ⚠️ MANDATORY SECTION ⚠️ -->
<!-- A human without LLM access must be able to verify this feature by following these steps. -->
<!-- Write commands that are copy-pasteable into a terminal. -->

### Prerequisites
```bash
# Commands to set up the verification environment
# e.g., npm install, docker-compose up, etc.
```

### Verification Steps
1. **Start the application:**
   ```bash
   [copy-pasteable command]
   ```
   **Expected:** [what the human should see]

2. **Trigger the happy path:**
   ```bash
   [copy-pasteable command or curl or UI steps]
   ```
   **Expected:** [what the human should see]

3. **Trigger error handling:**
   ```bash
   [copy-pasteable command]
   ```
   **Expected:** [what the human should see]

4. **Run automated tests:**
   ```bash
   [copy-pasteable test command]
   ```
   **Expected:** All tests pass, 0 failures

5. **Run lint/typecheck:**
   ```bash
   [copy-pasteable lint command]
   ```
   **Expected:** 0 errors

---

## 8. Review Checklist

### Requirement Completeness
- [ ] No `[NEEDS CLARIFICATION]` markers remain
- [ ] Every user story has testable acceptance criteria
- [ ] Success criteria are measurable
- [ ] Error and edge cases addressed
- [ ] Non-functional requirements specified

### Specification Quality
- [ ] Focuses on WHAT/WHY, not HOW (no tech stack mentions)
- [ ] No speculative or "might need" features
- [ ] No vague requirements — each item is specific
- [ ] Consistent terminology throughout

### Human-Readable Traceability
- [ ] **Section 5 (Out of Scope) is filled in — NOT empty, NOT deleted**
- [ ] **Section 7 (E2E Human Verification) has copy-pasteable commands**
- [ ] All file references match actual files in the repository
- [ ] A human can read this document and verify the feature without LLM

### Process Compliance
- [ ] Spec written before code
- [ ] Simplicity — minimal scope
- [ ] Data integrity for engine features
- [ ] AGENTS.md / SOT reference present

---

> **Instructions for Business Analyst / LLM:**
> - Focus on WHAT users need and WHY
> - Do NOT include technology choices, APIs, or code structure
> - Mark ALL ambiguities with `[NEEDS CLARIFICATION: specific question]`
> - Do NOT guess — if the user prompt doesn't specify something, mark it
> - **Section 5 (Out of Scope) is MANDATORY — never leave empty**
> - **Section 7 (E2E Human Verification) is MANDATORY — provide copy-pasteable commands**
> - Complete the Review Checklist before submitting for PM review

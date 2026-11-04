# Review Policy: [Repository / Project Name]

This policy defines the deterministic review passes, severity classifications, and nit caps for both AI agents and human reviewers across Pull Requests and implementation changes.

---

## 1. Review Passes

Every comprehensive review must execute three distinct passes and tag each finding with its pass:

### Pass 1: Logic & Bugs
- **Focus:** Logic errors, unhandled edge cases, subtle regressions, race conditions, memory leaks, and broken lifecycle states.
- **Target:** Verify that the code satisfies the stated problem without side effects on neighboring components.

### Pass 2: Security & Privacy
- **Focus:** Injection risks, authentication/authorization bypasses, unvalidated inputs, raw disk/shell execution, secret exposure, and PII leakage in logs.
- **Target:** Zero high/critical vulnerabilities. Strict enforcement of data classification boundaries.

### Pass 3: Compliance vs `plan.md` & Architecture Invariants
- **Focus:** 
  - Traceability against the approved `plan.md` / `implementation_plan.md`: Does the diff change files that were not planned? Did it skip promised tests?
  - Adherence to repository invariants (e.g. 66 Master Invariants, 0px Razor geometry, Golden Metric ratio, token economy).
- **Target:** Scope drift within approved budget; zero unauthorized architectural mutations.

---

## 2. Severity Classification

- **CRITICAL / BLOCKING:** Breaks system integrity, introduces security vulnerabilities, leaks credentials/PII, causes data loss, or violates core architectural laws. Merging is prohibited.
- **IMPORTANT:** Significant logic bugs, performance regressions, missing error boundaries, or uncovered edge cases. Must be addressed before production release.
- **NIT:** Minor code style, naming nuances, non-critical comments, or cosmetic refactor suggestions that do not affect behavior.

---

## 3. Complete Finding Reporting (Uncapped List Invariant)

To ensure complete visibility without artificial truncation:
- **Full Uncapped List:** Report all actionable findings and nits in full; never truncate to a "top 5".
- **Never block on nits:** Nits must never block a PR merge or gate sign-off.

---

## 4. Excluded Paths (Zero-Noise Zone)

Do not report style or structural findings on:
- Auto-generated files (e.g. `src/gen/**`, `*.generated.*`, proto outputs).
- Third-party vendor bundles or lockfiles (`package-lock.json`, `pnpm-lock.yaml`, `Cargo.lock`).
- Issues already caught and enforced by automated deterministic CI linters (e.g. ESLint, Prettier, Ruff).

---

## 5. Review Resolution Loop

1. Findings are ranked by severity: `[CRITICAL]` $\to$ `[IMPORTANT]` $\to$ `[NIT]`.
2. Author or agent addresses findings directly on the branch.
3. If an agent repeats a mistake flagged in a previous review, update the repository's `AGENTS.md` under *"Learned Lessons / Agent Corrections"* to permanently prevent recurrence.

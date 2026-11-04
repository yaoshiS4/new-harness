# Full protocol: e2e_testing

Loaded on demand; see SKILL.md for triggers and core rules.

### 1. Establish Scope And Baseline
- Read the current task context, SOT docs, and `AGENTS.md`.
- Use curated context, local knowledge, and CodeGraph-first exploration before broad scanning when the project provides them.
- Record the baseline: existing failing tests, build state, type/lint state, and known environmental limits.
- Identify critical user journeys, APIs, data flows, integrations, state transitions, permissions, and deployment/runtime surfaces affected by the change.
- Classify validation depth with the project's regression strategy or native regression gate.

### 2. Build The Test Matrix
Cover each applicable lens:

- **Smoke:** app/service starts, primary route or command works, auth/session basics work, no obvious console/runtime crash.
- **Functional:** acceptance criteria, happy path, alternate path, error path, empty/loading states, retries, cancellation, and recovery.
- **Boundary and input:** min/max, off-by-one, invalid values, malformed payloads, missing fields, duplicate submissions, time/date/timezone edges, locale/encoding, large payloads, and stale cached state.
- **Integration/API:** request/response shape, status codes, validation errors, auth headers, pagination/filtering/sorting, idempotency, persistence, event queues, and third-party failures.
- **System/E2E:** full workflow through real entry points, browser or CLI/runtime path, storage/database effects, refresh/restart behavior, and cross-module consistency.
- **Regression:** affected callers, shared dependencies, previous bug seams, unchanged-but-adjacent workflows, and project-native full regression when risk warrants it.
- **UI/UX and accessibility:** layout, responsive breakpoints, keyboard navigation, focus order, visible states, touch targets, contrast, labels, screen-reader affordances, and no overlap/clipping.
- **Performance:** render churn, slow queries, expensive loops, bundle/runtime size, load latency, memory/resource leaks, long-task behavior, and realistic load when relevant.
- **Security:** authz/authn boundaries, secret exposure, injection/XSS/CSRF/SSRF/path traversal, dependency vulnerabilities, unsafe file writes, permission prompts, and data leakage.
- **Compatibility:** supported browsers/devices/OSes, mobile/desktop, network conditions, offline/cache behavior, environment variables, and deployment configuration.
- **Resilience:** dependency outage, network failure, timeout, partial writes, restart recovery, graceful degradation, and clear user-facing errors.
- **Observability:** actionable logs, no noisy false success, metrics/traces where expected, and enough evidence to debug failures.

### 3. Execute From Outside In, Then Inside Out
- Start with black-box smoke and critical journey tests through the real user/runtime entry points.
- Run gray-box API, contract, data, and integration checks using project schemas and docs.
- Run white-box inspection for risky branches, unreachable code, stale state, race conditions, resource cleanup, and untested changed logic.
- Use automation for repeatable regression and API checks; use exploratory/manual testing for complex UX and surprising workflows.
- For UI work, include live browser validation and screenshots when feasible.
- For backend/runtime work, include real command/service entrypoints and persistence checks when feasible.

### 4. Common Bug Symptoms To Hunt
- Happy path passes but refresh, back/forward navigation, restart, or retry breaks state.
- UI displays stale data after store updates, async completion, cache restoration, or route changes.
- Inputs accept values that downstream code cannot handle.
- Validation errors differ between UI, API, and database constraints.
- Loading, empty, disabled, and error states are missing or misleading.
- Duplicate clicks, double submits, and concurrent requests create duplicate records or race bugs.
- Timezone, DST, leap day, month boundary, locale, and encoding cases produce inconsistent results.
- Permission prompts appear too early, too often, or on unrelated screens.
- Mobile layout clips controls, overlaps text, hides focus, or depends on hover-only interaction.
- API shape or docs drift from implementation.
- Build/test scripts pass while the deployed/runtime path uses stale generated assets.
- Security or privacy-sensitive data appears in logs, URLs, client bundles, screenshots, or exported artifacts.
- Performance is acceptable on warm local state but slow on cold load, large data, or repeated interaction.
- Error handling reports success, swallows failures, or cannot be traced to a cause.

### 5. Evidence And Triage
For each finding, record:

```yaml
finding:
  severity: critical|high|medium|low
  surface: ui|api|data|security|performance|compatibility|resilience|docs|runtime
  symptom: <what failed>
  reproduction: <minimal steps or command>
  expected: <expected behavior>
  actual: <actual behavior>
  evidence: <test, screenshot, log, trace, or file reference>
  suspected_cause: <if known>
  fix_status: open|fixed|deferred|not_reproducible
```

Severity guide:
- **Critical:** data loss, security exposure, broken launch/deploy, unusable core workflow.
- **High:** core workflow wrong, serious regression, crash, auth/permission defect, severe performance failure.
- **Medium:** important edge case, confusing recovery, compatibility issue, incomplete validation.
- **Low:** polish issue, minor copy/state mismatch, non-blocking observability gap.

### 6. Completion Gate
Before declaring the sweep complete:
- Re-run focused tests for every fix made during the sweep.
- Run the project-native regression gate when exposed and risk warrants it.
- Apply `auto-verification-harness` (`test-3-round-loop.sh` scaffolded via `ensure-verification-gates.py`) for completion claims.
- Apply `oracle-review` when code was changed.
- Apply `ui-ux-audit` / `frontend-qc` for UI surfaces.
- Report remaining risks honestly; do not convert untested assumptions into pass claims.


---
## Output

```yaml
e2e_testing_report:
  scope: <features/workflows covered>
  baseline: <known initial state>
  test_matrix:
    smoke: pass|fail|not_applicable
    functional: pass|fail|not_applicable
    boundary_input: pass|fail|not_applicable
    integration_api: pass|fail|not_applicable
    system_e2e: pass|fail|not_applicable
    regression: pass|fail|not_applicable
    ui_accessibility: pass|fail|not_applicable
    performance: pass|fail|not_applicable
    security: pass|fail|not_applicable
    compatibility: pass|fail|not_applicable
    resilience: pass|fail|not_applicable
    observability: pass|fail|not_applicable
  commands_run:
    - command: <command>
      result: pass|fail
      notes: <brief evidence>
  findings: <list>
  fixes_applied: <list>
  residual_risks: <list>
  verdict: PASS|FAIL|CONDITIONAL
```

## Guardrails
- Do not run destructive tests against production data or real third-party services without explicit approval.
- Do not add dependencies, migrations, new infrastructure, or broad architecture changes without approval.
- Do not claim full E2E coverage if only static review or unit tests ran.
- Do not hide environmental blockers; separate product defects from test-environment failures.
- Keep fixes surgical and retest the exact failing path after each fix.

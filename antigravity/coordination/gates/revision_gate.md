# Revision Gate

## Purpose
When output misses the contract or evidence, send it back for correction before proceeding to Oracle review. The revision gate is a quality filter that prevents unready work from reaching Oracle.

## Revision Decision Tree

```
Builder submits output after completing a slice
    │
    ▼
PM runs revision gate checks (Section 1)
    │
    ▼
Are there any issues?
    │
    ├── NO → Verdict: PROCEED. Send to oracle_review_gate.
    │
    └── YES → Classify issues by severity (Section 2)
                │
                ├── Minor → Verdict: REVISE (minor). Return to builder.
                │
                ├── Major → Verdict: REVISE (major). PM reviews scope. Return to builder.
                │
                └── Critical → Verdict: ESCALATE. Fundamental approach is wrong.
                            └── PM re-scopes or invokes ./escalation_gate.md
```

## When to Trigger

Trigger the revision gate after builder completes implementation and BEFORE Oracle review. The gate fires automatically at the end of every slice.

**Specific trigger conditions:**

| Condition | Detection Method | Typical Severity |
|-----------|------------------|------------------|
| Implementation doesn't match task contract scope | PM task contract review | Major or Critical |
| Missing test evidence for claimed functionality | `run_command` with test runner shows 0 tests for changed file | Minor or Major |
| AOP consistency check finds conflicts | `call_mcp_tool(ServerName="codex_knowledge", ToolName="graph_query")` | Major or Critical |
| Minimalism review flags over-engineering | `oracle-review` skill | Minor or Major |
| Unapproved files were modified | `scope-drift-control` skill shows files outside planned set | Major |
| Builder did not follow approved approach | Compare output against task contract | Major or Critical |
| Tests fail | `run_command` with test runner | Minor (if trivial fix) or Major |
| LSP errors in changed files | Language server diagnostics | Minor |
| Missing documentation for public API changes | `rg` for docstrings/comments in changed files | Minor |

---

## Steps

### 1. Identify What Needs Revision

PM compares builder output against the task contract systematically:

**Checklist:**
1. **Scope Alignment:**
   - Load task contract via `call_mcp_tool(ServerName="codex_knowledge", ToolName="handoff_read")` or `call_mcp_tool(ServerName="codex_knowledge", ToolName="vault_read")`.
   - List all acceptance criteria from the contract.
   - For each criterion, verify evidence in the builder output.
   - Run PM task contract review to validate alignment.

2. **Test Evidence:**
   - Run the test suite: `run_command` with `pytest -v` or equivalent.
   - For each claimed feature, find the corresponding test.
   - If a feature has no test, flag as missing evidence.

3. **AOP Consistency:**
   - Invoke `call_mcp_tool(ServerName="codex_knowledge", ToolName="graph_query")`:
     - `claims`: architectural claims implied by the new code
     - `rules`: existing project rules from memory or vault
   - Record any conflicts.

4. **Minimalism:**
   - Apply `oracle-review` skill:
     - `change_summary`: description of the slice
     - `added_lines`: from `git diff --stat`
     - `removed_lines`: from `git diff --stat`
     - `file_count`: count of changed files
   - Record any over-engineering flags.

5. **File Scope:**
   - Apply `scope-drift-control` skill:
     - `planned_files`: from task contract
     - `actual_files`: from `git diff --name-only`
     - `allowed_slack`: 1
   - Flag any unapproved files.

**Output of Identification:**
```yaml
revision_needed:
  task_ref: <task contract ID>
  slice_ref: <slice identifier>
  timestamp: <ISO-8601>
  issues:
    - issue_id: <unique identifier>
      issue: <specific description of what's wrong>
      severity: <critical|major|minor>
      category: <scope|test|aop|minimalism|file|approach|quality>
      evidence: <specific evidence of the issue>
      recommendation: <concrete, actionable fix>
      check_tool: <which tool detected it>
```

---

### 2. Determine Revision Scope

Classify the revision into one of three scopes:

#### Minor Revision
- **Definition:** Small fixes that do not change the scope or architecture.
- **Examples:** Fix type errors, add missing tests, adjust variable naming, fix formatting, add missing docstrings.
- **Who Does It:** Same builder agent.
- **Budget:** No scope drift budget consumed (fixes are within contract).
- **PM Action:** Send back with specific checklist. No PM review required before re-submission.

#### Major Revision
- **Definition:** Changes that affect scope or require architectural adjustments, but the fundamental approach is correct.
- **Examples:** Refactor to use a different pattern within the same approach, add error handling that was overlooked, split a function that grew too large, adjust API signatures.
- **Who Does It:** Same builder agent, but PM reviews the plan before builder proceeds.
- **Budget:** May consume up to 2% of scope drift budget.
- **PM Action:** Review the revision plan with builder. Update slice contract if needed. Set a scope drift budget for the revision.

#### Critical Revision
- **Definition:** The fundamental approach is wrong or the task was misunderstood.
- **Examples:** Builder implemented REST when task required GraphQL, builder used sync when async was mandated, builder touched entirely wrong subsystem.
- **Who Does It:** PM decides. May re-assign to different agent, re-scope the task, or abort.
- **Budget:** Not applicable—task contract may need rewriting.
- **PM Action:**
  - Assess whether the task contract was unclear (PM fault) or builder misunderstood (builder fault).
  - If PM fault: Re-scope task, update contract, restart slice.
  - If builder fault: Re-assign to different agent or provide extensive guidance.
  - If approach is fundamentally flawed: Consider `independent_ensemble` to explore alternatives.
  - If unresolvable: Invoke `./escalation_gate.md` or `./abort_gate.md`.

**Decision Matrix:**

| Issue Mix | Verdict | Revision Scope |
|-----------|---------|----------------|
| Only minor issues | REVISE | Minor |
| 1-2 major issues, no critical | REVISE | Major |
| ≥1 critical issue | ESCALATE | Critical |
| Mix of minor and major | REVISE | Major (address major first, then minor) |

---

### 3. Send Back for Correction

PM provides clear, specific feedback to the builder:

**Required Feedback Format:**
```yaml
revision_request:
  task_ref: <task contract ID>
  slice_ref: <slice identifier>
  revision_scope: <minor|major|critical>
  scope_drift_budget: <percentage> (0 for minor, ≤2% for major, N/A for critical)

  issues:
    - issue_id: <matches revision_needed.issue_id>
      issue: <description>
      severity: <critical|major|minor>
      what_to_change: <specific instructions>
      what_NOT_to_change: <guardrails to prevent scope creep>
      acceptance_criteria: <how PM will verify the fix>

  resources:
    - tool: <recommended tool for the fix>
      purpose: <why this tool helps>
    - document: <reference to pattern or example>

  deadline: <ISO-8601 or "none">
  max_attempts: <integer, default 2>
```

**Feedback Quality Standards:**
- Each issue must have a concrete, actionable fix (not "make it better" but "extract the retry logic into a separate function named `with_retry`").
- Each issue must include `what_NOT_to_change` to prevent the builder from introducing new scope.
- For major revisions, PM must provide a recommended approach or reference implementation.
- For critical revisions, PM must decide whether to re-scope, re-assign, or escalate BEFORE sending feedback.

---

### 4. Re-review After Revision

After builder submits revised output:

1. **Re-run Failed Checks Only:**
   - Do not re-run checks that passed previously (unless the revision could have affected them).
   - Focus on the specific issues from the `revision_request`.

2. **Verify Fixes:**
   - For each issue in `revision_request`, verify the fix using the stated `acceptance_criteria`.
   - If a fix is insufficient, document why and send back again (count against `max_attempts`).

3. **Count Attempts:**
   - Track revision attempts per slice.
   - If `max_attempts` exceeded, escalate to PM for intervention.
   - Default `max_attempts`: 2 for minor, 2 for major, 1 for critical.

4. **Proceed or Escalate:**
   - If all issues resolved → Verdict: PROCEED. Send to `oracle_review_gate`.
   - If issues persist after max attempts → Verdict: ESCALATE. PM intervenes.

---

## Output Format

Every revision gate MUST produce the following artifact:

```yaml
revision_gate:
  # Identity
  revision_id: <unique identifier>
  task_ref: <task contract reference>
  slice_ref: <slice identifier>
  timestamp: <ISO-8601>

  # Issues Found
  issues_found: <count>
  issues:
    - issue_id: <uuid>
      issue: <description>
      severity: <critical|major|minor>
      category: <scope|test|aop|minimalism|file|approach|quality>
      evidence: <specific finding>
      recommendation: <how to fix>
      check_tool: <tool that found it>

  # Verdict
  verdict: <proceed|revise|escalate>
  revision_scope: <minor|major|critical> (if revise)
  scope_drift_budget: <percentage> (if revise)

  # Revision Request (if verdict is revise)
  revision_request:
    issues:
      - issue_id: <uuid>
        what_to_change: <specific instructions>
        what_NOT_to_change: <guardrails>
        acceptance_criteria: <verification method>
    resources:
      - tool: <name>
        purpose: <description>
    deadline: <ISO-8601>
    max_attempts: <integer>

  # Attempt Tracking
  attempt_number: <integer>
  max_attempts: <integer>
  attempts_remaining: <integer>

  # Next Action
  next_action: <send_to_oracle|send_back_to_builder|escalate_to_pm|abort>
  next_action_rationale: <why>
```

**Persistence:**
- Save revision gate artifact via `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "knowledge_capture"`) with key `revision_gate_<task_ref>_<slice_ref>`.
- If `verdict: proceed`, also update the slice status in the pipeline tracker.
- If `verdict: escalate`, invoke `./escalation_gate.md` or `./abort_gate.md` as appropriate.

---

## Tool References

| Tool | Purpose | When to Invoke |
|------|---------|----------------|
| PM task contract review | Validate scope alignment | Step 1: Scope alignment |
| `run_command` with test runner | Verify test evidence | Step 1: Test evidence |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="graph_query")` | Detect architectural conflicts | Step 1: AOP consistency |
| `oracle-review` skill | Flag over-engineering | Step 1: Minimalism |
| `scope-drift-control` skill | Detect unapproved files | Step 1: File scope |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="handoff_read")` | Load task contract | Step 1: Scope alignment |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="vault_read")` | Load project patterns | Step 1: AOP consistency |
| `rg` | Check for documentation | Step 1: Quality |
| `view_file` | Inspect changed files | Step 1: All checks |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="knowledge_capture")` | Persist revision gate output | After every gate run |

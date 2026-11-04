# Release Gate

## Purpose
Final gate before shipping. Verify the diff matches the task contract, all validation passed, and no secrets or surprises are present. This gate is the last line of defense against shipping bad code.

## Release Decision Tree

```
Oracle review passed (PASS or CONDITIONAL with all conditions resolved)
    │
    ▼
Run release gate checklist (Section 1-5)
    │
    ▼
Did ALL checks pass?
    │
    ├── YES → Verdict: SHIP (Section 6)
    │
    └── NO → Are issues minor and fixable quickly?
                │
                ├── YES → Verdict: HOLD (Section 6)
                │           └── Fix issues → Re-run release gate
                │
                └── NO → Verdict: BLOCK (Section 6)
                            └── Fix issues → Re-run from revision_gate or abort
```

## Checklist

### 1. Diff Matches Task Contract

**Objective:** Ensure the shipped code only contains what was approved.

**Actions:**
1. Verify file scope against `allowed_files`:
   - `planned_files`: list of files from the Story Shard / task contract
   - `actual_files`: list of files in the final diff (`git diff --name-only`)
   - `allowed_slack`: 1
2. Review surgical diff (`~/.gemini/antigravity/scripts/clean-diff.sh`) against the 4-Angle Anti-Bloat Diff Review:
   - `added_lines` / `removed_lines`: count from `git diff --stat`
   - `file_count`: count of files in diff
   - `tests`: list of test files that cover the change
3. Verify scope drift is within budget (<=5%):
   - Calculate: `(actual_files - planned_files) / planned_files * 100`
   - If drift >5%, investigate and either remove unapproved files or update the task contract.

**Pass Criteria:**
- All planned files are present in the diff.
- No unapproved files are in the diff (within `allowed_slack`).
- Scope drift <=5%.
- Surgical diff review does not flag over-engineering.

**Fail Actions:**
- If unapproved files found -> Remove them or escalate.
- If scope drift >5% -> Invoke `./abort_gate.md` or re-scope.

---

### 2. Validation Passed

**Objective:** Confirm the code works correctly and cleanly.

**Actions:**
1. **Run All Required Tests:**
   ```bash
   # Python example
   pytest --tb=short -q
   ```
   - All tests MUST pass (0 failures).
   - Test coverage for changed files SHOULD be >=80% (or match project standard).

2. **Run Compiler / Type Diagnostics:**
   - Run the typechecker or compiler (`tsc --noEmit`, `py_compile`, `cargo check`) on changed files.
   - Zero errors in changed files.
   - Warnings in changed files SHOULD be resolved or documented.

3. **Run AOP & Invariant Consistency Check:**
   - Query `codex_knowledge` (`ToolName: "graph_query"`) and apply `../../skills/oracle-review/SKILL.md`:
     - `claims`: list of architectural claims from the diff
     - `rules`: project-specific rules from memory or vault
   - Result MUST be pass (0 critical conflicts).

4. **Run Architectural & Automated Gate Verification (for non-trivial changes):**
   - If the change is >200 lines or touches >3 domains, apply `../../skills/senior-architect/SKILL.md` / `../../skills/auto-verification-harness/SKILL.md` (scaffolded via `ensure-verification-gates.py`: `bash scripts/verification/verify-oracle.sh` and `bash scripts/verification/test-3-round-loop.sh`) and store validated outcome via `codex_knowledge` (`ToolName: "memory_store"`):
     - `goal`: verify the change meets its stated goal
     - `constraints`: ["must not break existing tests", "must follow project patterns"]
   - Execute the verification program and verify results.

**Pass Criteria:**
- Tests: 0 failures.
- Type Diagnostics: 0 errors in changed files.
- AOP: pass.
- Architectural verification (`codex_knowledge` & `codegraph`): pass (if applicable).

**Fail Actions:**
- If tests fail -> Return to builder for fixes.
- If type errors -> Return to builder for fixes.
- If AOP fails -> Return to Oracle for architectural review.
- If architectural verification fails -> Re-evaluate the approach.

---

### 3. No Secrets

**Objective:** Prevent accidental commit of sensitive data.

**Actions:**
1. **Scan for API Keys and Tokens:**
   ```bash
   rg -n -m 50 '(API_KEY|SECRET|PASSWORD|TOKEN|ACCESS_KEY|PRIVATE_KEY)' -g '*.{py,js,ts,json,yaml,yml,env,sh}' .
   ```
2. **Scan for Certificates and Keys:**
   ```bash
   rg -n -m 50 'BEGIN (PRIVATE KEY|RSA PRIVATE KEY|EC PRIVATE KEY|OPENSSH PRIVATE KEY|CERTIFICATE)' -g '*.{pem,key,crt,cer,pub}' .
   ```
3. **Scan for Hardcoded URLs with Credentials:**
   ```bash
   rg -n -m 50 'https?://[^:]+:[^@]+@' -g '*.{py,js,ts,json,yaml,yml,sh}' .
   ```
4. **Check `.env` Files:**
   - Ensure `.env` files are in `.gitignore`.
   - Ensure no `.env` files are staged for commit.
   ```bash
   git diff --cached --name-only | rg -m 50 '\.env'
   ```
5. **Check for Hardcoded Credentials:**
   ```bash
   rg -n -m 50 '(admin|root|password|passwd|pwd)\s*[=:]\s*["\x27][^"\x27]+["\x27]' -g '*.{py,js,ts,json,yaml,yml}' .
   ```

**Pass Criteria:**
- 0 secret patterns found in the diff.
- No `.env` files in the staged changes.
- No hardcoded credentials.

**Fail Actions:**
- If secrets found → **BLOCK** immediately.
- Rotate any exposed credentials.
- Remove secrets from history (if already committed).
- Escalate to user and security team.

---

### 4. No Dependency Surprises

**Objective:** Ensure dependencies are expected, pinned, and secure.

**Actions:**
1. **Identify New Dependencies:**
   - Compare `requirements.txt`, `package.json`, `Cargo.toml`, etc. against the task contract.
   - Use `run_command` with `git diff` to find added dependencies.

2. **Verify Dependency Approval:**
   - Check if new dependencies were listed in the task contract.
   - If not, check if they were approved via `../independent_ensemble/merge_policy.md` or escalation.

3. **Check Version Pinning:**
   - All new dependencies MUST have pinned versions or exact semver.
   - Example: `fastapi==0.110.0` (good), `fastapi>=0.110.0` (bad for reproducibility).

4. **Check for Known Vulnerabilities:**
   - Run dependency vulnerability scanner:
     ```bash
     # Python example
     safety check -r requirements.txt
     # Node example
     npm audit --audit-level=moderate
     ```
   - If scanner is unavailable, manually check critical dependencies on CVE databases.

**Pass Criteria:**
- All new dependencies are approved.
- All versions are pinned.
- 0 known vulnerabilities in new dependencies.

**Fail Actions:**
- If unapproved dependencies → Remove or escalate.
- If unpinned versions → Pin them.
- If vulnerabilities found → Update to patched version or select alternative.

---

### 5. Oracle Ran

**Objective:** Confirm Oracle review was completed and passed.

**Actions:**
1. Load Oracle review artifact:
   - `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "knowledge_capture"`) with key `oracle_review_<task_ref>`.
   - Or `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "handoff_checkpoint"`) with `trace_class`: "oracle_review".

2. Verify verdict:
   - Verdict MUST be `PASS` or `CONDITIONAL`.
   - If `CONDITIONAL`, verify ALL conditions were resolved.
   - Check for unresolved conditions in `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "settings_review_queue"`).

3. Verify review completeness:
   - All dimensions scored (correctness, scope, minimalism, AOP, tests, security).
   - No dimension scored below 5/10.

**Pass Criteria:**
- Oracle review artifact exists.
- Verdict is `PASS` or resolved `CONDITIONAL`.
- All dimensions scored ≥5/10.

**Fail Actions:**
- If Oracle review missing → Run `oracle_review_gate`.
- If verdict is `FAIL` → Return to builder for major revision.
- If conditions unresolved → Resolve them before release.

---

## Verdict

| Verdict | Condition | Next Action |
|---------|-----------|-------------|
| **SHIP** | All checks pass, Oracle approved, no secrets, no blockers | Ship the diff. Record in `call_mcp_tool(ServerName="codex_knowledge", ToolName="handoff_checkpoint")`. Update project index. |
| **HOLD** | Minor issues found (e.g., unpinned dependency, LSP warning in changed file) | Fix issues. Re-run release gate. Max 2 hold cycles before escalating. |
| **BLOCK** | Critical issues found (secrets, vulnerabilities, Oracle FAIL, unapproved files) | Do NOT ship. Fix issues or invoke `./abort_gate.md`. Record blockers. |

---

## Output Format

Every release gate MUST produce the following artifact:

```yaml
release_gate:
  # Identity
  release_id: <unique identifier>
  task_ref: <task contract reference>
  timestamp: <ISO-8601>

  # Check 1: Diff Matches Contract
  diff_matches_contract:
    planned_files: <count>
    actual_files: <count>
    unapproved_files: <list or none>
    scope_drift_percent: <percentage>
    minimalist_review: <pass|fail>

  # Check 2: Validation
  validation_passed:
    tests:
      passing: <count>
      failing: <count>
      coverage_percent: <percentage>
    lsp_diagnostics:
      errors: <count>
      warnings: <count>
    aop_consistency: <pass|fail>
    architectural_verification: <pass|fail|not_applicable>

  # Check 3: Secrets
  secrets_found: <count>
  secret_details:
    - file: <path>
      pattern: <what was found>
      severity: <critical|major>
    # Use "none" if no secrets

  # Check 4: Dependencies
  dependency_surprises: <count>
  new_dependencies:
    - name: <dependency>
      version: <pinned version>
      approved: <true|false>
      vulnerabilities: <count>
    # Use "none" if no new dependencies

  # Check 5: Oracle
  oracle_verdict: <PASS|CONDITIONAL|FAIL>
  oracle_review_ref: <artifact reference>
  conditions_resolved: <true|false|not_applicable>

  # Verdict
  verdict: <SHIP|HOLD|BLOCK>
  blockers:
    - blocker: <description>
      check: <which check failed>
      severity: <critical|major|minor>
    # Use "none" if no blockers

  # Next Action
  next_action: <ship|fix_and_rerun|escalate|abort>
  next_action_rationale: <why this action was chosen>
```

**Persistence:**
- Save release gate artifact to `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "knowledge_capture"`) with key `release_gate_<task_ref>`.
- If `verdict: SHIP`, also record in `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "handoff_checkpoint"`):
  - `trace_class`: "release"
  - `title`: "Task shipped: <task_ref>"
  - `payload`: { `release_id`, `task_ref`, `verdict` }
- Update project index: `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "project_index"`).

---

## Tool References

| Tool | Purpose | Check |
|------|---------|-------|
| `scope-drift-control` skill | Compare planned vs. actual files | Diff matches contract |
| `oracle-review` skill | Score minimalism and invariants | Diff matches contract |
| `run_command` with `git diff --name-only`, `git diff --stat` | Generate diff statistics | Diff matches contract |
| `run_command` with test runner | Run full test suite | Validation |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="graph_query")` | Architectural consistency | Validation |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="memory_store")` | Non-trivial change verification | Validation |
| `rg` | Secret pattern scanning | No secrets |
| `run_command` with `safety check` / `npm audit` | Dependency vulnerability scan | No dependency surprises |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="knowledge_capture")` | Load Oracle review | Oracle ran |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="settings_review_queue")` | Check unresolved conditions | Oracle ran |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="handoff_checkpoint")` | Audit trail | All verdicts |

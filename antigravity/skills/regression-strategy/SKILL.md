---
name: regression-strategy
description: Risk-based test selection skill for choosing the right regression set after a change.
---

# Regression Strategy & TDD Regression Locking

## When to Use
- When selecting the exact regression test suite for a PR, bug fix, or release candidate.
- When locking a bug fix or new behavior with Red-Green-Refactor TDD.
- When mapping blast radius across callers and verifying test effectiveness via diff-scoped mutation probing.

> [!IMPORTANT]
> **Red-Green-Refactor Regression Locking (`obra/superpowers` — `test-driven-development`)**:
> For every bug fix or behavior change, enforce the strict 3-step TDD cycle:
> 1. **RED (Write Failing Regression Test)**: Write a minimal test that reproduces the bug or asserts the new requirement, run it, and watch it fail for the expected reason.
> 2. **GREEN (Minimal Surgical Fix)**: Write the smallest production code change that makes the failing test pass (`Fix-The-Code-Not-The-Test` — never weaken assertions).
> 3. **REFACTOR & MUTATION PROBE**: Clean up duplication while keeping all affected tests green, then verify the test actually catches regressions via `run-compiled-qc.py --mutation-probe`.

---

## Process

### 1. Blast-Radius Mapping (`codegraph:impact_analysis`)
Query the AST call graph in a single turn to identify all downstream callers and candidate test files impacted by the modified paths and symbols:
```json
{
  "ServerName": "codegraph",
  "ToolName": "impact_analysis",
  "Arguments": {
    "root": "/path/to/project",
    "changed_paths": ["src/path/to/modified_file.py"],
    "symbols": ["<modified_function_or_class>"],
    "limit": 60
  }
}
```

### 2. Automated Affected Test Selection (`select-affected-tests.py`)
Map git diffs and AST callers to runnable test suites automatically:
```bash
python3 ~/.gemini/antigravity/scripts/select-affected-tests.py --workspace <path>
```

### 3. Diff-Scoped Mutation & Compiled QC Probe (`run-compiled-qc.py`)
Verify that the selected tests are not tautological or overly permissive by running the compiled QC runner with diff-scoped mutation probing:
```bash
python3 ~/.gemini/antigravity/scripts/run-compiled-qc.py --workspace <path> --mutation-probe
```

### 4. Apply Routing Thresholds (`routing-thresholds`)
- **Docs/Comment-Only (Zero Generated Artifacts)**: Targeted readback, link check, or `validate-harness-tree.py`; skip full runtime test suite unless docs drive runtime behavior.
- **Path 1 (Atomic / Quick Flow — `<= 3` files, 1 domain, no shared contract)**: Red-Green regression test + `select-affected-tests.py` + fast type/compile check (`tsc --noEmit` / `py_compile`).
- **Path 2 (Standard / Tactical — `4–10` files, shared core logic, skills, or build config)**: Full affected test suite + `run-compiled-qc.py --mutation-probe` + `verify-harness.sh` (for harness changes).
- **Path 3 (Long-Horizon / Architecture — `> 10` files, migrations, auth/security, or cross-package)**: Clean baseline check before edits, full project regression suite, `run-compiled-qc.py --mutation-probe`, and 3-round `oracle-review` gate.

---

## Selection Heuristics
- **Shared Dependency / Utility Change**: Run `codegraph:impact_analysis` and execute all transitive caller test suites.
- **UI or CSS Change**: Run unit/snapshot tests plus `frontend-qc` Anti-Slop and responsive layout verification.
- **Core Logic / Bug Fix**: Enforce Red-Green-Refactor locking (`test fails before fix -> passes after fix`) plus affected caller tests.
- **Harness / Hook / MCP Change**: Run `bash scripts/verify-harness.sh` and `python3 ~/.gemini/antigravity/scripts/validate-harness-tree.py` (must maintain 100% pass rate).

---

## Output Format
```yaml
regression_report:
  changed_files: <list>
  changed_symbols: <list>
  impact_analysis_hits: <caller & test count from codegraph:impact_analysis>
  tdd_lock:
    red_command: "<test command that failed before fix>"
    green_command: "<test command that passed after fix>"
  selected_tests: <list from select-affected-tests.py>
  mutation_probe: <pass|fail|skipped from run-compiled-qc.py --mutation-probe>
  residual_risks: <none | specific uncovered edge cases>
```

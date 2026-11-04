---
name: auto-verification-harness
description: Inspects and scaffolds out-of-process Oracle Plan Review and 3-round zero-bug verification test harnesses.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# Auto Verification Harness Skill

Ensures any workspace strictly adheres to the SOL Verification Gates:
1. **Out-of-Process Oracle Plan Review Gate** (`scripts/verification/verify-oracle.sh --plan`)
2. **Continuous Multi-Round Zero-Bug Verification Loop** (`scripts/verification/test-3-round-loop.sh`)

---

## 1. Discovery & Audit Protocol

At the beginning of any project or session, determine if the verification gates exist:

```bash
# Check if gates exist
test -f scripts/verification/verify-oracle.sh && test -f scripts/verification/test-3-round-loop.sh
```

If either script is missing, trigger autonomous scaffolding immediately.

---

## 2. Autonomous Scaffolding Command

Run the global verification scaffolder CLI:

```bash
ensure-verification-gates
# Or explicitly pass target path:
ensure-verification-gates /path/to/repo
```

The tool automatically:
- Inspects the project tech stack (Python, Node/TypeScript, Rust, C++, Go).
- Generates `scripts/verification/verify-oracle.sh` with `--plan` support, plan auto-discovery, out-of-process AI Oracle reviewer (`claude`), and fallback deterministic checks.
- Generates `scripts/verification/test-3-round-loop.sh` tailored to the stack, requiring 3 consecutive passes with 0 defects before completion.
- Injects npm scripts (`gate:oracle`, `gate:oracle:plan`, `gate:3-round`) if `package.json` exists.
- Injects verification contracts into `AGENTS.md` and `docs/STATUS.md` if present.
- Sets execute permissions (`chmod +x`).

---

## 3. Mandatory Execution Lifecycle

### Phase A: Planning Gate (Pre-Execution)
When `implementation_plan.md` is authored or modified, the agent MUST run:
```bash
bash scripts/verification/verify-oracle.sh --plan
```
Ensure the output terminates with:
`ORACLE REVIEW GATEWAY SIGN-OFF: APPROVED`
before presenting the plan to the user for approval.

### Phase B: Post-Implementation Continuous Verification
After implementing changes and passing local tests, the agent MUST run:
```bash
bash scripts/verification/test-3-round-loop.sh
```
Verify that the output achieves:
`★★★ SUCCESS: 3 CONSECUTIVE ROUNDS PASSED WITH ZERO DEFECTS! ★★★`
If any gate breaks during any round, the streak resets to 0. The task is only complete when 3 consecutive clean rounds pass.

---

## 4. Structured Validation Formatting (Log Compression Standard)

When executing and reporting test runner outputs:
- **Zero Full-Log Pasting**: Never dump > 20 lines of raw command output into chat context.
- **Pass/Fail Compression**: Summarize aggregate metrics (total tests, passed, failed, duration).
- **Actionable Failure Triples**: For each failure, isolate `(test_name_or_file_line, error_message_summary, concrete_fix_directive)`.
- **Structured Schema**:
```yaml
validation:
  command: <command run>
  total: <count>
  passed: <count>
  failed: <count>
  failures:
    - test: <test name or file:line>
      error: <concise error message>
      fix: <remedy suggestion>
  summary: <one-line summary>
```

---

## 5. Specification-First Blind Test Synthesis & Diff-Scoped Mutation Hardening

Out-of-process verification enforces that test suites cannot collude with candidate implementations:

1. **Blinded Test Synthesis**: Tests are synthesized directly from specification contracts, acceptance criteria, and edge boundary invariants prior to inspecting or executing builder modifications.
2. **Diff-Scoped Mutation Hardening**: Validate verification suite sensitivity by injecting targeted mutant perturbations into the modified code paths:
   ```bash
   python3 antigravity/scripts/run-compiled-qc.py --mutation-probe <file> --test-cmd "<cmd>" --strict-mutation
   ```
   - **Mutation Kill Rate**: A robust verification gate must detect and kill synthetic logic/syntax mutations within diff boundaries.
   - **Zero Collusion**: If a mutated implementation passes all assertions, the verification suite is rejected as non-sensitive or colluding, requiring immediate assertion tightening under Oracle custody rules.

---

## 6. DevSecOps Sandboxed Verification & Fail-Closed PR Diff Gates (`google/mantis` + `google/nsjail`)

When running untrusted reproducers, mutation probes, or automated PR verification gates, enforce these four DevSecOps runtime invariants:

1. **gVisor (`runsc`) & `google/nsjail` Sandbox Preflight (`gvisor_env.py`)**:
   - **Container Tier (`runsc`)**: Verify `docker info` / `podman info` for the `runsc` (gVisor) runtime and execute untrusted test harnesses with `--runtime=runsc --network=none --read-only --cap-drop=ALL`, mounting only an isolated scratch workspace writable.
   - **Host-Local Tier (`nsjail`)**: When container daemons are unavailable, run preflight for `nsjail` (`command -v nsjail`) with isolated user/PID/mount/net namespaces (`--disable_clone_newnet=false`), cgroup v2 limits, `rlimit` caps (`--rlimit_as`, `--rlimit_cpu`, `--rlimit_fsize`, `--rlimit_nofile`), and a Kafel `seccomp-bpf` policy.
   - **Fail-Closed Preflight**: If neither sandbox tier can enforce networklessness and filesystem write isolation, abort target-controlled execution immediately rather than falling back to unsandboxed host execution.

2. **Pure-Python Unified Diff Fallback (`patch_fallback.py`)**:
   - Slim, scratch, or distroless verification containers frequently lack `patch(1)` or `git apply`.
   - Provide a zero-dependency Python 3 stdlib unified-diff applier (`patch_fallback.py`) that parses `--- a/<path>`, `+++ b/<path>`, and `@@ -l,s +l,s @@` hunks, verifies context lines strictly against target files, rejects path traversal (`..` or absolute paths) and symlinks (`O_NOFOLLOW`), and atomically writes patched files in memory/temp before rename.

3. **Fail-Closed PR Diff Verification Gate (`pr_scan.py`)**:
   - **PR Checkout as Read-Only DATA**: Treat the pull request worktree strictly as untrusted read-only data. Never execute scripts, hooks, build plugins, or `.env` files from the PR branch on the host or privileged runner.
   - **Unscanned File Floor (`REVIEW`)**: Track coverage across every modified file in `git diff --name-only <base>...<head>`. If any changed file is skipped, truncated, or times out during analysis, floor the overall gate verdict at `REVIEW` (never `APPROVE` / `PASS`).
   - **Deterministic Setup Failure Exit (`3`)**: Distinguish infrastructure/sandbox/checkout setup errors (exit code `3`) from clean pass (`0`) and verified defect/policy block (`1` or `2`) so CI pipelines fail closed on harness breakage.

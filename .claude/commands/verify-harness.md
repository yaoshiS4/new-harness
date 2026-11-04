---
description: Run the Claude Code harness verification gate (hook unit tests, MCP pytest suites, JSON/YAML integrity, housekeeping dry-run, tree validator) and report pass/fail per gate with fresh output.
allowed-tools: Bash(bash scripts/verify-claude-harness.sh *), Bash(python3 scripts/validate-claude-tree.py *), Bash(python3 -m unittest *)
---

# /verify-harness

1. `set -o pipefail; bash scripts/verify-claude-harness.sh 2>&1 | tail -n 60`
2. If a gate fails, re-run only that gate for detail:
   - hooks: `python3 -m unittest discover -s .claude/hooks/tests -p "test_*.py" -v 2>&1 | tail -n 40`
   - tree: `python3 scripts/validate-claude-tree.py --json`
   - MCP: `<server>/.venv/bin/pytest <server>/tests -q`
3. Report each gate as `[PASS]`/`[FAIL]` with the verbatim failure lines; never claim a pass without the fresh output above. Fix failures through the normal routing (hook changes are harness code: run the suite again after every edit).

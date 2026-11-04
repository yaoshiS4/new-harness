#!/usr/bin/env bash
# ==============================================================================
# verify-claude-harness.sh: Verification gate for the Claude Code SOTA Harness
#   1. Hook unit tests (.claude/hooks/tests)      4. YAML integrity
#   2. MCP server pytest suites (3 local servers) 5. Housekeeping dry-run
#   3. JSON integrity (.claude, .mcp.json, cli)   6. validate-claude-tree.py (5 checks)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${1:-${REPO_ROOT}}"
MCP_SRC="${CLAUDE_HARNESS_MCP_DIR:-${REPO_ROOT}/antigravity/mcp_servers}"
STRICT_MCP="${STRICT_MCP:-0}"

cleanup_caches() {
  python3 - "${REPO_ROOT}" <<'EOF' 2>/dev/null || true
import pathlib, shutil, sys
root = pathlib.Path(sys.argv[1])
for pat in ("__pycache__", ".pytest_cache"):
    for p in root.rglob(pat):
        if p.is_dir() and ".venv" not in p.parts and "node_modules" not in p.parts:
            shutil.rmtree(p, ignore_errors=True)
for p in root.rglob("*.pyc"):
    if ".venv" not in p.parts:
        p.unlink(missing_ok=True)
EOF
}
trap cleanup_caches EXIT

echo "======================================================================"
echo " [Claude Code Harness Verification] Starting Verification Gate"
echo " Target Root: ${TARGET_DIR}"
echo "======================================================================"

TOTAL=6; PASSED=0; FAILED=0
pass() { echo "  [PASS] $1"; PASSED=$((PASSED + 1)); }
fail() { echo "  [FAIL] $1"; FAILED=$((FAILED + 1)); }

# 1. Hook unit tests --------------------------------------------------------
echo ""; echo ">>> [1/6] Running Claude Code hook unit tests..."
HOOK_TESTS="${TARGET_DIR}/.claude/hooks/tests"
[ -d "${HOOK_TESTS}" ] || HOOK_TESTS="${REPO_ROOT}/.claude/hooks/tests"
if (cd "${TARGET_DIR}" && CLAUDE_HARNESS_STATE_DIR="$(mktemp -d)" python3 -m unittest discover -s "${HOOK_TESTS}" -p "test_*.py"); then
  pass "Hook unit tests succeeded."
else
  fail "Hook unit tests failed."
fi

# 2. MCP pytest suites ------------------------------------------------------
echo ""; echo ">>> [2/6] Running MCP server pytest suites..."
run_mcp() {
  # Tests always run from the repo checkout (they locate the legacy config/hooks via parents[4]);
  # the interpreter may come from the repo venv or the installed ~/.claude/harness venv.
  local srv="$1" dir="${MCP_SRC}/$1" py=""
  if [ -x "${dir}/.venv/bin/pytest" ]; then py="${dir}/.venv/bin/pytest";
  elif [ -x "${HOME}/.claude/harness/mcp_servers/${srv}/.venv/bin/pytest" ]; then py="${HOME}/.claude/harness/mcp_servers/${srv}/.venv/bin/pytest";
  fi
  if [ -z "${py}" ]; then
    if [ "${STRICT_MCP}" = "1" ]; then echo "  [FAIL] ${srv}: no venv (run scripts/install-claude-harness.sh)"; return 1; fi
    echo "  [WARN] ${srv}: no venv found; skipping (run scripts/install-claude-harness.sh to create it)."; return 0
  fi
  local attempt=0
  while [ "${attempt}" -lt 2 ]; do
    attempt=$((attempt + 1))
    if (cd "${dir}" && "${py}" "${dir}/tests" -q -p no:cacheprovider); then echo "  [PASS] MCP server: ${srv}"; return 0; fi
    [ "${attempt}" -lt 2 ] && echo "  [RETRY] ${srv} attempt ${attempt} failed; retrying..."
  done
  echo "  [FAIL] MCP server: ${srv}"; return 1
}
MCP_FAIL=0
for srv in codegraph codex_knowledge context_health; do run_mcp "${srv}" || MCP_FAIL=1; done
if [ "${MCP_FAIL}" -eq 0 ]; then pass "MCP suites ok."; else fail "MCP suites failed."; fi

# 3. JSON integrity ---------------------------------------------------------
echo ""; echo ">>> [3/6] Validating JSON files..."
if python3 - "${TARGET_DIR}" <<'EOF'
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
skip = {".venv", "node_modules", ".pytest_cache", "__pycache__", "backups", "brain", "cache", "logs", ".git", "research_cache"}
errors, count = [], 0
targets = [root / ".mcp.json"] + list((root / ".claude").rglob("*.json")) + list((root / "antigravity-cli").rglob("*.json")) + list((root / "config").rglob("*.json")) + list((root / "antigravity" / "skills").rglob("*.json"))
for p in targets:
    if not p.is_file() or any(part in skip for part in p.parts):
        continue
    count += 1
    try:
        json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append((str(p), str(exc)))
print("  Validated %d JSON files." % count)
for path, err in errors:
    print("    - %s: %s" % (path, err))
sys.exit(1 if errors else 0)
EOF
then pass "JSON files valid."; else fail "JSON validation failed."; fi

# 4. YAML integrity ---------------------------------------------------------
echo ""; echo ">>> [4/6] Validating YAML files and agent/skill frontmatter..."
if python3 - "${TARGET_DIR}" <<'EOF'
import pathlib, re, sys
root = pathlib.Path(sys.argv[1])
try:
    import yaml
except ImportError:
    yaml = None
skip = {".venv", "node_modules", ".pytest_cache", "__pycache__", "backups", ".git"}
errors, count = [], 0
if yaml:
    for p in list(root.rglob("*.yaml")) + list(root.rglob("*.yml")):
        if any(part in skip for part in p.parts):
            continue
        count += 1
        try:
            yaml.safe_load(p.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append((str(p), str(exc)))
else:
    print("  [WARN] PyYAML not available in system python3; skipping YAML parse (frontmatter still checked).")
fm_re = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
for p in list((root / ".claude" / "agents").glob("*.md")) + list((root / ".claude" / "skills").glob("*/SKILL.md")) + list((root / ".claude" / "commands").glob("*.md")):
    count += 1
    text = p.read_text(encoding="utf-8", errors="ignore")
    m = fm_re.match(text)
    if not m:
        errors.append((str(p), "missing frontmatter"))
        continue
    if yaml:
        try:
            data = yaml.safe_load(m.group(1))
            if not isinstance(data, dict) or not data.get("description"):
                errors.append((str(p), "frontmatter lacks description"))
        except Exception as exc:
            errors.append((str(p), "frontmatter yaml: %s" % exc))
    elif "description:" not in m.group(1):
        errors.append((str(p), "frontmatter lacks description"))
print("  Validated %d YAML/frontmatter files." % count)
for path, err in errors:
    print("    - %s: %s" % (path, err))
sys.exit(1 if errors else 0)
EOF
then pass "YAML/frontmatter valid."; else fail "YAML validation failed."; fi

# 5. Housekeeping dry-run ---------------------------------------------------
echo ""; echo ">>> [5/6] Housekeeping sweeper dry-run..."
HK="${TARGET_DIR}/antigravity/scripts/housekeeping.sh"
[ -f "${HK}" ] || HK="${REPO_ROOT}/antigravity/scripts/housekeeping.sh"
if bash "${HK}" --dry-run >/dev/null 2>&1; then pass "Housekeeping dry-run ok."; else fail "Housekeeping dry-run failed."; fi

# 6. Tree validator ---------------------------------------------------------
echo ""; echo ">>> [6/6] validate-claude-tree.py..."
VT="${TARGET_DIR}/scripts/validate-claude-tree.py"
[ -f "${VT}" ] || VT="${REPO_ROOT}/scripts/validate-claude-tree.py"
if python3 "${VT}" --root "${TARGET_DIR}"; then pass "Tree invariants ok."; else fail "Tree invariants failed."; fi

echo ""; echo "======================================================================"
echo " [Claude Code Harness Verification Summary] Passed: ${PASSED}/${TOTAL}  Failed: ${FAILED}/${TOTAL}"
echo "======================================================================"
if [ "${FAILED}" -eq 0 ]; then echo ">>> ALL VERIFICATION GATES PASSED."; exit 0; fi
echo ">>> VERIFICATION GATES FAILED."; exit 1

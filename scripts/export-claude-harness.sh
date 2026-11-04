#!/usr/bin/env bash
# ==============================================================================
# export-claude-harness.sh: capture the live ~/.claude harness back into the repo
#   Copies hooks, agents, commands, output styles, harness skills, the managed
#   CLAUDE.md block, and guardrails.json from ~/.claude into .claude/, then runs
#   the verification gate. User-private settings (permissions, model) are never
#   exported.
#   Usage: bash scripts/export-claude-harness.sh [SOURCE=~/.claude]
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE="${1:-${HOME}/.claude}"
DST="${REPO_ROOT}/.claude"

echo "======================================================================"
echo " [Claude Code Harness Exporter] ${SOURCE} -> ${DST}"
echo "======================================================================"
[ -d "${SOURCE}" ] || { echo "source ${SOURCE} does not exist" >&2; exit 1; }

# Hooks (harness files only)
for f in harness_lib.py session_start.py user_prompt_submit.py pre_tool_use.py post_tool_use.py post_tool_use_failure.py subagent_start.py subagent_stop.py pre_compact.py stop.py statusline.py; do
  [ -f "${SOURCE}/hooks/${f}" ] && cp -a "${SOURCE}/hooks/${f}" "${DST}/hooks/${f}"
done
[ -d "${SOURCE}/hooks/tests" ] && rsync -a --exclude '__pycache__' "${SOURCE}/hooks/tests/" "${DST}/hooks/tests/"

# Agents / commands / output styles: only names the repo already tracks (no personal agents leak in)
for kind in agents commands output-styles; do
  if [ -d "${SOURCE}/${kind}" ]; then
    for f in "${DST}/${kind}"/*.md; do
      b="$(basename "${f}")"
      [ -f "${SOURCE}/${kind}/${b}" ] && cp -a "${SOURCE}/${kind}/${b}" "${f}"
    done
  fi
done
# Skills: only harness skill directories
if [ -d "${SOURCE}/skills" ]; then
  for d in "${DST}/skills"/*/; do
    name="$(basename "${d}")"
    if [ -d "${SOURCE}/skills/${name}" ]; then
      rsync -a --delete --exclude 'node_modules' --exclude '__pycache__' "${SOURCE}/skills/${name}/" "${d}"
    fi
  done
fi
# Managed block of CLAUDE.md
if [ -f "${SOURCE}/CLAUDE.md" ]; then
  python3 - "${SOURCE}/CLAUDE.md" "${DST}/GLOBAL_CLAUDE.md" <<'EOF'
import pathlib, re, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
m = re.search(r"<!-- BEGIN CLAUDE_HARNESS_MANAGED -->.*?<!-- END CLAUDE_HARNESS_MANAGED -->\n?", text, re.DOTALL)
if m:
    pathlib.Path(sys.argv[2]).write_text(m.group(0), encoding="utf-8")
    print("  [OK] exported managed CLAUDE.md block (%d chars)" % len(m.group(0)))
else:
    print("  [WARN] no managed block found in live CLAUDE.md; GLOBAL_CLAUDE.md left unchanged")
EOF
fi
[ -f "${SOURCE}/harness/guardrails.json" ] && cp -a "${SOURCE}/harness/guardrails.json" "${DST}/harness/guardrails.json"

# Purge caches and verify
find "${REPO_ROOT}/.claude" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
bash "${REPO_ROOT}/scripts/verify-claude-harness.sh" "${REPO_ROOT}"
echo "[SUCCESS] Live harness exported and verified."

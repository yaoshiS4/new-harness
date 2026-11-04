#!/usr/bin/env bash
# mcp-launch.sh <server>: start a local harness MCP server (codegraph | codex_knowledge | context_health)
# using the first interpreter that exists: repo venv -> ~/.claude/harness venv -> uv run (creates an env on the fly).
set -euo pipefail
SRV="${1:?usage: mcp-launch.sh <codegraph|codex_knowledge|context_health>}"
case "${SRV}" in
  codegraph) MOD="codegraph.server" ;;
  codex_knowledge) MOD="codex_knowledge.server" ;;
  context_health) MOD="context_health.server" ;;
  *) echo "unknown server ${SRV}" >&2; exit 2 ;;
esac
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)/antigravity/mcp_servers/${SRV}"
HOME_DIR="${CLAUDE_HARNESS_HOME:-${HOME}/.claude/harness}/mcp_servers/${SRV}"
for dir in "${REPO_DIR}" "${HOME_DIR}"; do
  if [ -x "${dir}/.venv/bin/python3" ]; then
    cd "${dir}" && exec "${dir}/.venv/bin/python3" -m "${MOD}"
  fi
done
if command -v uv >/dev/null 2>&1 && [ -d "${REPO_DIR}" ]; then
  cd "${REPO_DIR}" && exec uv run --python 3.12 --with pytest python -m "${MOD}"
fi
echo "No environment for ${SRV}. Run: bash scripts/install-claude-harness.sh (or uv venv --python 3.12 ${REPO_DIR}/.venv && uv pip install --python ${REPO_DIR}/.venv/bin/python3 -e ${REPO_DIR})" >&2
exit 1

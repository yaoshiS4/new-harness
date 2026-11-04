#!/usr/bin/env bash
# ==============================================================================
# install-claude-harness.sh: Idempotent installer for the Claude Code SOTA Harness
#   Deploys the repo's .claude/ harness to ~/.claude (user scope) so it is the
#   default for every project, plus the shared harness tree (scripts, skillbank,
#   guidelines, MCP servers) to ~/.claude/harness.
#
#   Usage: bash scripts/install-claude-harness.sh [TARGET=~/.claude] [--no-venv] [--no-verify]
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET="${HOME}/.claude"
DO_VENV=1; DO_VERIFY=1
for arg in "$@"; do
  case "${arg}" in
    --no-venv) DO_VENV=0 ;;
    --no-verify) DO_VERIFY=0 ;;
    --*) echo "unknown flag ${arg}" >&2; exit 2 ;;
    *) TARGET="${arg}" ;;
  esac
done
HARNESS="${TARGET}/harness"
SRC_CLAUDE="${REPO_ROOT}/.claude"

echo "======================================================================"
echo " [Claude Code Harness Installer]"
echo " Source: ${REPO_ROOT}"
echo " Target: ${TARGET}  (shared tree: ${HARNESS})"
echo "======================================================================"
command -v rsync >/dev/null 2>&1 || { echo "rsync is required" >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 1; }

# 1. Backup ------------------------------------------------------------------
TS="$(date +%Y%m%d_%H%M%S)"
BACKUP="${TARGET}/backups/claude_harness_backup_${TS}"
echo ""; echo ">>> [1/6] Backing up existing user-scope files to ${BACKUP}..."
mkdir -p "${BACKUP}"
for item in CLAUDE.md settings.json agents skills commands output-styles hooks harness; do
  if [ -e "${TARGET}/${item}" ]; then
    if [ -d "${TARGET}/${item}" ]; then
      rsync -a --exclude '.venv' --exclude '__pycache__' --exclude 'node_modules' --exclude '*.sqlite*' "${TARGET}/${item}/" "${BACKUP}/${item}/" || true
    else
      cp -a "${TARGET}/${item}" "${BACKUP}/" || true
    fi
  fi
done
ls -dt "${TARGET}/backups"/claude_harness_backup_* 2>/dev/null | tail -n +4 | while read -r old; do rm -rf "${old}"; done
echo "  [OK] Backup complete."

# 2. Sync harness components ---------------------------------------------------
echo ""; echo ">>> [2/6] Syncing hooks, agents, skills, commands, output styles..."
mkdir -p "${TARGET}/hooks" "${TARGET}/agents" "${TARGET}/skills" "${TARGET}/commands" "${TARGET}/output-styles" "${HARNESS}"
rsync -a --exclude '__pycache__' --exclude '*.pyc' --exclude 'tests' "${SRC_CLAUDE}/hooks/" "${TARGET}/hooks/"
mkdir -p "${TARGET}/hooks/tests"; rsync -a --exclude '__pycache__' "${SRC_CLAUDE}/hooks/tests/" "${TARGET}/hooks/tests/"
rsync -a "${SRC_CLAUDE}/agents/" "${TARGET}/agents/"
rsync -a --exclude 'node_modules' --exclude '__pycache__' "${SRC_CLAUDE}/skills/" "${TARGET}/skills/"
rsync -a "${SRC_CLAUDE}/commands/" "${TARGET}/commands/"
rsync -a "${SRC_CLAUDE}/output-styles/" "${TARGET}/output-styles/"
mkdir -p "${HARNESS}"
if [ ! -f "${HARNESS}/guardrails.json" ]; then cp "${SRC_CLAUDE}/harness/guardrails.json" "${HARNESS}/guardrails.json"; fi
for d in scripts skillbank guidelines guardrails contracts coordination workflows templates docs; do
  if [ -d "${REPO_ROOT}/antigravity/${d}" ]; then
    rsync -a --exclude '__pycache__' --exclude '*.pyc' --exclude '*.sqlite*' --exclude '*.db*' "${REPO_ROOT}/antigravity/${d}/" "${HARNESS}/${d}/"
  fi
done
rsync -a --exclude '__pycache__' --exclude '*.pyc' --exclude '.venv' --exclude '.pytest_cache' --exclude '*.sqlite*' --exclude '*.egg-info' "${REPO_ROOT}/antigravity/mcp_servers/" "${HARNESS}/mcp_servers/"
cp "${REPO_ROOT}/scripts/validate-claude-tree.py" "${HARNESS}/scripts/validate-claude-tree.py"
chmod +x "${TARGET}/hooks/"*.py "${HARNESS}/scripts/"*.py "${HARNESS}/scripts/"*.sh 2>/dev/null || true
echo "  [OK] Components synced."

# 3. Global contract (managed block in ~/.claude/CLAUDE.md) -------------------
echo ""; echo ">>> [3/6] Installing managed block into ${TARGET}/CLAUDE.md..."
python3 - "${SRC_CLAUDE}/GLOBAL_CLAUDE.md" "${TARGET}/CLAUDE.md" <<'EOF'
import pathlib, re, sys
src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").strip() + "\n"
dst = pathlib.Path(sys.argv[2])
begin, end = "<!-- BEGIN CLAUDE_HARNESS_MANAGED -->", "<!-- END CLAUDE_HARNESS_MANAGED -->"
existing = dst.read_text(encoding="utf-8") if dst.is_file() else ""
pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end) + r"\n?", re.DOTALL)
if pattern.search(existing):
    merged = pattern.sub(lambda m: src, existing)
else:
    merged = (src + "\n" + existing.lstrip("\n")) if existing.strip() else src
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_text(merged, encoding="utf-8")
print("  [OK] %s (%d chars managed block)" % (dst, len(src)))
EOF

# 4. settings.json merge --------------------------------------------------------
echo ""; echo ">>> [4/6] Merging hooks, statusLine, and env into ${TARGET}/settings.json..."
python3 - "${SRC_CLAUDE}/settings.json" "${TARGET}/settings.json" "${TARGET}" <<'EOF'
import json, os, pathlib, re, sys
src = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
dst_path = pathlib.Path(sys.argv[2])
target = sys.argv[3]
hooks_dir = os.path.join(target, "hooks")
live = {}
if dst_path.is_file():
    try:
        live = json.loads(dst_path.read_text(encoding="utf-8"))
    except Exception:
        backup = dst_path.with_suffix(".json.invalid")
        dst_path.rename(backup)
        print("  [WARN] existing settings.json was invalid JSON; moved to %s" % backup)
        live = {}

def rewrite(cmd: str) -> str:
    # Global hooks defer to the project's own harness hooks when the project ships them (no double execution).
    cmd = cmd.replace('"${CLAUDE_PROJECT_DIR}/.claude/hooks/', '"%s/' % hooks_dir)
    script = cmd.split('/')[-1].rstrip('"')
    guard = '[ -n "${CLAUDE_PROJECT_DIR:-}" ] && [ -f "${CLAUDE_PROJECT_DIR}/.claude/hooks/%s" ] && exit 0; ' % script
    return guard + cmd

merged_hooks = dict(live.get("hooks") or {})
for event, entries in (src.get("hooks") or {}).items():
    new_entries = []
    for entry in entries:
        e = json.loads(json.dumps(entry))
        for h in e.get("hooks", []):
            h["command"] = rewrite(h["command"])
        new_entries.append(e)
    kept = [e for e in (merged_hooks.get(event) or []) if not any("claude_harness" in json.dumps(h) or hooks_dir in json.dumps(h) for h in e.get("hooks", []))]
    merged_hooks[event] = kept + new_entries
live["hooks"] = merged_hooks
sl = dict(src.get("statusLine") or {})
if sl:
    sl["command"] = re.sub(r'"\$\{CLAUDE_PROJECT_DIR[^}]*\}/\.claude/hooks/', '"%s/' % hooks_dir, sl["command"])
    live["statusLine"] = sl
env = dict(live.get("env") or {})
for k, v in (src.get("env") or {}).items():
    env.setdefault(k, v)
env["CLAUDE_HARNESS_HOME"] = os.path.join(target, "harness")
live["env"] = env
perms = dict(live.get("permissions") or {})
deny = list(perms.get("deny") or [])
for rule in (src.get("permissions") or {}).get("deny", []):
    if rule not in deny:
        deny.append(rule)
perms["deny"] = deny
live["permissions"] = perms
dst_path.parent.mkdir(parents=True, exist_ok=True)
tmp = dst_path.with_suffix(".json.tmp")
tmp.write_text(json.dumps(live, indent=2) + "\n", encoding="utf-8")
os.replace(tmp, dst_path)
print("  [OK] settings.json merged (%d hook events)." % len(merged_hooks))
EOF

# 5. MCP server venvs + registration ---------------------------------------------
echo ""; echo ">>> [5/6] MCP servers (codegraph, codex_knowledge, context_health)..."
PY_SPEC="${CLAUDE_HARNESS_PYTHON:-3.12}"
if [ "${DO_VENV}" -eq 1 ]; then
  for srv in codegraph codex_knowledge context_health; do
    dir="${HARNESS}/mcp_servers/${srv}"; venv="${dir}/.venv"
    if [ ! -x "${venv}/bin/python3" ]; then
      echo "  Creating venv for ${srv} (python ${PY_SPEC})..."
      if command -v uv >/dev/null 2>&1; then
        uv venv --python "${PY_SPEC}" "${venv}" >/dev/null
        uv pip install --python "${venv}/bin/python3" -e "${dir}" pytest anyio >/dev/null
      else
        python3 -m venv "${venv}"; "${venv}/bin/pip" install -q --upgrade pip; "${venv}/bin/pip" install -q -e "${dir}" pytest anyio
      fi
      echo "  [OK] ${srv} ready."
    else
      echo "  [OK] ${srv} venv exists."
    fi
  done
else
  echo "  [SKIP] venv creation (--no-venv)."
fi
MCP_JSON="${HARNESS}/mcp.user.json"
python3 - "${HARNESS}" "${MCP_JSON}" <<'EOF'
import json, os, sys
h, out = sys.argv[1], sys.argv[2]
cfg = {"mcpServers": {"context7": {"command": "npx", "args": ["-y", "@upstash/context7-mcp"]}}}
for srv, mod in (("codegraph", "codegraph.server"), ("codex_knowledge", "codex_knowledge.server"), ("context_health", "context_health.server")):
    d = os.path.join(h, "mcp_servers", srv)
    cfg["mcpServers"][srv] = {"command": os.path.join(d, ".venv", "bin", "python3"), "args": ["-m", mod], "cwd": d}
cfg["mcpServers"]["context_health"]["env"] = {"CODEX_BRAIN_DIR": os.path.expanduser("~/.claude/projects")}
with open(out, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2)
print("  [OK] wrote %s" % out)
EOF
if command -v claude >/dev/null 2>&1; then
  for srv in codegraph codex_knowledge context_health context7; do
    claude mcp remove -s user "${srv}" >/dev/null 2>&1 || true
    claude mcp add-json -s user "${srv}" "$(python3 -c "import json,sys; print(json.dumps(json.load(open('${MCP_JSON}'))['mcpServers']['${srv}']))")" >/dev/null 2>&1 \
      && echo "  [OK] registered MCP server '${srv}' (user scope)" || echo "  [WARN] could not register '${srv}' via claude mcp; add it manually from ${MCP_JSON}"
  done
else
  echo "  [INFO] 'claude' CLI not on PATH: register MCP servers later with"
  echo "         claude mcp add-json -s user <name> '<json from ${MCP_JSON}>'"
fi

# 6. Verify ------------------------------------------------------------------------
echo ""; echo ">>> [6/6] Verification..."
if [ "${DO_VERIFY}" -eq 1 ]; then
  bash "${REPO_ROOT}/scripts/verify-claude-harness.sh" "${REPO_ROOT}"
else
  echo "  [SKIP] verification (--no-verify)."
fi
echo ""; echo "======================================================================"
echo " [SUCCESS] Claude Code SOTA Harness installed to ${TARGET}"
echo " Backup: ${BACKUP}"
echo " Next: restart Claude Code; run /verify-harness inside any project."
echo "======================================================================"

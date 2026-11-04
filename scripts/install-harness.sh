#!/usr/bin/env bash
# ==============================================================================
# install-harness.sh: Idempotent Installer for Antigravity SOTA Harness
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${1:-${HOME}/.gemini}"

echo "======================================================================"
echo " [Antigravity Harness Installer] Deploying Harness Snapshot"
echo " Source Repository: ${REPO_ROOT}"
echo " Target Directory:  ${TARGET_DIR}"
echo "======================================================================"

# ------------------------------------------------------------------------------
# 0. Preflight Checks
# ------------------------------------------------------------------------------
if ! command -v rsync >/dev/null 2>&1; then
  echo "✗ Error: 'rsync' command not found in PATH. Please install rsync before deploying the harness." >&2
  exit 1
fi

# ------------------------------------------------------------------------------
# 1. Pre-deployment Backup of Existing Target Settings
# ------------------------------------------------------------------------------
BACKUP_TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${TARGET_DIR}/backups/harness_backup_${BACKUP_TIMESTAMP}"

if [ -d "${TARGET_DIR}" ]; then
  echo ""
  echo ">>> [1/5] Creating safety backup in ${BACKUP_DIR}..."
  mkdir -p "${BACKUP_DIR}"
  for item in config antigravity antigravity-cli GEMINI.md; do
    if [ -e "${TARGET_DIR}/${item}" ]; then
      echo "  Archiving existing ${item}..."
      if [ "${item}" = "antigravity-cli" ]; then
        mkdir -p "${BACKUP_DIR}/antigravity-cli"
        for sub in settings.json mcp builtin bin; do
          if [ -e "${TARGET_DIR}/antigravity-cli/${sub}" ]; then
            if [ -d "${TARGET_DIR}/antigravity-cli/${sub}" ]; then
              mkdir -p "${BACKUP_DIR}/antigravity-cli/${sub}"
              rsync -a \
                --exclude '.venv' \
                --exclude '__pycache__' \
                --exclude '.pytest_cache' \
                --exclude 'node_modules' \
                --exclude '*.pyc' \
                "${TARGET_DIR}/antigravity-cli/${sub}/" "${BACKUP_DIR}/antigravity-cli/${sub}/" || true
            else
              cp -a "${TARGET_DIR}/antigravity-cli/${sub}" "${BACKUP_DIR}/antigravity-cli/" || true
            fi
          fi
        done
      elif [ -d "${TARGET_DIR}/${item}" ]; then
        mkdir -p "${BACKUP_DIR}/${item}"
        rsync -a \
          --exclude '.venv' \
          --exclude '__pycache__' \
          --exclude '.pytest_cache' \
          --exclude 'node_modules' \
          --exclude '*.pyc' \
          --exclude 'docs/CONTEXT_LEDGER.md' \
          --exclude '*/docs/CONTEXT_LEDGER.md' \
          "${TARGET_DIR}/${item}/" "${BACKUP_DIR}/${item}/" || true
      else
        cp -a "${TARGET_DIR}/${item}" "${BACKUP_DIR}/" || true
      fi
    fi
  done

  # Also back up ~/.local/bin files and ~/.local/lib/agy_tui_core.py that will be overwritten
  mkdir -p "${BACKUP_DIR}/local_bin" "${BACKUP_DIR}/local_lib"
  if [ -d "${REPO_ROOT}/bin" ]; then
    for f in "${REPO_ROOT}/bin/"*; do
      bname="$(basename "$f")"
      if [ -e "${HOME}/.local/bin/${bname}" ]; then
        cp -a "${HOME}/.local/bin/${bname}" "${BACKUP_DIR}/local_bin/" || true
      fi
    done
  fi
  if [ -e "${HOME}/.local/lib/agy_tui_core.py" ]; then
    cp -a "${HOME}/.local/lib/agy_tui_core.py" "${BACKUP_DIR}/local_lib/" || true
  fi

  # Rotate backups: keep newest 3
  echo "  Rotating backups: keeping newest 3..."
  ls -dt "${TARGET_DIR}/backups"/harness_backup_* 2>/dev/null | tail -n +4 | while read -r old_bk; do
    [ -e "$old_bk" ] && rm -rf "$old_bk"
  done
  echo "  [OK] Safety backup completed."
else
  echo ""
  echo ">>> [1/5] Target directory ${TARGET_DIR} does not exist yet. Initializing."
  mkdir -p "${TARGET_DIR}"
fi

# ------------------------------------------------------------------------------
# 2. Synchronize Configurations & Assets
# ------------------------------------------------------------------------------
echo ""
echo ">>> [2/5] Synchronizing harness components..."

mkdir -p "${TARGET_DIR}/config"
mkdir -p "${TARGET_DIR}/config/skills"
mkdir -p "${TARGET_DIR}/antigravity"
mkdir -p "${TARGET_DIR}/antigravity-cli"

# Sync antigravity/ FIRST (before config/ and Priority #3 skill symlink promotion)
echo "  Deploying antigravity/ -> ${TARGET_DIR}/antigravity/..."
rsync -av \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.venv' \
  --exclude '.pytest_cache' \
  --exclude '*.sqlite*' \
  --exclude '*.db*' \
  --exclude 'docs/CONTEXT_LEDGER.md' \
  --exclude '*/docs/CONTEXT_LEDGER.md' \
  "${REPO_ROOT}/antigravity/" "${TARGET_DIR}/antigravity/"

# Remove stale antigravity/AGENTS.md so hierarchical AGENTS.md scanner never double-loads global rules
rm -f "${TARGET_DIR}/antigravity/AGENTS.md"

# Sync config/ (protecting live JetboxWriteState config.json, sidecars, .migrated, projects, and skills/*)
echo "  Deploying config/ -> ${TARGET_DIR}/config/..."
rsync -av --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '/config.json' \
  --exclude '/sidecars' \
  --exclude '/.migrated' \
  --exclude '/projects' \
  --filter='P /skills/*' \
  "${REPO_ROOT}/config/" "${TARGET_DIR}/config/"

# Non-destructively merge config/config.json at 0600 (preserving live JetboxWriteState userSettings & grants)
python3 - <<EOF
import json, os, pathlib, tempfile

repo_cfg_path = pathlib.Path("${REPO_ROOT}").resolve() / "config" / "config.json"
target_cfg_path = pathlib.Path("${TARGET_DIR}").resolve() / "config" / "config.json"

repo_cfg = {}
if repo_cfg_path.is_file():
    try:
        repo_cfg = json.loads(repo_cfg_path.read_text(encoding="utf-8"))
    except Exception:
        repo_cfg = {}

live_cfg = {}
if target_cfg_path.is_file():
    try:
        live_cfg = json.loads(target_cfg_path.read_text(encoding="utf-8"))
    except Exception:
        live_cfg = {}

merged = dict(live_cfg)
merged_plugins = dict(merged.get("plugins") or {}) if isinstance(merged.get("plugins"), dict) else {}
repo_plugins = repo_cfg.get("plugins") or {}
if isinstance(repo_plugins, dict):
    for p_key, p_val in repo_plugins.items():
        if p_key not in merged_plugins:
            merged_plugins[p_key] = p_val if isinstance(p_val, dict) else {"enabled": False}
merged["plugins"] = merged_plugins

target_cfg_path.parent.mkdir(parents=True, exist_ok=True)
fd, tmp_path = tempfile.mkstemp(dir=str(target_cfg_path.parent), prefix=".config.json.")
try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
        f.write("\n")
    os.chmod(tmp_path, 0o600)
    os.replace(tmp_path, target_cfg_path)
    os.chmod(target_cfg_path, 0o600)
except Exception:
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)
    raise
EOF

# Promote core skills in antigravity/skills/* to Priority #3 (config/skills/<name>) via ln -sfn and prune broken links
if [ -d "${TARGET_DIR}/antigravity/skills" ]; then
  echo "  Promoting antigravity/skills/* -> ${TARGET_DIR}/config/skills/ (Priority #3)..."
  for skill_dir in "${TARGET_DIR}/antigravity/skills"/*; do
    if [ -d "${skill_dir}" ]; then
      skill_name="$(basename "${skill_dir}")"
      ln -sfn "${skill_dir}" "${TARGET_DIR}/config/skills/${skill_name}"
    fi
  done
fi
for entry in "${TARGET_DIR}/config/skills"/*; do
  if [ -L "${entry}" ] && [ ! -e "${entry}" ]; then
    rm -f "${entry}"
  fi
done

# Dynamically adjust paths in config JSON files for portability
python3 - <<EOF
import pathlib

target_dir = pathlib.Path("${TARGET_DIR}").resolve()
home_dir = pathlib.Path("${HOME}").resolve()

json_targets = [
    target_dir / "config" / conf_name
    for conf_name in ["hooks.json", "skills.json", "mcp_config.json"]
]
plugins_dir = target_dir / "config" / "plugins"
if plugins_dir.is_dir():
    json_targets.extend(plugins_dir.glob("*/*.json"))
    json_targets.extend(plugins_dir.rglob("*.json"))

seen = set()
for conf_path in json_targets:
    if conf_path in seen or not conf_path.exists():
        continue
    seen.add(conf_path)
    content = conf_path.read_text(encoding="utf-8")
    content = content.replace("/home/heocop/.gemini", str(target_dir))
    content = content.replace("/home/heocop", str(home_dir))
    conf_path.write_text(content, encoding="utf-8")
EOF

# Sync antigravity-cli/ and MCP tool schemas (including browseros-neo/ and context_health/)
echo "  Deploying antigravity-cli/ -> ${TARGET_DIR}/antigravity-cli/..."
mkdir -p "${TARGET_DIR}/antigravity-cli/mcp"
rsync -av \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  "${REPO_ROOT}/antigravity-cli/" "${TARGET_DIR}/antigravity-cli/"

if [ -d "${REPO_ROOT}/antigravity-cli/mcp/browseros-neo" ]; then
  echo "  Deploying browseros-neo MCP schemas -> ${TARGET_DIR}/antigravity-cli/mcp/browseros-neo/..."
  mkdir -p "${TARGET_DIR}/antigravity-cli/mcp/browseros-neo"
  rsync -av \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    "${REPO_ROOT}/antigravity-cli/mcp/browseros-neo/" "${TARGET_DIR}/antigravity-cli/mcp/browseros-neo/"
fi

# Deploy TUI binaries and helper libraries
if [ -d "${REPO_ROOT}/bin" ]; then
  echo "  Deploying bin/* -> ${HOME}/.local/bin/..."
  mkdir -p "${HOME}/.local/bin"
  for f in "${REPO_ROOT}/bin/"*; do
    if [ -f "$f" ]; then
      cp -a "$f" "${HOME}/.local/bin/"
      chmod +x "${HOME}/.local/bin/$(basename "$f")" || true
    fi
  done
fi

if [ -f "${REPO_ROOT}/lib/agy_tui_core.py" ]; then
  echo "  Deploying lib/agy_tui_core.py -> ${HOME}/.local/lib/agy_tui_core.py..."
  mkdir -p "${HOME}/.local/lib"
  cp -a "${REPO_ROOT}/lib/agy_tui_core.py" "${HOME}/.local/lib/agy_tui_core.py"
fi

# Ensure executable permissions on hooks and scripts
chmod +x "${TARGET_DIR}/config/hooks/"*.py "${TARGET_DIR}/config/hooks/"*.sh || true
chmod +x "${TARGET_DIR}/config/scripts/"*.sh || true
chmod +x "${TARGET_DIR}/antigravity/scripts/"*.sh "${TARGET_DIR}/antigravity/scripts/"*.py || true

# ------------------------------------------------------------------------------
# 3. Create Canonical Symlinks
# ------------------------------------------------------------------------------
echo ""
echo ">>> [3/5] Setting up canonical symlinks..."
ln -sfn "${TARGET_DIR}/antigravity/GLOBAL_AGENTS.md" "${TARGET_DIR}/GEMINI.md"
echo "  Linked ${TARGET_DIR}/GEMINI.md -> ${TARGET_DIR}/antigravity/GLOBAL_AGENTS.md"

# ------------------------------------------------------------------------------
# 4. Set Up Python Virtual Environments for MCP Servers
# ------------------------------------------------------------------------------
echo ""
echo ">>> [4/5] Checking MCP server virtual environments..."
MCP_SERVERS=("codegraph" "codex_knowledge" "context_health")

for srv in "${MCP_SERVERS[@]}"; do
  srv_path="${TARGET_DIR}/antigravity/mcp_servers/${srv}"
  venv_path="${srv_path}/.venv"

  if [ ! -d "${venv_path}" ]; then
    echo "  Creating virtualenv for ${srv} at ${venv_path}..."
    if command -v uv >/dev/null 2>&1; then
      uv venv "${venv_path}"
      echo "  Installing dependencies for ${srv} via uv..."
      uv pip install --python "${venv_path}" -e "${srv_path}" pytest anyio
    else
      echo "  uv not found; falling back to python3 -m venv..."
      python3 -m venv "${venv_path}"
      "${venv_path}/bin/pip" install --upgrade pip
      "${venv_path}/bin/pip" install -e "${srv_path}" pytest anyio
    fi
    echo "  [OK] ${srv} environment ready."
  else
    echo "  [OK] Virtualenv already exists for ${srv}."
  fi
done

# ------------------------------------------------------------------------------
# 5. Execute Comprehensive Verification Gate
# ------------------------------------------------------------------------------
echo ""
echo ">>> [5/5] Executing post-installation verification gate..."
bash "${REPO_ROOT}/scripts/verify-harness.sh" "${TARGET_DIR}"

echo ""
echo "======================================================================"
echo " [SUCCESS] Antigravity SOTA Harness Successfully Deployed & Verified!"
echo " Target Root: ${TARGET_DIR}"
echo " Backup Dir:  ${BACKUP_DIR}"
echo "======================================================================"

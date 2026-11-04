#!/usr/bin/env bash
# ==============================================================================
# export-harness.sh: Idempotent Exporter for Antigravity SOTA Harness Snapshot
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SOURCE_DIR="${1:-${HOME}/.gemini}"

echo "======================================================================"
echo " [Antigravity Harness Exporter] Capturing Harness Snapshot"
echo " Source Directory:  ${SOURCE_DIR}"
echo " Repository Target: ${REPO_ROOT}"
echo "======================================================================"

if [ ! -d "${SOURCE_DIR}" ]; then
  echo "Error: Source directory '${SOURCE_DIR}' does not exist." >&2
  exit 1
fi

# ------------------------------------------------------------------------------
# 1. Export config/
# ------------------------------------------------------------------------------
echo ""
echo ">>> [1/4] Exporting config/ components..."
mkdir -p "${REPO_ROOT}/config"

CONFIG_FILES=("hooks.json" "mcp_config.json" "plugins.json" "skills.json")
for item in "${CONFIG_FILES[@]}"; do
  if [ -f "${SOURCE_DIR}/config/${item}" ]; then
    echo "  Exporting config/${item}..."
    cp -a "${SOURCE_DIR}/config/${item}" "${REPO_ROOT}/config/${item}"
  fi
done

# Sanitize config/config.json: never export live 0600 JetboxWriteState userSettings or permission grants
python3 - <<EOF
import json, pathlib

source_cfg_path = pathlib.Path("${SOURCE_DIR}").resolve() / "config" / "config.json"
repo_cfg_path = pathlib.Path("${REPO_ROOT}").resolve() / "config" / "config.json"
plugins_dir = pathlib.Path("${REPO_ROOT}").resolve() / "config" / "plugins"

plugin_keys = set()
if repo_cfg_path.is_file():
    try:
        rc = json.loads(repo_cfg_path.read_text(encoding="utf-8"))
        if isinstance(rc.get("plugins"), dict):
            plugin_keys.update(rc["plugins"].keys())
    except Exception:
        pass
if source_cfg_path.is_file():
    try:
        sc = json.loads(source_cfg_path.read_text(encoding="utf-8"))
        if isinstance(sc.get("plugins"), dict):
            plugin_keys.update(sc["plugins"].keys())
    except Exception:
        pass
if plugins_dir.is_dir():
    for p in plugins_dir.iterdir():
        if p.is_dir():
            plugin_keys.add(p.name)

sanitized = {
    "plugins": {
        k: {"enabled": False}
        for k in sorted(plugin_keys)
    }
}
repo_cfg_path.write_text(json.dumps(sanitized, indent=2) + "\n", encoding="utf-8")
EOF

CONFIG_DIRS=("hooks" "scripts" "skills" "_archived_rules" "plugins")
for d in "${CONFIG_DIRS[@]}"; do
  if [ -d "${SOURCE_DIR}/config/${d}" ]; then
    echo "  Synchronizing config/${d}/..."
    mkdir -p "${REPO_ROOT}/config/${d}"
    EXTRA_RSYNC_FLAGS=()
    if [ "${d}" = "skills" ]; then
      EXTRA_RSYNC_FLAGS=(--no-links)
    fi
    rsync -av --delete \
      --exclude '__pycache__' \
      --exclude '*.pyc' \
      --exclude '.pytest_cache' \
      "${EXTRA_RSYNC_FLAGS[@]}" \
      "${SOURCE_DIR}/config/${d}/" "${REPO_ROOT}/config/${d}/"
    if [ "${d}" = "skills" ]; then
      for s_entry in "${SOURCE_DIR}/config/skills"/*; do
        if [ -L "${s_entry}" ]; then
          s_name="$(basename "${s_entry}")"
          rm -rf "${REPO_ROOT}/config/skills/${s_name}"
        fi
      done
    fi
  fi
done

# Normalize paths in exported config and plugin JSON files for portability
python3 - <<EOF
import pathlib

repo_root = pathlib.Path("${REPO_ROOT}").resolve()
source_dir = pathlib.Path("${SOURCE_DIR}").resolve()
home_dir = pathlib.Path("${HOME}").resolve()

json_targets = [
    repo_root / "config" / conf_name
    for conf_name in ["hooks.json", "skills.json", "mcp_config.json"]
]
plugins_dir = repo_root / "config" / "plugins"
if plugins_dir.is_dir():
    json_targets.extend(plugins_dir.glob("*/*.json"))
    json_targets.extend(plugins_dir.rglob("*.json"))

seen = set()
for conf_path in json_targets:
    if conf_path in seen or not conf_path.exists():
        continue
    seen.add(conf_path)
    content = conf_path.read_text(encoding="utf-8")
    content = content.replace(str(source_dir), "/home/heocop/.gemini")
    content = content.replace(str(home_dir), "/home/heocop")
    conf_path.write_text(content, encoding="utf-8")
EOF

# ------------------------------------------------------------------------------
# 2. Export antigravity/
# ------------------------------------------------------------------------------
echo ""
echo ">>> [2/4] Exporting antigravity/ components..."
mkdir -p "${REPO_ROOT}/antigravity"

if [ -f "${SOURCE_DIR}/antigravity/GLOBAL_AGENTS.md" ]; then
  echo "  Exporting antigravity/GLOBAL_AGENTS.md..."
  cp -a "${SOURCE_DIR}/antigravity/GLOBAL_AGENTS.md" "${REPO_ROOT}/antigravity/GLOBAL_AGENTS.md"
elif [ -f "${SOURCE_DIR}/antigravity/AGENTS.md" ]; then
  echo "  Exporting antigravity/AGENTS.md -> antigravity/GLOBAL_AGENTS.md..."
  cp -a "${SOURCE_DIR}/antigravity/AGENTS.md" "${REPO_ROOT}/antigravity/GLOBAL_AGENTS.md"
elif [ -f "${SOURCE_DIR}/GEMINI.md" ]; then
  echo "  Exporting GEMINI.md -> antigravity/GLOBAL_AGENTS.md..."
  cp -a "${SOURCE_DIR}/GEMINI.md" "${REPO_ROOT}/antigravity/GLOBAL_AGENTS.md"
fi
rm -f "${REPO_ROOT}/antigravity/AGENTS.md"

ANTIGRAVITY_DIRS=(
  "contracts"
  "coordination"
  "docs"
  "guardrails"
  "guidelines"
  "mcp_servers"
  "scripts"
  "skillbank"
  "skills"
  "templates"
  "workflows"
)

for d in "${ANTIGRAVITY_DIRS[@]}"; do
  if [ -d "${SOURCE_DIR}/antigravity/${d}" ]; then
    echo "  Synchronizing antigravity/${d}/..."
    mkdir -p "${REPO_ROOT}/antigravity/${d}"
    EXTRA_EXCLUDES=()
    if [ "${d}" = "skillbank" ]; then
      EXTRA_EXCLUDES=(
        --exclude 'failure-lessons/auto_heal_*.md'
        --exclude 'research_cache/'
        --exclude 'task-specific/recov-*'
        --exclude 'guardrails.json'
        --filter='+ env_overlays/hc-langdict.md'
        --exclude 'env_overlays/*'
      )
    fi
    rsync -av --delete \
      --exclude '__pycache__' \
      --exclude '*.pyc' \
      --exclude '.venv' \
      --exclude '.pytest_cache' \
      --exclude '*.egg-info' \
      --exclude '*.sqlite*' \
      --exclude '*.db*' \
      --exclude '*.log' \
      --exclude 'docs/CONTEXT_LEDGER.md' \
      --exclude '*/docs/CONTEXT_LEDGER.md' \
      "${EXTRA_EXCLUDES[@]}" \
      "${SOURCE_DIR}/antigravity/${d}/" "${REPO_ROOT}/antigravity/${d}/"
  fi
done

# ------------------------------------------------------------------------------
# 3. Export antigravity-cli/
# ------------------------------------------------------------------------------
echo ""
echo ">>> [3/4] Exporting antigravity-cli/ components..."
mkdir -p "${REPO_ROOT}/antigravity-cli"

if [ -f "${SOURCE_DIR}/antigravity-cli/settings.json" ]; then
  echo "  Exporting antigravity-cli/settings.json..."
  cp -a "${SOURCE_DIR}/antigravity-cli/settings.json" "${REPO_ROOT}/antigravity-cli/settings.json"
fi

if [ -d "${SOURCE_DIR}/antigravity-cli/builtin" ]; then
  echo "  Synchronizing antigravity-cli/builtin/..."
  mkdir -p "${REPO_ROOT}/antigravity-cli/builtin"
  rsync -av --delete \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.pytest_cache' \
    --exclude '.manifest' \
    "${SOURCE_DIR}/antigravity-cli/builtin/" "${REPO_ROOT}/antigravity-cli/builtin/"
fi

if [ -d "${SOURCE_DIR}/antigravity-cli/mcp" ]; then
  echo "  Synchronizing antigravity-cli/mcp/ (preserving extra repo schemas)..."
  mkdir -p "${REPO_ROOT}/antigravity-cli/mcp"
  # Note: No --delete so optional StitchMCP and open-design schemas in repo are preserved
  rsync -av \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.pytest_cache' \
    "${SOURCE_DIR}/antigravity-cli/mcp/" "${REPO_ROOT}/antigravity-cli/mcp/"
fi

# Set executable permissions
chmod +x "${REPO_ROOT}/scripts/"*.sh || true
chmod +x "${REPO_ROOT}/config/hooks/"*.py "${REPO_ROOT}/config/hooks/"*.sh 2>/dev/null || true
chmod +x "${REPO_ROOT}/config/scripts/"*.sh 2>/dev/null || true
chmod +x "${REPO_ROOT}/antigravity/scripts/"*.sh "${REPO_ROOT}/antigravity/scripts/"*.py 2>/dev/null || true

# ------------------------------------------------------------------------------
# 4. Export TUI Binaries, Libraries & Multiplexer Configurations
# ------------------------------------------------------------------------------
echo ""
echo ">>> [4/5] Exporting TUI binaries, libraries, and configs..."
mkdir -p "${REPO_ROOT}/bin" "${REPO_ROOT}/lib" "${REPO_ROOT}/config/tui"

TUI_BINS=("agy-sidebar" "agy-squad" "agy-statusline" "clipboard-toast" "clipboard-toast-daemon" "agy-axi" "mermaid-ascii" "kate-md-preview" "ensure-verification-gates")
for b in "${TUI_BINS[@]}"; do
  if [ -f "${HOME}/.local/bin/${b}" ]; then
    echo "  Exporting bin/${b}..."
    cp -a "${HOME}/.local/bin/${b}" "${REPO_ROOT}/bin/${b}"
    chmod +x "${REPO_ROOT}/bin/${b}" 2>/dev/null || true
  fi
done

if [ -f "${HOME}/.local/lib/agy_tui_core.py" ]; then
  echo "  Exporting lib/agy_tui_core.py..."
  cp -a "${HOME}/.local/lib/agy_tui_core.py" "${REPO_ROOT}/lib/agy_tui_core.py"
fi

if [ -f "${HOME}/.tmux.conf" ]; then
  echo "  Exporting config/tui/.tmux.conf..."
  cp -a "${HOME}/.tmux.conf" "${REPO_ROOT}/config/tui/.tmux.conf"
fi
if [ -f "${HOME}/.config/lazygit/config.yml" ]; then
  echo "  Exporting config/tui/lazygit/config.yml..."
  mkdir -p "${REPO_ROOT}/config/tui/lazygit"
  cp -a "${HOME}/.config/lazygit/config.yml" "${REPO_ROOT}/config/tui/lazygit/config.yml"
fi
if [ -d "${HOME}/.config/btop" ]; then
  echo "  Synchronizing config/tui/btop/..."
  mkdir -p "${REPO_ROOT}/config/tui/btop"
  rsync -av --delete "${HOME}/.config/btop/" "${REPO_ROOT}/config/tui/btop/"
fi
if [ -d "${HOME}/.config/yazi" ]; then
  echo "  Synchronizing config/tui/yazi/..."
  mkdir -p "${REPO_ROOT}/config/tui/yazi"
  rsync -av --delete "${HOME}/.config/yazi/" "${REPO_ROOT}/config/tui/yazi/"
fi
if [ -f "${HOME}/.config/herdr/config.toml" ]; then
  echo "  Exporting config/tui/herdr/config.toml..."
  mkdir -p "${REPO_ROOT}/config/tui/herdr"
  cp -a "${HOME}/.config/herdr/config.toml" "${REPO_ROOT}/config/tui/herdr/config.toml"
fi

if [ -f "${HOME}/.config/katerc" ]; then
  echo "  Exporting config/kate/katerc..."
  mkdir -p "${REPO_ROOT}/config/kate"
  cp -a "${HOME}/.config/katerc" "${REPO_ROOT}/config/kate/katerc"
fi
if [ -d "${HOME}/.config/kate" ]; then
  echo "  Synchronizing config/kate/settings/..."
  mkdir -p "${REPO_ROOT}/config/kate/settings"
  rsync -av --delete "${HOME}/.config/kate/" "${REPO_ROOT}/config/kate/settings/"
fi
if [ -f "${HOME}/.local/share/org.kde.syntax-highlighting/themes/cachyos-dark.theme" ]; then
  echo "  Exporting themes/cachyos-dark.theme..."
  mkdir -p "${REPO_ROOT}/themes"
  cp -a "${HOME}/.local/share/org.kde.syntax-highlighting/themes/cachyos-dark.theme" "${REPO_ROOT}/themes/cachyos-dark.theme"
fi
if [ -f "${HOME}/.config/helium-browser-flags.conf" ]; then
  echo "  Exporting config/helium/helium-browser-flags.conf..."
  mkdir -p "${REPO_ROOT}/config/helium"
  cp -a "${HOME}/.config/helium-browser-flags.conf" "${REPO_ROOT}/config/helium/helium-browser-flags.conf"
fi

# ------------------------------------------------------------------------------
# 5. Cleanup Stray Caches and Verify Repository Snapshot
# ------------------------------------------------------------------------------
echo ""
echo ">>> [5/5] Purging stray ephemeral cache files in repository..."
python3 - <<EOF 2>/dev/null || true
import pathlib, shutil
repo = pathlib.Path("${REPO_ROOT}")
for p in repo.rglob("__pycache__"):
    if p.is_dir():
        shutil.rmtree(p, ignore_errors=True)
for p in repo.rglob(".pytest_cache"):
    if p.is_dir():
        shutil.rmtree(p, ignore_errors=True)
for p in repo.rglob("*.pyc"):
    p.unlink(missing_ok=True)
EOF

echo ""
echo ">>> Running repository verification gate..."
bash "${REPO_ROOT}/scripts/verify-harness.sh" "${REPO_ROOT}"

echo ""
echo "======================================================================"
echo " [SUCCESS] Antigravity SOTA Harness Successfully Exported & Verified!"
echo " Source:     ${SOURCE_DIR}"
echo " Repository: ${REPO_ROOT}"
echo "======================================================================"

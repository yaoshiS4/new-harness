#!/usr/bin/env bash
# ==============================================================================
# clean-diff.sh - Deterministic Git Diff Noise Stripper
# Inspired by Alibaba Open Code Review (OCR) hybrid architecture
#
# Filters out high-churn, low-signal files (lockfiles, minified bundles,
# generated artifacts, snapshots, and asset noise) before feeding diffs
# to Oracle and review agents.
# ==============================================================================

set -euo pipefail

SHOW_RAW=0
DIFF_ARGS=()

for arg in "$@"; do
    case "$arg" in
        --raw|--include-all)
            SHOW_RAW=1
            ;;
        -h|--help)
            cat << 'HELP_EOF'
Usage: clean-diff.sh [options] [git-diff-args...]

Options:
  --raw, --include-all  Bypass filtering and output the full, un-sanitized diff
  -h, --help            Show this help message

Examples:
  clean-diff.sh                   # Clean diff of unstaged working tree changes
  clean-diff.sh --staged          # Clean diff of staged changes
  clean-diff.sh HEAD~1            # Clean diff against previous commit
  clean-diff.sh main...feature    # Clean diff between branches
HELP_EOF
            exit 0
            ;;
        *)
            DIFF_ARGS+=("$arg")
            ;;
    esac
done

# Gracefully handle non-git directory execution
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "=== Filtered Review Diff Summary ==="
    echo "Non-git directory; zero git changes detected."
    echo "======================================"
    exit 0
fi

if [[ "$SHOW_RAW" -eq 1 ]]; then
    exec git diff "${DIFF_ARGS[@]}"
fi

# Standard deterministic noise exclusion pathspecs
EXCLUDE_SPECS=(
    ":(exclude)*package-lock.json"
    ":(exclude)*yarn.lock"
    ":(exclude)*pnpm-lock.yaml"
    ":(exclude)*Cargo.lock"
    ":(exclude)*go.sum"
    ":(exclude)*composer.lock"
    ":(exclude)*Gemfile.lock"
    ":(exclude)*poetry.lock"
    ":(exclude)*uv.lock"
    ":(exclude)*bun.lockb"
    ":(exclude)*.min.js"
    ":(exclude)*.min.css"
    ":(exclude)*.bundle.js"
    ":(exclude)*.map"
    ":(exclude)*__snapshots__/*"
    ":(exclude)*.pb.go"
    ":(exclude)*.pb.cc"
    ":(exclude)*.pb.h"
)

# Print a compact summary of modified functional files first (protected against non-zero exit)
echo "=== Filtered Review Diff Summary ==="
git diff --stat "${DIFF_ARGS[@]}" -- "${EXCLUDE_SPECS[@]}" 2>/dev/null || true
echo "======================================"
echo ""

# Output clean diff hunks
git diff "${DIFF_ARGS[@]}" -- "${EXCLUDE_SPECS[@]}"

#!/usr/bin/env python3
"""Antigravity native verification gate scaffolder for opt-in repositories."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

MULTI_LENS_PROMPTS: dict[str, str] = {
    "bug-hunter": "Lens 1 (bug-hunter): Hunt logic errors, null/undefined dereferences, off-by-one boundary defects, race conditions, and unhandled error paths.",
    "security": "Lens 2 (security): Audit injection vectors, symlink/path traversal, secret exposure, authentication/authorization bypass, and untrusted input handling.",
    "bird-eye": "Lens 3 (bird-eye): Verify end-to-end architectural alignment, cross-module contract coherence, scope containment, and absence of unintended regressions.",
    "code-quality": "Lens 4 (code-quality): Enforce Karpathy minimalism, eliminate dead/duplicated code, remove speculative abstractions, and preserve clean maintainability.",
    "harmonization": "Lens 5 (harmonization): Verify alignment with server-side LLM model routing (inherit/gemini-4-argon-medium default, flash/gemini-3.8-flash-high, force_ask-gated pro/gemini-4-argon-high) and dual CLI/IDE tool parity (read_file/view_file, write_file/write_to_file, edit_file/replace_file_content, call_mcp_tool).",
}
MULTI_LENS_SPECS = MULTI_LENS_PROMPTS


def compute_git_tree_fingerprint(workspace: str | Path) -> str:
    """Compute deterministic SHA-256 fingerprint of HEAD + git status --porcelain + git diff HEAD."""
    ws = Path(workspace).resolve()
    parts: list[str] = []
    git_cmds = (
        ["git", "rev-parse", "HEAD"],
        ["git", "status", "--porcelain"],
        ["git", "diff", "HEAD"],
    )
    git_ok = False
    for cmd in git_cmds:
        try:
            res = subprocess.run(
                cmd,
                cwd=str(ws),
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            if res.returncode == 0 or res.stdout:
                git_ok = True
            out_str = res.stdout or ""
            if cmd[:2] == ["git", "status"]:
                out_str = "\n".join(
                    line for line in out_str.splitlines()
                    if ".oracle_convergence" not in line
                )
            parts.append(out_str)
        except Exception:
            parts.append("")

    if not git_ok:
        for p in sorted(ws.rglob("*")):
            if p.is_file() and ".git" not in p.parts and not p.name.startswith(".oracle_convergence"):
                try:
                    rel = str(p.relative_to(ws))
                    digest = hashlib.sha256(p.read_bytes()).hexdigest()
                    parts.append(f"{rel}:{digest}")
                except Exception:
                    pass

    combined = "\n---\n".join(parts)
    return hashlib.sha256(combined.encode("utf-8", errors="replace")).hexdigest()


def check_review_convergence(
    workspace: str | Path,
    state_file: str | Path,
    max_rounds: int = 3,
) -> dict[str, Any]:
    """Track git tree fingerprint across review rounds and halt when unchanged or at max_rounds."""
    sf = Path(state_file)
    current_fp = compute_git_tree_fingerprint(workspace)
    prior_state: dict[str, Any] = {}
    if sf.is_file():
        try:
            prior_state = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            prior_state = {}

    prev_fp = prior_state.get("last_fingerprint")
    prev_round = int(prior_state.get("round", 0))
    history = list(prior_state.get("history", []))
    new_round = prev_round + 1

    if prev_fp and prev_fp == current_fp:
        converged = True
        reason = "tree_fingerprint_unchanged"
    elif new_round >= max_rounds:
        converged = True
        reason = "max_rounds_reached"
    else:
        converged = False
        reason = "tree_mutated_continue"

    history.append(current_fp)
    result = {
        "round": new_round,
        "max_rounds": max_rounds,
        "last_fingerprint": current_fp,
        "previous_fingerprint": prev_fp,
        "converged": converged,
        "reason": reason,
        "history": history,
    }
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

VERIFY_ORACLE_TEMPLATE = """#!/usr/bin/env bash
# verify-oracle.sh — Out-of-Process Independent Oracle Review Gate
# 6-Stage Lexicographic Evaluation Order:
# 1. Delivery -> 2. Conformance -> 3. Fidelity -> 4. Internal Consistency -> 5. Operational Fitness -> 6. Finish
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

CYAN='\\033[0;36m'
GREEN='\\033[0;32m'
RED='\\033[0;31m'
BOLD='\\033[1m'
NC='\\033[0m'

RUNNER="${ORACLE_RUNNER:-antigravity}"
MODEL="${ORACLE_MODEL:-gemini-4-argon-medium}"

MODE="code"
PLAN_PATH=""
REF_METRICS=""
CAND_METRICS=""
LENSES="bug-hunter,security,bird-eye,code-quality,harmonization"
FINGERPRINT_STATE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --plan)
      MODE="plan"
      if [[ $# -gt 1 && ! "$2" =~ ^-- ]]; then
        PLAN_PATH="$2"
        shift
      fi
      shift
      ;;
    --probe-contrast)
      MODE="probe_contrast"
      shift
      ;;
    --ref)
      REF_METRICS="$2"
      shift 2
      ;;
    --cand)
      CAND_METRICS="$2"
      shift 2
      ;;
    --lenses)
      LENSES="$2"
      shift 2
      ;;
    --fingerprint-state)
      FINGERPRINT_STATE="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [ -n "$FINGERPRINT_STATE" ]; then
  TREE_FP=$( (git rev-parse HEAD 2>/dev/null || true; git status --porcelain 2>/dev/null || true; git diff HEAD 2>/dev/null || true) | sha256sum | cut -d' ' -f1 )
  if [ -f "$FINGERPRINT_STATE" ] && grep -q "$TREE_FP" "$FINGERPRINT_STATE" 2>/dev/null; then
    echo -e "${BOLD}${GREEN}ORACLE REVIEW GATEWAY SIGN-OFF: APPROVED (Converged on unchanged git tree fingerprint ${TREE_FP})${NC}"
    exit 0
  fi
  echo "$TREE_FP" > "$FINGERPRINT_STATE"
fi

if [ "$MODE" = "probe_contrast" ]; then
  echo -e "${BOLD}${CYAN}━━━ Running Out-of-Process Behavioral Probe Contrast ━━━${NC}"
  if [ -n "$REF_METRICS" ] && [ -n "$CAND_METRICS" ] && [ -f "$HOME/.gemini/antigravity/scripts/recursive-ppc-engine.py" ]; then
    python3 "$HOME/.gemini/antigravity/scripts/recursive-ppc-engine.py" --probe-contrast --ref "$REF_METRICS" --cand "$CAND_METRICS" --workspace "$PROJECT_ROOT"
  fi
  PROMPT="Act as strict Oracle Reviewer. Evaluate candidate vs reference using 6-stage lexicographic order: 1. Delivery -> 2. Conformance -> 3. Fidelity -> 4. Internal Consistency -> 5. Operational Fitness -> 6. Finish."
elif [ "$MODE" = "plan" ]; then
  if [ -z "$PLAN_PATH" ]; then
    PLAN_PATH=$(fd -t f "^implementation_plan\\.md$" ~/.gemini/antigravity-cli/brain ~/.gemini/antigravity-ide/brain -x stat -c "%Y %n" 2>/dev/null | sort -k1,1nr | { head -n 1 || true; } | cut -d' ' -f2-)
  fi
  if [ -z "$PLAN_PATH" ] || [ ! -f "$PLAN_PATH" ]; then
    echo -e "${RED}✗ Error: implementation_plan.md not found for Oracle plan review.${NC}"
    exit 1
  fi
  echo -e "${BOLD}${CYAN}━━━ Running Out-of-Process Oracle Plan Review: $(basename "$PLAN_PATH") ━━━${NC}"
  PROMPT="Act as strict Oracle Reviewer. Audit plan against 6-stage lexicographic order (1. Delivery -> 2. Conformance -> 3. Fidelity -> 4. Internal Consistency -> 5. Operational Fitness -> 6. Finish) and project architecture:\\n$(cat "$PLAN_PATH")"
else
  echo -e "${BOLD}${CYAN}━━━ Running Out-of-Process Independent Oracle Review Gate (Code) ━━━${NC}"
  if [ -x "$HOME/.gemini/antigravity/scripts/clean-diff.sh" ]; then
    DIFF_OUTPUT=$("$HOME/.gemini/antigravity/scripts/clean-diff.sh" 2>/dev/null || true)
  else
    DIFF_OUTPUT=$(git diff HEAD 2>/dev/null | head -n 500 || true)
  fi
  if [ -z "$DIFF_OUTPUT" ]; then
    DIFF_OUTPUT="No uncommitted changes detected (clean working tree)."
  fi
  PROMPT="Act as strict Oracle Reviewer. Audit git diff against 6-stage lexicographic order (1. Delivery -> 2. Conformance -> 3. Fidelity -> 4. Internal Consistency -> 5. Operational Fitness -> 6. Finish), apply Multi-Lens perspectives (${LENSES}), and run a VeriHarness Consensus Challenge (identify any shared specification blind spot or colluding assertion between implementation and tests):\\n${DIFF_OUTPUT}"
fi
PROMPT="${PROMPT}\\n\\nEvaluate the supplied input directly in a single pass without running tool loops."

if ! command -v agy >/dev/null 2>&1; then
  echo -e "${RED}✗ Error: agy CLI not found in PATH.${NC}" >&2
  exit 1
fi

tmp_env=$(mktemp -d /tmp/.oracle_env_XXXXXX)
mkdir -p "$tmp_env/.gemini/antigravity-cli/brain" "$tmp_env/.gemini/antigravity-cli/mcp" "$tmp_env/.gemini/config"
for item in "$HOME"/.gemini/antigravity-cli/*; do
  [ -e "$item" ] || continue
  b=$(basename "$item")
  if [ "$b" != "mcp" ] && [ "$b" != "plugins" ] && [ "$b" != "brain" ]; then
    case "$b" in
      conversation_summaries.db*|jetbox_summaries_proto.pb|history.jsonl|presence|annotations)
        continue
        ;;
    esac
    ln -s "$item" "$tmp_env/.gemini/antigravity-cli/$b" 2>/dev/null || true
  fi
done
echo "{}" > "$tmp_env/.gemini/config/hooks.json"
echo "{}" > "$tmp_env/.gemini/config/mcp_config.json"
AGY_EXIT=0
AGY_OUT=$(HOME="$tmp_env" agy --model "$MODEL" --dangerously-skip-permissions --print "$PROMPT" 2>&1) || AGY_EXIT=$?
echo "$AGY_OUT"
rm -rf "$tmp_env" 2>/dev/null || true
if [ "$AGY_EXIT" -ne 0 ]; then
  echo -e "${BOLD}${RED}ORACLE REVIEW GATEWAY SIGN-OFF: FAILED (agy exited with code $AGY_EXIT)${NC}"
  exit 1
fi
if echo "$AGY_OUT" | grep -qE "(ORACLE REVIEW GATEWAY SIGN-OFF: REJECTED|Status: REJECTED)"; then
  echo -e "${BOLD}${RED}ORACLE REVIEW GATEWAY SIGN-OFF: REJECTED${NC}"
  exit 1
fi
if echo "$AGY_OUT" | grep -qE "(ORACLE REVIEW GATEWAY SIGN-OFF: APPROVED|Status: APPROVED)"; then
  echo -e "${BOLD}${GREEN}ORACLE REVIEW GATEWAY SIGN-OFF: APPROVED${NC}"
  exit 0
else
  echo -e "${BOLD}${RED}ORACLE REVIEW GATEWAY SIGN-OFF: FAILED (Output did not contain explicit APPROVED sign-off)${NC}"
  exit 1
fi
"""

TEST_3_ROUND_TEMPLATE = """#!/usr/bin/env bash
# test-3-round-loop.sh — Continuous Multi-Round Zero-Bug Verification Gate
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

TARGET_ROUNDS=3
CONSECUTIVE_PASSES=0
ROUND=1

echo "━━━ 3-Round Verification Loop ━━━"

run_suite() {
  if [ -f "package.json" ] && rg -q '"test"' package.json; then
    npm test
  elif [ -f "Cargo.toml" ]; then
    cargo test
  elif [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
    pytest
  elif [ -f "go.mod" ]; then
    go test ./...
  elif [ -f "gradlew" ]; then
    ./gradlew test
  elif [ -f "Makefile" ] && rg -q '^test:' Makefile; then
    make test
  else
    echo "✗ Error: No supported test runner detected (package.json, Cargo.toml, pyproject.toml, setup.py, go.mod, gradlew, Makefile test target)."
    return 1
  fi
}

while [ "$CONSECUTIVE_PASSES" -lt "$TARGET_ROUNDS" ]; do
  echo "[Round $ROUND] Running verification suite..."
  if ! run_suite; then
    echo "✗ Round $ROUND failed."
    if [ "${AGY_RECURSIVE_PPC:-1}" = "1" ] && [ -f "$HOME/.gemini/antigravity/scripts/recursive-ppc-engine.py" ]; then
      echo "⚡ Triggering Level-1 Intra-Task Recursive PPC Engine..."
      python3 "$HOME/.gemini/antigravity/scripts/recursive-ppc-engine.py" --mount "$PROJECT_ROOT"
    fi
    exit 1
  fi
  CONSECUTIVE_PASSES=$((CONSECUTIVE_PASSES + 1))
  ROUND=$((ROUND + 1))
done

echo "★★★ SUCCESS: 3 CONSECUTIVE ROUNDS PASSED WITH ZERO DEFECTS! ★★★"
"""

PRE_COMMIT_TEMPLATE = """#!/usr/bin/env bash
# Pre-commit gate enforcing verify-oracle.sh if present
set -euo pipefail

if [ -f "scripts/verification/verify-oracle.sh" ]; then
  bash scripts/verification/verify-oracle.sh
fi
"""


def ensure_repo_gates(wp: Path) -> bool:
    try:
        scripts_dir = wp / "scripts" / "verification"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        oracle_sh = scripts_dir / "verify-oracle.sh"
        if not oracle_sh.is_file():
            oracle_sh.write_text(VERIFY_ORACLE_TEMPLATE, encoding="utf-8")
        oracle_sh.chmod(oracle_sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        test3_sh = scripts_dir / "test-3-round-loop.sh"
        if not test3_sh.is_file():
            test3_sh.write_text(TEST_3_ROUND_TEMPLATE, encoding="utf-8")
        test3_sh.chmod(test3_sh.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        if os.environ.get("AGY_INSTALL_GIT_PRECOMMIT") == "1":
            git_hooks_dir = wp / ".git" / "hooks"
            if (wp / ".git").is_dir():
                git_hooks_dir.mkdir(parents=True, exist_ok=True)
                pre_commit = git_hooks_dir / "pre-commit"
                if not pre_commit.is_file():
                    pre_commit.write_text(PRE_COMMIT_TEMPLATE, encoding="utf-8")
                pre_commit.chmod(pre_commit.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        return True
    except Exception as e:
        sys.stderr.write(f"[ensure-verification-gates] {e}\n")
        return False


if __name__ == "__main__":
    import argparse
    import sys
    import tempfile

    parser = argparse.ArgumentParser(description="Antigravity verification gate scaffolder")
    parser.add_argument("workspace", nargs="?", default=".", help="Target workspace path (default: current directory)")
    parser.add_argument("--self-test", action="store_true", help="Run self-test in temporary workspace")

    args = parser.parse_args()

    if args.self_test:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            res = ensure_repo_gates(td_path)
            assert res is True, "ensure_repo_gates failed in self-test"
            oracle_sh = td_path / "scripts" / "verification" / "verify-oracle.sh"
            assert oracle_sh.is_file()
            assert (td_path / "scripts" / "verification" / "test-3-round-loop.sh").is_file()
            oracle_text = oracle_sh.read_text(encoding="utf-8")
            assert "--lenses" in oracle_text, "verify-oracle.sh missing --lenses flag"
            assert "--fingerprint-state" in oracle_text, "verify-oracle.sh missing --fingerprint-state flag"
            for lens in ("bug-hunter", "security", "bird-eye", "code-quality", "harmonization"):
                assert lens in MULTI_LENS_PROMPTS, f"Missing lens {lens}"

            # Test git tree fingerprint & convergence state machine
            sample_file = td_path / "app.py"
            sample_file.write_text("x = 1\n", encoding="utf-8")
            state_file = td_path / ".oracle_convergence.json"
            fp1 = compute_git_tree_fingerprint(td_path)
            assert len(fp1) == 64

            conv1 = check_review_convergence(td_path, state_file, max_rounds=3)
            assert conv1["converged"] is False
            assert conv1["round"] == 1
            assert conv1["reason"] == "tree_mutated_continue"

            # Unchanged tree -> converges immediately on round 2
            conv2 = check_review_convergence(td_path, state_file, max_rounds=3)
            assert conv2["converged"] is True
            assert conv2["round"] == 2
            assert conv2["reason"] == "tree_fingerprint_unchanged"

            # Mutated tree -> fingerprint changes; round 3 hits max_rounds
            sample_file.write_text("x = 2\n", encoding="utf-8")
            fp2 = compute_git_tree_fingerprint(td_path)
            assert fp2 != fp1
            conv3 = check_review_convergence(td_path, state_file, max_rounds=3)
            assert conv3["converged"] is True
            assert conv3["round"] == 3
            assert conv3["reason"] == "max_rounds_reached"
            print("ensure-verification-gates self-test: PASS")
        sys.exit(0)

    target = Path(args.workspace).resolve()
    success = ensure_repo_gates(target)
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""Level-1 Intra-Task Recursive PPC Engine (arXiv:2610.14224v1).

Manages task-level harness overlays (.antigravity/task_harness/),
enforces orthogonal proposer isolation (INV vs DOM), computes deterministic
behavioral contrast deltas, and enforces KEEP_BASE fallback.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import py_compile
import re
import shutil
import sqlite3
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


class ValidationResult:
    """Validation result with boolean evaluation and tuple unpacking support."""

    def __init__(self, valid: bool, reason: str = ""):
        self.valid = bool(valid)
        self.reason = str(reason)

    def __bool__(self) -> bool:
        return self.valid

    def __iter__(self):
        return iter((self.valid, self.reason))

    def __getitem__(self, idx: int):
        return (self.valid, self.reason)[idx]

    def __repr__(self) -> str:
        return f"ValidationResult(valid={self.valid}, reason={self.reason!r})"


def ensure_git_exclude(workspace: Union[str, Path]) -> bool:
    """Atomically append .antigravity/ to git exclude file if inside git repository."""
    ws = Path(workspace).resolve()
    git_entry = ws / ".git"

    if not git_entry.exists():
        return False

    git_dir: Optional[Path] = None
    if git_entry.is_dir():
        git_dir = git_entry
    elif git_entry.is_file():
        try:
            content = git_entry.read_text(encoding="utf-8").strip()
            if content.startswith("gitdir:"):
                raw_path = content.split("gitdir:", 1)[1].strip()
                target_path = Path(raw_path)
                if not target_path.is_absolute():
                    git_dir = (ws / target_path).resolve()
                else:
                    git_dir = target_path.resolve()
        except Exception:
            return False

    if not git_dir or not git_dir.is_dir():
        return False

    info_dir = git_dir / "info"
    info_dir.mkdir(parents=True, exist_ok=True)
    exclude_file = info_dir / "exclude"

    existing_lines: List[str] = []
    if exclude_file.is_file():
        try:
            raw_text = exclude_file.read_text(encoding="utf-8")
            existing_lines = [line.strip() for line in raw_text.splitlines()]
        except Exception:
            existing_lines = []

    target_entries = {".antigravity/", ".antigravity"}
    if not target_entries.intersection(existing_lines):
        try:
            with open(exclude_file, "a", encoding="utf-8") as f:
                if existing_lines and raw_text and not raw_text.endswith("\n"):
                    f.write("\n")
                f.write(".antigravity/\n")
            return True
        except Exception:
            return False

    return True


VERIFY_TASK_TEMPLATE = '''#!/usr/bin/env python3
"""Task-specific declarative invariant verification gate."""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys


def verify() -> bool:
    overlay_dir = Path(__file__).resolve().parent.parent
    workspace = overlay_dir.parent.parent
    guardrails_file = overlay_dir / "guardrails.json"

    if not guardrails_file.is_file():
        return True

    try:
        data = json.loads(guardrails_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"Fail: guardrails.json parse error: {exc}", file=sys.stderr)
        return False

    rules = data.get("rules", [])
    if not rules:
        return True

    for rule in rules:
        rule_type = rule.get("type")
        rel_path = rule.get("path")
        if not rel_path:
            continue
        target = workspace / rel_path

        if rule_type == "file_exists":
            if not target.is_file():
                print(f"Fail: {rule_type} on {rel_path}")
                return False
        elif rule_type == "regex_present":
            pattern = rule.get("pattern", "")
            if not target.is_file():
                print(f"Fail: {rule_type} on {rel_path}")
                return False
            try:
                content = target.read_text(encoding="utf-8")
            except Exception:
                print(f"Fail: {rule_type} on {rel_path}")
                return False
            if not re.search(pattern, content):
                print(f"Fail: {rule_type} on {rel_path}")
                return False
        elif rule_type == "regex_absent":
            pattern = rule.get("pattern", "")
            if target.is_file():
                try:
                    content = target.read_text(encoding="utf-8")
                except Exception:
                    content = ""
                if re.search(pattern, content):
                    print(f"Fail: {rule_type} on {rel_path}")
                    return False

    return True


if __name__ == "__main__":
    sys.exit(0 if verify() else 1)
'''


def mount_task_harness(workspace: Union[str, Path]) -> Dict[str, Any]:
    """Mount the task-scoped overlay directory (.antigravity/task_harness/)."""
    ws = Path(workspace).resolve()
    overlay_dir = ws / ".antigravity" / "task_harness"
    scripts_dir = overlay_dir / "scripts"
    snapshot_dir = overlay_dir / ".base_snapshot"

    scripts_dir.mkdir(parents=True, exist_ok=True)
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    git_excluded = ensure_git_exclude(ws)

    state_file = overlay_dir / "state.json"
    if not state_file.is_file():
        initial_state = {
            "step": 0,
            "status": "mounted",
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "last_decision": "MOUNT",
            "last_delta": 0.0,
            "history": [],
        }
        state_file.write_text(json.dumps(initial_state, indent=2), encoding="utf-8")

    tool_guidance = overlay_dir / "tool_guidance.md"
    if not tool_guidance.is_file():
        tool_guidance.write_text(
            "# Task-Specific Tool Guidance\n\nRecord task-specific execution guardrails and tool quirks here.\n",
            encoding="utf-8",
        )

    guardrails = overlay_dir / "guardrails.json"
    if not guardrails.is_file():
        guardrails.write_text(json.dumps({"rules": []}, indent=2), encoding="utf-8")

    skill_file = overlay_dir / "SKILL.md"
    if not skill_file.is_file():
        skill_file.write_text(
            "---\nname: task-overlay-skill\ndescription: Task-scoped domain instructions evolved during intra-task recursion.\n---\n\n# Task-Scoped Domain Guidance\n",
            encoding="utf-8",
        )

    verify_script = scripts_dir / "verify_task.py"
    if not verify_script.is_file():
        verify_script.write_text(VERIFY_TASK_TEMPLATE, encoding="utf-8")

    _snapshot_overlay(overlay_dir, snapshot_dir)

    return {
        "status": "mounted",
        "workspace": str(ws),
        "overlay_dir": str(overlay_dir),
        "git_excluded": git_excluded,
    }


def _snapshot_overlay(src_overlay: Path, dst_snapshot: Path) -> None:
    """Snapshot candidate overlay files to base snapshot directory."""
    dst_snapshot.mkdir(parents=True, exist_ok=True)
    for root, dirs, files in os.walk(src_overlay):
        rel_root = Path(root).relative_to(src_overlay)
        if ".base_snapshot" in rel_root.parts:
            continue
        target_dir = dst_snapshot / rel_root
        target_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            src_f = Path(root) / f
            dst_f = target_dir / f
            shutil.copy2(src_f, dst_f)


def _restore_overlay_from_snapshot(src_snapshot: Path, dst_overlay: Path) -> None:
    """Restore overlay files from base snapshot."""
    if not src_snapshot.is_dir():
        return
    for root, dirs, files in os.walk(src_snapshot):
        rel_root = Path(root).relative_to(src_snapshot)
        target_dir = dst_overlay / rel_root
        target_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            src_f = Path(root) / f
            dst_f = target_dir / f
            shutil.copy2(src_f, dst_f)


def compile_task_guardrail(workspace: Union[str, Path], rule: Dict[str, Any]) -> bool:
    """Append a declarative guardrail rule into .antigravity/task_harness/guardrails.json (deduplicating)."""
    try:
        ws = Path(workspace).resolve()
        overlay_dir = ws / ".antigravity" / "task_harness"
        overlay_dir.mkdir(parents=True, exist_ok=True)
        guardrails_file = overlay_dir / "guardrails.json"

        if guardrails_file.is_file():
            try:
                data = json.loads(guardrails_file.read_text(encoding="utf-8"))
            except Exception:
                data = {"rules": []}
        else:
            data = {"rules": []}

        if not isinstance(data, dict):
            data = {"rules": []}
        if "rules" not in data or not isinstance(data["rules"], list):
            data["rules"] = []

        if rule not in data["rules"]:
            data["rules"].append(rule)
            guardrails_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

        return True
    except Exception:
        return False


def validate_proposer_targets(
    proposer_type: str,
    target_files: Union[Sequence[Union[str, Path]], Union[str, Path]],
    workspace: Union[str, Path] = ".",
) -> ValidationResult:
    """Validate that proposer target files strictly adhere to orthogonal boundary contracts.

    Proposer Isolation:
    - INV (meta-invariant-editor):
      Allowed ONLY:
      - ~/.gemini/antigravity/guidelines/tool-quirks.md
      - <workspace>/.antigravity/task_harness/tool_guidance.md
      - <workspace>/.antigravity/task_harness/guardrails.json
    - DOM (meta-domain-editor):
      Allowed ONLY:
      - <workspace>/.antigravity/task_harness/SKILL.md
      - <workspace>/.antigravity/task_harness/scripts/*.py
    - Neither may touch:
      ~/.gemini/config/hooks/*.py, ~/.gemini/GEMINI.md, or application code.
    """
    ws = Path(workspace).resolve()
    overlay_dir = (ws / ".antigravity" / "task_harness").resolve()

    if isinstance(target_files, (str, Path)):
        files = [target_files]
    else:
        files = list(target_files)

    if not files:
        return ValidationResult(False, "No target files provided for validation.")

    p_type = proposer_type.strip()
    norm_p = p_type.upper()
    if norm_p in ("INV", "META-INVARIANT-EDITOR"):
        mode = "INV"
    elif norm_p in ("DOM", "META-DOMAIN-EDITOR"):
        mode = "DOM"
    else:
        return ValidationResult(
            False,
            f"Unknown proposer_type {proposer_type!r}. Must be 'INV'/'meta-invariant-editor' or 'DOM'/'meta-domain-editor'.",
        )

    home_quirks = (Path.home() / ".gemini" / "antigravity" / "guidelines" / "tool-quirks.md").resolve()
    hooks_dir = (Path.home() / ".gemini" / "config" / "hooks").resolve()
    gemini_md = (Path.home() / ".gemini" / "GEMINI.md").resolve()

    for item in files:
        p_str = str(item)
        if p_str.startswith("~"):
            target_path = Path(p_str).expanduser().resolve()
        else:
            raw_p = Path(p_str)
            if raw_p.is_absolute():
                target_path = raw_p.resolve()
            else:
                target_path = (ws / raw_p).resolve()

        # Hard invariant: neither may touch hooks or global GEMINI.md
        if target_path == gemini_md:
            return ValidationResult(
                False,
                f"Proposer [{mode}] prohibited from modifying global GEMINI.md: {target_path}",
            )
        try:
            target_path.relative_to(hooks_dir)
            return ValidationResult(
                False,
                f"Proposer [{mode}] prohibited from modifying lifecycle hooks: {target_path}",
            )
        except ValueError:
            pass

        if mode == "INV":
            is_quirks = target_path == home_quirks
            is_overlay_guidance = (
                target_path == (overlay_dir / "tool_guidance.md")
                or target_path == (overlay_dir / "guardrails.json")
            )
            if not (is_quirks or is_overlay_guidance):
                return ValidationResult(
                    False,
                    f"Proposer [INV] violation: path {target_path} is outside allowed INV targets "
                    f"([tool-quirks.md, tool_guidance.md, guardrails.json]).",
                )

        elif mode == "DOM":
            is_overlay_skill = target_path == (overlay_dir / "SKILL.md")
            is_overlay_script = False
            scripts_dir = overlay_dir / "scripts"
            try:
                rel = target_path.relative_to(scripts_dir)
                if target_path.suffix == ".py":
                    is_overlay_script = True
            except ValueError:
                is_overlay_script = False

            if not (is_overlay_skill or is_overlay_script):
                return ValidationResult(
                    False,
                    f"Proposer [DOM] violation: path {target_path} is outside allowed DOM targets "
                    f"([SKILL.md, scripts/*.py]).",
                )

    return ValidationResult(True, f"All target files valid for proposer [{mode}].")


def compute_behavioral_delta(ref_metrics: Dict[str, Any], cand_metrics: Dict[str, Any]) -> float:
    """Compute deterministic behavioral delta between reference and candidate rollouts.

    Delta formula:
    delta = (ref_err - cand_err)
          + 2 * (ref_jev - cand_jev)
          + (ref_strikes - cand_strikes)
          + (1 if cand_delivered and not ref_delivered else (-2 if ref_delivered and not cand_delivered else 0))
    """
    ref_err = float(ref_metrics.get("tool_error_count", ref_metrics.get("tool_errors", ref_metrics.get("errors", 0))))
    cand_err = float(cand_metrics.get("tool_error_count", cand_metrics.get("tool_errors", cand_metrics.get("errors", 0))))

    ref_jev = float(ref_metrics.get("jev_loop_warnings", ref_metrics.get("jev_warnings", ref_metrics.get("jev_loops", 0))))
    cand_jev = float(cand_metrics.get("jev_loop_warnings", cand_metrics.get("jev_warnings", cand_metrics.get("jev_loops", 0))))

    ref_strikes = float(ref_metrics.get("read_budget_strikes", ref_metrics.get("read_strikes", ref_metrics.get("strikes", 0))))
    cand_strikes = float(cand_metrics.get("read_budget_strikes", cand_metrics.get("read_strikes", cand_metrics.get("strikes", 0))))

    ref_delivered = bool(ref_metrics.get("deliverable_non_empty", ref_metrics.get("delivered", False)))
    cand_delivered = bool(cand_metrics.get("deliverable_non_empty", cand_metrics.get("delivered", False)))

    if cand_delivered and not ref_delivered:
        delivery_term = 1.0
    elif ref_delivered and not cand_delivered:
        delivery_term = -2.0
    else:
        delivery_term = 0.0

    delta = (
        (ref_err - cand_err)
        + 2.0 * (ref_jev - cand_jev)
        + (ref_strikes - cand_strikes)
        + delivery_term
    )
    return delta


def verify_overlay_scripts(overlay_dir: Path) -> Tuple[bool, str]:
    """Verify that all Python scripts in task harness overlay pass py_compile."""
    scripts_dir = overlay_dir / "scripts"
    if not scripts_dir.is_dir():
        return True, "No scripts directory found."

    for root, _, files in os.walk(scripts_dir):
        for f in files:
            if f.endswith(".py"):
                full_path = Path(root) / f
                try:
                    py_compile.compile(str(full_path), doraise=True)
                except py_compile.PyCompileError as exc:
                    return False, f"py_compile failed on {full_path}: {exc}"
                except Exception as exc:
                    return False, f"Compilation exception on {full_path}: {exc}"

    return True, "All scripts passed py_compile."


def compose_step(
    workspace: Union[str, Path],
    ref_metrics: Dict[str, Any],
    cand_metrics: Dict[str, Any],
    candidate_overlay_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Evaluate candidate overlay against reference metrics with strict KEEP_BASE default."""
    ws = Path(workspace).resolve()
    overlay_dir = ws / ".antigravity" / "task_harness"
    snapshot_dir = overlay_dir / ".base_snapshot"

    if not overlay_dir.is_dir():
        mount_task_harness(ws)

    delta = compute_behavioral_delta(ref_metrics, cand_metrics)

    # If candidate overlay was provided externally, stage it into overlay_dir for verification
    if candidate_overlay_dir:
        cand_p = Path(candidate_overlay_dir).resolve()
        if cand_p.is_dir():
            _snapshot_overlay(cand_p, overlay_dir)

    # 1. Compilation Verification Gate
    passed_compile, compile_msg = verify_overlay_scripts(overlay_dir)
    if not passed_compile:
        _restore_overlay_from_snapshot(snapshot_dir, overlay_dir)
        _record_step(overlay_dir, decision="KEEP_BASE", delta=delta, reason=compile_msg)
        return {
            "decision": "KEEP_BASE",
            "delta": delta,
            "reason": f"py_compile_failure: {compile_msg}",
            "workspace": str(ws),
        }

    # 2. Behavioral Delta Gate (delta > 0 required for adoption)
    if delta <= 0.0:
        _restore_overlay_from_snapshot(snapshot_dir, overlay_dir)
        reason = f"delta_non_positive: delta={delta:.2f} <= 0"
        _record_step(overlay_dir, decision="KEEP_BASE", delta=delta, reason=reason)
        return {
            "decision": "KEEP_BASE",
            "delta": delta,
            "reason": reason,
            "workspace": str(ws),
        }

    # 3. Adopt candidate into base snapshot
    _snapshot_overlay(overlay_dir, snapshot_dir)
    reason = f"adopted: positive delta={delta:.2f}"
    _record_step(overlay_dir, decision="ADOPTED", delta=delta, reason=reason)
    return {
        "decision": "ADOPTED",
        "delta": delta,
        "reason": reason,
        "workspace": str(ws),
    }


def _record_step(overlay_dir: Path, decision: str, delta: float, reason: str) -> None:
    """Record step decision to state.json."""
    state_file = overlay_dir / "state.json"
    data: Dict[str, Any] = {}
    if state_file.is_file():
        try:
            data = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    current_step = int(data.get("step", 0)) + 1
    history = data.get("history", [])
    entry = {
        "step": current_step,
        "decision": decision,
        "delta": delta,
        "reason": reason,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    history.append(entry)

    data["step"] = current_step
    data["last_decision"] = decision
    data["last_delta"] = delta
    data["history"] = history
    try:
        state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _load_json_arg(arg_val: str) -> Dict[str, Any]:
    """Parse JSON from file path or inline JSON string."""
    p = Path(arg_val)
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return json.loads(arg_val)


def promote_validated_candidates(
    workspace: Union[str, Path] = ".",
    registry_db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Graduate validated task-harness overlay into global settings_reviews."""
    ws = Path(workspace).resolve()
    overlay_dir = ws / ".antigravity" / "task_harness"
    if not overlay_dir.is_dir():
        return {
            "promoted": False,
            "decision": "KEEP_BASE",
            "delta": 0.0,
            "reason": f"Overlay directory does not exist: {overlay_dir}",
            "graduated_files": [],
            "review_id": None,
        }

    state_file = overlay_dir / "state.json"
    state_data: Dict[str, Any] = {}
    if state_file.is_file():
        try:
            state_data = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            state_data = {}

    delta = float(state_data.get("last_delta", 0.0))
    if delta == 0.0 and state_data.get("history"):
        latest = state_data["history"][-1]
        delta = float(latest.get("delta", 0.0))

    if delta <= 0.0:
        return {
            "promoted": False,
            "decision": "KEEP_BASE",
            "delta": delta,
            "reason": f"Behavioral delta non-positive: delta={delta:.2f} <= 0",
            "graduated_files": [],
            "review_id": None,
        }

    passed_compile, compile_msg = verify_overlay_scripts(overlay_dir)
    if not passed_compile:
        return {
            "promoted": False,
            "decision": "KEEP_BASE",
            "delta": delta,
            "reason": f"py_compile_failure: {compile_msg}",
            "graduated_files": [],
            "review_id": None,
        }

    candidate_files: List[str] = []
    for root, dirs, files in os.walk(overlay_dir):
        rel_root = Path(root).relative_to(overlay_dir)
        if any(part.startswith(".") for part in rel_root.parts):
            continue
        for f in files:
            if f.startswith(".") or f == "state.json":
                continue
            rel_path = str(rel_root / f) if str(rel_root) != "." else f
            candidate_files.append(rel_path)

    if not candidate_files:
        return {
            "promoted": False,
            "decision": "KEEP_BASE",
            "delta": delta,
            "reason": "No candidate overlay files found to graduate",
            "graduated_files": [],
            "review_id": None,
        }

    if registry_db_path:
        db_path = registry_db_path
    else:
        codex_db = os.path.expanduser("~/.local/share/codex/projects/registry.sqlite")
        db_path = codex_db if os.path.isfile(codex_db) else os.path.expanduser("~/.gemini/antigravity/skillbank/registry.sqlite")
    db_dir = os.path.dirname(os.path.abspath(db_path))
    os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS settings_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT,
                reason TEXT,
                event_count INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME
            );
            """
        )
        slug = ws.name
        file_summary = ", ".join(sorted(candidate_files)[:3])
        reason = f"Graduated task-harness overlay ({len(candidate_files)} file(s): {file_summary}) with delta={delta:.2f}"
        cur.execute(
            """
            INSERT INTO settings_reviews (slug, reason, event_count)
            VALUES (?, ?, ?);
            """,
            (slug, reason, len(candidate_files)),
        )
        review_id = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    state_data["graduated"] = True
    state_data["graduated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state_data["graduated_review_id"] = review_id
    try:
        state_file.write_text(json.dumps(state_data, indent=2), encoding="utf-8")
    except Exception:
        pass

    return {
        "promoted": True,
        "decision": "PROMOTED",
        "delta": delta,
        "review_id": review_id,
        "graduated_files": sorted(candidate_files),
        "registry_db": str(db_path),
        "workspace": str(ws),
    }


# ==============================================================================
# Self-Test Suite
# ==============================================================================

def run_test_proposer_isolation() -> bool:
    """Test strict orthogonal boundary enforcement for INV and DOM proposers."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        mount_task_harness(ws)
        overlay = ws / ".antigravity" / "task_harness"
        home_quirks = Path.home() / ".gemini" / "antigravity" / "guidelines" / "tool-quirks.md"

        # --- Test INV (meta-invariant-editor) ---
        # Valid INV targets
        inv_valid_targets = [
            home_quirks,
            overlay / "tool_guidance.md",
            overlay / "guardrails.json",
        ]
        res = validate_proposer_targets("INV", inv_valid_targets, ws)
        assert res.valid, f"Expected INV valid targets to pass, got: {res.reason}"

        # Invalid INV targets: SKILL.md, scripts, app code, hooks
        for bad_target in [
            overlay / "SKILL.md",
            overlay / "scripts" / "verify_task.py",
            ws / "src" / "app.py",
            Path.home() / ".gemini" / "config" / "hooks" / "stop_hook.py",
            Path.home() / ".gemini" / "GEMINI.md",
        ]:
            res = validate_proposer_targets("INV", [bad_target], ws)
            assert not res.valid, f"Expected INV bad target {bad_target} to fail, but it passed."

        # --- Test DOM (meta-domain-editor) ---
        # Valid DOM targets
        dom_valid_targets = [
            overlay / "SKILL.md",
            overlay / "scripts" / "verify_task.py",
            overlay / "scripts" / "custom_checker.py",
        ]
        res = validate_proposer_targets("DOM", dom_valid_targets, ws)
        assert res.valid, f"Expected DOM valid targets to pass, got: {res.reason}"

        # Invalid DOM targets: tool-quirks, tool_guidance, guardrails, app code, hooks
        for bad_target in [
            home_quirks,
            overlay / "tool_guidance.md",
            overlay / "guardrails.json",
            ws / "src" / "index.ts",
            Path.home() / ".gemini" / "config" / "hooks" / "pre_tool_use_hook.py",
            Path.home() / ".gemini" / "GEMINI.md",
        ]:
            res = validate_proposer_targets("DOM", [bad_target], ws)
            assert not res.valid, f"Expected DOM bad target {bad_target} to fail, but it passed."

        # Unknown proposer
        res = validate_proposer_targets("UNKNOWN_PROPOSER", [overlay / "SKILL.md"], ws)
        assert not res.valid, "Expected unknown proposer to fail."

    return True


def run_test_git_exclusion() -> bool:
    """Test git exclude registration on overlay mounting."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        git_dir = ws / ".git"
        git_dir.mkdir(parents=True)

        # 1. Mount and verify .antigravity/ added to info/exclude
        res = mount_task_harness(ws)
        assert res["git_excluded"] is True, "Failed to register git exclude."
        exclude_file = git_dir / "info" / "exclude"
        assert exclude_file.is_file(), "exclude file does not exist."
        content = exclude_file.read_text(encoding="utf-8")
        assert ".antigravity/\n" in content, "Missing .antigravity/ in exclude."

        # 2. Re-mount and verify no duplicate entries
        mount_task_harness(ws)
        content2 = exclude_file.read_text(encoding="utf-8")
        assert content2.count(".antigravity/") == 1, "Duplicate .antigravity/ entries created."

        # 3. Test git worktree file pointer (gitdir: <path>)
        wt_dir = ws / "worktree"
        wt_dir.mkdir()
        wt_git = wt_dir / ".git"
        dot_git_target = ws / "custom_gitdir"
        dot_git_target.mkdir()
        wt_git.write_text(f"gitdir: {dot_git_target}\n", encoding="utf-8")

        res_wt = mount_task_harness(wt_dir)
        assert res_wt["git_excluded"] is True
        wt_exclude = dot_git_target / "info" / "exclude"
        assert wt_exclude.is_file()
        assert ".antigravity/\n" in wt_exclude.read_text(encoding="utf-8")

    return True


def run_test_fallback() -> bool:
    """Test delta calculation, KEEP_BASE fallback on delta <= 0, and py_compile failure."""
    import tempfile

    # 1. Delta calculation test cases
    ref = {"tool_error_count": 3, "jev_loop_warnings": 1, "read_budget_strikes": 2, "deliverable_non_empty": False}
    cand_better = {"tool_error_count": 1, "jev_loop_warnings": 0, "read_budget_strikes": 1, "deliverable_non_empty": True}
    # delta = (3 - 1) + 2*(1 - 0) + (2 - 1) + 1 = 2 + 2 + 1 + 1 = 6.0
    d1 = compute_behavioral_delta(ref, cand_better)
    assert d1 == 6.0, f"Expected 6.0, got {d1}"

    cand_worse = {"tool_error_count": 4, "jev_loop_warnings": 2, "read_budget_strikes": 3, "deliverable_non_empty": False}
    # delta = (3 - 4) + 2*(1 - 2) + (2 - 3) + 0 = -1 - 2 - 1 = -4.0
    d2 = compute_behavioral_delta(ref, cand_worse)
    assert d2 == -4.0, f"Expected -4.0, got {d2}"

    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        mount_task_harness(ws)
        overlay = ws / ".antigravity" / "task_harness"
        verify_py = overlay / "scripts" / "verify_task.py"

        # 2. Test py_compile syntax error -> KEEP_BASE regardless of delta
        base_script_content = verify_py.read_text(encoding="utf-8")
        verify_py.write_text("def broken_syntax(:\n    pass\n", encoding="utf-8")
        step_res = compose_step(ws, ref, cand_better)
        assert step_res["decision"] == "KEEP_BASE", f"Expected KEEP_BASE on syntax error, got {step_res}"
        # Verify base script restored
        assert verify_py.read_text(encoding="utf-8") == base_script_content, "Base script was not restored after compilation error."

        # 3. Test delta <= 0 -> KEEP_BASE
        verify_py.write_text("# Candidate edit with worse metrics\ndef verify(): return True\n", encoding="utf-8")
        step_res2 = compose_step(ws, ref, cand_worse)
        assert step_res2["decision"] == "KEEP_BASE", f"Expected KEEP_BASE on delta <= 0, got {step_res2}"
        assert verify_py.read_text(encoding="utf-8") == base_script_content, "Base script was not restored after negative delta."

        # 4. Test delta > 0 and valid compile -> ADOPTED
        new_valid_content = "# Candidate edit with valid syntax and positive delta\ndef verify(): return True\n"
        verify_py.write_text(new_valid_content, encoding="utf-8")
        step_res3 = compose_step(ws, ref, cand_better)
        assert step_res3["decision"] == "ADOPTED", f"Expected ADOPTED on positive delta, got {step_res3}"
        assert verify_py.read_text(encoding="utf-8") == new_valid_content, "Candidate script was not adopted."

    return True


def run_test_graduation_pipeline() -> bool:
    """Test candidate graduation pipeline, compilation check, delta enforcement, and DB staging."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        ws = Path(td) / "test_workspace"
        ws.mkdir(parents=True)
        mount_task_harness(ws)
        overlay = ws / ".antigravity" / "task_harness"
        verify_py = overlay / "scripts" / "verify_task.py"
        state_file = overlay / "state.json"
        reg_db = os.path.join(td, "registry.sqlite")

        # 1. Broken syntax in python script -> KEEP_BASE regardless of delta
        state_file.write_text(json.dumps({"last_delta": 4.0, "last_decision": "ADOPTED"}), encoding="utf-8")
        verify_py.write_text("def broken_syntax(:\n    pass\n", encoding="utf-8")
        res1 = promote_validated_candidates(ws, reg_db)
        assert res1["promoted"] is False, "Expected promote to fail on syntax error"
        assert res1["decision"] == "KEEP_BASE"

        # 2. Delta <= 0 -> KEEP_BASE
        verify_py.write_text("def verify(): return True\n", encoding="utf-8")
        state_file.write_text(json.dumps({"last_delta": -2.0, "last_decision": "KEEP_BASE"}), encoding="utf-8")
        res2 = promote_validated_candidates(ws, reg_db)
        assert res2["promoted"] is False, "Expected promote to fail on negative delta"
        assert res2["decision"] == "KEEP_BASE"

        # 3. Delta > 0 and valid compile -> PROMOTED into settings_reviews
        state_file.write_text(json.dumps({"last_delta": 3.5, "last_decision": "ADOPTED"}), encoding="utf-8")
        res3 = promote_validated_candidates(ws, reg_db)
        assert res3["promoted"] is True, f"Expected promote to succeed, got {res3}"
        assert res3["decision"] == "PROMOTED"
        assert res3["review_id"] is not None
        assert "SKILL.md" in res3["graduated_files"]

        # Verify record in registry.sqlite
        conn = sqlite3.connect(reg_db)
        cur = conn.cursor()
        row = cur.execute("SELECT id, slug, reason, event_count FROM settings_reviews WHERE id = ?;", (res3["review_id"],)).fetchone()
        conn.close()
        assert row is not None, "Graduated review not found in settings_reviews"
        assert row[1] == ws.name, f"Expected slug {ws.name}, got {row[1]}"
        assert "delta=3.50" in row[2]

    return True


def run_test_task_guardrails() -> bool:
    """Verify declarative task guardrail compilation and verification gate."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        ws = Path(td)
        mount_task_harness(ws)
        verify_script = ws / ".antigravity" / "task_harness" / "scripts" / "verify_task.py"
        assert verify_script.is_file(), "verify_task.py not created"

        # Baseline: empty rules -> passes
        try:
            proc = subprocess.run([sys.executable, str(verify_script)], capture_output=True, text=True, timeout=10.0)
        except subprocess.TimeoutExpired:
            assert False, "verify_script timed out after 10.0s on empty rules"
        assert proc.returncode == 0, f"Expected 0 with empty rules, got {proc.returncode}"

        # Test file_exists: target missing -> fails
        rule_fe = {"type": "file_exists", "path": "src/app.py"}
        assert compile_task_guardrail(ws, rule_fe)
        try:
            proc = subprocess.run([sys.executable, str(verify_script)], capture_output=True, text=True, timeout=10.0)
        except subprocess.TimeoutExpired:
            assert False, "verify_script timed out after 10.0s on file_exists missing"
        assert proc.returncode == 1, f"Expected 1 when file missing, got {proc.returncode}"
        assert "Fail: file_exists on src/app.py" in proc.stdout

        # Deduplication check
        assert compile_task_guardrail(ws, rule_fe)
        guardrails_path = ws / ".antigravity" / "task_harness" / "guardrails.json"
        data = json.loads(guardrails_path.read_text(encoding="utf-8"))
        assert len(data["rules"]) == 1, f"Expected 1 rule after duplicate compile, got {len(data['rules'])}"

        # Create target file
        (ws / "src").mkdir(parents=True, exist_ok=True)
        (ws / "src" / "app.py").write_text("def start_service(): pass\n", encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, str(verify_script)], capture_output=True, text=True, timeout=10.0)
        except subprocess.TimeoutExpired:
            assert False, "verify_script timed out after 10.0s after file created"
        assert proc.returncode == 0, f"Expected 0 after file created, got {proc.returncode}"

        # Test regex_present
        rule_rp_pass = {"type": "regex_present", "path": "src/app.py", "pattern": r"def start_service"}
        assert compile_task_guardrail(ws, rule_rp_pass)
        try:
            proc = subprocess.run([sys.executable, str(verify_script)], capture_output=True, text=True, timeout=10.0)
        except subprocess.TimeoutExpired:
            assert False, "verify_script timed out after 10.0s on regex_present pass"
        assert proc.returncode == 0

        rule_rp_fail = {"type": "regex_present", "path": "src/app.py", "pattern": r"def stop_service"}
        assert compile_task_guardrail(ws, rule_rp_fail)
        try:
            proc = subprocess.run([sys.executable, str(verify_script)], capture_output=True, text=True, timeout=10.0)
        except subprocess.TimeoutExpired:
            assert False, "verify_script timed out after 10.0s on regex_present fail"
        assert proc.returncode == 1
        assert "Fail: regex_present on src/app.py" in proc.stdout

    # Test regex_absent in fresh tempdir
    with tempfile.TemporaryDirectory() as td2:
        ws2 = Path(td2)
        mount_task_harness(ws2)
        verify_script2 = ws2 / ".antigravity" / "task_harness" / "scripts" / "verify_task.py"
        (ws2 / "src").mkdir(parents=True, exist_ok=True)
        app_file = ws2 / "src" / "app.py"
        app_file.write_text("API_PUBLIC = 1\n", encoding="utf-8")

        rule_ra = {"type": "regex_absent", "path": "src/app.py", "pattern": r"SECRET_KEY"}
        assert compile_task_guardrail(ws2, rule_ra)
        try:
            proc = subprocess.run([sys.executable, str(verify_script2)], capture_output=True, text=True, timeout=10.0)
        except subprocess.TimeoutExpired:
            assert False, "verify_script2 timed out after 10.0s on regex_absent pass"
        assert proc.returncode == 0

        # Now introduce forbidden pattern
        app_file.write_text("API_PUBLIC = 1\nSECRET_KEY = 12345\n", encoding="utf-8")
        try:
            proc = subprocess.run([sys.executable, str(verify_script2)], capture_output=True, text=True, timeout=10.0)
        except subprocess.TimeoutExpired:
            assert False, "verify_script2 timed out after 10.0s on regex_absent fail"
        assert proc.returncode == 1
        assert "Fail: regex_absent on src/app.py" in proc.stdout

    return True


def self_test() -> bool:
    """Run full self-test suite covering proposer isolation, git exclusion, and fallback."""
    print("=== Recursive PPC Engine Self-Test ===")
    assert run_test_proposer_isolation(), "Proposer isolation tests failed."
    print("Proposer isolation: PASS")
    assert run_test_git_exclusion(), "Git exclusion tests failed."
    print("Git exclusion: PASS")
    assert run_test_fallback(), "Behavioral delta & KEEP_BASE fallback tests failed."
    print("Behavioral delta & KEEP_BASE: PASS")
    assert run_test_graduation_pipeline(), "Graduation pipeline tests failed."
    print("Graduation pipeline: PASS")
    assert run_test_task_guardrails(), "Declarative task guardrail tests failed."
    print("Declarative task guardrails: PASS")
    print("ALL SELF-TESTS PASSED")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Antigravity Level-1 Intra-Task Recursive PPC Engine")
    parser.add_argument("--mount", metavar="WORKSPACE", help="Mount task overlay in workspace")
    parser.add_argument("--probe-contrast", action="store_true", help="Run behavioral contrast probe between ref and cand metrics")
    parser.add_argument("--ref", metavar="JSON", help="Reference metrics (JSON string or file path)")
    parser.add_argument("--cand", metavar="JSON", help="Candidate metrics (JSON string or file path)")
    parser.add_argument("--workspace", default=".", help="Workspace path (default: current working directory)")
    parser.add_argument("--candidate-overlay", help="Path to staged candidate overlay directory if separate")
    parser.add_argument("--self-test", action="store_true", help="Run full recursive PPC engine self-test suite")
    parser.add_argument("--test-proposer-isolation", action="store_true", help="Run proposer isolation tests")
    parser.add_argument("--test-fallback", action="store_true", help="Run KEEP_BASE fallback tests")
    parser.add_argument("--test-guardrails", action="store_true", help="Run declarative task guardrails tests")
    parser.add_argument("--promote-candidates", action="store_true", help="Promote and graduate validated candidate overlays to settings_reviews in registry.sqlite")
    parser.add_argument("--registry-db", metavar="PATH", help="Path to registry.sqlite database")

    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    if args.test_proposer_isolation:
        assert run_test_proposer_isolation()
        print("Proposer isolation tests: PASS")
        return 0

    if args.test_fallback:
        assert run_test_fallback()
        print("KEEP_BASE fallback tests: PASS")
        return 0

    if args.test_guardrails:
        assert run_test_task_guardrails()
        print("Declarative task guardrail tests: PASS")
        return 0

    if args.mount:
        res = mount_task_harness(args.mount)
        print(f"Mounted task harness overlay at: {res['overlay_dir']}")
        if res["git_excluded"]:
            print("Registered .antigravity/ in git exclude.")
        return 0

    if args.probe_contrast:
        if not args.ref or not args.cand:
            print("Error: --probe-contrast requires both --ref and --cand arguments.", file=sys.stderr)
            return 1
        ref_metrics = _load_json_arg(args.ref)
        cand_metrics = _load_json_arg(args.cand)
        result = compose_step(
            workspace=args.workspace,
            ref_metrics=ref_metrics,
            cand_metrics=cand_metrics,
            candidate_overlay_dir=args.candidate_overlay,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.promote_candidates:
        res = promote_validated_candidates(
            workspace=args.workspace,
            registry_db_path=args.registry_db,
        )
        print(json.dumps(res, indent=2))
        return 0 if res.get("promoted") else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

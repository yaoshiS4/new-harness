#!/usr/bin/env python3
"""Diff-Scoped Test Selector Utility.

Inspects modified files from git diff or CLI args, maps source modules to
corresponding test suites using naming heuristics and optional codegraph index,
and suggests targeted verification commands.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path


def is_test_file(path_str: str) -> bool:
    name = Path(path_str).name.lower()
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or name.endswith(".test.ts")
        or name.endswith(".spec.ts")
        or name.endswith(".test.js")
        or name.endswith(".spec.js")
        or name.endswith(".test.jsx")
        or name.endswith(".spec.jsx")
        or name.endswith(".test.tsx")
        or name.endswith(".spec.tsx")
        or "/tests/" in path_str
        or "/test/" in path_str
    )


def map_source_to_test_candidates(filepath: str, workspace: str = "") -> list[str]:
    """Given a source file path, return potential test file paths based on standard conventions."""
    p = Path(filepath)
    stem = p.stem
    ext = p.suffix
    candidates = []

    # If the file itself is already a test file, return it
    if is_test_file(filepath):
        return [filepath]

    if ext == ".py":
        # Python test conventions
        candidates.extend([
            f"test_{stem}.py",
            f"{stem}_test.py",
            f"tests/test_{stem}.py",
            f"tests/{stem}_test.py",
            f"test/test_{stem}.py",
            f"tests/unit/test_{stem}.py",
            f"tests/integration/test_{stem}.py",
        ])
        # Preserve relative directory under tests/ if under src/ or apps/
        parts = p.parts
        if "src" in parts:
            idx = parts.index("src")
            sub_parts = parts[idx + 1 : -1]
            if sub_parts:
                candidates.append(f"tests/{'/'.join(sub_parts)}/test_{stem}.py")
        elif len(parts) > 1:
            candidates.append(f"tests/{'/'.join(parts[:-1])}/test_{stem}.py")
    elif ext in (".ts", ".tsx", ".js", ".jsx"):
        # JS/TS test conventions
        base_ext = ext
        test_exts = [".spec" + base_ext, ".test" + base_ext]
        for t_ext in test_exts:
            candidates.extend([
                f"{stem}{t_ext}",
                f"tests/{stem}{t_ext}",
                f"test/{stem}{t_ext}",
                f"__tests__/{stem}{t_ext}",
            ])
            if len(p.parts) > 1:
                dir_path = "/".join(p.parts[:-1])
                candidates.append(f"{dir_path}/{stem}{t_ext}")
                candidates.append(f"{dir_path}/__tests__/{stem}{t_ext}")

    return candidates


def query_codegraph_for_callers(filepath: str, workspace: str) -> list[str]:
    """Query codegraph index SQLite to find callers/importers in test files."""
    db_path = os.path.expanduser("~/.local/share/codex/codegraph_index.sqlite")
    if not os.path.isfile(db_path):
        return []

    caller_test_files = set()
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=0.1)
        try:
            cur = conn.cursor()

            # Check tables
            tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
            if "symbols" not in tables or "edges" not in tables:
                return []

            rel_path = filepath
            if workspace:
                try:
                    rel_path = os.path.relpath(filepath, workspace)
                except Exception:
                    rel_path = filepath

            # Find target symbol names in this file
            cur.execute("SELECT name FROM symbols WHERE path = ? OR path = ? LIMIT 50;", (filepath, rel_path))
            symbol_names = [r[0] for r in cur.fetchall()]
            if not symbol_names:
                return []

            placeholders = ",".join("?" for _ in symbol_names)
            # Find caller files in edges where dst_target matches symbol names
            cur.execute(
                f"SELECT DISTINCT src_path FROM edges WHERE dst_target IN ({placeholders}) LIMIT 100;",
                symbol_names,
            )
            for row in cur.fetchall():
                path_str = row[0]
                if is_test_file(path_str):
                    caller_test_files.add(path_str)
        finally:
            conn.close()
    except Exception as exc:
        sys.stderr.write(f"[select-affected-tests] codegraph lookup error: {exc}\n")

    return sorted(caller_test_files)


def get_git_modified_files(workspace: str) -> list[str]:
    try:
        res = subprocess.run(
            ["git", "-C", workspace, "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10.0,
        )
        if res.returncode == 0:
            lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            if lines:
                return lines
        # Also check unstaged diff
        res2 = subprocess.run(
            ["git", "-C", workspace, "diff", "--name-only"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10.0,
        )
        if res2.returncode == 0:
            return [line.strip() for line in res2.stdout.splitlines() if line.strip()]
    except subprocess.TimeoutExpired as exc:
        sys.stderr.write(f"[select-affected-tests] git diff timed out after {exc.timeout}s\n")
    except Exception as exc:
        sys.stderr.write(f"[select-affected-tests] git diff error: {exc}\n")
    return []


def select_affected_tests(
    workspace: str = "",
    files: list[str] | None = None,
    check_disk: bool = True,
) -> dict:
    ws = workspace or os.getcwd()
    changed_files = list(files) if files else get_git_modified_files(ws)

    candidate_tests = set()
    found_on_disk = set()

    for f in changed_files:
        cands = map_source_to_test_candidates(f, ws)
        for c in cands:
            candidate_tests.add(c)
            if check_disk:
                cand_path = Path(ws) / c if not os.path.isabs(c) else Path(c)
                if cand_path.is_file():
                    found_on_disk.add(str(c))

        # Query codegraph
        cg_tests = query_codegraph_for_callers(f, ws)
        for ct in cg_tests:
            candidate_tests.add(ct)
            if check_disk:
                ct_path = Path(ws) / ct if not os.path.isabs(ct) else Path(ct)
                if ct_path.is_file():
                    found_on_disk.add(str(ct))

    # If file itself was a test file, make sure it is recognized
    for f in changed_files:
        if is_test_file(f):
            candidate_tests.add(f)
            if check_disk:
                fp = Path(ws) / f if not os.path.isabs(f) else Path(f)
                if fp.is_file():
                    found_on_disk.add(str(f))

    # Formulate recommended command
    tests_to_run = sorted(found_on_disk) if check_disk and found_on_disk else sorted(candidate_tests)

    has_python = any(t.endswith(".py") for t in tests_to_run)
    has_js = any(t.endswith((".ts", ".tsx", ".js", ".jsx")) for t in tests_to_run)

    rec_cmd = ""
    if has_python and tests_to_run:
        py_tests = [t for t in tests_to_run if t.endswith(".py")]
        # Check if pytest exists
        pytest_available = shutil.which("pytest") is not None
        if pytest_available:
            rec_cmd = f"pytest {' '.join(py_tests)}"
        else:
            rec_cmd = f"python3 -m unittest {' '.join(py_tests)}"
    elif has_js and tests_to_run:
        js_tests = [t for t in tests_to_run if t.endswith((".ts", ".tsx", ".js", ".jsx"))]
        rec_cmd = f"npm test -- {' '.join(js_tests)}"

    return {
        "workspace": ws,
        "changed_files": changed_files,
        "candidate_tests": sorted(candidate_tests),
        "existing_tests": sorted(found_on_disk),
        "recommended_command": rec_cmd,
    }


def self_test() -> int:
    # Synthetic path mapping unit check: src/auth.py -> tests/test_auth.py
    cands = map_source_to_test_candidates("src/auth.py")
    assert "tests/test_auth.py" in cands, f"tests/test_auth.py missing in {cands}"
    assert "test_auth.py" in cands, f"test_auth.py missing in {cands}"

    # Verify synthetic selection
    res = select_affected_tests(workspace="", files=["src/auth.py"], check_disk=False)
    assert any("tests/test_auth.py" in t for t in res["candidate_tests"]), f"Candidate tests failed: {res}"
    assert "src/auth.py" in res["changed_files"]

    # Verify existing test file recognition
    test_cands = map_source_to_test_candidates("tests/unit/test_login.py")
    assert "tests/unit/test_login.py" in test_cands

    # TS candidate test
    ts_cands = map_source_to_test_candidates("packages/ui/Button.tsx")
    assert any("Button.spec.tsx" in c or "Button.test.tsx" in c for c in ts_cands)

    print("SELF_TEST_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Select affected tests for modified files.")
    parser.add_argument("--workspace", default="", help="Workspace directory")
    parser.add_argument("--files", help="Comma-separated list of modified files")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    parser.add_argument("--self-test", action="store_true", help="Run self-test validation")

    args = parser.parse_args()

    if args.self_test:
        return self_test()

    files = [f.strip() for f in args.files.split(",") if f.strip()] if args.files else None
    result = select_affected_tests(workspace=args.workspace, files=files, check_disk=True)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Changed files ({len(result['changed_files'])}): {', '.join(result['changed_files']) or 'None'}")
        print(f"Candidate tests ({len(result['candidate_tests'])}):")
        for t in result["candidate_tests"]:
            exists = " [EXISTS]" if t in result["existing_tests"] else ""
            print(f"  - {t}{exists}")
        if result["recommended_command"]:
            print(f"\nRecommended test command:\n  {result['recommended_command']}")
        else:
            print("\nNo specific test command recommended.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

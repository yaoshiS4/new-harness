#!/usr/bin/env python3
"""Stage 7 Compiled Quality Control Runner.

Performs deterministic syntax verification, UI anti-slop audits,
and targeted test command execution.
"""
from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
from pathlib import Path


def _strip_comments_and_strings(content: str) -> str:
    """Strip string literals and comments to avoid bracket false positives."""
    out = []
    i = 0
    n = len(content)
    while i < n:
        c = content[i]
        # Line comment
        if c == "/" and i + 1 < n and content[i + 1] == "/":
            nl = content.find("\n", i)
            if nl == -1:
                break
            out.append("\n")
            i = nl + 1
            continue
        # Block comment
        if c == "/" and i + 1 < n and content[i + 1] == "*":
            end_bc = content.find("*/", i + 2)
            if end_bc == -1:
                break
            i = end_bc + 2
            continue
        # Quotes
        if c in ('"', "'", "`"):
            quote = c
            i += 1
            while i < n:
                if content[i] == "\\":
                    i += 2
                    continue
                if content[i] == quote:
                    i += 1
                    break
                i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _check_brackets(content: str, filepath: str) -> str | None:
    cleaned = _strip_comments_and_strings(content)
    stack = []
    pairs = {")": "(", "}": "{", "]": "["}
    for char in cleaned:
        if char in "({[":
            stack.append(char)
        elif char in ")}]":
            if not stack or stack[-1] != pairs[char]:
                return f"Unmatched closing bracket '{char}' in {filepath}"
            stack.pop()
    if stack:
        return f"Unclosed opening bracket(s) '{''.join(stack)}' in {filepath}"
    return None


def _check_conflict_markers(content: str, filepath: str) -> str | None:
    if re.search(r"^(<{7}|={7}|>{7})(?:\s.*)?$", content, re.MULTILINE):
        return f"Git conflict marker found in {filepath}"
    return None


def check_syntax(filepath: str) -> list[str]:
    errors = []
    ext = Path(filepath).suffix.lower()

    if ext == ".py":
        try:
            py_compile.compile(filepath, doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"Python syntax error in {filepath}: {e.msg if hasattr(e, 'msg') else str(e)}")
        except Exception as e:
            errors.append(f"Python compile error in {filepath}: {e}")

    elif ext == ".json":
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                json.load(f)
        except Exception as e:
            errors.append(f"JSON syntax error in {filepath}: {e}")

    elif ext in (".js", ".mjs", ".cjs"):
        node_bin = shutil.which("node")
        if node_bin:
            try:
                proc = subprocess.run([node_bin, "-c", filepath], capture_output=True, text=True, timeout=15)
                if proc.returncode != 0:
                    err = (proc.stderr or proc.stdout).strip()
                    errors.append(f"JavaScript syntax error in {filepath}: {err}")
            except Exception as e:
                errors.append(f"Node execution error in {filepath}: {e}")
        else:
            try:
                content = Path(filepath).read_text(encoding="utf-8", errors="ignore")
                cm = _check_conflict_markers(content, filepath)
                if cm:
                    errors.append(cm)
            except Exception as e:
                errors.append(f"Read error in {filepath}: {e}")

    elif ext in (".ts", ".tsx"):
        try:
            content = Path(filepath).read_text(encoding="utf-8", errors="ignore")
            cm = _check_conflict_markers(content, filepath)
            if cm:
                errors.append(cm)
            brk = _check_brackets(content, filepath)
            if brk:
                errors.append(brk)
        except Exception as e:
            errors.append(f"Read error in {filepath}: {e}")

    return errors


def check_anti_slop(filepath: str) -> list[str]:
    warnings = []
    ext = Path(filepath).suffix.lower()
    if ext not in (".tsx", ".jsx", ".vue", ".svelte"):
        return warnings

    try:
        content = Path(filepath).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return warnings

    # L-01: Nested Card inside Card
    tokens = re.findall(r"(<Card\b|</Card>)", content)
    depth = 0
    nested_detected = False
    for tok in tokens:
        if tok.startswith("<Card"):
            depth += 1
            if depth >= 2:
                nested_detected = True
        elif tok == "</Card>":
            depth = max(0, depth - 1)
    if nested_detected:
        warnings.append(f"L-01 Card Inception detected in {filepath}: Nested `<Card>` inside `<Card>`.")

    # L-16: Careless ellipsis truncation (> 5 per file)
    ellipsis_count = len(re.findall(r"\b(?:truncate|text-ellipsis|ellipsis)\b", content))
    if ellipsis_count > 5:
        warnings.append(
            f"L-16 Careless Ellipsis Truncation in {filepath}: {ellipsis_count} occurrences of "
            "truncate/text-ellipsis exceeds ceiling of 5 per file."
        )

    # D-09: Badge proliferation (> 6 per file)
    badge_count = len(re.findall(r"<Badge\b", content))
    if badge_count > 6:
        warnings.append(
            f"D-09 Badge Proliferation in {filepath}: {badge_count} `<Badge>` components "
            "exceeds ceiling of 6 per file."
        )

    # L-13: Card Soup (>= 6 occurrences of <Card or card-container)
    card_count = len(re.findall(r"(?:<Card\b|card-container)", content))
    if card_count >= 6:
        warnings.append(
            f"L-13 Card Soup in {filepath}: {card_count} card elements exceeds ceiling of 5 per file."
        )

    # T-12: Icon Fatigue (>= 10 occurrences of Icon or Lucide components)
    icon_count = len(re.findall(r"(?:<[A-Z][A-Za-z0-9]*Icon\b|<Lucide[A-Za-z0-9]+\b)", content))
    if icon_count >= 10:
        warnings.append(
            f"T-12 Icon Fatigue in {filepath}: {icon_count} icon elements exceeds ceiling of 9 per file."
        )

    # W-07: Redundant Category Over-Expressing
    w07_matches = re.findall(r"\b(Status:\s*Status|Category:\s*Category|Type:\s*Type)\b", content)
    if w07_matches:
        warnings.append(
            f"W-07 Redundant Category Over-Expressing in {filepath}: {len(w07_matches)} occurrences detected."
        )

    return warnings


def check_plan_audit_tags(filepath: str) -> list[str]:
    warnings = []
    f_low = filepath.lower()
    # Only enforce on application source code outside /.gemini/ and node_modules
    if "/.gemini/" in f_low or "/node_modules/" in f_low or "/.git/" in f_low:
        return warnings

    ext = Path(filepath).suffix.lower()
    if ext not in (
        ".py", ".ts", ".tsx", ".js", ".jsx", ".vue", ".svelte",
        ".kt", ".java", ".go", ".rs", ".c", ".cpp", ".h", ".hpp",
    ):
        return warnings

    try:
        content = Path(filepath).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return warnings

    # Match comments containing Wave [1-9], UG-[0-9]{1,2}, F[0-9]{2}
    tag_pattern = re.compile(
        r"(?:(?://|#|--)\s*|/\*+\s*|<!--\s*).*?\b(Wave\s*[1-9]|UG-0?[1-9][0-9]?|F0?[1-9][0-9]?)\b",
        re.IGNORECASE,
    )

    for line_idx, line in enumerate(content.splitlines(), start=1):
        m = tag_pattern.search(line)
        if m:
            tag = m.group(1)
            warnings.append(
                f"Zero Plan/Audit Tag Invariant: Forbidden plan/audit tag `{tag}` detected in {filepath}:{line_idx}. "
                "Never write phase numbers, task IDs, or finding tags in application code comments."
            )

    return warnings


def detect_modified_git_files() -> list[str]:
    files = set()
    try:
        res = subprocess.run(["git", "diff", "--name-only", "HEAD"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0 and res.stdout.strip():
            for line in res.stdout.strip().splitlines():
                if line.strip() and os.path.isfile(line.strip()):
                    files.add(line.strip())
    except Exception:
        pass

    if not files:
        try:
            res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and res.stdout.strip():
                for line in res.stdout.strip().splitlines():
                    if len(line) > 3:
                        p = line[3:].strip()
                        if os.path.isfile(p):
                            files.add(p)
        except Exception:
            pass

    return sorted(files)


def _get_git_diff_changed_lines(filepath: str) -> set[int]:
    """Parses git diff -U0 HEAD -- <filepath> to collect modified line numbers (1-indexed)."""
    changed_lines: set[int] = set()
    hunk_re = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
    try:
        proc = subprocess.run(
            ["git", "diff", "-U0", "HEAD", "--", filepath],
            capture_output=True,
            text=True,
            timeout=5.0,
        )
        diff_out = proc.stdout
        if proc.returncode != 0 or not diff_out:
            proc2 = subprocess.run(
                ["git", "diff", "-U0", "--", filepath],
                capture_output=True,
                text=True,
                timeout=5.0,
            )
            if proc2.returncode == 0:
                diff_out = proc2.stdout

        for line in diff_out.splitlines():
            m = hunk_re.match(line)
            if m:
                start = int(m.group(1))
                count = int(m.group(2)) if m.group(2) is not None else 1
                for l_num in range(start, start + count):
                    changed_lines.add(l_num)
    except Exception:
        pass
    return changed_lines


def _is_equivalent_or_non_semantic_line(line_text: str) -> bool:
    """Returns True for blank lines, comments, docstrings, logging, TYPE_CHECKING, and __name__ ==."""
    stripped = line_text.strip()
    if not stripped:
        return True
    if stripped.startswith(("#", "//", "/*", "*")):
        return True
    if stripped.startswith(('"""', "'''")) or stripped.endswith(('"""', "'''")):
        return True
    if any(pat in stripped for pat in ("logger.", "logging.", "print(", "console.log(")):
        return True
    if "TYPE_CHECKING" in stripped:
        return True
    if "__name__ ==" in stripped:
        return True
    return False


_MUTATION_OPS = [
    (re.compile(r"\bTrue\b"), "False", "True -> False"),
    (re.compile(r"\bFalse\b"), "True", "False -> True"),
    (re.compile(r"(?<!=)==(?!=)"), "!=", "== -> !="),
    (re.compile(r"(?<!=)!=(?!=)"), "==", "!= -> =="),
    (re.compile(r"<="), ">", "<= -> >"),
    (re.compile(r">="), "<", ">= -> <"),
    (re.compile(r"(?<![-=>])>(?![=>])"), "<", "> -> <"),
]


def _find_mutation_on_line(line_text: str) -> tuple[str, str] | None:
    for pat, repl, desc in _MUTATION_OPS:
        if pat.search(line_text):
            mutated = pat.sub(repl, line_text, count=1)
            if mutated != line_text:
                return (mutated, desc)
    return None


def run_differential_mutation_probe(
    filepath: str,
    test_cmd: str,
    timeout: float = 10.0,
    max_mutants: int = 3,
) -> dict:
    """Differential Mutation Probe.

    Backs up `filepath` in memory, mutates candidate operators on changed/code lines,
    runs `test_cmd`, and verifies that the test suite fails (mutant killed).
    Restores the exact original file bytes in a `finally:` block.
    """
    p = Path(filepath)
    if not p.is_file():
        return {
            "mutant_killed": False,
            "status": "NO_MUTATION_CANDIDATE",
            "mutants_tested": 0,
            "survived_mutants": [],
            "exit_code": 0,
            "error": f"File not found: {filepath}",
        }

    original_bytes = p.read_bytes()
    original_text = original_bytes.decode("utf-8", errors="replace")
    lines = original_text.splitlines(keepends=True)

    changed_lines = _get_git_diff_changed_lines(filepath)

    priority_line_indices = [
        i for i in range(1, len(lines) + 1)
        if i in changed_lines and not _is_equivalent_or_non_semantic_line(lines[i - 1])
    ]
    fallback_line_indices = [
        i for i in range(1, len(lines) + 1)
        if i not in changed_lines and not _is_equivalent_or_non_semantic_line(lines[i - 1])
    ]

    candidate_line_order = priority_line_indices + fallback_line_indices
    candidates: list[tuple[int, str, str]] = []

    for line_no in candidate_line_order:
        line_str = lines[line_no - 1]
        mut = _find_mutation_on_line(line_str)
        if mut:
            candidates.append((line_no, mut[0], mut[1]))
            if len(candidates) >= max_mutants:
                break

    if not candidates:
        return {
            "mutant_killed": False,
            "status": "NO_MUTATION_CANDIDATE",
            "mutants_tested": 0,
            "survived_mutants": [],
            "exit_code": 0,
        }

    tested = 0
    survived_mutants: list[str] = []
    last_exit_code = 0

    try:
        for line_no, mutated_line, desc in candidates:
            mutated_lines = list(lines)
            mutated_lines[line_no - 1] = mutated_line
            p.write_text("".join(mutated_lines), encoding="utf-8")
            try:
                proc = subprocess.run(test_cmd, shell=True, capture_output=True, text=True, timeout=timeout)
                last_exit_code = proc.returncode
                tested += 1
                if proc.returncode == 0:
                    survived_mutants.append(f"L{line_no}: {desc}")
            except subprocess.TimeoutExpired:
                tested += 1
                last_exit_code = -1
            except Exception:
                pass
            finally:
                p.write_bytes(original_bytes)
    finally:
        p.write_bytes(original_bytes)

    mutant_killed = (len(survived_mutants) == 0 and tested > 0)
    if mutant_killed:
        status = "MUTANT_KILLED"
    elif survived_mutants:
        status = "MUTANT_SURVIVED"
    else:
        status = "NO_MUTATION_CANDIDATE"

    return {
        "mutant_killed": mutant_killed,
        "status": status,
        "mutants_tested": tested,
        "survived_mutants": survived_mutants,
        "exit_code": last_exit_code,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 7 Compiled QC Runner")
    parser.add_argument("--files", nargs="*", help="Specific files to check")
    parser.add_argument("--test-cmd", help="Optional targeted test command to run")
    parser.add_argument("--mutation-probe", help="Optional file path to run differential mutation probe against")
    parser.add_argument("--strict-mutation", action="store_true", help="Fail with exit code 1 if differential mutation probe survives")
    args = parser.parse_args()

    target_files = args.files
    if not target_files:
        target_files = detect_modified_git_files()

    checked_files = []
    failures = []
    anti_slop_warnings = []
    plan_tag_warnings = []

    for f_path in target_files:
        p = Path(f_path)
        if not p.is_file():
            continue
        checked_files.append(str(p))

        # 1. Syntax check
        syntax_errs = check_syntax(str(p))
        failures.extend(syntax_errs)

        # 2. UI Anti-Slop scan
        slop_warns = check_anti_slop(str(p))
        anti_slop_warnings.extend(slop_warns)

        # 3. Plan/Audit tag scan
        tag_warns = check_plan_audit_tags(str(p))
        plan_tag_warnings.extend(tag_warns)

    # 3. Optional test command
    if args.test_cmd:
        try:
            proc = subprocess.run(args.test_cmd, shell=True, capture_output=True, text=True, timeout=60)
            if proc.returncode != 0:
                err_detail = (proc.stderr or proc.stdout).strip()[:500]
                failures.append(f"Targeted test command failed (exit code {proc.returncode}): {err_detail}")
        except subprocess.TimeoutExpired:
            failures.append("Targeted test command timed out after 60 seconds.")
        except Exception as e:
            failures.append(f"Targeted test command execution failed: {e}")

    # 4. Optional differential mutation probe
    mutation_result = None
    if args.mutation_probe:
        if not args.test_cmd:
            failures.append("Cannot run --mutation-probe without --test-cmd")
        else:
            mutation_result = run_differential_mutation_probe(args.mutation_probe, args.test_cmd)
            if mutation_result.get("status") == "MUTANT_SURVIVED":
                anti_slop_warnings.append(
                    f"Differential Mutation Warning: Mutant survived in {args.mutation_probe}. "
                    "Tests passed despite inverted logic."
                )
                if getattr(args, "strict_mutation", False):
                    failures.append(
                        f"Differential Mutation Failure: Mutant survived in {args.mutation_probe}. "
                        f"Survived: {mutation_result.get('survived_mutants', [])}"
                    )

    status = "PASS" if not failures else "FAIL"
    summary = {
        "status": status,
        "checked_files": checked_files,
        "failures": failures,
        "anti_slop_warnings": anti_slop_warnings,
        "plan_tag_warnings": plan_tag_warnings,
    }
    if mutation_result is not None:
        summary["mutation_probe"] = mutation_result
    print(json.dumps(summary, indent=2))
    sys.exit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()

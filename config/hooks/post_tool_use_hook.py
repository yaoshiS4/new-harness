#!/usr/bin/env python3
"""Antigravity PostToolUse hook for SWE-agent-style post-edit syntax smoke validation."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def _unwrap_outer_quotes(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = s.strip()
    while (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        if len(s) >= 2:
            s = s[1:-1].strip()
        else:
            break
    return s


def _normalize(path: str, cwd: str) -> str:
    cleaned = _unwrap_outer_quotes(path)
    expanded = os.path.expanduser(cleaned)
    if not os.path.isabs(expanded):
        expanded = os.path.join(cwd, expanded)
    return os.path.normpath(os.path.abspath(expanded))


def _is_test_env() -> bool:
    return "unittest" in sys.modules or "pytest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))


def _check_python_syntax(file_path: str) -> str | None:
    try:
        py_compile.compile(file_path, doraise=True)
    except py_compile.PyCompileError as err:
        msg = str(err).strip()
        return msg if msg else "Unknown Python syntax error"
    except Exception as err:
        return f"Syntax check failed: {err}"

    # Shift-Left ruff check --select F821
    enable_ruff = os.environ.get("ANTIGRAVITY_ENABLE_RUFF_F821") == "1" or not _is_test_env()
    if enable_ruff:
        ruff_bin = shutil.which("ruff")
        if ruff_bin:
            try:
                res = subprocess.run(
                    [ruff_bin, "check", "--select", "F821", "--no-cache", "--quiet", file_path],
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=1.5,
                )
                if res.returncode != 0:
                    lines = [l.strip() for l in (res.stdout or res.stderr or "").splitlines() if l.strip()]
                    if lines:
                        return f"Ruff Diagnostic (F821 undefined name): {lines[0]}"
            except Exception:
                pass
    return None


def _strip_json_comments_and_trailing_commas(content: str) -> str:
    # Match string literals or comments. Keep strings intact, strip comments.
    pattern = re.compile(r'("(?:\\.|[^"\\])*")|//[^\r\n]*|/\*[\s\S]*?\*/')

    def replacer(match: re.Match) -> str:
        if match.group(1) is not None:
            return match.group(1)
        return ""

    content = pattern.sub(replacer, content)
    # Remove trailing commas before } or ]
    content = re.sub(r',\s*([}\]])', r'\1', content)
    return content


def _check_json_syntax(file_path: str) -> str | None:
    try:
        p = Path(file_path)
        filename = p.name.lower()
        is_jsonc = (
            p.suffix.lower() == ".jsonc"
            or filename.startswith("tsconfig")
            or ".vscode" in str(p)
        )
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read()

        if is_jsonc:
            cleaned = _strip_json_comments_and_trailing_commas(raw)
            json.loads(cleaned)
        else:
            json.loads(raw)
        return None
    except json.JSONDecodeError as err:
        return f"JSONDecodeError: {err.msg} at line {err.lineno} column {err.colno}"
    except Exception as err:
        return f"JSON check failed: {err}"


def _check_node_syntax(file_path: str) -> str | None:
    node_bin = shutil.which("node")
    if not node_bin:
        return None

    try:
        res = subprocess.run(
            [node_bin, "-c", file_path],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=5,
        )
        if res.returncode != 0:
            err_output = (res.stderr or res.stdout or "").strip()
            lines = err_output.splitlines()[:4]
            return "\n".join(lines) if lines else "Syntax validation failed"
        return None
    except Exception:
        return None


def _validate_ts_tsx_syntax(file_path: str) -> str | None:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        return f"Cannot read file: {e}"

    lines = content.splitlines()
    for line_idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue
        if stripped.startswith("<<<<<<<") or stripped.startswith(">>>>>>>"):
            return f"Git conflict marker detected at line {line_idx}: {stripped[:30]}"
        if stripped.startswith("=======") and set(stripped) == {"="}:
            return f"Git conflict marker detected at line {line_idx}: {stripped[:30]}"

    stack: list[tuple[str, int, int]] = []
    i = 0
    n = len(content)
    line = 1
    col = 1
    state_stack = ["CODE"]

    last_token = ""

    while i < n:
        c = content[i]

        if c == "\n":
            line += 1
            col = 1
            i += 1
            continue

        state = state_stack[-1]

        if state == "TEMPLATE":
            if c == "`":
                state_stack.pop()
                last_token = "`"
                i += 1
                col += 1
            elif c == "$" and i + 1 < n and content[i + 1] == "{":
                stack.append(("${", line, col))
                state_stack.append("CODE")
                last_token = "${"
                i += 2
                col += 2
            elif c == "\\":
                i += 2
                col += 2
            else:
                i += 1
                col += 1
            continue

        # CODE state
        # 1. Line comment
        if c == "/" and i + 1 < n and content[i + 1] == "/":
            i += 2
            col += 2
            while i < n and content[i] != "\n":
                i += 1
                col += 1
            continue

        # 2. Block comment
        if c == "/" and i + 1 < n and content[i + 1] == "*":
            start_line, start_col = line, col
            i += 2
            col += 2
            closed = False
            while i < n:
                if content[i] == "\n":
                    line += 1
                    col = 1
                    i += 1
                elif content[i] == "*" and i + 1 < n and content[i + 1] == "/":
                    i += 2
                    col += 2
                    closed = True
                    break
                else:
                    i += 1
                    col += 1
            if not closed:
                return f"Unclosed block comment starting at {start_line}:{start_col}"
            continue

        # 3. Strings
        if c in ('"', "'"):
            q = c
            start_line, start_col = line, col
            i += 1
            col += 1
            closed = False
            while i < n:
                if content[i] == "\n":
                    break
                elif content[i] == "\\":
                    i += 2
                    col += 2
                elif content[i] == q:
                    i += 1
                    col += 1
                    closed = True
                    break
                else:
                    i += 1
                    col += 1
            if not closed:
                return f"Unclosed string literal starting at {start_line}:{start_col}"
            last_token = "STRING"
            continue

        # 4. Template literal
        if c == "`":
            state_stack.append("TEMPLATE")
            i += 1
            col += 1
            continue

        # 5. Regex literal vs division
        if c == "/":
            if i + 1 < n and content[i + 1] == ">":
                i += 1
                col += 1
                last_token = "/>"
                continue
            regex_starters = {
                "", "(", "[", "{", ",", ";", ":", "=", "==", "===", "!=", "!==",
                "+", "-", "*", "%", "<", ">", "<=", ">=", "!", "?", "&", "|", "^", "~",
                "&&", "||", "??", "=>", "return", "case", "throw", "yield", "await",
                "typeof", "void", "delete", "instanceof", "in", "default", "${"
            }
            if last_token in regex_starters:
                start_line, start_col = line, col
                start_i = i
                i += 1
                col += 1
                closed = False
                in_char_class = False
                while i < n and content[i] != "\n":
                    rc = content[i]
                    if rc == "\\":
                        i += 2
                        col += 2
                    elif rc == "[" and not in_char_class:
                        in_char_class = True
                        i += 1
                        col += 1
                    elif rc == "]" and in_char_class:
                        in_char_class = False
                        i += 1
                        col += 1
                    elif rc == "/" and not in_char_class:
                        i += 1
                        col += 1
                        while i < n and content[i].isalpha():
                            i += 1
                            col += 1
                        closed = True
                        break
                    else:
                        i += 1
                        col += 1
                if closed:
                    last_token = "REGEX"
                    continue
                else:
                    i = start_i
                    col = start_col
                    line = start_line

        # 6. Delimiters
        if c in "({[":
            stack.append((c, line, col))
            last_token = c
            i += 1
            col += 1
            continue

        if c in ")}]":
            if not stack:
                return f"Unmatched closing delimiter '{c}' at {line}:{col}"
            top, s_line, s_col = stack.pop()
            matches = {")": "(", "]": "[", "}": "{"}
            expected = matches[c]
            if top == "${" and c == "}":
                if state_stack and state_stack[-1] == "CODE":
                    state_stack.pop()
                last_token = "}"
                i += 1
                col += 1
                continue
            if top != expected:
                return f"Mismatched delimiter: expected '{top}' to match, got '{c}' at {line}:{col} (opened at {s_line}:{s_col})"
            last_token = c
            i += 1
            col += 1
            continue

        if not c.isspace():
            if c.isalnum() or c in "_$":
                start_i = i
                while i < n and (content[i].isalnum() or content[i] in "_$"):
                    i += 1
                    col += 1
                last_token = content[start_i:i]
                continue
            else:
                last_token = c

        i += 1
        col += 1

    if len(state_stack) > 1:
        return "Unclosed template literal at end of file"

    if stack:
        top, s_line, s_col = stack[-1]
        return f"Unclosed delimiter '{top}' opened at {s_line}:{s_col}"

    return None


def _get_syntax_warning_targets(payload: dict, workspace: str) -> list[Path]:
    import hashlib
    import tempfile

    conv_id = payload.get("conversationId", "")
    targets: list[Path] = []

    art_dir = payload.get("artifactDirectoryPath")
    if art_dir:
        targets.append(Path(art_dir) / "syntax_error_pending.json")

    if conv_id:
        for root in (
            "~/.gemini/antigravity-ide/brain",
            "~/.gemini/antigravity/brain",
            "~/.gemini/antigravity-cli/brain",
        ):
            targets.append(Path(f"{root}/{conv_id}/syntax_error_pending.json").expanduser())

    if workspace:
        ws_hash = hashlib.sha256(str(Path(workspace).resolve()).encode()).hexdigest()[:12]
        targets.append(Path(tempfile.gettempdir()) / f".antigravity_syntax_error_{ws_hash}.json")

    return targets


def _record_pending_syntax_warning(
    payload: dict,
    workspace: str,
    file_path: str,
    error_msg: str,
    kind: str = "syntax",
    delivered_inline: bool = False,
) -> None:
    targets = _get_syntax_warning_targets(payload, workspace)
    data: dict[str, object] = {
        "file": file_path,
        "error": error_msg,
        "kind": kind,
    }
    if delivered_inline:
        data["delivered_inline"] = True

    for target in targets:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass


def _clear_resolved_syntax_warning(payload: dict, workspace: str, file_path: str) -> None:
    for target in _get_syntax_warning_targets(payload, workspace):
        if target.is_file():
            try:
                existing = json.loads(target.read_text(encoding="utf-8"))
                if existing.get("file") == file_path:
                    target.unlink(missing_ok=True)
            except Exception:
                pass


def _resolve_conv_id(payload: dict) -> str:
    conv_id = str(payload.get("conversationId") or "").strip()
    if conv_id:
        return conv_id
    transcript_p = str(payload.get("transcriptPath") or "").strip()
    if transcript_p:
        m = re.search(r"/brain/([a-f0-9\-]+)/", transcript_p)
        if m:
            return m.group(1)
    return ""


def _find_read_ledger_for_conv(conv_id: str, transcript_p: str = "") -> Path | None:
    if not conv_id:
        return None
    tmp_dir = Path(tempfile.gettempdir())
    if transcript_p:
        t_abs = os.path.abspath(transcript_p)
        cache_key = hashlib.sha256(f"{conv_id}:{t_abs}".encode("utf-8")).hexdigest()[:16]
        direct = tmp_dir / f".antigravity_reads_{cache_key}.json"
        if direct.is_file():
            return direct

    fallback_16 = tmp_dir / f".antigravity_reads_{conv_id[:16]}.json"
    if fallback_16.is_file():
        return fallback_16

    fallback_full = tmp_dir / f".antigravity_reads_{conv_id}.json"
    if fallback_full.is_file():
        return fallback_full

    try:
        for p in tmp_dir.glob(".antigravity_reads_*.json"):
            if p.is_file():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    if data.get("conv_id") == conv_id:
                        return p
                except Exception:
                    pass
    except Exception:
        pass
    return None


_find_read_ledger = _find_read_ledger_for_conv


def _record_post_tool_syntax_failure(payload: dict, resolved_path: str, error_msg: str) -> None:
    """Record PostToolUse syntax failures into cross-session failure ledger (<10ms budget)."""
    if ("unittest" in sys.modules or "pytest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))) and not os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB"):
        return
    try:
        conv_id = _resolve_conv_id(payload)
        workspace = ""
        ws_paths = payload.get("workspacePaths", [])
        if ws_paths and isinstance(ws_paths, list):
            workspace = ws_paths[0]
        slug = os.path.basename(workspace.rstrip("/")) if workspace else "default"

        sentinel_dir = os.path.expanduser("~/.gemini/antigravity/scripts")
        if sentinel_dir not in sys.path:
            sys.path.insert(0, sentinel_dir)
        import importlib
        sentinel = importlib.import_module("burn-rate-sentinel")
        sentinel.record_harness_failure(
            conv_id=conv_id,
            failure_type="syntax_error",
            slug=slug,
            tool_name=payload.get("toolCall", {}).get("name", "write_to_file"),
            reason=f"Syntax smoke check failed on {os.path.basename(resolved_path)}",
            details=error_msg[:1000],
            severity_tier="S1_critical",
            vertex="codebase",
            session_type="subagent" if payload.get("subagentRole") else "top_level",
        )
    except Exception:
        pass


def _record_stale_read_mutation(payload: dict, target_file: str, resolved_path: str) -> None:
    conv_id = _resolve_conv_id(payload)
    if not conv_id:
        return
    transcript_p = str(payload.get("transcriptPath") or "").strip()
    tmp_dir = Path(tempfile.gettempdir())
    tracker_file = tmp_dir / f".antigravity_superseded_{conv_id}.json"
    read_ledger = _find_read_ledger_for_conv(conv_id, transcript_p)

    if not read_ledger:
        return

    try:
        ledger_data = json.loads(read_ledger.read_text(encoding="utf-8"))
        if not isinstance(ledger_data, dict):
            return
        read_files = ledger_data.get("files", {})
        if not isinstance(read_files, dict):
            return

        norm_resolved = os.path.abspath(os.path.realpath(resolved_path)) if resolved_path else ""
        norm_target = os.path.abspath(os.path.realpath(target_file)) if target_file else ""

        is_read = False
        if resolved_path in read_files or target_file in read_files:
            is_read = True
        elif norm_resolved:
            for rf in read_files:
                if os.path.abspath(os.path.realpath(rf)) == norm_resolved:
                    is_read = True
                    break
        elif norm_target:
            for rf in read_files:
                if os.path.abspath(os.path.realpath(rf)) == norm_target:
                    is_read = True
                    break

        if is_read:
            for rf, rf_entry in list(read_files.items()):
                if isinstance(rf_entry, dict):
                    norm_rf = os.path.abspath(os.path.realpath(rf))
                    if norm_rf in (norm_resolved, norm_target) or rf in (resolved_path, target_file):
                        rf_entry["file_slices"] = []
                        rf_entry["slice_ranges"] = []
                        rf_entry["reads_since_edit"] = 0
            try:
                tmp_rl = read_ledger.with_suffix(".tmp")
                tmp_rl.write_text(json.dumps(ledger_data, indent=2), encoding="utf-8")
                tmp_rl.replace(read_ledger)
            except Exception:
                pass
        else:
            return
    except Exception:
        return

    lines_count = 0
    try:
        if os.path.isfile(resolved_path):
            with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
                lines_count = sum(1 for _ in f)
    except Exception:
        pass

    data: dict = {}
    if tracker_file.is_file():
        try:
            data = json.loads(tracker_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                data = {}
        except Exception:
            data = {}

    file_key = target_file if target_file else resolved_path
    data[file_key] = {
        "mutated_at": time.time(),
        "lines": lines_count,
        "delivered": False,
    }

    try:
        tmp_target = tracker_file.with_suffix(".tmp")
        tmp_target.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp_target.replace(tracker_file)
    except Exception:
        pass


def _check_anti_slop(filepath: str) -> list[str]:
    warnings = []
    ext = Path(filepath).suffix.lower()
    if ext not in (".tsx", ".jsx", ".vue", ".svelte"):
        return warnings

    try:
        content = Path(filepath).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return warnings

    # L-01: Nested Card inside Card (self-closing <Card ... /> must not increase depth)
    card_tags = re.findall(r"(<Card\b[^>]*\/?>|</Card>)", content)
    depth = 0
    nested_detected = False
    for tag in card_tags:
        if tag.startswith("</Card"):
            depth = max(0, depth - 1)
        elif tag.rstrip().endswith("/>"):
            # Self-closing <Card ... /> does not increase nesting depth
            continue
        elif tag.startswith("<Card"):
            depth += 1
            if depth >= 2:
                nested_detected = True
    if nested_detected:
        warnings.append(f"L-01 Card Inception detected in {os.path.basename(filepath)}: Nested `<Card>` inside `<Card>`.")

    # L-16: Careless ellipsis truncation (> 5 per file)
    ellipsis_count = len(re.findall(r"\b(?:truncate|text-ellipsis|ellipsis)\b", content))
    if ellipsis_count > 5:
        warnings.append(
            f"L-16 Careless Ellipsis Truncation in {os.path.basename(filepath)}: {ellipsis_count} occurrences of "
            "truncate/text-ellipsis exceeds ceiling of 5 per file."
        )

    # D-09: Badge proliferation (> 6 per file)
    badge_count = len(re.findall(r"<Badge\b", content))
    if badge_count > 6:
        warnings.append(
            f"D-09 Badge Proliferation in {os.path.basename(filepath)}: {badge_count} `<Badge>` components "
            "exceeds ceiling of 6 per file."
        )

    # L-13: Card Soup (>= 6 card container tags in a single file)
    card_container_count = len(re.findall(r"<Card\b|className=[^\"']*card-container", content))
    if card_container_count >= 6:
        warnings.append(
            f"L-13 Card Soup in {os.path.basename(filepath)}: {card_container_count} card containers "
            "detected (>= 6 ceiling). Consider grouped tables, definition lists, or master-detail views."
        )

    # T-12: Icon Fatigue (>= 10 icon usages in a single file)
    icon_count = len(re.findall(r"<[A-Z][A-Za-z0-9]*Icon\b|<Lucide[A-Za-z0-9]+\b", content))
    if icon_count >= 10:
        warnings.append(
            f"T-12 Icon Fatigue in {os.path.basename(filepath)}: {icon_count} icon elements "
            "detected (>= 10 ceiling). Reserve icons for high-signal affordances."
        )

    # W-07: Redundant Category Over-Expressing
    w07_matches = re.findall(r"\b(Status:\s*Status|Category:\s*Category|Type:\s*Type)\b", content, re.IGNORECASE)
    if w07_matches:
        warnings.append(
            f"W-07 Redundant Category Over-Expressing in {os.path.basename(filepath)}: "
            f"Detected redundant label repetition ({', '.join(set(w07_matches))})."
        )

    return warnings


def _check_plan_audit_tags(filepath: str) -> list[str]:
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

    # Match comments containing UG-digits, two-digit F-tags (excluding function keys), or Wave tag style
    tag_pattern = re.compile(
        r"(?:(?://|#|--)\s*|/\*+\s*|<!--\s*).*?(\bUG-\d+\b|\bF(?:0[1-9]|1[3-9]|[2-9]\d)\b|\b(?:Phase|Audit)\b[^\n\r]*?\bWave\s*\d+\b|\bWave\s*\d+\s*[:—\-])",
        re.IGNORECASE,
    )

    for line_idx, line in enumerate(content.splitlines(), start=1):
        m = tag_pattern.search(line)
        if m:
            tag = m.group(1)
            warnings.append(
                f"Zero Plan/Audit Tag Invariant: Forbidden plan/audit tag `{tag}` in {os.path.basename(filepath)}:{line_idx}. "
                "Never write phase numbers, task IDs, or finding tags in application code comments."
            )

    return warnings


_UNFINISHED_STUB_PATTERNS = [
    re.compile(r"\braise\s+NotImplementedError\b"),
    re.compile(r'\bthrow\s+new\s+Error\s*\(\s*["\']Not implemented["\']\s*\)', re.IGNORECASE),
    re.compile(r"(?:#|//)\s*TODO:\s*implement\b", re.IGNORECASE),
]


def _check_unfinished_stubs(filepath: str, args: dict) -> list[str]:
    warnings = []
    base_low = os.path.basename(filepath).lower()
    if (
        "test" in base_low
        or "spec" in base_low
        or base_low.endswith(".d.ts")
        or "/.gemini/" in filepath
    ):
        return warnings

    new_content = (
        args.get("Replacement")
        or args.get("ReplacementContent")
        or args.get("CodeContent")
        or args.get("Content")
        or ""
    )
    if not isinstance(new_content, str) or not new_content.strip():
        return warnings

    if re.search(r"@abstractmethod|abstract\s+(?:class|def|\w+\s*\()", new_content):
        return warnings

    for pat in _UNFINISHED_STUB_PATTERNS:
        match = pat.search(new_content)
        if match:
            matched_str = match.group(0)
            warnings.append(
                f"Unfinished Implementation Stub: Found newly added placeholder stub in {os.path.basename(filepath)}: '{matched_str}'. "
                "Implement production logic or remove stub before finalizing."
            )
            break
    return warnings


def _transform_mermaid_markdown(file_path: str) -> None:
    """User decision: Stop mutating markdown files on disk."""
    pass


def _classify_bug_category(
    error_type: str = "",
    message: str = "",
    reason: str = "",
    vertex: str = "",
) -> str:
    """Classify failure signature into one of the 8 canonical bug categories."""
    text = f"{error_type} {message} {reason}".strip()
    text_lower = text.lower()

    if any(k in text_lower for k in ("test_assertion_lock", "test_lock_violation", "lease_violation", "tautological", "oracle custody")):
        return "SPEC_GAMING_ATTEMPT"
    if any(k in text_lower for k in ("nonetype", "undefined is not", "null pointer")):
        return "NULL_UNDEFINED_ACCESS"
    if any(k in text_lower for k in ("importerror", "modulenotfounderror", "cannot find module")):
        return "IMPORT_DEPENDENCY_GAP"
    if any(k in text_lower for k in ("filenotfounderror", "permissionerror", "ioerror", "oserror")):
        return "RESOURCE_IO_LIFECYCLE"
    if any(k in text_lower for k in ("indexerror", "keyerror", "zerodivisionerror", "out of range", "boundary")):
        return "BOUNDARY_INDEX_ERROR"
    if any(k in text_lower for k in ("timeouterror", "deadlock", "database is locked", "lock")):
        return "ASYNC_CONCURRENCY_LOCK"
    if "assertionerror" in text_lower or "assert " in text_lower:
        return "LOGIC_ASSERTION_DRIFT"
    if any(k in text_lower for k in ("typeerror", "attributeerror", "e0308")) or bool(re.search(r'\bTS\d+\b', text, re.IGNORECASE)):
        return "TYPE_CONTRACT_MISMATCH"
    if (vertex or "").lower() == "codebase":
        return "LOGIC_ASSERTION_DRIFT"
    return ""


def _extract_structured_command_feedback(output_text: str) -> dict:
    failures = []
    if not output_text or not isinstance(output_text, str):
        return {"failures": []}

    # 1. Python tracebacks: File "...", line X\n ... Error: message
    py_tb_re = re.compile(
        r'File "(?P<file>[^"]+)", line (?P<line>\d+)(?:, in [^\n]+)?\n(?:\s+.*\n)*?(?P<error_type>[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception|Warning|Interrupt))(?::\s*(?P<message>[^\n]+))?',
        re.MULTILINE,
    )
    for m in py_tb_re.finditer(output_text):
        f = m.group("file").strip()
        l = int(m.group("line"))
        et = m.group("error_type").strip()
        msg = (m.group("message") or "").strip()
        failures.append({
            "file": f,
            "line": l,
            "error_type": et,
            "message": msg,
            "failure_label": f"{et} at {os.path.basename(f)}:{l}",
            "bug_category": _classify_bug_category(et, msg),
        })

    # 2. Pytest test failure lines and headers
    pytest_re = re.compile(
        r'FAILED\s+(?P<file>[^:\s\n]+)(?:::[^\s\n]+)?\s*-\s*(?P<error_type>[A-Za-z_][A-Za-z0-9_.]*):\s*(?P<message>[^\n]+)',
        re.MULTILINE,
    )
    for m in pytest_re.finditer(output_text):
        f = m.group("file").strip()
        et = m.group("error_type").strip()
        msg = m.group("message").strip()
        failures.append({
            "file": f,
            "line": None,
            "error_type": et,
            "message": msg,
            "failure_label": f"{et} at {os.path.basename(f)}",
            "bug_category": _classify_bug_category(et, msg),
        })

    pytest_loc_re = re.compile(
        r'^(?P<file>[^\s:\n]+\.py):(?P<line>\d+):\s*(?P<error_type>[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception))(?::\s*(?P<message>[^\n]+))?',
        re.MULTILINE,
    )
    for m in pytest_loc_re.finditer(output_text):
        f = m.group("file").strip()
        l = int(m.group("line"))
        et = m.group("error_type").strip()
        msg = (m.group("message") or "").strip()
        failures.append({
            "file": f,
            "line": l,
            "error_type": et,
            "message": msg,
            "failure_label": f"{et} at {os.path.basename(f)}:{l}",
            "bug_category": _classify_bug_category(et, msg),
        })

    # 3. TypeScript errors: src/foo.ts(10,5): error TS1234: ... or src/foo.ts:10:5 - error TS1234: ...
    ts_re = re.compile(
        r'^(?P<file>[^\s:(]+?)(?:\((?P<line>\d+),\d+\)|:(?P<line2>\d+)(?::\d+)?)\s*[:-]\s*error\s+(?P<error_type>TS\d+):\s*(?P<message>[^\n]+)',
        re.MULTILINE,
    )
    for m in ts_re.finditer(output_text):
        f = m.group("file").strip()
        l_str = m.group("line") or m.group("line2")
        l = int(l_str) if l_str else None
        et = m.group("error_type").strip()
        msg = m.group("message").strip()
        failures.append({
            "file": f,
            "line": l,
            "error_type": et,
            "message": msg,
            "failure_label": f"{et} at {os.path.basename(f)}:{l}" if l else f"{et} at {os.path.basename(f)}",
            "bug_category": _classify_bug_category(et, msg),
        })

    # 4. Rust compiler errors: error[E0425]: ...\n  --> path:line:col
    rust_re = re.compile(
        r'error\[(?P<error_type>E\d+)\]:\s*(?P<message>[^\n]+)\n\s*-->\s*(?P<file>[^:\s\n]+):(?P<line>\d+):(?P<col>\d+)',
        re.MULTILINE,
    )
    for m in rust_re.finditer(output_text):
        f = m.group("file").strip()
        l = int(m.group("line"))
        et = m.group("error_type").strip()
        msg = m.group("message").strip()
        failures.append({
            "file": f,
            "line": l,
            "error_type": et,
            "message": msg,
            "failure_label": f"{et} at {os.path.basename(f)}:{l}",
            "bug_category": _classify_bug_category(et, msg),
        })

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for fail in failures:
        key = (fail["file"], fail["line"], fail["error_type"])
        if key not in seen:
            seen.add(key)
            if fail["error_type"] == "AssertionError" and "assert" in fail.get("message", ""):
                m_assert = re.search(r'assert\s+(?P<obs>.+?)\s*==\s*(?P<exp>.+)', fail["message"])
                if m_assert:
                    fail["observed"] = m_assert.group("obs").strip()
                    fail["expected"] = m_assert.group("exp").strip()
            deduped.append(fail)

    result = {
        "failures": deduped,
        "raw_summary": output_text[:2000] if output_text else "",
    }
    if deduped:
        first = deduped[0]
        result["file"] = first["file"]
        result["line"] = first["line"]
        result["error_type"] = first["error_type"]
        result["message"] = first["message"]
        result["failure_label"] = first["failure_label"]
        result["bug_category"] = first.get("bug_category", "")
        if "observed" in first:
            result["observed"] = first["observed"]
        if "expected" in first:
            result["expected"] = first["expected"]
    return result


def _query_matching_remedies(feedback: dict) -> list[str]:
    remedies: list[str] = []
    try:
        env_test_db = os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB")
        if env_test_db:
            db_path = os.path.abspath(env_test_db)
        else:
            candidates = [
                os.path.expanduser("~/.local/share/codex/projects/registry.sqlite"),
                os.path.expanduser("~/.gemini/antigravity/skillbank/registry.sqlite"),
            ]
            db_path = None
            for candidate in candidates:
                if os.path.isfile(candidate):
                    db_path = candidate
                    break
            if not db_path:
                return remedies

        if not os.path.isfile(db_path):
            return remedies

        import sqlite3
        conn = sqlite3.connect(db_path, timeout=0.05)
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA busy_timeout=50;")
            tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            if "harness_failures" not in tables:
                return remedies

            cols = {r[1] for r in cursor.execute("PRAGMA table_info(harness_failures)").fetchall()}
            if "remedy" not in cols:
                return remedies

            first_fail = feedback.get("failures", [{}])[0] if feedback.get("failures") else feedback
            err_type = str(first_fail.get("error_type") or "").strip()
            bug_cat = str(first_fail.get("bug_category") or "").strip()

            has_bug_cat = "bug_category" in cols
            has_err_type = "error_type" in cols

            if has_bug_cat and has_err_type and (err_type or bug_cat):
                rows = cursor.execute(
                    """
                    SELECT remedy FROM harness_failures
                    WHERE (error_type = ? OR (bug_category != '' AND bug_category = ?))
                      AND remedy IS NOT NULL AND remedy != ''
                    ORDER BY id DESC LIMIT 3
                    """,
                    (err_type, bug_cat),
                ).fetchall()
            elif has_err_type and err_type:
                rows = cursor.execute(
                    """
                    SELECT remedy FROM harness_failures
                    WHERE error_type = ?
                      AND remedy IS NOT NULL AND remedy != ''
                    ORDER BY id DESC LIMIT 3
                    """,
                    (err_type,),
                ).fetchall()
            else:
                rows = []

            for r in rows:
                rem = (r[0] or "").strip()
                if rem and rem not in remedies:
                    remedies.append(rem)
        finally:
            conn.close()
    except Exception:
        pass
    return remedies


def _record_fail_to_pass_remedy(conv_id: str, feedback_file: str, payload: dict) -> None:
    """Harvest fail-to-pass remediation on successful command after prior failure."""
    try:
        if not os.path.isfile(feedback_file):
            return

        feedback_data: dict = {}
        try:
            with open(feedback_file, "r", encoding="utf-8") as f:
                feedback_data = json.load(f)
        except Exception:
            return

        if not isinstance(feedback_data, dict):
            return

        failures = feedback_data.get("failures", [])
        first_fail = failures[0] if (isinstance(failures, list) and failures) else feedback_data
        err_type = str(first_fail.get("error_type") or "").strip()
        msg = str(first_fail.get("message") or "").strip()
        bug_cat = str(first_fail.get("bug_category") or "").strip()
        if not bug_cat:
            bug_cat = _classify_bug_category(err_type, msg)

        failure_label = str(first_fail.get("failure_label") or "").strip()
        if not failure_label:
            file_name = os.path.basename(str(first_fail.get("file") or "codebase"))
            line_num = first_fail.get("line")
            failure_label = f"{err_type} at {file_name}:{line_num}" if line_num else f"{err_type} at {file_name}"

        # Find last mutated file from .antigravity_mutations_{conv_id}.json
        tmp_dir = tempfile.gettempdir()
        mutations_file = os.path.join(tmp_dir, f".antigravity_mutations_{conv_id}.json")
        mutated_basename = "codebase"
        if os.path.isfile(mutations_file):
            try:
                with open(mutations_file, "r", encoding="utf-8") as mf:
                    m_data = json.load(mf)
                if isinstance(m_data, list) and m_data:
                    mutated_basename = os.path.basename(str(m_data[-1]))
                elif isinstance(m_data, dict):
                    m_files = m_data.get("files", list(m_data.keys()))
                    if isinstance(m_files, list) and m_files:
                        mutated_basename = os.path.basename(str(m_files[-1]))
            except Exception:
                pass

        remedy = f"Resolved {err_type} ({bug_cat}) at {failure_label} via fix in {mutated_basename}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Resolve destination registry DB
        env_test_db = os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB")
        if env_test_db:
            db_path = os.path.abspath(env_test_db)
        else:
            candidates = [
                os.path.expanduser("~/.local/share/codex/projects/registry.sqlite"),
                os.path.expanduser("~/.gemini/antigravity/skillbank/registry.sqlite"),
            ]
            db_path = None
            for candidate in candidates:
                if os.path.isfile(candidate):
                    db_path = candidate
                    break
            if not db_path:
                db_path = candidates[0]

        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        import sqlite3
        conn = sqlite3.connect(db_path, timeout=3.0)
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA busy_timeout=3000;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS harness_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    session_type TEXT DEFAULT 'top_level',
                    vertex TEXT NOT NULL DEFAULT 'hook',
                    failure_type TEXT NOT NULL,
                    tool_name TEXT DEFAULT '',
                    severity_tier TEXT NOT NULL DEFAULT 'S3_minor',
                    severity_weight REAL NOT NULL DEFAULT 0.01,
                    reason TEXT NOT NULL,
                    details TEXT DEFAULT '',
                    bug_category TEXT DEFAULT '',
                    error_type TEXT DEFAULT '',
                    remedy TEXT DEFAULT '',
                    settings_review_id INTEGER,
                    resolved_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            cur.execute("PRAGMA table_info(harness_failures);")
            cols = {r[1] for r in cur.fetchall()}
            if "bug_category" not in cols:
                cur.execute("ALTER TABLE harness_failures ADD COLUMN bug_category TEXT DEFAULT '';")
            if "error_type" not in cols:
                cur.execute("ALTER TABLE harness_failures ADD COLUMN error_type TEXT DEFAULT '';")
            if "remedy" not in cols:
                cur.execute("ALTER TABLE harness_failures ADD COLUMN remedy TEXT DEFAULT '';")

            cur.execute(
                """
                INSERT INTO harness_failures (
                    conv_id, slug, session_type, vertex, failure_type,
                    tool_name, severity_tier, severity_weight, reason, details,
                    bug_category, error_type, remedy, resolved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    conv_id,
                    "default",
                    "top_level",
                    "codebase",
                    "test_command_failure",
                    "run_command",
                    "S3_minor",
                    0.01,
                    f"Fail-to-pass remediation: {remedy}",
                    msg[:1000],
                    bug_cat,
                    err_type,
                    remedy,
                    now_iso,
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


_VERIFICATION_COMMAND_REGEX = re.compile(
    r"""(?xi)
    \b(?:
        py(?:test|\.test)|unittest|vitest|jest|mocha|cypress|playwright|
        tsc|ruff|flake8|mypy|pyright|py_compile|
        verify-oracle|verify-harness|test-3-round|run-compiled-qc|validate-harness-tree|
        cargo\s+(?:test|check|clippy|audit)|
        npm\s+(?:(?:run\s+)?(?:test|check|lint|build|typecheck)|audit)|
        pnpm\s+(?:(?:run\s+)?(?:test|check|lint|build|typecheck)|audit|run)|
        yarn\s+(?:(?:run\s+)?(?:test|check|lint|build|typecheck)|audit|test)|
        bun\s+(?:(?:run\s+)?(?:test|check|lint|build|typecheck)|audit|test)|
        python3?\s+-m\s+(?:unittest|pytest|py_compile)
    )\b"""
)


def _is_matching_remediation_command(raw_cmd: str, target_file: str) -> bool:
    if not raw_cmd or not _VERIFICATION_COMMAND_REGEX.search(raw_cmd):
        return False
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            prior_data = json.load(f)
    except Exception:
        return False
    if not isinstance(prior_data, dict):
        return False

    prior_cmd = str(prior_data.get("command") or "").strip()
    prior_runner_match = _VERIFICATION_COMMAND_REGEX.search(prior_cmd) if prior_cmd else None
    cur_runner_match = _VERIFICATION_COMMAND_REGEX.search(raw_cmd)
    if prior_runner_match and cur_runner_match:
        p_tok = prior_runner_match.group(0).lower().strip()
        c_tok = cur_runner_match.group(0).lower().strip()
        if p_tok == c_tok or (("test" in p_tok or "pytest" in p_tok or "unittest" in p_tok) and ("test" in c_tok or "pytest" in c_tok or "unittest" in c_tok)):
            return True

    failures = prior_data.get("failures", [])
    if isinstance(failures, list):
        for fail in failures:
            if isinstance(fail, dict):
                f_path = str(fail.get("file") or "").strip()
                if f_path:
                    base = os.path.basename(f_path)
                    if base and base in raw_cmd:
                        return True

    if not prior_cmd and cur_runner_match:
        return True

    return False


_ZERO_WIDTH_BIDI_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\u2060-\u2069\ufeff]")
_HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->|<!--|-->")
_INJECTION_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("system_tag", re.compile(r"</?\s*(?:system|system_message|user_request|assistant|developer)\s*>", re.IGNORECASE), "[DEFANGED_ROLE_TAG]"),
    ("inst_tag", re.compile(r"\[/?INST\]|<<\s*/?\s*SYS\s*>>", re.IGNORECASE), "[DEFANGED_INST_TAG]"),
    ("fence_escape", re.compile(r"</?\s*untrusted_external_content\s*>", re.IGNORECASE), "[DEFANGED_FENCE_TAG]"),
    (
        "ignore_instructions",
        re.compile(
            r"\b(?:IGNORE|DISREGARD|FORGET|OVERRIDE)\s+(?:ALL\s+)?(?:PREVIOUS|PRIOR|ABOVE|SYSTEM)\s+(?:INSTRUCTIONS|PROMPTS|DIRECTIONS|RULES)\b",
            re.IGNORECASE,
        ),
        "[DEFANGED_PROMPT_INJECTION]",
    ),
]


def defang_untrusted_text(
    text: str,
    author: str = "",
    trusted_users: set[str] | None = None,
    trusted_orgs: set[str] | None = None,
    author_org: str = "",
) -> dict[str, object]:
    """Sanitize untrusted external text (GitHub issues, PRs, comments) against prompt injection."""
    raw = str(text or "")
    env_users = {
        u.strip().lstrip("@").lower()
        for u in os.environ.get("GITHUB_TRUSTED_USERS", "").split(",")
        if u.strip()
    }
    env_orgs = {
        o.strip().lstrip("@").lower()
        for o in os.environ.get("GITHUB_TRUSTED_ORGS", "").split(",")
        if o.strip()
    }
    eff_users = env_users | {u.strip().lstrip("@").lower() for u in (trusted_users or set()) if u.strip()}
    eff_orgs = env_orgs | {o.strip().lstrip("@").lower() for o in (trusted_orgs or set()) if o.strip()}

    author_clean = str(author or "").strip().lstrip("@").lower()
    org_clean = str(author_org or "").strip().lstrip("@").lower()
    if not org_clean and "/" in author_clean:
        org_clean, author_clean = author_clean.split("/", 1)

    if (author_clean and author_clean in eff_users) or (org_clean and org_clean in eff_orgs):
        return {
            "text": raw,
            "defanged_text": raw,
            "raw_defanged": raw,
            "trusted": True,
            "author": author,
            "author_org": author_org,
            "injections_neutralized": 0,
            "zero_width_stripped": 0,
            "triggers": [],
        }

    triggers: list[str] = []
    injections_neutralized = 0

    zw_matches = _ZERO_WIDTH_BIDI_RE.findall(raw)
    zero_width_stripped = len(zw_matches)
    cleaned = _ZERO_WIDTH_BIDI_RE.sub("", raw)
    if zero_width_stripped > 0:
        triggers.append("zero_width_bidi")
        injections_neutralized += 1

    cleaned, comment_count = _HTML_COMMENT_RE.subn("[DEFANGED_HTML_COMMENT]", cleaned)
    if comment_count > 0:
        triggers.append("html_comment")
        injections_neutralized += comment_count

    for trig_name, pat, replacement in _INJECTION_PATTERNS:
        cleaned, count = pat.subn(replacement, cleaned)
        if count > 0:
            triggers.append(trig_name)
            injections_neutralized += count

    wrapped = f"<untrusted_external_content>\n{cleaned}\n</untrusted_external_content>"
    return {
        "text": wrapped,
        "defanged_text": wrapped,
        "raw_defanged": cleaned,
        "trusted": False,
        "author": author,
        "author_org": author_org,
        "injections_neutralized": injections_neutralized,
        "zero_width_stripped": zero_width_stripped,
        "triggers": triggers,
    }


def _scan_cloned_repo_hazards(raw_cmd: str, payload: dict) -> list[str]:
    ws_paths = payload.get("workspacePaths", [])
    workspace = ""
    if ws_paths and isinstance(ws_paths, list) and ws_paths[0]:
        workspace = str(ws_paths[0]).strip()
    if not workspace:
        workspace = os.getcwd()

    candidate_dirs: list[str] = []
    if workspace and os.path.isdir(workspace):
        candidate_dirs.append(os.path.abspath(workspace))
        try:
            for entry in os.scandir(workspace):
                if entry.is_dir(follow_symlinks=False) and not entry.name.startswith("."):
                    candidate_dirs.append(os.path.abspath(entry.path))
        except Exception:
            pass

    for tok in re.split(r"[\s;&|\"']+", raw_cmd):
        tok = tok.strip()
        if not tok or tok.startswith("-"):
            continue
        if os.path.isabs(tok) and os.path.isdir(tok):
            candidate_dirs.append(os.path.abspath(tok))
        elif workspace:
            joined = os.path.abspath(os.path.join(workspace, tok))
            if os.path.isdir(joined):
                candidate_dirs.append(joined)
            base = tok.rstrip("/").rsplit("/", 1)[-1]
            if base.endswith(".git"):
                base = base[:-4]
            if base:
                repo_dir = os.path.abspath(os.path.join(workspace, base))
                if os.path.isdir(repo_dir):
                    candidate_dirs.append(repo_dir)

    seen_dirs: set[str] = set()
    unique_dirs: list[str] = []
    for d in candidate_dirs:
        if d not in seen_dirs:
            seen_dirs.add(d)
            unique_dirs.append(d)

    hazard_rel_paths = (
        ".agents/hooks.json",
        ".agent/hooks.json",
        "_agents/hooks.json",
        "_agent/hooks.json",
        ".agents/plugins",
        ".agents/skills.json",
    )
    found: list[str] = []
    seen_found: set[str] = set()
    for d in unique_dirs:
        for rel in hazard_rel_paths:
            full_p = os.path.join(d, rel)
            if rel == ".agents/plugins":
                if os.path.isdir(full_p):
                    display_p = full_p.rstrip("/") + "/"
                    if display_p not in seen_found:
                        seen_found.add(display_p)
                        found.append(display_p)
            elif os.path.exists(full_p):
                if full_p not in seen_found:
                    seen_found.add(full_p)
                    found.append(full_p)
    return found


def _maybe_spillover_wire_result(tool_name: str, raw_text: str, max_chars: int = 16000) -> str | None:
    if not isinstance(raw_text, str) or len(raw_text) <= max_chars:
        return None
    if "[Wire-Boundary Spillover:" in raw_text:
        return None

    digest = hashlib.sha256(raw_text.encode("utf-8", errors="ignore")).hexdigest()[:10]
    spill_path = f"/tmp/ag_wire_spillover_{digest}.txt"
    try:
        fd = os.open(spill_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8", errors="replace") as f:
            f.write(raw_text)
        os.chmod(spill_path, 0o600)
    except Exception:
        return None

    schema_summary = ""
    stripped = raw_text.strip()
    if stripped.startswith(("{", "[")):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict):
                keys_preview = [
                    f"{k}:{type(v).__name__}" + (f"[{len(v)}]" if isinstance(v, (list, dict)) else "")
                    for k, v in list(parsed.items())[:15]
                ]
                schema_summary = f"JSON Schema: dict(keys={len(parsed)}) {{{', '.join(keys_preview)}}}"
            elif isinstance(parsed, list):
                elem_info = ""
                if parsed and isinstance(parsed[0], dict):
                    elem_keys = list(parsed[0].keys())[:12]
                    elem_info = f", item_keys={elem_keys}"
                schema_summary = f"JSON Schema: list(len={len(parsed)}{elem_info})"
        except Exception:
            pass

    fatal_re = re.compile(
        r"(?:\b(?:FATAL|ERROR|FAIL|FAILED|Exception|Traceback|SyntaxError|TypeError|ValueError|AssertionError|KeyError|IndexError|RuntimeError|panic)\b|error\[E\d+\]|error TS\d+|\[GitHub Defang Gate|\[SECURITY ALERT)",
        re.IGNORECASE,
    )
    fatal_lines: list[str] = []
    seen_fatal: set[str] = set()
    for line in raw_text.splitlines():
        sline = line.strip()
        if sline and fatal_re.search(sline):
            clipped = sline[:160]
            if clipped not in seen_fatal:
                seen_fatal.add(clipped)
                fatal_lines.append(clipped)
                if len(fatal_lines) >= 10:
                    break

    head = raw_text[:1200]
    tail = raw_text[-1000:]

    parts = [
        f"[Wire-Boundary Spillover: {tool_name} output ({len(raw_text)} chars > {max_chars}) -> {spill_path}]",
        f"Full raw output persisted at {spill_path} (mode 0600). Use targeted read_file slices or rg -n if needed.",
    ]
    if schema_summary:
        parts.append(schema_summary[:350])
    if fatal_lines:
        parts.append("Fatal/Key Diagnostics:\n" + "\n".join(f"  {fl}" for fl in fatal_lines)[:800])
    parts.append(f"--- HEAD (1200 chars) ---\n{head}")
    parts.append(f"--- TAIL (1000 chars) ---\n{tail}")

    envelope = "\n".join(parts)
    if len(envelope) > 3800:
        envelope = envelope[:3797] + "..."
    return envelope


def _handle_post_run_command(payload: dict) -> str | None:
    working_text = ""
    modified = False
    try:
        conv_id = _resolve_conv_id(payload) or "default"
        target_file = f"/tmp/.antigravity_structured_feedback_{conv_id}.json"

        tool_call = payload.get("toolCall", {})
        args = tool_call.get("args", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
        raw_cmd = str(args.get("CommandLine") or args.get("command") or "").strip()

        tool_resp = (
            payload.get("toolResponse")
            or payload.get("tool_response")
            or payload.get("toolResult")
            or payload.get("result")
            or payload.get("output")
            or {}
        )
        output_text = ""
        if isinstance(tool_resp, dict):
            output_text = str(tool_resp.get("output") or tool_resp.get("stdout") or tool_resp.get("result") or "")
            err = str(tool_resp.get("stderr") or "")
            if err:
                output_text = f"{output_text}\n{err}" if output_text else err
        elif isinstance(tool_resp, str):
            output_text = tool_resp
        else:
            output_text = str(payload.get("output") or payload.get("stderr") or payload.get("stdout") or "")

        working_text = output_text

        # (a) [GitHub Defang Gate]
        if working_text and re.search(r"(?:^|[;&|]\s*|\b)(?:gh|gh-axi)\b", raw_cmd):
            defang_res = defang_untrusted_text(working_text)
            n_inj = int(defang_res.get("injections_neutralized", 0))
            if not defang_res.get("trusted") and n_inj > 0:
                triggers = defang_res.get("triggers", [])
                untrusted_file = f"/tmp/.antigravity_untrusted_content_{conv_id}.json"
                untrusted_record = {
                    "conversation_id": conv_id,
                    "timestamp": time.time(),
                    "command": raw_cmd,
                    "injections_neutralized": n_inj,
                    "zero_width_stripped": defang_res.get("zero_width_stripped", 0),
                    "triggers": triggers,
                    "defanged_text": defang_res["defanged_text"],
                }
                with tempfile.NamedTemporaryFile("w", dir="/tmp", delete=False, encoding="utf-8") as utf:
                    json.dump(untrusted_record, utf, indent=2)
                    utemp = utf.name
                os.replace(utemp, untrusted_file)
                sys.stderr.write(
                    f"[GitHub Defang Gate] Neutralized {n_inj} "
                    f"prompt-injection pattern(s) in untrusted GitHub output ({', '.join(triggers)}).\n"
                )
                working_text = (
                    f"[GitHub Defang Gate: Neutralized {n_inj} injection pattern(s): {', '.join(triggers)}]\n"
                    f"{defang_res['defanged_text']}"
                )
                modified = True

        # (b) Untrusted Priority #1 .agents/ Clone Guard
        if re.search(r"\b(?:git\s+clone|gh\s+repo\s+clone)\b", raw_cmd):
            found_hazards = _scan_cloned_repo_hazards(raw_cmd, payload)
            if found_hazards:
                alert_banner = (
                    "[SECURITY ALERT: Untrusted Priority #1 Antigravity Customization Detected]\n"
                    f"Detected untrusted customization file(s): {', '.join(found_hazards)}"
                )
                sys.stderr.write(f"{alert_banner}\n")
                working_text = f"{alert_banner}\n{working_text}" if working_text else alert_banner
                modified = True

        # (c) Wire-Boundary Runaway Output Spillover (> 16,000 chars)
        has_wire_output = any(
            k in payload for k in ("result", "toolResponse", "tool_response", "toolResult", "output")
        )
        if has_wire_output and working_text and len(working_text) > 16000:
            spilled = _maybe_spillover_wire_result("run_command", working_text)
            if spilled is not None:
                working_text = spilled
                modified = True

        feedback = _extract_structured_command_feedback(output_text) if output_text else None
        if not feedback or not feedback.get("failures"):
            if os.path.exists(target_file):
                if _is_matching_remediation_command(raw_cmd, target_file):
                    try:
                        _record_fail_to_pass_remedy(conv_id, target_file, payload)
                    except Exception:
                        pass
                    try:
                        os.unlink(target_file)
                    except OSError:
                        pass
            return working_text if modified else None

        feedback["conversation_id"] = conv_id
        feedback["timestamp"] = time.time()
        feedback["command"] = raw_cmd

        remedies = _query_matching_remedies(feedback)
        if remedies:
            feedback["remedies"] = remedies

        with tempfile.NamedTemporaryFile("w", dir="/tmp", delete=False, encoding="utf-8") as tf:
            json.dump(feedback, tf, indent=2)
            temp_name = tf.name
        os.replace(temp_name, target_file)
    except Exception:
        pass
    return working_text if modified else None


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({}))
            return

        payload = json.loads(raw_input)
        tool_call = payload.get("toolCall", {})
        tool_name = str(tool_call.get("name", "") or "")

        if tool_name == "run_command":
            overwritten = _handle_post_run_command(payload)
            if overwritten is not None and not payload.get("error"):
                print(json.dumps({"overwriteResult": overwritten}))
            else:
                print(json.dumps({}))
            return

        if tool_name == "call_mcp_tool" or tool_name.startswith("mcp_"):
            raw_res = payload.get("result")
            if isinstance(raw_res, str) and not payload.get("error"):
                envelope = _maybe_spillover_wire_result(tool_name, raw_res)
                if envelope is not None:
                    print(json.dumps({"overwriteResult": envelope}))
                    return
            print(json.dumps({}))
            return

        EDIT_TOOLS = (
            "replace_file_content",
            "write_to_file",
            "multi_replace_file_content",
            "write_file",
            "edit_file",
        )
        if tool_name not in EDIT_TOOLS:
            print(json.dumps({}))
            return

        args = tool_call.get("args", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}

        target_file = (
            args.get("TargetFile")
            or args.get("Path")
            or args.get("target_file")
            or args.get("path")
            or args.get("file")
            or ""
        )
        if not target_file:
            print(json.dumps({}))
            return

        workspace = ""
        ws_paths = payload.get("workspacePaths", [])
        if ws_paths and isinstance(ws_paths, list):
            workspace = ws_paths[0]
        if not workspace:
            workspace = os.getcwd()

        resolved_path = _normalize(target_file, workspace)
        if not os.path.isfile(resolved_path):
            print(json.dumps({}))
            return

        ext = Path(resolved_path).suffix.lower()
        error_msg: str | None = None

        if ext == ".py":
            error_msg = _check_python_syntax(resolved_path)
        elif ext in (".json", ".jsonc"):
            error_msg = _check_json_syntax(resolved_path)
        elif ext in (".js", ".mjs", ".cjs"):
            error_msg = _check_node_syntax(resolved_path)
        elif ext in (".ts", ".tsx"):
            error_msg = _validate_ts_tsx_syntax(resolved_path)

        can_deliver_inline = ("result" in payload) and not bool(payload.get("error"))
        diag_banner: str | None = None

        if error_msg:
            diag_banner = f"[SWE-Agent Syntax Smoke Guard] Broken syntax detected in {os.path.basename(resolved_path)}:\n{error_msg}"
            sys.stderr.write(f"{diag_banner}\n")
            _record_pending_syntax_warning(
                payload, workspace, resolved_path, error_msg, kind="syntax", delivered_inline=can_deliver_inline
            )
            _record_post_tool_syntax_failure(payload, resolved_path, error_msg)
        else:
            quality_warnings: list[str] = []
            try:
                # 1. UI Anti-Slop Check (check_anti_slop)
                if ext in (".tsx", ".jsx", ".vue", ".svelte"):
                    quality_warnings.extend(_check_anti_slop(resolved_path))

                # 2. Plan/Audit Tag Check (Wave tags, UG tags, F tags)
                quality_warnings.extend(_check_plan_audit_tags(resolved_path))

                # 3. Unfinished Stub Check
                quality_warnings.extend(_check_unfinished_stubs(resolved_path, args))
            except Exception:
                pass

            if quality_warnings:
                warn_msg = "\n".join(quality_warnings)
                diag_banner = f"[Post-Tool Quality Guard] Quality warnings in {os.path.basename(resolved_path)}:\n{warn_msg}"
                sys.stderr.write(f"{diag_banner}\n")
                _record_pending_syntax_warning(
                    payload, workspace, resolved_path, warn_msg, kind="quality", delivered_inline=can_deliver_inline
                )
            else:
                _clear_resolved_syntax_warning(payload, workspace, resolved_path)

        _record_stale_read_mutation(payload, target_file, resolved_path)

        if can_deliver_inline and diag_banner:
            base_res = str(payload.get("result") or "")
            combined = f"{base_res}\n\n{diag_banner}".strip()
            print(json.dumps({"overwriteResult": combined}))
        else:
            print(json.dumps({}))

    except Exception:
        print(json.dumps({}))


if __name__ == "__main__":
    main()

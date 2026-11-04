#!/usr/bin/env python3
"""Antigravity PreToolUse hook for safety, anti-loop, and context rot enforcement."""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import fnmatch
import fcntl
import time
from pathlib import Path


def _is_test_env() -> bool:
    return "unittest" in sys.modules or "pytest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))


_TAUTOLOGICAL_ASSERT_RE = re.compile(
    r"^\s*assert\s+(?:True|1|not\s+False)\b|\bexpect\s*\(\s*(?:true|1)\s*\)\s*\.\s*toBe\s*\(\s*(?:true|1)\s*\)",
    re.MULTILINE | re.IGNORECASE,
)

_TEST_SKIP_RE = re.compile(
    r"@pytest\.mark\.(?:skip|xfail)\b|\bpytest\.xfail\s*\(|@?unittest\.(?:skip[a-zA-Z_]*|expectedFailure)\b|\b(?:it|test|describe)\.(?:skip|todo)\s*\(|\b(?:xit|xdescribe|xtest)\s*\(",
    re.MULTILINE,
)

_ZERO_EXIT_RE = re.compile(r"\b(?:sys\.exit|os\._exit|process\.exit)\s*\(\s*0\s*\)")
_SUPPRESSION_RE = re.compile(
    r"(?://\s*@ts-(?:ignore|expect-error)\b|#\s*type:\s*ignore\b|/\*\s*eslint-disable\b|//\s*eslint-disable-next-line\b)"
)
_RUNNER_INVOCATION_RE = re.compile(
    r"(?:^|[;&|(`\n]|\$\()\s*(?:set\s+[^;\n]*;\s*)*(?:(?:env\s+[\w=]+\s+|time\s+|npx\s+|uv\s+run\s+|poetry\s+run\s+|python3?\s+-m\s+)*)(?:\S*\/)?(?:py\.?test|vitest|jest|npm\s+test|pnpm\s+test|yarn\s+test|cargo\s+(?:test|check)|tsc|ruff\s+check|py_compile|unittest|verify-oracle(?:\.sh)?|test-3-round-loop(?:\.sh)?|run-compiled-qc(?:\.py)?)\b"
)
_VERIFICATION_RUNNER_RE = _RUNNER_INVOCATION_RE
_EPISTEMIC_UNCERTAINTY_RE = re.compile(
    r"\b(?:ModuleNotFoundError|ImportError|Cannot find module|TS2305|TS2339)\b|has no exported member",
    re.IGNORECASE,
)


def _detect_epistemic_uncertainty_error(error_text: str) -> str | None:
    if not error_text or not isinstance(error_text, str):
        return None
    m = _EPISTEMIC_UNCERTAINTY_RE.search(error_text)
    if m:
        return m.group(0)
    return None


def _atomic_json_read(path: str | os.PathLike, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception:
        return default


def _atomic_json_write(path: str | os.PathLike, data: any) -> bool:
    try:
        dir_name = os.path.dirname(path) or "."
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
            temp_path = tf.name
            fcntl.flock(tf.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data, tf, indent=2)
                tf.flush()
                os.fsync(tf.fileno())
            finally:
                fcntl.flock(tf.fileno(), fcntl.LOCK_UN)
        os.replace(temp_path, path)
        return True
    except Exception:
        if "temp_path" in locals() and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        return False


def _atomic_json_update(path: str | os.PathLike, update_fn, default=None):
    lock_path = f"{str(path)}.lock"
    try:
        with open(lock_path, "w") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                current_data = _atomic_json_read(path, default=default)
                updated_data = update_fn(current_data)
                _atomic_json_write(path, updated_data)
                return updated_data
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    except Exception:
        current_data = _atomic_json_read(path, default=default)
        updated_data = update_fn(current_data)
        _atomic_json_write(path, updated_data)
        return updated_data


IMAGE_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".bmp",
    ".ico",
    ".tiff",
)

SCOUT_BLOCK_DIRS = (
    ".cargo/registry",
    "node_modules",
    ".next",
    "dist",
    ".turbo",
    ".gradle",
)

PRIVACY_EXEMPT_BASENAMES = {
    ".env.example",
    ".env.sample",
    ".env.template",
    ".env.test",
}

PRIVACY_BLOCKED_EXACT_BASENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "id_rsa",
    "id_ed25519",
    ".npmrc",
    ".pypirc",
}


def _is_privacy_blocked(file_path: str) -> tuple[bool, str]:
    base = os.path.basename(file_path)
    base_low = base.lower()
    if base_low in PRIVACY_EXEMPT_BASENAMES:
        return False, ""
    if any(base_low.endswith(sfx) for sfx in (".example", ".sample", ".template", ".test")):
        return False, ""
    if base_low in PRIVACY_BLOCKED_EXACT_BASENAMES:
        return True, base
    if fnmatch.fnmatch(base_low, "*.pem") or fnmatch.fnmatch(base_low, "*.key"):
        return True, base
    return False, ""


def _check_scout_blocked_dir(path_str: str) -> str | None:
    norm_path = path_str.replace("\\", "/").strip("/")
    norm_slashed = f"/{norm_path}/"
    for d in SCOUT_BLOCK_DIRS:
        if f"/{d}/" in norm_slashed or norm_slashed.endswith(f"/{d}/") or norm_slashed == f"/{d}/":
            return d
    return None


APPLICATION_CODE_EXTENSIONS = (
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".py",
    ".kt",
    ".java",
    ".go",
    ".rs",
    ".swift",
    ".c",
    ".cpp",
    ".cs",
    ".vue",
    ".svelte",
    ".css",
    ".scss",
    ".html",
    ".sql",
    ".prisma",
    ".graphql",
)

NON_BUILDER_ROLES = (
    "pm",
    "oracle-review",
    "hallucination-auditor",
    "implementation-review",
    "frontend-qc",
    "sa",
    "senior-architect",
    "critical-planner",
    "frontend-explorer",
    "backend-explorer",
    "research-explorer",
    "user-tester",
    "doc-sync-worker",
    "librarian",
    "diff-helper",
    "test-runner",
)

DESTRUCTIVE_COMMAND_PATTERNS = [
    (
        re.compile(r"\brm\s+(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force|--force\s+--recursive)\b"),
        "Recursive force removal (rm -rf) detected",
    ),
    (
        re.compile(r"\bgit\s+reset\s+--hard\b"),
        "Destructive git hard reset detected",
    ),
    (
        re.compile(r"\bgit\s+clean\s+-[a-zA-Z]*f\b"),
        "Destructive git clean -f detected",
    ),
    (
        re.compile(r"\bgit\s+push\b"),
        "Git remote push detected",
    ),
    (
        re.compile(r"\bgit\s+restore\s+(?:\.|\*)"),
        "Wholesale git restore detected",
    ),
    (
        re.compile(r"\bgit\s+checkout\s+(?:--\s+)?(?:\.|\*)"),
        "Wholesale git checkout discard detected",
    ),
    (
        re.compile(r"\b(?:dropdb|drop\s+database|drop\s+table)\b", re.IGNORECASE),
        "Database drop statement detected",
    ),
    (
        re.compile(r"\bprisma\s+migrate\s+reset\b"),
        "Prisma database reset detected",
    ),
    (
        re.compile(r"\balembic\s+downgrade\b"),
        "Alembic database downgrade detected",
    ),
    (
        re.compile(r"\b(?:mkfs(?:\.[a-zA-Z0-9]+)?|dd\s+if=)\b"),
        "Raw disk/filesystem write command detected",
    ),
]

DEPENDENCY_MUTATION_PATTERNS = [
    (
        re.compile(r"\b(?:npm|pnpm|yarn|bun)\s+(?:install|i|add|remove|uninstall)\s+(?!-(?:-save-exact|E|-save-dev|D|-global|g|-frozen-lockfile)\b)[a-zA-Z0-9@/._-]+"),
        "Package dependency modification detected",
    ),
    (
        re.compile(r"\bpip(?:3)?\s+install\s+(?!-r\b|--requirement\b)[a-zA-Z0-9_.-]+"),
        "Python package installation detected",
    ),
    (
        re.compile(r"\bpoetry\s+add\b"),
        "Poetry package dependency modification detected",
    ),
    (
        re.compile(r"\bcargo\s+add\b"),
        "Cargo dependency modification detected",
    ),
    (
        re.compile(r"\bgo\s+get\b"),
        "Go dependency modification detected",
    ),
]


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


def _to_int(val: any) -> int | None:
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        cleaned = val.strip().strip("'\"")
        if cleaned.isdigit():
            try:
                return int(cleaned)
            except Exception:
                pass
    return None


def _count_file_lines(file_path: str) -> int:
    """Count lines in file using 64KB binary buffer with EOF newline handling (Oracle Directive D1)."""
    total = 0
    last_byte = b""
    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                total += chunk.count(b"\n")
                last_byte = chunk[-1:]
        if last_byte and last_byte != b"\n":
            total += 1
    except Exception:
        return 0
    return total


def _is_unconstrained_command(cmd_structure: str, raw_cmd: str, cwd: str = "") -> str | None:
    """Check for unconstrained commands likely to output massive unpaged text dumps (Oracle Directive D3)."""
    # 1. Pipeline or redirection exemption
    if "|" in cmd_structure or ">" in cmd_structure:
        return None

    stripped = cmd_structure.strip()

    # 2. Check for bare git log without bounding flags
    git_log_match = re.search(r"(?:^|[;&|(`\n])\s*git\s+log\b([^;&|\n]*)", stripped)
    if git_log_match:
        args_str = git_log_match.group(1).strip()
        has_bound = bool(re.search(
            r"(?:^|\s)(?:-[0-9]+|-n\s*[0-9]+|--max-count=[0-9]+|--oneline|--grep|--author|--since|--after|--until|--before|-S|-G)(?:\s|=|$)",
            args_str
        ))
        if not has_bound and (not args_str or args_str.startswith("-")):
            return (
                "Token Economy Invariant: Unbounded `git log` detected without pagination or line limits. "
                "Specify limit flags (e.g. `git log -n 20 --oneline` or `git log -5`) or pipe to `head` (e.g. `git log | head -n 30`) "
                "to prevent context saturation."
            )

    # 3. SWE-agent 50-Hit Search Flood Guard on rg and fd
    rg_match = re.search(r"(?:^|[;&|(`\n])\s*rg(?![-\w])([^;&|\n]*)", stripped)
    if rg_match:
        rg_args_str = rg_match.group(1).strip()
        has_bound = bool(re.search(
            r"(?:^|\s)(?:-m(?:=|\s|[0-9]|$)|--max-count\b|-l\b|--files-with-matches\b|-c\b|--count\b|-q\b|--quiet\b|--stats\b|-1\b|--help\b|-h\b|--version\b|-V\b)",
            rg_args_str
        ))
        if not has_bound:
            try:
                tokens = shlex.split(rg_args_str)
            except Exception:
                tokens = rg_args_str.split()
            has_single_file = False
            for tok in tokens:
                if tok.startswith("-"):
                    continue
                resolved = _normalize(tok, cwd or os.getcwd())
                if os.path.isfile(resolved):
                    has_single_file = True
                    break
            if not has_single_file:
                return (
                    "Token Economy Invariant: SWE-agent 50-Hit Search Flood Guard: Unbounded `rg` detected without output limits. "
                    "Specify output bounds (e.g. `rg -m 50 <pattern>`, `rg -l`, or `rg -c`) or pipe to `head` (e.g. `| head -n 50`) "
                    "or target a specific file to prevent token saturation."
                )

    fd_match = re.search(r"(?:^|[;&|(`\n])\s*fd(?![-\w])([^;&|\n]*)", stripped)
    if fd_match:
        fd_args_str = fd_match.group(1).strip()
        has_bound = bool(re.search(
            r"(?:^|\s)(?:--max-results\b|-1\b|--max-depth\b|-d(?:=|\s|[0-9]|$)|-l\b|-c\b|--count\b|-q\b|--quiet\b|--stats\b|--help\b|-h\b|--version\b|-V\b)",
            fd_args_str
        ))
        if not has_bound:
            try:
                tokens = shlex.split(fd_args_str)
            except Exception:
                tokens = fd_args_str.split()
            has_single_file = False
            for tok in tokens:
                if tok.startswith("-"):
                    continue
                resolved = _normalize(tok, cwd or os.getcwd())
                if os.path.isfile(resolved):
                    has_single_file = True
                    break
            if not has_single_file:
                has_invalid_m = bool(re.search(r"(?:^|\s)-m(?:\s+\d+|\d+)?\b", fd_args_str))
                clean_fd_args = re.sub(r"(?:^|\s)-m(?:\s+\d+|\d+)?\b", "", fd_args_str).strip()
                sugg_args = f" {clean_fd_args}".rstrip() if clean_fd_args else ""
                note = "Note: fd does not support -m (use --max-results instead). " if has_invalid_m else ""
                return (
                    f"Token Economy Invariant: SWE-agent 50-Hit Search Flood Guard: {note}Unbounded `fd` detected without output limits. "
                    f"Specify output bounds (e.g. `fd --max-results 50{sugg_args}`, `fd -d 2`) or pipe to `head` (e.g. `| head -n 50`) "
                    f"to prevent token saturation."
                )

    # 4. Check for tree without -L or recursive ls -R
    tree_match = re.search(r"(?:^|[;&|(`\n])\s*tree(?![-\w])([^;&|\n]*)", stripped)
    if tree_match:
        tree_args = tree_match.group(1).strip()
        has_tree_limit = bool(re.search(r"(?:-L\s*\d+|-L=\d+|--level(?:\s+|=)\d+|--help\b|-h\b|--version\b|-v\b)", tree_args))
        if not has_tree_limit:
            return (
                "Token Economy Invariant: Unbounded `tree` detected without depth limits. "
                "Specify depth limit with `-L <depth>` (e.g. `tree -L 2`) or pipe to `head -n 40`."
            )
    if re.search(r"(?:^|[;&|(`\n])\s*ls\s+-[a-zA-Z]*R[a-zA-Z]*\b", stripped):
        return (
            "Token Economy Invariant: Recursive `ls -R` detected without limits. "
            "Specify non-recursive listings, use `eza --tree --level=2`, or pipe to `head -n 40`."
        )

    # 5. Check for bare cat on files > 200 lines (resolved relative to command Cwd)
    cat_match = re.search(r"(?:^|[;&|(`\n])\s*cat\s+(?:-[a-zA-Z0-9]+\s+)*([^\s;&|<>\'\"]+)", stripped)
    if cat_match:
        target_p = cat_match.group(1).strip().strip("'\"")
        if not target_p.startswith("-"):
            try:
                resolved_p = _normalize(target_p, cwd or os.getcwd())
                if os.path.isfile(resolved_p):
                    cnt = _count_file_lines(resolved_p)
                    if cnt > 200:
                        return (
                            f"Token Economy Invariant: `cat` on `{os.path.basename(resolved_p)}` ({cnt} lines) without pagination. "
                            "Use `read_file` (CLI) / `view_file` (IDE), or pipe to `head -n 50` / `tail -n 50` to avoid dumping the whole file into context."
                        )
            except Exception:
                pass

    # 6. Check for unconstrained gradle/gradlew PTY progress output
    gradle_match = re.search(r"(?:^|[;&|(`\n])\s*(?:\./|\S+/)?gradlew?(?![-\w])([^;&|\n]*)", stripped)
    if gradle_match:
        gradle_args = gradle_match.group(1).strip()
        has_gradle_bound = bool(re.search(
            r"(?:^|\s)(?:--console=plain\b|-q\b|--quiet\b|--version\b|-v\b|--help\b|-h\b|--status\b|--stop\b)",
            gradle_args,
        ))
        if not has_gradle_bound:
            return (
                "Token Economy Invariant: SWE-agent 50-Hit Search Flood Guard: Unbounded `gradle`/`gradlew` PTY progress output detected. "
                "Pass `--console=plain -q` (e.g. `./gradlew assembleRelease --console=plain -q`) to prevent carriage-return (\\r) progress-bar context saturation."
            )

    return None


def _normalize(path: str, cwd: str) -> str:
    cleaned = _unwrap_outer_quotes(path)
    expanded = os.path.expanduser(cleaned)
    if not os.path.isabs(expanded):
        expanded = os.path.join(cwd, expanded)
    return os.path.normpath(os.path.abspath(expanded))


def _strip_safe_quoted_strings(cmd: str) -> str:
    # If the command is a direct bash/sh execution wrapper, unwrap outer quotes first
    m = re.match(r"^\s*(?:bash|sh|zsh)\s+-c\s+([\"'])(.*)\1\s*$", cmd, flags=re.DOTALL)
    if m:
        target = m.group(2)
    else:
        target = cmd
    # Replace contents of escaped double/single quoted strings with empty string
    target = re.sub(r'\\\"(?:\\\\|\\(?!")|[^"\\])*\\\"|\\\'(?:\\\\|\\(?!\')|[^\'\\])*\\\'', '""', target, flags=re.DOTALL)
    # Replace contents of double and single quoted strings with empty string
    return re.sub(r'(\"(?:\\.|[^"\\])*\"|\'(?:\\.|[^\'\\])*\')', '""', target, flags=re.DOTALL)


def _is_untargeted_test_command(cmd: str) -> bool:
    # Bypass if explicit env var flags are set in command line or environment
    if "ALL_TESTS=1" in cmd or "PRE_SHIP=1" in cmd:
        return False
    if os.environ.get("ALL_TESTS") == "1" or os.environ.get("PRE_SHIP") == "1":
        return False

    # Check for test runners
    pkg_test = bool(re.search(r"\b(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?test\b", cmd))
    bare_test = bool(re.search(r"\b(?:npx\s+)?(?:vitest|jest)(?:\s+run)?\b", cmd))

    if not (pkg_test or bare_test):
        return False

    # Recognize explicit test name/pattern filter flags (-t, --testNamePattern, --grep, --related, --changed)
    if re.search(r"(?:^|\s)(?:-t|--testNamePattern|--grep|--related|--changed)\b", cmd):
        return False

    # Check if a specific test file or targeted pattern is specified
    tokens = cmd.split()
    for token in tokens:
        token_clean = token.strip("'\"")
        if token_clean.startswith("-"):
            continue
        if token_clean in (
            "npm", "pnpm", "yarn", "bun", "npx", "run", "test",
            "vitest", "jest", "--", "bash", "sh", "zsh", "-c"
        ):
            continue
        # If there is a targeted test path or file
        if (
            re.search(r"\.(?:test|spec)\.[a-zA-Z0-9]+", token_clean)
            or token_clean.startswith("test/")
            or token_clean.startswith("./test/")
            or token_clean.startswith("__tests__/")
            or (token_clean.endswith((".ts", ".tsx", ".js", ".jsx", ".py")) and not token_clean.startswith("-"))
        ):
            return False

    return True


def _is_sdk_grounding_step(step: any) -> bool:
    if not isinstance(step, dict):
        return False
    if step.get("source") == "SYSTEM_SDK":
        return True
    content = str(step.get("content") or "").lstrip()
    if content.startswith(("[Session Grounding Anchor]", "[Active Knowledge Grounding")):
        return True
    return False


def _get_first_transcript_step(payload: dict) -> dict | None:
    if "transcript" in payload and isinstance(payload["transcript"], list) and payload["transcript"]:
        for step in payload["transcript"][:6]:
            if isinstance(step, dict) and not _is_sdk_grounding_step(step):
                return step
        return None
    transcript_p = payload.get("transcriptPath", "")
    conv_id = payload.get("conversationId", "")
    if not transcript_p or not os.path.isfile(transcript_p):
        if conv_id:
            for cand_path in (
                f"~/.gemini/antigravity-cli/brain/{conv_id}/.system_generated/logs/transcript.jsonl",
                f"~/.gemini/antigravity-ide/brain/{conv_id}/.system_generated/logs/transcript.jsonl",
                f"~/.gemini/antigravity/brain/{conv_id}/.system_generated/logs/transcript.jsonl",
            ):
                cand = os.path.expanduser(cand_path)
                if os.path.isfile(cand):
                    transcript_p = cand
                    break

    if transcript_p and os.path.isfile(transcript_p):
        meta_path = os.path.join(tempfile.gettempdir(), f".antigravity_meta_{conv_id}.json") if conv_id else ""
        if not _is_test_env() and meta_path:
            try:
                mtime = os.path.getmtime(transcript_p)
                cached_meta = _atomic_json_read(meta_path)
                if (
                    isinstance(cached_meta, dict)
                    and cached_meta.get("transcript_path") == os.path.abspath(transcript_p)
                    and cached_meta.get("mtime") == mtime
                    and "first_step" in cached_meta
                    and not _is_sdk_grounding_step(cached_meta["first_step"])
                ):
                    return cached_meta["first_step"]
            except Exception:
                pass

        try:
            with open(transcript_p, "r", encoding="utf-8") as f:
                scanned = 0
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    scanned += 1
                    try:
                        step = json.loads(line_str)
                    except Exception:
                        if scanned >= 6:
                            break
                        continue
                    if isinstance(step, dict) and not _is_sdk_grounding_step(step):
                        if not _is_test_env() and meta_path and step:
                            try:
                                _atomic_json_write(meta_path, {
                                    "transcript_path": os.path.abspath(transcript_p),
                                    "mtime": os.path.getmtime(transcript_p),
                                    "first_step": step,
                                })
                            except Exception:
                                pass
                        return step
                    if scanned >= 6:
                        break
        except Exception:
            return None
    return None


def _is_subagent_conversation(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False
    if bool(payload.get("is_subagent")) or bool(payload.get("isSubagent")):
        return True
    if str(payload.get("subagentRole") or "").strip() or str(payload.get("parentConversationId") or "").strip():
        return True
    agent_role = str(payload.get("agentRole") or payload.get("role") or "").strip().lower()
    if agent_role and agent_role not in ("pm", "root", "user", "orchestrator", "main", "root orchestrator (pm)"):
        return True
    first_step = _get_first_transcript_step(payload)
    if isinstance(first_step, dict) and not _is_sdk_grounding_step(first_step):
        if first_step.get("type") == "SYSTEM_MESSAGE":
            return True
    return False


def _detect_non_builder_session(payload: dict) -> tuple[bool, str]:
    direct_role = payload.get("role") or payload.get("agentRole") or payload.get("subagentRole")
    if direct_role and isinstance(direct_role, str):
        role_lower = direct_role.lower()
        for nb_role in NON_BUILDER_ROLES:
            if role_lower == nb_role.lower():
                return (True, direct_role)

    first_step = _get_first_transcript_step(payload)
    if not first_step or not isinstance(first_step, dict):
        return (False, "")

    step_type = first_step.get("type")
    step_source = first_step.get("source")

    # Case 1 — Root Orchestrator Session
    if step_type == "USER_INPUT" and step_source == "USER_EXPLICIT":
        return (True, "Root Orchestrator (PM)")

    # Case 2 — Non-Builder Subagent Session
    if step_type == "SYSTEM_MESSAGE":
        content = str(first_step.get("content", ""))
        role_match = re.search(r'Role:\s*[`\'"]?([a-zA-Z0-9_-]+)[`\'"]?', content, re.IGNORECASE)
        if role_match:
            declared_role = role_match.group(1).lower()
            for nb_role in NON_BUILDER_ROLES:
                if declared_role == nb_role.lower():
                    return (True, role_match.group(1))

    return (False, "")


def _is_test_file_path(path_str: str) -> bool:
    """Matches test files across ecosystems: *.test.*, *.spec.*, test_*.py, *_test.py, *_test.go, *_test.rs, /__tests__/."""
    if not path_str or not isinstance(path_str, str):
        return False
    norm = path_str.replace("\\", "/")
    norm_low = norm.lower()
    base_name = os.path.basename(norm_low)

    if "/__tests__/" in norm_low or norm_low.startswith("__tests__/") or norm_low.endswith("/__tests__"):
        return True

    if fnmatch.fnmatch(base_name, "*.test.*") or fnmatch.fnmatch(base_name, "*.spec.*"):
        return True

    if fnmatch.fnmatch(base_name, "test_*.py") or fnmatch.fnmatch(base_name, "*_test.py"):
        return True

    if fnmatch.fnmatch(base_name, "*_test.go") or fnmatch.fnmatch(base_name, "*_test.rs"):
        return True

    return False


def _extract_session_role(payload: dict) -> str:
    """Extracts normalized subagent or session role from payload or transcript."""
    direct_role = payload.get("role") or payload.get("agentRole") or payload.get("subagentRole")
    if direct_role and isinstance(direct_role, str):
        return direct_role.strip().lower()

    first_step = _get_first_transcript_step(payload)
    if not first_step or not isinstance(first_step, dict):
        return ""

    step_type = first_step.get("type")
    step_source = first_step.get("source")

    if step_type == "USER_INPUT" and step_source == "USER_EXPLICIT":
        return "pm"

    if step_type == "SYSTEM_MESSAGE":
        content = str(first_step.get("content", ""))
        role_match = re.search(r'Role:\s*[`\'"]?([a-zA-Z0-9_-]+)[`\'"]?', content, re.IGNORECASE)
        if role_match:
            return role_match.group(1).strip().lower()

    return ""


def _is_app_source_file(file_str: str, cwd: str = "") -> bool:
    cleaned = file_str.strip().strip("'\"`")
    if not cleaned:
        return False
    if cleaned.startswith("&") or cleaned in ("/dev/null", "/dev/stdout", "/dev/stderr", "/dev/zero"):
        return False
    norm = os.path.normpath(os.path.join(cwd, cleaned) if not os.path.isabs(cleaned) else cleaned).lower()
    if cleaned.startswith(("~/.gemini", ".gemini", "/.gemini")) or (os.path.isabs(cleaned) and "/.gemini/" in norm):
        return False
    if "/tmp/" in norm or norm.startswith(("/tmp", tempfile.gettempdir().lower())):
        return False
    if norm.endswith(APPLICATION_CODE_EXTENSIONS):
        return True
    return False


def _detect_shell_source_mutation(cmd: str, cwd: str = "") -> str | None:
    cmd_structure = _strip_safe_quoted_strings(cmd)

    # 1. Output redirection > or >>
    if ">" in cmd_structure:
        redir_pattern = re.compile(
            r"(?:(?<![<0-9&])>|(?<!<)[0-9&]>|>>|[0-9&]>>)\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s;&|<>]+))"
        )
        for m in redir_pattern.finditer(cmd_structure):
            target = m.group(1) or m.group(2) or m.group(3) or ""
            if not target:
                span_start, span_end = m.span()
                raw_chunk = cmd[span_start:span_end + 100]
                m_raw = redir_pattern.match(raw_chunk)
                if m_raw:
                    target = m_raw.group(1) or m_raw.group(2) or m_raw.group(3) or ""
            if target and _is_app_source_file(target, cwd):
                return target

    # 2. tee command
    if re.search(r"\btee\b", cmd_structure):
        for tee_match in re.finditer(r"\btee\b([^;|&]+)", cmd):
            tee_args = tee_match.group(1).strip()
            try:
                tokens = shlex.split(tee_args)
            except Exception:
                tokens = tee_args.split()
            for tok in tokens:
                if tok.startswith("-"):
                    continue
                if _is_app_source_file(tok, cwd):
                    return tok

    # 3. sed with in-place flag (-i, --in-place)
    if re.search(r"\bsed\b", cmd_structure):
        for sed_match in re.finditer(r"\bsed\b([^;|&]+)", cmd):
            sed_cmd = sed_match.group(0)
            if re.search(r"(?:^|\s)(?:-[a-zA-Z]*i[a-zA-Z0-9._-]*|--in-place(?:=\S*)?)\b", sed_cmd):
                try:
                    tokens = shlex.split(sed_match.group(1))
                except Exception:
                    tokens = sed_match.group(1).split()
                for tok in tokens:
                    if tok.startswith("-"):
                        continue
                    if _is_app_source_file(tok, cwd):
                        return tok

    # 4. perl with in-place flag (-i, -pi, etc.)
    if re.search(r"\bperl\b", cmd_structure):
        for perl_match in re.finditer(r"\bperl\b([^;|&]+)", cmd):
            perl_cmd = perl_match.group(0)
            if re.search(r"(?:^|\s)(?:-[a-zA-Z]*i[a-zA-Z0-9._-]*)\b", perl_cmd):
                try:
                    tokens = shlex.split(perl_match.group(1))
                except Exception:
                    tokens = perl_match.group(1).split()
                for tok in tokens:
                    if tok.startswith("-"):
                        continue
                    if _is_app_source_file(tok, cwd):
                        return tok

    # 5. sd command targeting source file (only tokens after the two pattern args are targets)
    if re.search(r"\bsd\b", cmd_structure):
        for sd_match in re.finditer(r"\bsd\b([^;|&]+)", cmd):
            try:
                tokens = shlex.split(sd_match.group(1))
            except Exception:
                tokens = sd_match.group(1).split()
            pos_count = 0
            for tok in tokens:
                if tok.startswith("-"):
                    continue
                pos_count += 1
                if pos_count <= 2:
                    continue
                if _is_app_source_file(tok, cwd):
                    return tok

    # 6. patch or git apply targeting source files
    if re.search(r"\b(?:patch|git\s+apply)\b", cmd):
        for p_match in re.finditer(r"\b(?:patch|git\s+apply)\b([^;|&]+)", cmd):
            try:
                tokens = shlex.split(p_match.group(1))
            except Exception:
                tokens = p_match.group(1).split()
            for tok in tokens:
                if tok.startswith("-"):
                    continue
                if _is_app_source_file(tok, cwd):
                    return tok

    # 7. python -c writing to source file (only flag the file argument actually passed to write operations)
    if re.search(r"\bpython3?\s+-c\b", cmd):
        open_targets = re.findall(
            r"""open\s*\(\s*(?:file\s*=\s*)?(?:Path\s*\(\s*)?['"]([^'"]+)['"]\s*\)?\s*,\s*(?:mode\s*=\s*)?['"][wa][b+]?['"]""",
            cmd,
        )
        for target in open_targets:
            if _is_app_source_file(target, cwd):
                return target

        path_targets = re.findall(
            r"""Path\s*\(\s*['"]([^'"]+)['"]\s*\)\s*\.\s*write_(?:text|bytes)\s*\(""",
            cmd,
        )
        for target in path_targets:
            if _is_app_source_file(target, cwd):
                return target

    return None


def _handle_run_command(args: dict, payload: dict) -> dict:
    raw_cmd = args.get("CommandLine", "").strip()
    if not raw_cmd:
        return {"decision": "allow"}

    # Unwrap any outer surrounding quotes from model tool argument formatting
    cmd = _unwrap_outer_quotes(raw_cmd)
    if not cmd:
        return {"decision": "allow"}

    # 0. Command string length guard (prevent massive script dumps into context)
    if len(cmd) > 4000:
        return {
            "decision": "deny",
            "reason": (
                f"Token Economy Invariant: Command string length ({len(cmd)}) exceeds 4,000 characters. "
                "To prevent context bloat, write multi-line scripts to scratch/ and execute via python3 <script_path>."
            ),
        }

    # 0b. Role Isolation Shell-Write Guard for Non-Builders (Collision 7 / Advisory 1) & Active Lease Check
    is_non_builder, role_label = _detect_non_builder_session(payload)
    cwd = str(args.get("Cwd") or os.getcwd())
    mutated_file = _detect_shell_source_mutation(cmd, cwd)
    if mutated_file:
        if is_non_builder:
            return {
                "decision": "deny",
                "reason": (
                    f"Role Isolation Shell-Write Guard (pm-no-implementation.md): "
                    f"Non-builder session ({role_label}) is strictly prohibited from mutating application source code via shell write (`{mutated_file}`). "
                    "Delegate code modifications to a specialist builder subagent (`Role: 'dev-fe' | 'dev-be' | 'debugger'`)."
                ),
            }

        first_step = _get_first_transcript_step(payload)
        if first_step and first_step.get("type") == "SYSTEM_MESSAGE":
            content = str(first_step.get("content", ""))
            has_allowed_files, allowed_files = _extract_allowed_files(content)
            if has_allowed_files:
                target_norm = os.path.normpath(os.path.join(cwd, mutated_file) if not os.path.isabs(mutated_file) else mutated_file)
                matched = any(_matches_allowed_file(target_norm, pat, cwd) for pat in allowed_files)
                if not matched:
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Story Shard File Lease Violation (BMAD): Shell write target is outside the subagent's leased allowed_files "
                            f"(`{os.path.basename(target_norm)}` not in {allowed_files}). "
                            "Escalate to Orchestrator to expand shard file leases before touching unleased files via shell commands."
                        ),
                    }

    # Use stripped version for syntactic checks so quoted arguments (e.g. commit messages, grep) don't false positive
    cmd_structure = _strip_safe_quoted_strings(cmd)

    # 1. Banned manual ADB input tap or screencap loop
    if re.search(r"\badb\s+shell\s+input\s+tap\b", cmd_structure) or re.search(r"\badb\s+shell\s+screencap\b", cmd_structure):
        return {
            "decision": "deny",
            "reason": (
                "Manual ADB coordinate tapping and screencap loops are strictly prohibited by core rules. "
                "Validate UI state, props, and behavior via deterministic Vitest component/hook tests."
            ),
        }

    # 2. Banned sleep in run_command bash string
    if re.search(r"(?:^|[;&|(`\"'\n]|\$\()\s*\bsleep\s+\d+", cmd_structure):
        return {
            "decision": "deny",
            "reason": (
                "Execution of sleep in run_command is strictly forbidden by token_economy rules. "
                "Use WaitMsBeforeAsync or the schedule tool instead of sleeping in bash."
            ),
        }

    # 3. Banned cd command in run_command
    if re.search(r"(?:^|[;&|(`\"'\n]|\$\()\s*\bcd(?:\s+|$|[\"';&|)])", cmd_structure):
        return {
            "decision": "deny",
            "reason": (
                "The cd command is strictly prohibited in run_command. "
                "Use tool-native directory flags (e.g. git -C <dir>, npm --prefix <dir>, pytest <dir>, make -C <dir>) or absolute paths instead."
            ),
        }

    # 3b. Enforce Modern CLI Tools (rg instead of grep/egrep/fgrep/rgrep; fd instead of find)
    legacy_grep_match = None
    for m in re.finditer(
        r"(?:^|[;&|(`\"'\n]|\$\()\s*(?:(?:/usr)?/bin/)?(?<!\bast-)\b(grep|egrep|fgrep|rgrep)\b",
        cmd_structure,
    ):
        # Allow git followed by any whitespace (\bgit\s+) before grep
        prefix = cmd_structure[:m.start(1)]
        if re.search(r"\bgit\s+$", prefix):
            continue
        legacy_grep_match = m
        break
    if legacy_grep_match:
        bad_tool = legacy_grep_match.group(1)
        return {
            "decision": "deny",
            "reason": (
                f"Modern CLI Tool Invariant: Legacy `{bad_tool}` is strictly forbidden in Antigravity. "
                "Use `rg` (ripgrep) or `ast-grep` (`sg`) instead (e.g. `rg -n -m 50 'pattern' path`)."
            ),
        }

    legacy_find_match = re.search(
        r"(?:^|[;&|(`\n]|\$\()\s*(?:(?:/usr)?/bin/)?\bfind\b",
        cmd_structure,
    )
    if legacy_find_match:
        return {
            "decision": "deny",
            "reason": (
                "Modern CLI Tool Invariant: Legacy `find` is strictly forbidden in Antigravity. "
                "Use `fd` instead (e.g. `fd --max-results 50 'pattern' path` or `fd -e ts --max-results 50 src/`)."
            ),
        }

    # 4. Process & Pipe Exit-Code Swallowing Guard
    m_mask = re.search(r"\|\|\s*(?:true\b|(?::(?:\s|;|$))|echo\b)", cmd_structure)
    if m_mask and _RUNNER_INVOCATION_RE.search(cmd_structure[:m_mask.start()]):
        return {
            "decision": "deny",
            "reason": (
                "Process Exit-Code Masking Invariant: Masking exit codes of verification/test/compiler runners via "
                "`|| true`, `|| :`, or `|| echo` is strictly forbidden. Commands must propagate non-zero exit codes so failures are detected."
            ),
        }
    m_pipe = re.search(r"\|\s*(?:head|tail|tee)\b", cmd_structure)
    if m_pipe and _RUNNER_INVOCATION_RE.search(cmd_structure[:m_pipe.start()]):
        has_pipefail = bool(re.search(r"\bset\s+[^;\n]*\bpipefail\b", cmd_structure))
        if not has_pipefail:
            return {
                "decision": "deny",
                "reason": (
                    "Process Pipe Exit-Code Swallowing Guard: Verification command piped to head/tail/tee without `pipefail`. "
                    f"Prefix your command with `set -o pipefail; ` (e.g. `set -o pipefail; {cmd}`) so non-zero test/compiler exit codes are not swallowed by the pipe."
                ),
            }

    # 4b. Enforce Strict Targeted Test Execution (Law 22 & AGENTS.md)
    if _is_untargeted_test_command(cmd_structure):
        return {
            "decision": "deny",
            "reason": (
                "Strict Targeted Test Execution Invariant (Law 22 & AGENTS.md): Untargeted full test suite runs "
                f"(`{cmd}`) are blocked to prevent token waste and test runner timeouts. "
                "Specify the targeted test file directly (e.g. `npx vitest run <path_to_test>`). "
                "To run the full suite at Pre-Ship gate, prefix with `PRE_SHIP=1` or `ALL_TESTS=1`."
            ),
        }

    # 5. Unconstrained command check (Oracle Directive D3)
    unconstrained_err = _is_unconstrained_command(cmd_structure, cmd, str(args.get("Cwd") or os.getcwd()))
    if unconstrained_err:
        reason = (
            unconstrained_err
            if unconstrained_err.startswith("Token Economy Invariant:")
            else f"Token Economy Invariant: {unconstrained_err}"
        )
        return {
            "decision": "deny",
            "reason": reason,
        }

    # 6. Destructive command gate -> force_ask user confirmation
    for pattern, desc in DESTRUCTIVE_COMMAND_PATTERNS:
        match = pattern.search(cmd_structure)
        if match:
            return {
                "decision": "force_ask",
                "reason": (
                    f"{desc}: `{match.group(0)}`. "
                    "Explicit user confirmation is required under Antigravity safety guardrails."
                ),
            }

    # 7. Dependency mutation gate -> force_ask user confirmation
    for pattern, desc in DEPENDENCY_MUTATION_PATTERNS:
        match = pattern.search(cmd_structure)
        if match:
            return {
                "decision": "force_ask",
                "reason": (
                    f"{desc}: `{match.group(0)}`. "
                    "Package modifications must be scanned and confirmed under dependency policy."
                ),
            }

    # 8. Subagent CLI Model Escalation Gate -> force_ask user confirmation
    if re.search(r"(?:^|[;&|(\n])\s*agy\b[^;&|\n]*--model(?:=|\s+)gemini-4-argon-high\b", cmd):
        return {
            "decision": "force_ask",
            "reason": (
                "Subagent CLI Model Escalation Gate: Spawning `agy` with strongest frontier model "
                "(`gemini-4-argon-high`) requires explicit user approval."
            ),
        }

    return {"decision": "allow"}


def _is_error_or_denied_step(step: dict) -> bool:
    if not isinstance(step, dict):
        return False
    if step.get("type") == "ERROR_MESSAGE" or step.get("status") == "ERROR":
        return True
    combined = (str(step.get("error", "")) + " " + str(step.get("content", ""))).lower()
    return "tool call denied" in combined


def _valid_step_idx(step: dict | None) -> int | None:
    if not isinstance(step, dict):
        return None
    idx = step.get("step_index")
    if isinstance(idx, int) and not isinstance(idx, bool):
        return idx
    return None


def _apply_tool_calls_to_ledger(
    tool_calls: list,
    files_ledger: dict,
    workspace: str,
    slice_cap: int | None = None,
) -> None:
    effective_slice_cap = (
        slice_cap
        if isinstance(slice_cap, int) and slice_cap > 0
        else int(_load_active_guardrail_policy(workspace).get("slice_cap", 250))
    )
    for tc in tool_calls:
        if not isinstance(tc, dict):
            continue
        tname = tc.get("name") or tc.get("function", {}).get("name")
        targs = tc.get("args", {})
        if isinstance(targs, str):
            try:
                targs = json.loads(targs)
            except Exception:
                pass
        if not isinstance(targs, dict):
            continue

        if tname in ("replace_file_content", "write_to_file", "multi_replace_file_content", "write_file", "edit_file"):
            ef = targs.get("TargetFile") or targs.get("Path") or targs.get("path") or targs.get("file") or ""
            if ef:
                norm = _normalize(ef, workspace)
                entry = files_ledger.setdefault(norm, {
                    "total_reads": 0,
                    "whole_reads": 0,
                    "edits_count": 0,
                    "reads_since_edit": 0,
                    "read_count": 0,
                    "file_slices": []
                })
                entry["edits_count"] = entry.get("edits_count", 0) + 1
                entry["reads_since_edit"] = 0
                entry["file_slices"] = []
                entry["slice_ranges"] = []

        elif tname in ("view_file", "read_file"):
            rf = targs.get("AbsolutePath") or targs.get("Path") or targs.get("path") or targs.get("file") or ""
            if rf:
                norm = _normalize(rf, workspace)
                entry = files_ledger.setdefault(norm, {
                    "total_reads": 0,
                    "whole_reads": 0,
                    "edits_count": 0,
                    "reads_since_edit": 0,
                    "read_count": 0,
                    "file_slices": [],
                    "slice_ranges": [],
                    "last_read_mtime": 0.0,
                })
                entry["total_reads"] += 1
                entry["reads_since_edit"] += 1
                if entry.get("last_read_mtime", 0.0) == 0.0 and os.path.exists(norm):
                    try:
                        entry["last_read_mtime"] = os.path.getmtime(norm)
                    except Exception:
                        pass
                sl = _to_int(targs.get("StartLine"))
                el = _to_int(targs.get("EndLine"))
                if isinstance(sl, int) and isinstance(el, int) and sl > 0 and el >= sl:
                    span = el - sl + 1
                    if span > effective_slice_cap:
                        line_cnt = _count_file_lines(norm) if os.path.isfile(norm) else 0
                        if line_cnt > 200 and span <= effective_slice_cap + 10:
                            el = min(line_cnt, sl + effective_slice_cap - 1) if sl <= line_cnt else (sl + effective_slice_cap - 1)
                    slices = entry.setdefault("file_slices", [])
                    overlapping = any(
                        not (el < s_start or sl > s_end)
                        for s_start, s_end in slices
                    )
                    slices.append([sl, el])
                    if overlapping or len(slices) > 6:
                        entry["read_count"] += 1
                else:
                    entry["whole_reads"] += 1
                    entry["read_count"] += 1


def _get_or_update_read_ledger(
    transcript_p: str, conv_id: str, workspace: str, target_norm: str
) -> tuple[int, int, int, int, int, list[tuple[int, int]]]:
    if not transcript_p or not os.path.isfile(transcript_p):
        return (0, 0, 0, 0, 0, [])

    try:
        st = os.stat(transcript_p)
        file_ino = st.st_ino
        file_size = st.st_size
    except Exception:
        return (0, 0, 0, 0, 0, [])

    cache_key = hashlib.sha256(f"{conv_id}:{os.path.abspath(transcript_p)}".encode("utf-8")).hexdigest()[:16]
    cache_file = os.path.join(tempfile.gettempdir(), f".antigravity_reads_{cache_key}.json")

    cached_data = None
    if os.path.isfile(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
        except Exception:
            cached_data = None

    is_usable = (
        isinstance(cached_data, dict)
        and cached_data.get("st_ino") == file_ino
        and isinstance(cached_data.get("offset"), int)
        and file_size >= cached_data["offset"]
    )

    if is_usable:
        offset = cached_data["offset"]
        files = cached_data.get("files", {})
        pending_step = cached_data.get("pending_step")
        raw_applied = cached_data.get("applied_step_indices", [])
        applied_step_indices = (
            [x for x in raw_applied if isinstance(x, int) and not isinstance(x, bool)][-64:]
            if isinstance(raw_applied, list)
            else []
        )
        initial_seek = offset
    else:
        offset = 0
        files = {}
        pending_step = None
        applied_step_indices = []
        initial_seek = max(0, file_size - 65536)

    active_slice_cap = int(_load_active_guardrail_policy(workspace).get("slice_cap", 250))

    def _mark_step_applied(s_idx: int | None) -> None:
        if s_idx is not None and s_idx not in applied_step_indices:
            applied_step_indices.append(s_idx)
            if len(applied_step_indices) > 64:
                del applied_step_indices[:-64]

    lines = []
    new_offset = offset

    try:
        if not is_usable and initial_seek > 0:
            with open(transcript_p, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(initial_seek)
                f.readline()  # discard possible partial line
                new_bytes_pos = f.tell()
                content = f.read()
                last_nl = content.rfind("\n")
                if last_nl != -1:
                    lines = content[:last_nl].splitlines()
                    new_offset = new_bytes_pos + last_nl + 1
                else:
                    lines = []
                    new_offset = new_bytes_pos
        elif file_size > offset:
            with open(transcript_p, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(offset)
                content = f.read()
                last_nl = content.rfind("\n")
                if last_nl != -1:
                    lines = content[:last_nl].splitlines()
                    new_offset = offset + last_nl + 1
                else:
                    lines = []
                    new_offset = offset
    except Exception:
        pass

    new_steps = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            new_steps.append(json.loads(line))
        except Exception:
            continue

    if new_steps:
        partial_offsets: dict[int, tuple[int, int]] = {}
        # Resolve pending_step from previous turn
        if pending_step:
            p_idx = _valid_step_idx(pending_step)
            if p_idx is not None and p_idx in applied_step_indices:
                pending_step = None
            else:
                pending_tcs = pending_step.get("tool_calls", [])
                if not isinstance(pending_tcs, list):
                    pending_tcs = []
                prior_offset = int(pending_step.get("resolved_offset", 0) or 0)
                result_steps = []
                j = 0
                while j < len(new_steps):
                    s = new_steps[j]
                    if s.get("type") in ("PLANNER_RESPONSE", "USER_INPUT") or isinstance(s.get("tool_calls"), list):
                        break
                    result_steps.append(s)
                    j += 1

                if len(result_steps) == 1 and result_steps[0].get("type") == "ERROR_MESSAGE":
                    _mark_step_applied(p_idx)
                    pending_step = None
                elif j < len(new_steps) and p_idx is not None and _valid_step_idx(new_steps[j]) == p_idx:
                    if j == 0:
                        partial_offsets[p_idx] = (prior_offset, prior_offset)
                    else:
                        resolved_cnt = min(len(pending_tcs), len(result_steps))
                        for k in range(resolved_cnt):
                            if not _is_error_or_denied_step(result_steps[k]):
                                _apply_tool_calls_to_ledger([pending_tcs[k]], files, workspace, slice_cap=active_slice_cap)
                        if resolved_cnt >= len(pending_tcs):
                            _mark_step_applied(p_idx)
                        else:
                            total_sofar = prior_offset + resolved_cnt
                            next_after = new_steps[j + 1] if (j + 1) < len(new_steps) else None
                            res_skip_next = total_sofar if _valid_step_idx(next_after) == p_idx + 1 else 0
                            partial_offsets[p_idx] = (total_sofar, res_skip_next)
                    pending_step = None
                elif j < len(new_steps):
                    for k, call_item in enumerate(pending_tcs):
                        if k < len(result_steps) and _is_error_or_denied_step(result_steps[k]):
                            continue
                        _apply_tool_calls_to_ledger([call_item], files, workspace, slice_cap=active_slice_cap)
                    _mark_step_applied(p_idx)
                    pending_step = None
                else:
                    resolved_cnt = min(len(pending_tcs), len(result_steps))
                    for k in range(resolved_cnt):
                        if not _is_error_or_denied_step(result_steps[k]):
                            _apply_tool_calls_to_ledger([pending_tcs[k]], files, workspace, slice_cap=active_slice_cap)
                    if len(result_steps) < len(pending_tcs):
                        pending_step = {
                            **pending_step,
                            "tool_calls": pending_tcs[len(result_steps):],
                            "resolved_offset": prior_offset + resolved_cnt,
                        }
                    else:
                        _mark_step_applied(p_idx)
                        pending_step = None

        for idx, step in enumerate(new_steps):
            s_idx = _valid_step_idx(step)
            if s_idx is not None and s_idx in applied_step_indices:
                continue

            tc = step.get("tool_calls")
            if not tc or not isinstance(tc, list):
                continue

            tc_skip, res_skip = partial_offsets.pop(s_idx, (0, 0)) if s_idx is not None else (0, 0)
            if tc_skip > 0:
                tc = tc[tc_skip:]
                if not tc:
                    _mark_step_applied(s_idx)
                    continue

            result_steps = []
            j = idx + 1
            while j < len(new_steps):
                s = new_steps[j]
                if s.get("type") in ("PLANNER_RESPONSE", "USER_INPUT") or isinstance(s.get("tool_calls"), list):
                    break
                result_steps.append(s)
                j += 1

            if res_skip > 0:
                result_steps = result_steps[res_skip:]

            if len(result_steps) == 1 and result_steps[0].get("type") == "ERROR_MESSAGE":
                _mark_step_applied(s_idx)
                continue
            elif j < len(new_steps) and s_idx is not None and _valid_step_idx(new_steps[j]) == s_idx:
                resolved_cnt = min(len(tc), len(result_steps))
                for k in range(resolved_cnt):
                    if not _is_error_or_denied_step(result_steps[k]):
                        _apply_tool_calls_to_ledger([tc[k]], files, workspace, slice_cap=active_slice_cap)
                if resolved_cnt >= len(tc):
                    _mark_step_applied(s_idx)
                else:
                    total_sofar = tc_skip + resolved_cnt
                    next_after = new_steps[j + 1] if (j + 1) < len(new_steps) else None
                    res_skip_next = total_sofar if _valid_step_idx(next_after) == s_idx + 1 else 0
                    partial_offsets[s_idx] = (total_sofar, res_skip_next)
            elif j < len(new_steps):
                for k, call_item in enumerate(tc):
                    if k < len(result_steps) and _is_error_or_denied_step(result_steps[k]):
                        continue
                    _apply_tool_calls_to_ledger([call_item], files, workspace, slice_cap=active_slice_cap)
                _mark_step_applied(s_idx)
            else:
                resolved_cnt = min(len(tc), len(result_steps))
                for k in range(resolved_cnt):
                    if not _is_error_or_denied_step(result_steps[k]):
                        _apply_tool_calls_to_ledger([tc[k]], files, workspace, slice_cap=active_slice_cap)
                if len(result_steps) < len(tc):
                    pending_step = {
                        **step,
                        "tool_calls": tc[len(result_steps):],
                        "resolved_offset": tc_skip + resolved_cnt,
                    }
                else:
                    _mark_step_applied(s_idx)
                    pending_step = None

    entry = files.get(target_norm)
    if entry and os.path.exists(target_norm):
        try:
            current_mtime = os.path.getmtime(target_norm)
        except Exception:
            current_mtime = 0.0
        last_mtime = float(entry.get("last_read_mtime", 0.0))
        if current_mtime > 0 and last_mtime > 0 and current_mtime > last_mtime:
            # File modified on disk since last read (via run_command, subagent, or external tool)
            entry["reads_since_edit"] = 0
            entry["whole_reads"] = 0
            entry["file_slices"] = []
            entry["slice_ranges"] = []
            entry["read_count"] = 0
            entry["edits_count"] = entry.get("edits_count", 0) + 1
            entry["last_read_mtime"] = current_mtime
        elif last_mtime == 0.0 and current_mtime > 0:
            entry["last_read_mtime"] = current_mtime

    total_reads = entry["total_reads"] if entry else 0
    whole_reads = entry["whole_reads"] if entry else 0
    edits_count = entry["edits_count"] if entry else 0
    reads_since_edit = entry["reads_since_edit"] if entry else 0
    read_count = entry["read_count"] if entry else 0
    file_slices = [tuple(s) for s in entry.get("file_slices", [])] if entry else []

    if pending_step and isinstance(pending_step.get("tool_calls"), list):
        for tc in pending_step["tool_calls"]:
            if not isinstance(tc, dict):
                continue
            tname = tc.get("name") or tc.get("function", {}).get("name")
            targs = tc.get("args", {})
            if isinstance(targs, str):
                try:
                    targs = json.loads(targs)
                except Exception:
                    pass
            if not isinstance(targs, dict):
                continue

            if tname in ("replace_file_content", "write_to_file", "multi_replace_file_content", "write_file", "edit_file"):
                ef = targs.get("TargetFile") or targs.get("Path") or targs.get("path") or targs.get("file") or ""
                if ef and _normalize(ef, workspace) == target_norm:
                    edits_count += 1
                    reads_since_edit = 0
                    file_slices = []

            elif tname in ("view_file", "read_file"):
                rf = targs.get("AbsolutePath") or targs.get("Path") or targs.get("path") or targs.get("file") or ""
                if rf and _normalize(rf, workspace) == target_norm:
                    sl = _to_int(targs.get("StartLine"))
                    el = _to_int(targs.get("EndLine"))
                    is_valid_slice = isinstance(sl, int) and isinstance(el, int) and sl > 0 and el >= sl
                    if is_valid_slice and (el - sl + 1) > active_slice_cap:
                        t_line_cnt = _count_file_lines(target_norm) if os.path.isfile(target_norm) else 0
                        if t_line_cnt > 200:
                            if (el - sl + 1) > active_slice_cap + 10:
                                continue
                            el = min(t_line_cnt, sl + active_slice_cap - 1) if sl <= t_line_cnt else (sl + active_slice_cap - 1)
                    total_reads += 1
                    reads_since_edit += 1
                    if is_valid_slice:
                        overlapping = any(
                            not (el < s_start or sl > s_end)
                            for s_start, s_end in file_slices
                        )
                        file_slices.append((sl, el))
                        if overlapping or len(file_slices) > 6:
                            read_count += 1
                    else:
                        whole_reads += 1
                        read_count += 1
                    if entry and os.path.exists(target_norm):
                        try:
                            entry["last_read_mtime"] = os.path.getmtime(target_norm)
                        except Exception:
                            pass

    # Save cache atomically
    cache_to_save = {
        "conv_id": conv_id,
        "transcript_p": os.path.abspath(transcript_p),
        "st_ino": file_ino,
        "offset": new_offset,
        "pending_step": pending_step,
        "applied_step_indices": applied_step_indices[-64:],
        "files": files,
    }
    try:
        tmp_c = f"{cache_file}.tmp.{os.getpid()}"
        with open(tmp_c, "w", encoding="utf-8") as f:
            json.dump(cache_to_save, f)
        os.replace(tmp_c, cache_file)
    except Exception:
        pass

    return (read_count, total_reads, whole_reads, edits_count, reads_since_edit, file_slices)


def _update_read_ledger_mtime(transcript_p: str, conv_id: str, target_norm: str, mtime: float) -> None:
    if not transcript_p or mtime <= 0:
        return
    cache_key = hashlib.sha256(f"{conv_id}:{os.path.abspath(transcript_p)}".encode("utf-8")).hexdigest()[:16]
    cache_file = os.path.join(tempfile.gettempdir(), f".antigravity_reads_{cache_key}.json")
    if not os.path.isfile(cache_file):
        return
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "files" in data and isinstance(data["files"], dict):
            entry = data["files"].setdefault(target_norm, {
                "total_reads": 0,
                "whole_reads": 0,
                "edits_count": 0,
                "reads_since_edit": 0,
                "read_count": 0,
                "file_slices": [],
                "slice_ranges": [],
                "last_read_mtime": mtime,
            })
            entry["last_read_mtime"] = mtime
            tmp_c = f"{cache_file}.tmp.{os.getpid()}"
            with open(tmp_c, "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.replace(tmp_c, cache_file)
    except Exception:
        pass


def _extract_inline_ast_skeleton(file_path: str, max_items: int = 35) -> str:
    """Extracts a compact top-level outline/skeleton with line numbers [Lstart-Lend] in <10ms."""
    items: list[str] = []
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".py":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source = f.read(500_000)
            parsed = ast.parse(source)
            for node in parsed.body:
                if len(items) >= max_items:
                    break
                start_l = getattr(node, "lineno", 0)
                end_l = getattr(node, "end_lineno", start_l)
                loc = f"[L{start_l}-L{end_l}]" if end_l > start_l else f"[L{start_l}]"
                if isinstance(node, ast.ClassDef):
                    items.append(f"  class {node.name} {loc}")
                    for sub in node.body:
                        if len(items) >= max_items:
                            break
                        sub_start = getattr(sub, "lineno", 0)
                        sub_end = getattr(sub, "end_lineno", sub_start)
                        sub_loc = f"[L{sub_start}-L{sub_end}]" if sub_end > sub_start else f"[L{sub_start}]"
                        if isinstance(sub, ast.FunctionDef):
                            items.append(f"    def {sub.name}() {sub_loc}")
                        elif isinstance(sub, ast.AsyncFunctionDef):
                            items.append(f"    async def {sub.name}() {sub_loc}")
                elif isinstance(node, ast.FunctionDef):
                    items.append(f"  def {node.name}() {loc}")
                elif isinstance(node, ast.AsyncFunctionDef):
                    items.append(f"  async def {node.name}() {loc}")
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            items.append(f"  {target.id} = ... {loc}")
                            break

        elif ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".kt", ".go", ".rs"):
            pattern = re.compile(
                r"^(?:export\s+(?:default\s+)?)?(?:async\s+)?"
                r"(class|interface|type|enum|function|const|let|var|def|fun|fn)\s+([A-Za-z0-9_$]+)"
            )
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[:3000]

            open_decl: dict | None = None
            depth = 0
            for i, line in enumerate(lines, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith(("//", "/*", "*", "#")):
                    continue

                if open_decl is None and depth == 0:
                    m = pattern.match(stripped)
                    if m:
                        kind, name = m.group(1), m.group(2)
                        open_decl = {"kind": kind, "name": name, "start": i, "is_export": "export" in stripped}

                depth += line.count("{") - line.count("}")
                if open_decl is not None:
                    if depth <= 0 or ";" in line or (depth == 0 and "}" in line):
                        end_l = i
                        loc = f"[L{open_decl['start']}-L{end_l}]" if end_l > open_decl['start'] else f"[L{open_decl['start']}]"
                        prefix = "export " if open_decl['is_export'] else ""
                        items.append(f"  {prefix}{open_decl['kind']} {open_decl['name']} {loc}")
                        open_decl = None
                        depth = max(0, depth)
                        if len(items) >= max_items:
                            break
    except Exception:
        pass

    if items:
        if len(items) >= max_items:
            items.append(f"  ... [and more symbols truncated at {max_items} items]")
        return "\n".join(items)
    return "  (No top-level AST declarations detected)"


def _load_active_guardrail_policy(workspace_dir: str | None = None) -> dict:
    defaults = {"slice_cap": 250, "max_slices": 6, "flood_limit": 50}
    # a) <workspace_dir>/.antigravity/task_harness/guardrails.json
    if workspace_dir:
        ws_guardrails = os.path.join(workspace_dir, ".antigravity", "task_harness", "guardrails.json")
        if os.path.isfile(ws_guardrails):
            try:
                with open(ws_guardrails, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        merged = dict(defaults)
                        merged.update(data)
                        return merged
            except Exception:
                pass

    # b) ~/.gemini/antigravity/skillbank/guardrails.json (ONLY when "unittest" not in sys.modules and os.environ.get("ANTIGRAVITY_TEST_MODE") != "1")
    if "unittest" not in sys.modules and os.environ.get("ANTIGRAVITY_TEST_MODE") != "1":
        global_guardrails = os.path.expanduser("~/.gemini/antigravity/skillbank/guardrails.json")
        if os.path.isfile(global_guardrails):
            try:
                with open(global_guardrails, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        merged = dict(defaults)
                        merged.update(data)
                        merged["slice_cap"] = max(250, int(merged.get("slice_cap", 250)))
                        return merged
            except Exception:
                pass

    return defaults


def _calculate_max_slices(line_cnt: int, base_max_slices: int = 6, slice_cap: int = 250) -> int:
    """Calculates max allowed sliced reads for a file.
    Files <= (base_max_slices * slice_cap) lines are capped at base_max_slices.
    Files > (base_max_slices * slice_cap) lines allow at least ceil(lines/slice_cap) + 2 so large files can be fully traversed.
    """
    threshold = base_max_slices * slice_cap
    if line_cnt <= threshold:
        return base_max_slices
    return (line_cnt + slice_cap - 1) // slice_cap + 2


def _handle_view_file(args: dict, payload: dict) -> dict:
    target_file = (
        args.get("AbsolutePath")
        or args.get("Path")
        or args.get("path")
        or args.get("file")
        or ""
    )
    if not target_file:
        return {"decision": "allow"}

    norm_low = target_file.lower().strip().strip("'\"")

    # 1. Zero Multimodal Poisoning: Block viewing image files
    if norm_low.endswith(IMAGE_EXTENSIONS):
        return {
            "decision": "deny",
            "reason": (
                f"Zero Multimodal Poisoning Invariant: Calling read_file (CLI) / view_file (IDE) on image file `{os.path.basename(target_file)}` "
                "is blocked to prevent context explosion (~3,000 tokens). Save images to artifacts directory for user viewing."
            ),
        }

    workspace = ""
    ws_paths = payload.get("workspacePaths", [])
    if ws_paths and isinstance(ws_paths, list):
        workspace = ws_paths[0]
    if not workspace:
        workspace = os.getcwd()

    target_norm = _normalize(target_file, workspace)

    # CK-02 Privacy-Block Gate (ClaudeKit): Block reading sensitive credential files
    is_priv, priv_base = _is_privacy_blocked(target_norm)
    if is_priv:
        return {
            "decision": "deny",
            "reason": (
                f"Privacy-Block Gate (ClaudeKit): Reading sensitive credential file ({priv_base}) "
                "is blocked to prevent secret leakage."
            ),
        }

    # CK-01 Scout-Block Gate (ClaudeKit): Block reading inside heavy build/vendor directories
    scout_dir = _check_scout_blocked_dir(target_norm)
    if scout_dir:
        return {
            "decision": "deny",
            "reason": (
                f"Scout-Block Gate (ClaudeKit): Traversing generated/vendor directory ({scout_dir}) "
                "leaks tokens. Target source files instead."
            ),
        }

    # 2. Pre-Verification: Check if file exists before reading
    if not os.path.exists(target_norm):
        return {
            "decision": "deny",
            "reason": (
                f"Pre-Verification Invariant: File does not exist: `{target_norm}`. "
                "Verify file path with fd, or rg -n before calling read_file (CLI) / view_file (IDE) to prevent retry loops."
            ),
        }

    # Retain skill.md, task.md, implementation_plan.md, and artifacts as exempt
    target_basename = os.path.basename(target_norm).lower()
    if (
        "skill.md" in norm_low
        or target_basename in (
            "task.md",
            "implementation_plan.md",
            "status.md",
            "manifest.md",
            "index.md",
            "agents.md",
            "gemini.md",
            "readme.md",
        )
        or "/brain/" in norm_low
        or args.get("IsSkillFile") is True
    ):
        return {"decision": "allow"}

    start_l = _to_int(args.get("StartLine"))
    end_l = _to_int(args.get("EndLine"))
    current_is_slice = (
        isinstance(start_l, int)
        and isinstance(end_l, int)
        and start_l > 0
        and end_l >= start_l
    )

    # 3. Hoisted Transcript Discovery and Parsing (Oracle Hardened Architecture)
    transcript_p = payload.get("transcriptPath", "")
    conv_id = payload.get("conversationId", "")
    if not transcript_p or not os.path.isfile(transcript_p):
        if conv_id:
            for cand_path in (
                f"~/.gemini/antigravity-cli/brain/{conv_id}/.system_generated/logs/transcript.jsonl",
                f"~/.gemini/antigravity-ide/brain/{conv_id}/.system_generated/logs/transcript.jsonl",
                f"~/.gemini/antigravity/brain/{conv_id}/.system_generated/logs/transcript.jsonl",
            ):
                cand = os.path.expanduser(cand_path)
                if os.path.isfile(cand):
                    transcript_p = cand
                    break

    read_count, total_reads, whole_reads, edits_count, reads_since_edit, file_slices = (
        _get_or_update_read_ledger(transcript_p, conv_id, workspace, target_norm)
    )

    line_cnt = _count_file_lines(target_norm) if os.path.isfile(target_norm) else 0
    basename = os.path.basename(target_norm)

    # 4. Read-Once Policy for Small Files (<= 200 lines):
    # Require whole read on initial inspection; once read once (total_reads >= 1) or edited (edits_count >= 1),
    # permit targeted slicing so post-edit verification never hits a Catch-22 deadlock.
    if line_cnt > 0 and line_cnt <= 200:
        if current_is_slice and whole_reads == 0 and total_reads == 0 and edits_count == 0:
            return {
                "decision": "deny",
                "reason": (
                    f"Read-Once Policy Invariant: `{basename}` has {line_cnt} lines (<= 200 lines). "
                    "Micro-slicing small files on initial read is blocked to prevent multi-turn token explosion. "
                    "Read the entire file once without StartLine/EndLine to populate context."
                ),
            }

    # 5. Mechanical Slice Boundary Guard for files > 200 lines
    policy = _load_active_guardrail_policy(workspace)
    slice_cap = int(policy.get("slice_cap", 250))
    policy_max_slices = int(policy.get("max_slices", 6))

    overwrite_args: dict | None = None
    if current_is_slice and line_cnt > 200 and (end_l - start_l + 1) > slice_cap:
        span = end_l - start_l + 1
        if span <= slice_cap + 10:
            end_l = min(line_cnt, start_l + slice_cap - 1) if start_l <= line_cnt else (start_l + slice_cap - 1)
            overwrite_args = {"StartLine": start_l, "EndLine": end_l}
        else:
            return {
                "decision": "deny",
                "reason": (
                    f"Token Economy Invariant: Slice window ({span} lines) on `{basename}` exceeds {slice_cap}-line maximum. "
                    f"Narrow the slice window (<= {slice_cap} lines) to the target function or block."
                ),
            }

    # 6. Outline-First Large File Guard (>400 lines): Block whole-file reads, require slices <= 250 lines
    if not current_is_slice and line_cnt > 400:
        skeleton = ""
        try:
            skeleton = _extract_inline_ast_skeleton(target_norm)
        except Exception:
            pass

        reason = (
            f"Outline-First Monolithic File Guard: `{basename}` has {line_cnt:,} total lines (> 400 lines). "
            "Whole-file reading is blocked to prevent context bloat. "
            "Suggested Action: Locate target coordinates first using rg -n, codegraph:symbol_lookup, "
            "codegraph:extract_symbols(root, path, symbols), codegraph:batch_query, or "
            "codegraph:summarize_path, then read a targeted semantic slice (<= 250 lines)."
        )
        if skeleton:
            reason += (
                f"\n\nInline AST Symbol Skeleton for `{basename}` ({line_cnt:,} lines):\n{skeleton}\n"
                "Read your target symbol directly using `read_file` (CLI) / `view_file` (IDE) with `StartLine` and `EndLine` (<= 250 lines)."
            )
        return {"decision": "deny", "reason": reason}

    # 7. Unedited session read ceiling (whole-file without intermediate edits)
    if not current_is_slice:
        effective_reads = reads_since_edit if edits_count > 0 else total_reads
        if effective_reads >= 8:
            basename = os.path.basename(target_norm)
            reason = (
                f"Active Loop Breaker ACTIVATED: `{basename}` has been read {effective_reads} times without intermediate edits. "
                "All further reads (whole-file or sliced) are blocked to prevent token exhaustion. "
                "Use rg -n for specific identifiers or codegraph:symbol_lookup instead."
            )
            return {"decision": "deny", "reason": reason}

    # 8. Slice Loop Breaker: Prevent duplicate slice loops or excessive unedited slicing
    if current_is_slice:
        slice_tuple = (start_l, end_l)
        prior_slices = list(file_slices)
        if slice_tuple in prior_slices:
            prior_slices.remove(slice_tuple)

        is_dup_slice = False
        len_cur = end_l - start_l + 1
        for ps in prior_slices:
            if ps == slice_tuple:
                is_dup_slice = True
                break
            inter = max(0, min(end_l, ps[1]) - max(start_l, ps[0]) + 1)
            if inter > 0:
                len_prior = ps[1] - ps[0] + 1
                if (inter / max(len_cur, len_prior)) >= 0.8:
                    is_dup_slice = True
                    break

        max_slices = _calculate_max_slices(line_cnt, base_max_slices=policy_max_slices, slice_cap=slice_cap)
        if is_dup_slice or len(file_slices) >= max_slices:
            basename = os.path.basename(target_norm)
            ceiling_str = "reached 6-slice ceiling" if max_slices == 6 else f"reached {max_slices}-slice ceiling"
            return {
                "decision": "deny",
                "reason": (
                    f"Slice Loop Breaker ACTIVATED: `{basename}` has already had {len(file_slices)} sliced reads "
                    f"({'duplicate slice loop' if is_dup_slice else ceiling_str}). "
                    "Further slicing is blocked to prevent token waste. Never sequential slice. "
                    "Use codegraph:extract_symbols(root, path, symbols), codegraph:batch_query, "
                    "rg -n for specific identifiers, or codegraph:symbol_lookup instead."
                ),
            }

    # 9. Whole-File Read Ceiling & Edit-Reset Loop Dampening (Decoupled, retaining required tokens)
    if whole_reads >= 2 and not current_is_slice:
        basename = os.path.basename(target_norm)
        reason = (
            f"Edit-Reset Loop Dampening ACTIVATED (Three-Strike Rule ACTIVATED): `{basename}` has been read whole {whole_reads} times across this session. "
            "Re-reading entire file is blocked to prevent context rot. "
            "Use rg -n or targeted slicing (<= 250 lines)."
        )
        return {"decision": "deny", "reason": reason}

    # 10. Three-Strike Read Budget Gate (without intermediate modifications or consecutive un-sliced reads)
    if read_count >= 3 and not current_is_slice:
        basename = os.path.basename(target_norm)
        reason = (
            f"Three-Strike Rule ACTIVATED: `{basename}` has been read {read_count} times without intermediate modifications. "
            "Re-reading entire file is blocked to prevent context rot. "
            "Use rg -n for specific lines/sections, targeted slicing (<= 250 lines), codegraph:summarize_path, or codegraph:callers_callees."
        )
        return {"decision": "deny", "reason": reason}

    if os.path.exists(target_norm):
        try:
            cur_mt = os.path.getmtime(target_norm)
            _update_read_ledger_mtime(transcript_p, conv_id, target_norm, cur_mt)
        except Exception:
            pass

    if overwrite_args is not None:
        return {"decision": "allow", "overwrite": overwrite_args}
    return {"decision": "allow"}


BLOCKED_DIR_PATTERNS = (
    "/node_modules",
    "/.venv",
    "/.git",
    "/.cache",
    "/.cargo",
    "/target",
    "/dist",
    "/build",
)


def _handle_list_dir(args: dict, payload: dict) -> dict:
    target_dir = (
        args.get("DirectoryPath")
        or args.get("path")
        or args.get("dir")
        or args.get("directory")
        or ""
    )
    if not target_dir:
        return {"decision": "allow"}

    workspace = ""
    ws_paths = payload.get("workspacePaths", [])
    if ws_paths and isinstance(ws_paths, list):
        workspace = ws_paths[0]
    if not workspace:
        workspace = os.getcwd()

    norm_dir = _normalize(target_dir, workspace)
    norm_low = norm_dir.lower().rstrip("/")

    # CK-01 Scout-Block Gate (ClaudeKit): Block listing generated/vendor directories
    scout_dir = _check_scout_blocked_dir(norm_dir)
    if scout_dir:
        return {
            "decision": "deny",
            "reason": (
                f"Scout-Block Gate (ClaudeKit): Traversing generated/vendor directory ({scout_dir}) "
                "leaks tokens. Target source files instead. Use targeted fd with --max-depth (e.g. `fd --max-depth 2 <dir>`) or inspect configuration manifests."
            ),
        }

    for blocked in BLOCKED_DIR_PATTERNS:
        if norm_low.endswith(blocked) or f"{blocked}/" in norm_low:
            basename = os.path.basename(norm_dir)
            return {
                "decision": "deny",
                "reason": (
                    f"Token Economy Invariant: Calling list_dir on dependency/cache directory (`{basename}`) "
                    "is blocked to prevent massive context dumps (~5,000–50,000 tokens). "
                    "Use targeted fd with --max-depth (e.g. `fd --max-depth 2 <dir>`) or inspect configuration manifests."
                ),
            }

    return {"decision": "allow"}


def _handle_manage_task(args: dict, payload: dict) -> dict:
    action = str(args.get("Action", "")).strip().lower()
    task_id = str(args.get("TaskId", "")).strip()

    if action == "status":
        conv_id = payload.get("conversationId") or f"pid_{os.getppid()}"
        from pathlib import Path
        state_file = Path(tempfile.gettempdir()) / f".antigravity_actions_{conv_id}.json"
        if state_file.is_file():
            try:
                actions = json.loads(state_file.read_text(encoding="utf-8"))
                # Note: current action is already appended by _track_and_check_loop_with_jev at index -1.
                prior_actions = actions[:-1] if isinstance(actions, list) else []
                if any(
                    isinstance(entry, dict)
                    and entry.get("tool") == "manage_task"
                    and str(entry.get("args", {}).get("Action", "")).strip().lower() == "status"
                    and str(entry.get("args", {}).get("TaskId", "")).strip() == task_id
                    for entry in prior_actions
                ):
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Token Economy & Anti-Polling Invariant: Consecutive status polling on background task `{task_id}` detected. "
                            "Antigravity reactively resumes execution when background tasks finish. "
                            "Do NOT poll `manage_task(Action='status')` in a loop. "
                            "Stop calling tools and yield the turn immediately to wait for reactive task completion notification."
                        ),
                    }
            except Exception:
                pass

    return {"decision": "allow"}


def _handle_manage_subagents(args: dict, payload: dict) -> dict:
    action = str(args.get("Action", "")).strip().lower()

    if action == "list":
        conv_id = payload.get("conversationId") or f"pid_{os.getppid()}"
        from pathlib import Path
        state_file = Path(tempfile.gettempdir()) / f".antigravity_actions_{conv_id}.json"
        if state_file.is_file():
            try:
                actions = json.loads(state_file.read_text(encoding="utf-8"))
                prior_actions = actions[:-1] if isinstance(actions, list) else []
                is_consecutive = (
                    bool(prior_actions)
                    and isinstance(prior_actions[-1], dict)
                    and prior_actions[-1].get("tool") == "manage_subagents"
                    and str(prior_actions[-1].get("args", {}).get("Action", "")).strip().lower() == "list"
                )
                list_count = sum(
                    1 for entry in prior_actions
                    if isinstance(entry, dict)
                    and entry.get("tool") == "manage_subagents"
                    and str(entry.get("args", {}).get("Action", "")).strip().lower() == "list"
                )
                if is_consecutive or list_count >= 2:
                    return {
                        "decision": "deny",
                        "reason": (
                            "Token Economy & Anti-Polling Invariant: Repetitive `manage_subagents(Action='list')` polling detected. "
                            "Antigravity reactively resumes execution when subagents complete or message you. "
                            "Yield the turn immediately instead of polling subagent status."
                        ),
                    }
            except Exception:
                pass

    return {"decision": "allow"}


_SCHEDULE_POLL_PROMPT_RE = re.compile(
    r"(?i)\b(?:subagent|builder|explorer|oracle-review|simplifier|task-\d+|"
    r"check\s+(?:progress|completion|status|after)|"
    r"wake\s+up\s+(?:on|when)\s+.*?(?:subagent|builder|complete|finish))"
)


def _handle_schedule(args: dict, payload: dict) -> dict:
    if not isinstance(args, dict):
        return {"decision": "allow"}

    duration = args.get("DurationSeconds")
    cron_expr = str(args.get("CronExpression") or "").strip()

    if duration is not None and not cron_expr:
        prompt = str(args.get("Prompt") or "").strip()
        timer_cond = str(args.get("TimerCondition") or "").strip()
        has_specific_sender = bool(timer_cond) and timer_cond.lower() not in ("never", "any", "none", "null")
        is_poll_prompt = bool(_SCHEDULE_POLL_PROMPT_RE.search(prompt))

        prior_actions = _get_prior_actions(payload)
        has_prior_poll_or_timer = any(
            isinstance(entry, dict)
            and (
                entry.get("tool") == "schedule"
                or (
                    entry.get("tool") == "manage_subagents"
                    and str((entry.get("args") or {}).get("Action", "")).strip().lower() == "list"
                )
                or (
                    entry.get("tool") == "manage_task"
                    and str((entry.get("args") or {}).get("Action", "")).strip().lower() == "status"
                )
            )
            for entry in prior_actions
        )

        if (is_poll_prompt and not has_specific_sender) or has_prior_poll_or_timer:
            return {
                "decision": "deny",
                "reason": (
                    "Token Economy & Anti-Polling Invariant: One-shot `schedule` timer polling on subagents or background tasks is blocked. "
                    "Stop calling `schedule` for polling and simply end your turn (call no more tools) to wait for reactive wakeup."
                ),
            }

    if bool(args.get("IsDaemon")):
        return {
            "decision": "force_ask",
            "reason": (
                "Standing Daemon Schedule Gate: Creating a persistent daemon schedule (`IsDaemon=True`) "
                "that continues firing after the task completes requires explicit user confirmation."
            ),
        }

    return {"decision": "allow"}


def _safe_shallow_overwrite(orig_args: dict, updates: dict) -> dict:
    """Preserves sibling keys inside nested dict objects (e.g. Arguments) for shallow top-level overwrite."""
    if not isinstance(updates, dict):
        return {}
    base = orig_args if isinstance(orig_args, dict) else {}
    merged: dict = {}
    for k, v in updates.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            merged[k] = {**base[k], **v}
        else:
            merged[k] = v
    return merged


def _count_parallel_branches_in_script(script: str) -> int:
    max_branches = 0
    try:
        tree = ast.parse(script)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name == "parallel":
                    if len(node.args) == 1 and isinstance(node.args[0], (ast.List, ast.Tuple, ast.Set)):
                        cnt = len(node.args[0].elts)
                    else:
                        cnt = len(node.args) + len(node.keywords)
                    if cnt > max_branches:
                        max_branches = cnt
    except Exception:
        pass

    for m in re.finditer(r"\bparallel\s*\(([\s\S]*?)\)", script):
        inner = m.group(1).strip()
        if not inner:
            continue
        if inner.startswith("[") and inner.endswith("]"):
            inner = inner[1:-1].strip()
        parts = [p.strip() for p in inner.split(",") if p.strip()]
        if len(parts) > max_branches:
            max_branches = len(parts)
    return max_branches


def _handle_run_workflow(args: dict, payload: dict) -> dict:
    if not isinstance(args, dict):
        return {"decision": "allow"}

    script = str(args.get("Script") or args.get("script") or args.get("Workflow") or "")
    branches_arg = args.get("Branches") or args.get("branches") or args.get("Parallel")
    branch_count = len(branches_arg) if isinstance(branches_arg, list) else 0
    if script:
        branch_count = max(branch_count, _count_parallel_branches_in_script(script))

    if branch_count > 6:
        return {
            "decision": "deny",
            "reason": (
                f"Workflow Concurrency Budget Violation: `parallel(...)` fan-out ({branch_count} branches) "
                "exceeds maximum of 6 concurrent branches. Batch workflow steps into smaller waves."
            ),
        }

    is_non_builder, role_label = _detect_non_builder_session(payload)
    if is_non_builder and script:
        cwd = str(args.get("Cwd") or os.getcwd())
        mutated_file = _detect_shell_source_mutation(script, cwd)
        if not mutated_file:
            for m_edit in re.finditer(
                r"""(?:write_file|write_to_file|edit_file|replace_file_content|multi_replace_file_content)\s*\([^)]*?['"]([^'"]+)['"]""",
                script,
            ):
                cand_file = m_edit.group(1)
                if _is_app_source_file(cand_file, cwd):
                    mutated_file = cand_file
                    break
        if mutated_file:
            return {
                "decision": "deny",
                "reason": (
                    f"Role Isolation Workflow Guard (pm-no-implementation.md): "
                    f"Non-builder session ({role_label}) is strictly prohibited from mutating application source code "
                    f"(`{mutated_file}`) via `run_workflow`. Delegate code modifications to a builder subagent."
                ),
            }

    model_arg = str(args.get("Model") or args.get("model") or "").strip().lower()
    has_model_escalation = model_arg in ("pro", "gemini-4-argon-high") or bool(
        re.search(
            r"""(?i)(?:\bmodel\s*[:=]\s*['"]?(?:pro|gemini-4-argon-high)\b|['"]model['"]\s*:\s*['"](?:pro|gemini-4-argon-high)['"]|--model(?:=|\s+)['"]?(?:pro|gemini-4-argon-high)\b)""",
            script,
        )
    )
    if has_model_escalation:
        return {
            "decision": "force_ask",
            "reason": (
                "Workflow Model Escalation Gate: `run_workflow` script requests frontier model "
                "(`pro` / `gemini-4-argon-high`). Explicit user confirmation is required."
            ),
        }

    return {"decision": "allow"}


def _handle_define_subagent(args: dict, payload: dict) -> dict:
    if not isinstance(args, dict):
        return {"decision": "allow"}

    if _is_subagent_conversation(payload):
        first_step = _get_first_transcript_step(payload)
        first_content = str((first_step or {}).get("content") or "") if isinstance(first_step, dict) else ""
        explicitly_leased = (
            bool(payload.get("allow_define_subagent"))
            or "allow_define_subagent" in first_content
            or "EnableSubagentTools: true" in first_content
        )
        if not explicitly_leased:
            return {
                "decision": "deny",
                "reason": (
                    "Subagent Recursion Depth Violation (max_depth = 1): Child subagents are not permitted "
                    "to define nested subagents (`define_subagent`). Return findings to the parent orchestrator instead."
                ),
            }

    sys_prompt = str(args.get("SystemPrompt") or args.get("systemPrompt") or "")
    if len(sys_prompt) > 8000:
        return {
            "decision": "deny",
            "reason": (
                f"Subagent SystemPrompt Budget Violation: `SystemPrompt` length ({len(sys_prompt)} chars) "
                "exceeds 8,000-character ceiling. Keep custom subagent definitions concise."
            ),
        }

    return {"decision": "allow"}


_KNOWN_MULTI_UNDERSCORE_MCP_SERVERS = (
    "codex_knowledge",
    "context_health",
    "codegraph",
    "context7",
    "browseros-neo",
    "browseros_neo",
)

_MUTATING_MCP_TOOLS = frozenset({
    "vault_write",
    "wiki_ingest",
    "wiki_rebuild",
    "memory_store",
    "graph_upsert",
    "knowledge_capture",
    "orchestration_lesson",
    "checkpoint_save",
    "handoff_write",
    "handoff_checkpoint",
    "commit_context_ledger",
})

_MUTATING_MCP_VERB_RE = re.compile(
    r"(?:^|_)(?:create|delete|update|write|drop|remove)(?:_|$)",
    re.IGNORECASE,
)

_READONLY_EXPLORER_ROLES = frozenset({
    "research",
    "research-explorer",
    "frontend-explorer",
    "backend-explorer",
    "explorer",
    "user-tester",
    "oracle-review",
    "hallucination-auditor",
    "implementation-review",
    "frontend-qc",
    "test-runner",
    "diff-helper",
})


def _extract_mcp_server_and_tool(tool_name: str, args: dict) -> tuple[str, str]:
    if tool_name == "call_mcp_tool":
        if not isinstance(args, dict):
            return ("", "")
        server_name = str(args.get("ServerName") or args.get("serverName") or args.get("server_name") or "").strip()
        bare_tool = str(args.get("ToolName") or args.get("toolName") or args.get("tool_name") or "").strip()
        return (server_name, bare_tool)
    if tool_name.startswith("mcp_"):
        rest = tool_name[4:]
        for srv in _KNOWN_MULTI_UNDERSCORE_MCP_SERVERS:
            prefix = f"{srv}_"
            if rest.startswith(prefix):
                return (srv, rest[len(prefix):])
        if "_" in rest:
            srv, bare = rest.split("_", 1)
            return (srv, bare)
        return (rest, "")
    return ("", "")


def _handle_mcp_tool(tool_name: str, args: dict, payload: dict) -> dict:
    server_name, bare_tool = _extract_mcp_server_and_tool(tool_name, args)
    if not bare_tool:
        return {"decision": "allow"}

    role = _extract_session_role(payload)
    subagent_type = str(payload.get("subagentType") or payload.get("typeName") or payload.get("TypeName") or "").strip().lower()
    is_readonly_explorer = role in _READONLY_EXPLORER_ROLES or (
        subagent_type == "research" and role not in ("doc-sync-worker", "librarian")
    )
    if not is_readonly_explorer and _is_subagent_conversation(payload):
        first_step = _get_first_transcript_step(payload)
        first_content = str((first_step or {}).get("content") or "") if isinstance(first_step, dict) else ""
        if re.search(r'TypeName:\s*[`\'"]?research[`\'"]?', first_content, re.IGNORECASE) and role not in ("doc-sync-worker", "librarian"):
            is_readonly_explorer = True

    if is_readonly_explorer:
        bare_low = bare_tool.lower()
        if bare_low in _MUTATING_MCP_TOOLS or bool(_MUTATING_MCP_VERB_RE.search(bare_low)):
            return {
                "decision": "deny",
                "reason": (
                    f"Read-Only Subagent MCP Mutation Lock: Subagent role '{role or 'research'}' is read-only "
                    f"and prohibited from invoking mutating MCP tool `{bare_tool}` on server `{server_name}`."
                ),
            }

    return {"decision": "allow"}


def _matches_allowed_file(target_norm: str, allowed_pattern: str, workspace: str) -> bool:
    target_clean = os.path.normpath(target_norm).lower()
    pattern_clean = allowed_pattern.strip().strip("'\"`")
    if not pattern_clean:
        return False

    workspace_clean = workspace.lower().rstrip("/")
    rel_path = os.path.relpath(target_clean, workspace_clean) if workspace_clean else ""
    pattern_norm = os.path.normpath(os.path.join(workspace_clean, pattern_clean) if not os.path.isabs(pattern_clean) else pattern_clean).lower()

    # Exact match
    if target_clean == pattern_norm or target_clean == pattern_clean.lower():
        return True
    if rel_path and (rel_path == pattern_clean.lower() or rel_path == os.path.normpath(pattern_clean.lower())):
        return True

    # Basename or suffix match
    target_basename = os.path.basename(target_clean)
    if target_clean.endswith("/" + pattern_clean.lower().lstrip("/")) or target_basename == pattern_clean.lower():
        return True

    # Glob match
    if any(c in pattern_clean for c in ("*", "?", "[", "]")):
        pat_low = pattern_clean.lower()
        if fnmatch.fnmatch(target_clean, pat_low):
            return True
        if rel_path and fnmatch.fnmatch(rel_path, pat_low):
            return True
        if fnmatch.fnmatch(target_basename, pat_low):
            return True
        if "**" in pat_low:
            regex_pat = re.escape(pat_low).replace(r"\*\*", ".*").replace(r"\*", "[^/]*") + "$"
            if re.search(regex_pat, target_clean) or (rel_path and re.search(regex_pat, rel_path)):
                return True

    # Directory prefix match
    if pattern_clean.endswith(("/", "/*")):
        dir_prefix = pattern_norm.rstrip("/*")
        if target_clean.startswith(dir_prefix + "/"):
            return True

    return False


def _extract_allowed_files(content: str) -> tuple[bool, list[str]]:
    m = re.search(r'(?:^|\n|\b)[ \t]*[`*_-]*allowed_files[`*_-]*\s*:\s*(.*)', content, re.IGNORECASE)
    if not m:
        return (False, [])

    rest = content[m.start():].strip()

    # Try YAML parsing first if yaml is available
    try:
        import yaml
        lines = []
        for i, line in enumerate(rest.splitlines()):
            if i == 0:
                lines.append(line)
            else:
                if re.match(r'^[A-Za-z0-9_-]+:', line) or re.match(r'^[#*]{2,}', line):
                    break
                lines.append(line)
        parsed = yaml.safe_load('\n'.join(lines))
        if isinstance(parsed, dict):
            for k, v in parsed.items():
                if 'allowed_files' in str(k).lower():
                    if isinstance(v, list):
                        return (True, [str(x).strip() for x in v if x is not None])
                    elif isinstance(v, str) and v.strip():
                        return (True, [v.strip()])
                    elif v is None:
                        return (True, [])
    except Exception:
        pass

    # Fallback JSON / regex extraction
    line_rest = m.group(1).strip()
    if line_rest.startswith('['):
        arr_m = re.search(r'\[(.*?)\]', rest, re.DOTALL)
        if arr_m:
            try:
                items = json.loads('[' + arr_m.group(1) + ']')
                return (True, [str(x).strip() for x in items if x is not None])
            except Exception:
                raw_items = [x.strip(' \'"') for x in arr_m.group(1).split(',') if x.strip(' \'"')]
                return (True, raw_items)

    # Fallback bullet lines
    files = []
    for line in rest.splitlines()[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(('-', '*')):
            val = stripped[1:].strip().strip('\'"`')
            if val:
                files.append(val)
        elif re.match(r'^[A-Za-z0-9_-]+:', stripped) or re.match(r'^[#*]{2,}', stripped):
            break
    return (True, files)


def _extract_ts_exports(content: str) -> set[str]:
    exports: set[str] = set()
    try:
        # Named export blocks: export { A, B as C, type D }
        for m in re.finditer(r"export\s*\{([^}]+)\}", content):
            for item in m.group(1).split(","):
                item = item.strip()
                if item.startswith("type "):
                    item = item[5:].strip()
                if " as " in item:
                    item = item.split(" as ")[1].strip()
                if item:
                    exports.add(item)
        # Declarations: export (declare)? (async)? (const|let|var|function|class|interface|type|enum) Name
        for m in re.finditer(r"export\s+(?:declare\s+)?(?:async\s+)?(?:const|let|var|function\*?|class|interface|type|enum)\s+([A-Za-z0-9_$]+)", content):
            exports.add(m.group(1))
        # Export default
        if re.search(r"export\s+default\b", content):
            exports.add("default")
    except Exception:
        pass
    return exports


def _find_package_root(start_dir: str, workspace: str) -> str:
    curr = start_dir
    workspace_norm = os.path.normpath(workspace)
    while True:
        if os.path.isfile(os.path.join(curr, "package.json")) or os.path.isfile(os.path.join(curr, "tsconfig.json")):
            return curr
        if curr == workspace_norm or curr == os.path.dirname(curr):
            break
        curr = os.path.dirname(curr)
    return workspace_norm


def _resolve_local_import_path(import_path: str, target_norm: str, workspace: str) -> tuple[str, list[str]]:
    base_dir = os.path.dirname(target_norm)
    if import_path.startswith(("./", "../")):
        raw_target = os.path.normpath(os.path.join(base_dir, import_path))
    elif import_path.startswith("@/"):
        pkg_root = _find_package_root(base_dir, workspace)
        sub_path = import_path[2:]
        src_dir = os.path.join(pkg_root, "src")
        if os.path.isdir(src_dir):
            raw_target = os.path.normpath(os.path.join(src_dir, sub_path))
        else:
            raw_target = os.path.normpath(os.path.join(pkg_root, sub_path))
    else:
        return "", []

    candidates: list[str] = []
    # Check exact match
    if os.path.isfile(raw_target):
        candidates.append(raw_target)
    # Check ESM .js -> .ts / .tsx mapping
    if raw_target.endswith(".js"):
        for ts_ext in (".ts", ".tsx"):
            alt = raw_target[:-3] + ts_ext
            if os.path.isfile(alt):
                candidates.append(alt)
    elif raw_target.endswith(".mjs"):
        alt = raw_target[:-4] + ".mts"
        if os.path.isfile(alt):
            candidates.append(alt)

    # Standard file extension probes
    for ext in (".ts", ".tsx", ".d.ts", ".js", ".jsx", ".mjs", ".cjs", ".json"):
        cand = raw_target + ext
        if os.path.isfile(cand):
            candidates.append(cand)

    # Directory barrel probes
    for ext in (".ts", ".tsx", ".d.ts", ".js", ".jsx", ".mjs", ".cjs", ".json"):
        cand = os.path.join(raw_target, "index" + ext)
        if os.path.isfile(cand):
            candidates.append(cand)

    return raw_target, candidates


def _verify_imports_shift_left(
    target_norm: str,
    tool_name: str,
    args: dict,
    payload: dict,
    workspace: str,
    allowed_files: list[str],
) -> dict | None:
    """Shift-Left Pre-Edit AST Import Verification (Upgrade 5).
    
    Verifies that newly added local relative or @/ alias imports exist on disk (or in allowed_files),
    and that imported named symbols are actually exported by the target module.
    Execution capped under <10ms with strict fail-open try/except.
    """
    try:
        ext = os.path.splitext(target_norm)[1].lower()
        if ext not in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
            return None

        target_norm_low = target_norm.lower()
        ws_low = (workspace or "").lower()
        in_temp = "/tmp/" in target_norm_low or target_norm_low.startswith(("/tmp/", tempfile.gettempdir().lower()))
        is_ws_in_temp = bool(ws_low and ("/tmp/" in ws_low or ws_low.startswith(("/tmp/", tempfile.gettempdir().lower()))))
        if "/.gemini/" in target_norm_low or (in_temp and not is_ws_in_temp):
            return None

        proposed_code = args.get("ReplacementContent") or args.get("CodeContent") or args.get("Replacement") or args.get("Content") or ""
        target_content = args.get("TargetContent") or args.get("Target") or ""
        if not proposed_code:
            return None

        if ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
            import_patterns = [
                re.compile(r"(?:import|export)\s+(?:type\s+)?(\{[\s\S]*?\}|[A-Za-z0-9_$,\s*]+)\s+from\s+['\"]([^'\"]+)['\"]"),
                re.compile(r"import\s+['\"]([^'\"]+)['\"]"),
            ]

            found_imports: list[tuple[str, str, str]] = []
            for m in import_patterns[0].finditer(proposed_code):
                clause = m.group(1).strip()
                import_path = m.group(2).strip()
                stmt = m.group(0).strip()
                found_imports.append((stmt, clause, import_path))

            for m in import_patterns[1].finditer(proposed_code):
                import_path = m.group(1).strip()
                stmt = m.group(0).strip()
                if not any(x[2] == import_path for x in found_imports):
                    found_imports.append((stmt, "", import_path))

            for stmt, clause, import_path in found_imports:
                if not import_path.startswith(("./", "../", "@/")):
                    continue

                if target_content and stmt in target_content:
                    continue

                raw_target, candidates = _resolve_local_import_path(import_path, target_norm, workspace)
                if not raw_target:
                    continue

                resolved_file = candidates[0] if candidates else None

                if not resolved_file:
                    potential_probes = [
                        raw_target,
                        raw_target + ".ts",
                        raw_target + ".tsx",
                        raw_target + ".js",
                        raw_target + ".jsx",
                        os.path.join(raw_target, "index.ts"),
                        os.path.join(raw_target, "index.tsx"),
                    ]
                    matches_allowed = False
                    if allowed_files:
                        for pat in allowed_files:
                            for probe in potential_probes:
                                if _matches_allowed_file(probe, pat, workspace):
                                    matches_allowed = True
                                    break
                            if matches_allowed:
                                break

                    if not matches_allowed:
                        target_rel = os.path.relpath(raw_target, workspace)
                        return {
                            "decision": "deny",
                            "reason": (
                                f"Shift-Left AST Import Guard: Imported local module '{import_path}' cannot be resolved on disk "
                                f"(checked '{target_rel}') and is not in the subagent's allowed_files lease. "
                                "Verify the path or obtain shard lease before importing uncreated modules."
                            ),
                        }
                    continue

                if "{" in clause and "}" in clause:
                    brace_match = re.search(r"\{([^}]+)\}", clause)
                    if not brace_match:
                        continue
                    symbol_tokens = [s.strip() for s in brace_match.group(1).split(",") if s.strip()]
                    imported_symbols: list[str] = []
                    for tok in symbol_tokens:
                        if tok.startswith("type "):
                            tok = tok[5:].strip()
                        if " as " in tok:
                            orig = tok.split(" as ")[0].strip()
                        else:
                            orig = tok
                        if orig and orig not in imported_symbols:
                            imported_symbols.append(orig)

                    if not imported_symbols:
                        continue

                    try:
                        with open(resolved_file, "r", encoding="utf-8", errors="ignore") as f:
                            target_file_content = f.read(200_000)
                    except Exception:
                        continue

                    if re.search(r"\bexport\s+\*", target_file_content):
                        continue

                    exports = _extract_ts_exports(target_file_content)

                    barrel_path = os.path.join(os.path.dirname(resolved_file), "index.ts")
                    if os.path.isfile(barrel_path) and barrel_path != resolved_file:
                        try:
                            with open(barrel_path, "r", encoding="utf-8", errors="ignore") as bf:
                                barrel_content = bf.read(200_000)
                            if re.search(r"\bexport\s+\*", barrel_content):
                                continue
                            barrel_exports = _extract_ts_exports(barrel_content)
                            exports.update(barrel_exports)
                        except Exception:
                            pass

                    for sym in imported_symbols:
                        if target_content and sym in target_content:
                            continue
                        if sym in exports:
                            continue

                        sym_in_content = bool(re.search(r"\b" + re.escape(sym) + r"\b", target_file_content))
                        if not sym_in_content:
                            target_rel = os.path.relpath(resolved_file, workspace)
                            sorted_exports = sorted(list(exports))[:15]
                            return {
                                "decision": "deny",
                                "reason": (
                                    f"Shift-Left AST Symbol Guard: Symbol '{sym}' is not exported by '{target_rel}'. "
                                    f"Verified exports in '{target_rel}': {sorted_exports}"
                                ),
                            }
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
    content = re.sub(r",\s*([}\]])", r"\1", content)
    return content


def _simulate_file_mutation(tool_name: str, args: dict, target_path: str) -> str | None:
    """Simulate resulting file content in memory for pre-write syntax validation."""
    try:
        if tool_name in ("write_to_file", "write_file"):
            code_content = args.get("CodeContent", "") if tool_name == "write_to_file" else args.get("Content", "")
            if not isinstance(code_content, str):
                return None
            is_append = bool(args.get("Append"))
            if is_append and os.path.isfile(target_path):
                try:
                    with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                        existing = f.read()
                    return existing + code_content
                except Exception:
                    return code_content
            return code_content

        if tool_name == "edit_file":
            target = args.get("Target", "")
            replacement = args.get("Replacement", "")
            if not isinstance(target, str) or not isinstance(replacement, str):
                return None
            if not os.path.isfile(target_path):
                return None
            try:
                with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                    existing = f.read()
            except Exception:
                return None
            if target and target in existing:
                return existing.replace(target, replacement)
            return None

        if tool_name == "replace_file_content":
            target_content = args.get("TargetContent", "")
            replacement_content = args.get("ReplacementContent", "")
            if not isinstance(target_content, str) or not isinstance(replacement_content, str):
                return None
            target_content = target_content.replace("\r\n", "\n")
            replacement_content = replacement_content.replace("\r\n", "\n")
            if not os.path.isfile(target_path):
                return replacement_content

            try:
                with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                    file_text = f.read().replace("\r\n", "\n")
            except Exception:
                return None

            start_line = _to_int(args.get("StartLine"))
            end_line = _to_int(args.get("EndLine"))
            allow_multiple = bool(args.get("AllowMultiple"))
            count = -1 if allow_multiple else 1

            if start_line is not None and end_line is not None:
                if start_line > end_line:
                    return None
                lines = file_text.splitlines(keepends=True)
                s_idx = max(0, start_line - 1)
                e_idx = min(len(lines), end_line)
                window = "".join(lines[s_idx:e_idx])
                if target_content in window:
                    rep_window = window.replace(target_content, replacement_content, count)
                    return "".join(lines[:s_idx]) + rep_window + "".join(lines[e_idx:])
                return None
            else:
                if target_content in file_text:
                    return file_text.replace(target_content, replacement_content, count)
                return None

        if tool_name == "multi_replace_file_content":
            if not os.path.isfile(target_path):
                simulated = ""
            else:
                try:
                    with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
                        simulated = f.read().replace("\r\n", "\n")
                except Exception:
                    return None

            chunks = args.get("ReplacementChunks", [])
            if not isinstance(chunks, list):
                return None

            for chunk in chunks:
                if not isinstance(chunk, dict):
                    continue
                tc = chunk.get("TargetContent", "")
                rc = chunk.get("ReplacementContent", "")
                if not isinstance(tc, str) or not isinstance(rc, str) or not tc:
                    continue
                tc = tc.replace("\r\n", "\n")
                rc = rc.replace("\r\n", "\n")
                s_l = _to_int(chunk.get("StartLine"))
                e_l = _to_int(chunk.get("EndLine"))
                if s_l is not None and e_l is not None:
                    if s_l > e_l:
                        return None
                    lines = simulated.splitlines(keepends=True)
                    s_idx = max(0, s_l - 1)
                    e_idx = min(len(lines), e_l)
                    win = "".join(lines[s_idx:e_idx])
                    if tc in win:
                        rep_win = win.replace(tc, rc, 1)
                        simulated = "".join(lines[:s_idx]) + rep_win + "".join(lines[e_idx:])
                    else:
                        return None
                else:
                    if tc in simulated:
                        simulated = simulated.replace(tc, rc, 1)
                    else:
                        return None
            return simulated

    except Exception:
        return None
    return None


def _validate_simulated_syntax(target_path: str, simulated: str) -> dict | None:
    """Validate in-memory simulated content for syntax errors before writing to disk."""
    if not simulated or not simulated.strip():
        return None

    filename = os.path.basename(target_path)
    ext = os.path.splitext(target_path)[1].lower()

    # 1. Python (.py)
    if ext == ".py":
        try:
            ast.parse(simulated, filename=target_path)
        except SyntaxError as e:
            err_detail = f"line {e.lineno}, col {e.offset}: {e.msg}"
            return {
                "decision": "deny",
                "reason": (
                    f"Pre-Edit Linter Gate (SWE-agent ACI): Syntax error in simulated edit to {filename}: "
                    f"{err_detail}. Fix syntax in-flight before writing to disk."
                ),
            }
        except Exception:
            pass

    # 2. JSON / JSONC (.json, .jsonc)
    elif ext in (".json", ".jsonc"):
        is_jsonc = (
            ext == ".jsonc"
            or filename.lower().startswith("tsconfig")
            or ".vscode" in target_path.lower()
        )
        try:
            if is_jsonc:
                cleaned = _strip_json_comments_and_trailing_commas(simulated)
                json.loads(cleaned)
            else:
                json.loads(simulated)
        except json.JSONDecodeError as e:
            err_detail = f"{e.msg} at line {e.lineno} col {e.colno}"
            return {
                "decision": "deny",
                "reason": (
                    f"Pre-Edit Linter Gate (SWE-agent ACI): Syntax error in simulated edit to {filename}: "
                    f"{err_detail}. Fix syntax in-flight before writing to disk."
                ),
            }
        except Exception:
            pass

    # 3. YAML (.yaml, .yml)
    elif ext in (".yaml", ".yml"):
        try:
            import yaml
            yaml.safe_load(simulated)
        except ImportError:
            pass
        except Exception as e:
            err_detail = str(e).strip()
            return {
                "decision": "deny",
                "reason": (
                    f"Pre-Edit Linter Gate (SWE-agent ACI): Syntax error in simulated edit to {filename}: "
                    f"{err_detail}. Fix syntax in-flight before writing to disk."
                ),
            }

    # 4. TOML (.toml)
    elif ext == ".toml":
        try:
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            tomllib.loads(simulated)
        except ImportError:
            pass
        except Exception as e:
            err_detail = str(e).strip()
            return {
                "decision": "deny",
                "reason": (
                    f"Pre-Edit Linter Gate (SWE-agent ACI): Syntax error in simulated edit to {filename}: "
                    f"{err_detail}. Fix syntax in-flight before writing to disk."
                ),
            }

    # 5. Shell (.sh, .bash)
    elif ext in (".sh", ".bash"):
        try:
            res = subprocess.run(
                ["bash", "-n"],
                input=simulated,
                text=True,
                capture_output=True,
                timeout=2,
            )
            if res.returncode != 0:
                err_detail = (res.stderr or res.stdout or "").strip()
                return {
                    "decision": "deny",
                    "reason": (
                        f"Pre-Edit Linter Gate (SWE-agent ACI): Syntax error in simulated edit to {filename}: "
                        f"{err_detail}. Fix syntax in-flight before writing to disk."
                    ),
                }
        except Exception:
            pass

    return None


def _verify_target_content_fuzzy(target_norm: str, args: dict) -> dict | None:
    """Aider-style TargetContent pre-edit verification with difflib fuzzy match hints."""
    target_content = args.get("TargetContent", "")
    if not isinstance(target_content, str) or not target_content.strip():
        return None
    if not os.path.isfile(target_norm):
        return None

    try:
        with open(target_norm, "r", encoding="utf-8", errors="ignore") as f:
            file_content = f.read()
    except Exception:
        return None

    if not file_content:
        return None

    # Normalize CRLF
    file_content = file_content.replace("\r\n", "\n")
    norm_target = target_content.replace("\r\n", "\n")

    file_lines = file_content.splitlines(keepends=True)
    total_lines = len(file_lines)
    if total_lines == 0:
        return None

    filename = os.path.basename(target_norm)
    start_line = _to_int(args.get("StartLine"))
    end_line = _to_int(args.get("EndLine"))

    # Case 1: Both StartLine and EndLine specified
    if start_line is not None and end_line is not None:
        if start_line > end_line:
            return {
                "decision": "deny",
                "reason": f"Invalid line range: StartLine ({start_line}) > EndLine ({end_line}).",
            }
        grace_start = max(1, start_line - 5)
        grace_end = min(total_lines, end_line + 5)
        window = "".join(file_lines[grace_start - 1 : grace_end])
        if norm_target in window:
            return None

        # Check for pure indentation or whitespace drift inside grace window (LOSS-01)
        target_lines = norm_target.splitlines(keepends=True)
        tc_stripped = [l.strip() for l in target_lines if l.strip()]

        if tc_stripped:
            tc_count = len(target_lines)
            min_i = grace_start - 1
            max_i = min(total_lines - tc_count + 1, grace_end)
            matches = []
            for i in range(min_i, max_i):
                cand = file_lines[i : i + tc_count]
                cand_stripped = [l.strip() for l in cand if l.strip()]
                if cand_stripped == tc_stripped:
                    dist = abs((i + 1) - start_line)
                    matches.append((dist, i + 1, i + tc_count, "".join(cand)))

            if not matches:
                for c_len in range(len(tc_stripped), min(tc_count + 3, grace_end - min_i + 1)):
                    if c_len == tc_count:
                        continue
                    for i in range(min_i, min(total_lines - c_len + 1, grace_end - c_len + 1)):
                        cand = file_lines[i : i + c_len]
                        cand_stripped = [l.strip() for l in cand if l.strip()]
                        if cand_stripped == tc_stripped:
                            dist = abs((i + 1) - start_line)
                            matches.append((dist, i + 1, i + c_len, "".join(cand)))

            if matches:
                matches.sort(key=lambda m: m[0])
                c_start, c_end, c_text = matches[0][1], matches[0][2], matches[0][3]
                return {
                    "decision": "allow",
                    "overwrite": {
                        "TargetContent": c_text,
                        "StartLine": c_start,
                        "EndLine": c_end,
                    },
                }

        # Check if TargetContent exists elsewhere in file
        if norm_target in file_content:
            allow_multiple = bool(args.get("AllowMultiple"))
            occ_count = file_content.count(norm_target)
            tc_line_count = len(norm_target.splitlines())
            if occ_count > 1:
                occurrences = []
                pos = 0
                while True:
                    idx = file_content.find(norm_target, pos)
                    if idx == -1:
                        break
                    s_line = file_content[:idx].count("\n") + 1
                    e_line = s_line + max(0, tc_line_count - 1)
                    occurrences.append((s_line, e_line))
                    pos = idx + len(norm_target)

                if allow_multiple:
                    first_start = occurrences[0][0]
                    last_end = occurrences[-1][1]
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Pre-Edit Fuzzy Match Gate (Aider ACI): TargetContent not found in {filename} lines {start_line}-{end_line}. "
                            f"TargetContent occurs {occ_count} times in {filename}. "
                            f"Since AllowMultiple=True, expand line range to span all occurrences [StartLine={first_start}, EndLine={last_end}] (or [1, {total_lines}]) to replace all instances."
                        ),
                    }
                else:
                    ranges_str = ", ".join(f"[{s}, {e}]" for s, e in occurrences)
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Pre-Edit Fuzzy Match Gate (Aider ACI): TargetContent not found in {filename} lines {start_line}-{end_line}. "
                            f"TargetContent occurs {occ_count} times in {filename} at line ranges: {ranges_str}. "
                            f"AllowMultiple is False; specify the exact line range for the single instance you intend to modify, or set AllowMultiple=True."
                        ),
                    }
            else:
                idx = file_content.find(norm_target)
                actual_start = file_content[:idx].count("\n") + 1
                actual_end = actual_start + max(0, tc_line_count - 1)
                return {
                    "decision": "deny",
                    "reason": (
                        f"Pre-Edit Fuzzy Match Gate (Aider ACI): TargetContent not found in {filename} lines {start_line}-{end_line}. "
                        f"TargetContent actually exists at lines {actual_start}-{actual_end}. "
                        f"Update StartLine and EndLine to [{actual_start}, {actual_end}] to match disk state without re-reading."
                    ),
                }

        # TargetContent not anywhere in file; find closest match via difflib sliding window
        target_lines = norm_target.splitlines(keepends=True)
        tc_count = max(1, len(target_lines))
        target_lines_stripped = [l.strip() for l in target_lines]

        if total_lines <= tc_count:
            best_start = 1
            best_end = total_lines
            best_text = "".join(file_lines)
            sim = difflib.SequenceMatcher(None, norm_target, best_text).ratio()
            pct = int(sim * 100)
        else:
            best_sim = -1.0
            best_start = 1
            best_end = tc_count
            best_text = "".join(file_lines[:tc_count])
            for i in range(total_lines - tc_count + 1):
                cand = file_lines[i : i + tc_count]
                cand_stripped = [l.strip() for l in cand]
                sim = difflib.SequenceMatcher(None, target_lines_stripped, cand_stripped).ratio()
                if sim > best_sim:
                    best_sim = sim
                    best_start = i + 1
                    best_end = i + tc_count
                    best_text = "".join(cand)
            full_ratio = difflib.SequenceMatcher(None, norm_target, best_text).ratio()
            pct = int(max(best_sim, full_ratio) * 100)

        return {
            "decision": "deny",
            "reason": (
                f"Pre-Edit Fuzzy Match Gate (Aider ACI): TargetContent not found in {filename} lines {start_line}-{end_line}. "
                f"Closest match is at lines {best_start}-{best_end} (similarity {pct}%):\n```\n{best_text.rstrip()}\n```\n"
                "Update TargetContent/StartLine/EndLine to match disk state without re-reading."
            ),
        }

    # Case 2: StartLine / EndLine not specified
    else:
        if norm_target in file_content:
            return None

        # Check for pure indentation or whitespace drift in whole file (LOSS-01)
        target_lines = norm_target.splitlines(keepends=True)
        tc_stripped = [l.strip() for l in target_lines if l.strip()]
        if tc_stripped:
            tc_count = len(target_lines)
            matches = []
            for i in range(total_lines - tc_count + 1):
                cand = file_lines[i : i + tc_count]
                cand_stripped = [l.strip() for l in cand if l.strip()]
                if cand_stripped == tc_stripped:
                    matches.append((i + 1, i + tc_count, "".join(cand)))
            if len(matches) == 1:
                c_start, c_end, c_text = matches[0]
                return {
                    "decision": "allow",
                    "overwrite": {
                        "TargetContent": c_text,
                        "StartLine": c_start,
                        "EndLine": c_end,
                    },
                }

        target_lines = norm_target.splitlines(keepends=True)
        tc_count = max(1, len(target_lines))
        target_lines_stripped = [l.strip() for l in target_lines]

        if total_lines <= tc_count:
            best_start = 1
            best_end = total_lines
            best_text = "".join(file_lines)
            sim = difflib.SequenceMatcher(None, norm_target, best_text).ratio()
            pct = int(sim * 100)
        else:
            best_sim = -1.0
            best_start = 1
            best_end = tc_count
            best_text = "".join(file_lines[:tc_count])
            for i in range(total_lines - tc_count + 1):
                cand = file_lines[i : i + tc_count]
                cand_stripped = [l.strip() for l in cand]
                sim = difflib.SequenceMatcher(None, target_lines_stripped, cand_stripped).ratio()
                if sim > best_sim:
                    best_sim = sim
                    best_start = i + 1
                    best_end = i + tc_count
                    best_text = "".join(cand)
            full_ratio = difflib.SequenceMatcher(None, norm_target, best_text).ratio()
            pct = int(max(best_sim, full_ratio) * 100)

        return {
            "decision": "deny",
            "reason": (
                f"Pre-Edit Fuzzy Match Gate (Aider ACI): TargetContent not found in {filename}. "
                f"Closest match is at lines {best_start}-{best_end} (similarity {pct}%):\n```\n{best_text.rstrip()}\n```\n"
                "Update TargetContent/StartLine/EndLine to match disk state without re-reading."
            ),
        }


def _check_reconnaissance_precondition(target_norm: str, payload: dict) -> dict | None:
    if os.path.basename(target_norm.lower()) != "implementation_plan.md":
        return None
    if os.path.exists(target_norm):
        return None
    enforce = os.environ.get("ANTIGRAVITY_ENFORCE_RECON_GATE") == "1" or not _is_test_env()
    if not enforce:
        return None

    transcript_steps = []
    if "transcript" in payload and isinstance(payload["transcript"], list):
        transcript_steps = payload["transcript"]
    else:
        transcript_p = payload.get("transcriptPath") or payload.get("transcript_path") or ""
        conv_id = payload.get("conversationId", "")
        if not transcript_p or not os.path.isfile(transcript_p):
            if conv_id and not _is_test_env():
                for cand_path in (
                    f"~/.gemini/antigravity-cli/brain/{conv_id}/.system_generated/logs/transcript.jsonl",
                    f"~/.gemini/antigravity-ide/brain/{conv_id}/.system_generated/logs/transcript.jsonl",
                    f"~/.gemini/antigravity/brain/{conv_id}/.system_generated/logs/transcript.jsonl",
                ):
                    cand = os.path.expanduser(cand_path)
                    if os.path.isfile(cand):
                        transcript_p = cand
                        break
        if transcript_p and os.path.isfile(transcript_p):
            try:
                with open(transcript_p, "r", encoding="utf-8", errors="ignore") as f:
                    transcript_steps = [json.loads(l) for l in f if l.strip()]
            except Exception:
                pass
        elif not transcript_p and os.environ.get("ANTIGRAVITY_ENFORCE_RECON_GATE") != "1":
            return None

    if not transcript_steps:
        if os.environ.get("ANTIGRAVITY_ENFORCE_RECON_GATE") == "1" and ("transcript" in payload or payload.get("transcriptPath")):
            return {
                "decision": "deny",
                "reason": (
                    "Agentic IR Reconnaissance Pre-Condition: You must explore the codebase or ground truth "
                    "(via codegraph, read_file, rg, or context7) before authoring implementation_plan.md."
                ),
            }
        return None

    has_recon = False
    for step in transcript_steps:
        tool_calls = step.get("tool_calls") or step.get("toolCalls") or []
        if isinstance(step, dict) and step.get("type") == "call":
            tool_calls = [step]
        if not isinstance(tool_calls, list):
            tool_calls = []

        for tc in tool_calls:
            if not isinstance(tc, dict):
                continue
            name = tc.get("name") or tc.get("tool_name") or tc.get("tool") or (tc.get("function") or {}).get("name") or ""
            args = tc.get("args") or tc.get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}

            if name in ("read_file", "view_file", "list_dir", "search_web"):
                has_recon = True
                break
            if name == "call_mcp_tool":
                server = str(args.get("ServerName") or args.get("server_name") or "")
                if server.lower() in ("codegraph", "context7", "codex_knowledge"):
                    has_recon = True
                    break
            if name == "invoke_subagent":
                t_name = str(args.get("TypeName") or args.get("type_name") or "").lower()
                role = str(args.get("Role") or args.get("role") or "").lower()
                if t_name == "research" or "research" in role or "explorer" in role:
                    has_recon = True
                    break
            if name == "run_command":
                cmd = str(args.get("CommandLine") or args.get("command") or "")
                if re.search(r"\b(?:rg|fd|eza|git|bat)\b", cmd):
                    has_recon = True
                    break
        if has_recon:
            break

    if not has_recon:
        return {
            "decision": "deny",
            "reason": (
                "Agentic IR Reconnaissance Pre-Condition: You must explore the codebase or ground truth "
                "(via codegraph, read_file, rg, or context7) before authoring implementation_plan.md."
            ),
        }
    return None


def _check_builder_suppression_injection(target_norm: str, args: dict) -> dict | None:
    chunks = args.get("ReplacementChunks") or args.get("edits")
    if isinstance(chunks, list) and chunks:
        tot_target_supp = 0
        tot_repl_supp = 0
        for chunk in chunks:
            if isinstance(chunk, dict):
                c_tgt = chunk.get("TargetContent") or chunk.get("Target") or chunk.get("target_string") or chunk.get("old_string") or ""
                c_repl = chunk.get("ReplacementContent") or chunk.get("Replacement") or chunk.get("replacement_string") or chunk.get("new_string") or ""
                tot_target_supp += len(_SUPPRESSION_RE.findall(c_tgt))
                tot_repl_supp += len(_SUPPRESSION_RE.findall(c_repl))
        if tot_repl_supp > tot_target_supp:
            return {
                "decision": "deny",
                "reason": (
                    f"Specification-Gaming Lock: Injecting linter/type-checker suppressions "
                    f"(@ts-ignore, type: ignore, eslint-disable) is forbidden in `{os.path.basename(target_norm)}`."
                ),
            }

    is_append = bool(args.get("Append", False))
    if is_append:
        append_content = args.get("CodeContent") or args.get("Content") or ""
        if _SUPPRESSION_RE.search(append_content):
            return {
                "decision": "deny",
                "reason": (
                    f"Specification-Gaming Lock: Injecting linter/type-checker suppressions "
                    f"(@ts-ignore, type: ignore, eslint-disable) is forbidden in `{os.path.basename(target_norm)}`."
                ),
            }

    target_content = args.get("TargetContent") or args.get("Target") or args.get("target_string") or ""
    repl_content = args.get("ReplacementContent") or args.get("Replacement") or args.get("replacement_string") or ""
    is_overwrite = bool(args.get("Overwrite", True)) if "Overwrite" in args else False

    if target_content:
        t_supp = len(_SUPPRESSION_RE.findall(target_content))
        r_supp = len(_SUPPRESSION_RE.findall(repl_content))
        if r_supp > t_supp:
            return {
                "decision": "deny",
                "reason": (
                    f"Specification-Gaming Lock: Injecting linter/type-checker suppressions "
                    f"(@ts-ignore, type: ignore, eslint-disable) is forbidden in `{os.path.basename(target_norm)}`."
                ),
            }
    elif is_overwrite and not is_append:
        new_content = args.get("CodeContent") or args.get("Content") or ""
        try:
            with open(target_norm, "r", encoding="utf-8", errors="ignore") as f:
                d_content = f.read()
            d_supp = len(_SUPPRESSION_RE.findall(d_content))
            n_supp = len(_SUPPRESSION_RE.findall(new_content))
            if n_supp > d_supp:
                return {
                    "decision": "deny",
                    "reason": (
                        f"Specification-Gaming Lock: Injecting linter/type-checker suppressions "
                        f"(@ts-ignore, type: ignore, eslint-disable) is forbidden in `{os.path.basename(target_norm)}`."
                    ),
                }
        except Exception:
            pass
    return None


_LITERAL_VAL_PAT = r"(?:'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|\b(?:True|False|true|false|None|null)\b|-?\d+(?:\.\d+)?)"
_ASSERT_EQ_RE = re.compile(rf"^\s*assert\s+(.+?)\s*==\s*({_LITERAL_VAL_PAT})\s*(?:,.*)?$", re.MULTILINE)
_SELF_ASSERT_EQ_RE = re.compile(rf"^\s*self\.assertEqual\s*\(\s*(.+?)\s*,\s*({_LITERAL_VAL_PAT})\s*(?:,.*)?\)\s*$", re.MULTILINE)
_EXPECT_BE_RE = re.compile(rf"^\s*expect\s*\(\s*(.+?)\s*\)\.(?:toBe|toEqual)\s*\(\s*({_LITERAL_VAL_PAT})\s*\)\s*;?$", re.MULTILINE)


def _extract_literal_assertions(text: str) -> list[tuple[str, str]]:
    """Extracts (lhs, rhs_literal) pairs from simple assertions."""
    pairs: list[tuple[str, str]] = []
    for line in text.splitlines():
        m = _ASSERT_EQ_RE.search(line) or _SELF_ASSERT_EQ_RE.search(line) or _EXPECT_BE_RE.search(line)
        if m:
            lhs = m.group(1).strip()
            lit = m.group(2).strip()
            pairs.append((lhs, lit))
    return pairs


def _has_oracle_custody_lease(payload: dict, workspace: str) -> bool:
    """Returns True if the session holds an Oracle-Custody-Lease for updating test assertions."""
    if os.environ.get("ORACLE_CUSTODY_LEASE") == "1":
        return True

    lease_marker = "Oracle-Custody-Lease: UPDATE_ASSERTIONS"

    # Check first transcript step
    first_step = _get_first_transcript_step(payload)
    if first_step:
        content = ""
        if isinstance(first_step, dict):
            content = str(first_step.get("content", ""))
        elif isinstance(first_step, str):
            content = first_step
        if lease_marker in content:
            return True

    # Check active implementation_plan.md
    plan_candidates = []
    art_dir = payload.get("artifactDirectoryPath")
    if art_dir:
        plan_candidates.append(os.path.join(art_dir, "implementation_plan.md"))

    conv_id = payload.get("conversationId", "")
    if conv_id:
        for root in (
            "~/.gemini/antigravity-cli/brain",
            "~/.gemini/antigravity-ide/brain",
            "~/.gemini/antigravity/brain",
        ):
            plan_candidates.append(os.path.expanduser(f"{root}/{conv_id}/implementation_plan.md"))

    if workspace:
        plan_candidates.append(os.path.join(workspace, "implementation_plan.md"))
        plan_candidates.append(os.path.join(workspace, ".gemini", "antigravity", "implementation_plan.md"))

    for cand in plan_candidates:
        if cand and os.path.isfile(cand):
            try:
                with open(cand, "r", encoding="utf-8", errors="ignore") as f:
                    plan_text = f.read()
                if lease_marker in plan_text:
                    return True
            except Exception:
                pass

    return False


def _check_semantic_assertion_drift(target_text: str, repl_text: str) -> str | None:
    """Inspects existing assertion lines in target_text vs repl_text for semantic drift or tampering."""
    if not target_text or not repl_text:
        return None

    assert_pat = re.compile(r"^\s*(?:assert\b|expect\s*\(|self\.assert)", re.MULTILINE)
    target_asserts = len(assert_pat.findall(target_text))
    repl_asserts = len(assert_pat.findall(repl_text))
    if target_asserts == 0 or repl_asserts < target_asserts:
        return None

    # Check A (Operator Weakening)
    strict_pat = re.compile(r"(?:==|\.assertEqual\s*\(|\.toBe\s*\(|\.toEqual\s*\()")
    weak_pat = re.compile(r"(?:\bis\s+not\s+None\b|\.assertIsNotNone\s*\(|\.toBeDefined\s*\(|\.toBeTruthy\s*\()")
    target_strict = len(strict_pat.findall(target_text))
    repl_strict = len(strict_pat.findall(repl_text))
    target_weak = len(weak_pat.findall(target_text))
    repl_weak = len(weak_pat.findall(repl_text))

    if target_strict > 0 and repl_strict < target_strict and repl_weak > target_weak:
        return (
            "Semantic Oracle Custody Lock: Weakening strict equality assertions (== / toEqual / assertEqual) "
            "into loose existence checks (is not None / toBeDefined) is forbidden without an Oracle-Custody-Lease."
        )

    # Check B (Expected Literal Tampering)
    target_pairs = _extract_literal_assertions(target_text)
    repl_pairs = _extract_literal_assertions(repl_text)
    if target_pairs and repl_pairs:
        target_dict = dict(target_pairs)
        repl_dict = dict(repl_pairs)
        for lhs, target_lit in target_dict.items():
            if lhs in repl_dict and repl_dict[lhs] != target_lit:
                return (
                    "Semantic Oracle Custody Lock: Mutating expected assertion literal values "
                    "to match altered code output is forbidden without 'Oracle-Custody-Lease: UPDATE_ASSERTIONS'."
                )

    return None


def _handle_file_mutation(tool_name: str, args: dict, payload: dict) -> dict:
    target_file = (
        args.get("TargetFile")
        or args.get("Path")
        or args.get("path")
        or args.get("file")
        or args.get("target_file")
        or ""
    )
    if not target_file:
        return {"decision": "allow"}

    workspace = ""
    ws_paths = payload.get("workspacePaths", [])
    if ws_paths and isinstance(ws_paths, list):
        workspace = ws_paths[0]
    if not workspace:
        workspace = os.getcwd()

    target_norm = _normalize(target_file, workspace)
    target_norm_low = target_norm.lower()

    role_label = _extract_session_role(payload)

    # Hook Immunity Guard
    if "/.gemini/config/hooks/" in target_norm_low and role_label in ("meta-invariant-editor", "meta-domain-editor", "debugger", "dev-fe"):
        return {
            "decision": "deny",
            "reason": (
                f"Hook Immunity Invariant: Role '{role_label}' is strictly prohibited from mutating "
                f"core system hooks in `/.gemini/config/hooks/` (`{os.path.basename(target_norm)}`). "
                "Core hook modifications are reserved for authorized system updates."
            ),
        }

    # Builder Specification-Gaming Lock: suppression injection in existing code/test files
    if os.path.isfile(target_norm) and role_label in ("dev-fe", "dev-be"):
        if not ("/brain/" in target_norm_low or target_norm_low.endswith((".md", ".txt"))):
            supp_deny = _check_builder_suppression_injection(target_norm, args)
            if supp_deny:
                return supp_deny

    # Debugger & Builder Test-Assertion Lock
    if os.path.isfile(target_norm) and _is_test_file_path(target_norm):
        if role_label == "debugger" or os.environ.get("FIX_CODE_ONLY") == "1":
            effective_role = role_label if role_label else "debugger"
            return {
                "decision": "deny",
                "reason": (
                    f"Fix-The-Code-Not-The-Test Invariant: Role '{effective_role}' is forbidden from mutating "
                    f"existing test file `{os.path.basename(target_norm)}`. Fix the application code, not the test assertions."
                ),
            }
        elif role_label in ("dev-fe", "dev-be"):
            has_lease = _has_oracle_custody_lease(payload, workspace)
            # Builder Test-Immutability Lock: cannot delete existing assert/expect lines
            target_content = args.get("TargetContent") or args.get("Target") or args.get("target_string") or ""
            repl_content = args.get("ReplacementContent") or args.get("Replacement") or args.get("replacement_string") or ""
            is_overwrite = bool(args.get("Overwrite", True)) if "Overwrite" in args else False
            is_append = bool(args.get("Append", False))

            assert_pat = re.compile(r"^\s*(?:assert\b|expect\s*\(|self\.assert)", re.MULTILINE)

            if is_append:
                append_content = args.get("CodeContent") or args.get("Content") or ""
                if _ZERO_EXIT_RE.search(append_content):
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Test-Immutability Lock (CATCH Execution Interference): Injecting early zero-exit calls (sys.exit(0) / process.exit(0)) "
                            f"to spoof test passes is forbidden in `{os.path.basename(target_norm)}`."
                        ),
                    }
                if _TEST_SKIP_RE.search(append_content):
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Test-Immutability Lock: Adding .skip / @pytest.mark.skip to bypass failing tests is forbidden in `{os.path.basename(target_norm)}`."
                        ),
                    }

            if target_content:
                if not has_lease:
                    target_asserts = len(assert_pat.findall(target_content))
                    repl_asserts = len(assert_pat.findall(repl_content))
                    if repl_asserts < target_asserts:
                        return {
                            "decision": "deny",
                            "reason": (
                                f"Fix-The-Code-Not-The-Test Invariant: Role '{role_label}' is forbidden from deleting "
                                f"or weakening existing assert/expect lines in `{os.path.basename(target_norm)}`. "
                                "Net-new test additions are allowed, but existing assertions are immutable."
                            ),
                        }
                    drift_reason = _check_semantic_assertion_drift(target_content, repl_content)
                    if drift_reason:
                        return {
                            "decision": "deny",
                            "reason": drift_reason,
                        }
                target_skips = len(_TEST_SKIP_RE.findall(target_content))
                repl_skips = len(_TEST_SKIP_RE.findall(repl_content))
                if repl_skips > target_skips:
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Test-Immutability Lock: Adding .skip / @pytest.mark.skip to bypass failing tests is forbidden in `{os.path.basename(target_norm)}`."
                        ),
                    }
                target_taut = len(_TAUTOLOGICAL_ASSERT_RE.findall(target_content))
                repl_taut = len(_TAUTOLOGICAL_ASSERT_RE.findall(repl_content))
                if repl_taut > target_taut:
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Test-Immutability Lock: Tautological assertions (assert True / expect(true).toBe(true)) are forbidden in `{os.path.basename(target_norm)}`."
                        ),
                    }
                target_zero = len(_ZERO_EXIT_RE.findall(target_content))
                repl_zero = len(_ZERO_EXIT_RE.findall(repl_content))
                if repl_zero > target_zero:
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Test-Immutability Lock (CATCH Execution Interference): Injecting early zero-exit calls (sys.exit(0) / process.exit(0)) "
                            f"to spoof test passes is forbidden in `{os.path.basename(target_norm)}`."
                        ),
                    }
            elif is_overwrite and not is_append:
                new_content = args.get("CodeContent") or args.get("Content") or ""
                try:
                    with open(target_norm, "r", encoding="utf-8", errors="ignore") as f:
                        disk_content = f.read()
                    if not has_lease:
                        disk_asserts = len(assert_pat.findall(disk_content))
                        new_asserts = len(assert_pat.findall(new_content))
                        if new_asserts < disk_asserts:
                            return {
                                "decision": "deny",
                                "reason": (
                                    f"Fix-The-Code-Not-The-Test Invariant: Role '{role_label}' is forbidden from deleting "
                                    f"or weakening existing assert/expect lines in `{os.path.basename(target_norm)}`. "
                                    "Net-new test additions are allowed, but existing assertions are immutable."
                                ),
                            }
                        drift_reason = _check_semantic_assertion_drift(disk_content, new_content)
                        if drift_reason:
                            return {
                                "decision": "deny",
                                "reason": drift_reason,
                            }
                    disk_skips = len(_TEST_SKIP_RE.findall(disk_content))
                    new_skips = len(_TEST_SKIP_RE.findall(new_content))
                    if new_skips > disk_skips:
                        return {
                            "decision": "deny",
                            "reason": (
                                f"Test-Immutability Lock: Adding .skip / @pytest.mark.skip to bypass failing tests is forbidden in `{os.path.basename(target_norm)}`."
                            ),
                        }
                    disk_taut = len(_TAUTOLOGICAL_ASSERT_RE.findall(disk_content))
                    new_taut = len(_TAUTOLOGICAL_ASSERT_RE.findall(new_content))
                    if new_taut > disk_taut:
                        return {
                            "decision": "deny",
                            "reason": (
                                f"Test-Immutability Lock: Tautological assertions (assert True / expect(true).toBe(true)) are forbidden in `{os.path.basename(target_norm)}`."
                            ),
                        }
                    disk_zero = len(_ZERO_EXIT_RE.findall(disk_content))
                    new_zero = len(_ZERO_EXIT_RE.findall(new_content))
                    if new_zero > disk_zero:
                        return {
                            "decision": "deny",
                            "reason": (
                                f"Test-Immutability Lock (CATCH Execution Interference): Injecting early zero-exit calls (sys.exit(0) / process.exit(0)) "
                                f"to spoof test passes is forbidden in `{os.path.basename(target_norm)}`."
                            ),
                        }
                except Exception:
                    pass

    # Agentic IR Reconnaissance Pre-Condition on implementation_plan.md
    if os.path.basename(target_norm_low) == "implementation_plan.md":
        recon_deny = _check_reconnaissance_precondition(target_norm, payload)
        if recon_deny:
            return recon_deny

    # 1. Non-code planning, documentation, or artifact paths are always allowed
    if "/brain/" in target_norm_low or target_norm_low.endswith((".md", ".txt")):
        return {"decision": "allow"}

    # 2. Check if target_file is an application source/code file outside /.gemini/ and /tmp/
    ws_low = (workspace or "").lower()
    in_temp = "/tmp/" in target_norm_low or target_norm_low.startswith(("/tmp/", tempfile.gettempdir().lower()))
    is_ws_in_temp = bool(ws_low and ("/tmp/" in ws_low or ws_low.startswith(("/tmp/", tempfile.gettempdir().lower()))))

    is_app_code = (
        target_norm_low.endswith(APPLICATION_CODE_EXTENSIONS)
        and "/.gemini/" not in target_norm_low
        and (not in_temp or is_ws_in_temp)
    )

    allowed_files: list[str] = []
    if is_app_code:
        # 3. Inspect session archetype
        first_step = _get_first_transcript_step(payload)
        is_non_builder, role_label = _detect_non_builder_session(payload)

        # Case 1 & Case 2 — Non-Builder Sessions (Root Orchestrator or Non-Builder Subagents)
        if is_non_builder:
            if role_label == "Root Orchestrator (PM)":
                return {
                    "decision": "deny",
                    "reason": (
                        f"PM / Orchestrator Zero-Code-Write Invariant (pm-no-implementation.md): "
                        f"Root Orchestrator (PM) must NEVER directly mutate application source code (`{os.path.basename(target_norm)}`). "
                        "Delegate code changes to a specialist builder subagent (`Role: 'dev-fe' | 'dev-be' | 'debugger'`) via `invoke_subagent`."
                    ),
                }
            else:
                return {
                    "decision": "deny",
                    "reason": (
                        f"Role Isolation Invariant (BMAD / pm-no-implementation.md): "
                        f"Non-builder subagent role (`{role_label}`) is strictly prohibited from mutating application source code (`{os.path.basename(target_norm)}`). "
                        "Route code modifications back to the Orchestrator to dispatch a Builder subagent (`dev-fe` / `dev-be` / `debugger`)."
                    ),
                }

        # Case 3 — Builder Subagents: Check Per-Shard Mechanical Lease (Advisory 2 / Collision 6)
        if first_step and first_step.get("type") == "SYSTEM_MESSAGE":
            content = str(first_step.get("content", ""))
            has_allowed_files, allowed_files = _extract_allowed_files(content)
            if has_allowed_files:
                matched = any(_matches_allowed_file(target_norm, pat, workspace) for pat in allowed_files)
                if not matched:
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Story Shard File Lease Violation (BMAD): Target file is outside the subagent's leased allowed_files "
                            f"(`{os.path.basename(target_norm)}` not in {allowed_files}). "
                            "Escalate to Orchestrator to expand shard file leases before touching unleased files."
                        ),
                    }

    # 4. Aider-Style Pre-Edit TargetContent Verification + difflib Fuzzy Line Hints
    effective_args = args
    fuzzy_overwrite_payload = None
    if tool_name == "replace_file_content":
        fuzzy_res = _verify_target_content_fuzzy(target_norm, args)
        if fuzzy_res:
            if fuzzy_res.get("decision") == "deny":
                return fuzzy_res
            if fuzzy_res.get("decision") == "allow" and "overwrite" in fuzzy_res:
                fuzzy_overwrite_payload = fuzzy_res
                effective_args = dict(args)
                effective_args.update(fuzzy_res["overwrite"])

    # 5. SWE-agent Pre-Write In-Memory AST & Syntax Gate
    simulated = _simulate_file_mutation(tool_name, effective_args, target_norm)
    if simulated is not None:
        syntax_deny = _validate_simulated_syntax(target_norm, simulated)
        if syntax_deny:
            return syntax_deny

    # 6. Shift-Left Pre-Edit AST Import Verification (Upgrade 5)
    if is_app_code:
        _maybe_create_shadow_git_checkpoint(workspace, payload.get("conversationId") or "")
        import_deny = _verify_imports_shift_left(target_norm, tool_name, effective_args, payload, workspace, allowed_files)
        if import_deny:
            return import_deny

    if fuzzy_overwrite_payload:
        return fuzzy_overwrite_payload

    return {"decision": "allow"}


def _maybe_create_shadow_git_checkpoint(workspace: str, conv_id: str) -> None:
    if not conv_id:
        return
    ckpt_path = os.path.join(tempfile.gettempdir(), f".antigravity_shadow_ckpt_{conv_id}.json")
    if os.path.isfile(ckpt_path):
        return
    if _is_test_env() and not os.environ.get("ANTIGRAVITY_TEST_SHADOW_CKPT"):
        return
    try:
        ws = workspace or os.getcwd()
        res = subprocess.run(
            ["git", "-C", ws, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=1.0, check=False,
        )
        if res.returncode != 0 or res.stdout.strip() != "true":
            return
        head_res = subprocess.run(
            ["git", "-C", ws, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=1.0, check=False,
        )
        head_sha = head_res.stdout.strip() if head_res.returncode == 0 else ""
        stash_res = subprocess.run(
            ["git", "-C", ws, "stash", "create"],
            capture_output=True, text=True, timeout=1.5, check=False,
        )
        stash_sha = stash_res.stdout.strip() if stash_res.returncode == 0 else ""
        data = {
            "conv_id": conv_id,
            "timestamp": time.time(),
            "workspace": ws,
            "head_sha": head_sha,
            "stash_sha": stash_sha,
        }
        _atomic_json_write(ckpt_path, data)
    except Exception:
        pass


def _normalize_error_signature(text: str) -> str:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return ""
    last_lines = lines[-5:]
    cleaned = []
    for l in last_lines:
        l = re.sub(r"\b\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?\b", "", l)
        l = re.sub(r"\b0x[0-9a-fA-F]+\b", "0x...", l)
        l = re.sub(r"\b(?:pid|PID|process)\s*[:=]?\s*\d+\b", "", l)
        cleaned.append(l.strip())
    norm_text = "\n".join(cleaned)
    return hashlib.sha256(norm_text.encode("utf-8")).hexdigest()


def _check_error_stagnation_circuit_breaker(payload: dict, tool_name: str, args: dict) -> dict | None:
    if tool_name != "run_command":
        return None
    conv_id = payload.get("conversationId") or ""
    if not conv_id:
        return None

    ledger_path = os.path.join(tempfile.gettempdir(), f".antigravity_err_sig_{conv_id}.json")
    ledger = _atomic_json_read(ledger_path, default={})
    signatures = ledger.get("signatures", [])

    if len(signatures) >= 3:
        last3 = signatures[-3:]
        if last3[0] and last3[0] == last3[1] == last3[2]:
            last_err = (
                ledger.get("last_error")
                or ledger.get("error_text")
                or (ledger.get("raw_errors", [])[-1] if ledger.get("raw_errors") else "")
                or str(last3[0])
            )
            reason = (
                "Error-Stagnation Circuit Breaker: The last 3 command executions failed with the identical error signature. "
                "Stop blind trial-and-error and inspect the root cause or symbols first."
            )
            epistemic = _detect_epistemic_uncertainty_error(str(last_err))
            if epistemic:
                reason += (
                    " AdaSearch Epistemic Uncertainty Trigger: Query authoritative library docs via "
                    "call_mcp_tool(ServerName='context7', ToolName='resolve-library-id') -> query-docs before retrying."
                )
            return {
                "decision": "deny",
                "reason": reason,
            }

    transcript_p = payload.get("transcriptPath", "")
    if transcript_p and os.path.isfile(transcript_p):
        try:
            file_size = os.path.getsize(transcript_p)
            read_size = min(file_size, 256 * 1024)
            with open(transcript_p, "rb") as f:
                if file_size > read_size:
                    f.seek(file_size - read_size)
                    tail_bytes = f.read(read_size)
                    first_nl = tail_bytes.find(b"\n")
                    if first_nl != -1:
                        tail_bytes = tail_bytes[first_nl + 1:]
                else:
                    tail_bytes = f.read(read_size)
            text = tail_bytes.decode("utf-8", errors="ignore")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            err_sigs = []
            raw_errs = []
            for line in lines[-25:]:
                try:
                    step = json.loads(line)
                except Exception:
                    continue
                content = step.get("content") or ""
                if isinstance(content, str) and (
                    re.search(r"\b(?:Command (?:failed|exited) with (?:exit )?code [1-9]|Exit code:?\s*[1-9]|FAILED\s*\(failures=)", content)
                ):
                    sig = _normalize_error_signature(content)
                    if sig:
                        err_sigs.append(sig)
                        raw_errs.append(content)
                elif isinstance(content, str) and "Command exited with code 0" in content:
                    err_sigs.clear()
                    raw_errs.clear()

            if len(err_sigs) >= 3 and err_sigs[-1] == err_sigs[-2] == err_sigs[-3]:
                reason = (
                    "Error-Stagnation Circuit Breaker: The last 3 command executions failed with the identical error signature. "
                    "Stop blind trial-and-error and inspect the root cause or symbols first."
                )
                epistemic = _detect_epistemic_uncertainty_error(raw_errs[-1] if raw_errs else "")
                if epistemic:
                    reason += (
                        " AdaSearch Epistemic Uncertainty Trigger: Query authoritative library docs via "
                        "call_mcp_tool(ServerName='context7', ToolName='resolve-library-id') -> query-docs before retrying."
                    )
                return {
                    "decision": "deny",
                    "reason": reason,
                }
        except Exception:
            pass
    return None


def _handle_send_message(args: dict, payload: dict) -> dict:
    recipient = str(args.get("Recipient") or args.get("recipient") or "").strip()
    msg = str(args.get("Message") or args.get("message") or "").strip()
    conv_id = payload.get("conversationId") or "default"

    if not recipient or not msg:
        return {"decision": "allow"}

    if len(msg) > 6000:
        return {
            "decision": "deny",
            "reason": (
                f"Pub/Sub Sparsification Invariant: Message length ({len(msg)} chars) "
                "exceeds 6,000-character ceiling. Write detailed reports or tables to an artifact/scratch file "
                "and send a compact summary (< 6,000 chars) instead."
            ),
        }

    now = time.time()
    msg_hash = hashlib.sha256(msg.encode("utf-8")).hexdigest()
    is_poll = len(msg) < 80 and bool(re.search(r"(?i)^(?:please\s+)?(?:return|report)\s+(?:your\s+)?(?:status|findings|summary)\b", msg))

    ledger_path = os.path.join(tempfile.gettempdir(), f".antigravity_msg_ledger_{conv_id}.json")
    ledger = _atomic_json_read(ledger_path, default=[])
    if not isinstance(ledger, list):
        ledger = []

    prior_actions = _get_prior_actions(payload)
    consecutive_in_actions = (
        len(prior_actions) >= 3
        and all(
            isinstance(e, dict)
            and e.get("tool") == "send_message"
            and str((e.get("args") or {}).get("Recipient") or (e.get("args") or {}).get("recipient") or "").strip() == recipient
            for e in prior_actions[-3:]
        )
    )
    consecutive_in_ledger = (
        not prior_actions
        and len(ledger) >= 3
        and all(isinstance(e, dict) and e.get("recipient") == recipient for e in ledger[-3:])
    )
    if consecutive_in_actions or consecutive_in_ledger:
        return {
            "decision": "deny",
            "reason": (
                f"Subagent Ping-Pong Cap ACTIVATED: 4 consecutive `send_message` calls to `{recipient}` detected "
                "without intermediate parent synthesis or tool work. Consolidate your questions or synthesize findings "
                "directly instead of ping-ponging."
            ),
        }

    for entry in reversed(ledger):
        if not isinstance(entry, dict):
            continue
        if entry.get("recipient") == recipient:
            entry_time = float(entry.get("time", 0.0))
            if (now - entry_time) < 30.0:
                if entry.get("hash") == msg_hash or (is_poll and entry.get("is_poll")):
                    return {
                        "decision": "deny",
                        "reason": (
                            "Reactive Wakeup Guard: Subagent is already processing your previous message. "
                            "Do not poll or double-send; yield your turn (call no more tools) and wait for reactive wakeup."
                        ),
                    }
            break

    ledger.append({
        "recipient": recipient,
        "hash": msg_hash,
        "time": now,
        "is_poll": is_poll,
    })
    _atomic_json_write(ledger_path, ledger[-20:])
    return {"decision": "allow"}


_COSMETIC_JEV_KEYS = frozenset({
    "toolsummary",
    "toolaction",
    "waitmsbeforeasync",
    "description",
    "instruction",
})


def _canonical_jev_args(args: dict) -> str:
    if not isinstance(args, dict):
        return ""
    filtered = {
        k: (" ".join(v.split()) if str(k).lower() == "commandline" and isinstance(v, str) else v)
        for k, v in args.items()
        if str(k).lower() not in _COSMETIC_JEV_KEYS
    }
    return json.dumps(filtered, sort_keys=True)


_LAST_TRACKED_PAYLOAD_STATE: tuple[int, list[dict]] | None = None


def _seed_actions_from_transcript(payload: dict) -> list[dict]:
    transcript_p = payload.get("transcriptPath", "") if isinstance(payload, dict) else ""
    if not transcript_p or not isinstance(transcript_p, str) or not os.path.isfile(transcript_p):
        return []
    seeded: list[dict] = []
    try:
        file_size = os.path.getsize(transcript_p)
        read_size = min(file_size, 64 * 1024)
        with open(transcript_p, "rb") as f:
            if file_size > read_size:
                f.seek(file_size - read_size)
                tail_bytes = f.read(read_size)
                first_nl = tail_bytes.find(b"\n")
                if first_nl != -1:
                    tail_bytes = tail_bytes[first_nl + 1:]
            else:
                tail_bytes = f.read(read_size)
        text = tail_bytes.decode("utf-8", errors="ignore")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()][-40:]
        last_step_count = 0
        for line in lines:
            try:
                step = json.loads(line)
            except Exception:
                continue
            if not isinstance(step, dict):
                continue
            if (
                step.get("type") == "USER_INPUT"
                and step.get("source") == "USER_EXPLICIT"
                and "<SYSTEM_MESSAGE>" not in str(step.get("content", ""))
            ):
                seeded.clear()
                last_step_count = 0
                continue
            if step.get("type") == "ERROR_MESSAGE" and last_step_count > 0:
                del seeded[-last_step_count:]
                last_step_count = 0
                continue
            tool_calls = step.get("tool_calls")
            last_step_count = 0
            if isinstance(tool_calls, list):
                for tc in tool_calls:
                    if not isinstance(tc, dict):
                        continue
                    fn_block = tc.get("function") if isinstance(tc.get("function"), dict) else {}
                    tc_name = tc.get("name") or fn_block.get("name")
                    if not tc_name or not isinstance(tc_name, str) or tc_name in ("view_file", "read_file"):
                        continue
                    tc_args = tc.get("args") if "args" in tc else fn_block.get("args")
                    if isinstance(tc_args, str):
                        try:
                            tc_args = json.loads(tc_args)
                        except Exception:
                            tc_args = {}
                    if not isinstance(tc_args, dict):
                        tc_args = {}
                    seeded.append({"tool": tc_name, "args": tc_args})
                    last_step_count += 1
    except Exception:
        return []
    return seeded[-16:]


def _get_prior_actions(payload: dict) -> list[dict]:
    if _LAST_TRACKED_PAYLOAD_STATE is not None and _LAST_TRACKED_PAYLOAD_STATE[0] == id(payload):
        return list(_LAST_TRACKED_PAYLOAD_STATE[1])
    conv_id = (payload.get("conversationId") if isinstance(payload, dict) else None) or f"pid_{os.getppid()}"
    from pathlib import Path
    state_file = Path(tempfile.gettempdir()) / f".antigravity_actions_{conv_id}.json"
    if state_file.is_file():
        try:
            actions = json.loads(state_file.read_text(encoding="utf-8"))
            if isinstance(actions, list):
                return actions[-16:]
        except Exception:
            pass
    return _seed_actions_from_transcript(payload)


_PRODUCER_COMMAND_RE = re.compile(
    r"^(?:(?:env\s+|[A-Za-z_][A-Za-z0-9_]*=\S+\s+|timeout\s+\S+\s+)*)"
    r"(?:dexdump|adb\s+(?:-[^\s]+\s+)*(?:logcat|shell|exec-out)|aapt2?|strings|unzip\s+-p|gh\s+api)\b"
)
_TRAILING_FILTER_STAGE_RE = re.compile(
    r"^(?:rg|grep|egrep|fgrep|sed|sd|awk|head|tail|cut)\b"
)


def _extract_command_skeleton(cmd: str) -> str:
    if not isinstance(cmd, str):
        return ""
    clean = " ".join(cmd.strip().split())
    if not clean:
        return ""

    first_stage = clean.split("|", 1)[0].strip()

    if re.match(r"^bat\b", first_stage) and re.search(r"(?:^|\s)(?:-r|--line-range)(?:=|\s+)\d*:\d*", first_stage):
        try:
            tokens = shlex.split(first_stage)
        except Exception:
            tokens = first_stage.split()
        target_path = ""
        skip_next = False
        for tok in tokens[1:]:
            if skip_next:
                skip_next = False
                continue
            if tok in ("-r", "--line-range", "--style", "--theme", "--pager", "--paging", "--language", "-l"):
                skip_next = True
                continue
            if tok.startswith("-") or re.match(r"^\d*:\d*$", tok):
                continue
            target_path = tok
        if target_path:
            return f"shell_slice:{os.path.normpath(target_path.strip(chr(34) + chr(39)))}"

    m_sed = re.match(
        r"""^sed\s+(?:-[a-zA-Z]*n[a-zA-Z]*\s+)+['"]?\d+\s*,\s*\d+\s*p(?:;\s*\d+\s*q)?['"]?\s+(['"]?[^'"\s|;&]+['"]?)""",
        first_stage,
    )
    if m_sed:
        target_path = m_sed.group(1).strip("'\"")
        if target_path:
            return f"shell_slice:{os.path.normpath(target_path)}"

    if re.search(r"\bpython3?\s+-c\b", clean) and "zipfile.ZipFile" in clean:
        m_zf = re.search(r"""zipfile\.ZipFile\(\s*r?\\?['"]([^'"\\]+)\\?['"]""", clean)
        if m_zf:
            return f"python3_zipfile:{os.path.normpath(m_zf.group(1).strip())}"
        m_ext = re.search(r"""['"]([^'"\\]+\.(?:apk|zip|jar|aab|whl))['"]""", clean)
        if m_ext:
            return f"python3_zipfile:{os.path.normpath(m_ext.group(1).strip())}"

    if "|" in clean:
        producer, rest = clean.split("|", 1)
        producer = producer.strip()
        rest = rest.strip()
        if _PRODUCER_COMMAND_RE.search(producer) and _TRAILING_FILTER_STAGE_RE.match(rest):
            return producer

    return clean


def _track_and_check_loop_with_jev(payload: dict, tool_name: str, args: dict) -> dict | None:
    global _LAST_TRACKED_PAYLOAD_STATE
    try:
        from pathlib import Path
        conv_id = payload.get("conversationId") or f"pid_{os.getppid()}"
        state_file = Path(tempfile.gettempdir()) / f".antigravity_actions_{conv_id}.json"
        actions: list[dict] = []
        if state_file.is_file():
            try:
                actions = json.loads(state_file.read_text(encoding="utf-8"))[-16:]
            except Exception:
                actions = []
        else:
            actions = _seed_actions_from_transcript(payload)[-16:]

        _LAST_TRACKED_PAYLOAD_STATE = (id(payload), list(actions))

        current_action = {"tool": tool_name, "args": args}
        actions.append(current_action)

        try:
            state_file.write_text(json.dumps(actions[-16:]), encoding="utf-8")
        except Exception:
            pass

        if tool_name == "run_command" and isinstance(args, dict):
            cur_cmd = str(args.get("CommandLine") or args.get("cmd") or "")
            cur_skel = _extract_command_skeleton(cur_cmd)
            if cur_skel.startswith("shell_slice:"):
                slice_count = sum(
                    1
                    for a in actions
                    if isinstance(a, dict)
                    and a.get("tool") == "run_command"
                    and _extract_command_skeleton(
                        str((a.get("args") or {}).get("CommandLine") or (a.get("args") or {}).get("cmd") or "")
                    ) == cur_skel
                )
                if slice_count >= 3:
                    target_path = cur_skel.split("shell_slice:", 1)[1]
                    return {
                        "decision": "deny",
                        "reason": (
                            f"Slice Loop Breaker ACTIVATED: `{target_path}` has been sliced {slice_count} times via shell range commands (`bat -r` / `sed -n`). "
                            "Sequential shell slicing is blocked to prevent token waste. "
                            "Use `codegraph:extract_symbols` or `codegraph:batch_query` instead."
                        ),
                    }

        # 1-Step Contiguous Triple Check (len(actions) >= 3)
        if len(actions) >= 3:
            last_3 = actions[-3:]
            sigs3 = [(a.get("tool"), _canonical_jev_args(a.get("args", {}))) for a in last_3]
            if sigs3[0] == sigs3[1] == sigs3[2]:
                return {
                    "decision": "deny",
                    "reason": (
                        "Jev Loop Circuit Breaker ACTIVATED (engine: deterministic_circuit_breaker, confidence: 0.95): "
                        f"Repetitive execution of `{tool_name}` detected with identical arguments. "
                        "Action cycling without progress is strictly prohibited. Enforce the 3-Turn Debug Spiral Hard Stop."
                    ),
                }

        # Semantic Command-Skeleton Loop Breaker (4 consecutive run_command calls with identical skeleton)
        if len(actions) >= 4:
            last_4 = actions[-4:]
            if all(isinstance(a, dict) and a.get("tool") == "run_command" for a in last_4):
                skels4 = [
                    _extract_command_skeleton(
                        str((a.get("args") or {}).get("CommandLine") or (a.get("args") or {}).get("cmd") or "")
                    )
                    for a in last_4
                ]
                if skels4[0] and skels4[0] == skels4[1] == skels4[2] == skels4[3]:
                    return {
                        "decision": "deny",
                        "reason": (
                            "Jev Loop Circuit Breaker ACTIVATED (engine: semantic_command_skeleton, confidence: 0.95): "
                            f"4 consecutive `run_command` executions share the identical command skeleton (`{skels4[0]}`). "
                            "Stop repetitive pipe/filter probing; batch your queries into a single expression "
                            "or write the command output to a scratch file once and inspect it directly."
                        ),
                    }

        # 2-Step Alternating Cycle Check (len(actions) >= 6)
        if len(actions) >= 6:
            last_6 = actions[-6:]
            has_mgmt_peer = any(
                isinstance(a, dict) and a.get("tool") in ("manage_subagents", "manage_task")
                for a in last_6
            )
            sigs = [
                (
                    ("schedule", "poll_timer")
                    if isinstance(a, dict)
                    and a.get("tool") == "schedule"
                    and (has_mgmt_peer or not (a.get("args") or {}).get("CronExpression"))
                    else (a.get("tool"), _canonical_jev_args(a.get("args", {})))
                )
                for a in last_6
            ]
            if sigs[0] == sigs[2] == sigs[4] and sigs[1] == sigs[3] == sigs[5] and sigs[0] != sigs[1]:
                return {
                    "decision": "deny",
                    "reason": (
                        f"Jev Loop Circuit Breaker ACTIVATED (engine: deterministic_alternating_breaker, confidence: 0.95): "
                        f"Alternating 2-step tool loop (`{sigs[0][0]}` <-> `{sigs[1][0]}`) detected across 6 consecutive calls with identical arguments. "
                        "Action cycling without progress is strictly prohibited. Enforce the 3-Turn Debug Spiral Hard Stop."
                    ),
                }
    except Exception:
        pass
    return None


_MODEL_TIER_RANKS = {"flash_lite": 0, "flash": 1, "inherit": 2, "pro": 3}
_FLASH_LITE_ROLES = frozenset({"diff-helper", "telemetry-helper"})
_FLASH_ROLES = frozenset({
    "research-explorer",
    "frontend-explorer",
    "backend-explorer",
    "test-runner",
    "doc-sync-worker",
    "librarian",
    "user-tester",
    "devops",
    "skillopt-optimizer",
})


def _handle_invoke_subagent(args: dict, payload: dict) -> dict:
    is_top_level = "Subagents" not in args and any(k in args for k in ("TypeName", "Role", "Prompt", "Model"))
    overwrite_model = None
    if "Subagents" in args:
        subagents = args.get("Subagents", [])
    elif is_top_level:
        subagents = [args]
    else:
        subagents = []

    if not isinstance(subagents, list):
        return {"decision": "allow"}

    # Swarm Budget & Depth Guard (ported from Codex max_threads / max_depth)
    if len(subagents) > 4:
        return {
            "decision": "deny",
            "reason": (
                f"Swarm Concurrency Budget Violation: Attempted to spawn {len(subagents)} subagents in a single call "
                "(max_threads = 4 per wave). Batch subagents into smaller bounded waves."
            ),
        }

    first_step = _get_first_transcript_step(payload)
    if first_step and first_step.get("type") != "USER_INPUT":
        return {
            "decision": "deny",
            "reason": (
                "Subagent Recursion Depth Violation (max_depth = 1): Child subagents are not permitted "
                "to spawn nested subagents. Return findings to the parent orchestrator instead."
            ),
        }

    for entry in subagents:
        if not isinstance(entry, dict):
            continue

        type_name = str(entry.get("TypeName", "")).strip()
        if type_name not in ("research", "self", "image-generator"):
            return {
                "decision": "deny",
                "reason": (
                    f"Native TypeName Contract Violation: TypeName '{type_name}' is invalid. "
                    "Use 'research' (read-only), 'self' (write/build/audit), or 'image-generator', "
                    "and pass the specialist persona via 'Role'."
                ),
            }

        model = entry.get("Model")
        model_str = ""
        if model is not None:
            model_str = str(model).strip()
            if model_str not in ("pro", "flash", "flash_lite", "inherit"):
                return {
                    "decision": "deny",
                    "reason": (
                        f"Native Model Contract Violation: Model '{model_str}' is invalid. "
                        "Allowed Gemini model tiers: ('pro', 'flash', 'flash_lite', 'inherit')."
                    ),
                }

        prompt = str(entry.get("Prompt", ""))
        if len(prompt) > 6000:
            return {
                "decision": "deny",
                "reason": (
                    f"Pub/Sub Sparsification Invariant: Subagent Prompt length ({len(prompt)} chars) "
                    "exceeds 6,000-character ceiling. Pass compact Story Shards / file coordinates "
                    "or write large stack traces to scratch artifacts instead of broadcasting raw dumps."
                ),
            }

        role = str(entry.get("Role", "")).strip().lower()
        if (type_name == "self" or not type_name) and role in ("dev-fe", "dev-be", "debugger", "designer", "meta-evolution", "frontend", "visual-engineer"):
            if "allowed_files" not in prompt:
                raw_role = entry.get("Role", role)
                return {
                    "decision": "deny",
                    "reason": (
                        f"BMAD Story Shard Lease Invariant: Builder subagent ('{raw_role}') "
                        "invoked without an `allowed_files` lease block in Prompt. "
                        "Specify `allowed_files:` (paths, globs, or `[]` for read-only probe)."
                    ),
                }

        if role in _FLASH_LITE_ROLES:
            assigned_tier = "flash_lite"
        elif role in _FLASH_ROLES or type_name == "research":
            assigned_tier = "flash"
        else:
            assigned_tier = "inherit"

        if model is not None:
            req_rank = _MODEL_TIER_RANKS[model_str]
            base_rank = _MODEL_TIER_RANKS[assigned_tier]
            if req_rank > base_rank:
                return {
                    "decision": "force_ask",
                    "reason": (
                        f"Subagent Model Escalation Gate: Role '{entry.get('Role') or type_name}' is assigned "
                        f"baseline model '{assigned_tier}', but Orchestrator requested stronger model '{model_str}'. "
                        "User confirmation is required before escalating a subagent to a stronger model."
                    ),
                }
            if req_rank < base_rank and is_top_level:
                overwrite_model = assigned_tier
        else:
            if is_top_level and assigned_tier in ("flash", "flash_lite"):
                overwrite_model = assigned_tier

    if overwrite_model:
        return {"decision": "allow", "overwrite": _safe_shallow_overwrite(args, {"Model": overwrite_model})}

    return {"decision": "allow"}


def _record_tool_denial_nonblocking(payload: dict, tool_name: str, res: dict, args: dict) -> None:
    """Record PreToolUse denials into cross-session failure ledger (<10ms budget)."""
    if ("unittest" in sys.modules or "pytest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))) and not os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB"):
        return
    try:
        reason = res.get("reason", "")
        if "Pre-Verification Invariant: File does not exist:" in reason:
            probe_path = ""
            if isinstance(args, dict):
                probe_path = (
                    args.get("AbsolutePath")
                    or args.get("Path")
                    or args.get("path")
                    or args.get("file")
                    or ""
                )
            if not probe_path:
                m_missing = re.search(
                    r"Pre-Verification Invariant: File does not exist:\s*`?([^`\n]+?)`?(?:\.|\s|$)",
                    reason,
                )
                if m_missing:
                    probe_path = m_missing.group(1)
            if os.path.basename(str(probe_path).rstrip("/\\")).lower() in (
                "status.md",
                "readme.md",
                "agents.md",
                "gemini.md",
                "context_ledger.md",
                "index.md",
            ):
                return
        conv_id = payload.get("conversationId", "")
        workspace = ""
        ws_paths = payload.get("workspacePaths", [])
        if ws_paths and isinstance(ws_paths, list):
            workspace = ws_paths[0]
        slug = os.path.basename(workspace.rstrip("/")) if workspace else "default"

        r_lower = reason.lower()
        if "jev" in r_lower:
            failure_type = "jev_loop"
            severity_tier = "S0_catastrophic"
            vertex = "skill"
        elif "hook immunity" in r_lower:
            failure_type = "hook_immunity_violation"
            severity_tier = "S0_catastrophic"
            vertex = "hook"
        elif "fix-the-code-not-the-test" in r_lower or "test-immutability lock" in r_lower or "debugger test-assertion lock" in r_lower:
            failure_type = "test_lock_violation"
            severity_tier = "S1_critical"
            vertex = "codebase"
        elif "three-strike rule activated" in r_lower or "three-strike" in r_lower or "three-strike file read" in r_lower:
            failure_type = "read_budget_lock"
            severity_tier = "S2_major"
            vertex = "tool_guidance"
        elif "6-slice" in r_lower or "slice loop breaker" in r_lower:
            failure_type = "slice_loop_breaker"
            severity_tier = "S2_major"
            vertex = "tool_guidance"
        elif "lease invariant" in r_lower or "allowed_files" in r_lower:
            failure_type = "lease_violation"
            severity_tier = "S2_major"
            vertex = "skill"
        elif "6,000-character ceiling" in r_lower or "6,000 character ceiling" in r_lower or "prompt exceeded" in r_lower:
            failure_type = "subagent_prompt_overflow"
            severity_tier = "S2_major"
            vertex = "routing"
        elif "flood" in r_lower:
            failure_type = "flood_guard"
            severity_tier = "S3_minor"
            vertex = "tool_guidance"
        elif "legacy" in r_lower:
            failure_type = "legacy_cli_blocked"
            severity_tier = "S3_minor"
            vertex = "tool_guidance"
        elif "slice" in r_lower or "250 lines" in r_lower or "250-line" in r_lower or ("exceeds " in r_lower and "-line maximum" in r_lower):
            failure_type = "slice_cap_exceeded"
            severity_tier = "S3_minor"
            vertex = "tool_guidance"
        elif "polling" in r_lower:
            failure_type = "task_polling_blocked"
            severity_tier = "S3_minor"
            vertex = "tool_guidance"
        else:
            failure_type = "tool_denial"
            severity_tier = "S3_minor"
            vertex = "tool_guidance"

        sentinel_dir = os.path.expanduser("~/.gemini/antigravity/scripts")
        if sentinel_dir not in sys.path:
            sys.path.insert(0, sentinel_dir)
        import importlib
        sentinel = importlib.import_module("burn-rate-sentinel")
        sentinel.record_harness_failure(
            conv_id=conv_id,
            failure_type=failure_type,
            slug=slug,
            tool_name=tool_name,
            reason=reason,
            details=json.dumps(args)[:500] if args else "",
            severity_tier=severity_tier,
            vertex=vertex,
            session_type="subagent" if payload.get("subagentRole") else "top_level",
        )
    except Exception:
        pass


def _emit_tool_decision(res: dict, payload: dict, tool_name: str, args: dict) -> None:
    if res.get("decision") in ("ask", "force_ask") and _is_subagent_conversation(payload):
        res = {
            "decision": "deny",
            "reason": (
                f"Subagent Interactive Gate Blocked: {res.get('reason', '')} "
                "Background subagents cannot request user confirmation; report this action back to the parent PM agent."
            ),
        }
    if res.get("decision") == "deny":
        _record_tool_denial_nonblocking(payload, tool_name, res, args)
    print(json.dumps(res))


def main() -> None:
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}

        loop_deny = _track_and_check_loop_with_jev(payload, tool_name, args)
        if loop_deny:
            _emit_tool_decision(loop_deny, payload, tool_name, args)
            return

        if tool_name == "manage_task":
            res = _handle_manage_task(args, payload)
            _emit_tool_decision(res, payload, tool_name, args)
            return

        if tool_name == "manage_subagents":
            res = _handle_manage_subagents(args, payload)
            _emit_tool_decision(res, payload, tool_name, args)
            return

        if tool_name == "schedule":
            res = _handle_schedule(args, payload)
            _emit_tool_decision(res, payload, tool_name, args)
            return

        if tool_name == "run_workflow":
            res = _handle_run_workflow(args, payload)
            _emit_tool_decision(res, payload, tool_name, args)
            return

        if tool_name == "define_subagent":
            res = _handle_define_subagent(args, payload)
            _emit_tool_decision(res, payload, tool_name, args)
            return

        if tool_name == "call_mcp_tool" or tool_name.startswith("mcp_"):
            res = _handle_mcp_tool(tool_name, args, payload)
            _emit_tool_decision(res, payload, tool_name, args)
            return

        if tool_name == "run_command":
            stagnation_deny = _check_error_stagnation_circuit_breaker(payload, tool_name, args)
            if stagnation_deny:
                _emit_tool_decision(stagnation_deny, payload, tool_name, args)
                return
            res = _handle_run_command(args, payload)
            _emit_tool_decision(res, payload, tool_name, args)
            return

        if tool_name == "send_message":
            res = _handle_send_message(args, payload)
            _emit_tool_decision(res, payload, tool_name, args)
            return

        if tool_name in ("view_file", "read_file"):
            res = _handle_view_file(args, payload)
            _emit_tool_decision(res, payload, tool_name, args)
            return

        if tool_name == "list_dir":
            res = _handle_list_dir(args, payload)
            _emit_tool_decision(res, payload, tool_name, args)
            return

        if tool_name in ("write_to_file", "write_file", "replace_file_content", "multi_replace_file_content", "edit_file"):
            res = _handle_file_mutation(tool_name, args, payload)
            _emit_tool_decision(res, payload, tool_name, args)
            return

        if tool_name == "invoke_subagent":
            res = _handle_invoke_subagent(args, payload)
            _emit_tool_decision(res, payload, tool_name, args)
            return

        print(json.dumps({"decision": "allow"}))

    except Exception:
        # Strict fail-safe: never block agent on unexpected internal hook errors
        print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()

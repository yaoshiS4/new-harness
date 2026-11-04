#!/usr/bin/env python3
"""PreToolUse gate for the Claude Code SOTA Harness.

Ports the Antigravity ``pre_tool_use_hook.py`` invariants onto Claude Code's
native tool surface (Bash, Read, Edit, Write, MultiEdit, Grep, Glob, Agent,
mcp__*). Output follows the Claude Code hook contract::

    {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                            "permissionDecision": "allow|deny|ask",
                            "permissionDecisionReason": "...",
                            "updatedInput": {...}}}

Gates (in dispatch order):
  * Jev loop circuit breaker (3-strike identical call, 4-skeleton, 2-step cycle)
  * Bash: length cap, role-isolation shell-write guard + lease, sleep/cd policy,
    modern-CLI nudge, exit-code masking + pipefail guard, untargeted test guard,
    unconstrained output guard (git log / rg / fd / tree / ls -R / cat / gradle),
    destructive + dependency ``ask`` gates, model escalation gate,
    error-stagnation circuit breaker.
  * Read: image block, privacy block, scout block, pre-verification, read-once
    small files, slice cap (auto-clamp via updatedInput), outline-first >400
    lines with inline AST skeleton, 3-strike / 6-slice / whole-read loop breakers.
  * Grep/Glob: scout block, head_limit injection.
  * Edit/Write/MultiEdit: hook immunity, suppression injection lock,
    test-assertion locks (Fix-The-Code-Not-The-Test), recon precondition for
    implementation_plan.md, PM zero-code-write + role isolation + Story Shard
    leases, Aider fuzzy old_string reconciliation, in-memory syntax gate,
    shift-left import verification, shadow git checkpoint.
  * Agent: nesting depth, prompt size, builder lease requirement, model escalation.
  * mcp__*: read-only role mutation lock.
"""
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
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as H  # noqa: E402

# ---------------------------------------------------------------------------
# Regex catalogue
# ---------------------------------------------------------------------------

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
    r"(?://\s*@ts-(?:ignore|expect-error)\b|#\s*type:\s*ignore\b|/\*\s*eslint-disable\b|//\s*eslint-disable-next-line\b|#\s*noqa\b)"
)
_RUNNER_INVOCATION_RE = re.compile(
    r"(?:^|[;&|(`\n]|\$\()\s*(?:set\s+[^;\n]*;\s*)*(?:(?:env\s+[\w=]+\s+|time\s+|npx\s+|uv\s+run\s+|poetry\s+run\s+|python3?\s+-m\s+)*)(?:\S*\/)?(?:py\.?test|vitest|jest|npm\s+test|pnpm\s+test|yarn\s+test|cargo\s+(?:test|check)|tsc|ruff\s+check|py_compile|unittest|verify-oracle(?:\.sh)?|test-3-round-loop(?:\.sh)?|run-compiled-qc(?:\.py)?|verify-claude-harness(?:\.sh)?|verify-harness(?:\.sh)?)\b"
)
_EPISTEMIC_UNCERTAINTY_RE = re.compile(
    r"\b(?:ModuleNotFoundError|ImportError|Cannot find module|TS2305|TS2339)\b|has no exported member",
    re.IGNORECASE,
)
_ASSERT_LINE_RE = re.compile(r"^\s*(?:assert\b|expect\s*\(|self\.assert)", re.MULTILINE)
_LITERAL_VAL_PAT = r"(?:'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|\b(?:True|False|true|false|None|null)\b|-?\d+(?:\.\d+)?)"
_ASSERT_EQ_RE = re.compile(r"^\s*assert\s+(.+?)\s*==\s*(%s)\s*(?:,.*)?$" % _LITERAL_VAL_PAT, re.MULTILINE)
_SELF_ASSERT_EQ_RE = re.compile(r"^\s*self\.assertEqual\s*\(\s*(.+?)\s*,\s*(%s)\s*(?:,.*)?\)\s*$" % _LITERAL_VAL_PAT, re.MULTILINE)
_EXPECT_BE_RE = re.compile(r"^\s*expect\s*\(\s*(.+?)\s*\)\.(?:toBe|toEqual)\s*\(\s*(%s)\s*\)\s*;?$" % _LITERAL_VAL_PAT, re.MULTILINE)

DESTRUCTIVE_COMMAND_PATTERNS = [
    (re.compile(r"\brm\s+(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+--force|--force\s+--recursive)\b"), "Recursive force removal (rm -rf) detected"),
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "Destructive git hard reset detected"),
    (re.compile(r"\bgit\s+clean\s+-[a-zA-Z]*f\b"), "Destructive git clean -f detected"),
    (re.compile(r"\bgit\s+push\b"), "Git remote push detected"),
    (re.compile(r"\bgit\s+restore\s+(?:\.|\*)"), "Wholesale git restore detected"),
    (re.compile(r"\bgit\s+checkout\s+(?:--\s+)?(?:\.|\*)"), "Wholesale git checkout discard detected"),
    (re.compile(r"\b(?:dropdb|drop\s+database|drop\s+table)\b", re.IGNORECASE), "Database drop statement detected"),
    (re.compile(r"\bprisma\s+migrate\s+reset\b"), "Prisma database reset detected"),
    (re.compile(r"\balembic\s+downgrade\b"), "Alembic database downgrade detected"),
    (re.compile(r"\b(?:mkfs(?:\.[a-zA-Z0-9]+)?|dd\s+if=)\b"), "Raw disk/filesystem write command detected"),
]

DEPENDENCY_MUTATION_PATTERNS = [
    (re.compile(r"\b(?:npm|pnpm|yarn|bun)\s+(?:install|i|add|remove|uninstall)\s+(?!-(?:-save-exact|E|-save-dev|D|-global|g|-frozen-lockfile)\b)[a-zA-Z0-9@/._-]+"), "Package dependency modification detected"),
    (re.compile(r"\bpip(?:3)?\s+install\s+(?!-r\b|--requirement\b|-e\b|--editable\b)[a-zA-Z0-9_.-]+"), "Python package installation detected"),
    (re.compile(r"\buv\s+(?:add|pip\s+install\s+(?!-e\b|--editable\b|-r\b)[a-zA-Z0-9_.-]+)"), "uv dependency modification detected"),
    (re.compile(r"\bpoetry\s+add\b"), "Poetry package dependency modification detected"),
    (re.compile(r"\bcargo\s+add\b"), "Cargo dependency modification detected"),
    (re.compile(r"\bgo\s+get\b"), "Go dependency modification detected"),
]

_MUTATING_MCP_TOOLS = frozenset({
    "vault_write", "wiki_ingest", "wiki_rebuild", "memory_store", "graph_upsert", "knowledge_capture",
    "orchestration_lesson", "checkpoint_save", "handoff_write", "handoff_checkpoint",
    "commit_context_ledger", "project_register", "project_index",
})
_MUTATING_MCP_VERB_RE = re.compile(r"(?:^|_)(?:create|delete|update|write|drop|remove|upsert)(?:_|$)", re.IGNORECASE)

_COSMETIC_JEV_KEYS = frozenset({"description", "timeout", "run_in_background", "statusmessage"})
_PRODUCER_COMMAND_RE = re.compile(
    r"^(?:(?:env\s+|[A-Za-z_][A-Za-z0-9_]*=\S+\s+|timeout\s+\S+\s+)*)"
    r"(?:dexdump|adb\s+(?:-[^\s]+\s+)*(?:logcat|shell|exec-out)|aapt2?|strings|unzip\s+-p|gh\s+api)\b"
)
_TRAILING_FILTER_STAGE_RE = re.compile(r"^(?:rg|grep|egrep|fgrep|sed|sd|awk|head|tail|cut)\b")

LEASE_REQUIRED_ROLES = frozenset({"dev-fe", "dev-be", "debugger", "designer", "meta-evolution", "frontend", "visual-engineer"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deny(reason: str) -> dict:
    return {"decision": "deny", "reason": reason}


def _ask(reason: str) -> dict:
    return {"decision": "ask", "reason": reason}


def _allow(updated: Optional[dict] = None, context: str = "") -> dict:
    out: dict = {"decision": "allow"}
    if updated:
        out["updatedInput"] = updated
    if context:
        out["context"] = context
    return out


def _strip_safe_quoted_strings(cmd: str) -> str:
    m = re.match(r"^\s*(?:bash|sh|zsh)\s+-c\s+([\"'])(.*)\1\s*$", cmd, flags=re.DOTALL)
    target = m.group(2) if m else cmd
    target = re.sub(r'\\\"(?:\\\\|\\(?!")|[^"\\])*\\\"|\\\'(?:\\\\|\\(?!\')|[^\'\\])*\\\'', '""', target, flags=re.DOTALL)
    return re.sub(r'(\"(?:\\.|[^"\\])*\"|\'(?:\\.|[^\'\\])*\')', '""', target, flags=re.DOTALL)


def _is_untargeted_test_command(cmd: str) -> bool:
    if "ALL_TESTS=1" in cmd or "PRE_SHIP=1" in cmd:
        return False
    if os.environ.get("ALL_TESTS") == "1" or os.environ.get("PRE_SHIP") == "1":
        return False
    pkg_test = bool(re.search(r"\b(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?test\b", cmd))
    bare_test = bool(re.search(r"\b(?:npx\s+)?(?:vitest|jest)(?:\s+run)?\b", cmd))
    if not (pkg_test or bare_test):
        return False
    if re.search(r"(?:^|\s)(?:-t|--testNamePattern|--grep|--related|--changed)\b", cmd):
        return False
    for token in cmd.split():
        tok = token.strip("'\"")
        if tok.startswith("-"):
            continue
        if tok in ("npm", "pnpm", "yarn", "bun", "npx", "run", "test", "vitest", "jest", "--", "bash", "sh", "zsh", "-c"):
            continue
        if (
            re.search(r"\.(?:test|spec)\.[a-zA-Z0-9]+", tok)
            or tok.startswith(("test/", "./test/", "__tests__/"))
            or tok.endswith((".ts", ".tsx", ".js", ".jsx", ".py"))
        ):
            return False
    return True


def _is_unconstrained_command(cmd_structure: str, raw_cmd: str, cwd: str, policy: dict) -> Optional[str]:
    if "|" in cmd_structure or ">" in cmd_structure:
        return None
    stripped = cmd_structure.strip()
    limit = int(policy.get("flood_limit", 50))

    git_log = re.search(r"(?:^|[;&|(`\n])\s*git\s+log\b([^;&|\n]*)", stripped)
    if git_log:
        args_str = git_log.group(1).strip()
        has_bound = bool(re.search(r"(?:^|\s)(?:-[0-9]+|-n\s*[0-9]+|--max-count=[0-9]+|--oneline|--grep|--author|--since|--after|--until|--before|-S|-G)(?:\s|=|$)", args_str))
        if not has_bound and (not args_str or args_str.startswith("-")):
            return "Token Economy Invariant: Unbounded `git log` detected without pagination. Use `git log -n 20 --oneline` or pipe to `head -n 30`."

    rg_match = re.search(r"(?:^|[;&|(`\n])\s*rg(?![-\w])([^;&|\n]*)", stripped)
    if rg_match:
        rg_args = rg_match.group(1).strip()
        has_bound = bool(re.search(r"(?:^|\s)(?:-m(?:=|\s|[0-9]|$)|--max-count\b|-l\b|--files-with-matches\b|-c\b|--count\b|-q\b|--quiet\b|--stats\b|-1\b|--help\b|-h\b|--version\b|-V\b)", rg_args))
        if not has_bound and not _targets_single_file(rg_args, cwd):
            return (
                "Token Economy Invariant: SWE-agent %d-Hit Search Flood Guard: unbounded `rg` detected. "
                "Add `-m %d`, `-l`, `-c`, pipe to `head -n %d`, target a single file, or use the Grep tool with head_limit." % (limit, limit, limit)
            )

    fd_match = re.search(r"(?:^|[;&|(`\n])\s*fd(?![-\w])([^;&|\n]*)", stripped)
    if fd_match:
        fd_args = fd_match.group(1).strip()
        has_bound = bool(re.search(r"(?:^|\s)(?:--max-results\b|-1\b|--max-depth\b|-d(?:=|\s|[0-9]|$)|-l\b|-c\b|--count\b|-q\b|--quiet\b|--stats\b|--help\b|-h\b|--version\b|-V\b)", fd_args))
        if not has_bound and not _targets_single_file(fd_args, cwd):
            return (
                "Token Economy Invariant: SWE-agent %d-Hit Search Flood Guard: unbounded `fd` detected. "
                "Add `--max-results %d` or `-d 2`, pipe to `head -n %d`, or use the Glob tool." % (limit, limit, limit)
            )

    tree_match = re.search(r"(?:^|[;&|(`\n])\s*tree(?![-\w])([^;&|\n]*)", stripped)
    if tree_match:
        tree_args = tree_match.group(1).strip()
        if not re.search(r"(?:-L\s*\d+|-L=\d+|--level(?:\s+|=)\d+|--help\b|-h\b|--version\b|-v\b)", tree_args):
            return "Token Economy Invariant: Unbounded `tree` detected. Use `tree -L 2` or pipe to `head -n 40`."
    if re.search(r"(?:^|[;&|(`\n])\s*ls\s+-[a-zA-Z]*R[a-zA-Z]*\b", stripped):
        return "Token Economy Invariant: Recursive `ls -R` detected. Use a non-recursive listing, the Glob tool, or pipe to `head -n 40`."

    cat_match = re.search(r"(?:^|[;&|(`\n])\s*cat\s+(?:-[a-zA-Z0-9]+\s+)*([^\s;&|<>\'\"]+)", stripped)
    if cat_match:
        target_p = cat_match.group(1).strip().strip("'\"")
        if not target_p.startswith("-"):
            try:
                resolved = H.normalize_path(target_p, cwd)
                if os.path.isfile(resolved):
                    cnt = H.count_lines(resolved)
                    if cnt > int(policy.get("read_once_threshold", 200)):
                        return (
                            "Token Economy Invariant: `cat` on `%s` (%d lines) without pagination. "
                            "Use the Read tool with offset/limit, or pipe to `head -n 50` / `tail -n 50`." % (os.path.basename(resolved), cnt)
                        )
            except Exception:
                pass

    gradle_match = re.search(r"(?:^|[;&|(`\n])\s*(?:\./|\S+/)?gradlew?(?![-\w])([^;&|\n]*)", stripped)
    if gradle_match:
        gradle_args = gradle_match.group(1).strip()
        if not re.search(r"(?:^|\s)(?:--console=plain\b|-q\b|--quiet\b|--version\b|-v\b|--help\b|-h\b|--status\b|--stop\b)", gradle_args):
            return "Token Economy Invariant: Unbounded gradle PTY progress output. Pass `--console=plain -q` to prevent carriage-return progress-bar saturation."
    return None


def _targets_single_file(args_str: str, cwd: str) -> bool:
    try:
        tokens = shlex.split(args_str)
    except Exception:
        tokens = args_str.split()
    for tok in tokens:
        if tok.startswith("-"):
            continue
        if os.path.isfile(H.normalize_path(tok, cwd)):
            return True
    return False


def _detect_shell_source_mutation(cmd: str, cwd: str) -> Optional[str]:
    cmd_structure = _strip_safe_quoted_strings(cmd)
    if ">" in cmd_structure:
        redir = re.compile(r"(?:(?<![<0-9&])>|(?<!<)[0-9&]>|>>|[0-9&]>>)\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s;&|<>]+))")
        for m in redir.finditer(cmd_structure):
            target = m.group(1) or m.group(2) or m.group(3) or ""
            if not target:
                span_start, span_end = m.span()
                m_raw = redir.match(cmd[span_start:span_end + 100])
                if m_raw:
                    target = m_raw.group(1) or m_raw.group(2) or m_raw.group(3) or ""
            if target and H.is_app_code(target, cwd):
                return target
    if re.search(r"\btee\b", cmd_structure):
        for tee_match in re.finditer(r"\btee\b([^;|&]+)", cmd):
            for tok in _tokens(tee_match.group(1)):
                if not tok.startswith("-") and H.is_app_code(tok, cwd):
                    return tok
    if re.search(r"\bsed\b", cmd_structure):
        for sed_match in re.finditer(r"\bsed\b([^;|&]+)", cmd):
            if re.search(r"(?:^|\s)(?:-[a-zA-Z]*i[a-zA-Z0-9._-]*|--in-place(?:=\S*)?)\b", sed_match.group(0)):
                for tok in _tokens(sed_match.group(1)):
                    if not tok.startswith("-") and H.is_app_code(tok, cwd):
                        return tok
    if re.search(r"\bperl\b", cmd_structure):
        for perl_match in re.finditer(r"\bperl\b([^;|&]+)", cmd):
            if re.search(r"(?:^|\s)(?:-[a-zA-Z]*i[a-zA-Z0-9._-]*)\b", perl_match.group(0)):
                for tok in _tokens(perl_match.group(1)):
                    if not tok.startswith("-") and H.is_app_code(tok, cwd):
                        return tok
    if re.search(r"\bsd\b", cmd_structure):
        for sd_match in re.finditer(r"\bsd\b([^;|&]+)", cmd):
            pos = 0
            for tok in _tokens(sd_match.group(1)):
                if tok.startswith("-"):
                    continue
                pos += 1
                if pos <= 2:
                    continue
                if H.is_app_code(tok, cwd):
                    return tok
    if re.search(r"\b(?:patch|git\s+apply)\b", cmd):
        for p_match in re.finditer(r"\b(?:patch|git\s+apply)\b([^;|&]+)", cmd):
            for tok in _tokens(p_match.group(1)):
                if not tok.startswith("-") and H.is_app_code(tok, cwd):
                    return tok
    if re.search(r"\bpython3?\s+-c\b", cmd):
        for target in re.findall(r"""open\s*\(\s*(?:file\s*=\s*)?(?:Path\s*\(\s*)?['"]([^'"]+)['"]\s*\)?\s*,\s*(?:mode\s*=\s*)?['"][wa][b+]?['"]""", cmd):
            if H.is_app_code(target, cwd):
                return target
        for target in re.findall(r"""Path\s*\(\s*['"]([^'"]+)['"]\s*\)\s*\.\s*write_(?:text|bytes)\s*\(""", cmd):
            if H.is_app_code(target, cwd):
                return target
    return None


def _tokens(s: str) -> list:
    try:
        return shlex.split(s)
    except Exception:
        return s.split()


def _lease_check(payload: dict, target_norm: str, cwd: str) -> Optional[dict]:
    """Story Shard lease enforcement for subagents carrying an allowed_files block."""
    lease = H.lease_for(payload)
    if not lease.get("has_allowed_files"):
        return None
    allowed = list(lease.get("allowed_files") or [])
    if any(H.matches_allowed_file(target_norm, pat, cwd) for pat in allowed):
        return None
    return _deny(
        "Story Shard File Lease Violation (BMAD): target `%s` is outside this subagent's leased allowed_files %s. "
        "Report back to the orchestrator to expand the lease before touching unleased files." % (os.path.basename(target_norm), allowed)
    )


# ---------------------------------------------------------------------------
# Bash
# ---------------------------------------------------------------------------

def handle_bash(tool_input: dict, payload: dict, policy: dict) -> dict:
    raw_cmd = str(tool_input.get("command") or "").strip()
    if not raw_cmd:
        return _allow()
    cmd = H.unwrap_outer_quotes(raw_cmd) or raw_cmd
    cwd = H.workspace(payload)
    role = H.role_of(payload)

    limit = int(policy.get("command_length_limit", 4000))
    if len(cmd) > limit:
        return _deny(
            "Token Economy Invariant: command string length (%d) exceeds %d characters. "
            "Write multi-line scripts to the scratchpad directory and execute them by path." % (len(cmd), limit)
        )

    # Role isolation shell-write guard + lease
    mutated = _detect_shell_source_mutation(cmd, cwd)
    if mutated:
        if H.is_non_builder_role(role) and not (role == H.ROOT_ROLE and policy.get("root_may_edit_code")):
            return _deny(
                "Role Isolation Shell-Write Guard (pm-no-implementation): non-builder session (%s) must not mutate application "
                "source via shell write (`%s`). Delegate to a builder subagent (dev-fe / dev-be / debugger) via the Agent tool." % (role, mutated)
            )
        lease_deny = _lease_check(payload, H.normalize_path(mutated, cwd), cwd)
        if lease_deny:
            return lease_deny

    cmd_structure = _strip_safe_quoted_strings(cmd)

    if re.search(r"\badb\s+shell\s+input\s+tap\b", cmd_structure) or re.search(r"\badb\s+shell\s+screencap\b", cmd_structure):
        return _deny("Manual ADB coordinate tapping and screencap loops are prohibited. Validate UI state via deterministic component/hook tests.")

    if re.search(r"(?:^|[;&|(`\"'\n]|\$\()\s*\bsleep\s+\d+", cmd_structure):
        return _deny(
            "Reactive Runtime Invariant: `sleep` in Bash is forbidden (no polling). Use `run_in_background` and wait for the "
            "completion notification, or the Monitor tool with an until-loop."
        )

    if policy.get("ban_cd") and re.search(r"(?:^|[;&|(`\"'\n]|\$\()\s*\bcd(?:\s+|$|[\"';&|)])", cmd_structure):
        return _deny("The `cd` command is prohibited by policy. Use tool-native directory flags (git -C, npm --prefix, make -C) or absolute paths.")

    modern = str(policy.get("require_modern_cli", "auto")).lower()
    if modern in ("auto", "true", "1", "yes"):
        enforce_rg = modern != "auto" or bool(H.which("rg"))
        enforce_fd = modern != "auto" or bool(H.which("fd"))
        if enforce_rg:
            for m in re.finditer(r"(?:^|[;&|(`\"'\n]|\$\()\s*(?:(?:/usr)?/bin/)?(?<!\bast-)\b(grep|egrep|fgrep|rgrep)\b", cmd_structure):
                if re.search(r"\bgit\s+$", cmd_structure[:m.start(1)]):
                    continue
                return _deny(
                    "Modern CLI Tool Invariant: legacy `%s` is blocked while `rg` is installed. Use the Grep tool, or `rg -n -m 50 'pattern' path`." % m.group(1)
                )
        if enforce_fd and re.search(r"(?:^|[;&|(`\n]|\$\()\s*(?:(?:/usr)?/bin/)?\bfind\b", cmd_structure):
            return _deny("Modern CLI Tool Invariant: legacy `find` is blocked while `fd` is installed. Use the Glob tool, or `fd --max-results 50 'pattern' path`.")

    m_mask = re.search(r"\|\|\s*(?:true\b|(?::(?:\s|;|$))|echo\b)", cmd_structure)
    if m_mask and _RUNNER_INVOCATION_RE.search(cmd_structure[:m_mask.start()]):
        return _deny(
            "Process Exit-Code Masking Invariant: masking verification/test/compiler exit codes via `|| true`, `|| :` or `|| echo` is forbidden. "
            "Commands must propagate non-zero exit codes so failures are detected."
        )
    m_pipe = re.search(r"\|\s*(?:head|tail|tee)\b", cmd_structure)
    if m_pipe and _RUNNER_INVOCATION_RE.search(cmd_structure[:m_pipe.start()]):
        if not re.search(r"\bset\s+[^;\n]*\bpipefail\b", cmd_structure):
            return _deny(
                "Process Pipe Exit-Code Swallowing Guard: verification command piped to head/tail/tee without `pipefail`. "
                "Prefix with `set -o pipefail; ` so non-zero test/compiler exit codes are not swallowed."
            )

    if _is_untargeted_test_command(cmd_structure):
        return _deny(
            "Strict Targeted Test Execution Invariant: untargeted full test suite runs (`%s`) are blocked to prevent token waste and timeouts. "
            "Target the test file directly (e.g. `npx vitest run <path>`). For the Pre-Ship gate prefix with `PRE_SHIP=1` or `ALL_TESTS=1`." % cmd
        )

    unconstrained = _is_unconstrained_command(cmd_structure, cmd, cwd, policy)
    if unconstrained:
        reason = unconstrained if unconstrained.startswith("Token Economy Invariant:") else "Token Economy Invariant: " + unconstrained
        return _deny(reason)

    for pattern, desc in DESTRUCTIVE_COMMAND_PATTERNS:
        m = pattern.search(cmd_structure)
        if m:
            return _ask("%s: `%s`. Explicit user confirmation is required under harness safety guardrails." % (desc, m.group(0)))
    for pattern, desc in DEPENDENCY_MUTATION_PATTERNS:
        m = pattern.search(cmd_structure)
        if m:
            return _ask("%s: `%s`. Package modifications must be confirmed under the dependency policy." % (desc, m.group(0)))

    if re.search(r"(?:^|[;&|(\n])\s*claude\b[^;&|\n]*--model(?:=|\s+)['\"]?(?:opus|fable|claude-opus|claude-fable)", cmd):
        return _ask("Subagent CLI Model Escalation Gate: spawning `claude` with a frontier-tier model requires explicit user approval.")

    annotated = _annotate_verification_exit_code(raw_cmd, tool_input, payload, policy)
    if annotated is not None:
        return _allow(annotated)
    return _allow()


def _annotate_verification_exit_code(raw_cmd: str, tool_input: dict, payload: dict, policy: dict) -> Optional[dict]:
    """Claude Code's Bash hook response carries stdout/stderr but no exit code, so a silently failing
    verification (e.g. a script exiting non-zero without output) would look like a pass. For verification
    commands we wrap the command so a non-zero exit prints `[harness] verification exit_code=N` and the
    exit status is preserved. Skipped for background runs, heredocs, and already-annotated commands."""
    if not policy.get("annotate_verification_exit_codes", True):
        return None
    if tool_input.get("run_in_background"):
        return None
    cmd = raw_cmd.rstrip()
    if not cmd or "[harness] verification exit_code" in cmd or "<<" in cmd or cmd.endswith("&") or re.search(r"(?:^|\s)exec\s", cmd):
        return None
    try:
        import post_tool_use as POST  # local import: avoids a cycle at module load
        if not POST.is_verification_command(cmd, H.workspace(payload)):
            return None
    except Exception:
        return None
    wrapped = "{\n%s\n}\n__hrc=$?; if [ \"$__hrc\" -ne 0 ]; then echo \"[harness] verification exit_code=$__hrc\"; fi; exit \"$__hrc\"" % cmd
    if len(wrapped) > int(policy.get("command_length_limit", 4000)):
        return None
    updated = dict(tool_input)
    updated["command"] = wrapped
    return updated


# ---------------------------------------------------------------------------
# Error-stagnation circuit breaker (fed by post_tool_use)
# ---------------------------------------------------------------------------

def check_error_stagnation(payload: dict) -> Optional[dict]:
    ledger = H.load_state(payload, "err_sig", default={})
    if not isinstance(ledger, dict):
        return None
    sigs = ledger.get("signatures") or []
    if len(sigs) >= 3 and sigs[-1] and sigs[-1] == sigs[-2] == sigs[-3]:
        reason = (
            "Error-Stagnation Circuit Breaker: the last 3 command executions failed with the identical error signature. "
            "Stop blind trial-and-error and inspect the root cause or symbols first."
        )
        if _EPISTEMIC_UNCERTAINTY_RE.search(str(ledger.get("last_error") or "")):
            reason += " AdaSearch Epistemic Uncertainty Trigger: query authoritative library docs (context7 `resolve-library-id` -> `query-docs`) before retrying."
        # Reset so the agent can proceed after acknowledging.
        ledger["signatures"] = []
        H.save_state(payload, "err_sig", ledger)
        return _deny(reason)
    return None


# ---------------------------------------------------------------------------
# Jev loop circuit breaker
# ---------------------------------------------------------------------------

def _canonical_args(args: dict) -> str:
    if not isinstance(args, dict):
        return ""
    filtered = {}
    for k, v in args.items():
        if str(k).lower() in _COSMETIC_JEV_KEYS:
            continue
        if str(k) == "command" and isinstance(v, str):
            v = " ".join(v.split())
        filtered[k] = v
    try:
        return json.dumps(filtered, sort_keys=True, default=str)
    except Exception:
        return str(filtered)


def _command_skeleton(cmd: str) -> str:
    if not isinstance(cmd, str):
        return ""
    clean = " ".join(cmd.strip().split())
    if not clean:
        return ""
    first = clean.split("|", 1)[0].strip()
    if re.match(r"^bat\b", first) and re.search(r"(?:^|\s)(?:-r|--line-range)(?:=|\s+)\d*:\d*", first):
        target = ""
        skip = False
        for tok in _tokens(first)[1:]:
            if skip:
                skip = False
                continue
            if tok in ("-r", "--line-range", "--style", "--theme", "--pager", "--paging", "--language", "-l"):
                skip = True
                continue
            if tok.startswith("-") or re.match(r"^\d*:\d*$", tok):
                continue
            target = tok
        if target:
            return "shell_slice:" + os.path.normpath(target.strip("\"'"))
    m_sed = re.match(r"""^sed\s+(?:-[a-zA-Z]*n[a-zA-Z]*\s+)+['"]?\d+\s*,\s*\d+\s*p(?:;\s*\d+\s*q)?['"]?\s+(['"]?[^'"\s|;&]+['"]?)""", first)
    if m_sed:
        return "shell_slice:" + os.path.normpath(m_sed.group(1).strip("'\""))
    m_head = re.match(r"""^(?:head|tail)\s+-n?\s*\d+\s+(['"]?[^'"\s|;&]+['"]?)$""", first)
    if m_head:
        return "shell_slice:" + os.path.normpath(m_head.group(1).strip("'\""))
    if "|" in clean:
        producer, rest = clean.split("|", 1)
        if _PRODUCER_COMMAND_RE.search(producer.strip()) and _TRAILING_FILTER_STAGE_RE.match(rest.strip()):
            return producer.strip()
    return clean


def track_and_check_loop(payload: dict, tool_name: str, tool_input: dict) -> Optional[dict]:
    try:
        actions = H.load_state(payload, "actions", default=[])
        if not isinstance(actions, list):
            actions = []
        actions = actions[-16:]
        actions.append({"tool": tool_name, "args": tool_input if isinstance(tool_input, dict) else {}, "ts": time.time()})
        H.save_state(payload, "actions", actions[-16:])

        if tool_name in H.SHELL_TOOLS and isinstance(tool_input, dict):
            cur_skel = _command_skeleton(str(tool_input.get("command") or ""))
            if cur_skel.startswith("shell_slice:"):
                count = sum(
                    1 for a in actions
                    if a.get("tool") in H.SHELL_TOOLS and _command_skeleton(str((a.get("args") or {}).get("command") or "")) == cur_skel
                )
                if count >= 3:
                    return _deny(
                        "Slice Loop Breaker ACTIVATED: `%s` has been sliced %d times via shell range commands. "
                        "Sequential shell slicing is blocked; use the Read tool with offset/limit once, Grep, or codegraph:extract_symbols." % (cur_skel.split(":", 1)[1], count)
                    )

        if len(actions) >= 3 and tool_name not in H.READ_TOOLS:
            sigs3 = [(a.get("tool"), _canonical_args(a.get("args", {}))) for a in actions[-3:]]
            if sigs3[0] == sigs3[1] == sigs3[2]:
                return _deny(
                    "Jev Loop Circuit Breaker ACTIVATED (deterministic_circuit_breaker, confidence 0.95): repetitive execution of `%s` with identical arguments. "
                    "Action cycling without progress is prohibited. Enforce the 3-Turn Debug Spiral Hard Stop: change approach or report the blocker." % tool_name
                )
        if len(actions) >= 4 and all(a.get("tool") in H.SHELL_TOOLS for a in actions[-4:]):
            skels = [_command_skeleton(str((a.get("args") or {}).get("command") or "")) for a in actions[-4:]]
            if skels[0] and skels[0] == skels[1] == skels[2] == skels[3]:
                return _deny(
                    "Jev Loop Circuit Breaker ACTIVATED (semantic_command_skeleton): 4 consecutive Bash executions share the identical command skeleton (`%s`). "
                    "Stop repetitive pipe/filter probing; batch queries or write the output to a scratch file once and inspect it." % skels[0]
                )
        if len(actions) >= 6:
            sigs = [(a.get("tool"), _canonical_args(a.get("args", {}))) for a in actions[-6:]]
            if sigs[0] == sigs[2] == sigs[4] and sigs[1] == sigs[3] == sigs[5] and sigs[0] != sigs[1]:
                return _deny(
                    "Jev Loop Circuit Breaker ACTIVATED (deterministic_alternating_breaker): Alternating 2-step tool loop (`%s` <-> `%s`) across 6 consecutive calls. "
                    "Action cycling without progress is prohibited." % (sigs[0][0], sigs[1][0])
                )
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def _extract_inline_ast_skeleton(file_path: str, max_items: int = 35) -> str:
    items = []
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
                loc = "[L%d-L%d]" % (start_l, end_l) if end_l > start_l else "[L%d]" % start_l
                if isinstance(node, ast.ClassDef):
                    items.append("  class %s %s" % (node.name, loc))
                    for sub in node.body:
                        if len(items) >= max_items:
                            break
                        s0 = getattr(sub, "lineno", 0)
                        s1 = getattr(sub, "end_lineno", s0)
                        sloc = "[L%d-L%d]" % (s0, s1) if s1 > s0 else "[L%d]" % s0
                        if isinstance(sub, ast.FunctionDef):
                            items.append("    def %s() %s" % (sub.name, sloc))
                        elif isinstance(sub, ast.AsyncFunctionDef):
                            items.append("    async def %s() %s" % (sub.name, sloc))
                elif isinstance(node, ast.FunctionDef):
                    items.append("  def %s() %s" % (node.name, loc))
                elif isinstance(node, ast.AsyncFunctionDef):
                    items.append("  async def %s() %s" % (node.name, loc))
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            items.append("  %s = ... %s" % (target.id, loc))
                            break
        elif ext in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".kt", ".go", ".rs", ".swift", ".java"):
            pattern = re.compile(
                r"^(?:export\s+(?:default\s+)?)?(?:public\s+|private\s+|internal\s+)?(?:async\s+)?"
                r"(class|interface|type|enum|function|const|let|var|def|fun|fn|struct|impl|trait|object)\s+([A-Za-z0-9_$]+)"
            )
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[:3000]
            open_decl = None
            depth = 0
            for i, line in enumerate(lines, start=1):
                stripped = line.strip()
                if not stripped or stripped.startswith(("//", "/*", "*", "#")):
                    continue
                if open_decl is None and depth == 0:
                    m = pattern.match(stripped)
                    if m:
                        open_decl = {"kind": m.group(1), "name": m.group(2), "start": i, "is_export": "export" in stripped}
                depth += line.count("{") - line.count("}")
                if open_decl is not None and (depth <= 0 or ";" in line or (depth == 0 and "}" in line)):
                    end_l = i
                    loc = "[L%d-L%d]" % (open_decl["start"], end_l) if end_l > open_decl["start"] else "[L%d]" % open_decl["start"]
                    prefix = "export " if open_decl["is_export"] else ""
                    items.append("  %s%s %s %s" % (prefix, open_decl["kind"], open_decl["name"], loc))
                    open_decl = None
                    depth = max(0, depth)
                    if len(items) >= max_items:
                        break
        elif ext in (".md", ".markdown"):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, start=1):
                    if line.startswith("#"):
                        items.append("  %s [L%d]" % (line.strip()[:80], i))
                        if len(items) >= max_items:
                            break
    except Exception:
        pass
    if items:
        if len(items) >= max_items:
            items.append("  ... [more symbols truncated at %d items]" % max_items)
        return "\n".join(items)
    return "  (No top-level AST declarations detected)"


def _max_slices(line_cnt: int, base: int, cap: int) -> int:
    if line_cnt <= base * cap:
        return base
    return (line_cnt + cap - 1) // cap + 2


def handle_read(tool_input: dict, payload: dict, policy: dict) -> dict:
    target = str(tool_input.get("file_path") or "").strip()
    if not target:
        return _allow()
    cwd = H.workspace(payload)
    norm = H.normalize_path(target, cwd)
    low = norm.lower()

    if policy.get("block_image_reads", True) and low.endswith(H.IMAGE_EXTENSIONS):
        return _deny(
            "Zero Multimodal Poisoning Invariant: reading image `%s` is blocked to prevent context explosion (~3,000 tokens). "
            "Save images to an artifacts directory for the user, or set block_image_reads=false in guardrails.json when inspection is required." % os.path.basename(norm)
        )
    is_priv, base = H.is_privacy_blocked(norm)
    if is_priv:
        return _deny("Privacy-Block Gate (CK-02): reading credential file `%s` is blocked to prevent secret leakage." % base)
    scout = H.scout_blocked_dir(norm)
    if scout:
        return _deny("Scout-Block Gate (CK-01): traversing generated/vendor directory (%s) leaks tokens. Target source files instead." % scout)
    if not os.path.exists(norm):
        return _deny(
            "Pre-Verification Invariant: file does not exist: `%s`. Verify the path with Glob or Grep before reading to prevent retry loops." % norm
        )
    if os.path.isdir(norm):
        return _allow()

    basename = os.path.basename(norm).lower()
    if (
        "skill.md" in low
        or basename in ("task.md", "implementation_plan.md", "status.md", "manifest.md", "index.md", "agents.md", "claude.md", "readme.md", "plan.md", "gates.md")
        or H.is_harness_path(low)
    ):
        return _allow()

    offset = H.to_int(tool_input.get("offset"))
    limit_n = H.to_int(tool_input.get("limit"))
    is_slice = (offset is not None and offset > 0) or (limit_n is not None and limit_n > 0)
    start_l = offset if (offset is not None and offset > 0) else 1
    end_l = (start_l + limit_n - 1) if (limit_n is not None and limit_n > 0) else None

    line_cnt = H.count_lines(norm) if os.path.isfile(norm) else 0
    if line_cnt == 0:
        return _allow()

    ledger = H.load_state(payload, "reads", default={})
    if not isinstance(ledger, dict):
        ledger = {}
    entry = ledger.get(norm) or {}
    # external mutation detection
    try:
        cur_mtime = os.path.getmtime(norm)
    except Exception:
        cur_mtime = 0.0
    last_mtime = float(entry.get("last_read_mtime") or 0.0)
    if cur_mtime > 0 and last_mtime > 0 and cur_mtime > last_mtime:
        entry = {"edits_count": int(entry.get("edits_count", 0)) + 1, "last_read_mtime": cur_mtime}
        ledger[norm] = entry
        H.save_state(payload, "reads", ledger)

    total_reads = int(entry.get("total_reads", 0))
    whole_reads = int(entry.get("whole_reads", 0))
    edits_count = int(entry.get("edits_count", 0))
    reads_since_edit = int(entry.get("reads_since_edit", 0))
    read_count = int(entry.get("read_count", 0))
    slices = [tuple(s) for s in entry.get("file_slices", []) if isinstance(s, (list, tuple)) and len(s) == 2]

    read_once = int(policy.get("read_once_threshold", 200))
    slice_cap = int(policy.get("slice_cap", 250))
    outline_threshold = int(policy.get("outline_threshold", 400))
    base_max_slices = int(policy.get("max_slices", 6))

    if line_cnt <= read_once and is_slice and whole_reads == 0 and total_reads == 0 and edits_count == 0:
        return _deny(
            "Read-Once Policy Invariant: `%s` has %d lines (<= %d). Micro-slicing small files on first read is blocked; "
            "read the whole file once without offset/limit." % (os.path.basename(norm), line_cnt, read_once)
        )

    updated = None
    if is_slice and end_l is None:
        end_l = line_cnt
    if is_slice and line_cnt > read_once and end_l is not None and (end_l - start_l + 1) > slice_cap:
        span = end_l - start_l + 1
        if span <= slice_cap + 10 or limit_n is None:
            end_l = min(line_cnt, start_l + slice_cap - 1) if start_l <= line_cnt else start_l + slice_cap - 1
            updated = {"file_path": target, "offset": start_l, "limit": end_l - start_l + 1}
        else:
            return _deny(
                "Token Economy Invariant: slice window (%d lines) on `%s` exceeds the %d-line maximum. Narrow the window to the target symbol." % (span, os.path.basename(norm), slice_cap)
            )

    if not is_slice and line_cnt > outline_threshold:
        skeleton = _extract_inline_ast_skeleton(norm)
        reason = (
            "Outline-First Monolithic File Guard: `%s` has %s total lines (> %d). Whole-file reading is blocked to prevent context bloat. "
            "Locate target coordinates first (Grep -n, codegraph:symbol_lookup / extract_symbols / summarize_path), then read a targeted slice "
            "(offset + limit <= %d lines)." % (os.path.basename(norm), format(line_cnt, ","), outline_threshold, slice_cap)
        )
        if skeleton:
            reason += "\n\nInline AST Symbol Skeleton for `%s` (%s lines):\n%s\nRead your target symbol with Read(file_path, offset, limit)." % (
                os.path.basename(norm), format(line_cnt, ","), skeleton
            )
        return _deny(reason)

    if not is_slice:
        effective = reads_since_edit if edits_count > 0 else total_reads
        if effective >= int(policy.get("unedited_read_ceiling", 8)):
            return _deny(
                "Active Loop Breaker ACTIVATED: `%s` has been read %d times without intermediate edits. Further reads are blocked; "
                "use Grep -n for specific identifiers or codegraph:symbol_lookup instead." % (os.path.basename(norm), effective)
            )

    if is_slice and end_l is not None:
        cur = (start_l, end_l)
        prior = list(slices)
        is_dup = False
        len_cur = end_l - start_l + 1
        for ps in prior:
            inter = max(0, min(end_l, ps[1]) - max(start_l, ps[0]) + 1)
            if ps == cur or (inter > 0 and (inter / max(len_cur, ps[1] - ps[0] + 1)) >= 0.8):
                is_dup = True
                break
        max_slices = _max_slices(line_cnt, base_max_slices, slice_cap)
        if is_dup or len(slices) >= max_slices:
            return _deny(
                "Slice Loop Breaker ACTIVATED: `%s` already had %d sliced reads (%s). Further slicing is blocked; never read sequentially. "
                "Use codegraph:extract_symbols, Grep -n for identifiers, or codegraph:symbol_lookup." % (
                    os.path.basename(norm), len(slices), "duplicate slice loop" if is_dup else "reached %d-slice ceiling" % max_slices
                )
            )

    if whole_reads >= int(policy.get("whole_read_ceiling", 2)) and not is_slice:
        return _deny(
            "Edit-Reset Loop Dampening ACTIVATED (Three-Strike Rule): `%s` was read whole %d times this session. Re-reading the entire file is blocked; "
            "use Grep -n or a targeted slice (<= %d lines)." % (os.path.basename(norm), whole_reads, slice_cap)
        )
    if read_count >= int(policy.get("read_strike_limit", 3)) and not is_slice:
        return _deny(
            "Three-Strike Rule ACTIVATED: `%s` was read %d times without intermediate modifications. Re-reading is blocked; "
            "use Grep -n, a targeted slice, codegraph:summarize_path, or codegraph:callers_callees." % (os.path.basename(norm), read_count)
        )

    return _allow(updated)


# ---------------------------------------------------------------------------
# Grep / Glob
# ---------------------------------------------------------------------------

def handle_search(tool_name: str, tool_input: dict, payload: dict, policy: dict) -> dict:
    cwd = H.workspace(payload)
    path = str(tool_input.get("path") or "").strip()
    if path:
        norm = H.normalize_path(path, cwd)
        scout = H.scout_blocked_dir(norm)
        if scout:
            return _deny("Scout-Block Gate (CK-01): searching generated/vendor directory (%s) leaks tokens. Target source directories instead." % scout)
        low = norm.lower().rstrip("/")
        for blocked in H.BLOCKED_LIST_DIRS:
            if low.endswith(blocked) or (blocked + "/") in low:
                return _deny(
                    "Token Economy Invariant: listing dependency/cache directory (`%s`) is blocked (~5,000-50,000 tokens). "
                    "Inspect configuration manifests instead." % os.path.basename(norm)
                )
    if tool_name == "Grep":
        mode = str(tool_input.get("output_mode") or "files_with_matches")
        head = H.to_int(tool_input.get("head_limit"))
        limit = int(policy.get("flood_limit", 50))
        if mode == "content" and (head is None or head <= 0 or head > limit * 4):
            updated = dict(tool_input)
            updated["head_limit"] = limit
            return _allow(updated, context="Harness: Grep head_limit set to %d (SWE-agent search flood guard)." % limit)
    return _allow()


# ---------------------------------------------------------------------------
# Edit / Write / MultiEdit
# ---------------------------------------------------------------------------

def _edits_of(tool_name: str, tool_input: dict) -> list:
    """Normalize to a list of (old, new, replace_all)."""
    if tool_name == "Edit":
        return [(str(tool_input.get("old_string") or ""), str(tool_input.get("new_string") or ""), bool(tool_input.get("replace_all")))]
    if tool_name == "MultiEdit":
        out = []
        for e in tool_input.get("edits") or []:
            if isinstance(e, dict):
                out.append((str(e.get("old_string") or ""), str(e.get("new_string") or ""), bool(e.get("replace_all"))))
        return out
    if tool_name == "NotebookEdit":
        return [("", str(tool_input.get("new_source") or ""), False)]
    return []


def _simulate_mutation(tool_name: str, tool_input: dict, target: str) -> Optional[str]:
    try:
        if tool_name == "Write":
            content = tool_input.get("content")
            return content if isinstance(content, str) else None
        if tool_name in ("Edit", "MultiEdit"):
            if not os.path.isfile(target):
                return None
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
            for old, new, replace_all in _edits_of(tool_name, tool_input):
                if not old or old not in text:
                    return None
                text = text.replace(old, new) if replace_all else text.replace(old, new, 1)
            return text
    except Exception:
        return None
    return None


def _strip_json_comments(content: str) -> str:
    pattern = re.compile(r'("(?:\\.|[^"\\])*")|//[^\r\n]*|/\*[\s\S]*?\*/')
    content = pattern.sub(lambda m: m.group(1) if m.group(1) is not None else "", content)
    return re.sub(r",\s*([}\]])", r"\1", content)


def _validate_syntax(target: str, simulated: str) -> Optional[dict]:
    if not simulated or not simulated.strip():
        return None
    filename = os.path.basename(target)
    ext = os.path.splitext(target)[1].lower()
    err = None
    try:
        if ext == ".py":
            try:
                ast.parse(simulated, filename=target)
            except SyntaxError as e:
                err = "line %s, col %s: %s" % (e.lineno, e.offset, e.msg)
        elif ext in (".json", ".jsonc"):
            is_jsonc = ext == ".jsonc" or filename.lower().startswith("tsconfig") or ".vscode" in target.lower() or filename.lower() == "settings.json"
            try:
                json.loads(_strip_json_comments(simulated) if is_jsonc else simulated)
            except json.JSONDecodeError as e:
                err = "%s at line %s col %s" % (e.msg, e.lineno, e.colno)
        elif ext in (".yaml", ".yml"):
            try:
                import yaml  # type: ignore
                yaml.safe_load(simulated)
            except ImportError:
                pass
            except Exception as e:
                err = str(e).strip()[:300]
        elif ext == ".toml":
            try:
                try:
                    import tomllib  # type: ignore
                except ImportError:
                    import tomli as tomllib  # type: ignore
                tomllib.loads(simulated)
            except ImportError:
                pass
            except Exception as e:
                err = str(e).strip()[:300]
        elif ext in (".sh", ".bash"):
            res = subprocess.run(["bash", "-n"], input=simulated, text=True, capture_output=True, timeout=2)
            if res.returncode != 0:
                err = (res.stderr or res.stdout or "").strip()[:300]
    except Exception:
        return None
    if err:
        return _deny("Pre-Edit Linter Gate (SWE-agent ACI): syntax error in simulated edit to %s: %s. Fix syntax in-flight before writing to disk." % (filename, err))
    return None


def _fuzzy_old_string(target_norm: str, tool_input: dict) -> Optional[dict]:
    """Aider-style old_string verification with whitespace-drift auto-repair."""
    old = tool_input.get("old_string")
    if not isinstance(old, str) or not old.strip() or not os.path.isfile(target_norm):
        return None
    try:
        with open(target_norm, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception:
        return None
    if not text:
        return None
    text = text.replace("\r\n", "\n")
    norm_old = old.replace("\r\n", "\n")
    filename = os.path.basename(target_norm)
    if norm_old in text:
        count = text.count(norm_old)
        if count > 1 and not tool_input.get("replace_all"):
            occ = []
            pos = 0
            n_lines = len(norm_old.splitlines())
            while True:
                idx = text.find(norm_old, pos)
                if idx == -1:
                    break
                s_line = text[:idx].count("\n") + 1
                occ.append("[%d, %d]" % (s_line, s_line + max(0, n_lines - 1)))
                pos = idx + len(norm_old)
            return _deny(
                "Pre-Edit Uniqueness Gate (Aider ACI): old_string occurs %d times in %s at line ranges %s. "
                "Include more surrounding context to make it unique, or set replace_all=true." % (count, filename, ", ".join(occ))
            )
        return None

    file_lines = text.splitlines(keepends=True)
    total = len(file_lines)
    old_lines = norm_old.splitlines(keepends=True)
    tc_count = max(1, len(old_lines))
    tc_stripped = [l.strip() for l in old_lines if l.strip()]
    if tc_stripped and total >= tc_count:
        matches = []
        for i in range(total - tc_count + 1):
            cand = file_lines[i:i + tc_count]
            if [l.strip() for l in cand if l.strip()] == tc_stripped:
                matches.append((i + 1, i + tc_count, "".join(cand)))
        if len(matches) == 1:
            c_text = matches[0][2]
            if norm_old.endswith("\n") is False and c_text.endswith("\n"):
                c_text = c_text[:-1]
            updated = dict(tool_input)
            updated["old_string"] = c_text
            return _allow(updated, context="Harness: old_string whitespace/indentation drift auto-reconciled to disk state (lines %d-%d)." % (matches[0][0], matches[0][1]))
        if len(matches) > 1:
            return _deny(
                "Pre-Edit Fuzzy Match Gate (Aider ACI): old_string not found verbatim in %s but matches %d locations modulo whitespace (%s). "
                "Copy the exact text from one location." % (filename, len(matches), ", ".join("lines %d-%d" % (m[0], m[1]) for m in matches[:5]))
            )

    old_stripped_lines = [l.strip() for l in old_lines]
    if total <= tc_count:
        best_start, best_end, best_text = 1, total, "".join(file_lines)
        pct = int(difflib.SequenceMatcher(None, norm_old, best_text).ratio() * 100)
    else:
        best_sim, best_start, best_end, best_text = -1.0, 1, tc_count, "".join(file_lines[:tc_count])
        for i in range(total - tc_count + 1):
            cand = file_lines[i:i + tc_count]
            sim = difflib.SequenceMatcher(None, old_stripped_lines, [l.strip() for l in cand]).ratio()
            if sim > best_sim:
                best_sim, best_start, best_end, best_text = sim, i + 1, i + tc_count, "".join(cand)
        pct = int(max(best_sim, difflib.SequenceMatcher(None, norm_old, best_text).ratio()) * 100)
    return _deny(
        "Pre-Edit Fuzzy Match Gate (Aider ACI): old_string not found in %s. Closest match is at lines %d-%d (similarity %d%%):\n```\n%s\n```\n"
        "Update old_string to match disk state without re-reading the whole file." % (filename, best_start, best_end, pct, best_text.rstrip())
    )


def _check_recon_precondition(target_norm: str, payload: dict) -> Optional[dict]:
    if os.path.basename(target_norm).lower() != "implementation_plan.md" or os.path.exists(target_norm):
        return None
    if H.is_test_env() and os.environ.get("CLAUDE_HARNESS_ENFORCE_RECON_GATE") != "1":
        return None
    events = H.iter_events(payload, tail=2000)
    for ev in events:
        tool = str(ev.get("tool") or "")
        if tool in ("Read", "Grep", "Glob", "WebFetch", "WebSearch"):
            return None
        if tool == "Agent" and ("explor" in str(ev.get("subagent_type") or "").lower() or "research" in str(ev.get("subagent_type") or "").lower()):
            return None
        if tool.startswith("mcp__") and any(s in tool for s in ("codegraph", "context7", "codex_knowledge")):
            return None
        if tool in H.SHELL_TOOLS and re.search(r"\b(?:rg|fd|eza|git|bat|ls|cat)\b", str(ev.get("command") or "")):
            return None
    if not events and not os.environ.get("CLAUDE_HARNESS_ENFORCE_RECON_GATE"):
        return None
    return _deny(
        "Agentic IR Reconnaissance Pre-Condition: explore the codebase or ground truth (Read, Grep, codegraph, context7, an explorer subagent) "
        "before authoring implementation_plan.md."
    )


def _check_suppression_injection(target_norm: str, tool_name: str, tool_input: dict) -> Optional[dict]:
    name = os.path.basename(target_norm)
    if tool_name == "Write":
        new_content = str(tool_input.get("content") or "")
        try:
            with open(target_norm, "r", encoding="utf-8", errors="ignore") as f:
                disk = f.read()
        except Exception:
            return None
        if len(_SUPPRESSION_RE.findall(new_content)) > len(_SUPPRESSION_RE.findall(disk)):
            return _deny("Specification-Gaming Lock: injecting linter/type-checker suppressions (@ts-ignore, type: ignore, eslint-disable, noqa) is forbidden in `%s`." % name)
        return None
    tot_old = tot_new = 0
    for old, new, _ in _edits_of(tool_name, tool_input):
        tot_old += len(_SUPPRESSION_RE.findall(old))
        tot_new += len(_SUPPRESSION_RE.findall(new))
    if tot_new > tot_old:
        return _deny("Specification-Gaming Lock: injecting linter/type-checker suppressions (@ts-ignore, type: ignore, eslint-disable, noqa) is forbidden in `%s`." % name)
    return None


def _extract_literal_assertions(text: str) -> list:
    pairs = []
    for line in text.splitlines():
        m = _ASSERT_EQ_RE.search(line) or _SELF_ASSERT_EQ_RE.search(line) or _EXPECT_BE_RE.search(line)
        if m:
            pairs.append((m.group(1).strip(), m.group(2).strip()))
    return pairs


def _semantic_assertion_drift(old: str, new: str) -> Optional[str]:
    if not old or not new:
        return None
    t_asserts = len(_ASSERT_LINE_RE.findall(old))
    r_asserts = len(_ASSERT_LINE_RE.findall(new))
    if t_asserts == 0 or r_asserts < t_asserts:
        return None
    strict = re.compile(r"(?:==|\.assertEqual\s*\(|\.toBe\s*\(|\.toEqual\s*\()")
    weak = re.compile(r"(?:\bis\s+not\s+None\b|\.assertIsNotNone\s*\(|\.toBeDefined\s*\(|\.toBeTruthy\s*\()")
    if len(strict.findall(old)) > 0 and len(strict.findall(new)) < len(strict.findall(old)) and len(weak.findall(new)) > len(weak.findall(old)):
        return "Semantic Oracle Custody Lock: weakening strict equality assertions into loose existence checks is forbidden without an Oracle-Custody-Lease."
    t_pairs = dict(_extract_literal_assertions(old))
    r_pairs = dict(_extract_literal_assertions(new))
    for lhs, lit in t_pairs.items():
        if lhs in r_pairs and r_pairs[lhs] != lit:
            return "Semantic Oracle Custody Lock: mutating expected assertion literals to match altered code output is forbidden without 'Oracle-Custody-Lease: UPDATE_ASSERTIONS'."
    return None


def _has_oracle_custody_lease(payload: dict, ws: str) -> bool:
    if os.environ.get("ORACLE_CUSTODY_LEASE") == "1":
        return True
    marker = "Oracle-Custody-Lease: UPDATE_ASSERTIONS"
    lease = H.lease_for(payload)
    if marker in str(lease.get("prompt") or ""):
        return True
    for cand in (os.path.join(ws, "implementation_plan.md"), os.path.join(ws, ".claude", "harness", "implementation_plan.md")):
        try:
            if os.path.isfile(cand):
                with open(cand, "r", encoding="utf-8", errors="ignore") as f:
                    if marker in f.read():
                        return True
        except Exception:
            pass
    return False


def _check_test_locks(target_norm: str, tool_name: str, tool_input: dict, role: str, payload: dict, ws: str) -> Optional[dict]:
    name = os.path.basename(target_norm)
    if role == "debugger" or os.environ.get("FIX_CODE_ONLY") == "1":
        return _deny(
            "Fix-The-Code-Not-The-Test Invariant: role '%s' is forbidden from mutating existing test file `%s`. Fix the application code, not the assertions." % (role or "debugger", name)
        )
    if role not in ("dev-fe", "dev-be", "frontend", "visual-engineer", "designer"):
        return None
    has_lease = _has_oracle_custody_lease(payload, ws)
    pairs = []
    if tool_name == "Write":
        try:
            with open(target_norm, "r", encoding="utf-8", errors="ignore") as f:
                pairs = [(f.read(), str(tool_input.get("content") or ""))]
        except Exception:
            return None
    else:
        pairs = [(o, n) for o, n, _ in _edits_of(tool_name, tool_input)]
    for old, new in pairs:
        if not has_lease:
            if len(_ASSERT_LINE_RE.findall(new)) < len(_ASSERT_LINE_RE.findall(old)):
                return _deny(
                    "Fix-The-Code-Not-The-Test Invariant: role '%s' may not delete or weaken existing assert/expect lines in `%s`. "
                    "Net-new tests are allowed; existing assertions are immutable without an Oracle-Custody-Lease." % (role, name)
                )
            drift = _semantic_assertion_drift(old, new)
            if drift:
                return _deny(drift)
        if len(_TEST_SKIP_RE.findall(new)) > len(_TEST_SKIP_RE.findall(old)):
            return _deny("Test-Immutability Lock: adding .skip / @pytest.mark.skip to bypass failing tests is forbidden in `%s`." % name)
        if len(_TAUTOLOGICAL_ASSERT_RE.findall(new)) > len(_TAUTOLOGICAL_ASSERT_RE.findall(old)):
            return _deny("Test-Immutability Lock: tautological assertions (assert True / expect(true).toBe(true)) are forbidden in `%s`." % name)
        if len(_ZERO_EXIT_RE.findall(new)) > len(_ZERO_EXIT_RE.findall(old)):
            return _deny("Test-Immutability Lock (CATCH Execution Interference): injecting early zero-exit calls to spoof test passes is forbidden in `%s`." % name)
    return None


def _extract_ts_exports(content: str) -> set:
    exports = set()
    for m in re.finditer(r"export\s*\{([^}]+)\}", content):
        for item in m.group(1).split(","):
            item = item.strip()
            if item.startswith("type "):
                item = item[5:].strip()
            if " as " in item:
                item = item.split(" as ")[1].strip()
            if item:
                exports.add(item)
    for m in re.finditer(r"export\s+(?:declare\s+)?(?:async\s+)?(?:const|let|var|function\*?|class|interface|type|enum)\s+([A-Za-z0-9_$]+)", content):
        exports.add(m.group(1))
    if re.search(r"export\s+default\b", content):
        exports.add("default")
    return exports


def _find_package_root(start_dir: str, ws: str) -> str:
    curr = start_dir
    ws_norm = os.path.normpath(ws)
    while True:
        if os.path.isfile(os.path.join(curr, "package.json")) or os.path.isfile(os.path.join(curr, "tsconfig.json")):
            return curr
        if curr == ws_norm or curr == os.path.dirname(curr):
            break
        curr = os.path.dirname(curr)
    return ws_norm


def _resolve_local_import(import_path: str, target_norm: str, ws: str) -> tuple:
    base_dir = os.path.dirname(target_norm)
    if import_path.startswith(("./", "../")):
        raw = os.path.normpath(os.path.join(base_dir, import_path))
    elif import_path.startswith("@/"):
        pkg_root = _find_package_root(base_dir, ws)
        src = os.path.join(pkg_root, "src")
        raw = os.path.normpath(os.path.join(src if os.path.isdir(src) else pkg_root, import_path[2:]))
    else:
        return "", []
    cands = []
    if os.path.isfile(raw):
        cands.append(raw)
    if raw.endswith(".js"):
        for ext in (".ts", ".tsx"):
            if os.path.isfile(raw[:-3] + ext):
                cands.append(raw[:-3] + ext)
    for ext in (".ts", ".tsx", ".d.ts", ".js", ".jsx", ".mjs", ".cjs", ".json"):
        if os.path.isfile(raw + ext):
            cands.append(raw + ext)
        if os.path.isfile(os.path.join(raw, "index" + ext)):
            cands.append(os.path.join(raw, "index" + ext))
    return raw, cands


def _verify_imports_shift_left(target_norm: str, tool_name: str, tool_input: dict, ws: str, allowed_files: list) -> Optional[dict]:
    try:
        ext = os.path.splitext(target_norm)[1].lower()
        if ext not in (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"):
            return None
        if H.is_harness_path(target_norm.lower()):
            return None
        proposed = ""
        existing = ""
        if tool_name == "Write":
            proposed = str(tool_input.get("content") or "")
        else:
            parts = _edits_of(tool_name, tool_input)
            proposed = "\n".join(n for _, n, _ in parts)
            existing = "\n".join(o for o, _, _ in parts)
        if not proposed:
            return None
        import_re = re.compile(r"(?:import|export)\s+(?:type\s+)?(\{[\s\S]*?\}|[A-Za-z0-9_$,\s*]+)\s+from\s+['\"]([^'\"]+)['\"]")
        side_re = re.compile(r"import\s+['\"]([^'\"]+)['\"]")
        found = [(m.group(0).strip(), m.group(1).strip(), m.group(2).strip()) for m in import_re.finditer(proposed)]
        for m in side_re.finditer(proposed):
            if not any(x[2] == m.group(1).strip() for x in found):
                found.append((m.group(0).strip(), "", m.group(1).strip()))
        for stmt, clause, import_path in found:
            if not import_path.startswith(("./", "../", "@/")):
                continue
            if existing and stmt in existing:
                continue
            raw, cands = _resolve_local_import(import_path, target_norm, ws)
            if not raw:
                continue
            if not cands:
                probes = [raw, raw + ".ts", raw + ".tsx", raw + ".js", raw + ".jsx", os.path.join(raw, "index.ts"), os.path.join(raw, "index.tsx")]
                if allowed_files and any(H.matches_allowed_file(p, pat, ws) for pat in allowed_files for p in probes):
                    continue
                return _deny(
                    "Shift-Left AST Import Guard: imported local module '%s' cannot be resolved on disk (checked '%s') and is not in the allowed_files lease. "
                    "Verify the path or obtain a lease before importing uncreated modules." % (import_path, os.path.relpath(raw, ws))
                )
            if "{" in clause and "}" in clause:
                brace = re.search(r"\{([^}]+)\}", clause)
                if not brace:
                    continue
                symbols = []
                for tok in brace.group(1).split(","):
                    tok = tok.strip()
                    if tok.startswith("type "):
                        tok = tok[5:].strip()
                    orig = tok.split(" as ")[0].strip() if " as " in tok else tok
                    if orig and orig not in symbols:
                        symbols.append(orig)
                if not symbols:
                    continue
                try:
                    with open(cands[0], "r", encoding="utf-8", errors="ignore") as f:
                        target_content = f.read(200_000)
                except Exception:
                    continue
                if re.search(r"\bexport\s+\*", target_content):
                    continue
                exports = _extract_ts_exports(target_content)
                barrel = os.path.join(os.path.dirname(cands[0]), "index.ts")
                if os.path.isfile(barrel) and barrel != cands[0]:
                    try:
                        with open(barrel, "r", encoding="utf-8", errors="ignore") as bf:
                            bc = bf.read(200_000)
                        if re.search(r"\bexport\s+\*", bc):
                            continue
                        exports.update(_extract_ts_exports(bc))
                    except Exception:
                        pass
                for sym in symbols:
                    if sym in exports or (existing and sym in existing):
                        continue
                    if not re.search(r"\b" + re.escape(sym) + r"\b", target_content):
                        return _deny(
                            "Shift-Left AST Symbol Guard: symbol '%s' is not exported by '%s'. Verified exports: %s" % (
                                sym, os.path.relpath(cands[0], ws), sorted(exports)[:15]
                            )
                        )
    except Exception:
        return None
    return None


def _maybe_shadow_checkpoint(ws: str, payload: dict) -> None:
    try:
        if H.is_test_env() and not os.environ.get("CLAUDE_HARNESS_TEST_SHADOW_CKPT"):
            return
        root = H.root_session_dir(payload)
        ckpt = root / "shadow_ckpt.json"
        if ckpt.is_file():
            return
        res = subprocess.run(["git", "-C", ws, "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True, timeout=1.0, check=False)
        if res.returncode != 0 or res.stdout.strip() != "true":
            return
        head = subprocess.run(["git", "-C", ws, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=1.0, check=False)
        stash = subprocess.run(["git", "-C", ws, "stash", "create"], capture_output=True, text=True, timeout=1.5, check=False)
        H.atomic_json_write(ckpt, {
            "session_id": H.session_id(payload),
            "timestamp": time.time(),
            "workspace": ws,
            "head_sha": head.stdout.strip() if head.returncode == 0 else "",
            "stash_sha": stash.stdout.strip() if stash.returncode == 0 else "",
        })
    except Exception:
        pass


def handle_mutation(tool_name: str, tool_input: dict, payload: dict, policy: dict) -> dict:
    target = H.target_file_of(tool_name, tool_input)
    if not target:
        return _allow()
    ws = H.workspace(payload)
    norm = H.normalize_path(target, ws)
    low = norm.lower()
    role = H.role_of(payload)
    name = os.path.basename(norm)

    is_priv, priv_base = H.is_privacy_blocked(norm)
    if is_priv and tool_name == "Write":
        return _ask("Privacy-Block Gate (CK-02): writing credential file `%s` requires explicit user confirmation." % priv_base)

    # Hook immunity: builders/debuggers never mutate the harness hooks
    if ("/.claude/hooks/" in low or "/hooks/" in low and H.is_harness_path(low)) and role in ("meta-invariant-editor", "meta-domain-editor", "debugger", "dev-fe", "dev-be"):
        return _deny(
            "Hook Immunity Invariant: role '%s' may not mutate core harness hooks (`%s`). Core hook modifications are reserved for authorized system updates." % (role, name)
        )

    is_md_like = low.endswith((".md", ".txt", ".markdown"))
    if os.path.isfile(norm) and role in ("dev-fe", "dev-be") and not is_md_like:
        supp = _check_suppression_injection(norm, tool_name, tool_input)
        if supp:
            return supp
    if os.path.isfile(norm) and H.is_test_file(norm):
        lock = _check_test_locks(norm, tool_name, tool_input, role, payload, ws)
        if lock:
            return lock
    if name.lower() == "implementation_plan.md":
        recon = _check_recon_precondition(norm, payload)
        if recon:
            return recon

    if is_md_like or ".claude/harness/" in low:
        return _allow()

    is_app = H.is_app_code(norm, ws)
    allowed_files: list = []
    if is_app:
        if H.is_non_builder_role(role):
            if role == H.ROOT_ROLE:
                if not policy.get("root_may_edit_code"):
                    return _deny(
                        "PM / Orchestrator Zero-Code-Write Invariant (pm-no-implementation): the root orchestrator must never directly mutate application source "
                        "(`%s`). Delegate via the Agent tool to a builder subagent (dev-fe / dev-be / debugger) with an `allowed_files:` lease. "
                        "Override: set root_may_edit_code=true in .claude/harness/guardrails.json or CLAUDE_HARNESS_ROOT_BUILDER=1." % name
                    )
            else:
                return _deny(
                    "Role Isolation Invariant (BMAD / pm-no-implementation): non-builder subagent role (`%s`) must not mutate application source (`%s`). "
                    "Route the change back to the orchestrator to dispatch a builder (dev-fe / dev-be / debugger)." % (role, name)
                )
        lease = H.lease_for(payload)
        if lease.get("has_allowed_files"):
            allowed_files = list(lease.get("allowed_files") or [])
            if not any(H.matches_allowed_file(norm, pat, ws) for pat in allowed_files):
                return _deny(
                    "Story Shard File Lease Violation (BMAD): `%s` is outside this subagent's leased allowed_files %s. "
                    "Report back to the orchestrator to expand the lease before touching unleased files." % (name, allowed_files)
                )

    effective = tool_input
    fuzzy_payload = None
    if tool_name == "Edit":
        fuzzy = _fuzzy_old_string(norm, tool_input)
        if fuzzy:
            if fuzzy.get("decision") == "deny":
                return fuzzy
            if fuzzy.get("updatedInput"):
                fuzzy_payload = fuzzy
                effective = fuzzy["updatedInput"]

    simulated = _simulate_mutation(tool_name, effective, norm)
    if simulated is not None:
        syntax_deny = _validate_syntax(norm, simulated)
        if syntax_deny:
            return syntax_deny

    if is_app:
        _maybe_shadow_checkpoint(ws, payload)
        import_deny = _verify_imports_shift_left(norm, tool_name, effective, ws, allowed_files)
        if import_deny:
            return import_deny

    if fuzzy_payload:
        return fuzzy_payload
    return _allow()


# ---------------------------------------------------------------------------
# Agent (subagent dispatch)
# ---------------------------------------------------------------------------

def handle_agent(tool_input: dict, payload: dict, policy: dict) -> dict:
    subagent_type = str(tool_input.get("subagent_type") or "").strip()
    prompt = str(tool_input.get("prompt") or "")
    model = str(tool_input.get("model") or "").strip().lower()
    role = subagent_type.lower()
    role = H.BUILTIN_AGENT_ALIASES.get(role, role)

    if H.is_subagent(payload):
        lease = H.lease_for(payload)
        if not lease.get("allow_nested_agents"):
            return _deny(
                "Subagent Recursion Depth Violation (max_depth = 1): child subagents may not spawn nested subagents. "
                "Return findings to the parent orchestrator instead (grant `allow_define_subagent` in the lease to override)."
            )

    limit = int(policy.get("subagent_prompt_limit", 6000))
    if len(prompt) > limit:
        return _deny(
            "Pub/Sub Sparsification Invariant: Agent prompt length (%s chars) exceeds the %s-character ceiling. Pass compact Story Shards / file coordinates, "
            "and write large stack traces or specs to a scratch file referenced by path." % (format(len(prompt), ","), format(limit, ","))
        )

    if role in LEASE_REQUIRED_ROLES and "allowed_files" not in prompt:
        return _deny(
            "BMAD Story Shard Lease Invariant: builder subagent ('%s') invoked without an `allowed_files:` lease block in the prompt. "
            "Specify `allowed_files:` (paths, globs, or `[]` for a read-only probe)." % subagent_type
        )

    if model:
        req = H.model_tier_rank(model)
        base = H.MODEL_TIER_RANKS[H.baseline_tier(role)]
        if req is not None and req > base:
            return _ask(
                "Subagent Model Escalation Gate: role '%s' is assigned baseline model tier '%s' but the orchestrator requested stronger model '%s'. "
                "User confirmation is required before escalating a subagent." % (subagent_type, H.baseline_tier(role), model)
            )

    H.record_lease(payload, subagent_type, prompt)
    return _allow()


# ---------------------------------------------------------------------------
# MCP
# ---------------------------------------------------------------------------

def handle_mcp(tool_name: str, payload: dict) -> dict:
    server, bare = H.mcp_server_and_tool(tool_name)
    if not bare:
        return _allow()
    role = H.role_of(payload)
    if H.is_subagent(payload) and H.is_readonly_role(role) and role not in ("doc-sync-worker", "librarian"):
        if bare.lower() in _MUTATING_MCP_TOOLS or _MUTATING_MCP_VERB_RE.search(bare.lower()):
            return _deny(
                "Read-Only Subagent MCP Mutation Lock: role '%s' is read-only and may not invoke mutating MCP tool `%s` on server `%s`." % (role, bare, server)
            )
    return _allow()


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def decide(payload: dict) -> dict:
    tool_name = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except Exception:
            tool_input = {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    policy = H.guardrail_policy(H.workspace(payload))

    loop_deny = track_and_check_loop(payload, tool_name, tool_input)
    if loop_deny:
        return loop_deny

    if tool_name in H.SHELL_TOOLS:
        stagnation = check_error_stagnation(payload)
        if stagnation:
            return stagnation
        return handle_bash(tool_input, payload, policy)
    if tool_name in H.READ_TOOLS:
        return handle_read(tool_input, payload, policy)
    if tool_name in H.SEARCH_TOOLS:
        return handle_search(tool_name, tool_input, payload, policy)
    if tool_name in H.MUTATION_TOOLS:
        return handle_mutation(tool_name, tool_input, payload, policy)
    if tool_name in H.AGENT_TOOLS:
        return handle_agent(tool_input, payload, policy)
    if tool_name.startswith("mcp__"):
        return handle_mcp(tool_name, payload)
    return _allow()


def to_hook_output(res: dict, payload: dict, tool_name: str, tool_input: dict) -> dict:
    decision = res.get("decision", "allow")
    reason = str(res.get("reason") or "")
    if decision == "deny":
        _record_denial(payload, tool_name, reason, tool_input)
        _forget_denied_action(payload)
        return H.pre_tool_deny(reason)
    if decision == "ask":
        return H.pre_tool_ask(reason)
    return H.pre_tool_allow(res.get("updatedInput"), str(res.get("context") or ""))


def _forget_denied_action(payload: dict) -> None:
    """A denied call never executed: drop it from the Jev ledger so a corrected retry is not mis-counted as a loop."""
    try:
        actions = H.load_state(payload, "actions", default=[])
        if isinstance(actions, list) and actions:
            H.save_state(payload, "actions", actions[:-1])
    except Exception:
        pass


def _record_denial(payload: dict, tool_name: str, reason: str, tool_input: dict) -> None:
    r = reason.lower()
    if "jev" in r:
        ft, tier, vertex = "jev_loop", "S0_catastrophic", "skill"
    elif "hook immunity" in r:
        ft, tier, vertex = "hook_immunity_violation", "S0_catastrophic", "hook"
    elif "fix-the-code-not-the-test" in r or "test-immutability" in r or "custody lock" in r:
        ft, tier, vertex = "test_lock_violation", "S1_critical", "codebase"
    elif "three-strike" in r:
        ft, tier, vertex = "read_budget_lock", "S2_major", "tool_guidance"
    elif "slice loop breaker" in r:
        ft, tier, vertex = "slice_loop_breaker", "S2_major", "tool_guidance"
    elif "lease" in r or "allowed_files" in r:
        ft, tier, vertex = "lease_violation", "S2_major", "skill"
    elif "ceiling" in r and "prompt" in r:
        ft, tier, vertex = "subagent_prompt_overflow", "S2_major", "routing"
    elif "flood" in r:
        ft, tier, vertex = "flood_guard", "S3_minor", "tool_guidance"
    elif "legacy" in r:
        ft, tier, vertex = "legacy_cli_blocked", "S3_minor", "tool_guidance"
    elif "slice" in r or "-line maximum" in r:
        ft, tier, vertex = "slice_cap_exceeded", "S3_minor", "tool_guidance"
    elif "does not exist" in r:
        return
    else:
        ft, tier, vertex = "tool_denial", "S3_minor", "tool_guidance"
    H.record_harness_failure(payload, ft, reason, tool_name=tool_name, details=json.dumps(tool_input, default=str)[:500], severity_tier=tier, vertex=vertex)


def main() -> None:
    try:
        payload = H.read_payload()
        if not payload:
            H.emit(H.pre_tool_allow())
            return
        tool_name = str(payload.get("tool_name") or "")
        tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
        res = decide(payload)
        H.emit(to_hook_output(res, payload, tool_name, tool_input))
    except Exception:
        # Fail-safe: never block the agent on internal hook errors.
        H.emit(H.pre_tool_allow())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Shared runtime library for the Claude Code SOTA Harness hooks.

Every hook in this directory imports this module. It owns:

* payload parsing and Claude Code hook output envelopes,
* the per-session state ledger (actions, reads, events, mutations, flags),
* role / lease resolution for subagents (``agent_type`` + ``allowed_files``),
* path helpers, guardrail policy loading, failure telemetry,
* a tolerant reader for Claude Code JSONL transcripts.

The module must stay importable on the host's system ``python3`` (3.9+): no
``match`` statements, no ``tomllib`` hard dependency, no ``X | Y`` at runtime.
"""
from __future__ import annotations

import fcntl
import fnmatch
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

HARNESS_VERSION = "1.0.0-claude"

# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

HOOKS_DIR = Path(__file__).resolve().parent


def is_test_env() -> bool:
    return "unittest" in sys.modules or "pytest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))


def state_dir() -> Path:
    """Root of all harness runtime state (never inside the repo)."""
    override = os.environ.get("CLAUDE_HARNESS_STATE_DIR")
    base = Path(override) if override else Path(os.path.expanduser("~/.cache/claude_harness"))
    try:
        base.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return base


def harness_home() -> Path:
    """Directory holding scripts/, skillbank/, guidelines/, mcp_servers/.

    Resolution order: ``$CLAUDE_HARNESS_HOME`` -> ``~/.claude/harness`` (installed)
    -> the in-repo ``antigravity/`` tree sitting next to this ``.claude`` dir.
    """
    override = os.environ.get("CLAUDE_HARNESS_HOME")
    if override and Path(override).is_dir():
        return Path(override)
    installed = Path(os.path.expanduser("~/.claude/harness"))
    if (installed / "scripts").is_dir():
        return installed
    repo_tree = HOOKS_DIR.parent.parent / "antigravity"
    if repo_tree.is_dir():
        return repo_tree
    return installed


def claude_home() -> Path:
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(override) if override else Path(os.path.expanduser("~/.claude"))


def scripts_dir() -> Path:
    return harness_home() / "scripts"


def skillbank_dir() -> Path:
    return harness_home() / "skillbank"


def registry_db_path() -> Path:
    override = os.environ.get("CLAUDE_HARNESS_REGISTRY_DB") or os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB")
    if override:
        return Path(override)
    primary = Path(os.path.expanduser("~/.local/share/codex/projects/registry.sqlite"))
    if primary.is_file():
        return primary
    return skillbank_dir() / "registry.sqlite"


def graph_db_path() -> Path:
    override = os.environ.get("CLAUDE_HARNESS_GRAPH_DB")
    if override:
        return Path(override)
    return Path(os.path.expanduser("~/.local/share/codex/projects/graph.sqlite"))


def codegraph_db_path() -> Path:
    override = os.environ.get("CLAUDE_HARNESS_CODEGRAPH_DB")
    if override:
        return Path(override)
    return Path(os.path.expanduser("~/.local/share/codex/codegraph_index.sqlite"))


def live_state_path() -> Path:
    override = os.environ.get("CLAUDE_HARNESS_LIVE_STATE")
    return Path(override) if override else state_dir() / "live_state.json"


# ---------------------------------------------------------------------------
# Payload + output envelopes
# ---------------------------------------------------------------------------

def read_payload() -> dict:
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def emit(obj: Optional[dict]) -> None:
    if obj is None:
        return
    sys.stdout.write(json.dumps(obj))
    sys.stdout.write("\n")
    sys.stdout.flush()


def pre_tool_allow(updated_input: Optional[dict] = None, context: str = "") -> dict:
    out: dict = {"hookEventName": "PreToolUse", "permissionDecision": "allow"}
    if updated_input:
        out["updatedInput"] = updated_input
    if context:
        out["additionalContext"] = context[:10000]
    return {"hookSpecificOutput": out}


def pre_tool_deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason[:10000],
        }
    }


def pre_tool_ask(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason[:10000],
        }
    }


def context_output(event: str, context: str, system_message: str = "") -> dict:
    out: dict = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": context[:10000]}}
    if system_message:
        out["systemMessage"] = system_message[:10000]
    return out


def block_output(reason: str, event: str = "") -> dict:
    out: dict = {"decision": "block", "reason": reason[:10000]}
    if event:
        out["hookSpecificOutput"] = {"hookEventName": event}
    return out


# ---------------------------------------------------------------------------
# Atomic JSON helpers
# ---------------------------------------------------------------------------

def atomic_json_read(path: os.PathLike, default: Any = None) -> Any:
    try:
        p = Path(path)
        if not p.is_file():
            return default
        with open(p, "r", encoding="utf-8") as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            except Exception:
                pass
            try:
                return json.load(f)
            finally:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
    except Exception:
        return default


def atomic_json_write(path: os.PathLike, data: Any) -> bool:
    p = Path(path)
    tmp = None
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", dir=str(p.parent), delete=False, encoding="utf-8") as tf:
            tmp = tf.name
            json.dump(data, tf, indent=2)
            tf.flush()
            os.fsync(tf.fileno())
        os.replace(tmp, p)
        return True
    except Exception:
        if tmp and os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass
        return False


def atomic_json_update(path: os.PathLike, fn: Callable[[Any], Any], default: Any = None) -> Any:
    p = Path(path)
    lock_path = str(p) + ".lock"
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "w") as lock_f:
            fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
            try:
                current = atomic_json_read(p, default=default)
                updated = fn(current)
                atomic_json_write(p, updated)
                return updated
            finally:
                fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
    except Exception:
        current = atomic_json_read(p, default=default)
        updated = fn(current)
        atomic_json_write(p, updated)
        return updated


# ---------------------------------------------------------------------------
# Session state ledger
# ---------------------------------------------------------------------------

def _sanitize(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", str(name or ""))[:120] or "default"


def session_id(payload: dict) -> str:
    sid = str(payload.get("session_id") or payload.get("sessionId") or "").strip()
    if sid:
        return sid
    tp = str(payload.get("transcript_path") or "").strip()
    if tp:
        return Path(tp).stem
    return "pid_%d" % os.getppid()


def agent_scope(payload: dict) -> str:
    """Ledger scope: the session, or ``session/agent_id`` inside a subagent."""
    sid = _sanitize(session_id(payload))
    aid = str(payload.get("agent_id") or "").strip()
    if aid:
        return "%s/agent_%s" % (sid, _sanitize(aid))
    return sid


def session_dir(payload: dict, scoped: bool = True) -> Path:
    key = agent_scope(payload) if scoped else _sanitize(session_id(payload))
    d = state_dir() / "sessions" / key
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


def root_session_dir(payload: dict) -> Path:
    return session_dir(payload, scoped=False)


def load_state(payload: dict, name: str, default: Any = None, scoped: bool = True) -> Any:
    return atomic_json_read(session_dir(payload, scoped) / ("%s.json" % name), default=default)


def save_state(payload: dict, name: str, data: Any, scoped: bool = True) -> None:
    atomic_json_write(session_dir(payload, scoped) / ("%s.json" % name), data)


def update_state(payload: dict, name: str, fn: Callable[[Any], Any], default: Any = None, scoped: bool = True) -> Any:
    return atomic_json_update(session_dir(payload, scoped) / ("%s.json" % name), fn, default=default)


def append_event(payload: dict, event: dict, scoped: bool = True) -> None:
    """Append a tool/lifecycle event to events.jsonl (root + scoped ledgers)."""
    event = dict(event)
    event.setdefault("ts", time.time())
    aid = str(payload.get("agent_id") or "").strip()
    if aid:
        event.setdefault("agent_id", aid)
        event.setdefault("agent_type", str(payload.get("agent_type") or ""))
    targets = [session_dir(payload, scoped=False) / "events.jsonl"]
    if scoped and aid:
        targets.append(session_dir(payload, scoped=True) / "events.jsonl")
    line = json.dumps(event, sort_keys=True)
    for target in targets:
        try:
            with open(target, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


def iter_events(payload: dict, tail: int = 600, scoped: bool = False) -> list:
    path = session_dir(payload, scoped=scoped) / "events.jsonl"
    if not path.is_file():
        return []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception:
        return []
    out = []
    for line in lines[-tail:]:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def once(payload: dict, key: str, ttl: float = 0.0) -> bool:
    """Return True the first time ``key`` is seen for this scope (dedupe marker)."""
    flags = session_dir(payload) / "flags"
    try:
        flags.mkdir(parents=True, exist_ok=True)
    except Exception:
        return True
    marker = flags / _sanitize(key)
    if marker.is_file():
        if ttl > 0:
            try:
                if time.time() - marker.stat().st_mtime < ttl:
                    return False
            except Exception:
                return False
        else:
            return False
    try:
        marker.write_text(str(time.time()), encoding="utf-8")
    except Exception:
        pass
    return True


def flag_set(payload: dict, key: str) -> bool:
    return (session_dir(payload) / "flags" / _sanitize(key)).is_file()


def flag_clear(payload: dict, key: str) -> None:
    try:
        (session_dir(payload) / "flags" / _sanitize(key)).unlink()
    except Exception:
        pass


def flag_touch(payload: dict, key: str) -> None:
    flags = session_dir(payload) / "flags"
    try:
        flags.mkdir(parents=True, exist_ok=True)
        (flags / _sanitize(key)).write_text(str(time.time()), encoding="utf-8")
    except Exception:
        pass


def reap_stale_state(max_age_sec: int = 86400 * 3) -> int:
    """Delete session ledgers older than ``max_age_sec`` (never the current one)."""
    reaped = 0
    now = time.time()
    sessions = state_dir() / "sessions"
    if not sessions.is_dir():
        return 0
    for entry in sessions.iterdir():
        try:
            if entry.is_dir() and (now - entry.stat().st_mtime) > max_age_sec:
                shutil.rmtree(entry, ignore_errors=True)
                reaped += 1
        except Exception:
            continue
    return reaped


# ---------------------------------------------------------------------------
# Workspace, paths, files
# ---------------------------------------------------------------------------

def workspace(payload: dict) -> str:
    for key in ("cwd",):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return os.path.abspath(val.strip())
    env_ws = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_ws:
        return os.path.abspath(env_ws)
    return os.getcwd()


def project_dir(payload: dict) -> str:
    env_ws = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_ws and os.path.isdir(env_ws):
        return os.path.abspath(env_ws)
    return workspace(payload)


def project_slug(ws: str) -> str:
    if not ws:
        ws = os.getcwd()
    ws = ws.strip().strip("'\"")
    slug = os.path.basename(os.path.normpath(ws)) or "default"
    reg = registry_db_path()
    if reg.is_file():
        conn = None
        try:
            conn = sqlite3.connect("file:%s?mode=ro" % reg, uri=True, timeout=0.5)
            conn.execute("PRAGMA busy_timeout=500;")
            cur = conn.cursor()
            row = None
            for query in (
                "SELECT slug FROM projects WHERE project_path = ? OR project_path LIKE ? LIMIT 1;",
                "SELECT slug FROM projects WHERE path = ? OR path LIKE ? LIMIT 1;",
            ):
                try:
                    row = cur.execute(query, (ws, "%%%s%%" % slug)).fetchone()
                    if row:
                        break
                except Exception:
                    continue
            if row and row[0]:
                slug = str(row[0])
        except Exception:
            pass
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    return slug


def unwrap_outer_quotes(s: Any) -> str:
    if not isinstance(s, str):
        return ""
    s = s.strip()
    while len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        s = s[1:-1].strip()
    return s


def normalize_path(path: str, cwd: str) -> str:
    cleaned = unwrap_outer_quotes(path)
    expanded = os.path.expanduser(cleaned)
    if not os.path.isabs(expanded):
        expanded = os.path.join(cwd or os.getcwd(), expanded)
    return os.path.normpath(os.path.abspath(expanded))


def to_int(val: Any) -> Optional[int]:
    if isinstance(val, bool):
        return None
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)
    if isinstance(val, str):
        cleaned = val.strip().strip("'\"")
        if cleaned.lstrip("-").isdigit():
            try:
                return int(cleaned)
            except Exception:
                return None
    return None


def count_lines(file_path: str) -> int:
    total = 0
    last = b""
    try:
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                total += chunk.count(b"\n")
                last = chunk[-1:]
        if last and last != b"\n":
            total += 1
    except Exception:
        return 0
    return total


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".ico", ".tiff")

SCOUT_BLOCK_DIRS = (".cargo/registry", "node_modules", ".next", "dist", ".turbo", ".gradle")

BLOCKED_LIST_DIRS = ("/node_modules", "/.venv", "/.git", "/.cache", "/.cargo", "/target", "/dist", "/build")

PRIVACY_EXEMPT_BASENAMES = {".env.example", ".env.sample", ".env.template", ".env.test"}
PRIVACY_BLOCKED_BASENAMES = {
    ".env", ".env.local", ".env.production", ".env.development",
    "id_rsa", "id_ed25519", ".npmrc", ".pypirc",
}

APPLICATION_CODE_EXTENSIONS = (
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".kt", ".java", ".go", ".rs",
    ".swift", ".c", ".cpp", ".cs", ".vue", ".svelte", ".css", ".scss", ".html", ".sql",
    ".prisma", ".graphql",
)


def is_privacy_blocked(file_path: str) -> tuple:
    base = os.path.basename(file_path)
    low = base.lower()
    if low in PRIVACY_EXEMPT_BASENAMES or low.endswith((".example", ".sample", ".template", ".test")):
        return (False, "")
    if low in PRIVACY_BLOCKED_BASENAMES:
        return (True, base)
    if fnmatch.fnmatch(low, "*.pem") or fnmatch.fnmatch(low, "*.key"):
        return (True, base)
    return (False, "")


def scout_blocked_dir(path_str: str) -> Optional[str]:
    norm = "/" + path_str.replace("\\", "/").strip("/") + "/"
    for d in SCOUT_BLOCK_DIRS:
        if "/%s/" % d in norm:
            return d
    return None


def is_harness_path(norm_low: str) -> bool:
    """Paths belonging to the harness itself (never treated as application code)."""
    if "/.claude/" in norm_low or norm_low.endswith("/.claude") or "/.gemini/" in norm_low:
        return True
    try:
        home = str(claude_home()).lower().rstrip("/")
        if norm_low.startswith(home + "/"):
            return True
        hh = str(harness_home()).lower().rstrip("/")
        if hh and norm_low.startswith(hh + "/"):
            return True
    except Exception:
        pass
    return False


def is_app_code(path: str, cwd: str = "") -> bool:
    cleaned = str(path or "").strip().strip("'\"`")
    if not cleaned or cleaned.startswith("&") or cleaned in ("/dev/null", "/dev/stdout", "/dev/stderr", "/dev/zero"):
        return False
    norm = normalize_path(cleaned, cwd or os.getcwd()).lower()
    if is_harness_path(norm):
        return False
    tmp = tempfile.gettempdir().lower()
    ws_low = (cwd or "").lower()
    in_tmp = "/tmp/" in norm or norm.startswith(("/tmp", tmp))
    ws_in_tmp = bool(ws_low) and ("/tmp/" in ws_low or ws_low.startswith(("/tmp", tmp)))
    if in_tmp and not ws_in_tmp:
        return False
    return norm.endswith(APPLICATION_CODE_EXTENSIONS)


def is_test_file(path_str: str) -> bool:
    if not path_str:
        return False
    norm = path_str.replace("\\", "/").lower()
    base = os.path.basename(norm)
    if "/__tests__/" in norm or norm.startswith("__tests__/") or norm.endswith("/__tests__"):
        return True
    for pat in ("*.test.*", "*.spec.*", "test_*.py", "*_test.py", "*_test.go", "*_test.rs"):
        if fnmatch.fnmatch(base, pat):
            return True
    return False


def find_sot_docs(ws: str) -> list:
    if not ws or not os.path.isdir(ws):
        return []
    found = []
    for cand in ("docs/STATUS.md", "docs/README.md", "CLAUDE.md", "AGENTS.md", "README.md"):
        if os.path.isfile(os.path.join(ws, cand)):
            found.append(cand)
    return found


# ---------------------------------------------------------------------------
# Guardrail policy
# ---------------------------------------------------------------------------

DEFAULT_POLICY = {
    "slice_cap": 250,
    "max_slices": 6,
    "flood_limit": 50,
    "outline_threshold": 400,
    "read_once_threshold": 200,
    "whole_read_ceiling": 2,
    "read_strike_limit": 3,
    "unedited_read_ceiling": 8,
    "command_length_limit": 4000,
    "subagent_prompt_limit": 6000,
    "root_may_edit_code": False,
    "block_image_reads": True,
    "ban_cd": False,
    "require_modern_cli": "auto",
    "teardown_file_threshold": 4,
    "simplify_loc_threshold": 400,
    "simplify_file_threshold": 8,
    "context_degraded_pct": 55.0,
    "context_critical_pct": 75.0,
    "auto_compact_pct": 65.0,
    "notify": False,
    "annotate_verification_exit_codes": True,
    "verification_patterns": [],
}


def guardrail_policy(ws: Optional[str] = None) -> dict:
    merged = dict(DEFAULT_POLICY)
    candidates = []
    if ws:
        candidates.append(Path(ws) / ".claude" / "harness" / "guardrails.json")
        candidates.append(Path(ws) / ".antigravity" / "task_harness" / "guardrails.json")
    if not is_test_env() or os.environ.get("CLAUDE_HARNESS_TEST_POLICY"):
        candidates.append(claude_home() / "harness" / "guardrails.json")
        candidates.append(skillbank_dir() / "guardrails.json")
    for cand in reversed(candidates):
        data = atomic_json_read(cand, default=None)
        if isinstance(data, dict):
            merged.update(data)
    env_root = os.environ.get("CLAUDE_HARNESS_ROOT_BUILDER")
    if env_root in ("1", "true", "yes"):
        merged["root_may_edit_code"] = True
    merged["slice_cap"] = max(50, int(merged.get("slice_cap", 250)))
    return merged


# ---------------------------------------------------------------------------
# Roles and leases
# ---------------------------------------------------------------------------

ROOT_ROLE = "pm"

BUILDER_ROLES = frozenset({
    "dev-fe", "dev-be", "debugger", "designer", "meta-evolution", "frontend",
    "visual-engineer", "general-purpose", "general", "claude", "statusline-setup",
})

NON_BUILDER_ROLES = frozenset({
    "pm", "oracle-review", "hallucination-auditor", "implementation-review", "frontend-qc",
    "sa", "senior-architect", "critical-planner", "frontend-explorer", "backend-explorer",
    "research-explorer", "user-tester", "doc-sync-worker", "librarian", "diff-helper",
    "test-runner", "security-audit", "whitehat", "simplifier-reviewer", "explore", "plan",
    "claude-code-guide", "skillopt-optimizer", "devops",
})

READONLY_ROLES = frozenset({
    "research", "research-explorer", "frontend-explorer", "backend-explorer", "explorer",
    "explore", "user-tester", "oracle-review", "hallucination-auditor", "implementation-review",
    "frontend-qc", "test-runner", "diff-helper", "security-audit", "whitehat",
    "simplifier-reviewer", "critical-planner", "plan", "claude-code-guide",
})

# Model tier baseline per role (Claude aliases). Tier ranks: haiku < sonnet < inherit < opus < fable.
MODEL_TIER_RANKS = {"haiku": 0, "sonnet": 1, "inherit": 2, "opus": 3, "fable": 4}
HAIKU_ROLES = frozenset({"diff-helper", "telemetry-helper"})
SONNET_ROLES = frozenset({
    "research-explorer", "frontend-explorer", "backend-explorer", "test-runner", "doc-sync-worker",
    "librarian", "user-tester", "devops", "skillopt-optimizer", "explore", "claude-code-guide",
})

BUILTIN_AGENT_ALIASES = {
    "explore": "explore",
    "plan": "critical-planner",
    "general-purpose": "general-purpose",
    "claude": "general-purpose",
    "claude-code-guide": "claude-code-guide",
    "statusline-setup": "general-purpose",
}

ROLE_SKILL_BUNDLES = {
    "pm": (["routing-thresholds", "spawn-governance"], "PM Orchestrator: classify complexity, emit Story Shards, never mutate application code."),
    "sa": (["senior-architect"], "Senior Architect: define interfaces, ADRs, and bounded contracts before implementation."),
    "senior-architect": (["senior-architect"], "Senior Architect: define interfaces, ADRs, and bounded contracts before implementation."),
    "critical-planner": (["senior-architect"], "Critical Planner: conduct adversarial plan review and challenge assumptions."),
    "dev-fe": (["ui-ux-craft"], "Frontend Builder: reuse shared design tokens, make surgical UI diffs, satisfy anti-slop invariants."),
    "dev-be": (["oracle-review", "auto-verification-harness"], "Backend Builder: verification-before-completion and structured validation for backend changes."),
    "designer": (["ui-ux-craft"], "UI/UX Designer: enforce visual hierarchy, token compliance, and anti-slop layout rules."),
    "visual-engineer": (["ui-ux-craft", "ui-ux-audit"], "Visual Engineer: UI/UX design tokens, layout ergonomics, animations, anti-slop audit."),
    "frontend-qc": (["ui-ux-audit"], "Frontend QC: read-only inspector auditing UI against the anti-slop taxonomy (L-01, L-13, T-12, D-09)."),
    "debugger": (["auto-verification-harness"], "Debugger: reproduce failures on the smallest surface and trace root-cause evidence before patching."),
    "oracle-review": (["oracle-review"], "Oracle Reviewer: read-only audit for regressions, scope drift, hallucinated references, missing tests."),
    "hallucination-auditor": (["oracle-review"], "Hallucination Auditor: verify all file paths, symbols, and execution claims against ground truth."),
    "implementation-review": (["oracle-review", "auto-verification-harness"], "Implementation Reviewer: independent audit of code changes, verification, regression control."),
    "simplifier-reviewer": (["oracle-review", "scope-drift-control"], "Simplifier Reviewer: scope drift control and anti-complexity simplification review."),
    "test-runner": (["e2e_testing", "auto-verification-harness"], "Test Runner: dynamic test execution, structured validation, verification logging."),
    "user-tester": (["e2e_testing", "auto-verification-harness"], "User Tester: end-to-end user journey validation and test suite execution."),
    "devops": (["auto-verification-harness"], "DevOps: build harness verification, test harnesses, environment validation."),
    "meta-evolution": (["harness-deficiency-audit"], "Meta Evolution: optimize agent skills and audit harness deficiencies."),
    "skillopt-optimizer": (["harness-deficiency-audit"], "Skill Optimizer: optimize skill documents with bounded edits and held-out validation."),
    "librarian": (["document-sync", "sot-context"], "Librarian: documentation sync, knowledge capture, SOT grounding."),
    "doc-sync-worker": (["document-sync"], "Doc Sync Worker: synchronize approved changes into docs/STATUS.md and codex_knowledge."),
    "diff-helper": (["scope-drift-control", "auto-verification-harness"], "Diff Helper: scope drift control and structured diff validation."),
    "security-audit": (["security-audit"], "Security Auditor: read-only check of auth, secrets, command execution, trust boundaries."),
    "whitehat": (["security-audit"], "Security Auditor: read-only check of auth, secrets, command execution, trust boundaries."),
    "backend-explorer": (["codegraph-explorer"], "Backend Explorer: read-only CodeGraph-first discovery of services, schemas, APIs."),
    "frontend-explorer": (["codegraph-explorer"], "Frontend Explorer: read-only CodeGraph-first discovery of components, state, routes."),
    "research-explorer": (["ground-truth-retrieval"], "Research Explorer: read-only external documentation and Context7 verification."),
    "explore": (["codegraph-explorer"], "Explorer: read-only codebase discovery; return coordinates, never code or plans."),
}


def is_subagent(payload: dict) -> bool:
    return bool(str(payload.get("agent_id") or "").strip()) or bool(str(payload.get("agent_type") or "").strip())


def role_of(payload: dict) -> str:
    """Normalized role: ``pm`` for the main thread, else the subagent's agent_type."""
    raw = str(payload.get("agent_type") or "").strip().lower()
    if not raw:
        return ROOT_ROLE
    if raw in BUILTIN_AGENT_ALIASES:
        return BUILTIN_AGENT_ALIASES[raw]
    return raw


def is_non_builder_role(role: str) -> bool:
    role = (role or "").lower()
    if role in BUILDER_ROLES:
        return False
    if role in NON_BUILDER_ROLES:
        return True
    return "explorer" in role or "review" in role or "audit" in role or role.endswith("-qc")


def is_readonly_role(role: str) -> bool:
    role = (role or "").lower()
    return role in READONLY_ROLES or "explorer" in role or role.endswith("-qc")


def baseline_tier(role: str) -> str:
    role = (role or "").lower()
    if role in HAIKU_ROLES:
        return "haiku"
    if role in SONNET_ROLES or "explorer" in role:
        return "sonnet"
    return "inherit"


def model_tier_rank(model: str) -> Optional[int]:
    m = str(model or "").strip().lower()
    if not m:
        return None
    if m in MODEL_TIER_RANKS:
        return MODEL_TIER_RANKS[m]
    for key, rank in MODEL_TIER_RANKS.items():
        if key != "inherit" and key in m:
            return rank
    return None


# ----- allowed_files leases -------------------------------------------------

def extract_allowed_files(content: str) -> tuple:
    """Parse an ``allowed_files:`` block (YAML list, JSON array, bullets, or inline)."""
    if not content:
        return (False, [])
    m = re.search(r"(?:^|\n|\b)[ \t]*[`*_-]*allowed_files[`*_-]*\s*:\s*(.*)", content, re.IGNORECASE)
    if not m:
        return (False, [])
    rest = content[m.start():].strip()
    line_rest = m.group(1).strip()

    if line_rest.startswith("["):
        arr = re.search(r"\[(.*?)\]", rest, re.DOTALL)
        if arr:
            try:
                items = json.loads("[" + arr.group(1) + "]")
                return (True, [str(x).strip() for x in items if x is not None and str(x).strip()])
            except Exception:
                raw_items = [x.strip(" '\"`") for x in arr.group(1).split(",") if x.strip(" '\"`")]
                return (True, raw_items)
        return (True, [])

    if line_rest and not line_rest.startswith(("-", "*", "|", ">")):
        cleaned = line_rest.strip().strip("`'\"")
        if cleaned.lower() in ("none", "null", "~", "[]"):
            return (True, [])
        parts = [p.strip().strip("`'\"") for p in re.split(r"[,\s]+", cleaned) if p.strip()]
        return (True, [p for p in parts if p])

    files = []
    for line in rest.splitlines()[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("-", "*")):
            val = stripped[1:].strip().strip("'\"`")
            if val:
                files.append(val)
        elif re.match(r"^[A-Za-z0-9_-]+\s*:", stripped) or re.match(r"^[#*]{2,}", stripped):
            break
        else:
            break
    return (True, files)


def matches_allowed_file(target_norm: str, pattern: str, ws: str) -> bool:
    target_clean = os.path.normpath(target_norm).lower()
    pattern_clean = str(pattern or "").strip().strip("'\"`")
    if not pattern_clean:
        return False
    ws_clean = (ws or "").lower().rstrip("/")
    rel = os.path.relpath(target_clean, ws_clean) if ws_clean else ""
    pat_norm = os.path.normpath(
        os.path.join(ws_clean, pattern_clean) if not os.path.isabs(pattern_clean) else pattern_clean
    ).lower()
    pat_low = pattern_clean.lower()

    if target_clean == pat_norm or target_clean == pat_low:
        return True
    if rel and (rel == pat_low or rel == os.path.normpath(pat_low)):
        return True
    base = os.path.basename(target_clean)
    if target_clean.endswith("/" + pat_low.lstrip("/")) or base == pat_low:
        return True
    if any(c in pattern_clean for c in "*?[]"):
        if fnmatch.fnmatch(target_clean, pat_low) or fnmatch.fnmatch(base, pat_low):
            return True
        if rel and fnmatch.fnmatch(rel, pat_low):
            return True
        if "**" in pat_low:
            regex = re.escape(pat_low).replace(r"\*\*", ".*").replace(r"\*", "[^/]*") + "$"
            if re.search(regex, target_clean) or (rel and re.search(regex, rel)):
                return True
    if pattern_clean.endswith(("/", "/*")):
        prefix = pat_norm.rstrip("/*")
        if target_clean.startswith(prefix + "/"):
            return True
    return False


def record_lease(payload: dict, subagent_type: str, prompt: str) -> None:
    """Called from the parent's PreToolUse(Agent): remember the lease for the child."""
    has, files = extract_allowed_files(prompt)
    role_m = re.search(r"\brole\s*[:=]\s*['\"`]?([a-z0-9_-]+)", prompt, re.IGNORECASE)
    entry = {
        "subagent_type": str(subagent_type or "").lower(),
        "role": (role_m.group(1).lower() if role_m else str(subagent_type or "").lower()),
        "has_allowed_files": bool(has),
        "allowed_files": files,
        "prompt_sha": hashlib.sha256(prompt.encode("utf-8", errors="ignore")).hexdigest()[:16],
        "prompt_head": prompt[:400],
        "allow_nested_agents": ("allow_define_subagent" in prompt) or ("EnableSubagentTools: true" in prompt),
        "ts": time.time(),
    }

    def _upd(cur):
        cur = cur if isinstance(cur, list) else []
        cur.append(entry)
        return cur[-32:]

    atomic_json_update(root_session_dir(payload) / "leases.json", _upd, default=[])


def root_transcript_path(payload: dict) -> str:
    """The main session transcript, recorded by UserPromptSubmit/SessionStart."""
    meta = load_state(payload, "session_meta", default={}, scoped=False)
    if isinstance(meta, dict) and meta.get("transcript_path"):
        return str(meta["transcript_path"])
    return ""


def claim_lease(payload: dict) -> Optional[dict]:
    """Bind the oldest unclaimed parent lease of this agent_type to this agent_id.

    Claude Code delivers ``transcript_path`` = the *parent* transcript inside
    subagent hooks, so the Agent prompt (and its ``allowed_files``) is only
    reliably known from the parent's ``leases.json`` written by PreToolUse(Agent).
    Dispatch order equals start order, so FIFO claiming is deterministic.
    """
    if not is_subagent(payload):
        return None
    role = str(payload.get("agent_type") or "").lower()
    aid = str(payload.get("agent_id") or "")
    claimed = {"entry": None}

    def _upd(cur):
        cur = cur if isinstance(cur, list) else []
        for entry in cur:
            if isinstance(entry, dict) and entry.get("agent_id") == aid and aid:
                claimed["entry"] = entry
                return cur
        for entry in cur:
            if isinstance(entry, dict) and entry.get("subagent_type") == role and not entry.get("agent_id"):
                entry["agent_id"] = aid
                entry["claimed_at"] = time.time()
                claimed["entry"] = entry
                return cur
        return cur

    atomic_json_update(root_session_dir(payload) / "leases.json", _upd, default=[])
    return claimed["entry"]


def lease_for(payload: dict) -> dict:
    """Resolve the active lease of the current subagent.

    Order: scoped cache -> the lease claimed by this ``agent_id`` (or the oldest
    unclaimed lease of this ``agent_type``) from the parent's ``leases.json`` ->
    the subagent's own transcript (``agent_transcript_path``, or
    ``transcript_path`` only when it differs from the root session transcript).
    Returns ``has_allowed_files``, ``allowed_files``, ``allow_nested_agents``,
    ``prompt``, ``source``.
    """
    empty = {"has_allowed_files": False, "allowed_files": [], "allow_nested_agents": False, "prompt": ""}
    if not is_subagent(payload):
        return empty
    cached = load_state(payload, "lease", default=None)
    if isinstance(cached, dict) and cached.get("resolved"):
        return cached

    result = dict(empty)
    entry = claim_lease(payload)
    if isinstance(entry, dict):
        result.update({
            "has_allowed_files": bool(entry.get("has_allowed_files")),
            "allowed_files": list(entry.get("allowed_files") or []),
            "allow_nested_agents": bool(entry.get("allow_nested_agents")),
            "prompt": str(entry.get("prompt_head") or ""),
            "source": "parent_lease",
        })
    else:
        root_tp = root_transcript_path(payload)
        candidates = [str(payload.get("agent_transcript_path") or "").strip()]
        tp = str(payload.get("transcript_path") or "").strip()
        if tp and tp != root_tp and "/agent-" in tp.replace("\\", "/"):
            candidates.append(tp)
        for cand in candidates:
            if cand and os.path.isfile(cand):
                prompt = transcript_first_user_text(cand)
                if prompt:
                    has, files = extract_allowed_files(prompt)
                    result.update({
                        "has_allowed_files": bool(has),
                        "allowed_files": files,
                        "allow_nested_agents": ("allow_define_subagent" in prompt) or ("EnableSubagentTools: true" in prompt),
                        "prompt": prompt[:4000],
                        "source": "agent_transcript",
                    })
                    break
    if result.get("source"):
        result["resolved"] = True
        save_state(payload, "lease", result)
    return result


# ---------------------------------------------------------------------------
# Claude Code transcript reader
# ---------------------------------------------------------------------------

def _message_text(msg: Any) -> str:
    if isinstance(msg, str):
        return msg
    if isinstance(msg, dict):
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text" and isinstance(block.get("text"), str):
                        parts.append(block["text"])
                elif isinstance(block, str):
                    parts.append(block)
            return "\n".join(parts)
    return ""


def iter_transcript(path: str, tail_bytes: int = 0) -> Iterable[dict]:
    if not path or not os.path.isfile(path):
        return []
    out = []
    try:
        with open(path, "rb") as f:
            if tail_bytes > 0:
                size = os.path.getsize(path)
                if size > tail_bytes:
                    f.seek(size - tail_bytes)
                    f.readline()
            for raw in f:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw.decode("utf-8", errors="ignore"))
                except Exception:
                    continue
                if isinstance(obj, dict):
                    out.append(obj)
    except Exception:
        return out
    return out


def transcript_first_user_text(path: str) -> str:
    for obj in iter_transcript(path):
        if obj.get("type") != "user":
            continue
        msg = obj.get("message") or {}
        content = msg.get("content") if isinstance(msg, dict) else None
        if isinstance(content, list) and content and all(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in content
        ):
            continue
        text = _message_text(msg)
        if text.strip():
            return text
    return ""


def transcript_last_user_text(path: str, tail_bytes: int = 262144) -> str:
    last = ""
    for obj in iter_transcript(path, tail_bytes=tail_bytes):
        if obj.get("type") != "user":
            continue
        msg = obj.get("message") or {}
        content = msg.get("content") if isinstance(msg, dict) else None
        if isinstance(content, list) and content and all(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in content
        ):
            continue
        text = _message_text(msg)
        if text.strip():
            last = text
    return last


def transcript_tool_uses(path: str, tail_bytes: int = 0) -> list:
    """Return ``[{name, input, id, ts}]`` for every assistant tool_use block."""
    uses = []
    for obj in iter_transcript(path, tail_bytes=tail_bytes):
        if obj.get("type") != "assistant":
            continue
        msg = obj.get("message") or {}
        content = msg.get("content") if isinstance(msg, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                uses.append({
                    "name": str(block.get("name") or ""),
                    "input": block.get("input") if isinstance(block.get("input"), dict) else {},
                    "id": str(block.get("id") or ""),
                    "ts": obj.get("timestamp"),
                })
    return uses


def transcript_has_compact(path: str) -> bool:
    for obj in iter_transcript(path, tail_bytes=1024 * 1024):
        if obj.get("type") == "summary" or obj.get("isCompactSummary") or obj.get("subtype") == "compact_boundary":
            return True
        if obj.get("type") == "system" and "compact" in str(obj.get("subtype") or "").lower():
            return True
    return False


# ---------------------------------------------------------------------------
# Tool-name canonicalization (Claude Code -> harness vocabulary)
# ---------------------------------------------------------------------------

READ_TOOLS = ("Read",)
EDIT_TOOLS = ("Edit", "MultiEdit", "NotebookEdit")
WRITE_TOOLS = ("Write",)
MUTATION_TOOLS = EDIT_TOOLS + WRITE_TOOLS
SEARCH_TOOLS = ("Grep", "Glob")
SHELL_TOOLS = ("Bash", "PowerShell")
AGENT_TOOLS = ("Agent", "Task")


def canonical_tool(tool_name: str) -> str:
    t = str(tool_name or "")
    if t in READ_TOOLS:
        return "read_file"
    if t in WRITE_TOOLS:
        return "write_file"
    if t in EDIT_TOOLS:
        return "edit_file"
    if t in SHELL_TOOLS:
        return "run_command"
    if t in AGENT_TOOLS:
        return "invoke_subagent"
    if t.startswith("mcp__"):
        return "call_mcp_tool"
    return t.lower()


def mcp_server_and_tool(tool_name: str) -> tuple:
    t = str(tool_name or "")
    if not t.startswith("mcp__"):
        return ("", "")
    rest = t[5:]
    if "__" in rest:
        srv, bare = rest.split("__", 1)
        return (srv, bare)
    return (rest, "")


def target_file_of(tool_name: str, tool_input: dict) -> str:
    if not isinstance(tool_input, dict):
        return ""
    for key in ("file_path", "notebook_path", "path", "filePath"):
        val = tool_input.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return ""


# ---------------------------------------------------------------------------
# Failure telemetry (burn-rate sentinel bridge)
# ---------------------------------------------------------------------------

SEVERITY_WEIGHTS = {"S0_catastrophic": 1.0, "S1_critical": 0.25, "S2_major": 0.05, "S3_minor": 0.01}


def _load_sentinel():
    sdir = str(scripts_dir())
    if not os.path.isfile(os.path.join(sdir, "burn-rate-sentinel.py")):
        return None
    if sdir not in sys.path:
        sys.path.insert(0, sdir)
    try:
        import importlib
        return importlib.import_module("burn-rate-sentinel")
    except Exception:
        return None


def record_harness_failure(
    payload: dict,
    failure_type: str,
    reason: str,
    tool_name: str = "",
    details: str = "",
    severity_tier: str = "S3_minor",
    vertex: str = "tool_guidance",
) -> None:
    """Best-effort cross-session failure ledger (<10ms budget, never raises)."""
    if is_test_env() and not os.environ.get("CLAUDE_HARNESS_REGISTRY_DB") and not os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB"):
        return
    conv_id = session_id(payload)
    ws = workspace(payload)
    slug = os.path.basename(ws.rstrip("/")) if ws else "default"
    session_type = "subagent" if is_subagent(payload) else "top_level"
    try:
        sentinel = _load_sentinel()
        if sentinel is not None and hasattr(sentinel, "record_harness_failure"):
            sentinel.record_harness_failure(
                conv_id=conv_id,
                failure_type=failure_type,
                slug=slug,
                tool_name=tool_name,
                reason=reason[:500],
                details=details[:500],
                severity_tier=severity_tier,
                vertex=vertex,
                session_type=session_type,
            )
            return
    except Exception:
        pass
    try:
        db = registry_db_path()
        db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db), timeout=0.5)
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA busy_timeout=500;")
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
            cur.execute(
                """
                INSERT INTO harness_failures (
                    conv_id, slug, session_type, vertex, failure_type, tool_name,
                    severity_tier, severity_weight, reason, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    conv_id, slug, session_type, vertex, failure_type, tool_name,
                    severity_tier, SEVERITY_WEIGHTS.get(severity_tier, 0.01), reason[:500], details[:500],
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------

_SECRET_SCRUB_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|passwd|authorization)\s*[:=]\s*['\"]?[A-Za-z0-9_\-./+=]{8,}"
)


def scrub_secrets(text: str) -> str:
    try:
        return _SECRET_SCRUB_RE.sub(lambda m: "%s=<redacted>" % m.group(1), str(text or ""))
    except Exception:
        return str(text or "")


def cap_text(text: str, max_chars: int, marker: str = "…(truncated)") -> str:
    if len(text) <= max_chars:
        return text
    budget = max(0, max_chars - len(marker))
    return text[:budget].rstrip() + marker


def format_alerts(alerts: list, max_chars: int = 1500) -> str:
    valid = [a.strip() for a in alerts if a and str(a).strip()]
    if not valid:
        return ""
    return cap_text("\n\n".join(valid), max_chars)


def which(binary: str) -> Optional[str]:
    return shutil.which(binary)


def context_window_size(payload: dict) -> int:
    """Best-effort context window: 1M for `[1m]` models, else 200k (override: CLAUDE_HARNESS_CONTEXT_WINDOW)."""
    override = os.environ.get("CLAUDE_HARNESS_CONTEXT_WINDOW")
    if override and override.isdigit():
        return int(override)
    model = str(payload.get("model") or "")
    if not model:
        meta = load_state(payload, "session_meta", default={}, scoped=False)
        if isinstance(meta, dict):
            model = str(meta.get("model") or "")
    if not model:
        try:
            data = atomic_json_read(claude_home() / "settings.json", default={}) or {}
            model = str(data.get("model") or "")
        except Exception:
            model = ""
    return 1_000_000 if "[1m]" in model.lower() else 200_000


def transcript_context_usage(path: str, window: int) -> dict:
    """Estimate context usage from the last assistant `usage` block in a Claude Code transcript."""
    if not path or not os.path.isfile(path):
        return {}
    last = None
    for obj in iter_transcript(path, tail_bytes=512 * 1024):
        if obj.get("type") != "assistant":
            continue
        msg = obj.get("message")
        if isinstance(msg, dict) and isinstance(msg.get("usage"), dict):
            last = msg
    if not last:
        return {}
    u = last["usage"]
    try:
        used = int(u.get("input_tokens") or 0) + int(u.get("cache_read_input_tokens") or 0) + int(u.get("cache_creation_input_tokens") or 0)
    except Exception:
        return {}
    if used <= 0:
        return {}
    return {
        "source": "transcript",
        "used_tokens": used,
        "context_window_size": window,
        "used_percentage": round(used * 100.0 / max(1, window), 1),
        "model": str(last.get("model") or ""),
    }


def live_context_usage(payload: dict) -> dict:
    """Context usage for this session: status-line mirror when fresh, else the transcript usage estimate."""
    try:
        p = live_state_path()
        if p.is_file() and (time.time() - p.stat().st_mtime) <= 900:
            data = atomic_json_read(p, default={})
            sid = session_id(payload)
            if isinstance(data, dict) and (not data.get("session_id") or not sid or data.get("session_id") == sid):
                if data.get("used_percentage") is not None:
                    data.setdefault("source", "statusline")
                    return data
    except Exception:
        pass
    try:
        tp = str(payload.get("transcript_path") or root_transcript_path(payload) or "")
        if tp and ("/agent-" not in tp.replace("\\", "/")):
            return transcript_context_usage(tp, context_window_size(payload))
    except Exception:
        pass
    return {}

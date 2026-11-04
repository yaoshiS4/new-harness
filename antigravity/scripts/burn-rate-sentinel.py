#!/usr/bin/env python3
"""Cross-Session Harness Failure Ledger & Multi-Window Severity Sentinel (Google SRE Workbook, ch.5 Alerting on SLOs / arXiv:2504.13171 Letta Sleep-Time Compute).

Manages persistent harness failures in registry.sqlite, classifies symbolic failure
vertices (hook, skill, tool_guidance, routing, codebase), computes multi-window
burn rates, and idempotently escalates to settings_reviews.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

# 4-Tier SRE x Agent RSI Severity Weights
SEVERITY_WEIGHTS: Dict[str, float] = {
    "S0_catastrophic": 1.00,
    "S1_critical": 0.25,
    "S2_major": 0.05,
    "S3_minor": 0.01,
}

BUG_CATEGORIES: Tuple[str, ...] = (
    "LOGIC_ASSERTION_DRIFT",
    "TYPE_CONTRACT_MISMATCH",
    "BOUNDARY_INDEX_ERROR",
    "NULL_UNDEFINED_ACCESS",
    "IMPORT_DEPENDENCY_GAP",
    "ASYNC_CONCURRENCY_LOCK",
    "RESOURCE_IO_LIFECYCLE",
    "SPEC_GAMING_ATTEMPT",
)

PENDING_FAILURES_PATH = Path("/tmp/.antigravity_failures_pending.jsonl")
_INITIALIZED_LEDGER_DBS: set[str] = set()


def get_registry_db_path(custom_path: Optional[Union[str, Path]] = None) -> Path:
    """Resolve SQLite registry path, prioritizing test environment override."""
    if custom_path:
        return Path(custom_path).resolve()
    env_test_db = os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB")
    if env_test_db:
        return Path(env_test_db).resolve()
    default_path = Path.home() / ".local" / "share" / "codex" / "projects" / "registry.sqlite"
    default_path.parent.mkdir(parents=True, exist_ok=True)
    return default_path


def classify_bug_category(
    error_type: str = "",
    message: str = "",
    reason: str = "",
    vertex: str = "",
) -> str:
    """Classify failure signature into one of the 8 canonical bug categories."""
    text = f"{error_type} {message} {reason}".strip()
    text_lower = text.lower()

    # Spec gaming attempt (evaluated first to avoid false-matching lock/assert)
    if any(k in text_lower for k in ("test_assertion_lock", "test_lock_violation", "lease_violation", "tautological", "oracle custody")):
        return "SPEC_GAMING_ATTEMPT"

    # Null / undefined access
    if any(k in text_lower for k in ("nonetype", "undefined is not", "null pointer")):
        return "NULL_UNDEFINED_ACCESS"

    # Import / dependency gap
    if any(k in text_lower for k in ("importerror", "modulenotfounderror", "cannot find module")):
        return "IMPORT_DEPENDENCY_GAP"

    # Resource / IO lifecycle
    if any(k in text_lower for k in ("filenotfounderror", "permissionerror", "ioerror", "oserror")):
        return "RESOURCE_IO_LIFECYCLE"

    # Boundary / index error
    if any(k in text_lower for k in ("indexerror", "keyerror", "zerodivisionerror", "out of range", "boundary")):
        return "BOUNDARY_INDEX_ERROR"

    # Async / concurrency lock
    if not any(k in text_lower for k in ("read_budget_lock", "slice_loop_breaker")):
        if bool(re.search(r"\b(?:timeouterror|deadlock|lock|locked|locking|mutex)\b", text_lower)):
            return "ASYNC_CONCURRENCY_LOCK"

    # Logic / assertion drift
    if "assertionerror" in text_lower or "assert " in text_lower:
        return "LOGIC_ASSERTION_DRIFT"

    # Type / contract mismatch
    if any(k in text_lower for k in ("typeerror", "attributeerror", "e0308")) or bool(re.search(r'\bTS\d+\b', text, re.IGNORECASE)):
        return "TYPE_CONTRACT_MISMATCH"

    if (vertex or "").lower() == "codebase":
        return "LOGIC_ASSERTION_DRIFT"

    return ""


def init_harness_ledger(db_path: Optional[Union[str, Path]] = None) -> None:
    """Initialize harness_failures and settings_reviews schema if not existing."""
    p = get_registry_db_path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p), timeout=0.5)
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
            CREATE TABLE IF NOT EXISTS settings_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                reason TEXT NOT NULL,
                event_count INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS harness_golden_dataset (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL,
                conv_id TEXT DEFAULT '',
                vertex TEXT DEFAULT '',
                failure_type TEXT DEFAULT '',
                bug_category TEXT DEFAULT '',
                input_signature TEXT NOT NULL,
                failing_trajectory_json TEXT DEFAULT '[]',
                expected_mode TEXT DEFAULT 'subset',
                expected_tools_json TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(slug, input_signature)
            );
            """
        )
        # Idempotently add missing columns on existing tables
        cur.execute("PRAGMA table_info(harness_failures);")
        existing_cols = {row[1] for row in cur.fetchall()}
        if "bug_category" not in existing_cols:
            cur.execute("ALTER TABLE harness_failures ADD COLUMN bug_category TEXT DEFAULT '';")
        if "error_type" not in existing_cols:
            cur.execute("ALTER TABLE harness_failures ADD COLUMN error_type TEXT DEFAULT '';")
        if "remedy" not in existing_cols:
            cur.execute("ALTER TABLE harness_failures ADD COLUMN remedy TEXT DEFAULT '';")
        conn.commit()
        _INITIALIZED_LEDGER_DBS.add(str(Path(p).resolve()))
    finally:
        conn.close()


def _normalize_sentinel_tool(tool_name: str) -> str:
    """Canonicalize dual CLI and IDE tool names in sentinel failure classification."""
    t = str(tool_name or "").strip().lower()
    if t in ("view_file", "read_file", "view_file / read_file"):
        return "read_file"
    if t in ("write_to_file", "write_file"):
        return "write_file"
    if t in ("replace_file_content", "multi_replace_file_content", "edit_file"):
        return "edit_file"
    return t


def _maybe_record_golden_dataset_entry(
    cur: sqlite3.Cursor,
    slug: str,
    conv_id: str,
    vertex: str,
    failure_type: str,
    tool_name: str,
    severity_tier: str,
    reason: str,
    bug_category: str,
    failing_trajectory_json: str = "",
    expected_mode: str = "subset",
    expected_tools_json: str = "",
) -> None:
    """Synthesize golden regression dataset row on S0/S1 or SPEC_GAMING_ATTEMPT failures."""
    if severity_tier not in ("S0_catastrophic", "S1_critical") and bug_category != "SPEC_GAMING_ATTEMPT":
        return
    canon_tool = _normalize_sentinel_tool(tool_name)
    sig = f"{vertex}:{failure_type}:{canon_tool}:{(reason or '')[:120]}"
    if not failing_trajectory_json:
        failing_trajectory_json = json.dumps([canon_tool] if canon_tool else [])
    if not expected_tools_json:
        base_expected = ["read_file", "edit_file", "write_file", "run_command", "call_mcp_tool"]
        if canon_tool and canon_tool not in base_expected:
            base_expected.insert(0, canon_tool)
        expected_tools_json = json.dumps(base_expected)
    cur.execute(
        """
        INSERT OR IGNORE INTO harness_golden_dataset (
            slug, conv_id, vertex, failure_type, bug_category,
            input_signature, failing_trajectory_json, expected_mode, expected_tools_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            slug or "default",
            conv_id or "",
            vertex or "hook",
            failure_type or "",
            bug_category or "",
            sig,
            failing_trajectory_json,
            expected_mode or "subset",
            expected_tools_json,
        ),
    )


def classify_vertex(failure_type: str, tool_name: str = "", reason: str = "") -> str:
    """Map failure signature to one of 5 symbolic vertices: hook, skill, tool_guidance, routing, codebase."""
    ft = failure_type.lower()
    tn = _normalize_sentinel_tool(tool_name)
    r = reason.lower()

    # 1. Codebase: syntax errors, AST breaks, test assertions
    if (
        ft in ("syntax_error", "ast_break", "test_assertion_lock", "test_lock_violation", "compile_error")
        or "syntax" in r
        or "debugger test-assertion lock" in r
        or "broken syntax" in r
        or (
            tn in ("write_file", "edit_file")
            and ("test-immutability" in r or "fix-the-code-not-the-test" in r or "assertion" in r)
        )
    ):
        return "codebase"

    # 2. Routing: subagent prompt ceiling, invalid roles/types, model routing
    if (
        tn == "invoke_subagent"
        and ("prompt" in r or "ceiling" in r or "role" in r or "typename" in r or "model" in r)
    ) or ft in ("routing_error", "subagent_prompt_overflow", "model_violation"):
        return "routing"

    # 3. Tool Guidance: search flood guards, legacy CLI blocks, slice cap, read-budget strikes/locks, task polling
    if (
        ft in (
            "flood_guard",
            "legacy_cli_blocked",
            "slice_cap_exceeded",
            "read_budget_strike",
            "read_budget_lock",
            "task_polling_blocked",
        )
        or "flood" in r
        or "legacy" in r
        or "slice cap" in r
        or "read budget" in r
        or "three-strike file read" in r
        or "polling" in r
        or (
            tn == "read_file"
            and ("slice" in r or "outline-first" in r or "monolithic" in r or "scout-block" in r)
        )
    ):
        return "tool_guidance"

    # 4. Skill: gate blocks, jev loops, allowed_files lease violations, PRD/plan gates
    if (
        ft in (
            "gate_block",
            "jev_loop",
            "lease_violation",
            "oracle_plan_gate",
            "teardown_gate",
            "verification_gate",
            "simplify_gate",
        )
        or "jev" in r
        or "lease invariant" in r
        or "oracle plan gate" in r
        or "teardown gate" in r
        or "verification gate" in r
        or "simplify" in r
    ):
        return "skill"

    # 5. Hook: hook unhandled crashes, hook immunity violations
    if ft in ("hook_crash", "hook_immunity_violation", "hook_error") or "hook immunity" in r or "hook crash" in r:
        return "hook"

    return "hook"


def classify_severity(failure_type: str, reason: str = "") -> Tuple[str, float]:
    """Map failure characteristics to severity tier and weight."""
    ft = failure_type.lower()
    r = reason.lower()

    # S0: catastrophic (1.00)
    if "jev" in r or "jev_loop" in ft or "hook immunity" in r or "hook_crash" in ft:
        return "S0_catastrophic", SEVERITY_WEIGHTS["S0_catastrophic"]

    # S1: critical (0.25)
    if (
        "syntax" in r
        or ft in ("syntax_error", "ast_break")
        or "debugger test-assertion lock" in r
        or "oracle plan gate" in r
        or "verification gate alert" in r
    ):
        return "S1_critical", SEVERITY_WEIGHTS["S1_critical"]

    # S2: major (0.05)
    if (
        "three-strike file read" in r
        or "read_budget" in ft
        or "6-slice" in r
        or "lease invariant" in r
        or "6,000" in r
        or "teardown gate" in r
        or "simplify" in r
    ):
        return "S2_major", SEVERITY_WEIGHTS["S2_major"]

    # S3: minor (0.01) - default
    return "S3_minor", SEVERITY_WEIGHTS["S3_minor"]


def record_harness_failure(
    conv_id: str,
    failure_type: str,
    slug: str = "default",
    tool_name: str = "",
    reason: str = "",
    details: str = "",
    severity_tier: Optional[str] = None,
    vertex: Optional[str] = None,
    session_type: str = "top_level",
    db_path: Optional[Union[str, Path]] = None,
    bug_category: str = "",
    error_type: str = "",
    remedy: str = "",
    resolved_at: Optional[str] = None,
) -> bool:
    """Non-blocking (<10ms) failure logger with test isolation and pending-queue fallback."""
    # Test isolation guard prevents synthetic test runs from polluting live ledger
    is_test_env = "unittest" in sys.modules or "pytest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))
    if is_test_env and not os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB") and not db_path:
        return False

    if not os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB") and not db_path:
        slug_lower = (slug or "").lower()
        if slug_lower.startswith(("test-alias", "tmp", ".tmp_")):
            return False

    if not severity_tier or severity_tier not in SEVERITY_WEIGHTS:
        severity_tier, severity_weight = classify_severity(failure_type, reason)
    else:
        severity_weight = SEVERITY_WEIGHTS[severity_tier]

    if not vertex:
        vertex = classify_vertex(failure_type, tool_name, reason)

    if not bug_category:
        bug_category = classify_bug_category(error_type=error_type, message=details, reason=reason, vertex=vertex)

    db_target = get_registry_db_path(db_path)
    db_key = str(Path(db_target).resolve())

    # Attempt direct SQLite insert with tight 100ms lock budget
    try:
        if db_key not in _INITIALIZED_LEDGER_DBS or not Path(db_target).is_file():
            init_harness_ledger(db_target)
        conn = sqlite3.connect(str(db_target), timeout=0.1)
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA busy_timeout=100;")
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
                    slug,
                    session_type,
                    vertex,
                    failure_type,
                    tool_name,
                    severity_tier,
                    severity_weight,
                    reason,
                    details,
                    bug_category,
                    error_type,
                    remedy,
                    resolved_at,
                ),
            )
            _maybe_record_golden_dataset_entry(
                cur,
                slug=slug,
                conv_id=conv_id,
                vertex=vertex,
                failure_type=failure_type,
                tool_name=tool_name,
                severity_tier=severity_tier,
                reason=reason,
                bug_category=bug_category,
            )
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception:
        # Fallback to pending JSONL file on lock contention or write error
        _append_pending_failure({
            "conv_id": conv_id,
            "slug": slug,
            "session_type": session_type,
            "vertex": vertex,
            "failure_type": failure_type,
            "tool_name": tool_name,
            "severity_tier": severity_tier,
            "severity_weight": severity_weight,
            "reason": reason,
            "details": details,
            "bug_category": bug_category,
            "error_type": error_type,
            "remedy": remedy,
            "resolved_at": resolved_at,
            "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        })
        return False


def _append_pending_failure(record: Dict[str, Any]) -> None:
    """Atomically append a pending failure record to /tmp/.antigravity_failures_pending.jsonl."""
    try:
        with open(PENDING_FAILURES_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass


def drain_pending_failures(db_path: Optional[Union[str, Path]] = None) -> int:
    """Flush pending failures from /tmp queue into SQLite ledger."""
    if not PENDING_FAILURES_PATH.is_file():
        return 0

    proc_path = PENDING_FAILURES_PATH.with_name(
        f"{PENDING_FAILURES_PATH.name}.{os.getpid()}.{time.time_ns()}.tmp"
    )
    try:
        os.replace(PENDING_FAILURES_PATH, proc_path)
    except OSError:
        return 0

    records: List[Dict[str, Any]] = []
    try:
        lines = proc_path.read_text(encoding="utf-8").splitlines()
        for line in lines:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        try:
            proc_path.unlink()
        except Exception:
            pass
        return 0

    if not records:
        try:
            proc_path.unlink()
        except Exception:
            pass
        return 0

    db_target = get_registry_db_path(db_path)
    init_harness_ledger(db_target)
    conn = sqlite3.connect(str(db_target), timeout=1.0)
    drained = 0
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA busy_timeout=1000;")
        for rec in records:
            vtx = rec.get("vertex", "hook")
            err_t = rec.get("error_type", "")
            det = rec.get("details", "")
            rsn = rec.get("reason", "")
            b_cat = rec.get("bug_category", "") or classify_bug_category(error_type=err_t, message=det, reason=rsn, vertex=vtx)
            rem = rec.get("remedy", "")
            res_at = rec.get("resolved_at")
            cur.execute(
                """
                INSERT INTO harness_failures (
                    conv_id, slug, session_type, vertex, failure_type,
                    tool_name, severity_tier, severity_weight, reason, details,
                    bug_category, error_type, remedy, resolved_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec.get("conv_id", ""),
                    rec.get("slug", "default"),
                    rec.get("session_type", "top_level"),
                    vtx,
                    rec.get("failure_type", ""),
                    rec.get("tool_name", ""),
                    rec.get("severity_tier", "S3_minor"),
                    float(rec.get("severity_weight", 0.01)),
                    rsn,
                    det,
                    b_cat,
                    err_t,
                    rem,
                    res_at,
                    rec.get("created_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
                ),
            )
            _maybe_record_golden_dataset_entry(
                cur,
                slug=rec.get("slug", "default"),
                conv_id=rec.get("conv_id", ""),
                vertex=vtx,
                failure_type=rec.get("failure_type", ""),
                tool_name=rec.get("tool_name", ""),
                severity_tier=rec.get("severity_tier", "S3_minor"),
                reason=rsn,
                bug_category=b_cat,
            )
            drained += 1
        conn.commit()
        try:
            proc_path.unlink()
        except Exception:
            pass
    finally:
        conn.close()

    return drained


def evaluate_burn_rate(
    slug: Optional[str] = None,
    db_path: Optional[Union[str, Path]] = None,
    evolution_file: Optional[Union[str, Path]] = None,
) -> Dict[str, Any]:
    """Compute rolling burn rate, check threshold breach, and idempotently escalate to settings_reviews."""
    db_target = get_registry_db_path(db_path)
    init_harness_ledger(db_target)

    conn = sqlite3.connect(str(db_target), timeout=1.0)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA busy_timeout=1000;")

        # 1. Unreviewed failures
        if slug:
            cur.execute(
                """
                SELECT id, conv_id, slug, severity_tier, severity_weight, created_at
                FROM harness_failures
                WHERE resolved_at IS NULL AND settings_review_id IS NULL AND slug = ?
                ORDER BY id ASC
                """,
                (slug,),
            )
        else:
            cur.execute(
                """
                SELECT id, conv_id, slug, severity_tier, severity_weight, created_at
                FROM harness_failures
                WHERE resolved_at IS NULL AND settings_review_id IS NULL
                ORDER BY id ASC
                """
            )
        unreviewed = cur.fetchall()
        unreviewed_ids = [r[0] for r in unreviewed]
        unreviewed_count = len(unreviewed)
        unreviewed_weight = sum(float(r[4]) for r in unreviewed) if unreviewed else 0.0
        s0_count = sum(1 for r in unreviewed if r[3] == "S0_catastrophic")

        # 2. Rolling short-window burn rate BR(W_short = 10) = sum(w_k) / (10 * 0.02)
        # With zero-division guard returning 0.0 on empty ledger
        if slug:
            cur.execute(
                "SELECT severity_weight FROM harness_failures WHERE slug = ? ORDER BY id DESC LIMIT 10",
                (slug,),
            )
        else:
            cur.execute("SELECT severity_weight FROM harness_failures ORDER BY id DESC LIMIT 10")
        recent_10 = cur.fetchall()

        if not recent_10:
            burn_rate_short = 0.0
        else:
            w_sum = sum(float(r[0]) for r in recent_10)
            burn_rate_short = w_sum / (10.0 * 0.02)  # w_sum / 0.20

        # 3. Check time elapsed since last evolution
        interval_due = False
        evo_path = Path(evolution_file) if evolution_file else (Path.home() / ".gemini" / "last_harness_evolution.json")
        if evo_path.is_file():
            try:
                evo_data = json.loads(evo_path.read_text(encoding="utf-8"))
                ts_raw = evo_data.get("last_run_timestamp") or evo_data.get("timestamp")
                last_ts: Optional[float] = None
                if isinstance(ts_raw, str):
                    try:
                        last_ts = datetime.datetime.fromisoformat(ts_raw).timestamp()
                    except Exception:
                        last_ts = float(ts_raw)
                elif isinstance(ts_raw, (int, float)):
                    last_ts = float(ts_raw)

                session_cnt = int(evo_data.get("session_count", 0))
                if last_ts is not None:
                    elapsed = time.time() - last_ts
                    if (elapsed >= 86400.0 or session_cnt >= 15) and unreviewed_count >= 1:
                        interval_due = True
            except Exception:
                pass
        else:
            if unreviewed_count >= 15:
                interval_due = True

        # Escalation trigger conditions
        should_escalate = (
            s0_count >= 1
            or burn_rate_short >= 3.0
            or unreviewed_weight >= 1.0
            or interval_due
        )

        review_id: Optional[int] = None
        if should_escalate and unreviewed_ids:
            target_slug = slug if slug else (unreviewed[0][2] if unreviewed else "default")
            # Idempotent escalation: reuse existing unresolved review if present
            cur.execute(
                "SELECT id, event_count FROM settings_reviews WHERE slug = ? AND resolved_at IS NULL ORDER BY id DESC LIMIT 1",
                (target_slug,),
            )
            existing_rev = cur.fetchone()
            if existing_rev:
                review_id = existing_rev[0]
                new_event_count = existing_rev[1] + unreviewed_count
                cur.execute(
                    "UPDATE settings_reviews SET event_count = ? WHERE id = ?",
                    (new_event_count, review_id),
                )
            else:
                triggers = []
                if s0_count >= 1:
                    triggers.append(f"{s0_count} S0 catastrophic events")
                if burn_rate_short >= 3.0:
                    triggers.append(f"burn rate spike (BR={burn_rate_short:.2f} >= 3.0)")
                if unreviewed_weight >= 1.0:
                    triggers.append(f"severity weight ({unreviewed_weight:.2f} >= 1.0)")
                if interval_due:
                    triggers.append("time/session interval due")
                reason_desc = f"Burn-Rate Sentinel Escalation: {', '.join(triggers)}"
                cur.execute(
                    "INSERT INTO settings_reviews (slug, reason, event_count) VALUES (?, ?, ?)",
                    (target_slug, reason_desc, unreviewed_count),
                )
                review_id = cur.lastrowid

            # Link unreviewed failures to review_id
            placeholders = ",".join("?" for _ in unreviewed_ids)
            cur.execute(
                f"UPDATE harness_failures SET settings_review_id = ? WHERE id IN ({placeholders})",
                [review_id] + unreviewed_ids,
            )
            conn.commit()

        return {
            "unreviewed_count": unreviewed_count,
            "unreviewed_weight": round(unreviewed_weight, 4),
            "s0_count": s0_count,
            "burn_rate_short": round(burn_rate_short, 4),
            "interval_due": interval_due,
            "escalated": should_escalate,
            "settings_review_id": review_id,
        }
    finally:
        conn.close()


# ==============================================================================
# Self-Test Suite
# ==============================================================================

def run_self_test() -> bool:
    """Run self-contained verification suite in temporary isolated SQLite db."""
    import tempfile
    global PENDING_FAILURES_PATH

    with tempfile.TemporaryDirectory() as td:
        orig_pending = PENDING_FAILURES_PATH
        PENDING_FAILURES_PATH = Path(td) / "test_pending.jsonl"
        test_db = Path(td) / "test_registry.sqlite"
        os.environ["ANTIGRAVITY_TEST_REGISTRY_DB"] = str(test_db)
        try:
            # 1. Schema & Weights Verification
            init_harness_ledger(test_db)
            assert test_db.is_file(), "Ledger database was not created."

            # Verify severity weights
            assert SEVERITY_WEIGHTS["S0_catastrophic"] == 1.00
            assert SEVERITY_WEIGHTS["S1_critical"] == 0.25
            assert SEVERITY_WEIGHTS["S2_major"] == 0.05
            assert SEVERITY_WEIGHTS["S3_minor"] == 0.01

            # 2. Symbolic Vertex Classification & Bug Taxonomy
            assert classify_vertex("syntax_error", "write_to_file", "SyntaxError in foo.py") == "codebase"
            assert classify_vertex("test_lock_violation", "write_to_file", "Debugger Test-Assertion Lock") == "codebase"
            assert classify_vertex("routing_error", "invoke_subagent", "Prompt exceeded 6,000 character ceiling") == "routing"
            assert classify_vertex("flood_guard", "run_command", "Search flood guard") == "tool_guidance"
            assert classify_vertex("read_budget_strike", "view_file", "Three-Strike File Read Gate") == "tool_guidance"
            assert classify_vertex("jev_loop", "run_command", "Jev Loop Circuit Breaker ACTIVATED") == "skill"
            assert classify_vertex("gate_block", "stop", "Oracle Plan Gate Alert") == "skill"
            assert classify_vertex("hook_crash", "", "Unexpected hook error") == "hook"

            # Bug category taxonomy verification
            assert classify_bug_category(error_type="AssertionError") == "LOGIC_ASSERTION_DRIFT"
            assert classify_bug_category(error_type="TypeError") == "TYPE_CONTRACT_MISMATCH"
            assert classify_bug_category(error_type="TS2322") == "TYPE_CONTRACT_MISMATCH"
            assert classify_bug_category(error_type="E0308") == "TYPE_CONTRACT_MISMATCH"
            assert classify_bug_category(error_type="IndexError") == "BOUNDARY_INDEX_ERROR"
            assert classify_bug_category(message="division by zero", reason="ZeroDivisionError") == "BOUNDARY_INDEX_ERROR"
            assert classify_bug_category(message="'NoneType' object has no attribute 'val'") == "NULL_UNDEFINED_ACCESS"
            assert classify_bug_category(error_type="ImportError") == "IMPORT_DEPENDENCY_GAP"
            assert classify_bug_category(error_type="TimeoutError") == "ASYNC_CONCURRENCY_LOCK"
            assert classify_bug_category(error_type="FileNotFoundError") == "RESOURCE_IO_LIFECYCLE"
            assert classify_bug_category(reason="test_assertion_lock") == "SPEC_GAMING_ATTEMPT"
            assert classify_bug_category(reason="oracle custody") == "SPEC_GAMING_ATTEMPT"
            assert classify_bug_category(vertex="codebase") == "LOGIC_ASSERTION_DRIFT"
            assert classify_bug_category() == ""

            # 3. Zero-Division Guard on Empty Ledger
            test_evo = Path(td) / "test_evolution.json"
            test_evo.write_text(
                json.dumps({
                    "last_run_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "session_count": 0,
                }),
                encoding="utf-8",
            )
            res_empty = evaluate_burn_rate(db_path=test_db, evolution_file=test_evo)
            assert res_empty["burn_rate_short"] == 0.0, "Empty ledger must return burn_rate_short = 0.0"
            assert res_empty["unreviewed_weight"] == 0.0
            assert res_empty["escalated"] is False

            # 4. Record Failures and Test Multi-Window Burn Rate Escalation
            conv = "conv_test_123"
            # Record an S3 failure (weight 0.01)
            record_harness_failure(conv, "flood_guard", slug="test_proj", tool_name="run_command", reason="Flood guard", db_path=test_db)
            res1 = evaluate_burn_rate(slug="test_proj", db_path=test_db, evolution_file=test_evo)
            assert res1["unreviewed_count"] == 1
            assert res1["unreviewed_weight"] == 0.01
            assert res1["escalated"] is False

            # Record an S0 failure (weight 1.00) -> Should immediately trigger escalation!
            record_harness_failure(conv, "jev_loop", slug="test_proj", tool_name="run_command", reason="Jev loop circuit breaker", db_path=test_db)
            res2 = evaluate_burn_rate(slug="test_proj", db_path=test_db, evolution_file=test_evo)
            assert res2["s0_count"] == 1
            assert res2["escalated"] is True
            assert res2["settings_review_id"] is not None

            # Verify settings_reviews escalation linkage in DB
            conn = sqlite3.connect(str(test_db))
            cur = conn.cursor()
            cur.execute("SELECT id, slug, event_count FROM settings_reviews WHERE id = ?", (res2["settings_review_id"],))
            s_row = cur.fetchone()
            assert s_row is not None and s_row[1] == "test_proj" and s_row[2] == 2

            # Verify harness_failures are linked
            cur.execute("SELECT COUNT(*) FROM harness_failures WHERE settings_review_id = ?", (res2["settings_review_id"],))
            linked_cnt = cur.fetchone()[0]
            assert linked_cnt == 2, f"Expected 2 linked failures, found {linked_cnt}"
            conn.close()

            # 5. Idempotent Escalation
            # Add another failure, evaluate again; should update existing open settings_review
            record_harness_failure(conv, "syntax_error", slug="test_proj", tool_name="write_to_file", reason="Broken syntax", db_path=test_db)
            res3 = evaluate_burn_rate(slug="test_proj", db_path=test_db, evolution_file=test_evo)
            # S1 (0.25) -> unreviewed_weight = 0.25 (not >= 1.0 and no s0 in this unreviewed batch), but BR_short includes prior S0 (1.00) + S3 (0.01) + S1 (0.25) = 1.26 / 0.20 = 6.30 >= 3.0!
            assert res3["burn_rate_short"] >= 3.0, f"Expected BR >= 3.0, got {res3['burn_rate_short']}"
            assert res3["escalated"] is True
            assert res3["settings_review_id"] == res2["settings_review_id"], "Did not reuse existing open settings_review"

            # 6. Test Pending Queue Fallback and Drain
            pending_rec = {
                "conv_id": "conv_fallback",
                "slug": "test_proj",
                "session_type": "top_level",
                "vertex": "tool_guidance",
                "failure_type": "slice_cap_exceeded",
                "tool_name": "view_file",
                "severity_tier": "S3_minor",
                "severity_weight": 0.01,
                "reason": "Exceeded 250 line slice cap",
                "details": "",
            }
            _append_pending_failure(pending_rec)
            assert PENDING_FAILURES_PATH.is_file(), "Pending failures file was not created."
            drained = drain_pending_failures(db_path=test_db)
            assert drained >= 1, "Failed to drain pending failures into DB."
            assert not PENDING_FAILURES_PATH.is_file(), "Pending failures file was not unlinked after drain."

            print("=== Burn-Rate Sentinel Self-Test: ALL PASS ===")
            return True
        finally:
            PENDING_FAILURES_PATH = orig_pending
            os.environ.pop("ANTIGRAVITY_TEST_REGISTRY_DB", None)


def main() -> int:
    parser = argparse.ArgumentParser(description="Antigravity Cross-Session Burn-Rate Sentinel")
    parser.add_argument("--self-test", action="store_true", help="Run self-test suite")
    parser.add_argument("--record-json", metavar="JSON", help="Record failure from JSON payload string")
    parser.add_argument("--evaluate", "--check-threshold", dest="evaluate", action="store_true", help="Evaluate burn rate and escalate if breached")
    parser.add_argument("--slug", default=None, help="Project slug for scoping evaluation")
    parser.add_argument("--drain-pending", action="store_true", help="Drain pending failure logs into SQLite ledger")
    parser.add_argument("--db-path", default=None, help="Custom SQLite DB path")

    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        return 0

    if args.drain_pending:
        count = drain_pending_failures(args.db_path)
        print(f"Drained {count} pending failures into registry.")
        return 0

    if args.record_json:
        data = json.loads(args.record_json)
        success = record_harness_failure(
            conv_id=data.get("conv_id", "unknown"),
            failure_type=data.get("failure_type", "unspecified"),
            slug=data.get("slug", "default"),
            tool_name=data.get("tool_name", ""),
            reason=data.get("reason", ""),
            details=data.get("details", ""),
            severity_tier=data.get("severity_tier"),
            vertex=data.get("vertex"),
            session_type=data.get("session_type", "top_level"),
            db_path=args.db_path,
            bug_category=data.get("bug_category", ""),
            error_type=data.get("error_type", ""),
            remedy=data.get("remedy", ""),
            resolved_at=data.get("resolved_at"),
        )
        print(json.dumps({"success": success}))
        return 0

    if args.evaluate:
        result = evaluate_burn_rate(slug=args.slug, db_path=args.db_path)
        print(json.dumps(result, indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

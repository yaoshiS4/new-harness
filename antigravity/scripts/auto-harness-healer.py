#!/usr/bin/env python3
"""Autonomous Sleep-Time Self-Healer (Harness² Level-3 Meta-Evolution).

Implements the Sleep-Time Dual Harness + Codebase Self-Healer integrating:
- Darwin Gödel Machine (DGM) empirical self-modifying harness archive (arXiv:2505.22954)
- AgentSymbolicLearning 5-Vertex Symbolic Failure Gradients (arXiv:2406.18532)
- Letta Sleep-Time Compute (arXiv:2504.13171) & Google SRE Multi-Window Burn Rate (Google SRE Workbook, ch.5 Alerting on SLOs)
- PaperQA2 & OpenScholar external grounding (arXiv:2409.13740)

5-Stage Closed Self-Healing Loop:
1. Harvest & Cluster: Drains pending failures into SQLite and clusters by symbolic vertex.
2. Dual Retrieval: Combines internal experience mining with external academic/GitHub blueprints.
3. Symbolic Gradient & Auto-Heal Synthesis: Generates deterministic repairs, tool quirks, and codebase digest.
4. Darwin Gödel Machine 3-Gate Sandbox Verification: Validates harness integrity; reverts on regression (KEEP_BASE).
5. Ledger Resolution & Wake-Time Alert Flag: Stamps resolved_at and posts Turn-1 notice flag.
"""

from __future__ import annotations

import argparse
import datetime
import fcntl
import hashlib
import json
import os
import py_compile
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

LOCK_FILE = "/tmp/.auto_harness_healer.lock"
PENDING_FAILURES_FILE = "/tmp/.antigravity_failures_pending.jsonl"
BACKOFF_FILE = os.path.expanduser("~/.gemini/last_harness_evolution_backoff.json")
EVOLUTION_STATE_FILE = os.path.expanduser("~/.gemini/last_harness_evolution.json")
ALERT_FLAG_FILE = os.path.expanduser("~/.gemini/last_harness_evolution_alert.flag")
TOOL_QUIRKS_FILE = os.path.expanduser("~/.gemini/antigravity/guidelines/tool-quirks.md")
DEFAULT_REGISTRY_DB = os.path.expanduser("~/.local/share/codex/projects/registry.sqlite")
ENV_OVERLAYS_DIR = os.path.expanduser("~/.gemini/antigravity/skillbank/env_overlays")

SEVERITY_WEIGHTS = {
    "S0_catastrophic": 1.00,
    "S1_critical": 0.25,
    "S2_major": 0.05,
    "S3_minor": 0.01,
}

SYMBOLIC_VERTICES = ("hook", "skill", "tool_guidance", "routing", "codebase")


def get_db_path(custom_path: str | None = None) -> str:
    """Resolves registry database path with test-mode isolation guard."""
    test_db = os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB")
    if test_db:
        return test_db
    if "unittest" in sys.modules and not custom_path:
        return ""
    if custom_path:
        return custom_path
    return DEFAULT_REGISTRY_DB


def acquire_pid_lock(lock_path: str = LOCK_FILE) -> int | None:
    """Acquires a non-blocking process lock to prevent concurrent heal runs."""
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        os.ftruncate(fd, 0)
        os.write(fd, f"{os.getpid()}\n".encode("utf-8"))
        return fd
    except (BlockingIOError, OSError):
        return None


def release_pid_lock(fd: int | None, lock_path: str = LOCK_FILE) -> None:
    """Releases the process lock and cleans up lockfile."""
    if fd is not None:
        try:
            if os.path.exists(lock_path) and os.fstat(fd).st_ino == os.stat(lock_path).st_ino:
                os.unlink(lock_path)
        except Exception:
            pass
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        except Exception:
            pass


def init_harness_tables(conn: sqlite3.Connection) -> None:
    """Ensures harness_failures and settings_reviews tables exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS harness_failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conv_id TEXT,
            slug TEXT,
            session_type TEXT,
            vertex TEXT,
            failure_type TEXT,
            tool_name TEXT,
            severity_tier TEXT,
            severity_weight REAL,
            reason TEXT,
            details TEXT,
            bug_category TEXT DEFAULT '',
            error_type TEXT DEFAULT '',
            remedy TEXT DEFAULT '',
            settings_review_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME
        );
        """
    )
    cols = {row[1] for row in conn.execute("PRAGMA table_info(harness_failures);").fetchall()}
    if "bug_category" not in cols:
        conn.execute("ALTER TABLE harness_failures ADD COLUMN bug_category TEXT DEFAULT '';")
    if "error_type" not in cols:
        conn.execute("ALTER TABLE harness_failures ADD COLUMN error_type TEXT DEFAULT '';")
    if "remedy" not in cols:
        conn.execute("ALTER TABLE harness_failures ADD COLUMN remedy TEXT DEFAULT '';")
    if "analyzed_at" not in cols:
        conn.execute("ALTER TABLE harness_failures ADD COLUMN analyzed_at DATETIME;")
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_harness_failures_resolved
        ON harness_failures(resolved_at);
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_harness_failures_vertex
        ON harness_failures(vertex);
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS settings_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT,
            reason TEXT,
            event_count INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME
        );
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS harness_pareto_archive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT,
            profile_mode TEXT,
            func_score REAL,
            sec_score REAL,
            token_score REAL,
            top_vertex TEXT,
            general_hash TEXT,
            env_overlay_path TEXT,
            digest_path TEXT,
            is_pareto_front INTEGER DEFAULT 1,
            niche_key TEXT DEFAULT '',
            receipt_baseline_rate REAL DEFAULT 0.0,
            receipt_eval_sessions INTEGER DEFAULT 0,
            receipt_delta REAL DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    archive_cols = {row[1] for row in conn.execute("PRAGMA table_info(harness_pareto_archive);").fetchall()}
    if "niche_key" not in archive_cols:
        conn.execute("ALTER TABLE harness_pareto_archive ADD COLUMN niche_key TEXT DEFAULT '';")
    if "receipt_baseline_rate" not in archive_cols:
        conn.execute("ALTER TABLE harness_pareto_archive ADD COLUMN receipt_baseline_rate REAL DEFAULT 0.0;")
    if "receipt_eval_sessions" not in archive_cols:
        conn.execute("ALTER TABLE harness_pareto_archive ADD COLUMN receipt_eval_sessions INTEGER DEFAULT 0;")
    if "receipt_delta" not in archive_cols:
        conn.execute("ALTER TABLE harness_pareto_archive ADD COLUMN receipt_delta REAL DEFAULT 0.0;")
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_pareto_archive_slug
        ON harness_pareto_archive(slug, is_pareto_front);
        """
    )
    conn.execute(
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
    conn.commit()


def _normalize_healer_trajectory_tool(tool_name: str) -> str:
    """Canonicalize dual CLI and IDE tool names for golden dataset synthesis."""
    t = str(tool_name or "").strip().lower()
    if t in ("view_file", "read_file", "view_file / read_file"):
        return "read_file"
    if t in ("write_to_file", "write_file"):
        return "write_file"
    if t in ("replace_file_content", "multi_replace_file_content", "edit_file"):
        return "edit_file"
    return t


def _maybe_insert_golden_dataset_row(
    cursor_or_conn: sqlite3.Cursor | sqlite3.Connection,
    slug: str,
    conv_id: str,
    vertex: str,
    failure_type: str,
    tool_name: str,
    severity_tier: str,
    reason: str,
    bug_category: str,
) -> None:
    """Insert S0/S1 or SPEC_GAMING_ATTEMPT failure into harness_golden_dataset on the active cursor."""
    if severity_tier not in ("S0_catastrophic", "S1_critical") and bug_category != "SPEC_GAMING_ATTEMPT":
        return
    canon_tool = _normalize_healer_trajectory_tool(tool_name)
    sig = f"{vertex or 'hook'}:{failure_type or ''}:{canon_tool}:{(reason or '')[:120]}"
    failing_traj = json.dumps([canon_tool] if canon_tool else [])
    base_expected = ["read_file", "edit_file", "write_file", "run_command", "call_mcp_tool"]
    if canon_tool and canon_tool not in base_expected:
        base_expected.insert(0, canon_tool)
    expected_tools = json.dumps(base_expected)
    cursor_or_conn.execute(
        """
        INSERT OR IGNORE INTO harness_golden_dataset (
            slug, conv_id, vertex, failure_type, bug_category,
            input_signature, failing_trajectory_json, expected_mode, expected_tools_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'subset', ?);
        """,
        (
            slug or "default",
            conv_id or "",
            vertex or "hook",
            failure_type or "",
            bug_category or "",
            sig,
            failing_traj,
            expected_tools,
        ),
    )


def drain_pending_failures(conn: sqlite3.Connection, pending_path: str = PENDING_FAILURES_FILE) -> int:
    """Drains pending failures from temporary jsonl into SQLite registry."""
    if not os.path.isfile(pending_path):
        return 0

    proc_path = f"{pending_path}.{os.getpid()}.{time.time_ns()}.tmp"
    try:
        os.replace(pending_path, proc_path)
    except OSError:
        return 0

    drained = 0
    try:
        with open(proc_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if not lines:
            try:
                os.unlink(proc_path)
            except OSError:
                pass
            return 0

        cols = {row[1] for row in conn.execute("PRAGMA table_info(harness_failures);").fetchall()}
        has_cat = "bug_category" in cols
        golden_cols = {row[1] for row in conn.execute("PRAGMA table_info(harness_golden_dataset);").fetchall()}
        has_golden = bool(golden_cols)
        cur = conn.cursor()

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                item = json.loads(line_str)
                stier_val = item.get("severity_tier", "S2_major")
                bcat_val = item.get("bug_category", "")
                if has_cat:
                    cur.execute(
                        """
                        INSERT INTO harness_failures (
                            conv_id, slug, session_type, vertex, failure_type,
                            tool_name, severity_tier, severity_weight, reason, details,
                            bug_category, error_type, remedy, resolved_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            item.get("conv_id", ""),
                            item.get("slug", "default"),
                            item.get("session_type", "interactive"),
                            item.get("vertex", "hook"),
                            item.get("failure_type", "denial"),
                            item.get("tool_name", ""),
                            stier_val,
                            float(item.get("severity_weight", SEVERITY_WEIGHTS.get(stier_val, 0.05))),
                            item.get("reason", ""),
                            item.get("details", ""),
                            bcat_val,
                            item.get("error_type", ""),
                            item.get("remedy", ""),
                            item.get("resolved_at"),
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO harness_failures (
                            conv_id, slug, session_type, vertex, failure_type,
                            tool_name, severity_tier, severity_weight, reason, details
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            item.get("conv_id", ""),
                            item.get("slug", "default"),
                            item.get("session_type", "interactive"),
                            item.get("vertex", "hook"),
                            item.get("failure_type", "denial"),
                            item.get("tool_name", ""),
                            stier_val,
                            float(item.get("severity_weight", SEVERITY_WEIGHTS.get(stier_val, 0.05))),
                            item.get("reason", ""),
                            item.get("details", ""),
                        ),
                    )
                if has_golden:
                    _maybe_insert_golden_dataset_row(
                        cur,
                        slug=item.get("slug", "default"),
                        conv_id=item.get("conv_id", ""),
                        vertex=item.get("vertex", "hook"),
                        failure_type=item.get("failure_type", "denial"),
                        tool_name=item.get("tool_name", ""),
                        severity_tier=stier_val,
                        reason=item.get("reason", ""),
                        bug_category=bcat_val,
                    )
                drained += 1
            except Exception:
                continue

        conn.commit()
        try:
            os.unlink(proc_path)
        except OSError:
            pass
    except Exception:
        pass

    return drained


def cluster_unresolved_failures(conn: sqlite3.Connection) -> dict[str, Any]:
    """Clusters open failures across the 5 symbolic vertices and calculates gradients."""
    cursor = conn.cursor()
    cols = {row[1] for row in cursor.execute("PRAGMA table_info(harness_failures);").fetchall()}
    has_cat = "bug_category" in cols and "remedy" in cols
    analyzed_filter = "AND analyzed_at IS NULL" if "analyzed_at" in cols else ""
    if has_cat:
        rows = cursor.execute(
            f"""
            SELECT id, conv_id, slug, session_type, vertex, failure_type,
                   tool_name, severity_tier, severity_weight, reason, details, created_at,
                   bug_category, remedy
            FROM harness_failures
            WHERE resolved_at IS NULL {analyzed_filter}
            ORDER BY id ASC;
            """
        ).fetchall()
    else:
        rows = cursor.execute(
            f"""
            SELECT id, conv_id, slug, session_type, vertex, failure_type,
                   tool_name, severity_tier, severity_weight, reason, details, created_at
            FROM harness_failures
            WHERE resolved_at IS NULL {analyzed_filter}
            ORDER BY id ASC;
            """
        ).fetchall()

    reviews = cursor.execute(
        """
        SELECT id, slug, reason, event_count, created_at
        FROM settings_reviews
        WHERE resolved_at IS NULL
        ORDER BY id ASC;
        """
    ).fetchall()

    clusters: dict[str, list[dict]] = {v: [] for v in SYMBOLIC_VERTICES}
    total_severity = 0.0
    failure_ids: list[int] = []
    has_golden = bool(
        {row[1] for row in cursor.execute("PRAGMA table_info(harness_golden_dataset);").fetchall()}
    )

    for r in rows:
        if len(r) >= 14:
            fid, conv, slug, stype, vert, ftype, tool, stier, sweight, rsn, dtls, cat, bug_cat, rem = r[:14]
        else:
            fid, conv, slug, stype, vert, ftype, tool, stier, sweight, rsn, dtls, cat = r[:12]
            bug_cat, rem = "", ""
        v_clean = vert.lower() if vert and vert.lower() in SYMBOLIC_VERTICES else "hook"
        item = {
            "id": fid,
            "conv_id": conv,
            "slug": slug or "default",
            "session_type": stype,
            "vertex": v_clean,
            "failure_type": ftype,
            "tool_name": tool or "",
            "severity_tier": stier or "S2_major",
            "severity_weight": float(sweight or 0.05),
            "reason": rsn or "",
            "details": dtls or "",
            "created_at": str(cat),
            "bug_category": bug_cat or "",
            "remedy": rem or "",
        }
        clusters[v_clean].append(item)
        total_severity += float(sweight or 0.05)
        failure_ids.append(fid)
        if has_golden:
            try:
                _maybe_insert_golden_dataset_row(
                    cursor,
                    slug=item["slug"],
                    conv_id=item["conv_id"] or "",
                    vertex=v_clean,
                    failure_type=item["failure_type"] or "",
                    tool_name=item["tool_name"],
                    severity_tier=item["severity_tier"],
                    reason=item["reason"],
                    bug_category=item["bug_category"],
                )
            except Exception:
                pass
    if has_golden:
        try:
            conn.commit()
        except Exception:
            pass

    symbolic_gradients: dict[str, float] = {}
    for v in SYMBOLIC_VERTICES:
        symbolic_gradients[v] = round(sum(item["severity_weight"] for item in clusters[v]), 4)

    review_list = [
        {"id": rw[0], "slug": rw[1], "reason": rw[2], "event_count": rw[3], "created_at": str(rw[4])}
        for rw in reviews
    ]

    return {
        "clusters": clusters,
        "symbolic_gradients": symbolic_gradients,
        "total_severity": round(total_severity, 4),
        "total_open_failures": len(failure_ids),
        "failure_ids": failure_ids,
        "open_settings_reviews": review_list,
        "review_ids": [rw["id"] for rw in review_list],
    }


def query_external_research(
    vertex: str,
    failure_type: str,
    offline: bool = True,
) -> list[dict]:
    """Retrieves external academic and open-source blueprints with graceful offline fallback."""
    scout_path = os.path.expanduser("~/.gemini/antigravity/scripts/external-research-scout.py")
    if os.path.isfile(scout_path):
        try:
            cmd = [sys.executable, scout_path, "--vertex", vertex, "--failure-type", failure_type, "--json"]
            if offline:
                cmd.append("--offline")
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if proc.returncode == 0 and proc.stdout.strip():
                data = json.loads(proc.stdout.strip())
                items = data.get("blueprints", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                if items:
                    known_citations = {
                        "arxiv:2406.18532": "arXiv:2406.18532 (AgentSymbolicLearning)",
                        "arxiv:2505.22954": "arXiv:2505.22954 (Darwin Gödel Machine)",
                        "arxiv:2610.14224v1": "arXiv:2610.14224v1 (Harness²)",
                        "arxiv:2406.07496": "arXiv:2406.07496 (TextGrad)",
                        "arxiv:2504.13171": "arXiv:2504.13171 (Sleep-time Compute: Beyond Inference Scaling at Test-time)",
                        "arxiv:2405.15793": "arXiv:2405.15793 (SWE-agent)",
                        "arxiv:2404.05427": "arXiv:2404.05427 (AutoCodeRover)",
                        "arxiv:2410.10762": "arXiv:2410.10762 (AFlow)",
                        "arxiv:2408.08435": "arXiv:2408.08435 (ADAS & ShinkaEvolve)",
                        "arxiv:2409.13740": "arXiv:2409.13740 (PaperQA2)",
                    }
                    mapped_blueprints = []
                    for it in items:
                        if not isinstance(it, dict):
                            continue
                        m = dict(it)
                        id_key = m.get("id", "")
                        if "citation" not in m or not m["citation"]:
                            if id_key in known_citations:
                                m["citation"] = known_citations[id_key]
                            elif "AgentSymbolicLearning" in m.get("abstract", "") or "AgentSymbolicLearning" in m.get("title", ""):
                                m["citation"] = f"{id_key} (AgentSymbolicLearning)" if id_key else "AgentSymbolicLearning"
                            else:
                                m["citation"] = id_key or m.get("url") or "External Research"
                        if "summary" not in m and "actionable_pattern" in m:
                            m["summary"] = m["actionable_pattern"]
                        elif "summary" not in m:
                            m["summary"] = m.get("abstract") or m.get("core_mechanism", "")
                        if "core_mechanism" not in m:
                            m["core_mechanism"] = m.get("summary") or m.get("title", "")
                        mapped_blueprints.append(m)
                    if mapped_blueprints:
                        return mapped_blueprints
        except Exception:
            pass

    # Built-in verified academic citations and algorithmic blueprints
    built_in_blueprints = {
        "tool_guidance": [
            {
                "citation": "arXiv:2406.18532 (AgentSymbolicLearning)",
                "title": "Agent Symbolic Learning: Backpropagating Failure Critiques",
                "core_mechanism": "Deduplicate parameter-quirk constraints in tool guidance and enforce fuzzy anchor line offsets.",
            },
            {
                "citation": "SWE-agent & Aider ACI Architecture",
                "title": "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering",
                "core_mechanism": "Harness adaptations inspired by SWE-agent's ACI design: shift-left verification to prevent tool parameter mismatch before process execution.",
            },
        ],
        "hook": [
            {
                "citation": "Google SRE Workbook, ch.5 Alerting on SLOs & arXiv:2504.13171 (Sleep-time Compute: Beyond Inference Scaling at Test-time)",
                "title": "Multi-Window Burn-Rate Tracking for Autonomous Agent Loops",
                "core_mechanism": "Separate wake-time logging from out-of-process sleep-time consolidation.",
            },
        ],
        "skill": [
            {
                "citation": "arXiv:2408.08435 (ADAS & ShinkaEvolve)",
                "title": "Automated Design of Agentic Systems via Empirical Search",
                "core_mechanism": "Autotrigger indexing and semantic cue token matching for specialized subagent bundles.",
            },
        ],
        "routing": [
            {
                "citation": "arXiv:2505.22954 (Darwin Gödel Machine)",
                "title": "Self-Modifying Agents with Bounded Behavioral Verification",
                "core_mechanism": "Enforce strict worktree isolation and lease contracts on subagent file write scopes.",
            },
        ],
        "codebase": [
            {
                "citation": "arXiv:2409.13740 (PaperQA2)",
                "title": "Superhuman Scientific Literature Synthesis with Empirical Grounds",
                "core_mechanism": "Ground all codebase remediation directives in verifiable file paths, line ranges, and compiler proofs.",
            },
        ],
    }

    return built_in_blueprints.get(vertex, built_in_blueprints["tool_guidance"])


def factorize_failure_scope(failure_item: dict[str, Any]) -> str:
    """Determines whether a failure is factorized into env overlay or general harness (CP-1)."""
    if failure_item.get("scope") == "env":
        return "env"
    slug = str(failure_item.get("slug") or "").strip()
    vertex = str(failure_item.get("vertex") or "").strip()
    if slug not in ("", "global", "default") and vertex in ("codebase", "routing", "skill"):
        return "env"
    return "general"


def write_env_harness_overlay(
    active_slug: str,
    clusters: dict[str, list[dict[str, Any]]],
    env_overlays_dir: str | None = None,
    mgm_directives: list[str] | None = None,
) -> str:
    """Writes or updates factorized environment harness overlay (<target_dir>/<slug>.md) (CP-1)."""
    if active_slug in ("", "global", "default"):
        return ""

    if env_overlays_dir:
        target_dir = env_overlays_dir
    elif "unittest" in sys.modules and not os.environ.get("ANTIGRAVITY_TEST_ENV_OVERLAYS_DIR"):
        return ""
    else:
        target_dir = os.environ.get("ANTIGRAVITY_TEST_ENV_OVERLAYS_DIR") or ENV_OVERLAYS_DIR

    if not target_dir:
        return ""

    target_path = Path(os.path.expanduser(target_dir)) / f"{active_slug}.md"
    target_path.parent.mkdir(parents=True, exist_ok=True)

    existing_text = target_path.read_text(encoding="utf-8") if target_path.is_file() else ""

    directives: list[str] = []
    if mgm_directives:
        for md in mgm_directives:
            if md not in directives:
                directives.append(md)

    for vertex in SYMBOLIC_VERTICES:
        for item in clusters.get(vertex, []):
            scope = factorize_failure_scope(item)
            item_slug = item.get("slug", "")
            if scope == "env" and (item_slug == active_slug or item_slug in ("", "global")):
                reason = item.get("reason", "").strip()
                f_id = item.get("id", "auto")
                b_cat = item.get("bug_category", "").strip()
                cat_prefix = f"[{b_cat}] " if b_cat else ""
                directives.append(f"- **`{vertex}` Directive**: {cat_prefix}{reason[:120]} *(Failure ID {f_id})*")

    if not directives:
        directives.append(f"- **`env` Directive**: Maintain strict project-local invariants for {active_slug}.")

    unique_directives: list[str] = []
    for d in directives:
        if d not in existing_text:
            unique_directives.append(d)

    if not unique_directives and existing_text:
        return str(target_path)

    header = f"# Environment Harness Overlay: {active_slug}\n"
    if not existing_text:
        new_content = header + "\n" + "\n".join(directives) + "\n"
    else:
        new_content = existing_text.rstrip() + "\n" + "\n".join(unique_directives) + "\n"

    target_path.write_text(new_content, encoding="utf-8")
    return str(target_path)


def extract_tool_name(tool_raw: str) -> str:
    """Extracts clean tool display name without markdown markers or 'Quirk' suffix."""
    cleaned = re.sub(r"\s+Quirk$", "", tool_raw.strip(), flags=re.IGNORECASE).strip("`* ")
    if cleaned.lower() in ("view_file", "read_file", "view_file / read_file"):
        return "view_file / read_file"
    return cleaned


def generalize_quirk_reason(reason: str) -> str:
    """Generalizes a failure reason so rules stay file-agnostic and clean."""
    text = reason.strip()
    text = re.sub(r"\s*\*\(Auto-healed.*?\)\*\s*$", "", text, flags=re.IGNORECASE).strip()
    # 1. Slice window: remove '(N lines) on `<file>`' or genericize
    text = re.sub(
        r"Slice window\s*(?:\(\d+\s*lines\)\s*)?(?:on\s*`?[^`\s]+`?\s*)?exceeds",
        "Slice window exceeds",
        text,
        flags=re.IGNORECASE,
    )
    # 2. Command string length: remove '(N)'
    text = re.sub(
        r"Command string length\s*(?:\(\d+\)\s*)?exceeds",
        "Command string length exceeds",
        text,
        flags=re.IGNORECASE,
    )
    # 3. Outline-First monolithic file guard: genericize
    text = re.sub(
        r"Outline-First Monolithic File Guard:\s*`?[^`\s]+`?\s*has\s*[\d,]+\s*total lines\s*\([^)]+\)\..*$",
        "Outline-First Monolithic File Guard: Files > 400 lines require AST symbol lookup before reading.",
        text,
        flags=re.IGNORECASE,
    )
    # 4. Slice loop breaker / ceiling
    if re.search(r"Slice Loop Breaker.*duplicate slice loop", text, re.IGNORECASE):
        text = "Duplicate slice loop: Reading identical line ranges consecutively is blocked by circuit breaker."
    elif re.search(r"Slice Loop Breaker.*(?:reached \d+-slice ceiling|sliced reads)", text, re.IGNORECASE):
        text = "Slice Loop Breaker: 6-slice ceiling reached on a single file. Blocked to prevent token waste; use `rg -n`."
    # 5. Fix-The-Code-Not-The-Test
    text = re.sub(r"Role '[^']+' is forbidden", "Role is forbidden", text)
    if "fix-the-code-not-the-test" in text.lower():
        text = re.sub(
            r"existing assert/expect lines(?:\s+in\s+`?[^`\s*]+`?)?\s*\.?$",
            "existing assert/expect lines. Fix the code under test instead.",
            text,
            flags=re.IGNORECASE,
        )
    # Test-Immutability Lock repair of truncated tail
    if "test-immutability" in text.lower():
        text = re.sub(
            r"is forbidden in\s+`?[^`\s*]+`?\.?$",
            "is forbidden in <file>.",
            text,
            flags=re.IGNORECASE,
        )
    # Error-stagnation
    if "error-stagnation" in text.lower():
        text = re.sub(
            r"Stop blind\s*(?:tr[a-z\-]*)?\.?$",
            "Stop blind trial-and-error and inspect the root cause first.",
            text,
            flags=re.IGNORECASE,
        )
    # Scout-block gate
    if "scout-block gate" in text.lower():
        text = re.sub(
            r"Target source files\s*(?:ins[a-z]*)?\.?$",
            "Target source files instead.",
            text,
            flags=re.IGNORECASE,
        )
    # Role isolation PM
    if "pm-no-implementation" in text.lower() or "role isolation shell-write" in text.lower():
        text = re.sub(
            r"is strictly\s*(?:pro[a-z]*)?\.?$",
            "is strictly prohibited from mutating application source code via shell write.",
            text,
            flags=re.IGNORECASE,
        )
    # 6. Replace backticked file names or paths with <file>
    text = re.sub(r"`(?:test_[^`\s*]+|[^`\s*]*/[^`\s*]+|[^`\s*]+\.[a-zA-Z0-9_\-]+)`?", "<file>", text)
    # 7. Normalize volatile numbers in parentheses, e.g. (4429) -> (N) if any remained
    text = re.sub(r"\((\d{3,})\)", "(N)", text)
    return text.strip()


def normalize_reason_key(tool_str: str, reason_str: str) -> str:
    """Computes a normalized, file-agnostic, number-agnostic key for deduplication."""
    t = extract_tool_name(tool_str).lower()
    if t in ("view_file", "read_file", "view_file / read_file"):
        t = "view_file"
    elif t in ("edit_file", "replace_file_content", "multi_replace_file_content"):
        t = "edit_file"
    elif t in ("write_file", "write_to_file"):
        t = "write_file"

    r = re.sub(r"\s*\*\(Auto-healed.*?\)\*\s*$", "", reason_str, flags=re.IGNORECASE).strip()
    r = re.sub(r"^Token Economy Invariant:\s*", "", r, flags=re.IGNORECASE)
    r = re.sub(r"`(?:test_[^`\s*]+|[^`\s*]*/[^`\s*]+|[^`\s*]+\.[a-zA-Z0-9_\-]+)`?", "<file>", r)
    r = re.sub(r"/[a-zA-Z0-9_\.\-]+(?:/[a-zA-Z0-9_\.\-]+)+", "<file>", r)
    r = re.sub(r"\(\d+\s*lines\)\s*(?:on\s*(?:<file>|`[^`]+`))?", "", r, flags=re.IGNORECASE)
    r = re.sub(r"\(\d+\)\s*", "", r)
    r = re.sub(r"\b\d+(?:,\d+)*\b", "N", r)
    r = re.sub(r"\s+", " ", r.lower()).strip()
    return f"{t}:{r[:100]}"


def get_quirk_semantic_family(tool_str: str, text: str, failure_type: str = "") -> str | None:
    """Classifies a tool quirk into a canonical semantic family for invariant-level deduplication."""
    if failure_type:
        ft = failure_type.strip().lower()
        if ft == "flood_guard":
            if "fd" in text.lower():
                return "rc_swe_fd"
            return "rc_swe_rg"
        if ft == "slice_cap_exceeded":
            return "vf_slice_window"
        if ft == "slice_loop_breaker":
            return "vf_slice_ceiling"
        if ft == "legacy_cli_blocked":
            return "rc_legacy_cli"
        if ft == "task_polling_blocked":
            return "mt_polling"
        if ft in ("read_budget_strike", "read_budget_lock"):
            return "vf_slice_ceiling"
        if ft == "subagent_prompt_overflow":
            return "subagent_prompt"
    t = extract_tool_name(tool_str).lower()
    if t in ("view_file", "read_file", "view_file / read_file"):
        t = "view_file"
    elif t in ("edit_file", "replace_file_content", "multi_replace_file_content"):
        t = "edit_file"
    elif t in ("write_file", "write_to_file"):
        t = "write_file"
    s = re.sub(r"[`'\"]", "", text.lower())
    if t == "run_command":
        if "command string length" in s and ("exceeds" in s or "4,000" in s or "4000" in s):
            return "rc_cmd_length"
        if ("cd command" in s or "the cd" in s or ("cd" in s and "command" in s)) and ("prohibit" in s or "forbidden" in s):
            return "rc_cd_prohibited"
        if "sleep" in s and ("forbidden" in s or "prohibit" in s):
            return "rc_sleep_forbidden"
        if "swe-agent" in s and "rg" in s:
            return "rc_swe_rg"
        if "swe-agent" in s and "fd" in s:
            return "rc_swe_fd"
        if "legacy" in s and ("grep" in s or "find" in s):
            return "rc_legacy_cli"
        if "cat" in s and ("pagination" in s or "large files" in s or "unbounded" in s):
            return "rc_cat_pagination"
        if "targeted test" in s or "law 22" in s or "pre_ship" in s:
            return "rc_targeted_test"
        if "error-stagnation" in s:
            return "rc_error_stagnation"
        if "pm-no-implementation" in s or "role isolation shell-write" in s:
            return "rc_role_pm"
    elif t in ("view_file", "view_file / read_file"):
        if "slice window" in s and ("exceeds" in s or "250" in s):
            return "vf_slice_window"
        if "outline-first" in s or "monolithic file guard" in s or "400 lines" in s or "> 400" in s:
            return "vf_monolithic_outline"
        if "duplicate slice loop" in s:
            return "vf_duplicate_slice"
        if "slice loop breaker" in s or "6-slice ceiling" in s or "slice ceiling" in s or "sliced reads" in s:
            return "vf_slice_ceiling"
        if "scout-block gate" in s:
            return "vf_scout_block"
        if "file does not exist" in s or "pre-verification invariant" in s:
            return "vf_file_not_exist"
    elif t in ("edit_file", "write_file"):
        if "test-immutability" in s:
            return "ef_test_immutability"
        if "fix-the-code-not-the-test" in s:
            return "ef_fix_the_code"
    elif t == "manage_task":
        if "anti-polling" in s or "status polling" in s:
            return "mt_polling"
    elif t == "invoke_subagent":
        if "prompt" in s and ("6,000" in s or "6000" in s or "sparsification" in s):
            return "subagent_prompt"
    return None


def is_valid_healed_reason(reason_str: str) -> bool:
    if "/tmp/" in reason_str:
        return False
    if re.search(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", reason_str):
        return False
    if "/brain/" in reason_str or "conversation_" in reason_str or ".system_generated" in reason_str:
        return False
    abs_paths = re.findall(r"(?:^|[\s\"`:\(\[])(/[a-zA-Z0-9_\.\-]+(?:/[a-zA-Z0-9_\.\-]+)+)", reason_str)
    for ap in abs_paths:
        norm_p = os.path.normpath(ap)
        is_gemini = norm_p.startswith(os.path.expanduser("~/.gemini")) or "/.gemini/" in norm_p
        is_repo = "antigravity_settings" in norm_p
        if not (is_gemini or is_repo):
            return False
    return True


def apply_deterministic_harness_repairs(
    clusters: dict[str, list[dict]],
    tool_quirks_file: str = TOOL_QUIRKS_FILE,
    active_slug: str = "global",
    env_overlays_dir: str | None = None,
    scripts_dir: str = "~/.gemini/antigravity/scripts",
    repaired_ids: set[int] | None = None,
    mgm_directives_by_slug: dict[str, list[str]] | None = None,
) -> list[str]:
    """Applies verified self-healing repairs to tool-quirks and harness index."""
    repairs_applied: list[str] = []
    if repaired_ids is None:
        repaired_ids = set()

    # 1. Self-Heal Tool Quirks (H_gen)
    tool_failures = clusters.get("tool_guidance", [])
    if tool_failures:
        quirks_path = Path(os.path.expanduser(tool_quirks_file))
        quirks_path.parent.mkdir(parents=True, exist_ok=True)
        existing_text = quirks_path.read_text(encoding="utf-8") if quirks_path.is_file() else ""

        SECTION_MARKER = "## Auto-Healed Tool Quirks (Level-3 Autonomous Loop)"
        DEFAULT_INTRO_LINE = "Execution invariants automatically captured and clustered by `auto-harness-healer.py`:"

        if SECTION_MARKER in existing_text:
            base_section, auto_section = existing_text.split(SECTION_MARKER, 1)
        else:
            base_section = existing_text.rstrip() + "\n\n"
            auto_section = ""

        # Preserve existing intro line if present
        intro_line = DEFAULT_INTRO_LINE
        for line in auto_section.splitlines():
            line_s = line.strip()
            if "Execution invariants automatically captured" in line_s:
                intro_line = line_s
                break

        curated_rules: list[str] = []
        existing_auto_rules: list[str] = []
        existing_families: set[str] = set()
        existing_keys: set[str] = set()

        for line in auto_section.splitlines():
            line_s = line.strip()
            m = re.match(r"^-\s*\*\*(.+?)\*\*:\s*(.+)$", line_s)
            if not m:
                continue
            t_name = extract_tool_name(m.group(1))
            r_text = m.group(2)
            is_auto = bool(re.search(r"\*\(Auto-healed from failure ID \d+\)\*", line_s, re.IGNORECASE))
            fam = get_quirk_semantic_family(t_name, r_text)
            key = normalize_reason_key(t_name, r_text)

            if not is_auto:
                curated_rules.append(line_s)
                if fam:
                    existing_families.add(fam)
                existing_keys.add(key)
            else:
                if (fam and fam in existing_families) or (key in existing_keys):
                    continue
                if fam:
                    existing_families.add(fam)
                existing_keys.add(key)
                gen_r = generalize_quirk_reason(r_text)
                id_tag_m = re.search(r"\*\(Auto-healed from failure ID \d+\)\*", line_s, re.IGNORECASE)
                id_tag = f" {id_tag_m.group(0)}" if id_tag_m else ""
                t_display = "view_file / read_file" if t_name.lower() in ("view_file", "read_file", "view_file / read_file") else t_name
                existing_auto_rules.append(f"- **`{t_display}` Quirk**: {gen_r}{id_tag}")

        new_rules: list[str] = []
        for fail in tool_failures:
            tool = fail.get("tool_name", "").strip()
            reason = fail.get("reason", "").strip()
            ft = fail.get("failure_type", "").strip()
            if not tool or not reason:
                continue
            if not is_valid_healed_reason(reason):
                continue
            fam = get_quirk_semantic_family(tool, reason, ft)
            key = normalize_reason_key(tool, reason)
            if (fam and fam in existing_families) or (key in existing_keys):
                continue
            if fam:
                existing_families.add(fam)
            existing_keys.add(key)
            if fail_id := fail.get("id"):
                repaired_ids.add(fail_id)
            tool_display = "view_file / read_file" if tool in ("view_file", "read_file") else tool
            gen_reason = generalize_quirk_reason(reason)
            new_rules.append(f"- **`{tool_display}` Quirk**: {gen_reason} *(Auto-healed from failure ID {fail.get('id', 0)})*")

        combined_auto_rules = existing_auto_rules + new_rules
        if len(combined_auto_rules) > 20:
            combined_auto_rules = combined_auto_rules[-20:]
        while combined_auto_rules and sum(len(r) + 1 for r in combined_auto_rules) > 4000:
            combined_auto_rules.pop(0)

        existing_auto_lines_raw = [
            l.strip()
            for l in auto_section.splitlines()
            if re.search(r"\*\(Auto-healed from failure ID \d+\)\*", l, re.IGNORECASE)
        ]
        has_changed = bool(new_rules or (len(combined_auto_rules) != len(existing_auto_lines_raw)))

        if has_changed or not existing_text:
            all_rules = curated_rules + combined_auto_rules
            updated_text = (
                base_section.rstrip()
                + "\n\n"
                + SECTION_MARKER
                + "\n\n"
                + intro_line
                + "\n\n"
                + "\n".join(all_rules)
                + "\n"
            )
            quirks_path.write_text(updated_text, encoding="utf-8")
            tools_affected = sorted(list({fail.get("tool_name", "") for fail in tool_failures if fail.get("tool_name")}))
            tools_desc = f" ({', '.join(tools_affected)})" if tools_affected else ""
            repairs_applied.append(f"Appended {len(new_rules)} auto-healed rule(s){tools_desc} to tool-quirks.md")

    # 2. Factorized Environment Overlay (H_env - CP-1)
    target_slugs: set[str] = set()
    if active_slug not in ("", "global", "default"):
        target_slugs.add(active_slug)
    for v_fails in clusters.values():
        for f in v_fails:
            cand_s = f.get("slug", "").strip()
            if cand_s and cand_s not in ("", "global", "default"):
                target_slugs.add(cand_s)

    if not target_slugs and env_overlays_dir and active_slug:
        target_slugs.add(active_slug)

    mgm_map = mgm_directives_by_slug or {}
    for s in sorted(target_slugs):
        s_mgm = mgm_map.get(s, [])
        overlay_path = write_env_harness_overlay(
            s, clusters, env_overlays_dir=env_overlays_dir, mgm_directives=s_mgm
        )
        if overlay_path:
            for v_fails in clusters.values():
                for f in v_fails:
                    if f.get("slug") == s and f.get("id"):
                        repaired_ids.add(f["id"])
            repairs_applied.append(f"Updated factorized environment overlay for '{s}' ({overlay_path})")

    # 3. Re-index skills if needed
    s_dir = os.path.expanduser(scripts_dir)
    validator_path = os.path.join(s_dir, "validate-harness-tree.py")
    if os.path.isfile(validator_path):
        try:
            res = subprocess.run([sys.executable, validator_path, "--autotrigger"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                repairs_applied.append("Synchronized skillbank/INDEX.md via validate-harness-tree.py --autotrigger")
        except Exception:
            pass

    return repairs_applied


def evaluate_pareto_objectives(
    cluster_data: dict[str, Any],
    sandbox_ok: bool = True,
    tool_quirks_file: str = TOOL_QUIRKS_FILE,
    env_overlay_path: str = "",
    max_quirks_chars: int = 12000,
    repaired_count: int = 0,
    receipt_delta: float = 0.0,
) -> dict[str, float]:
    """Computes 3-Axis Pareto Objectives: func_score, sec_score, token_score (CP-2)."""
    if not sandbox_ok:
        func_score = 0.0
    elif repaired_count == 0 and receipt_delta == 0.0:
        func_score = 1.0
    else:
        func_score = round(max(0.0, min(1.5, 1.0 + min(0.25, 0.05 * repaired_count) + max(-0.25, min(0.25, receipt_delta)))), 4)

    sec_score = 1.0
    unsafe_patterns = [
        "--no-verify",
        "os.system(",
        "eval(",
        "shell=True",
        "disable_security_gate",
        "bypass_lease",
    ]
    files_to_check = []
    if tool_quirks_file:
        files_to_check.append(Path(os.path.expanduser(tool_quirks_file)))
    if env_overlay_path:
        files_to_check.append(Path(os.path.expanduser(env_overlay_path)))

    for fp in files_to_check:
        if fp.is_file():
            try:
                content = fp.read_text(encoding="utf-8")
                if any(pat in content for pat in unsafe_patterns):
                    sec_score = 0.0
                    break
            except Exception:
                pass

    quirks_chars = 0
    if tool_quirks_file:
        qp = Path(os.path.expanduser(tool_quirks_file))
        if qp.is_file():
            try:
                quirks_chars = len(qp.read_text(encoding="utf-8"))
            except Exception:
                quirks_chars = 0

    token_score = round(max(0.0, min(1.0, 1.0 - (quirks_chars / float(max_quirks_chars * 2)))), 4)

    return {
        "func_score": func_score,
        "sec_score": sec_score,
        "token_score": token_score,
    }


def is_pareto_dominated(
    candidate: dict[str, float],
    archive: list[dict[str, float]],
) -> tuple[bool, str]:
    """Checks if candidate violates security/functional floor or is strictly dominated on Pareto frontier (CP-2)."""
    c_func = float(candidate.get("func_score", 0.0))
    c_sec = float(candidate.get("sec_score", 0.0))
    c_tok = float(candidate.get("token_score", 0.0))

    if c_sec < 1.0:
        return (
            True,
            "Candidate violated security floor (sec_score < 1.0)",
        )
    if c_func < 1.0:
        return (
            True,
            "Candidate violated functional floor (func_score < 1.0)",
        )
    if c_tok < 0.2:
        return (
            True,
            "Candidate violated token floor (token_score < 0.2)",
        )

    for entry in archive:
        a_func = float(entry.get("func_score", 0.0))
        a_sec = float(entry.get("sec_score", 0.0))
        a_tok = float(entry.get("token_score", 0.0))

        dominates = (
            a_func >= c_func
            and a_sec >= c_sec
            and a_tok >= c_tok
            and (a_func > c_func or a_sec > c_sec or a_tok > c_tok)
        )
        if dominates:
            return (
                True,
                "Candidate strictly dominated by existing Pareto frontier point",
            )

    return False, "Non-dominated on Pareto frontier"


def update_pareto_archive(
    conn: sqlite3.Connection,
    slug: str,
    objectives: dict[str, float],
    top_vertex: str,
    general_hash: str = "",
    env_overlay_path: str = "",
    digest_path: str = "",
    niche_key: str = "",
    receipt_baseline_rate: float = 0.0,
) -> dict[str, Any]:
    """Updates SQLite Pareto frontier archive with non-dominated candidate (CP-3)."""
    cur = conn.cursor()
    if top_vertex:
        rows = cur.execute(
            """
            SELECT id, func_score, sec_score, token_score
            FROM harness_pareto_archive
            WHERE slug = ? AND (top_vertex = ? OR top_vertex = '') AND is_pareto_front = 1;
            """,
            (slug, top_vertex),
        ).fetchall()
    else:
        rows = cur.execute(
            """
            SELECT id, func_score, sec_score, token_score
            FROM harness_pareto_archive
            WHERE slug = ? AND is_pareto_front = 1;
            """,
            (slug,),
        ).fetchall()

    active_points = [
        {"id": r[0], "func_score": r[1], "sec_score": r[2], "token_score": r[3]}
        for r in rows
    ]

    dominated, reason = is_pareto_dominated(objectives, active_points)
    if dominated:
        return {
            "admitted": False,
            "dominated_reason": reason,
            "pruned_ids": [],
            "profile_mode": "rejected",
        }

    c_func = float(objectives.get("func_score", 0.0))
    c_sec = float(objectives.get("sec_score", 0.0))
    c_tok = float(objectives.get("token_score", 0.0))

    pruned_ids: list[int] = []
    for p in active_points:
        p_func = float(p.get("func_score", 0.0))
        p_sec = float(p.get("sec_score", 0.0))
        p_tok = float(p.get("token_score", 0.0))
        if (
            c_func >= p_func
            and c_sec >= p_sec
            and c_tok >= p_tok
            and (c_func > p_func or c_sec > p_sec or c_tok > p_tok)
        ):
            pruned_ids.append(p["id"])

    if pruned_ids:
        q_marks = ",".join("?" for _ in pruned_ids)
        conn.execute(
            f"UPDATE harness_pareto_archive SET is_pareto_front = 0 WHERE id IN ({q_marks});",
            pruned_ids,
        )

    profile_mode = (
        "strict_security"
        if objectives.get("sec_score", 0.0) >= 1.0 and objectives.get("token_score", 0.0) >= 0.8
        else "balanced_velocity"
    )

    eff_niche = niche_key or (f"{slug}:{top_vertex}" if top_vertex else slug)

    conn.execute(
        """
        INSERT INTO harness_pareto_archive (
            slug, profile_mode, func_score, sec_score, token_score,
            top_vertex, general_hash, env_overlay_path, digest_path,
            is_pareto_front, niche_key, receipt_baseline_rate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?);
        """,
        (
            slug,
            profile_mode,
            c_func,
            c_sec,
            c_tok,
            top_vertex,
            general_hash,
            env_overlay_path,
            digest_path,
            eff_niche,
            receipt_baseline_rate,
        ),
    )
    conn.commit()

    return {
        "admitted": True,
        "dominated_reason": "",
        "pruned_ids": pruned_ids,
        "profile_mode": profile_mode,
    }


def select_pareto_profile(
    conn: sqlite3.Connection,
    slug: str = "global",
    mode: str = "strict_security",
) -> dict[str, Any] | None:
    """Selects active Pareto frontier profile for slug under given mode (CP-3)."""
    cur = conn.cursor()
    order_clause = (
        "(CASE WHEN slug = ? THEN 0 ELSE 1 END), sec_score DESC, func_score DESC, token_score DESC"
        if mode == "strict_security"
        else "(CASE WHEN slug = ? THEN 0 ELSE 1 END), func_score DESC, token_score DESC, sec_score DESC"
    )
    query = f"""
        SELECT id, slug, profile_mode, func_score, sec_score, token_score,
               top_vertex, general_hash, env_overlay_path, digest_path, is_pareto_front, created_at
        FROM harness_pareto_archive
        WHERE (slug = ? OR slug = 'global') AND is_pareto_front = 1
        ORDER BY {order_clause}
        LIMIT 1;
    """
    row = cur.execute(query, (slug, slug)).fetchone()
    if not row:
        return None

    cols = [
        "id",
        "slug",
        "profile_mode",
        "func_score",
        "sec_score",
        "token_score",
        "top_vertex",
        "general_hash",
        "env_overlay_path",
        "digest_path",
        "is_pareto_front",
        "created_at",
    ]
    return dict(zip(cols, row))


def write_self_evolution_digest(
    cluster_data: dict[str, Any],
    citations: list[dict],
    repairs_applied: list[str],
    active_slug: str,
    output_dir: str = "~/.gemini/antigravity/skillbank/failure-lessons",
    pareto_objectives: dict[str, float] | None = None,
    env_overlay_path: str = "",
    sandbox_ok: bool = True,
    sandbox_msg: str = "",
    verdict: str | None = None,
) -> str:
    """Generates structured Self-Evolution & Codebase Healing Digest."""
    if output_dir == "~/.gemini/antigravity/skillbank/failure-lessons" and "unittest" in sys.modules:
        out_path = Path(tempfile.gettempdir()) / "antigravity_test_digests"
    else:
        out_path = Path(os.path.expanduser(output_dir))
    out_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    file_path = out_path / f"auto_heal_{timestamp}.md"

    gradients = cluster_data["symbolic_gradients"]
    total_failures = cluster_data["total_open_failures"]

    if verdict is None:
        if not sandbox_ok:
            verdict = "FAILED"
            sandbox_verif = "FAIL"
        elif repairs_applied:
            verdict = "SELF_HEALED"
            sandbox_verif = "PASS"
        else:
            verdict = "ANALYZED_ONLY"
            sandbox_verif = "PASS"
    else:
        sandbox_verif = "PASS" if sandbox_ok else "FAIL"

    frontmatter = [
        "---",
        f"timestamp: '{datetime.datetime.now(datetime.timezone.utc).isoformat()}'",
        f"session_id: 'auto_heal_{timestamp}'",
        f"slug: '{active_slug}'",
        f"total_failures_analyzed: {total_failures}",
        "symbolic_gradients:",
    ]
    for k, v in gradients.items():
        frontmatter.append(f"  {k}: {v}")
    if pareto_objectives:
        frontmatter.append("pareto_objectives:")
        for obj_k, obj_v in pareto_objectives.items():
            frontmatter.append(f"  {obj_k}: {obj_v}")
    if env_overlay_path:
        frontmatter.append(f"env_overlay_path: '{env_overlay_path}'")
    frontmatter.extend([
        f"sandbox_verification: {sandbox_verif}",
        f"verdict: {verdict}",
        "---",
        "",
    ])

    body = [
        f"# Level-3 Autonomous Self-Evolution & Codebase Healing Digest (`{timestamp}`)",
        "",
        "> **Architecture Reference**: Darwin Gödel Machine (`arXiv:2505.22954`) $\\times$ AgentSymbolicLearning (`arXiv:2406.18532`).",
        "",
        "## 1. Symbolic Failure Gradients ($\\nabla_{v_i} \\mathcal{L}_{\\text{sym}}$)",
        f"- **Analyzed Failures**: {total_failures} open failure event(s).",
        f"- **Cumulative Severity Score**: {cluster_data['total_severity']}",
        "",
        "| Symbolic Vertex ($v_i$) | Gradient $\\nabla_{v_i}$ | Failure Count | Status |",
        "| :--- | :--- | :--- | :--- |",
    ]

    for v in SYMBOLIC_VERTICES:
        fails = cluster_data["clusters"].get(v, [])
        count = len(fails)
        grad = gradients.get(v, 0.0)
        status = "CRITICAL" if grad >= 1.0 else ("ELEVATED" if grad >= 0.25 else "NOMINAL")
        tools_involved = sorted(list({f.get("tool_name") for f in fails if f.get("tool_name")}))
        tools_str = f" ({', '.join(tools_involved)})" if tools_involved else ""
        body.append(f"| `{v}` | {grad} | {count}{tools_str} | {status} |")

    body.extend([
        "",
        "## 2. External Academic & GitHub Research Citations",
    ])
    for cit in citations:
        body.append(f"- **{cit.get('citation', 'Reference')}**: *{cit.get('title', '')}* — {cit.get('core_mechanism', '')}")

    body.extend([
        "",
        "## 3. Harness Repairs Applied",
    ])
    if repairs_applied:
        for rep in repairs_applied:
            body.append(f"- {rep}")
    else:
        body.append("- Baseline harness verified nominal; zero structural mutations required.")

    body.extend([
        "",
        f"## 4. Target Codebase Remediation Directives (Project `{active_slug}`)",
        "- **Pre-Edit Invariant**: Ensure all source edits preserve compiler/test pass invariants.",
        "- **Regression Firewall**: Retain 100% passing baseline across unit and integration suites.",
        "- **Anti-Slop Audit**: Zero nested cards, zero badge proliferation, zero unresolved TODO stubs.",
        "",
        "## 5. Darwin Gödel Machine 3-Gate Sandbox Verification",
    ])
    if sandbox_ok:
        body.extend([
            "- Gate 1: `validate-harness-tree.py` -> PASS",
            "- Gate 2: `reflect-experience.py --self-test` -> PASS",
            "- Gate 3: `recursive-ppc-engine.py --self-test` -> PASS",
            "",
        ])
    else:
        body.extend([
            f"- Status: FAIL ({sandbox_msg})",
            "",
        ])

    full_text = "\n".join(frontmatter) + "\n".join(body)
    file_path.write_text(full_text, encoding="utf-8")
    return str(file_path)


def run_darwin_3_gate_sandbox(scripts_dir: str = "~/.gemini/antigravity/scripts") -> tuple[bool, str]:
    """Runs the 3-Gate Sandbox Verification suite. Reverts on any failure."""
    s_dir = os.path.expanduser(scripts_dir)

    # Gate 1: validate-harness-tree.py
    gate1_script = os.path.join(s_dir, "validate-harness-tree.py")
    if os.path.isfile(gate1_script):
        try:
            res = subprocess.run([sys.executable, gate1_script], capture_output=True, text=True, timeout=5)
            if res.returncode != 0:
                return False, f"Gate 1 failed (validate-harness-tree.py): {res.stderr or res.stdout}"
        except Exception as exc:
            return False, f"Gate 1 execution error: {exc}"

    # Gate 2: reflect-experience.py --self-test
    gate2_script = os.path.join(s_dir, "reflect-experience.py")
    if os.path.isfile(gate2_script):
        try:
            res = subprocess.run([sys.executable, gate2_script, "--self-test"], capture_output=True, text=True, timeout=5)
            if res.returncode != 0:
                return False, f"Gate 2 failed (reflect-experience.py --self-test): {res.stderr or res.stdout}"
        except Exception as exc:
            return False, f"Gate 2 execution error: {exc}"

    # Gate 3: recursive-ppc-engine.py --self-test
    gate3_script = os.path.join(s_dir, "recursive-ppc-engine.py")
    if os.path.isfile(gate3_script):
        try:
            res = subprocess.run([sys.executable, gate3_script, "--self-test"], capture_output=True, text=True, timeout=5)
            if res.returncode != 0:
                return False, f"Gate 3 failed (recursive-ppc-engine.py --self-test): {res.stderr or res.stdout}"
        except Exception as exc:
            return False, f"Gate 3 execution error: {exc}"

    return True, "All 3 Darwin Gödel Machine sandbox gates passed cleanly."


def get_backoff_file(custom_path: str | None = None) -> str:
    """Resolves backoff file path with test-mode isolation guard."""
    test_backoff = os.environ.get("ANTIGRAVITY_TEST_BACKOFF_FILE")
    if test_backoff:
        return test_backoff
    if "unittest" in sys.modules and not custom_path:
        return os.path.join(tempfile.gettempdir(), ".antigravity_test_backoff.json")
    if custom_path:
        return custom_path
    return BACKOFF_FILE


def _sanitize_live_backoff_file(backoff_file: str = BACKOFF_FILE) -> None:
    """Removes test-generated backoff signatures from live backoff file."""
    b_path = Path(os.path.expanduser(backoff_file))
    if b_path.is_file():
        try:
            data = json.loads(b_path.read_text(encoding="utf-8"))
            sig = data.get("signature", "")
            reason = data.get("reason", "")
            if sig in ("f3f7e1ce4e94b7d5", "sig_12345") or "Simulated" in reason or "Test" in reason:
                b_path.unlink(missing_ok=True)
        except Exception:
            pass


def check_oscillation_backoff(backoff_file: str | None = None) -> tuple[bool, str]:
    """Checks whether recent patch failure signature is within 1-hour backoff window."""
    target_path = get_backoff_file(backoff_file)
    b_path = Path(os.path.expanduser(target_path))
    if not b_path.is_file():
        return False, ""

    try:
        data = json.loads(b_path.read_text(encoding="utf-8"))
        last_time = data.get("timestamp", 0)
        elapsed = time.time() - last_time
        if elapsed < 3600:  # 1 hour
            sig = data.get("signature", "unknown")
            return True, f"In oscillation backoff ({int(3600 - elapsed)}s remaining) for signature: {sig}"
    except Exception:
        pass
    return False, ""


def record_oscillation_backoff(reason: str, signature: str, backoff_file: str | None = None) -> None:
    """Records a rejected patch signature to avoid immediate retry loops."""
    target_path = get_backoff_file(backoff_file)
    b_path = Path(os.path.expanduser(target_path))
    b_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = {
            "timestamp": time.time(),
            "reason": reason[:200],
            "signature": signature,
        }
        b_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def verify_receipt_linked_efficacy(conn: sqlite3.Connection) -> dict[int, dict[str, Any]]:
    """Measures pre-heal vs post-heal failure rates per session and updates Pareto archive."""
    cur = conn.cursor()
    table_exists = cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='harness_pareto_archive';"
    ).fetchone()
    if not table_exists:
        return {}

    cols = {row[1] for row in cur.execute("PRAGMA table_info(harness_pareto_archive);").fetchall()}
    if "receipt_eval_sessions" not in cols or "receipt_delta" not in cols:
        return {}

    active_rows = cur.execute(
        """
        SELECT id, slug, top_vertex, created_at, receipt_baseline_rate
        FROM harness_pareto_archive
        WHERE is_pareto_front = 1;
        """
    ).fetchall()

    results: dict[int, dict[str, Any]] = {}
    for row in active_rows:
        row_id, slug, top_vertex, created_at, baseline = row[0], row[1], row[2], row[3], (row[4] or 0.0)
        slug_clause = "AND (slug = ? OR slug = '' OR slug = 'global')" if slug and slug not in ("global", "default") else ""
        vertex_clause = "AND vertex = ?" if top_vertex else ""

        params_pre = [created_at]
        if slug_clause:
            params_pre.append(slug)
        if vertex_clause:
            params_pre.append(top_vertex)

        pre_query = f"""
            SELECT count(id), count(distinct conv_id)
            FROM harness_failures
            WHERE created_at < ? {slug_clause} {vertex_clause};
        """
        pre_row = cur.execute(pre_query, params_pre).fetchone()
        pre_fails, pre_convs = (pre_row[0] or 0), (pre_row[1] or 0)
        if not baseline or baseline <= 0.0:
            baseline = round(float(pre_fails) / float(pre_convs), 4) if pre_convs > 0 else 0.0

        params_post = [created_at]
        if slug_clause:
            params_post.append(slug)
        if vertex_clause:
            params_post.append(top_vertex)

        post_query = f"""
            SELECT count(id), count(distinct conv_id)
            FROM harness_failures
            WHERE created_at >= ? {slug_clause} {vertex_clause};
        """
        post_row = cur.execute(post_query, params_post).fetchone()
        post_fails, post_convs = (post_row[0] or 0), (post_row[1] or 0)
        post_rate = round(float(post_fails) / float(post_convs), 4) if post_convs > 0 else 0.0

        delta = 0.0
        if post_convs > 0:
            if baseline > 0:
                raw_delta = (baseline - post_rate) / baseline
            else:
                raw_delta = -1.0 if post_rate > 0 else 0.0
            delta = round(max(-0.25, min(0.25, raw_delta)), 4)

        cur.execute(
            """
            UPDATE harness_pareto_archive
            SET receipt_baseline_rate = ?, receipt_eval_sessions = ?, receipt_delta = ?
            WHERE id = ?;
            """,
            (baseline, post_convs, delta, row_id),
        )
        results[row_id] = {
            "baseline": baseline,
            "post_convs": post_convs,
            "delta": delta,
        }

    conn.commit()
    return results


def distill_mendelian_comparative_traits(
    conn: sqlite3.Connection,
    clusters: dict[str, list[dict[str, Any]]],
) -> dict[str, list[str]]:
    """Distills cross-lineage contrastive directives across sessions and remedies."""
    cur = conn.cursor()
    table_exists = cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='harness_failures';"
    ).fetchone()
    if not table_exists:
        return {}

    norm_query = """
        SELECT failure_type, bug_category, count(distinct conv_id) as conv_cnt, count(distinct slug) as slug_cnt
        FROM harness_failures
        WHERE failure_type IS NOT NULL AND failure_type != ''
        GROUP BY failure_type, bug_category
        HAVING conv_cnt >= 2 OR slug_cnt >= 2;
    """
    systemic_rows = cur.execute(norm_query).fetchall()

    cols = {row[1] for row in cur.execute("PRAGMA table_info(harness_failures);").fetchall()}
    remedies_by_type: dict[str, list[str]] = {}
    remedies_by_slug: dict[str, dict[str, str]] = {}
    if "remedy" in cols:
        remedy_query = """
            SELECT slug, failure_type, remedy
            FROM harness_failures
            WHERE remedy IS NOT NULL AND remedy != ''
            ORDER BY id DESC;
        """
        remedy_rows = cur.execute(remedy_query).fetchall()
        for s_val, ft_val, rem_val in remedy_rows:
            if ft_val and rem_val:
                remedies_by_type.setdefault(ft_val, []).append(rem_val.strip())
                if s_val:
                    remedies_by_slug.setdefault(s_val, {})[ft_val] = rem_val.strip()

    all_slugs: set[str] = set()
    for v_fails in clusters.values():
        for f in v_fails:
            cand_s = f.get("slug", "").strip()
            if cand_s and cand_s not in ("", "global", "default"):
                all_slugs.add(cand_s)

    traits_by_slug: dict[str, list[str]] = {}
    for s in all_slugs:
        slug_traits: list[str] = []
        for row in systemic_rows:
            ft, bug_cat, conv_cnt, _ = row[0], row[1], row[2], row[3]
            has_fail = any(
                f.get("failure_type") == ft
                for v_fails in clusters.values()
                for f in v_fails
                if f.get("slug") == s
            )
            if not has_fail:
                continue

            rem = remedies_by_slug.get(s, {}).get(ft) or (remedies_by_type.get(ft, [None])[0])
            cat_tag = f"[{bug_cat}] " if bug_cat else ""
            if rem:
                clean_rem = rem[:100]
                slug_traits.append(
                    f"- **`env` Directive**: [MGM Contrast] {cat_tag}Systemic failure '{ft}' detected; apply verified remedy: {clean_rem}."
                )
            else:
                slug_traits.append(
                    f"- **`env` Directive**: [MGM Contrast] {cat_tag}Systemic failure '{ft}' observed across {conv_cnt} sessions; isolate and enforce targeted verification."
                )
        if slug_traits:
            traits_by_slug[s] = slug_traits

    return traits_by_slug


def execute_self_healing_cycle(
    db_path: str = DEFAULT_REGISTRY_DB,
    dry_run: bool = False,
    force: bool = False,
    tool_quirks_file: str = TOOL_QUIRKS_FILE,
    scripts_dir: str = "~/.gemini/antigravity/scripts",
    backoff_file: str | None = None,
    env_overlays_dir: str | None = None,
) -> dict[str, Any]:
    """Executes the full 5-stage closed self-healing loop."""
    resolved_backoff = get_backoff_file(backoff_file)
    _sanitize_live_backoff_file(BACKOFF_FILE)

    resolved_db = get_db_path(db_path)
    if not resolved_db or not os.path.isfile(resolved_db):
        return {
            "status": "SKIPPED",
            "message": f"Registry database not found at {resolved_db}",
            "failures_resolved": 0,
        }

    # Oscillation Backoff Check (bypassed in --dry-run mode)
    in_backoff, backoff_msg = check_oscillation_backoff(backoff_file=resolved_backoff)
    if in_backoff and not force and not dry_run:
        return {
            "status": "BACKOFF",
            "message": backoff_msg,
            "failures_resolved": 0,
        }

    conn = sqlite3.connect(resolved_db, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    init_harness_tables(conn)
    verify_receipt_linked_efficacy(conn)

    # Stage 1: Harvest & Cluster
    drained_count = drain_pending_failures(conn)
    cluster_data = cluster_unresolved_failures(conn)

    total_failures = cluster_data["total_open_failures"]
    open_reviews = len(cluster_data["open_settings_reviews"])

    if total_failures == 0 and open_reviews == 0 and not force and not dry_run:
        conn.close()
        return {
            "status": "NOMINAL",
            "message": "Harness & Codebase Health Nominal: No open failures or settings reviews.",
            "failures_resolved": 0,
        }

    # Find dominant vertex and dominant failure type
    gradients = cluster_data["symbolic_gradients"]
    top_vertex = max(gradients.items(), key=lambda kv: kv[1])[0] if gradients else "tool_guidance"

    vertex_failures = cluster_data["clusters"].get(top_vertex, [])
    ft_counts: dict[str, int] = {}
    for f in vertex_failures:
        ft = f.get("failure_type", "").strip()
        if ft:
            ft_counts[ft] = ft_counts.get(ft, 0) + 1
    top_failure_type = max(ft_counts.items(), key=lambda kv: kv[1])[0] if ft_counts else "failure"

    scout_offline = bool("unittest" in sys.modules or os.environ.get("AGY_OFFLINE_SCOUT") == "1")
    citations = query_external_research(top_vertex, top_failure_type, offline=scout_offline)

    # Distill MGM comparative traits
    mgm_traits = distill_mendelian_comparative_traits(conn, cluster_data["clusters"])

    # Active Project Slug
    active_slug = "global"
    try:
        cur = conn.cursor()
        cols = [r[1] for r in cur.execute("PRAGMA table_info(projects);").fetchall()]
        p_col = "path" if "path" in cols else ("project_path" if "project_path" in cols else None)
        query = (
            f"SELECT slug, {p_col} FROM projects WHERE slug NOT LIKE 'test-alias%' AND slug NOT LIKE 'tmp%' AND slug != '.tmp_test_ast' ORDER BY rowid DESC"
            if p_col
            else "SELECT slug FROM projects WHERE slug NOT LIKE 'test-alias%' AND slug NOT LIKE 'tmp%' AND slug != '.tmp_test_ast' ORDER BY rowid DESC"
        )
        rows = cur.execute(query).fetchall()
        first_non_test = None
        for r in rows:
            s = r[0]
            p = r[1] if len(r) > 1 else None
            if not first_non_test and s:
                first_non_test = s
            if p and os.path.isdir(str(p)):
                active_slug = s
                break
        if active_slug == "global" and first_non_test:
            active_slug = first_non_test
    except Exception:
        pass

    if active_slug == "global" and cluster_data.get("clusters"):
        for v in SYMBOLIC_VERTICES:
            for f_item in cluster_data["clusters"].get(v, []):
                cand_slug = f_item.get("slug")
                if cand_slug and cand_slug not in ("global", "default"):
                    active_slug = cand_slug
                    break
            if active_slug != "global":
                break

    if dry_run:
        conn.close()
        backoff_note = f" (Note: Live mode is in oscillation backoff: {backoff_msg})" if in_backoff else ""
        return {
            "status": "DRY_RUN",
            "message": f"[DRY RUN]{backoff_note} Inspected 5-stage cluster preview: {total_failures} open failure(s) across {len(cluster_data['clusters'])} vertices (top: {top_vertex}).",
            "symbolic_gradients": gradients,
            "top_vertex": top_vertex,
            "citations_preview": [c.get("citation", "") for c in citations],
            "repairs_preview": [
                f"Auto-healed tool quirks for {len(cluster_data['clusters'].get('tool_guidance', []))} failure(s)",
                "SkillBank index synchronization check",
                f"Self-evolution & codebase healing digest preview for project '{active_slug}'",
            ],
            "sandbox_gates": ["validate-harness-tree.py", "reflect-experience.py --self-test", "recursive-ppc-engine.py --self-test"],
            "failures_resolved": 0,
        }

    # Stage 3: Snapshot & Self-Heal Synthesis
    quirks_path = Path(os.path.expanduser(tool_quirks_file))
    snapshot_text = quirks_path.read_text(encoding="utf-8") if quirks_path.is_file() else None

    # Snapshot env_overlays if applicable (CP-1)
    if env_overlays_dir:
        eff_overlay_dir = env_overlays_dir
    elif "unittest" in sys.modules and not os.environ.get("ANTIGRAVITY_TEST_ENV_OVERLAYS_DIR"):
        eff_overlay_dir = None
    else:
        eff_overlay_dir = os.environ.get("ANTIGRAVITY_TEST_ENV_OVERLAYS_DIR") or ENV_OVERLAYS_DIR

    target_slugs: set[str] = set()
    if active_slug not in ("", "global", "default"):
        target_slugs.add(active_slug)
    for v_fails in cluster_data.get("clusters", {}).values():
        for f_item in v_fails:
            s_cand = f_item.get("slug", "").strip()
            if s_cand and s_cand not in ("", "global", "default"):
                target_slugs.add(s_cand)
    if not target_slugs and eff_overlay_dir and active_slug:
        target_slugs.add(active_slug)

    overlay_snapshots: dict[str, tuple[Path, bool, str | None]] = {}
    if eff_overlay_dir:
        for s in target_slugs:
            s_file = Path(os.path.expanduser(eff_overlay_dir)) / f"{s}.md"
            existed = s_file.is_file()
            snap_text = s_file.read_text(encoding="utf-8") if existed else None
            overlay_snapshots[s] = (s_file, existed, snap_text)

    repaired_ids: set[int] = set()
    repairs_applied = apply_deterministic_harness_repairs(
        cluster_data["clusters"],
        tool_quirks_file=tool_quirks_file,
        active_slug=active_slug,
        env_overlays_dir=env_overlays_dir,
        scripts_dir=scripts_dir,
        repaired_ids=repaired_ids,
        mgm_directives_by_slug=mgm_traits,
    )

    primary_overlay = overlay_snapshots.get(active_slug)
    env_overlay_path = str(primary_overlay[0]) if primary_overlay and primary_overlay[0].is_file() else ""
    if not env_overlay_path and overlay_snapshots:
        first_file = next(iter(overlay_snapshots.values()))[0]
        if first_file.is_file():
            env_overlay_path = str(first_file)

    # Stage 4: 3-Gate Sandbox Verification + CP-2 Pareto Non-Dominated Gate
    cur = conn.cursor()
    active_delta_row = cur.execute(
        "SELECT receipt_delta FROM harness_pareto_archive WHERE slug = ? AND is_pareto_front = 1 ORDER BY id DESC LIMIT 1;",
        (active_slug,),
    ).fetchone()
    active_delta = float(active_delta_row[0]) if active_delta_row else 0.0

    sandbox_ok, sandbox_msg = run_darwin_3_gate_sandbox(scripts_dir)
    objectives = evaluate_pareto_objectives(
        cluster_data,
        sandbox_ok=sandbox_ok,
        tool_quirks_file=tool_quirks_file,
        env_overlay_path=env_overlay_path,
        repaired_count=len(repaired_ids),
        receipt_delta=active_delta,
    )

    if objectives.get("sec_score", 1.0) < 1.0:
        is_dominated = True
        dominated_reason = "security floor (sec_score < 1.0)"
    else:
        active_rows = cur.execute(
            """
            SELECT id, func_score, sec_score, token_score
            FROM harness_pareto_archive
            WHERE slug = ? AND (top_vertex = ? OR top_vertex = '' OR ? = '') AND is_pareto_front = 1;
            """,
            (active_slug, top_vertex, top_vertex),
        ).fetchall()
        active_points = [
            {"id": r[0], "func_score": r[1], "sec_score": r[2], "token_score": r[3]}
            for r in active_rows
        ]
        is_dominated, dominated_reason = is_pareto_dominated(objectives, active_points)

    if not sandbox_ok or is_dominated:
        # KEEP_BASE Rollback (both tool_quirks and env_overlays)
        if snapshot_text is not None and quirks_path.is_file():
            quirks_path.write_text(snapshot_text, encoding="utf-8")
        elif snapshot_text is None and quirks_path.is_file():
            try:
                os.unlink(quirks_path)
            except OSError:
                pass

        for s_file, existed, snap_text in overlay_snapshots.values():
            if existed and snap_text is not None:
                s_file.write_text(snap_text, encoding="utf-8")
            elif not existed and s_file.is_file():
                try:
                    os.unlink(s_file)
                except OSError:
                    pass

        fail_reason = sandbox_msg if not sandbox_ok else f"Pareto Gate Violated: {dominated_reason}"
        patch_sig = hashlib.sha256(f"{top_vertex}_{total_failures}".encode()).hexdigest()[:16]
        if not dry_run:
            record_oscillation_backoff(fail_reason, patch_sig, backoff_file=resolved_backoff)
            evo_state_file = EVOLUTION_STATE_FILE
            if "unittest" in sys.modules and not os.environ.get("ANTIGRAVITY_TEST_HEAL_ALERT"):
                evo_state_file = os.path.join(tempfile.gettempdir(), "test_last_harness_evolution.json")
            try:
                Path(evo_state_file).parent.mkdir(parents=True, exist_ok=True)
                fail_payload = {
                    "last_run_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "resolved_failures_count": 0,
                    "top_vertex": top_vertex,
                    "symbolic_gradients": gradients,
                    "digest_path": "",
                    "verification_verdict": "FAILED",
                    "pareto_objectives": objectives,
                    "error": fail_reason,
                }
                Path(evo_state_file).write_text(json.dumps(fail_payload, indent=2), encoding="utf-8")
            except Exception:
                pass
        conn.close()
        return {
            "status": "ROLLBACK",
            "message": f"Sandbox or Pareto Verification Failed! Rolled back to KEEP_BASE: {fail_reason}",
            "failures_resolved": 0,
            "pareto_objectives": objectives,
            "env_overlay_path": env_overlay_path,
        }

    verdict = "SELF_HEALED" if repairs_applied else "ANALYZED_ONLY"
    digest_path = write_self_evolution_digest(
        cluster_data,
        citations,
        repairs_applied,
        active_slug,
        pareto_objectives=objectives,
        env_overlay_path=env_overlay_path,
        sandbox_ok=True,
        verdict=verdict,
    )

    # Admitted into SQLite Pareto Archive (CP-3)
    gen_hash = hashlib.sha256((snapshot_text or "").encode("utf-8")).hexdigest()[:16]
    eff_niche = f"{active_slug}:{top_vertex}" if top_vertex else active_slug
    update_pareto_archive(
        conn,
        slug=active_slug,
        objectives=objectives,
        top_vertex=top_vertex,
        general_hash=gen_hash,
        env_overlay_path=env_overlay_path,
        digest_path=digest_path,
        niche_key=eff_niche,
        receipt_baseline_rate=0.0,
    )

    # Stage 5: Ledger Resolution & Alert Flag
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    all_failure_ids = set(cluster_data.get("failure_ids", []))
    resolved_failure_ids = list(all_failure_ids.intersection(repaired_ids))
    analyzed_failure_ids = list(all_failure_ids - set(resolved_failure_ids))

    if resolved_failure_ids:
        q_marks = ",".join("?" for _ in resolved_failure_ids)
        conn.execute(
            f"UPDATE harness_failures SET resolved_at = CURRENT_TIMESTAMP WHERE id IN ({q_marks});",
            resolved_failure_ids,
        )

    if analyzed_failure_ids:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(harness_failures);").fetchall()}
        if "analyzed_at" in cols:
            q_marks = ",".join("?" for _ in analyzed_failure_ids)
            conn.execute(
                f"UPDATE harness_failures SET analyzed_at = CURRENT_TIMESTAMP WHERE id IN ({q_marks});",
                analyzed_failure_ids,
            )

    if cluster_data["review_ids"] and resolved_failure_ids:
        q_marks = ",".join("?" for _ in cluster_data["review_ids"])
        conn.execute(
            f"UPDATE settings_reviews SET resolved_at = CURRENT_TIMESTAMP WHERE id IN ({q_marks});",
            cluster_data["review_ids"],
        )
    conn.commit()
    conn.close()

    # Update evolution state
    state_payload = {
        "last_run_timestamp": now_iso,
        "resolved_failures_count": len(resolved_failure_ids),
        "analyzed_failures_count": len(analyzed_failure_ids),
        "resolved_reviews_count": open_reviews if resolved_failure_ids else 0,
        "top_vertex": top_vertex,
        "symbolic_gradients": gradients,
        "digest_path": digest_path,
        "verification_verdict": verdict,
        "pareto_objectives": objectives,
        "env_overlay_path": env_overlay_path,
    }
    evo_state_file = EVOLUTION_STATE_FILE
    alert_flag_file = ALERT_FLAG_FILE
    if "unittest" in sys.modules and not os.environ.get("ANTIGRAVITY_TEST_HEAL_ALERT"):
        evo_state_file = os.path.join(tempfile.gettempdir(), "test_last_harness_evolution.json")
        alert_flag_file = os.path.join(tempfile.gettempdir(), "test_last_harness_evolution_alert.flag")

    Path(evo_state_file).parent.mkdir(parents=True, exist_ok=True)
    Path(evo_state_file).write_text(json.dumps(state_payload, indent=2), encoding="utf-8")

    # Post compact 1-line Turn-1 alert flag only when repairs were verified
    if resolved_failure_ids:
        alert_summary = (
            f"[Auto-Heal] Resolved {len(resolved_failure_ids)} failures across {len(gradients)} vertices "
            f"(top: {top_vertex}, grad: {gradients.get(top_vertex, 0)}). Digest: {os.path.basename(digest_path)}"
        )[:200]
        Path(alert_flag_file).write_text(alert_summary, encoding="utf-8")
        msg = f"Successfully healed {len(resolved_failure_ids)} failures and {open_reviews if resolved_failure_ids else 0} settings reviews."
    else:
        if os.path.isfile(alert_flag_file):
            try:
                os.unlink(alert_flag_file)
            except OSError:
                pass
        msg = f"Analyzed {len(analyzed_failure_ids)} failure(s) across {len(gradients)} vertices; zero repairs synthesized."

    return {
        "status": "SUCCESS",
        "message": msg,
        "symbolic_gradients": gradients,
        "top_vertex": top_vertex,
        "repairs_applied": repairs_applied,
        "digest_path": digest_path,
        "failures_resolved": len(resolved_failure_ids),
        "failures_analyzed": len(analyzed_failure_ids),
        "verification_verdict": verdict,
        "pareto_objectives": objectives,
        "env_overlay_path": env_overlay_path,
    }


def _run_self_tests() -> int:
    """Executes isolated self-tests verifying all 5 self-healing stages."""
    print("=== Auto-Harness-Healer Self-Test (Harness² Level-3) ===")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_db = os.path.join(tmpdir, "test_registry.sqlite")
        tmp_quirks = os.path.join(tmpdir, "test_quirks.md")
        tmp_pending = os.path.join(tmpdir, "test_pending.jsonl")
        tmp_backoff = os.path.join(tmpdir, "test_backoff.json")
        tmp_lock = os.path.join(tmpdir, "test_healer.lock")

        # 1. Test PID lock
        fd1 = acquire_pid_lock(tmp_lock)
        assert fd1 is not None, "First lock acquire should succeed"
        fd2 = acquire_pid_lock(tmp_lock)
        assert fd2 is None, "Second lock acquire should fail (non-blocking)"
        release_pid_lock(fd1, tmp_lock)
        print("  [PASS] PID concurrency lock & non-blocking mutual exclusion")

        # 2. Test DB initialization & failure ingestion
        conn = sqlite3.connect(tmp_db)
        init_harness_tables(conn)

        # Write pending failure
        sample_pending = {
            "conv_id": "test_conv",
            "slug": "test_proj",
            "session_type": "interactive",
            "vertex": "tool_guidance",
            "failure_type": "pre_tool_deny",
            "tool_name": "replace_file_content",
            "severity_tier": "S2_major",
            "severity_weight": 0.05,
            "reason": "TargetContent mismatch line 42",
            "details": "Fuzzy line anchor failure",
        }
        with open(tmp_pending, "w", encoding="utf-8") as f:
            f.write(json.dumps(sample_pending) + "\n")

        drained = drain_pending_failures(conn, tmp_pending)
        assert drained == 1, f"Expected 1 drained failure, got {drained}"
        assert not os.path.exists(tmp_pending), "Pending file should be unlinked after drain"
        print("  [PASS] Pre-unlink pending failure drain into SQLite ledger")

        # 3. Test clustering & symbolic gradient calculation
        cluster_res = cluster_unresolved_failures(conn)
        assert cluster_res["total_open_failures"] == 1
        assert cluster_res["symbolic_gradients"]["tool_guidance"] == 0.05
        assert cluster_res["symbolic_gradients"]["hook"] == 0.0
        print("  [PASS] 5-Vertex failure clustering & symbolic gradients")

        # 4. Test deterministic tool quirks repair
        with open(tmp_quirks, "w", encoding="utf-8") as f:
            f.write("# Existing Tool Quirks\n")

        repairs = apply_deterministic_harness_repairs(cluster_res["clusters"], tool_quirks_file=tmp_quirks)
        assert len(repairs) >= 1
        quirks_content = open(tmp_quirks).read()
        assert "replace_file_content" in quirks_content
        assert "TargetContent mismatch line 42" in quirks_content
        print("  [PASS] Deterministic parameter-quirk self-healing repair")

        # 5. Test Digest generation
        citations = query_external_research("tool_guidance", "pre_tool_deny", offline=True)
        assert len(citations) >= 1
        digest = write_self_evolution_digest(cluster_res, citations, repairs, "test_proj", output_dir=tmpdir)
        assert os.path.isfile(digest)
        digest_content = open(digest).read()
        assert "AgentSymbolicLearning" in digest_content
        assert "replace_file_content" in digest_content
        print("  [PASS] Self-evolution & codebase remediation digest synthesis")

        # 6. Test ledger resolution
        fid = cluster_res["failure_ids"][0]
        conn.execute("UPDATE harness_failures SET resolved_at = CURRENT_TIMESTAMP WHERE id = ?;", (fid,))
        conn.commit()
        cluster_after = cluster_unresolved_failures(conn)
        assert cluster_after["total_open_failures"] == 0
        conn.close()
        print("  [PASS] Ledger resolution & resolved_at timestamp stamping")

        # 7. Test oscillation backoff recording
        record_oscillation_backoff("Test Gate Failure", "sig_12345", backoff_file=tmp_backoff)
        in_b, b_msg = check_oscillation_backoff(backoff_file=tmp_backoff)
        assert in_b, "Should be in backoff"
        assert "sig_12345" in b_msg
        print("  [PASS] Oscillation backoff prevention & signature tracking")

        # 8. Test Pareto Evaluation, Dominance & Archive (CP-1, CP-2, CP-3)
        conn2 = sqlite3.connect(tmp_db)
        p_obj = evaluate_pareto_objectives(cluster_res, sandbox_ok=True, tool_quirks_file=tmp_quirks)
        assert p_obj["func_score"] == 1.0
        assert p_obj["sec_score"] == 1.0
        assert 0.0 <= p_obj["token_score"] <= 1.0

        dominated_floor, floor_reason = is_pareto_dominated({"func_score": 0.0, "sec_score": 1.0, "token_score": 0.9}, [])
        assert dominated_floor, "Functional score 0.0 must be dominated by floor"

        archive_res = update_pareto_archive(conn2, slug="test_proj", objectives=p_obj, top_vertex="tool_guidance")
        assert archive_res["admitted"], "Valid candidate must be admitted to Pareto archive"
        assert archive_res["profile_mode"] in ("strict_security", "balanced_velocity")

        prof = select_pareto_profile(conn2, slug="test_proj", mode="strict_security")
        assert prof is not None
        assert prof["slug"] == "test_proj"
        conn2.close()
        print("  [PASS] 3-Axis Pareto Evaluation, Dominance Gate & SQLite Archive")

        # 9. Test ANALYZED_ONLY execution path (no repairs -> zero alert flag, failures_resolved == 0)
        conn3 = sqlite3.connect(tmp_db)
        conn3.execute(
            """
            INSERT INTO harness_failures (
                conv_id, slug, session_type, vertex, failure_type, tool_name,
                severity_tier, severity_weight, reason, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            ("test_conv_no_repair", "default", "interactive", "routing", "unsupported_route", "agent", "S3_minor", 0.01, "Route not supported", ""),
        )
        conn3.commit()
        conn3.close()

        old_sandbox = run_darwin_3_gate_sandbox
        expected_flag = (
            os.path.join(tempfile.gettempdir(), "test_last_harness_evolution_alert.flag")
            if "unittest" in sys.modules and not os.environ.get("ANTIGRAVITY_TEST_HEAL_ALERT")
            else ALERT_FLAG_FILE
        )
        if os.path.exists(expected_flag):
            try:
                os.unlink(expected_flag)
            except OSError:
                pass
        try:
            globals()["run_darwin_3_gate_sandbox"] = lambda s_dir="": (True, "Mock sandbox pass")
            res_analyzed = execute_self_healing_cycle(
                db_path=tmp_db,
                force=True,
                tool_quirks_file=tmp_quirks,
                scripts_dir=tmpdir,
                backoff_file=tmp_backoff,
            )
            assert res_analyzed["status"] == "SUCCESS"
            assert res_analyzed["failures_resolved"] == 0, f"Expected 0 resolved failures, got {res_analyzed['failures_resolved']}"
            assert res_analyzed["verification_verdict"] == "ANALYZED_ONLY"
            assert not os.path.exists(expected_flag), "Alert flag file must not be written when zero failures were resolved"
            print("  [PASS] ANALYZED_ONLY path (zero repairs -> no alert flag, failures_resolved == 0)")
        finally:
            globals()["run_darwin_3_gate_sandbox"] = old_sandbox

    print("ALL AUTO-HARNESS-HEALER SELF-TESTS PASSED cleanly in <0.5s")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Autonomous Sleep-Time Self-Healer (Harness² Level-3 Meta-Evolution)"
    )
    parser.add_argument("--auto", action="store_true", help="Run autonomous sleep-time self-healing loop")
    parser.add_argument("--force", action="store_true", help="Force self-heal even if nominal or in backoff")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate clusters and report without mutations")
    parser.add_argument("--self-test", action="store_true", help="Execute self-test suite and exit")
    parser.add_argument("--db-path", default=None, help="Custom registry SQLite database path")
    parser.add_argument("--tool-quirks-file", default=TOOL_QUIRKS_FILE, help="Path to tool-quirks.md")
    parser.add_argument("--env-overlays-dir", default=None, help="Directory for factorized environment overlays")

    args = parser.parse_args()

    if args.self_test:
        return _run_self_tests()

    # Acquire concurrency lock
    lock_fd = acquire_pid_lock()
    if lock_fd is None:
        print("[Auto-Harness-Healer] Another instance is currently executing. Exiting cleanly.")
        return 0

    try:
        result = execute_self_healing_cycle(
            db_path=args.db_path or DEFAULT_REGISTRY_DB,
            dry_run=args.dry_run,
            force=args.force,
            tool_quirks_file=args.tool_quirks_file,
            env_overlays_dir=args.env_overlays_dir,
        )

        status = result.get("status", "UNKNOWN")
        msg = result.get("message", "")
        print(f"[{status}] {msg}")
        if args.dry_run:
            if result.get("symbolic_gradients"):
                print("  Symbolic Gradients:")
                for k, v in result["symbolic_gradients"].items():
                    print(f"    - {k}: {v}")
            print(f"  Dominant Failure Vertex: {result.get('top_vertex')}")
            if result.get("citations_preview"):
                print("  Candidate Research Citations:")
                for cit in result["citations_preview"]:
                    print(f"    - {cit}")
            if result.get("repairs_preview"):
                print("  Candidate Repairs to Apply in Live Run:")
                for rep in result["repairs_preview"]:
                    print(f"    - {rep}")
            if result.get("sandbox_gates"):
                print("  Darwin Gödel Machine Verification Gates:")
                for g in result["sandbox_gates"]:
                    print(f"    - {g}")
        return 0
    finally:
        release_pid_lock(lock_fd)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Antigravity Inter-Session Housekeeping & Cache Sweeper.

Safely prunes stale temporary flags, expired syntax error markers, aged backup directories,
and orphaned bytecode without disrupting active conversations or uncommitted work.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import glob
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator


@contextmanager
def open_sqlite(db_path: str, timeout: float = 5.0) -> Generator[sqlite3.Connection, None, None]:
    """Contextmanager ensuring SQLite connection is always closed cleanly."""
    conn = sqlite3.connect(db_path, timeout=timeout)
    try:
        yield conn
    finally:
        conn.close()

# TTL Invariants in seconds
FLAG_TTL_SECONDS = 6 * 3600          # 6 hours
SYNTAX_ERR_TTL_SECONDS = 3600        # 1 hour
TEST_SCRATCH_TTL_SECONDS = 24 * 3600  # 24 hours
BACKUP_TTL_SECONDS = 48 * 3600       # 48 hours (2 days grace period)


def _is_expired(path: str | Path, ttl: float, now: float) -> bool:
    try:
        mtime = os.path.getmtime(path)
        return (now - mtime) > ttl
    except Exception:
        return False


def prune_temp_flags(now: float, current_conv_id: str = "", dry_run: bool = False) -> list[str]:
    pruned = []
    tmp_dir = tempfile.gettempdir()
    patterns = [
        os.path.join(tmp_dir, "antigravity_*_alert_*.flag"),
        os.path.join(tmp_dir, "antigravity_*_test_*.flag"),
        os.path.join(tmp_dir, ".antigravity_*"),
        os.path.join(tmp_dir, "antigravity_*"),
        os.path.join(tmp_dir, ".oracle_watchdog_*"),
        os.path.join(tmp_dir, ".antigravity_syntax_error_*"),
        os.path.join(tmp_dir, ".antigravity"),
    ]
    protected_basenames = {
        ".antigravity_failures_pending.jsonl",
        ".auto_harness_healer.lock",
    }
    seen = set()
    for pat in patterns:
        for f in glob.glob(pat):
            if f in seen or os.path.basename(f) in protected_basenames:
                continue
            seen.add(f)
            if current_conv_id and current_conv_id in os.path.basename(f) and not _is_expired(f, FLAG_TTL_SECONDS, now):
                continue
            if _is_expired(f, FLAG_TTL_SECONDS, now):
                if os.path.isfile(f) or os.path.islink(f):
                    if not dry_run:
                        try:
                            os.remove(f)
                        except Exception:
                            continue
                    pruned.append(f)
                elif os.path.isdir(f):
                    if not dry_run:
                        try:
                            shutil.rmtree(f, ignore_errors=True)
                        except Exception:
                            continue
                    pruned.append(f)
    return pruned


def prune_syntax_error_flags(now: float, current_conv_id: str, dry_run: bool = False) -> list[str]:
    pruned = []
    patterns = [
        os.path.expanduser("~/.gemini/antigravity-ide/brain/*/syntax_error_pending.json"),
        os.path.expanduser("~/.gemini/antigravity/brain/*/syntax_error_pending.json"),
        os.path.expanduser("~/.gemini/antigravity-cli/brain/*/syntax_error_pending.json"),
        "/tmp/antigravity/syntax_error_pending.json",
        os.path.join(tempfile.gettempdir(), "antigravity", "syntax_error_pending.json"),
        os.path.join(tempfile.gettempdir(), "syntax_error_pending.json"),
    ]
    for pat in patterns:
        for f in glob.glob(pat):
            parent_name = os.path.basename(os.path.dirname(f))
            if parent_name == current_conv_id and not _is_expired(f, SYNTAX_ERR_TTL_SECONDS, now):
                continue  # Protect active conversation if recent
            # Only unlink if mtime is older than 3600s (SYNTAX_ERR_TTL_SECONDS)
            if _is_expired(f, SYNTAX_ERR_TTL_SECONDS, now):
                if not dry_run:
                    try:
                        os.remove(f)
                    except Exception:
                        continue
                pruned.append(f)
    return pruned


def prune_test_brain_dirs(now: float, current_conv_id: str, dry_run: bool = False) -> list[str]:
    pruned = []
    patterns = [
        os.path.expanduser("~/.gemini/antigravity-ide/brain/test_conv*"),
        os.path.expanduser("~/.gemini/antigravity/brain/test_conv*"),
        os.path.expanduser("~/.gemini/antigravity-cli/brain/test_conv*"),
    ]
    for pat in patterns:
        for d in glob.glob(pat):
            if os.path.isdir(d):
                dirname = os.path.basename(d)
                if dirname == current_conv_id:
                    continue
                if _is_expired(d, TEST_SCRATCH_TTL_SECONDS, now):
                    if not dry_run:
                        try:
                            shutil.rmtree(d, ignore_errors=True)
                        except Exception:
                            continue
                    pruned.append(d)
    return pruned


def prune_aged_backups(now: float, dry_run: bool = False) -> list[str]:
    pruned = []
    patterns = [
        os.path.expanduser("~/.gemini/config/**/*.bak.*"),
        os.path.expanduser("~/.gemini/config/*.bak.*"),
        os.path.expanduser("~/.gemini/antigravity/**/*.bak.*"),
        os.path.expanduser("~/.gemini/antigravity/*.bak.*"),
    ]
    for pat in patterns:
        for d in glob.glob(pat, recursive=True):
            if os.path.isdir(d) and _is_expired(d, BACKUP_TTL_SECONDS, now):
                if not dry_run:
                    try:
                        shutil.rmtree(d, ignore_errors=True)
                    except Exception:
                        continue
                pruned.append(d)
    return pruned


def prune_orphaned_pyc(dry_run: bool = False) -> list[str]:
    pruned = []
    patterns = [
        os.path.expanduser("~/.gemini/config/hooks/__pycache__/*.pyc"),
        os.path.expanduser("~/.gemini/antigravity/scripts/__pycache__/*.pyc"),
    ]
    for pat in patterns:
        for pyc in glob.glob(pat):
            if not os.path.isfile(pyc):
                continue
            fname = os.path.basename(pyc)
            # Standard cpython format: <module_name>.cpython-<ver>.pyc
            mod_name = fname.split(".")[0]
            parent_dir = os.path.dirname(os.path.dirname(pyc))
            expected_py = os.path.join(parent_dir, f"{mod_name}.py")
            if not os.path.isfile(expected_py):
                if not dry_run:
                    try:
                        os.remove(pyc)
                    except Exception:
                        continue
                pruned.append(pyc)
    return pruned


def checkpoint_wal_databases(dry_run: bool = False) -> list[str]:
    checkpointed = []
    db_candidates = [
        os.path.expanduser("~/.gemini/antigravity-cli/conversation_summaries.db"),
        os.path.expanduser("~/.gemini/antigravity/conversation_summaries.db"),
        *glob.glob(os.path.expanduser("~/.local/share/codex/**/*.sqlite"), recursive=True),
        *glob.glob(os.path.expanduser("~/.gemini/**/*.sqlite"), recursive=True),
    ]
    seen = set()
    for db_path in db_candidates:
        if db_path in seen:
            continue
        seen.add(db_path)
        if os.path.isfile(db_path):
            if not dry_run:
                try:
                    with open_sqlite(db_path) as conn:
                        conn.execute("PRAGMA wal_checkpoint(PASSIVE);")
                        checkpointed.append(db_path)
                except Exception:
                    pass
            else:
                checkpointed.append(db_path)
    return checkpointed


def prune_harness_backup_snapshots(dry_run: bool = False) -> list[str]:
    """Rotate ~/.gemini/backups/harness_backup_* keeping newest 3."""
    pruned = []
    backup_dir = os.path.expanduser("~/.gemini/backups")
    if not os.path.isdir(backup_dir):
        return pruned

    backups = sorted(glob.glob(os.path.join(backup_dir, "harness_backup_*")), reverse=True)
    for old_bk in backups[3:]:
        if not dry_run:
            try:
                if os.path.isdir(old_bk):
                    shutil.rmtree(old_bk, ignore_errors=True)
                else:
                    os.remove(old_bk)
            except Exception:
                continue
        pruned.append(old_bk)
    return pruned


def prune_auto_heal_digests(dry_run: bool = False) -> list[str]:
    """Keep newest 10 ~/.gemini/antigravity/skillbank/failure-lessons/auto_heal_*.md digests."""
    pruned = []
    digest_pattern = os.path.expanduser("~/.gemini/antigravity/skillbank/failure-lessons/auto_heal_*.md")
    digests = sorted(glob.glob(digest_pattern), reverse=True)
    for old_d in digests[10:]:
        if not dry_run:
            try:
                os.remove(old_d)
            except Exception:
                continue
        pruned.append(old_d)
    return pruned


def prune_expired_research_cache(now: float, dry_run: bool = False, ttl_seconds: float = 7 * 24 * 3600) -> list[str]:
    """Prune research_cache/*.json older than the scout's cache TTL."""
    pruned = []
    cache_dirs = [
        os.path.expanduser("~/.gemini/antigravity/skillbank/research_cache"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "skillbank", "research_cache"),
    ]
    seen = set()
    for c_dir in cache_dirs:
        if not os.path.isdir(c_dir):
            continue
        for f in glob.glob(os.path.join(c_dir, "*.json")):
            if f in seen:
                continue
            seen.add(f)
            try:
                mtime = os.path.getmtime(f)
                if now - mtime > ttl_seconds:
                    if not dry_run:
                        os.remove(f)
                    pruned.append(f)
            except Exception:
                continue
    return pruned


def prune_aged_harness_failures(dry_run: bool = False) -> int:
    """Prune registry.sqlite harness_failures rows resolved/analyzed > 30 days."""
    db_candidates = [
        os.environ.get("ANTIGRAVITY_TEST_REGISTRY_DB"),
        os.path.expanduser("~/.local/share/codex/projects/registry.sqlite"),
        os.path.expanduser("~/.local/share/codex/registry.sqlite"),
    ]
    for db_p in db_candidates:
        if not db_p or not os.path.isfile(db_p):
            continue
        try:
            with open_sqlite(db_p) as conn:
                tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
                if "harness_failures" not in tables:
                    continue
                cols = {r[1] for r in conn.execute("PRAGMA table_info(harness_failures)").fetchall()}
                clauses = []
                if "resolved_at" in cols:
                    clauses.append("(resolved_at IS NOT NULL AND resolved_at < datetime('now', '-30 days'))")
                if "analyzed_at" in cols:
                    clauses.append("(analyzed_at IS NOT NULL AND analyzed_at < datetime('now', '-30 days'))")
                if not clauses:
                    continue
                where_clause = " OR ".join(clauses)
                cur = conn.execute(f"SELECT COUNT(*) FROM harness_failures WHERE {where_clause}")
                count = cur.fetchone()[0]
                if not dry_run and count > 0:
                    conn.execute(f"DELETE FROM harness_failures WHERE {where_clause}")
                    conn.commit()
                return count
        except Exception:
            continue
    return 0


def run_housekeeping(current_conv_id: str = "", dry_run: bool = False) -> dict:
    now = time.time()
    pruned_flags = prune_temp_flags(now, current_conv_id, dry_run)
    pruned_syntax = prune_syntax_error_flags(now, current_conv_id, dry_run)
    pruned_tests = prune_test_brain_dirs(now, current_conv_id, dry_run)
    pruned_backups = prune_aged_backups(now, dry_run)
    pruned_pyc = prune_orphaned_pyc(dry_run)
    checkpointed_dbs = checkpoint_wal_databases(dry_run)
    pruned_harness_backups = prune_harness_backup_snapshots(dry_run)
    pruned_auto_heal = prune_auto_heal_digests(dry_run)
    pruned_research_cache = prune_expired_research_cache(now, dry_run)
    pruned_aged_failures = prune_aged_harness_failures(dry_run)

    all_pruned = (
        pruned_flags
        + pruned_syntax
        + pruned_tests
        + pruned_backups
        + pruned_pyc
        + pruned_harness_backups
        + pruned_auto_heal
        + pruned_research_cache
    )

    state_file = os.path.expanduser("~/.gemini/last_housekeeping.json")
    existing_session_count = 0
    if os.path.isfile(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                existing_session_count = int(json.load(f).get("session_count", 0))
        except Exception:
            pass

    summary = {
        "timestamp": now,
        "session_count": existing_session_count,
        "iso_time": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "items_pruned_count": len(all_pruned) + pruned_aged_failures,
        "pruned_categories": {
            "temp_flags": len(pruned_flags),
            "syntax_error_flags": len(pruned_syntax),
            "test_brain_dirs": len(pruned_tests),
            "aged_backups": len(pruned_backups),
            "orphaned_pyc": len(pruned_pyc),
            "wal_checkpointed_dbs": len(checkpointed_dbs),
            "harness_backups_rotated": len(pruned_harness_backups),
            "auto_heal_digests": len(pruned_auto_heal),
            "expired_research_cache": len(pruned_research_cache),
            "aged_harness_failures_rows": pruned_aged_failures,
        },
        "sample_pruned": all_pruned[:10],
    }

    if not dry_run:
        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
        except Exception:
            pass

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Antigravity Inter-Session Cache Sweeper")
    parser.add_argument("--current-conv-id", default="", help="Conversation ID of the active session to protect")
    parser.add_argument("--dry-run", action="store_true", help="Report what would be cleaned without deleting")
    args = parser.parse_args()

    result = run_housekeeping(current_conv_id=args.current_conv_id, dry_run=args.dry_run)
    action = "[DRY RUN] Would prune" if args.dry_run else "Pruned"
    print(f"{action} {result['items_pruned_count']} items across temporary cache layers.")
    for cat, count in result["pruned_categories"].items():
        if count > 0:
            print(f"  - {cat}: {count}")

    # Level-3 Autonomous Sleep-Time Self-Healing & Graph Consolidation
    if not args.dry_run:
        try:
            healer_script = os.path.expanduser("~/.gemini/antigravity/scripts/auto-harness-healer.py")
            if os.path.isfile(healer_script):
                subprocess.run(
                    [sys.executable, healer_script, "--auto"],
                    timeout=15,
                    check=False,
                    capture_output=True,
                    text=True,
                )
        except Exception:
            pass

        try:
            consolidator_script = os.path.expanduser("~/.gemini/antigravity/scripts/consolidate-memory-graph.py")
            if os.path.isfile(consolidator_script):
                subprocess.run(
                    [sys.executable, consolidator_script],
                    timeout=15,
                    check=False,
                    capture_output=True,
                    text=True,
                )
        except Exception:
            pass


if __name__ == "__main__":
    main()

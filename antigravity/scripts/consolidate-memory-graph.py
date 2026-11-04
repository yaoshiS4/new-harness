#!/usr/bin/env python3
"""Antigravity Async Background Graph Consolidation Sweeper.

Folds harness failures and orchestration events from registry.sqlite into
project graph.sqlite databases as causal / episodic edges, and prunes
orphaned entities older than 7 days.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from typing import Any, Generator


@contextmanager
def open_db(path: Path | str, timeout: float = 5.0) -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(path, timeout=timeout)
    try:
        with conn:
            yield conn
    finally:
        conn.close()

# Add codex_knowledge to sys.path if not present
knowledge_src = Path.home() / ".gemini/antigravity/mcp_servers/codex_knowledge/src"
if not knowledge_src.exists():
    fallback_src = Path(__file__).resolve().parent.parent / "mcp_servers/codex_knowledge/src"
    if fallback_src.exists():
        knowledge_src = fallback_src
if knowledge_src.exists() and str(knowledge_src) not in sys.path:
    sys.path.insert(0, str(knowledge_src))

try:
    from codex_knowledge.graph_layer import GraphLayer
except ImportError:
    GraphLayer = None


def get_registry_db_path() -> str:
    env_override = os.getenv("ANTIGRAVITY_TEST_REGISTRY_DB")
    if env_override:
        return env_override
    return os.path.expanduser("~/.local/share/codex/projects/registry.sqlite")


def get_project_graph_root(slug: str) -> Path:
    env_override = os.getenv("ANTIGRAVITY_TEST_GRAPH_DIR")
    if env_override:
        return Path(env_override)
    return Path(os.path.expanduser(f"~/.local/share/codex/projects/{slug}/graph"))


def consolidate_project_graph(
    slug: str,
    graph_root: Path,
    failures: list[dict[str, Any]],
    events: list[dict[str, Any]],
    dry_run: bool = False,
) -> dict[str, int]:
    stats = {"edges_folded": 0, "orphans_pruned": 0}
    if not graph_root.exists() and not dry_run:
        graph_root.mkdir(parents=True, exist_ok=True)

    db_path = graph_root / "graph.sqlite"
    if not db_path.exists() and not (failures or events):
        return stats

    if GraphLayer is not None:
        graph = GraphLayer(graph_root)
    else:
        graph = None

    if not dry_run and graph is not None:
        # 1. Fold harness failures
        for f in failures:
            failure_type = f.get("failure_type") or "unknown_failure"
            tool_name = f.get("tool_name")
            conv_id = f.get("conv_id") or ""
            resolved_at = f.get("resolved_at")

            graph.upsert_edge(
                f"project:{slug}",
                "EXPERIENCED_FAILURE",
                f"failure:{failure_type}",
                payload={
                    "severity_tier": f.get("severity_tier", ""),
                    "reason": (f.get("reason") or "")[:200],
                    "created_at": f.get("created_at", ""),
                },
                layer="causal",
                causal_conv_id=conv_id,
            )
            stats["edges_folded"] += 1

            if tool_name:
                graph.upsert_edge(
                    f"tool:{tool_name}",
                    "TRIGGERED",
                    f"failure:{failure_type}",
                    payload={"conv_id": conv_id},
                    layer="causal",
                    causal_conv_id=conv_id,
                )
                stats["edges_folded"] += 1

            if resolved_at:
                actor = f"session:{conv_id[:8]}" if conv_id else "system"
                graph.upsert_edge(
                    actor,
                    "RESOLVED_BY",
                    f"failure:{failure_type}",
                    payload={"resolved_at": resolved_at},
                    layer="causal",
                    causal_conv_id=conv_id,
                )
                stats["edges_folded"] += 1

        # 2. Fold orchestration events
        for ev in events:
            cat = ev.get("category") or "general"
            summary = (ev.get("summary") or "")[:200]
            severity = ev.get("severity") or "minor"
            graph.upsert_edge(
                f"project:{slug}",
                "EXPERIENCED_FAILURE",
                f"event:{cat}",
                payload={"severity": severity, "summary": summary, "created_at": ev.get("created_at", "")},
                layer="causal",
            )
            stats["edges_folded"] += 1

        # 3. Prune orphaned entities older than 7 days
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        try:
            with open_db(db_path, timeout=5.0) as conn:
                # Find orphaned entities
                orphan_rows = conn.execute(
                    """
                    SELECT id FROM entities
                    WHERE id NOT IN (SELECT src FROM edges UNION SELECT dst FROM edges)
                      AND updated_at < ?
                    """,
                    (seven_days_ago,),
                ).fetchall()
                if orphan_rows:
                    orphan_ids = [r[0] for r in orphan_rows]
                    placeholders = ",".join("?" for _ in orphan_ids)
                    conn.execute(f"DELETE FROM entities WHERE id IN ({placeholders})", orphan_ids)
                    try:
                        conn.execute(f"DELETE FROM entities_fts WHERE id IN ({placeholders})", orphan_ids)
                    except Exception:
                        pass
                    stats["orphans_pruned"] = len(orphan_ids)
        except Exception:
            pass
    elif dry_run:
        stats["edges_folded"] = len(failures) * 2 + len(events)
        if db_path.exists():
            try:
                seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
                with open_db(db_path, timeout=5.0) as conn:
                    c = conn.execute(
                        """
                        SELECT COUNT(*) FROM entities
                        WHERE id NOT IN (SELECT src FROM edges UNION SELECT dst FROM edges)
                          AND updated_at < ?
                        """,
                        (seven_days_ago,),
                    ).fetchone()
                    stats["orphans_pruned"] = c[0] if c else 0
            except Exception:
                pass

    return stats


def run_consolidation(dry_run: bool = False) -> dict[str, Any]:
    registry_path = get_registry_db_path()
    if not os.path.isfile(registry_path):
        return {"status": "SKIPPED", "reason": "registry_sqlite_not_found", "registry_path": registry_path}

    failures_by_slug: dict[str, list[dict[str, Any]]] = {}
    events_by_slug: dict[str, list[dict[str, Any]]] = {}

    try:
        with open_db(registry_path, timeout=5.0) as conn:
            conn.row_factory = sqlite3.Row
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

            if "harness_failures" in tables:
                rows = conn.execute(
                    """
                    SELECT id, conv_id, slug, failure_type, tool_name, severity_tier, reason, created_at, resolved_at
                    FROM harness_failures
                    ORDER BY id DESC
                    LIMIT 200
                    """
                ).fetchall()
                for r in rows:
                    sl = r["slug"] or "default"
                    failures_by_slug.setdefault(sl, []).append(dict(r))

            if "orchestration_events" in tables:
                rows = conn.execute(
                    """
                    SELECT id, slug, category, severity, summary, created_at
                    FROM orchestration_events
                    ORDER BY id DESC
                    LIMIT 200
                    """
                ).fetchall()
                for r in rows:
                    sl = r["slug"] or "default"
                    events_by_slug.setdefault(sl, []).append(dict(r))
    except Exception as exc:
        return {"status": "ERROR", "error": str(exc), "registry_path": registry_path}

    all_slugs = set(failures_by_slug.keys()).union(set(events_by_slug.keys()))
    if not all_slugs:
        # Also check existing project graph dirs to prune orphans
        base_dir = os.path.expanduser("~/.local/share/codex/projects")
        if os.path.isdir(base_dir):
            for d in os.listdir(base_dir):
                if os.path.isdir(os.path.join(base_dir, d, "graph")):
                    all_slugs.add(d)

    total_edges = 0
    total_orphans = 0
    project_stats = {}

    for slug in all_slugs:
        graph_root = get_project_graph_root(slug)
        res = consolidate_project_graph(
            slug=slug,
            graph_root=graph_root,
            failures=failures_by_slug.get(slug, []),
            events=events_by_slug.get(slug, []),
            dry_run=dry_run,
        )
        total_edges += res["edges_folded"]
        total_orphans += res["orphans_pruned"]
        project_stats[slug] = res

    return {
        "status": "OK" if not dry_run else "DRY_RUN",
        "projects_processed": len(all_slugs),
        "total_edges_folded": total_edges,
        "total_orphans_pruned": total_orphans,
        "details": project_stats,
    }


def run_self_test() -> None:
    temp_dir = Path(tempfile.mkdtemp(prefix="test_consolidate_"))
    try:
        reg_db = temp_dir / "registry.sqlite"
        proj_dir = temp_dir / "projects" / "test-slug" / "graph"
        proj_dir.mkdir(parents=True, exist_ok=True)

        os.environ["ANTIGRAVITY_TEST_REGISTRY_DB"] = str(reg_db)
        os.environ["ANTIGRAVITY_TEST_GRAPH_DIR"] = str(proj_dir)

        # 1. Create registry tables
        with open_db(reg_db) as conn:
            conn.execute(
                """
                CREATE TABLE harness_failures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id TEXT,
                    slug TEXT,
                    failure_type TEXT,
                    tool_name TEXT,
                    severity_tier TEXT,
                    reason TEXT,
                    created_at TEXT,
                    resolved_at TEXT
                )
                """
            )
            conn.execute(
                """
                INSERT INTO harness_failures (conv_id, slug, failure_type, tool_name, severity_tier, reason, created_at, resolved_at)
                VALUES ('conv1234', 'test-slug', 'rate_limit', 'search_web', 'high', 'Exceeded QPS quota', '2026-10-20T10:00:00Z', '2026-10-20T10:05:00Z')
                """
            )
            conn.execute(
                """
                CREATE TABLE orchestration_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT,
                    category TEXT,
                    severity TEXT,
                    summary TEXT,
                    created_at TEXT
                )
                """
            )
            conn.execute(
                """
                INSERT INTO orchestration_events (slug, category, severity, summary, created_at)
                VALUES ('test-slug', 'context_drift', 'major', 'Goal deviated from PRD', '2026-10-20T11:00:00Z')
                """
            )

        # 2. Seed an old orphaned entity and a connected entity in graph.sqlite
        gl = GraphLayer(proj_dir)
        old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        with open_db(proj_dir / "graph.sqlite") as conn:
            conn.execute(
                """
                INSERT INTO entities (id, entity_type, layer, summary, confidence, entrenchment, valid_from, updated_at)
                VALUES ('orphan:aged', 'concept', 'semantic', 'stale orphan', 1.0, 1.0, ?, ?)
                """,
                (old_time, old_time),
            )
            conn.execute(
                """
                INSERT INTO entities (id, entity_type, layer, summary, confidence, entrenchment, valid_from, updated_at)
                VALUES ('orphan:fresh', 'concept', 'semantic', 'fresh orphan', 1.0, 1.0, ?, ?)
                """,
                (datetime.now(timezone.utc).isoformat(), datetime.now(timezone.utc).isoformat()),
            )

        # 3. Run consolidation
        res = run_consolidation(dry_run=False)
        assert res["status"] == "OK"
        assert res["total_edges_folded"] >= 3, f"Expected >= 3 edges folded, got {res['total_edges_folded']}"
        assert res["total_orphans_pruned"] == 1, f"Expected 1 orphan pruned, got {res['total_orphans_pruned']}"

        # 4. Verify in graph.sqlite
        with open_db(proj_dir / "graph.sqlite") as conn:
            conn.row_factory = sqlite3.Row
            edges = conn.execute("SELECT src, rel, dst, layer FROM edges").fetchall()
            edge_map = {(e["src"], e["rel"], e["dst"]): e["layer"] for e in edges}
            assert ("project:test-slug", "EXPERIENCED_FAILURE", "failure:rate_limit") in edge_map
            assert edge_map[("project:test-slug", "EXPERIENCED_FAILURE", "failure:rate_limit")] == "causal"
            assert ("tool:search_web", "TRIGGERED", "failure:rate_limit") in edge_map
            assert ("session:conv1234", "RESOLVED_BY", "failure:rate_limit") in edge_map
            assert ("project:test-slug", "EXPERIENCED_FAILURE", "event:context_drift") in edge_map

            remaining_entities = {r[0] for r in conn.execute("SELECT id FROM entities").fetchall()}
            assert "orphan:aged" not in remaining_entities, "Aged orphan should have been pruned"
            assert "orphan:fresh" in remaining_entities, "Fresh orphan should have been retained"

        print("PASS: consolidate-memory-graph self-test")
    finally:
        os.environ.pop("ANTIGRAVITY_TEST_REGISTRY_DB", None)
        os.environ.pop("ANTIGRAVITY_TEST_GRAPH_DIR", None)
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Antigravity Async Background Graph Consolidation Sweeper")
    parser.add_argument("--dry-run", action="store_true", help="Report without mutating databases")
    parser.add_argument("--self-test", action="store_true", help="Run comprehensive self-tests and exit")
    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        sys.exit(0)

    result = run_consolidation(dry_run=args.dry_run)
    action = "[DRY RUN] Would fold" if args.dry_run else "Folded"
    print(f"{action} {result.get('total_edges_folded', 0)} edges, pruned {result.get('total_orphans_pruned', 0)} orphaned entities across {result.get('projects_processed', 0)} projects.")


if __name__ == "__main__":
    main()

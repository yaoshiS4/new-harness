from __future__ import annotations

import os
import sqlite3
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from codegraph.parsers import parse_file

DEFAULT_DB_PATH = Path(os.environ.get("CODEGRAPH_DB_PATH", str(Path.home() / ".local/share/codex/codegraph_index.sqlite")))

CODE_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".rs",
    ".go",
    ".java",
    ".kt",
    ".kts",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
}

SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
    "target",
}

_connection_cache: dict[str, sqlite3.Connection] = {}
_last_sync_timestamp: dict[str, float] = {}
_cached_workspace_roots: dict[str, Path] = {}


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    key = str(db_path.resolve())
    if key in _connection_cache:
        try:
            _connection_cache[key].execute("SELECT 1")
            return _connection_cache[key]
        except Exception:
            pass

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -64000;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    _init_db(conn)
    _connection_cache[key] = conn
    return conn


def _init_db(conn: sqlite3.Connection) -> None:
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                workspace TEXT NOT NULL,
                rel_path TEXT NOT NULL,
                mtime_ns INTEGER NOT NULL,
                size INTEGER NOT NULL,
                indexed_at REAL NOT NULL,
                PRIMARY KEY (workspace, rel_path)
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace TEXT NOT NULL,
                path TEXT NOT NULL,
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                signature TEXT,
                exported INTEGER NOT NULL DEFAULT 0
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_ws_path ON symbols(workspace, path);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_ws_name ON symbols(workspace, name);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_ws_kind ON symbols(workspace, kind);")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace TEXT NOT NULL,
                src_path TEXT NOT NULL,
                src_symbol TEXT,
                rel TEXT NOT NULL,
                dst_target TEXT NOT NULL,
                line INTEGER NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_ws_src ON edges(workspace, src_path);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_ws_dst ON edges(workspace, dst_target);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_ws_sym ON edges(workspace, src_symbol);")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS file_metrics (
                path TEXT PRIMARY KEY,
                mtime_ns INTEGER NOT NULL,
                size INTEGER NOT NULL,
                language TEXT NOT NULL,
                line_count INTEGER NOT NULL,
                symbol_count INTEGER NOT NULL,
                class_count INTEGER NOT NULL,
                function_count INTEGER NOT NULL,
                heading_count INTEGER NOT NULL,
                parse_backend TEXT NOT NULL,
                cached_at REAL NOT NULL
            );
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_file_metrics_path ON file_metrics(path);")


def resolve_workspace_root(target: Path) -> Path:
    target_str = str(target.resolve())
    if target_str in _cached_workspace_roots:
        return _cached_workspace_roots[target_str]

    cur = target.resolve() if target.is_dir() else target.parent.resolve()
    for p in [cur, *cur.parents]:
        if (p / ".git").exists() or (p / "package.json").exists() or (p / "pyproject.toml").exists() or (p / "uv.lock").exists():
            _cached_workspace_roots[target_str] = p
            return p
    _cached_workspace_roots[target_str] = cur
    return cur


def _scan_directory(root: Path) -> dict[str, tuple[int, int]]:
    result: dict[str, tuple[int, int]] = {}
    root_str = str(root)
    root_len = len(root_str) + 1

    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    name = entry.name
                    if name in SKIP_DIRS:
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        ext = os.path.splitext(name)[1].lower()
                        if ext in CODE_SUFFIXES:
                            try:
                                st = entry.stat()
                                rel_path = entry.path[root_len:]
                                result[rel_path] = (st.st_mtime_ns, st.st_size)
                            except OSError:
                                pass
        except OSError:
            pass
    return result


def ensure_indexed(
    workspace_root: Path,
    force: bool = False,
    db_path: Path = DEFAULT_DB_PATH,
    ttl_seconds: float = 3.0,
) -> dict[str, int]:
    ws_str = str(workspace_root.resolve())
    now = time.time()
    if not force and (now - _last_sync_timestamp.get(ws_str, 0.0)) < ttl_seconds:
        return {"added": 0, "updated": 0, "deleted": 0, "scanned": 0}

    conn = get_connection(db_path)
    disk_files = _scan_directory(workspace_root)

    # Fetch known files from database
    cursor = conn.cursor()
    cursor.execute("SELECT rel_path, mtime_ns, size FROM files WHERE workspace = ?", (ws_str,))
    db_files = {row["rel_path"]: (row["mtime_ns"], row["size"]) for row in cursor.fetchall()}

    to_add_or_update: list[str] = []
    for rel_path, stat in disk_files.items():
        known = db_files.get(rel_path)
        if known is None or known != stat:
            to_add_or_update.append(rel_path)

    to_delete = [rel_path for rel_path in db_files if rel_path not in disk_files]

    if not to_add_or_update and not to_delete:
        _last_sync_timestamp[ws_str] = now
        return {"added": 0, "updated": 0, "deleted": 0, "scanned": len(disk_files)}

    # Apply incremental updates
    with conn:
        if to_delete:
            cursor.executemany(
                "DELETE FROM files WHERE workspace = ? AND rel_path = ?",
                [(ws_str, p) for p in to_delete],
            )
            cursor.executemany(
                "DELETE FROM symbols WHERE workspace = ? AND path = ?",
                [(ws_str, p) for p in to_delete],
            )
            cursor.executemany(
                "DELETE FROM edges WHERE workspace = ? AND src_path = ?",
                [(ws_str, p) for p in to_delete],
            )

        if to_add_or_update:
            # Delete old symbols and edges for updated files
            cursor.executemany(
                "DELETE FROM symbols WHERE workspace = ? AND path = ?",
                [(ws_str, p) for p in to_add_or_update if p in db_files],
            )
            cursor.executemany(
                "DELETE FROM edges WHERE workspace = ? AND src_path = ?",
                [(ws_str, p) for p in to_add_or_update if p in db_files],
            )

            files_insert = []
            symbols_insert = []
            edges_insert = []

            for rel_path in to_add_or_update:
                abs_path = workspace_root / rel_path
                mtime_ns, size = disk_files[rel_path]
                files_insert.append((ws_str, rel_path, mtime_ns, size, now))

                syms, edgs = parse_file(abs_path, ws_str, rel_path)
                for s in syms:
                    symbols_insert.append((
                        ws_str,
                        s["path"],
                        s["name"],
                        s["kind"],
                        s["line"],
                        s["end_line"],
                        s.get("signature"),
                        s.get("exported", 0),
                    ))
                for e in edgs:
                    # e: (ws_str, src_path, src_symbol, rel, dst_target, line)
                    edges_insert.append(e)

            cursor.executemany(
                """
                INSERT OR REPLACE INTO files (workspace, rel_path, mtime_ns, size, indexed_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                files_insert,
            )
            if symbols_insert:
                cursor.executemany(
                    """
                    INSERT INTO symbols (workspace, path, name, kind, line, end_line, signature, exported)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    symbols_insert,
                )
            if edges_insert:
                cursor.executemany(
                    """
                    INSERT INTO edges (workspace, src_path, src_symbol, rel, dst_target, line)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    edges_insert,
                )

    _last_sync_timestamp[ws_str] = time.time()
    return {
        "added": len([p for p in to_add_or_update if p not in db_files]),
        "updated": len([p for p in to_add_or_update if p in db_files]),
        "deleted": len(to_delete),
        "scanned": len(disk_files),
    }

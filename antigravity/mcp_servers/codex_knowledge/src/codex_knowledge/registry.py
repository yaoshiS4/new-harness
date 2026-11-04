from __future__ import annotations

from contextlib import contextmanager
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

from .settings import SETTINGS


@dataclass
class ProjectPaths:
    slug: str
    data_root: Path
    vault_root: Path
    project_root: Path | None = None


class Registry:
    def __init__(self) -> None:
        SETTINGS.data_root.mkdir(parents=True, exist_ok=True)
        self.db_path = SETTINGS.data_root / "registry.sqlite"
        self._init_db()

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    slug TEXT PRIMARY KEY,
                    project_path TEXT NOT NULL,
                    vault_path TEXT NOT NULL,
                    data_path TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT NOT NULL,
                    name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS handoffs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT NOT NULL,
                    name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    slug TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    file_mtime INTEGER NOT NULL DEFAULT 0,
                    indexed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (slug, relative_path)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orchestration_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    source_ref TEXT DEFAULT '',
                    settings_review_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    event_count INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TEXT,
                    rubric_scores_json TEXT DEFAULT '{}',
                    resolution_note TEXT DEFAULT '',
                    priority_score REAL DEFAULT 0.0
                )
                """
            )
            for col_def in (
                "rubric_scores_json TEXT DEFAULT '{}'",
                "resolution_note TEXT DEFAULT ''",
                "priority_score REAL DEFAULT 0.0",
            ):
                try:
                    conn.execute(f"ALTER TABLE settings_reviews ADD COLUMN {col_def}")
                except sqlite3.OperationalError:
                    pass
            # SQLite FTS5 for memory
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                    key,
                    value,
                    content='memory',
                    content_rowid='id',
                    tokenize='unicode61'
                )
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS memory_fts_ai AFTER INSERT ON memory BEGIN
                    INSERT INTO memory_fts(rowid, key, value) VALUES (new.id, new.key, new.value);
                END
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS memory_fts_ad AFTER DELETE ON memory BEGIN
                    INSERT INTO memory_fts(memory_fts, rowid, key, value) VALUES ('delete', old.id, old.key, old.value);
                END
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS memory_fts_au AFTER UPDATE ON memory BEGIN
                    INSERT INTO memory_fts(memory_fts, rowid, key, value) VALUES ('delete', old.id, old.key, old.value);
                    INSERT INTO memory_fts(rowid, key, value) VALUES (new.id, new.key, new.value);
                END
                """
            )
            # SQLite FTS5 for vault documents
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    slug UNINDEXED,
                    relative_path UNINDEXED,
                    category UNINDEXED,
                    title,
                    content,
                    tokenize='unicode61'
                )
                """
            )
            try:
                mem_cnt = conn.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
                fts_cnt = conn.execute("SELECT COUNT(*) FROM memory_fts").fetchone()[0]
                if mem_cnt > fts_cnt:
                    conn.execute("INSERT OR IGNORE INTO memory_fts(rowid, key, value) SELECT id, key, value FROM memory")
            except Exception:
                pass

    @staticmethod
    def slug_from_path(project_path: str) -> str:
        base = Path(project_path).name.strip().lower()
        slug = "".join(ch if ch.isalnum() or ch == "-" else "-" for ch in base)
        slug = "-".join(filter(None, slug.split("-")))
        return slug or "project"

    def resolve(self, slug: str) -> ProjectPaths | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT slug, data_path, vault_path, project_path FROM projects WHERE slug = ?", (slug,)
            ).fetchone()
        if not row:
            return None
        project_root = Path(row["project_path"]) if row["project_path"] else None
        return ProjectPaths(row["slug"], Path(row["data_path"]), Path(row["vault_path"]), project_root)

    def ensure_project(self, project_path: str, slug: str | None = None) -> ProjectPaths:
        path = str(Path(project_path).resolve())
        use_slug = slug or self.slug_from_path(path)
        data = SETTINGS.data_root / use_slug
        vault = SETTINGS.vault_root / use_slug
        data.mkdir(parents=True, exist_ok=True)
        vault.mkdir(parents=True, exist_ok=True)

        for rel in [
            "raw/docs",
            "raw/code",
            "sot",
            "sot/adrs",
            "plans",
            "plans/epics",
            "plans/stories",
            "plans/tasks",
            "wiki/entities",
            "wiki/concepts",
            "wiki/sources",
            "wiki/synthesis",
            ".wiki",
        ]:
            (vault / rel).mkdir(parents=True, exist_ok=True)

        files = {
            "index.md": "# Index\n",
            "log.md": "# Log\n",
            ".wiki/SCHEMA.md": "# Wiki Schema\n",
        }
        for rel, content in files.items():
            p = vault / rel
            if not p.exists():
                p.write_text(content, encoding="utf-8")

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO projects (slug, project_path, vault_path, data_path)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(slug) DO UPDATE SET
                  project_path=excluded.project_path,
                  vault_path=excluded.vault_path,
                  data_path=excluded.data_path
                """,
                (use_slug, path, str(vault), str(data)),
            )
        return ProjectPaths(use_slug, data, vault, Path(path))


REGISTRY = Registry()

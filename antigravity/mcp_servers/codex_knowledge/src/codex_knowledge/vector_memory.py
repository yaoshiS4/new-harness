from __future__ import annotations

from contextlib import contextmanager
import json
import math
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any, Generator


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"\w+", text.lower())
    tokens = list(words)
    # Include character 3-grams for subword matching
    for w in words:
        if len(w) >= 4:
            for i in range(len(w) - 2):
                tokens.append(w[i : i + 3])
    return tokens


def _compute_vector(tokens: list[str]) -> tuple[dict[str, float], float]:
    counts = Counter(tokens)
    vec = {k: 1.0 + math.log(v) for k, v in counts.items()}
    norm = math.sqrt(sum(v * v for v in vec.values()))
    return vec, norm


def _cosine_similarity(
    v1: dict[str, float], n1: float, v2: dict[str, float], n2: float
) -> float:
    if n1 == 0.0 or n2 == 0.0:
        return 0.0
    if len(v1) > len(v2):
        v1, v2 = v2, v1
    dot = sum(val * v2.get(k, 0.0) for k, val in v1.items())
    return dot / (n1 * n2)


class VectorMemory:
    """
    Zero-overhead lightweight vector and BM25 memory layer.
    Pure-Python token cosine similarity and SQLite-backed storage (<1ms latency).
    """

    def __init__(self, persist_dir: Path) -> None:
        self.persist_dir = persist_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.persist_dir / "vector.sqlite"
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
                CREATE TABLE IF NOT EXISTS items (
                    collection TEXT NOT NULL,
                    id TEXT NOT NULL,
                    document TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (collection, id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_items_collection ON items(collection)"
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
                    collection UNINDEXED,
                    id UNINDEXED,
                    document,
                    tokenize='unicode61'
                )
                """
            )

    def add(
        self,
        item_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
        collection: str = "memories",
    ) -> bool:
        meta_json = json.dumps(metadata or {}, ensure_ascii=False)
        try:
            with self._conn() as conn:
                conn.execute(
                    """
                    INSERT INTO items (collection, id, document, metadata, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(collection, id) DO UPDATE SET
                        document = excluded.document,
                        metadata = excluded.metadata,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (collection, item_id, text, meta_json),
                )
                try:
                    conn.execute(
                        "DELETE FROM items_fts WHERE collection = ? AND id = ?",
                        (collection, item_id),
                    )
                except Exception:
                    pass
                try:
                    conn.execute(
                        "INSERT INTO items_fts (collection, id, document) VALUES (?, ?, ?)",
                        (collection, item_id, text),
                    )
                except Exception:
                    pass
            return True
        except Exception:
            return False

    def query(
        self,
        text: str,
        limit: int = 10,
        collection: str = "memories",
    ) -> list[dict[str, Any]]:
        if not text.strip():
            return []

        q_tokens = _tokenize(text)
        if not q_tokens:
            return []
        q_vec, q_norm = _compute_vector(q_tokens)

        # 1. Candidate selection: try FTS5 BM25 match if possible, or fetch all items in collection
        words = re.findall(r"\w+", text.lower())
        candidates: dict[str, dict[str, Any]] = {}

        with self._conn() as conn:
            if words:
                safe_match = " OR ".join(f'"{w}"' for w in words)
                try:
                    fts_rows = conn.execute(
                        """
                        SELECT id, document, bm25(items_fts) AS bm25_rank
                        FROM items_fts
                        WHERE collection = ? AND items_fts MATCH ?
                        ORDER BY bm25_rank ASC
                        LIMIT ?
                        """,
                        (collection, safe_match, max(50, limit * 4)),
                    ).fetchall()
                    if fts_rows:
                        id_list = [r["id"] for r in fts_rows]
                        placeholders = ",".join("?" for _ in id_list)
                        item_rows = conn.execute(
                            f"SELECT id, document, metadata FROM items WHERE collection = ? AND id IN ({placeholders})",
                            [collection] + id_list,
                        ).fetchall()
                        for ir in item_rows:
                            candidates[ir["id"]] = {
                                "id": ir["id"],
                                "document": ir["document"],
                                "metadata": json.loads(ir["metadata"]) if ir["metadata"] else {},
                            }
                except Exception:
                    candidates = {}

            # If candidates are fewer than needed, retrieve all items in this collection
            if len(candidates) < limit:
                all_rows = conn.execute(
                    "SELECT id, document, metadata FROM items WHERE collection = ? LIMIT 1000",
                    (collection,),
                ).fetchall()
                for ar in all_rows:
                    if ar["id"] not in candidates:
                        candidates[ar["id"]] = {
                            "id": ar["id"],
                            "document": ar["document"],
                            "metadata": json.loads(ar["metadata"]) if ar["metadata"] else {},
                        }

        if not candidates:
            return []

        # 2. Token Cosine Similarity Scoring
        scored: list[dict[str, Any]] = []
        for item in candidates.values():
            doc_tokens = _tokenize(item["document"])
            d_vec, d_norm = _compute_vector(doc_tokens)
            cos_sim = _cosine_similarity(q_vec, q_norm, d_vec, d_norm)
            if cos_sim > 0.0:
                dist = round(max(0.0, 1.0 - cos_sim), 4)
                sim = round(cos_sim, 4)
                scored.append(
                    {
                        "id": item["id"],
                        "document": item["document"],
                        "metadata": item["metadata"],
                        "distance": dist,
                        "similarity": sim,
                    }
                )

        # Sort descending by similarity, ascending by distance
        scored.sort(key=lambda x: -x["similarity"])
        return scored[:limit]

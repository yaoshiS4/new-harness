from __future__ import annotations

from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sqlite3
from typing import Any, Generator

MAGMA_REL_LAYERS: dict[str, str] = {
    # Semantic: factual / structural relationships
    "IMPLEMENTS": "semantic",
    "PROVIDES": "semantic",
    "DEPENDS_ON": "semantic",
    "DERIVED_FROM": "semantic",
    "PART_OF": "semantic",
    "SIMILAR_TO": "semantic",
    "EXTENDS": "semantic",
    "APPLIES_TO": "semantic",
    "HAS_MEMORY": "semantic",
    "NAVIGATES_TO": "semantic",
    "USES": "semantic",
    "HAS_MODULE": "semantic",
    "HAS_SERVICE": "semantic",
    "CONNECTS_TO": "semantic",
    # Temporal: sequencing and lifecycle
    "PRECEDES": "temporal",
    "SUCCEEDS": "temporal",
    "SUPERSEDES": "temporal",
    "FOLLOWED_BY": "temporal",
    # Causal: failures, fixes, dependencies, contradictions
    "CAUSES": "causal",
    "CAUSED_BY": "causal",
    "RESOLVED_BY": "causal",
    "MITIGATED_BY": "causal",
    "BROKEN_BY": "causal",
    "CONTRADICTS": "causal",
    "FAILED_AT": "causal",
    "TRIGGERED": "causal",
    "EXPERIENCED_FAILURE": "causal",
    # Episodic: session actions, tool runs, mutations
    "MODIFIED_IN": "episodic",
    "VERIFIED_BY": "episodic",
    "CALLED_TOOL": "episodic",
    "SOURCE": "episodic",
    "OBSERVED_IN": "episodic",
}

VALID_LAYERS = {"semantic", "temporal", "causal", "episodic"}


def _infer_edge_layer(rel: str, explicit_layer: str = "") -> str:
    if explicit_layer and explicit_layer.lower() in VALID_LAYERS:
        return explicit_layer.lower()
    return MAGMA_REL_LAYERS.get(rel.upper(), "semantic")


def _classify_query_intent(query_str: str) -> dict[str, float]:
    q = (query_str or "").lower()
    if any(k in q for k in ("fix", "bug", "error", "fail", "broken", "why", "crash", "loop")):
        return {"causal": 1.8, "episodic": 1.4, "temporal": 1.1, "semantic": 0.8}
    if any(k in q for k in ("when", "history", "timeline", "previous", "superseded", "changed")):
        return {"temporal": 1.8, "episodic": 1.5, "causal": 1.1, "semantic": 0.8}
    return {"semantic": 1.5, "causal": 1.2, "temporal": 1.0, "episodic": 0.9}


class GraphLayer:
    """
    Local bi-temporal graph layer with SQLite-first storage,
    MAGMA 4-layer taxonomy, Kumiho AGM belief revision,
    and Personalized PageRank (PPR) spreading activation.
    """

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.sqlite_path = self.root / "graph.sqlite"
        self._init_sqlite()

    @contextmanager
    def _sql(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.sqlite_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_sqlite(self) -> None:
        with self._sql() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    src TEXT NOT NULL,
                    rel TEXT NOT NULL,
                    dst TEXT NOT NULL,
                    payload TEXT,
                    valid_from TEXT,
                    valid_to TEXT,
                    recorded_at TEXT,
                    is_current INTEGER NOT NULL DEFAULT 1,
                    layer TEXT NOT NULL DEFAULT 'semantic',
                    weight REAL NOT NULL DEFAULT 1.0,
                    invalidated_at TEXT,
                    superseded_by INTEGER,
                    causal_conv_id TEXT DEFAULT ''
                )
                """
            )
            # Safe ALTER TABLE migration for existing graph.sqlite files
            cols = {row["name"] for row in conn.execute("PRAGMA table_info(edges)").fetchall()}
            if "valid_from" not in cols:
                conn.execute("ALTER TABLE edges ADD COLUMN valid_from TEXT")
            if "valid_to" not in cols:
                conn.execute("ALTER TABLE edges ADD COLUMN valid_to TEXT")
                if "valid_until" in cols:
                    conn.execute("UPDATE edges SET valid_to = valid_until WHERE valid_until IS NOT NULL")
            if "recorded_at" not in cols:
                conn.execute("ALTER TABLE edges ADD COLUMN recorded_at TEXT")
            if "is_current" not in cols:
                conn.execute("ALTER TABLE edges ADD COLUMN is_current INTEGER NOT NULL DEFAULT 1")
                conn.execute(
                    """
                    UPDATE edges
                    SET is_current = CASE
                        WHEN valid_to IS NOT NULL AND valid_to != '' THEN 0
                        ELSE 1
                    END
                    """
                )
            if "layer" not in cols:
                conn.execute("ALTER TABLE edges ADD COLUMN layer TEXT NOT NULL DEFAULT 'semantic'")
            if "weight" not in cols:
                conn.execute("ALTER TABLE edges ADD COLUMN weight REAL NOT NULL DEFAULT 1.0")
            if "invalidated_at" not in cols:
                conn.execute("ALTER TABLE edges ADD COLUMN invalidated_at TEXT")
            if "superseded_by" not in cols:
                conn.execute("ALTER TABLE edges ADD COLUMN superseded_by INTEGER")
            if "causal_conv_id" not in cols:
                conn.execute("ALTER TABLE edges ADD COLUMN causal_conv_id TEXT DEFAULT ''")

            now_iso = datetime.now(timezone.utc).isoformat()
            conn.execute("UPDATE edges SET valid_from = ? WHERE valid_from IS NULL OR valid_from = ''", (now_iso,))
            conn.execute("UPDATE edges SET recorded_at = ? WHERE recorded_at IS NULL OR recorded_at = ''", (now_iso,))
            conn.execute("UPDATE edges SET is_current = 1 WHERE is_current IS NULL")
            conn.execute("UPDATE edges SET layer = 'semantic' WHERE layer IS NULL OR layer = ''")
            conn.execute("UPDATE edges SET weight = 1.0 WHERE weight IS NULL")

            # Entities table (Kumiho AGM + Bi-Temporal)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL DEFAULT 'concept',
                    layer TEXT NOT NULL DEFAULT 'semantic',
                    summary TEXT DEFAULT '',
                    confidence REAL NOT NULL DEFAULT 1.0,
                    entrenchment REAL NOT NULL DEFAULT 1.0,
                    valid_from TEXT NOT NULL,
                    invalidated_at TEXT,
                    causal_conv_id TEXT DEFAULT '',
                    updated_at TEXT NOT NULL
                )
                """
            )
            try:
                conn.execute(
                    "CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(id, summary, tokenize='unicode61')"
                )
            except Exception:
                pass

            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_src_rel_current ON edges(src, rel, is_current)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_src_current ON edges(src, is_current)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_dst_current ON edges(dst, is_current)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_edges_layer ON edges(layer)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)")

    @staticmethod
    def _compute_entrenchment(confidence: float, in_degree: int) -> float:
        return float(confidence) + 0.25 * math.log(1.0 + max(0, in_degree))

    def _upsert_entity_conn(
        self,
        conn: sqlite3.Connection,
        entity_id: str,
        entity_type: str = "concept",
        layer: str = "semantic",
        summary: str = "",
        confidence: float = 1.0,
        causal_conv_id: str = "",
    ) -> dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        in_degree_row = conn.execute(
            "SELECT COUNT(*) FROM edges WHERE dst = ? AND is_current = 1", (entity_id,)
        ).fetchone()
        in_degree = in_degree_row[0] if in_degree_row else 0
        entrenchment = round(self._compute_entrenchment(confidence, in_degree), 4)

        existing = conn.execute("SELECT id, valid_from, summary FROM entities WHERE id = ?", (entity_id,)).fetchone()
        if existing:
            v_from = existing["valid_from"] or now_iso
            new_summary = summary or existing["summary"] or ""
            conn.execute(
                """
                UPDATE entities
                SET entity_type = ?, layer = ?, summary = ?, confidence = ?, entrenchment = ?, causal_conv_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (entity_type, layer, new_summary, confidence, entrenchment, causal_conv_id, now_iso, entity_id),
            )
        else:
            v_from = now_iso
            new_summary = summary or ""
            conn.execute(
                """
                INSERT INTO entities (id, entity_type, layer, summary, confidence, entrenchment, valid_from, causal_conv_id, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (entity_id, entity_type, layer, new_summary, confidence, entrenchment, v_from, causal_conv_id, now_iso),
            )

        try:
            conn.execute("DELETE FROM entities_fts WHERE id = ?", (entity_id,))
        except Exception:
            pass
        try:
            conn.execute("INSERT INTO entities_fts (id, summary) VALUES (?, ?)", (entity_id, new_summary))
        except Exception:
            pass

        return {
            "id": entity_id,
            "entity_type": entity_type,
            "layer": layer,
            "summary": new_summary,
            "confidence": confidence,
            "entrenchment": entrenchment,
            "updated_at": now_iso,
        }

    def upsert_entity(
        self,
        entity_id: str,
        entity_type: str = "concept",
        layer: str = "semantic",
        summary: str = "",
        confidence: float = 1.0,
        causal_conv_id: str = "",
    ) -> dict[str, Any]:
        with self._sql() as conn:
            return self._upsert_entity_conn(
                conn,
                entity_id=entity_id,
                entity_type=entity_type,
                layer=layer,
                summary=summary,
                confidence=confidence,
                causal_conv_id=causal_conv_id,
            )

    def upsert_edge(
        self,
        src: str,
        rel: str,
        dst: str,
        payload: dict[str, Any] | str | None = None,
        layer: str = "",
        weight: float = 1.0,
        causal_conv_id: str = "",
    ) -> dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        resolved_layer = _infer_edge_layer(rel, layer)
        if isinstance(payload, dict):
            payload_str = json.dumps(payload, ensure_ascii=False)
        elif payload is None:
            payload_str = ""
        else:
            payload_str = str(payload)

        with self._sql() as conn:
            # Auto-upsert entities for src and dst inside the same connection
            self._upsert_entity_conn(conn, src, layer=resolved_layer, causal_conv_id=causal_conv_id)
            self._upsert_entity_conn(conn, dst, layer=resolved_layer, causal_conv_id=causal_conv_id)

            active_edge = conn.execute(
                """
                SELECT id, src, rel, dst, payload, valid_from, recorded_at, layer, weight
                FROM edges
                WHERE src = ? AND rel = ? AND is_current = 1
                ORDER BY id DESC LIMIT 1
                """,
                (src, rel),
            ).fetchone()

            if active_edge is not None:
                existing_payload = active_edge["payload"] or ""
                if active_edge["dst"] == dst and existing_payload == payload_str:
                    conn.execute(
                        "UPDATE edges SET recorded_at = ?, layer = ?, weight = ? WHERE id = ?",
                        (now_iso, resolved_layer, weight, active_edge["id"]),
                    )
                    return {
                        "status": "unchanged",
                        "id": active_edge["id"],
                        "layer": resolved_layer,
                        "action": "updated_recorded_at",
                        "edge_id": active_edge["id"],
                        "old_edge_id": None,
                        "valid_from": active_edge["valid_from"] or now_iso,
                        "is_current": 1,
                    }
                else:
                    # AGM Levi Belief Revision
                    old_edge_id = active_edge["id"]
                    old_dst = active_edge["dst"]

                    # 1. Insert new edge FIRST
                    cur = conn.execute(
                        """
                        INSERT INTO edges (src, rel, dst, payload, valid_from, recorded_at, is_current, layer, weight, causal_conv_id)
                        VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                        """,
                        (src, rel, dst, payload_str, now_iso, now_iso, resolved_layer, weight, causal_conv_id),
                    )
                    new_edge_id = cur.lastrowid

                    # 2. Update old edge
                    conn.execute(
                        """
                        UPDATE edges
                        SET valid_to = ?, invalidated_at = ?, is_current = 0, superseded_by = ?
                        WHERE id = ?
                        """,
                        (now_iso, now_iso, new_edge_id, old_edge_id),
                    )

                    # 3. RippleEngine Pass: find active dependent edges where dst is src
                    dep_rows = conn.execute(
                        """
                        SELECT id, payload
                        FROM edges
                        WHERE dst = ? AND rel IN ('DEPENDS_ON', 'DERIVED_FROM', 'IMPLEMENTS') AND is_current = 1
                        """,
                        (src,),
                    ).fetchall()

                    for d_row in dep_rows:
                        d_id = d_row["id"]
                        raw_d_payload = d_row["payload"] or ""
                        try:
                            d_dict = json.loads(raw_d_payload) if raw_d_payload else {}
                            if not isinstance(d_dict, dict):
                                d_dict = {"raw": d_dict}
                        except Exception:
                            d_dict = {"raw": raw_d_payload}

                        d_dict["stale_dependency"] = True
                        d_dict["stale_since"] = now_iso
                        d_dict["superseded_edge_id"] = new_edge_id
                        conn.execute(
                            "UPDATE edges SET payload = ? WHERE id = ?",
                            (json.dumps(d_dict, ensure_ascii=False), d_id),
                        )

                    # Recompute entrenchment for src, dst, old_dst
                    self._upsert_entity_conn(conn, src, layer=resolved_layer, causal_conv_id=causal_conv_id)
                    self._upsert_entity_conn(conn, dst, layer=resolved_layer, causal_conv_id=causal_conv_id)
                    if old_dst != dst and old_dst != src:
                        self._upsert_entity_conn(conn, old_dst, layer="semantic")

                    return {
                        "status": "superseded",
                        "id": new_edge_id,
                        "superseded_id": old_edge_id,
                        "layer": resolved_layer,
                        "action": "invalidated_and_inserted",
                        "edge_id": new_edge_id,
                        "old_edge_id": old_edge_id,
                        "valid_from": now_iso,
                        "is_current": 1,
                    }
            else:
                cur = conn.execute(
                    """
                    INSERT INTO edges (src, rel, dst, payload, valid_from, recorded_at, is_current, layer, weight, causal_conv_id)
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                    """,
                    (src, rel, dst, payload_str, now_iso, now_iso, resolved_layer, weight, causal_conv_id),
                )
                new_edge_id = cur.lastrowid
                self._upsert_entity_conn(conn, src, layer=resolved_layer, causal_conv_id=causal_conv_id)
                self._upsert_entity_conn(conn, dst, layer=resolved_layer, causal_conv_id=causal_conv_id)

                return {
                    "status": "inserted",
                    "id": new_edge_id,
                    "layer": resolved_layer,
                    "action": "inserted",
                    "edge_id": new_edge_id,
                    "old_edge_id": None,
                    "valid_from": now_iso,
                    "is_current": 1,
                }

    def upsert(
        self,
        src: str,
        rel: str,
        dst: str,
        payload: dict[str, Any] | str | None = None,
        layer: str = "",
        weight: float = 1.0,
        causal_conv_id: str = "",
    ) -> dict[str, Any]:
        return self.upsert_edge(
            src=src,
            rel=rel,
            dst=dst,
            payload=payload,
            layer=layer,
            weight=weight,
            causal_conv_id=causal_conv_id,
        )

    @staticmethod
    def _estimate_tokens(edge: dict[str, Any]) -> int:
        text = f"{edge['src']} {edge['rel']} {edge['dst']} {edge.get('payload') or ''}"
        return max(4, int(len(text) / 3.5) + 2)

    def _expand_and_rank_ppr(
        self,
        seed_entities: dict[str, float],
        term: str = "",
        limit: int = 50,
        include_historical: bool = False,
        max_tokens: int = 400,
    ) -> list[dict[str, Any]]:
        if not seed_entities:
            return []

        where_current = "" if include_historical else "AND is_current = 1"
        seeds = set(seed_entities.keys())
        intent_weights = _classify_query_intent(term)

        edge_cols = (
            "id, src, rel, dst, payload, valid_from, valid_to, recorded_at, is_current, "
            "layer, weight, invalidated_at, superseded_by, causal_conv_id"
        )

        with self._sql() as conn:
            # 1-Hop Expansion: find all edges directly incident to seeds
            placeholders = ",".join("?" for _ in seeds)
            sql_1hop = f"""
                SELECT {edge_cols}
                FROM edges
                WHERE (src IN ({placeholders}) OR dst IN ({placeholders}))
                {where_current}
            """
            params_1hop = list(seeds) + list(seeds)
            rows_1hop = conn.execute(sql_1hop, params_1hop).fetchall()

            edges_by_id: dict[int, dict[str, Any]] = {}
            nodes_hop1: set[str] = set(seeds)
            for r in rows_1hop:
                d = dict(r)
                edges_by_id[d["id"]] = d
                nodes_hop1.add(d["src"])
                nodes_hop1.add(d["dst"])

            # 2-Hop Expansion: find edges incident to nodes_hop1
            new_nodes_hop1 = nodes_hop1 - seeds
            if new_nodes_hop1:
                hop1_sample = list(new_nodes_hop1)[:100]
                placeholders_2 = ",".join("?" for _ in hop1_sample)
                sql_2hop = f"""
                    SELECT {edge_cols}
                    FROM edges
                    WHERE (src IN ({placeholders_2}) OR dst IN ({placeholders_2}))
                    {where_current}
                    LIMIT 200
                """
                params_2hop = list(hop1_sample) + list(hop1_sample)
                rows_2hop = conn.execute(sql_2hop, params_2hop).fetchall()
                for r in rows_2hop:
                    d = dict(r)
                    edges_by_id[d["id"]] = d

        all_edges = list(edges_by_id.values())
        if not all_edges:
            return []

        all_nodes: set[str] = set(seeds)
        for e in all_edges:
            all_nodes.add(e["src"])
            all_nodes.add(e["dst"])

        total_seed_weight = sum(seed_entities.values()) or 1.0
        p0 = {node: (seed_entities.get(node, 0.0) / total_seed_weight) for node in all_nodes}

        # Weighted Adjacency using MAGMA policy intent weights and edge weights
        adj: dict[str, list[tuple[str, float]]] = {node: [] for node in all_nodes}
        out_weight_sum: dict[str, float] = {node: 0.0 for node in all_nodes}

        for e in all_edges:
            u, v = e["src"], e["dst"]
            e_layer = e.get("layer") or "semantic"
            raw_w = float(e.get("weight") or 1.0)
            trans_w = max(0.05, raw_w) * intent_weights.get(e_layer, 1.0)
            adj[u].append((v, trans_w))
            adj[v].append((u, trans_w))
            out_weight_sum[u] += trans_w
            out_weight_sum[v] += trans_w

        # Personalized PageRank (PPR) Power Iteration with intent-weighted transitions
        alpha = 0.85
        p = dict(p0)
        for _ in range(25):
            p_next = {node: (1.0 - alpha) * p0[node] for node in all_nodes}
            for u, nbrs in adj.items():
                total_w = out_weight_sum[u]
                if total_w > 0:
                    for v, w in nbrs:
                        share = (alpha * p[u] * w) / total_w
                        p_next[v] += share
                else:
                    for node in all_nodes:
                        p_next[node] += alpha * p[u] * p0[node]
            diff = sum(abs(p_next[n] - p[n]) for n in all_nodes)
            p = p_next
            if diff < 1e-5:
                break

        # Score & Rank Triples
        scored_edges: list[dict[str, Any]] = []
        term_lower = term.lower().strip() if term else ""

        for e in all_edges:
            src, dst, rel = e["src"], e["dst"], e["rel"]
            payload = e.get("payload") or ""

            if src in seeds and dst in seeds:
                hop = 0
            elif src in seeds or dst in seeds:
                hop = 1
            else:
                hop = 2

            score = p.get(src, 0.0) + p.get(dst, 0.0)

            if term_lower:
                if (
                    term_lower in src.lower()
                    or term_lower in dst.lower()
                    or term_lower in rel.lower()
                    or term_lower in payload.lower()
                ):
                    score *= 1.5
                if term_lower == src.lower() or term_lower == dst.lower():
                    score *= 1.2

            item = dict(e)
            item["score"] = round(score, 5)
            item["hop"] = hop
            scored_edges.append(item)

        scored_edges.sort(key=lambda x: (-x["score"], x["hop"], -x["id"]))

        # Apply token budget constraint (max_tokens = 400)
        selected: list[dict[str, Any]] = []
        accumulated_tokens = 0
        for edge in scored_edges:
            toks = self._estimate_tokens(edge)
            if selected and (accumulated_tokens + toks > max_tokens):
                break
            if len(selected) >= limit:
                break
            selected.append(edge)
            accumulated_tokens += toks

        return selected

    def seeded_subgraph_tuples(
        self,
        seeds: list[str],
        intent_query: str = "",
        max_hops: int = 2,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        seed_entities = {s: 1.0 for s in seeds if s}
        if not seed_entities:
            return []
        edges = self._expand_and_rank_ppr(
            seed_entities=seed_entities,
            term=intent_query,
            limit=limit,
            include_historical=False,
            max_tokens=600,
        )
        for e in edges:
            layer = e.get("layer") or "semantic"
            e["linearized"] = f"({e['src']}) --[{e['rel']} {{{layer}}}]--> ({e['dst']})"
        return edges

    def find_path(
        self,
        src: str,
        dst: str,
        max_hops: int = 4,
        include_historical: bool = False,
    ) -> dict[str, Any]:
        if not src or not dst:
            return {"found": False, "hops": 0, "path": []}
        if src == dst:
            return {"found": True, "hops": 0, "path": []}

        where_current = "" if include_historical else "WHERE is_current = 1"
        edge_cols = (
            "id, src, rel, dst, payload, valid_from, valid_to, recorded_at, is_current, "
            "layer, weight, invalidated_at, superseded_by, causal_conv_id"
        )

        with self._sql() as conn:
            rows = conn.execute(f"SELECT {edge_cols} FROM edges {where_current}").fetchall()

        adj: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        for r in rows:
            d = dict(r)
            s, d_dst = d["src"], d["dst"]
            adj.setdefault(s, []).append((d_dst, d))
            adj.setdefault(d_dst, []).append((s, d))

        queue: deque[tuple[str, list[dict[str, Any]]]] = deque([(src, [])])
        visited: set[str] = {src}

        while queue:
            current, path = queue.popleft()
            if len(path) >= max_hops:
                continue

            for nxt, edge in adj.get(current, []):
                new_path = path + [edge]
                if nxt == dst:
                    return {
                        "found": True,
                        "hops": len(new_path),
                        "path": [
                            {
                                "id": e["id"],
                                "src": e["src"],
                                "rel": e["rel"],
                                "dst": e["dst"],
                                "layer": e.get("layer", "semantic"),
                                "weight": e.get("weight", 1.0),
                                "is_current": e.get("is_current", 1),
                                "invalidated_at": e.get("invalidated_at"),
                                "superseded_by": e.get("superseded_by"),
                                "causal_conv_id": e.get("causal_conv_id", ""),
                            }
                            for e in new_path
                        ],
                    }
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, new_path))

        return {"found": False, "hops": 0, "path": []}

    def query(
        self,
        term: str,
        limit: int = 50,
        include_historical: bool = False,
        max_tokens: int = 400,
    ) -> list[dict[str, Any]]:
        where_current = "" if include_historical else "AND is_current = 1"
        q = f"%{term}%"
        edge_cols = (
            "id, src, rel, dst, payload, valid_from, valid_to, recorded_at, is_current, "
            "layer, weight, invalidated_at, superseded_by, causal_conv_id"
        )
        with self._sql() as conn:
            matching_rows = conn.execute(
                f"""
                SELECT {edge_cols}
                FROM edges
                WHERE (src LIKE ? OR rel LIKE ? OR dst LIKE ? OR payload LIKE ?)
                {where_current}
                ORDER BY id DESC
                LIMIT ?
                """,
                (q, q, q, q, limit),
            ).fetchall()

        seed_entities: dict[str, float] = {}
        term_lower = term.lower().strip()
        for r in matching_rows:
            src, dst = r["src"], r["dst"]
            w_src = 3.0 if term_lower == src.lower() else (2.0 if term_lower in src.lower() else 1.0)
            w_dst = 3.0 if term_lower == dst.lower() else (2.0 if term_lower in dst.lower() else 1.0)
            seed_entities[src] = max(seed_entities.get(src, 0.0), w_src)
            seed_entities[dst] = max(seed_entities.get(dst, 0.0), w_dst)

        if not seed_entities and term.strip():
            seed_entities[term.strip()] = 1.0

        return self._expand_and_rank_ppr(
            seed_entities=seed_entities,
            term=term,
            limit=limit,
            include_historical=include_historical,
            max_tokens=max_tokens,
        )

    def neighbors(
        self,
        entity_id: str,
        limit: int = 10,
        include_historical: bool = False,
        max_tokens: int = 400,
    ) -> list[dict[str, Any]]:
        seed_entities = {entity_id: 1.0}
        return self._expand_and_rank_ppr(
            seed_entities=seed_entities,
            term="",
            limit=limit,
            include_historical=include_historical,
            max_tokens=max_tokens,
        )

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any
import warnings

warnings.filterwarnings(
    "ignore",
    message=".*Field 'lifespan' has an incomplete definition.*",
    category=UserWarning,
)

try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:  # pragma: no cover
    raise SystemExit(
        "Missing MCP runtime dependency. Install with: uv sync --project runtime/codex_knowledge"
    ) from exc

from .graph_layer import GraphLayer
from .registry import REGISTRY, ProjectPaths
from .vector_memory import VectorMemory
from .workflows import ENGINE

mcp = FastMCP("codex_knowledge")


def _project_layers(slug: str):
    pp = REGISTRY.resolve(slug)
    if not pp:
        return None, None, None
    vector = VectorMemory(pp.data_root / "vector")
    graph = GraphLayer(pp.data_root / "graph")
    return pp, vector, graph


def _resolve_doc_path(pp: ProjectPaths, rel: str) -> Path:
    if pp.project_root and (pp.project_root / rel).exists():
        return (pp.project_root / rel).resolve()
    return (pp.vault_root / rel).resolve()


def _document_category(relative_path: str) -> str:
    if (
        relative_path.startswith("sot/")
        or relative_path.startswith("docs/")
        or relative_path in {"AGENTS.md", "STATUS.md", "PRD.md", "plan.md", "README.md", "intent.md"}
    ):
        return "sot"
    if relative_path.startswith("plans/"):
        return "plans"
    if relative_path.startswith("wiki/"):
        return "wiki"
    if relative_path.startswith("raw/"):
        return "raw"
    if relative_path.startswith(".wiki/") or relative_path in {"index.md", "log.md"}:
        return "meta"
    return "other"


def _document_title(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith("#"):
                return line.lstrip("#").strip() or path.stem
    except Exception:
        pass
    return path.stem


def _get_sot_files(pp: ProjectPaths) -> list[tuple[Path, str]]:
    """Return list of (file_path, relative_path) for repository SOT and local docs."""
    files: list[tuple[Path, str]] = []
    seen_rel: set[str] = set()

    # 1. Repository SOT (primary source of truth)
    if pp.project_root and pp.project_root.exists():
        docs_dir = pp.project_root / "docs"
        if docs_dir.exists():
            for md in sorted(docs_dir.rglob("*.md")):
                rel = str(md.relative_to(pp.project_root))
                if rel not in seen_rel:
                    seen_rel.add(rel)
                    files.append((md, rel))
        for md in sorted(pp.project_root.glob("*.md")):
            rel = md.name
            if rel not in seen_rel:
                seen_rel.add(rel)
                files.append((md, rel))

    # 2. Vault root docs (supplementary/wiki/plans, omitting stale duplicated sot/ files)
    if pp.vault_root and pp.vault_root.exists():
        for md in sorted(pp.vault_root.rglob("*.md")):
            rel = str(md.relative_to(pp.vault_root))
            if pp.project_root and rel.startswith("sot/"):
                repo_stem = md.stem
                if any(f[0].stem == repo_stem for f in files):
                    continue
            if rel not in seen_rel:
                seen_rel.add(rel)
                files.append((md, rel))

    return files


def _refresh_document_inventory(slug: str) -> dict[str, Any]:
    pp = REGISTRY.resolve(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}

    sot_files = _get_sot_files(pp)
    rows: list[tuple[str, str, str, str, int]] = []
    fts_rows: list[tuple[str, str, str, str, str]] = []
    for md, rel in sot_files:
        title = _document_title(md)
        cat = _document_category(rel)
        mtime = int(md.stat().st_mtime)
        try:
            content = md.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            content = ""
        rows.append((slug, rel, cat, title, mtime))
        fts_rows.append((slug, rel, cat, title, content))

    with REGISTRY._conn() as conn:  # type: ignore[attr-defined]
        conn.execute("DELETE FROM documents WHERE slug = ?", (slug,))
        conn.executemany(
            """
            INSERT INTO documents (slug, relative_path, category, title, file_mtime)
            VALUES (?, ?, ?, ?, ?)
            """,
            rows,
        )
        try:
            conn.execute("DELETE FROM documents_fts WHERE slug = ?", (slug,))
            conn.executemany(
                """
                INSERT INTO documents_fts (slug, relative_path, category, title, content)
                VALUES (?, ?, ?, ?, ?)
                """,
                fts_rows,
            )
        except Exception:
            pass

    # Index into VectorMemory documents collection
    _, vector, _ = _project_layers(slug)
    if vector is not None:
        for rel, cat, title, content in [(r[1], r[2], r[3], r[4]) for r in fts_rows]:
            doc_id = hashlib.sha256(f"{slug}:{rel}".encode("utf-8")).hexdigest()[:24]
            vector.add(
                item_id=doc_id,
                text=content[:4000] if content else title,
                metadata={"slug": slug, "relative_path": rel, "title": title, "category": cat},
                collection="documents",
            )

    return {"slug": slug, "indexed": len(rows), "refreshed": True}


def _ensure_document_inventory(slug: str) -> dict[str, Any]:
    pp = REGISTRY.resolve(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}

    sot_files = _get_sot_files(pp)
    fs_count = len(sot_files)
    fs_latest = max((int(f[0].stat().st_mtime) for f in sot_files), default=0)

    with REGISTRY._conn() as conn:  # type: ignore[attr-defined]
        row = conn.execute(
            """
            SELECT COUNT(*) AS count, COALESCE(MAX(file_mtime), 0) AS latest
            FROM documents
            WHERE slug = ?
            """,
            (slug,),
        ).fetchone()
        try:
            fts_count = conn.execute("SELECT COUNT(*) FROM documents_fts WHERE slug = ?", (slug,)).fetchone()[0]
        except Exception:
            fts_count = -1

    indexed_count = int(row["count"]) if row else 0
    indexed_latest = int(row["latest"]) if row else 0
    if indexed_count != fs_count or indexed_latest != fs_latest or fts_count != indexed_count:
        return _refresh_document_inventory(slug)

    return {"slug": slug, "indexed": indexed_count, "refreshed": False}


def _settings_review_rows(slug: str, include_resolved: bool = False, limit: int = 10) -> list[dict[str, Any]]:
    query = """
        SELECT id, reason, event_count, created_at, resolved_at,
               COALESCE(rubric_scores_json, '{}') AS rubric_scores_json,
               COALESCE(resolution_note, '') AS resolution_note,
               COALESCE(priority_score, 0.0) AS priority_score
        FROM settings_reviews
        WHERE slug = ?
    """
    params: list[Any] = [slug]
    if not include_resolved:
        query += " AND resolved_at IS NULL"
    query += " ORDER BY priority_score DESC, id DESC LIMIT ?"
    params.append(limit)
    with REGISTRY._conn() as conn:  # type: ignore[attr-defined]
        rows = conn.execute(query, tuple(params)).fetchall()
    results: list[dict[str, Any]] = []
    for r in rows:
        item = dict(r)
        raw_rubric = item.pop("rubric_scores_json", "{}") or "{}"
        try:
            parsed_rubric = json.loads(raw_rubric) if isinstance(raw_rubric, str) else raw_rubric
        except Exception:
            parsed_rubric = {}
        item["rubric_scores"] = parsed_rubric if isinstance(parsed_rubric, dict) else {}
        item["resolution_note"] = str(item.get("resolution_note") or "")
        item["priority_score"] = round(float(item.get("priority_score") or 0.0), 4)
        results.append(item)
    return results


def _text_score(query_lower: str, *parts: str) -> float:
    text = " ".join(part for part in parts if part).lower()
    if not text:
        return 0.0
    if text == query_lower:
        return 3.0
    score = 0.0
    if query_lower in text:
        score += 1.5
    for word in query_lower.split():
        if word and word in text:
            score += 0.3
    return score


def _format_context_tier(text: str, tier: str = "L2") -> str:
    """Format document/context text according to OpenViking L0/L1/L2 disclosure tiers."""
    if not text:
        return ""
    norm_tier = (tier or "L2").strip().upper()
    if norm_tier == "L0":
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        headings = [ln for ln in lines if ln.startswith("#")][:3]
        body_lines = [ln for ln in lines if not ln.startswith("#")]
        first_sentence = ""
        if body_lines:
            first_line = body_lines[0]
            parts = re.split(r"(?<=[.!?])\s+", first_line, maxsplit=1)
            first_sentence = parts[0]
        pieces = headings + ([first_sentence] if first_sentence else [])
        summary = " | ".join(pieces) if pieces else text.strip()
        return summary[:240]
    if norm_tier == "L1":
        lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
        selected: list[str] = []
        sig_re = re.compile(r"^\s*(?:#+|-|\*|\+|\d+\.|def\s+|class\s+|function\s+|export\s+|interface\s+|type\s+)")
        for ln in lines:
            if sig_re.match(ln):
                selected.append(ln)
        if not selected:
            selected = lines
        overview = "\n".join(selected)
        return overview[:1200]
    return text


def _rerank_hits(
    query: str,
    wiki_hits: list[dict[str, Any]],
    keyword_hits: list[dict[str, Any]],
    semantic_hits: list[dict[str, Any]],
    graph_hits: list[dict[str, Any]],
    limit: int,
    tier: str = "L2",
) -> list[dict[str, Any]]:
    query_lower = query.lower()
    norm_tier = (tier or "L2").strip().upper()
    if norm_tier not in {"L0", "L1", "L2"}:
        norm_tier = "L2"
    scored: list[dict[str, Any]] = []

    for hit in wiki_hits:
        score = 2.0 + _text_score(
            query_lower,
            hit.get("relative_path", ""),
            hit.get("title", ""),
            hit.get("excerpt", ""),
        )
        scored.append(
            {
                "source": "wiki",
                "score": round(score, 3),
                "label": hit.get("title") or hit.get("name") or hit.get("relative_path", ""),
                "path": hit.get("relative_path") or hit.get("path", ""),
                "detail": _format_context_tier(hit.get("excerpt", ""), norm_tier),
                "context_tier": norm_tier,
            }
        )

    for hit in keyword_hits:
        score = 3.0 + _text_score(query_lower, hit.get("key", ""), hit.get("value", ""))
        raw_val = hit.get("value", "")
        detail_val = raw_val[:240] if norm_tier == "L2" else _format_context_tier(raw_val, norm_tier)
        scored.append(
            {
                "source": "memory_keyword",
                "score": round(score, 3),
                "label": hit.get("key", ""),
                "path": hit.get("key", ""),
                "detail": detail_val,
                "context_tier": norm_tier,
            }
        )

    for hit in semantic_hits:
        score = 1.5 + _text_score(
            query_lower,
            str(hit.get("metadata", {}).get("key", "")),
            hit.get("document", ""),
        )
        raw_doc = hit.get("document", "")
        detail_doc = raw_doc[:240] if norm_tier == "L2" else _format_context_tier(raw_doc, norm_tier)
        scored.append(
            {
                "source": "memory_semantic",
                "score": round(score, 3),
                "label": str(hit.get("metadata", {}).get("key", "")),
                "path": str(hit.get("id", "")),
                "detail": detail_doc,
                "context_tier": norm_tier,
            }
        )

    for hit in graph_hits:
        score = 2.2 + _text_score(
            query_lower,
            hit.get("src", ""),
            hit.get("rel", ""),
            hit.get("dst", ""),
            hit.get("payload", ""),
        )
        raw_payload = hit.get("payload", "")
        detail_payload = raw_payload[:240] if norm_tier == "L2" else _format_context_tier(raw_payload, norm_tier)
        scored.append(
            {
                "source": "graph",
                "score": round(score, 3),
                "label": f"{hit.get('src', '')} -[{hit.get('rel', '')}]-> {hit.get('dst', '')}",
                "path": hit.get("src", ""),
                "detail": detail_payload,
                "context_tier": norm_tier,
            }
        )

    scored.sort(key=lambda item: (-item["score"], item["source"], item["label"]))
    return scored[:limit]


@mcp.tool()
def project_register(project_path: str, slug: str | None = None) -> dict[str, Any]:
    pp = REGISTRY.ensure_project(project_path, slug)
    inventory = _ensure_document_inventory(pp.slug)
    return {
        "slug": pp.slug,
        "data_root": str(pp.data_root),
        "vault_root": str(pp.vault_root),
        "document_count": inventory.get("indexed", 0),
    }


@mcp.tool()
def project_resolve(slug: str) -> dict[str, Any]:
    pp = REGISTRY.resolve(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}
    return {"slug": pp.slug, "data_root": str(pp.data_root), "vault_root": str(pp.vault_root)}


@mcp.tool()
def project_index(slug: str = "", project: str = "") -> dict[str, Any]:
    slug = slug or project
    if not slug:
        return {"error": "slug_or_project_required"}
    pp = REGISTRY.resolve(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}

    inventory = _ensure_document_inventory(slug)
    with REGISTRY._conn() as conn:  # type: ignore[attr-defined]
        docs = conn.execute(
            """
            SELECT relative_path, category, title, file_mtime
            FROM documents
            WHERE slug = ?
            ORDER BY category, relative_path
            """,
            (slug,),
        ).fetchall()
        checkpoints = conn.execute(
            """
            SELECT name, created_at
            FROM checkpoints
            WHERE slug = ?
            ORDER BY id DESC
            LIMIT 5
            """,
            (slug,),
        ).fetchall()
        handoffs = conn.execute(
            """
            SELECT name, created_at
            FROM handoffs
            WHERE slug = ?
            ORDER BY id DESC
            LIMIT 5
            """,
            (slug,),
        ).fetchall()
        memory_keys = conn.execute(
            """
            SELECT key, MAX(created_at) AS created_at, MAX(id) AS latest_id
            FROM memory
            WHERE slug = ?
            GROUP BY key
            ORDER BY latest_id DESC
            LIMIT 10
            """,
            (slug,),
        ).fetchall()

    key_docs: dict[str, list[dict[str, Any]]] = {
        "sot": [],
        "plans": [],
        "wiki": [],
        "raw": [],
        "meta": [],
        "other": [],
    }
    for row in docs:
        category = row["category"]
        if category not in key_docs:
            category = "other"
        if len(key_docs[category]) >= 6:
            continue
        key_docs[category].append(
            {
                "relative_path": row["relative_path"],
                "title": row["title"],
                "path": str(_resolve_doc_path(pp, row["relative_path"])),
            }
        )

    return {
        "slug": slug,
        "project": {
            "slug": pp.slug,
            "data_root": str(pp.data_root),
            "vault_root": str(pp.vault_root),
            "project_root": str(pp.project_root) if pp.project_root else None,
        },
        "index_stats": {
            "document_count": inventory.get("indexed", 0),
            "refreshed": inventory.get("refreshed", False),
        },
        "key_docs": key_docs,
        "recent_checkpoints": [dict(r) for r in checkpoints],
        "recent_handoffs": [dict(r) for r in handoffs],
        "recent_memory_keys": [dict(r) for r in memory_keys],
        "settings_reviews": _settings_review_rows(slug, include_resolved=False, limit=5),
    }


@mcp.tool()
def project_context(
    slug: str = "",
    query: str = "",
    limit: int = 3,
    project: str = "",
    tier: str = "L2",
) -> dict[str, Any]:
    """Return a compact layered context bundle from wiki, memory, and graph stores."""
    slug = slug or project
    if not slug:
        return {"error": "slug_or_project_required"}
    norm_tier = (tier or "L2").strip().upper()
    if norm_tier not in {"L0", "L1", "L2"}:
        norm_tier = "L2"

    index = project_index(slug)
    if index.get("error"):
        return index

    pp = REGISTRY.resolve(slug)
    wiki = vault_search(slug, query, limit=limit)
    memory = memory_query(slug, query, limit=limit)
    graph = graph_query(slug, query, limit=limit)

    raw_wiki_hits = wiki.get("hits", [])[:limit]
    tiered_wiki_hits: list[dict[str, Any]] = []
    for w_hit in raw_wiki_hits:
        item = dict(w_hit)
        rel_p = item.get("relative_path", "")
        full_doc = ""
        if pp and rel_p:
            try:
                doc_p = _resolve_doc_path(pp, rel_p)
                if doc_p.is_file():
                    full_doc = doc_p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                full_doc = ""
        source_text = full_doc or item.get("excerpt", "")
        if norm_tier in ("L0", "L1"):
            item["excerpt"] = _format_context_tier(source_text, norm_tier)
        elif full_doc:
            item["excerpt"] = _format_context_tier(full_doc, "L2")
        item["context_tier"] = norm_tier
        tiered_wiki_hits.append(item)

    kw_hits: list[dict[str, Any]] = []
    for k_hit in memory.get("keyword_results", [])[:limit]:
        k_item = dict(k_hit)
        if norm_tier in ("L0", "L1"):
            k_item["value"] = _format_context_tier(k_item.get("value", ""), norm_tier)
        k_item["context_tier"] = norm_tier
        kw_hits.append(k_item)

    sem_hits: list[dict[str, Any]] = []
    for s_hit in memory.get("semantic_results", [])[:limit]:
        s_item = dict(s_hit)
        if norm_tier in ("L0", "L1"):
            s_item["document"] = _format_context_tier(s_item.get("document", ""), norm_tier)
        s_item["context_tier"] = norm_tier
        sem_hits.append(s_item)

    g_hits: list[dict[str, Any]] = []
    for g_hit in graph.get("results", [])[:limit]:
        g_item = dict(g_hit)
        if norm_tier in ("L0", "L1"):
            g_item["payload"] = _format_context_tier(g_item.get("payload", ""), norm_tier)
        g_item["context_tier"] = norm_tier
        g_hits.append(g_item)

    top_hits = _rerank_hits(
        query,
        tiered_wiki_hits,
        kw_hits,
        sem_hits,
        g_hits,
        limit=limit,
        tier=norm_tier,
    )

    return {
        "slug": slug,
        "project": index["project"],
        "query": query,
        "context_tier": norm_tier,
        "index_summary": {
            "document_count": index["index_stats"]["document_count"],
            "recent_memory_keys": index.get("recent_memory_keys", [])[:limit],
            "settings_reviews": index.get("settings_reviews", [])[:limit],
        },
        "top_hits": top_hits,
        "wiki_hits": tiered_wiki_hits,
        "memory_keyword_hits": kw_hits,
        "memory_semantic_hits": sem_hits,
        "graph_hits": g_hits,
    }


def _reciprocal_rank_fusion(
    fts_items: list[dict[str, Any]],
    vec_items: list[dict[str, Any]],
    id_fn: Any,
    k: int = 60,
) -> list[dict[str, Any]]:
    """
    Reciprocal Rank Fusion (RRF) combining lexical BM25 and vector semantic ranks:
    score = 1 / (k + rank_fts) + 1 / (k + rank_vec)
    """
    rank_fts_map: dict[str, int] = {}
    item_map: dict[str, dict[str, Any]] = {}

    for i, item in enumerate(fts_items):
        item_id = id_fn(item)
        if not item_id:
            continue
        rank_fts_map[item_id] = i + 1
        item_map[item_id] = dict(item)

    rank_vec_map: dict[str, int] = {}
    for j, item in enumerate(vec_items):
        item_id = id_fn(item)
        if not item_id:
            continue
        rank_vec_map[item_id] = j + 1
        if item_id not in item_map:
            item_map[item_id] = dict(item)

    fused: list[dict[str, Any]] = []
    for item_id, item_data in item_map.items():
        r_fts = rank_fts_map.get(item_id)
        r_vec = rank_vec_map.get(item_id)
        score = 0.0
        if r_fts is not None:
            score += 1.0 / (k + r_fts)
        if r_vec is not None:
            score += 1.0 / (k + r_vec)

        merged = dict(item_data)
        merged["score"] = round(score, 6)
        merged["rank_fts"] = r_fts
        merged["rank_vec"] = r_vec
        fused.append(merged)

    fused.sort(key=lambda x: -x["score"])
    return fused


@mcp.tool()
def vault_search(slug: str, query: str, limit: int = 20) -> dict[str, Any]:
    pp, vector, _graph = _project_layers(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}

    _ensure_document_inventory(slug)

    # 1. SQLite FTS5 BM25 search with safe tokenization
    fts_items: list[dict[str, Any]] = []
    tokens = [f'"{w}"' for w in query.replace('"', ' ').replace("'", " ").split() if w]
    safe_match = " ".join(tokens) if tokens else f'"{query}"'

    with REGISTRY._conn() as conn:  # type: ignore[attr-defined]
        try:
            rows = conn.execute(
                """
                SELECT relative_path, category, title,
                       snippet(documents_fts, 4, '[', ']', '...', 15) AS excerpt,
                       bm25(documents_fts) AS bm25_rank
                FROM documents_fts
                WHERE slug = ? AND documents_fts MATCH ?
                ORDER BY bm25_rank ASC
                LIMIT ?
                """,
                (slug, safe_match, limit * 2),
            ).fetchall()
            for r in rows:
                rel = r["relative_path"]
                fts_items.append(
                    {
                        "relative_path": rel,
                        "path": str(_resolve_doc_path(pp, rel)),
                        "name": Path(rel).name,
                        "title": r["title"],
                        "category": r["category"],
                        "excerpt": r["excerpt"] or "",
                        "bm25_rank": round(float(r["bm25_rank"]), 4),
                    }
                )
        except Exception:
            fts_items = []

        # Fallback to LIKE if FTS5 had 0 hits or syntax error
        if not fts_items:
            query_like = f"%{query.lower()}%"
            rows = conn.execute(
                """
                SELECT relative_path, category, title
                FROM documents
                WHERE slug = ?
                  AND (
                    LOWER(relative_path) LIKE ?
                    OR LOWER(title) LIKE ?
                    OR LOWER(category) LIKE ?
                  )
                ORDER BY category, relative_path
                LIMIT ?
                """,
                (slug, query_like, query_like, query_like, limit * 2),
            ).fetchall()
            for r in rows:
                rel = r["relative_path"]
                fts_items.append(
                    {
                        "relative_path": rel,
                        "path": str(_resolve_doc_path(pp, rel)),
                        "name": Path(rel).name,
                        "title": r["title"],
                        "category": r["category"],
                        "excerpt": "",
                        "bm25_rank": 0.0,
                    }
                )

    # Last-resort markdown file scan if database returned no results
    if not fts_items:
        query_lower = query.lower()
        for md, rel in _get_sot_files(pp):
            try:
                text = md.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            idx = text.lower().find(query_lower)
            if idx < 0:
                continue
            excerpt = text[max(0, idx - 80) : idx + len(query) + 120].replace("\n", " ").strip()
            fts_items.append(
                {
                    "relative_path": rel,
                    "path": str(md.resolve()),
                    "name": md.name,
                    "title": _document_title(md),
                    "category": _document_category(rel),
                    "excerpt": excerpt,
                    "bm25_rank": 0.0,
                }
            )

    # 2. Vector Similarity Search on documents collection
    vec_items: list[dict[str, Any]] = []
    if vector is not None:
        raw_vec = vector.query(query, limit=limit * 2, collection="documents")
        for v in raw_vec:
            meta = v.get("metadata", {})
            rel = meta.get("relative_path", "")
            if not rel:
                continue
            vec_items.append(
                {
                    "relative_path": rel,
                    "path": str(_resolve_doc_path(pp, rel)),
                    "name": Path(rel).name,
                    "title": meta.get("title", ""),
                    "category": meta.get("category", ""),
                    "excerpt": v.get("document", "")[:240],
                    "vector_similarity": v.get("similarity", 1.0),
                }
            )

    # 3. Reciprocal Rank Fusion (RRF)
    fused_hits = _reciprocal_rank_fusion(
        fts_items=fts_items,
        vec_items=vec_items,
        id_fn=lambda x: x.get("relative_path", ""),
        k=60,
    )

    return {
        "slug": slug,
        "query": query,
        "count": len(fused_hits),
        "search_mode": "hybrid_rrf",
        "hits": fused_hits[:limit],
    }


@mcp.tool()
def vault_read(slug: str, relative_path: str) -> dict[str, Any]:
    pp = REGISTRY.resolve(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}

    fp: Path | None = None
    # 1. Check repository SOT first
    if pp.project_root and pp.project_root.exists():
        proj_root = pp.project_root.resolve()
        cand = (pp.project_root / relative_path).resolve()
        if cand.is_relative_to(proj_root) and cand.is_file():
            fp = cand
        elif relative_path.startswith("sot/"):
            stripped = relative_path[4:]
            cand_docs = (pp.project_root / "docs" / stripped).resolve()
            cand_root = (pp.project_root / stripped).resolve()
            if cand_docs.is_relative_to(proj_root) and cand_docs.is_file():
                fp = cand_docs
            elif cand_root.is_relative_to(proj_root) and cand_root.is_file():
                fp = cand_root
        elif not relative_path.startswith("docs/"):
            cand_docs = (pp.project_root / "docs" / relative_path).resolve()
            if cand_docs.is_relative_to(proj_root) and cand_docs.is_file():
                fp = cand_docs

    # 2. Check vault_root fallback
    if fp is None and pp.vault_root and pp.vault_root.exists():
        vault_root = pp.vault_root.resolve()
        cand_vault = (pp.vault_root / relative_path).resolve()
        if cand_vault.is_relative_to(vault_root) and cand_vault.is_file():
            fp = cand_vault

    if fp is None or not fp.exists():
        return {"error": "not_found", "path": relative_path}
    return {"path": str(fp), "content": fp.read_text(encoding="utf-8", errors="ignore")}


@mcp.tool()
def vault_write(slug: str, relative_path: str, content: str) -> dict[str, Any]:
    pp = REGISTRY.resolve(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}

    fp: Path | None = None
    if pp.project_root and pp.project_root.exists():
        proj_root = pp.project_root.resolve()
        if (
            relative_path.startswith("docs/")
            or relative_path in {"AGENTS.md", "README.md", "STATUS.md", "PRD.md", "plan.md", "intent.md"}
        ):
            cand = (pp.project_root / relative_path).resolve()
            if not cand.is_relative_to(proj_root):
                return {"error": "invalid_path"}
            fp = cand
        elif relative_path.startswith("sot/"):
            stripped = relative_path[4:]
            if (pp.project_root / "docs").exists():
                cand = (pp.project_root / "docs" / stripped).resolve()
            else:
                cand = (pp.project_root / stripped).resolve()
            if not cand.is_relative_to(proj_root):
                return {"error": "invalid_path"}
            fp = cand

    if fp is None:
        if not pp.vault_root:
            return {"error": "invalid_path"}
        vault_root = pp.vault_root.resolve()
        cand = (pp.vault_root / relative_path).resolve()
        if not cand.is_relative_to(vault_root):
            return {"error": "invalid_path"}
        fp = cand

    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")
    inventory = _refresh_document_inventory(slug)
    return {
        "path": str(fp),
        "bytes": len(content.encode("utf-8")),
        "document_count": inventory.get("indexed", 0),
    }


def _wiki_ingest_raw(slug: str, source_path: str) -> dict[str, Any]:
    pp = REGISTRY.resolve(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}
    src = Path(source_path)
    if not src.exists() or not src.is_file():
        return {"error": "invalid_source", "source_path": source_path}

    if pp.project_root and pp.project_root.exists():
        target_dir = pp.project_root / "docs" / "wiki"
        target_dir.mkdir(parents=True, exist_ok=True)
        dst = target_dir / src.name
        dst.write_text(src.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
        log_file = pp.project_root / "docs" / "log.md"
        old_log = log_file.read_text(encoding="utf-8") if log_file.exists() else "# Log\n"
        log_file.write_text(old_log + f"\n- ingest: {src.name}\n", encoding="utf-8")
    else:
        dst = pp.vault_root / "raw" / "docs" / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
        log_file = pp.vault_root / "log.md"
        old_log = log_file.read_text(encoding="utf-8") if log_file.exists() else "# Log\n"
        log_file.write_text(old_log + f"\n- ingest: {src.name}\n", encoding="utf-8")

    return {"slug": slug, "source": str(src), "target": str(dst)}


def _wiki_rebuild_raw(slug: str) -> dict[str, Any]:
    pp = REGISTRY.resolve(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}
    sot_files = _get_sot_files(pp)
    lines = ["# Index", ""]
    for _, rel in sorted(sot_files, key=lambda x: x[1]):
        if Path(rel).name not in {"index.md", "log.md"}:
            lines.append(f"- {rel}")
    index_path = (pp.project_root / "docs" / "index.md") if (pp.project_root and pp.project_root.exists()) else (pp.vault_root / "index.md")
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"slug": slug, "indexed": len(lines) - 2}


@mcp.tool()
def wiki_ingest(slug: str, source_path: str) -> dict[str, Any]:
    """Ingest docs and run wiki rebuild in LangGraph-backed workflow path."""
    result = ENGINE.run_wiki_ingest(slug, source_path, _wiki_ingest_raw, _wiki_rebuild_raw)
    result["inventory"] = _refresh_document_inventory(slug)
    return result


@mcp.tool()
def wiki_rebuild(slug: str) -> dict[str, Any]:
    result = _wiki_rebuild_raw(slug)
    result["inventory"] = _refresh_document_inventory(slug)
    return result


@mcp.tool()
def memory_store(
    slug: str = "",
    key: str = "",
    value: str = "",
    project: str = "",
    content: str = "",
    title: str = "",
) -> dict[str, Any]:
    slug = slug or project
    key = key or title
    value = value or content
    if not slug:
        return {"error": "slug_or_project_required"}
    if not key:
        return {"error": "key_or_title_required"}
    pp, vector, _graph = _project_layers(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}

    with REGISTRY._conn() as conn:  # type: ignore[attr-defined]
        conn.execute("INSERT INTO memory (slug, key, value) VALUES (?, ?, ?)", (slug, key, value))

    item_id = hashlib.sha256(f"{slug}:{key}:{value}".encode("utf-8")).hexdigest()[:24]
    vector_ok = vector.add(item_id=item_id, text=value, metadata={"key": key, "slug": slug})

    if _graph is not None:
        try:
            _graph.upsert_entity(f"mem:{key}", entity_type="memory", layer="semantic", summary=value[:200])
        except Exception:
            pass

        # Search for existing related memories (A-MEM Zettelkasten Auto-Linking)
        matches: list[dict[str, Any]] = []
        try:
            if hasattr(vector, "search"):
                matches = vector.search("memory", value, top_k=4) or []
            else:
                matches = vector.query(value, limit=4, collection="memories") or []
        except Exception:
            matches = []

        for m in matches:
            m_meta = m.get("metadata") or {}
            cand_key = m_meta.get("key") or m.get("id")
            if not cand_key or cand_key == key or m.get("id") == item_id:
                continue

            score = m.get("score") if "score" in m else m.get("similarity", 0.0)
            try:
                score_f = float(score)
            except (ValueError, TypeError):
                score_f = 0.0

            if score_f >= 0.25:
                n_key = cand_key
                try:
                    _graph.upsert_edge(
                        f"mem:{key}",
                        "EXTENDS",
                        f"mem:{n_key}",
                        payload={"similarity": round(score_f, 3)},
                        layer="semantic",
                    )
                except Exception:
                    pass

                # Retrospective Evolution: update neighbor's metadata in vector memory
                linked_from = list(m_meta.get("linked_from") or [])
                if key not in linked_from:
                    linked_from.append(key)
                    m_meta["linked_from"] = linked_from[-10:]
                    doc_text = m.get("document") or m.get("text") or ""
                    try:
                        vector.add(item_id=m["id"], text=doc_text, metadata=m_meta, collection="memories")
                    except Exception:
                        pass

        # Link file references mentioned in value
        seen_fnames: set[str] = set()
        file_matches = re.findall(r"\b[\w\-]+\.(?:py|ts|tsx|js|rs|go|sh|md|json)\b", value)
        for fname in file_matches:
            if fname not in seen_fnames:
                seen_fnames.add(fname)
                try:
                    _graph.upsert_edge(f"mem:{key}", "APPLIES_TO", f"file:{fname}", layer="semantic")
                except Exception:
                    pass
                if len(seen_fnames) >= 5:
                    break

    return {"slug": slug, "key": key, "stored": True, "vector_indexed": vector_ok}


@mcp.tool()
def knowledge_capture(
    slug: str,
    key: str,
    value: str,
    entity_id: str = "",
    source_ref: str = "",
) -> dict[str, Any]:
    """Persist a lesson into memory and mirror a compact graph link for retrieval."""
    memory_result = memory_store(slug, key, value)
    if memory_result.get("error"):
        return memory_result

    target = entity_id or f"memory:{key}"
    graph_results = [
        graph_upsert(slug, f"project:{slug}", "HAS_MEMORY", target, key),
    ]
    if source_ref:
        graph_results.append(graph_upsert(slug, target, "SOURCE", source_ref, key))

    return {
        "slug": slug,
        "key": key,
        "stored": True,
        "vector_indexed": memory_result.get("vector_indexed", False),
        "graph_links": graph_results,
    }


@mcp.tool()
def orchestration_lesson(
    slug: str,
    category: str,
    summary: str,
    severity: str = "minor",
    source_ref: str = "",
) -> dict[str, Any]:
    if not REGISTRY.resolve(slug):
        return {"error": "project_not_found", "slug": slug}
    if severity not in {"minor", "major", "critical"}:
        return {"error": "invalid_severity", "severity": severity}

    with REGISTRY._conn() as conn:  # type: ignore[attr-defined]
        cursor = conn.execute(
            """
            INSERT INTO orchestration_events (slug, category, severity, summary, source_ref)
            VALUES (?, ?, ?, ?, ?)
            """,
            (slug, category, severity, summary, source_ref),
        )
        event_id = int(cursor.lastrowid)
        counts = conn.execute(
            """
            SELECT
              SUM(CASE WHEN severity = 'critical' AND settings_review_id IS NULL THEN 1 ELSE 0 END) AS critical_open,
              SUM(CASE WHEN severity != 'critical' AND settings_review_id IS NULL THEN 1 ELSE 0 END) AS noncritical_open
            FROM orchestration_events
            WHERE slug = ?
            """,
            (slug,),
        ).fetchone()

        critical_open = int(counts["critical_open"] or 0)
        noncritical_open = int(counts["noncritical_open"] or 0)
        settings_review_required = critical_open >= 1 or noncritical_open >= 3
        settings_review: dict[str, Any] | None = None

        if settings_review_required:
            reason = (
                f"settings review required after orchestration lessons: "
                f"{critical_open} critical, {noncritical_open} noncritical open events"
            )
            cursor = conn.execute(
                """
                INSERT INTO settings_reviews (slug, reason, event_count)
                VALUES (?, ?, ?)
                """,
                (slug, reason, critical_open + noncritical_open),
            )
            review_id = int(cursor.lastrowid)
            conn.execute(
                """
                UPDATE orchestration_events
                SET settings_review_id = ?
                WHERE slug = ? AND settings_review_id IS NULL
                """,
                (review_id, slug),
            )
            settings_review = {
                "id": review_id,
                "reason": reason,
                "event_count": critical_open + noncritical_open,
            }

    capture = None
    if settings_review:
        capture = knowledge_capture(
            slug,
            key=f"settings-review:{settings_review['id']}",
            value=settings_review["reason"],
            entity_id=f"settings-review:{settings_review['id']}",
            source_ref=source_ref or f"orchestration:{category}",
        )

    return {
        "slug": slug,
        "event_id": event_id,
        "category": category,
        "severity": severity,
        "settings_review_required": settings_review is not None,
        "settings_review": settings_review,
        "capture": capture,
    }


@mcp.tool()
def settings_review_queue(
    slug: str,
    include_resolved: bool = False,
    review_id: int | None = None,
    rubric_scores: dict[str, float] | None = None,
    resolution_note: str = "",
) -> dict[str, Any]:
    if not REGISTRY.resolve(slug):
        return {"error": "project_not_found", "slug": slug}

    updated_review: dict[str, Any] | None = None
    if review_id is not None and (rubric_scores is not None or resolution_note):
        conn_fn = getattr(REGISTRY, "_conn")
        with conn_fn() as conn:
            row = conn.execute(
                """
                SELECT id, event_count,
                       COALESCE(rubric_scores_json, '{}') AS rubric_scores_json,
                       COALESCE(resolution_note, '') AS resolution_note,
                       COALESCE(priority_score, 0.0) AS priority_score
                FROM settings_reviews
                WHERE id = ? AND slug = ?
                """,
                (review_id, slug),
            ).fetchone()
            if row:
                existing_rubric: dict[str, float] = {}
                try:
                    loaded = json.loads(row["rubric_scores_json"] or "{}")
                    if isinstance(loaded, dict):
                        existing_rubric = {str(k): float(v) for k, v in loaded.items()}
                except Exception:
                    existing_rubric = {}

                if rubric_scores is not None:
                    for k, v in rubric_scores.items():
                        existing_rubric[str(k)] = float(v)

                note_val = resolution_note if resolution_note else str(row["resolution_note"] or "")
                ev_count = int(row["event_count"] or 1)
                axes = ("intent_match", "trajectory_optimality", "token_economy")
                if existing_rubric:
                    vals = [float(existing_rubric.get(ax, 0.0)) for ax in axes if ax in existing_rubric]
                    if not vals:
                        vals = [float(v) for v in existing_rubric.values()]
                    avg_score = sum(vals) / max(1, len(vals))
                    deficit = max(0.0, 1.0 - avg_score)
                    priority_val = round(ev_count * (1.0 + deficit * 2.0) + avg_score, 4)
                else:
                    priority_val = round(float(ev_count), 4)

                auto_resolve = all(float(existing_rubric.get(ax, 0.0)) >= 0.7 for ax in axes)
                rubric_json = json.dumps(existing_rubric, sort_keys=True)
                if auto_resolve:
                    conn.execute(
                        """
                        UPDATE settings_reviews
                        SET rubric_scores_json = ?,
                            resolution_note = ?,
                            priority_score = ?,
                            resolved_at = COALESCE(resolved_at, CURRENT_TIMESTAMP)
                        WHERE id = ? AND slug = ?
                        """,
                        (rubric_json, note_val, priority_val, review_id, slug),
                    )
                else:
                    conn.execute(
                        """
                        UPDATE settings_reviews
                        SET rubric_scores_json = ?,
                            resolution_note = ?,
                            priority_score = ?
                        WHERE id = ? AND slug = ?
                        """,
                        (rubric_json, note_val, priority_val, review_id, slug),
                    )
                updated_row = conn.execute(
                    """
                    SELECT id, reason, event_count, created_at, resolved_at,
                           COALESCE(rubric_scores_json, '{}') AS rubric_scores_json,
                           COALESCE(resolution_note, '') AS resolution_note,
                           COALESCE(priority_score, 0.0) AS priority_score
                    FROM settings_reviews
                    WHERE id = ? AND slug = ?
                    """,
                    (review_id, slug),
                ).fetchone()
                if updated_row:
                    updated_review = dict(updated_row)
                    updated_review.pop("rubric_scores_json", None)
                    updated_review["rubric_scores"] = existing_rubric
                    updated_review["resolution_note"] = note_val
                    updated_review["priority_score"] = priority_val

    res: dict[str, Any] = {
        "slug": slug,
        "include_resolved": include_resolved,
        "reviews": _settings_review_rows(slug, include_resolved=include_resolved, limit=25),
    }
    if updated_review is not None:
        res["updated_review"] = updated_review
    return res


@mcp.tool()
def memory_query(slug: str = "", query: str = "", limit: int = 20, project: str = "") -> dict[str, Any]:
    slug = slug or project
    if not slug:
        return {"error": "slug_or_project_required"}
    pp, vector, _graph = _project_layers(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}

    # 1. SQLite FTS5 BM25 search
    fts_rows: list[dict[str, Any]] = []
    tokens = [f'"{w}"' for w in query.replace('"', ' ').replace("'", " ").split() if w]
    safe_match = " ".join(tokens) if tokens else f'"{query}"'

    with REGISTRY._conn() as conn:  # type: ignore[attr-defined]
        try:
            rows = conn.execute(
                """
                SELECT m.id, m.key, m.value, m.created_at, bm25(memory_fts) AS bm25_rank
                FROM memory_fts
                JOIN memory m ON m.id = memory_fts.rowid
                WHERE m.slug = ? AND memory_fts MATCH ?
                ORDER BY bm25_rank ASC
                LIMIT ?
                """,
                (slug, safe_match, limit * 2),
            ).fetchall()
            fts_rows = [
                {
                    "key": r["key"],
                    "value": r["value"],
                    "created_at": r["created_at"],
                    "bm25_rank": round(float(r["bm25_rank"]), 4),
                }
                for r in rows
            ]
        except Exception:
            fts_rows = []

        # Fallback cleanly to LIKE if FTS5 produced 0 results or encountered error
        if not fts_rows:
            q_like = f"%{query}%"
            rows = conn.execute(
                """
                SELECT key, value, created_at, 0.0 AS bm25_rank
                FROM memory
                WHERE slug = ? AND (key LIKE ? OR value LIKE ?)
                ORDER BY id DESC
                LIMIT ?
                """,
                (slug, q_like, q_like, limit * 2),
            ).fetchall()
            fts_rows = [
                {
                    "key": r["key"],
                    "value": r["value"],
                    "created_at": r["created_at"],
                    "bm25_rank": 0.0,
                }
                for r in rows
            ]

    # 2. ChromaDB Vector Similarity search
    semantic: list[dict[str, Any]] = []
    vec_items: list[dict[str, Any]] = []
    if vector is not None:
        semantic = vector.query(query, limit=limit * 2, collection="memories")
        for s in semantic:
            meta = s.get("metadata", {})
            vec_items.append(
                {
                    "key": meta.get("key", ""),
                    "value": s.get("document", ""),
                    "created_at": "",
                    "vector_similarity": s.get("similarity", 1.0),
                }
            )

    # 3. Reciprocal Rank Fusion (RRF)
    def _mem_id(item: dict[str, Any]) -> str:
        k_val = item.get("key", "").strip()
        v_val = item.get("value", "").strip()
        return hashlib.sha256(f"{slug}:{k_val}:{v_val}".encode("utf-8")).hexdigest()[:24]

    hybrid_results = _reciprocal_rank_fusion(
        fts_items=fts_rows,
        vec_items=vec_items,
        id_fn=_mem_id,
        k=60,
    )

    return {
        "slug": slug,
        "query": query,
        "keyword_results": fts_rows[:limit],
        "semantic_results": semantic[:limit],
        "hybrid_results": hybrid_results[:limit],
        "results": hybrid_results[:limit],
    }


@mcp.tool()
def graph_upsert(
    slug: str = "",
    src: str = "",
    rel: str = "",
    dst: str = "",
    payload: str = "",
    project: str = "",
    layer: str = "",
    causal_conv_id: str = "",
) -> dict[str, Any]:
    slug = slug or project
    if not slug:
        return {"error": "slug_or_project_required"}
    pp, _vector, graph = _project_layers(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}
    assert graph is not None
    res = graph.upsert_edge(
        src=src,
        rel=rel,
        dst=dst,
        payload=payload,
        layer=layer,
        causal_conv_id=causal_conv_id,
    )
    return {"slug": slug, "src": src, "rel": rel, "dst": dst, "upserted": True, **res}


@mcp.tool()
def find_path(
    src: str = "",
    dst: str = "",
    max_hops: int = 4,
    include_historical: bool = False,
    project: str = "",
    slug: str = "",
) -> dict[str, Any]:
    """Find the shortest path between two entities in the knowledge graph."""
    slug = slug or project
    if not slug:
        return {"error": "slug_or_project_required"}
    pp, _vector, graph = _project_layers(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}
    assert graph is not None
    res = graph.find_path(src=src, dst=dst, max_hops=max_hops, include_historical=include_historical)
    return {"slug": slug, "src": src, "dst": dst, **res}


def _annotate_edge_provenance(edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Annotate graph edges with Graphify provenance ('EXTRACTED' vs 'INFERRED')."""
    annotated: list[dict[str, Any]] = []
    for edge in edges:
        item = dict(edge)
        prov = item.get("provenance")
        if prov not in ("EXTRACTED", "INFERRED"):
            raw_payload = item.get("payload")
            if isinstance(raw_payload, str) and raw_payload.strip().startswith("{"):
                try:
                    p_dict = json.loads(raw_payload)
                    if isinstance(p_dict, dict) and p_dict.get("provenance") in ("EXTRACTED", "INFERRED"):
                        prov = p_dict["provenance"]
                except Exception:
                    pass
            if prov not in ("EXTRACTED", "INFERRED"):
                hop = item.get("hop", 1)
                prov = "EXTRACTED" if (hop <= 1 and item.get("is_current", 1) == 1) else "INFERRED"
        item["provenance"] = prov
        annotated.append(item)
    return annotated


@mcp.tool()
def graph_query(
    slug: str = "",
    term: str = "",
    limit: int = 50,
    include_historical: bool = False,
    max_tokens: int = 400,
    project: str = "",
    query: str = "",
) -> dict[str, Any]:
    slug = slug or project
    term = term or query
    if not slug:
        return {"error": "slug_or_project_required"}
    pp, _vector, graph = _project_layers(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}
    assert graph is not None
    raw_results = graph.query(
        term,
        limit=limit,
        include_historical=include_historical,
        max_tokens=max_tokens,
    )
    results = _annotate_edge_provenance(raw_results)
    return {
        "slug": slug,
        "term": term,
        "edge_provenance_model": "graphify-v1",
        "include_historical": include_historical,
        "max_tokens": max_tokens,
        "results": results,
    }


@mcp.tool()
def graph_neighbors(
    slug: str = "",
    entity_id: str = "",
    limit: int = 10,
    include_historical: bool = False,
    max_tokens: int = 400,
    project: str = "",
    entity: str = "",
) -> dict[str, Any]:
    slug = slug or project
    entity_id = entity_id or entity
    if not slug:
        return {"error": "slug_or_project_required"}
    pp, _vector, graph = _project_layers(slug)
    if not pp:
        return {"error": "project_not_found", "slug": slug}
    assert graph is not None
    raw_results = graph.neighbors(
        entity_id,
        limit=limit,
        include_historical=include_historical,
        max_tokens=max_tokens,
    )
    results = _annotate_edge_provenance(raw_results)
    return {
        "slug": slug,
        "entity_id": entity_id,
        "edge_provenance_model": "graphify-v1",
        "include_historical": include_historical,
        "max_tokens": max_tokens,
        "results": results,
        "neighbors": results,
    }


@mcp.tool()
def checkpoint_save(slug: str, name: str, payload: str) -> dict[str, Any]:
    if not REGISTRY.resolve(slug):
        return {"error": "project_not_found", "slug": slug}
    with REGISTRY._conn() as conn:  # type: ignore[attr-defined]
        conn.execute(
            "INSERT INTO checkpoints (slug, name, payload) VALUES (?, ?, ?)",
            (slug, name, payload),
        )
    return {"slug": slug, "name": name, "saved": True}


@mcp.tool()
def checkpoint_restore(slug: str, name: str) -> dict[str, Any]:
    if not REGISTRY.resolve(slug):
        return {"error": "project_not_found", "slug": slug}
    with REGISTRY._conn() as conn:  # type: ignore[attr-defined]
        row = conn.execute(
            "SELECT payload, created_at FROM checkpoints WHERE slug = ? AND name = ? ORDER BY id DESC LIMIT 1",
            (slug, name),
        ).fetchone()
    if not row:
        return {"error": "checkpoint_not_found", "slug": slug, "name": name}
    return {"slug": slug, "name": name, "payload": row["payload"], "created_at": row["created_at"]}


@mcp.tool()
def handoff_write(slug: str, name: str, payload: str) -> dict[str, Any]:
    if not REGISTRY.resolve(slug):
        return {"error": "project_not_found", "slug": slug}
    with REGISTRY._conn() as conn:  # type: ignore[attr-defined]
        conn.execute("INSERT INTO handoffs (slug, name, payload) VALUES (?, ?, ?)", (slug, name, payload))
    return {"slug": slug, "name": name, "saved": True}


@mcp.tool()
def handoff_checkpoint(slug: str = "", name: str = "", payload: str = "", project: str = "") -> dict[str, Any]:
    """Persist the same summary as both handoff and checkpoint for cheap resume paths."""
    slug = slug or project
    if not slug:
        return {"error": "slug_or_project_required"}
    handoff = handoff_write(slug, name, payload)
    if handoff.get("error"):
        return handoff
    checkpoint = checkpoint_save(slug, name, payload)
    return {
        "slug": slug,
        "name": name,
        "handoff_saved": handoff.get("saved", False),
        "checkpoint_saved": checkpoint.get("saved", False),
    }


@mcp.tool()
def handoff_read(slug: str, name: str) -> dict[str, Any]:
    if not REGISTRY.resolve(slug):
        return {"error": "project_not_found", "slug": slug}
    with REGISTRY._conn() as conn:  # type: ignore[attr-defined]
        row = conn.execute(
            "SELECT payload, created_at FROM handoffs WHERE slug = ? AND name = ? ORDER BY id DESC LIMIT 1",
            (slug, name),
        ).fetchone()
    if not row:
        return {"error": "handoff_not_found", "slug": slug, "name": name}
    return {"slug": slug, "name": name, "payload": row["payload"], "created_at": row["created_at"]}


def _format_toon(header_name: str, fields: list[str], rows: list[dict[str, Any]]) -> str:
    """Format tabular data in AXI TOON format ({header_name}[{len(rows)}]{{{','.join(fields)}}}:\\n  val1 | val2 ...)."""
    header = f"{header_name}[{len(rows)}]{{{','.join(fields)}}}:"
    if not rows:
        return header
    lines = [header]
    for row in rows:
        vals = [str(row.get(f, "")).replace("\n", " ").strip() for f in fields]
        lines.append("  " + " | ".join(vals))
    return "\n".join(lines)


@mcp.tool()
def batch_knowledge_query(
    slug: str = "",
    steps: list[dict[str, Any]] | None = None,
    output_format: str = "toon",
    project: str = "",
) -> dict[str, Any]:
    """Execute multiple codex_knowledge read and query operations in a single turn with compact TOON output."""
    target_slug = slug or project
    if not target_slug:
        return {"error": "slug_or_project_required"}

    if steps is None:
        steps = [
            {"op": "project_context", "query": ""},
            {"op": "memory_query", "query": ""},
            {"op": "graph_query", "query": ""},
        ]

    distilled_results: list[dict[str, Any]] = []
    toon_blocks: list[str] = []

    for idx, step in enumerate(steps, start=1):
        op = step.get("op", "").strip()
        step_res: dict[str, Any] = {}
        step_toon = ""

        if op == "project_context":
            q = step.get("query", "")
            lim = step.get("limit", 3)
            res = project_context(slug=target_slug, query=q, limit=lim)
            hits = res.get("top_context_hits", [])
            dist_hits = [
                {"source": h.get("source", ""), "title": h.get("title", ""), "score": h.get("score", 0)}
                for h in hits
            ]
            step_res = {
                "op": op,
                "query": q,
                "document_count": res.get("index_summary", {}).get("document_count", 0),
                "hits_count": len(hits),
                "top_context_hits": dist_hits,
            }
            step_toon = _format_toon(f"step_{idx}_project_context", ["source", "title", "score"], dist_hits)

        elif op == "memory_query":
            q = step.get("query", "")
            lim = step.get("limit", 20)
            res = memory_query(slug=target_slug, query=q, limit=lim)
            kw = res.get("keyword_results", [])
            sem = res.get("semantic_results", [])
            rows = [
                {"source": r.get("source", "keyword"), "key": r.get("key", ""), "value": (r.get("value") or "")[:80]}
                for r in (kw[:5] + sem[:5])
            ]
            step_res = {
                "op": op,
                "query": q,
                "count": res.get("count", len(rows)),
                "results": rows,
            }
            step_toon = _format_toon(f"step_{idx}_memory", ["source", "key", "value"], rows)

        elif op == "graph_query":
            q = step.get("query") or step.get("term", "")
            lim = step.get("limit", 20)
            res = graph_query(slug=target_slug, query=q, limit=lim)
            nodes = res.get("results", [])
            rows = [
                {"id": n.get("id", ""), "type": n.get("type", ""), "score": n.get("score", 0)}
                for n in nodes[:10]
            ]
            step_res = {
                "op": op,
                "query": q,
                "count": len(nodes),
                "results": rows,
            }
            step_toon = _format_toon(f"step_{idx}_graph_nodes", ["id", "type", "score"], rows)

        elif op == "graph_neighbors":
            nid = step.get("node_id") or step.get("node") or step.get("entity_id") or step.get("entity", "")
            depth = step.get("depth", 1)
            res = graph_neighbors(slug=target_slug, node_id=nid, depth=depth)
            nbrs = res.get("neighbors", [])
            rows = [
                {"target": n.get("target", ""), "rel": n.get("relation", ""), "weight": n.get("weight", 1.0)}
                for n in nbrs[:10]
            ]
            step_res = {
                "op": op,
                "node_id": nid,
                "count": len(nbrs),
                "neighbors": rows,
            }
            step_toon = _format_toon(f"step_{idx}_neighbors", ["target", "rel", "weight"], rows)

        elif op == "vault_search":
            q = step.get("query", "")
            lim = step.get("limit", 20)
            res = vault_search(slug=target_slug, query=q, limit=lim)
            hits = res.get("hits", [])
            rows = [
                {"path": h.get("relative_path", ""), "score": h.get("score", 0)}
                for h in hits[:10]
            ]
            step_res = {
                "op": op,
                "query": q,
                "count": len(hits),
                "hits": rows,
            }
            step_toon = _format_toon(f"step_{idx}_vault_search", ["path", "score"], rows)

        elif op == "vault_read":
            rel_p = step.get("relative_path") or step.get("path", "")
            res = vault_read(slug=target_slug, relative_path=rel_p)
            step_res = {
                "op": op,
                "relative_path": rel_p,
                "found": "error" not in res,
                "length": len(res.get("content", "")),
            }
            step_toon = f"step_{idx}_vault_read: {rel_p} (length={len(res.get('content', ''))})"

        elif op == "handoff_read":
            name = step.get("name", "latest")
            res = handoff_read(slug=target_slug, name=name)
            step_res = {
                "op": op,
                "name": name,
                "found": "error" not in res,
                "created_at": res.get("created_at", ""),
            }
            step_toon = f"step_{idx}_handoff_read: {name} (created_at={res.get('created_at', '')})"

        else:
            step_res = {"op": op, "error": f"unsupported_operation: {op}"}
            step_toon = f"step_{idx}_error: unsupported {op}"

        distilled_results.append(step_res)
        if step_toon:
            toon_blocks.append(step_toon)

    combined_toon = "\n\n".join(toon_blocks)
    return {
        "slug": target_slug,
        "step_count": len(steps),
        "format": output_format,
        "toon": combined_toon,
        "results": distilled_results,
    }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

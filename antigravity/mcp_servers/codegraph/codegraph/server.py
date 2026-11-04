from __future__ import annotations

import functools
import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:  # pragma: no cover
    raise SystemExit("Missing MCP runtime dependency. Run uv sync in mcp/codegraph.") from exc

from codegraph.db import (
    DEFAULT_DB_PATH,
    _last_sync_timestamp,
    ensure_indexed,
    get_connection,
    resolve_workspace_root,
)
from codegraph.metrics import (
    changed_symbols as _changed_symbols_impl,
    summarize_path as _summarize_path_impl,
)
from codegraph.pagerank import (
    generate_repo_map,
    get_file_ppr,
    get_graph,
    register_cache_invalidated_callback,
)

mcp = FastMCP("codegraph")

_callers_callees_cache: dict[tuple[str, float, str, int], dict[str, Any]] = {}
_symbol_lookup_cache: dict[tuple[str, float, str, int], dict[str, Any]] = {}
_impact_analysis_cache: dict[tuple[str, float, tuple[str, ...], tuple[str, ...], int], dict[str, Any]] = {}
_semantic_search_cache: dict[tuple[str, float, str, int], dict[str, Any]] = {}

_BUILTIN_CALLEE_NOISE: frozenset[str] = frozenset({
    "get", "set", "str", "int", "float", "bool", "len", "list", "dict", "tuple",
    "append", "extend", "pop", "keys", "values", "items", "lower", "upper",
    "strip", "lstrip", "rstrip", "split", "join", "replace", "startswith", "endswith",
    "isinstance", "getattr", "setattr", "hasattr", "print", "range", "enumerate",
    "zip", "sorted", "min", "max", "round", "sum", "any", "all", "open", "Path",
    "tool", "execute", "fetchall", "fetchone", "commit", "close", "cursor", "format",
    "add", "update", "clear", "copy", "push", "map", "filter", "reduce", "forEach",
    "includes", "slice", "trim",
})


def _clear_server_caches(workspace: str | None = None) -> None:
    _read_line.cache_clear()
    if workspace:
        for k in list(_callers_callees_cache.keys()):
            if k[0] == workspace:
                _callers_callees_cache.pop(k, None)
        for k in list(_symbol_lookup_cache.keys()):
            if k[0] == workspace:
                _symbol_lookup_cache.pop(k, None)
        for k in list(_impact_analysis_cache.keys()):
            if k[0] == workspace:
                _impact_analysis_cache.pop(k, None)
        for k in list(_semantic_search_cache.keys()):
            if k[0] == workspace:
                _semantic_search_cache.pop(k, None)
    else:
        _callers_callees_cache.clear()
        _symbol_lookup_cache.clear()
        _impact_analysis_cache.clear()
        _semantic_search_cache.clear()


register_cache_invalidated_callback(_clear_server_caches)


def _root(root: str) -> tuple[Path, Path]:
    target = Path(root).expanduser().resolve()
    if not target.exists():
        raise ValueError(f"root_not_found: {target}")
    workspace = resolve_workspace_root(target)
    return target, workspace


@functools.lru_cache(maxsize=1024)
def _read_line(file_path: Path, line_no: int) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for idx, line in enumerate(f, 1):
                if idx == line_no:
                    return line.strip()[:180]
    except OSError:
        pass
    return ""


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


def _infer_compact_schema(payload: Any, max_depth: int = 3) -> str:
    """Infer a deterministic compact JSON/TOON schema string for a payload."""
    val = payload
    if isinstance(val, str):
        stripped = val.strip()
        if (stripped.startswith("{") and stripped.endswith("}")) or (
            stripped.startswith("[") and stripped.endswith("]")
        ):
            try:
                val = json.loads(stripped)
            except Exception:
                return f"str[{len(val)}]"
        else:
            return f"str[{len(val)}]"

    def _schema(node: Any, depth: int) -> str:
        if node is None:
            return "null"
        if isinstance(node, bool):
            return "bool"
        if isinstance(node, int):
            return "int"
        if isinstance(node, float):
            return "float"
        if isinstance(node, str):
            return f"str[{len(node)}]"
        if isinstance(node, dict):
            if not node:
                return "dict{}"
            if depth <= 0:
                return f"dict[{len(node)}]"
            fields = [f"{k}:{_schema(v, depth - 1)}" for k, v in list(node.items())[:8]]
            if len(node) > 8:
                fields.append("...")
            return "dict{" + ",".join(fields) + "}"
        if isinstance(node, (list, tuple)):
            if not node:
                return "list[0]<null>"
            if depth <= 0:
                return f"list[{len(node)}]"
            return f"list[{len(node)}]<{_schema(node[0], depth - 1)}>"
        return type(node).__name__

    return _schema(val, max_depth)


def _maybe_spillover(payload: dict[str, Any], max_chars: int = 8000) -> dict[str, Any]:
    """Write large JSON payloads to disk and return compact metadata with spillover path."""
    serialized = json.dumps(payload, ensure_ascii=False)
    if len(serialized) <= max_chars:
        return payload
    sha = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:10]
    spillover_file = Path(f"/tmp/ag_mcp_spillover_{sha}.json")
    try:
        spillover_file.write_text(serialized, encoding="utf-8")
        compact_payload = dict(payload)
        compact_payload["spillover_path"] = str(spillover_file)
        compact_payload["spillover_schema"] = _infer_compact_schema(payload)
        compact_payload["spillover_note"] = (
            f"Payload ({len(serialized)} chars) exceeded limit ({max_chars}). Full content saved to {spillover_file}."
        )
        if "results" in compact_payload and isinstance(compact_payload["results"], list) and len(compact_payload["results"]) > 2:
            compact_payload["results"] = compact_payload["results"][:2]
        return compact_payload
    except Exception:
        return payload


@mcp.tool()
def repo_map(
    root: str,
    max_tokens: int = 1500,
    focus_files: list[str] | None = None,
    query: str | None = None,
) -> dict[str, Any]:
    """Render a concise, high-salience map of the repository's files and exported symbol signatures ranked by Personalized PageRank (PPR) within a token budget."""
    try:
        target, workspace = _root(root)
    except ValueError as exc:
        return {"error": str(exc)}

    ensure_indexed(workspace)
    res = generate_repo_map(
        workspace,
        max_tokens=max_tokens,
        focus_files=focus_files,
        query=query,
    )
    return {
        "root": str(workspace),
        "target": str(target),
        "max_tokens": max_tokens,
        "token_estimate": res["token_estimate"],
        "file_count": res["file_count"],
        "repo_map": res["repo_map"],
        "top_files": res["top_files"],
    }


@mcp.tool()
def symbol_lookup(root: str, query: str, limit: int = 20) -> dict[str, Any]:
    """Find likely symbol definitions and references in a project using incremental index and PageRank."""
    try:
        target, workspace = _root(root)
    except ValueError as exc:
        return {"error": str(exc)}

    needle = query.strip()
    if not needle:
        return {"error": "empty_query"}

    ensure_indexed(workspace)
    ws_str = str(workspace)
    sync_ts = _last_sync_timestamp.get(ws_str, 0.0)
    cache_key = (ws_str, sync_ts, needle, limit)
    if cache_key in _symbol_lookup_cache:
        cached = _symbol_lookup_cache[cache_key]
        return {
            "root": cached["root"],
            "target": cached["target"],
            "query": cached["query"],
            "count": cached["count"],
            "results": list(cached["results"]),
        }

    conn = get_connection()
    c = conn.cursor()

    file_ppr = get_file_ppr(ws_str, query=query)

    # 1. Look for definitions in symbols table
    needle_lower = needle.lower()
    c.execute(
        """
        SELECT name, kind, line, end_line, path, signature, exported
        FROM symbols
        WHERE workspace = ? AND LOWER(name) LIKE ?
        LIMIT 100
        """,
        (ws_str, f"%{needle_lower}%"),
    )
    def_rows = c.fetchall()

    results: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()

    for r in def_rows:
        name = r["name"]
        path_str = r["path"]
        line = r["line"]
        name_lower = name.lower()

        # Scoring: exact match > prefix match > substring match + PPR boost + exported boost
        score = 0.0
        if name == needle:
            score += 100.0
        elif name_lower == needle_lower:
            score += 80.0
        elif name_lower.startswith(needle_lower):
            score += 40.0
        else:
            score += 20.0

        if r["exported"]:
            score += 10.0
        kind = r["kind"]
        if kind in ("class", "interface", "type", "struct", "trait"):
            score += 15.0
        elif kind == "function":
            score += 10.0

        score += (file_ppr.get(path_str, 0.0) * 50.0)

        abs_path = workspace / path_str
        seen.add((path_str, line))
        results.append({
            "symbol": name,
            "kind": kind,
            "line": line,
            "end_line": r["end_line"],
            "path": str(abs_path),
            "match": "definition",
            "signature": r["signature"] or name,
            "exported": bool(r["exported"]),
            "score": round(score, 3),
        })

    # 2. Look for references in edges if room remains
    if len(results) < limit:
        c.execute(
            """
            SELECT src_path, src_symbol, rel, line
            FROM edges
            WHERE workspace = ? AND (dst_target = ? OR dst_target LIKE ?)
            LIMIT ?
            """,
            (ws_str, needle, f"%.{needle}", limit * 2),
        )
        edge_rows = c.fetchall()
        for er in edge_rows:
            src_path = er["src_path"]
            line = er["line"]
            if (src_path, line) in seen:
                continue
            seen.add((src_path, line))

            abs_path = workspace / src_path
            excerpt = _read_line(abs_path, line)
            score = 10.0 + (file_ppr.get(src_path, 0.0) * 30.0)

            results.append({
                "symbol": needle,
                "kind": "reference",
                "line": line,
                "end_line": line,
                "path": str(abs_path),
                "match": "reference",
                "signature": er["src_symbol"] or "<module>",
                "exported": False,
                "excerpt": excerpt,
                "score": round(score, 3),
            })
            if len(results) >= limit * 2:
                break

    # Sort results by score descending
    results.sort(key=lambda item: (-item["score"], item["path"], item["line"]))
    trimmed = results[:limit]

    res = {
        "root": str(workspace),
        "target": str(target),
        "query": query,
        "count": len(trimmed),
        "results": trimmed,
    }
    _symbol_lookup_cache[cache_key] = res
    return {
        "root": str(workspace),
        "target": str(target),
        "query": query,
        "count": len(trimmed),
        "results": list(trimmed),
    }


@mcp.tool()
def callers_callees(root: str, symbol: str, limit: int = 40) -> dict[str, Any]:
    """Return local caller and callee hints for a symbol using indexed structural edges and PageRank."""
    try:
        target, workspace = _root(root)
    except ValueError as exc:
        return {"error": str(exc)}

    sym = symbol.strip()
    if not sym:
        return {"error": "empty_symbol"}

    ensure_indexed(workspace)
    ws_str = str(workspace)
    sync_ts = _last_sync_timestamp.get(ws_str, 0.0)
    cache_key = (ws_str, sync_ts, sym, limit)
    if cache_key in _callers_callees_cache:
        cached = _callers_callees_cache[cache_key]
        return {
            "root": str(workspace),
            "symbol": sym,
            "edge_provenance_model": cached.get("edge_provenance_model", "graphify-v1"),
            "callers": list(cached["callers"]),
            "callees": list(cached["callees"]),
        }

    conn = get_connection()
    c = conn.cursor()
    file_ppr = get_file_ppr(ws_str, query=sym)

    # 1. Callers: edges targeting this symbol
    c.execute(
        """
        SELECT src_path, src_symbol, line, dst_target
        FROM edges
        WHERE workspace = ? AND (dst_target = ? OR dst_target LIKE ?)
        LIMIT 200
        """,
        (ws_str, sym, f"%.{sym}"),
    )
    raw_callers = c.fetchall()

    candidates: list[dict[str, Any]] = []
    seen_callers: set[tuple[str, int]] = set()

    for r in raw_callers:
        src_path = r["src_path"]
        line = r["line"]
        if (src_path, line) in seen_callers:
            continue
        seen_callers.add((src_path, line))

        abs_path = workspace / src_path
        caller_name = r["src_symbol"] or "<module>"
        ppr = file_ppr.get(src_path, 0.0)
        caller_prov = "EXTRACTED" if (r["dst_target"] == sym or bool(r["src_symbol"])) else "INFERRED"

        candidates.append({
            "caller": caller_name,
            "caller_kind": "function" if caller_name != "<module>" else "module",
            "path": str(abs_path),
            "abs_path": abs_path,
            "line": line,
            "ppr": round(ppr, 5),
            "provenance": caller_prov,
        })

    # Sort callers by (-item["ppr"], item["path"], item["line"]) and slice callers = callers[:limit] BEFORE calling _read_line
    candidates.sort(key=lambda item: (-item["ppr"], item["path"], item["line"]))
    top_candidates = candidates[:limit]

    callers: list[dict[str, Any]] = []
    for item in top_candidates:
        excerpt = _read_line(item["abs_path"], item["line"])
        callers.append({
            "caller": item["caller"],
            "caller_kind": item["caller_kind"],
            "path": item["path"],
            "line": item["line"],
            "excerpt": excerpt,
            "ppr": item["ppr"],
            "provenance": item["provenance"],
        })

    # 2. Callees: edges from this symbol
    # First, look up definitions of this symbol to scope callees to the symbol's body
    c.execute(
        """
        SELECT path, line, end_line
        FROM symbols
        WHERE workspace = ? AND name = ?
        """,
        (ws_str, sym),
    )
    sym_defs = c.fetchall()

    scoped_conditions: list[str] = []
    scoped_params: list[Any] = [ws_str, sym]
    for d in sym_defs:
        d_path = d["path"]
        d_line = d["line"]
        d_end = d["end_line"]
        if d_end and d_end >= d_line:
            scoped_conditions.append("(src_path = ? AND line >= ? AND line <= ?)")
            scoped_params.extend([d_path, d_line, d_end])
        else:
            scoped_conditions.append("(src_path = ? AND src_symbol = ?)")
            scoped_params.extend([d_path, sym])

    raw_callees = []
    callee_provenance = "EXTRACTED"
    if scoped_conditions:
        where_clause = f"workspace = ? AND rel IN ('CALLS', 'REFERENCES') AND (src_symbol = ? OR {' OR '.join(scoped_conditions)})"
        c.execute(
            f"""
            SELECT dst_target, COUNT(*) as cnt
            FROM edges
            WHERE {where_clause}
            GROUP BY dst_target
            ORDER BY cnt DESC
            LIMIT ?
            """,
            scoped_params + [limit * 4],
        )
        raw_callees = c.fetchall()

    if not raw_callees:
        c.execute(
            """
            SELECT dst_target, COUNT(*) as cnt
            FROM edges
            WHERE workspace = ? AND src_symbol = ? AND rel IN ('CALLS', 'REFERENCES')
            GROUP BY dst_target
            ORDER BY cnt DESC
            LIMIT ?
            """,
            (ws_str, sym, limit * 4),
        )
        raw_callees = c.fetchall()

    if not raw_callees:
        callee_provenance = "INFERRED"
        c.execute(
            """
            SELECT dst_target, COUNT(*) as cnt
            FROM edges
            WHERE workspace = ? AND src_path IN (SELECT path FROM symbols WHERE workspace = ? AND name = ?)
              AND rel IN ('CALLS', 'REFERENCES')
            GROUP BY dst_target
            ORDER BY cnt DESC
            LIMIT ?
            """,
            (ws_str, ws_str, sym, limit * 4),
        )
        raw_callees = c.fetchall()

    filter_noise = sym not in _BUILTIN_CALLEE_NOISE
    callees: list[dict[str, Any]] = []
    for row in raw_callees:
        t_name = row["dst_target"]
        if filter_noise and (t_name in _BUILTIN_CALLEE_NOISE or t_name.split(".")[-1] in _BUILTIN_CALLEE_NOISE):
            continue
        callees.append({"symbol": t_name, "count": row["cnt"], "provenance": callee_provenance})
        if len(callees) >= limit:
            break

    result = {
        "root": str(workspace),
        "symbol": sym,
        "edge_provenance_model": "graphify-v1",
        "callers": callers,
        "callees": callees,
    }
    _callers_callees_cache[cache_key] = result
    return {
        "root": str(workspace),
        "symbol": sym,
        "edge_provenance_model": "graphify-v1",
        "callers": list(callers),
        "callees": list(callees),
    }


@mcp.tool()
def impact_analysis(
    root: str,
    changed_paths: list[str] | None = None,
    symbols: list[str] | None = None,
    limit: int = 60,
) -> dict[str, Any]:
    """Estimate files and tests affected by changed paths or symbols using edge reference index and PageRank."""
    try:
        target, workspace = _root(root)
    except ValueError as exc:
        return {"error": str(exc)}

    changed_paths = changed_paths or []
    symbols = symbols or []

    ensure_indexed(workspace)
    ws_str = str(workspace)
    sync_ts = _last_sync_timestamp.get(ws_str, 0.0)
    paths_key = tuple(sorted(changed_paths))
    syms_key = tuple(sorted(symbols))
    cache_key = (ws_str, sync_ts, paths_key, syms_key, limit)
    if cache_key in _impact_analysis_cache:
        cached = _impact_analysis_cache[cache_key]
        return {
            "root": cached["root"],
            "edge_provenance_model": cached.get("edge_provenance_model", "graphify-v1"),
            "changed_paths": list(cached["changed_paths"]),
            "symbols": list(cached["symbols"]),
            "affected_files": list(cached["affected_files"]),
            "candidate_tests": list(cached["candidate_tests"]),
        }

    conn = get_connection()
    c = conn.cursor()

    # Normalize changed paths to relative paths
    norm_changed: list[str] = []
    for p in changed_paths:
        p_path = Path(p)
        if p_path.is_absolute():
            try:
                norm_changed.append(str(p_path.relative_to(workspace)))
            except ValueError:
                norm_changed.append(p)
        else:
            norm_changed.append(p)

    file_ppr = get_file_ppr(ws_str, focus_files=norm_changed, query=" ".join(symbols) if symbols else None)

    affected: dict[str, dict[str, Any]] = {}
    tests: list[str] = []

    # 1. Analyze changed paths
    for rel in norm_changed:
        abs_path = workspace / rel
        if abs_path.exists():
            affected[str(abs_path)] = {"reason": "changed_path", "score": 10.0, "provenance": "EXTRACTED"}

        # Find symbols defined in changed path
        c.execute("SELECT name FROM symbols WHERE workspace = ? AND path = ?", (ws_str, rel))
        file_syms = [row["name"] for row in c.fetchall()]

        # Find files that import or call these symbols
        if file_syms:
            placeholders = ",".join(["?"] * len(file_syms))
            c.execute(
                f"""
                SELECT src_path, COUNT(*) as cnt
                FROM edges
                WHERE workspace = ? AND dst_target IN ({placeholders}) AND src_path != ?
                GROUP BY src_path
                """,
                [ws_str, *file_syms, rel],
            )
            for row in c.fetchall():
                src_path = row["src_path"]
                full_src = str(workspace / src_path)
                entry = affected.setdefault(
                    full_src,
                    {"reason": "imports_changed_symbols", "score": 0.0, "provenance": "EXTRACTED"},
                )
                entry["provenance"] = "EXTRACTED"
                entry["score"] += row["cnt"] * 2.0
                if "test" in src_path.lower() or "spec" in src_path.lower():
                    tests.append(full_src)

    # 2. Analyze symbols
    for sym in symbols:
        c.execute(
            """
            SELECT src_path, COUNT(*) as cnt
            FROM edges
            WHERE workspace = ? AND (dst_target = ? OR dst_target LIKE ?)
            GROUP BY src_path
            """,
            (ws_str, sym, f"%.{sym}"),
        )
        for row in c.fetchall():
            src_path = row["src_path"]
            full_src = str(workspace / src_path)
            entry = affected.setdefault(
                full_src,
                {"reason": "symbol_reference", "score": 0.0, "provenance": "EXTRACTED"},
            )
            entry["provenance"] = "EXTRACTED"
            entry["score"] += row["cnt"] * 1.5
            if "test" in src_path.lower() or "spec" in src_path.lower():
                tests.append(full_src)

    # 3. Discover test candidates by path stems
    for rel in norm_changed:
        stem = Path(rel).stem.lower()
        c.execute(
            """
            SELECT rel_path FROM files
            WHERE workspace = ? AND (LOWER(rel_path) LIKE ? OR LOWER(rel_path) LIKE ?)
            """,
            (ws_str, f"%{stem}%test%", f"%{stem}%spec%"),
        )
        for row in c.fetchall():
            t_path = str(workspace / row["rel_path"])
            tests.append(t_path)
            affected.setdefault(t_path, {"reason": "test_stem_match", "score": 5.0, "provenance": "INFERRED"})

    # Blend with PPR scores
    ranked_affected = []
    for full_path, meta in affected.items():
        rel = str(Path(full_path).relative_to(workspace)) if Path(full_path).is_relative_to(workspace) else full_path
        ppr = file_ppr.get(rel, 0.0)
        total_score = meta["score"] + (ppr * 50.0)
        ranked_affected.append({
            "path": full_path,
            "reason": meta["reason"],
            "provenance": meta.get("provenance", "EXTRACTED"),
            "score": round(total_score, 2),
            "ppr": round(ppr, 5),
        })

    ranked_affected.sort(key=lambda item: (-item["score"], item["path"]))

    res = {
        "root": str(workspace),
        "edge_provenance_model": "graphify-v1",
        "changed_paths": list(changed_paths),
        "symbols": list(symbols),
        "affected_files": ranked_affected[:limit],
        "candidate_tests": sorted(set(tests))[:limit],
    }
    _impact_analysis_cache[cache_key] = res
    return {
        "root": str(workspace),
        "edge_provenance_model": "graphify-v1",
        "changed_paths": list(changed_paths),
        "symbols": list(symbols),
        "affected_files": list(ranked_affected[:limit]),
        "candidate_tests": list(sorted(set(tests))[:limit]),
    }


@mcp.tool()
def semantic_search(root: str, query: str, limit: int = 20) -> dict[str, Any]:
    """Run lightweight structure-aware search over symbol index and PageRank ranking."""
    try:
        target, workspace = _root(root)
    except ValueError as exc:
        return {"error": str(exc)}

    terms = [term.lower() for term in re.findall(r"[A-Za-z0-9_.$/-]+", query) if len(term) > 1]
    if not terms:
        return {"error": "empty_query"}

    ensure_indexed(workspace)
    ws_str = str(workspace)
    sync_ts = _last_sync_timestamp.get(ws_str, 0.0)
    cache_key = (ws_str, sync_ts, query, limit)
    if cache_key in _semantic_search_cache:
        cached = _semantic_search_cache[cache_key]
        return {
            "root": cached["root"],
            "query": cached["query"],
            "count": cached["count"],
            "results": list(cached["results"]),
        }

    conn = get_connection()
    c = conn.cursor()
    file_ppr = get_file_ppr(ws_str, query=query)

    # 1. Match symbols and signatures across files
    candidate_scores: dict[str, float] = {}
    for term in terms:
        c.execute(
            """
            SELECT path, name, signature, exported
            FROM symbols
            WHERE workspace = ? AND (LOWER(name) LIKE ? OR LOWER(signature) LIKE ?)
            LIMIT 100
            """,
            (ws_str, f"%{term}%", f"%{term}%"),
        )
        for row in c.fetchall():
            p = row["path"]
            score = 5.0 if term in row["name"].lower() else 2.0
            if row["exported"]:
                score += 2.0
            candidate_scores[p] = candidate_scores.get(p, 0.0) + score

    # Also score files matching path terms
    for term in terms:
        c.execute(
            "SELECT rel_path FROM files WHERE workspace = ? AND LOWER(rel_path) LIKE ? LIMIT 50",
            (ws_str, f"%{term}%"),
        )
        for row in c.fetchall():
            p = row["rel_path"]
            candidate_scores[p] = candidate_scores.get(p, 0.0) + 4.0

    # Combine with PPR score to get top files
    ranked_candidates = []
    for rel_path, term_score in candidate_scores.items():
        ppr = file_ppr.get(rel_path, 0.0)
        combined = term_score + (ppr * 30.0)
        ranked_candidates.append((rel_path, combined))

    ranked_candidates.sort(key=lambda item: -item[1])

    # Read excerpts for top candidates only
    hits: list[dict[str, Any]] = []
    for rel_path, combined_score in ranked_candidates[:limit * 2]:
        abs_path = workspace / rel_path
        try:
            text = abs_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        lines = text.splitlines()
        excerpts: list[dict[str, Any]] = []
        for index, line in enumerate(lines, start=1):
            line_lower = line.lower()
            if any(term in line_lower for term in terms):
                excerpts.append({"line": index, "text": line.strip()[:180]})
            if len(excerpts) >= 3:
                break

        hits.append({
            "path": str(abs_path),
            "score": round(combined_score, 2),
            "excerpts": excerpts,
        })
        if len(hits) >= limit:
            break

    hits.sort(key=lambda item: (-item["score"], item["path"]))

    res = {
        "root": str(workspace),
        "query": query,
        "count": len(hits[:limit]),
        "results": hits[:limit],
    }
    _semantic_search_cache[cache_key] = res
    return {
        "root": str(workspace),
        "query": query,
        "count": len(hits[:limit]),
        "results": list(hits[:limit]),
    }


@mcp.tool()
def summarize_path(path: str, limit: int = 50) -> dict[str, Any]:
    """Summarize structural metrics for a file or directory with fast persistent SQLite caching."""
    return _summarize_path_impl(path, limit=limit)


@mcp.tool()
def extract_symbols(
    root: str,
    path: str,
    symbols: list[str],
    max_total_lines: int = 250,
) -> dict[str, Any]:
    """Extract exact code slices for multiple symbols in a file up to max_total_lines in a single turn without hitting read slice limits."""
    try:
        target, workspace = _root(root)
    except ValueError as exc:
        return {"error": str(exc)}

    abs_path = (Path(path) if Path(path).is_absolute() else (workspace / path)).resolve()
    if not abs_path.is_file():
        return {"error": f"file_not_found: {abs_path}"}

    ensure_indexed(workspace)
    ws_str = str(workspace)
    rel_path = str(abs_path.relative_to(workspace)) if abs_path.is_relative_to(workspace) else abs_path.name

    try:
        file_lines = abs_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception as exc:
        return {"error": f"read_file_error: {exc}"}

    conn = get_connection()
    c = conn.cursor()

    budget = max(1, min(max_total_lines, 250))
    extracted: list[dict[str, Any]] = []
    toon_rows: list[dict[str, Any]] = []
    total_lines = 0

    for sym_name in symbols:
        sym_clean = sym_name.strip()
        if not sym_clean:
            continue

        # 1. Lookup in symbols table
        c.execute(
            """
            SELECT name, kind, line, end_line
            FROM symbols
            WHERE workspace = ? AND (path = ? OR path LIKE ?) AND name = ?
            ORDER BY line ASC
            LIMIT 1
            """,
            (ws_str, rel_path, f"%{abs_path.name}", sym_clean),
        )
        row = c.fetchone()
        start_line = None
        end_line = None
        kind = "symbol"

        if row:
            start_line = row["line"]
            end_line = row["end_line"]
            kind = row["kind"]
        else:
            # AST fallback
            try:
                from codegraph.parsers import parse_file
                syms, _ = parse_file(abs_path, ws_str, rel_path)
                for s in syms:
                    if s["name"] == sym_clean:
                        start_line = s["line"]
                        end_line = s["end_line"]
                        kind = s.get("kind", "symbol")
                        break
            except Exception:
                pass

        if start_line is None or end_line is None:
            # Fallback: simple line search for def/class/function
            for idx, line in enumerate(file_lines, start=1):
                if re.search(rf"\b{re.escape(sym_clean)}\b", line):
                    start_line = idx
                    end_line = min(idx + 30, len(file_lines))
                    kind = "fallback"
                    break

        if start_line is None:
            continue

        start_idx = max(1, start_line)
        end_idx = min(len(file_lines), max(start_idx, end_line if end_line else start_idx + 20))
        slice_lines = file_lines[start_idx - 1 : end_idx]
        lines_count = len(slice_lines)

        if total_lines + lines_count > budget:
            allowed = max(0, budget - total_lines)
            if allowed <= 0:
                break
            slice_lines = slice_lines[:allowed]
            end_idx = start_idx + allowed - 1
            lines_count = len(slice_lines)

        total_lines += lines_count
        content_str = "\n".join(slice_lines)

        extracted.append({
            "symbol": sym_clean,
            "kind": kind,
            "start_line": start_idx,
            "end_line": end_idx,
            "content": content_str,
        })
        toon_rows.append({
            "symbol": sym_clean,
            "kind": kind,
            "start_line": start_idx,
            "end_line": end_idx,
            "lines": lines_count,
        })

        if total_lines >= budget:
            break

    toon_str = _format_toon("extracted_symbols", ["symbol", "kind", "start_line", "end_line", "lines"], toon_rows)
    return {
        "root": str(workspace),
        "path": str(abs_path),
        "count": len(extracted),
        "total_lines": total_lines,
        "extracted": extracted,
        "toon": toon_str,
    }


@mcp.tool()
def batch_query(
    root: str,
    steps: list[dict[str, Any]],
    output_format: str = "toon",
) -> dict[str, Any]:
    """Execute a sequential batch of codegraph queries in-memory in a single turn with compact TOON output and spillover protection."""
    try:
        target, workspace = _root(root)
    except ValueError as exc:
        return {"error": str(exc)}

    ensure_indexed(workspace)
    distilled_results: list[dict[str, Any]] = []
    toon_blocks: list[str] = []

    last_symbols: list[str] = []
    last_paths: list[str] = []

    for idx, step in enumerate(steps, start=1):
        op = step.get("op", "").strip()
        from_prev = step.get("from_prev", False)

        step_res: dict[str, Any] = {}
        step_toon = ""

        if op == "symbol_lookup":
            q = step.get("query")
            if (not q or from_prev) and last_symbols:
                q = last_symbols[0]
            limit = step.get("limit", 20)
            res = symbol_lookup(root=root, query=q or "", limit=limit)
            raw_items = res.get("results", [])

            # Code-first filtering for prev_symbols and prev_paths
            code_items = [
                r for r in raw_items
                if r.get("kind") != "heading" and not str(r.get("path", "")).endswith(".md")
            ]
            filter_items = code_items if code_items else raw_items

            # Prioritize match == "definition"
            defs_first = sorted(
                filter_items,
                key=lambda r: (0 if r.get("match") == "definition" else 1),
            )
            last_symbols = [r["symbol"] for r in defs_first if "symbol" in r]
            last_paths = [r["path"] for r in defs_first if "path" in r]
            distilled_items = [
                {
                    "symbol": r.get("symbol", ""),
                    "kind": r.get("kind", ""),
                    "line": r.get("line", 0),
                    "path": r.get("path", ""),
                }
                for r in raw_items[:10]
            ]
            step_res = {"op": op, "count": len(raw_items), "results": distilled_items}
            step_toon = _format_toon(f"step_{idx}_symbol_lookup", ["symbol", "kind", "line", "path"], distilled_items)

        elif op == "callers_callees":
            sym = step.get("symbol")
            if (not sym or from_prev) and last_symbols:
                sym = last_symbols[0]
            limit = step.get("limit", 40)
            res = callers_callees(root=root, symbol=sym or "", limit=limit)
            callers_raw = res.get("callers", [])
            callees_raw = res.get("callees", [])
            if callers_raw:
                last_paths = [c["path"] for c in callers_raw if "path" in c and not str(c["path"]).endswith(".md")]
            c_syms = [c["caller"] for c in callers_raw if c.get("caller") != "<module>"] + [c["symbol"] for c in callees_raw]
            if c_syms:
                last_symbols = [s for s in c_syms if s not in _BUILTIN_CALLEE_NOISE]
            distilled_callers = [
                {"caller": c.get("caller", ""), "line": c.get("line", 0), "path": c.get("path", "")}
                for c in callers_raw[:10]
            ]
            distilled_callees = [
                {"symbol": c.get("symbol", ""), "count": c.get("count", 0)}
                for c in callees_raw[:10]
            ]
            step_res = {
                "op": op,
                "symbol": sym,
                "callers_count": len(callers_raw),
                "callees_count": len(callees_raw),
                "callers": distilled_callers,
                "callees": distilled_callees,
            }
            step_toon = _format_toon(f"step_{idx}_callers", ["caller", "line", "path"], distilled_callers)
            if distilled_callees:
                step_toon += "\n" + _format_toon(f"step_{idx}_callees", ["symbol", "count"], distilled_callees)

        elif op == "impact_analysis":
            changed_p = step.get("changed_paths")
            if (changed_p is None or from_prev) and last_paths:
                changed_p = last_paths[:5]
            syms = step.get("symbols")
            if (syms is None or from_prev) and last_symbols:
                syms = last_symbols[:5]
            limit = step.get("limit", 60)
            res = impact_analysis(root=root, changed_paths=changed_p, symbols=syms, limit=limit)
            aff_raw = res.get("affected_files", [])
            cand_raw = res.get("candidate_tests", [])
            distilled_aff = [
                {"path": a.get("path", ""), "score": a.get("score", 0), "reason": a.get("reason", "")}
                for a in aff_raw[:10]
            ]
            step_res = {
                "op": op,
                "affected_count": len(aff_raw),
                "candidate_tests": cand_raw[:10],
                "affected_files": distilled_aff,
            }
            step_toon = _format_toon(f"step_{idx}_impact", ["path", "score", "reason"], distilled_aff)

        elif op == "extract_symbols":
            p = step.get("path")
            if (not p or from_prev) and last_paths:
                p = last_paths[0]
            syms = step.get("symbols")
            if (not syms or from_prev) and last_symbols:
                syms = last_symbols[:5]
            max_lines = step.get("max_total_lines", 250)
            res = extract_symbols(root=root, path=p or "", symbols=syms or [], max_total_lines=max_lines)
            ext_raw = res.get("extracted", [])
            distilled_ext = [
                {
                    "symbol": e.get("symbol", ""),
                    "kind": e.get("kind", ""),
                    "start_line": e.get("start_line", 0),
                    "end_line": e.get("end_line", 0),
                }
                for e in ext_raw
            ]
            step_res = {
                "op": op,
                "path": res.get("path", ""),
                "count": len(ext_raw),
                "total_lines": res.get("total_lines", 0),
                "extracted": distilled_ext,
            }
            step_toon = res.get("toon") or _format_toon(f"step_{idx}_extracted", ["symbol", "kind", "start_line", "end_line"], distilled_ext)

        elif op == "semantic_search":
            q = step.get("query")
            if (not q or from_prev) and last_symbols:
                q = last_symbols[0]
            limit = step.get("limit", 20)
            res = semantic_search(root=root, query=q or "", limit=limit)
            raw_hits = res.get("results", [])
            dist_hits = [{"path": h.get("path", ""), "score": h.get("score", 0)} for h in raw_hits[:10]]
            if raw_hits:
                last_paths = [h["path"] for h in raw_hits if "path" in h]
            step_res = {"op": op, "count": len(raw_hits), "results": dist_hits}
            step_toon = _format_toon(f"step_{idx}_semantic", ["path", "score"], dist_hits)

        elif op == "repo_map":
            max_tok = step.get("max_tokens", 1500)
            f_files = step.get("focus_files")
            q = step.get("query")
            res = repo_map(root=root, max_tokens=max_tok, focus_files=f_files, query=q)
            step_res = {
                "op": op,
                "file_count": res.get("file_count", 0),
                "token_estimate": res.get("token_estimate", 0),
                "top_files": res.get("top_files", [])[:10],
            }
            top_rows = [{"file": f} for f in res.get("top_files", [])[:10]]
            step_toon = _format_toon(f"step_{idx}_repo_map", ["file"], top_rows)

        elif op == "summarize_path":
            p = step.get("path")
            if (not p or from_prev) and last_paths:
                p = last_paths[0]
            res = summarize_path(path=p or root, limit=step.get("limit", 50))
            step_res = {"op": op, "path": p, "metrics": res}
            step_toon = f"step_{idx}_summarize_path: {p}"

        else:
            step_res = {"op": op, "error": f"unsupported_operation: {op}"}
            step_toon = f"step_{idx}_error: unsupported {op}"

        distilled_results.append(step_res)
        if step_toon:
            toon_blocks.append(step_toon)

    combined_toon = "\n\n".join(toon_blocks)
    payload = {
        "root": str(workspace),
        "step_count": len(steps),
        "format": output_format,
        "toon": combined_toon,
        "results": distilled_results,
    }
    return _maybe_spillover(payload, max_chars=8000)


@mcp.tool()
def changed_symbols(diff_text: str) -> dict[str, Any]:
    """Extract symbol-like names from a diff with fast LRU caching."""
    return _changed_symbols_impl(diff_text)


if __name__ == "__main__":
    mcp.run(transport="stdio")

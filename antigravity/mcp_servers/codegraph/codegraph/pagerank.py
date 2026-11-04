from __future__ import annotations

import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from codegraph.db import DEFAULT_DB_PATH, _last_sync_timestamp, get_connection

_graph_cache: dict[str, Any] = {}
_graph_cache_timestamp: dict[str, float] = {}
_ppr_cache: dict[tuple[str, float, tuple[str, ...], str | None], dict[str, float]] = {}
_repo_map_cache: dict[tuple[str, float, int, tuple[str, ...], str | None], dict[str, Any]] = {}
_cache_invalidated_callbacks: list[Any] = []


def register_cache_invalidated_callback(cb: Any) -> None:
    if cb not in _cache_invalidated_callbacks:
        _cache_invalidated_callbacks.append(cb)


def invalidate_graph_cache(workspace: str | None = None) -> None:
    if workspace:
        _graph_cache.pop(workspace, None)
        _graph_cache_timestamp.pop(workspace, None)
        to_del_ppr = [k for k in _ppr_cache if k[0] == workspace]
        for k in to_del_ppr:
            _ppr_cache.pop(k, None)
        to_del_map = [k for k in _repo_map_cache if k[0] == workspace]
        for k in to_del_map:
            _repo_map_cache.pop(k, None)
    else:
        _graph_cache.clear()
        _graph_cache_timestamp.clear()
        _ppr_cache.clear()
        _repo_map_cache.clear()

    for cb in _cache_invalidated_callbacks:
        try:
            cb(workspace)
        except Exception:
            pass


def get_graph(workspace: str, db_path: Path = DEFAULT_DB_PATH) -> dict[str, Any]:
    if workspace in _graph_cache:
        return _graph_cache[workspace]

    conn = get_connection(db_path)
    c = conn.cursor()

    # Fetch all files
    c.execute("SELECT rel_path FROM files WHERE workspace = ?", (workspace,))
    all_files = [row["rel_path"] for row in c.fetchall()]
    N = len(all_files)
    node_to_idx = {name: i for i, name in enumerate(all_files)}
    file_set = set(all_files)

    # Fetch all symbols
    c.execute("SELECT name, path, kind, signature, exported FROM symbols WHERE workspace = ?", (workspace,))
    sym_to_files: dict[str, list[tuple[str, int]]] = defaultdict(list)
    file_to_symbols: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in c.fetchall():
        name = row["name"]
        path = row["path"]
        exported = row["exported"]
        sym_to_files[name].append((path, exported))
        file_to_symbols[path].append({
            "name": name,
            "kind": row["kind"],
            "signature": row["signature"] or name,
            "exported": exported,
        })

    # Fetch edges
    c.execute("SELECT src_path, dst_target, rel FROM edges WHERE workspace = ?", (workspace,))
    edges_map: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

    for row in c.fetchall():
        src = row["src_path"]
        dst = row["dst_target"]
        rel = row["rel"]

        if rel == "IMPORTS":
            # Direct/relative path matching
            src_parent = Path(src).parent
            candidate = (src_parent / dst).as_posix()
            matched = False
            for ext in ("", ".ts", ".tsx", ".js", ".jsx", ".py", "/index.ts", "/index.tsx"):
                cand_ext = (candidate + ext).lstrip("/")
                norm = Path(cand_ext).as_posix()
                if norm in file_set and norm != src:
                    edges_map[src][norm] += 2.0
                    matched = True
                    break
            if not matched and dst in sym_to_files:
                for def_path, exp in sym_to_files[dst]:
                    if def_path != src:
                        edges_map[src][def_path] += (2.0 if exp else 1.0)
        elif rel in ("CALLS", "REFERENCES"):
            if dst in sym_to_files:
                for def_path, exp in sym_to_files[dst]:
                    if def_path != src:
                        edges_map[src][def_path] += (1.5 if exp else 1.0)

    # Build flat edges and transition probabilities
    raw_edges: list[tuple[int, int, float]] = []
    out_sum = [0.0] * N
    for src, targets in edges_map.items():
        u = node_to_idx.get(src)
        if u is not None:
            for dst, w in targets.items():
                v = node_to_idx.get(dst)
                if v is not None and u != v:
                    raw_edges.append((u, v, w))
                    out_sum[u] += w

    flat_edges = [(u, v, w / out_sum[u]) for u, v, w in raw_edges if out_sum[u] > 0]
    dangling_indices = [i for i in range(N) if out_sum[i] == 0.0]

    graph_data = {
        "all_files": all_files,
        "node_to_idx": node_to_idx,
        "flat_edges": flat_edges,
        "dangling_indices": dangling_indices,
        "sym_to_files": sym_to_files,
        "file_to_symbols": file_to_symbols,
        "N": N,
    }
    _graph_cache[workspace] = graph_data
    _graph_cache_timestamp[workspace] = time.time()
    return graph_data


def compute_ppr(
    N: int,
    flat_edges: list[tuple[int, int, float]],
    dangling_indices: list[int],
    p_vec: list[float],
    alpha: float = 0.85,
    max_iter: int = 15,
) -> list[float]:
    if N == 0:
        return []
    rank = list(p_vec)
    one_minus_alpha = 1.0 - alpha
    for _ in range(max_iter):
        dangling_sum = sum(rank[i] for i in dangling_indices)
        base = one_minus_alpha + alpha * dangling_sum
        new_rank = [base * p_vec[i] for i in range(N)]
        for u, v, w in flat_edges:
            new_rank[v] += alpha * rank[u] * w
        rank = new_rank
    return rank


def get_file_ppr(
    workspace: str,
    focus_files: list[str] | None = None,
    query: str | None = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> dict[str, float]:
    sync_ts = _last_sync_timestamp.get(workspace, 0.0)
    focus_tuple = tuple(sorted(focus_files)) if focus_files else ()
    cache_key = (workspace, sync_ts, focus_tuple, query)
    if cache_key in _ppr_cache:
        return _ppr_cache[cache_key]

    graph = get_graph(workspace, db_path)
    N = graph["N"]
    if N == 0:
        return {}

    all_files = graph["all_files"]
    node_to_idx = graph["node_to_idx"]
    flat_edges = graph["flat_edges"]
    dangling_indices = graph["dangling_indices"]

    p_vec = [0.0] * N
    has_custom_prior = False

    # Check focus_files
    if focus_files:
        focus_indices: list[int] = []
        for f in focus_files:
            clean_f = Path(f).as_posix()
            if clean_f in node_to_idx:
                focus_indices.append(node_to_idx[clean_f])
            else:
                for path_str, idx in node_to_idx.items():
                    if path_str.endswith(clean_f) or clean_f.endswith(path_str):
                        focus_indices.append(idx)
        if focus_indices:
            focus_mass = 0.8
            each_focus = focus_mass / len(focus_indices)
            for idx in focus_indices:
                p_vec[idx] += each_focus
            rem_mass = 0.2 / N
            for i in range(N):
                p_vec[i] += rem_mass
            has_custom_prior = True

    # Check query terms
    if query and not has_custom_prior:
        terms = [t.lower() for t in re.findall(r"[A-Za-z0-9_]+", query) if len(t) > 1]
        if terms:
            match_scores = [0.0] * N
            total_score = 0.0
            sym_to_files = graph["sym_to_files"]
            for s_name, f_list in sym_to_files.items():
                s_lower = s_name.lower()
                for t in terms:
                    if t == s_lower:
                        weight = 5.0
                    elif t in s_lower:
                        weight = 2.0
                    else:
                        continue
                    for p_str, exp in f_list:
                        u = node_to_idx.get(p_str)
                        if u is not None:
                            match_scores[u] += weight * (1.5 if exp else 1.0)
                            total_score += weight

            if total_score > 0.0:
                query_mass = 0.85
                for i in range(N):
                    p_vec[i] = (query_mass * (match_scores[i] / total_score)) + ((1.0 - query_mass) / N)
                has_custom_prior = True

    if not has_custom_prior:
        p_vec = [1.0 / N] * N

    ranks = compute_ppr(N, flat_edges, dangling_indices, p_vec)
    result = {all_files[i]: ranks[i] for i in range(N)}
    _ppr_cache[cache_key] = result
    return result


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 3.5)


def generate_repo_map(
    workspace_root: Path,
    max_tokens: int = 1500,
    focus_files: list[str] | None = None,
    query: str | None = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> dict[str, Any]:
    ws_str = str(workspace_root.resolve())
    sync_ts = _last_sync_timestamp.get(ws_str, 0.0)
    focus_tuple = tuple(sorted(focus_files)) if focus_files else ()
    cache_key = (ws_str, sync_ts, max_tokens, focus_tuple, query)
    if cache_key in _repo_map_cache:
        return dict(_repo_map_cache[cache_key])

    graph = get_graph(ws_str, db_path)
    file_ppr = get_file_ppr(ws_str, focus_files=focus_files, query=query, db_path=db_path)
    if not file_ppr:
        return {
            "root": ws_str,
            "max_tokens": max_tokens,
            "token_estimate": 0,
            "file_count": 0,
            "repo_map": "",
            "top_files": [],
        }

    sorted_files = sorted(file_ppr.items(), key=lambda x: -x[1])
    file_to_syms = graph["file_to_symbols"]

    def kind_priority(kind: str) -> int:
        if kind in ("class", "struct"):
            return 1
        if kind in ("interface", "trait", "type", "enum"):
            return 2
        if kind == "function":
            return 3
        return 4

    prepared_files: list[dict[str, Any]] = []
    for rel_path, score in sorted_files:
        syms = file_to_syms.get(rel_path, [])
        filtered = [s for s in syms if s.get("exported", 0) == 1]
        if not filtered:
            filtered = syms
        filtered.sort(key=lambda s: (kind_priority(s.get("kind", "")), s.get("line", 0)))
        prepared_files.append({
            "path": rel_path,
            "score": score,
            "symbols": filtered,
        })

    def render_map(n_files: int, max_syms_per_file: int = 8) -> tuple[str, list[dict[str, Any]]]:
        lines: list[str] = []
        included: list[dict[str, Any]] = []
        for item in prepared_files[:n_files]:
            rel_p = item["path"]
            syms = item["symbols"][:max_syms_per_file]
            lines.append(f"{rel_p}:")
            included_syms = []
            for s in syms:
                sig = s.get("signature") or s["name"]
                lines.append(f"  {sig}")
                included_syms.append(s["name"])
            included.append({
                "path": rel_p,
                "score": round(item["score"], 5),
                "symbols": included_syms,
            })
        return "\n".join(lines), included

    low = 1
    high = len(prepared_files)
    best_text = ""
    best_included: list[dict[str, Any]] = []

    while low <= high:
        mid = (low + high) // 2
        candidate_text, candidate_included = render_map(mid, max_syms_per_file=6)
        tok = _estimate_tokens(candidate_text)
        if tok <= max_tokens:
            best_text = candidate_text
            best_included = candidate_included
            low = mid + 1
        else:
            high = mid - 1

    if not best_text and prepared_files:
        candidate_text, candidate_included = render_map(1, max_syms_per_file=2)
        best_text = candidate_text
        best_included = candidate_included

    res = {
        "root": ws_str,
        "max_tokens": max_tokens,
        "token_estimate": int(_estimate_tokens(best_text)),
        "file_count": len(best_included),
        "repo_map": best_text,
        "top_files": best_included,
    }
    _repo_map_cache[cache_key] = res
    return dict(res)

from __future__ import annotations

import tempfile
import time
from pathlib import Path
import sys

pkg_root = Path(__file__).resolve().parent.parent
if str(pkg_root) not in sys.path:
    sys.path.insert(0, str(pkg_root))

from codegraph.db import (
    ensure_indexed,
    get_connection,
    resolve_workspace_root,
)
from codegraph.pagerank import (
    compute_ppr,
    generate_repo_map,
    get_file_ppr,
    get_graph,
    invalidate_graph_cache,
)
from codegraph.parsers import parse_file
from codegraph.server import (
    batch_query,
    callers_callees,
    changed_symbols,
    extract_symbols,
    impact_analysis,
    repo_map,
    semantic_search,
    summarize_path,
    symbol_lookup,
    _format_toon,
    _infer_compact_schema,
    _maybe_spillover,
)


def test_parsers_multilang() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)

        # 1. Python file
        py_file = tmp / "service.py"
        py_file.write_text(
            """
import os
from math import sqrt

class CalculatorService:
    def add(self, a: int, b: int) -> int:
        return a + b
    def compute(self, x: int) -> float:
        return sqrt(x)

def run_service():
    calc = CalculatorService()
    return calc.add(1, 2)
""",
            encoding="utf-8",
        )
        syms_py, edges_py = parse_file(py_file, str(tmp), "service.py")
        py_names = {s["name"] for s in syms_py}
        assert "CalculatorService" in py_names
        assert "add" in py_names
        assert "compute" in py_names
        assert "run_service" in py_names
        py_rels = {e[3] for e in edges_py}
        assert "IMPORTS" in py_rels
        assert "CALLS" in py_rels

        # 2. TypeScript file
        ts_file = tmp / "almanac.ts"
        ts_file.write_text(
            """
import { useState } from 'react';

export interface AlmanacDay {
    solarDate: string;
    lunarDate: string;
}

export class AlmanacEngine {
    computeDay(): AlmanacDay {
        return { solarDate: '2026-10-15', lunarDate: '2026-09-05' };
    }
}

export function getGoldenHours(day: AlmanacDay): string[] {
    return ['Giờ Tý', 'Giờ Dần'];
}
""",
            encoding="utf-8",
        )
        syms_ts, edges_ts = parse_file(ts_file, str(tmp), "almanac.ts")
        ts_names = {s["name"] for s in syms_ts}
        assert "AlmanacDay" in ts_names
        assert "AlmanacEngine" in ts_names
        assert "getGoldenHours" in ts_names

        # 3. Kotlin file
        kt_file = tmp / "Helper.kt"
        kt_file.write_text(
            """
package com.lichviet.app
import android.content.Context

class LocationHelper(val context: Context) {
    fun getLocation(): String {
        return "10.77, 106.69"
    }
}
""",
            encoding="utf-8",
        )
        syms_kt, edges_kt = parse_file(kt_file, str(tmp), "Helper.kt")
        kt_names = {s["name"] for s in syms_kt}
        assert "LocationHelper" in kt_names
        assert "getLocation" in kt_names

        # 4. Go file
        go_file = tmp / "engine.go"
        go_file.write_text(
            """
package main
import "fmt"

type ServerConfig struct {
    Port int
}

func StartServer(cfg ServerConfig) {
    fmt.Println(cfg.Port)
}
""",
            encoding="utf-8",
        )
        syms_go, edges_go = parse_file(go_file, str(tmp), "engine.go")
        go_names = {s["name"] for s in syms_go}
        assert "ServerConfig" in go_names
        assert "StartServer" in go_names

        # 5. Rust file
        rs_file = tmp / "lib.rs"
        rs_file.write_text(
            """
pub struct AstroModel {
    pub jd: f64,
}

pub fn calculate_ephemeris(jd: f64) -> AstroModel {
    AstroModel { jd }
}
""",
            encoding="utf-8",
        )
        syms_rs, edges_rs = parse_file(rs_file, str(tmp), "lib.rs")
        rs_names = {s["name"] for s in syms_rs}
        assert "AstroModel" in rs_names
        assert "calculate_ephemeris" in rs_names


def test_incremental_sqlite_indexing() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        db_path = tmp / "test_codegraph.sqlite"

        # Create 3 files
        f1 = tmp / "a.ts"
        f1.write_text("export function funcA() { return 1; }", encoding="utf-8")
        f2 = tmp / "b.ts"
        f2.write_text("import { funcA } from './a'; export function funcB() { return funcA(); }", encoding="utf-8")
        f3 = tmp / "c.ts"
        f3.write_text("export function funcC() { return 3; }", encoding="utf-8")

        # Initial index
        res1 = ensure_indexed(tmp, force=True, db_path=db_path)
        assert res1["added"] == 3
        assert res1["updated"] == 0
        assert res1["deleted"] == 0

        conn = get_connection(db_path)
        c = conn.cursor()
        ws_key = str(tmp.resolve())  # the indexer stores resolved paths (macOS /var -> /private/var)
        c.execute("SELECT COUNT(*) FROM files WHERE workspace = ?", (ws_key,))
        assert c.fetchone()[0] == 3

        c.execute("SELECT COUNT(*) FROM symbols WHERE workspace = ?", (ws_key,))
        assert c.fetchone()[0] == 3

        # Modify file 2 only
        time.sleep(0.01)
        f2.write_text("import { funcA } from './a'; export function funcB2() { return funcA(); }", encoding="utf-8")
        res2 = ensure_indexed(tmp, force=True, db_path=db_path)
        assert res2["added"] == 0
        assert res2["updated"] == 1
        assert res2["deleted"] == 0

        c.execute("SELECT name FROM symbols WHERE workspace = ? AND path = 'b.ts'", (ws_key,))
        names = [r[0] for r in c.fetchall()]
        assert "funcB2" in names
        assert "funcB" not in names

        # Delete file 3
        f3.unlink()
        res3 = ensure_indexed(tmp, force=True, db_path=db_path)
        assert res3["deleted"] == 1
        c.execute("SELECT COUNT(*) FROM files WHERE workspace = ?", (ws_key,))
        assert c.fetchone()[0] == 2


def test_ppr_and_repo_map() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        db_path = tmp / "ppr_test.sqlite"

        # Hub and authority graph: core.ts is imported by view1.ts, view2.ts, view3.ts
        core = tmp / "core.ts"
        core.write_text(
            """
export interface CoreConfig { debug: boolean; }
export class CoreEngine {
    start() {}
}
export function computeCoreValue() { return 42; }
""",
            encoding="utf-8",
        )
        for i in range(1, 4):
            v = tmp / f"view{i}.ts"
            v.write_text(
                f"""
import {{ CoreEngine, computeCoreValue }} from './core';
export function renderView{i}() {{
    const engine = new CoreEngine();
    return computeCoreValue();
}}
""",
                encoding="utf-8",
            )

        ensure_indexed(tmp, force=True, db_path=db_path)
        invalidate_graph_cache(str(tmp.resolve()))

        ppr = get_file_ppr(str(tmp.resolve()), db_path=db_path)
        # core.ts should have highest PageRank because all views call/import it
        assert ppr["core.ts"] > ppr["view1.ts"]

        # repo_map with budget
        res_map = generate_repo_map(tmp, max_tokens=200, db_path=db_path)
        assert res_map["token_estimate"] <= 200
        assert "core.ts:" in res_map["repo_map"]
        assert "CoreEngine" in res_map["repo_map"]


def test_treesitter_caching() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        py_file = tmp / "example.py"
        py_file.write_text(
            """
class Demo:
    def method_one(self): pass
    def method_two(self): pass

def standalone(): pass
""",
            encoding="utf-8",
        )
        md_file = tmp / "README.md"
        md_file.write_text("# Title\n## Section 1\n### Section 2\n", encoding="utf-8")

        # Cold summary
        res1 = summarize_path(str(tmp))
        assert res1["file_count"] == 2
        py_metric = next(m for m in res1["files"] if m["language"] == "python")
        assert py_metric["class_count"] == 1
        assert py_metric["function_count"] == 3

        # Warm summary
        t0 = time.perf_counter()
        res2 = summarize_path(str(tmp))
        t1 = time.perf_counter()
        warm_ms = (t1 - t0) * 1000
        assert warm_ms < 5.0, f"Warm summarize_path took {warm_ms:.2f}ms >= 5ms"
        assert res2["file_count"] == 2


def test_changed_symbols_lru() -> None:
    diff = """
--- a/app.py
+++ b/app.py
@@ -10,3 +10,5 @@
-def deprecated_helper():
+def new_optimized_helper():
+class NewFeatureEngine:
"""
    res1 = changed_symbols(diff)
    assert "new_optimized_helper" in res1["added_symbols"]
    assert "NewFeatureEngine" in res1["added_symbols"]
    assert "deprecated_helper" in res1["removed_symbols"]

    # Warm call (LRU)
    t0 = time.perf_counter()
    res2 = changed_symbols(diff)
    t1 = time.perf_counter()
    warm_ms = (t1 - t0) * 1000
    assert warm_ms < 1.0, f"changed_symbols took {warm_ms:.3f}ms >= 1ms"
    assert res1 == res2


def test_warm_latency_benchmark() -> None:
    ws = "/home/heocop/Projects/lich-viet-lich-only"
    if not Path(ws).exists():
        return

    # Warm up
    repo_map(ws, max_tokens=1500)
    symbol_lookup(ws, query="Almanac")
    callers_callees(ws, symbol="calculateAlmanac")
    impact_analysis(ws, changed_paths=["packages/core/src/calendar/canchiHelper.ts"])
    semantic_search(ws, query="almanac golden hour")
    summarize_path(ws)
    changed_symbols("--- a/f.py\n+++ b/f.py\n@@ -1,2 +1,2 @@\n-def a():\n+def b():\n")

    # Benchmarks
    t0 = time.perf_counter()
    rm = repo_map(ws, max_tokens=1500)
    t1 = time.perf_counter()
    rm_ms = (t1 - t0) * 1000
    assert rm_ms < 15.0, f"repo_map took {rm_ms:.2f}ms >= 15ms"
    assert rm["file_count"] > 0
    assert rm["token_estimate"] <= 1500

    t0 = time.perf_counter()
    sl = symbol_lookup(ws, query="Almanac")
    t1 = time.perf_counter()
    sl_ms = (t1 - t0) * 1000
    assert sl_ms < 15.0, f"symbol_lookup took {sl_ms:.2f}ms >= 15ms"

    t0 = time.perf_counter()
    cc = callers_callees(ws, symbol="calculateAlmanac")
    t1 = time.perf_counter()
    cc_ms = (t1 - t0) * 1000
    assert cc_ms < 15.0, f"callers_callees took {cc_ms:.2f}ms >= 15ms"

    t0 = time.perf_counter()
    ia = impact_analysis(ws, changed_paths=["packages/core/src/calendar/canchiHelper.ts"])
    t1 = time.perf_counter()
    ia_ms = (t1 - t0) * 1000
    assert ia_ms < 15.0, f"impact_analysis took {ia_ms:.2f}ms >= 15ms"

    t0 = time.perf_counter()
    ss = semantic_search(ws, query="almanac golden hour")
    t1 = time.perf_counter()
    ss_ms = (t1 - t0) * 1000
    assert ss_ms < 15.0, f"semantic_search took {ss_ms:.2f}ms >= 15ms"

    t0 = time.perf_counter()
    sp = summarize_path(ws)
    t1 = time.perf_counter()
    sp_ms = (t1 - t0) * 1000
    assert sp_ms < 15.0, f"summarize_path took {sp_ms:.2f}ms >= 15ms"

    t0 = time.perf_counter()
    cs = changed_symbols("--- a/f.py\n+++ b/f.py\n@@ -1,2 +1,2 @@\n-def a():\n+def b():\n")
    t1 = time.perf_counter()
    cs_ms = (t1 - t0) * 1000
    assert cs_ms < 5.0, f"changed_symbols took {cs_ms:.2f}ms >= 5ms"


def test_extract_symbols_and_batch_query_toon() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        svc_file = tmp / "processor.py"
        svc_file.write_text(
            """class DataProcessor:
    def process_records(self, records: list) -> int:
        n = len(records)
        s = str(n)
        return self.do_work(s)

    def do_work(self, val: str) -> int:
        return 42

def run_pipeline():
    dp = DataProcessor()
    return dp.process_records([1, 2, 3])
""",
            encoding="utf-8",
        )
        md_file = tmp / "README.md"
        md_file.write_text("# DataProcessor Reference Guide\nDocumentation.\n", encoding="utf-8")

        # 1. Test extract_symbols
        ext = extract_symbols(
            root=str(tmp),
            path="processor.py",
            symbols=["DataProcessor", "run_pipeline"],
            max_total_lines=250,
        )
        assert ext["count"] == 2
        assert ext["total_lines"] > 0
        assert "extracted_symbols[2]{symbol,kind,start_line,end_line,lines}:" in ext["toon"]
        assert "DataProcessor" in ext["toon"]
        assert "run_pipeline" in ext["toon"]
        for item in ext["extracted"]:
            assert item["symbol"] in ("DataProcessor", "run_pipeline")
            assert item["content"]

        # 2. Test callers_callees filters built-in noise (len, str, get) and scopes to body
        cc = callers_callees(root=str(tmp), symbol="process_records")
        assert cc.get("edge_provenance_model") == "graphify-v1"
        callee_syms = [c["symbol"] for c in cc.get("callees", [])]
        assert "len" not in callee_syms, "Built-in 'len' must be filtered from callees"
        assert "str" not in callee_syms, "Built-in 'str' must be filtered from callees"
        assert "get" not in callee_syms, "Built-in 'get' must be filtered from callees"
        assert "do_work" in callee_syms, "Domain method 'do_work' must be preserved in callees"
        for c_item in cc.get("callers", []):
            assert c_item.get("provenance") in ("EXTRACTED", "INFERRED")
        for c_item in cc.get("callees", []):
            assert c_item.get("provenance") in ("EXTRACTED", "INFERRED")

        ia_res = impact_analysis(root=str(tmp), changed_paths=["processor.py"], symbols=["DataProcessor"])
        assert ia_res.get("edge_provenance_model") == "graphify-v1"
        assert len(ia_res.get("affected_files", [])) >= 1
        for af in ia_res.get("affected_files", []):
            assert af.get("provenance") in ("EXTRACTED", "INFERRED")

        # 3. Test batch_query with from_prev=True: excludes markdown headings from code impact seeding
        steps = [
            {"op": "symbol_lookup", "query": "DataProcessor", "limit": 5},
            {"op": "callers_callees", "from_prev": True, "limit": 10},
            {"op": "impact_analysis", "from_prev": True, "limit": 10},
            {"op": "extract_symbols", "from_prev": True, "max_total_lines": 250},
        ]
        bq = batch_query(root=str(tmp), steps=steps, output_format="toon")
        assert bq["step_count"] == 4
        assert bq["format"] == "toon"
        assert len(bq["results"]) == 4
        assert "step_1_symbol_lookup" in bq["toon"]
        assert "step_2_callers" in bq["toon"]
        assert "step_3_impact" in bq["toon"]
        aff_paths = [f["path"] for f in bq["results"][2].get("affected_files", [])]
        assert not any(p.endswith(".md") for p in aff_paths), "Markdown headings must be excluded from from_prev code impact"

        # 4. Test spillover protection
        large_payload = {
            "root": str(tmp),
            "step_count": 1,
            "format": "toon",
            "toon": "X" * 10000,
            "results": [{"data": "large"}],
        }
        spilled = _maybe_spillover(large_payload, max_chars=1000)
        assert "spillover_path" in spilled
        assert "spillover_schema" in spilled
        assert spilled["spillover_schema"].startswith("dict{root:str")
        sp_path = Path(spilled["spillover_path"])
        assert sp_path.is_file()
        sp_path.unlink(missing_ok=True)


def test_infer_compact_schema() -> None:
    assert _infer_compact_schema(None) == "null"
    assert _infer_compact_schema(False) == "bool"
    assert _infer_compact_schema(10) == "int"
    assert _infer_compact_schema(2.5) == "float"
    assert _infer_compact_schema("abc") == "str[3]"
    assert _infer_compact_schema({"k": [1, 2]}) == "dict{k:list[2]<int>}"


def test_spillover_write_failure_resilience() -> None:
    from unittest.mock import patch
    large_payload = {
        "root": "/tmp",
        "step_count": 1,
        "format": "toon",
        "toon": "X" * 10000,
        "results": [{"data": "large"}],
    }
    with patch.object(Path, "write_text", side_effect=OSError("Disk full")):
        res = _maybe_spillover(large_payload, max_chars=1000)
        assert "spillover_path" not in res
        assert res == large_payload


if __name__ == "__main__":
    test_parsers_multilang()
    print("✓ test_parsers_multilang passed")
    test_incremental_sqlite_indexing()
    print("✓ test_incremental_sqlite_indexing passed")
    test_ppr_and_repo_map()
    print("✓ test_ppr_and_repo_map passed")
    test_treesitter_caching()
    print("✓ test_treesitter_caching passed")
    test_changed_symbols_lru()
    print("✓ test_changed_symbols_lru passed")
    test_extract_symbols_and_batch_query_toon()
    print("✓ test_extract_symbols_and_batch_query_toon passed")
    test_spillover_write_failure_resilience()
    print("✓ test_spillover_write_failure_resilience passed")
    test_warm_latency_benchmark()
    print("✓ test_warm_latency_benchmark passed (<15ms)")

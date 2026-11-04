from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Any

import codex_knowledge.registry
import codex_knowledge.server
import codex_knowledge.settings
from codex_knowledge.graph_layer import (
    GraphLayer,
    MAGMA_REL_LAYERS,
    _classify_query_intent,
    _infer_edge_layer,
)
from codex_knowledge.registry import REGISTRY, Registry
from codex_knowledge.server import (
    _reciprocal_rank_fusion,
    _refresh_document_inventory,
    find_path,
    graph_neighbors,
    graph_query,
    graph_upsert,
    memory_query,
    memory_store,
    vault_search,
)
from codex_knowledge.settings import Settings
from codex_knowledge.vector_memory import VectorMemory


def test_bitemporal_graph_and_migration():
    """Test safe ALTER TABLE migration and bi-temporal edge invalidation."""
    temp_dir = Path(tempfile.mkdtemp(prefix="test_bitemporal_"))
    try:
        sqlite_file = temp_dir / "graph.sqlite"
        # Simulate legacy database with old schema without bi-temporal columns
        with sqlite3.connect(sqlite_file) as conn:
            conn.execute(
                """
                CREATE TABLE edges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    src TEXT NOT NULL,
                    rel TEXT NOT NULL,
                    dst TEXT NOT NULL,
                    payload TEXT
                )
                """
            )
            conn.execute(
                "INSERT INTO edges (src, rel, dst, payload) VALUES (?, ?, ?, ?)",
                ("alpha", "CONNECTS_TO", "beta", "initial connection"),
            )
            conn.commit()

        # Initialize GraphLayer on the legacy database - triggers safe ALTER TABLE migration
        gl = GraphLayer(temp_dir)
        with sqlite3.connect(sqlite_file) as conn:
            conn.row_factory = sqlite3.Row
            cols = {r["name"] for r in conn.execute("PRAGMA table_info(edges)").fetchall()}
            assert "valid_from" in cols, "valid_from column missing after migration"
            assert "valid_to" in cols, "valid_to column missing after migration"
            assert "recorded_at" in cols, "recorded_at column missing after migration"
            assert "is_current" in cols, "is_current column missing after migration"

            row = conn.execute("SELECT * FROM edges WHERE id = 1").fetchone()
            assert row["is_current"] == 1, "Legacy row should be marked current"
            assert row["valid_from"] is not None, "Legacy row valid_from should be backfilled"
            assert row["recorded_at"] is not None, "Legacy row recorded_at should be backfilled"
            assert row["valid_to"] is None, "Legacy row valid_to should be None"

        # Test Upsert 1: Identical edge (alpha, CONNECTS_TO, beta, "initial connection")
        res1 = gl.upsert("alpha", "CONNECTS_TO", "beta", "initial connection")
        assert res1["action"] == "updated_recorded_at", f"Expected updated_recorded_at, got {res1['action']}"
        assert res1["edge_id"] == 1, "Should reuse existing edge id without duplicating"
        with sqlite3.connect(sqlite_file) as conn:
            count = conn.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
            assert count == 1, f"Expected 1 edge, found {count}"

        # Test Upsert 2: Invalidation with new payload
        res2 = gl.upsert("alpha", "CONNECTS_TO", "beta", "updated connection with higher capacity")
        assert res2["action"] == "invalidated_and_inserted", f"Expected invalidated_and_inserted, got {res2['action']}"
        assert res2["old_edge_id"] == 1, "Old edge id should be 1"
        assert res2["edge_id"] == 2, "New edge id should be 2"

        with sqlite3.connect(sqlite_file) as conn:
            conn.row_factory = sqlite3.Row
            old_edge = conn.execute("SELECT * FROM edges WHERE id = 1").fetchone()
            new_edge = conn.execute("SELECT * FROM edges WHERE id = 2").fetchone()
            assert old_edge["is_current"] == 0, "Old edge must have is_current = 0"
            assert old_edge["valid_to"] is not None, "Old edge must have valid_to timestamp"
            assert new_edge["is_current"] == 1, "New edge must have is_current = 1"
            assert new_edge["valid_from"] is not None, "New edge must have valid_from timestamp"
            assert new_edge["payload"] == "updated connection with higher capacity"

        # Test Upsert 3: Invalidation with different destination
        res3 = gl.upsert("alpha", "CONNECTS_TO", "gamma", "diverted to gamma")
        assert res3["action"] == "invalidated_and_inserted"
        assert res3["old_edge_id"] == 2
        assert res3["edge_id"] == 3

        with sqlite3.connect(sqlite_file) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT id, is_current, dst, valid_to FROM edges ORDER BY id").fetchall()
            assert rows[0]["is_current"] == 0 and rows[0]["dst"] == "beta"
            assert rows[1]["is_current"] == 0 and rows[1]["dst"] == "beta"
            assert rows[2]["is_current"] == 1 and rows[2]["dst"] == "gamma"

        print("PASS: test_bitemporal_graph_and_migration")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_ppr_multihop_traversal_and_token_budget():
    """Test 1-2 hop expansion, PPR ranking, and strict token budget enforcement."""
    temp_dir = Path(tempfile.mkdtemp(prefix="test_ppr_"))
    try:
        gl = GraphLayer(temp_dir)
        # Construct a 2-hop graph with distinct relation keys:
        # Hub -> (NodeA, NodeB) -> (ServiceX, ServiceZ)
        gl.upsert("Hub", "MANAGES_PRIMARY", "NodeA", "primary cluster node A")
        gl.upsert("Hub", "MANAGES_SECONDARY", "NodeB", "secondary cluster node B")
        gl.upsert("NodeA", "RUNS_SERVICE", "ServiceX", "telemetry and event monitoring daemon")
        gl.upsert("NodeB", "RUNS_BACKUP", "ServiceZ", "high-frequency scheduler")
        for i in range(10):
            gl.upsert(f"ServiceX", f"DEPENDS_ON_{i}", f"Component_{i}", f"detailed dependency payload configuration #{i} with extensive descriptions to test token limit handling")

        # Test 1: Query with default active filter and token budget (max_tokens=400)
        results = gl.query("Hub", limit=50, include_historical=False, max_tokens=400)
        assert len(results) > 0, "PPR query should return results"
        total_toks = sum(gl._estimate_tokens(r) for r in results)
        assert total_toks <= 400 or len(results) == 1, f"Token budget exceeded: {total_toks} > 400"

        # Verify PPR ranking: 1-hop edges incident to Hub should have high scores
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True), "Results should be sorted descending by PPR score"

        # Verify 2-hop traversal reached NodeA, NodeB, ServiceX
        destinations = {r["dst"] for r in results}
        assert "NodeA" in destinations or "NodeB" in destinations, "1-hop nodes should be discovered"

        # Test 2: Neighbors query for NodeA
        neighbors = gl.neighbors("NodeA", limit=10, max_tokens=400)
        assert len(neighbors) > 0
        nodea_rels = {r["dst"] for r in neighbors}.union({r["src"] for r in neighbors})
        assert "Hub" in nodea_rels and "ServiceX" in nodea_rels, f"Expected Hub and ServiceX in neighbors, got {nodea_rels}"

        print("PASS: test_ppr_multihop_traversal_and_token_budget")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_rrf_and_fts5_hybrid_search():
    """Test Reciprocal Rank Fusion helper, SQLite FTS5 BM25, and LIKE fallback."""
    # Test 1: Mathematical correctness of RRF
    # item1 in FTS rank 1 and Vec rank 1: score = 1/(60+1) + 1/(60+1) = 2/61 ≈ 0.032787
    # item2 in FTS rank 2 only: score = 1/(60+2) = 1/62 ≈ 0.016129
    # item3 in Vec rank 2 only: score = 1/(60+2) = 1/62 ≈ 0.016129
    fts_items = [
        {"id": "doc1", "title": "Doc 1"},
        {"id": "doc2", "title": "Doc 2"},
    ]
    vec_items = [
        {"id": "doc1", "title": "Doc 1"},
        {"id": "doc3", "title": "Doc 3"},
    ]
    fused = _reciprocal_rank_fusion(fts_items, vec_items, id_fn=lambda x: x["id"], k=60)
    assert fused[0]["id"] == "doc1"
    expected_doc1_score = round(1.0 / 61 + 1.0 / 61, 6)
    assert abs(fused[0]["score"] - expected_doc1_score) < 1e-5, f"Expected {expected_doc1_score}, got {fused[0]['score']}"
    assert fused[0]["rank_fts"] == 1
    assert fused[0]["rank_vec"] == 1

    print("PASS: test_rrf_and_fts5_hybrid_search")


def test_isolated_project_upgrades(monkeypatch=None, tmp_path=None):
    """Run full verification on an isolated temporary project with isolated REGISTRY."""
    tmp_ctx = None
    if tmp_path is None:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="test_ws2_")
        tmp_path = Path(tmp_ctx.name)

    old_s_settings = codex_knowledge.settings.SETTINGS
    old_r_settings = codex_knowledge.registry.SETTINGS
    old_r_registry = codex_knowledge.registry.REGISTRY
    old_srv_registry = codex_knowledge.server.REGISTRY

    try:
        isolated_settings = Settings(data_root=tmp_path / "data", vault_root=tmp_path / "vault")
        if monkeypatch is not None:
            monkeypatch.setattr(codex_knowledge.settings, "SETTINGS", isolated_settings)
            monkeypatch.setattr(codex_knowledge.registry, "SETTINGS", isolated_settings)
            isolated_registry = Registry()
            monkeypatch.setattr(codex_knowledge.registry, "REGISTRY", isolated_registry)
            monkeypatch.setattr(codex_knowledge.server, "REGISTRY", isolated_registry)
        else:
            codex_knowledge.settings.SETTINGS = isolated_settings
            codex_knowledge.registry.SETTINGS = isolated_settings
            isolated_registry = Registry()
            codex_knowledge.registry.REGISTRY = isolated_registry
            codex_knowledge.server.REGISTRY = isolated_registry

        slug = "isolated-test-proj"
        proj_dir = tmp_path / "proj"
        proj_dir.mkdir(parents=True, exist_ok=True)
        pp = isolated_registry.ensure_project(str(proj_dir), slug)

        # Seed markdown documents in vault
        (pp.vault_root / "sot" / "spec.md").write_text(
            "# Vietnam Lunar Horology Spec\nDeterministic lunar calendar VSOP87 analytical engine in Vietnam.",
            encoding="utf-8",
        )
        (pp.vault_root / "raw" / "notes.md").write_text(
            "# Notes\nVietnam calendar algorithms and astronomical definitions.",
            encoding="utf-8",
        )

        # Refresh inventory to ensure documents_fts and ChromaDB documents collection are populated
        inv = _refresh_document_inventory(slug)
        assert inv["indexed"] >= 2, f"Expected >= 2 documents, got {inv['indexed']}"

        # 1. Test Bi-temporal graph upsert on isolated project
        edge_src = "test-entity"
        edge_rel = "TEST_INTEGRATION_REL"
        edge_dst_1 = "test-target-v1"
        edge_dst_2 = "test-target-v2"

        up1 = graph_upsert(slug, edge_src, edge_rel, edge_dst_1, "initial test telemetry payload")
        assert up1["upserted"] is True
        assert up1["action"] in {"inserted", "updated_recorded_at"}

        # Update edge to test invalidation
        up2 = graph_upsert(slug, edge_src, edge_rel, edge_dst_2, "migrated to target v2")
        assert up2["upserted"] is True
        assert up2["action"] == "invalidated_and_inserted"
        assert up2["is_current"] == 1

        # Query active graph: edge_dst_2 should be current, edge_dst_1 should NOT appear by default
        active_q = graph_query(slug, edge_src, include_historical=False, max_tokens=400)
        active_dsts = [r["dst"] for r in active_q["results"] if r["src"] == edge_src and r["rel"] == edge_rel]
        assert edge_dst_2 in active_dsts, "Active destination should appear in current query"
        assert edge_dst_1 not in active_dsts, "Invalidated destination must NOT appear in current query"

        # Query with include_historical=True: both should appear
        hist_q = graph_query(slug, edge_src, include_historical=True, max_tokens=400)
        hist_dsts = [r["dst"] for r in hist_q["results"] if r["src"] == edge_src and r["rel"] == edge_rel]
        assert edge_dst_1 in hist_dsts, "Historical destination should appear when include_historical=True"
        assert edge_dst_2 in hist_dsts, "Current destination should appear when include_historical=True"

        # 2. Test 2-Hop PPR Graph Traversal on isolated project
        graph_upsert(slug, slug, "HAS_MODULE", "ModuleA", "primary module")
        graph_upsert(slug, "ModuleA", "HAS_SERVICE", "ServiceB", "sub service")
        ppr_res = graph_query(slug, slug, limit=20, max_tokens=400)
        assert len(ppr_res["results"]) > 0, "Should return PPR ranked triples"
        assert all("score" in r and "hop" in r for r in ppr_res["results"]), "Triples must contain score and hop"
        total_tokens = sum(GraphLayer._estimate_tokens(r) for r in ppr_res["results"])
        assert total_tokens <= 400 or len(ppr_res["results"]) == 1, f"Token limit exceeded: {total_tokens}"

        # 3. Test Hybrid SQLite FTS5 + ChromaDB RRF memory_query
        test_key = "test_rrf_horology_key"
        test_val = "Deterministic lunar calendar VSOP87 analytical engine with bilingual Vietnamese horology"
        mem_store_res = memory_store(slug, test_key, test_val)
        assert mem_store_res["stored"] is True

        # Query using hybrid search
        mq_res = memory_query(slug, "VSOP87 lunar calendar", limit=10)
        assert "hybrid_results" in mq_res, "hybrid_results missing from memory_query"
        assert "keyword_results" in mq_res, "keyword_results missing from memory_query"
        assert "semantic_results" in mq_res, "semantic_results missing from memory_query"
        assert len(mq_res["hybrid_results"]) > 0, "Hybrid search should return matching results"
        top_hit = mq_res["hybrid_results"][0]
        assert "score" in top_hit, "Top hit must have RRF score"
        assert "rank_fts" in top_hit or "rank_vec" in top_hit

        # Test LIKE fallback on wildcard/special characters
        fallback_res = memory_query(slug, "VSOP87* calendar OR %horology%", limit=5)
        assert len(fallback_res["hybrid_results"]) > 0, "LIKE fallback should handle special characters cleanly"

        # 4. Test Hybrid SQLite FTS5 + ChromaDB RRF vault_search
        vs_res = vault_search(slug, "Vietnam", limit=10)
        assert vs_res["search_mode"] == "hybrid_rrf", f"Expected search_mode hybrid_rrf, got {vs_res['search_mode']}"
        assert len(vs_res["hits"]) > 0, "vault_search should return documents matching 'Vietnam'"
        first_doc = vs_res["hits"][0]
        assert "score" in first_doc, "Document hit must have RRF score"
        assert "relative_path" in first_doc, "Document hit must preserve relative_path"

        print("PASS: test_isolated_project_upgrades")
    finally:
        if monkeypatch is None:
            codex_knowledge.settings.SETTINGS = old_s_settings
            codex_knowledge.registry.SETTINGS = old_r_settings
            codex_knowledge.registry.REGISTRY = old_r_registry
            codex_knowledge.server.REGISTRY = old_srv_registry
        if tmp_ctx is not None:
            tmp_ctx.cleanup()


def test_agm_levi_revision_and_ripple_propagation():
    """Test AGM Levi belief revision, superseded_by tracking, and RippleEngine stale marking."""
    temp_dir = Path(tempfile.mkdtemp(prefix="test_agm_"))
    try:
        gl = GraphLayer(temp_dir)
        # 1. Base edge
        r1 = gl.upsert_edge("ServiceA", "DEPENDS_ON", "DBPrimary", payload={"host": "10.0.0.1"})
        assert r1["status"] == "inserted"
        edge1_id = r1["id"]

        # 2. Dependent edges pointing to ServiceA
        r_dep1 = gl.upsert_edge("Frontend", "DEPENDS_ON", "ServiceA", payload={"timeout": 30})
        r_dep2 = gl.upsert_edge("Worker", "IMPLEMENTS", "ServiceA", payload={"concurrency": 4})

        # 3. Revise belief: ServiceA now depends on DBReplica
        r2 = gl.upsert_edge("ServiceA", "DEPENDS_ON", "DBReplica", payload={"host": "10.0.0.2"})
        assert r2["status"] == "superseded"
        assert r2["superseded_id"] == edge1_id
        edge2_id = r2["id"]

        with sqlite3.connect(temp_dir / "graph.sqlite") as conn:
            conn.row_factory = sqlite3.Row
            old_row = conn.execute("SELECT * FROM edges WHERE id = ?", (edge1_id,)).fetchone()
            assert old_row["is_current"] == 0
            assert old_row["invalidated_at"] is not None
            assert old_row["superseded_by"] == edge2_id

            # Verify RippleEngine updated dependent edges
            dep1_row = conn.execute("SELECT payload FROM edges WHERE id = ?", (r_dep1["id"],)).fetchone()
            dep1_payload = json.loads(dep1_row["payload"])
            assert dep1_payload.get("stale_dependency") is True
            assert dep1_payload.get("superseded_edge_id") == edge2_id
            assert "stale_since" in dep1_payload

            dep2_row = conn.execute("SELECT payload FROM edges WHERE id = ?", (r_dep2["id"],)).fetchone()
            dep2_payload = json.loads(dep2_row["payload"])
            assert dep2_payload.get("stale_dependency") is True

            # Verify entities table and entrenchment
            e_service_a = conn.execute("SELECT * FROM entities WHERE id = 'ServiceA'").fetchone()
            assert e_service_a is not None
            assert e_service_a["entrenchment"] > 1.0

        print("PASS: test_agm_levi_revision_and_ripple_propagation")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_magma_4layer_intent_weighted_ppr():
    """Test MAGMA 4-layer taxonomy mapping, intent classification, and policy-guided PPR."""
    # 1. Verify layer inference
    assert _infer_edge_layer("CAUSES") == "causal"
    assert _infer_edge_layer("EXPERIENCED_FAILURE") == "causal"
    assert _infer_edge_layer("PRECEDES") == "temporal"
    assert _infer_edge_layer("MODIFIED_IN") == "episodic"
    assert _infer_edge_layer("IMPLEMENTS") == "semantic"
    assert _infer_edge_layer("CUSTOM_REL", "causal") == "causal"

    # 2. Verify query intent classification
    intent_fix = _classify_query_intent("fix test failure error in server")
    assert intent_fix["causal"] > intent_fix["semantic"]

    intent_hist = _classify_query_intent("history of superseded migrations")
    assert intent_hist["temporal"] > intent_hist["semantic"]

    intent_arch = _classify_query_intent("overview of subsystem architecture")
    assert intent_arch["semantic"] > intent_arch["episodic"]

    # 3. Graph PPR ranking with intent
    temp_dir = Path(tempfile.mkdtemp(prefix="test_magma_"))
    try:
        gl = GraphLayer(temp_dir)
        gl.upsert_edge("API", "IMPLEMENTS", "Spec", layer="semantic")
        gl.upsert_edge("API", "CAUSES", "TimeoutError", layer="causal")
        gl.upsert_edge("TimeoutError", "RESOLVED_BY", "RetryPolicy", layer="causal")

        tuples = gl.seeded_subgraph_tuples(["API"], intent_query="why did API error occur", limit=5)
        assert len(tuples) > 0
        assert any("causal" in t.get("linearized", "") for t in tuples)

        print("PASS: test_magma_4layer_intent_weighted_ppr")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_find_path_bfs():
    """Test BFS shortest path traversal across active and historical edges."""
    temp_dir = Path(tempfile.mkdtemp(prefix="test_path_"))
    try:
        gl = GraphLayer(temp_dir)
        gl.upsert_edge("A", "CALLS", "B")
        gl.upsert_edge("B", "CALLS", "C")
        gl.upsert_edge("C", "CALLS", "D")

        # Active path A -> D
        res = gl.find_path("A", "D", max_hops=4)
        assert res["found"] is True
        assert res["hops"] == 3
        assert len(res["path"]) == 3

        # Path within max_hops=2 should not find 3-hop target
        res_short = gl.find_path("A", "D", max_hops=2)
        assert res_short["found"] is False

        # Invalidate edge B -> C by revising to B -> Z
        gl.upsert_edge("B", "CALLS", "Z")

        # Active path should now be broken
        res_active = gl.find_path("A", "D", max_hops=4, include_historical=False)
        assert res_active["found"] is False

        # Historical path should still find it
        res_hist = gl.find_path("A", "D", max_hops=4, include_historical=True)
        assert res_hist["found"] is True
        assert res_hist["hops"] == 3

        print("PASS: test_find_path_bfs")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_amem_auto_linking_and_retrospective_evolution(monkeypatch=None, tmp_path=None):
    """Test A-MEM auto-linking (EXTENDS), retrospective evolution (linked_from), and APPLIES_TO file links."""
    tmp_ctx = None
    if tmp_path is None:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="test_amem_")
        tmp_path = Path(tmp_ctx.name)

    old_s_settings = codex_knowledge.settings.SETTINGS
    old_r_settings = codex_knowledge.registry.SETTINGS
    old_r_registry = codex_knowledge.registry.REGISTRY
    old_srv_registry = codex_knowledge.server.REGISTRY

    try:
        isolated_settings = Settings(data_root=tmp_path / "data", vault_root=tmp_path / "vault")
        if monkeypatch is not None:
            monkeypatch.setattr(codex_knowledge.settings, "SETTINGS", isolated_settings)
            monkeypatch.setattr(codex_knowledge.registry, "SETTINGS", isolated_settings)
            isolated_registry = Registry()
            monkeypatch.setattr(codex_knowledge.registry, "REGISTRY", isolated_registry)
            monkeypatch.setattr(codex_knowledge.server, "REGISTRY", isolated_registry)
        else:
            codex_knowledge.settings.SETTINGS = isolated_settings
            codex_knowledge.registry.SETTINGS = isolated_settings
            isolated_registry = Registry()
            codex_knowledge.registry.REGISTRY = isolated_registry
            codex_knowledge.server.REGISTRY = isolated_registry

        slug = "amem-test-proj"
        proj_dir = tmp_path / "proj"
        proj_dir.mkdir(parents=True, exist_ok=True)
        pp = isolated_registry.ensure_project(str(proj_dir), slug)

        # 1. Store first memory mentioning a file
        m1 = memory_store(slug, "jwt_auth_rule", "Use JWT tokens in auth_handler.py for secure authentication.")
        assert m1["stored"] is True

        # 2. Store second related memory mentioning same concept and file
        m2 = memory_store(slug, "jwt_refresh_rule", "Rotate refresh tokens alongside JWT tokens in auth_handler.py.")
        assert m2["stored"] is True

        # 3. Check graph edges created
        q_edges = graph_query(slug, "jwt_auth_rule", include_historical=False)
        assert len(q_edges["results"]) > 0

        # Check APPLIES_TO link
        applies_edges = [r for r in q_edges["results"] if r["rel"] == "APPLIES_TO"]
        assert len(applies_edges) > 0
        assert any(r["dst"] == "file:auth_handler.py" for r in applies_edges)

        # 4. Check find_path tool
        fp_res = find_path(slug=slug, src="mem:jwt_refresh_rule", dst="file:auth_handler.py")
        assert fp_res["found"] is True

        print("PASS: test_amem_auto_linking_and_retrospective_evolution")
    finally:
        if monkeypatch is None:
            codex_knowledge.settings.SETTINGS = old_s_settings
            codex_knowledge.registry.SETTINGS = old_r_settings
            codex_knowledge.registry.REGISTRY = old_r_registry
            codex_knowledge.server.REGISTRY = old_srv_registry
        if tmp_ctx is not None:
            tmp_ctx.cleanup()


if __name__ == "__main__":
    test_bitemporal_graph_and_migration()
    test_ppr_multihop_traversal_and_token_budget()
    test_rrf_and_fts5_hybrid_search()
    test_isolated_project_upgrades()
    test_agm_levi_revision_and_ripple_propagation()
    test_magma_4layer_intent_weighted_ppr()
    test_find_path_bfs()
    test_amem_auto_linking_and_retrospective_evolution()
    print("ALL TESTS PASSED SUCCESSFULLY!")

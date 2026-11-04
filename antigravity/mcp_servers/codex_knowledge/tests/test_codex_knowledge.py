from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

from codex_knowledge.registry import REGISTRY
from codex_knowledge.server import (
    _format_context_tier,
    _format_toon,
    batch_knowledge_query,
    graph_neighbors,
    graph_query,
    graph_upsert,
    handoff_write,
    memory_store,
    project_context,
    project_register,
    vault_write,
)


def test_format_toon_helper() -> None:
    rows = [{"id": "item1", "score": 9.5}, {"id": "item2", "score": 8.0}]
    res = _format_toon("test_block", ["id", "score"], rows)
    assert res.startswith("test_block[2]{id,score}:")
    assert "item1 | 9.5" in res
    assert "item2 | 8.0" in res

    empty_res = _format_toon("empty_block", ["col1", "col2"], [])
    assert empty_res == "empty_block[0]{col1,col2}:"


def test_batch_knowledge_query_end_to_end() -> None:
    slug = f"test-batch-{uuid.uuid4().hex[:8]}"
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        proj_dir = tmp / "sample_proj"
        proj_dir.mkdir(parents=True)
        docs_dir = proj_dir / "docs"
        docs_dir.mkdir()
        (docs_dir / "PRD.md").write_text("# Core Requirements\n- Real-time indexing\n", encoding="utf-8")

        try:
            # Register project
            reg = project_register(project_path=str(proj_dir), slug=slug)
            assert reg.get("slug") == slug

            # Populate memory and handoff
            memory_store(slug=slug, key="arch_decision", value="Use SQLite for low latency")
            handoff_write(slug=slug, name="phase1", payload='{"status": "completed"}')

            # 1. Test missing slug error
            err_res = batch_knowledge_query(slug="", project="")
            assert "error" in err_res

            # 2. Test batch execution with steps
            steps = [
                {"op": "project_context", "query": "indexing", "limit": 3},
                {"op": "memory_query", "query": "SQLite", "limit": 5},
                {"op": "graph_query", "query": "requirements", "limit": 5},
                {"op": "vault_search", "query": "Requirements", "limit": 5},
                {"op": "vault_read", "relative_path": "docs/PRD.md"},
                {"op": "handoff_read", "name": "phase1"},
            ]
            res = batch_knowledge_query(slug=slug, steps=steps, output_format="toon")
            assert res.get("slug") == slug
            assert res.get("step_count") == 6
            assert res.get("format") == "toon"
            assert len(res.get("results", [])) == 6
            assert "toon" in res
            assert "step_1_project_context" in res["toon"]
            assert "step_2_memory" in res["toon"]
            assert "step_4_vault_search" in res["toon"]
            assert "step_5_vault_read" in res["toon"]
            assert "step_6_handoff_read" in res["toon"]

            # 3. Test default steps
            def_res = batch_knowledge_query(slug=slug, steps=None)
            assert def_res.get("step_count") == 3
            assert len(def_res.get("results", [])) == 3
        finally:
            try:
                with REGISTRY._conn() as conn:  # type: ignore[attr-defined]
                    conn.execute("DELETE FROM memory WHERE slug = ?", (slug,))
                    conn.execute("DELETE FROM handoffs WHERE slug = ?", (slug,))
                    conn.execute("DELETE FROM projects WHERE slug = ?", (slug,))
                    conn.execute("DELETE FROM documents WHERE slug = ?", (slug,))
            except Exception:
                pass


def test_openviking_tiered_context_and_graphify_provenance() -> None:
    slug = f"test-tier-{uuid.uuid4().hex[:8]}"
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        proj_dir = tmp / "tiered_proj"
        proj_dir.mkdir(parents=True)
        docs_dir = proj_dir / "docs"
        docs_dir.mkdir()
        long_doc = (
            "# System Architecture\n"
            "This system implements tiered context disclosure and explicit edge provenance across MCP servers. "
            "Additional narrative details follow in subsequent paragraphs.\n"
            "## Key Invariants\n"
            "- Tier L0 provides a compact abstract under 240 chars\n"
            "- Tier L1 provides headings and bullet points under 1200 chars\n"
            "- Tier L2 provides full retrieved context\n"
            + ("Detailed architectural prose line with extra padding for L2.\n" * 30)
        )
        (docs_dir / "ARCHITECTURE.md").write_text(long_doc, encoding="utf-8")

        try:
            project_register(project_path=str(proj_dir), slug=slug)
            graph_upsert(slug=slug, src="ServiceA", rel="DEPENDS_ON", dst="ServiceB", payload="direct AST dependency")
            graph_upsert(slug=slug, src="ServiceB", rel="DEPENDS_ON", dst="ServiceC", payload="transitive dependency")

            # Verify helper _format_context_tier
            t_l0 = _format_context_tier(long_doc, "L0")
            t_l1 = _format_context_tier(long_doc, "L1")
            t_l2 = _format_context_tier(long_doc, "L2")
            assert len(t_l0) <= 240
            assert len(t_l1) <= 1200
            assert len(t_l0) < len(t_l1) < len(t_l2)

            # Verify project_context tiers L0, L1, and default L2
            ctx_l0 = project_context(slug=slug, query="Architecture", tier="L0")
            ctx_l1 = project_context(slug=slug, query="Architecture", tier="L1")
            ctx_l2 = project_context(slug=slug, query="Architecture")

            assert ctx_l0["context_tier"] == "L0"
            assert ctx_l1["context_tier"] == "L1"
            assert ctx_l2["context_tier"] == "L2"
            assert len(ctx_l0["wiki_hits"][0]["excerpt"]) <= 240
            assert len(ctx_l1["wiki_hits"][0]["excerpt"]) <= 1200
            assert len(ctx_l2["wiki_hits"][0]["excerpt"]) > len(ctx_l1["wiki_hits"][0]["excerpt"])

            # Verify Graphify provenance in graph_query and graph_neighbors
            gq = graph_query(slug=slug, term="ServiceA")
            assert gq.get("edge_provenance_model") == "graphify-v1"
            assert len(gq.get("results", [])) >= 1
            for edge in gq["results"]:
                assert edge.get("provenance") in ("EXTRACTED", "INFERRED")

            gn = graph_neighbors(slug=slug, entity_id="ServiceA")
            assert gn.get("edge_provenance_model") == "graphify-v1"
            assert len(gn.get("results", [])) >= 1
            by_dst = {e["dst"]: e["provenance"] for e in gn["results"]}
            assert by_dst.get("ServiceB") == "EXTRACTED"
            if "ServiceC" in by_dst:
                assert by_dst["ServiceC"] == "INFERRED"
        finally:
            try:
                conn_fn = getattr(REGISTRY, "_conn")
                with conn_fn() as conn:
                    conn.execute("DELETE FROM memory WHERE slug = ?", (slug,))
                    conn.execute("DELETE FROM handoffs WHERE slug = ?", (slug,))
                    conn.execute("DELETE FROM projects WHERE slug = ?", (slug,))
                    conn.execute("DELETE FROM documents WHERE slug = ?", (slug,))
            except Exception:
                pass



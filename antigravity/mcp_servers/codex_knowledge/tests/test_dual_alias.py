from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import codex_knowledge.registry
import codex_knowledge.server
import codex_knowledge.settings
from codex_knowledge.registry import Registry
from codex_knowledge.server import (
    graph_neighbors,
    graph_query,
    graph_upsert,
    handoff_checkpoint,
    memory_query,
    memory_store,
    project_context,
    project_index,
)
from codex_knowledge.settings import Settings


def test_dual_alias_support(monkeypatch=None, tmp_path=None):
    tmp_ctx = None
    if tmp_path is None:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="test_alias_")
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

        proj_dir = tmp_path / "proj"
        proj_dir.mkdir(parents=True, exist_ok=True)
        slug = f"test-alias-{uuid.uuid4().hex[:8]}"
        pp = isolated_registry.ensure_project(str(proj_dir), slug)

        # 1. project_index: canonical slug vs alias project
        res_slug = project_index(slug=slug)
        assert res_slug.get("slug") == slug
        res_proj = project_index(project=slug)
        assert res_proj.get("slug") == slug

        # 2. memory_store: slug/key/value vs project/title/content
        ms1 = memory_store(slug=slug, key="rule1", value="Value 1")
        assert ms1.get("stored") is True
        ms2 = memory_store(project=slug, title="rule2", content="Content 2")
        assert ms2.get("stored") is True
        assert ms2.get("key") == "rule2"

        # 3. memory_query: canonical slug vs alias project
        mq1 = memory_query(slug=slug, query="Value")
        assert len(mq1.get("keyword_results", [])) >= 1
        mq2 = memory_query(project=slug, query="Content")
        assert len(mq2.get("keyword_results", [])) >= 1

        # 4. graph_upsert: canonical slug vs alias project
        gu1 = graph_upsert(slug=slug, src="A", rel="LINKS", dst="B", payload="test1")
        assert gu1.get("upserted") is True
        gu2 = graph_upsert(project=slug, src="B", rel="LINKS", dst="C", payload="test2")
        assert gu2.get("upserted") is True

        # 5. graph_query: term vs query, slug vs project
        gq1 = graph_query(slug=slug, term="A")
        assert "results" in gq1
        gq2 = graph_query(project=slug, query="B")
        assert "results" in gq2

        # 6. graph_neighbors: entity_id vs entity, slug vs project
        gn1 = graph_neighbors(slug=slug, entity_id="B")
        assert "results" in gn1
        gn2 = graph_neighbors(project=slug, entity="B")
        assert "results" in gn2

        # 7. handoff_checkpoint: canonical slug vs alias project
        hc1 = handoff_checkpoint(slug=slug, name="phase1", payload="summary 1")
        assert hc1.get("checkpoint_saved") is True
        hc2 = handoff_checkpoint(project=slug, name="phase2", payload="summary 2")
        assert hc2.get("checkpoint_saved") is True

        # 8. project_context: canonical slug vs alias project
        pc1 = project_context(slug=slug, query="rule")
        assert pc1.get("slug") == slug
        pc2 = project_context(project=slug, query="rule")
        assert pc2.get("slug") == slug

    finally:
        if monkeypatch is None:
            codex_knowledge.settings.SETTINGS = old_s_settings
            codex_knowledge.registry.SETTINGS = old_r_settings
            codex_knowledge.registry.REGISTRY = old_r_registry
            codex_knowledge.server.REGISTRY = old_srv_registry
        if tmp_ctx is not None:
            tmp_ctx.cleanup()


if __name__ == "__main__":
    test_dual_alias_support()
    print("PASS: test_dual_alias_support")

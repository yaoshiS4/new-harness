from __future__ import annotations

import importlib
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
for _mod_name in list(sys.modules):
    if _mod_name == "codex_knowledge" or _mod_name.startswith("codex_knowledge."):
        del sys.modules[_mod_name]

from codex_knowledge.registry import REGISTRY
from codex_knowledge.server import (
    orchestration_lesson,
    project_register,
    settings_review_queue,
)


def test_settings_review_queue_rubric_scoring_and_auto_resolution() -> None:
    slug = f"test-review-{uuid.uuid4().hex[:8]}"
    with tempfile.TemporaryDirectory() as tmpdir:
        proj_dir = Path(tmpdir) / "review_proj"
        proj_dir.mkdir(parents=True)

        try:
            project_register(project_path=str(proj_dir), slug=slug)

            res1 = orchestration_lesson(
                slug=slug,
                category="routing",
                severity="critical",
                summary="High latency on initial route",
                source_ref="trace:1",
            )
            assert res1["settings_review_required"] is True
            rev1_id = int(res1["settings_review"]["id"])

            res2 = orchestration_lesson(
                slug=slug,
                category="token_budget",
                severity="critical",
                summary="Repeated read slice overflow",
                source_ref="trace:2",
            )
            assert res2["settings_review_required"] is True
            rev2_id = int(res2["settings_review"]["id"])

            upd1 = settings_review_queue(
                slug=slug,
                include_resolved=False,
                review_id=rev1_id,
                rubric_scores={
                    "intent_match": 0.4,
                    "trajectory_optimality": 0.3,
                    "token_economy": 0.5,
                },
                resolution_note="Needs additional routing refinement",
            )
            assert "updated_review" in upd1
            assert upd1["updated_review"]["resolved_at"] is None
            assert upd1["updated_review"]["resolution_note"] == "Needs additional routing refinement"
            assert upd1["updated_review"]["rubric_scores"]["intent_match"] == 0.4
            assert upd1["updated_review"]["priority_score"] > 0.0

            open_reviews = upd1["reviews"]
            assert len(open_reviews) == 2
            assert open_reviews[0]["id"] == rev1_id
            assert open_reviews[0]["priority_score"] >= open_reviews[1]["priority_score"]

            upd2 = settings_review_queue(
                slug=slug,
                include_resolved=False,
                review_id=rev2_id,
                rubric_scores={
                    "intent_match": 0.85,
                    "trajectory_optimality": 0.9,
                    "token_economy": 0.75,
                },
                resolution_note="All three rubric thresholds satisfied",
            )
            assert "updated_review" in upd2
            assert upd2["updated_review"]["resolved_at"] is not None
            assert upd2["updated_review"]["resolution_note"] == "All three rubric thresholds satisfied"

            remaining_open = [r["id"] for r in upd2["reviews"]]
            assert rev2_id not in remaining_open
            assert rev1_id in remaining_open

            all_q = settings_review_queue(slug=slug, include_resolved=True)
            all_ids = [r["id"] for r in all_q["reviews"]]
            assert rev1_id in all_ids
            assert rev2_id in all_ids
        finally:
            conn_fn = getattr(REGISTRY, "_conn")
            with conn_fn() as conn:
                conn.execute("DELETE FROM settings_reviews WHERE slug = ?", (slug,))
                conn.execute("DELETE FROM orchestration_events WHERE slug = ?", (slug,))
                conn.execute("DELETE FROM memory WHERE slug = ?", (slug,))
                conn.execute("DELETE FROM projects WHERE slug = ?", (slug,))
                conn.execute("DELETE FROM documents WHERE slug = ?", (slug,))

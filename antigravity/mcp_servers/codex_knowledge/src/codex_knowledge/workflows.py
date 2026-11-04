from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict

from .registry import REGISTRY


class FlowState(TypedDict, total=False):
    slug: str
    source_path: str
    result: dict[str, Any]


@dataclass
class WorkflowEngine:
    """LangGraph orchestration hooks with safe fallback if unavailable."""

    enabled: bool

    @classmethod
    def create(cls) -> "WorkflowEngine":
        try:
            import langgraph  # noqa: F401
            return cls(enabled=True)
        except Exception:
            return cls(enabled=False)

    def run_wiki_ingest(self, slug: str, source_path: str, ingest_fn, rebuild_fn) -> dict[str, Any]:
        # Keep behavior deterministic; use LangGraph presence as capability marker.
        ingest_result = ingest_fn(slug, source_path)
        rebuild_result = rebuild_fn(slug)
        return {
            "langgraph_enabled": self.enabled,
            "ingest": ingest_result,
            "rebuild": rebuild_result,
        }


ENGINE = WorkflowEngine.create()

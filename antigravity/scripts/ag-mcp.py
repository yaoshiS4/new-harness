#!/usr/bin/env python3
"""Standalone Code Mode for MCP CLI & Python SDK Bridge (Harness² CodeAct Protocol).

Modeled on CodeAct (arXiv:2402.01030), Program-Aided Language Models (PAL, arXiv:2211.10435),
and ViperGPT (arXiv:2303.08128), this bridge allows running multi-step MCP operations
programmatically in-memory within a single turn, eliminating conversational round-trip ping-pong
and high-frequency read slice looping.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

WRITE_TOOLS: frozenset[str] = frozenset({
    "memory_store",
    "vault_write",
    "wiki_ingest",
    "wiki_rebuild",
    "graph_upsert",
    "checkpoint_save",
    "handoff_write",
    "handoff_checkpoint",
    "commit_context_ledger",
    "knowledge_capture",
    "orchestration_lesson",
    "project_register",
    "project_index",
})


def _setup_mcp_paths() -> None:
    """Ensure in-process MCP server packages and their virtualenv dependencies are discoverable."""
    curr = Path(__file__).resolve()
    # Find venv python if current python lacks mcp
    venv_py_candidates = [
        curr.parent.parent / "mcp_servers" / "codegraph" / ".venv" / "bin" / "python",
        Path("~/.gemini/antigravity/mcp_servers/codegraph/.venv/bin/python").expanduser(),
    ]
    venv_py = next((str(p) for p in venv_py_candidates if p.is_file() and os.access(p, os.X_OK)), None)
    if venv_py and os.environ.get("_AG_MCP_REEXEC") != "1":
        try:
            import mcp  # noqa: F401
        except Exception:
            os.environ["_AG_MCP_REEXEC"] = "1"
            os.execv(venv_py, [venv_py] + sys.argv)

    # Put local repository candidate first on sys.path
    candidates = [
        Path("~/.gemini/antigravity/mcp_servers").expanduser(),
        curr.parent.parent / "mcp_servers",
    ]
    for c in candidates:
        if c.is_dir():
            for srv_name in ("codegraph", "codex_knowledge", "context_health"):
                srv_dir = c / srv_name
                pkg_dir = srv_dir / "src" if srv_name == "codex_knowledge" else srv_dir
                if pkg_dir.is_dir():
                    if str(pkg_dir) in sys.path:
                        sys.path.remove(str(pkg_dir))
                    sys.path.insert(0, str(pkg_dir))


_setup_mcp_paths()


class AgMcpClient:
    """In-process Python SDK client for Code-Mode MCP batch execution."""

    WRITE_TOOLS = WRITE_TOOLS

    def __init__(self) -> None:
        _setup_mcp_paths()
        self._cg = None
        self._ck = None
        self._ch = None
        self._code_mode_active: bool = False
        self._code_mode_allow_write: bool = False
        self._code_mode_records: list[dict[str, Any]] | None = None

    @property
    def codegraph(self):
        if self._cg is None:
            import codegraph.server as cg_server
            self._cg = cg_server
        return self._cg

    @property
    def codex_knowledge(self):
        if self._ck is None:
            import codex_knowledge.server as ck_server
            self._ck = ck_server
        return self._ck

    @property
    def context_health(self):
        if self._ch is None:
            import context_health.server as ch_server
            self._ch = ch_server
        return self._ch

    def call_tool(
        self,
        server: str,
        tool: str,
        args: dict[str, Any] | None = None,
        allow_write: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Invoke an in-process MCP tool with a read-only default fence against write tools."""
        effective_allow_write = (
            self._code_mode_allow_write if self._code_mode_active else allow_write
        )
        call_args: dict[str, Any] = {}
        if args:
            call_args.update(args)
        if kwargs:
            call_args.update(kwargs)

        if tool in WRITE_TOOLS and not effective_allow_write:
            raise PermissionError(
                f"Write tool '{tool}' on server '{server}' is blocked in read-only mode (set allow_write=True to permit)."
            )
        if not effective_allow_write and tool == "settings_review_queue":
            if any(
                call_args.get(k) not in (None, "", {}, [])
                for k in ("review_id", "rubric_scores", "resolution_note")
            ):
                raise PermissionError(
                    "Mutating settings_review_queue is blocked in read-only mode (set allow_write=True to permit)."
                )

        if server not in ("codegraph", "codex_knowledge", "context_health"):
            raise ValueError(f"Unknown MCP server: {server}")

        srv_mod = getattr(self, server)
        fn = getattr(srv_mod, tool, None)
        if fn is None or not callable(fn):
            raise AttributeError(f"Unknown tool '{tool}' on server '{server}'")

        res = fn(**call_args)
        if self._code_mode_active and self._code_mode_records is not None:
            self._code_mode_records.append(
                {
                    "tool_name": f"{server}.{tool}",
                    "content": res,
                }
            )
        return res

    def execute_code_mode(
        self,
        code: str,
        allow_write: bool = False,
        max_single_chars: int = 6000,
        max_batch_chars: int = 12000,
    ) -> dict[str, Any]:
        """Execute multi-step Python code with injected MCP bindings and dual-threshold batch spillover."""
        records: list[dict[str, Any]] = []
        stdout_buf = io.StringIO()

        def _injected_call_tool(
            server: str,
            tool: str,
            args: dict[str, Any] | None = None,
            **kwargs: Any,
        ) -> Any:
            return self.call_tool(
                server=server,
                tool=tool,
                args=args,
                allow_write=allow_write,
                **kwargs,
            )

        exec_globals: dict[str, Any] = {
            "__builtins__": __builtins__,
            "mcp": self,
            "client": self,
            "call_tool": _injected_call_tool,
            "json": json,
            "Path": Path,
        }

        prev_active = self._code_mode_active
        prev_allow = self._code_mode_allow_write
        prev_records = self._code_mode_records
        self._code_mode_active = True
        self._code_mode_allow_write = allow_write
        self._code_mode_records = records
        try:
            with contextlib.redirect_stdout(stdout_buf):
                exec(code, exec_globals)
        finally:
            self._code_mode_active = prev_active
            self._code_mode_allow_write = prev_allow
            self._code_mode_records = prev_records

        stdout_str = stdout_buf.getvalue()
        batch_spill = self.context_health.spillover_batch(
            payloads=records,
            max_single_chars=max_single_chars,
            max_batch_chars=max_batch_chars,
        )

        rows: list[dict[str, Any]] = []
        for idx, item in enumerate(batch_spill.get("items", [])):
            chars_val = item.get("chars", item.get("original_chars", 0))
            rows.append(
                {
                    "tool": item.get("tool_name", f"call_{idx}"),
                    "status": item.get("status", "unknown"),
                    "chars": chars_val,
                    "schema": item.get("schema", ""),
                    "spillover_path": item.get("spillover_path", "-"),
                }
            )
        toon = self.codegraph._format_toon(
            "code_mode_calls",
            ["tool", "status", "chars", "schema", "spillover_path"],
            rows,
        )
        if stdout_str.strip():
            toon = f"{toon}\nstdout:\n{stdout_str.rstrip()}"

        return {
            "status": "ok",
            "allow_write": allow_write,
            "call_count": len(records),
            "stdout": stdout_str,
            "result": exec_globals.get("result"),
            "batch_spillover": batch_spill,
            "items": batch_spill.get("items", []),
            "spilled_count": batch_spill.get("spilled_count", 0),
            "total_original_chars": batch_spill.get("total_original_chars", 0),
            "total_inline_chars": batch_spill.get("total_inline_chars", 0),
            "toon": toon,
        }

    def codegraph_batch(
        self,
        root: str,
        symbol: str,
        limit: int = 20,
        output_format: str = "toon",
    ) -> dict[str, Any]:
        """Execute 1-shot pipeline: symbol_lookup -> callers_callees -> impact_analysis."""
        steps = [
            {"op": "symbol_lookup", "query": symbol, "limit": limit},
            {"op": "callers_callees", "from_prev": True, "limit": limit},
            {"op": "impact_analysis", "from_prev": True, "limit": limit},
        ]
        return self.codegraph.batch_query(root=root, steps=steps, output_format=output_format)

    def codegraph_extract(
        self,
        root: str,
        path: str,
        symbols: list[str],
        max_total_lines: int = 250,
    ) -> dict[str, Any]:
        """Extract multi-symbol AST slices in a single shot without circuit breakers."""
        return self.codegraph.extract_symbols(
            root=root, path=path, symbols=symbols, max_total_lines=max_total_lines
        )

    def knowledge_bundle(
        self,
        slug: str,
        query: str = "",
        limit: int = 5,
        output_format: str = "toon",
    ) -> dict[str, Any]:
        """Execute 1-shot layered knowledge retrieval: context + memory + graph."""
        steps = [
            {"op": "project_context", "query": query, "limit": limit},
            {"op": "memory_query", "query": query, "limit": limit},
            {"op": "graph_query", "query": query, "limit": limit},
        ]
        return self.codex_knowledge.batch_knowledge_query(
            slug=slug, steps=steps, output_format=output_format
        )

    def spillover_payload(
        self,
        content: str,
        tool_name: str = "mcp",
        max_chars: int = 6000,
    ) -> dict[str, Any]:
        """Offload large payload to disk and return compact TOON summary pointer."""
        return self.context_health.spillover_large_payload(
            content=content, tool_name=tool_name, max_chars=max_chars
        )


def run_self_test() -> int:
    """Run deterministic self-test verifying TOON formatting, batch pipeline, and spillover."""
    print(">>> [AgMcpClient] Running self-test...")
    client = AgMcpClient()

    # 1. Test TOON formatter
    rows = [{"sym": "alpha", "line": 10}, {"sym": "beta", "line": 42}]
    toon = client.codegraph._format_toon("test_block", ["sym", "line"], rows)
    assert toon.startswith("test_block[2]{sym,line}:"), f"Invalid TOON header: {toon}"
    assert "alpha | 10" in toon
    assert "beta | 42" in toon
    print("  [PASS] TOON formatting verified.")

    # 2. Test spillover protection
    small_data = {"key": "val", "num": 123}
    inline_res = client.codegraph._maybe_spillover(small_data, max_chars=500)
    assert "spillover_path" not in inline_res, "Small data should not spill over"

    large_data = {"data": "X" * 12000, "results": [{"idx": i} for i in range(20)]}
    spilled_res = client.codegraph._maybe_spillover(large_data, max_chars=1000)
    assert "spillover_path" in spilled_res, "Large data must spill over"
    spill_p = Path(spilled_res["spillover_path"])
    assert spill_p.is_file(), f"Spillover file must exist: {spill_p}"
    spill_p.unlink(missing_ok=True)
    print("  [PASS] Spillover file protection verified.")

    # 3. Test codegraph batch pipeline in temporary workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        code_file = tmp / "example.py"
        code_file.write_text(
            """def compute_total(a, b):
    return a + b

def run_calculation():
    val = compute_total(5, 10)
    return val
""",
            encoding="utf-8",
        )

        # Test extract_symbols
        ext = client.codegraph_extract(
            root=str(tmp),
            path="example.py",
            symbols=["compute_total", "run_calculation"],
            max_total_lines=250,
        )
        assert ext.get("count") == 2, f"Expected 2 extracted symbols, got {ext.get('count')}"
        assert len(ext.get("extracted", [])) == 2
        assert "compute_total" in ext.get("toon", "")

        # Test batch query
        batch_res = client.codegraph_batch(
            root=str(tmp),
            symbol="compute_total",
            limit=5,
            output_format="toon",
        )
        assert batch_res.get("step_count") == 3, f"Expected 3 steps, got {batch_res.get('step_count')}"
        assert "toon" in batch_res
        assert len(batch_res.get("results", [])) == 3
        print("  [PASS] In-memory batch query pipeline and AST extraction verified.")

        # 4. Test call_tool & @write guardrail
        lookup_res = client.call_tool(
            "codegraph",
            "symbol_lookup",
            {"root": str(tmp), "query": "compute_total", "limit": 5},
        )
        assert lookup_res.get("count", 0) >= 1
        try:
            client.call_tool(
                "context_health",
                "commit_context_ledger",
                {
                    "milestone": "test",
                    "goals_completed": [],
                    "files_modified": [],
                    "active_constraints": [],
                    "project_dir": str(tmp),
                },
                allow_write=False,
            )
            raise AssertionError("Expected PermissionError for write tool when allow_write=False")
        except PermissionError:
            pass

        # 5. Test execute_code_mode across codegraph + context_health and @write enforcement
        cm_script = f"""
r1 = call_tool("codegraph", "symbol_lookup", {{"root": {str(tmp)!r}, "query": "compute_total", "limit": 5}})
r2 = mcp.call_tool("context_health", "spillover_large_payload", {{"content": "Z" * 100, "tool_name": "cm_test", "max_chars": 500}})
print("FOUND:", r1.get("count"))
result = r1.get("count", 0)
"""
        cm_res = client.execute_code_mode(cm_script, allow_write=False)
        assert cm_res["status"] == "ok"
        assert cm_res["call_count"] == 2
        assert "FOUND:" in cm_res["stdout"]
        assert "code_mode_calls[2]{tool,status,chars,schema,spillover_path}:" in cm_res["toon"]

        try:
            client.execute_code_mode(
                f'call_tool("context_health", "commit_context_ledger", {{"milestone": "m", "goals_completed": [], "files_modified": [], "active_constraints": [], "project_dir": {str(tmp)!r}}})',
                allow_write=False,
            )
            raise AssertionError("Expected PermissionError in execute_code_mode with allow_write=False")
        except PermissionError:
            pass

        cm_write_res = client.execute_code_mode(
            f'call_tool("context_health", "commit_context_ledger", {{"milestone": "m", "goals_completed": ["g1"], "files_modified": ["example.py"], "active_constraints": ["c1"], "project_dir": {str(tmp)!r}}})',
            allow_write=True,
        )
        assert cm_write_res["status"] == "ok"
        assert cm_write_res["call_count"] == 1
        print("  [PASS] Cross-MCP code-mode and @write fence verified.")

    print(">>> [AgMcpClient] ALL SELF-TESTS PASSED (100% Verified).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Code Mode for MCP CLI & Python SDK Bridge")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic self-test")
    subparsers = parser.add_subparsers(dest="subcommand", help="Target subsystem")

    # codegraph subparser
    cg_parser = subparsers.add_parser("codegraph", help="CodeGraph operations")
    cg_subs = cg_parser.add_subparsers(dest="cg_action")

    # codegraph batch
    batch_p = cg_subs.add_parser("batch", help="1-shot pipeline: lookup -> callers -> impact")
    batch_p.add_argument("--root", default=".", help="Workspace root path")
    batch_p.add_argument("--symbol", required=True, help="Target symbol name")
    batch_p.add_argument("--limit", type=int, default=20, help="Per-operation limit")
    batch_p.add_argument("--format", default="toon", choices=["toon", "json"], help="Output format")

    # codegraph extract
    ext_p = cg_subs.add_parser("extract", help="Multi-symbol AST extraction")
    ext_p.add_argument("--root", default=".", help="Workspace root path")
    ext_p.add_argument("--path", required=True, help="File path")
    ext_p.add_argument("--symbols", required=True, help="Comma-separated symbol names")
    ext_p.add_argument("--max-lines", type=int, default=250, help="Maximum total lines")

    # knowledge subparser
    ck_parser = subparsers.add_parser("knowledge", help="Codex Knowledge operations")
    ck_subs = ck_parser.add_subparsers(dest="ck_action")

    # knowledge bundle
    bundle_p = ck_subs.add_parser("bundle", help="1-shot knowledge bundle: context + memory + graph")
    bundle_p.add_argument("--slug", required=True, help="Project slug")
    bundle_p.add_argument("--query", default="", help="Search query")
    bundle_p.add_argument("--limit", type=int, default=5, help="Result limit")
    bundle_p.add_argument("--format", default="toon", choices=["toon", "json"], help="Output format")

    # code-mode subparser
    cm_parser = subparsers.add_parser("code-mode", help="Execute cross-MCP Python code in a single turn")
    cm_group = cm_parser.add_mutually_exclusive_group(required=True)
    cm_group.add_argument("--code", help="Inline Python code to execute")
    cm_group.add_argument("--file", help="Path to Python script file to execute")
    cm_parser.add_argument("--allow-write", action="store_true", help="Permit state-mutating MCP write tools")
    cm_parser.add_argument("--max-single-chars", type=int, default=6000, help="Single payload spillover threshold")
    cm_parser.add_argument("--max-batch-chars", type=int, default=12000, help="Combined batch inline threshold")
    cm_parser.add_argument("--format", default="toon", choices=["toon", "json"], help="Output format")

    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    client = AgMcpClient()

    if args.subcommand == "codegraph":
        if args.cg_action == "batch":
            res = client.codegraph_batch(
                root=args.root,
                symbol=args.symbol,
                limit=args.limit,
                output_format=args.format,
            )
            if args.format == "toon":
                print(res.get("toon", ""))
            else:
                print(json.dumps(res, indent=2))
            return 0
        elif args.cg_action == "extract":
            sym_list = [s.strip() for s in args.symbols.split(",") if s.strip()]
            res = client.codegraph_extract(
                root=args.root,
                path=args.path,
                symbols=sym_list,
                max_total_lines=args.max_lines,
            )
            print(res.get("toon", ""))
            return 0
        else:
            cg_parser.print_help()
            return 1

    elif args.subcommand == "knowledge":
        if args.ck_action == "bundle":
            res = client.knowledge_bundle(
                slug=args.slug,
                query=args.query,
                limit=args.limit,
                output_format=args.format,
            )
            if args.format == "toon":
                print(res.get("toon", ""))
            else:
                print(json.dumps(res, indent=2))
            return 0
        else:
            ck_parser.print_help()
            return 1

    elif args.subcommand == "code-mode":
        code_str = (
            args.code
            if args.code is not None
            else Path(args.file).expanduser().read_text(encoding="utf-8")
        )
        res = client.execute_code_mode(
            code=code_str,
            allow_write=args.allow_write,
            max_single_chars=args.max_single_chars,
            max_batch_chars=args.max_batch_chars,
        )
        if args.format == "toon":
            print(res.get("toon", ""))
        else:
            print(json.dumps(res, indent=2, default=str))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

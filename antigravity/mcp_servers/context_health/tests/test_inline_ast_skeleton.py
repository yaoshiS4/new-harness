import json
import os
from pathlib import Path
import subprocess
import tempfile


def test_inline_ast_skeleton_on_monolithic_files():
    repo_hook = Path(__file__).resolve().parents[4] / "config" / "hooks" / "pre_tool_use_hook.py"
    hook_path = str(repo_hook) if repo_hook.is_file() else os.path.expanduser("~/.gemini/config/hooks/pre_tool_use_hook.py")

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Create a >400-line Python file
        py_path = os.path.join(tmpdir, "large_service.py")
        py_lines = [
            "import os",
            "import sys",
            "",
            "class UserService:",
            "    def __init__(self):",
            "        self.users = []",
            "",
            "    def get_user_by_id(self, user_id: int):",
            "        return None",
            "",
            "    async def fetch_remote_user(self, url: str):",
            "        return {'id': 1}",
            "",
            "def calculate_metrics():",
            "    return 42",
            "",
        ]
        # Pad to > 400 lines
        while len(py_lines) < 450:
            py_lines.append(f"# line padding {len(py_lines)}")

        with open(py_path, "w", encoding="utf-8") as f:
            f.write("\n".join(py_lines))

        # Test view_file on large Python file without StartLine/EndLine
        payload_py = {
            "workspacePaths": [tmpdir],
            "toolCall": {
                "name": "view_file",
                "args": {
                    "AbsolutePath": py_path,
                },
            },
        }

        p = subprocess.run(
            ["python3", hook_path],
            input=json.dumps(payload_py),
            text=True,
            capture_output=True,
        )
        assert p.returncode == 0
        res_py = json.loads(p.stdout.strip())
        assert res_py.get("decision") == "deny"
        reason_py = res_py.get("reason", "")
        print("=== Python Monolithic Denial Reason ===")
        print(reason_py)
        print("=======================================")

        assert "Outline-First Monolithic File Guard" in reason_py
        assert "Inline AST Symbol Skeleton for `large_service.py`" in reason_py
        assert "class UserService [L4-" in reason_py
        assert "def get_user_by_id() [L8-" in reason_py
        assert "async def fetch_remote_user() [L11-" in reason_py
        assert "def calculate_metrics() [L14-" in reason_py
        assert "Read your target symbol directly using" in reason_py
        assert "with `StartLine` and `EndLine`" in reason_py

        # 2. Create a >400-line TypeScript file
        ts_path = os.path.join(tmpdir, "LargeComponent.tsx")
        ts_lines = [
            "import React from 'react';",
            "",
            "export interface LargeComponentProps {",
            "  title: string;",
            "  count: number;",
            "}",
            "",
            "export function formatTitle(title: string) {",
            "  return title.trim();",
            "}",
            "",
            "export class ComponentController {",
            "  render() { return null; }",
            "}",
            "",
            "export const DefaultSettings = {",
            "  theme: 'dark'",
            "};",
            "",
        ]
        while len(ts_lines) < 450:
            ts_lines.append(f"// padding line {len(ts_lines)}")

        with open(ts_path, "w", encoding="utf-8") as f:
            f.write("\n".join(ts_lines))

        payload_ts = {
            "workspacePaths": [tmpdir],
            "toolCall": {
                "name": "view_file",
                "args": {
                    "AbsolutePath": ts_path,
                },
            },
        }

        p2 = subprocess.run(
            ["python3", hook_path],
            input=json.dumps(payload_ts),
            text=True,
            capture_output=True,
        )
        assert p2.returncode == 0
        res_ts = json.loads(p2.stdout.strip())
        assert res_ts.get("decision") == "deny"
        reason_ts = res_ts.get("reason", "")
        print("=== TypeScript Monolithic Denial Reason ===")
        print(reason_ts)
        print("==========================================")

        assert "Outline-First Monolithic File Guard" in reason_ts
        assert "Inline AST Symbol Skeleton for `LargeComponent.tsx`" in reason_ts
        assert "export interface LargeComponentProps [L3-" in reason_ts
        assert "export function formatTitle [L8-" in reason_ts
        assert "export class ComponentController [L12-" in reason_ts
        assert "export const DefaultSettings [L16-" in reason_ts

        print("ALL INLINE AST SKELETON TESTS PASSED!")


if __name__ == "__main__":
    test_inline_ast_skeleton_on_monolithic_files()

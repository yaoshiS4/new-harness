import json
import os
from pathlib import Path
import subprocess
import tempfile
import time


def test_shift_left_ast_import_verification():
    repo_hook = Path(__file__).resolve().parents[4] / "config" / "hooks" / "pre_tool_use_hook.py"
    hook_path = str(repo_hook) if repo_hook.is_file() else os.path.expanduser("~/.gemini/config/hooks/pre_tool_use_hook.py")

    test_base = os.path.join(tempfile.gettempdir(), ".tmp_test_ast")
    if os.path.exists(test_base):
        import shutil
        shutil.rmtree(test_base, ignore_errors=True)
    os.makedirs(test_base, exist_ok=True)
    try:
        tmpdir = test_base
        # Set up mock package
        pkg_dir = os.path.join(tmpdir, "my-pkg")
        src_dir = os.path.join(pkg_dir, "src")
        os.makedirs(src_dir, exist_ok=True)
        with open(os.path.join(pkg_dir, "package.json"), "w") as f:
            f.write("{}")

        # Exporting file
        mod_path = os.path.join(src_dir, "utils.ts")
        with open(mod_path, "w") as f:
            f.write("""
export const alpha = 1;
export function beta() { return 2; }
export type Gamma = string;
export { alpha as delta };
""")

        target_ts = os.path.join(src_dir, "index.ts")

        def run_hook(payload):
            t0 = time.time()
            p = subprocess.run(
                ["python3", hook_path],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
            )
            dur_ms = (time.time() - t0) * 1000
            return json.loads(p.stdout.strip()), dur_ms

        # Test 1: Valid import of existing symbols
        payload1 = {
            "workspacePaths": [tmpdir],
            "toolCall": {
                "name": "replace_file_content",
                "args": {
                    "TargetFile": target_ts,
                    "TargetContent": "const x = 1;",
                    "ReplacementContent": 'import { alpha, beta, Gamma } from "./utils";\nconst x = 1;',
                },
            },
        }
        res1, dur1 = run_hook(payload1)
        print(f"Test 1 (Valid import): decision={res1.get('decision')} in {dur1:.2f}ms")
        assert res1.get("decision") == "allow", f"Expected allow, got {res1}"

        # Test 2: Non-existent symbol from existing file
        payload2 = {
            "workspacePaths": [tmpdir],
            "toolCall": {
                "name": "replace_file_content",
                "args": {
                    "TargetFile": target_ts,
                    "TargetContent": "const x = 1;",
                    "ReplacementContent": 'import { alpha, NonExistentSym } from "./utils";\nconst x = 1;',
                },
            },
        }
        res2, dur2 = run_hook(payload2)
        print(f"Test 2 (Missing symbol): decision={res2.get('decision')} in {dur2:.2f}ms")
        assert res2.get("decision") == "deny", f"Expected deny, got {res2}"
        assert "Shift-Left AST Symbol Guard" in res2.get("reason", "")
        assert "NonExistentSym" in res2.get("reason", "")

        # Test 3: Module does not exist and not in allowed_files
        payload3 = {
            "workspacePaths": [tmpdir],
            "toolCall": {
                "name": "replace_file_content",
                "args": {
                    "TargetFile": target_ts,
                    "TargetContent": "const x = 1;",
                    "ReplacementContent": 'import { Foo } from "./does_not_exist";\nconst x = 1;',
                },
            },
        }
        res3, dur3 = run_hook(payload3)
        print(f"Test 3 (Missing module): decision={res3.get('decision')} in {dur3:.2f}ms")
        assert res3.get("decision") == "deny", f"Expected deny, got {res3}"
        assert "Shift-Left AST Import Guard" in res3.get("reason", "")

        # Test 4: Module does not exist BUT is in allowed_files (sibling file)
        payload4 = {
            "workspacePaths": [tmpdir],
            "toolCall": {
                "name": "replace_file_content",
                "args": {
                    "TargetFile": target_ts,
                    "TargetContent": "const x = 1;",
                    "ReplacementContent": 'import { Foo } from "./future_sibling";\nconst x = 1;',
                },
            },
            "transcript": [
                {
                    "source": "SYSTEM",
                    "type": "SYSTEM_MESSAGE",
                    "content": "allowed_files:\n  - " + target_ts + "\n  - " + os.path.join(src_dir, "future_sibling.ts"),
                }
            ],
        }
        res4, dur4 = run_hook(payload4)
        print(f"Test 4 (Sibling in allowed_files): decision={res4.get('decision')} in {dur4:.2f}ms")
        assert res4.get("decision") == "allow", f"Expected allow, got {res4}"

        # Test 5: Module has export *
        wildcard_mod = os.path.join(src_dir, "wildcard.ts")
        with open(wildcard_mod, "w") as f:
            f.write('export * from "somewhere_external";\n')
        payload5 = {
            "workspacePaths": [tmpdir],
            "toolCall": {
                "name": "replace_file_content",
                "args": {
                    "TargetFile": target_ts,
                    "TargetContent": "const x = 1;",
                    "ReplacementContent": 'import { AnyWildcardSymbol } from "./wildcard";\nconst x = 1;',
                },
            },
        }
        res5, dur5 = run_hook(payload5)
        print(f"Test 5 (Module with export *): decision={res5.get('decision')} in {dur5:.2f}ms")
        assert res5.get("decision") == "allow", f"Expected allow, got {res5}"

        # Test 6: Alias import @/utils
        payload6 = {
            "workspacePaths": [tmpdir],
            "toolCall": {
                "name": "replace_file_content",
                "args": {
                    "TargetFile": target_ts,
                    "TargetContent": "const x = 1;",
                    "ReplacementContent": 'import { beta } from "@/utils";\nconst x = 1;',
                },
            },
        }
        res6, dur6 = run_hook(payload6)
        print(f"Test 6 (Alias @/ import): decision={res6.get('decision')} in {dur6:.2f}ms")
        assert res6.get("decision") == "allow", f"Expected allow, got {res6}"


    finally:
        import shutil
        shutil.rmtree(test_base, ignore_errors=True)


if __name__ == "__main__":
    test_shift_left_ast_import_verification()
    print("ALL 6 TESTS PASSED!")

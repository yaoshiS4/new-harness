#!/usr/bin/env python3
"""Restore Shadow Checkpoint Utility.

Allows rolling back working tree state to an automatic shadow git checkpoint
created before a Builder mutation wave.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def get_checkpoint_path(conv_id: str) -> Path:
    return Path(tempfile.gettempdir()) / f".antigravity_shadow_ckpt_{conv_id}.json"


def list_shadow_checkpoints() -> list[dict]:
    checkpoints = []
    pattern = os.path.join(tempfile.gettempdir(), ".antigravity_shadow_ckpt_*.json")
    for p in glob.glob(pattern):
        try:
            data = json.loads(Path(p).read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data["_file"] = p
                checkpoints.append(data)
        except Exception:
            continue
    checkpoints.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return checkpoints


def restore_shadow_checkpoint(conv_id: str, dry_run: bool = False) -> dict:
    ckpt_path = get_checkpoint_path(conv_id)
    if not ckpt_path.is_file():
        return {
            "success": False,
            "error": f"Checkpoint file not found: {ckpt_path}",
        }

    try:
        ckpt = json.loads(ckpt_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"success": False, "error": f"Failed to parse checkpoint JSON: {e}"}

    workspace = ckpt.get("workspace") or os.getcwd()
    head_sha = ckpt.get("head_sha", "").strip()
    stash_sha = ckpt.get("stash_sha", "").strip()

    if not head_sha and not stash_sha:
        return {
            "success": False,
            "error": "Checkpoint contains neither head_sha nor stash_sha",
        }

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "conv_id": conv_id,
            "workspace": workspace,
            "head_sha": head_sha,
            "stash_sha": stash_sha,
        }

    commands = []
    if stash_sha:
        # Working tree was dirty when checkpointed
        # Reset to base HEAD and restore files captured in stash commit object
        if head_sha:
            commands.append(["git", "-C", workspace, "reset", "--hard", head_sha])
        commands.append(["git", "-C", workspace, "checkout", stash_sha, "--", "."])
    else:
        # Working tree was clean when checkpointed
        if head_sha:
            commands.append(["git", "-C", workspace, "reset", "--hard", head_sha])
        else:
            commands.append(["git", "-C", workspace, "checkout", "HEAD", "--", "."])

    executed = []
    for cmd in commands:
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=30.0,
            )
            executed.append({
                "cmd": " ".join(cmd),
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
            })
            if res.returncode != 0:
                return {
                    "success": False,
                    "error": f"Command failed: {' '.join(cmd)}\n{res.stderr}",
                    "executed": executed,
                }
        except subprocess.TimeoutExpired as exc:
            return {
                "success": False,
                "error": f"Command timed out after {exc.timeout}s: {' '.join(cmd)}",
                "executed": executed,
            }
        except Exception as ex:
            return {
                "success": False,
                "error": f"Subprocess invocation failed: {ex}",
                "executed": executed,
            }

    return {
        "success": True,
        "conv_id": conv_id,
        "workspace": workspace,
        "head_sha": head_sha,
        "stash_sha": stash_sha,
        "executed": executed,
    }


def self_test() -> int:
    """Validate internal JSON parsing and argument handling without touching live git repos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_conv = "self_test_conv_99999"
        fake_ckpt = Path(tmpdir) / f".antigravity_shadow_ckpt_{fake_conv}.json"
        data = {
            "conv_id": fake_conv,
            "timestamp": 1729500000.0,
            "stash_sha": "abc123def456",
            "head_sha": "789fed654cba",
            "workspace": "/fake/workspace",
        }
        fake_ckpt.write_text(json.dumps(data), encoding="utf-8")

        # Test parsing
        loaded = json.loads(fake_ckpt.read_text(encoding="utf-8"))
        assert loaded["conv_id"] == fake_conv, "conv_id mismatch"
        assert loaded["stash_sha"] == "abc123def456", "stash_sha mismatch"
        assert loaded["head_sha"] == "789fed654cba", "head_sha mismatch"

        # Test dry-run logic with monkeypatched path
        orig_get_checkpoint_path = globals()["get_checkpoint_path"]
        try:
            globals()["get_checkpoint_path"] = lambda cid: fake_ckpt
            res = restore_shadow_checkpoint(fake_conv, dry_run=True)
            assert res["success"] is True, f"dry_run failed: {res}"
            assert res["dry_run"] is True, "dry_run flag missing"
            assert res["stash_sha"] == "abc123def456", "stash_sha mismatch"
        finally:
            globals()["get_checkpoint_path"] = orig_get_checkpoint_path

    print("SELF_TEST_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore shadow git checkpoint before a wave.")
    parser.add_argument("--conv-id", help="Conversation ID to restore checkpoint for")
    parser.add_argument("--restore", action="store_true", help="Perform restoration")
    parser.add_argument("--list", action="store_true", help="List available shadow checkpoints")
    parser.add_argument("--dry-run", action="store_true", help="Simulate restoration without modifying git state")
    parser.add_argument("--self-test", action="store_true", help="Run self-test validation")

    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if args.list:
        ckpts = list_shadow_checkpoints()
        if not ckpts:
            print(f"No active shadow checkpoints found in {tempfile.gettempdir()}.")
            return 0
        print(f"Found {len(ckpts)} shadow checkpoint(s):")
        for c in ckpts:
            ts = c.get("timestamp", "unknown")
            cid = c.get("conv_id", "unknown")
            ws = c.get("workspace", "unknown")
            h = c.get("head_sha", "none")[:8]
            s = c.get("stash_sha", "none")[:8] if c.get("stash_sha") else "clean"
            print(f"- Conv: {cid} | Time: {ts} | Stash: {s} | Head: {h} | WS: {ws}")
        return 0

    if args.restore:
        conv_id = args.conv_id
        if not conv_id:
            # Try finding the most recent checkpoint
            ckpts = list_shadow_checkpoints()
            if not ckpts:
                print("Error: No shadow checkpoints available to restore.", file=sys.stderr)
                return 1
            conv_id = ckpts[0].get("conv_id")
            print(f"No --conv-id supplied; using most recent checkpoint: {conv_id}")

        result = restore_shadow_checkpoint(conv_id, dry_run=args.dry_run)
        if result.get("success"):
            action = "Simulated rollback" if args.dry_run else "Successfully restored"
            print(f"{action} checkpoint for conv_id: {conv_id}")
            return 0
        else:
            print(f"Restore failed: {result.get('error')}", file=sys.stderr)
            return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

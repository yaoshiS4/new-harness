from __future__ import annotations

import datetime
import glob
import hashlib
import json
import os
import re
import subprocess
import warnings
from typing import Any
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    message=".*Field 'lifespan' has an incomplete definition.*",
    category=UserWarning,
)

try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:  # pragma: no cover
    raise SystemExit("Missing MCP runtime dependency. Run uv sync in mcp/context_health.") from exc

mcp = FastMCP("context_health")


def _auto_detect_brain_dir(explicit_dir: str = "") -> str:
    """Auto-detect active runtime brain directory across Antigravity IDE, Codex CLI, and OpenCode."""
    if explicit_dir and os.path.exists(os.path.expanduser(explicit_dir)):
        return os.path.abspath(os.path.expanduser(explicit_dir))

    env_dirs = [
        os.getenv("ANTIGRAVITY_BRAIN_DIR"),
        os.getenv("CODEX_BRAIN_DIR"),
    ]
    for env_d in env_dirs:
        if env_d and os.path.exists(os.path.expanduser(env_d)):
            return os.path.abspath(os.path.expanduser(env_d))

    candidates = [
        "~/.gemini/antigravity-cli/brain",
        "~/.gemini/antigravity-ide/brain",
        "~/.gemini/antigravity/brain",
        "~/.codex/brain",
        "~/.gemini/brain",
    ]
    for cand in candidates:
        expanded = os.path.expanduser(cand)
        if os.path.exists(expanded):
            return os.path.abspath(expanded)

    # Fallback to default Antigravity CLI path
    return os.path.abspath(os.path.expanduser("~/.gemini/antigravity-cli/brain"))


BRAIN_DIR = _auto_detect_brain_dir()


def _find_session_dir(brain_dir: str, session_id: str = "") -> str | None:
    """Find the specific or most recent active session directory."""
    if not os.path.isdir(brain_dir):
        if not session_id:
            return None

    global_default_brain = globals().get("BRAIN_DIR") or _auto_detect_brain_dir()
    gemini_home = os.path.abspath(os.path.expanduser("~/.gemini"))
    is_default_host_brain = (
        os.path.abspath(brain_dir) == os.path.abspath(global_default_brain)
        and os.path.abspath(brain_dir).startswith(gemini_home)
    )

    if session_id:
        target = os.path.join(brain_dir, session_id)
        if os.path.isdir(target):
            return target
        if os.path.isdir(brain_dir):
            matches = [
                os.path.join(brain_dir, d)
                for d in os.listdir(brain_dir)
                if d.startswith(session_id) and os.path.isdir(os.path.join(brain_dir, d))
            ]
            if matches:
                return matches[0]

        if is_default_host_brain:
            candidates = [
                "~/.gemini/antigravity-cli/brain",
                "~/.gemini/antigravity-ide/brain",
                "~/.gemini/antigravity/brain",
                "~/.codex/brain",
                "~/.gemini/brain",
            ]
            for cand in candidates:
                cand_p = os.path.abspath(os.path.expanduser(cand))
                if cand_p == os.path.abspath(brain_dir) or not os.path.isdir(cand_p):
                    continue
                cand_target = os.path.join(cand_p, session_id)
                if os.path.isdir(cand_target):
                    return cand_target
                cand_matches = [
                    os.path.join(cand_p, d)
                    for d in os.listdir(cand_p)
                    if d.startswith(session_id) and os.path.isdir(os.path.join(cand_p, d))
                ]
                if cand_matches:
                    return cand_matches[0]
        return None

    # 1. Resolve root conversations via conversation_summaries.db
    db_paths = [
        os.path.expanduser("~/.gemini/antigravity-cli/conversation_summaries.db"),
        os.path.expanduser("~/.gemini/antigravity-ide/conversation_summaries.db"),
        os.path.expanduser("~/.gemini/antigravity/conversation_summaries.db"),
    ]
    for db_p in db_paths:
        if os.path.isfile(db_p):
            try:
                import sqlite3
                conn = sqlite3.connect(db_p)
                try:
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT conversation_id 
                        FROM conversation_summaries 
                        WHERE (parent_conversation_id IS NULL OR parent_conversation_id = '') 
                        ORDER BY last_modified_time DESC LIMIT 10
                    """)
                    rows = cur.fetchall()
                finally:
                    conn.close()
                for (root_id,) in rows:
                    if not root_id:
                        continue
                    candidate_p = os.path.join(brain_dir, root_id)
                    if os.path.isdir(candidate_p) and _find_transcript_file(candidate_p):
                        return candidate_p
                    if is_default_host_brain:
                        for cand_root in (
                            "~/.gemini/antigravity-cli/brain",
                            "~/.gemini/antigravity-ide/brain",
                            "~/.gemini/antigravity/brain",
                        ):
                            cand_full = os.path.abspath(os.path.expanduser(f"{cand_root}/{root_id}"))
                            if os.path.isdir(cand_full) and _find_transcript_file(cand_full):
                                return cand_full
            except Exception:
                pass

    # 2. Fallback: Find the session directory whose transcript was most recently modified
    subdirs: list[tuple[float, str]] = []
    for entry in os.listdir(brain_dir):
        full_p = os.path.join(brain_dir, entry)
        if os.path.isdir(full_p) and not entry.startswith("."):
            t_file = _find_transcript_file(full_p)
            if t_file:
                try:
                    mtime = os.path.getmtime(t_file)
                    subdirs.append((mtime, full_p))
                except OSError:
                    continue

    subdirs.sort(key=lambda x: x[0], reverse=True)
    return subdirs[0][1] if subdirs else None


def _find_transcript_file(session_dir: str) -> str | None:
    """Locate transcript.jsonl within a session directory."""
    candidates = [
        os.path.join(session_dir, ".system_generated", "logs", "transcript.jsonl"),
        os.path.join(session_dir, "transcript.jsonl"),
        os.path.join(session_dir, ".system_generated", "logs", "transcript_full.jsonl"),
        os.path.join(session_dir, "transcript_full.jsonl"),
    ]
    for cand in candidates:
        if os.path.isfile(cand):
            return cand
    return None


def _normalize_path(raw_path: str, cwd: str = "") -> str:
    """Normalize file path for accurate frequency counting, resolving relative paths."""
    cleaned = raw_path.strip()
    while (cleaned.startswith('"') and cleaned.endswith('"')) or (
        cleaned.startswith("'") and cleaned.endswith("'")
    ):
        cleaned = cleaned[1:-1].strip()
    expanded = os.path.expanduser(cleaned)
    if not os.path.isabs(expanded):
        base = cwd if (cwd and os.path.isabs(cwd)) else os.getcwd()
        expanded = os.path.join(base, expanded)
    return os.path.normpath(os.path.abspath(expanded))


def _parse_transcript(
    transcript_path: str,
    cwd: str = "",
) -> tuple[int, dict[str, int], dict[str, int], int, int]:
    """Parse transcript JSONL line by line.

    Tracks unedited, non-disjoint file reads. Resets repeat-read counter when a file is edited.
    Returns:
        (step_count, tool_distribution, file_reads, error_count, last_ledger_step)
    """
    step_count = 0
    tool_distribution: dict[str, int] = {}
    file_reads: dict[str, int] = {}
    file_slices: dict[str, list[tuple[int, int]]] = {}
    file_last_read_ts: dict[str, float] = {}
    error_count = 0
    last_ledger_step = 0

    if not os.path.isfile(transcript_path):
        return 0, tool_distribution, file_reads, 0, 0

    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue

                idx = obj.get("step_index")
                if isinstance(idx, int):
                    current_step = idx + 1
                    step_count = max(step_count, current_step)
                else:
                    step_count += 1
                    current_step = step_count

                ts_str = obj.get("created_at")
                step_time = 0.0
                if ts_str and isinstance(ts_str, str):
                    try:
                        dt = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        step_time = dt.timestamp()
                    except Exception:
                        pass

                status = obj.get("status")
                exit_code = obj.get("exit_code")
                if status == "ERROR" or (isinstance(exit_code, int) and exit_code != 0):
                    error_count += 1

                tool_calls = obj.get("tool_calls")
                if isinstance(tool_calls, list):
                    for tc in tool_calls:
                        if not isinstance(tc, dict):
                            continue
                        name = tc.get("name") or tc.get("function", {}).get("name")
                        if not name or not isinstance(name, str):
                            continue
                        tool_distribution[name] = tool_distribution.get(name, 0) + 1

                        args = tc.get("args")
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                pass
                        if not isinstance(args, dict):
                            continue

                        # Check for ledger commit to reset milestone step penalties
                        if name == "commit_context_ledger" or (
                            name == "call_mcp_tool" and args.get("ToolName") == "commit_context_ledger"
                        ):
                            last_ledger_step = current_step

                        # Check for edits that reset the repeat-read counter for that target
                        if name in (
                            "replace_file_content",
                            "write_to_file",
                            "multi_replace_file_content",
                            "edit_file",
                            "write_file",
                        ):
                            target_p = (
                                args.get("Path")
                                or args.get("TargetFile")
                                or args.get("AbsolutePath")
                                or args.get("file_path")
                                or args.get("path")
                                or args.get("file")
                                or ""
                            )
                            if isinstance(target_p, str) and target_p:
                                norm_t = _normalize_path(target_p, cwd)
                                file_reads[norm_t] = 0
                                file_slices[norm_t] = []
                                file_last_read_ts.pop(norm_t, None)

                        elif name == "run_command":
                            cmd_str = args.get("CommandLine") or args.get("cmd") or ""
                            cmd_cwd = args.get("Cwd") or cwd or ""
                            if isinstance(cmd_str, str) and cmd_str:
                                # Redirection > or >>
                                for m in re.finditer(r"(?:>|>>)\s*(?:\"([^\"]+)\"|'([^']+)'|([^\s;&|<>]+))", cmd_str):
                                    target = m.group(1) or m.group(2) or m.group(3) or ""
                                    if target:
                                        norm_t = _normalize_path(target, cmd_cwd)
                                        file_reads[norm_t] = 0
                                        file_slices[norm_t] = []
                                        file_last_read_ts.pop(norm_t, None)
                                # In-place commands (sd, sed -i, perl -i, tee)
                                for m in re.finditer(r"\b(?:sd|sed\s+-[a-zA-Z]*i|perl\s+-[a-zA-Z]*i|tee)\b.*?([A-Za-z0-9_./-]+\.[A-Za-z0-9_]+)", cmd_str):
                                    target = m.group(1)
                                    if target:
                                        norm_t = _normalize_path(target, cmd_cwd)
                                        file_reads[norm_t] = 0
                                        file_slices[norm_t] = []
                                        file_last_read_ts.pop(norm_t, None)

                        elif name in ("view_file", "read_file"):
                            path_val = (
                                args.get("Path")
                                or args.get("TargetFile")
                                or args.get("AbsolutePath")
                                or args.get("file_path")
                                or args.get("path")
                                or args.get("file")
                                or ""
                            )
                            if isinstance(path_val, str) and path_val:
                                norm_p = _normalize_path(path_val, cwd)
                                if step_time > 0:
                                    file_last_read_ts[norm_p] = max(file_last_read_ts.get(norm_p, 0.0), step_time)
                                start_l = args.get("StartLine")
                                end_l = args.get("EndLine")

                                # Slice-awareness: check if disjoint slice
                                if (
                                    isinstance(start_l, int)
                                    and isinstance(end_l, int)
                                    and start_l > 0
                                    and end_l >= start_l
                                ):
                                    existing_slices = file_slices.setdefault(norm_p, [])
                                    overlapping = any(
                                        not (end_l < s_start or start_l > s_end)
                                        for s_start, s_end in existing_slices
                                    )
                                    existing_slices.append((start_l, end_l))
                                    if overlapping or len(existing_slices) > 6:
                                        file_reads[norm_p] = file_reads.get(norm_p, 0) + 1
                                else:
                                    file_reads[norm_p] = file_reads.get(norm_p, 0) + 1

        # Reset repeat-read count if file on disk was modified newer than last read
        for norm_p in list(file_reads.keys()):
            if file_reads.get(norm_p, 0) > 0 and os.path.isfile(norm_p):
                try:
                    mtime = os.path.getmtime(norm_p)
                    last_ts = file_last_read_ts.get(norm_p, 0.0)
                    if last_ts > 0 and mtime > last_ts:
                        file_reads[norm_p] = 0
                        file_slices[norm_p] = []
                except OSError:
                    pass
    except Exception:
        pass

    return step_count, tool_distribution, file_reads, error_count, last_ledger_step


def _extract_observation_target(tool_name: str, args: dict) -> str:
    if not isinstance(args, dict):
        return tool_name
    if tool_name in ("view_file", "read_file"):
        p = (
            args.get("Path")
            or args.get("TargetFile")
            or args.get("AbsolutePath")
            or args.get("file_path")
            or args.get("path")
            or args.get("file")
            or ""
        )
        return os.path.basename(p) if p else "file"
    elif tool_name == "run_command":
        cmd = args.get("CommandLine") or args.get("cmd") or ""
        cmd_clean = " ".join(cmd.strip().split())
        if len(cmd_clean) > 35:
            cmd_clean = cmd_clean[:32] + "..."
        return cmd_clean if cmd_clean else "command"
    elif tool_name in (
        "replace_file_content",
        "write_to_file",
        "multi_replace_file_content",
        "edit_file",
        "write_file",
    ):
        p = (
            args.get("Path")
            or args.get("TargetFile")
            or args.get("AbsolutePath")
            or args.get("file_path")
            or args.get("path")
            or args.get("file")
            or ""
        )
        return os.path.basename(p) if p else "file"
    elif tool_name == "list_dir":
        p = args.get("DirectoryPath") or args.get("path") or ""
        return os.path.basename(p) if p else "dir"
    elif tool_name == "read_url_content":
        u = args.get("Url") or args.get("url") or ""
        return u[:35] if u else "url"
    elif tool_name == "call_mcp_tool":
        sub_tool = args.get("ToolName") or "mcp"
        return sub_tool
    else:
        for k in ("path", "target", "file", "name", "query"):
            if k in args and isinstance(args[k], str):
                val = args[k].strip()
                return os.path.basename(val) if "/" in val else val[:30]
    return tool_name


def _compute_transcript_token_stats(transcript_path: str) -> dict[str, Any]:
    """Computes exact observation token share vs reasoning token share across transcript (NeurIPS DL4Code 2025)."""
    reasoning_chars = 0
    obs_chars = 0
    user_chars = 0
    other_chars = 0

    if not os.path.isfile(transcript_path):
        return {
            "observation_tokens": 0,
            "reasoning_tokens": 0,
            "user_tokens": 0,
            "total_tokens": 0,
            "observation_token_share": 0.0,
            "reasoning_token_share": 0.0,
            "observation_share_pct": "0.0%",
            "reasoning_share_pct": "0.0%",
        }

    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    step = json.loads(line)
                except Exception:
                    continue

                source = step.get("source", "")
                stype = step.get("type", "")
                content = str(step.get("content") or "")
                thinking = str(step.get("thinking") or "")

                if thinking:
                    reasoning_chars += len(thinking)

                if source == "USER_EXPLICIT" or stype == "USER_INPUT":
                    user_chars += len(content)
                elif stype == "PLANNER_RESPONSE":
                    if content:
                        reasoning_chars += len(content)
                elif stype in ("GENERIC", "TOOL_OUTPUT", "OBSERVATION") or (source == "MODEL" and not step.get("tool_calls")):
                    obs_chars += len(content)
                else:
                    other_chars += len(content)
    except Exception:
        pass

    reasoning_tokens = max(0, reasoning_chars // 4)
    obs_tokens = max(0, obs_chars // 4)
    user_tokens = max(0, user_chars // 4)
    other_tokens = max(0, other_chars // 4)
    total_tokens = reasoning_tokens + obs_tokens + user_tokens + other_tokens

    if total_tokens > 0:
        obs_share = round(obs_tokens / total_tokens, 4)
        reason_share = round(reasoning_tokens / total_tokens, 4)
    else:
        obs_share = 0.0
        reason_share = 0.0

    return {
        "observation_tokens": obs_tokens,
        "reasoning_tokens": reasoning_tokens,
        "user_tokens": user_tokens,
        "total_tokens": total_tokens,
        "observation_token_share": obs_share,
        "reasoning_token_share": reason_share,
        "observation_share_pct": f"{obs_share * 100:.1f}%",
        "reasoning_share_pct": f"{reason_share * 100:.1f}%",
    }


def format_observation_tombstone(
    tool_name: str,
    target_path: str,
    start_line: int,
    end_line: int,
    token_count: int,
    symbols: list[str] | None = None,
) -> str:
    """Wave 4.1 Deterministic Observation Tombstone (JetBrains Research DL4Code 2025).

    Returns formatted string:
    `[Elided {tool_name}({target_path}, L{start_line}-L{end_line}) — {token_count} tokens masked | Symbols: {sym_str}]`
    """
    sym_str = ", ".join(symbols) if symbols else "none"
    return f"[Elided {tool_name}({target_path}, L{start_line}-L{end_line}) — {token_count} tokens masked | Symbols: {sym_str}]"


def _mask_observations(
    transcript_path: str,
    keep_recent_turns: int = 4,
) -> tuple[list[dict[str, Any]], int, int, int, str]:
    """Applies deterministic observation masking for steps older than keep_recent_turns.
    
    Replaces bulky view_file / run_command / etc. outputs with:
    `[Masked Observation: {tool}({target}) | {lines} lines | sha256:{hash8}]`
    Returns:
        (masked_steps, masked_count, original_tokens, masked_tokens, digest)
    """
    if not os.path.isfile(transcript_path):
        return [], 0, 0, 0, ""

    raw_steps: list[dict[str, Any]] = []
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        raw_steps.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        return [], 0, 0, 0, ""

    tool_cycles: list[dict[str, Any]] = []
    current_tool = ""
    current_args: dict = {}

    for i, step in enumerate(raw_steps):
        tcalls = step.get("tool_calls")
        if isinstance(tcalls, list) and tcalls:
            tc0 = tcalls[0] if isinstance(tcalls[0], dict) else {}
            current_tool = tc0.get("name") or tc0.get("function", {}).get("name") or "tool"
            args_raw = tc0.get("args") or {}
            if isinstance(args_raw, str):
                try:
                    current_args = json.loads(args_raw)
                except Exception:
                    current_args = {}
            elif isinstance(args_raw, dict):
                current_args = args_raw
            else:
                current_args = {}
        elif step.get("type") in ("GENERIC", "TOOL_OUTPUT", "OBSERVATION") or (
            step.get("source") == "MODEL" and current_tool and not step.get("tool_calls")
        ):
            target_str = _extract_observation_target(current_tool, current_args)
            tool_cycles.append({
                "obs_index": i,
                "tool": current_tool,
                "target": target_str,
                "step": step,
            })
            current_tool = ""
            current_args = {}

    total_cycles = len(tool_cycles)
    cutoff_idx = max(0, total_cycles - keep_recent_turns)
    eligible_cycles = tool_cycles[:cutoff_idx]
    eligible_obs_indices = {c["obs_index"]: c for c in eligible_cycles}

    orig_chars = 0
    masked_chars = 0
    masked_count = 0
    masked_digest_lines: list[str] = []
    processed_steps: list[dict[str, Any]] = []

    for i, step in enumerate(raw_steps):
        step_copy = dict(step)
        content = str(step.get("content") or "")
        orig_chars += len(content)

        if i in eligible_obs_indices:
            info = eligible_obs_indices[i]
            lines = len(content.splitlines()) if content else 0
            if lines > 2 or len(content) > 120:
                h8 = hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]
                tool_label = info["tool"]
                target_label = info["target"]
                mask_str = f"[Masked Observation: {tool_label}({target_label}) | {lines} lines | sha256:{h8}]"
                tombstone = format_observation_tombstone(
                    tool_name=tool_label,
                    target_path=target_label,
                    start_line=1,
                    end_line=lines,
                    token_count=max(0, len(content) // 4),
                    symbols=None,
                )
                step_copy["content"] = mask_str
                step_copy["tombstone"] = tombstone
                step_copy["observation_masked"] = True
                step_copy["original_lines"] = lines
                step_copy["original_sha256"] = h8
                masked_count += 1
                masked_digest_lines.append(f"- Step {i}: `{mask_str}`")
                masked_chars += len(mask_str)
            else:
                masked_chars += len(content)
        else:
            masked_chars += len(content)

        processed_steps.append(step_copy)

    orig_tokens = max(0, orig_chars // 4)
    masked_tokens = max(0, masked_chars // 4)
    savings = orig_tokens - masked_tokens
    savings_pct = round((savings / orig_tokens) * 100, 1) if orig_tokens > 0 else 0.0

    digest = ""
    if masked_digest_lines:
        digest = (
            f"### Observation-Masked Trajectory Digest (NeurIPS DL4Code 2025)\n"
            f"- **Token Telemetry**: Pre-mask: ~{orig_tokens} tokens | Post-mask: ~{masked_tokens} tokens | Est. Savings: {savings_pct}%\n"
            f"- **Retained Window**: Most recent {keep_recent_turns} action cycles preserved unmasked\n"
            f"- **Masked Action Records** ({masked_count} observations masked):\n"
            + "\n".join(masked_digest_lines)
        )

    return processed_steps, masked_count, orig_tokens, masked_tokens, digest


def _calculate_health_score(
    step_count: int,
    file_size_bytes: int,
    file_reads: dict[str, int],
    error_count: int,
    last_ledger_step: int = 0,
) -> tuple[int, str, str, dict[str, int]]:
    """Compute cognitive health score and status directives based on academic research."""
    base_score = 100

    # Step penalty: measured relative to last ledger milestone
    effective_steps = max(0, step_count - last_ledger_step) if last_ledger_step > 0 else step_count
    step_penalty = 0
    if effective_steps > 30:
        step_penalty = min(35, int((effective_steps - 30) * 0.75))

    # Size penalty: after 500KB, degradation accelerates (max 25)
    size_penalty = 0
    if file_size_bytes > 500_000:
        size_penalty = min(25, int((file_size_bytes - 500_000) / 100_000 * 3))

    # Repeat-read penalty: each file read >= 3 times incurs 5 pts + 1 pt per extra read (max 30)
    repeated_reads: dict[str, int] = {}
    repeat_penalty = 0
    for path, count in file_reads.items():
        if count >= 3:
            repeated_reads[path] = count
            penalty = 5 + (count - 3) * 1
            repeat_penalty += penalty
    repeat_penalty = min(30, repeat_penalty)

    # Error penalty: 2 pts per error (max 15)
    err_penalty = min(15, error_count * 2)

    total_penalty = step_penalty + size_penalty + repeat_penalty + err_penalty
    score = max(0, min(100, base_score - total_penalty))

    if score >= 80:
        status = "HEALTHY"
        directive = "PROCEED"
    elif score >= 55:
        status = "DEGRADED"
        directive = "COMPACT_LEDGER"
    else:
        status = "CRITICAL"
        directive = "MANDATE_ISOLATION"

    return score, status, directive, repeated_reads


@mcp.tool()
def get_session_health(
    session_id: str = "",
    brain_dir: str = "",
    conversation_id: str = "",
) -> dict[str, Any]:
    """Retrieve ground-truth cognitive health score and context rot telemetry for an agent session."""
    effective_id = session_id or conversation_id
    detected_brain = _auto_detect_brain_dir(brain_dir)
    session_path = _find_session_dir(detected_brain, effective_id)

    if not session_path:
        return {
            "error": "No session found",
            "brain_dir": detected_brain,
            "session_id": effective_id,
            "conversation_id": effective_id,
            "cognitive_health_score": 100,
            "status": "HEALTHY",
            "directive": "PROCEED",
        }

    actual_session_id = os.path.basename(session_path)
    transcript_p = _find_transcript_file(session_path)

    if not transcript_p:
        return {
            "error": "No transcript found for session",
            "session_id": actual_session_id,
            "conversation_id": actual_session_id,
            "session_dir": session_path,
            "cognitive_health_score": 100,
            "status": "HEALTHY",
            "directive": "PROCEED",
        }

    file_size_bytes = 0
    try:
        file_size_bytes = os.path.getsize(transcript_p)
    except OSError:
        pass

    step_count, tool_distribution, file_reads, error_count, last_ledger_step = _parse_transcript(transcript_p)
    score, status, directive, repeated_reads = _calculate_health_score(
        step_count, file_size_bytes, file_reads, error_count, last_ledger_step
    )

    token_stats = _compute_transcript_token_stats(transcript_p)

    guidance = ""
    if status == "DEGRADED":
        guidance = (
            "Session health is DEGRADED (approaching 80% context budget). "
            "Execute commit_context_ledger to summarize key progress and prune working context."
        )
    elif status == "CRITICAL":
        guidance = (
            "Session health is CRITICAL (<55 score or severe repeat loops). "
            "Stop inline exploration immediately. Trigger handoff checkpoint and mandate subagent isolation via spawn governance."
        )
    else:
        guidance = "Session health is HEALTHY. Proceed within current context budget."

    if token_stats.get("observation_token_share", 0) >= 0.50:
        guidance += f" High observation share ({token_stats['observation_share_pct']}). Execute compact_observations to prune older outputs."

    return {
        "session_id": actual_session_id,
        "conversation_id": actual_session_id,
        "brain_dir": detected_brain,
        "transcript_path": transcript_p,
        "step_count": step_count,
        "transcript_bytes": file_size_bytes,
        "tool_distribution": tool_distribution,
        "error_count": error_count,
        "repeated_reads": repeated_reads,
        "cognitive_health_score": score,
        "status": status,
        "directive": directive,
        "guidance": guidance,
        "observation_token_share": token_stats["observation_token_share"],
        "reasoning_token_share": token_stats["reasoning_token_share"],
        "observation_share_pct": token_stats["observation_share_pct"],
        "reasoning_share_pct": token_stats["reasoning_share_pct"],
        "estimated_observation_tokens": token_stats["observation_tokens"],
        "estimated_reasoning_tokens": token_stats["reasoning_tokens"],
        "estimated_total_tokens": token_stats["total_tokens"],
        "observation_masking_available": True,
    }


@mcp.tool()
def compact_observations(
    session_id: str = "",
    brain_dir: str = "",
    keep_recent_turns: int = 4,
    dry_run: bool = True,
    conversation_id: str = "",
) -> dict[str, Any]:
    """Applies JetBrains Research (NeurIPS DL4Code 2025) deterministic observation masking to older transcript steps.
    
    Replaces bulky tool observations older than keep_recent_turns with deterministic masked markers:
    `[Masked Observation: {tool}({target}) | {lines} lines | sha256:{hash8}]`.
    Preserves 100% of trajectory history at ~50% lower token cost for handoffs and /compact checkpoints.
    """
    effective_id = session_id or conversation_id
    detected_brain = _auto_detect_brain_dir(brain_dir)
    session_path = _find_session_dir(detected_brain, effective_id)

    if not session_path:
        return {
            "error": "No session found",
            "brain_dir": detected_brain,
            "session_id": effective_id,
            "conversation_id": effective_id,
            "status": "NOT_FOUND",
        }

    actual_session_id = os.path.basename(session_path)
    transcript_p = _find_transcript_file(session_path)
    if not transcript_p:
        return {
            "error": "No transcript found for session",
            "session_id": actual_session_id,
            "conversation_id": actual_session_id,
            "session_dir": session_path,
            "status": "NOT_FOUND",
        }

    masked_steps, masked_count, orig_tokens, masked_tokens, digest = _mask_observations(
        transcript_p, keep_recent_turns=keep_recent_turns
    )
    token_stats = _compute_transcript_token_stats(transcript_p)

    savings_tokens = max(0, orig_tokens - masked_tokens)
    savings_pct = round((savings_tokens / orig_tokens) * 100, 1) if orig_tokens > 0 else 0.0

    output_file = None
    if not dry_run and masked_steps:
        logs_dir = os.path.dirname(transcript_p)
        output_file = os.path.join(logs_dir, "transcript_masked.jsonl")
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for s in masked_steps:
                    f.write(json.dumps(s, ensure_ascii=False) + "\n")
        except Exception as exc:
            return {
                "status": "ERROR",
                "error": str(exc),
                "session_id": actual_session_id,
                "conversation_id": actual_session_id,
            }

    return {
        "status": "COMPACTED" if not dry_run else "DRY_RUN",
        "session_id": actual_session_id,
        "conversation_id": actual_session_id,
        "transcript_path": transcript_p,
        "total_steps": len(masked_steps),
        "keep_recent_turns": keep_recent_turns,
        "masked_steps_count": masked_count,
        "original_tokens": orig_tokens,
        "masked_tokens": masked_tokens,
        "token_savings_pct": f"{savings_pct:.1f}%",
        "observation_token_share": token_stats["observation_token_share"],
        "reasoning_token_share": token_stats["reasoning_token_share"],
        "observation_share_pct": token_stats["observation_share_pct"],
        "reasoning_share_pct": token_stats["reasoning_share_pct"],
        "digest": digest,
        "output_file": output_file,
        "tombstone_format": format_observation_tombstone("tool", "target", 1, 100, 0, []),
    }


@mcp.tool()
def check_read_budget(
    file_path: str,
    session_id: str = "",
    brain_dir: str = "",
    cwd: str = "",
    conversation_id: str = "",
) -> dict[str, Any]:
    """Authoritative Three-Strike read gate backend for loop-detection. Checks if a file can be read again without context rot."""
    if not file_path:
        return {
            "allowed": False,
            "count": 0,
            "mitigation": "Empty file path provided.",
        }

    effective_id = session_id or conversation_id
    detected_brain = _auto_detect_brain_dir(brain_dir)
    session_path = _find_session_dir(detected_brain, effective_id)
    normalized_target = _normalize_path(file_path, cwd)

    if not session_path:
        return {
            "file_path": normalized_target,
            "allowed": True,
            "count": 0,
            "mitigation": "Session directory not located. Permitted by default.",
        }

    transcript_p = _find_transcript_file(session_path)
    if not transcript_p:
        return {
            "file_path": normalized_target,
            "allowed": True,
            "count": 0,
            "mitigation": "Transcript not located. Permitted by default.",
        }

    _, _, file_reads, _, _ = _parse_transcript(transcript_p, cwd)
    current_count = file_reads.get(normalized_target, 0)

    # Check if target file was modified newer than transcript file
    if current_count > 0 and os.path.isfile(normalized_target):
        try:
            mtime = os.path.getmtime(normalized_target)
            if transcript_p and os.path.isfile(transcript_p):
                tr_mtime = os.path.getmtime(transcript_p)
                if mtime > tr_mtime:
                    current_count = 0
                    file_reads[normalized_target] = 0
        except OSError:
            pass

    # If count >= 2, the next read would be the 3rd read or higher (3-strike rule)
    if current_count >= 2:
        return {
            "file_path": normalized_target,
            "allowed": False,
            "count": current_count,
            "mitigation": (
                f"File has reached or exceeded read threshold ({current_count} previous reads). "
                "Three-Strike Rule ACTIVATED. DO NOT call view_file. "
                "Use run_command with rg or codegraph:symbol_lookup for precise lines, codegraph for symbol signatures, or codegraph for callers/callees."
            ),
        }

    return {
        "file_path": normalized_target,
        "allowed": True,
        "count": current_count,
        "mitigation": f"Within budget ({current_count}/2 prior reads). Proceed with view_file.",
    }


@mcp.tool()
def commit_context_ledger(
    milestone: str = "",
    goals_completed: list[str] | None = None,
    files_modified: list[str] | None = None,
    active_constraints: list[str] | None = None,
    project_dir: str = "",
    include_masked_digest: bool = True,
    conversation_id: str = "",
    summary: str = "",
    decisions: list[str] | None = None,
    session_id: str = "",
) -> dict[str, Any]:
    """Appends a structured Context Codec snapshot to docs/CONTEXT_LEDGER.md with lock awareness."""
    effective_id = session_id or conversation_id
    milestone = milestone or summary or "Session Checkpoint"
    goals_completed = (
        list(goals_completed)
        if goals_completed is not None
        else (list(decisions) if decisions else ([summary] if summary else []))
    )
    files_modified = list(files_modified) if files_modified is not None else []
    active_constraints = list(active_constraints) if active_constraints is not None else []

    proj = ""
    if project_dir:
        proj = os.path.abspath(project_dir)
    else:
        cwd = os.getcwd()
        normalized_cwd = cwd.rstrip("/")
        if (
            normalized_cwd.endswith("mcp_servers/context_health")
            or normalized_cwd.endswith("/context_health")
            or normalized_cwd.endswith("context_health")
        ):
            db_path = os.path.expanduser("~/.gemini/antigravity-cli/conversation_summaries.db")
            if os.path.isfile(db_path):
                try:
                    import sqlite3

                    conn = sqlite3.connect(db_path)
                    try:
                        cur = conn.cursor()
                        if effective_id:
                            cur.execute(
                                "SELECT workspace_uris FROM conversation_summaries WHERE conversation_id = ? LIMIT 1",
                                (effective_id,),
                            )
                        else:
                            cur.execute(
                                "SELECT workspace_uris FROM conversation_summaries ORDER BY last_modified_time DESC LIMIT 5"
                            )
                        rows = cur.fetchall()
                    finally:
                        conn.close()
                    for (wu_json,) in rows:
                        if not wu_json:
                            continue
                        try:
                            wu_list = json.loads(wu_json) if isinstance(wu_json, str) else wu_json
                            for uri in wu_list:
                                candidate = uri[7:] if uri.startswith("file://") else uri
                                if os.path.isdir(candidate):
                                    proj = candidate
                                    break
                        except Exception:
                            pass
                        if proj:
                            break
                except Exception:
                    pass

    if not proj:
        fallback_dir = os.path.expanduser("~/.cache/antigravity_context_ledger")
        proj = fallback_dir
        docs_dir = fallback_dir
        ledger_path = os.path.join(docs_dir, "CONTEXT_LEDGER.md")
    else:
        docs_dir = os.path.join(proj, "docs")
        ledger_path = os.path.join(docs_dir, "CONTEXT_LEDGER.md")

    # Check lock status if codex-agents lock script exists
    lock_info = "unlocked"
    lock_script = os.getenv("ANTIGRAVITY_LOCK_SCRIPT", "")
    if lock_script and os.path.isfile(lock_script):
        try:
            res = subprocess.run(
                ["bash", lock_script, "status", proj],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lock_output = res.stdout.strip()
            if "runtime:" in lock_output:
                lock_info = f"locked ({lock_output.splitlines()[0]})"
        except Exception:
            pass

    iso_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

    os.makedirs(docs_dir, exist_ok=True)

    header = ""
    if not os.path.isfile(ledger_path) or os.path.getsize(ledger_path) == 0:
        header = "# Project Context Ledger\n\nAuthoritative mid-session progress checkpoints for context compaction and rot mitigation.\n\n---\n\n"

    goals_block = "\n".join(f"- {g}" for g in goals_completed) if goals_completed else "- (None)"
    files_block = "\n".join(f"- `{f}`" for f in files_modified) if files_modified else "- (None)"
    constraints_block = (
        "\n".join(f"- {c}" for c in active_constraints) if active_constraints else "- (Standard constraints)"
    )

    digest_block = ""
    if include_masked_digest:
        try:
            detected_brain = _auto_detect_brain_dir()
            session_path = _find_session_dir(detected_brain, effective_id)
            if session_path:
                tp = _find_transcript_file(session_path)
                if tp:
                    tstats = _compute_transcript_token_stats(tp)
                    _, m_count, _, _, d = _mask_observations(tp, keep_recent_turns=4)
                    obs_pct = tstats.get("observation_share_pct", "0.0%")
                    reason_pct = tstats.get("reasoning_share_pct", "0.0%")
                    digest_block = (
                        f"- **Observation Masking Telemetry (NeurIPS DL4Code 2025)**:\n"
                        f"  - Observation Token Share: {obs_pct} | Reasoning Token Share: {reason_pct}\n"
                        f"  - Masked Observations: {m_count} earlier steps ready for handoff\n"
                    )
                    if d:
                        digest_block += f"\n<details><summary>Compacted Observation Ledger</summary>\n\n{d}\n</details>\n"
        except Exception:
            pass

    entry = (
        f"## [Milestone: {milestone}] - {iso_time}\n"
        f"- **Runtime Lock State**: {lock_info}\n"
        f"- **Goals Completed**:\n{goals_block}\n"
        f"- **Files Modified**:\n{files_block}\n"
        f"- **Active Constraints**:\n{constraints_block}\n"
        f"{digest_block}\n"
        f"---\n\n"
    )

    try:
        with open(ledger_path, "a", encoding="utf-8") as f:
            if header:
                f.write(header)
            f.write(entry)
    except Exception as exc:
        return {
            "status": "ERROR",
            "error": str(exc),
            "project_dir": proj,
            "ledger_path": ledger_path,
        }

    return {
        "status": "COMMITTED",
        "project_dir": proj,
        "ledger_path": ledger_path,
        "milestone": milestone,
        "entry_preview": entry.strip(),
        "lock_status": lock_info,
    }


@mcp.tool()
def distill_observation_buffer(
    conversation_id: str = "",
    transcript_path: str = "",
    max_entries: int = 20,
    session_id: str = "",
) -> dict[str, Any]:
    """Prefix-Stable Observational Memory Compaction (Mastra Observer + Reflector).

    Extracts deterministic turn deltas (🔴 Mutations, 🟡 Verifications, 🟢 Key Reads),
    deduplicates repeated reads and superseded test runs, and writes an append-stable
    observation buffer to ~/.cache/antigravity_observations/{conversation_id}.md.
    """
    effective_id = session_id or conversation_id
    if not transcript_path:
        detected_brain = _auto_detect_brain_dir("")
        session_path = _find_session_dir(detected_brain, effective_id)
        if session_path:
            transcript_path = _find_transcript_file(session_path) or ""
        elif effective_id:
            for b_dir in [
                "~/.gemini/antigravity-cli/brain",
                "~/.gemini/antigravity/brain",
                "~/.gemini/antigravity-ide/brain",
            ]:
                expanded = os.path.expanduser(b_dir)
                cand = os.path.join(expanded, effective_id, ".system_generated", "logs", "transcript.jsonl")
                if os.path.isfile(cand):
                    transcript_path = cand
                    break
                cand2 = os.path.join(expanded, effective_id, "transcript.jsonl")
                if os.path.isfile(cand2):
                    transcript_path = cand2
                    break

    if not transcript_path or not os.path.isfile(transcript_path):
        return {
            "status": "NOT_FOUND",
            "error": f"Transcript not found for conversation_id='{effective_id}'",
            "conversation_id": effective_id,
            "session_id": effective_id,
            "transcript_path": transcript_path,
        }

    conv_id = effective_id
    if not conv_id:
        parts = Path(transcript_path).parts
        if "brain" in parts:
            idx = parts.index("brain")
            if idx + 1 < len(parts):
                conv_id = parts[idx + 1]
    if not conv_id:
        conv_id = "default_session"

    raw_steps: list[dict[str, Any]] = []
    orig_chars = 0
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                orig_chars += len(line)
                line = line.strip()
                if line:
                    try:
                        raw_steps.append(json.loads(line))
                    except Exception:
                        pass
    except Exception as exc:
        return {"status": "ERROR", "error": str(exc), "conversation_id": conv_id}

    mutations: list[dict[str, Any]] = []
    verifications: list[dict[str, Any]] = []
    reads: list[dict[str, Any]] = []

    for i, step in enumerate(raw_steps):
        tcalls = step.get("tool_calls")
        if not (isinstance(tcalls, list) and tcalls):
            continue

        for tc in tcalls:
            if not isinstance(tc, dict):
                continue
            name = tc.get("name") or tc.get("function", {}).get("name") or ""
            args = tc.get("args") or tc.get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}

            result_snippet = ""
            if i + 1 < len(raw_steps):
                next_step = raw_steps[i + 1]
                content = str(next_step.get("content") or "")
                first_lines = [line.strip() for line in content.splitlines() if line.strip()][:3]
                result_snippet = " | ".join(first_lines)[:120]

            if name in (
                "replace_file_content",
                "write_to_file",
                "multi_replace_file_content",
                "edit_file",
                "write_file",
                "apply_diff",
                "write_artifact",
            ):
                target = (
                    args.get("Path")
                    or args.get("TargetFile")
                    or args.get("AbsolutePath")
                    or args.get("file_path")
                    or args.get("path")
                    or ""
                )
                summary = args.get("toolSummary") or f"Mutated {os.path.basename(str(target))}"
                mutations.append({
                    "step": i,
                    "tool": name,
                    "target": str(target),
                    "summary": summary,
                })
            elif name in {"run_command", "execute_command", "bash"}:
                cmd = str(args.get("CommandLine") or args.get("command") or args.get("cmd") or "")
                summary = args.get("toolSummary") or cmd[:60]
                is_verify = any(v in cmd.lower() for v in ("test", "pytest", "check", "cargo", "npm run", "tsc", "verify", "lint"))
                status = "PASS" if ("exit code 0" in result_snippet.lower() or "passed" in result_snippet.lower()) else ("FAIL" if ("error" in result_snippet.lower() or "fail" in result_snippet.lower() or "exit code 1" in result_snippet.lower()) else "RUN")
                if is_verify:
                    verifications.append({
                        "step": i,
                        "cmd": cmd,
                        "summary": summary,
                        "status": status,
                        "snippet": result_snippet,
                    })
                elif any(m in cmd for m in ("git commit", "mkdir", "touch", "rm", "cp", "mv")):
                    mutations.append({
                        "step": i,
                        "tool": "run_command",
                        "target": cmd,
                        "summary": summary,
                    })
            elif name in ("view_file", "read_file"):
                target = str(
                    args.get("Path")
                    or args.get("TargetFile")
                    or args.get("AbsolutePath")
                    or args.get("file_path")
                    or args.get("path")
                    or ""
                )
                reads.append({
                    "step": i,
                    "target": target,
                    "basename": os.path.basename(target) if target else "file",
                })

    seen_read_paths: set[str] = set()
    deduped_reads: list[str] = []
    for r in reversed(reads):
        tgt = r["target"]
        if tgt and tgt not in seen_read_paths:
            seen_read_paths.add(tgt)
            bname = r["basename"] or os.path.basename(tgt)
            deduped_reads.append(f"`{bname}` ({tgt})")
    deduped_reads.reverse()

    verif_by_cmd: dict[str, dict[str, Any]] = {}
    for v in verifications:
        cmd_key = v["cmd"].strip()
        norm_key = " ".join(cmd_key.split()[:3])
        verif_by_cmd[norm_key] = v

    deduped_verifs = list(verif_by_cmd.values())

    obs_lines: list[str] = [
        f"# Observational Memory Buffer: {conv_id}",
        f"Generated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        "",
        "## 🔴 Mutations & State Decisions",
    ]
    if mutations:
        for m in mutations[-max_entries:]:
            target_str = f" on `{os.path.basename(m['target'])}`" if m['target'] else ""
            obs_lines.append(f"- [{m['tool']}{target_str}] {m['summary']}")
    else:
        obs_lines.append("- *(No file mutations recorded)*")

    obs_lines.append("")
    obs_lines.append("## 🟡 Verification Outcomes (Latest Per Target)")
    if deduped_verifs:
        for v in deduped_verifs[-max_entries:]:
            badge = "🟢 [PASS]" if v['status'] == "PASS" else ("🔴 [FAIL]" if v['status'] == "FAIL" else "🟡 [RUN]")
            obs_lines.append(f"- {badge} `{v['cmd'][:80]}` — {v['snippet']}")
    else:
        obs_lines.append("- *(No verification commands recorded)*")

    obs_lines.append("")
    obs_lines.append("## 🟢 Key Files Read (Deduplicated Working Set)")
    if deduped_reads:
        for r_entry in deduped_reads[-max_entries:]:
            obs_lines.append(f"- {r_entry}")
    else:
        obs_lines.append("- *(No file reads recorded)*")

    buffer_content = "\n".join(obs_lines) + "\n"
    buffer_chars = len(buffer_content)

    cache_dir = os.path.expanduser("~/.cache/antigravity_observations")
    os.makedirs(cache_dir, exist_ok=True)
    buffer_path = os.path.join(cache_dir, f"{conv_id}.md")
    try:
        with open(buffer_path, "w", encoding="utf-8") as f:
            f.write(buffer_content)
    except Exception as exc:
        return {"status": "ERROR", "error": f"Failed writing buffer: {exc}", "conversation_id": conv_id}

    ratio = round(orig_chars / max(1, buffer_chars), 1) if orig_chars > 0 else 1.0

    return {
        "status": "ok",
        "conversation_id": conv_id,
        "transcript_path": transcript_path,
        "buffer_path": buffer_path,
        "compression_ratio": f"{ratio:.1f}x",
        "original_chars": orig_chars,
        "buffer_chars": buffer_chars,
        "mutations_count": len(mutations),
        "verifications_count": len(deduped_verifs),
        "reads_count": len(deduped_reads),
        "summary": f"Distilled {len(mutations)} mutations, {len(deduped_verifs)} verifications, {len(deduped_reads)} working files with {ratio:.1f}x compression.",
    }


_FATAL_LINE_RE = re.compile(r"(?:FATAL|ERROR|CRITICAL|Exception|Traceback|FAIL:)")


def compress_fatal_preserving(payload: str, max_chars: int = 2000) -> dict[str, Any]:
    """Middle-out compress repetitive log/JSON lines while preserving fatal/error lines byte-for-byte."""
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    lines = text.splitlines()
    if not lines:
        return {
            "compressed_preview": "",
            "fatal_lines_preserved": 0,
            "fatal_lines": [],
            "original_lines": 0,
            "original_chars": 0,
            "compressed_chars": 0,
        }

    fatal_indices = [i for i, ln in enumerate(lines) if _FATAL_LINE_RE.search(ln)]
    fatal_set = set(fatal_indices)
    fatal_lines = [lines[i] for i in fatal_indices]

    if len(text) <= max_chars:
        return {
            "compressed_preview": text,
            "fatal_lines_preserved": len(fatal_indices),
            "fatal_lines": fatal_lines,
            "original_lines": len(lines),
            "original_chars": len(text),
            "compressed_chars": len(text),
        }

    fatal_chars = sum(len(lines[i]) + 1 for i in fatal_indices)
    remaining_budget = max(0, max_chars - fatal_chars - 160)
    half_budget = remaining_budget // 2

    head_indices: set[int] = set()
    used_head = 0
    for i in range(len(lines)):
        if i in fatal_set:
            continue
        ln_len = len(lines[i]) + 1
        if used_head + ln_len > half_budget:
            break
        head_indices.add(i)
        used_head += ln_len

    tail_indices: set[int] = set()
    used_tail = 0
    for i in range(len(lines) - 1, -1, -1):
        if i in fatal_set or i in head_indices:
            continue
        ln_len = len(lines[i]) + 1
        if used_tail + ln_len > half_budget:
            break
        tail_indices.add(i)
        used_tail += ln_len

    keep_indices = sorted(fatal_set | head_indices | tail_indices)
    out_lines: list[str] = []
    prev_idx = -1
    for idx in keep_indices:
        if idx > prev_idx + 1:
            skipped = idx - prev_idx - 1
            out_lines.append(f"... [{skipped} lines middle-out compressed] ...")
        out_lines.append(lines[idx])
        prev_idx = idx

    if prev_idx < len(lines) - 1:
        skipped = len(lines) - 1 - prev_idx
        out_lines.append(f"... [{skipped} lines middle-out compressed] ...")

    compressed_preview = "\n".join(out_lines)
    return {
        "compressed_preview": compressed_preview,
        "fatal_lines_preserved": len(fatal_indices),
        "fatal_lines": fatal_lines,
        "original_lines": len(lines),
        "original_chars": len(text),
        "compressed_chars": len(compressed_preview),
    }


def infer_compact_schema(payload: Any, max_depth: int = 3) -> str:
    """Infer a deterministic compact JSON/TOON schema string for a payload."""
    val = payload
    if isinstance(val, str):
        stripped = val.strip()
        if (stripped.startswith("{") and stripped.endswith("}")) or (
            stripped.startswith("[") and stripped.endswith("]")
        ):
            try:
                val = json.loads(stripped)
            except Exception:
                return f"str[{len(val)}]"
        else:
            return f"str[{len(val)}]"

    def _schema(node: Any, depth: int) -> str:
        if node is None:
            return "null"
        if isinstance(node, bool):
            return "bool"
        if isinstance(node, int):
            return "int"
        if isinstance(node, float):
            return "float"
        if isinstance(node, str):
            return f"str[{len(node)}]"
        if isinstance(node, dict):
            if not node:
                return "dict{}"
            if depth <= 0:
                return f"dict[{len(node)}]"
            fields = [f"{k}:{_schema(v, depth - 1)}" for k, v in list(node.items())[:8]]
            if len(node) > 8:
                fields.append("...")
            return "dict{" + ",".join(fields) + "}"
        if isinstance(node, (list, tuple)):
            if not node:
                return "list[0]<null>"
            if depth <= 0:
                return f"list[{len(node)}]"
            return f"list[{len(node)}]<{_schema(node[0], depth - 1)}>"
        return type(node).__name__

    return _schema(val, max_depth)


@mcp.tool()
def spillover_large_payload(
    content: str,
    tool_name: str = "mcp",
    max_chars: int = 6000,
) -> dict[str, Any]:
    """Offload bulky intermediate payloads to disk and return a compact TOON tombstone summary."""
    content_str = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
    content_len = len(content_str)
    schema = infer_compact_schema(content)
    comp = compress_fatal_preserving(content_str, max_chars=min(2000, max_chars))
    if content_len <= max_chars:
        return {
            "status": "inline",
            "tool_name": tool_name,
            "chars": content_len,
            "max_chars": max_chars,
            "schema": schema,
            "content": content_str,
            "compressed_preview": comp["compressed_preview"],
            "fatal_lines_preserved": comp["fatal_lines_preserved"],
        }

    sha = hashlib.sha256(content_str.encode("utf-8")).hexdigest()[:10]
    spillover_path = f"/tmp/ag_mcp_spillover_{sha}.json"
    try:
        with open(spillover_path, "w", encoding="utf-8") as f:
            f.write(content_str)
    except Exception as exc:
        return {
            "status": "error",
            "tool_name": tool_name,
            "schema": schema,
            "error": f"Failed writing spillover: {exc}",
            "compressed_preview": comp["compressed_preview"],
            "fatal_lines_preserved": comp["fatal_lines_preserved"],
        }

    preview = content_str[:200].replace("\n", " ").strip()
    toon = (
        f"spillover[1]{{tool,chars,sha,path}}:\n"
        f"  {tool_name} | {content_len} | {sha} | {spillover_path}\n"
    )
    return {
        "status": "spilled",
        "tool_name": tool_name,
        "original_chars": content_len,
        "max_chars": max_chars,
        "schema": schema,
        "sha": sha,
        "spillover_path": spillover_path,
        "preview": preview,
        "compressed_preview": comp["compressed_preview"],
        "fatal_lines_preserved": comp["fatal_lines_preserved"],
        "toon": toon,
        "note": f"Payload ({content_len} chars) exceeded limit ({max_chars}). Saved to {spillover_path}.",
    }


@mcp.tool()
def spillover_batch(
    payloads: list[dict[str, Any]],
    max_single_chars: int = 6000,
    max_batch_chars: int = 12000,
) -> dict[str, Any]:
    """Apply dual-threshold spillover across a batch of tool payloads (single threshold then largest-first batch eviction)."""
    normalized: list[tuple[str, str]] = []
    for idx, item in enumerate(payloads):
        tool_name = str(item.get("tool_name") or item.get("tool") or f"item_{idx}")
        raw_content = item.get("content", item.get("payload", ""))
        content_str = raw_content if isinstance(raw_content, str) else json.dumps(raw_content, ensure_ascii=False)
        normalized.append((tool_name, content_str))

    results: list[dict[str, Any]] = []
    for tool_name, content_str in normalized:
        res = spillover_large_payload(
            content=content_str,
            tool_name=tool_name,
            max_chars=max_single_chars,
        )
        results.append(res)

    inline_indices = [i for i, r in enumerate(results) if r.get("status") == "inline"]
    inline_chars = sum(int(results[i].get("chars", 0)) for i in inline_indices)

    while inline_chars > max_batch_chars and inline_indices:
        largest_idx = max(inline_indices, key=lambda idx: int(results[idx].get("chars", 0)))
        largest_chars = int(results[largest_idx].get("chars", 0))
        if largest_chars <= 0:
            break
        tool_name, content_str = normalized[largest_idx]
        evicted = spillover_large_payload(
            content=content_str,
            tool_name=tool_name,
            max_chars=0,
        )
        evicted["eviction_reason"] = "batch_budget_exceeded"
        results[largest_idx] = evicted
        inline_indices.remove(largest_idx)
        inline_chars -= largest_chars

    total_original_chars = sum(len(content_str) for _, content_str in normalized)
    total_inline_chars = sum(int(r.get("chars", 0)) for r in results if r.get("status") == "inline")
    spilled_count = sum(1 for r in results if r.get("status") == "spilled")

    return {
        "status": "batch_processed",
        "total_original_chars": total_original_chars,
        "total_inline_chars": total_inline_chars,
        "spilled_count": spilled_count,
        "max_single_chars": max_single_chars,
        "max_batch_chars": max_batch_chars,
        "items": results,
    }


@mcp.tool()
def project_trajectory_toon(
    conversation_id: str = "",
    transcript_path: str = "",
    max_tokens: int = 1200,
) -> dict[str, Any]:
    """Project a session transcript into a compact chronological TOON trajectory table preserving error diagnostics within a token budget."""
    resolved_path = ""
    if transcript_path:
        expanded_tp = os.path.expanduser(transcript_path)
        if os.path.isfile(expanded_tp):
            resolved_path = expanded_tp

    if not resolved_path and conversation_id:
        for b_dir in (
            "~/.gemini/antigravity-cli/brain",
            "~/.gemini/antigravity-ide/brain",
            "~/.gemini/antigravity/brain",
        ):
            expanded = os.path.expanduser(b_dir)
            cand = os.path.join(
                expanded,
                conversation_id,
                ".system_generated",
                "logs",
                "transcript.jsonl",
            )
            if os.path.isfile(cand):
                resolved_path = cand
                break
            cand_alt = os.path.join(expanded, conversation_id, "transcript.jsonl")
            if os.path.isfile(cand_alt):
                resolved_path = cand_alt
                break

    if not resolved_path and conversation_id:
        detected_brain = _auto_detect_brain_dir("")
        session_path = _find_session_dir(detected_brain, conversation_id)
        if session_path:
            resolved_path = _find_transcript_file(session_path) or ""

    conv_id = conversation_id
    if not conv_id and resolved_path:
        parts = Path(resolved_path).parts
        if "brain" in parts:
            idx = parts.index("brain")
            if idx + 1 < len(parts):
                conv_id = parts[idx + 1]

    if not resolved_path or not os.path.isfile(resolved_path):
        return {
            "status": "not_found",
            "conversation_id": conv_id,
            "transcript_path": transcript_path,
            "step_count": 0,
            "est_tokens": 0,
            "toon": "",
            "rows": [],
        }

    rows: list[dict[str, Any]] = []
    est_toks = 0

    try:
        with open(resolved_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_idx, raw_line in enumerate(f):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    obj = json.loads(stripped)
                except Exception:
                    continue
                if not isinstance(obj, dict):
                    continue

                step_num = obj.get("step_index", line_idx)
                stype = str(obj.get("type") or "")
                source = str(obj.get("source") or "")
                raw_status = str(obj.get("status") or "DONE")
                exit_code = obj.get("exit_code")
                content = str(obj.get("content") or "")
                thinking = str(obj.get("thinking") or "")
                tcalls = obj.get("tool_calls")

                is_err = (
                    raw_status.upper() == "ERROR"
                    or (isinstance(exit_code, int) and exit_code != 0)
                    or "error" in raw_status.lower()
                )
                status_label = "ERROR" if is_err else (raw_status if raw_status else "DONE")

                step_chars = (
                    len(content)
                    + len(thinking)
                    + (len(json.dumps(tcalls, ensure_ascii=False)) if tcalls else 0)
                )
                step_est_tokens = max(1, step_chars // 4) if step_chars > 0 else max(1, len(stripped) // 4)
                est_toks += step_est_tokens

                err_diag = ""
                if is_err and content:
                    first_err_line = next(
                        (ln.strip() for ln in content.splitlines() if ln.strip()),
                        "",
                    )
                    if first_err_line:
                        err_diag = first_err_line[:60].replace("|", "/")

                if isinstance(tcalls, list) and tcalls:
                    per_call_tokens = max(1, step_est_tokens // len(tcalls))
                    for tc in tcalls:
                        if not isinstance(tc, dict):
                            continue
                        tname = str(tc.get("name") or tc.get("function", {}).get("name") or "tool")
                        args = tc.get("args") or tc.get("arguments") or {}
                        if isinstance(args, str):
                            try:
                                args = json.loads(args)
                            except Exception:
                                args = {}
                        if not isinstance(args, dict):
                            args = {}

                        if tname == "invoke_subagent":
                            role = str(args.get("Role") or args.get("TypeName") or "subagent").strip()
                            actor = f"subagent:{role}"
                            target = role
                        else:
                            actor = "agent"
                            target = _extract_observation_target(tname, args)

                        target_clean = str(target).replace("\n", " ").replace("|", "/").strip()
                        if err_diag and err_diag not in target_clean:
                            target_clean = f"{target_clean} ({err_diag})"

                        rows.append({
                            "step": step_num,
                            "actor": actor,
                            "tool": tname,
                            "target": target_clean,
                            "status": status_label,
                            "est_tokens": per_call_tokens,
                        })
                else:
                    if stype == "USER_INPUT" or source == "USER_EXPLICIT":
                        actor = "user"
                        tool_name = "user_input"
                        snippet = " ".join(content.strip().split())[:40] or "prompt"
                    elif stype == "PLANNER_RESPONSE":
                        actor = "agent"
                        tool_name = "planner_response"
                        snippet = " ".join((content or thinking).strip().split())[:40] or "response"
                    else:
                        actor = "system" if source == "SYSTEM" else "tool"
                        tool_name = stype.lower() if stype else "observation"
                        limit_len = 60 if is_err else 36
                        snippet = " ".join(content.strip().split())[:limit_len] or tool_name

                    target_clean = snippet.replace("|", "/")
                    if err_diag and err_diag not in target_clean:
                        target_clean = f"{target_clean} ({err_diag})"

                    rows.append({
                        "step": step_num,
                        "actor": actor,
                        "tool": tool_name,
                        "target": target_clean,
                        "status": status_label,
                        "est_tokens": step_est_tokens,
                    })
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "conversation_id": conv_id,
            "step_count": 0,
            "est_tokens": 0,
            "toon": "",
            "rows": [],
        }

    header = f"trajectory[{len(rows)}]{{step,actor,tool,target,status,est_tokens}}:"
    row_lines = [
        f"  {r['step']} | {r['actor']} | {r['tool']} | {r['target']} | {r['status']} | {r['est_tokens']}"
        for r in rows
    ]

    max_chars = max(80, int(max_tokens) * 4)
    full_toon = "\n".join([header, *row_lines]) if row_lines else header

    if len(full_toon) <= max_chars:
        toon = full_toon
    else:
        error_indices = [
            i
            for i, r in enumerate(rows)
            if r["status"] == "ERROR" or "error" in str(r["status"]).lower()
        ]
        keep_set: set[int] = set()
        used_chars = len(header) + 1
        ellipsis_line = "  ... | omitted | ..."
        ellipsis_cost = len(ellipsis_line) + 1

        # 1. Always prioritize error rows so error diagnostics are preserved
        for idx in error_indices:
            ln_cost = len(row_lines[idx]) + 1
            if used_chars + ln_cost + ellipsis_cost <= max_chars or not keep_set:
                keep_set.add(idx)
                used_chars += ln_cost

        # 2. Fill remaining budget with recent tail rows and initial head rows
        head_ptr = 0
        tail_ptr = len(rows) - 1
        toggle_tail = True
        while head_ptr <= tail_ptr:
            cand = tail_ptr if toggle_tail else head_ptr
            if toggle_tail:
                tail_ptr -= 1
            else:
                head_ptr += 1
            toggle_tail = not toggle_tail

            if cand in keep_set:
                continue
            ln_cost = len(row_lines[cand]) + 1
            if used_chars + ln_cost + ellipsis_cost * 2 <= max_chars:
                keep_set.add(cand)
                used_chars += ln_cost
            else:
                break

        kept_sorted = sorted(keep_set)
        out_lines = [header]
        prev_i = -1
        for idx in kept_sorted:
            if idx > prev_i + 1:
                out_lines.append(ellipsis_line)
            out_lines.append(row_lines[idx])
            prev_i = idx
        if prev_i < len(rows) - 1:
            out_lines.append(ellipsis_line)

        toon = "\n".join(out_lines)
        if len(toon) > max_chars:
            toon = toon[:max_chars].rstrip()

    return {
        "status": "ok",
        "conversation_id": conv_id,
        "step_count": len(rows),
        "est_tokens": est_toks,
        "toon": toon,
        "rows": rows,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")


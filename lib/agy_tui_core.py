#!/usr/bin/env python3
"""
agy_tui_core.py - Shared Semantic Core & Rendering Primitives for Antigravity TUI.
Provides canonical paths, CachyOS Emerald Dark palette, Unicode width calculation,
smooth gauges, worktree discovery, conversation locks, and inotify watching.
"""

from __future__ import annotations

import contextlib
import ctypes
import ctypes.util
import fcntl
import json
import os
import re
import select
import shutil
import sqlite3
import subprocess
import sys
import time
import unicodedata
from collections import defaultdict, deque
from typing import Callable

# -----------------------------------------------------------------------------
# 1. Canonical Paths
# -----------------------------------------------------------------------------
LIVE_STATE_PATH = os.path.expanduser("~/.cache/antigravity_live_state.json")
LIVE_STATE_LOCK_PATH = os.path.expanduser("~/.cache/antigravity_live_state.lock")
SIDEBAR_MODE_PATH = os.path.expanduser("~/.cache/antigravity_sidebar_mode")
CACHE_PATH = os.path.expanduser("~/.cache/antigravity_quota.json")
PERSISTENT_CACHE_PATH = os.path.expanduser("~/.gemini/antigravity-cli/quota_cache.json")
CACHE_PATHS = (PERSISTENT_CACHE_PATH, CACHE_PATH)
LOCK_PATH = os.path.expanduser("~/.cache/antigravity_quota.lock")
PRESENCE_DIR = os.path.expanduser("~/.gemini/antigravity-cli/presence")
DB_PATH = os.path.expanduser("~/.gemini/antigravity-cli/conversation_summaries.db")
BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity-cli/brain")
STATUSLINE_BIN = os.path.expanduser("~/.local/bin/agy-statusline")
SQUAD_BIN = os.path.expanduser("~/.local/bin/agy-squad")
SIDEBAR_BIN = os.path.expanduser("~/.local/bin/agy-sidebar")
MCP_CONFIG_PATH = os.path.expanduser("~/.gemini/config/mcp_config.json")
MCP_TOOLS_DIR = os.path.expanduser("~/.gemini/antigravity-cli/mcp")

# -----------------------------------------------------------------------------
# 2. CachyOS Blue Dark TrueColor Constants
# -----------------------------------------------------------------------------
C_COMMENT = "\033[38;2;148;156;166m"   # Slate Muted (#949ca6)
C_CYAN = "\033[38;2;96;165;250m"        # Sky Blue (#60a5fa)
C_GREEN = "\033[38;2;39;174;96m"        # Positive Green (#27ae60)
C_ORANGE = "\033[38;2;246;116;0m"      # Neutral Orange (#f67400)
C_PINK = "\033[38;2;245;194;231m"      # Pink (#f5c2e7)
C_PURPLE = "\033[38;2;59;130;246m"     # Accent Blue (#3b82f6)
C_RED = "\033[38;2;235;96;107m"        # Negative Red (#eb606b)
C_YELLOW = "\033[38;2;247;235;149m"    # Focus Yellow (#f7eb95)
C_WHITE = "\033[38;2;236;240;244m"     # Crisp Off-White (#ecf0f4)
C_ROSEWATER = "\033[38;2;245;224;220m" # Rosewater (#f5e0dc)
C_SURFACE = "\033[48;2;32;37;45m"      # Deep Slate Surface (#20252d)
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_REV = "\033[7m"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# -----------------------------------------------------------------------------
# 3. Semantic Agent States & Badges
# -----------------------------------------------------------------------------
STATE_BLOCKED = f"{C_ORANGE}{C_BOLD}⚠{C_RESET}"
STATE_ACTIVE = f"{C_PURPLE}⠋{C_RESET}"
STATE_WAITING = f"{C_CYAN}◐{C_RESET}"
STATE_HEALING = f"{C_YELLOW}🩹{C_RESET}"
STATE_DONE = f"{C_GREEN}✓{C_RESET}"
STATE_ERR = f"{C_RED}✗{C_RESET}"
STATE_IDLE = f"{C_COMMENT}○{C_RESET}"

STATE_PRIORITY: dict[str, int] = {
    "blocked": 0,
    "healing": 1,
    "errored": 1,
    "active": 2,
    "waiting": 3,
    "done": 4,
    "idle": 5,
}

SPINNER_FRAMES: tuple[str, ...] = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


def get_spinner_frame(tick: float | None = None) -> str:
    """Return animated Braille spinner frame based on tick time."""
    t = time.time() if tick is None else float(tick)
    idx = int(t * 10.0) % len(SPINNER_FRAMES)
    return SPINNER_FRAMES[idx]


def classify_agent_state(
    raw_status: str,
    state_detail: str = "",
    is_locked: bool = False,
    is_healing: bool = False,
) -> str:
    """Classify agent lifecycle into one of: blocked, healing, errored, active, waiting, done, idle."""
    st = (raw_status or "").strip().lower()
    detail = (state_detail or "").strip().lower()

    # 1. Healing / loop retry state
    if (
        is_healing
        or "healing" in detail
        or "round " in detail
        or "loop" in detail
        or "retry" in detail
        or "heal" in st
    ):
        return "healing"

    # 2. Blocked / waiting for human input / approval
    if (
        st in ("waiting_for_input", "blocked", "approval_needed", "requires_action", "prompt")
        or "blocked" in st
        or ("waiting" in st and "input" in st)
        or "approval" in detail
    ):
        return "blocked"

    # 3. Errored / failed
    if (
        st in ("errored", "failed", "error", "crash", "crashed")
        or "error" in st
        or "fail" in st
    ):
        return "errored"

    # 4. Terminal completion / done
    if (
        st in (
            "completed",
            "done",
            "terminated",
            "killed",
            "cancelled",
            "canceled",
            "success",
            "cascade_run_status_idle",
        )
        or "completed" in st
    ):
        return "done"

    # 5. Waiting for message / dependency
    if st in ("waiting", "waiting_for_message", "waiting_for_dependents"):
        return "waiting"

    # 6. Actively running
    if (
        st in ("running", "active", "busy", "cascade_run_status_running", "subagent_state_alive")
        or "running" in st
        or is_locked
    ):
        return "active"

    # 7. Idle / unspecified
    if st in ("idle", "unspecified", ""):
        return "active" if is_locked else "idle"

    if "wait" in st:
        return "waiting"

    return "active" if is_locked else "idle"


def format_state_badge(
    state: str,
    tick: float | None = None,
    compact: bool = False,
) -> tuple[str, str]:
    """
    Format a state into (icon_with_color, text_with_color).
    If compact is True, returns short mnemonic label (3-4 chars).
    """
    norm_state = (state or "idle").strip().lower()
    if norm_state == "blocked":
        icon = f"{C_ORANGE}{C_BOLD}⚠{C_RESET}"
        lbl = f"{C_ORANGE}{C_BOLD}blk{C_RESET}" if compact else f"{C_ORANGE}{C_BOLD}BLOCKED{C_RESET}"
    elif norm_state == "healing":
        icon = f"{C_YELLOW}🩹{C_RESET}"
        lbl = f"{C_YELLOW}heal{C_RESET}" if compact else f"{C_YELLOW}HEALING{C_RESET}"
    elif norm_state == "errored":
        icon = f"{C_RED}✗{C_RESET}"
        lbl = f"{C_RED}err{C_RESET}" if compact else f"{C_RED}ERROR{C_RESET}"
    elif norm_state == "active":
        frame = get_spinner_frame(tick)
        icon = f"{C_PURPLE}{frame}{C_RESET}"
        lbl = f"{C_PURPLE}run{C_RESET}" if compact else f"{C_PURPLE}RUNNING{C_RESET}"
    elif norm_state == "waiting":
        icon = f"{C_CYAN}◐{C_RESET}"
        lbl = f"{C_CYAN}wait{C_RESET}" if compact else f"{C_CYAN}WAITING{C_RESET}"
    elif norm_state == "done":
        icon = f"{C_GREEN}✓{C_RESET}"
        lbl = f"{C_COMMENT}done{C_RESET}" if compact else f"{C_COMMENT}DONE{C_RESET}"
    else:  # idle
        icon = f"{C_COMMENT}○{C_RESET}"
        lbl = f"{C_COMMENT}idle{C_RESET}" if compact else f"{C_COMMENT}IDLE{C_RESET}"
    return (icon, lbl)


# -----------------------------------------------------------------------------
# 4. Unicode Width & ANSI Slicing
# -----------------------------------------------------------------------------
_SINGLE_WIDTH_CHARS = frozenset(
    "▰▱◆●○◐◑◒◓⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏█▉▊▋▌▍▎▏░▒▓✓✗⚠↻⏱󰘳└─├│━…"
)


def strip_ansi(s: str) -> str:
    """Strip ANSI escape sequences from string."""
    return ANSI_RE.sub("", s)


def char_cell_width(ch: str) -> int:
    """
    Calculate terminal column cell width for a single character or grapheme.
    0 for combining / zero-width / control chars.
    1 for standard ASCII, box drawing, geometric symbols, and NerdFont PUA.
    2 for East Asian Wide/Fullwidth and wide emojis.
    """
    if not ch:
        return 0
    cp = ord(ch[0])

    # 1. Zero-width and control characters
    if cp in (0x200B, 0x200C, 0x200D, 0xFEFF):  # ZWSP, ZWNJ, ZWJ, BOM
        return 0
    cat = unicodedata.category(ch[0])
    if cat in ("Mn", "Me", "Cf", "Cc", "Cs") or unicodedata.combining(ch[0]):
        return 0

    # 2. Explicit single-width TUI, Braille, and geometric overrides
    if ch[0] in _SINGLE_WIDTH_CHARS:
        return 1

    # 3. NerdFont Private Use Areas (PUA) are 1 cell in patched monospace terminals
    if (0xE000 <= cp <= 0xF8FF) or (0xF0000 <= cp <= 0xFFFFD) or (0x100000 <= cp <= 0x10FFFD):
        return 1

    # 4. Explicit wide emoji code points and ranges
    if (0x1F300 <= cp <= 0x1FAFF) or cp == 0x26A1 or cp == 0x1FA79:
        return 2

    # 5. East Asian Width classification
    eaw = unicodedata.east_asian_width(ch[0])
    if eaw in ("W", "F"):
        return 2

    # 6. Default to single-width
    return 1


def visible_len(s: str) -> int:
    """Return visible terminal cell width of string (ignoring ANSI escapes)."""
    plain = strip_ansi(s)
    return sum(char_cell_width(c) for c in plain)


def format_line(text: str, width: int, pad_right: bool = False) -> str:
    """
    Slice text cleanly on character cell boundaries to fit exactly within width.
    Appends ellipsis '…' and resets ANSI codes on truncation.
    Optionally pads with trailing spaces to fill exact width.
    """
    if width <= 0:
        return ""
    vlen = visible_len(text)
    if vlen <= width:
        if pad_right and vlen < width:
            return text + (" " * (width - vlen))
        return text

    cutoff = max(0, width - 1)
    vis = 0
    res: list[str] = []
    i = 0
    n = len(text)
    while i < n and vis < cutoff:
        m = ANSI_RE.match(text, i)
        if m:
            res.append(m.group(0))
            i = m.end()
            continue
        ch = text[i]
        w = char_cell_width(ch)
        if vis + w > cutoff:
            break
        res.append(ch)
        vis += w
        i += 1

    res.append("…")
    res.append(C_RESET)
    vis += 1
    if pad_right and vis < width:
        res.append(" " * (width - vis))
    return "".join(res)


# -----------------------------------------------------------------------------
# 5. Smooth Gauges & Sparklines
# -----------------------------------------------------------------------------
_EIGHTHS = ("", "▏", "▎", "▍", "▌", "▋", "▊", "▉")
_BRAILLE_LEFT = (0, 0x40, 0x44, 0x46, 0x47)
_BRAILLE_RIGHT = (0, 0x80, 0xA0, 0xB0, 0xB8)


def _gradient_color(pct: float, invert: bool = False) -> str:
    """Interpolate RGB linearly across the CachyOS semantic gradient."""
    p = max(0.0, min(100.0, float(pct)))
    if not invert:
        if p <= 65.0:
            t = p / 65.0
            r = int(round(39 + (247 - 39) * t))
            g = int(round(174 + (235 - 174) * t))
            b = int(round(96 + (149 - 96) * t))
        else:
            t = (p - 65.0) / 35.0
            r = int(round(247 + (235 - 247) * t))
            g = int(round(235 + (96 - 235) * t))
            b = int(round(149 + (107 - 149) * t))
    else:
        if p <= 35.0:
            t = p / 35.0
            r = int(round(235 + (247 - 235) * t))
            g = int(round(96 + (235 - 96) * t))
            b = int(round(107 + (149 - 107) * t))
        else:
            t = (p - 35.0) / 65.0
            r = int(round(247 + (39 - 247) * t))
            g = int(round(235 + (174 - 235) * t))
            b = int(round(149 + (96 - 149) * t))
    return f"\033[38;2;{r};{g};{b}m"


def render_gradient_gauge(pct: float, cells: int = 5, invert: bool = False) -> str:
    """
    Render high-resolution TrueColor RGB linear gradient smooth gauge.
    Uses fractional eighth-blocks for filled portion and dimmed ░ for empty cells.
    Linearly interpolates RGB per cell across CachyOS semantic gradient.
    """
    if cells <= 0:
        return ""
    clamped = max(0.0, min(100.0, float(pct)))
    total_units = int(round((clamped / 100.0) * (cells * 8)))

    parts: list[str] = []
    dim_empty = "\033[38;2;75;82;96m"

    for i in range(cells):
        cell_pct = (i / max(1, cells - 1)) * 100.0
        c_code = _gradient_color(cell_pct, invert=invert)

        cell_start = i * 8
        cell_units = max(0, min(8, total_units - cell_start))

        if cell_units == 8:
            parts.append(f"{c_code}█")
        elif cell_units > 0:
            parts.append(f"{c_code}{_EIGHTHS[cell_units]}")
        else:
            parts.append(f"{dim_empty}░")

    parts.append(C_RESET)
    return "".join(parts)


def render_smooth_gauge(
    pct: float,
    cells: int = 5,
    style: str = "smooth",
    invert_colors: bool = False,
) -> str:
    """
    Render high-resolution gauge:
    - style="smooth" / "gradient": 2.5% precision TrueColor RGB linear gradient gauge.
    - style="blocks": half-step 10% precision using ▰, ◐, ▱.
    """
    if style in ("smooth", "gradient"):
        return render_gradient_gauge(pct, cells=cells, invert=invert_colors)
    else:
        clamped = max(0.0, min(100.0, float(pct)))
        total_half = int(round((clamped / 100.0) * (cells * 2)))
        full_cells = min(cells, total_half // 2)
        has_half = (total_half % 2) == 1
        if full_cells == cells:
            return "▰" * cells
        partial = "◐" if has_half else ""
        empty_count = max(0, cells - full_cells - (1 if partial else 0))
        return ("▰" * full_cells) + partial + ("▱" * empty_count)


def render_braille_sparkline(values: list[float], width: int = 6) -> str:
    """
    Render a 2x4 sub-pixel Braille sparkline colored in C_CYAN.
    Each character cell encodes 2 horizontal samples (4 vertical dot levels each).
    Pads or takes the last width * 2 samples from values.
    """
    if width <= 0:
        return ""
    num_samples = width * 2
    raw = [float(v) for v in values] if values else []
    if len(raw) < num_samples:
        samples = [0.0] * (num_samples - len(raw)) + raw
    else:
        samples = raw[-num_samples:]

    max_v = max(samples) if samples else 0.0
    norm_max = max(max_v, 100.0) if max_v <= 100.0 else max_v
    if norm_max <= 0.0:
        norm_max = 100.0

    chars: list[str] = []
    for i in range(width):
        lv = samples[i * 2]
        rv = samples[i * 2 + 1]
        l_ratio = max(0.0, min(1.0, lv / norm_max))
        r_ratio = max(0.0, min(1.0, rv / norm_max))
        l_lvl = int(round(l_ratio * 4.0))
        r_lvl = int(round(r_ratio * 4.0))
        cp = 0x2800 + _BRAILLE_LEFT[l_lvl] + _BRAILLE_RIGHT[r_lvl]
        chars.append(chr(cp))

    return f"{C_CYAN}{''.join(chars)}{C_RESET}"


# -----------------------------------------------------------------------------
# 6. Git Worktree & Lock Helpers
# -----------------------------------------------------------------------------
_GIT_WORKTREE_CACHE: dict[str, tuple[float, list[dict]]] = {}


def get_git_worktrees(proj_dir: str) -> list[dict]:
    """
    Discover git worktrees for proj_dir using `git worktree list --porcelain`.
    Cached for 3.0s with a 0.25s execution timeout.
    Returns list of dicts: [{"path": str, "branch": str, "short": str, "is_main": bool}]
    """
    if not proj_dir or not os.path.exists(proj_dir):
        return []
    now = time.time()
    cached = _GIT_WORKTREE_CACHE.get(proj_dir)
    if cached and (now - cached[0] < 3.0):
        return cached[1]

    worktrees: list[dict] = []
    try:
        res = subprocess.run(
            ["git", "-C", proj_dir, "worktree", "list", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=0.25,
            check=False,
        )
        if res.returncode == 0 and res.stdout:
            current_wt: dict = {}
            for line in res.stdout.splitlines():
                line = line.strip()
                if not line:
                    if current_wt.get("path"):
                        worktrees.append(current_wt)
                        current_wt = {}
                    continue
                if line.startswith("worktree "):
                    if current_wt.get("path"):
                        worktrees.append(current_wt)
                        current_wt = {}
                    wt_path = line[9:].strip()
                    is_main = len(worktrees) == 0
                    current_wt = {
                        "path": wt_path,
                        "branch": "",
                        "short": "",
                        "is_main": is_main,
                    }
                elif line.startswith("branch "):
                    ref = line[7:].strip()
                    br = ref.replace("refs/heads/", "")
                    current_wt["branch"] = br
                    current_wt["short"] = f"wt:{br}"
                elif line == "detached":
                    if not current_wt.get("branch"):
                        current_wt["branch"] = "detached"
                    if not current_wt.get("short"):
                        current_wt["short"] = "wt:detached"
                elif line.startswith("HEAD "):
                    h = line[5:].strip()[:7]
                    if not current_wt.get("short") or current_wt.get("short") == "wt:detached":
                        current_wt["short"] = f"wt:{h}"
            if current_wt.get("path"):
                worktrees.append(current_wt)
    except Exception:
        pass

    _GIT_WORKTREE_CACHE[proj_dir] = (now, worktrees)
    return worktrees


_LOCKED_CIDS_CACHE: tuple[float, set[str]] = (0.0, set())
_LAST_PRUNE_TS: float = 0.0


def get_locked_conversation_ids(force: bool = False) -> set[str]:
    """
    Inspect presence lockfiles to find all actively running conversation IDs.
    Uses a 2.0-second in-memory cache and prunes unlocked stale lockfiles older than 7 days once per 300s.
    """
    global _LOCKED_CIDS_CACHE, _LAST_PRUNE_TS
    now = time.time()
    if not force and (now - _LOCKED_CIDS_CACHE[0] < 2.0):
        return _LOCKED_CIDS_CACHE[1]

    locked_ids: set[str] = set()
    if not os.path.isdir(PRESENCE_DIR):
        _LOCKED_CIDS_CACHE = (now, locked_ids)
        return locked_ids

    do_prune = (now - _LAST_PRUNE_TS > 300.0)
    try:
        with os.scandir(PRESENCE_DIR) as it:
            for entry in it:
                if not entry.name.endswith(".lock"):
                    continue
                try:
                    st = entry.stat()
                    age = now - st.st_mtime
                    try:
                        fd = os.open(entry.path, os.O_RDONLY)
                        try:
                            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            fcntl.flock(fd, fcntl.LOCK_UN)
                            # Lock acquired: not running. Prune if stale.
                            if do_prune and age > 604800.0:
                                try:
                                    os.unlink(entry.path)
                                except Exception:
                                    pass
                        except (BlockingIOError, OSError):
                            # Lock could not be acquired: actively running!
                            locked_ids.add(entry.name[:-5])
                        finally:
                            os.close(fd)
                    except Exception:
                        pass
                except Exception:
                    pass
        if do_prune:
            _LAST_PRUNE_TS = now
    except Exception:
        pass

    _LOCKED_CIDS_CACHE = (now, locked_ids)
    return locked_ids


@contextlib.contextmanager
def connect_db_ro(db_path: str = DB_PATH):
    """
    Safely open a read-only SQLite connection, ensuring it is ALWAYS closed
    in a finally block to prevent file descriptor leaks.
    Yields None if the file does not exist or connection fails.
    """
    if not db_path or not os.path.isfile(db_path):
        yield None
        return
    con = None
    try:
        uri = f"file:{db_path}?mode=ro"
        con = sqlite3.connect(uri, uri=True, timeout=1.0)
        yield con
    except Exception:
        yield None
    finally:
        if con is not None:
            try:
                con.close()
            except Exception:
                pass


# -----------------------------------------------------------------------------
# 7. Live State & Ground-Truth Readers
# -----------------------------------------------------------------------------
_SESSION_KEY_CACHE: tuple[float, str] = (0.0, "")


def get_current_session_key() -> str:
    """
    Query current tmux session name or pane id for session state partitioning.
    Uses a 2.0s cache when querying tmux display-message.
    """
    global _SESSION_KEY_CACHE
    now = time.time()
    if now - _SESSION_KEY_CACHE[0] < 2.0 and _SESSION_KEY_CACHE[1]:
        return _SESSION_KEY_CACHE[1]

    sk = ""
    if os.environ.get("TMUX"):
        try:
            res = subprocess.run(
                ["tmux", "display-message", "-p", "#S"],
                capture_output=True,
                text=True,
                timeout=0.1,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                sk = res.stdout.strip()
        except Exception:
            pass

    if not sk:
        sk = os.environ.get("TMUX_PANE", "")

    _SESSION_KEY_CACHE = (now, sk)
    return sk


def update_live_state_atomic(mutator_fn: Callable[[dict], dict]) -> dict:
    """
    Atomically update LIVE_STATE_PATH under exclusive fcntl.flock on LIVE_STATE_LOCK_PATH.
    Applies mutator_fn to the current data dict, writes to a temp file, and os.replace-s.
    Does NOT unlink LIVE_STATE_LOCK_PATH.
    """
    lock_dir = os.path.dirname(LIVE_STATE_LOCK_PATH)
    if not os.path.exists(lock_dir):
        os.makedirs(lock_dir, exist_ok=True)
    lock_fd = os.open(LIVE_STATE_LOCK_PATH, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        current_data: dict = {}
        if os.path.exists(LIVE_STATE_PATH):
            try:
                with open(LIVE_STATE_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    current_data = loaded
            except Exception:
                current_data = {}

        updated_data = mutator_fn(current_data)
        if not isinstance(updated_data, dict):
            updated_data = current_data

        tmp_path = f"{LIVE_STATE_PATH}.tmp.{os.getpid()}"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, indent=2)
        os.replace(tmp_path, LIVE_STATE_PATH)
        return updated_data
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            os.close(lock_fd)
        except Exception:
            pass


def get_sidebar_mode(state: dict | None = None) -> str:
    """
    Get sidebar mode ('rail' or 'full').
    Checks state dict first, then SIDEBAR_MODE_PATH, defaulting to 'full'.
    """
    if state is None:
        state = read_live_state()
    mode = (state.get("sidebar_mode") or "").strip().lower()
    if mode in ("rail", "full"):
        return mode
    if os.path.exists(SIDEBAR_MODE_PATH):
        try:
            with open(SIDEBAR_MODE_PATH, "r", encoding="utf-8") as f:
                val = f.read().strip().lower()
                if val in ("rail", "full"):
                    return val
        except Exception:
            pass
    return "full"


def set_sidebar_mode(mode: str, session_key: str = "") -> None:
    """
    Persist sidebar mode ('rail' or 'full') to SIDEBAR_MODE_PATH and atomically in LIVE_STATE_PATH.
    """
    mode = "rail" if mode == "rail" else "full"
    try:
        os.makedirs(os.path.dirname(SIDEBAR_MODE_PATH), exist_ok=True)
        with open(SIDEBAR_MODE_PATH, "w", encoding="utf-8") as f:
            f.write(mode)
    except Exception:
        pass

    sk = session_key or get_current_session_key()

    def mutator(data: dict) -> dict:
        data["sidebar_mode"] = mode
        data["sidebar_hidden"] = False
        if sk:
            sessions = data.setdefault("sessions", {})
            if isinstance(sessions, dict):
                sess_entry = sessions.setdefault(sk, {})
                if isinstance(sess_entry, dict):
                    sess_entry["sidebar_mode"] = mode
                    sess_entry["sidebar_hidden"] = False
        return data

    update_live_state_atomic(mutator)


_TMUX_SESSION_CID_CACHE: tuple[float, str] = (0.0, "")


def discover_tmux_session_conversation_id() -> str:
    """
    Inspect pane PIDs of the current tmux session to find child agy processes
    holding presence/<cid>.lock. Cached for 2.0s.
    """
    global _TMUX_SESSION_CID_CACHE
    if not os.environ.get("TMUX"):
        return ""
    now = time.time()
    if now - _TMUX_SESSION_CID_CACHE[0] < 2.0:
        return _TMUX_SESSION_CID_CACHE[1]

    try:
        res = subprocess.run(
            ["tmux", "list-panes", "-s", "-F", "#{pane_pid}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=0.5,
        )
        if res.returncode != 0:
            res = subprocess.run(
                ["tmux", "list-panes", "-F", "#{pane_pid}"],
                capture_output=True,
                text=True,
                check=False,
                timeout=0.5,
            )
        if res.returncode == 0:
            pane_pids = [p.strip() for p in res.stdout.strip().splitlines() if p.strip()]
            pids_to_check: list[int] = []
            for p_str in pane_pids:
                try:
                    p = int(p_str)
                    pids_to_check.append(p)
                    # Check direct children and grandchildren
                    children_file = f"/proc/{p}/task/{p}/children"
                    if os.path.isfile(children_file):
                        with open(children_file, "r") as cf:
                            for c_str in cf.read().split():
                                c_int = int(c_str)
                                pids_to_check.append(c_int)
                                g_file = f"/proc/{c_int}/task/{c_int}/children"
                                if os.path.isfile(g_file):
                                    with open(g_file, "r") as gf:
                                        for g_str in gf.read().split():
                                            pids_to_check.append(int(g_str))
                except Exception:
                    pass

            for pid in pids_to_check:
                fd_dir = f"/proc/{pid}/fd"
                if not os.path.isdir(fd_dir):
                    continue
                try:
                    for fd_name in os.listdir(fd_dir):
                        try:
                            target = os.readlink(os.path.join(fd_dir, fd_name))
                            if target.endswith(".lock") and (PRESENCE_DIR in target or "/presence/" in target):
                                cid = os.path.basename(target)[:-5]
                                if cid:
                                    _TMUX_SESSION_CID_CACHE = (now, cid)
                                    return cid
                        except Exception:
                            pass
                except Exception:
                    pass
    except Exception:
        pass

    _TMUX_SESSION_CID_CACHE = (now, "")
    return ""


def _walk_up_root(cid: str) -> str:
    """Walk up parent_conversation_id in DB_PATH to find root conversation ID."""
    if not cid or not os.path.isfile(DB_PATH):
        return cid
    with connect_db_ro(DB_PATH) as con:
        if con is not None:
            try:
                cur = con.cursor()
                curr = cid
                depth = 0
                while curr and depth < 10:
                    cur.execute(
                        "SELECT parent_conversation_id FROM conversation_summaries WHERE conversation_id = ?",
                        (curr,),
                    )
                    row = cur.fetchone()
                    if row and row[0]:
                        curr = str(row[0])
                        depth += 1
                    else:
                        break
                return curr
            except Exception:
                pass
    return cid


_TMUX_CWD_CACHE: tuple[float, str] = (0.0, "")


def resolve_workspace_cwd(explicit_dir: str = "", state: dict | None = None) -> str:
    """
    Consolidates the tmux pane cwd -> explicit_dir -> state workspace current_dir/project_dir -> os.getcwd() resolution.
    """
    global _TMUX_CWD_CACHE
    now = time.time()

    # 1. Tmux pane cwd check if running inside tmux
    if os.environ.get("TMUX"):
        if now - _TMUX_CWD_CACHE[0] < 2.0 and _TMUX_CWD_CACHE[1] and _TMUX_CWD_CACHE[1] != "/" and os.path.isdir(_TMUX_CWD_CACHE[1]):
            return _TMUX_CWD_CACHE[1]
        try:
            my_pane = os.environ.get("TMUX_PANE", "")
            res = subprocess.run(
                ["tmux", "list-panes", "-F", "#{pane_id}\t#{pane_current_path}\t#{pane_current_command}"],
                capture_output=True,
                text=True,
                timeout=0.15,
                check=False,
            )
            if res.returncode == 0 and res.stdout.strip():
                pane_path = ""
                for line in res.stdout.strip().splitlines():
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        p_id, p_path = parts[0], parts[1]
                        if (not my_pane or p_id != my_pane) and p_path and p_path != "/" and os.path.isdir(p_path):
                            pane_path = p_path
                            break
                        elif p_path and p_path != "/" and os.path.isdir(p_path) and not pane_path:
                            pane_path = p_path
                if pane_path:
                    _TMUX_CWD_CACHE = (now, pane_path)
                    return pane_path
        except Exception:
            pass

    # 2. explicit_dir
    if explicit_dir and explicit_dir != "/" and os.path.isdir(explicit_dir):
        return explicit_dir

    # 3. state workspace current_dir / project_dir
    if state and isinstance(state, dict):
        ws = state.get("workspace") if isinstance(state.get("workspace"), dict) else {}
        cand = ws.get("project_dir") or ws.get("current_dir") or state.get("project_dir") or state.get("current_dir")
        if cand and cand != "/" and os.path.isdir(cand):
            return cand

    # 4. Fallback to explicit_dir even if not validated as dir
    if explicit_dir and explicit_dir != "/":
        return explicit_dir

    # 5. Fallback to os.getcwd()
    try:
        cwd = os.getcwd()
        if cwd and cwd != "/":
            return cwd
    except Exception:
        pass

    return "/"


_ROOT_CID_CACHE: tuple[str, float, str] = ("", 0.0, "")


def resolve_root_conversation_id(conv_id: str | None = None) -> str:
    """
    Resolve root conversation ID:
    1. First check discover_tmux_session_conversation_id() - if current tmux session holds presence/<cid>.lock.
    2. Otherwise, if conv_id provided, only trust it if its root is in get_locked_conversation_ids() or locked set is empty.
    3. Fall back to presence lockfiles or recent DB root.
    Cached for 1.5s.
    """
    global _ROOT_CID_CACHE
    now = time.time()
    cid_str = conv_id or ""
    if _ROOT_CID_CACHE[0] == cid_str and (now - _ROOT_CID_CACHE[1] < 1.5):
        return _ROOT_CID_CACHE[2]

    # 1. Ground truth for active tmux session
    tmux_cid = discover_tmux_session_conversation_id()
    if tmux_cid:
        root_tmux = _walk_up_root(tmux_cid)
        if root_tmux:
            _ROOT_CID_CACHE = (cid_str, now, root_tmux)
            return root_tmux

    locked_ids = set(get_locked_conversation_ids())

    # 2. Check conv_id candidate if provided
    if cid_str:
        cand_root = _walk_up_root(cid_str)
        # Only trust candidate conv_id if its root is currently locked OR no sessions are locked anywhere
        if not locked_ids or cand_root in locked_ids:
            _ROOT_CID_CACHE = (cid_str, now, cand_root)
            return cand_root

    # 3. Fallback to active locked presence in DB
    if os.path.isfile(DB_PATH):
        with connect_db_ro(DB_PATH) as con:
            if con is not None:
                try:
                    cur = con.cursor()
                    if locked_ids:
                        placeholders = ",".join("?" for _ in locked_ids)
                        cur.execute(
                            f"SELECT conversation_id FROM conversation_summaries "
                            f"WHERE conversation_id IN ({placeholders}) "
                            f"AND (parent_conversation_id IS NULL OR parent_conversation_id = '') "
                            f"ORDER BY last_modified_time DESC LIMIT 1",
                            list(locked_ids),
                        )
                        row = cur.fetchone()
                        if row and row[0]:
                            res_cid = str(row[0])
                            _ROOT_CID_CACHE = (cid_str, now, res_cid)
                            return res_cid
                        # Walk up first locked id
                        first_locked = next(iter(locked_ids))
                        res_cid = _walk_up_root(first_locked)
                        if res_cid:
                            _ROOT_CID_CACHE = (cid_str, now, res_cid)
                            return res_cid

                    cur.execute(
                        "SELECT conversation_id FROM conversation_summaries "
                        "WHERE (parent_conversation_id IS NULL OR parent_conversation_id = '') "
                        "ORDER BY last_modified_time DESC LIMIT 1"
                    )
                    row = cur.fetchone()
                    if row and row[0]:
                        res_cid = str(row[0])
                        _ROOT_CID_CACHE = (cid_str, now, res_cid)
                        return res_cid
                except Exception:
                    pass

    fallback_cid = _walk_up_root(cid_str) if cid_str else ""
    _ROOT_CID_CACHE = (cid_str, now, fallback_cid)
    return fallback_cid


_GIT_DIFF_CACHE: dict[str, tuple[float, tuple[int, int, int]]] = {}


def get_git_diff_stat(proj_dir: str, timeout: float = 0.20) -> tuple[int, int, int]:
    """
    Get (files, insertions, deletions) git diff stats for proj_dir.
    Cached for 2.5s.
    """
    if not proj_dir or not os.path.exists(proj_dir):
        return (0, 0, 0)
    now = time.time()
    cached = _GIT_DIFF_CACHE.get(proj_dir)
    if cached and (now - cached[0] <= 2.5):
        return cached[1]

    cmd = ["git", "-C", proj_dir, "diff", "--shortstat", "HEAD"]
    diff_val = (0, 0, 0)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        out = res.stdout.strip()
        if res.returncode != 0 or not out:
            res = subprocess.run(
                ["git", "-C", proj_dir, "diff", "--shortstat"],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            out = res.stdout.strip()
        if out:
            m_files = re.search(r"(\d+)\s+file", out)
            m_ins = re.search(r"(\d+)\s+insertion", out)
            m_del = re.search(r"(\d+)\s+deletion", out)
            files = int(m_files.group(1)) if m_files else 0
            insertions = int(m_ins.group(1)) if m_ins else 0
            deletions = int(m_del.group(1)) if m_del else 0
            diff_val = (files, insertions, deletions)
    except Exception:
        pass
    _GIT_DIFF_CACHE[proj_dir] = (now, diff_val)
    return diff_val


def read_quota_cache() -> dict:
    """
    Read latest quota cache dictionary from CACHE_PATHS.
    Returns the cache state dict containing 'quota' and 'ts', or empty dict.
    """
    cur_home = os.environ.get("HOME")
    if cur_home and not LIVE_STATE_PATH.startswith(cur_home):
        cache_paths = (
            os.path.join(cur_home, ".gemini", "antigravity-cli", "quota_cache.json"),
            os.path.join(cur_home, ".cache", "antigravity_quota.json"),
            os.path.join(cur_home, ".cache", "antigravity_quota_cache.json"),
        )
    else:
        cache_paths = CACHE_PATHS + (os.path.expanduser("~/.cache/antigravity_quota_cache.json"),)

    best_state: dict = {}
    best_ts = -1.0
    for path in cache_paths:
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict) and data.get("quota"):
                    ts = float(data.get("ts") or 0.0)
                    if ts > best_ts:
                        best_ts = ts
                        best_state = data
        except Exception:
            pass
    return best_state


def write_quota_cache(payload: dict) -> None:
    """
    Atomically write quota cache payload to CACHE_PATHS.
    """
    cur_home = os.environ.get("HOME")
    if cur_home and not LIVE_STATE_PATH.startswith(cur_home):
        cache_paths = (
            os.path.join(cur_home, ".gemini", "antigravity-cli", "quota_cache.json"),
            os.path.join(cur_home, ".cache", "antigravity_quota.json"),
            os.path.join(cur_home, ".cache", "antigravity_quota_cache.json"),
        )
    else:
        cache_paths = CACHE_PATHS

    for path in cache_paths:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp_path = f"{path}.tmp.{os.getpid()}"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            os.replace(tmp_path, path)
        except Exception:
            pass


def refresh_quota_cache_now(timeout_sec: int = 6) -> dict:
    """
    Refresh quota cache synchronously via `agy -p /quota --output-format json`.
    Does NOT unlink LOCK_PATH in finally to preserve lock inode.
    Returns the refreshed cache dict.
    """
    lock_fd = None
    try:
        os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)
        lock_fd = open(LOCK_PATH, "a+", encoding="utf-8")
        fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_fd.seek(0)
        lock_fd.truncate()
        lock_fd.write(str(os.getpid()))
        lock_fd.flush()
    except Exception:
        if lock_fd:
            try:
                lock_fd.close()
            except Exception:
                pass
        return read_quota_cache()

    try:
        agy_cmd = shutil.which("agy") or os.path.expanduser("~/.local/bin/agy")
        proc = subprocess.run(
            [agy_cmd, "-p", "/quota", "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=6 if timeout_sec == 6 else timeout_sec,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout:
            payload = json.loads(proc.stdout.strip().splitlines()[-1])
            groups = (((payload.get("command") or {}).get("data") or {}).get("groups")) or []
            fresh_quota = {}
            for grp in groups:
                for b in grp.get("buckets") or []:
                    bid = b.get("id")
                    if bid:
                        fresh_quota[bid] = {
                            "remaining_fraction": b.get("remaining_fraction"),
                            "remaining_amount": b.get("remaining_amount"),
                            "reset_time": b.get("reset_time"),
                            "window": b.get("window"),
                        }
            if fresh_quota:
                state = read_quota_cache()
                state["ts"] = time.time()
                state["quota"] = fresh_quota
                write_quota_cache(state)
                return state
    except Exception:
        pass
    finally:
        if lock_fd:
            try:
                fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                lock_fd.close()
            except Exception:
                pass
    return read_quota_cache()


def trigger_background_quota_refresh(last_ts: float = 0.0) -> None:
    """
    Trigger background refresh of quota cache if stale (>300s or older than LOCK_PATH).
    """
    now = time.time()
    if last_ts > 0.0 and (now - last_ts < 300.0):
        return
    try:
        if os.path.exists(LOCK_PATH) and (now - os.path.getmtime(LOCK_PATH) < 20.0):
            return
    except Exception:
        pass

    try:
        subprocess.Popen(
            [sys.executable, STATUSLINE_BIN, "--refresh-cache"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception:
        pass


trigger_background_refresh_if_needed = trigger_background_quota_refresh


def resolve_quota_pair(buckets: dict, model_name: str = "", model_display_name: str = "") -> tuple[dict | None, dict | None, str]:
    """
    Resolve (bucket_5h, bucket_weekly, prefix) for given model name from quota buckets map.
    """
    if not buckets:
        return (None, None, "gemini")

    combined = f"{model_name or ''} {model_display_name or ''}".lower()
    is_3p = any(k in combined for k in ("claude", "sonnet", "opus", "haiku", "gpt", "3p"))
    prefix = "3p" if is_3p else "gemini"

    b_5h = buckets.get(f"{prefix}-5h")
    b_wk = buckets.get(f"{prefix}-weekly")

    if not b_5h or not b_wk:
        for k, v in buckets.items():
            kl = k.lower()
            if not b_5h and (kl == f"{prefix}-5h" or (kl.startswith(prefix) and "5h" in kl)):
                b_5h = v
            if not b_wk and (kl == f"{prefix}-weekly" or (kl.startswith(prefix) and "week" in kl)):
                b_wk = v

    if not b_5h:
        for k, v in buckets.items():
            if "5h" in k.lower():
                b_5h = v
                break
    if not b_wk:
        for k, v in buckets.items():
            if "week" in k.lower():
                b_wk = v
                break

    return (b_5h, b_wk, prefix)


def compute_cache_hit_pct(data_or_usage: dict, ctx_obj: dict | None = None) -> tuple[int, int, int]:
    """
    Returns (curr_in, cache_read, cache_pct) using the unified token fallback chain.
    """
    if ctx_obj is None:
        ctx_obj = data_or_usage.get("context_window") or {}
    usage = data_or_usage.get("usage") if isinstance(data_or_usage.get("usage"), dict) else data_or_usage
    curr_u = ctx_obj.get("current_usage") or {}

    cache_read = int(
        curr_u.get("cache_read_input_tokens")
        or usage.get("cache_read_tokens")
        or usage.get("cached_content_token_count")
        or ctx_obj.get("cache_read_tokens")
        or ctx_obj.get("cached_content_token_count")
        or 0
    )
    curr_in = int(
        curr_u.get("input_tokens")
        or usage.get("input_tokens")
        or usage.get("prompt_tokens")
        or ctx_obj.get("total_input_tokens")
        or ctx_obj.get("input_tokens")
        or 0
    )
    cache_pct = 0
    if cache_read > 0:
        cache_pct = min(100, round((cache_read / max(1, cache_read + curr_in)) * 100))
    return (curr_in, cache_read, cache_pct)


def format_token_k(n: int) -> str:
    """Format token count: 1.2M, 45.2k, or exact integer string."""
    try:
        val = int(n)
    except (ValueError, TypeError):
        return "0"
    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    elif val >= 1_000:
        return f"{val / 1_000:.1f}k"
    return str(val)


class TokenTelemetry(dict):
    """
    Subclass of dict that unpacks as (in_tokens, out_tokens, used_pct, cache_hit_pct)
    when iterated over, preserving compatibility with tuple unpacking while
    supporting dict key lookups.
    """

    def __iter__(self):
        return iter((
            int(self.get("in_tokens", 0)),
            int(self.get("out_tokens", 0)),
            float(self.get("used_pct", 0.0)),
            int(self.get("cache_hit_pct", 0)),
        ))


_TOKEN_TELEM_CACHE: dict[str, tuple[float, float, dict]] = {}  # root_cid -> (cache_ts, mtime, result)


def resolve_session_token_telemetry(state: dict, root_cid: str = "") -> dict:
    """
    Resolves session token telemetry with robust fallback to transcript.jsonl.
    Cached for 2.0s per (root_cid, mtime).
    Returns TokenTelemetry dict:
      {
        "used_pct": float,
        "in_tokens": int,
        "out_tokens": int,
        "cache_hit_pct": int,
        "exceeds_200k": bool,
      }
    """
    conv_id = str(state.get("conversation_id") or "").strip()
    is_explicit_reset = (state.get("conversation_id") == "")

    ctx = state.get("context_window") if isinstance(state.get("context_window"), dict) else {}
    usage = state.get("usage") if isinstance(state.get("usage"), dict) else {}
    curr_in, cache_read, cache_hit_pct = compute_cache_hit_pct(state, ctx)

    used_pct = ctx.get("used_percentage")
    in_tok = int(
        ctx.get("total_input_tokens")
        or usage.get("input_tokens")
        or usage.get("prompt_tokens")
        or ctx.get("input_tokens")
        or curr_in
        or 0
    )
    out_tok = int(
        ctx.get("total_output_tokens")
        or usage.get("output_tokens")
        or usage.get("candidates_token_count")
        or ctx.get("output_tokens")
        or 0
    )

    # Short-circuit immediately on explicit reset or empty conversation ID
    if (not root_cid or not conv_id or is_explicit_reset):
        if in_tok == 0 and out_tok == 0 and (not used_pct or float(used_pct) == 0.0):
            return TokenTelemetry({
                "used_pct": 0.0,
                "in_tokens": 0,
                "out_tokens": 0,
                "cache_hit_pct": 0,
                "exceeds_200k": False,
            })

    if state.get("cache_hit_pct") is not None:
        try:
            s_pct = int(state.get("cache_hit_pct") or 0)
            if s_pct > cache_hit_pct:
                cache_hit_pct = s_pct
        except (ValueError, TypeError):
            pass

    has_live_in_tok = in_tok > 0
    ctx_limit = int(ctx.get("context_window_size") or 200_000)

    has_live_used_pct = False
    if used_pct is not None:
        try:
            has_live_used_pct = float(used_pct) > 0.0
        except (ValueError, TypeError):
            has_live_used_pct = False

    if has_live_in_tok and not has_live_used_pct:
        if ctx_limit > 200_000 and in_tok < 200_000:
            used_pct = max(0.5, round((in_tok / 200_000.0) * 100.0, 1))
        else:
            used_pct = max(0.5, round((in_tok / float(ctx_limit)) * 100.0, 1))
        has_live_used_pct = True

    curr_u = ctx.get("current_usage") if isinstance(ctx.get("current_usage"), dict) else {}
    explicit_zero_cache_read = (cache_read == 0) and any(
        k in src_dict
        for src_dict in (curr_u, usage, ctx)
        for k in ("cache_read_input_tokens", "cache_read_tokens", "cached_content_token_count")
    )

    # Transcript Fallback: ONLY read transcript when live input, output, or context percentage is missing/zero
    # (never solely because cache_hit_pct == 0 when live telemetry is already present),
    # and only when root_cid is non-empty, session was not reset to "", and conv_id matches root_cid.
    need_transcript_fallback = (not has_live_in_tok or out_tok == 0 or not has_live_used_pct)
    if need_transcript_fallback and root_cid and not is_explicit_reset and (not conv_id or conv_id == root_cid):
        tr_path = os.path.join(BRAIN_DIR, root_cid, ".system_generated", "logs", "transcript.jsonl")
        if os.path.exists(tr_path):
            try:
                tr_mtime = os.path.getmtime(tr_path)
                tr_bytes = os.path.getsize(tr_path)
                now = time.time()
                cached = _TOKEN_TELEM_CACHE.get(root_cid)
                if cached and (now - cached[0] < 2.0) and (cached[1] == tr_mtime):
                    fb = cached[2]
                else:
                    steps = 0
                    planner_steps = 0
                    out_bytes = 0
                    last_in = 0
                    last_cache_read = 0
                    has_exact_in = False
                    total_exact_out = 0
                    with open(tr_path, "r", encoding="utf-8", errors="replace") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            steps += 1
                            try:
                                step_obj = json.loads(line)
                                if step_obj.get("type") == "PLANNER_RESPONSE":
                                    planner_steps += 1
                                    c = step_obj.get("content") or ""
                                    th = step_obj.get("thinking") or ""
                                    tc = step_obj.get("tool_calls") or ""
                                    out_bytes += len(str(c)) + len(str(th)) + len(str(tc))

                                    s_in = int(step_obj.get("input_tokens") or 0)
                                    s_cr = int(step_obj.get("cache_read_tokens") or 0)
                                    s_out = int(step_obj.get("output_tokens") or 0)
                                    if s_in > 0 or s_cr > 0:
                                        last_in = s_in
                                        last_cache_read = s_cr
                                        has_exact_in = True
                                    if s_out > 0:
                                        total_exact_out += s_out
                            except Exception:
                                pass

                    if has_exact_in:
                        active_tok = last_in + last_cache_read
                        fb_in_tok = active_tok
                        if last_cache_read > 0:
                            fb_cache_hit = min(100, round((last_cache_read / max(1, active_tok)) * 100))
                        else:
                            fb_cache_hit = 0
                    else:
                        in_bytes = max(0, tr_bytes - out_bytes)
                        active_tok = max(1, tr_bytes // 4)
                        fb_in_tok = max(active_tok, int(in_bytes // 4) + int(active_tok * min(steps, 12) * 0.4))
                        fb_cache_hit = (
                            min(98, round(((planner_steps - 1) / planner_steps) * 96))
                            if planner_steps > 1
                            else 0
                        )

                    if ctx_limit > 200_000 and active_tok < 200_000:
                        fb_used_pct = max(0.5, round((active_tok / 200_000.0) * 100.0, 1))
                    else:
                        fb_used_pct = max(0.5, round((active_tok / float(ctx_limit)) * 100.0, 1))

                    fb_out_tok = total_exact_out if total_exact_out > 0 else max(1, out_bytes // 4)

                    fb = {
                        "used_pct": fb_used_pct,
                        "in_tokens": fb_in_tok,
                        "out_tokens": fb_out_tok,
                        "cache_hit_pct": fb_cache_hit,
                        "has_exact_cache_hit": bool(has_exact_in and last_cache_read > 0),
                    }
                    _TOKEN_TELEM_CACHE[root_cid] = (now, tr_mtime, fb)

                if not has_live_used_pct:
                    used_pct = fb.get("used_pct", 0.0)
                if in_tok == 0:
                    in_tok = fb.get("in_tokens", 0)
                if out_tok == 0:
                    out_tok = fb.get("out_tokens", 0)
                if cache_hit_pct == 0 and not explicit_zero_cache_read:
                    if not has_live_in_tok or fb.get("has_exact_cache_hit"):
                        cache_hit_pct = fb.get("cache_hit_pct", 0)
            except Exception:
                pass

    return TokenTelemetry({
        "used_pct": float(used_pct or 0.0),
        "in_tokens": int(in_tok),
        "out_tokens": int(out_tok),
        "cache_hit_pct": int(cache_hit_pct),
        "exceeds_200k": bool(ctx.get("exceeds_200k_tokens") or in_tok > 200_000),
    })


def extract_step_tool_summaries(step_obj: dict) -> list[str]:
    """
    Extract formatted tool summaries from step_obj.get("tool_calls").
    Returns list of formatted strings e.g. ["run_command: git status"].
    """
    tool_calls = step_obj.get("tool_calls") or []
    tool_descs: list[str] = []
    for tc in tool_calls:
        if not isinstance(tc, dict):
            continue
        name = tc.get("name") or tc.get("tool_name") or ""
        args = tc.get("args") or tc.get("parameters") or tc.get("Arguments") or {}
        if not isinstance(args, dict):
            args = {}
        act = args.get("toolAction") or args.get("toolSummary") or args.get("summary")
        if not act:
            cmd = args.get("CommandLine") or args.get("command") or args.get("cmd")
            tgt = (
                args.get("TargetFile")
                or args.get("AbsolutePath")
                or args.get("Path")
                or args.get("path")
                or args.get("Url")
                or args.get("url")
            )
            if cmd:
                act = str(cmd).strip()[:45]
            elif tgt:
                act = os.path.basename(str(tgt))
        if act:
            clean_act = str(act).strip('"\'')
            tool_descs.append(f"{name}: {clean_act}" if name else clean_act)
        elif name:
            tool_descs.append(name)
    return tool_descs


def read_live_state(session_key: str = "") -> dict:
    """
    Safely read live state JSON. If session_key (or current tmux session/pane)
    is present and session overrides exist in data["sessions"][session_key],
    merges session-specific overrides onto the base state.
    """
    cur_home = os.environ.get("HOME")
    if cur_home and not LIVE_STATE_PATH.startswith(cur_home):
        live_path = os.path.join(cur_home, ".cache", "antigravity_live_state.json")
    else:
        live_path = LIVE_STATE_PATH

    data: dict = {}
    try:
        if os.path.exists(live_path):
            with open(live_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                data = loaded
    except Exception:
        return {}

    if not data:
        return {}

    sk = session_key or get_current_session_key()

    if sk:
        sessions = data.get("sessions")
        if isinstance(sessions, dict):
            s_overrides = sessions.get(sk)
            if not s_overrides and os.environ.get("TMUX_PANE"):
                s_overrides = sessions.get(os.environ.get("TMUX_PANE"))
            if isinstance(s_overrides, dict):
                merged = dict(data)
                for field in (
                    "workspace",
                    "vcs",
                    "git_diff",
                    "git_diff_turn",
                    "conversation_id",
                    "sidebar_mode",
                    "subagents",
                    "subagent_count",
                    "subagent_completed_count",
                    "blocked_count",
                    "task_count",
                    "artifact_count",
                    "cost",
                    "model",
                    "context_window",
                    "cache_hit_pct",
                    "usage",
                    "tok_per_min",
                    "ctx_history",
                    "vel_history",
                    "turn_duration_sec",
                    "turn_start_ts",
                ):
                    if field in s_overrides:
                        merged[field] = s_overrides[field]
                return merged

    return data


def format_countdown(bucket: dict, short: bool = False) -> str:
    """Format quota bucket countdown into human-readable representation."""
    diff_sec = bucket.get("reset_in_seconds")
    if diff_sec is None:
        rt = bucket.get("reset_time")
        if rt:
            try:
                from datetime import datetime, timezone
                rt_clean = rt.replace("Z", "+00:00")
                target = datetime.fromisoformat(rt_clean)
                now = datetime.now(timezone.utc)
                diff_sec = int((target - now).total_seconds())
            except Exception:
                diff_sec = None
    if diff_sec is None:
        return ""
    diff_sec = max(0, int(diff_sec))
    days = diff_sec // 86400
    hours = (diff_sec % 86400) // 3600
    mins = (diff_sec % 3600) // 60
    if short:
        if days > 0:
            return f"↻{days}d"
        elif hours > 0:
            return f"↻{hours}h"
        else:
            return f"↻{mins}m"
    else:
        if days > 0:
            return f"↻{days}d{hours:02d}h"
        elif hours > 0:
            return f"↻{hours}h{mins:02d}m"
        else:
            return f"↻{mins}m"


def format_countdown_short(bucket: dict) -> str:
    """Format short quota bucket countdown."""
    return format_countdown(bucket, short=True)


def discover_brain_subagents(root_cid: str) -> list[dict]:
    """
    Read ground-truth subagents from ~/.gemini/antigravity-cli/brain/<root_cid>/.system_generated/subagents/*.json.
    Determines completion using active presence locks, DB status, and transcript state.
    Returns list of dicts with keys: id, conversationId, role, name, status, raw_status, workspace, step_count, started_at.
    """
    if not root_cid:
        return []
    subagents_dir = os.path.join(BRAIN_DIR, root_cid, ".system_generated", "subagents")
    if not os.path.isdir(subagents_dir):
        return []

    locked_cids = get_locked_conversation_ids()
    now = time.time()
    results: list[dict] = []
    try:
        with os.scandir(subagents_dir) as it:
            entries = [e for e in it if e.name.endswith(".json")]
        entries.sort(key=lambda e: e.stat().st_mtime)

        # Query conversation_summaries in DB_PATH for parent_conversation_id = root_cid
        db_statuses: dict[str, str] = {}
        if root_cid and os.path.isfile(DB_PATH):
            with connect_db_ro(DB_PATH) as con:
                if con is not None:
                    try:
                        cur = con.cursor()
                        cur.execute(
                            "SELECT conversation_id, status FROM conversation_summaries WHERE parent_conversation_id = ?",
                            (root_cid,),
                        )
                        for r_cid, r_st in cur.fetchall():
                            db_statuses[str(r_cid)] = str(r_st or "")
                    except Exception:
                        pass

        for entry in entries:
            try:
                with open(entry.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    continue
                cid = str(data.get("conversationId") or entry.name[:-5]).strip()
                desc = data.get("subagentDescriptor") or {}
                raw_role = desc.get("role") or desc.get("typeName") or "agent"
                type_name = desc.get("typeName") or "agent"
                raw_state = str(data.get("state") or "running").strip().upper()

                is_locked = cid in locked_cids
                tr_path = os.path.join(BRAIN_DIR, cid, ".system_generated", "logs", "transcript.jsonl")
                tr_mtime = 0.0
                tr_is_finished = False
                if os.path.isfile(tr_path):
                    try:
                        tr_mtime = os.path.getmtime(tr_path)
                        with open(tr_path, "rb") as tf:
                            size = os.path.getsize(tr_path)
                            tf.seek(max(0, size - 8192))
                            tail_lines = tf.read().decode("utf-8", errors="replace").splitlines()
                            for t_line in reversed(tail_lines):
                                t_line = t_line.strip()
                                if not t_line:
                                    continue
                                try:
                                    item = json.loads(t_line)
                                    l_type = item.get("type")
                                    l_status = str(item.get("status") or "").upper()
                                    l_calls = item.get("tool_calls") or []
                                    if l_type == "PLANNER_RESPONSE" and not l_calls and l_status == "DONE":
                                        tr_is_finished = True
                                    elif l_status in ("COMPLETED", "TERMINATED", "CANCELLED", "CANCELED"):
                                        tr_is_finished = True
                                    break
                                except Exception:
                                    continue
                    except Exception:
                        pass

                db_st = db_statuses.get(cid, "").upper()
                if not db_st and os.path.isfile(DB_PATH):
                    with connect_db_ro(DB_PATH) as con:
                        if con is not None:
                            try:
                                cur = con.cursor()
                                cur.execute("SELECT status FROM conversation_summaries WHERE conversation_id = ?", (cid,))
                                row = cur.fetchone()
                                if row and row[0]:
                                    db_st = str(row[0]).upper()
                                    db_statuses[cid] = db_st
                            except Exception:
                                pass

                if is_locked:
                    state = "running"
                elif "TERMINAT" in raw_state or "KILL" in raw_state or "CANCEL" in raw_state:
                    state = "done"
                elif "ERROR" in raw_state or "FAIL" in raw_state:
                    state = "errored"
                elif "RUNNING" in db_st:
                    if raw_state in ("TERMINATED", "KILLED", "COMPLETED", "DONE"):
                        state = "completed"
                    elif tr_is_finished and (now - tr_mtime > 5.0):
                        state = "completed"
                    else:
                        state = "running"
                elif ("IDLE" in db_st or "COMPLETE" in db_st):
                    if (now - tr_mtime > 3.0) or tr_is_finished:
                        state = "completed"
                    else:
                        state = "running"
                elif tr_is_finished:
                    state = "completed"
                elif "DONE" in raw_state or "COMPLET" in raw_state:
                    state = "completed"
                elif tr_mtime > 0.0:
                    # Fallback stale-transcript timeout: 300.0s (5 minutes)
                    state = "completed" if (now - tr_mtime > 300.0) else "running"
                elif (now - entry.stat().st_mtime > 300.0):
                    state = "completed"
                else:
                    state = "running"

                ws_uris = data.get("workspaceUris") or []
                ws_path = ""
                if ws_uris and isinstance(ws_uris, list) and ws_uris[0]:
                    uri = str(ws_uris[0])
                    ws_path = uri[7:] if uri.startswith("file://") else uri

                results.append({
                    "id": cid,
                    "conversationId": cid,
                    "role": raw_role,
                    "name": type_name,
                    "status": state,
                    "raw_status": "completed" if state == "completed" else raw_state.lower(),
                    "workspace": ws_path or "inherit",
                    "step_count": int(data.get("spawnStepIndex") or 0),
                    "started_at": entry.stat().st_mtime,
                })
            except Exception:
                pass
    except Exception:
        pass
    return results


def merge_and_dedup_subagents(raw_subs: list[dict], root_cid_or_brain_subs: str | list[dict] = "") -> list[dict]:
    """
    Merge and deduplicate subagents between raw_subs and discover_brain_subagents(root_cid) or brain_subs list.
    Strips ID-less entries when brain_subs is present to avoid ghost duplicates,
    preserving status updates by zipping if lengths match.
    """
    if isinstance(root_cid_or_brain_subs, list):
        brain_subs = root_cid_or_brain_subs
    elif isinstance(root_cid_or_brain_subs, str) and root_cid_or_brain_subs:
        brain_subs = discover_brain_subagents(root_cid_or_brain_subs)
    else:
        brain_subs = []

    if not brain_subs:
        seen: set[str] = set()
        deduped: list[dict] = []
        for s in raw_subs:
            if not isinstance(s, dict):
                continue
            s_id = str(s.get("id") or s.get("conversationId") or s.get("conversation_id") or s.get("session_id") or "").strip()
            if s_id:
                if s_id not in seen:
                    seen.add(s_id)
                    deduped.append(dict(s))
            else:
                deduped.append(dict(s))
        return deduped

    merged: dict[str, dict] = {}
    for b in brain_subs:
        bid = str(b.get("id") or b.get("conversationId") or "").strip()
        if bid:
            merged[bid] = dict(b)

    valid_raw = [s for s in raw_subs if isinstance(s, dict)]

    id_less = [
        s for s in valid_raw
        if not (s.get("id") or s.get("conversationId") or s.get("conversation_id") or s.get("session_id"))
    ]
    if len(id_less) == len(valid_raw) and len(valid_raw) == len(brain_subs):
        for raw_s, b_s in zip(valid_raw, brain_subs):
            bid = str(b_s.get("id") or b_s.get("conversationId") or "").strip()
            if bid in merged:
                for k in ("status", "raw_status", "state", "stateDetail", "toolAction", "toolSummary"):
                    if raw_s.get(k):
                        merged[bid][k] = raw_s[k]
        return list(merged.values())

    for s in valid_raw:
        sid = str(s.get("id") or s.get("conversationId") or s.get("conversation_id") or s.get("session_id") or "").strip()
        if not sid:
            continue
        if sid in merged:
            target = merged[sid]
            cur_r = str(s.get("role") or "").strip().lower()
            if cur_r and cur_r not in ("self", "research", "agent", "subagent"):
                target["role"] = s["role"]
            ws = s.get("workspace")
            if ws and ws not in ("inherit", "/"):
                target["workspace"] = ws
            for k in ("status", "raw_status", "state", "stateDetail", "toolAction", "toolSummary"):
                if s.get(k):
                    target[k] = s[k]
        else:
            merged[sid] = dict(s)

    return list(merged.values())


_PROC_OPEN_FILES_CACHE: tuple[float, set[str]] = (0.0, set())
_RELEVANT_PROC_COMMS: tuple[str, ...] = (
    "agy",
    "antigravity",
    "python",
    "bash",
    "sh",
    "zsh",
    "dash",
    "fish",
    "node",
    "bun",
    "deno",
    "pytest",
    "uv",
    "tmux",
    "cat",
    "tee",
    "tail",
    "sleep",
)


def parse_agy_stream_json_line(line: str) -> dict | None:
    """
    Parse a single NDJSON line emitted by `agy --output-format stream-json`.
    Handles `thought`, `tool_call`, `text`/`content`, and `error` events safely
    without raising on malformed or empty input.
    """
    if not isinstance(line, str):
        return None
    stripped = line.strip()
    if not stripped or not stripped.startswith("{"):
        return None
    try:
        payload = json.loads(stripped)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None

    result = dict(payload)
    ev_type = str(result.get("type") or result.get("event") or "").strip().lower()
    if not ev_type:
        if result.get("error") is not None:
            ev_type = "error"
        elif "tool_call" in result or "tool_calls" in result or "tool_name" in result:
            ev_type = "tool_call"
        elif "thought" in result or "thinking" in result:
            ev_type = "thought"
        elif "text" in result or "content" in result:
            ev_type = "text"
        else:
            ev_type = "unknown"

    result.setdefault("type", ev_type)

    if ev_type in ("thought", "thinking") or "thought" in result or "thinking" in result:
        thought_val = result.get("thought") if result.get("thought") is not None else result.get("thinking")
        if thought_val is not None:
            result.setdefault("thought", thought_val)

    if ev_type in ("tool_call", "tool_calls", "tool_use") or "tool_call" in result or "tool_calls" in result:
        tc_val = result.get("tool_call")
        if tc_val is None:
            tcs = result.get("tool_calls")
            if isinstance(tcs, list) and tcs:
                tc_val = tcs[0]
            elif "name" in result or "tool_name" in result:
                tc_val = {
                    "name": result.get("name") or result.get("tool_name"),
                    "args": result.get("args") or result.get("arguments") or {},
                }
        if tc_val is not None:
            result.setdefault("tool_call", tc_val)

    if ev_type in ("text", "content", "message", "delta") or "text" in result or "content" in result:
        txt_val = result.get("text") if result.get("text") is not None else result.get("content")
        if txt_val is not None:
            result.setdefault("text", txt_val)
            result.setdefault("content", txt_val)

    if ev_type == "error" or "error" in result:
        err_val = result.get("error") if result.get("error") is not None else result.get("message")
        if err_val is not None:
            result.setdefault("error", err_val)

    return result


def _get_proc_open_files() -> set[str]:
    global _PROC_OPEN_FILES_CACHE
    now = time.time()
    if now - _PROC_OPEN_FILES_CACHE[0] < 2.0:
        return _PROC_OPEN_FILES_CACHE[1]
    open_fds: set[str] = set()
    try:
        uid = os.getuid()
        self_pid = str(os.getpid())
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                proc_dir = f"/proc/{pid}"
                if os.stat(proc_dir).st_uid != uid:
                    continue
                if pid != self_pid:
                    with open(f"{proc_dir}/comm", "r", encoding="utf-8", errors="replace") as cf:
                        comm = cf.read().strip().lower()
                    if not comm.startswith(_RELEVANT_PROC_COMMS):
                        continue
                fd_dir = f"{proc_dir}/fd"
                for fd in os.listdir(fd_dir)[:128]:
                    try:
                        link = os.readlink(f"{fd_dir}/{fd}")
                        if link.startswith("/"):
                            open_fds.add(link)
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass
    _PROC_OPEN_FILES_CACHE = (now, open_fds)
    return open_fds


def discover_brain_tasks(root_cid: str) -> list[dict]:
    """
    Check ~/.gemini/antigravity-cli/brain/<root_cid>/.system_generated/tasks/ for active background tasks,
    or inspect running child processes of agy.
    Returns list of task dicts: [{"id": str, "command": str, "status": "running"}]
    """
    tasks: list[dict] = []
    seen_ids: set[str] = set()

    if root_cid:
        brain_base = os.path.join(BRAIN_DIR, root_cid)
        tasks_dir = os.path.join(brain_base, ".system_generated", "tasks")
        tr_path = os.path.join(brain_base, ".system_generated", "logs", "transcript.jsonl")

        completed_task_ids: set[str] = set()
        if os.path.isfile(tr_path):
            try:
                with open(tr_path, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if "task-" in line:
                            for m in re.findall(r"task-\d+", line):
                                if (
                                    "finished" in line
                                    or "exited with code" in line
                                    or "Command exited with code" in line
                                ):
                                    completed_task_ids.add(m)
            except Exception:
                pass

        def is_path_open_in_proc(p: str) -> bool:
            return os.path.realpath(p) in _get_proc_open_files()

        if os.path.isdir(tasks_dir):
            try:
                now = time.time()
                with os.scandir(tasks_dir) as it:
                    entries = list(it)

                json_tids: set[str] = set()
                for entry in entries:
                    if entry.name.endswith(".json"):
                        tid = entry.name[:-5]
                        json_tids.add(tid)
                        if tid in completed_task_ids:
                            continue
                        try:
                            with open(entry.path, "r", encoding="utf-8") as f:
                                td = json.load(f)
                            if isinstance(td, dict):
                                cmd = td.get("command") or td.get("cmd") or ""
                                status = td.get("status") or "running"
                                if status == "running" and tid not in seen_ids:
                                    tasks.append({
                                        "id": tid,
                                        "command": cmd or tid,
                                        "status": status,
                                    })
                                    seen_ids.add(tid)
                        except Exception:
                            pass

                for entry in entries:
                    if entry.name.endswith(".log"):
                        tid = entry.name[:-4]
                        if tid in completed_task_ids or tid in seen_ids or tid in json_tids:
                            continue
                        try:
                            st = entry.stat()
                            is_running = is_path_open_in_proc(entry.path)
                            if is_running:
                                tasks.append({
                                    "id": tid,
                                    "command": entry.name,
                                    "status": "running",
                                })
                                seen_ids.add(tid)
                        except Exception:
                            pass
            except Exception:
                pass

    return tasks


def discover_cycle_mode(raw_mode: str = "", root_cid: str = "") -> str:
    """
    Discover active execution cycle mode ('normal', 'plan', or 'auto').
    Inspects raw_mode argument or parent/running agy process command-line arguments.
    """
    if raw_mode and raw_mode.strip().lower() not in ("", "normal"):
        return raw_mode.strip().lower()

    try:
        res = subprocess.run(
            ["pgrep", "-a", "-f", "agy"],
            capture_output=True,
            text=True,
            timeout=0.15,
            check=False,
        )
        if res.returncode == 0 and res.stdout:
            for line in res.stdout.splitlines():
                if "agy-statusline" in line or "agy-sidebar" in line or "agy-squad" in line:
                    continue
                if "--mode plan" in line or "-m plan" in line:
                    return "plan"
                elif "--mode auto" in line or "-m auto" in line:
                    return "auto"
    except Exception:
        pass

    return "normal"


# -----------------------------------------------------------------------------
# 8. Inotify Event Watcher (Linux ctypes libc.so.6)
# -----------------------------------------------------------------------------
IN_NONBLOCK = 0x800
IN_CLOEXEC = 0x80000
# Safe mask: IN_MODIFY | IN_CLOSE_WRITE | IN_MOVED_FROM | IN_MOVED_TO | IN_CREATE | IN_DELETE
# NEVER include IN_ACCESS (0x1), IN_OPEN (0x20), or IN_CLOSE_NOWRITE (0x10) to avoid busy-loops!
IN_DEFAULT_MASK = 0x0000038A


class InotifyWatcher:
    """
    Lightweight non-blocking Linux inotify wrapper using ctypes libc.so.6.
    Avoids polling loops and provides <15ms wakeup latency.
    """

    def __init__(self) -> None:
        self._libc = ctypes.CDLL(ctypes.util.find_library("c") or "libc.so.6", use_errno=True)
        self._libc.inotify_init1.argtypes = [ctypes.c_int]
        self._libc.inotify_init1.restype = ctypes.c_int
        self._libc.inotify_add_watch.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32]
        self._libc.inotify_add_watch.restype = ctypes.c_int
        self._fd = self._libc.inotify_init1(IN_NONBLOCK | IN_CLOEXEC)
        self._watches: dict[int, str] = {}
        self._paths: dict[str, int] = {}

    @property
    def fd(self) -> int:
        """File descriptor for use with select.poll() or select.select()."""
        return self._fd

    def add_path(self, path: str, mask: int = IN_DEFAULT_MASK) -> int:
        """Add inotify watch on path. Always watches parent directory to capture atomic os.replace renames."""
        if self._fd < 0 or not path:
            return -1
        expanded = os.path.abspath(os.path.expanduser(path))
        parent = os.path.dirname(expanded)

        parent_wd = -1
        if parent and os.path.exists(parent):
            if parent in self._paths:
                parent_wd = self._paths[parent]
            else:
                try:
                    pwd = self._libc.inotify_add_watch(self._fd, parent.encode("utf-8"), mask)
                    if pwd >= 0:
                        self._watches[pwd] = parent
                        self._paths[parent] = pwd
                        parent_wd = pwd
                except Exception:
                    pass

        if not os.path.exists(expanded):
            return parent_wd

        if expanded in self._paths:
            return self._paths[expanded]

        try:
            wd = self._libc.inotify_add_watch(self._fd, expanded.encode("utf-8"), mask)
            if wd >= 0:
                self._watches[wd] = expanded
                self._paths[expanded] = wd
            return wd
        except Exception:
            return parent_wd

    def drain(self) -> bool:
        """
        Drain all pending inotify events from the non-blocking buffer.
        Returns True if at least one event was read, False otherwise.
        """
        if self._fd < 0:
            return False
        got_events = False
        while True:
            try:
                chunk = os.read(self._fd, 4096)
                if not chunk:
                    break
                got_events = True
            except (BlockingIOError, InterruptedError, OSError):
                break
        return got_events

    def close(self) -> None:
        """Close inotify file descriptor and clean up watches."""
        if self._fd >= 0:
            try:
                os.close(self._fd)
            except Exception:
                pass
            self._fd = -1
            self._watches.clear()
            self._paths.clear()

    def __enter__(self) -> InotifyWatcher:
        return self

    def __exit__(self, exc_type: any, exc_val: any, exc_tb: any) -> None:
        self.close()


# -----------------------------------------------------------------------------
# 9. Mermaid Diagram Unicode Box-Drawing Renderer
# -----------------------------------------------------------------------------
def _extract_mermaid_node_info(token: str) -> tuple[str, str, str]:
    token = token.strip()
    if token == "[*]":
        return "[*]", "Start/End", "circle"
    patterns = [
        (r'^([A-Za-z0-9_\-\.]+)\s*\[\s*"([^"]+)"\s*\]$', "rect"),
        (r'^([A-Za-z0-9_\-\.]+)\s*\[\s*\[\s*([^\]]+)\s*\]\s*\]$', "subroutine"),
        (r'^([A-Za-z0-9_\-\.]+)\s*\[\s*\(\s*([^)]+)\s*\)\s*\]$', "database"),
        (r'^([A-Za-z0-9_\-\.]+)\s*\[\s*([^\]]+)\s*\]$', "rect"),
        (r'^([A-Za-z0-9_\-\.]+)\s*\(\s*\[\s*([^\]]+)\s*\]\s*\)$', "stadium"),
        (r'^([A-Za-z0-9_\-\.]+)\s*\(\s*\(\s*([^)]+)\s*\)\s*\)$', "circle"),
        (r'^([A-Za-z0-9_\-\.]+)\s*\(\s*"([^"]+)"\s*\)$', "round"),
        (r'^([A-Za-z0-9_\-\.]+)\s*\(\s*([^)]+)\s*\)$', "round"),
        (r'^([A-Za-z0-9_\-\.]+)\s*\{\s*"([^"]+)"\s*\}$', "decision"),
        (r'^([A-Za-z0-9_\-\.]+)\s*\{\s*([^}]+)\s*\}$', "decision"),
        (r'^([A-Za-z0-9_\-\.]+)\s*>\s*([^\]]+)\s*\]$', "flag"),
    ]
    for pat, shape in patterns:
        m = re.match(pat, token)
        if m:
            return m.group(1).strip(), m.group(2).strip(), shape
    m = re.match(r'^([A-Za-z0-9_\-\.]+)$', token)
    if m:
        return m.group(1), m.group(1), "plain"
    return token, token, "plain"


def _render_mermaid_box(label: str, shape: str = "rect", max_width: int = 40) -> list[str]:
    clean = label.replace("\n", " ").strip()
    if shape == "database":
        clean = f"[( {clean} )]"
    elif shape == "decision":
        clean = f"◇ {clean} ?"
    elif shape == "circle":
        clean = f"(( {clean} ))"
    elif shape == "stadium":
        clean = f"([ {clean} ])"
    elif shape == "subroutine":
        clean = f"[[ {clean} ]]"

    if len(clean) > max_width - 4:
        clean = clean[:max_width - 7] + "..."
    w = max(len(clean) + 4, 10)
    inner_w = w - 2
    pad_l = (inner_w - len(clean)) // 2
    pad_r = inner_w - len(clean) - pad_l

    top = "╭" + "─" * inner_w + "╮"
    mid = f"│{' ' * pad_l}{clean}{' ' * pad_r}│"
    bot = "╰" + "─" * inner_w + "╯"
    return [top, mid, bot]


def _render_mermaid_sequence_diagram(lines: list[str], max_width: int = 76) -> str:
    participants = []
    part_order = []
    messages = []

    for line in lines:
        l = line.strip()
        if not l or l.startswith("%%") or l.startswith("autonumber"):
            continue
        m_p = re.match(r'^(?:participant|actor)\s+([A-Za-z0-9_\.]+)(?:\s+as\s+(.+))?$', l, re.IGNORECASE)
        if m_p:
            pid = m_p.group(1).strip()
            lbl = (m_p.group(2) or pid).strip().strip('"')
            if pid not in part_order:
                part_order.append(pid)
                participants.append((pid, lbl))
            continue

        m_msg = re.match(r'^([A-Za-z0-9_]+)\s*(-->>|->>|-->|->|-\)|--\)|-x|--x)\s*([A-Za-z0-9_]+)\s*:\s*(.+)$', l)
        if m_msg:
            src = m_msg.group(1).strip()
            arrow = m_msg.group(2).strip()
            dst = m_msg.group(3).strip()
            msg = m_msg.group(4).strip()
            for p in (src, dst):
                if p not in part_order:
                    part_order.append(p)
                    participants.append((p, p))
            messages.append((src, dst, arrow, msg))
            continue

    if not participants:
        return "  (empty sequence diagram)"

    n = len(participants)
    col_width = max(12, min(24, (max_width - 2) // max(1, n)))
    total_w = col_width * n

    col_centers = []
    for i, (pid, lbl) in enumerate(participants):
        c_lbl = lbl[:col_width - 4]
        box_w = min(col_width - 2, len(c_lbl) + 4)
        box_w = max(box_w, 8)
        col_start = i * col_width
        center = col_start + (col_width // 2)
        col_centers.append(center)

    res = []
    line_top = [" "] * total_w
    line_mid = [" "] * total_w
    line_bot = [" "] * total_w

    for i, (pid, lbl) in enumerate(participants):
        c_lbl = lbl[:col_width - 4]
        box_w = min(col_width - 2, len(c_lbl) + 4)
        box_w = max(box_w, 8)
        inner_w = box_w - 2
        pad_l = (inner_w - len(c_lbl)) // 2
        pad_r = inner_w - len(c_lbl) - pad_l
        top = "╭" + "─" * inner_w + "╮"
        mid = f"│{' ' * pad_l}{c_lbl}{' ' * pad_r}│"
        bot = "╰" + "─" * inner_w + "╯"
        start_x = col_centers[i] - (box_w // 2)
        for offset, ch in enumerate(top):
            line_top[start_x + offset] = ch
        for offset, ch in enumerate(mid):
            line_mid[start_x + offset] = ch
        for offset, ch in enumerate(bot):
            line_bot[start_x + offset] = ch

    res.append("".join(line_top).rstrip())
    res.append("".join(line_mid).rstrip())
    res.append("".join(line_bot).rstrip())

    for src, dst, arrow, text in messages:
        ll = [" "] * total_w
        for c in col_centers:
            ll[c] = "│"
        res.append("".join(ll).rstrip())

        i_src = part_order.index(src)
        i_dst = part_order.index(dst)
        c_src = col_centers[i_src]
        c_dst = col_centers[i_dst]

        msg_line = [" "] * total_w
        for c in col_centers:
            msg_line[c] = "│"

        dash = "┄" if "--" in arrow else "─"
        if c_src < c_dst:
            dist = c_dst - c_src
            t = text[:max(0, dist - 4)]
            arr_inner = dash * (dist - 1)
            arr_chars = list(arr_inner)
            if t:
                t_pad = (len(arr_chars) - len(t)) // 2
                for idx, ch in enumerate(t):
                    if 0 <= t_pad + idx < len(arr_chars):
                        arr_chars[t_pad + idx] = ch
            for offset, ch in enumerate(arr_chars):
                msg_line[c_src + 1 + offset] = ch
            msg_line[c_dst] = "▶"
        elif c_src > c_dst:
            dist = c_src - c_dst
            t = text[:max(0, dist - 4)]
            arr_inner = dash * (dist - 1)
            arr_chars = list(arr_inner)
            if t:
                t_pad = (len(arr_chars) - len(t)) // 2
                for idx, ch in enumerate(t):
                    if 0 <= t_pad + idx < len(arr_chars):
                        arr_chars[t_pad + idx] = ch
            for offset, ch in enumerate(arr_chars):
                msg_line[c_dst + offset] = ch
            msg_line[c_dst] = "◀"
        else:
            t = text[:col_width]
            for offset, ch in enumerate(f"─┐ {t}"):
                if c_src + offset < total_w:
                    msg_line[c_src + offset] = ch

        res.append("".join(msg_line).rstrip())

    ll = [" "] * total_w
    for c in col_centers:
        ll[c] = "│"
    res.append("".join(ll).rstrip())

    line_ftop = [" "] * total_w
    line_fmid = [" "] * total_w
    line_fbot = [" "] * total_w
    for i, (pid, lbl) in enumerate(participants):
        c_lbl = lbl[:col_width - 4]
        box_w = min(col_width - 2, len(c_lbl) + 4)
        box_w = max(box_w, 8)
        inner_w = box_w - 2
        pad_l = (inner_w - len(c_lbl)) // 2
        pad_r = inner_w - len(c_lbl) - pad_l
        top = "╭" + "─" * inner_w + "╮"
        mid = f"│{' ' * pad_l}{c_lbl}{' ' * pad_r}│"
        bot = "╰" + "─" * inner_w + "╯"
        start_x = col_centers[i] - (box_w // 2)
        for offset, ch in enumerate(top):
            line_ftop[start_x + offset] = ch
        for offset, ch in enumerate(mid):
            line_fmid[start_x + offset] = ch
        for offset, ch in enumerate(bot):
            line_fbot[start_x + offset] = ch

    res.append("".join(line_ftop).rstrip())
    res.append("".join(line_fmid).rstrip())
    res.append("".join(line_fbot).rstrip())
    return "\n".join(res)


def _parse_mermaid_flowchart(lines: list[str]) -> tuple[str, dict[str, dict], list[tuple[str, str, str, str]]]:
    direction = "TD"
    nodes: dict[str, dict] = {}
    edges: list[tuple[str, str, str, str]] = []

    edge_pat = re.compile(
        r'^(.*?)\s*(-->|==>|-\.->|-->>|->>|---|--)\s*(?:\|([^\|]+)\|)?\s*(-->|==>|-\.->|-->>|->>|---|--)?\s*(.*)$'
    )
    state_edge_pat = re.compile(
        r'^([A-Za-z0-9_\-\.\*\[\]]+)\s*-->\s*([A-Za-z0-9_\-\.\*\[\]]+)(?:\s*:\s*(.+))?$'
    )

    for line in lines:
        l = line.strip()
        if not l or l.startswith("%%"):
            continue
        m_head = re.match(r'^(?:flowchart|graph|stateDiagram(?:-v2)?)\s*([A-Za-z]*)', l, re.IGNORECASE)
        if m_head:
            d_str = m_head.group(1).upper()
            if d_str in ("TD", "TB", "LR", "RL", "BT"):
                direction = d_str
            continue
        if l.startswith("subgraph") or l == "end" or l.startswith("classDef") or l.startswith("class ") or l.startswith("style "):
            continue

        m_se = state_edge_pat.match(l)
        if m_se and (m_se.group(1) == "[*]" or m_se.group(2) == "[*]" or m_se.group(3)):
            s_src = m_se.group(1).strip()
            s_dst = m_se.group(2).strip()
            s_lbl = (m_se.group(3) or "").strip()
            if s_src == "[*]":
                s_src, src_lbl, src_shape = "[*]start", "Start", "circle"
            else:
                s_src, src_lbl, src_shape = _extract_mermaid_node_info(s_src)
            if s_dst == "[*]":
                s_dst, dst_lbl, dst_shape = "[*]end", "End", "circle"
            else:
                s_dst, dst_lbl, dst_shape = _extract_mermaid_node_info(s_dst)
            if s_src not in nodes:
                nodes[s_src] = {"label": src_lbl, "shape": src_shape}
            if s_dst not in nodes:
                nodes[s_dst] = {"label": dst_lbl, "shape": dst_shape}
            edges.append((s_src, s_dst, "-->", s_lbl))
            continue

        m_edge = edge_pat.match(l)
        if m_edge:
            left_token = m_edge.group(1).strip()
            arrow1 = m_edge.group(2)
            label = (m_edge.group(3) or "").strip()
            arrow2 = m_edge.group(4)
            right_token = m_edge.group(5).strip()

            arrow_type = arrow2 or arrow1
            src_id, src_lbl, src_shape = _extract_mermaid_node_info(left_token)
            dst_id, dst_lbl, dst_shape = _extract_mermaid_node_info(right_token)

            if src_id not in nodes or nodes[src_id]["shape"] == "plain":
                nodes[src_id] = {"label": src_lbl, "shape": src_shape}
            if dst_id not in nodes or nodes[dst_id]["shape"] == "plain":
                nodes[dst_id] = {"label": dst_lbl, "shape": dst_shape}

            edges.append((src_id, dst_id, arrow_type, label))
            continue

        nid, lbl, shape = _extract_mermaid_node_info(l)
        if nid:
            nodes[nid] = {"label": lbl, "shape": shape}

    return direction, nodes, edges


def _render_mermaid_flowchart_ascii(direction: str, nodes: dict, edges: list, max_width: int = 76) -> str:
    if not nodes:
        return "  (empty diagram)"

    succs = defaultdict(list)
    preds = defaultdict(list)
    for src, dst, arrow, label in edges:
        succs[src].append((dst, arrow, label))
        preds[dst].append((src, arrow, label))

    roots = [n for n in nodes if not preds[n]]
    if not roots:
        roots = list(nodes.keys())[:1]

    if direction in ("LR", "RL"):
        is_linear = all(len(succs[n]) <= 1 for n in nodes) and all(len(preds[n]) <= 1 for n in nodes)
        if is_linear:
            curr = roots[0]
            chain = [curr]
            visited = {curr}
            while succs[curr]:
                nxt = succs[curr][0][0]
                if nxt in visited:
                    break
                visited.add(nxt)
                chain.append(nxt)
                curr = nxt

            boxes = [_render_mermaid_box(nodes[nid]["label"], nodes[nid]["shape"], max_width=24) for nid in chain]
            arrows = [succs[nid][0][2] if (succs[nid] and succs[nid][0][2]) else "" for nid in chain[:-1]]

            total_req = sum(len(b[0]) for b in boxes) + sum(len(a) + 6 for a in arrows)
            if total_req <= max_width:
                res_lines = ["", "", ""]
                for i, b in enumerate(boxes):
                    res_lines[0] += b[0]
                    res_lines[1] += b[1]
                    res_lines[2] += b[2]
                    if i < len(arrows):
                        lbl = arrows[i]
                        arr_str = f" ──[{lbl}]─▶ " if lbl else " ────▶ "
                        pad = " " * len(arr_str)
                        res_lines[0] += pad
                        res_lines[1] += arr_str
                        res_lines[2] += pad
                return "\n".join(res_lines)

    levels: dict[str, int] = {}
    q = deque([(r, 0) for r in roots])
    visited = set()
    for r in roots:
        levels[r] = 0
        visited.add(r)

    while q:
        curr, lvl = q.popleft()
        for dst, arrow, label in succs[curr]:
            if dst not in levels or levels[dst] < lvl + 1:
                levels[dst] = lvl + 1
            if dst not in visited:
                visited.add(dst)
                q.append((dst, lvl + 1))

    for n in nodes:
        if n not in levels:
            levels[n] = max(levels.values(), default=0) + 1

    by_level: dict[int, list[str]] = defaultdict(list)
    for n, lvl in sorted(levels.items(), key=lambda x: (x[1], x[0])):
        by_level[lvl].append(n)

    output_lines: list[str] = []
    max_lvl = max(by_level.keys(), default=0)

    for lvl in range(max_lvl + 1):
        lvl_nodes = by_level[lvl]
        if not lvl_nodes:
            continue

        rendered_boxes = [_render_mermaid_box(nodes[nid]["label"], nodes[nid]["shape"], max_width=min(32, max_width // len(lvl_nodes))) for nid in lvl_nodes]
        box_widths = [len(b[0]) for b in rendered_boxes]
        spacing = 4
        total_w = sum(box_widths) + spacing * (len(lvl_nodes) - 1)

        if total_w <= max_width and len(lvl_nodes) <= 3:
            start_x = max(0, (max_width - total_w) // 2)
            row_lines = ["", "", ""]
            curr_pos = start_x
            centers = []

            for i, b in enumerate(rendered_boxes):
                bw = box_widths[i]
                c = curr_pos + (bw // 2)
                centers.append(c)
                pad_needed = curr_pos - len(row_lines[0])
                if pad_needed > 0:
                    for r in range(3):
                        row_lines[r] += " " * pad_needed
                for r in range(3):
                    row_lines[r] += b[r]
                curr_pos += bw + spacing

            for r in range(3):
                output_lines.append(row_lines[r].rstrip())

            if lvl < max_lvl:
                next_lvl_nodes = by_level[lvl + 1]
                edge_labels = []
                for nid in lvl_nodes:
                    for dst, arr, lbl in succs[nid]:
                        if dst in next_lvl_nodes:
                            edge_labels.append(lbl)

                lbl_text = f" [{edge_labels[0]}]" if (edge_labels and edge_labels[0]) else ""
                if len(centers) == 1:
                    c = centers[0]
                    output_lines.append(f"{' ' * c}│{lbl_text}")
                    output_lines.append(f"{' ' * c}▼")
                elif len(centers) == 2:
                    c1, c2 = centers[0], centers[1]
                    output_lines.append(f"{' ' * c1}│{' ' * (c2 - c1 - 1)}│")
                    output_lines.append(f"{' ' * c1}▼{' ' * (c2 - c1 - 1)}▼")
                else:
                    con = [" "] * (total_w + start_x + 1)
                    arr = [" "] * (total_w + start_x + 1)
                    for c in centers:
                        con[c] = "│"
                        arr[c] = "▼"
                    output_lines.append("".join(con).rstrip())
                    output_lines.append("".join(arr).rstrip())

        else:
            for i, nid in enumerate(lvl_nodes):
                b = rendered_boxes[i]
                indent = "   "
                output_lines.append(f"{indent}{b[0]}")
                output_lines.append(f"{indent}{b[1]}")
                output_lines.append(f"{indent}{b[2]}")
                if i < len(lvl_nodes) - 1 or lvl < max_lvl:
                    output_lines.append(f"{indent}   │")
                    output_lines.append(f"{indent}   ▼")

    return "\n".join(output_lines)


def render_mermaid_ascii(mermaid_src: str, max_width: int = 76) -> str:
    """
    Renders Mermaid diagram syntax into clean Unicode rounded box-drawing text.
    Supports flowchart TD/TB/LR/RL, graph, sequenceDiagram, and stateDiagram.
    """
    lines = [l for l in mermaid_src.strip().splitlines() if l.strip()]
    if not lines:
        return ""
    first_line = lines[0].strip().lower()
    if first_line.startswith("sequencediagram"):
        return _render_mermaid_sequence_diagram(lines, max_width=max_width)
    direction, nodes, edges = _parse_mermaid_flowchart(lines)
    return _render_mermaid_flowchart_ascii(direction, nodes, edges, max_width=max_width)


def preprocess_mermaid_blocks(md_text: str, max_width: int = 76) -> str:
    """
    Finds fenced ```mermaid code blocks in markdown and converts them
    to ```text blocks containing rendered Unicode box-drawing diagrams.
    """
    if "```mermaid" not in md_text:
        return md_text

    def _replace_block(m: re.Match) -> str:
        code = m.group(1).strip()
        try:
            rendered = render_mermaid_ascii(code, max_width=max_width)
            if rendered:
                return f"```text\n{rendered}\n```"
            return m.group(0)
        except Exception:
            return m.group(0)

    pattern = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
    return pattern.sub(_replace_block, md_text)


__all__ = [
    # Canonical Paths
    "LIVE_STATE_PATH",
    "LIVE_STATE_LOCK_PATH",
    "SIDEBAR_MODE_PATH",
    "CACHE_PATH",
    "PERSISTENT_CACHE_PATH",
    "CACHE_PATHS",
    "LOCK_PATH",
    "PRESENCE_DIR",
    "DB_PATH",
    "BRAIN_DIR",
    "STATUSLINE_BIN",
    "SQUAD_BIN",
    "SIDEBAR_BIN",
    "MCP_CONFIG_PATH",
    "MCP_TOOLS_DIR",
    # CachyOS Emerald Dark Colors
    "C_COMMENT",
    "C_CYAN",
    "C_GREEN",
    "C_ORANGE",
    "C_PINK",
    "C_PURPLE",
    "C_RED",
    "C_YELLOW",
    "C_WHITE",
    "C_ROSEWATER",
    "C_SURFACE",
    "C_RESET",
    "C_BOLD",
    "C_DIM",
    "C_REV",
    "ANSI_RE",
    # Agent State Tokens & Badges
    "STATE_BLOCKED",
    "STATE_ACTIVE",
    "STATE_WAITING",
    "STATE_HEALING",
    "STATE_DONE",
    "STATE_ERR",
    "STATE_IDLE",
    "STATE_PRIORITY",
    "classify_agent_state",
    "format_state_badge",
    # Text & Unicode Helpers
    "strip_ansi",
    "char_cell_width",
    "visible_len",
    "format_line",
    # Gauges & Spinners
    "SPINNER_FRAMES",
    "get_spinner_frame",
    "render_smooth_gauge",
    "render_gradient_gauge",
    "render_braille_sparkline",
    # Worktrees & Locks & DB
    "get_git_worktrees",
    "get_locked_conversation_ids",
    "connect_db_ro",
    # Live State & Ground-Truth Readers
    "read_live_state",
    "get_current_session_key",
    "update_live_state_atomic",
    "get_sidebar_mode",
    "set_sidebar_mode",
    "discover_tmux_session_conversation_id",
    "resolve_root_conversation_id",
    "resolve_workspace_cwd",
    "get_git_diff_stat",
    "read_quota_cache",
    "write_quota_cache",
    "refresh_quota_cache_now",
    "trigger_background_quota_refresh",
    "trigger_background_refresh_if_needed",
    "resolve_quota_pair",
    "compute_cache_hit_pct",
    "format_token_k",
    "TokenTelemetry",
    "resolve_session_token_telemetry",
    "extract_step_tool_summaries",
    "format_countdown",
    "format_countdown_short",
    "discover_brain_subagents",
    "discover_brain_tasks",
    "discover_cycle_mode",
    "merge_and_dedup_subagents",
    # Mermaid Box Rendering
    "render_mermaid_ascii",
    "preprocess_mermaid_blocks",
    # Inotify
    "InotifyWatcher",
]

from __future__ import annotations

import ast
import functools
import json
import os
import re
import sqlite3
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from codegraph.db import DEFAULT_DB_PATH, get_connection

SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
    "target",
}

MATCH_EXTS = {
    ".py",
    ".sh",
    ".md",
    ".toml",
    ".yaml",
    ".yml",
    ".json",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".rs",
    ".go",
    ".kt",
    ".kts",
    ".java",
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".rb",
    ".php",
    ".cs",
    ".swift",
    ".sql",
    ".css",
    ".scss",
    ".html",
    ".vue",
    ".svelte",
}


@dataclass
class FileMetrics:
    path: str
    language: str
    line_count: int
    symbol_count: int
    class_count: int
    function_count: int
    heading_count: int
    parse_backend: str


_mem_cache: dict[str, tuple[int, int, FileMetrics]] = {}
_dir_summary_cache: dict[tuple[str, int], tuple[float, dict[str, Any]]] = {}


def _iter_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    files: list[Path] = []
    path_str = str(path)
    stack = [path_str]
    while stack:
        curr = stack.pop()
        try:
            with os.scandir(curr) as it:
                for entry in it:
                    if entry.name in SKIP_DIRS:
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        ext = os.path.splitext(entry.name)[1].lower()
                        if ext in MATCH_EXTS:
                            files.append(Path(entry.path))
        except OSError:
            pass
    return sorted(files)


def _language(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix == ".sh":
        return "shell"
    if suffix == ".md":
        return "markdown"
    if suffix == ".toml":
        return "toml"
    if suffix in {".yaml", ".yml"}:
        return "yaml"
    if suffix == ".json":
        return "json"
    if suffix in {".ts", ".tsx"}:
        return "typescript"
    if suffix in {".js", ".jsx", ".mjs", ".cjs"}:
        return "javascript"
    if suffix in {".kt", ".kts"}:
        return "kotlin"
    if suffix == ".go":
        return "go"
    if suffix == ".rs":
        return "rust"
    if suffix == ".java":
        return "java"
    if suffix in {".c", ".h"}:
        return "c"
    if suffix in {".cc", ".cpp", ".cxx", ".hh", ".hpp"}:
        return "cpp"
    if suffix == ".rb":
        return "ruby"
    if suffix == ".php":
        return "php"
    if suffix == ".cs":
        return "csharp"
    if suffix == ".swift":
        return "swift"
    if suffix == ".sql":
        return "sql"
    if suffix in {".css", ".scss"}:
        return "css"
    if suffix in {".html", ".vue", ".svelte"}:
        return "html"
    return "text"


def _tree_sitter_summary(path: Path) -> tuple[dict[str, Any] | None, str]:
    try:
        proc = subprocess.run(
            ["tree-sitter", "parse", "--json-summary", str(path)],
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None, "fallback"
    if proc.returncode != 0:
        return None, "fallback"
    raw = proc.stdout.strip()
    if not raw:
        return None, "fallback"
    try:
        data = json.loads(raw)
        return data, "tree-sitter-cli"
    except Exception:
        return None, "fallback"


def _python_metrics(path: Path, text: str) -> tuple[int, int, int]:
    try:
        tree = ast.parse(text)
    except Exception:
        return 0, 0, 0
    classes = 0
    functions = 0
    symbols = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes += 1
            symbols += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
            symbols += 1
    return symbols, classes, functions


def _shell_metrics(text: str) -> tuple[int, int]:
    functions = len(re.findall(r"^\s*[A-Za-z_][A-Za-z0-9_]*\s*\(\)\s*\{", text, flags=re.M))
    return functions, functions


def _markdown_headings(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.lstrip().startswith("#"))


def _code_metrics(lang: str, text: str) -> tuple[int, int, int]:
    classes = 0
    functions = 0
    if lang in ("typescript", "javascript"):
        classes = len(re.findall(r"(?:^|;|\n)\s*(?:export\s+(?:default\s+)?)?(?:class|interface|enum)\s+[A-Za-z_$]", text))
        functions = len(re.findall(r"(?:^|;|\n)\s*(?:export\s+(?:default\s+)?)?(?:async\s+)?function\s+[A-Za-z_$]", text))
        functions += len(re.findall(r"(?:^|;|\n)\s*(?:export\s+)?(?:const|let|var)\s+[A-Za-z_$][\w$]*(?:\s*:\s*[^=]+)?\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>", text))
    elif lang in ("kotlin", "java"):
        classes = len(re.findall(r"^\s*(?:(?:public|private|internal|protected|open|abstract|sealed|data)\s+)*(?:class|interface|object|enum(?:\s+class)?)\s+[A-Za-z_]", text, flags=re.M))
        functions = len(re.findall(r"^\s*(?:(?:public|private|internal|protected|suspend|override|inline)\s+)*fun\s+(?:<[^>]+>\s*)?[A-Za-z_]", text, flags=re.M))
        if lang == "java":
            functions += len(re.findall(r"^\s*(?:(?:public|private|protected|static|final|synchronized|abstract)\s+)+[\w<>\[\],\s]+\s+[A-Za-z_]\w*\s*\([^;]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{", text, flags=re.M))
    elif lang == "go":
        classes = len(re.findall(r"^\s*type\s+[A-Za-z_][\w]*\s+(?:struct|interface)", text, flags=re.M))
        functions = len(re.findall(r"^\s*func\s+(?:\([^\)]+\)\s+)?[A-Za-z_]", text, flags=re.M))
    elif lang == "rust":
        classes = len(re.findall(r"^\s*(?:pub(?:\([^\)]+\))?\s+)?(?:struct|enum|trait)\s+[A-Za-z_]", text, flags=re.M))
        functions = len(re.findall(r"^\s*(?:pub(?:\([^\)]+\))?\s+)?(?:async\s+)?fn\s+[A-Za-z_]", text, flags=re.M))
    elif lang in ("c", "cpp"):
        classes = len(re.findall(r"^\s*(?:class|struct)\s+[A-Za-z_]", text, flags=re.M))
        functions = len(re.findall(r"^\s*(?:[\w:*&<>]+\s+)+[A-Za-z_]\w*\s*\([^;]*\)\s*(?:const)?\s*\{", text, flags=re.M))
    elif lang == "ruby":
        classes = len(re.findall(r"^\s*(?:class|module)\s+[A-Za-z_]", text, flags=re.M))
        functions = len(re.findall(r"^\s*def\s+[A-Za-z_]", text, flags=re.M))
    elif lang == "php":
        classes = len(re.findall(r"^\s*(?:abstract\s+|final\s+)?(?:class|interface|trait)\s+[A-Za-z_]", text, flags=re.M))
        functions = len(re.findall(r"^\s*(?:(?:public|private|protected|static)\s+)*function\s+[A-Za-z_]", text, flags=re.M))
    elif lang == "csharp":
        classes = len(re.findall(r"^\s*(?:(?:public|private|protected|internal|static|abstract|sealed)\s+)*(?:class|interface|struct|enum)\s+[A-Za-z_]", text, flags=re.M))
        functions = len(re.findall(r"^\s*(?:(?:public|private|protected|internal|static|async|override|virtual)\s+)+[\w<>\[\],\s]+\s+[A-Za-z_]\w*\s*\(", text, flags=re.M))
    elif lang == "swift":
        classes = len(re.findall(r"^\s*(?:(?:public|private|fileprivate|internal|open)\s+)*(?:class|struct|enum|protocol)\s+[A-Za-z_]", text, flags=re.M))
        functions = len(re.findall(r"^\s*(?:(?:public|private|fileprivate|internal|open|static|override)\s+)*func\s+[A-Za-z_]", text, flags=re.M))
    else:
        classes = len(re.findall(r"^\s*(?:export\s+)?class\s+[A-Za-z_$]", text, flags=re.M))
        functions = len(re.findall(r"^\s*(?:def|fun|fn|function)\s+[A-Za-z_$]", text, flags=re.M))

    symbols = classes + functions
    return symbols, classes, functions


def _summarize_file(path: Path) -> FileMetrics:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lang = _language(path)
    line_count = len(text.splitlines())
    parse_data, backend = _tree_sitter_summary(path)
    if lang == "python":
        symbol_count, class_count, function_count = _python_metrics(path, text)
        heading_count = 0
        if parse_data and isinstance(parse_data, dict):
            function_count = int(parse_data.get("functions", function_count) or function_count)
            class_count = int(parse_data.get("classes", class_count) or class_count)
            symbol_count = function_count + class_count
        return FileMetrics(str(path), lang, line_count, symbol_count, class_count, function_count, heading_count, backend)
    if lang == "shell":
        symbol_count, function_count = _shell_metrics(text)
        return FileMetrics(str(path), lang, line_count, symbol_count, 0, function_count, 0, backend)
    if lang == "markdown":
        headings = _markdown_headings(text)
        return FileMetrics(str(path), lang, line_count, headings, 0, 0, headings, backend)
    if lang in {
        "typescript", "javascript", "kotlin", "java", "go", "rust",
        "c", "cpp", "ruby", "php", "csharp", "swift",
    }:
        symbol_count, class_count, function_count = _code_metrics(lang, text)
        if parse_data and isinstance(parse_data, dict):
            function_count = int(parse_data.get("functions", function_count) or function_count)
            class_count = int(parse_data.get("classes", class_count) or class_count)
            symbol_count = function_count + class_count
        return FileMetrics(str(path), lang, line_count, symbol_count, class_count, function_count, 0, backend)
    return FileMetrics(str(path), lang, line_count, 0, 0, 0, 0, backend)


_compute_metrics_for = _summarize_file


def _get_cached_or_compute_batch(files: list[Path], db_path: Path = DEFAULT_DB_PATH) -> list[FileMetrics]:
    if not files:
        return []

    conn = get_connection(db_path)
    results: dict[str, FileMetrics] = {}
    to_query_db: list[tuple[Path, int, int]] = []

    # 1. Check in-memory cache
    for f in files:
        f_str = str(f)
        try:
            st = f.stat()
            mtime_ns, size = st.st_mtime_ns, st.st_size
        except OSError:
            continue

        if f_str in _mem_cache:
            c_mtime, c_size, cached_metric = _mem_cache[f_str]
            if c_mtime == mtime_ns and c_size == size:
                results[f_str] = cached_metric
                continue

        to_query_db.append((f, mtime_ns, size))

    if not to_query_db:
        return [results[str(f)] for f in files if str(f) in results]

    # 2. Check SQLite cache
    c = conn.cursor()
    chunk_size = 500
    misses: list[tuple[Path, int, int]] = []
    now = time.time()

    for i in range(0, len(to_query_db), chunk_size):
        chunk = to_query_db[i : i + chunk_size]
        paths = [str(f) for f, _, _ in chunk]
        placeholders = ",".join(["?"] * len(paths))

        c.execute(
            f"""
            SELECT path, mtime_ns, size, language, line_count, symbol_count,
                   class_count, function_count, heading_count, parse_backend
            FROM file_metrics
            WHERE path IN ({placeholders})
            """,
            paths,
        )
        db_rows = {row["path"]: row for row in c.fetchall()}

        for f, mtime_ns, size in chunk:
            f_str = str(f)
            row = db_rows.get(f_str)
            if row and row["mtime_ns"] == mtime_ns and row["size"] == size:
                fm = FileMetrics(
                    path=row["path"],
                    language=row["language"],
                    line_count=row["line_count"],
                    symbol_count=row["symbol_count"],
                    class_count=row["class_count"],
                    function_count=row["function_count"],
                    heading_count=row["heading_count"],
                    parse_backend=row["parse_backend"],
                )
                results[f_str] = fm
                _mem_cache[f_str] = (mtime_ns, size, fm)
            else:
                misses.append((f, mtime_ns, size))

    # 3. Compute misses and save to SQLite
    if misses:
        new_rows = []
        for f, mtime_ns, size in misses:
            f_str = str(f)
            try:
                fm = _compute_metrics_for(f)
                results[f_str] = fm
                _mem_cache[f_str] = (mtime_ns, size, fm)
                new_rows.append((
                    fm.path,
                    mtime_ns,
                    size,
                    fm.language,
                    fm.line_count,
                    fm.symbol_count,
                    fm.class_count,
                    fm.function_count,
                    fm.heading_count,
                    fm.parse_backend,
                    now,
                ))
            except Exception:
                pass

        if new_rows:
            with conn:
                conn.executemany(
                    """
                    INSERT OR REPLACE INTO file_metrics
                    (path, mtime_ns, size, language, line_count, symbol_count,
                     class_count, function_count, heading_count, parse_backend, cached_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    new_rows,
                )

    return [results[str(f)] for f in files if str(f) in results]


def summarize_path(path: str, limit: int = 50, db_path: Path = DEFAULT_DB_PATH) -> dict[str, Any]:
    """Summarize structural metrics for a file or directory with fast persistent SQLite caching."""
    target = Path(path).expanduser().resolve()
    if not target.exists():
        return {"error": "path_not_found", "path": str(target)}

    target_str = str(target)
    cache_key = (target_str, limit)
    now = time.time()
    # 2-second short-lived memoization for repeated directory queries
    if cache_key in _dir_summary_cache:
        ts, cached_result = _dir_summary_cache[cache_key]
        if now - ts < 2.0:
            return cached_result

    files = _iter_files(target)
    metrics = _get_cached_or_compute_batch(files, db_path=db_path)
    sorted_files = sorted([metric.__dict__ for metric in metrics], key=lambda x: x.get("line_count", 0), reverse=True)
    capped_files = sorted_files[:limit]
    total_files = len(files)
    truncated = total_files > limit

    result = {
        "path": str(target),
        "file_count": total_files,
        "total_files": total_files,
        "truncated": truncated,
        "files": capped_files,
        "language_counts": {
            lang: sum(1 for metric in metrics if metric.language == lang)
            for lang in sorted({metric.language for metric in metrics})
        },
    }
    _dir_summary_cache[cache_key] = (now, result)
    return result


@functools.lru_cache(maxsize=4096)
def _parse_diff_symbols(diff_text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    added = re.findall(r"^\+\s*(?:def|class|function)\s+([A-Za-z_][A-Za-z0-9_]*)", diff_text, flags=re.M)
    removed = re.findall(r"^\-\s*(?:def|class|function)\s+([A-Za-z_][A-Za-z0-9_]*)", diff_text, flags=re.M)
    return tuple(sorted(set(added))), tuple(sorted(set(removed)))


def changed_symbols(diff_text: str) -> dict[str, Any]:
    """Extract symbol-like names from a diff with fast LRU caching."""
    added, removed = _parse_diff_symbols(diff_text)
    return {
        "added_symbols": list(added),
        "removed_symbols": list(removed),
        "count_added": len(added),
        "count_removed": len(removed),
    }

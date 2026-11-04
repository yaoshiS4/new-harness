#!/usr/bin/env python3
"""Terminal TUI Table Formatter (Zero Column Shift).

Formats Markdown pipe tables and JSON table definitions into 100%
column-symmetric Unicode box-drawing tables with exact terminal display-width
measurement, NFC normalization, link stripping, and multi-line cell wrapping.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union


def char_display_width(ch: str) -> int:
    """Return terminal display width (0, 1, or 2) of a single Unicode character."""
    if unicodedata.combining(ch) != 0:
        return 0
    cat = unicodedata.category(ch)
    if cat in ("Mn", "Me", "Cf", "Cc"):
        return 0
    eaw = unicodedata.east_asian_width(ch)
    if eaw in ("W", "F"):
        return 2
    return 1


def string_display_width(text: str) -> int:
    """Return exact terminal display width of an NFC-normalized string."""
    norm = unicodedata.normalize("NFC", text)
    return sum(char_display_width(ch) for ch in norm)


def strip_markdown_links(text: str) -> str:
    """Strip inline Markdown links [label](url) to bare label."""
    return re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)


def wrap_cell(text: str, max_width: int) -> List[str]:
    """Wrap cell text into lines with display width <= max_width."""
    cleaned = strip_markdown_links(text)
    norm = unicodedata.normalize("NFC", cleaned.strip())
    if not norm:
        return [""]

    raw_paragraphs = re.split(r'<br\s*/?>|\n', norm)
    result_lines: List[str] = []

    for para in raw_paragraphs:
        words = para.split()
        if not words:
            result_lines.append("")
            continue

        curr_line = ""
        curr_width = 0

        for w in words:
            w_norm = unicodedata.normalize("NFC", w)
            w_w = string_display_width(w_norm)

            if w_w > max_width:
                if curr_line:
                    result_lines.append(curr_line)
                    curr_line = ""
                    curr_width = 0

                chunk = ""
                chunk_w = 0
                for ch in w_norm:
                    ch_w = char_display_width(ch)
                    if chunk_w + ch_w > max_width:
                        result_lines.append(chunk)
                        chunk = ch
                        chunk_w = ch_w
                    else:
                        chunk += ch
                        chunk_w += ch_w
                if chunk:
                    curr_line = chunk
                    curr_width = chunk_w
                continue

            space_w = 1 if curr_line else 0
            if curr_width + space_w + w_w <= max_width:
                if curr_line:
                    curr_line += " " + w_norm
                    curr_width += 1 + w_w
                else:
                    curr_line = w_norm
                    curr_width = w_w
            else:
                result_lines.append(curr_line)
                curr_line = w_norm
                curr_width = w_w

        if curr_line:
            result_lines.append(curr_line)

    return result_lines if result_lines else [""]


def parse_markdown_table(text: str) -> Tuple[List[str], List[List[str]]]:
    """Parse a Markdown pipe table into headers and data rows."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    table_lines = [l for l in lines if "|" in l]
    if not table_lines:
        return [], []

    raw_rows: List[List[str]] = []
    divider_idx = -1

    for idx, l in enumerate(table_lines):
        content = l
        if content.startswith("|"):
            content = content[1:]
        if content.endswith("|"):
            content = content[:-1]

        cells = [c.strip() for c in content.split("|")]
        is_divider = all(re.match(r'^:?-+:?$', c) for c in cells if c) and any("-" in c for c in cells)
        if is_divider and divider_idx == -1:
            divider_idx = idx
            continue
        raw_rows.append(cells)

    if divider_idx > 0 and raw_rows:
        headers = raw_rows[0]
        data_rows = raw_rows[1:]
    elif len(raw_rows) > 1:
        headers = raw_rows[0]
        data_rows = raw_rows[1:]
    elif raw_rows:
        headers = raw_rows[0]
        data_rows = []
    else:
        headers, data_rows = [], []

    return headers, data_rows


def parse_json_table(data_str: str) -> Tuple[List[str], List[List[str]]]:
    """Parse JSON table input into headers and data rows."""
    parsed = json.loads(data_str)
    if isinstance(parsed, dict):
        headers = [str(h) for h in parsed.get("headers", [])]
        rows = [[str(cell) for cell in r] for r in parsed.get("rows", [])]
        return headers, rows

    if isinstance(parsed, list):
        if not parsed:
            return [], []
        if isinstance(parsed[0], dict):
            headers = list(parsed[0].keys())
            rows = [[str(item.get(k, "")) for k in headers] for item in parsed]
            return headers, rows
        if isinstance(parsed[0], list):
            headers = [str(c) for c in parsed[0]]
            rows = [[str(cell) for cell in r] for r in parsed[1:]]
            return headers, rows

    return [], []


def format_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    max_col_width: int = 36,
    min_col_width: int = 4,
    row_separators: bool = True,
) -> str:
    """Render headers and data rows as a 100% column-symmetric Unicode box-drawing table."""
    num_cols = len(headers)
    for r in rows:
        if len(r) > num_cols:
            num_cols = len(r)

    if num_cols == 0:
        return ""

    norm_headers = [strip_markdown_links(str(h or "")) for h in list(headers) + [""] * (num_cols - len(headers))]
    norm_rows = [
        [strip_markdown_links(str(cell or "")) for cell in list(r) + [""] * (num_cols - len(r))]
        for r in rows
    ]

    col_widths: List[int] = []
    for c in range(num_cols):
        h_w = string_display_width(norm_headers[c])
        max_seen = h_w
        for r in norm_rows:
            cell_w = string_display_width(r[c])
            if cell_w > max_seen:
                max_seen = cell_w

        chosen_w = min(max_seen, max_col_width)
        for r in norm_rows:
            for w in r[c].split():
                w_w = string_display_width(w)
                if w_w > chosen_w:
                    chosen_w = min(w_w, max_col_width)

        chosen_w = max(chosen_w, min_col_width)
        col_widths.append(chosen_w)

    top_border = "┌─" + "─┬─".join("─" * w for w in col_widths) + "─┐"
    header_sep = "├─" + "─┼─".join("─" * w for w in col_widths) + "─┤"
    row_sep = "├─" + "─┼─".join("─" * w for w in col_widths) + "─┤"
    bot_border = "└─" + "─┴─".join("─" * w for w in col_widths) + "─┘"

    def render_row_lines(cells: Sequence[str]) -> List[str]:
        wrapped = [wrap_cell(cells[c], col_widths[c]) for c in range(num_cols)]
        height = max(len(w) for w in wrapped)
        lines: List[str] = []
        for h in range(height):
            line_cells: List[str] = []
            for c in range(num_cols):
                line_text = wrapped[c][h] if h < len(wrapped[c]) else ""
                pad_needed = col_widths[c] - string_display_width(line_text)
                padded = line_text + (" " * max(0, pad_needed))
                line_cells.append(padded)
            lines.append("│ " + " │ ".join(line_cells) + " │")
        return lines

    output_lines: List[str] = [top_border]

    if any(norm_headers):
        output_lines.extend(render_row_lines(norm_headers))
        output_lines.append(header_sep)

    for idx, r in enumerate(norm_rows):
        if idx > 0 and row_separators:
            output_lines.append(row_sep)
        output_lines.extend(render_row_lines(r))

    output_lines.append(bot_border)
    return "\n".join(output_lines)


def format_markdown_or_json(raw_input: str, max_col_width: int = 36) -> str:
    """Auto-detect format (JSON or Markdown) and return formatted Unicode box table."""
    stripped = raw_input.strip()
    if (stripped.startswith("{") and stripped.endswith("}")) or (stripped.startswith("[") and stripped.endswith("]")):
        try:
            headers, rows = parse_json_table(stripped)
            if headers or rows:
                return format_table(headers, rows, max_col_width=max_col_width)
        except Exception:
            pass

    headers, rows = parse_markdown_table(stripped)
    return format_table(headers, rows, max_col_width=max_col_width)


def self_test() -> bool:
    """Verify terminal display width, Vietnamese diacritics, and 100% column divider symmetry."""
    sample_table = (
        "| Thành Phần (Bát Tự / Tử Vi) | Vai Trò Trong Lá Số | Ý Nghĩa Triết Học & Dữ Liệu |\n"
        "| :--- | :--- | :--- |\n"
        "| 1. Bát Tự Tứ Trụ (baziAnalysisEngine.ts) | Nhật chủ [Ất Mộc](file:///apps/web/bazi.ts) | Đại diện cho bản mệnh âm mộc, linh hoạt, thích nghi cao, cần hỏa sưởi ấm và thủy dưỡng. |\n"
        "| 2. Tử Vi Đẩu Số (luuNienEngine.ts) | Cung Mệnh / Lưu Niên | Chu kỳ vận hạn 10 năm chuyển dịch theo cung chức và tiểu hạn hàng năm. |\n"
        "| 3. Ngũ Hành Phối Hợp | [Hỏa / Thổ](file:///apps/web/elements.ts) | Cân bằng sinh khắc điều hòa bát tự theo thiên can địa chi. |\n"
    )

    formatted = format_markdown_or_json(sample_table, max_col_width=32)
    lines = formatted.splitlines()

    assert len(lines) >= 8, f"Expected multi-line output, got {len(lines)} lines"
    assert "file:///" not in formatted, "Link URLs were not stripped from table output"
    assert "Ất Mộc" in formatted, "Vietnamese label lost during link stripping"

    expected_total_width = string_display_width(lines[0])
    for idx, l in enumerate(lines):
        w = string_display_width(l)
        assert w == expected_total_width, (
            f"Line {idx} display width mismatch: expected {expected_total_width}, got {w}\nLine: {l}"
        )

    content_lines = [l for l in lines if l.startswith("│")]
    first_divider_indices = [i for i, ch in enumerate(content_lines[0]) if ch == "│"]
    for idx, cl in enumerate(content_lines[1:], start=1):
        indices = [i for i, ch in enumerate(cl) if ch == "│"]
        assert indices == first_divider_indices, (
            f"Column divider index shift at content line {idx}!\n"
            f"Expected {first_divider_indices}, got {indices}\nLine: {cl}"
        )

    print("=== TUI Table Formatter Self-Test ===")
    print("NFC Diacritic Normalization: PASS")
    print("Markdown Link Stripping: PASS")
    print(f"Total Display Width ({expected_total_width}): PASS (100% consistent across all {len(lines)} lines)")
    print("Vertical Divider Symmetry: PASS (Zero column shift)")
    print("ALL TESTS PASSED")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Format tables for Terminal TUI with 100% column symmetry")
    parser.add_argument("--input", "-i", help="Input table file path (Markdown or JSON). Defaults to stdin.")
    parser.add_argument("--max-col-width", "-w", type=int, default=36, help="Maximum column width (default: 36)")
    parser.add_argument("--self-test", action="store_true", help="Run self-test suite covering Vietnamese diacritics and column alignment")

    args = parser.parse_args()

    if args.self_test:
        self_test()
        return 0

    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            raw_text = f.read()
    else:
        if sys.stdin.isatty():
            parser.print_help()
            return 1
        raw_text = sys.stdin.read()

    result = format_markdown_or_json(raw_text, max_col_width=args.max_col_width)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())

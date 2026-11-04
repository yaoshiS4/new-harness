#!/usr/bin/env python3
"""Mechanical Harness Tree Validator (Harness² Protocol).

Modeled on arXiv:2610.14224v1 (Harness²), this validator enforces:
1. Check 1 (Always-On Byte Budget): Verifies ~/.gemini/GEMINI.md char count <= --max-chars (default 12000).
2. Check 2 (Skill Trigger & Index Coverage): Verifies all 29 skills in ~/.gemini/antigravity/skills/ and config/skills/
   are referenced in GEMINI.md, ROLE_SKILL_BUNDLES in pre_invocation_hook.py, or
   ~/.gemini/antigravity/skillbank/INDEX.md (with --autotrigger flag support).
3. Check 3 (Template Brace Sanitizer): Checks ~/.gemini/GEMINI.md outside fenced code blocks
   for unescaped {{ or {%.
4. Check 4 (Script Existence & Compile Check): Verifies all ~/.gemini/.../*.py and *.sh paths
   in hooks.json, GEMINI.md, and ~/.gemini/antigravity/scripts/ exist on disk and pass py_compile / bash -n.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path


def _resolve_gemini_target(gemini_path: str | Path) -> Path:
    """Resolves GEMINI.md target path, falling back to repo antigravity/GLOBAL_AGENTS.md if missing."""
    target = Path(os.path.expanduser(str(gemini_path)))
    if target.is_file():
        return target
    repo_root = Path(__file__).resolve().parent.parent.parent
    fallback = repo_root / "antigravity" / "GLOBAL_AGENTS.md"
    if fallback.is_file() and (
        target.name in ("GEMINI.md", "AGENTS.md", "GLOBAL_AGENTS.md")
    ):
        return fallback
    return target


def check_active_rules_byte_budget(
    gemini_path: str | Path,
    repo_root: str | Path | None = None,
    max_file_bytes: int = 24000,
    max_aggregate_bytes: int = 64000,
) -> tuple[bool, str, dict]:
    """Verifies active rule files stay < 24,000 bytes each and <= 64,000 bytes aggregate,
    excluding antigravity-cli/builtin/, _archived*, and disabled config/plugins/*/rules/."""
    target = _resolve_gemini_target(gemini_path)
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parent.parent.parent

    # Determine enabled plugins from config/config.json if present
    enabled_plugins: set[str] = set()
    for cfg_candidate in (
        root / "config" / "config.json",
        Path(os.path.expanduser("~/.gemini/config/config.json")),
    ):
        if cfg_candidate.is_file():
            try:
                cfg_data = json.loads(cfg_candidate.read_text(encoding="utf-8"))
                plugins_map = cfg_data.get("plugins") or {}
                if isinstance(plugins_map, dict):
                    for p_name, p_state in plugins_map.items():
                        if isinstance(p_state, dict) and p_state.get("enabled") is True:
                            enabled_plugins.add(p_name)
                break
            except Exception:
                pass

    rule_files: list[Path] = []
    seen_real: set[Path] = set()

    def _add_rule(p: Path) -> None:
        if not p.is_file():
            return
        p_str = str(p)
        if "antigravity-cli/builtin/" in p_str or "_archived" in p_str:
            return
        try:
            real_p = p.resolve()
        except Exception:
            real_p = p
        if real_p in seen_real:
            return
        seen_real.add(real_p)
        rule_files.append(p)

    _add_rule(target)
    if root.is_dir():
        _add_rule(root / "AGENTS.md")
        for r_dir in (root / ".agents" / "rules", root / "config" / "rules"):
            if r_dir.is_dir():
                for rf in sorted(r_dir.rglob("*.md")):
                    _add_rule(rf)
        plugins_root = root / "config" / "plugins"
        if plugins_root.is_dir():
            for p_dir in sorted(plugins_root.iterdir()):
                if not p_dir.is_dir():
                    continue
                if p_dir.name not in enabled_plugins:
                    continue
                p_rules = p_dir / "rules"
                if p_rules.is_dir():
                    for rf in sorted(p_rules.rglob("*.md")):
                        _add_rule(rf)

    per_file_bytes: dict[str, int] = {}
    oversized: list[str] = []
    aggregate_bytes = 0

    for rf in rule_files:
        try:
            sz = len(rf.read_bytes())
        except Exception:
            sz = 0
        per_file_bytes[str(rf)] = sz
        aggregate_bytes += sz
        if sz >= max_file_bytes:
            oversized.append(f"{rf.name} ({sz} >= {max_file_bytes}B)")

    details = {
        "files_checked": len(rule_files),
        "per_file_bytes": per_file_bytes,
        "aggregate_bytes": aggregate_bytes,
        "max_file_bytes": max_file_bytes,
        "max_aggregate_bytes": max_aggregate_bytes,
        "oversized_files": oversized,
    }
    if oversized:
        return (
            False,
            f"Rule File Byte Budget Exceeded: {', '.join(oversized)}",
            details,
        )
    if aggregate_bytes > max_aggregate_bytes:
        return (
            False,
            f"Aggregate Rules Byte Budget Exceeded: {aggregate_bytes}B > {max_aggregate_bytes}B",
            details,
        )
    return (
        True,
        f"Active Rules Budget OK: {aggregate_bytes}B <= {max_aggregate_bytes}B across {len(rule_files)} file(s) (<{max_file_bytes}B/file)",
        details,
    )


def check_always_on_byte_budget(
    gemini_path: str | Path,
    max_chars: int = 12000,
) -> tuple[bool, str, int]:
    """Check 1: Verifies GEMINI.md char count and active rules byte budgets stay within configured ceilings."""
    target = _resolve_gemini_target(gemini_path)
    if not target.is_file():
        return False, f"GEMINI.md not found at {target}", 0

    try:
        content = target.read_text(encoding="utf-8")
    except Exception as exc:
        return False, f"Failed reading {target}: {exc}", 0

    char_count = len(content)
    if char_count > max_chars:
        return (
            False,
            f"Always-On Byte Budget Exceeded: GEMINI.md has {char_count} chars (ceiling: {max_chars})",
            char_count,
        )
    rules_ok, rules_msg, _ = check_active_rules_byte_budget(target)
    if not rules_ok:
        return False, rules_msg, char_count
    return (
        True,
        f"Always-On Byte Budget OK: GEMINI.md char count = {char_count} <= {max_chars} | {rules_msg}",
        char_count,
    )


def extract_template_brace_violations(text: str) -> list[dict]:
    """Finds unescaped {{ or {% outside of fenced code blocks."""
    violations: list[dict] = []
    in_fence = False
    fence_char = ""
    fence_len = 0

    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Check fence entry/exit (``` or ~~~)
        if not in_fence:
            m = re.match(r"^(`{3,}|~{3,})", stripped)
            if m:
                in_fence = True
                fence_char = m.group(1)[0]
                fence_len = len(m.group(1))
                continue
        else:
            m = re.match(r"^(`{3,}|~{3,})", stripped)
            if m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len:
                in_fence = False
                continue
            continue

        # Outside fences: check for unescaped {{ or {%
        for brace_pat in (r"(?<!\\)\{\{", r"(?<!\\)\{%"):
            for match in re.finditer(brace_pat, line):
                violations.append({
                    "line": idx,
                    "token": match.group(0),
                    "context": line.strip()[:100],
                })

    return violations


def check_template_braces(gemini_path: str | Path) -> tuple[bool, str, list[dict]]:
    """Check 3: Checks GEMINI.md outside fenced code blocks for unescaped {{ or {%."""
    target = _resolve_gemini_target(gemini_path)
    if not target.is_file():
        return False, f"GEMINI.md not found at {target}", []

    try:
        content = target.read_text(encoding="utf-8")
    except Exception as exc:
        return False, f"Failed reading {target}: {exc}", []

    violations = extract_template_brace_violations(content)
    if violations:
        return (
            False,
            f"Template Brace Sanitizer: Found {len(violations)} unescaped template brace(s) outside code fences",
            violations,
        )
    return (
        True,
        "Template Brace Sanitizer OK: 0 unescaped template braces outside code fences",
        [],
    )


def _extract_skill_frontmatter(skill_md_path: Path) -> tuple[str, str]:
    """Extracts name and description from SKILL.md frontmatter."""
    name = skill_md_path.parent.name
    desc = ""
    if not skill_md_path.is_file():
        return name, desc

    try:
        content = skill_md_path.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm = parts[1]
                for line in fm.splitlines():
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip()
                    elif line.startswith("description:"):
                        desc = line.split(":", 1)[1].strip()
    except Exception:
        pass
    return name, desc


def _generate_skill_cues(name: str, desc: str) -> str:
    """Generates trigger cues from skill name and description."""
    tokens = [name.replace("-", " "), name]
    words = re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", desc.lower())
    stop_words = {"the", "and", "for", "with", "this", "that", "from", "when", "your", "into", "over"}
    useful_words = [w for w in words if w not in stop_words]
    tokens.extend(useful_words[:5])
    # deduplicate preserving order
    seen = set()
    deduped = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return ", ".join(deduped[:6])


def sync_skillbank_index(
    skills_dir: Path,
    skillbank_index_path: Path,
) -> int:
    """Rebuilds or updates skillbank INDEX.md with all skills found in skills_dir."""
    skills_dir = Path(os.path.expanduser(str(skills_dir)))
    skillbank_index_path = Path(os.path.expanduser(str(skillbank_index_path)))
    skillbank_index_path.parent.mkdir(parents=True, exist_ok=True)

    scan_dirs = [skills_dir]
    cfg_skills = Path(os.path.expanduser("~/.gemini/config/skills"))
    if cfg_skills.is_dir() and cfg_skills not in scan_dirs:
        scan_dirs.append(cfg_skills)

    skill_entries: list[tuple[str, Path, str]] = []
    seen_skills: set[str] = set()
    for sd in scan_dirs:
        if not sd.is_dir():
            continue
        for d in sorted(sd.iterdir()):
            if d.is_dir() and (d / "SKILL.md").is_file() and d.name not in seen_skills:
                seen_skills.add(d.name)
                home_p = Path.home()
                if str(d).startswith(str(home_p)):
                    rel_p = "~/" + str(d.relative_to(home_p))
                else:
                    rel_p = str(d)
                skill_entries.append((d.name, d / "SKILL.md", f"{rel_p}/SKILL.md"))

    skill_entries.sort(key=lambda x: x[0])

    lines = [
        "# Antigravity SkillBank & Cue Index",
        "",
        "> Master cue-indexed registry mapping prompt tokens, roles, and workflows to specialist skills.",
        f"> Generated / verified by `validate-harness-tree.py` across {len(skill_entries)} skills.",
        "",
        "## Indexed Skills & Trigger Cues",
        "",
    ]

    for name, skill_file, display_path in skill_entries:
        s_name, desc = _extract_skill_frontmatter(skill_file)
        cues = _generate_skill_cues(s_name, desc)
        lines.append(f"### `{s_name}`")
        lines.append(f"- **Path**: `{display_path}`")
        lines.append(f"- **Cues**: {cues}")
        if desc:
            lines.append(f"- **Description**: {desc}")
        lines.append("")

    skillbank_index_path.write_text("\n".join(lines), encoding="utf-8")
    return len(skill_entries)


def check_skill_trigger_coverage(
    skills_dir: str | Path,
    gemini_path: str | Path,
    pre_inv_path: str | Path,
    skillbank_index_path: str | Path,
    autotrigger: bool = False,
) -> tuple[bool, str, dict]:
    """Check 2: Verifies all skills in skills_dir and ~/.gemini/config/skills are referenced in GEMINI.md, pre_invocation_hook.py, or INDEX.md."""
    s_dir = Path(os.path.expanduser(str(skills_dir)))
    scan_dirs = [s_dir]
    repo_cfg_skills = s_dir.parent.parent / "config" / "skills"
    if repo_cfg_skills.is_dir() and repo_cfg_skills not in scan_dirs:
        scan_dirs.append(repo_cfg_skills)
    cfg_skills = Path(os.path.expanduser("~/.gemini/config/skills"))
    if cfg_skills.is_dir() and cfg_skills not in scan_dirs:
        scan_dirs.append(cfg_skills)

    all_skills_set = set()
    for sd in scan_dirs:
        if sd.is_dir():
            for d in sd.iterdir():
                if d.is_dir() and (d / "SKILL.md").is_file():
                    all_skills_set.add(d.name)

    all_skills = sorted(list(all_skills_set))

    if not all_skills:
        return False, f"No skills found in {scan_dirs}", {}

    gemini_p = _resolve_gemini_target(gemini_path)
    gemini_text = gemini_p.read_text(encoding="utf-8") if gemini_p.is_file() else ""

    pre_inv_p = Path(os.path.expanduser(str(pre_inv_path)))
    pre_inv_text = pre_inv_p.read_text(encoding="utf-8") if pre_inv_p.is_file() else ""

    index_p = Path(os.path.expanduser(str(skillbank_index_path)))

    # If autotrigger is requested or index file is missing/incomplete, sync INDEX.md
    if autotrigger:
        sync_skillbank_index(s_dir, index_p)

    index_text = index_p.read_text(encoding="utf-8") if index_p.is_file() else ""

    covered: list[str] = []
    uncovered: list[str] = []

    for skill in all_skills:
        in_gemini = skill in gemini_text
        in_pre_inv = skill in pre_inv_text
        in_index = skill in index_text

        if in_gemini or in_pre_inv or in_index:
            covered.append(skill)
        elif autotrigger:
            # Under autotrigger, all skills in skills_dir with SKILL.md are covered
            covered.append(skill)
        else:
            uncovered.append(skill)

    details = {
        "total_skills": len(all_skills),
        "covered_count": len(covered),
        "uncovered_count": len(uncovered),
        "covered": covered,
        "uncovered": uncovered,
        "index_exists": index_p.is_file(),
    }

    overlap_ok, overlap_msg, overlap_details = check_skill_lexical_overlap(s_dir)
    details["lexical_overlap"] = overlap_details

    if uncovered:
        return (
            False,
            f"Skill Trigger & Index Coverage: {len(uncovered)}/{len(all_skills)} skill(s) lack triggers or index entries (run with --autotrigger to fix): {uncovered}",
            details,
        )

    if not overlap_ok:
        return (
            False,
            f"Skill Trigger & Index Coverage FAILED ({overlap_msg})",
            details,
        )

    top_rival = overlap_details.get("top_rivals", [{}])[0] if overlap_details.get("top_rivals") else {}
    rival_suffix = (
        f" | reach.overlap max={top_rival.get('similarity', 0.0):.2f} ({top_rival.get('pair', 'n/a')})"
        if top_rival else ""
    )

    return (
        True,
        f"Skill Trigger & Index Coverage OK: {len(covered)}/{len(all_skills)} skills referenced across GEMINI.md, pre_invocation_hook.py, and skillbank/INDEX.md{rival_suffix}",
        details,
    )


def check_skill_lexical_overlap(
    skills_dir: str | Path = "~/.gemini/antigravity/skills",
    max_similarity: float = 0.90,
    include_host_config_skills: bool = True,
) -> tuple[bool, str, dict]:
    """google/skill-reach (reach.overlap): Computes BM25/cosine & Jaccard lexical overlap across skill descriptions + cues."""
    s_dir = Path(os.path.expanduser(str(skills_dir)))
    scan_dirs = [s_dir]
    repo_cfg_skills = s_dir.parent.parent / "config" / "skills"
    if repo_cfg_skills.is_dir() and repo_cfg_skills not in scan_dirs:
        scan_dirs.append(repo_cfg_skills)
    if include_host_config_skills:
        cfg_skills = Path(os.path.expanduser("~/.gemini/config/skills"))
        if cfg_skills.is_dir() and cfg_skills not in scan_dirs:
            scan_dirs.append(cfg_skills)

    stop_words = {
        "the", "and", "for", "with", "this", "that", "from", "when", "your",
        "into", "over", "are", "use", "using", "across", "before", "after",
    }

    skill_docs: dict[str, dict] = {}
    empty_descriptions: list[str] = []

    for sd in scan_dirs:
        if not sd.is_dir():
            continue
        for d in sorted(sd.iterdir()):
            skill_md = d / "SKILL.md"
            if d.is_dir() and skill_md.is_file() and d.name not in skill_docs:
                _, desc = _extract_skill_frontmatter(skill_md)
                desc_clean = desc.strip()
                if not desc_clean:
                    empty_descriptions.append(d.name)
                cues = _generate_skill_cues(d.name, desc_clean)
                combined_text = f"{desc_clean} {cues}".lower()
                raw_tokens = re.findall(r"\b[a-z0-9_]{2,}\b", combined_text)
                tokens = [t for t in raw_tokens if t not in stop_words and t != d.name.lower().replace("-", "_")]
                if not tokens:
                    tokens = raw_tokens or [d.name.lower()]
                tf: dict[str, int] = {}
                for t in tokens:
                    tf[t] = tf.get(t, 0) + 1
                skill_docs[d.name] = {
                    "description": desc_clean,
                    "tokens": tokens,
                    "token_set": set(tokens),
                    "tf": tf,
                }

    n_docs = len(skill_docs)
    if n_docs == 0:
        return False, f"No skills found in {scan_dirs}", {"total_skills": 0}

    # Compute BM25 IDF weights across the skill corpus
    df: dict[str, int] = {}
    total_len = 0
    for doc in skill_docs.values():
        total_len += len(doc["tokens"])
        for term in doc["token_set"]:
            df[term] = df.get(term, 0) + 1
    avgdl = max(total_len / n_docs, 1.0)
    k1 = 1.5
    b = 0.75

    bm25_vecs: dict[str, dict[str, float]] = {}
    for name, doc in skill_docs.items():
        vec: dict[str, float] = {}
        dl = len(doc["tokens"])
        for term, freq in doc["tf"].items():
            idf = math.log(1.0 + (n_docs - df[term] + 0.5) / (df[term] + 0.5))
            weight = idf * ((freq * (k1 + 1.0)) / (freq + k1 * (1.0 - b + b * (dl / avgdl))))
            vec[term] = weight
        bm25_vecs[name] = vec

    def _cosine(v1: dict[str, float], v2: dict[str, float]) -> float:
        dot = sum(w * v2.get(t, 0.0) for t, w in v1.items())
        n1 = math.sqrt(sum(w * w for w in v1.values()))
        n2 = math.sqrt(sum(w * w for w in v2.values()))
        if n1 == 0.0 or n2 == 0.0:
            return 0.0
        return dot / (n1 * n2)

    rivals: list[dict] = []
    collisions: list[dict] = []
    skill_names = sorted(skill_docs.keys())

    for i in range(len(skill_names)):
        for j in range(i + 1, len(skill_names)):
            s1, s2 = skill_names[i], skill_names[j]
            d1, d2 = skill_docs[s1], skill_docs[s2]
            union_sz = len(d1["token_set"] | d2["token_set"])
            jaccard = (len(d1["token_set"] & d2["token_set"]) / union_sz) if union_sz else 0.0
            bm25_cos = _cosine(bm25_vecs[s1], bm25_vecs[s2])
            exact_dup = (
                bool(d1["description"])
                and d1["description"].casefold() == d2["description"].casefold()
            )
            sim = 1.0 if exact_dup else round(max(jaccard, bm25_cos), 4)
            entry = {
                "pair": f"{s1} <-> {s2}",
                "skill_a": s1,
                "skill_b": s2,
                "similarity": sim,
                "jaccard": round(jaccard, 4),
                "bm25_cosine": round(bm25_cos, 4),
            }
            rivals.append(entry)
            if sim >= max_similarity:
                collisions.append(entry)

    rivals.sort(key=lambda x: (-x["similarity"], x["pair"]))
    top_rivals = rivals[:5]
    details = {
        "total_skills": n_docs,
        "empty_descriptions": empty_descriptions,
        "collisions": collisions,
        "top_rivals": top_rivals,
        "max_similarity_ceiling": max_similarity,
    }

    if empty_descriptions:
        return (
            False,
            f"Skill Lexical Overlap (reach.overlap): {len(empty_descriptions)} skill(s) have empty descriptions: {empty_descriptions}",
            details,
        )
    if collisions:
        col_str = ", ".join(f"{c['pair']} ({c['similarity']:.2f})" for c in collisions)
        return (
            False,
            f"Skill Lexical Overlap (reach.overlap): {len(collisions)} near-identical skill pair(s) >= {max_similarity}: {col_str}",
            details,
        )

    max_sim = top_rivals[0]["similarity"] if top_rivals else 0.0
    return (
        True,
        f"Skill Lexical Overlap OK (reach.overlap): {n_docs} distinct skills verified (max rival similarity = {max_sim:.2f} < {max_similarity:.2f})",
        details,
    )



def _is_binary_file(file_path: Path) -> bool:
    """Returns True if the file appears to be a non-text binary."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
        if not chunk:
            return False
        return chunk.startswith(b"\x7fELF") or b"\x00" in chunk
    except Exception:
        return False


def _detect_script_type(file_path: Path) -> str:
    """Detects whether a file is a 'python', 'shell', or 'other' script."""
    if file_path.suffix == ".py":
        return "python"
    if file_path.suffix == ".sh":
        return "shell"

    try:
        with open(file_path, "rb") as f:
            first_line = f.readline().lower().strip()
    except Exception:
        return "other"

    if first_line.startswith(b"#!"):
        if b"python" in first_line:
            return "python"
        if any(sh in first_line for sh in (b"bash", b"/sh", b" sh", b"zsh")):
            return "shell"

    return "other"


def extract_script_paths(
    hooks_json_path: str | Path,
    gemini_path: str | Path,
    scripts_dir: str | Path = "~/.gemini/antigravity/scripts",
) -> list[str]:
    """Extracts all script paths (.py, .sh) referenced in hooks.json, GEMINI.md, and inside scripts_dir."""
    found_paths: set[str] = set()
    script_pattern = re.compile(r'((?:~|/home/[^/\s"\',;:`()]+)/\.gemini[^\s"\',;:`()]+\.(?:py|sh))')

    # 1. hooks.json
    h_p = Path(os.path.expanduser(str(hooks_json_path)))
    if h_p.is_file():
        try:
            raw_text = h_p.read_text(encoding="utf-8")
            for m in script_pattern.finditer(raw_text):
                candidate = os.path.expanduser(m.group(1))
                if "/brain/" not in candidate:
                    found_paths.add(candidate)
        except Exception:
            pass

    # 2. GEMINI.md
    g_p = _resolve_gemini_target(gemini_path)
    if g_p.is_file():
        try:
            raw_text = g_p.read_text(encoding="utf-8")
            for m in script_pattern.finditer(raw_text):
                candidate = os.path.expanduser(m.group(1))
                if "/brain/" not in candidate:
                    found_paths.add(candidate)
        except Exception:
            pass

    # 3. scripts_dir
    s_p = Path(os.path.expanduser(str(scripts_dir)))
    if s_p.is_dir():
        for script_file in s_p.iterdir():
            if script_file.is_file() and script_file.suffix in (".py", ".sh"):
                candidate = str(script_file.resolve())
                if "/brain/" not in candidate:
                    found_paths.add(candidate)

    # 4. TUI core scripts, utilities and library (explicit allowlist of harness utilities and lib/agy_tui_core.py)
    harness_bin_utilities = (
        "agy-axi",
        "agy-sidebar",
        "agy-squad",
        "agy-statusline",
        "clipboard-toast",
        "clipboard-toast-daemon",
        "ensure-verification-gates",
        "kate-md-preview",
        "mermaid-ascii",
    )
    repo_root = Path(__file__).resolve().parent.parent.parent
    bin_dir = repo_root / "bin"
    if bin_dir.is_dir():
        for util_name in harness_bin_utilities:
            b = bin_dir / util_name
            found_paths.add(str(b.resolve() if b.is_file() else b))
    else:
        local_bin = Path(os.path.expanduser("~/.local/bin"))
        for util_name in harness_bin_utilities:
            b = local_bin / util_name
            found_paths.add(str(b.resolve() if b.is_file() else b))

    tui_lib = repo_root / "lib" / "agy_tui_core.py"
    if tui_lib.is_file():
        found_paths.add(str(tui_lib.resolve()))
    else:
        local_lib = Path(os.path.expanduser("~/.local/lib/agy_tui_core.py"))
        found_paths.add(str(local_lib.resolve() if local_lib.is_file() else local_lib))

    return sorted(p for p in found_paths if "/brain/" not in p)


def check_scripts_exist_and_compile(
    hooks_json_path: str | Path,
    gemini_path: str | Path,
    scripts_dir: str | Path = "~/.gemini/antigravity/scripts",
) -> tuple[bool, str, list[dict]]:
    """Check 4: Verifies all ~/.gemini/.../*.py and *.sh paths in hooks.json, GEMINI.md, and scripts_dir exist and compile."""
    script_paths = extract_script_paths(hooks_json_path, gemini_path, scripts_dir=scripts_dir)
    if not script_paths:
        return True, "Script Existence & Compile Check: 0 scripts referenced", []

    results: list[dict] = []
    has_failure = False

    for script_p in script_paths:
        p = Path(script_p)
        entry: dict = {"path": script_p, "exists": p.is_file(), "compiles": False, "error": None}

        if not p.is_file():
            entry["error"] = "File not found on disk"
            has_failure = True
            results.append(entry)
            continue

        if _is_binary_file(p):
            entry["compiles"] = True
            entry["note"] = "non-text binary skipped"
            results.append(entry)
            continue

        stype = _detect_script_type(p)
        if stype == "python":
            try:
                py_compile.compile(str(p), doraise=True)
                entry["compiles"] = True
            except py_compile.PyCompileError as exc:
                entry["error"] = str(exc)
                has_failure = True
            except Exception as exc:
                entry["error"] = f"Unexpected compile error: {exc}"
                has_failure = True

        elif stype == "shell":
            try:
                proc = subprocess.run(["bash", "-n", str(p)], capture_output=True, text=True, timeout=10.0)
                if proc.returncode == 0:
                    entry["compiles"] = True
                else:
                    entry["error"] = proc.stderr.strip() or f"bash -n failed with code {proc.returncode}"
                    has_failure = True
            except subprocess.TimeoutExpired:
                entry["error"] = "bash -n timed out after 10.0s"
                has_failure = True
            except Exception as exc:
                entry["error"] = f"Unexpected execution error: {exc}"
                has_failure = True
        else:
            # Non-python/shell text file skipped gracefully rather than failing
            entry["compiles"] = True
            entry["note"] = "non-script text file skipped"

        results.append(entry)

    if has_failure:
        failed_count = sum(1 for r in results if not r["exists"] or not r["compiles"])
        return (
            False,
            f"Script Existence & Compile Check: {failed_count}/{len(results)} script(s) failed existence or compile check",
            results,
        )

    return (
        True,
        f"Script Existence & Compile Check OK: All {len(results)} script(s) exist and compile cleanly",
        results,
    )


def check_security_guardrail_integrity(
    hooks_dir: str | Path = "~/.gemini/config/hooks",
    gemini_path: str | Path = "~/.gemini/GEMINI.md",
) -> tuple[bool, str, float]:
    """Check 5 (CP-2): Verifies critical security and safety invariants exist."""
    h_dir = Path(os.path.expanduser(str(hooks_dir)))
    hook_file = h_dir / "pre_tool_use_hook.py"
    if not hook_file.is_file():
        # Fallback to repo config/hooks/pre_tool_use_hook.py
        repo_hook = Path(__file__).resolve().parent.parent.parent / "config" / "hooks" / "pre_tool_use_hook.py"
        if repo_hook.is_file():
            hook_file = repo_hook
        else:
            local_hook = Path("config/hooks/pre_tool_use_hook.py").resolve()
            if local_hook.is_file():
                hook_file = local_hook

    hook_content = ""
    if hook_file.is_file():
        try:
            hook_content = hook_file.read_text(encoding="utf-8")
        except Exception:
            hook_content = ""

    gemini_file = _resolve_gemini_target(gemini_path)
    gemini_content = ""
    if gemini_file.is_file():
        try:
            gemini_content = gemini_file.read_text(encoding="utf-8")
        except Exception:
            gemini_content = ""

    combined = hook_content + "\n" + gemini_content

    # Invariant 1: Vendor directory block (CK-01 / node_modules)
    inv1 = ("CK-01" in combined) or ("node_modules" in combined)
    # Invariant 2: Secret/privacy block (concrete definition like PRIVACY_BLOCKED_EXACT_BASENAMES or _is_privacy_blocked)
    inv2 = bool(
        re.search(r"(?:PRIVACY_BLOCKED_EXACT_BASENAMES|_is_privacy_blocked\s*\(|CK-02|re\.compile\(.*?secret.*?\))", hook_content, re.IGNORECASE)
        or ("PRIVATE KEY" in combined)
    )
    # Invariant 3: Story Shard / Role Lease enforcement (allowed_files or Story Shard)
    inv3 = ("allowed_files" in combined) or ("Story Shard" in combined)
    # Invariant 4: Pre-write in-memory AST/Syntax gate (actual ast.parse( call outside comments)
    inv4 = False
    for line in hook_content.splitlines():
        line_clean = line.strip()
        if not line_clean.startswith("#") and "ast.parse(" in line:
            inv4 = True
            break
    # Invariant 5: Destructive command guard (rm -rf or git reset --hard)
    inv5 = ("rm -rf" in combined) or ("git reset --hard" in combined)

    passed_count = sum([1 for inv in (inv1, inv2, inv3, inv4, inv5) if inv])
    sec_score = round(passed_count / 5.0, 4)
    ok = (sec_score >= 1.0)

    if ok:
        msg = f"Security Guardrail Integrity OK: 5/5 critical invariants verified (sec_score = {sec_score:.2f})"
    else:
        missing = []
        if not inv1:
            missing.append("vendor_directory_block")
        if not inv2:
            missing.append("secret_privacy_block")
        if not inv3:
            missing.append("story_shard_lease")
        if not inv4:
            missing.append("ast_syntax_gate")
        if not inv5:
            missing.append("destructive_command_guard")
        msg = f"Security Guardrail Integrity FAILED: {passed_count}/5 invariants verified (sec_score = {sec_score:.2f}, missing: {', '.join(missing)})"

    return ok, msg, sec_score


def run_all_checks(
    gemini_path: str = "~/.gemini/GEMINI.md",
    skills_dir: str = "~/.gemini/antigravity/skills",
    hooks_json_path: str = "~/.gemini/config/hooks.json",
    pre_inv_path: str = "~/.gemini/config/hooks/pre_invocation_hook.py",
    skillbank_index_path: str = "~/.gemini/antigravity/skillbank/INDEX.md",
    scripts_dir: str = "~/.gemini/antigravity/scripts",
    hooks_dir: str = "~/.gemini/config/hooks",
    max_chars: int = 12000,
    autotrigger: bool = False,
) -> dict:
    """Executes all 5 mechanical harness tree checks."""
    c1_ok, c1_msg, c1_count = check_always_on_byte_budget(gemini_path, max_chars)
    c2_ok, c2_msg, c2_details = check_skill_trigger_coverage(
        skills_dir, gemini_path, pre_inv_path, skillbank_index_path, autotrigger=autotrigger
    )
    c3_ok, c3_msg, c3_violations = check_template_braces(gemini_path)
    c4_ok, c4_msg, c4_results = check_scripts_exist_and_compile(
        hooks_json_path, gemini_path, scripts_dir=scripts_dir
    )
    c5_ok, c5_msg, c5_sec_score = check_security_guardrail_integrity(
        hooks_dir=hooks_dir, gemini_path=gemini_path
    )

    all_passed = c1_ok and c2_ok and c3_ok and c4_ok and c5_ok
    return {
        "success": all_passed,
        "checks": {
            "check1_byte_budget": {"passed": c1_ok, "message": c1_msg, "char_count": c1_count, "limit": max_chars},
            "check2_skill_coverage": {"passed": c2_ok, "message": c2_msg, "details": c2_details},
            "check3_template_braces": {"passed": c3_ok, "message": c3_msg, "violations": c3_violations},
            "check4_script_compiles": {"passed": c4_ok, "message": c4_msg, "results": c4_results},
            "check5_security_guardrails": {"passed": c5_ok, "message": c5_msg, "sec_score": c5_sec_score},
        },
    }


def _run_self_tests() -> int:
    """Runs internal self tests."""
    print("Running validate-harness-tree self-tests...")

    # Test 1: Byte Budget
    import tempfile
    with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
        tf.write("a" * 100)
        tf_name = tf.name
    try:
        ok, msg, c = check_always_on_byte_budget(tf_name, max_chars=150)
        assert ok, "Should pass when within budget"
        ok, msg, c = check_always_on_byte_budget(tf_name, max_chars=50)
        assert not ok, "Should fail when budget exceeded"
    finally:
        os.unlink(tf_name)

    # Test 2: Template Braces
    sample_md = (
        "# Title\n"
        "Here is {{ unescaped }} template\n"
        "```jinja\n"
        "Here is {{ inside_code_block }} ignored\n"
        "```\n"
        "Here is \\{{ escaped \\}} token\n"
        "Another {% if block %} token\n"
    )
    violations = extract_template_brace_violations(sample_md)
    lines_flagged = [v["line"] for v in violations]
    assert 2 in lines_flagged, f"Line 2 should be flagged, got {lines_flagged}"
    assert 4 not in lines_flagged, f"Line 4 (inside code block) should not be flagged, got {lines_flagged}"
    assert 6 not in lines_flagged, f"Line 6 (escaped) should not be flagged, got {lines_flagged}"
    assert 7 in lines_flagged, f"Line 7 should be flagged, got {lines_flagged}"

    # Test 3: Security Guardrail Integrity (CP-2)
    with tempfile.TemporaryDirectory() as td:
        hook_p = Path(td) / "pre_tool_use_hook.py"
        # Incomplete hook
        hook_p.write_text("def hook(): pass\n", encoding="utf-8")
        ok, msg, score = check_security_guardrail_integrity(hooks_dir=td, gemini_path=td)
        assert not ok, "Incomplete hook must fail security integrity check"
        assert score < 1.0, f"Score should be < 1.0, got {score}"

        # Complete hook satisfying all 5 invariants
        complete_content = (
            "# CK-01 node_modules vendor guard\n"
            "# CK-02 PRIVATE KEY API_KEY secret privacy block\n"
            "# Story Shard allowed_files lease guard\n"
            "ast.parse(code)\n"
            "# destructive guard: rm -rf and git reset --hard\n"
        )
        hook_p.write_text(complete_content, encoding="utf-8")
        ok, msg, score = check_security_guardrail_integrity(hooks_dir=td, gemini_path=td)
        assert ok, f"Complete hook must pass security integrity check: {msg}"
        assert score == 1.0, f"Score should be 1.0, got {score}"

    # Test 4: Binary File Detection & Text Script Type Identification
    with tempfile.TemporaryDirectory() as td:
        py_f = Path(td) / "test_script.py"
        py_f.write_text("print('test')\n", encoding="utf-8")
        sh_f = Path(td) / "test_script.sh"
        sh_f.write_text("#!/bin/bash\necho test\n", encoding="utf-8")
        bin_f = Path(td) / "test_bin"
        bin_f.write_bytes(b"\x7fELF\x00\x01\x02\x03\x04")

        assert _is_binary_file(bin_f), "Must identify ELF binary"
        assert not _is_binary_file(py_f), "Must not identify python as binary"
        assert not _is_binary_file(sh_f), "Must not identify shell script as binary"

        assert _detect_script_type(py_f) == "python", "Must detect python script"
        assert _detect_script_type(sh_f) == "shell", "Must detect shell script"
        assert _detect_script_type(bin_f) == "other", "Must classify binary as other"

    # Test 5: Skill Lexical Overlap (google/skill-reach reach.overlap)
    with tempfile.TemporaryDirectory() as td:
        s1_dir = Path(td) / "skill-alpha"
        s2_dir = Path(td) / "skill-beta"
        s1_dir.mkdir()
        s2_dir.mkdir()
        (s1_dir / "SKILL.md").write_text("---\nname: skill-alpha\ndescription: Spring physics and animation curves for UI components.\n---\n", encoding="utf-8")
        (s2_dir / "SKILL.md").write_text("---\nname: skill-beta\ndescription: Database schema migrations and SQL query indexing.\n---\n", encoding="utf-8")
        ok, msg, details = check_skill_lexical_overlap(td, include_host_config_skills=False)
        assert ok, f"Distinct skills should pass lexical overlap: {msg}"

        (s2_dir / "SKILL.md").write_text("---\nname: skill-beta\ndescription: Spring physics and animation curves for UI components.\n---\n", encoding="utf-8")
        ok, msg, details = check_skill_lexical_overlap(td, include_host_config_skills=False)
        assert not ok, "Near-identical skill descriptions must fail lexical overlap"
        assert len(details["collisions"]) == 1, "Should record 1 collision"

    # Test 6: Active Rules Byte Budget & Fallback Resolution
    with tempfile.TemporaryDirectory() as td:
        td_root = Path(td)
        g_file = td_root / "GLOBAL_AGENTS.md"
        g_file.write_text("x" * 1000, encoding="utf-8")
        (td_root / "AGENTS.md").write_text("y" * 500, encoding="utf-8")
        # Disabled plugin rules and builtin rules must be ignored
        disabled_rules = td_root / "config" / "plugins" / "disabled-p" / "rules"
        disabled_rules.mkdir(parents=True)
        (disabled_rules / "big.md").write_text("z" * 30000, encoding="utf-8")
        builtin_rules = td_root / "antigravity-cli" / "builtin" / "rules"
        builtin_rules.mkdir(parents=True)
        (builtin_rules / "huge.md").write_text("w" * 30000, encoding="utf-8")
        ok, msg, r_details = check_active_rules_byte_budget(g_file, repo_root=td_root)
        assert ok, f"Active rules budget should pass when disabled/builtin excluded: {msg}"
        assert r_details["aggregate_bytes"] == 1500, f"Expected 1500B, got {r_details['aggregate_bytes']}"

        # Oversized single rule file (>= 24,000 bytes) must fail
        g_file.write_text("x" * 24000, encoding="utf-8")
        ok, msg, _ = check_active_rules_byte_budget(g_file, repo_root=td_root)
        assert not ok, "Single rule file >= 24000 bytes must fail"

    print("Self-test passed successfully!")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mechanical Harness Tree Validator (Harness² Protocol)"
    )
    parser.add_argument("--max-chars", type=int, default=12000, help="Always-on byte budget ceiling (default 12000)")
    parser.add_argument("--autotrigger", action="store_true", help="Sync skills into skillbank INDEX.md and cover unreferenced skills")
    parser.add_argument("--gemini-path", default="~/.gemini/GEMINI.md", help="Path to GEMINI.md")
    parser.add_argument("--skills-dir", default="~/.gemini/antigravity/skills", help="Path to skills directory")
    parser.add_argument("--hooks-json", default="~/.gemini/config/hooks.json", help="Path to hooks.json")
    parser.add_argument("--pre-invocation-hook", default="~/.gemini/config/hooks/pre_invocation_hook.py", help="Path to pre_invocation_hook.py")
    parser.add_argument("--skillbank-index", default="~/.gemini/antigravity/skillbank/INDEX.md", help="Path to skillbank INDEX.md")
    parser.add_argument("--scripts-dir", default="~/.gemini/antigravity/scripts", help="Path to scripts directory")
    parser.add_argument("--hooks-dir", default="~/.gemini/config/hooks", help="Path to hooks directory")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--self-test", action="store_true", help="Run self-tests and exit")

    args = parser.parse_args()

    if args.self_test:
        return _run_self_tests()

    report = run_all_checks(
        gemini_path=args.gemini_path,
        skills_dir=args.skills_dir,
        hooks_json_path=args.hooks_json,
        pre_inv_path=args.pre_invocation_hook,
        skillbank_index_path=args.skillbank_index,
        scripts_dir=args.scripts_dir,
        hooks_dir=args.hooks_dir,
        max_chars=args.max_chars,
        autotrigger=args.autotrigger,
    )

    if args.json:
        print(json.dumps(report, indent=2))
        return 0 if report["success"] else 1

    print("=" * 64)
    print("Antigravity Harness Tree Validator (Harness² Protocol)")
    print("=" * 64)

    for k, v in report["checks"].items():
        tag = "[PASS]" if v["passed"] else "[FAIL]"
        print(f"{tag} {v['message']}")

    print("-" * 64)
    if report["success"]:
        print("ALL HARNESS TREE CHECKS PASSED.")
        return 0
    else:
        print("HARNESS TREE VALIDATION FAILED.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

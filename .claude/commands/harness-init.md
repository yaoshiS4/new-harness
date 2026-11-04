---
description: Bootstrap the harness in a product repository - verify the toolchain and MCP servers, create docs/STATUS.md and the project guardrails policy, register and index the project in codex_knowledge and codegraph, and run a first grounding check. Run once before the first task in a new project.
argument-hint: [project-slug]
---

# /harness-init

Slug: $ARGUMENTS (default: the repository directory name).

Run these steps in order; each ends with `[Step N of 6 Done: ...] -> Next: ...`.

1. **Toolchain check**: `command -v python3 rg fd jq uv node npx git` and `python3 --version`; report what is missing (the Bash guard only enforces `rg`/`fd` when present). Confirm the hooks are active: `/harness-status`.
2. **Project policy**: if `.claude/harness/guardrails.json` is absent, create it with the defaults and `root_may_edit_code: false` (set it to `true` only if this repository's root thread is meant to build directly). Add `.claude/settings.local.json` and `.claude/harness/*.sqlite*` to `.gitignore` if missing.
3. **SOT docs**: create `docs/STATUS.md` if absent with sections `## Current State`, `## In Progress`, `## Next Actions`, `## Verification`, `## Risks`; ensure `CLAUDE.md` (or `AGENTS.md`) states the build/test commands and the verification command the harness should treat as authoritative. Optionally add project-specific verification runners to `guardrails.json` as `verification_patterns: ["<regex>"]`.
4. **Knowledge registration**: `mcp__codex_knowledge__project_register(project_path=<abs path>, slug=<slug>)`, then `mcp__codex_knowledge__project_index(slug)`; `mcp__codegraph__repo_map(root=<abs path>, max_tokens=1500)` to build the symbol index. If the MCP servers are not reachable, run `bash scripts/install-claude-harness.sh` from the harness repo (or `claude mcp add-json -s user ...` from `~/.claude/harness/mcp.user.json`) and retry.
5. **Verification gates (optional)**: for Path 2/3 projects, ask the user before scaffolding `scripts/verification/` via `python3 ${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/ensure-verification-gates.py .`; note that the generated `verify-oracle.sh` still targets the legacy CLI, so `/oracle-review` is the supported Oracle path.
6. **First grounding check**: `mcp__codex_knowledge__project_context(slug, "<one-line project summary>")` and `mcp__codegraph__symbol_lookup(root, "<main entry symbol>")`; store the project summary with `mcp__codex_knowledge__memory_store(slug, "project_summary", "<summary>")`. Report readiness: GO / CONDITIONAL (list gaps) / NO-GO.

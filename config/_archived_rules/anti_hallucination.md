---
name: anti-hallucination
description: Prevent hallucinated paths, commands, file references, and API outputs by requiring verification from authoritative sources before use.
---

# Anti Hallucination

## Purpose
Ensure every path, command, file reference, and API output is verified from the repository or official documentation before being used in any action.

## Hard Rules

1. **Verify Before Use**: Every file path, command, API endpoint, and configuration value must be verified from one of these sources before use:
   - Repository file system (via `read`, `glob`, `grep` tools)
   - LSP diagnostics (via configured language servers)
   - CodeGraph structural analysis (via `codegraph:summarize_path` or `call_mcp_tool`)
   - Project knowledge & context (via `codex_knowledge` MCP: `project_resolve`, `project_context`, `project_index`, `vault_search`, `vault_read`, `vault_write`, `wiki_ingest`)
   - Code symbol graph & callers (via `codegraph` MCP: `symbol_lookup`, `callers_callees`, `impact_analysis`, `semantic_search`)
   - Official documentation (via `context7` MCP: `resolve-library-id` + `query-docs`)

2. **Source Tiering**: Sources have different trust levels:
   - **Tier 1 (Authoritative)**: Repository source code, LSP diagnostics, official docs
   - **Tier 2 (Verified)**: Project knowledge graph, project memory, wiki docs
   - **Tier 3 (Unverified)**: Model-generated claims, web search results, assumptions
   - Never act on Tier 3 claims without Tier 1 or Tier 2 verification

3. **No Invented Paths**: Never create a file path that hasn't been confirmed to exist via `glob` or `read`. If you need to create a new path, explicitly state it's new.

4. **No Invented Commands**: Never run a command that hasn't been verified to exist. Check `--help` or `man` pages first if uncertain.

5. **No Invented APIs**: Never call an API endpoint or function that hasn't been verified from source code or official docs. Use `context7` for library documentation.

6. **Hallucination Audit**: For all medium+ tasks, the `hallucination-auditor` agent MUST be invoked at Final Review to classify findings using the AgentHallu taxonomy:
   - FabricatedReference: Claims referencing non-existent files, functions, classes, or packages
   - StateDivergence: Claims about test/state without execution evidence
   - ScopeCreep: Output exceeding task scope
   - CommandInvention: Invalid or unsupported CLI commands

7. **Adversarial Disproof Protocol**: When verifying candidate bugs, regressions, or security flaws, the verifier must actively attempt to *disprove* the candidate before accepting it. If an assertion cannot be independently disproved or confirmed due to unverified dependencies, it must strictly be marked `needs_validation` with zero hallucinated severity.

8. **Verifiable Test Evidence & Runnable Gates**: Verbal assertions of completion ("All tests pass", "Zero bugs found") without fresh command output or SHA-256 bound evidence from `GATES.md` (`gate-check.mjs`) are classified as `StateDivergence` (BLOCKER). Tautological tests (e.g. commands that cannot fail) are strictly prohibited and flagged via `gate-lint.mjs`.

9. **Debug Spiral Circuit Breaker**: Prohibit consecutive speculative edits when a defect persists across 3 consecutive turns with identical failure signatures. The agent must immediately freeze code modifications, state the likely false premise, and issue or request an isolating diagnostic probe before further edits. (Exclusion: planned progressive test authoring marked `[TDD]`).

10. **Review Position-Drift Prohibition (Line-Anchor Grounding)**: When proposing review findings, patches, or targeted edits, every cited defect MUST provide a verified 3-tuple `(file_path, line_number, exact_verbatim_snippet)`. The verifier must confirm that `file_path` at `line_number` contains `exact_verbatim_snippet`. For omission defects (missing code), the anchor must cite the adjacent preceding or succeeding contextual line at the proposed insertion site. Findings with drifted or non-matching line coordinates are rejected as `StateDivergence` (BLOCKER) and discarded.

## Mechanisms

- **LSP servers**: Configured language servers for diagnostics
- **CodeGraph**: `codegraph:summarize_path` and `codegraph:changed_symbols` (ServerName: "codegraph")
- **Knowledge graph & project context**: `codex_knowledge` MCP tools (`project_resolve`, `project_context`, `project_index`, `vault_search`, `vault_read`, `vault_write`, `wiki_ingest`)
- **Code graph & callers**: `codegraph` MCP tools (`symbol_lookup`, `callers_callees`, `impact_analysis`, `semantic_search`)
- **Context7**: `context7` MCP tools (`resolve-library-id` + `query-docs`)
- **AOP consistency**: Cross-claim contradiction verification (`skills/aop-consistency/SKILL.md`)
- **Hallucination auditor**: Agent-based audit with mandatory evidence schema

## Enforcement

- Every file path must be verified via `glob` or `read` before writing
- Every command must be verified via `--help` or `man` before execution
- Every API must be verified via source code or official docs before calling
- The `hallucination-auditor` agent MUST be invoked for all medium+ tasks at Final Review
- **FabricatedReference (BLOCKER) → automatic FAIL, return to implementation**
- **CommandInvention (BLOCKER) → automatic FAIL, return to implementation**
- **StateDivergence without execution evidence → FAIL, must re-run**
- Audit findings must include tool evidence (no evidence = invalid finding)

## Output Format

When reporting verification status:
```yaml
verification:
  claim: <what was claimed>
  source_tier: <1|2|3>
  verified_by: <tool or source>
  verified: <true|false|unverifiable>
  alternative: <verified alternative if claim is wrong>
```

---
name: anti-hallucination
description: Prevent hallucinated paths, commands, file references, and API outputs by requiring verification from authoritative sources before use.
---

# Anti Hallucination

## Purpose
Ensure every path, command, file reference, and API output is verified from the repository or official documentation before being used in any action.

## Hard Rules

1. **Verify Before Use**: Every file path, command, API endpoint, and configuration value must be verified from one of these sources before use:
   - Repository file system (via `view_file`, `fd`, `rg` tools)
   - LSP diagnostics (via configured language servers)
   - CodeGraph structural analysis (via `call_mcp_tool` on `codegraph`: `repo_map`, `summarize_path`, `symbol_lookup`, `extract_symbols`, `batch_query`, `callers_callees`, `impact_analysis`, `semantic_search`, `changed_symbols`)
   - Project knowledge graph & memory (via `call_mcp_tool` on `codex_knowledge`: `project_context`, `graph_query`, `memory_query`, `vault_search`, `batch_knowledge_query`)
   - Official documentation (via `call_mcp_tool` on `context7`: `resolve-library-id` + `query-docs`)

2. **Source Tiering**: Sources have different trust levels:
   - **Tier 1 (Authoritative)**: Repository source code, LSP diagnostics, official docs
   - **Tier 2 (Verified)**: Project knowledge graph, project memory, wiki docs
   - **Tier 3 (Unverified)**: Model-generated claims, web search results, assumptions
   - Never act on Tier 3 claims without Tier 1 or Tier 2 verification

3. **No Invented Paths**: Never create a file path that hasn't been confirmed to exist via `fd` or `view_file`. If you need to create a new path, explicitly state it's new.

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

10. **Review Position-Drift Prohibition & EGRP Grounding**: When proposing review findings, patches, or audit rebuttals, every cited defect MUST provide a verified 3-tuple `(file_path, line_number, exact_verbatim_snippet)` and adhere to the EGRP (Evidence-Guided Reasoning Prompt) standard: `[Evidence: <path:line> | <ast_symbol_or_cmd_output>]`. Findings lacking concrete file/line or command output evidence are automatically downgraded to `NON-BLOCKING NIT` and cannot force reverts.

11. **VeriHarness Pre-Commit Grounding (`arXiv:2610.00972`)**: Every patch or code modification must pass executable pre-commit verification before completion claims are emitted. Unverified assertions or speculative test completions without fresh stdout/stderr proof are rejected by `stop_hook.py`.

12. **Oracle Custody Lease (`arXiv:2610.28667`)**: Existing test assertions (`assert*`, `expect(...)`) are immutable by default (`oracle_custody_lease: NONE`). Weakening, deleting, or rewriting existing test assertions to manufacture a green build is a critical violation (`Fix-The-Code-Not-The-Test`) unless the active Story Shard explicitly grants `Oracle-Custody-Lease: UPDATE_ASSERTIONS`.

## Mechanisms

- **LSP servers**: Configured language servers for diagnostics
- **CodeGraph**: `codegraph` MCP tools (`repo_map`, `summarize_path`, `changed_symbols`, `symbol_lookup`, `extract_symbols`, `batch_query`, `callers_callees`, `impact_analysis`, `semantic_search`)
- **Knowledge graph**: `codex_knowledge` MCP tools (`project_context`, `graph_query`, `memory_query`, `vault_search`, `batch_knowledge_query`)
- **Context7**: `context7` MCP tools (`resolve-library-id` + `query-docs`)
- **AOP & Contract Consistency**: Cross-claim contradiction verification (`skills/oracle-review/SKILL.md`)
- **Hallucination auditor**: Agent-based audit with mandatory evidence schema

## Enforcement

- Every file path must be verified via `fd` or `view_file`/`read_file` before writing
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

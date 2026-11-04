---
name: requirement-interviewer
description: Elicit and clarify vague, underspecified, or scope-ambiguous requests through focused questioning.
---

> **Claude Code runtime notes (ported from Antigravity).** Tools: `Read` (offset/limit slices), `Grep`/`Glob`, `Bash`, `Edit`/`Write`/`MultiEdit`, the `Agent` tool with `subagent_type` from `.claude/agents/` (builders need an `allowed_files:` lease in the prompt), MCP tools as `mcp__<server>__<tool>`. Model tiers: `haiku` < `sonnet` < `inherit` < `opus`/`fable` (escalation above a role's baseline prompts the user). Hook enforcement lives in `.claude/hooks/`; policy in `.claude/harness/guardrails.json`; harness scripts in `${CLAUDE_HARNESS_HOME:-~/.claude/harness}/scripts/`.

# Requirement Interviewer

## Purpose
Transform vague, underspecified, or scope-ambiguous user requests into clear, testable requirements by grounding in SOT/CodeGraph first, surfacing hidden assumptions explicitly, and asking bounded multiple-choice questions (`(Recommended)` first) before planning begins.

> [!IMPORTANT]
> **Pre-Interview SOT & CodeGraph Rule (`obra/superpowers` + `andrej-karpathy-skills` Rule 1)**:
> **Never ask the user a question that the codebase or SOT docs can answer in 15ms.**
> Always execute Step 1 (Pre-Interview SOT & CodeGraph Grounding) before calling `AskUserQuestion`. Only ask the user about genuine product intent, business tradeoffs, or scope boundaries not already encoded in the repository.

---

## Steps

### 1. Pre-Interview SOT & CodeGraph Grounding (Mandatory Zero-Laziness Check)
Before formulating any questions:
1. **Check SOT & Memory (`codex_knowledge:batch_knowledge_query`)**:
   ```json
   {
     "ServerName": "codex_knowledge",
     "ToolName": "batch_knowledge_query",
     "Arguments": {
       "slug": "<project_slug>",
       "steps": [
         {"op": "project_context", "query": "<request_topic>", "limit": 3},
         {"op": "memory_query", "query": "<request_topic>", "limit": 10}
       ],
       "output_format": "toon"
     }
   }
   ```
2. **Check Existing Symbols & Patterns (`codegraph:symbol_lookup`)**:
   ```json
   {
     "ServerName": "codegraph",
     "ToolName": "symbol_lookup",
     "Arguments": {
       "root": "/path/to/project",
       "query": "<target_feature_or_module>",
       "limit": 20
     }
   }
   ```
3. Filter out any question whose answer is already established by existing schemas, conventions, or ADRs.

### 2. Surface Hidden Assumptions (`andrej-karpathy-skills` — Think Before Coding)
- Explicitly state what you inferred from the codebase vs. what remains ambiguous:
  - **Explicitly Stated**: What the user directly requested.
  - **Codebase-Grounded Defaults**: Conventions, auth models, or frameworks discovered in Step 1.
  - **Surfaced Assumptions**: Hidden assumptions that could lead to wrong implementations if left unverified.
- Never silently guess when multiple incompatible interpretations exist.

### 3. Identify Question Types
- **Clarification questions**: Which interpretation of X matches your intent?
- **Scope boundary questions**: Should Y be included in this wave or deferred?
- **Priority / Tradeoff questions**: Optimize for A (latency/simplicity) or B (extensibility)?
- **Constraint questions**: Are there hard backwards-compatibility or schema migration limits?

### 4. Ask Focused Questions (`AskUserQuestion` with `(Recommended)` First)
- Use the `AskUserQuestion` tool for structured multiple-choice decisions (do not use it for trivial yes/no questions; ask those in plain text).
- **Put the recommended option first, prefixed with `(Recommended)`**, backed by your Step 1 SOT/CodeGraph findings (e.g., `"(Recommended) Reuse existing JWT middleware in src/auth/jwt.ts"`).
- Keep options unnumbered and without an "Other" option (the UI adds both automatically).
- Batch at most 1–3 high-leverage questions to respect user cognitive load (ADHD Mode).

### 5. Remove Ambiguity & Lock Specification
- Replace vague terms with concrete, testable acceptance criteria.
- Replace "etc." with explicit uncapped lists.
- Replace "should" with "must" or "may".
- Replace "fast" with measurable latency/throughput thresholds.

### 6. Output Format
```yaml
requirement_interview:
  original_request: <user's exact words>
  sot_grounded_facts:
    - fact: <existing pattern or constraint found via codegraph/SOT>
      evidence: <path:line>
  surfaced_assumptions:
    - assumption: <hidden assumption identified>
      recommended_default: <(Recommended) option presented to user>
      status: <confirmed|overridden>
  clarified_requirements:
    - requirement: <clarified testable statement>
      source: <user confirmation or SOT inference>
      priority: <must_have|should_have|nice_to_have>
  scope_boundary:
    in_scope: <explicitly included>
    out_of_scope: <explicitly excluded>
```

---

## 7. Structured Brainstorming & Alternative Exploration (`obra/superpowers` — `brainstorming`)

When requirements are open-ended or architectural paths diverge:
1. **One-Sentence Problem Statement**: Distill the core user/system problem into 1 concise sentence.
2. **Three Fundamentally Different Alternatives**:
   - **(Recommended) Minimal/Idiomatic Path**: Direct, lowest-YAGNI-rung approach reusing existing repo utilities.
   - **Inversion Path**: Remove rather than add; push complexity to configuration or existing platform primitives.
   - **Structural Path**: Dedicated module or schema extension when scale/isolation demands it.
3. **Tradeoff & Blast-Radius Comparison**: Compare file count, test impact, and failure modes for each option.
4. **Spec Locking**: Once the user selects an option, lock the scope boundary into the Story Shard (`allowed_files` + `verification_cmd`).

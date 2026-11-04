---
name: oracle
description: Autonomous out-of-process Oracle verification gate, adversarial critique, and anti-hallucination protocols.
---

# Oracle Rules

- Oracle is independent.
- Oracle reviews after every major phase.
- **Mandatory Plan Critique & Hardening (Phase 6)**: During Plan Review, Oracle independently critiques the Implementation Plan and Task Breakdown (adversarial scrutiny, edge case coverage, AOP consistency, complexity justification, and test sufficiency).
- **Autonomous Oracle Plan Gate**: In Planning Mode, immediately after creating or modifying `implementation_plan.md`, the agent MUST invoke `bash scripts/verification/verify-oracle.sh --plan` within the same turn. The agent must append the Oracle critique, directives, and sign-off to `implementation_plan.md` under `## Oracle Hardening, Directives & Verification Matrix` *before* yielding the turn for user approval.
- **Separation of Concerns in Plan Updates**: To preserve unbiased validation, Oracle does NOT rewrite the author's architecture sections. Instead, Oracle updates the plan exclusively via the dedicated `## Oracle Hardening, Directives & Sign-Off` section, appending binding constraints, risk mitigations, and verified testing mandates.
- **Atomic Task Synchronization**: Any new edge cases, mitigations, or tests mandated by Oracle must be atomically synced into `task.md` before implementation begins.
- **Cross-Artifact & Consistency Gate**: Before granting PASS, Oracle verifies cross-artifact alignment (Spec $\leftrightarrow$ Plan $\leftrightarrow$ Tasks) and architectural contract consistency.
- **Fresh Command Verification (D12)**: After implementing a fix, the agent must re-read test/verification output from a fresh `run_command` invocation rather than relying on memory of previous runs. The agent must never declare tests pass without actual execution evidence in the turn.
- Oracle can approve (PASS), request changes (CONDITIONAL), escalate, or abort (FAIL).
- Oracle MUST include hallucination audit for medium+ tasks at Final Review.
- Hallucination audit uses AgentHallu taxonomy via `hallucination-auditor` agent or independent review.
- FabricatedReference or CommandInvention findings = automatic FAIL.
- Cross-model oracle independence preferred when multi-model available.

## Minimal-Input Review Protocol & Anti-Anchoring Discipline (O-R1)
- Oracle reviews operate as an independent verification gate.
- To prevent anchoring bias, Oracle review prompts are strictly restricted to a 3-part minimal payload:
  1. **Spec & Constraints**: The approved Feature Spec or Control Manifest.
  2. **Code Evidence**: The surgical Git Diff (`git diff` filtered via `~/.gemini/antigravity/scripts/clean-diff.sh` to deterministically exclude lockfiles, minified bundles, and asset noise, unless inspecting raw dependency upgrades via `--raw`).
  3. **Fresh Execution Logs**: Raw command output from tests, lints, and type checks executed in the current turn.
- Oracle does not evaluate or rely upon the builder's conversational dialogue, intermediate scratchpad, or self-justifying narrative.
- Oracle updates implementation plans exclusively via `## Oracle Hardening, Directives & Verification Matrix`.

## Cross-Model Advisor Protocol (Gemini Variations Only)
- For high-risk architecture migrations or epic-level designs, Oracle may invoke a cross-tier second opinion (Gemini 3.1 Pro High $\leftrightarrow$ Gemini 3.8 Flash High) via configured CLI/MCP tools before final PASS.


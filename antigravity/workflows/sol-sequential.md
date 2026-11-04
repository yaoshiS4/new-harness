---
name: sol-sequential
summary: Path 3 Long-Horizon Route execution for epics, deep architecture, and multi-subsystem tasks (> 10 files).
---

# Path 3: Long-Horizon Route Workflow (Epic / Deep Architecture — > 10 Files)

## Purpose
Execute large-scale epics, architectural migrations, and multi-subsystem initiatives (> 10 files, >= 3 domains, or `/goal`) with zero scope drift, absolute role isolation, worktree concurrency isolation, context checkpointing, and deterministic multi-round verification.

## Deep Orchestration Sequence

```
1. Parallel 3-Explore ──> 2. Architect Spec & ADR ──> 3. PM Depth-Tree & Story Shards ──> 4. Adversarial Plan Gate ──> 5. Wave-Isolated Builders ──> 6. Context Checkpointing ──> 7. 3-Round Zero-Bug Loop ──> 8. Doc Sync
```

### Phase 1: Parallel 3-Explore
- Dispatched by Root Orchestrator: 3 read-only explorer subagents (`TypeName: "research"`, `Model: "flash"`):
  - `Role: "backend-explorer"`
  - `Role: "frontend-explorer"`
  - `Role: "research-explorer"`
- Method: CodeGraph facade first, symbol lookup, AST dependency analysis, and fallback reads.
- Output: 3 structured exploration briefs with affected symbol coordinates, dependencies, and candidate tests.

### Phase 2: Architect Spec & ADR Formulation (`sa`)
- Specialist Architect: `invoke_subagent TypeName: "self", Role: "sa" | "senior-architect", Model: "inherit"` (`"pro"` requires `force_ask`).
- Formulates technical specification, C4 topology, NFR metrics, and Architecture Decision Records (ADRs).
- **Strict Role Invariant**: Architect owns system design and ADRs; Architect **NEVER** writes application feature code.

### Phase 3: PM Depth-Tree & Story Shards Formulation (`pm`)
- Root Orchestrator (`pm`) decomposes epic using `unlazy` discipline:
  - Generates `PLAN.md` and `GATES.md` depth-trees with immutable acceptance gates.
  - Slices epic into atomic, disjoint **BMAD Story Shards** with strict file leases (`allowed_files`).
- **Strict Role Invariant**: PM orchestrates and drafts contracts; PM **NEVER** mutates application source code (`apps/**`, `packages/**`, `src/**`, etc.).

### Phase 4: Adversarial Plan Gate (`critical-planner` & Oracle)
- Specialist Planner: `invoke_subagent TypeName: "self", Role: "critical-planner", Model: "inherit"` (`"pro"` requires `force_ask`).
- Adversarial assumption challenging, epistemic stress testing, and failure mode analysis.
- Execute automated plan verification: `bash scripts/verification/verify-oracle.sh --plan` (when present, or scaffolded via `ensure-verification-gates.py`).

### Phase 5: Wave-Isolated Builders in Git Worktrees (`worktree-isolation`)
- Execute implementation in waves using `worktree-isolation` to prevent filesystem and lock contention.
- Max 2 concurrent write-capable Builder subagents (`TypeName: "self"`, `Role: "dev-fe" | "dev-be" | "debugger"`, `Model: "inherit"`).
- Builders operate strictly within their leased `allowed_files` inside isolated worktrees.

### Phase 6: Context Checkpointing (`handoff_checkpoint`)
- Monitor cognitive health via `context-rot-prevention`.
- When reaching 60% context budget or 8 user turns without completion:
  - Emit checkpoint: `call_mcp_tool(ServerName="codex_knowledge", ToolName="handoff_checkpoint", Arguments={"name": "sol:<task_id>:<phase>"})`.
  - Record break-resume contract in local SOT (`docs/STATUS.md`) and compact/resume.

### Phase 7: 3-Round Zero-Bug Loop & Oracle Release Gate
- Execute continuous verification harness:
  - `bash scripts/verification/test-3-round-loop.sh` (when present, or scaffolded via `ensure-verification-gates.py`)
  - `bash scripts/verification/verify-oracle.sh` (when present, or scaffolded via `ensure-verification-gates.py`)
- Read-Only QC & Audit:
  - `frontend-qc`: strictly read-only anti-slop and UI invariants review.
  - `test-runner`: runs regression test suites.
  - `oracle-review` / `hallucination-auditor`: audits clean diff (`scripts/clean-diff.sh`) against High-Precision Defect Taxonomy and AgentHallu checks. Any defects are routed back to a Builder subagent.

### Phase 8: Documentation Sync (`doc-sync-worker`)
- Dispatch `invoke_subagent TypeName: "research", Role: "doc-sync-worker", Model: "flash"`.
- Sync approved changes to `docs/STATUS.md`, `README.md`, PRD traceability matrices, and local knowledge graph.

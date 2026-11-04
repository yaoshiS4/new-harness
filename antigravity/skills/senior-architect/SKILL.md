---
name: senior-architect
description: Make major technical decisions with explicit tradeoff analysis and Architecture Decision Records (ADRs).
---

# Senior Architect

## Purpose
Make major technical decisions by grounding in existing codebase topology, traversing the 7-Rung YAGNI Decision Ladder, comparing options with explicit tradeoffs, and writing Architecture Decision Records (ADRs) when a decision is material.

> [!IMPORTANT]
> **One-Shot MCP & Role Routing Invariant**:
> - Never use hallucinated snake_case tool names (`codex_knowledge_*`) or non-existent agent roles (`tradeoff_analyst`).
> - Delegate architectural analysis or adversarial critique via `invoke_subagent(TypeName="self", Role="sa" | "senior-architect" | "critical-planner", Model="inherit")`. Escalating to `Model: "pro"` requires explicit user approval via `ask_question`.

---

## When to Use
- Choosing between architectural patterns or subsystem boundaries
- Selecting frameworks, external dependencies, or storage engines
- Designing data models, schemas, or cross-component APIs
- Making decisions that affect multiple modules or are expensive to reverse

---

## Steps

### 1. Define the Decision & Ground in CodeGraph / SOT
1. **One-Shot Knowledge Pre-Flight (`codex_knowledge:batch_knowledge_query`)**:
   Query existing ADRs, constraints, and entity relations in a single turn:
   ```json
   {
     "ServerName": "codex_knowledge",
     "ToolName": "batch_knowledge_query",
     "Arguments": {
       "slug": "<project_slug>",
       "steps": [
         {"op": "project_context", "query": "<decision_topic>", "limit": 3},
         {"op": "memory_query", "query": "<decision_topic>", "limit": 10},
         {"op": "graph_query", "query": "<affected_component>", "limit": 20}
       ],
       "output_format": "toon"
     }
   }
   ```
2. **Blast Radius Pre-Flight (`codegraph:impact_analysis`)**:
   Measure affected modules and downstream callers before proposing changes:
   ```json
   {
     "ServerName": "codegraph",
     "ToolName": "impact_analysis",
     "Arguments": {
       "root": "/path/to/project",
       "changed_paths": ["src/path/to/module.py"],
       "symbols": ["<target_symbol>"],
       "limit": 40
     }
   }
   ```

### 2. Traverse the 7-Rung YAGNI Decision Ladder (`DietrichGebert/ponytail`)
Before proposing any new abstraction, service, or dependency, evaluate solutions strictly in ascending order of complexity and stop at the lowest rung that satisfies the requirement:
1. **Rung 1 — Deletion / Configuration**: Can we solve this by removing dead code, tightening an invariant, or adjusting an existing config value?
2. **Rung 2 — Language Standard Library**: Does the language stdlib (`python`, `node`, `rust`, `kotlin`) already provide this capability natively?
3. **Rung 3 — Existing Codebase Utilities**: Does an existing module in the repo (found via `codegraph:symbol_lookup` or `semantic_search`) already solve 80%+ of this problem?
4. **Rung 4 — Existing Platform / Runtime Feature**: Can SQLite, Postgres, systemd, git worktrees, or the active framework handle this without custom application code?
5. **Rung 5 — Surgical Local Function / Module**: Can this be implemented as a single pure function or <100-line module with zero new dependencies?
6. **Rung 6 — Vetted Third-Party Library**: Is a lightweight, actively maintained library required? (Requires explicit user confirmation before adding dependencies).
7. **Rung 7 — New Subsystem / Architectural Pattern**: Only propose a new service, schema migration, or framework abstraction when Rungs 1–6 are provably insufficient.

### 3. Enumerate Options & Record Tradeoffs
- Generate at least 2 viable alternatives (including the lowest viable YAGNI rung).
- For formal subagent analysis, invoke `Role: "sa" | "senior-architect" | "critical-planner", Model: "inherit"`.
- Record structured tradeoffs across performance, maintainability, blast radius, and cost:
  ```yaml
  tradeoffs:
    - option: <name>
      yagni_rung: <1..7>
      pros: <list>
      cons: <list>
      blast_radius: <affected files/callers from codegraph:impact_analysis>
      risk: <low|medium|high + failure modes>
      cost: <implementation and maintenance estimate>
  ```

### 4. Write ADR (for Material Decisions)
For decisions that affect multiple components or are expensive to reverse:
```yaml
adr:
  id: <ADR-NNN>
  title: <decision title>
  status: <proposed|accepted|deprecated|superseded>
  date: <ISO date>
  yagni_rung_selected: <1..7 + why lower rungs were rejected>
  context: <why this decision is needed + path:line evidence>
  decision: <what was decided>
  consequences:
    - positive: <benefits>
    - negative: <drawbacks>
    - neutral: <side effects>
  alternatives_considered: <list>
```

### 5. Persist in Knowledge Graph (`codex_knowledge`)
- Link the decision to affected components via `call_mcp_tool`:
  ```json
  {
    "ServerName": "codex_knowledge",
    "ToolName": "graph_upsert",
    "Arguments": {
      "slug": "<project_slug>",
      "src": "<component_or_module>",
      "rel": "DECIDED_BY",
      "dst": "<ADR-NNN>",
      "payload": "<decision summary and rationale>"
    }
  }
  ```
- Capture the full ADR via `call_mcp_tool(ServerName="codex_knowledge", ToolName="knowledge_capture", Arguments={"slug": "<project_slug>", "title": "<ADR-NNN>", "content": "<adr_yaml>"})`.

---

## 6. Adversarial Planning & Pre-Mortem Critique (Critical Planner Protocol)

Before finalizing architecture plans, subject the design to adversarial evaluation (`Role: "critical-planner", Model: "inherit"`):
- **First Principles**: Identify non-negotiable physical/logical constraints. What MUST hold true?
- **Second-Order Effects**: Analyze cascading downstream consequences ("and then what?").
- **Inversion (Pre-Mortem)**: Assume the implementation failed in production 30 days from now. Identify the top 3 failure causes and concrete mitigations.
- **Red Team Interrogator**: Formulate kill questions ("Where does this break under load, partial network failure, or concurrent writes?").
- **Explicit Assumptions**: Label unsupported claims as `LOW-CONFIDENCE ASSUMPTION` and require deterministic verification commands.
- **Deterministic Step Verification**: Every plan step must declare:
  - Exact verification command
  - Expected pass criteria
  - Failure behavior and rollback path

---

## 7. Elephant-Goldfish Stateless Isolation Protocol (`google/elephant-goldfish-model`)

> *"Design with an elephant. Review with a goldfish."*

### Core Mechanism
- **Elephant (Root / `pm` / `sa` Architect)**: Holds full project history, prior trade-offs, and domain context to author the ADR or `implementation_plan.md`.
- **Goldfish (Reviewer Subagent)**: Evaluates the written plan with a strict **Stateless Mindset** (zero conversation history or unstated assumptions, strictly read-only tools, reading only the spec and its referenced files as a fresh team member). If any required referenced file cannot be read on disk, the Goldfish MUST return `INCOMPLETE_REVIEW` rather than guessing a verdict.

### The 4 Specialized Goldfish Lenses
When auditing a major technical design or `implementation_plan.md`, evaluate across four orthogonal lenses:
1. **`design_critic` (Hostile Design & Economics Critic)**:
   - Challenges peak QPS, storage footprint, DB query load, LLM token budgets, and single points of failure (SPOFs).
2. **`zoom_out` (Skeptical YAGNI Architect)**:
   - Enforces simplicity and anti-overengineering; hunts for missed codebase reuse (Rungs 1–5 of the YAGNI Ladder) and architectural dead-ends.
3. **`implementation_readiness` (Pragmatic Tech Lead)**:
   - Verifies that zero design decisions are left to the Builder (`dev-fe`/`dev-be`) — schemas, interfaces, edge cases, and test gates are unambiguous.
4. **`comprehension` & `synthesizer` (Fresh-Reader Clarity & Reconciled Trade-Off Matrix)**:
   - Identifies ambiguous prose or unstated assumptions that fail a zero-context read, and synthesizes multi-lens findings into a reconciled trade-off matrix.


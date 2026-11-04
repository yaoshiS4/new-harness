# Escalation Gate

## Purpose
When the runtime cannot decide safely, escalate to the user rather than guessing. This gate prevents high-cost wrong decisions by forcing human input at critical junctures.

## Escalation Decision Tree

```
PM or agent encounters a decision point
    │
    ▼
Is the decision covered by the task contract with clear guidance?
    │
    ├── YES → Make the decision per contract (no escalation needed)
    │
    └── NO → What is the cost of being wrong?
                │
                ├── LOW → Make the decision using best judgment; document in knowledge_capture
                │
                ├── MEDIUM → Use independent_ensemble to generate 2 proposals; PM selects
                │
                └── HIGH → ESCALATE to user (this gate)
                            │
                            ├── Prepare escalation package (Section 2)
                            ├── Present options to user (Section 3)
                            ├── Record decision (Section 4)
                            └── Resume execution
```

## When to Trigger

Trigger the escalation gate when ANY of the following conditions are met AND the cost of being wrong is HIGH:

| Condition | Cost of Wrong Decision | Examples |
|-----------|------------------------|----------|
| Ambiguous requirements that could change scope | HIGH | User said "make it fast"—does that mean caching, async, or hardware upgrade? |
| Multiple valid approaches with different tradeoffs | HIGH | REST vs. GraphQL for public API; choice affects 3+ downstream services |
| Security-sensitive decisions | HIGH | Authentication method, encryption algorithm, secret storage location |
| Architecture changes that affect multiple components | HIGH | Changing the database layer, introducing a message queue, splitting a monolith |
| Technology selection with long-term lock-in | HIGH | Choosing a framework that will be used across 10+ future tasks |
| Data model changes affecting existing data | HIGH | Schema migration that requires data transformation or downtime |
| Legal or compliance implications | HIGH | GDPR data handling, licensing of dependencies, export control |
| Budget or resource allocation decisions | HIGH | Adding new cloud services, increasing team size, extending timeline |

**Do NOT escalate for:**
- Naming conventions (use project style guide or `call_mcp_tool(ServerName="codex_knowledge", ToolName="vault_search")`)
- Minor refactoring decisions (use `oracle-review` skill)
- Test coverage thresholds (use task contract defaults)
- Code formatting (use linter configuration)
- Single-file implementation details (use builder judgment)

---

## Steps

### 1. Identify the Decision

PM MUST document the decision clearly before escalating:

| Field | Description | Example |
|-------|-------------|---------|
| Decision statement | One-sentence description of what needs to be decided | "Which authentication mechanism should we implement for the public API?" |
| Stakeholders | Who is affected by this decision | "All API consumers, security team, DevOps" |
| Deadline | When the decision is needed | "Within 2 hours to stay on sprint schedule" |
| Default option | What will happen if no decision is made | "Defer to next sprint; current basic auth remains" |

**Tool References:**
- `call_mcp_tool(ServerName="codex_knowledge", ToolName="project_context")` — gather background on affected components
- `call_mcp_tool(ServerName="codex_knowledge", ToolName="vault_search")` — check for existing decisions or patterns
- `call_mcp_tool(ServerName="codex_knowledge", ToolName="graph_query")` — search for related architectural decisions in memory

---

### 2. Prepare the Escalation Package

Gather ALL relevant context needed for the user to make an informed decision:

#### 2.1 Context Gathering Checklist

- [ ] Task contract reference and current scope
- [ ] List of options with detailed descriptions
- [ ] Tradeoffs for each option (pros, cons, quantified impacts where possible)
- [ ] Risks for each option with severity and mitigation
- [ ] Evidence supporting each option (Tier 1 sources preferred)
- [ ] Consequences of choosing wrong
- [ ] Urgency level and deadline
- [ ] Recommendation from PM/Oracle (if any)
- [ ] Default option if user does not respond

#### 2.2 Escalation YAML

Structure the escalation as:

```yaml
escalation:
  escalation_id: <unique identifier>
  task_ref: <task contract reference>
  timestamp: <ISO-8601>
  decision: <one-sentence description>
  urgency: <low|medium|high|critical>
  deadline: <ISO-8601 or "none">
  default_option: <what happens if no response>

  context:
    background: <why this decision is needed now>
    affected_components: <list of systems/files>
    constraints: <budget, time, technology restrictions>

  options:
    - option_id: "A"
      label: <short name>
      description: <detailed description>
      tradeoffs:
        - pro: <advantage with quantified impact if possible>
          con: <disadvantage with quantified impact if possible>
      risks:
        - risk: <description>
          severity: <critical|major|minor>
          mitigation: <how to address>
      evidence:
        - source: <tool or document>
          finding: <what supports this option>
          tier: <1|2|3>
      estimated_effort: <time or LOC>
      estimated_impact: <performance, cost, or maintainability impact>

    - option_id: "B"
      label: <short name>
      description: <detailed description>
      # ... same structure as option A

    # Minimum 2 options required; maximum 4 options

  consequences_of_wrong_decision: |
    <what happens if we choose the wrong option>
    <include rollback difficulty, cost, and timeline>

  pm_recommendation: <which option PM favors and why, or "no recommendation">
  oracle_recommendation: <which option Oracle favors and why, or "no recommendation">

  user_response:
    selected_option: <A|B|C|D or "none">
    rationale: <user's reasoning>
    conditions: <any conditions or caveats attached to the decision>
    responded_at: <ISO-8601>
```

**Tool References:**
- `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "project_context"`) — generate diverse option perspectives
- `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "graph_query"`) — validate options for logical consistency
- `call_mcp_tool` (`ServerName: "context7"`, `ToolName: "query-docs"`) — verify technology claims in options

---

### 3. Escalate to User

1. **Present Options:**
   - Use the `ask_question` tool to present the escalation package to the user.
   - Format: multiple-choice with the options from the escalation YAML.
   - Include a "Type your own answer" option for custom responses.
   - Include all context needed for an informed decision (do not assume user remembers prior conversations).

2. **Set Expectations:**
   - State the deadline clearly.
   - State the default option if no response is received.
   - State the urgency level.

3. **Wait for Response:**
   - Pipeline is PAUSED until user responds.
   - Do NOT proceed with any implementation until the decision is recorded.
   - If user does not respond within the deadline, use the default option and document the timeout.

**Example `ask_question` Tool Invocation:**

```yaml
questions:
  - header: "Auth Method Selection"
    question: |
      We need to choose an authentication mechanism for the public API.
      This decision affects all API consumers and has security implications.
      Please select one of the following options:
    options:
      - label: "Option A: JWT with Refresh Tokens"
        description: "Stateless tokens with 15-min TTL and refresh rotation. Lower DB load, but token revocation requires blacklist."
      - label: "Option B: Session-Based Auth"
        description: "Server-side sessions in Redis. Immediate revocation, but requires Redis dependency and higher DB load."
      - label: "Option C: OAuth2 with External Provider"
        description: "Delegate auth to Auth0 or similar. Minimal code, but adds vendor dependency and cost."
    multiple: false
```

---

### 4. Record the Decision

Once the user responds (or timeout occurs):

1. **Capture Decision:**
   - Use `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "knowledge_capture"`):
     - `key`: `escalation_decision_<escalation_id>`
     - `value`: the full escalation YAML with `user_response` filled in
   - Use `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "graph_upsert"`) to store the decision as a durable fact:
     - `subject`: the decision topic (e.g., "public_api_auth_method")
     - `relation`: "decided_as"
     - `target`: the selected option
     - `evidence`: the escalation_id and rationale

2. **Update Task Contract (if scope changed):**
   - If the user's decision changes the scope, update the task contract.
   - Run PM task contract review to validate the updated scope.
   - If drift exceeds budget, invoke `./abort_gate.md` or renegotiate.

3. **Resume Execution:**
   - Builder continues implementation based on the user's decision.
   - PM updates the pipeline state to reflect the decision.
   - Record the decision via `call_mcp_tool` (`ServerName: "codex_knowledge"`, `ToolName: "handoff_checkpoint"`):
     - `trace_class`: "escalation_resolution"
     - `title`: "Escalation resolved: <decision>"
     - `payload`: { `escalation_id`, `selected_option`, `rationale` }

---

## Guardrails

| Guardrail | Enforcement | Violation Action |
|-----------|-------------|------------------|
| Never guess when cost is high | PM must escalate if cost of wrong decision is HIGH | If violated, Oracle flags the decision and forces escalation retroactively |
| Never skip escalation for security | Security-sensitive decisions MUST go through this gate | If violated, abort the slice and force security review |
| Always present ≥2 options | Escalation package must include at least 2 viable options | Return package to PM for revision |
| Always include tradeoffs | Each option must have explicit pros and cons | Return package to PM for revision |
| Always record decisions | Every escalation must be persisted in knowledge_capture and graph | If missing, pipeline cannot proceed |
| Always set a default | Every escalation must define what happens if user does not respond | If missing, default to "pause until response" |
| Never manipulate user toward a preferred option | Options must be presented neutrally | If bias detected, Oracle rewrites options |

---

## Tool References

| Tool | Purpose | When to Invoke |
|------|---------|----------------|
| `ask_question` | Present options to user and capture response | During escalation step 3 |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="knowledge_capture")` | Persist escalation package and decision | After context gathering and after user response |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="graph_upsert")` | Store decision as durable architectural fact | After user response |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="project_context")` | Gather background on affected components | During context gathering |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="vault_search")` | Check for existing decisions or patterns | During context gathering |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="graph_query")` | Search for related architectural decisions | During context gathering |
| `call_mcp_tool(ServerName="context7", ToolName="query-docs")` | Verify technology claims in options | During option preparation |
| PM task contract review | Re-validate scope if decision changes it | After user response |
| `call_mcp_tool(ServerName="codex_knowledge", ToolName="handoff_checkpoint")` | Audit trail of escalation and resolution | After escalation and after resolution |

# Oracle Review Rubric

The Oracle is the independent review gate. Every major phase must pass Oracle review before proceeding.

## Review Checklist

### 1. Correctness
- [ ] All acceptance criteria met
- [ ] No type errors (LSP diagnostics clean)
- [ ] No dead code or unreachable branches
- [ ] Edge cases handled

### 2. Scope Drift
- [ ] Implementation matches task contract / Story Shard scope
- [ ] No feature creep beyond original request
- [ ] Scope drift budget not exceeded (default: 5%)
- [ ] Compare `git diff --name-only` against Story Shard `allowed_files`

### 3. Regression Risk
- [ ] Existing tests still pass
- [ ] No breaking API changes without migration
- [ ] Dependency changes are minimal and justified

### 4. Test Evidence
- [ ] Unit tests cover new logic
- [ ] Integration tests cover happy paths
- [ ] Edge case tests exist for critical paths

### 5. Document Alignment
- [ ] Code matches documentation
- [ ] Changelog updated if needed
- [ ] SOT (vault/wiki) updated if architectural change

### 6. AOP Consistency Gate (MANDATORY)
- [ ] Verify cross-claim consistency (`skills/oracle-review/SKILL.md`) across all claims from the implementation
- [ ] Verify no logical contradictions in:
  - Design claims vs. implementation reality
  - Stated constraints vs. actual behavior
  - Inter-module contracts vs. actual interfaces
- [ ] If AOP check returns conflicts, they MUST be resolved before passing Oracle
- [ ] Record AOP check result in the review output

### 7. Minimalism Gate
- [ ] Surgical diff (`~/.gemini/antigravity/scripts/clean-diff.sh`) passes 4-Angle Anti-Bloat Review
- [ ] No unnecessary abstractions
- [ ] Diff is surgical (minimal added/removed lines)

### 8. Hallucination Audit Gate (MANDATORY for medium+ tasks)
- [ ] Spawn `hallucination-auditor` subagent (`TypeName: "self"`, `Role: "hallucination-auditor"`, `Model: "inherit"`; escalating to `"pro"` requires `force_ask`) with AgentHallu taxonomy
- [ ] Verify no FabricatedReference (non-existent files, functions, packages)
  - Evidence: `fd` / `view_file` / `call_mcp_tool(ServerName="codegraph", ToolName="symbol_lookup")` results
- [ ] Verify no CommandInvention (invalid or unsupported CLI commands)
  - Evidence: `command -v`/`--help` output
- [ ] Verify no StateDivergence (test/state claims without execution evidence)
  - Evidence: actual test/command execution output
- [ ] Verify no ScopeCreep (changes beyond task contract `allowed_files`)
  - Evidence: `git diff --name-only` vs `allowed_files`
- [ ] Audit output includes `findings[]`, `evidence_refs[]`, `verdict: PASS|FAIL`
- [ ] **FabricatedReference or CommandInvention = automatic FAIL, return to implementation**

### 9. VeriHarness (`arXiv:2610.00972`) & Oracle Custody Lease (`arXiv:2610.28667`)
- [ ] **VeriHarness Grounding**: Fresh executable test and typecheck outputs are attached; zero unverified completion claims.
- [ ] **Oracle Custody Lease**: Verify existing test assertions were not deleted, weakened, or tautologized unless the Story Shard explicitly grants `Oracle-Custody-Lease: UPDATE_ASSERTIONS`.

## 6-Stage Lexicographic Deliverable Selection Ladder

When comparing candidate patches or evaluating a deliverable against the baseline (`KEEP_BASE`), apply strict lexicographic ordering (earlier stages dominate later stages):
1. **Stage 1 — Security & Custody Invariant**: Zero security regressions (`sec_score == 1.0`) and zero unauthorized test assertion mutations (`Oracle-Custody-Lease` respected).
2. **Stage 2 — Contract & Scope Compliance**: Zero edits outside `allowed_files` and scope drift $\le 5\%$.
3. **Stage 3 — Functional Verification (`func_score`)**: 100% pass rate on required unit/integration tests and compiler diagnostics (`VeriHarness`).
4. **Stage 4 — AOP & Hallucination Cleanliness**: Zero `FabricatedReference`, `CommandInvention`, `StateDivergence`, or AOP contradictions.
5. **Stage 5 — Behavioral Equivalence / Improvement ($\Delta_{\text{behav}}$)**: Positive behavioral delta on target acceptance criteria; ties default to `KEEP_BASE`.
6. **Stage 6 — Minimalism & Token Efficiency (`token_score`)**: Smallest surgical diff (`clean-diff.sh`) that satisfies Stages 1–5.

## Oracle Verdict

| Verdict | Condition |
|---------|-----------|
| PASS | All checklist items pass, AOP clean, hallucination audit clean |
| CONDITIONAL | Minor issues that can be fixed in-place |
| FAIL | Scope drift, AOP conflicts, hallucination findings (BLOCKER), or regression detected |

## Output Format

```yaml
oracle_review:
  task_ref: <task contract reference>
  verdict: <PASS|CONDITIONAL|FAIL>
  checklist:
    correctness: <pass|fail>
    scope_drift: <pass|fail>
    regression_risk: <pass|fail>
    test_evidence: <pass|fail>
    document_alignment: <pass|fail>
    aop_consistency: <pass|fail|conflicts_found>
    minimalism: <pass|fail>
    hallucination_audit: <pass|fail>
  aop_result:
    conflicts: <number>
    details: <list of conflicts if any>
  hallucination_result:
    findings: <count>
    blocker_count: <number>
    verdict: <PASS|FAIL>
    evidence_refs: <list>
  scope_drift_budget_used: <percentage>
  recommendations: <list>
```


## Post-Oracle Capture (MANDATORY)

After Oracle PASS:
- Record validated findings via `call_mcp_tool` on `codex_knowledge` (`ToolName: "knowledge_capture"`) with `source_ref` pointing to the task contract.
- This mirrors the lesson to both memory (deduped) and project graph.
- Do NOT capture from FAIL or CONDITIONAL verdicts - only validated outcomes.
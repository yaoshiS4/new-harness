# Security Checklist Guideline

**Trigger**: Task involves authentication, authorization, data storage, external APIs, shell/hook execution, or untrusted user input.

## OWASP & Agent Harness Security Checklist
- [ ] **Zero Secrets in Code or Logs**: No API keys, private keys, or credentials in source or git history (`rg -n -m 50` secret scan clean).
- [ ] **Strict Input Validation & Parameterization (OWASP A03)**: Schema-validate all external inputs (Zod/Pydantic); use parameterized queries to prevent SQL/NoSQL/command injection (`shell=False`).
- [ ] **Output Encoding & XSS Prevention**: Context-aware encoding on rendered data; strict Content-Security-Policy (CSP) headers; avoid `dangerouslySetInnerHTML`.
- [ ] **Authentication & Object-Level Authorization (OWASP API1 / BOLA)**: Verify identity and resource ownership on every protected endpoint; enforce least-privilege RBAC/scopes.
- [ ] **Rate Limiting & SSRF Protection**: Enforce rate limits on public endpoints; validate and allowlist outbound URLs against internal/metadata IP ranges.
- [ ] **Dependency & Supply Chain Integrity**: Pin exact lockfile versions (`dependency-policy.md`) and verify 0 critical/high CVEs (`npm audit` / `pip-audit`).
- [ ] **Agent Harness Guardrails (CK-02 & CP-2 `sec_score == 1.0`)**:
  - Preserve **CK-02 Security Guardrail Integrity**: Never weaken, bypass, or delete block rules in `config/hooks/pre_tool_use_hook.py` or `stop_hook.py`.
  - Maintain **Harmony CP-2 `sec_score == 1.0`**: All 5 mechanical checks in `python3 antigravity/scripts/validate-harness-tree.py` must pass at 100%.

## Enforcement
- Run `security-audit` (`Role: "security-audit" | "whitehat"`, `Model: "inherit"`) before merging auth, crypto, or hook changes.
- Block release immediately if any checklist item fails or `sec_score < 1.0`.
- Document any approved architectural exceptions in the task contract.

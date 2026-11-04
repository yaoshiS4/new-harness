---
description: Dependency Policy - update cadence, auto-merge rules, and major upgrade reviews
---

# RULE: DEPENDENCY POLICY

**Mode:** Always On
**Scope:** DevOps, Development

---

## Update Cadence
| Type | Policy | Review Required |
|---|---|---|
| Patch (x.y.Z) | Auto-merge if tests pass | No |
| Minor (x.Y.0) | Merge after test run | Light review |
| Major (X.0.0) | Manual review required | Senior dev review |
| Security fix | Immediate (any level) | Post-merge review OK |

## Maximum Age
- No dependency should be more than **2 major versions** behind latest.
- Security patches must be applied within **48 hours** of disclosure.

## Adding New Dependencies
Before adding a new dependency, evaluate:
- [ ] Is there a native/simpler alternative?
- [ ] Bundle size impact (< 50KB gzipped)?
- [ ] Maintenance health (last commit < 6 months)?
- [ ] Download count (> 1000/week)?
- [ ] License compatibility (MIT, Apache-2.0, BSD preferred)?
- [ ] Security audit (no known vulnerabilities)?

## Rules
- Never add a dependency without documenting the justification and obtaining user approval (`ask_question`).
- Require exact lockfile pinning (`package-lock.json`, `pnpm-lock.yaml`, `uv.lock`, `Cargo.lock`) combined with explicit semver bounds in manifests (e.g., `==x.y.z` for reproducible Python services or explicit `^x.y.z` / `~x.y.z` paired with committed lockfiles).
- Use lock files for reproducible builds (`npm ci`, `pnpm install --frozen-lockfile`, `uv sync --frozen`).
- Run security audit as part of CI pipeline (`npm audit`, `pip-audit` / `safety check`).

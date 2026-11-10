# Gates: 1.1 Foundation integration

Scope: integrate children 1.1.1 (tokens and styles) and 1.1.2 (domain types, fixtures, data) into one verified foundation

- [ ] N1: every named direct child is reverified from its exact ledger
  CHECK: node ~/.claude/skills/unlazy/scripts/gate-check.mjs --root . --cwd . --reverify --jobs 1 .unlazy/yaobet-p1/gates/leaf-1.1.1.md .unlazy/yaobet-p1/gates/leaf-1.1.2.md
  EXPECT: ALL MET
  EVIDENCE: pending

- [ ] N2: merged main lints, typechecks and builds with both leaves present
  CHECK: npm run lint && npx next typegen && npx tsc --noEmit && npm run build && echo FOUNDATION_BUILD_OK
  EXPECT: FOUNDATION_BUILD_OK
  EVIDENCE: pending

- [ ] N3: the Fixture contract and the token contract agree with PLAN.md Interfaces (core.ts exports Fixture with the four states; tokens.css declares every TOKENS.md §3 group)
  CHECK: node scripts/verify-tokens.mjs && node -e "const s=require('fs').readFileSync('src/lib/types/core.ts','utf8');for(const k of ['\"ready\"','\"loading\"','\"error\"','\"stale\"','Fixture']){if(!s.includes(k)){console.log('missing',k);process.exit(1)}}console.log('fixture contract ok')"
  EXPECT: fixture contract ok
  EVIDENCE: pending

- [ ] N5: every direct leaf child's ownership lease was released after parent verification
  EVIDENCE: pending

- [ ] N6: consequential manual outcomes from the children were reviewed at branch level (placeholder ramp renders readable AA contrast; formatDong output checked by hand on 3 values)
  EVIDENCE: pending

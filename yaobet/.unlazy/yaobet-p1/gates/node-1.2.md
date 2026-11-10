# Gates: 1.2 Shell integration

Scope: integrate children 1.2.1 (UI primitives) and 1.2.2 (app shell and notifications) into one verified shell on top of the foundation

- [ ] N1: every named direct child is reverified from its exact ledger
  CHECK: node ~/.claude/skills/unlazy/scripts/gate-check.mjs --root . --cwd . --reverify --jobs 1 .unlazy/yaobet-p1/gates/leaf-1.2.1.md .unlazy/yaobet-p1/gates/leaf-1.2.2.md
  EXPECT: ALL MET
  EVIDENCE: pending

- [ ] N2: merged main lints, typechecks and builds with the shell mounted in the root layout
  CHECK: npm run lint && npx next typegen && npx tsc --noEmit && npm run build && echo SHELL_BUILD_OK
  EXPECT: SHELL_BUILD_OK
  EVIDENCE: pending

- [ ] N3: the route sweep passes for the routes that exist at this point (/, not-found)
  CHECK: node scripts/verify-routes.mjs / /khong-ton-tai-404
  EXPECT: routes verification passed
  EVIDENCE: pending

- [ ] N4: token and import gates stay clean across ui and layout
  CHECK: node scripts/verify-tokens.mjs && node scripts/verify-content.mjs
  EXPECT: content verification passed
  EVIDENCE: pending

- [ ] N5: every direct leaf child's ownership lease was released after parent verification
  EVIDENCE: pending

- [ ] N6: frontend-qc anti-slop pass on the shell (T-12: nav items are label-first; D-09: one unread pill max; L-01: no nested surfaces in the bell panel) reviewed at branch level
  EVIDENCE: pending

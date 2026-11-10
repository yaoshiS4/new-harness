# Gates: 1.3 Surfaces integration

Scope: integrate children 1.3.1 through 1.3.9 into one verified set of phase-1 surfaces on the shell

- [ ] N1: every named direct child is reverified from its exact ledger
  CHECK: node ~/.claude/skills/unlazy/scripts/gate-check.mjs --root . --cwd . --reverify --jobs 1 .unlazy/yaobet-p1/gates/leaf-1.3.1.md .unlazy/yaobet-p1/gates/leaf-1.3.2.md .unlazy/yaobet-p1/gates/leaf-1.3.3.md .unlazy/yaobet-p1/gates/leaf-1.3.4.md .unlazy/yaobet-p1/gates/leaf-1.3.5.md .unlazy/yaobet-p1/gates/leaf-1.3.6.md .unlazy/yaobet-p1/gates/leaf-1.3.7.md .unlazy/yaobet-p1/gates/leaf-1.3.8.md .unlazy/yaobet-p1/gates/leaf-1.3.9.md
  EXPECT: ALL MET
  EVIDENCE: pending

- [ ] N2: merged main lints, typechecks and builds with every surface present
  CHECK: npm run lint && npx next typegen && npx tsc --noEmit && npm run build && echo SURFACES_BUILD_OK
  EXPECT: SURFACES_BUILD_OK
  EVIDENCE: pending

- [ ] N3: every phase-1 route renders with status 200, lang="vi", a "— Yaobet" title, and no error boundary text
  CHECK: node scripts/verify-routes.mjs / /sanh-game /sanh-game/the-thao /sanh-game/casino /sanh-game/no-hu /sanh-game/ban-ca /sanh-game/game-bai /sanh-game/xo-so /sanh-game/da-ga /sanh-game/ban-choi /sanh-game/game-nhanh /sanh-game/khong-co-404 /vi-tien /tai-khoan /tin-nhan /vip /hoan-tra /cuoc-hop-le /cua-hang /gioi-thieu /khuyen-mai "/khuyen-mai/$(node --experimental-strip-types -e "import('./src/lib/mock/promos.ts').then(m=>console.log((m.PROMOS??m.promos)[0].id))")" /khuyen-mai/khong-co-404 /bo-suu-tap /ve-so /ho-tro /khong-ton-tai-404
  EXPECT: routes verification passed
  EVIDENCE: pending

- [ ] N4: token, literal and import gates stay clean across all surfaces
  CHECK: node scripts/verify-tokens.mjs && node scripts/verify-content.mjs
  EXPECT: content verification passed
  EVIDENCE: pending

- [ ] N5: every direct leaf child's ownership lease was released after parent verification
  EVIDENCE: pending

- [ ] N6: frontend-qc anti-slop reports for all eight surfaces reviewed at branch level with zero open `Fail:` items; cross-surface consistency (same Money, Skeleton, StateBlock everywhere; BRAND.md §4 gold rule on every surface) confirmed
  EVIDENCE: pending

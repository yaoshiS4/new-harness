# Gates: 1.3.9 Scratch card

OWNS: src/app/ve-so/**, src/components/scratch/**, src/lib/copy/scratch.ts, src/lib/types/scratch.ts, src/lib/mock/scratch.ts, src/lib/data/scratch.ts

Scope: the scratch-card hub `/ve-so` with the 12-panel card interaction that credits money before it celebrates, on mock data, at 375 and 1440.

Deliverable detail (read SOT §4 4.7 (cards earned by settled betting and bought; no consolation payment; face fixed before touch; money lands before the celebration; fairness board, earn ledger, card history), §3 (lucky numbers), §2 (celebration only on money-landed); REFERENCE_APP_INVENTORY.md §2 scratch card; ADR-001 §2.7; TOKENS.md §3.9 (`--motion-duration-celebrate`); PLAN.md Conventions (lib-layer rule, provenance vocabulary)):
- Hub: cards earned (from settled bets) and buyable (`Money` price `[OWNER DATA]`), a prize ladder from the fixture (11 rungs from 10.000 ₫ to 20.000.000 ₫ is the as-built shape `[APP + OWNER rulings 2026-09-18]`; rung amounts `[OWNER DATA]`, placeholders follow the lucky rule and carry `// [OWNER DATA]`), "Tỷ lệ thẻ trúng" fairness board rendered as the pending `Pill` (the 38.7% figure is `[APP]`, not printed), earn ledger, card history.
- Card component: 12 panels and four winning numbers `[APP + OWNER rulings 2026-09-18]`, face fixed in the fixture before any interaction, reveal interaction (client component) whose outcome enum is exactly `"win" | "none"`; on `win` the balance row updates first (a `money-landed` event name in code) and only then the single celebration motion runs (`--motion-duration-celebrate`, final frame under reduced motion); on `none` a plain "Chúc may mắn lần sau" line, no payment of any kind.
- Fixtures with four variants; copy file; page exports `metadata.title`.

- [ ] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: pending

- [ ] G2: typecheck passes after route typegen
  CHECK: npx next typegen && npx tsc --noEmit && echo TSC_OK
  EXPECT: TSC_OK
  EVIDENCE: pending

- [ ] G3: production build passes
  CHECK: npm run build && echo BUILD_OK
  EXPECT: BUILD_OK
  EVIDENCE: pending

- [ ] G4: token, import and content gates pass
  CHECK: node scripts/verify-tokens.mjs && node scripts/verify-content.mjs
  EXPECT: content verification passed
  EVIDENCE: pending

- [ ] G5: the route renders; the outcome enum is exactly win | none; the celebration is bound to money-landed; the copy has no consolation wording
  CHECK: node scripts/verify-routes.mjs /ve-so && node -e "const fs=require('fs');const t=fs.readFileSync('src/lib/types/scratch.ts','utf8');if(!/\"win\"\s*\|\s*\"none\"/.test(t)){console.log('outcome enum');process.exit(1)}const comp=fs.readdirSync('src/components/scratch').map(f=>fs.readFileSync('src/components/scratch/'+f,'utf8')).join('');if(!comp.includes('money-landed')){console.log('celebration not bound');process.exit(1)}const c=fs.readFileSync('src/lib/copy/scratch.ts','utf8');if(/an ủi|\bdust\b/i.test(c)){console.log('consolation wording');process.exit(1)}console.log('scratch verified')"
  EXPECT: scratch verified
  EVIDENCE: pending

- [ ] G6: frontend-qc anti-slop and money-truth pass at 375 and 1440 (celebration only after the credit row updates, one CTA, BRAND.md §4 gold rule) with zero open Fail items
  EVIDENCE: pending

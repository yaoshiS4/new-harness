# Gates: S8 promo routes

OWNS: src/components/promo/**, src/app/khuyen-mai/**, src/styles/areas/promo.css

Wave: W9 · Needs (merged before dispatch): F5, S6 · Dev-server port: 3128

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/components/promo/**
  - src/app/khuyen-mai/**
  - src/styles/areas/promo.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `L8 promo-routes` row in `docs/rebuild/review/shell-home.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/S8.sh` (PM-authored; never edit it).

- [x] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=eb7a2e14e3169d81be1e61fe79fc94ac8e6e81df4e4a933527b90030ffee4607; exit=0; EXPECT=matched; output-sha256=3006516902c604a845b19946dd7dda6e224c7c00040b87bff313077f683f1e7b; output-bytes=833; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G2: typecheck passes
  CHECK: npx tsc --noEmit && echo TSC_OK
  EXPECT: TSC_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=48a822910fccd73a590c55e6e847659263f5ac983269371a7d08e6f1ca184cb6; exit=0; EXPECT=matched; output-sha256=d018f66bb24b65f8f3c86936c97cc0c033c796f2f7b335753a186d3d2c5818a4; output-bytes=7; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G3: token lint holds
  CHECK: npm run lint:tokens
  EXPECT: token-lint OK: GROUP-A/GROUP-B contract (A1/A2/A3) holds.
  EVIDENCE: automatic-evidence=v1; definition-sha256=01eb0790729ad5f627d4be9e85ef9d3ddc125f92852a0905ea9d8217fec286c9; exit=0; EXPECT=matched; output-sha256=c576eb087c276de3cf017a2f9f0df27b06fa6cf0f15d6418d922b255386e2645; output-bytes=117; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G4: owned files have no banned class token, no silent no-op class, no tag or legal comment, and the CSS census holds
  CHECK: node scripts/rebuild-rules.mjs 'src/components/promo/**' 'src/app/khuyen-mai/**' 'src/styles/areas/promo.css' && node scripts/tw-unknown-classes.mjs 'src/components/promo/**' 'src/app/khuyen-mai/**' 'src/styles/areas/promo.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=24901e9224f1eae96a1fa6615389160ee8cb554fa3a398b0ac74b746c20d8e6f; exit=0; EXPECT=matched; output-sha256=1a7bc92d090dd0160356a6a6acdcbaa533ba371bc547aa4df2997ee160cf667f; output-bytes=68; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/S8.sh
  EXPECT: CHECKS OK S8
  EVIDENCE: automatic-evidence=v1; definition-sha256=792044382888cc892e4b7b64178fe41308086d0ef3a50e7a0c47b528c9f3a950; exit=0; EXPECT=matched; output-sha256=5d86e458992542a9d94c4acd73b3d5fcd3669a9fe59ef0233c3cfff61700f281; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-S8.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=d1f2bdfaac91acf30f9fd60d7dbcaba74e38c2d3c1a87f24569bce37c594296f; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: routes answer as the inventory says, on this leaf's own dev server
  CHECK: node scripts/with-dev-server.mjs --port 3128 -- node scripts/verify-routes.mjs --base http://localhost:3128 --only /khuyen-mai,/khuyen-mai/pr1,/khuyen-mai/pr2,/khuyen-mai/pr3,/khuyen-mai/pr4,/khuyen-mai/pr5,/khuyen-mai/pr6,/khuyen-mai/pr7,/khuyen-mai/pr8,/khuyen-mai/pr9
  EXPECT: ROUTES OK 10/10
  EVIDENCE: automatic-evidence=v1; definition-sha256=b63bf0503dc0a4fba24d3332b904f64710eb97b5235ef16551945d370dbd3f5d; exit=0; EXPECT=matched; output-sha256=ebd31dadb27d94c6634b2404d20f154c787b7b68e5b8b96cea8eb59d8b02a49d; output-bytes=317; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh S8
  EXPECT: LEASE OK S8
  EVIDENCE: rc=0 LEASE OK S8 7 paths. PM back-fill fresh at wt rb-S8@c6c50e7 base=5f71109 (scratchpad bf/S8-G8.out), run on main c1c9a08.

- [x] G9: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: 2026-11-05 frontend-qc PASS, 0 Fails. TSX code_equal True for the 6 files (33 class refs, 0 unmapped); barrel order equal; promo.css reverse-mapped diff rc=0 against the 4 original sheets; rename map 31 classes, bijection, no collisions, 31 used = 31 declared; D3 SH-21, SH-22, SH-29, SH-32 reproduced (promo.svg sha256 equal); rebuild-rules RULES OK 7, tw-unknown-classes CLASSES OK 31, compiled-qc PASS. FIX-LIST: PromoGrid.tsx:81 badge repeat, :85 timer box in tile, PromoDetail.tsx:56,65 aria-label vs h2, :30 member CTA no-op, promo.css:79-82 hover without hover media, khuyen-mai/page.tsx:24 no error state, PromoGrid.tsx:77 title clamp.

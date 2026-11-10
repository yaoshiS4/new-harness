# Gates: S6 home route

OWNS: src/components/home/ProviderGameGrid.tsx, src/components/home/SportsLifestyle.tsx, src/components/home/SportsMatchCard.tsx, src/components/home/index.ts, src/app/page.tsx, src/app/loading.tsx, src/styles/areas/home.css

Wave: W8b · Needs (merged before dispatch): F5, S3, S5 · Dev-server port: 3126

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/components/home/ProviderGameGrid.tsx
  - src/components/home/SportsLifestyle.tsx
  - src/components/home/SportsMatchCard.tsx
  - src/components/home/index.ts
  - src/app/page.tsx
  - src/app/loading.tsx
  - src/styles/areas/home.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `L6 home-route-grid` row in `docs/rebuild/review/shell-home.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/S6.sh` (PM-authored; never edit it).

Leaf notes: `index.ts` keeps the original barrel minus the export lines of the 8 dead bands (PR-19, PR-34). `home.css` passes from S5 (W7): append only. F0 already removed the deletions this row lists. The 1440 filler count runs in I1 (box-check).

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
  CHECK: node scripts/rebuild-rules.mjs 'src/components/home/ProviderGameGrid.tsx' 'src/components/home/SportsLifestyle.tsx' 'src/components/home/SportsMatchCard.tsx' 'src/components/home/index.ts' 'src/app/page.tsx' 'src/app/loading.tsx' 'src/styles/areas/home.css' && node scripts/tw-unknown-classes.mjs 'src/components/home/ProviderGameGrid.tsx' 'src/components/home/SportsLifestyle.tsx' 'src/components/home/SportsMatchCard.tsx' 'src/components/home/index.ts' 'src/app/page.tsx' 'src/app/loading.tsx' 'src/styles/areas/home.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=1eb821238f206424967ab21371438e6de7e3b913b841bfc42beaf40db6ea2fb1; exit=0; EXPECT=matched; output-sha256=2d138f113eb349ef1d198a7529d8f31c4253d2e0e365c652b4c60e75a8d0e695; output-bytes=68; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/S6.sh
  EXPECT: CHECKS OK S6
  EVIDENCE: automatic-evidence=v1; definition-sha256=e9aa4569ece7233f607257c94695fb2e4b3ef80e84c77186ed352179ff8db1f5; exit=0; EXPECT=matched; output-sha256=dfd239b4f83a9630e96f435f82b0c3a8f13b8d2cfbc60708cd1cdebf852b40e3; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-S6.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=9a2612a10f98f6ac9bd564c979d874cbdc5dc4628adc5e9a89ccf1dab088df60; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: routes answer as the inventory says, on this leaf's own dev server
  CHECK: node scripts/with-dev-server.mjs --port 3126 -- node scripts/verify-routes.mjs --base http://localhost:3126 --only /
  EXPECT: ROUTES OK 1/1
  EVIDENCE: automatic-evidence=v1; definition-sha256=c596beebc2934f5c890c158b91aa67ef2d6a097e29fba39d3ec9691be7d3ecd1; exit=0; EXPECT=matched; output-sha256=ca160b27d63120691ec88a6c370eb7e8e921f5eaaf5bc311a8fbc078fed1bca5; output-bytes=98; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh S6
  EXPECT: LEASE OK S6
  EVIDENCE: rc=0 LEASE OK S6 7 paths. PM back-fill fresh at wt rb-S6@5e21d6d base=8b78b53 (scratchpad bf/S6-G8.out), run on main c1c9a08.

- [x] G9: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: 2026-11-05 frontend-qc PASS on rb-S6 at 5e21d6d (merged c93c61e): 0 code-diff lines, 34-class bijection; D3 SH-15, SH-17, SH-18, SH-24, SH-19, SH-01 reproduced; comment-only rewording accepted by the PM at the time (prompt-qc-S6.md).

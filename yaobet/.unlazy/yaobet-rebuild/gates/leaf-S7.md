# Gates: S7 vertical route

OWNS: src/components/category/**, src/app/[vertical]/**, src/styles/areas/vertical.css

Wave: W9 · Needs (merged before dispatch): F5, S6 · Dev-server port: 3127

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/components/category/**
  - src/app/[vertical]/**
  - src/styles/areas/vertical.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `L7 vertical-route` row in `docs/rebuild/review/shell-home.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/S7.sh` (PM-authored; never edit it).

Leaf notes: Path parity (PR-05): the folders are `src/components/layout` and `src/components/category`. shell-home §5 G-02, ADR-SH-01 and every `components/shell|vertical` or `src/styles/components/` path in shell-home §7 are superseded (ADR-002 §6). 

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
  CHECK: node scripts/rebuild-rules.mjs 'src/components/category/**' 'src/app/[vertical]/**' 'src/styles/areas/vertical.css' && node scripts/tw-unknown-classes.mjs 'src/components/category/**' 'src/app/[vertical]/**' 'src/styles/areas/vertical.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=40082573c3bdd4df096b176feb55f405f9b31e23bbdfe9c1d41108a11f78a8d7; exit=0; EXPECT=matched; output-sha256=2580d0a8bc6c1be1614bd34154b914d469cdfc1bc3f72e8f91f2c1928fd05e41; output-bytes=69; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/S7.sh
  EXPECT: CHECKS OK S7
  EVIDENCE: automatic-evidence=v1; definition-sha256=21031b57ae655b71dadabbd1aec8992ef5e4c122e7b780e17c3089f71a5d26f6; exit=0; EXPECT=matched; output-sha256=1565e26a99ac68c863e45d941e597c3ddadd0eb4f7bc27203e47077ab9fabc4f; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-S7.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=1d406c3f817c4aade52ff1ada09917b4cf76835c476be2ff34bb9db6d75c0505; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: routes answer as the inventory says, on this leaf's own dev server
  CHECK: node scripts/with-dev-server.mjs --port 3127 -- node scripts/verify-routes.mjs --base http://localhost:3127 --only /casino,/slots,/sports,/fishing,/card,/lottery,/cockfight,/table,/arcade,/foo
  EXPECT: ROUTES OK 10/10
  EVIDENCE: automatic-evidence=v1; definition-sha256=3d4278fbd74d4802dbc42121d5a9f4ebe97e0e2c102bef47a202d60291c0c338; exit=0; EXPECT=matched; output-sha256=fae7727f9a2aa0703ca2a1c7c08598978f10f336915828241c73c93f406801a8; output-bytes=239; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh S7
  EXPECT: LEASE OK S7
  EVIDENCE: rc=0 LEASE OK S7 10 paths. PM back-fill fresh at wt rb-S7@b299107 base=e1cc1ad (scratchpad bf/S7-G8.out), run on main c1c9a08.

- [x] G9: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: 2026-11-05 frontend-qc PASS, 0 Fails. TS-printer code diff of 9 files: only sheet-import removal and styles.x to literal classes; barrel equal; vertical.css reverse-mapped equal to the 5 original sheets (order confirmed from the original build chunks); rename map 38 classes (builder said 39), bijection, no collisions, CLASSES OK 38; D3 SH-19, SH-20, SH-25, SH-28 reproduced; rebuild-rules RULES OK 10. Two comment rewordings (reference-site art, final art) accepted per main Tile.tsx:3,5 precedent. FIX-LIST: CategoryGrid.tsx:93 same-page tap, CategoryBanner.tsx:34 icon map drift, :54,62 aria-label repeats h1, vertical.css:217-224 team-name ellipsis, loading.tsx:28 160px skeleton shift, LiveOddsBoard.tsx:70 no stale timer, vertical.css:79-90 placeholder 4.54:1, no route error.tsx, stale comments CategoryGrid.tsx:4 and vertical.css:36.

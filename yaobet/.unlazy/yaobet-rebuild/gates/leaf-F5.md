# Gates: F5 root layout

OWNS: src/app/layout.tsx, src/app/favicon.ico

Wave: W8 · Needs (merged before dispatch): F1, F2, S3, S5 · Dev-server port: 3125

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/app/layout.tsx
  - src/app/favicon.ico
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `F5 root-composition` row in `docs/rebuild/review/foundations-core.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/F5.sh` (PM-authored; never edit it).

Leaf notes: Byte-copy `favicon.ico` (25,931 bytes). F5 owns no page, so it has no route gate; its curl checks run in I1 and the capture `setState`/`checkState` check is part of A5. The PM runs the fonts preflight (G-fonts) before dispatch.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/app/layout.tsx' && node scripts/tw-unknown-classes.mjs 'src/app/layout.tsx' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=b799751dce219858b1810ae74b559039309c44509fd65f0cd709075e33418ce2; exit=0; EXPECT=matched; output-sha256=827bd47e8f4e789d20ee9cd491a9806a308665e16b2480e14f2cd67c349cc5b6; output-bytes=67; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/F5.sh
  EXPECT: CHECKS OK F5
  EVIDENCE: automatic-evidence=v1; definition-sha256=d121e10d4f0362d6d7dc9fa86d653f83aa4214f4d56295237a858219a62d7e6d; exit=0; EXPECT=matched; output-sha256=e96902df9d57758f680c0cb2c9912b55a440ea7e4875463c65c97c7718aa629a; output-bytes=17; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-F5.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=af84fa05c662603ca076fd7be22deec65ecdbc6ab2ef74b4440e4886447c4e28; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh F5
  EXPECT: LEASE OK F5
  EVIDENCE: rc=0 LEASE OK F5 2 paths. PM back-fill fresh at wt rb-F5@75ff1ad base=0905baf (scratchpad bf/F5-G7.out), run on main c1c9a08.

- [x] G8: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: 2026-11-05 frontend-qc PASS on rb-F5 at 75ff1ad (merged 8b78b53): 0 Fails; 4 comment-only diff lines vs the original; favicon byte-equal (25931 bytes); layout.tsx:11 "(§F)" kept (the ADR-002 TAG_RE has no § family).

# Gates: R5 store

OWNS: src/components/store/**, src/app/cua-hang/**, src/styles/areas/store.css

Wave: W13 · Needs (merged before dispatch): R1, F5 · Dev-server port: 3135

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/components/store/**
  - src/app/cua-hang/**
  - src/styles/areas/store.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `R5 store` row in `docs/rebuild/review/rewards.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/R5.sh` (PM-authored; never edit it).

Leaf notes: Reproduce the module-load cooldown timing (PR-04).

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
  CHECK: node scripts/rebuild-rules.mjs 'src/components/store/**' 'src/app/cua-hang/**' 'src/styles/areas/store.css' && node scripts/tw-unknown-classes.mjs 'src/components/store/**' 'src/app/cua-hang/**' 'src/styles/areas/store.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=e48a1e4f2f5dfea8d95519a33918ecf1406db789c8b6113d1fda9cc7d8b123a2; exit=0; EXPECT=matched; output-sha256=550112aa06526a7da1cbad998874018fca07a21995118777c6257ffd231a5c88; output-bytes=69; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/R5.sh
  EXPECT: CHECKS OK R5
  EVIDENCE: automatic-evidence=v1; definition-sha256=004a8d134034c1bd2ee8efe901f465db24f6aa01f5054616e78a005aa3c71ad9; exit=0; EXPECT=matched; output-sha256=0a3b042890f67d0609eb2b36e55ebff8796c786ceb8a362ba09baae0cadfbddf; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-R5.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=6dbeca0a0027882da38a4beb07deea8a513f2faf924244e20659f3702d052739; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: routes answer as the inventory says, on this leaf's own dev server
  CHECK: node scripts/with-dev-server.mjs --port 3135 -- node scripts/verify-routes.mjs --base http://localhost:3135 --only /cua-hang
  EXPECT: ROUTES OK 1/1
  EVIDENCE: automatic-evidence=v1; definition-sha256=b60a3eb24384177872caa53cd795ce8a42110ffd2546f9769a39871ad8555a49; exit=0; EXPECT=matched; output-sha256=c44c3e12d6da6824aa6af1f5a4775fed8e44bcf27643c56da614ceb8919b5e91; output-bytes=106; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh R5
  EXPECT: LEASE OK R5
  EVIDENCE: rc=0 LEASE OK R5 8 paths. PM Stage A fresh on rb-R5 at 1444c70 (scratchpad stageA-R5.out), STAGE_A rc=0 checks=8.

- [x] G9: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: frontend-qc PASS at 1444c70, 0 Fails: TSX token streams match the original for 7/7 files (ProductCard differs only by a line break); CSS equivalence verified in the built chunk (tab hover 0,2,0 beats active, grid 2/3/4 columns, store.css selectors, specificity and order 1:1 incl. both reduced-motion blocks); adjudications: data-* selectors and their base rules in store.css allowed (ADR-002 §2, PR-02, layer order), sold-out and cost-row flattenings identical, per-side callout border identical; D3 REWARDS-16..19 reproduced; comment drops limited to tag tokens, SPEC refs, Wave 7.1 and the regulatory word Compliance (PR-31); six anti-slop and a11y items sent to FIX-LIST.

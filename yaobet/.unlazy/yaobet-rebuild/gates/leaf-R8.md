# Gates: R8 collection mine and dev ports

OWNS: src/components/collection/MyCards.tsx, src/components/collection/CardDetail.tsx, src/app/bo-suu-tap/cua-toi/**, src/app/dev/collection-ports/**, src/styles/areas/collection.css

Wave: W15 · Needs (merged before dispatch): R7 · Dev-server port: 3139

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/components/collection/MyCards.tsx
  - src/components/collection/CardDetail.tsx
  - src/app/bo-suu-tap/cua-toi/**
  - src/app/dev/collection-ports/**
  - src/styles/areas/collection.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `R8 collection-mine-dev` row in `docs/rebuild/review/rewards.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/R8.sh` (PM-authored; never edit it).

Leaf notes: `collection.css` passes from R7 (W14): append only. `dev/collection-ports/page.tsx` renders tag tokens in its copy: see PR-32 (ruled: ported verbatim and listed in `checks/a11-allow.txt`).

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
  CHECK: node scripts/rebuild-rules.mjs 'src/components/collection/MyCards.tsx' 'src/components/collection/CardDetail.tsx' 'src/app/bo-suu-tap/cua-toi/**' 'src/app/dev/collection-ports/**' 'src/styles/areas/collection.css' && node scripts/tw-unknown-classes.mjs 'src/components/collection/MyCards.tsx' 'src/components/collection/CardDetail.tsx' 'src/app/bo-suu-tap/cua-toi/**' 'src/app/dev/collection-ports/**' 'src/styles/areas/collection.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=180bf8f27411b0b49b320d4b02e3070ed4501b9518f61d7819b9954d28561e40; exit=0; EXPECT=matched; output-sha256=78986aba6cbdbe5902f1ceffda3a3f9ddea798d14bd337c930ef28572da641df; output-bytes=69; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/R8.sh
  EXPECT: CHECKS OK R8
  EVIDENCE: automatic-evidence=v1; definition-sha256=5a883922c3a34480e621b5f068efa0ac2506ffacc00e633def15cf9e9072d5ba; exit=0; EXPECT=matched; output-sha256=7945f30071c31a829db58595e6d7af4df4818e45f96b3ffd3d89d804e27e9057; output-bytes=17; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-R8.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=3b7494a32fae5eb000baab5a5865d79e7594589bb996c00eabcdea4f856d7200; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: routes answer as the inventory says, on this leaf's own dev server
  CHECK: node scripts/with-dev-server.mjs --port 3139 -- node scripts/verify-routes.mjs --base http://localhost:3139 --only /bo-suu-tap/cua-toi,/dev/collection-ports
  EXPECT: ROUTES OK 2/2
  EVIDENCE: automatic-evidence=v1; definition-sha256=df327bf099a004d59bb4433848abea14991b03a60144c3d9110218718427b256; exit=0; EXPECT=matched; output-sha256=133056b7df6c4d57f500919fb06274ba3546564837b7e44a26147b9ff8d3b432; output-bytes=145; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh R8
  EXPECT: LEASE OK R8
  EVIDENCE: rc=0 LEASE OK R8 5 paths. PM Stage A fresh on rb-R8 at ba5351e (scratchpad stageA-R8.out), STAGE_A rc=0 checks=8.

- [x] G9: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: frontend-qc PASS at ba5351e (round 1 at d953d59 failed on 4 whole-comment drops only; fixed in ba5351e, comment-only; code, CSS, D3, a11y and ?tab=lich-su verified)

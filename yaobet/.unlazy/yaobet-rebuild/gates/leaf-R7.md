# Gates: R7 collection surface

OWNS: src/components/collection/CollectionApp.tsx, src/components/collection/PackStage.tsx, src/components/collection/CardArt.tsx, src/components/collection/RewardCeremony.tsx, src/components/collection/CollectionTerms.tsx, src/components/collection/CollectionHistory.tsx, src/app/bo-suu-tap/page.tsx, src/app/bo-suu-tap/CollectionRoot.tsx, src/styles/areas/collection.css

Wave: W14 · Needs (merged before dispatch): R2, S1, F5 · Dev-server port: 3137

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/components/collection/CollectionApp.tsx
  - src/components/collection/PackStage.tsx
  - src/components/collection/CardArt.tsx
  - src/components/collection/RewardCeremony.tsx
  - src/components/collection/CollectionTerms.tsx
  - src/components/collection/CollectionHistory.tsx
  - src/app/bo-suu-tap/page.tsx
  - src/app/bo-suu-tap/CollectionRoot.tsx
  - src/styles/areas/collection.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `R7 collection-surface` row in `docs/rebuild/review/rewards.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/R7.sh` (PM-authored; never edit it).

Leaf notes: CardArt's `sweep` becomes `card-foil-sweep`; every other keyframe keeps its guide name (PR-29).

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
  CHECK: node scripts/rebuild-rules.mjs 'src/components/collection/CollectionApp.tsx' 'src/components/collection/PackStage.tsx' 'src/components/collection/CardArt.tsx' 'src/components/collection/RewardCeremony.tsx' 'src/components/collection/CollectionTerms.tsx' 'src/components/collection/CollectionHistory.tsx' 'src/app/bo-suu-tap/page.tsx' 'src/app/bo-suu-tap/CollectionRoot.tsx' 'src/styles/areas/collection.css' && node scripts/tw-unknown-classes.mjs 'src/components/collection/CollectionApp.tsx' 'src/components/collection/PackStage.tsx' 'src/components/collection/CardArt.tsx' 'src/components/collection/RewardCeremony.tsx' 'src/components/collection/CollectionTerms.tsx' 'src/components/collection/CollectionHistory.tsx' 'src/app/bo-suu-tap/page.tsx' 'src/app/bo-suu-tap/CollectionRoot.tsx' 'src/styles/areas/collection.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=23dcba31a266fed9c66e05fbc58f47fd7a2effe2a47f9a4c7da97f13e72d2fb2; exit=0; EXPECT=matched; output-sha256=914c37eb82c9ea08aa6fa4034491de2033a4b89f8d1ac305eebad939db6c0fe1; output-bytes=69; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/R7.sh
  EXPECT: CHECKS OK R7
  EVIDENCE: automatic-evidence=v1; definition-sha256=c67712d026c9b68bc83c556f5ab2faef05551c2e75aa523ef628e3ea4b1a84de; exit=0; EXPECT=matched; output-sha256=ce8d1676eee391b7cd3a38cd32052b40c9c9c01282f22ea19ed54c77906167a2; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-R7.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=2b38fe9d291683e59ceb7e0ea7f5a3da106ed7db77ee14adc04f034d41f0346e; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: routes answer as the inventory says, on this leaf's own dev server
  CHECK: node scripts/with-dev-server.mjs --port 3137 -- node scripts/verify-routes.mjs --base http://localhost:3137 --only /bo-suu-tap
  EXPECT: ROUTES OK 1/1
  EVIDENCE: automatic-evidence=v1; definition-sha256=389d9ccd4afa70ff16bf15ce277c71221d35515f8e363d50d42cf00ca57a3f6f; exit=0; EXPECT=matched; output-sha256=d230de91df214df477e958255759849e1630a24b6785acd28d58fa19bd3d9d43; output-bytes=108; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh R7
  EXPECT: LEASE OK R7
  EVIDENCE: rc=0 LEASE OK R7 9 paths. PM Stage A fresh on rb-R7 at b0833c1 (scratchpad stageA-R7.out), STAGE_A rc=0 checks=8.

- [x] G9: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: PASS. frontend-qc G9 on rb-R7: round 1 at 271de69 passed TSX fidelity, CSS equivalence, D3 (REWARDS-23, -27..-31) and anti-slop, failed on reworded comments; fixed in 55821fd and b0833c1; re-check at b0833c1 PASS (code unchanged after stripping comments, 146 comments mapped, every difference a tag or regulatory deletion, headers verbatim, no tags). FIX-LIST candidates in the scratchpad file fixlist-candidates.md under R7.

# Gates: F3a mock data 1

OWNS: src/lib/mock/helpers.ts, src/lib/mock/types.ts, src/lib/mock/lobby.ts, src/lib/mock/games.ts, src/lib/mock/vip.ts, src/lib/mock/wallet.ts, src/lib/mock/promos.ts, src/lib/mock/store.ts, src/lib/mock/referral.ts, src/lib/mock/cashback.ts

Wave: W2 · Needs (merged before dispatch): F2 · Dev-server port: 3113

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/lib/mock/helpers.ts
  - src/lib/mock/types.ts
  - src/lib/mock/lobby.ts
  - src/lib/mock/games.ts
  - src/lib/mock/vip.ts
  - src/lib/mock/wallet.ts
  - src/lib/mock/promos.ts
  - src/lib/mock/store.ts
  - src/lib/mock/referral.ts
  - src/lib/mock/cashback.ts
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `F3a mock-data-1` row in `docs/rebuild/review/foundations-core.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/F3a.sh` (PM-authored; never edit it).

Leaf notes: Comments: PR-27, PR-31.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/lib/mock/helpers.ts' 'src/lib/mock/types.ts' 'src/lib/mock/lobby.ts' 'src/lib/mock/games.ts' 'src/lib/mock/vip.ts' 'src/lib/mock/wallet.ts' 'src/lib/mock/promos.ts' 'src/lib/mock/store.ts' 'src/lib/mock/referral.ts' 'src/lib/mock/cashback.ts' && node scripts/tw-unknown-classes.mjs 'src/lib/mock/helpers.ts' 'src/lib/mock/types.ts' 'src/lib/mock/lobby.ts' 'src/lib/mock/games.ts' 'src/lib/mock/vip.ts' 'src/lib/mock/wallet.ts' 'src/lib/mock/promos.ts' 'src/lib/mock/store.ts' 'src/lib/mock/referral.ts' 'src/lib/mock/cashback.ts' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=9e13d30194f16eaadc64cfa43c221ea699a68634a9c6887f72b141510a115169; exit=0; EXPECT=matched; output-sha256=602c8280dfbe17fc54481e419ec3661e9cd58929a20d4793e6377e31430eccca; output-bytes=68; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/F3a.sh
  EXPECT: CHECKS OK F3a
  EVIDENCE: automatic-evidence=v1; definition-sha256=2b6456fd27f0be4bd7d4576e0a54c0b903064839fe70718bc08421370ebdd62c; exit=0; EXPECT=matched; output-sha256=2dd9ec3035443bd755c0aad22373cd38f2825abd767550d789e94b6c9618e3ef; output-bytes=18; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh F3a
  EXPECT: LEASE OK F3a
  EVIDENCE: rc=0 LEASE OK F3a 10 paths. PM back-fill fresh at wt rb-F3a@0df3970 base=fe17fc5 (scratchpad bf/F3a-G6.out), run on main c1c9a08.

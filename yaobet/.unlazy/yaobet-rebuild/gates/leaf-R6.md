# Gates: R6 lottery

OWNS: src/components/lottery/**, src/app/ve-so/**, src/styles/areas/lottery.css

Wave: W13 · Needs (merged before dispatch): F3b, S1, F5 · Dev-server port: 3136

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/components/lottery/**
  - src/app/ve-so/**
  - src/styles/areas/lottery.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `R6 lottery` row in `docs/rebuild/review/rewards.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/R6.sh` (PM-authored; never edit it).

Leaf notes: The canvas reads `--brand-accent`, `--brand-accent-2`, `--canvas` and `--text-hi` (PR-13). The manual canvas erase check is part of A8.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/components/lottery/**' 'src/app/ve-so/**' 'src/styles/areas/lottery.css' && node scripts/tw-unknown-classes.mjs 'src/components/lottery/**' 'src/app/ve-so/**' 'src/styles/areas/lottery.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=752d5698cf00bc88b0a7fba4d708513d1fbf149af4d2e5da5a3656e148298465; exit=0; EXPECT=matched; output-sha256=f0b83225018bae6c88b24fa31a5c4c9ef8dbd45f589fae1370077984f8716dcf; output-bytes=69; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/R6.sh
  EXPECT: CHECKS OK R6
  EVIDENCE: automatic-evidence=v1; definition-sha256=935df9bcb546b55303514c09bd4c1f011accb260a85ce4c5a745707e047dabd6; exit=0; EXPECT=matched; output-sha256=2628571dfc308c1c3b6d19bcfdad3134c402f9eeddb442027a14a1e9366b9afb; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-R6.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=7aa6160fd20b0bf799705f34030a773c1c16ea5ecf3d5cd9290a346d90a2ab68; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: routes answer as the inventory says, on this leaf's own dev server
  CHECK: node scripts/with-dev-server.mjs --port 3136 -- node scripts/verify-routes.mjs --base http://localhost:3136 --only /ve-so
  EXPECT: ROUTES OK 1/1
  EVIDENCE: automatic-evidence=v1; definition-sha256=663bfd0a82e94f0394656ccb4a4fbc6190b863a37f2600b64c742728692d66d3; exit=0; EXPECT=matched; output-sha256=4131ec327528a5ef94c20b67464324c4dd2fc2fea0c930f527b6d2d8fe45958b; output-bytes=103; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh R6
  EXPECT: LEASE OK R6
  EVIDENCE: rc=0 LEASE OK R6 8 paths. PM Stage A fresh on rb-R6 at 1520048 (scratchpad stageA-R6.out), STAGE_A rc=0 checks=8.

- [x] G9: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: PASS (frontend-qc, read-only, at 1520048): no Fails. TSX/TS fidelity holds (page.tsx and coverArt.ts byte-identical; CLEAR_THRESHOLD 0.58; PR-13 token reads; PR-42 eslint-disable on the original statement). CSS equivalence identical for OutcomeFrame, ScratchSurface, ScratchCardGame, LotteryRoot (194 utilities + 61 lottery.css rules from the build CSS). Adjudications: data states as lottery.css selectors per ADR-002 section 2 and PR-02; font:inherit omission OK, all four elements are buttons reached by reset.css. D3: REWARDS-20 and REWARDS-22 reproduced in lease; REWARDS-21 is lib. FIX-LIST candidates recorded by the PM.

# Gates: S5 home bands and DEV toggle

OWNS: src/components/home/HeroBand.tsx, src/components/home/CategoryLauncher.tsx, src/components/home/StatsBar.tsx, src/components/home/DevAuthToggle.tsx, src/styles/areas/home.css

Wave: W7 · Needs (merged before dispatch): S1, U2 · Dev-server port: 3124

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/components/home/HeroBand.tsx
  - src/components/home/CategoryLauncher.tsx
  - src/components/home/StatsBar.tsx
  - src/components/home/DevAuthToggle.tsx
  - src/styles/areas/home.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `L5 home-bands` row in `docs/rebuild/review/shell-home.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/S5.sh` (PM-authored; never edit it).

Leaf notes: There is no `Home.tsx` (PR-33): the original `Home.module.css` becomes classes in `home.css`, used directly by `app/page.tsx` and `app/loading.tsx` (S6). DevAuthToggle follows foundations-core §3.9 and PR-08. The prod/dev toggle checks run in I1.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/components/home/HeroBand.tsx' 'src/components/home/CategoryLauncher.tsx' 'src/components/home/StatsBar.tsx' 'src/components/home/DevAuthToggle.tsx' 'src/styles/areas/home.css' && node scripts/tw-unknown-classes.mjs 'src/components/home/HeroBand.tsx' 'src/components/home/CategoryLauncher.tsx' 'src/components/home/StatsBar.tsx' 'src/components/home/DevAuthToggle.tsx' 'src/styles/areas/home.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=7f3d5055724b61b4c4a1ade4e038fb91ff95275b8104dbaf37e52435de259a8e; exit=0; EXPECT=matched; output-sha256=bf75fa9d11a91ecb3bfb96f51aaf9dad53f1eaf239dc516e370905e2178bfeb4; output-bytes=68; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/S5.sh
  EXPECT: CHECKS OK S5
  EVIDENCE: automatic-evidence=v1; definition-sha256=9c5c6ff4e221e25f0b78f345294b1f0542ea32069e12c07e8012d14d9517477b; exit=0; EXPECT=matched; output-sha256=170ae72a5b0ecf92e1cac9be46640f7bcff48e05685172acab93f08cd6183789; output-bytes=17; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh S5
  EXPECT: LEASE OK S5
  EVIDENCE: rc=0 LEASE OK S5 5 paths. PM back-fill fresh at wt rb-S5@f79b186 base=d4e0e2b (scratchpad bf/S5-G6.out), run on main c1c9a08.

- [x] G7: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: 2026-11-05 frontend-qc PASS on rb-S5 at f79b186 (merged a5385f9): 82/82 rules, 39/39 class bijection (scratchpad qcS5/).

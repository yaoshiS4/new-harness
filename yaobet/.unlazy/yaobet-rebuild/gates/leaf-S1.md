# Gates: S1 shell internals

OWNS: src/components/layout/_internal/**, src/styles/areas/shell.css

Wave: W5 · Needs (merged before dispatch): U1, F3b · Dev-server port: 3120

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/components/layout/_internal/**
  - src/styles/areas/shell.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `L1 shell-internal` row in `docs/rebuild/review/shell-home.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/S1.sh` (PM-authored; never edit it).

Leaf notes: Path parity (PR-05): the folders are `src/components/layout` and `src/components/category`. shell-home §5 G-02, ADR-SH-01 and every `components/shell|vertical` or `src/styles/components/` path in shell-home §7 are superseded (ADR-002 §6). All 8 shell keyframes keep their guide names (PR-29) and live in `shell.css`.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/components/layout/_internal/**' 'src/styles/areas/shell.css' && node scripts/tw-unknown-classes.mjs 'src/components/layout/_internal/**' 'src/styles/areas/shell.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=a2c53a281247afcfaa61785bca04b22dcf432038a191eae4d939d9b9916a3298; exit=0; EXPECT=matched; output-sha256=d99342f9198dd357d924bab345b87ad8358a2ccaadd59732b5636c9c856a520b; output-bytes=68; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/S1.sh
  EXPECT: CHECKS OK S1
  EVIDENCE: automatic-evidence=v1; definition-sha256=67e8e722f0593c06d35944f430295da276f9fccd86d490e4dff7062a02c9042f; exit=0; EXPECT=matched; output-sha256=ba227c6b0a8608a1470cb684977b2aca06606a13870b122c656858d71f62da56; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh S1
  EXPECT: LEASE OK S1
  EVIDENCE: rc=0 LEASE OK S1 8 paths. PM back-fill fresh at wt rb-S1@84fb216 base=1bff569 (scratchpad bf/S1-G6.out), run on main c1c9a08.

- [x] G7: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: 2026-11-05 frontend-qc PASS on rb-S1 at 84fb216 (merged 787ca68): 34/34 rules, 23/23 classes, 8/8 keyframes equal to the original sheets (scratchpad qcS1/).

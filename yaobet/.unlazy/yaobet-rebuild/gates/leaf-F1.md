# Gates: F1 styles foundation

OWNS: src/app/globals.css, src/styles/**, src/ui/ui.css

Wave: W1 · Needs (merged before dispatch): F0 · Dev-server port: 3111

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/app/globals.css
  - src/styles/**
  - src/ui/ui.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `F1 styles-foundation` row in `docs/rebuild/review/foundations-core.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/F1.sh` (PM-authored; never edit it).

Leaf notes: ADR-002 §1 is the exact import list. Create `src/ui/ui.css` and the 10 `src/styles/areas/*.css` as empty files. `src/styles/stub.css` replaces the original `src/app/stub.module.css` (PR-33). Custom variants per PR-16. The 7 `ui-*` keyframes go in `src/styles/keyframes.css` (PR-18). The built-CSS checks of this row run in I1.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/app/globals.css' 'src/styles/**' 'src/ui/ui.css' && node scripts/tw-unknown-classes.mjs 'src/app/globals.css' 'src/styles/**' 'src/ui/ui.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=8c06740b14dc0b4604a81d8af6a67e76a714bd052c34422cb6b6b87fd2347e2c; exit=0; EXPECT=matched; output-sha256=afcfd14a6f762ec1157601192993c855bb11a0e517017fa1ad866c7ad13a43f8; output-bytes=68; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/F1.sh
  EXPECT: CHECKS OK F1
  EVIDENCE: automatic-evidence=v1; definition-sha256=8c5a025eb5f6af1c527238225508d3a950772bfbb905f693fd6f97635ca97424; exit=0; EXPECT=matched; output-sha256=cc637d07a6045651949dc1e1b93a0b787fff6101678ea6c86624fcd509b6bce0; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh F1
  EXPECT: LEASE OK F1
  EVIDENCE: rc=0 LEASE OK F1 21 paths. PM back-fill fresh at wt rb-F1@bf3e9d1 base=87563bb (scratchpad bf/F1-G6.out), run on main c1c9a08.

- [x] G7: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: 2026-11-06 frontend-qc PASS round 3 on rb-F1fix at c9f009b (merged ce40546), after round 1 on main c1c9a08 and round 2 at ee5622d failed only on reworded comments: code byte-exact to the original for all sheets with one, 163/163 token values, keyframes, states and globals.css unchanged; every differing comment line is a tag-token or legal-word deletion only; F1.sh 24/24. Outputs scratchpad qcF1/, qcF1b/, qcF1c/.

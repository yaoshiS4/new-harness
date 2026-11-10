# Gates: U2 ui composite, overlays, barrel

OWNS: src/ui/ui.css, src/ui/EmptyState/**, src/ui/ErrorState/**, src/ui/Countdown/**, src/ui/Odometer/**, src/ui/Scroller/**, src/ui/Tabs/**, src/ui/Tile/**, src/ui/Modal/**, src/ui/Sheet/**, src/ui/Dropdown/**, src/ui/index.ts

Wave: W5 · Needs (merged before dispatch): U1 · Dev-server port: 3119

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/ui/ui.css
  - src/ui/EmptyState/**
  - src/ui/ErrorState/**
  - src/ui/Countdown/**
  - src/ui/Odometer/**
  - src/ui/Scroller/**
  - src/ui/Tabs/**
  - src/ui/Tile/**
  - src/ui/Modal/**
  - src/ui/Sheet/**
  - src/ui/Dropdown/**
  - src/ui/index.ts
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `UIM-L2 ui-composite` row in `docs/rebuild/review/ui-member.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/U2.sh` (PM-authored; never edit it).

Leaf notes: `src/ui/ui.css` passes from U1 (W4) to U2 (W5): append the composite rules below U1's. Primitive keyframes are never redeclared (PR-18).

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
  CHECK: node scripts/rebuild-rules.mjs 'src/ui/ui.css' 'src/ui/EmptyState/**' 'src/ui/ErrorState/**' 'src/ui/Countdown/**' 'src/ui/Odometer/**' 'src/ui/Scroller/**' 'src/ui/Tabs/**' 'src/ui/Tile/**' 'src/ui/Modal/**' 'src/ui/Sheet/**' 'src/ui/Dropdown/**' 'src/ui/index.ts' && node scripts/tw-unknown-classes.mjs 'src/ui/ui.css' 'src/ui/EmptyState/**' 'src/ui/ErrorState/**' 'src/ui/Countdown/**' 'src/ui/Odometer/**' 'src/ui/Scroller/**' 'src/ui/Tabs/**' 'src/ui/Tile/**' 'src/ui/Modal/**' 'src/ui/Sheet/**' 'src/ui/Dropdown/**' 'src/ui/index.ts' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=6565c33dc06940a04f11e56530008217f837327d52987ac1e0b7173242199a1e; exit=0; EXPECT=matched; output-sha256=bb32869956276f97af14b1a736966f79bcc988a5015fe6aaf89ef8aa6d8fc87d; output-bytes=69; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/U2.sh
  EXPECT: CHECKS OK U2
  EVIDENCE: automatic-evidence=v1; definition-sha256=92153906ea067ee3a230b67de6ece3ce7ffe9d387f0dc6d37eccd3cd12e03a2d; exit=0; EXPECT=matched; output-sha256=0fddac43d0f9f4813bc78cbf18856ff9100f63a809acb9aeaa948ad39e5b7605; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh U2
  EXPECT: LEASE OK U2
  EVIDENCE: rc=0 LEASE OK U2 13 paths. PM back-fill fresh at wt rb-U2@0286b7a base=787ca68 (scratchpad bf/U2-G6.out), run on main c1c9a08.

- [x] G7: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: 2026-11-05 frontend-qc on rb-U2 at 0286b7a (merged 4c52dd0): the U2 lease files are faithful (91/91 rules, 67/67 classes, 11/11 keyframes, scratchpad qcU2/). Its one Fail was outside this lease: ui-slide-up media-scoped in keyframes.css (F1-owned), fixed by leaf KF1 (d2c9b56, merged e955416, lightningcss proof PASS: global, 7 keyframes, 0 @media).

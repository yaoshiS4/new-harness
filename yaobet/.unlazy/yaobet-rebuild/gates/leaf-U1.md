# Gates: U1 ui base primitives

OWNS: src/ui/ui.css, src/ui/Icon/**, src/ui/Badge/**, src/ui/Button/**, src/ui/Card/**, src/ui/Pill/**, src/ui/MoneyValue/**, src/ui/Skeleton/**

Wave: W4 · Needs (merged before dispatch): F1, F2 · Dev-server port: 3117

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/ui/ui.css
  - src/ui/Icon/**
  - src/ui/Badge/**
  - src/ui/Button/**
  - src/ui/Card/**
  - src/ui/Pill/**
  - src/ui/MoneyValue/**
  - src/ui/Skeleton/**
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `UIM-L1 ui-base` row in `docs/rebuild/review/ui-member.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/U1.sh` (PM-authored; never edit it).

Leaf notes: PR-15: base rules in `src/ui/ui.css`, plain class rules only, no `@layer` wrapper (ADR-002 §1). Write the base-primitive rules only; U2 appends the composite rules below them. The spinner uses `ui-spin 700ms linear infinite` (PR-18).

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
  CHECK: node scripts/rebuild-rules.mjs 'src/ui/ui.css' 'src/ui/Icon/**' 'src/ui/Badge/**' 'src/ui/Button/**' 'src/ui/Card/**' 'src/ui/Pill/**' 'src/ui/MoneyValue/**' 'src/ui/Skeleton/**' && node scripts/tw-unknown-classes.mjs 'src/ui/ui.css' 'src/ui/Icon/**' 'src/ui/Badge/**' 'src/ui/Button/**' 'src/ui/Card/**' 'src/ui/Pill/**' 'src/ui/MoneyValue/**' 'src/ui/Skeleton/**' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=d4052824cbdc08a3fe3ef5a48c27f26dbaf3e6c1ea9dd13676041e512b8ba0b9; exit=0; EXPECT=matched; output-sha256=780f075c6a4f245c7702dc041a66b770bee6d00937b344b3f46c8d5b0720d672; output-bytes=69; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/U1.sh
  EXPECT: CHECKS OK U1
  EVIDENCE: automatic-evidence=v1; definition-sha256=6ff1595d2cb31ff9e2fef05756de9bdf987c4a9b1922bae43844a7892b9d4817; exit=0; EXPECT=matched; output-sha256=eed5a8cae8c045260c9c17d902fcce49ffddc218807ed53621fee7ff07210b85; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh U1
  EXPECT: LEASE OK U1
  EVIDENCE: rc=0 LEASE OK U1 10 paths. PM back-fill fresh at wt rb-U1@35a61f3 base=5ef89ac (scratchpad bf/U1-G6.out), run on main c1c9a08.

- [x] G7: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: 2026-11-05 frontend-qc PASS on rb-U1 at 35a61f3 (merged 1bff569): tsx diffs only the dropped sheet import and styles.x to ui-* renames (ADR-002 §4, PR-15); 86/86 rules and 49/49 classes equal to the original sheets.

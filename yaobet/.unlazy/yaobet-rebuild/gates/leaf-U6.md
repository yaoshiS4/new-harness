# Gates: U6 contribution components

OWNS: src/components/contribution/**

Wave: W10 · Needs (merged before dispatch): U2, F3b · Dev-server port: 3129

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/components/contribution/**
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `UIM-L6 contribution` row in `docs/rebuild/review/ui-member.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/U6.sh` (PM-authored; never edit it).

Leaf notes: The noscript hooks of SearchField are an inline `<style>` with `data-*` selectors (ui-member G-5); no partial.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/components/contribution/**' && node scripts/tw-unknown-classes.mjs 'src/components/contribution/**' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=6fdc64b2d14f8070079e1d972b745e7d1a89f4bcfdf46bfd3131eef8706ca0b6; exit=0; EXPECT=matched; output-sha256=d35f3306075854d5bce1c4792850a0a7e89d2cce8977a691090ed1b33b160e90; output-bytes=70; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/U6.sh
  EXPECT: CHECKS OK U6
  EVIDENCE: automatic-evidence=v1; definition-sha256=1c10a2e7a96dc3cd23a09404ec885d527c2780a8298646525d757b36acbedfe3; exit=0; EXPECT=matched; output-sha256=389fabe3cc5170326658451bc27978016bc63ebe0c1181a161d54773eca0b38a; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-U6.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=438b1c8c59a47ce40c4ba6e441b81f1c402fa07b99076b8ce8eb8608cbd09f6d; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh U6
  EXPECT: LEASE OK U6
  EVIDENCE: rc=0 LEASE OK U6 14 paths. PM back-fill fresh at wt rb-U6@a350c83 base=178fb26 (scratchpad bf/U6-G7.out), run on main c1c9a08.

- [x] G8: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: 2026-11-06 frontend-qc PASS, 0 Fails (rb-U6 a350c83). Code-only diff: 12/14 identical, RateTable drops only the headRow class (folded onto th), SearchField adds only the G-5 data-* hooks; index.ts byte-equal. Per-element compiled CSS equals the original module cascade for all 13 components; zero values as [0] emit 0; no /NN, stock scale, group-hover. Noscript unlayered beats layered hidden. D3 UIM-53..58, 60 reproduced; UIM-57 "two lines" note was a CSS Module comment only, gone with the module, no rendered effect (PM accepts); UIM-55 Pill and UIM-59 i18n sit outside the lease; UIM-52 is U7's. Verbatim eslint-disable exhaustive-deps kept (PM decision, D1). rebuild-rules RULES OK 14, tw-unknown CLASSES OK 142. FIX-LIST candidates: RateTable.tsx:101-102 hover contrast 4.28:1; RateTable.tsx:96 flex th; RateFilters.tsx:69 ellipsis; Pager.tsx:63,81,95 + SearchField.tsx:149 ungated hover scale; SearchField.tsx:133 duplicate id; SearchField.tsx:138 border-only focus; ContributionRoot.tsx:310 no scroll on page change; ContributionRoot.tsx:276 count always shown; PageIntro.tsx:36 caveat self-link; NotFoundResolver.tsx:37 aria-pressed chips; RateTableSkeleton.tsx:42 skeleton shape.

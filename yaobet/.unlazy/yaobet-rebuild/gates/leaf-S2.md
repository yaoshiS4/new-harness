# Gates: S2 header and nav

OWNS: src/components/layout/Header.tsx, src/components/layout/MemberMenu.tsx, src/components/layout/NotificationBell.tsx, src/components/layout/BottomTabBar.tsx, src/components/layout/CategorySheet.tsx, src/styles/areas/shell.css

Wave: W6 · Needs (merged before dispatch): S1, U2 · Dev-server port: 3121

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/components/layout/Header.tsx
  - src/components/layout/MemberMenu.tsx
  - src/components/layout/NotificationBell.tsx
  - src/components/layout/BottomTabBar.tsx
  - src/components/layout/CategorySheet.tsx
  - src/styles/areas/shell.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `L2 shell-header-nav` row in `docs/rebuild/review/shell-home.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/S2.sh` (PM-authored; never edit it).

Leaf notes: Path parity (PR-05): the folders are `src/components/layout` and `src/components/category`. shell-home §5 G-02, ADR-SH-01 and every `components/shell|vertical` or `src/styles/components/` path in shell-home §7 are superseded (ADR-002 §6). Reproduce SH-02 (PR-09). `shell.css` passes from S1 (W5): append only. The curl and box checks of this row run in I1.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/components/layout/Header.tsx' 'src/components/layout/MemberMenu.tsx' 'src/components/layout/NotificationBell.tsx' 'src/components/layout/BottomTabBar.tsx' 'src/components/layout/CategorySheet.tsx' 'src/styles/areas/shell.css' && node scripts/tw-unknown-classes.mjs 'src/components/layout/Header.tsx' 'src/components/layout/MemberMenu.tsx' 'src/components/layout/NotificationBell.tsx' 'src/components/layout/BottomTabBar.tsx' 'src/components/layout/CategorySheet.tsx' 'src/styles/areas/shell.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=fa2e27bcacfb88bab3774994c7a4a366d0f753f125adb120adc9630193504109; exit=0; EXPECT=matched; output-sha256=6fc35867fae8e76faabdcfc5867ede9407f814fec8d6ca77fe143e029a4c6680; output-bytes=68; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/S2.sh
  EXPECT: CHECKS OK S2
  EVIDENCE: automatic-evidence=v1; definition-sha256=1be07bcc560c1a60b0f24f9f9ffb93cd73f28f747b9e9bff850be944be969c64; exit=0; EXPECT=matched; output-sha256=af86203aa9cf5aeddb02c75b020cbb77033d68993b4fa8d2b8b7baa8113807e5; output-bytes=17; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh S2
  EXPECT: LEASE OK S2
  EVIDENCE: rc=0 LEASE OK S2 6 paths. PM back-fill fresh at wt rb-S2@ffe3bd5 base=a5385f9 (scratchpad bf/S2-G6.out), run on main c1c9a08.

- [x] G7: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: 2026-11-05 frontend-qc PASS on rb-S2 at ffe3bd5 (merged e518566): 128/128 rules, 82/82 classes; original defects (Escape focus return, bell loading and error path, menu roles) routed to the FIX-LIST (scratchpad qcS2/).

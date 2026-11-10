# Gates: R4 vip tier and club

OWNS: src/components/vip/CurrentTierCard.tsx, src/components/vip/TierLadder.tsx, src/components/vip/PrivilegeTable.tsx, src/components/vip/PerkGallery.tsx, src/components/vip/VipRules.tsx, src/components/vip/VipSection.tsx, src/components/vip/copy.ts, src/components/vip/index.ts, src/app/tier/**, src/app/cau-lac-bo/**, src/styles/areas/vip.css

Wave: W14 · Needs (merged before dispatch): R3 · Dev-server port: 3138

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/components/vip/CurrentTierCard.tsx
  - src/components/vip/TierLadder.tsx
  - src/components/vip/PrivilegeTable.tsx
  - src/components/vip/PerkGallery.tsx
  - src/components/vip/VipRules.tsx
  - src/components/vip/VipSection.tsx
  - src/components/vip/copy.ts
  - src/components/vip/index.ts
  - src/app/tier/**
  - src/app/cau-lac-bo/**
  - src/styles/areas/vip.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `R4 vip-tier-club` row in `docs/rebuild/review/rewards.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/R4.sh` (PM-authored; never edit it).

Leaf notes: `/cau-lac-bo` uses F1's `stub-*` utilities (PR-33). The original `VipPage.module.css` (used only by `/tier`) becomes utilities or `vip.css` classes. `vip.css` passes from R3 (W12): append only.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/components/vip/CurrentTierCard.tsx' 'src/components/vip/TierLadder.tsx' 'src/components/vip/PrivilegeTable.tsx' 'src/components/vip/PerkGallery.tsx' 'src/components/vip/VipRules.tsx' 'src/components/vip/VipSection.tsx' 'src/components/vip/copy.ts' 'src/components/vip/index.ts' 'src/app/tier/**' 'src/app/cau-lac-bo/**' 'src/styles/areas/vip.css' && node scripts/tw-unknown-classes.mjs 'src/components/vip/CurrentTierCard.tsx' 'src/components/vip/TierLadder.tsx' 'src/components/vip/PrivilegeTable.tsx' 'src/components/vip/PerkGallery.tsx' 'src/components/vip/VipRules.tsx' 'src/components/vip/VipSection.tsx' 'src/components/vip/copy.ts' 'src/components/vip/index.ts' 'src/app/tier/**' 'src/app/cau-lac-bo/**' 'src/styles/areas/vip.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=e7687fb970a9c53279141ba4d72cfa59935f03d1073fbe96de367cf42442aaa5; exit=0; EXPECT=matched; output-sha256=dd9d4d6a0c2be4c95e25544694197459286761ec5a4479adc902bdc4e048d092; output-bytes=70; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/R4.sh
  EXPECT: CHECKS OK R4
  EVIDENCE: automatic-evidence=v1; definition-sha256=a53b66e1f05dae39ea9cc98ab7481817adaff66e7e64a204e3f556ecaf6bb853; exit=0; EXPECT=matched; output-sha256=1c24f7d839c53120c0e9b8c123f69045103134854d3714d37b84a9c3944b96ec; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-R4.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=9f1b6ddfcec310b33df759eb5d350fec58cd4bbbe5673478b09e3b16ad83c4e3; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: routes answer as the inventory says, on this leaf's own dev server
  CHECK: node scripts/with-dev-server.mjs --port 3138 -- node scripts/verify-routes.mjs --base http://localhost:3138 --only /tier,/cau-lac-bo
  EXPECT: ROUTES OK 2/2
  EVIDENCE: automatic-evidence=v1; definition-sha256=9a06c58403c5f059df331ecd557ec452fa57b8185c7ac8f506bac704dd3d7597; exit=0; EXPECT=matched; output-sha256=f82cef0468c0024086af4e5c492ee41093d830d52de3bd068bb43e3eb93ccff0; output-bytes=121; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh R4
  EXPECT: LEASE OK R4
  EVIDENCE: rc=0 LEASE OK R4 10 paths. PM Stage A fresh on rb-R4 at f2ae4e1 (scratchpad stageA-R4.out), STAGE_A rc=0 checks=8.

- [x] G9: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: PASS. frontend-qc G9 on rb-R4 at f2ae4e1: 10/10 files code-identical to the original after stripping comments and classNames, copy.ts byte-identical; build CSS equivalent per element and state (Scroller >div reaches the rail per src/ui/Scroller/Scroller.tsx:62-88; [&_button] matches :global(button) specificity); stub-* classes as in ho-tro (PR-33); vip.css unchanged; D3 REWARDS-05/12/13/14/15 reproduced; comments only tag and regulatory removals (TierLadder.tsx:4 'J9's' to 'the' accepted per merged precedent tokens.css:100, types.ts:136); restating utilities ruled value-identical; 0 Fails; 11 FIX-LIST items.

# Gates: R3 vip program

OWNS: src/components/vip/VipProgram.tsx, src/components/vip/VipSectionHeading.tsx, src/components/vip/VipHeroGuest.tsx, src/components/vip/VipHeroMember.tsx, src/components/vip/LevelRing.tsx, src/components/vip/TierDeck.tsx, src/components/vip/PrivilegeComparison.tsx, src/components/vip/PrivilegeMatrix.tsx, src/components/vip/LevelTable.tsx, src/components/vip/VipFaq.tsx, src/app/vip/**, src/styles/areas/vip.css

Wave: W12 · Needs (merged before dispatch): R1, F5 · Dev-server port: 3134

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/components/vip/VipProgram.tsx
  - src/components/vip/VipSectionHeading.tsx
  - src/components/vip/VipHeroGuest.tsx
  - src/components/vip/VipHeroMember.tsx
  - src/components/vip/LevelRing.tsx
  - src/components/vip/TierDeck.tsx
  - src/components/vip/PrivilegeComparison.tsx
  - src/components/vip/PrivilegeMatrix.tsx
  - src/components/vip/LevelTable.tsx
  - src/components/vip/VipFaq.tsx
  - src/app/vip/**
  - src/styles/areas/vip.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `R3 vip-program` row in `docs/rebuild/review/rewards.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/R3.sh` (PM-authored; never edit it).

Leaf notes: No `@utility` in `vip.css` (ADR-002 §1): rewards T8 becomes plain classes `.vip-hero-guest-bg` and `.vip-hero-member-bg`. The luxury palette comes from the F1 tokens; this leaf only applies them.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/components/vip/VipProgram.tsx' 'src/components/vip/VipSectionHeading.tsx' 'src/components/vip/VipHeroGuest.tsx' 'src/components/vip/VipHeroMember.tsx' 'src/components/vip/LevelRing.tsx' 'src/components/vip/TierDeck.tsx' 'src/components/vip/PrivilegeComparison.tsx' 'src/components/vip/PrivilegeMatrix.tsx' 'src/components/vip/LevelTable.tsx' 'src/components/vip/VipFaq.tsx' 'src/app/vip/**' 'src/styles/areas/vip.css' && node scripts/tw-unknown-classes.mjs 'src/components/vip/VipProgram.tsx' 'src/components/vip/VipSectionHeading.tsx' 'src/components/vip/VipHeroGuest.tsx' 'src/components/vip/VipHeroMember.tsx' 'src/components/vip/LevelRing.tsx' 'src/components/vip/TierDeck.tsx' 'src/components/vip/PrivilegeComparison.tsx' 'src/components/vip/PrivilegeMatrix.tsx' 'src/components/vip/LevelTable.tsx' 'src/components/vip/VipFaq.tsx' 'src/app/vip/**' 'src/styles/areas/vip.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=3fb724d3dc3b0fce187fa5977f8240a8bf3ba219a9ba677d463d0754f3826e24; exit=0; EXPECT=matched; output-sha256=fa0c7b589828b1841702aa40b129c181509d92942143bfb67adc464514be8f6d; output-bytes=70; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/R3.sh
  EXPECT: CHECKS OK R3
  EVIDENCE: automatic-evidence=v1; definition-sha256=4cc0a5fd06bdeb3a87d18d323c33807c8b7684e985d4904cce2f6c6e787324a2; exit=0; EXPECT=matched; output-sha256=d4fd514c434bd4f134a5812c5d503c67d176e367c11ecfc8d35d203bc63d2234; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-R3.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=5337587441b03af5237dba3e307fe4f57d1528778ef1656f1fbf1f258463ae13; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: routes answer as the inventory says, on this leaf's own dev server
  CHECK: node scripts/with-dev-server.mjs --port 3134 -- node scripts/verify-routes.mjs --base http://localhost:3134 --only /vip
  EXPECT: ROUTES OK 1/1
  EVIDENCE: automatic-evidence=v1; definition-sha256=03cb787393e0404ea200276a10cff50d06e67d1d9f1eed88e167aefdd6ff2a86; exit=0; EXPECT=matched; output-sha256=97a527cb26bd1b5dafc94ec826a9a4daaad9b9733a00fa4fcec71cd1e47872da; output-bytes=101; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh R3
  EXPECT: LEASE OK R3
  EVIDENCE: rc=0 LEASE OK R3 12 paths. PM Stage A fresh on rb-R3 at 758503a (scratchpad stageA-R3.out), STAGE_A rc=0 checks=8

- [x] G9: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: frontend-qc PASS, 0 findings at 758503a. TSX fidelity: token diff vs the original (comments and className values stripped) shows only removed CSS Module imports; page.tsx byte-identical. CSS equivalence matched per element and state for all 10 files and vip.css (cascade order and layer checked in the build CSS; zero banned tokens). Adjudications: LevelTable cellClasses inlined as exclusive ternaries allowed per T6 (computed set per cell identical); font: inherit omitted allowed (reset button{font:inherit} gives identical font and weight); corner z-index var(--z-sticky) matches the original computed value (.headRow .th 0,2,0 beats .corner), guide 04-10 "z 101" is guide errata. D3: REWARDS-01..11 reproduced; VipPage.module.css used only by /tier. Comments: only "(ruling B1)" removed. Original-app defects found go to FIX-LIST.

# Gates: KF1 global ui-slide-up keyframe (fix leaf, U2 Stage B finding)

OWNS: src/styles/keyframes.css

Wave: W5-fix · Needs (merged before dispatch): F1, U2

Spawn contract lease (paste as-is):

```yaml
allowed_files:
  - src/styles/keyframes.css
```

Read first: `docs/rebuild/PM-RULINGS.md` row PR-18 (amended for this fix), `docs/rebuild/ADR-002.md` line 42, then the originals `apps/web/src/ui/Sheet/Sheet` and `apps/web/src/ui/Modal/Modal` CSS Module sheets (Sheet declares `slideUp` globally near line 87; Modal declares it inside `@media (max-width: 639px)` near line 134).

Finding (frontend-qc, U2 Stage B): `src/styles/keyframes.css:46-47` declares `ui-slide-up` only inside `@media (max-width: 639px)`, so `src/ui/ui.css` Sheet panel (`animation: ui-slide-up ...`) has no keyframe at 640px and wider; the original Sheet slides up at every width.

Leaf notes: move `@keyframes ui-slide-up` out of the `@media (max-width: 639px)` wrapper to the top level, body byte-unchanged, and delete the now-empty wrapper. Rewrite the comment above it to say it serves the Modal bottom sheet and the Sheet panel (no tag tokens). Touch nothing else.

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

- [x] G4: the fix is in place
  CHECK: bash .unlazy/yaobet-rebuild/checks/KF1.sh
  EXPECT: CHECKS OK KF1
  EVIDENCE: automatic-evidence=v1; definition-sha256=1a3236ad246ed8fafaac37c8c3fa549004efc8e3016182e925db9263e4f61655; exit=0; EXPECT=matched; output-sha256=22096dde1427a314e420050d516e86d2ff4e2caf7b0a9096ebac9b3f75cd8e30; output-bytes=18; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: F1 and U2 acceptance still hold
  CHECK: bash .unlazy/yaobet-rebuild/checks/F1.sh && bash .unlazy/yaobet-rebuild/checks/U2.sh && echo F1_U2_OK
  EXPECT: F1_U2_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=65b7a85308fcdf50a2568ad3804c87955be19965068de3f01caf5e2b9176967e; exit=0; EXPECT=matched; output-sha256=9a341e9ff807873b1aaeea5219e5b66f67e812f1620ffa4fe860d11fe55570bd; output-bytes=47; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: lease holds
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh KF1
  EXPECT: LEASE OK KF1
  EVIDENCE: rc=0 LEASE OK KF1 1 paths. PM back-fill fresh at wt rb-KF1@d2c9b56 base=d5cf5b7 (scratchpad bf/KF1-G6.out), run on main c1c9a08.

# Gates: I1 deferred integration checks

Wave: W16 · Needs (merged before dispatch): every leaf W0-W15 · Dev-server port: 3140

Leaf notes: Verification only: no lease, no builder. The PM (or test-runner) runs it on `main` after the last merge. It holds every acceptance check that cannot run in its leaf's own wave: built CSS (F1, PR-13, fonts), the curl checks of F5, S2, S3 and S5, the SH-02 box check and the 1440 filler count (S2, S6), and the auth flow (S4).

- [x] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=eb7a2e14e3169d81be1e61fe79fc94ac8e6e81df4e4a933527b90030ffee4607; exit=0; EXPECT=matched; output-sha256=3006516902c604a845b19946dd7dda6e224c7c00040b87bff313077f683f1e7b; output-bytes=833; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G2: typecheck passes
  CHECK: npx tsc --noEmit && echo TSC_OK
  EXPECT: TSC_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=48a822910fccd73a590c55e6e847659263f5ac983269371a7d08e6f1ca184cb6; exit=0; EXPECT=matched; output-sha256=d018f66bb24b65f8f3c86936c97cc0c033c796f2f7b335753a186d3d2c5818a4; output-bytes=7; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G3: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/I1.sh
  EXPECT: CHECKS OK I1
  EVIDENCE: automatic-evidence=v1; definition-sha256=1d21d3faf3b163d51b46d30bf2913ad78314af96a24491d9bbadd9fded0e2628; exit=0; EXPECT=matched; output-sha256=99a622dd886980a58264a6cedbabbf64e57d831d424e3bd062a4cbed545264c4; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G4: production build passes
  CHECK: npm run build > /tmp/yb-build-I1.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=6f0c20428f97243283f9ac15289ed3f047687ce9443e5a4ab18023137fce8453; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

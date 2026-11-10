# Gates: HF5 I1 expectation hot-fix (PR-36, PR-43, I1 back-fill finding)

OWNS: .unlazy/yaobet-rebuild/genplan.py, .unlazy/yaobet-rebuild/checks/I1.sh, .unlazy/yaobet-rebuild/checks/boxes.json

Wave: back-fill fix · Needs (merged before dispatch): all leaves (main 5449753 or later)

Spawn contract lease (paste as-is):

```yaml
allowed_files:
  - .unlazy/yaobet-rebuild/genplan.py
  - .unlazy/yaobet-rebuild/checks/I1.sh
  - .unlazy/yaobet-rebuild/checks/boxes.json
```

Finding: on main the I1 check fails 2/36, and the original app fails the same two the same way (test-runner, scratchpad trI1/). Read `docs/rebuild/PM-RULINGS.md` PR-43 first; it is the spec.

Leaf notes:
1. `genplan.py`, S2_SSR list: drop the last entry `'href="/cau-lac-bo"'` (the other 12 entries and their ids I1-S2-ssr-1..12 stay as they are). Add, in the I1 list right after the S2_SSR html rows, `nohtml("I1-S2-member-menu-closed", "/", 'href="/cau-lac-bo"')`.
2. `genplan.py`, boxes.json writer, `identity` entry: selector `header ul[aria-label=\"Tiện ích\"] + div`; `_src` becomes `components/layout/Header.tsx:126 div.identity, directly after the utility list at :112 (original)`. Keep the guide values unless G3 shows the original differs by more than 1 px at a width; then set that width to the original's measured value (one decimal, as box-check prints) and report each change with both numbers. Other boxes stay untouched.
3. Regenerate with the generator (from a worktree set `GENPLAN_REPO` to the main checkout; it only affects reads), then `git status --porcelain`: the only changed paths may be the three OWNS paths. If anything else changes (a ledger losing ticked evidence included), revert the generated outputs, stop and report each extra path (generator drift is the PM's call).

- [x] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=eb7a2e14e3169d81be1e61fe79fc94ac8e6e81df4e4a933527b90030ffee4607; exit=0; EXPECT=matched; output-sha256=3006516902c604a845b19946dd7dda6e224c7c00040b87bff313077f683f1e7b; output-bytes=833; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G2: the corrected expectations are in the generator and the generated files
  CHECK: bash .unlazy/yaobet-rebuild/checks/HF5.sh
  EXPECT: CHECKS OK HF5
  EVIDENCE: automatic-evidence=v1; definition-sha256=2b91e23730d81f2c434eb2c19f83cf13c721c91c6f713e130e99388ec39f1575; exit=0; EXPECT=matched; output-sha256=caac89a44e833592ac7f9d1f9beea8925ebd425a5602cb243cccc19708974285; output-bytes=20; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G3: the original app, measured with the corrected boxes.json, passes every box (evidence that the expectation is the original's)
  CHECK: ORIG_APP=/private/tmp/claude-502/-Users-maxime-Documents-Technical-Projects-Harness-Agents-V1/4df8d2d0-f7dc-4df2-901e-9cba47678abc/scratchpad/orig-web PORT=3163 bash .unlazy/yaobet-rebuild/checks/orig-boxes.sh
  EXPECT: BOXES OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=b04ca43d58bff5a0289d5542c4e7f89114c0c4515da56f62b4d24b7f8257c80d; exit=0; EXPECT=matched; output-sha256=6eddb79da75335242a7e350f2acc302860c0f09cb2af61850a6955661b940e2e; output-bytes=1071; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G4: the rebuild passes the same boxes
  CHECK: node scripts/with-dev-server.mjs --port 3164 -- node scripts/box-check.mjs --boxes .unlazy/yaobet-rebuild/checks/boxes.json
  EXPECT: BOXES OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=d95c88c01c509e79edad44c1a1070300f8b14e2f3678cffce43042d4005c9701; exit=0; EXPECT=matched; output-sha256=9b24d9eb5126f5b9b5cc13f7f01fd2938be1f28e55c95aed503bc1e3d6dcffcf; output-bytes=1146; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: lease holds
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh HF5
  EXPECT: LEASE OK HF5
  EVIDENCE: rc=0 LEASE OK HF5 3 paths. PM back-fill fresh at wt rb-HF5@33d468d base=edda77f (scratchpad bf/HF5-G5.out), run on main c1c9a08.

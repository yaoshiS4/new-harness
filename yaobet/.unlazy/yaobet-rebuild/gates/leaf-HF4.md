# Gates: HF4 redirect expectation hot-fix (PR-36, PR-41, U3 Stage A finding)

OWNS: scripts/verify-routes.mjs, .unlazy/yaobet-rebuild/genplan.py, .unlazy/yaobet-rebuild/checks/U3.sh, .unlazy/yaobet-rebuild/checks/U7.sh, .unlazy/yaobet-rebuild/GATES.md

Wave: W10-fix · Needs (merged before dispatch): HF3, U6

Spawn contract lease (paste as-is):

```yaml
allowed_files:
  - scripts/verify-routes.mjs
  - .unlazy/yaobet-rebuild/genplan.py
  - .unlazy/yaobet-rebuild/checks/U3.sh
  - .unlazy/yaobet-rebuild/checks/U7.sh
  - .unlazy/yaobet-rebuild/GATES.md
```

Finding: the original app (Next 16.2.9, `next start`) answers `/bao-mat`, `/lich-su`, `/hoan-tra` and `/game-han-che` with 200, no Location header, and `<meta http-equiv="refresh" content="1;url=<target>">`, because the root `src/app/loading.tsx` streams before `redirect()`. The rebuild's U3 worktree does the same in dev. Read `docs/rebuild/PM-RULINGS.md` PR-41 first; it is the spec.

Leaf notes:
1. `scripts/verify-routes.mjs`: an INVENTORY row may carry a 5th element, a refresh target. When present, `probe` reads the body text and fails with `Fail: <url> | Expected: body with refresh to <target> | Got: absent` if it lacks `http-equiv="refresh" content="1;url=<target>"`. The redirect rows become exactly `...REDIRECTS.map(([from, to]) => [from, 200, null, null, to])`. Update the row comment. The Location branch for the 3rd element stays as is. No other behaviour change.
2. `genplan.py`: U3 replaces `U3-bao-mat-307`/`U3-bao-mat-target` with `code U3-bao-mat-200 /bao-mat 200` and `html U3-bao-mat-refresh /bao-mat 'http-equiv="refresh" content="1;url=/tai-khoan"'`; the same for lich-su (`U3-lich-su-200`, `U3-lich-su-refresh`); adds `nohtml U3-tai-khoan-direct /tai-khoan 'http-equiv="refresh"'`. U7 replaces `U7-ghc-307`/`U7-ghc-target` with `code U7-ghc-200 /game-han-che 200` and `html U7-ghc-refresh /game-han-che 'http-equiv="refresh" content="1;url=/cuoc-hop-le?tab=han-che"'`, and `U7-hoan-tra-307`/`U7-hoan-tra-target` with `code U7-hoan-tra-200 /hoan-tra 200` and `html U7-hoan-tra-refresh /hoan-tra 'http-equiv="refresh" content="1;url=/khuyen-mai"'`. The A4 text says "the four redirects 200 with a meta refresh to their targets (PR-41)". Use the generator's existing helpers.
3. Regenerate with the generator (from a worktree set `GENPLAN_REPO` to the main checkout; it only affects reads), then `git status --porcelain`: the only changed paths may be the five OWNS paths. If anything else changes (a ledger losing ticked evidence included), revert the generated outputs, stop and report each extra path (generator drift is the PM's call).

- [x] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=eb7a2e14e3169d81be1e61fe79fc94ac8e6e81df4e4a933527b90030ffee4607; exit=0; EXPECT=matched; output-sha256=3006516902c604a845b19946dd7dda6e224c7c00040b87bff313077f683f1e7b; output-bytes=833; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G2: the new expectations are in the inventory, the generator and the generated checks
  CHECK: bash .unlazy/yaobet-rebuild/checks/HF4.sh
  EXPECT: CHECKS OK HF4
  EVIDENCE: automatic-evidence=v1; definition-sha256=5a7770029a637ac20f3ca8d2991648a74b37b73b0d29567f0cccce4319ecca28; exit=0; EXPECT=matched; output-sha256=fd71f5ff2b4cb01f99dbba1d89eaede47fea813ec2111c79c7ef1596812e9bda; output-bytes=20; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G3: rows without a marker still pass on a live server (main's tree). The redirect rows need the U3 and U7 routes, which main lacks before they merge; they run live in U3 G7 and U7 after HF4 merges.
  CHECK: node scripts/with-dev-server.mjs --port 3129 -- node scripts/verify-routes.mjs --base http://localhost:3129 --only /
  EXPECT: ROUTES OK 1/1
  EVIDENCE: automatic-evidence=v1; definition-sha256=adb57137a6d0fc1754232d5db6382ac3a3265dfbceb98b94a5fc044a65ec60b9; exit=0; EXPECT=matched; output-sha256=1109a8eba2e281ab006d5335381b70c6bc163f6a2d5fb288a833a8fe8dc7ed87; output-bytes=98; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G4: lease holds
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh HF4
  EXPECT: LEASE OK HF4
  EVIDENCE: rc=0 LEASE OK HF4 5 paths. PM Stage A fresh on rb-HF4 at ac75372 (scratchpad stageA-HF4.out), STAGE_A rc=0

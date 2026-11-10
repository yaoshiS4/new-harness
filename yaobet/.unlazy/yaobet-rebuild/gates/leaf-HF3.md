# Gates: HF3 soft-404 expectation hot-fix (PR-36, PR-40, S7 and S8 builder finding)

OWNS: scripts/verify-routes.mjs, .unlazy/yaobet-rebuild/genplan.py, .unlazy/yaobet-rebuild/checks/S7.sh, .unlazy/yaobet-rebuild/checks/S8.sh, .unlazy/yaobet-rebuild/GATES.md

Wave: W9-fix · Needs (merged before dispatch): F2 (gate scripts), S6

Spawn contract lease (paste as-is):

```yaml
allowed_files:
  - scripts/verify-routes.mjs
  - .unlazy/yaobet-rebuild/genplan.py
  - .unlazy/yaobet-rebuild/checks/S7.sh
  - .unlazy/yaobet-rebuild/checks/S8.sh
  - .unlazy/yaobet-rebuild/GATES.md
```

Finding: the original app (Next 16.2.9, measured in dev and `next start`) answers `/foo` and `/khuyen-mai/pr9` with 200 and `<meta name="robots" content="noindex">`, because the root `src/app/loading.tsx` streams before `notFound()`. Valid pages (`/casino`, `/khuyen-mai/pr1`) answer 200 without that meta. Read `docs/rebuild/PM-RULINGS.md` PR-40 first; it is the spec.

Leaf notes:
1. `scripts/verify-routes.mjs`: an INVENTORY row may carry a 4th element, a body marker. When present, `probe` reads the body text and fails with `Fail: <url> | Expected: body with <marker> | Got: absent` if it lacks `name="robots" content="<marker>"`. The two rows become exactly `["/foo", 200, null, "noindex"]` and `["/khuyen-mai/pr9", 200, null, "noindex"]`. Update the row comment. No other behaviour change.
2. `genplan.py`: S7 replaces `S7-foo-404` with `code S7-foo-200 /foo 200` and `html S7-foo-noindex /foo 'name="robots" content="noindex"'`; replaces the served `S7-foo-copy` with a file check `has S7-foo-copy 'Không tìm thấy hạng mục' 'src/app/[vertical]/not-found.tsx'`; keeps `S7-foo-title`; adds `nohtml S7-casino-indexable /casino 'content="noindex"'`. S8 replaces `S8-pr9-404` with `code S8-pr9-200 /khuyen-mai/pr9 200`, replaces `S8-pr9-default` with `html S8-pr9-noindex /khuyen-mai/pr9 'name="robots" content="noindex"'`, adds `nohtml S8-pr1-indexable /khuyen-mai/pr1 'content="noindex"'`. The A4 text says "/foo and /khuyen-mai/pr9 200 with the noindex meta (soft 404, PR-40)". Use the generator's existing helpers.
3. Regenerate with the generator (from a worktree set `GENPLAN_REPO` to the main checkout; it only affects reads, genplan.py:29 and :285), then `git status --porcelain`: the only changed paths may be the five OWNS paths. If anything else changes, revert the generated outputs, stop and report each extra path (generator drift is the PM's call).

- [x] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=eb7a2e14e3169d81be1e61fe79fc94ac8e6e81df4e4a933527b90030ffee4607; exit=0; EXPECT=matched; output-sha256=3006516902c604a845b19946dd7dda6e224c7c00040b87bff313077f683f1e7b; output-bytes=833; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G2: the new expectations are in the inventory, the generator and the generated checks
  CHECK: bash .unlazy/yaobet-rebuild/checks/HF3.sh
  EXPECT: CHECKS OK HF3
  EVIDENCE: automatic-evidence=v1; definition-sha256=948b3afa463d0618616bc7e03cb21aa20ee14b6f1721a444939e9dfb742bbf52; exit=0; EXPECT=matched; output-sha256=aa6d49a2bd8df92e84fae983f6a9cfa9c352d6d5f231c224e62565ef7424af46; output-bytes=20; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G3: rows without a marker still pass on a live server (main's tree). The two marker rows need the `[vertical]` and `khuyen-mai/[id]` routes, which main lacks before S7 and S8 merge (there, both URLs are a real 404 with no matched route); they run live in S7 G7 and S8 G7 after HF3 merges.
  CHECK: node scripts/with-dev-server.mjs --port 3129 -- node scripts/verify-routes.mjs --base http://localhost:3129 --only /
  EXPECT: ROUTES OK 1/1
  EVIDENCE: automatic-evidence=v1; definition-sha256=adb57137a6d0fc1754232d5db6382ac3a3265dfbceb98b94a5fc044a65ec60b9; exit=0; EXPECT=matched; output-sha256=1109a8eba2e281ab006d5335381b70c6bc163f6a2d5fb288a833a8fe8dc7ed87; output-bytes=98; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G4: lease holds
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh HF3
  EXPECT: LEASE OK HF3
  EVIDENCE: rc=0 LEASE OK HF3 5 paths. PM back-fill fresh at wt rb-HF3@b51024b base=2317674 (scratchpad bf/HF3-G4.out), run on main c1c9a08.

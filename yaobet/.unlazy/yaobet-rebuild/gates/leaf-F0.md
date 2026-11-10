# Gates: F0 stack, gate scripts and wipe

OWNS: package.json, package-lock.json, next.config.ts, tsconfig.json, eslint.config.mjs, .gitignore, scripts/**, src/**

Wave: W0 · Needs (merged before dispatch): none · Dev-server port: 3110

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - package.json
  - package-lock.json
  - next.config.ts
  - tsconfig.json
  - eslint.config.mjs
  - .gitignore
  - scripts/**
  - src/**
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `F0 stack-and-gates` row in `docs/rebuild/review/foundations-core.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/F0.sh` (PM-authored; never edit it).

Leaf notes: `src/**` is a deletion-only lease: delete every file under `src/` (PR-07, D4) and create nothing there. Delete the old `scripts/verify-content.mjs`, `verify-format.mjs` and `verify-tokens.mjs`; rewrite `scripts/verify-routes.mjs`; `--only` with a URL outside the inventory exits 1 and prints `not in inventory` before any request, with or without `--base`. `next.config.ts` per PR-24. Pin `"playwright": "1.61.1"` exactly (PR-30). Write every gate script exactly to the contracts in ADR-002 §4 and §5: `token-lint.mjs`, `rebuild-rules.mjs`, `tw-unknown-classes.mjs`, `verify-routes.mjs`, `with-dev-server.mjs`, `capture-shots.mjs`, `shot-diff.mjs`, `box-check.mjs`, `auth-flow.mjs`. Keep the `.claude/**` ignore in `eslint.config.mjs` and add the collection ports-barrel rule the row checks. Add `/.shots/` and `/shots/` to `.gitignore`. Never edit `.unlazy/**`.

- [x] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=eb7a2e14e3169d81be1e61fe79fc94ac8e6e81df4e4a933527b90030ffee4607; exit=0; EXPECT=matched; output-sha256=3006516902c604a845b19946dd7dda6e224c7c00040b87bff313077f683f1e7b; output-bytes=833; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G2: typecheck passes
  CHECK: npx tsc --noEmit && echo TSC_OK
  EXPECT: TSC_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=48a822910fccd73a590c55e6e847659263f5ac983269371a7d08e6f1ca184cb6; exit=0; EXPECT=matched; output-sha256=d018f66bb24b65f8f3c86936c97cc0c033c796f2f7b335753a186d3d2c5818a4; output-bytes=7; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G3: token-lint self-test fires on every seed
  CHECK: npm run lint:tokens:self-test
  EXPECT: SELF-TEST OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=5e3f21fff8831ba8176f6603dfc88df508817bfdfb6b1e7f9973e72a0d0b0494; exit=0; EXPECT=matched; output-sha256=74f7e2d825344ef10fd69a29b15df28c616fb9cec228bbe52f069c9f0d91aaab; output-bytes=1403; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G4: rule-gate self-test fires on every positive seed and passes every clean seed
  CHECK: node scripts/rebuild-rules.mjs --self-test
  EXPECT: SELF-TEST OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=3c600fcccfedbabdc0b44464b43e247c3ae5ba5fca2a6f9f0c5a4d849b175b60; exit=0; EXPECT=matched; output-sha256=7b5a06b563c828adbf18269aa91b85e5b6b2f4ec7e0a6eb91565aca1484adf4c; output-bytes=2936; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: unknown-class self-test flags stock utilities and passes repo-declared classes
  CHECK: node scripts/tw-unknown-classes.mjs --self-test
  EXPECT: SELF-TEST OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=4c8828fce1d9ff83fca3a0b1883873f0aa652201296da916c1066b957aae0cff; exit=0; EXPECT=matched; output-sha256=2d45ea36992c5723c80b4b6063d0b504dc4ea3ad6a5016e1bfb17f934ac81770; output-bytes=341; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: Google Fonts is reachable from this build environment
  CHECK: bash .unlazy/yaobet-rebuild/checks/fonts-preflight.sh
  EXPECT: CHECKS OK fonts
  EVIDENCE: automatic-evidence=v1; definition-sha256=afa08f4c28886c6a29a61ceabbfea7fa8d953af8e5b3cf507eec119fbaabd8fe; exit=0; EXPECT=matched; output-sha256=9d88bd6494e587b77e5563c4f0542193cd060d125887a39303f1ddbd61f50fc6; output-bytes=20; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/F0.sh
  EXPECT: CHECKS OK F0
  EVIDENCE: automatic-evidence=v1; definition-sha256=54846b596564bd29835526fb6cfbc6647815724a98f9c542d91416ffa55bfc67; exit=0; EXPECT=matched; output-sha256=962e10353f1a6579f5365c5bd590b09b8c2d0af7ce1010b9325ed234b5726526; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh F0
  EXPECT: LEASE OK F0
  EVIDENCE: rc=0 LEASE OK F0 202 paths. PM back-fill fresh at wt rb-F0@e91f060 base=3ff6d0f (scratchpad bf/F0-G8.out), run on main c1c9a08.

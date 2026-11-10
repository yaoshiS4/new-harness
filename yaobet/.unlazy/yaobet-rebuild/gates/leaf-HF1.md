# Gates: HF1 class-token extractor hot-fix (PR-36, S2 builder finding)

OWNS: scripts/class-tokens.mjs

Wave: W6-fix · Needs (merged before dispatch): F2 (gate scripts)

Spawn contract lease (paste as-is):

```yaml
allowed_files:
  - scripts/class-tokens.mjs
```

Finding (dev-fe, S2): `scripts/class-tokens.mjs` `scanExpr` (near line 171) reports every string literal inside `className={...}` as a class token, including arguments of ordinary calls. The verbatim original `BottomTabBar.tsx` writes `className={[styles.tab, isActive("/") ? styles.active : ""].filter(Boolean).join(" ")}`, so the route strings `/`, `/khuyen-mai`, `/vi-tien`, `/tai-khoan` are flagged as `unknown-class` (4 false positives).

Leaf notes: inside a className expression, skip string literals that are arguments of a call whose callee is not `cn`, `clsx` or `cx` (and template parts inside such arguments). Literals outside those call parentheses, ternary branches, array items and arguments of `cn`/`clsx`/`cx` stay class tokens. Smallest diff; keep the exported API; touch nothing else.

- [x] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=eb7a2e14e3169d81be1e61fe79fc94ac8e6e81df4e4a933527b90030ffee4607; exit=0; EXPECT=matched; output-sha256=3006516902c604a845b19946dd7dda6e224c7c00040b87bff313077f683f1e7b; output-bytes=833; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G2: the fix holds and real tokens are still caught
  CHECK: bash .unlazy/yaobet-rebuild/checks/HF1.sh
  EXPECT: CHECKS OK HF1
  EVIDENCE: automatic-evidence=v1; definition-sha256=58eaafb494c25ab1cbf5ce8d025f2a0e3fe7c9afb452c2ee83ac17671209ba58; exit=0; EXPECT=matched; output-sha256=9b0eff7bdeac7b0b7cf3908fbe627a7eea60a2bd2318f6e47c8c94c2bc1a68b9; output-bytes=18; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G3: the token lint and rule gates still pass on main's tree
  CHECK: npm run lint:tokens && node scripts/rebuild-rules.mjs src && echo GATES_OK
  EXPECT: GATES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=94092af93f16bd84201b0f7d33c9613f479e0d3df7d262ed77420d152f56398e; exit=0; EXPECT=matched; output-sha256=2f9a01c75a84951a01a016c9086bfa9d80e4e968e969701bf28bedbf3b235eca; output-bytes=145; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G4: lease holds
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh HF1
  EXPECT: LEASE OK HF1
  EVIDENCE: rc=0 LEASE OK HF1 1 paths. PM back-fill fresh at wt rb-HF1@6a8e481 base=785f7f9 (scratchpad bf/HF1-G4.out), run on main c1c9a08.

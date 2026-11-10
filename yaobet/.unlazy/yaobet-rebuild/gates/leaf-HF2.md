# Gates: HF2 class-token extractor hot-fix (PR-36, S7 builder finding)

OWNS: scripts/class-tokens.mjs

Wave: W9-fix · Needs (merged before dispatch): HF1

Spawn contract lease (paste as-is):

```yaml
allowed_files:
  - scripts/class-tokens.mjs
```

Finding (dev-fe, S7): `scripts/class-tokens.mjs` `scanExpr` (string branch near lines 199-201) emits every string literal inside `className={...}`, including operands of comparisons. The verbatim original `LiveOddsBoard.tsx:115` writes `className={odds.direction === "up" ? styles.up : styles.down}` (ported as class strings), so the operand `up` is reported as `unknown-class up`. Probe: `<i className={d === "up" ? "a-up" : "a-down"} />` yields the tokens `up`, `a-up`, `a-down`.

Leaf notes: inside a className expression, skip a string literal (and a template literal) that is a direct operand of `===`, `!==`, `==` or `!=` (on either side). Ternary branches, array items, `&&` right-hand sides and arguments of `cn`/`clsx`/`cx` stay class tokens. Keep HF1's call-argument rule. Smallest diff; keep the exported API; touch nothing else.

- [x] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=eb7a2e14e3169d81be1e61fe79fc94ac8e6e81df4e4a933527b90030ffee4607; exit=0; EXPECT=matched; output-sha256=3006516902c604a845b19946dd7dda6e224c7c00040b87bff313077f683f1e7b; output-bytes=833; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G2: the fix holds, real tokens are still caught, HF1 still holds
  CHECK: bash .unlazy/yaobet-rebuild/checks/HF2.sh && bash .unlazy/yaobet-rebuild/checks/HF1.sh
  EXPECT: CHECKS OK HF1
  EVIDENCE: automatic-evidence=v1; definition-sha256=8021a31c35d5219cc599915086bd3b7a5941a78aac08eb709f600ef0d4e705a2; exit=0; EXPECT=matched; output-sha256=bc300fc367155c9aee4157592e955a85ad17fe53f0e4c06ac78b010d1282bedd; output-bytes=38; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G3: the token lint and rule gates still pass on main's tree
  CHECK: npm run lint:tokens && node scripts/rebuild-rules.mjs src && echo GATES_OK
  EXPECT: GATES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=94092af93f16bd84201b0f7d33c9613f479e0d3df7d262ed77420d152f56398e; exit=0; EXPECT=matched; output-sha256=2f9a01c75a84951a01a016c9086bfa9d80e4e968e969701bf28bedbf3b235eca; output-bytes=145; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G4: lease holds
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh HF2
  EXPECT: LEASE OK HF2
  EVIDENCE: rc=0 LEASE OK HF2 1 paths. PM back-fill fresh at wt rb-HF2@a71df91 base=efb8455 (scratchpad bf/HF2-G4.out), run on main c1c9a08.

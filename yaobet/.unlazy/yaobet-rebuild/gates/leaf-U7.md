# Gates: U7 trust, restricted, utility routes

OWNS: src/app/cuoc-hop-le/**, src/app/game-han-che/**, src/app/hoan-tra/**, src/app/ho-tro/**, src/app/tro-giup/**, src/app/tai-app/**, src/app/phong-cach/**, src/components/restricted/**

Wave: W11 · Needs (merged before dispatch): U6, F5 · Dev-server port: 3131

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/app/cuoc-hop-le/**
  - src/app/game-han-che/**
  - src/app/hoan-tra/**
  - src/app/ho-tro/**
  - src/app/tro-giup/**
  - src/app/tai-app/**
  - src/app/phong-cach/**
  - src/components/restricted/**
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `UIM-L7 trust routes` row in `docs/rebuild/review/ui-member.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/U7.sh` (PM-authored; never edit it).

Leaf notes: There is no `src/components/utility` and no `StubPage` (PR-33): each stub page uses F1's `stub-*` utilities, as the original pages used `../stub.module.css`.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/app/cuoc-hop-le/**' 'src/app/game-han-che/**' 'src/app/hoan-tra/**' 'src/app/ho-tro/**' 'src/app/tro-giup/**' 'src/app/tai-app/**' 'src/app/phong-cach/**' 'src/components/restricted/**' && node scripts/tw-unknown-classes.mjs 'src/app/cuoc-hop-le/**' 'src/app/game-han-che/**' 'src/app/hoan-tra/**' 'src/app/ho-tro/**' 'src/app/tro-giup/**' 'src/app/tai-app/**' 'src/app/phong-cach/**' 'src/components/restricted/**' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=913fc469cac3f8fb2f57085c16ae74e986c3020e221d8be75fefe3cafbb2432e; exit=0; EXPECT=matched; output-sha256=d4ddee5c276761457eb6bcad40255a1a14ff989b13d0bfe15d64458d861cfdef; output-bytes=69; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/U7.sh
  EXPECT: CHECKS OK U7
  EVIDENCE: automatic-evidence=v1; definition-sha256=580374e5fdfb02f7b077d029c0474e2b38bb742a3e82cf46347c9e46fce8d196; exit=0; EXPECT=matched; output-sha256=c4575bd451d1e885bb918addf47db330aad969d49df3e4fe43217b0b33cc7e35; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-U7.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=2c56fab0858c0ee95f00ae84ba040c64ba0279c09c6586abea6b682c9361186b; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: routes answer as the inventory says, on this leaf's own dev server
  CHECK: node scripts/with-dev-server.mjs --port 3131 -- node scripts/verify-routes.mjs --base http://localhost:3131 --only /cuoc-hop-le,/game-han-che,/hoan-tra,/ho-tro,/tro-giup,/tai-app,/phong-cach
  EXPECT: ROUTES OK 7/7
  EVIDENCE: automatic-evidence=v1; definition-sha256=29901f4fc8d278218c6f9f723539cf7d7244f41b7e1016f0bd889405b4746e9c; exit=0; EXPECT=matched; output-sha256=705ebf7cba393d488c84fb623502f6069956fc32e93d1b44bb2bff0b0210d5de; output-bytes=214; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh U7
  EXPECT: LEASE OK U7
  EVIDENCE: rc=0 LEASE OK U7 14 paths. PM Stage A fresh on rb-U7 at ef9d0d6 (scratchpad stageA-U7.out), STAGE_A rc=0 checks=8

- [x] G9: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: frontend-qc PASS, 0 Fails across 14 files: TSX diffed against the original (logic, props, hooks, getters, copy, redirects byte-identical), every class token mapped to its built CSS rule and checked against the original sheets after the cascade (8 sheet groups match), D3 defects UIM-52/56/57/58/61/62/63/64 reproduced, no tags or legal terms. The one pending item (original exhaustive-deps comment line, RestrictedRoot.tsx:147) was restored verbatim in ef9d0d6; a diff against the original lines 140-152 prints nothing. Original-app defects go to FIX-LIST.

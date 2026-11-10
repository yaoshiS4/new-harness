# Gates: U4 wallet

OWNS: src/app/(member)/vi-tien/**, src/components/wallet/**, src/styles/areas/member.css

Wave: W11 · Needs (merged before dispatch): U3 · Dev-server port: 3132

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/app/(member)/vi-tien/**
  - src/components/wallet/**
  - src/styles/areas/member.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `UIM-L4 wallet` row in `docs/rebuild/review/ui-member.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/U4.sh` (PM-authored; never edit it).

Leaf notes: `member.css` passes from U3 (W10): append only.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/app/(member)/vi-tien/**' 'src/components/wallet/**' 'src/styles/areas/member.css' && node scripts/tw-unknown-classes.mjs 'src/app/(member)/vi-tien/**' 'src/components/wallet/**' 'src/styles/areas/member.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=0eb7776a21f380a2ebd3d9ca7ba3dc88c0a99ca18c1f92d7ff8080becc920c29; exit=0; EXPECT=matched; output-sha256=ca35c89218b4a351be286c3132c25808ed5f8dab65a736534d23537af750fc93; output-bytes=70; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/U4.sh
  EXPECT: CHECKS OK U4
  EVIDENCE: automatic-evidence=v1; definition-sha256=620c108731dd44e3de2b425c94149baa4c4066979bb09512ac0c524278b1cc2a; exit=0; EXPECT=matched; output-sha256=e43039eec9f5bec0834f880804ec29ab276417bf48130701518c6a5ec93337b7; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-U4.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=842a9524d913cfb3f6e4684626ec8a261837821c79522cff6a102ed3b7aff345; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: routes answer as the inventory says, on this leaf's own dev server
  CHECK: node scripts/with-dev-server.mjs --port 3132 -- node scripts/verify-routes.mjs --base http://localhost:3132 --only /vi-tien
  EXPECT: ROUTES OK 1/1
  EVIDENCE: automatic-evidence=v1; definition-sha256=54eacfe3e8503579ea2995e30295e50f62ede9710cbf232e9ed46200799a6c63; exit=0; EXPECT=matched; output-sha256=a8deeae52a80356f340b24df81526e9a139b88cddf2519d631ec8576df9f0a62; output-bytes=105; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh U4
  EXPECT: LEASE OK U4
  EVIDENCE: rc=0 LEASE OK U4 9 paths. PM Stage A fresh on rb-U4 at 3af3c7d (scratchpad stageA-U4b.out), STAGE_A rc=0 checks=8

- [x] G9: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: frontend-qc PASS, 0 findings. First pass at c84fd62 passed TSX fidelity, CSS equivalence (108 tokens mapped to the build CSS, cascade order checked), D3 (UIM-37/38/40/41/42/43 reproduced) and comment tokens, and failed 6 comment lines reworded beyond tag removal. Fixed in 3af3c7d (comment-only, 3 files, 6 lines). Recheck: diff c84fd62..3af3c7d comment-only rc=0, word-level comment diff of all 9 files shows only tag/legal removals rc=0. Original-app defects found go to FIX-LIST.

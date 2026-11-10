# Gates: U3 member frame and account

OWNS: src/app/(member)/layout.tsx, src/app/(member)/tai-khoan/**, src/app/bao-mat/**, src/app/lich-su/**, src/components/account/**, src/styles/areas/member.css

Wave: W10 · Needs (merged before dispatch): F5, S3 · Dev-server port: 3130

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/app/(member)/layout.tsx
  - src/app/(member)/tai-khoan/**
  - src/app/bao-mat/**
  - src/app/lich-su/**
  - src/components/account/**
  - src/styles/areas/member.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `UIM-L3 member frame + account` row in `docs/rebuild/review/ui-member.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/U3.sh` (PM-authored; never edit it).

Leaf notes: The member keyframes keep their guide names `pulseDot` and `progressShimmer` (PR-29) in `src/styles/areas/member.css`. The original `(member)/member.module.css` becomes classes in `member.css`. Do not build ProfileHeader, QuickActions, AccountMenu or LogoutMenuItem (PR-19); drop their barrel exports (PR-34). The port comes from with-dev-server, not 3000.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/app/(member)/layout.tsx' 'src/app/(member)/tai-khoan/**' 'src/app/bao-mat/**' 'src/app/lich-su/**' 'src/components/account/**' 'src/styles/areas/member.css' && node scripts/tw-unknown-classes.mjs 'src/app/(member)/layout.tsx' 'src/app/(member)/tai-khoan/**' 'src/app/bao-mat/**' 'src/app/lich-su/**' 'src/components/account/**' 'src/styles/areas/member.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=f754f4f7265c199ccc242f1bdf00825199247a30a64c9c12d7b31c8b3dfb6ceb; exit=0; EXPECT=matched; output-sha256=db7fcf6738b0c1d09f40b5e7e63a78d3d0db5f4ebaa02b5342af2bef798b57fb; output-bytes=70; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/U3.sh
  EXPECT: CHECKS OK U3
  EVIDENCE: automatic-evidence=v1; definition-sha256=1b561dd6e91958c1501d02557f2042f773bb5b3818f9bd2c85e8aacdcb97f9d7; exit=0; EXPECT=matched; output-sha256=2f4669d9d912178bd3d90b0f90f8bad93f8617cc9c3f94f12d95d3ceb9d54917; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-U3.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=66b522ccb87953e91116f235a973c039d5b70c44f48f3f692cbfff7474ae0bb3; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: routes answer as the inventory says, on this leaf's own dev server
  CHECK: node scripts/with-dev-server.mjs --port 3130 -- node scripts/verify-routes.mjs --base http://localhost:3130 --only /tai-khoan,/bao-mat,/lich-su
  EXPECT: ROUTES OK 3/3
  EVIDENCE: automatic-evidence=v1; definition-sha256=772338ff141c13ba1f2ac4786cef9e284ce3065d439b989e05dbb3e6cf09671e; exit=0; EXPECT=matched; output-sha256=9206c5b35710373b65eed2efb020a8059b91510c717d236d1ed58f68664206e4; output-bytes=139; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh U3
  EXPECT: LEASE OK U3
  EVIDENCE: rc=0 LEASE OK U3 13 paths. PM Stage A fresh on rb-U3 at 55ef892 (scratchpad stageA-U3.out), STAGE_A rc=0 checks=8

- [x] G9: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: frontend-qc PASS, 0 findings. First pass flagged 4 stock zero-border tokens; fixed in 55ef892 (exactly 4 tokens, 3 files). Recheck: each token compiles to the original declaration (border: 0; :last-child border-bottom: 0), rebuild-rules RULES OK 3 files rc=0, tw-unknown-classes CLASSES OK 187 tokens rc=0, U3.sh CHECKS OK U3 31/31 rc=0. Original-app defects found go to FIX-LIST.

# Gates: U5 messages and referral

OWNS: src/app/(member)/tin-nhan/**, src/app/(member)/gioi-thieu/**, src/app/(member)/dai-ly/**, src/components/messages/**, src/components/referral/**, src/styles/areas/member.css

Wave: W12 · Needs (merged before dispatch): U3 · Dev-server port: 3133

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/app/(member)/tin-nhan/**
  - src/app/(member)/gioi-thieu/**
  - src/app/(member)/dai-ly/**
  - src/components/messages/**
  - src/components/referral/**
  - src/styles/areas/member.css
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `UIM-L5 messages + referral` row in `docs/rebuild/review/ui-member.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/U5.sh` (PM-authored; never edit it).

Leaf notes: `member.css` passes from U4 (W11): append only.

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
  CHECK: node scripts/rebuild-rules.mjs 'src/app/(member)/tin-nhan/**' 'src/app/(member)/gioi-thieu/**' 'src/app/(member)/dai-ly/**' 'src/components/messages/**' 'src/components/referral/**' 'src/styles/areas/member.css' && node scripts/tw-unknown-classes.mjs 'src/app/(member)/tin-nhan/**' 'src/app/(member)/gioi-thieu/**' 'src/app/(member)/dai-ly/**' 'src/components/messages/**' 'src/components/referral/**' 'src/styles/areas/member.css' && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=c1bed3d93323c10d3ad9171700c35b5bf3dc59fc839511a67762c5e4798e377b; exit=0; EXPECT=matched; output-sha256=f087885889bf1ea193f6a2ed3fa3532c10711d31979a1f759743546c8e4b9612; output-bytes=70; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/U5.sh
  EXPECT: CHECKS OK U5
  EVIDENCE: automatic-evidence=v1; definition-sha256=56f3d4c8b9a34cecb52e7689e9b4006c0cd69d7bf9b4edb0ba2d61ab88f4e6c6; exit=0; EXPECT=matched; output-sha256=31ca31c97c747941b601b2426af9c4142192a09688f3be7ddae6792209be8064; output-bytes=19; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G6: production build passes
  CHECK: npm run build > /tmp/yb-build-U5.log 2>&1; echo BUILD_EXIT=$?
  EXPECT: BUILD_EXIT=0
  EVIDENCE: automatic-evidence=v1; definition-sha256=c932392a5864f90b6edc7fc625fba5fbf13c1473103c35b078b56e78b671d3d1; exit=0; EXPECT=matched; output-sha256=ce706d40b6f9b1b9add553f35b5b482d4812f773d13013fb4cd667e1d78c7ab5; output-bytes=13; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G7: routes answer as the inventory says, on this leaf's own dev server
  CHECK: node scripts/with-dev-server.mjs --port 3133 -- node scripts/verify-routes.mjs --base http://localhost:3133 --only /tin-nhan,/gioi-thieu,/dai-ly
  EXPECT: ROUTES OK 3/3
  EVIDENCE: automatic-evidence=v1; definition-sha256=71e622d0232d3021ff8a2ee60ec0b83de9a2795aab19fffd28cd787d6203bcb2; exit=0; EXPECT=matched; output-sha256=442915fdee035a3fae7de4f1539e4e1c4aa1617011333d864f6b36869f16680c; output-bytes=140; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G8: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh U5
  EXPECT: LEASE OK U5
  EVIDENCE: rc=0 LEASE OK U5 14 paths. PM Stage A fresh on rb-U5 at 715af69 (scratchpad stageA-U5.out), STAGE_A rc=0 checks=8.

- [x] G9: frontend-qc fidelity pass: states, focus, keyboard and reduced motion match the guide rows for this lease; anti-slop findings that would change the guide go to FIX-LIST, never into code (owner fidelity and defect decisions)
  EVIDENCE: frontend-qc PASS at 715af69, 0 Fails: code-only diff identical for 12/13 files (MessageCenter differs only by line wrap); CSS equivalence verified per element in the built chunk (MessageCenter 23/23 incl. the 8-declaration unread ::before, InviteTools 640px block, Card padding overrides, reduced-motion order); adjudications: StepExplainer index-picked tone classes conform (ADR-002 §4 extracts literals inside className, all 7 tokens seen and emitted), omitted font:inherit identical via reset.css button rule; D3 UIM-44..51 reproduced; comment drops limited to J9, SPEC-03/04, Wave 7.2 and Decree-174; eleven anti-slop, a11y and build-fallback items sent to FIX-LIST.

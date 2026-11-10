# Gates: F2 lib core and providers

OWNS: src/lib/format.ts, src/lib/i18n.ts, src/lib/rg.ts, src/lib/types.ts, src/lib/auth/**, src/app/providers.tsx

Wave: W1 · Needs (merged before dispatch): F0 · Dev-server port: 3112

Spawn contract lease (paste as-is; one exact path or one `dir/**` per bullet, the form the lease hook accepts):

```yaml
allowed_files:
  - src/lib/format.ts
  - src/lib/i18n.ts
  - src/lib/rg.ts
  - src/lib/types.ts
  - src/lib/auth/**
  - src/app/providers.tsx
```

Read first, in this order: `docs/rebuild/ADR-002.md`, `docs/rebuild/PM-RULINGS.md`, then the `F2 lib-core-and-providers` row in `docs/rebuild/review/foundations-core.md` (leaves table) together with that review's §2-§5 entries for the same items, except the statements ADR-002 §6 lists as superseded, then every guide section in `docs/rebuild/sections/` that the row's Implements column names. Where the guide shows code or CSS, reproduce it exactly. Reproduce every defect in that review's §4 that falls inside this lease (D3). The acceptance checks are mechanised in `.unlazy/yaobet-rebuild/checks/F2.sh` (PM-authored; never edit it).

Leaf notes: Port `i18n.ts` verbatim from the original (PR-26) and list the ported files. Token lint is not a gate here (F1 writes the definition files in the same wave); the PM runs it after the W1 merge. Drop tag tokens and regulatory references from comments only (PR-27, PR-31).

- [x] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=eb7a2e14e3169d81be1e61fe79fc94ac8e6e81df4e4a933527b90030ffee4607; exit=0; EXPECT=matched; output-sha256=3006516902c604a845b19946dd7dda6e224c7c00040b87bff313077f683f1e7b; output-bytes=833; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G2: typecheck passes
  CHECK: npx tsc --noEmit && echo TSC_OK
  EXPECT: TSC_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=48a822910fccd73a590c55e6e847659263f5ac983269371a7d08e6f1ca184cb6; exit=0; EXPECT=matched; output-sha256=d018f66bb24b65f8f3c86936c97cc0c033c796f2f7b335753a186d3d2c5818a4; output-bytes=7; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G3: owned files have no banned class token, no silent no-op class, no tag or legal comment, and the CSS census holds
  CHECK: node scripts/rebuild-rules.mjs 'src/lib/format.ts' 'src/lib/i18n.ts' 'src/lib/rg.ts' 'src/lib/types.ts' 'src/lib/auth/**' 'src/app/providers.tsx' && node scripts/tw-unknown-classes.mjs 'src/lib/format.ts' 'src/lib/i18n.ts' 'src/lib/rg.ts' 'src/lib/types.ts' 'src/lib/auth/**' 'src/app/providers.tsx' && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: automatic-evidence=v1; definition-sha256=7a0ad56351733bd5a1a230a42a44890851ae6ed0609e2a81c98c2751b329bc02; exit=0; EXPECT=matched; output-sha256=6c3acfad911cedfc59783372c7eb551740da1eef5c26763edc97a3dd8566f56a; output-bytes=47; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G4: the review row's acceptance checks pass, mechanised with the leaf-note normalisations
  CHECK: bash .unlazy/yaobet-rebuild/checks/F2.sh
  EXPECT: CHECKS OK F2
  EVIDENCE: automatic-evidence=v1; definition-sha256=941050274421220de47bc0e7b783f571d16838ecb0fc8756d33544a2575880f4; exit=0; EXPECT=matched; output-sha256=048c64f47127642c2bb6fe4210525f8fd787b959012b49f80e23d76293a3d9e4; output-bytes=17; shell=/bin/sh; cwd=/Users/maxime/Documents/Technical/Projects/Harness Agents V1/yaobet; path=fb2e6f61e154/18 entries

- [x] G5: lease holds: the branch diff stays inside OWNS
  CHECK: bash .unlazy/yaobet-rebuild/checks/lease.sh F2
  EXPECT: LEASE OK F2
  EVIDENCE: rc=0 LEASE OK F2 10 paths. PM back-fill fresh at wt rb-F2@4416dac base=ebd8a70 (scratchpad bf/F2-G5.out), run on main c1c9a08.

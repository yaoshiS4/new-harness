# Gates: Yaobet Wine-Gold migration (root audit)

Scope: every shard in `PLAN.md` has been merged into `main` with `--no-ff`. These gates are the delivery audit for `docs/design/ADR-003-wine-gold.md` under owner decisions D-DS1..D-DS15 and PM rulings R1-R4 (`docs/design/DS-WINE-GOLD-REVIEW.md` §5). Run them in order from a clean checkout of `main` with `node_modules` present. `YB_DS_BASELINE` defaults to `~/.cache/yaobet-ds/baseline` (D-DS11): `export YB_DS_BASELINE="${YB_DS_BASELINE:-$HOME/.cache/yaobet-ds/baseline}"`. Each VERIFY line is a runnable command or a named reviewer, and EXPECT is the exact pass line. Anything else is a `Fail:` routed to the owning shard. Pixel parity with the original app (rebuild GATES A5/A6) is retired by D-DS1 and is not run.

- [x] G1: every shard branch is merged into `main`
  VERIFY: L="ds-sc ds-s0 ds-sp ds-s1 ds-s2 ds-s3 ds-s4 ds-s5 ds-s6a ds-s6b ds-sg"; if git rev-parse -q --verify ds-s7a >/dev/null; then L="$L ds-s7a ds-s7b"; else L="$L ds-s7"; fi; M=0; for b in $L; do if git merge-base --is-ancestor "$b" main; then :; else printf 'MISSING %s\n' "$b"; M=1; fi; done; test "$M" = 0 && echo MERGE_CHECK_DONE
  EXPECT: MERGE_CHECK_DONE as the only line (12 branches, or 13 when S7 split under R4)
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `MERGE_CHECK_DONE` as the only line.

- [x] G2: static checks: token lint and its self-test, lint, route types, types, build
  VERIFY: npm run lint:tokens && npm run lint:tokens:self-test && npm run lint && npx next typegen && npx tsc --noEmit && npm run build > /tmp/yb-ds-root-build.log 2>&1 && echo STATIC_OK
  EXPECT: STATIC_OK
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `STATIC_OK`.

- [x] G3: the build lists every inventory route; the class rules, the class census and the CSS file census are clean over `src/`
  VERIFY: node scripts/verify-routes.mjs --build-log /tmp/yb-ds-root-build.log && npm run lint:rules && npm run lint:rules:self-test && npm run lint:classes && npm run lint:classes:self-test && bash .unlazy/yaobet-rebuild/checks/census.sh && echo RULES_OK
  EXPECT: RULES_OK
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `INVENTORY OK 26/26`, `RULES OK 243 files`, `RULES_OK`. The earlier run at 98ae59c failed with 3 hits; fixed by the ds-sl merge (520286f).

- [x] G4a: every rebuild leaf check still passes, so a by-design break cannot hide. This covers the 29 static checks (PLAN.md `STATIC`) and the 13 served ones. Retired and not run: `orig-boxes.sh` (D-DS1). Helpers: `lib.sh`, `fetch.sh`, `lease.sh`, `no-dev-toggle.sh` (inside I1), `fonts-preflight.sh`.
  VERIFY: bash .unlazy/yaobet-ds/checks/static.sh && for c in R3 R4 R5 R6 R7 R8 S6 S7 S8 U3 U4 U5 U7; do bash .unlazy/yaobet-rebuild/checks/$c.sh || exit 1; done && echo LEAF_CHECKS_OK
  EXPECT: STATIC OK 29/29, 13 x CHECKS OK, then LEAF_CHECKS_OK
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `STATIC OK 29/29`, 13 x `CHECKS OK`, `LEAF_CHECKS_OK`.

- [x] G4b: the rebuild checks, token-lint and genplan.py changed only at owner-approved pins (D-DS6, D-DS9, D-DS12, D-DS14)
  VERIFY: git diff -U0 635a4dc main -- .unlazy/yaobet-rebuild/checks .unlazy/yaobet-rebuild/genplan.py scripts/token-lint.mjs | rg '^(\+\+\+|@@)' > /tmp/yb-ds-pins.diff; node -e 'const fs=require("fs");const allow=fs.readFileSync(".unlazy/yaobet-ds/checks/pins.txt","utf8").split("\n").filter(Boolean).map(r=>{const m=r.match(/^(.+):(\d+)(?:-(\d+))?$/);return {f:m[1],a:+m[2],b:+(m[3]||m[2])}});let f="",bad=0,n=0;const fail=g=>{bad++;console.log("Fail: pin | Expected: allowed range | Got: "+g)};for(const l of fs.readFileSync("/tmp/yb-ds-pins.diff","utf8").split("\n")){if(l.startsWith("+++ ")){const p=l.slice(4);if(p==="/dev/null"){f="";fail("deleted file")}else{f=p.replace(/^b\//,"")}continue}const h=l.match(/^@@ -(\d+)(?:,(\d+))?/);if(!h)continue;n++;const a=+h[1],len=h[2]===undefined?1:+h[2],b=len?a+len-1:a;if(!allow.some(r=>r.f===f&&a>=r.a&&b<=r.b))fail(f+":"+a+"-"+b)}if(n<10)fail(n+" hunks, at least 10 required");console.log(bad?"PINS FAILED":"PINS OK "+n);process.exit(bad?1:0)'
  EXPECT: PINS OK n with n >= 10 (9 check pins plus the SG mirrors). Rows match by exact full path (`r.f === f`). A deleted file (`+++ /dev/null`) FAILS. An empty or short diff FAILS rather than passing on zero hunks. Every hunk's old range is inside a `pins.txt` row: the 19 SC rows plus the PM-appended boxes.json rows. oracle-review compares each old value against its new value from the shard returns.
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `PINS OK 38`.

- [x] G5: token parity: every MAPPING.md §2-§10 data row and every overlay token is present in the built CSS with its mapped value; every `--wg-color-*` equals its JSON value; the VIP block is byte-equal to 635a4dc
  VERIFY: set -o pipefail; test -f .next/BUILD_ID && R=$(awk '/^## 2\./{on=1} /^## 11\./{on=0} on && /^\|/ {n++} on && /^\|[-| :]+\|$/ {t++} END {print n-2*t}' docs/design/wine-gold/MAPPING.md) && O=$(jq '[paths(scalars) | map(tostring) | join(".") | select(endswith("$value"))] | length' docs/design/wine-gold/overlay.proposal.json) && N=$((R+O)) && node .unlazy/yaobet-ds/checks/parity.mjs | tee /tmp/yb-ds-parity.out && rg -qx 'OBSIDIAN OK 20/20' /tmp/yb-ds-parity.out && test "$(tail -n 1 /tmp/yb-ds-parity.out)" = "PARITY OK $N/$N"
  EXPECT: one count line per section; `OBSIDIAN OK 20/20` (the 16 ladder names of MAPPING.md:158 plus the 4 old win/loss/error/focus values, D-DS8); then `PARITY OK N/N` as the last line, with N computed independently (on 2026-11-07: 192 MAPPING data rows + 109 overlay tokens = `PARITY OK 301/301`)
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `OBSIDIAN OK 20/20`, `PARITY OK 301/301`.

- [x] G6: contrast: every overlay pair meets its class (text 4.5:1, UI 3:1; decorative pairs listed by name), every pair token resolves from `.next/static`, and the win/loss luminance difference |La − Lb| / max(La, Lb) is at most 5% (TOKENS.md rule 4.1)
  VERIFY: test -f .next/BUILD_ID && node .unlazy/yaobet-ds/checks/contrast.mjs
  EXPECT: CONTRAST OK n/n with n >= 55, then WINLOSS OK <pct> with pct <= 5
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `CONTRAST OK 55/55`, `WINLOSS OK 0.2%`.

- [x] G7: tier rule: only the three definition files read `--wg-*`; primitives hold literals; component tokens read semantic tokens (TOKENS.md:14, ADR-003 §3.3)
  VERIFY: bash .unlazy/yaobet-ds/checks/tier.sh
  EXPECT: CHECKS OK tier
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `CHECKS OK tier 167/167`.

- [x] G8: no new colour value: every colour (hex, rgb, hsl, normalised to RGBA) on a line added since 635a4dc in `src/styles/{tokens,themes,brands}.css` is a DS or overlay value, the single D-DS5 loss primitive included, or a 635a4dc value of those three files (D-DS2, D-DS5)
  VERIFY: bash .unlazy/yaobet-ds/checks/newhex.sh
  EXPECT: CHECKS OK newhex
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `CHECKS OK newhex 52/52`.

- [x] G9: zero raw hex and zero numeric rgb/hsl literals in `src/` outside the three token definition files, comments included. The only exceptions are the 4 allow rows of PLAN.md SC: themeColor 1, coverArt doc comment 2 (R6), CardArt hsl 16, PackStage hsl 10 (D-DS13). Each count is the number of hex.sh pattern hits in the file. The D-DS13 hsl lines are byte-unchanged since 635a4dc.
  VERIFY: bash .unlazy/yaobet-ds/checks/hex.sh && test "$(rg -c -v '^(#|$)' .unlazy/yaobet-ds/checks/hex-allow.txt)" = 4 && git diff 635a4dc HEAD -- src/components/collection/CardArt.tsx src/components/collection/PackStage.tsx > /tmp/yb-ds-G9-hsl.diff && D=$(rg -c '^[-+][^-+].*hsl\(' /tmp/yb-ds-G9-hsl.diff); rc=$?; test "$rc" = 1 && test -z "$D" && echo HEX_ALLOW_4_HSL_SAME
  EXPECT: CHECKS OK hex, then HEX_ALLOW_4_HSL_SAME. git diff writes to a file first, so a git error stops the chain and FAILS (in a pipe, rg's exit 1 on empty input would hide it). rg exits 1 with empty output on zero changed hsl lines, which is the pass case; rc 0 or rc 2 FAILS.
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `CHECKS OK hex 9/9`, `HEX_ALLOW_4_HSL_SAME`.

- [x] G10: fonts: Be Vietnam Pro, Playfair Display and Inter load through next/font with the vietnamese subset at 400/500/600; none of the three at 700/800; Montserrat stays for emerald (D-DS3, D-DS8)
  VERIFY: test -f .next/BUILD_ID && bash .unlazy/yaobet-ds/checks/fonts.sh && rg -l --no-ignore --hidden -g '*.css' 'U\+1EA0-1EF9' .next/static | rg -q . && echo FONT_SUBSET_OK
  EXPECT: CHECKS OK fonts, then FONT_SUBSET_OK
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `CHECKS OK fonts 21/21`, `FONT_SUBSET_OK`.

- [x] G11: every inventory URL answers as specified (pages 200, the four redirects with meta refresh, soft 404s with noindex)
  VERIFY: node scripts/with-dev-server.mjs --port 3163 -- node scripts/verify-routes.mjs --base http://localhost:3163
  EXPECT: ROUTES OK 43/43
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `ROUTES OK 43/43`.

- [x] G12: the shell boxes match the re-pinned `boxes.json` within its unchanged 1 px tolerance at every width, after the fonts load, and the home grid has its columns and fillers (A5b kept by D-DS1, re-pinned by D-DS12)
  VERIFY: node scripts/with-dev-server.mjs --port 3163 -- node scripts/box-check.mjs --boxes .unlazy/yaobet-rebuild/checks/boxes.json && test "$(git show 635a4dc:.unlazy/yaobet-rebuild/checks/boxes.json | jq .tolerance_px)" = "$(jq .tolerance_px .unlazy/yaobet-rebuild/checks/boxes.json)" && echo TOLERANCE_KEPT
  EXPECT: BOXES OK, then TOLERANCE_KEPT. Every changed boxes.json line is in the reviewed S0 box list (G4b).
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `BOXES OK`, `TOLERANCE_KEPT`.

- [x] G13: mock auth: fresh load tiered; register leads to level-0; log in leads to tiered; reload stays tiered; Escape closes the modal and focus returns to the trigger
  VERIFY: node scripts/with-dev-server.mjs --port 3163 -- node scripts/auth-flow.mjs
  EXPECT: AUTH FLOW OK 5/5
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `AUTH FLOW OK 5/5`.

- [x] G14: integration: SSR strings, html attributes, theme-color, production build without the DEV toggle, boxes and auth (rebuild I1, pins updated under D-DS9)
  VERIFY: bash .unlazy/yaobet-rebuild/checks/I1.sh
  EXPECT: CHECKS OK I1
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `CHECKS OK I1 36/36`.

- [x] G15: hygiene: no tag family and no legal term in `src/` outside the approved rows; the dependency set is exact with Playwright pinned; no committed runtime artefacts
  VERIFY: bash .unlazy/yaobet-rebuild/checks/hygiene.sh
  EXPECT: CHECKS OK hygiene
  EVIDENCE: 2026-11-10, main de4102c, run serially, rc=0: `CHECKS OK hygiene 5/5`.

- [x] G16: new baseline: 72 shots at m375 and d1440 in both auth states, captured once from `main` after the SG merge, with the state checks holding; sha256 manifest committed (D-DS1, D-DS11)
  PRODUCE (once, PM): B="$YB_DS_BASELINE"; rm -rf "$B" && mkdir -p "$(dirname "$B")" && SHOTS_OUT="$B" node scripts/with-dev-server.mjs --port 3107 -- node scripts/capture-shots.mjs > /tmp/yb-ds-baseline.log 2>&1; cp /tmp/yb-ds-baseline.log "$B/capture.log" && (cd "$B" && shasum -a 256 *.jpg) > .unlazy/yaobet-ds/checks/baseline.sha256
  VERIFY: B="$YB_DS_BASELINE"; test "$(rg -c 'final check: ok' "$B/capture.log")" = 4 && rg -q 'DONE 72' "$B/capture.log" && test "$(rg -c . .unlazy/yaobet-ds/checks/baseline.sha256)" = 72 && (cd "$B" && shasum -a 256 -c "$OLDPWD/.unlazy/yaobet-ds/checks/baseline.sha256" > /dev/null) && echo BASELINE_OK
  EXPECT: BASELINE_OK (the manifest is committed only after G19 passes; any later revert re-runs G16-G19)
  EVIDENCE: 2026-11-10, main c1bd492: PRODUCE then VERIFY gave `capture rc=0` and `BASELINE_OK` (72-row manifest, shasum -c clean). It was recaptured after the 375 fit merge, superseding the 5c8615b baseline.

- [x] G17: the baseline is reproducible: a fresh capture matches it outside the time-based masks
  VERIFY: rm -rf .shots && node scripts/with-dev-server.mjs --port 3107 -- node scripts/capture-shots.mjs > /tmp/yb-ds-capture.log 2>&1 && rg -q 'DONE 72' /tmp/yb-ds-capture.log && node scripts/shot-diff.mjs --ref "$YB_DS_BASELINE" --got ./.shots --masks .unlazy/yaobet-rebuild/checks/shot-masks.json --justify .unlazy/yaobet-ds/checks/shot-justify.json
  EXPECT: SHOTS OK 72/72 (`shot-justify.json` has no rows)
  EVIDENCE: 2026-11-10, main c1bd492: `SHOTS OK 72/72`, rc=0, against the c1bd492 baseline. Re-run at de4102c after the ds-sl class fix: `SHOTS OK 72/72`, rc=0, so 375 and 1440 are unchanged.

- [x] G18: 8 UI states on the key screens (`/` with the auth modal, `/vi-tien`, `/vip`, `/cua-hang`, `/bo-suu-tap`) at m375 and d1440, plus "tạm dừng" on money surfaces
  VERIFY: STATES_OUT=/tmp/yb-ds-states node scripts/with-dev-server.mjs --port 3164 -- node .unlazy/yaobet-ds/checks/states.mjs; then frontend-qc reviews every captured state and every `unreachable:` row
  EXPECT: STATES DONE n, plus a frontend-qc PASS that names each `unreachable` row as accepted or as a `Fail:` routed to its shard
  EVIDENCE: 2026-11-10, main c1bd492: run 7 (`/tmp/yb-ds-states7`) gave rc=0, `STATES DONE 60`, 30 `unreachable:` rows; no errors or timeouts in the log. frontend-qc PASS named all 30 rows ACCEPT: 29 identical to accepted run-6 rows, plus `d1440 /vi-tien loading` (the same loading race on the fast mock; the route is not in the c1bd492 diff). The 18 /cua-hang rows are byte-identical to run 6. Run 6 (5c8615b: DONE 59, 31 unreachable) had a QC PASS earlier.

- [x] G19: baseline review (D-DS1): designer and frontend-qc review every pair of the G16 capture at 375 and 1440 against this checklist:
  - section order, the Wine-Gold surfaces and text steps, gold as accent only (TOKENS.md rule 4.2);
  - the gold primary on login, submit and Register (D-DS7); the header on the page canvas (D-DS26, 2026-11-10, replaces the wine header of D-DS7);
  - the destructive button (D-DS19, D-DS23; `ui.css:230-239`) at `LogoutButton.tsx:40` and `MessageCenter.tsx:101`; the header has no danger caller since `Header.tsx:152` became the Register primary (D-DS24);
  - ivory gradients, 8 px content radius, 4 px controls, the return of shadows, emerald on Montserrat including `--brand-font-display` (D-DS8);
  - no Playfair below 26 px (MAPPING.md:230);
  - the D-DS13 card art unchanged except for its `#fff` lines.
  VERIFY: reviewers designer + frontend-qc; each returns PASS or `Fail: <route>@<width> | Expected | Got` routed to the owning shard
  EXPECT: PASS from both; the PM then commits `baseline.sha256`
  EVIDENCE: The full checklist got a PASS from both reviewers on the 5c8615b baseline (W9-QC, W9-DES). Its 3 Fails were /gioi-thieu@375 and /dai-ly@375 (ReferralKpiHeader) and /cua-hang@375 (StoreTerms). They were fixed in c1bd492 (eac0cd9, 39da58e). On 2026-11-10, designer and frontend-qc re-read all 9 affected c1bd492 images: PASS from both, prior Fails gone, no 1440 regression (W9-RECHK). Image reads were temporarily allowed by the owner (option A) and blocking has been restored.

- [x] G20: designer audit (`.claude/agents/designer.md:18` finish gate): purpose clear in 3 s on each key screen, every control works, 8 UI states covered, no HARD BAN from the anti-slop taxonomy
  VERIFY: reviewer designer, using G16-G18 output
  EXPECT: PASS with one line per key screen
  EVIDENCE: The designer passed every key screen at 5c8615b except /cua-hang@375 (W9-DES). That screen was fixed in c1bd492. On 2026-11-10 the designer recheck (W9-RECHK) passed /cua-hang, /gioi-thieu and /dai-ly at both 375 and 1440.

- [x] G21: frontend-qc anti-slop pass on the full diff: no nested cards L-01, card soup L-13, badge proliferation D-09, ellipsis clipping L-16, icon fatigue T-12, category over-expressing W-07 (CLAUDE.md:21); M-03 states; money never gold; one shadow level per branch
  VERIFY: reviewer frontend-qc over `git diff 635a4dc main -- src` and the G16 capture
  EXPECT: PASS; every finding is a `Fail:` routed to a shard and re-verified
  EVIDENCE: 2026-11-10, main c0342d0 (src at de4102c): frontend-qc PASS over `git diff 635a4dc main -- src` (116 files, +2417/-1144), with no findings introduced by the diff. L-01, L-13, D-09, L-16, T-12, W-07 and M-03 PASS; money is never gold (gold only on the jackpots D-DS25, points and the unused odometer); one shadow level per branch (ui.css:326-330). PM ruling: G21 is scoped to the diff. Five older issues already present at 635a4dc go to the backlog: P-1 L-01 li-in-Card at SecurityCenter.tsx:167 and LinkedAccounts.tsx:55,108; P-2 L-16 ellipsis at shell.css:1149, MemberSidebar.tsx:247, ProfileBasic.tsx:89; P-3 T-12 per-row icons at LinkedAccounts.tsx:57,110; P-4 the VipFaq glyph chevron; P-5 tap targets under 44px at MemberSidebar.tsx:251 and SecurityCenter.tsx:223.

- [x] G22: PM audit: each owner decision D-DS1..D-DS15 and each ruling R1-R4 is traced to path:line on `main` (ADR-003 §5 table)
  VERIFY: reviewer PM. For each decision or ruling, cite at least one `path:line` on `main` plus the gate that proves it:
    - D-DS1: G12-G19.
    - D-DS2: G8.
    - D-DS3: G10.
    - D-DS4 and R1: the themes.css, brands.css and VIP blocks.
    - D-DS5: G6 and the `--loss` line.
    - D-DS6, D-DS9, D-DS14: G4b.
    - D-DS7: the ui.css, shell.css and auth lines.
    - D-DS8: one line per default.
    - D-DS10: layout.tsx without the attribute.
    - D-DS11: G16.
    - D-DS12: G12 and SP.
    - D-DS13: G9.
    - D-DS15: the `ds-base` commit.
    - R2: no `--surface-canvas` declared.
    - R3: no checkbox component added.
    - R4: G1.
  EXPECT: 19/19 traced; no decision without a path:line
  SCOPE 2026-11-09: extended to D-DS16..D-DS25 and R5..R16 (41 rows) in `docs/design/wine-gold/G22-TRACE.md`
  EVIDENCE: 2026-11-09, main 4a66d3e: 41/41 traced in docs/design/wine-gold/G22-TRACE.md. The trace was collected read-only by frontend-explorer; the PM re-read 8 citations on main and all matched (Header.tsx:152-165, QuickActionRail.tsx:55-61, ui.css:230-239, tokens.css:66 and :156, brands.css:56, shell.css:1855-1861, typography.css:45-56). D-DS12 is traced through task.md:24 and :37 only, because the box pins sit in a check file. 5 stale doc line references are listed there; the code is correct.

- [x] G23: oracle-review on the full diff `635a4dc..main`: leases held per shard, pins only (G4a/G4b), no weakened assertion, no fabricated token, scope drift within the spawn-contract budget
  VERIFY: reviewer oracle-review
  EXPECT: APPROVE
  EVIDENCE: 2026-11-10, main c0342d0 (src at de4102c): oracle-review APPROVE (0.90), 0 blocking, 3 NIT. All 26 first-parent merges stayed inside their leases; the 35 direct commits on main touch no src/**. genplan.py hunks and the changed rebuild check files match the pin rows; `PINS OK 38`. rebuild-rules.allow.json stays `{}`; package.json, eslint, tsconfig and test files are unchanged; scripts/ is additive only. All 71 `--wg-*` declarations trace to the JSON files. Scope drift 0%. NIT: the ledger is inconsistent on the scripted .mjs edit (0e96e78); code is 1.79x the old size without the licence files; status.log is to be removed at teardown.

- [x] G24: hallucination-auditor: every `--wg-*` value exists in `design-tokens.all.json` or `overlay.proposal.json`; every new name is in ADR-003 §3.4; no Vietnamese copy changed; no invented number, name or legal text; every path:line cited in ADR-003, PLAN.md and the GATES evidence resolves
  VERIFY: reviewer hallucination-auditor
  EXPECT: PASS
  EVIDENCE: 2026-11-10, main c0342d0 + doc fixes: hallucination-auditor PASS on recheck. 71/71 `--wg-*` values are in the JSON files; ADR-003 §3.4 covers 86/86 new names after adding the R7/R10 names at :57; no Vietnamese copy changed (the only added copy, "tỷ ₫/triệu ₫", is D-DS18); no invented numbers, names or legal text (OFL is D-DS17); 202/204 citations resolve, and the 2 that do not are labelled as scratch. The first pass failed on ADR-003:57 (5 names missing) and G22-TRACE.md:68 (ease count 3, should be 4); both are fixed.

- [x] G25: teardown: `docs/STATUS.md` records the delivered Wine-Gold migration (Current State, Next Actions, a Verification pointer to this file); the working tree holds no runtime artefacts
  VERIFY: rg -q 'Wine-Gold' docs/STATUS.md && rg -q 'yaobet-ds/GATES.md' docs/STATUS.md && A=$(git status --porcelain -- . ':!.claude/worktrees' | rg -c -e '\.(log|sqlite|db|tsbuildinfo)$|(^|/)\.?shots/'); rc=$?; test "$rc" = 1 && test -z "$A" && echo TEARDOWN_OK
  EXPECT: TEARDOWN_OK
  EVIDENCE: 2026-11-10, main b34924c plus this commit, rc=0: TEARDOWN_OK; STATUS.md records the delivery (Current State, Next Actions, Verification); phase-1 status.log removed; ds-* worktree removal awaits the owner (STATUS.md Next Actions 1)

# Plan: Yaobet migration to the Wine-Gold design system

Scope: yaobet-ds (this file: .unlazy/yaobet-ds/PLAN.md, hand-written by sa, revision 2 after critical-planner gate 1; the lease ledger is `task.md`)
Depth: tree 1 (root → 12 builder shards, 13 if S7 splits; root integration and audits in `GATES.md`)
Mode: orchestrated, Path 3 (long-horizon), base `ds-base` 2dc3b92. Diffs that deliberately compare against the pre-migration tree still use 635a4dc; the docs-only commit 2dc3b92 changes no `src/`, checks or scripts.

## Contract

- Goal: `src/` renders the Wine-Gold design system (`docs/design/wine-gold/`, with the owner-approved overlay) on every route at 375 and 1440 and passes `GATES.md`. Architecture: `docs/design/ADR-003-wine-gold.md` (alias strategy). Builders read it in full before writing code.
- Binding docs, in precedence order: `docs/design/DS-WINE-GOLD-REVIEW.md` §5 (D-DS1..D-DS15 and PM rulings R1-R4; never re-opened) → `docs/design/ADR-003-wine-gold.md` → `docs/design/wine-gold/MAPPING.md` + `overlay.proposal.json` (the values) → `docs/design/TOKENS.md` §4 → `docs/rebuild/ADR-002.md` (CSS architecture, unchanged except where ADR-003 says).
- Names stay; values move. No existing custom-property name is deleted or renamed (ADR-003 §3.1, R1, R2). New names come only from the ADR-003 §3.4 list. A builder who needs any other token stops and reports `Fail: MAPPING.md | Expected: <token> | Got: none` (TOKENS.md rule 4.4).
- No new colour value. Every colour in the three definition files (`src/styles/{tokens,themes,brands}.css`, token-lint.mjs:61) is a DS or overlay value, or a value already present at 635a4dc (D-DS2, D-DS5). Outside those files, `src/` holds no hex and no numeric `rgb()/rgba()/hsl()` literal (GATES G9). `checks/hex-allow.txt` lists the only exceptions: the layout themeColor, the coverArt doc comment, and the D-DS13 card-art `hsl()` lines.
- No TSX shadow, ring, gradient, `bg-(--x)` or `rounded-full` classes; `scripts/rebuild-rules.mjs:15-27` stays unchanged. Shadows and the gold sheen are applied in `ui.css` or the area CSS. Radius changes through the `--radius-*` values.
- Check pins: a rebuild check changes only at an owner-approved pin (D-DS6, D-DS9, D-DS12, D-DS14; ADR-003 §3.9), and only inside the shard whose change breaks it. The before → after evidence goes in the return. `.unlazy/yaobet-rebuild/genplan.py` is touched by SG only. Every other assertion of every static rebuild check still runs in every shard (`STATIC` below).
- Content: Vietnamese copy does not change. No legal or regulatory text. No plan, wave, shard, gate or ADR tags in `src/` comments (hygiene.sh:7 matches `ADR-[0-9]+` and `Wave [0-9]`). A comment that quotes an old hex or contrast ratio is rewritten to name the token instead.
- Ownership: each shard's `allowed_files:` block is its lease: one exact path or one `dir/**` per entry. Leases are disjoint inside a wave. Files no shard owns are expected to stay unchanged: `src/app/globals.css`, `src/styles/{reset,stub}.css`, `src/app/providers.tsx`, `src/app/{ho-tro,tro-giup,tai-app,phong-cach}/**`, and `src/lib/**` except the leased dirs. If one of them needs a change, the builder stops with `next_action: expand lease: <path>`.
- Launch: background `Agent(subagent_type: <role>)`. The prompt starts with `Role: <role>` + the spawn contract, pastes the shard's `allowed_files:` YAML verbatim and stays under 6,000 chars. The PM creates the worktree `.claude/worktrees/ds-<id>` on branch `ds-<id>` (lower case, e.g. `ds-s6a`) from current `main`. Then, in the worktree, the PM runs `bash .unlazy/yaobet-rebuild/checks/fonts-preflight.sh && bash .unlazy/yaobet-ds/checks/fonts-preflight.sh` (each worktree starts with an empty `.next/cache`) and proves `npm run lint` + `npx tsc --noEmit` before dispatch. Every builder Bash call starts with `cd <worktree> || exit 1`. At most 2 builders at once, at most 4 agents per wave. The PM merges a VERIFIED shard into `main` with `--no-ff` before the next wave starts.
- Review of every return. Stage A: the PM re-runs the shard's `verification_cmd` in the worktree and needs a fresh `exit_code: 0`, and checks that `git diff --name-only main...ds-<id>` stays inside the lease. Stage B: `frontend-qc` reviews the shard's routes at 375 and 1440 (`SHOTS_OUT=/tmp/yb-ds-<id>-shots` capture) for anti-slop and for the D-DS7/D-DS8 points the shard owns. Each `Fail:` goes back to the same shard.
- Builds: `npm run build` writes to `/tmp/yb-ds-<id>-build.log`; never pipe it through `head` or `rg -m`. `next build` needs Google Fonts (rebuild PLAN.md:43). Without them `next dev` falls back silently to a local font, and the box check then fails for no real reason. A font-fetch failure is an environment stop, not a code fix.
- Dev servers: never shared. Each served check runs through `scripts/with-dev-server.mjs --port <port>`. Shard ports: SC 3150, S0 3151, SP 3152, S1 3153, S2 3154, S3 3155, S4 3156, S5 3157, S6a 3158, S6b 3159, S7 or S7a 3160, S7b 3161, SG none; root 3163-3165. The rebuild served checks keep their built-in ports (R3 3134, R4 3138, R5 3135, R6 3136, R7 3137, R8 3139, S6 3126, S7 3127, S8 3128, U3 3130, U4 3132, U5 3133, U7 3131, I1 3140-3141). No two shards that run the same one share a wave.
- DS checks live in `.unlazy/yaobet-ds/checks/`, written by SC and never edited by a later shard. Each sources `.unlazy/yaobet-rebuild/checks/lib.sh` and prints `Fail: <id> | Expected | Got` per failure, and its OK line only on a full pass. Two exceptions: the PM appends the reviewed `boxes.json` rows to `pins.txt` and commits `baseline.sha256`. Both are data, not code.

### Preconditions (before SC)

1. D-DS15: the PM makes one local commit on `main` (no push) holding only `docs/design/ADR-003-wine-gold.md`, `docs/design/DS-WINE-GOLD-REVIEW.md`, `docs/design/wine-gold/**` and `.unlazy/yaobet-ds/{PLAN,GATES,task}.md`, then tags it `ds-base`. Done: `ds-base` = 2dc3b92. Later revisions of these docs are committed the same way (docs only) before SC is dispatched. Every worktree branches from `main` at or after `ds-base`, so builders can read the binding docs.
2. W1-loss passed Stage A: MAPPING.md:3 reads "approved", `--loss` maps to the overlay `primitive.color.red.300` (MAPPING.md:83), and overlay.proposal.json parses (109 tokens).
3. Decided, nothing to approve: the extra pins (D-DS9, D-DS14), the box re-pin (D-DS12), the baseline location `~/.cache/yaobet-ds/baseline` (D-DS11) and the card-art exception (D-DS13). S7 may split into S7a/S7b (R4): the PM decides at dispatch.

### Shared verification

- `BASE(<id>)`: `npm run lint && npx tsc --noEmit && npm run build > /tmp/yb-ds-<id>-build.log 2>&1 && node scripts/token-lint.mjs && node scripts/rebuild-rules.mjs src && node scripts/tw-unknown-classes.mjs src`
- `STATIC`: `bash .unlazy/yaobet-ds/checks/static.sh`. It runs the 29 static rebuild checks: F0 F1 F2 F3a F3b F4 F5 FTfix HF1 HF2 HF3 HF4 HF5 HF7 KF1 R1 R2 S1 S2 S3 S4 S5 S6fix U1 U2 U6 built-css census hygiene. It prints `STATIC OK 29/29`. Retired, and not run: `orig-boxes.sh` (it measures the original app, retired by D-DS1). Helpers, not checks: `lib.sh`, `fetch.sh`, `lease.sh` (per branch), `no-dev-toggle.sh` (runs inside I1) and `fonts-preflight.sh` (runs at worktree creation).
- `LEASE(<files>)`: `bash .unlazy/yaobet-ds/checks/hex.sh <files> && bash .unlazy/yaobet-ds/checks/tier.sh <files>`. The shard's own files hold zero hex or numeric colour-function literals outside the allow rows, and read no `--wg-*`.
- `BOX(<port>)`: `node scripts/with-dev-server.mjs --port <port> -- node scripts/box-check.mjs --boxes .unlazy/yaobet-rebuild/checks/boxes.json` (expects `BOXES OK`). Every shard after SP runs it against the re-pinned file (D-DS12).

## Dispatch table

| Wave | Shard | Role | Title | Needs | Port |
|---|---|---|---|---|---|
| W0 | SC | dev-fe | DS gate scripts | preconditions | 3150 |
| W1 | S0 | dev-fe | token layer, fonts, pins | SC | 3151 |
| W1b | SP | dev-fe (PM may choose) | boxes.json re-pin | S0 + box review | 3152 |
| W2 | S1 | designer | ui primitives (`ui.css`) | SP | 3153 |
| W2 | S2 | dev-fe | shell chrome | SP | 3154 |
| W3 | S3 | designer | home, sports, tiles, vertical | S1, S2 | 3155 |
| W3 | S4 | dev-fe | auth, wallet, account | S1, S2 | 3156 |
| W4 | S5 | designer | VIP | S1 | 3157 |
| W4 | S6a | dev-fe | collection | S1 | 3158 |
| W5 | S6b | dev-fe | lottery | S1 | 3159 |
| W5 | S7 (or S7a) | dev-fe | store, promo, contribution, restricted, referral, messages | S1, S4 | 3160 |
| W5b | S7b (only if split) | dev-fe | contribution, restricted | S1 | 3161 |
| W6 | SG | dev-fe | genplan.py mirrors | all above | — |
| W7 | root | PM + QC | baseline, states, `GATES.md` | all | 3163-3165 |

## Shards

### SC: DS gate scripts (W0, dev-fe)

```yaml
allowed_files:
  - .unlazy/yaobet-ds/checks/**
```

- `parity.mjs` reads MAPPING.md and overlay.proposal.json at run time. It resolves names through the `var()` chain in the built `.next/static` CSS, in cascade order: `:root` (tokens.css), then `[data-brand="yaobet"]` (brands.css:19-32), following the import order at F1.sh:16. `[data-theme]` is not applied, because D-DS10 removes the attribute. It handles each table data row of MAPPING §2-§10 by an explicit class:
  - Literal "New" cell: the resolved value equals it, after case and whitespace normalisation.
  - Range cell (`19-22px`): equals the `$value` of the overlay role named in "Maps to".
  - Value-plus-note cell (`#3D2312 bg`): the leading colour equals the resolved value of the token named in "Maps to".
  - `composite`: declared, with every inner `var()` resolving.
  - `keep`: equals the 635a4dc value.
  - `retired`: declared at the MAPPING value.
  - §3 emerald rows: resolved inside `[data-brand="emerald"]`.
  - MAPPING.md:158 obsidian names: the 16 ladder names are mapped back to the current names through the §2 "Maps to" column (R1) and resolved inside `[data-theme="obsidian"]`. They must equal the MAPPING.md:158 values, and the 4 old `--win/--loss/--error/--focus-ring` values must equal the 635a4dc tokens.css literals (D-DS8). The check prints `OBSIDIAN OK 20/20`; any other count FAILS.
  - §3 VIP table (MAPPING.md:162-177): `--vip-pal-*` is not introduced (R1, R2), so the VIP block of tokens.css must be byte-equal to 635a4dc.
  - §4 role ramp: equals the overlay `semantic.type.role.*` values.
  - §10 breakpoint rows: the `@media` width is still present.

  Every overlay token is declared under its ADR-003 §3.4 or MAPPING name, and every `--wg-color-*` equals its JSON `$value`. A row that fits no class FAILS; nothing is skipped. It prints one count line per section and the `OBSIDIAN OK 20/20` line, then `PARITY OK N/N` as its last line, where N = data rows + 109 (301 on 2026-11-07; GATES G5 recomputes N independently).
- `pairs.json` (a JSON array) + `contrast.mjs`: the designer's 55 pairs, vendored from scratch `wg-overlay-check.py.txt:42-43`, with classes text 4.5, UI 3.0 and decorative 1.0. Every pair token resolves from `.next/static` or the check FAILS; there is no JSON fallback. Win/loss uses relative luminance difference = |La − Lb| / max(La, Lb), at most 0.05 (TOKENS.md:116). Prints `CONTRAST OK n/n` and `WINLOSS OK <pct>`.
- `tier.sh [files]`: no file except the three definition files reads `var(--wg-`. Every `--wg-*` value is a literal or a next/font `--font-*` loader var. No `--wg-*` is declared outside the `:root` of tokens.css. The ADR-003 §3.4 component names never read `--wg-*`.
- `hex.sh [files]` + `hex-allow.txt`: `rg --pcre2` for `(?<!&)#[0-9a-fA-F]{3,8}(?![0-9A-Za-z_-])`, and for `rgba?\(|hsla?\(` with a numeric first argument, across `src/` outside the three definition files, comments included. The trailing lookahead keeps `url(#back-bg)` (CardArt.tsx:197) from matching `#bac`. Allow rows have the form `path<TAB>label<TAB>exact count`. The count is the number of hex.sh pattern hits in that file, not the number of lines that contain a substring. There are exactly 4 rows:
  - `src/app/layout.tsx` themeColor, 1 (the check asserts it equals the built page primitive).
  - `src/components/lottery/_internal/coverArt.ts` format doc comment, 2 (coverArt.ts:75 names `#abc` and `#aabbcc`; PM ruling R6).
  - `src/components/collection/CardArt.tsx` hsl, 16 numeric hits (D-DS13: lines 60, 63-66, 73-75, 112, 150, 161, 177, 193, 194, 198, 210). The file has 19 `hsl(` substring lines; the 3 template lines `hsl(${accent} …)` (58, 59, 100) have no numeric argument and are not pattern hits.
  - `src/components/collection/PackStage.tsx` hsl, 10 numeric hits (D-DS13: lines 184-186, 189-190, 201, 219, 251-253).

  A hit count that differs from its row FAILS. The D-DS13 lines must also stay byte-unchanged. `HSL_SAME` is `D=$(git diff 635a4dc HEAD -- src/components/collection/CardArt.tsx src/components/collection/PackStage.tsx | rg -c '^[-+][^-+].*hsl\('); rc=$?; test "$rc" = 1 && test -z "$D"`. rg exits 1 with empty output when there are zero matches, which is the pass case. rc 0 (a changed hsl line) or rc 2 (an error) FAILS. No line holds both `hsl(` and `#fff`, so moving the `#fff` paint cannot trip it.
- `newhex.sh`: every colour (hex, `rgb()`, `hsl()`, normalised to RGBA, case-insensitive) on a line added since 635a4dc in the three definition files appears in the union of `design-tokens.all.json`, `overlay.proposal.json` and the 635a4dc versions of tokens.css, themes.css and brands.css.
- `fonts.sh`: the built CSS has a `@font-face` with `U+1EA0-1EF9` and weights 400/500/600 for Be Vietnam Pro, Playfair Display and Inter. None of those three faces has 700 or 800, and Montserrat is present. `layout.tsx` imports `Playfair_Display` and `Inter` with `"vietnamese"` in subsets. The family names match case-insensitively; the exact next/font output is an assumption the builder confirms against a build.
- `fonts-preflight.sh`: Google Fonts reachability for Playfair Display and Inter, the same shape as `.unlazy/yaobet-rebuild/checks/fonts-preflight.sh:8-12`, which covers only Be Vietnam Pro and Montserrat.
- `static.sh`: runs the 29 checks listed under `STATIC`.
- `pins.txt`: the G4b allow list. Each row is `<full repo path>:<old-start>[-<old-end>]`, matched by exact path equality, never by a suffix. The 19 rows:
  - `.unlazy/yaobet-rebuild/checks/F1.sh:7`
  - `.unlazy/yaobet-rebuild/checks/F1.sh:12`
  - `.unlazy/yaobet-rebuild/checks/built-css.sh:9`
  - `.unlazy/yaobet-rebuild/checks/built-css.sh:13`
  - `.unlazy/yaobet-rebuild/checks/U1.sh:10-11`
  - `.unlazy/yaobet-rebuild/checks/I1.sh:10`
  - `.unlazy/yaobet-rebuild/checks/I1.sh:13`
  - `.unlazy/yaobet-rebuild/checks/F5.sh:7`
  - `.unlazy/yaobet-rebuild/checks/S3.sh:7`
  - `.unlazy/yaobet-rebuild/genplan.py:450`
  - `.unlazy/yaobet-rebuild/genplan.py:455`
  - `.unlazy/yaobet-rebuild/genplan.py:527-528`
  - `.unlazy/yaobet-rebuild/genplan.py:565`
  - `.unlazy/yaobet-rebuild/genplan.py:747`
  - `.unlazy/yaobet-rebuild/genplan.py:761`
  - `.unlazy/yaobet-rebuild/genplan.py:764`
  - `.unlazy/yaobet-rebuild/genplan.py:922-928`
  - `.unlazy/yaobet-rebuild/genplan.py:932`
  - `.unlazy/yaobet-rebuild/genplan.py:989-997`

  The PM appends one `.unlazy/yaobet-rebuild/checks/boxes.json:<range>` row per reviewed box after the S0 box review.
  Rows added after the plan was written are logged in `task.md` with their before and after values: the SP and S2 boxes.json rows, the SF row (D-DS16, D-DS17, with `a11-allow.txt`) and the W6 row `.unlazy/yaobet-rebuild/genplan.py:998`. On main there are 32 rows.
- `mirror.sh`: SG's check. For each pins.txt check row, it takes the new key literal from the check file on `main`: the integer after `eq` (F1.sh:7, :12, F5.sh:7), the `--canvas` declaration string (built-css.sh:9), each 64-hex hash (built-css.sh:13), the quoted pattern (U1.sh:10-11), the quoted html string (I1.sh:10, :13), the quoted expected file list (S3.sh:7), and each re-pinned box array (boxes.json). It then runs `rg -F` for that literal inside the new-side range of the genplan.py hunk whose old start equals the mirror row: :450, :455, :527-528, :565, :747, :761, :764, :922-928, :932, :989-997. The new-side range is taken from the `@@ -a,b +c,d @@` header, so a longer WOFF2 list cannot shift the lookups. A literal absent from its range FAILS. Prints `MIRROR OK n/n`.
- `states.mjs`: uses Playwright (pinned at hygiene.sh:13, no new dependency). On `/` (with the auth modal open), `/vi-tien`, `/vip`, `/cua-hang` and `/bo-suu-tap` at m375 and d1440, it captures default, hover, focus-visible, active, disabled, loading, empty and error (anti-slop M-03), plus "tạm dừng" on money surfaces (CLAUDE.md:22). A state the mock cannot reach is written to the manifest as `unreachable: <reason>`, never skipped silently. Prints `STATES DONE n`.
- `shot-justify.json` (`{"_note": ...}`, no rows).
- `verification_cmd`: `for f in parity contrast states; do node --check .unlazy/yaobet-ds/checks/$f.mjs || exit 1; done && for f in tier hex newhex fonts fonts-preflight static mirror; do bash -n .unlazy/yaobet-ds/checks/$f.sh || exit 1; done && jq -e 'type == "array" and length >= 55' .unlazy/yaobet-ds/checks/pairs.json && test "$(rg -c . .unlazy/yaobet-ds/checks/pins.txt)" = 19 && bash .unlazy/yaobet-ds/checks/fonts-preflight.sh && npm run build > /tmp/yb-ds-SC-build.log 2>&1 && bash .unlazy/yaobet-ds/checks/static.sh` (STATIC OK 29/29 on `ds-base`, proving that the list is green before any change). The return must also show the red run on 635a4dc after `npm run build`. parity, fonts and hex each FAIL with the expected reason, and contrast FAILS with `WINLOSS` at about 48% (old `--win`/`--loss` luminance 0.4576 vs 0.2362 → 48.4%). That proves the checks bite.

### S0: token layer, fonts and pins (W1, dev-fe, alone)

```yaml
allowed_files:
  - src/styles/tokens.css
  - src/styles/tw-theme.css
  - src/styles/brands.css
  - src/styles/themes.css
  - src/styles/typography.css
  - src/styles/motion.css
  - src/styles/keyframes.css
  - src/app/layout.tsx
  - scripts/token-lint.mjs
  - .unlazy/yaobet-rebuild/checks/F1.sh
  - .unlazy/yaobet-rebuild/checks/built-css.sh
  - .unlazy/yaobet-rebuild/checks/I1.sh
  - .unlazy/yaobet-rebuild/checks/F5.sh
```

1. tokens.css:
   - Add the `--wg-*` primitives `:root` block (ADR-003 §3.2).
   - Re-point every semantic name to `var(--wg-*)` per the MAPPING "New" column; component names keep reading semantic names (§3.3).
   - Add the §3.4 names.
   - Leave the VIP palette (tokens.css:307-345, byte-equal), the `keep` rows and `--qr-surface` unchanged.
   - Radius 12/16 → the 8 px step; `--lift/--shadow-2/--halo` → elevation 1/2/3 (MAPPING.md:275-290).
   - Re-tint the gradient composites to ivory through primitives (D-DS8).
   - Rewrite comments that quote old ratios.
2. brands.css: re-point the yaobet block per MAPPING.md:122-130, and add `--brand-accent-fg` to the yaobet and emerald blocks (MAPPING.md:138, :145). In the emerald block (brands.css:36-53), add `--brand-font-display` with the Montserrat stack of brands.css:51, so emerald does not inherit Playfair through tokens.css:362 (D-DS8). Emerald's other values stay unchanged.
3. themes.css: the obsidian block re-declares the old ladder (MAPPING.md:158, R1) and the old `--win/--loss/--error/--focus-ring` literals (D-DS8). These values are unused by default (D-DS10).
4. typography.css:
   - Display, h1 and h2 use the display face. h3-h6 and `[data-label="upper"]` use the body face (MAPPING.md:203); this also moves emerald h3-h6 off Montserrat (ADR-003 §3.5).
   - `letter-spacing` at :47 → 0 (D-DS8).
   - `font-weight: 800` at :60 → `var(--weight-bold)` (= 600, MAPPING.md:209).

   motion.css: reduced motion zeroes every duration token (MAPPING.md:308). keyframes.css changes only if a colour literal or duration needs a token.
5. tw-theme.css: one `--color-*` key per new colour name (§3.4). Existing keys stay untouched, and no `--shadow-*` key is added.
6. layout.tsx: load the fonts per ADR-003 §3.6, with Montserrat on `preload: false`. Remove `data-theme="obsidian"` (:79, D-DS10). Set themeColor (:69) to the page primitive value.
7. Pins, each logged before → after: `F1.sh:7` and `:12` take the fresh counts. `built-css.sh:9` takes the built `--canvas` declaration, copied verbatim from `.next/static`. `built-css.sh:13` takes the new woff2 list (D-DS9). `I1.sh:10` takes the new html attributes and `I1.sh:13` the new theme-color (D-DS9). `F5.sh:7` goes from `eq 2` to `eq 4` (D-DS14). token-lint.mjs: the diff is expected to be empty; any change must cite a removed name at `:29-55`.
8. Box log (D-DS12, not a pass/fail step): after the verification passes, run `BOX(3151) > /tmp/yb-ds-S0-box.log 2>&1` and return every moved box as `id | width | before | after`. The PM routes the list to designer + frontend-qc. `boxes.json` is not touched in S0.
- `verification_cmd`: `BASE(S0) && node scripts/token-lint.mjs --self-test && STATIC && bash .unlazy/yaobet-rebuild/checks/R3.sh && bash .unlazy/yaobet-rebuild/checks/R6.sh && node .unlazy/yaobet-ds/checks/parity.mjs && node .unlazy/yaobet-ds/checks/contrast.mjs && bash .unlazy/yaobet-ds/checks/newhex.sh && bash .unlazy/yaobet-ds/checks/fonts.sh && LEASE(src/styles/tokens.css src/styles/tw-theme.css src/styles/brands.css src/styles/themes.css src/styles/typography.css src/styles/motion.css src/styles/keyframes.css src/app/layout.tsx)`. The area CSS is not in the S0 lease check, because its comment hex (shell.css:25, home.css:741, auth.css:16) belongs to later shards.

### SP: boxes.json re-pin (W1b, dev-fe unless the PM picks another builder)

```yaml
allowed_files:
  - .unlazy/yaobet-rebuild/checks/boxes.json
```

Starts only after designer + frontend-qc have accepted the S0 box list and the PM has appended the matching rows to `pins.txt`. SP changes exactly the reviewed boxes to their "after" values, logged before → after. The tolerance stays at 1 px and no selector changes (D-DS12).
- `verification_cmd`: `BOX(3152) && git diff -U0 main -- .unlazy/yaobet-rebuild/checks/boxes.json | rg -c '^\+[^+]'` (the count equals the reviewed list).

### SF: self-hosted fonts (W1c, dev-fe, D-DS16)

```yaml
allowed_files:
  - src/app/layout.tsx
  - src/app/fonts/**
```

- The four families (Be Vietnam Pro, Playfair Display, Inter at 400/500/600; Montserrat at 700/800) load through next/font/local from WOFF2 files fetched once from the Google Fonts css2 API and committed under `src/app/fonts/`. Subsets: latin, latin-ext, vietnamese, each its own @font-face with Google's unicode-range and the real family name, so fonts.sh:11-31 stay valid. One OFL.txt per family and a SOURCE.md (URL, sha256, version per file).
- The `--font-*` variables and class names on `<html>` keep their names, so tokens.css and tier.sh are unaffected.
- `verification_cmd`: `BASE(SF) && LEASE(src/app/layout.tsx) && BOX(3162)`, then two clean builds (`rm -rf .next`) with an identical WOFF2 sha256 list, and STATIC failing only on the three D-DS16 pins (fonts-woff2-unchanged, fonts-import-*/fonts-subset-*, F5-font-subsets). The PM then edits the three pins and re-runs STATIC to 29/29.

### S1: ui primitives (W2, designer)

```yaml
allowed_files:
  - src/ui/**
  - .unlazy/yaobet-rebuild/checks/U1.sh
```

- `.ui-btn-primary` becomes the gold primary, with the sheen in CSS and the `--brand-on-accent` label (D-DS7). Secondary and ghost buttons use the secondary tokens.
- `.ui-btn-danger` (ui.css:213-220) reads `--brand-cta-accent`, which turns gold (MAPPING.md:120). Keep the `--shell` ink that MAPPING.md:120 measures, and list the danger consumers for G19.
- Card, modal and sheet bind `--card-bg`, `--modal-border` (defect 2) and `--modal-meta` (defect 1), with one shadow level per branch (L-01).
- MoneyValue's stale state uses `--status-paused-*` (TOKENS.md rule 4.3). Focus uses `--focus-ring` with the gap. Spinner and sweep durations read the motion tokens (MAPPING.md:307).
- Remove the ui.css literal lines: 10 in total, 9 hex in comments plus the `rgba()` at ui.css:896. Remove the comment hex at TileSkeleton.tsx:3.
- `U1.sh:10-11` take the new strings (D-DS6), logged.
- `verification_cmd`: `BASE(S1) && STATIC && LEASE(src/ui) && BOX(3153)`

### S2: shell chrome (W2, dev-fe)

```yaml
allowed_files:
  - src/styles/areas/shell.css
  - src/components/layout/**
  - .unlazy/yaobet-rebuild/checks/S3.sh
```

- The header uses the wine header surface through `--header-bg` (D-DS7). The register CTA ink at shell.css:1307 moves to `--brand-on-accent` (MAPPING.md:130). The danger button at `Header.tsx:152` turns gold; it is checked in Stage B and G19.
- `--space-7` at shell.css:1180 is checked against BOX. The QuickActionRail menus use `--shadow-2` (MAPPING.md:289).
- The QR art at QuickActionRail.tsx:381-382 moves to `currentColor` bound to `--qr-surface` and `--canvas`. `S3.sh:7` (the expected file list for `#fff|#171a21`) then takes the new value, logged before → after (D-DS14).
- Remove the comment hex in shell.css (14 lines) and at Footer.tsx:5, :9.
- `verification_cmd`: `BASE(S2) && STATIC && LEASE(src/styles/areas/shell.css src/components/layout) && BOX(3154)`

### S3: home, sports, tiles, vertical (W3, designer)

```yaml
allowed_files:
  - src/styles/areas/home.css
  - src/styles/areas/vertical.css
  - src/components/home/**
  - src/components/category/**
  - src/app/page.tsx
  - src/app/loading.tsx
  - src/app/[vertical]/**
```

Sports cards use `--odds-up|down`. Tiles use the tile surface and caption tokens. Hero and launcher show gold as accent only (TOKENS.md rule 4.2). Remove the comment hex at home.css:741 and HeroBand.tsx:11, :190.
- `verification_cmd`: `BASE(S3) && STATIC && bash .unlazy/yaobet-rebuild/checks/S6.sh && bash .unlazy/yaobet-rebuild/checks/S7.sh && LEASE(src/styles/areas/home.css src/styles/areas/vertical.css src/components/home src/components/category src/app/page.tsx src/app/loading.tsx 'src/app/[vertical]') && BOX(3155)`

### S4: auth, wallet, account (W3, dev-fe)

```yaml
allowed_files:
  - src/styles/areas/auth.css
  - src/styles/areas/member.css
  - src/components/auth/**
  - src/components/wallet/**
  - src/components/account/**
  - src/app/(member)/layout.tsx
  - src/app/(member)/tai-khoan/**
  - src/app/(member)/vi-tien/**
  - src/app/bao-mat/**
  - src/app/lich-su/**
```

- Fields use `--input-text|label|helper|error-text` and never rely on the hairline alone (defect 15). Tabs (WalletTabs, MemberSidebar) use `--tab-text-rest|active`.
- Login and submit use the gold `.ui-btn-primary`; Register uses the gold primary (D-DS7). The logout danger button at `LogoutButton.tsx:40` turns gold; it is checked in Stage B and G19. Money is never gold.
- `S4.sh:13` (`hasre S4-timer-700 '\b700\b'` on AuthModal.tsx) matches the timer value `}, 700);` at AuthModal.tsx:163, not a font weight. S4 leaves that line and that check alone, even though D-DS3 retires weight 700.
- Remove the auth.css literal lines: 5 in total, 4 hex in comments plus the `rgba()` at auth.css:350.
- `verification_cmd`: `BASE(S4) && STATIC && bash .unlazy/yaobet-rebuild/checks/U3.sh && bash .unlazy/yaobet-rebuild/checks/U4.sh && LEASE(src/styles/areas/auth.css src/styles/areas/member.css src/components/auth src/components/wallet src/components/account 'src/app/(member)/layout.tsx' 'src/app/(member)/tai-khoan' 'src/app/(member)/vi-tien' src/app/bao-mat src/app/lich-su) && node scripts/with-dev-server.mjs --port 3156 -- node scripts/auth-flow.mjs && BOX(3156)`

### S5: VIP (W4, designer)

```yaml
allowed_files:
  - src/styles/areas/vip.css
  - src/components/vip/**
  - src/lib/vip/**
  - src/app/vip/**
  - src/app/tier/**
  - src/app/cau-lac-bo/**
```

The VIP palette values do not change (D-DS4, R1). The display face applies only at 26 px and above; smaller headings use the body face (MAPPING.md:230). Radii follow MAPPING.md:278-280. Remove the comment hex at TierDeck.tsx:113. `LevelTable.tsx:106` is an HTML entity, not a colour, and stays.
- `verification_cmd`: `BASE(S5) && STATIC && bash .unlazy/yaobet-rebuild/checks/R3.sh && bash .unlazy/yaobet-rebuild/checks/R4.sh && LEASE(src/styles/areas/vip.css src/components/vip src/lib/vip src/app/vip src/app/tier src/app/cau-lac-bo) && BOX(3157)`

### S6a: collection (W4, dev-fe)

```yaml
allowed_files:
  - src/styles/areas/collection.css
  - src/components/collection/**
  - src/app/bo-suu-tap/**
  - src/app/dev/collection-ports/**
  - src/lib/collection/fixtures/**
```

The `#fff` paint in CardArt.tsx (10 lines) and PackStage.tsx (15 lines) moves to `currentColor` with the ivory text token (D-DS8). The `hsl()` illustration colours stay as they are (D-DS13; allow rows in `hex-allow.txt`). SVG weights 700/800 become 600 (D-DS3). The raw durations stay for now (ADR-003 §4 follow-up).
- `verification_cmd`: `BASE(S6a) && STATIC && bash .unlazy/yaobet-rebuild/checks/R7.sh && bash .unlazy/yaobet-rebuild/checks/R8.sh && LEASE(src/styles/areas/collection.css src/components/collection src/app/bo-suu-tap src/app/dev/collection-ports src/lib/collection/fixtures) && HSL_SAME && BOX(3158)` (`HSL_SAME` as defined under SC `hex.sh`)

### S6b: lottery (W5, dev-fe)

```yaml
allowed_files:
  - src/styles/areas/lottery.css
  - src/components/lottery/**
  - src/app/ve-so/**
```

The runtime reads of `--brand-accent`, `--brand-accent-2`, `--canvas` and `--text-hi` stay, because R6.sh:15-18 pins them. ScratchCardGame's display-face uses follow the 26 px rule.
- `verification_cmd`: `BASE(S6b) && STATIC && bash .unlazy/yaobet-rebuild/checks/R6.sh && LEASE(src/styles/areas/lottery.css src/components/lottery src/app/ve-so) && BOX(3159)`

### S7: store, promo, contribution, restricted, referral, messages (W5, dev-fe)

```yaml
allowed_files:
  - src/styles/areas/store.css
  - src/styles/areas/promo.css
  - src/components/store/**
  - src/components/promo/**
  - src/components/contribution/**
  - src/components/restricted/**
  - src/components/referral/**
  - src/components/messages/**
  - src/app/cua-hang/**
  - src/app/khuyen-mai/**
  - src/app/cuoc-hop-le/**
  - src/app/game-han-che/**
  - src/app/hoan-tra/**
  - src/app/(member)/gioi-thieu/**
  - src/app/(member)/dai-ly/**
  - src/app/(member)/tin-nhan/**
```

RedeemDialog uses the modal tokens. Tables use the line and surface steps, not nested cards (L-01). The contribution PageIntro display face follows the 26 px rule. `text-brand-cta-accent` at `MessageCenter.tsx:103` turns gold; it is checked in Stage B and G19.
- `verification_cmd`: `BASE(S7) && STATIC && for c in R5 S8 U5 U7; do bash .unlazy/yaobet-rebuild/checks/$c.sh || exit 1; done && LEASE(<the 16 lease paths above, dirs without /**>) && BOX(3160)`
- Split (R4), at the area boundary; the leases stay disjoint.
  - S7a (W5, port 3160) leases store.css, promo.css, components/{store,promo,referral,messages}/**, app/cua-hang/**, app/khuyen-mai/** and app/(member)/{gioi-thieu,dai-ly,tin-nhan}/**. It runs R5, S8 and U5.
  - S7b (W5b, port 3161) leases components/{contribution,restricted}/** and app/{cuoc-hop-le,game-han-che,hoan-tra}/**, plus src/styles/typography.css as widened at issue (`task.md`). It runs U7.
  - SX (W5b, after S7b) leases the header button pair, the right-rail jackpot ink and the flat decorative accents; its 6 files are listed in its `task.md` ISSUED row.

### SG: genplan.py mirrors (W6, dev-fe, alone)

```yaml
allowed_files:
  - .unlazy/yaobet-rebuild/genplan.py
```

Mirrors every pin merged on `main` at its generator line, emitting the same strings, and nothing else: :450 and :455 (F1), :527-528 (U1), :565 (S3), :747 (F5), :761 and :764 (I1), :922-928 (WOFF2 list), :932 (built-css canvas), :989-997 (boxes). genplan.py is never run.
- `verification_cmd`: `python3 -m py_compile .unlazy/yaobet-rebuild/genplan.py && bash .unlazy/yaobet-ds/checks/mirror.sh`. mirror.sh reads `git diff -U0 635a4dc HEAD -- .unlazy/yaobet-rebuild/genplan.py` and expects `MIRROR OK n/n`, with n = the number of key literals across the 9 check rows plus the boxes.json rows. Every hunk's old range must also be a `pins.txt` genplan row, which GATES G4b re-checks on `main`.

## Risks

1. Font hashes and network: `next build` without Google Fonts fails (rebuild PLAN.md:43). The two preflights run at every worktree creation.
2. Box moves (D-DS12): S0 is expected to move the footer height (boxes.json `footerHeight`: 675 at 375, 355 at 1440, tolerance 1) through `--lh-body` (shell.css:1506, :1557; MAPPING.md:196), and possibly the 321.3 px identity box (boxes.json `identity`) through weights and numerals (MAPPING.md:200, :202). If the review rejects a move, it goes back to S0 as a `Fail:`. `boxes.json` changes only in SP.
3. Silent value regressions: S0 changes no consumer, so G5/G6 (parity, contrast) are the only proof. The PM reads both outputs section by section.
4. An unlisted static rebuild check may break by design. Then the shard stops and the PM asks the owner for a pin decision (as in D-DS14). The check is never edited outside an approved pin.
5. MAPPING.md:31 and :58 propose `bg-(image:--accent-sheen)` and `shadow-1..3` TSX utilities. `rebuild-rules.mjs:22` bans the shadow classes; ADR-003 §3.7 keeps both in CSS.
6. The danger button goes gold (MAPPING.md:120) at LogoutButton.tsx:40, Header.tsx:152 and MessageCenter.tsx:103. This is visible in G19; any change to it needs a new owner decision.
7. Weight 700/800 requests on Be Vietnam Pro or Inter render as synthetic bold. They map to 600. Emerald keeps Montserrat 700/800 (with `preload: false`), but emerald h3-h6 move to the body face.
8. The contrast pairs live in session scratch, which is ephemeral. SC vendors them; if the scratch is gone, the designer re-derives the 55 pairs before SC returns.
9. S7 size: about 860 token touches across store, contribution, restricted, referral and messages (223 + 295 + 137 + 131 + 76, inventory:665-672; promo 0, inventory:700; scratch inventory, not retained). R4 allows the split.

## Rollback

- Base: the tag `ds-base` (precondition 1). Each shard lands as one `--no-ff` merge.
- Roll back a shard with `git revert -m 1 <merge>`, in reverse wave order (SG, S7 … S1, SP, S0), because later shards read the names S0 adds. A full rollback reverts every `ds-*` merge back to `ds-base`. The check pins travel with their shard: S0 restores F1.sh, built-css.sh, I1.sh and F5.sh; SP restores boxes.json; S1 restores U1.sh; S2 restores S3.sh; SG restores genplan.py.
- A partial revert after W6 of any pin-carrying shard (S0, SP, S1 or S2) also reverts SG, because SG mirrors that shard's pins. Then SG is re-run as a new shard that mirrors only the pins still merged. mirror.sh and G4b must pass again.
- Re-merging a reverted `ds-*` branch needs a revert of the revert; a plain re-merge of the same commits is a no-op.
- Any revert after G16 invalidates `baseline.sha256`, so G16-G19 run again.
- Restoring `data-theme="obsidian"` on `<html>` is diagnostic only. It breaks the re-pinned `I1.sh:10` and puts back the old win/loss pair, which fails rule 4.1 (48.4%). It never lands on `main`.
- The old reference shots stay unchanged at the guide path, so a full rollback can be proven against them with the rebuild GATES A5 command.

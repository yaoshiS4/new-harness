# Guide review: foundations-core

Reviewer: `sa` (read-only on the guide; this file is the only write). Date: 2026-11-05.
Binding inputs: `docs/rebuild/REVIEW-BRIEF.md`, `docs/rebuild/DECISIONS.md` (D1 exact rebuild, D2 Tailwind v4, D3 reproduce defects, D4 replace current code).
Scope: sections `00-01..00-05`, `01-01..01-07`, `01-09`, `01-10`, `01-11`, `05-01` under `docs/rebuild/sections/`.
Original source `Igaming-Agent-1/apps/web` was read (read-only) only to settle the gaps marked "verified in source".
Fresh probes against the installed compiler (`node_modules/tailwindcss` 4.3.4, `@tailwindcss/turbopack` 4.3.4) back every Tailwind claim marked "(probe)".

## 1. Coverage

| section file | h3 | read fully | components / routes / topics covered |
|---|---|---|---|
| 00-01-i-how-to-use.html | 1 | yes | precedence rule (code > tables > prose > shots), callout and copy conventions |
| 00-02-i-rebuild-order.html | 0 | yes | 8-step rebuild order |
| 00-03-i-runtime.html | 1 | yes | MockAuthProvider states, boot `tiered`, register/login transitions, DEV toggle, 6 package scripts |
| 00-04-i-routes.html | 0 | yes | 26 route rows: 22 pages + 4 server redirects |
| 00-05-i-discrepancies.html | 0 | yes | 16 collated discrepancies (cross-track) |
| 01-01-f-stack.html | 10 | yes | package.json, next.config.ts, tsconfig, eslint flat config, token-lint.mjs (verbatim), verify-app-ds.mjs (verbatim), root files, src layout, App Router conventions, RSC split |
| 01-02-f-tokens.html | 19 | yes | 163 custom properties in 18 groups + tokens.css verbatim (363 lines) |
| 01-03-f-themes.html | 3 | yes | themes.css, brands.css (yaobet, emerald), `/vip` palette hook |
| 01-04-f-typography.html | 5 | yes | next/font loaders, type scale, cascade, `.u-label`, `.money`/`[data-numeric]`, numeric rules, typography.css verbatim |
| 01-05-f-motion.html | 1 | yes | motion tokens, motion.css verbatim, 7 foundation keyframes, JS motion |
| 01-06-f-reset.html | 3 | yes | import order, reset.css + globals.css verbatim, stub.module.css, root loading.tsx |
| 01-07-f-root-layout.html | 4 | yes | metadata, viewport, `<html>`/`<body>`, provider tree, wrappers, layout.tsx + providers.tsx verbatim |
| 01-09-f-lib.html | 6 | yes (3,840 text lines in 20 slices) | format.ts, i18n.ts (398 leaves / 20 namespaces), rg.ts, types.ts, auth/* (5 files), mock/* (19 files) |
| 01-10-f-assets.html | 1 | yes | 36 public files, 5 empty folders, 9 SVGs verbatim, assets README verbatim |
| 01-11-f-unused.html | 1 | yes | 22 unused items, 18 literal-exception rows |
| 05-01-v-checklist.html | 6 | yes | 5 check groups + Playwright capture recipe (verbatim) |

Total: 16 files, 61 h3, 12 amber callout blocks (split into 24 defect items in section 4).

## 2. Inventory

### 2.1 Stack, config and gates

| name | original source path | guide anchor | depends on |
|---|---|---|---|
| package.json (name web, 6 scripts) | `apps/web/package.json` | `01-01-f-stack.html#f-stack-packages` | npm, playwright (dev) |
| next.config.ts (empty) | `apps/web/next.config.ts` | `01-01-f-stack.html#f-stack-next-config` | - |
| tsconfig.json (`@/*` -> `./src/*`) | `apps/web/tsconfig.json` | `01-01-f-stack.html#f-stack-tsconfig` | - |
| eslint.config.mjs (collection seam ban) | `apps/web/eslint.config.mjs` | `01-01-f-stack.html#f-stack-eslint` | eslint-config-next |
| scripts/token-lint.mjs (A1/A2/A3 + self-test) | `apps/web/scripts/token-lint.mjs` | `01-01-f-stack.html#f-stack-token-lint` | styles/tokens.css, themes.css, brands.css |
| verify-app-ds.mjs (7 visual invariants, 22 routes x 390/1440) | `apps/web/verify-app-ds.mjs` | `01-01-f-stack.html#f-stack-verify-ds` | playwright, dev server :3000 |
| _shots.mjs, README.md, .gitignore, next-env.d.ts | `apps/web/*` | `01-01-f-stack.html#f-stack-other-root` | not rebuilt (non-build) |
| favicon.ico | `apps/web/src/app/favicon.ico` | `01-01-f-stack.html#f-stack-other-root` | App Router file convention |
| Capture script (Playwright, :3107) | `.hc/.../shots` recipe | `05-01-v-checklist.html#v-capture` | DevAuthToggle classes `cycle`, `stateLabel` |

### 2.2 Styles and token groups

| name | original source path | guide anchor | depends on |
|---|---|---|---|
| reset.css | `src/styles/reset.css` | `01-06-f-reset.html#f-reset-order` | `--focus-ring` |
| tokens.css (one `:root`, 163 props) | `src/styles/tokens.css` | `01-02-f-tokens.html#f-tokens-verbatim` | next/font vars |
| Canvas and surfaces (9) | tokens.css | `01-02-f-tokens.html#f-tokens-surfaces` | - |
| Semantic (8, 4 PINNED) | tokens.css | `01-02-f-tokens.html#f-tokens-semantic` | - |
| Text ladder (4) | tokens.css | `01-02-f-tokens.html#f-tokens-text` | - |
| Border and tint (2) | tokens.css | `01-02-f-tokens.html#f-tokens-border` | - |
| Type scale, line-height, weight (15) | tokens.css | `01-02-f-tokens.html#f-tokens-type` | - |
| Spacing (10) | tokens.css | `01-02-f-tokens.html#f-tokens-space` | - |
| Radius (5) | tokens.css | `01-02-f-tokens.html#f-tokens-radius` | - |
| Elevation, all `none` (4) | tokens.css | `01-02-f-tokens.html#f-tokens-shadow` | - |
| Z ladder (5) | tokens.css | `01-02-f-tokens.html#f-tokens-z` | - |
| Chrome sizes (8) | tokens.css | `01-02-f-tokens.html#f-tokens-chrome` | - |
| Grid / tile / band (11) | tokens.css | `01-02-f-tokens.html#f-tokens-grid` | - |
| Motion (6) | tokens.css | `01-02-f-tokens.html#f-tokens-motion` | motion.css |
| Tap targets (2) | tokens.css | `01-02-f-tokens.html#f-tokens-tap` | - |
| Member-hub layer (18) | tokens.css | `01-02-f-tokens.html#f-tokens-member` | `--brand-accent`, `--canvas`, `--surface`, `--green` |
| Raw ramp (9) | tokens.css | `01-02-f-tokens.html#f-tokens-ramp` | - |
| Font stacks (3) | tokens.css | `01-02-f-tokens.html#f-tokens-fonts` | `--font-be-vietnam`, `--font-montserrat` |
| Brand indirection (12) | tokens.css, brands.css | `01-02-f-tokens.html#f-tokens-brand` | raw ramp |
| Luxury VIP layer (32) | tokens.css | `01-02-f-tokens.html#f-tokens-vip` | `.vipPalette` (track R) |
| themes.css `[data-theme="obsidian"]` (empty) | `src/styles/themes.css` | `01-03-f-themes.html#f-themes-theme` | `<html data-theme>` |
| brands.css `yaobet` + `emerald` (12 vars each) | `src/styles/brands.css` | `01-03-f-themes.html#f-themes-brand` | raw ramp, next/font vars |
| /vip palette hook | `components/vip/VipProgram.module.css` | `01-03-f-themes.html#f-themes-vip` | track R |
| typography.css | `src/styles/typography.css` | `01-04-f-typography.html#f-typography-numeric` | `--brand-font-*`, `--t-*` |
| next/font loaders (Be Vietnam Pro, Montserrat) | `src/app/layout.tsx` | `01-04-f-typography.html#f-typography-loaders` | next/font/google |
| `.u-label`, `[data-label="upper"]` (unused) | typography.css | `01-04-f-typography.html#f-typography-utilities` | - |
| `.money`, `[data-numeric]` (4 users of `[data-numeric]`) | typography.css | `01-04-f-typography.html#f-typography-utilities` | track M contribution/restricted |
| motion.css | `src/styles/motion.css` | `01-05-f-motion.html#f-motion` | `--dur-*` |
| 7 keyframes (spin, drop, pop, fade, slideUp, sweep, tileSweep) | `src/ui/*/*.module.css` | `01-05-f-motion.html#f-motion-keyframes` | src/ui primitives |
| globals.css (6 imports + 4 rules) | `src/app/globals.css` | `01-06-f-reset.html#f-reset-order` | all style files |
| stub.module.css (.page .heading .body) | `src/app/stub.module.css` | `01-06-f-reset.html#f-reset-stub` | 5 stub routes (track M) |

### 2.3 App shell files owned by foundations

| name | original source path | guide anchor | depends on |
|---|---|---|---|
| RootLayout, `metadata`, `viewport` | `src/app/layout.tsx` | `01-07-f-root-layout.html#f-root-layout-html` | globals.css, Providers, AppShell, Footer, QuickActionRail (track S) |
| Providers ("use client") | `src/app/providers.tsx` | `01-07-f-root-layout.html#f-root-layout-providers` | MockAuthProvider, AuthModalProvider |
| HomeLoading (root loading.tsx) | `src/app/loading.tsx` | `01-06-f-reset.html#f-reset-loading` | Skeleton (src/ui), Home.module.css classes (track S) |

Components referenced here but specified by other tracks: AppShell, ShellChrome, Header, CategorySheet, BottomTabBar, Footer, QuickActionRail (`02-01-s-shell-h.html#s-app-shell`, `#s-shell-chrome`, `#s-header`, `#s-category-sheet`, `#s-bottom-tab-bar`, `#s-footer`, `#s-quick-action-rail`), AuthModal (`02-02-s-auth-h.html#s-auth-modal`), DevAuthToggle (`02-03-s-home-h.html#s-dev-auth-toggle`), Skeleton (`01-08-f-ui.html#f-ui-skeleton`). All 8 root-layout anchors resolve (verified with `rg id=` on the sections).

### 2.4 Lib modules and hooks

| name | original source path | guide anchor | depends on |
|---|---|---|---|
| format.ts: formatVnd, formatSignedVnd, formatOdds, formatCount, formatPercent, LUCKY_DEPOSIT_PRESETS, formatPresetChip, hasDigitFour, isLuckySafe, isStale, relativeTime, money type re-exports | `src/lib/format.ts` | `01-09-f-lib.html#f-lib-format` | types.ts, i18n.ts (`vi.notifications`) |
| i18n.ts: `vi` (398 leaves, 20 namespaces), `Vi`, `t()` | `src/lib/i18n.ts` (691 lines, verified in source) | `01-09-f-lib.html#f-lib-i18n` | - |
| rg.ts: usePrefersReducedMotion (hook), outcomeColorVar (unused) | `src/lib/rg.ts` | `01-09-f-lib.html#f-lib-rg` | react |
| types.ts (money, envelopes, auth, 40+ domain types, `isLiveMoney`) | `src/lib/types.ts` (560 lines) | `01-09-f-lib.html#f-lib-types` | - |
| auth/session.tsx: MockAuthProvider, useAuth | `src/lib/auth/session.tsx` | `01-09-f-lib.html#f-lib-auth` | auth/fixtures.ts, types.ts |
| auth/modal.tsx: AuthModalProvider, useAuthModal, AuthModalMode | `src/lib/auth/modal.tsx` | `01-09-f-lib.html#f-lib-auth` | types.ts |
| auth/guard.ts: useRequireAuth, isGuest/isLevelZero/isTiered (unused) | `src/lib/auth/guard.ts` | `01-09-f-lib.html#f-lib-auth` | session, modal |
| auth/fixtures.ts: LEVEL_0_USER, TIERED_USER, SESSIONS | `src/lib/auth/fixtures.ts` | `01-09-f-lib.html#f-lib-auth` | types.ts |
| auth/index.ts barrel | `src/lib/auth/index.ts` | `01-09-f-lib.html#f-lib-auth` | the four above |

Hooks: `usePrefersReducedMotion` (rg.ts), `useAuth` (session), `useAuthModal` (modal), `useRequireAuth` (guard). Duplicate hook `components/layout/_internal/usePrefersReducedMotion.ts` belongs to track S.

Out of this track (guide says so, `01-09-f-lib.html#f-lib-mock` final amber callout): `src/lib/vip/*` (tiers, formulas, copy: the "VIP maths"), `src/lib/collection/*`, `src/lib/store/escalation.ts`. They are specified in `04-01-r-vip.html`, `04-31-r-collection-lib.html`, `04-18-r-store.html` (track R).

### 2.5 Mock datasets (`src/lib/mock/*`, 19 files incl. index; verified in source)

| module | exports | count / key values | guide anchor | depends on |
|---|---|---|---|---|
| helpers.ts | DEMO_EMPTY=false, simulateFetch, liveMoney, nowIso, isoIn, isoAgo | ms<=0 -> Promise.resolve | `01-09-f-lib.html#f-lib-mock` | types |
| index.ts | barrel (+ `export * from "./types"`) | - | `#f-lib-mock` | all below |
| types.ts | `export * from "../types"` | - | `#f-lib-mock` | lib/types |
| lobby.ts | getVerticals, getJackpot, getMemberDayCountdown, getLeaderboard, getSportsMatches, getLiveMatch | 9 verticals (`href: "/?v=<id>"`), pool 28.686.888.000, 7 leader rows (rank 4 absent), 4 sports matches, 1 live match | `#f-lib-mock` | helpers |
| games.ts | getGames, getProviders, FEATURE_GAME_ART (unused) | 16 tiles over 5 arts, 6 providers | `#f-lib-mock` | helpers |
| vip.ts | getVipTiers, getClubTiers (unused), getPerks, getVipProgress | 5 tiers (0.6..1.5), 4 perks, progress 18.600.000/30.000.000 | `#f-lib-mock` | helpers |
| wallet.ts | getWallet, getBalance | balance 6.886.000, 3 products | `#f-lib-mock` | helpers |
| promos.ts | getPromos | 8 promos pr1..pr8 (order pr1,pr2,pr3,pr7,pr8,pr4,pr5,pr6) | `#f-lib-mock` | helpers |
| store.ts | getProducts, getPointsBalance, DEMO_STATE, DEMO_ERROR, DEMO_PAUSED, DemoState | 11 products, 7 demo fixtures, points 3250 | `#f-lib-mock` | helpers |
| referral.ts | getReferral, getReferralKpi, getCommissions | code YB668812, KPI 2/1.250.000/6.800.000/42.000, 2 commissions | `#f-lib-mock` | helpers |
| cashback.ts | getCashback (unused) | 3 entries, accrued 406.000, claimable 366.000 | `#f-lib-mock` | helpers |
| records.ts | getRecords | 6 transactions | `#f-lib-mock` | helpers |
| messages.ts | getMessages | 3 messages (2 unread) | `#f-lib-mock` | helpers |
| notification-feed.ts (387 lines) | getNotificationBell | 34 rows, 6 unread, sorted by `at` desc (stable) | `#f-lib-mock` (row table only) | helpers, format, i18n |
| profile.ts | getSecurityIndex, getVerification, getAccountSummary, getBankCards, getCryptoAddresses | 5 factors (score 40), 5 verification rows, points 86.880, 2 cards, 2 addresses | `#f-lib-mock` | helpers |
| deposit.ts | getDepositOffer, getBankTransferMemo | 1 offer, memo YB668812 | `#f-lib-mock` | helpers |
| medals.ts | getMedals (unused) | 3 medals | `#f-lib-mock` | helpers |
| contribution.ts (548 lines) | getContributionRates, getContributionCatalogue, getRestrictedGames, deriveProviders, resolveTierRates, coalesceAdjacentEqual, rateBucket, CONTRIB_TIERS, BONUS_RESTRICTED_IDS + 8 types | 8 categories, 240 titles (21 curated + 219 generated), 19 providers, 30 restricted | `#f-lib-mock` | i18n, helpers |
| lottery.ts (443 lines) | LADDER, SCRATCH_ODDS, makeScratchCard, assertCard, selfTest | 11 rungs, mulberry32; seed 1 -> id `sc-v7zqd9py` | `#f-lib-mock` | format |

### 2.6 Routes (inventory from `00-04-i-routes.html#i-routes`; specs owned by other tracks)

| URL | kind | owner track (from section prefix; inference) |
|---|---|---|
| `/` (+loading) | home | S |
| `/[vertical]` (+loading, not-found) | 9 verticals | S |
| `/khuyen-mai`, `/khuyen-mai/[id]` (pr1..pr8) | promotions | S |
| `/tai-khoan`, `/vi-tien`, `/tin-nhan`, `/gioi-thieu` (+loading each), `/dai-ly` | `(member)` group | M |
| `/cuoc-hop-le` (+loading) | contribution + restricted tab | M |
| `/ho-tro`, `/tro-giup`, `/tai-app`, `/phong-cach`, `/cau-lac-bo` | stub / utility pages | M (`03-09-m-utility.html`) |
| `/bao-mat`, `/lich-su` -> `/tai-khoan`; `/hoan-tra` -> `/khuyen-mai`; `/game-han-che` -> `/cuoc-hop-le?tab=han-che` | 307 redirects | M |
| `/vip`, `/tier` | VIP | R |
| `/cua-hang`, `/ve-so`, `/bo-suu-tap`, `/bo-suu-tap/cua-toi`, `/dev/collection-ports` | rewards | R |

Foundations owns no route page. It owns the root layout, providers, root loading fallback styling contract and the stub-page styles the five stub routes import.

## 3. Tailwind translation notes

### 3.1 Decisions (tradeoffs and ADRs)

```yaml
tradeoffs:
  - option: A. Keep tokens.css/themes.css/brands.css verbatim as plain CSS; expose them to Tailwind with `@theme inline reference` keys named mechanically after the token
    yagni_rung: 4
    pros: [every guide var() name survives, brand re-pointing stays runtime CSS, A1/A3 run unchanged on the same files, zero new deps]
    cons: [utility names read oddly (border-border, p-space-5), 115 keys to keep in sync]
    blast_radius: src/styles/**, src/app/globals.css; every builder's className vocabulary
    risk: low (probe-verified on tailwindcss 4.3.4)
    cost: ~1 leaf
  - option: B. Same verbatim token files, no @theme keys; builders write var shorthand only (bg-(--surface), text-(length:--t-sm))
    yagni_rung: 4
    pros: [no mapping file, no name collisions at all]
    cons: [ambiguous type hints (text-(...) colour vs length, font-(...) family vs weight), no autocomplete, more builder error]
    risk: medium (silent wrong-property output)
  - option: C. Move token values into @theme literals and delete tokens.css
    yagni_rung: 4
    pros: [idiomatic Tailwind]
    cons: [breaks A1/A3 file contract, loses [data-brand] runtime re-pointing, renames every token, not exact]
    risk: high
adr:
  - id: ADR-003
    title: Foundation CSS architecture for the Tailwind v4 exact rebuild
    status: proposed
    date: 2026-11-05
    yagni_rung_selected: "4 (platform feature: Tailwind @theme/@layer/@custom-variant); rungs 1-3 cannot express utilities"
    context: "Guide styles are plain CSS on custom properties (01-02-f-tokens.html#f-tokens-verbatim). Tailwind preflight would change heading sizes the guide relies on (01-04-f-typography.html#f-typography-cascade: browser default heading sizes apply)."
    decision: "Option A. No preflight. Import tailwindcss/theme.css and utilities.css only. Import reset, tokens, themes, brands, typography, motion (in guide order) into @layer base. Map utilities with @theme inline reference and --*: initial. Override hover to plain :hover."
    consequences:
      - positive: "Cascade matches the original: utilities beat element/base rules like module classes did; motion.css !important in base is the strongest layered important."
      - negative: "Stock utilities (p-4, text-sm, shadow-md) emit nothing (probe), so a builder mistake is silent."
      - neutral: "Same-name keys (--radius-*, --ease-*) are not emitted to :root under `reference` (probe), so no self-reference."
    alternatives_considered: [B, C, "keep preflight and patch headings/img/borders"]
  - id: ADR-002
    title: Token-lint A1-A3 re-specified for Tailwind
    status: proposed
    date: 2026-11-05
    yagni_rung_selected: "5 (one zero-dependency Node script, extended); stylelint/eslint plugins would be rung 6"
    context: "Original A2 only scans *.module.css (01-01-f-stack.html#f-stack-token-lint). Under D2 component styling lives in className strings, style objects and @theme/@utility CSS, which the original never reads."
    decision: "Keep A1 and A3 byte-identical. Widen A2 to every non-definition .css plus every .ts/.tsx, and to Tailwind's var-shorthand forms. Self-test keeps the 3 original seeds and adds 5 Tailwind seeds (3 positive, 1 clean, 1 boundary)."
    consequences:
      - positive: "npm run lint:tokens and lint:tokens:self-test keep their names, messages and exit codes."
      - negative: "Dynamically built names (`var(--${x})`) are not detectable."
      - neutral: "A comment-only mention (lottery/_internal/coverArt.ts:14 in source) passes because TS comments are stripped."
    alternatives_considered: ["copy original byte-for-byte (blind to Tailwind)", "eslint custom rule (needs AST plugin)", "stylelint (new dependency)"]
```

### 3.2 globals.css layout (exact proposal)

```css
@layer theme, base, components, utilities;
@import "tailwindcss/theme.css" layer(theme);
@import "tailwindcss/utilities.css" layer(utilities) source(none);
@import "../styles/reset.css" layer(base);
@import "../styles/tokens.css" layer(base);
@import "../styles/themes.css" layer(base);
@import "../styles/brands.css" layer(base);
@import "../styles/typography.css" layer(base);
@import "../styles/motion.css" layer(base);
@import "../styles/keyframes.css";
@import "../styles/tw-theme.css";
@import "../styles/stub.css";
@source "../";
@custom-variant hover (&:hover);
@layer base {
  /* globals.css own rules, verbatim from 01-06-f-reset.html#f-reset-order */
  html { height: 100%; background: var(--shell); color-scheme: dark; overflow-x: hidden; }
  body { min-height: 100%; background: var(--canvas); color: var(--text-hi); font-family: var(--brand-font-body); font-size: var(--t-body); line-height: var(--lh-body); overflow-x: hidden; }
  h1, h2, h3, h4, h5, h6 { font-weight: var(--weight-bold); line-height: var(--lh-tight); }
  small { font-size: var(--t-sm); color: var(--text-mid); }
}
```

Why each line (exactness):
- No `@import "tailwindcss"`: that pulls preflight, which sets `h1..h6 { font-size: inherit }`, `img { height: auto }`, `* { border: 0 solid }`, `small { font-size: 80% }`. The guide relies on UA heading sizes (`01-04-f-typography.html#f-typography-cascade`) and has its own reset.
- All six guide sheets go in `@layer base`, in the guide order. Within one layer, source order is the original order, so `[data-brand]` still beats `:root` and motion.css's reduced-motion `:root` still overrides tokens.css. If tokens.css stayed unlayered while motion.css went to base, the `--dur-*: 0ms` override would lose (unlayered beats layered). Utilities beat base rules just as hashed module classes beat element rules in the original.
- `source(none)` + `@source "../"` scans `src/` only, so the guide HTML under `docs/` is never scanned (probe: `root:"none", sources:[{pattern:"../"}]`).
- `@custom-variant hover (&:hover)`: stock v4 `hover:` wraps in `@media (hover: hover)`. The probe shows the override emits plain `:hover`, which matches the original `.fab:hover`.
- The token lint scans `keyframes.css`, `tw-theme.css` and `stub.css` with A2. None of their names end in `tokens.css`, `themes.css` or `brands.css`, so A1/A3 scope is unchanged.

### 3.3 Mechanical translation rules (all tracks; foundations publishes them)

| # | guide CSS | Tailwind (exact) | evidence |
|---|---|---|---|
| R1 | `prop: var(--token)` where the token has a key (section 3.6) | utility from the map, e.g. `bg-surface`, `text-text-hi`, `border-border`, `p-space-5`, `gap-gap-sm`, `w-rail-w`, `rounded-card`, `text-t-sm`, `leading-lh-tight`, `font-weight-bold`, `font-brand-font-head`, `ease-standard` | probe: each emits `prop: var(--token)` |
| R2 | `z-index: var(--z-*)`, `transition-duration: var(--dur-*)` | `z-(--z-modal)`, `duration-(--dur-fast)` | probe |
| R3 | any `background:` shorthand (`var(--brand-cta-grad)`, `var(--page-bloom)`, `var(--header-card-grad)`, gradients) | `[background:var(--x)]`, never `bg-(--x)` | probe: `bg-(--surface)` emits `background-color`. A gradient there is invalid, so emerald's gradient defect FC-07 would vanish and `--page-bloom` (ends in a colour layer) would not paint |
| R4 | `background-image: var(--progress-fill-grad)` | `[background-image:var(--progress-fill-grad)]` | `01-02-f-tokens.html#f-tokens-verbatim` comment "The app's ONLY background-image call-site" |
| R5 | `transform: scale()/translate()/rotate()` | `[transform:scale(1.02)]` | probe: `scale-105` emits the separate `scale:` property, which composes differently with keyframed `transform` |
| R6 | colour with alpha / `color-mix(in srgb, …)` | literal arbitrary value, e.g. `[background:color-mix(in_srgb,var(--brand-accent)_12%,transparent)]`; never `/NN` modifiers | probe: `bg-canvas/50` emits `color-mix(in oklab, …)` |
| R7 | `linear-/radial-gradient(...)` | arbitrary `[background:...]`; never `bg-linear-*` / `bg-radial-*` | (inference) v4 gradient utilities interpolate in oklab by default |
| R8 | `@media (max-width: 639px)` | `[@media(max-width:639px)]:` | probe: `max-[639px]:` emits `(width < 639px)`, which is off by one at 639px |
| R9 | `@media (min-width: Npx)` | `min-[Npx]:` | probe: `(width >= Npx)`, same set |
| R10 | `:hover` / `@media (hover:hover){:hover}` | `hover:` (overridden) / `[@media(hover:hover)]:hover:` | probe |
| R11 | `transition: border-color 200ms …` | `[transition:border-color_var(--dur-fast)_var(--ease-standard)]` | probe: `transition-colors` sets a 10-property list and `var(--tw-duration,0s)` |
| R12 | module `@keyframes` | global `ui-*` keyframes in `src/styles/keyframes.css` + `animate-[ui-pop_var(--dur-base)_var(--ease-entrance)]` or `[animation:…]` | `01-05-f-motion.html#f-motion-keyframes` note: names must be renamed when global |
| R13 | literals (2px, 0.06em, 60ch, 1.6, 160px, 1.25em) | arbitrary values `gap-[2px]`, `tracking-[0.06em]`, `max-w-[60ch]`, `leading-[1.6]`, `w-[160px]` | probe: stock `p-4`/`text-sm` emit nothing after `--*: initial` |
| R14 | `border-radius: var(--radius-pill)` | `rounded-pill` (never `rounded-full`) | probe: `rounded-full` = `calc(infinity * 1px)` |
| R15 | pseudo-elements, masks, clip-path, `:has`, container queries, descendant selectors, canvas art | `@layer components { .x::before {…} }` in the owning leaf's CSS when there are more than 3 declarations or a compound selector; else arbitrary variants (`before:content-['']`, `[&_.b]:`, `has-[…]:`) | precedence rule `00-01-i-how-to-use.html#i-how-to-use` (verbatim CSS wins) |
| R16 | zero depth (`verify-app-ds.mjs`) | never `shadow-*`, `ring-*`, `drop-shadow-*`, `backdrop-blur-*`; `box-shadow: var(--lift)` -> `[box-shadow:var(--lift)]` | `01-01-f-stack.html#f-stack-verify-ds`; `ring` is not theme-driven, so `--*: initial` does not disable it |
| R17 | `!important` | never on animation/transition utilities (a layered `!` beats motion.css's reduced-motion rule) | `01-05-f-motion.html#f-motion` |
| R18 | hashed module class names used as hooks | literal marker classes, unstyled: `cycle`, `stateLabel` (DevAuthToggle) | `05-01-v-checklist.html#v-capture` note |

### 3.4 Per-item translation

| item | translation | exactness notes |
|---|---|---|
| reset.css | verbatim file, `@import … layer(base)` | the `svg { display:block }` rule stays, so the Icon primitive must keep `inline-block` (`01-06-f-reset.html#f-reset-order` note) |
| tokens.css | verbatim file (163 props, comments may drop plan tags, see G19), `layer(base)` | A1/A3 parse it unchanged |
| themes.css | verbatim (empty `[data-theme="obsidian"]` rule) | no-op by design |
| brands.css | verbatim (2 blocks x 12 `--brand-*`) | emerald never activated; keep |
| typography.css | verbatim, `layer(base)` | class utilities (`font-brand-font-display`) still beat the `h1..h6` element rule, like `.vipSectionHeading` did |
| motion.css | verbatim, `layer(base)` | the `*` `!important` rule is the strongest layered important; the `:root` zeroing wins over tokens.css by order |
| keyframes.css (new) | `@keyframes ui-spin`, `ui-drop`, `ui-pop`, `ui-fade`, `ui-slide-up`, `ui-sweep`, `ui-tile-sweep`, with frames verbatim from `01-05-f-motion.html#f-motion-keyframes` | Sheet's `fade` is not rebuilt (Sheet unused, `01-11-f-unused.html#f-unused`) |
| tw-theme.css (new) | the `@theme inline reference` block in 3.6 | 115 keys; RAW ramp and never-read tokens get no key |
| stub.css (new) | `@utility stub-page { display:flex; flex-direction:column; gap:var(--space-4); min-width:0 }`, `@utility stub-heading { font-size:var(--t-h1); color:var(--text-hi); font-weight:var(--weight-bold) }`, `@utility stub-body { font-size:var(--t-body); color:var(--text-mid); max-width:60ch; line-height:1.6 }` | replaces `app/stub.module.css`; the five stub routes use `stub-page/stub-heading/stub-body` |
| globals.css | section 3.2 | - |
| layout.tsx | verbatim TSX (`01-07-f-root-layout.html#f-root-layout-html`), `import "./globals.css"` | see 3.7 |
| providers.tsx | verbatim TSX | see 3.8 |
| loading.tsx | verbatim structure and copy; the four Home classes come from track S (G9) | no CSS of its own |
| lib/** | pure TS, verbatim; no styling | `outcomeColorVar` returns `"var(--win)"`/`"var(--loss)"`, not raw ramp, so A2 is clean |
| public/** | binary copy from the original `public/` | section 6 |

### 3.5 Keyframes (foundation set, renamed for global scope)

| original | file | global name | frames (verbatim) | used as |
|---|---|---|---|---|
| spin | Button.module.css | ui-spin | `to { transform: rotate(360deg) }` | `animate-[ui-spin_700ms_linear_infinite]` |
| drop | Dropdown.module.css | ui-drop | `from { opacity:0; transform: translateY(-4px) } to { opacity:1; transform: translateY(0) }` | `[animation:ui-drop_var(--dur-fast)_var(--ease-entrance)]` |
| pop | Modal.module.css | ui-pop | `from { opacity:0; transform: translateY(8px) scale(0.98) } to { opacity:1; transform: translateY(0) scale(1) }` | `[animation:ui-pop_var(--dur-base)_var(--ease-entrance)]` |
| fade | Modal.module.css | ui-fade | `from { opacity:0 } to { opacity:1 }` | `[animation:ui-fade_var(--dur-base)_var(--ease-standard)]` |
| slideUp | Modal.module.css (inside max-width:639px) | ui-slide-up | `from { transform: translateY(100%) } to { transform: translateY(0) }` | `[@media(max-width:639px)]:[animation:ui-slide-up_var(--dur-slow)_var(--ease-entrance)]` |
| sweep | Skeleton.module.css | ui-sweep | `from { background-position: 200% 0 } to { background-position: -200% 0 }` | `[animation:ui-sweep_var(--dur-slow)_linear_infinite] [animation-duration:1400ms]` |
| tileSweep | TileSkeleton.module.css | ui-tile-sweep | same as sweep | `[animation:ui-tile-sweep_1400ms_linear_infinite]` |

### 3.6 Token map: every custom property, value per brand/theme, proposed Tailwind v4 key

`[data-theme="obsidian"]` overrides nothing, so the obsidian value of every row equals `:root`. `[data-brand="yaobet"]` re-declares the 12 `--brand-*` with the same aliases. Rows marked "follows emerald `--brand-accent`" resolve through `color-mix`/`var(--brand-accent)` declared on `:root`. They follow emerald only because `data-brand` sits on `<html>`, which is the `:root` element (FC-10). "same name (benign)" means the Tailwind key equals the guide token; under `@theme … reference` it is never emitted, so no cycle exists (probe).

| # | token | :root and [data-brand="yaobet"] | [data-brand="emerald"] | `@theme inline` key / utility |
|---|---|---|---|---|
| 1 | `--canvas` | `#0a0a0a` | = :root | `--color-canvas` / `bg-canvas`, `text-canvas`, `border-canvas` |
| 2 | `--shell` | `#050505` | = :root | `--color-shell` / `bg-shell`, `text-shell`, `border-shell` |
| 3 | `--surface` | `#141414` | = :root | `--color-surface` / `bg-surface`, `text-surface`, `border-surface` |
| 4 | `--surface-2` | `#1a1a1a` | = :root | `--color-surface-2` / `bg-surface-2`, `text-surface-2`, `border-surface-2` |
| 5 | `--surface-3` | `#212121` | = :root | `--color-surface-3` / `bg-surface-3`, `text-surface-3`, `border-surface-3` |
| 6 | `--tile` | `#171717` | = :root | `--color-tile` / `bg-tile`, `text-tile`, `border-tile` |
| 7 | `--surface-hover` | `#262626` | = :root | `--color-surface-hover` / `bg-surface-hover`, `text-surface-hover`, `border-surface-hover` |
| 8 | `--surface-disabled` | `#303030` | = :root | `--color-surface-disabled` / `bg-surface-disabled`, `text-surface-disabled`, `border-surface-disabled` |
| 9 | `--scrim` | `rgba(0, 0, 0, 0.7)` | = :root | `--color-scrim` / `bg-scrim`, `text-scrim`, `border-scrim` |
| 10 | `--win` | `#45c9a5` | = :root | `--color-win` / `bg-win`, `text-win`, `border-win` |
| 11 | `--loss` | `#f53f55` | = :root | `--color-loss` / `bg-loss`, `text-loss`, `border-loss` |
| 12 | `--error` | `#e42946` | = :root | `--color-error` / `bg-error`, `text-error`, `border-error` |
| 13 | `--green` | `#31bc69` | = :root | `--color-green` / `bg-green`, `text-green`, `border-green` |
| 14 | `--info` | `#018fff` | = :root | `--color-info` / `bg-info`, `text-info`, `border-info` |
| 15 | `--caution` | `#f5a623` | = :root | `--color-caution` / `bg-caution`, `text-caution`, `border-caution` |
| 16 | `--on-caution` | `#2a1a00` | = :root | `--color-on-caution` / `bg-on-caution`, `text-on-caution`, `border-on-caution` |
| 17 | `--focus-ring` | `#6ea8ff` | = :root | `--color-focus-ring` / `bg-focus-ring`, `text-focus-ring`, `border-focus-ring` |
| 18 | `--text-hi` | `#f2f0e4` | = :root | `--color-text-hi` / `bg-text-hi`, `text-text-hi`, `border-text-hi` |
| 19 | `--text` | `#d6d3c7` | = :root | `--color-text` / `bg-text`, `text-text`, `border-text` |
| 20 | `--text-mid` | `#888888` | = :root | `--color-text-mid` / `bg-text-mid`, `text-text-mid`, `border-text-mid` |
| 21 | `--text-dim` | `#6f6f6f` | = :root | `--color-text-dim` / `bg-text-dim`, `text-text-dim`, `border-text-dim` |
| 22 | `--border` | `rgba(212, 175, 55, 0.55)` | = :root | `--color-border` / `bg-border`, `text-border`, `border-border` |
| 23 | `--tint` | `rgba(242, 240, 228, 0.05)` | = :root | `--color-tint` / `bg-tint`, `text-tint`, `border-tint` |
| 24 | `--t-micro` | `12px` | = :root | `--text-t-micro` / `text-t-micro` |
| 25 | `--t-sm` | `14px` | = :root | `--text-t-sm` / `text-t-sm` |
| 26 | `--t-body` | `16px` | = :root | `--text-t-body` / `text-t-body` |
| 27 | `--t-h3` | `18px` | = :root | `--text-t-h3` / `text-t-h3` |
| 28 | `--t-h2` | `20px` | = :root | `--text-t-h2` / `text-t-h2` |
| 29 | `--t-h1` | `24px` | = :root | `--text-t-h1` / `text-t-h1` |
| 30 | `--t-display` | `32px` | = :root | `--text-t-display` / `text-t-display` |
| 31 | `--t-hero` | `40px` | = :root | `--text-t-hero` / `text-t-hero` |
| 32 | `--t-num` | `16px` | = :root | `--text-t-num` / `text-t-num` |
| 33 | `--t-num-lg` | `32px` | = :root | `--text-t-num-lg` / `text-t-num-lg` |
| 34 | `--lh-body` | `1.5` | = :root | `--leading-lh-body` / `leading-lh-body` |
| 35 | `--lh-tight` | `1.3` | = :root | `--leading-lh-tight` / `leading-lh-tight` |
| 36 | `--weight-reg` | `400` | = :root | `--font-weight-weight-reg` / `font-weight-reg` |
| 37 | `--weight-semi` | `600` | = :root | `--font-weight-weight-semi` / `font-weight-semi` |
| 38 | `--weight-bold` | `700` | = :root | `--font-weight-weight-bold` / `font-weight-bold` |
| 39 | `--space-1` | `4px` | = :root | `--spacing-space-1` / `p-space-1`, `m-space-1`, `gap-space-1`, `w-space-1`, `h-space-1` |
| 40 | `--space-2` | `8px` | = :root | `--spacing-space-2` / `p-space-2`, `m-space-2`, `gap-space-2`, `w-space-2`, `h-space-2` |
| 41 | `--space-3` | `12px` | = :root | `--spacing-space-3` / `p-space-3`, `m-space-3`, `gap-space-3`, `w-space-3`, `h-space-3` |
| 42 | `--space-4` | `16px` | = :root | `--spacing-space-4` / `p-space-4`, `m-space-4`, `gap-space-4`, `w-space-4`, `h-space-4` |
| 43 | `--space-5` | `24px` | = :root | `--spacing-space-5` / `p-space-5`, `m-space-5`, `gap-space-5`, `w-space-5`, `h-space-5` |
| 44 | `--space-6` | `32px` | = :root | `--spacing-space-6` / `p-space-6`, `m-space-6`, `gap-space-6`, `w-space-6`, `h-space-6` |
| 45 | `--space-7` | `40px` | = :root | `--spacing-space-7` / `p-space-7`, `m-space-7`, `gap-space-7`, `w-space-7`, `h-space-7` |
| 46 | `--space-8` | `48px` | = :root | `--spacing-space-8` / `p-space-8`, `m-space-8`, `gap-space-8`, `w-space-8`, `h-space-8` |
| 47 | `--gutter` | `16px` | = :root | `--spacing-gutter` / `p-gutter`, `m-gutter`, `gap-gutter`, `w-gutter`, `h-gutter` |
| 48 | `--field-rhythm` (never read) | `24px` | = :root | no key (never read; kept verbatim in tokens.css) |
| 49 | `--radius-sm` | `4px` | = :root | same name (benign) / `rounded-sm` |
| 50 | `--radius-md` | `8px` | = :root | same name (benign) / `rounded-md` |
| 51 | `--radius-lg` | `12px` | = :root | same name (benign) / `rounded-lg` |
| 52 | `--radius-card` | `16px` | = :root | same name (benign) / `rounded-card` |
| 53 | `--radius-pill` | `9999px` | = :root | same name (benign) / `rounded-pill` |
| 54 | `--glow-gold` (never read) | `none` | = :root | no key (never read; kept verbatim in tokens.css) |
| 55 | `--halo` (never read) | `none` | = :root | no key (never read; kept verbatim in tokens.css) |
| 56 | `--lift` (never read) | `none` | = :root | no key (never read; kept verbatim in tokens.css) |
| 57 | `--shadow-2` (never read) | `none` | = :root | no key (never read; kept verbatim in tokens.css) |
| 58 | `--z-content` | `1` | = :root | `z-(--z-content)` |
| 59 | `--z-sticky` | `100` | = :root | `z-(--z-sticky)` |
| 60 | `--z-dropdown` | `1000` | = :root | `z-(--z-dropdown)` |
| 61 | `--z-modal` | `2000` | = :root | `z-(--z-modal)` |
| 62 | `--z-toast` | `3000` | = :root | `z-(--z-toast)` |
| 63 | `--header-h` | `72px` | = :root | `--spacing-header-h` / `p-header-h`, `m-header-h`, `gap-header-h`, `w-header-h`, `h-header-h` |
| 64 | `--nav-h` | `48px` | = :root | `--spacing-nav-h` / `p-nav-h`, `m-nav-h`, `gap-nav-h`, `w-nav-h`, `h-nav-h` |
| 65 | `--logo-h` | `44px` | = :root | `--spacing-logo-h` / `p-logo-h`, `m-logo-h`, `gap-logo-h`, `w-logo-h`, `h-logo-h` |
| 66 | `--header-bg` | `#0a0a0a` | = :root | `--color-header-bg` / `bg-header-bg`, `text-header-bg`, `border-header-bg` |
| 67 | `--rail-w` | `304px` | = :root | `--spacing-rail-w` / `p-rail-w`, `m-rail-w`, `gap-rail-w`, `w-rail-w`, `h-rail-w` |
| 68 | `--frame-w` | `1424px` | = :root | `--spacing-frame-w` / `p-frame-w`, `m-frame-w`, `gap-frame-w`, `w-frame-w`, `h-frame-w` |
| 69 | `--frame-min` (never read) | `1150px` | = :root | no key (never read; kept verbatim in tokens.css) |
| 70 | `--bottombar-h` | `56px` | = :root | `--spacing-bottombar-h` / `p-bottombar-h`, `m-bottombar-h`, `gap-bottombar-h`, `w-bottombar-h`, `h-bottombar-h` |
| 71 | `--band-gap` | `16px` | = :root | `--spacing-band-gap` / `p-band-gap`, `m-band-gap`, `gap-band-gap`, `w-band-gap`, `h-band-gap` |
| 72 | `--gap` | `16px` | = :root | `--spacing-gap` / `p-gap`, `m-gap`, `gap-gap`, `w-gap`, `h-gap` |
| 73 | `--gap-sm` | `8px` | = :root | `--spacing-gap-sm` / `p-gap-sm`, `m-gap-sm`, `gap-gap-sm`, `w-gap-sm`, `h-gap-sm` |
| 74 | `--gap-xs` | `4px` | = :root | `--spacing-gap-xs` / `p-gap-xs`, `m-gap-xs`, `gap-gap-xs`, `w-gap-xs`, `h-gap-xs` |
| 75 | `--feature-w` | `418px` | = :root | `--spacing-feature-w` / `p-feature-w`, `m-feature-w`, `gap-feature-w`, `w-feature-w`, `h-feature-w` |
| 76 | `--tile-h` | `205px` | = :root | `--spacing-tile-h` / `p-tile-h`, `m-tile-h`, `gap-tile-h`, `w-tile-h`, `h-tile-h` |
| 77 | `--provider-w` | `128px` | = :root | `--spacing-provider-w` / `p-provider-w`, `m-provider-w`, `gap-provider-w`, `w-provider-w`, `h-provider-w` |
| 78 | `--provider-h` | `48px` | = :root | `--spacing-provider-h` / `p-provider-h`, `m-provider-h`, `gap-provider-h`, `w-provider-h`, `h-provider-h` |
| 79 | `--card-pad` | `24px` | = :root | `--spacing-card-pad` / `p-card-pad`, `m-card-pad`, `gap-card-pad`, `w-card-pad`, `h-card-pad` |
| 80 | `--card-pad-sm` | `16px` | = :root | `--spacing-card-pad-sm` / `p-card-pad-sm`, `m-card-pad-sm`, `gap-card-pad-sm`, `w-card-pad-sm`, `h-card-pad-sm` |
| 81 | `--banner-mb` (never read) | `22px` | = :root | no key (never read; kept verbatim in tokens.css) |
| 82 | `--dur-fast` | `200ms` | = :root | `duration-(--dur-fast)` |
| 83 | `--dur-base` | `200ms` | = :root | `duration-(--dur-base)` |
| 84 | `--dur-slow` | `300ms` | = :root | `duration-(--dur-slow)` |
| 85 | `--dur-header` (never read) | `300ms` | = :root | no key (never read; kept verbatim in tokens.css) |
| 86 | `--ease-standard` | `cubic-bezier(0.645, 0.045, 0.355, 1)` | = :root | same name (benign) / `ease-standard` |
| 87 | `--ease-entrance` | `cubic-bezier(0.23, 1, 0.32, 1)` | = :root | same name (benign) / `ease-entrance` |
| 88 | `--tap-min` | `44px` | = :root | `--spacing-tap-min` / `p-tap-min`, `m-tap-min`, `gap-tap-min`, `w-tap-min`, `h-tap-min` |
| 89 | `--tap-bar` | `48px` | = :root | `--spacing-tap-bar` / `p-tap-bar`, `m-tap-bar`, `gap-tap-bar`, `w-tap-bar`, `h-tap-bar` |
| 90 | `--page-bloom` | `radial-gradient(120% 80% at 50% -10%, color-mix(in srgb, var(--brand-accent) 6%, transparent) 0%, rgba(10, 10, 10, 0) 46%), radial-gradient(140% 120% at 50% 120%, rgba(30, 61, 89, 0.25) 0%, rgba(10, 10, 10, 0) 55%), var(--canvas)` | follows emerald `--brand-accent` | `[background:var(--page-bloom)]` |
| 91 | `--member-canvas` | `var(--canvas)` | = :root | `--color-member-canvas` / `bg-member-canvas`, `text-member-canvas`, `border-member-canvas` |
| 92 | `--header-card-grad` | `radial-gradient(120% 140% at 14% 30%, color-mix(in srgb, var(--brand-accent) 14%, transparent) 0%, rgba(20, 20, 20, 0) 52%), var(--surface)` | follows emerald `--brand-accent` | `[background:var(--header-card-grad)]` |
| 93 | `--wallet-sheen-grad` | `linear-gradient(118deg, rgba(242, 240, 228, 0.05) -10%, rgba(242, 240, 228, 0.012) 60%, transparent 100%)` | = :root | `[background:var(--wallet-sheen-grad)]` |
| 94 | `--card-sheen-grad` | `radial-gradient(circle at 78% 26%, rgba(242, 240, 228, 0.04) 0%, rgba(242, 240, 228, 0.01) 57%, transparent 72%)` | = :root | `[background:var(--card-sheen-grad)]` |
| 95 | `--qr-surface` | `#ffffff` | = :root | `--color-qr-surface` / `bg-qr-surface`, `text-qr-surface`, `border-qr-surface` |
| 96 | `--balance-text` | `var(--text-hi)` | = :root | `--color-balance-text` / `bg-balance-text`, `text-balance-text`, `border-balance-text` |
| 97 | `--t-balance` | `28px` | = :root | `--text-t-balance` / `text-t-balance` |
| 98 | `--progress-track` | `hsla(0, 0%, 100%, 0.12)` | = :root | `--color-progress-track` / `bg-progress-track`, `text-progress-track`, `border-progress-track` |
| 99 | `--progress-fill` | `var(--brand-accent)` | follows emerald `--brand-accent` | `--color-progress-fill` / `bg-progress-fill`, `text-progress-fill`, `border-progress-fill` |
| 100 | `--progress-fill-grad` | `linear-gradient(90deg, var(--brand-accent), var(--brand-accent))` | follows emerald `--brand-accent` | `[background:var(--progress-fill-grad)]` |
| 101 | `--progress-dot` | `#ffffff` | = :root | `--color-progress-dot` / `bg-progress-dot`, `text-progress-dot`, `border-progress-dot` |
| 102 | `--progress-dot-glow` (never read) | `none` | = :root | no key (never read; kept verbatim in tokens.css) |
| 103 | `--progress-tag-bg` (never read) | `var(--surface-3)` | = :root | no key (never read; kept verbatim in tokens.css) |
| 104 | `--progress-tag-text` | `var(--brand-accent)` | follows emerald `--brand-accent` | `--color-progress-tag-text` / `bg-progress-tag-text`, `text-progress-tag-text`, `border-progress-tag-text` |
| 105 | `--progress-tag-border` (never read) | `color-mix(in srgb, var(--brand-accent) 32%, transparent)` | follows emerald `--brand-accent` | no key (never read; kept verbatim in tokens.css) |
| 106 | `--status-locked-bg` (never read) | `color-mix(in srgb, var(--green) 12%, transparent)` | = :root | no key (never read; kept verbatim in tokens.css) |
| 107 | `--status-locked-text` (never read) | `var(--green)` | = :root | no key (never read; kept verbatim in tokens.css) |
| 108 | `--gold-500` | `#d4af37` | = :root | not exposed (RAW RAMP, A2) |
| 109 | `--gold-600` | `#b4952f` | = :root | not exposed (RAW RAMP, A2) |
| 110 | `--gold-grad` | `#d4af37` | = :root | not exposed (RAW RAMP, A2) |
| 111 | `--gold-hairline` | `rgba(212, 175, 55, 0.55)` | = :root | not exposed (RAW RAMP, A2) |
| 112 | `--text-on-gold` | `#0a0a0a` | = :root | not exposed (RAW RAMP, A2) |
| 113 | `--cta` | `#5e97c9` | = :root | not exposed (RAW RAMP, A2) |
| 114 | `--cta-grad` | `#1e3d59` | = :root | not exposed (RAW RAMP, A2) |
| 115 | `--cta-accent` | `#f53f55` | = :root | not exposed (RAW RAMP, A2) |
| 116 | `--blue-soft` (never read) | `#8fb4d6` | = :root | no key (never read; kept verbatim in tokens.css) |
| 117 | `--font-body` | `var(--font-be-vietnam), system-ui, "Segoe UI", Roboto, Arial, sans-serif` | = :root | not exposed (RAW RAMP, A2) |
| 118 | `--font-num` | `var(--font-be-vietnam), ui-monospace, "DIN Alternate", "Segoe UI", sans-serif` | = :root | not exposed (RAW RAMP, A2) |
| 119 | `--font-head` | `var(--font-montserrat), system-ui, "Segoe UI", Roboto, Arial, sans-serif` | = :root | not exposed (read --brand-font-head) |
| 120 | `--brand-accent` | `var(--gold-500)` | `#1fbf73` | `--color-brand-accent` / `bg-brand-accent`, `text-brand-accent`, `border-brand-accent` |
| 121 | `--brand-accent-2` | `var(--gold-600)` | `#169a5b` | `--color-brand-accent-2` / `bg-brand-accent-2`, `text-brand-accent-2`, `border-brand-accent-2` |
| 122 | `--brand-accent-grad` | `var(--gold-grad)` | `linear-gradient(90deg, #1fbf73, #7ff0bf)` | `[background:var(--brand-accent-grad)]` |
| 123 | `--brand-accent-hairline` | `var(--gold-hairline)` | `rgba(31, 191, 115, 0.32)` | `--color-brand-accent-hairline` / `bg-brand-accent-hairline`, `text-brand-accent-hairline`, `border-brand-accent-hairline` |
| 124 | `--brand-on-accent` | `var(--text-on-gold)` | `#04140c` | `--color-brand-on-accent` / `bg-brand-on-accent`, `text-brand-on-accent`, `border-brand-on-accent` |
| 125 | `--brand-cta` | `var(--cta)` | `#2f6bff` | `--color-brand-cta` / `bg-brand-cta`, `text-brand-cta`, `border-brand-cta` |
| 126 | `--brand-cta-grad` | `var(--cta-grad)` | `linear-gradient(90deg, #3b7bff, #2f6bff)` | `[background:var(--brand-cta-grad)]` |
| 127 | `--brand-cta-accent` | `var(--cta-accent)` | `#ff3d57` | `--color-brand-cta-accent` / `bg-brand-cta-accent`, `text-brand-cta-accent`, `border-brand-cta-accent` |
| 128 | `--brand-font-body` | `var(--font-body)` | `var(--font-be-vietnam), system-ui, "Segoe UI", Roboto, Arial, sans-serif` | `--font-brand-font-body` / `font-brand-font-body` |
| 129 | `--brand-font-num` | `var(--font-num)` | `var(--font-be-vietnam), ui-monospace, "DIN Alternate", sans-serif` | `--font-brand-font-num` / `font-brand-font-num` |
| 130 | `--brand-font-head` | `var(--font-head)` | `var(--font-montserrat), system-ui, "Segoe UI", Roboto, Arial, sans-serif` | `--font-brand-font-head` / `font-brand-font-head` |
| 131 | `--brand-logo` (never read) | `url("/assets/brand/logo.svg")` | `url("/assets/brand/emerald-logo.svg")` | no key (never read; kept verbatim in tokens.css) |
| 132 | `--vip-page-bg` | `#0b0a07` | = :root | `--color-vip-page-bg` / `bg-vip-page-bg`, `text-vip-page-bg`, `border-vip-page-bg` |
| 133 | `--vip-panel-bg` | `#17140d` | = :root | `--color-vip-panel-bg` / `bg-vip-panel-bg`, `text-vip-panel-bg`, `border-vip-panel-bg` |
| 134 | `--vip-panel-alt` | `#141019` | = :root | `--color-vip-panel-alt` / `bg-vip-panel-alt`, `text-vip-panel-alt`, `border-vip-panel-alt` |
| 135 | `--vip-inner-bg` | `#0f0c07` | = :root | `--color-vip-inner-bg` / `bg-vip-inner-bg`, `text-vip-inner-bg`, `border-vip-inner-bg` |
| 136 | `--vip-text-primary` | `#e6ebf5` | = :root | `--color-vip-text-primary` / `bg-vip-text-primary`, `text-vip-text-primary`, `border-vip-text-primary` |
| 137 | `--vip-text-secondary` | `#c9c3b4` | = :root | `--color-vip-text-secondary` / `bg-vip-text-secondary`, `text-vip-text-secondary`, `border-vip-text-secondary` |
| 138 | `--vip-text-muted` | `#8b96ad` | = :root | `--color-vip-text-muted` / `bg-vip-text-muted`, `text-vip-text-muted`, `border-vip-text-muted` |
| 139 | `--vip-text-faint` | `#6b7690` | = :root | `--color-vip-text-faint` / `bg-vip-text-faint`, `text-vip-text-faint`, `border-vip-text-faint` |
| 140 | `--vip-text-disabled` | `#565f70` | = :root | `--color-vip-text-disabled` / `bg-vip-text-disabled`, `text-vip-text-disabled`, `border-vip-text-disabled` |
| 141 | `--vip-gold-start` | `#9a7b1e` | = :root | `--color-vip-gold-start` / `bg-vip-gold-start`, `text-vip-gold-start`, `border-vip-gold-start` |
| 142 | `--vip-gold-mid` | `#e3c15a` | = :root | `--color-vip-gold-mid` / `bg-vip-gold-mid`, `text-vip-gold-mid`, `border-vip-gold-mid` |
| 143 | `--vip-gold-end` | `#f6e39a` | = :root | `--color-vip-gold-end` / `bg-vip-gold-end`, `text-vip-gold-end`, `border-vip-gold-end` |
| 144 | `--vip-gold-ink` | `#2e2404` | = :root | `--color-vip-gold-ink` / `bg-vip-gold-ink`, `text-vip-gold-ink`, `border-vip-gold-ink` |
| 145 | `--vip-gold-grad` (never read) | `linear-gradient(135deg, #9a7b1e, #e3c15a, #f6e39a)` | = :root | no key (never read; kept verbatim in tokens.css) |
| 146 | `--vip-gold-tint` | `rgba(227, 193, 90, 0.08)` | = :root | `--color-vip-gold-tint` / `bg-vip-gold-tint`, `text-vip-gold-tint`, `border-vip-gold-tint` |
| 147 | `--vip-positive` | `#34d399` | = :root | `--color-vip-positive` / `bg-vip-positive`, `text-vip-positive`, `border-vip-positive` |
| 148 | `--vip-negative` (never read) | `#fb7185` | = :root | no key (never read; kept verbatim in tokens.css) |
| 149 | `--vip-hairline` | `rgba(255, 255, 255, 0.07)` | = :root | `--color-vip-hairline` / `bg-vip-hairline`, `text-vip-hairline`, `border-vip-hairline` |
| 150 | `--vip-tier-bronze-grad` | `linear-gradient(135deg, #8c5a2b, #c88f5a, #e0a56b)` | = :root | `[background:var(--vip-tier-bronze-grad)]` |
| 151 | `--vip-tier-bronze-acc` | `#e0a56b` | = :root | `--color-vip-tier-bronze-acc` / `bg-vip-tier-bronze-acc`, `text-vip-tier-bronze-acc`, `border-vip-tier-bronze-acc` |
| 152 | `--vip-tier-silver-grad` | `linear-gradient(135deg, #8a94a6, #cbd3df, #eef2f7)` | = :root | `[background:var(--vip-tier-silver-grad)]` |
| 153 | `--vip-tier-silver-acc` | `#cbd3df` | = :root | `--color-vip-tier-silver-acc` / `bg-vip-tier-silver-acc`, `text-vip-tier-silver-acc`, `border-vip-tier-silver-acc` |
| 154 | `--vip-tier-gold-grad` | `linear-gradient(135deg, #9a7b1e, #e3c15a, #f6e39a)` | = :root | `[background:var(--vip-tier-gold-grad)]` |
| 155 | `--vip-tier-gold-acc` | `#e3c15a` | = :root | `--color-vip-tier-gold-acc` / `bg-vip-tier-gold-acc`, `text-vip-tier-gold-acc`, `border-vip-tier-gold-acc` |
| 156 | `--vip-tier-platinum-grad` | `linear-gradient(135deg, #6b7280, #cfd6e0, #e8edf3)` | = :root | `[background:var(--vip-tier-platinum-grad)]` |
| 157 | `--vip-tier-platinum-acc` | `#cfd6e0` | = :root | `--color-vip-tier-platinum-acc` / `bg-vip-tier-platinum-acc`, `text-vip-tier-platinum-acc`, `border-vip-tier-platinum-acc` |
| 158 | `--vip-tier-diamond-grad` | `linear-gradient(135deg, #3f7fb5, #9fd7ee, #e6f7ff)` | = :root | `[background:var(--vip-tier-diamond-grad)]` |
| 159 | `--vip-tier-diamond-acc` | `#9fd7ee` | = :root | `--color-vip-tier-diamond-acc` / `bg-vip-tier-diamond-acc`, `text-vip-tier-diamond-acc`, `border-vip-tier-diamond-acc` |
| 160 | `--vip-radius-table` | `14px` | = :root | `--radius-vip-radius-table` / `rounded-vip-radius-table` |
| 161 | `--vip-radius-control` | `12px` | = :root | `--radius-vip-radius-control` / `rounded-vip-radius-control` |
| 162 | `--vip-radius-gem` | `8px` | = :root | `--radius-vip-radius-gem` / `rounded-vip-radius-gem` |
| 163 | `--brand-font-display` | `var(--font-head)` | = :root | `--font-brand-font-display` / `font-brand-font-display` |

Proposed `src/styles/tw-theme.css`, generated from the 163 rows above. The probe compiled it on tailwindcss 4.3.4; sample output: `.p-space-5{padding:var(--space-5)}`, `.max-w-frame-w{max-width:var(--frame-w)}`, `.text-t-balance{font-size:var(--t-balance)}` with no line-height, `.font-weight-bold{font-weight:var(--weight-bold)}`.

```css
/* src/styles/tw-theme.css: maps utility names onto the unchanged tokens.css properties. */
@theme inline reference {
  --*: initial;
  /* color (58) */
  --color-canvas: var(--canvas); --color-shell: var(--shell); --color-surface: var(--surface);
  --color-surface-2: var(--surface-2); --color-surface-3: var(--surface-3); --color-tile: var(--tile);
  --color-surface-hover: var(--surface-hover); --color-surface-disabled: var(--surface-disabled); --color-scrim: var(--scrim);
  --color-win: var(--win); --color-loss: var(--loss); --color-error: var(--error);
  --color-green: var(--green); --color-info: var(--info); --color-caution: var(--caution);
  --color-on-caution: var(--on-caution); --color-focus-ring: var(--focus-ring); --color-text-hi: var(--text-hi);
  --color-text: var(--text); --color-text-mid: var(--text-mid); --color-text-dim: var(--text-dim);
  --color-border: var(--border); --color-tint: var(--tint); --color-header-bg: var(--header-bg);
  --color-member-canvas: var(--member-canvas); --color-qr-surface: var(--qr-surface); --color-balance-text: var(--balance-text);
  --color-progress-track: var(--progress-track); --color-progress-fill: var(--progress-fill); --color-progress-dot: var(--progress-dot);
  --color-progress-tag-text: var(--progress-tag-text); --color-brand-accent: var(--brand-accent); --color-brand-accent-2: var(--brand-accent-2);
  --color-brand-accent-hairline: var(--brand-accent-hairline); --color-brand-on-accent: var(--brand-on-accent); --color-brand-cta: var(--brand-cta);
  --color-brand-cta-accent: var(--brand-cta-accent); --color-vip-page-bg: var(--vip-page-bg); --color-vip-panel-bg: var(--vip-panel-bg);
  --color-vip-panel-alt: var(--vip-panel-alt); --color-vip-inner-bg: var(--vip-inner-bg); --color-vip-text-primary: var(--vip-text-primary);
  --color-vip-text-secondary: var(--vip-text-secondary); --color-vip-text-muted: var(--vip-text-muted); --color-vip-text-faint: var(--vip-text-faint);
  --color-vip-text-disabled: var(--vip-text-disabled); --color-vip-gold-start: var(--vip-gold-start); --color-vip-gold-mid: var(--vip-gold-mid);
  --color-vip-gold-end: var(--vip-gold-end); --color-vip-gold-ink: var(--vip-gold-ink); --color-vip-gold-tint: var(--vip-gold-tint);
  --color-vip-positive: var(--vip-positive); --color-vip-hairline: var(--vip-hairline); --color-vip-tier-bronze-acc: var(--vip-tier-bronze-acc);
  --color-vip-tier-silver-acc: var(--vip-tier-silver-acc); --color-vip-tier-gold-acc: var(--vip-tier-gold-acc); --color-vip-tier-platinum-acc: var(--vip-tier-platinum-acc);
  --color-vip-tier-diamond-acc: var(--vip-tier-diamond-acc);
  /* spacing (27) */
  --spacing-space-1: var(--space-1); --spacing-space-2: var(--space-2); --spacing-space-3: var(--space-3);
  --spacing-space-4: var(--space-4); --spacing-space-5: var(--space-5); --spacing-space-6: var(--space-6);
  --spacing-space-7: var(--space-7); --spacing-space-8: var(--space-8); --spacing-gutter: var(--gutter);
  --spacing-header-h: var(--header-h); --spacing-nav-h: var(--nav-h); --spacing-logo-h: var(--logo-h);
  --spacing-rail-w: var(--rail-w); --spacing-frame-w: var(--frame-w); --spacing-bottombar-h: var(--bottombar-h);
  --spacing-band-gap: var(--band-gap); --spacing-gap: var(--gap); --spacing-gap-sm: var(--gap-sm);
  --spacing-gap-xs: var(--gap-xs); --spacing-feature-w: var(--feature-w); --spacing-tile-h: var(--tile-h);
  --spacing-provider-w: var(--provider-w); --spacing-provider-h: var(--provider-h); --spacing-card-pad: var(--card-pad);
  --spacing-card-pad-sm: var(--card-pad-sm); --spacing-tap-min: var(--tap-min); --spacing-tap-bar: var(--tap-bar);
  /* text (11) */
  --text-t-micro: var(--t-micro); --text-t-sm: var(--t-sm); --text-t-body: var(--t-body);
  --text-t-h3: var(--t-h3); --text-t-h2: var(--t-h2); --text-t-h1: var(--t-h1);
  --text-t-display: var(--t-display); --text-t-hero: var(--t-hero); --text-t-num: var(--t-num);
  --text-t-num-lg: var(--t-num-lg); --text-t-balance: var(--t-balance);
  /* leading (2) */
  --leading-lh-body: var(--lh-body); --leading-lh-tight: var(--lh-tight);
  /* font-weight (3) */
  --font-weight-weight-reg: var(--weight-reg); --font-weight-weight-semi: var(--weight-semi); --font-weight-weight-bold: var(--weight-bold);
  /* font (4) */
  --font-brand-font-body: var(--brand-font-body); --font-brand-font-num: var(--brand-font-num); --font-brand-font-head: var(--brand-font-head);
  --font-brand-font-display: var(--brand-font-display);
  /* radius (8) */
  --radius-sm: var(--radius-sm); --radius-md: var(--radius-md); --radius-lg: var(--radius-lg);
  --radius-card: var(--radius-card); --radius-pill: var(--radius-pill); --radius-vip-radius-table: var(--vip-radius-table);
  --radius-vip-radius-control: var(--vip-radius-control); --radius-vip-radius-gem: var(--vip-radius-gem);
  /* ease (2) */
  --ease-standard: var(--ease-standard); --ease-entrance: var(--ease-entrance);
}
```

### 3.7 Token lint for Tailwind (ADR-002): exact re-specification

The file stays `scripts/token-lint.mjs`. It stays zero-dependency Node ESM with `ROOT = resolve(__dirname, "..", "src")`. Package scripts are unchanged: `"lint:tokens": "node scripts/token-lint.mjs"` and `"lint:tokens:self-test": "node scripts/token-lint.mjs --self-test"`.

Unchanged byte-for-byte from `01-01-f-stack.html#f-stack-token-lint`: `GROUP_A_EXACT`, `GROUP_A_PREFIX`, `isGroupA`, `RAW_RAMP` (same 10 names, same order), `PINNED`, `stripComments`, `topLevelBlocks`, `declaredVars`, every A1 and A3 branch and message, and the final OK/FAILED output and exit codes.

Changes:
1. `walk()` collects files ending `.css`, `.ts` or `.tsx`. The original collects `.css` only.
2. `lintContent(raw, rel)`:
   - `isDefinition = rel.endsWith("brands.css") || rel.endsWith("tokens.css") || rel.endsWith("themes.css")`.
   - `isScript = rel.endsWith(".ts") || rel.endsWith(".tsx")`.
   - `isStyle = rel.endsWith(".css") && !isDefinition`. This replaces `isModule`, and `*.module.css` stays covered.
   - Preprocess: CSS uses `stripComments`. TS uses `stripComments(raw).replace(/(^|[^:\\])\/\/.*$/gm, "$1")`, which drops line comments but not `https://`.
   - A1/A3 run when `isDefinition` (unchanged).
   - A2 runs when `isStyle || isScript`. For each `ramp` of `RAW_RAMP`, test `new RegExp(\`(?:var\\(\\s*|\\(\\s*(?:[a-z-]+:)?|\\[\\s*)${ramp}(?![a-z0-9-])\`, "i")`. That catches `var(--gold-500)`, Tailwind `bg-(--gold-500)`, typed `text-(color:--text-on-gold)` and v3-style `bg-[--cta]`, and keeps the `--cta-grad`/`--cta` boundary. Message unchanged: `A2 ${rel}: component reads RAW-RAMP ${ramp} via var() — use its --brand-* alias`.
3. Self-test: 8 seeds `[content, rel, expectedIds, exact?]`. A seed passes when it is clean-expected with zero violations, or when every violation id (text before the first space) is in `expectedIds`, the count is at least `expectedIds.length`, and, if `exact`, the count equals that length.

| # | content | rel | expected |
|---|---|---|---|
| S1 | `[data-brand="x"]{--canvas:#000;--win:#0f0;}` | `styles/brands.css` | A1, A1 (fires 4 lines) |
| S2 | `.a{color:var(--gold-500);}` | `ui/X/X.module.css` | A2 |
| S3 | `:root{--focus-ring:var(--brand-accent);}` | `styles/tokens.css` | A3 |
| S4 | `@theme inline reference{--color-accent:var(--gold-500);}` | `styles/tw-theme.css` | A2 |
| S5 | `export const c = "bg-(--cta-grad) text-(color:--text-on-gold)";` | `ui/Button/Button.tsx` | A2, A2 (exact) |
| S6 | `export const s = { fontFamily: "var(--font-num)" };` | `components/x/X.tsx` | A2 |
| S7 | `// var(--gold-500) in a comment` + newline + `export const c = "bg-(--brand-cta-grad) font-brand-font-num";` | `ui/Y/Y.tsx` | none (clean) |
| S8 | `.b{color:var(--cta-accent);}` | `ui/Z/z.css` | A2 (exact: 1, the boundary) |

Output per seed: `  seed ${rel}: ${v.length ? v.join("; ") : "NO VIOLATION"}`. On success it prints the original line verbatim, `SELF-TEST OK: A1/A2/A3 each fire on a seeded violation; a clean tree passes.`, and exits 0. Otherwise it prints `SELF-TEST FAILED: expected all 8 seeds to behave, got ${ok}` and exits 1.

Acceptance (mechanical):
- `npm run lint:tokens:self-test` exits 0, and its output contains 8 `seed` lines and `SELF-TEST OK`.
- `npm run lint:tokens` on the rebuilt tree exits 0 and prints exactly `token-lint OK: GROUP-A/GROUP-B contract (A1/A2/A3) holds.`
- Negative probe (scratch copy, not committed): adding `className="bg-(--gold-500)"` to any `src/**/*.tsx` makes `lint:tokens` exit 1 with an `A2` line.

Checklist mapping (`05-01-v-checklist.html#v-static`): "No CSS module reads a raw ramp variable" becomes "no component source (`.css` outside the three definition files, `.ts`, `.tsx`) reads a raw ramp variable". A2 enforces it. A1/A3 wording is unchanged.

### 3.8 next/font (vietnamese subset), data-brand / data-theme

- `src/app/layout.tsx` is verbatim. `Be_Vietnam_Pro({ subsets: ["latin", "vietnamese"], weight: ["400", "600", "700"], variable: "--font-be-vietnam", display: "swap" })` and `Montserrat({ subsets: ["latin", "vietnamese"], weight: ["700", "800"], variable: "--font-montserrat", display: "swap" })`. Both `.variable` classes go on `<html className>`. There are no `@font-face` rules and no font `@theme` key for `--font-be-vietnam`/`--font-montserrat`. The chain stays `--font-be-vietnam` -> `--font-body`/`--font-num` (raw, never read by components) -> `--brand-font-body`/`--brand-font-num` -> `font-brand-font-body`/`font-brand-font-num` utilities. Body gets it from typography.css/globals in base.
- Weight gaps are reproduced as built: no Montserrat 600, no Be Vietnam Pro 800 (FC-11).
- `<html lang="vi" data-brand="yaobet" data-theme="obsidian">` is static. There is no switcher and no `@custom-variant` per brand (YAGNI; brand re-skins through var re-pointing only). `data-brand` must stay on `<html>` (FC-10).
- Checks: built HTML matches `<html lang="vi" data-brand="yaobet" data-theme="obsidian" class="`. At least 2 `@font-face` blocks with `unicode-range` covering `U+1EA0-1EF9` exist in `.next/static/**/*.css`. The verify-app-ds "Vietnamese sets in one face" check passes on ữ ặ ở.

### 3.9 MockAuthProvider (initialState "tiered") and the DEV toggle

- `src/lib/auth/{session.tsx, modal.tsx, guard.ts, fixtures.ts, index.ts}` are verbatim (`01-09-f-lib.html#f-lib-auth`). The provider default stays `initialState = "guest"`. `signIn(as = "tiered")`, `signOut()` -> guest, and `cycleDevState()` steps guest -> level-0 -> tiered -> guest. The error text is `useAuth must be used within <MockAuthProvider>`. State is never persisted (no storage, no cookie).
- `src/app/providers.tsx` is verbatim: `<MockAuthProvider initialState="tiered"><AuthModalProvider>{children}</AuthModalProvider></MockAuthProvider>` (FC-14 reproduced).
- The DEV toggle component is track S (`02-03-s-home-h.html#s-dev-auth-toggle`). Foundations fixes this contract for it:
  1. `if (process.env.NODE_ENV === "production") return null;`
  2. `button` with aria-label `Mở bảng chuyển trạng thái đăng nhập (dev)`, title `Dev: auth state`, label `DEV`.
  3. Panel `role="group"`, aria-label `Trạng thái đăng nhập (dev)`, close button aria-label `Đóng`.
  4. The cycle button className must include the literal unstyled class `cycle`, and its label span the literal class `stateLabel`. They must come first in DOM order among elements matching `[class*="cycle"]`. Labels: `Khách`, `Cấp 0`, `Hội viên`.
- Acceptance: run `npm run build && npx next start -p 3108`, then `curl -s :3108/ | rg -c 'Mở bảng chuyển trạng thái đăng nhập'` gives 0. In dev on :3107, the `05-01` capture script's `setState` reaches `Hội viên` and `Khách`, and `checkState` returns `ok`.

## 4. Defects to reproduce

| id | anchor | what | how to reproduce | proposed later fix |
|---|---|---|---|---|
| FC-01 | `01-01-f-stack.html#f-stack-token-lint` | Lint is narrower than the tokens.css header claim ("No component hardcodes a hex / px / duration"); only RAW-ramp var() reads are banned | Keep A2 scoped to RAW-ramp reads (ADR-002); keep the src/ui literal list (`01-11-f-unused.html#f-unused-literals`) as arbitrary values | Add a literal hex/px lint for class strings |
| FC-02 | `01-02-f-tokens.html#f-tokens`, `01-11-f-unused.html#f-unused` | 17 tokens defined, never read | Keep all 17 in tokens.css, give them no @theme key | Delete or wire them |
| FC-03 | `01-02-f-tokens.html#f-tokens` | `--shadow-2` comment says QuickActionRail reads it; nothing does | Keep the token and comment | Delete both |
| FC-04 | `01-02-f-tokens.html#f-tokens`, `00-05-i-discrepancies.html#i-discrepancies` (5) | `--brand-logo` never read; Header/AuthModal hard-code `/assets/logo.svg` | Keep the token; track S keeps the hard-coded `<img src="/assets/logo.svg">` | Read the logo from brand config |
| FC-05 | `01-02-f-tokens.html#f-tokens` | Stale `--progress-track` comment ("our OLED #1f222e") | Keep the comment | Fix the comment |
| FC-06 | `01-02-f-tokens.html#f-tokens` | `--gold-grad` and `--cta-grad` are solid colours despite the name | Keep the values | Rename |
| FC-07 | `01-02-f-tokens.html#f-tokens`, `01-03-f-themes.html#f-themes-brand`, `00-05` (6) | Under emerald, `--brand-cta-grad` is a gradient, so the primary button carries one | Button `.primary` uses `[background:var(--brand-cta-grad)]` (R3). Check: set `data-brand="emerald"` in devtools; the button's computed background-image is `linear-gradient(...)` | Flat emerald CTA, or Button reads `--brand-cta` |
| FC-08 | `01-02-f-tokens.html#f-tokens` | `--vip-text-*` cool blue-greys against the warm app ladder (intentional seam) | Keep the values | Owner decision |
| FC-09 | `01-02-f-tokens.html#f-tokens`, `01-04-f-typography.html#f-typography` | Stale Cinzel comments (`--brand-font-display`, typography.css "Cinzel luxury layer is untouched", tokens.css VIP block "--font-cinzel is provided at runtime") | Comments only, no runtime effect; keep the wording minus plan tags (G19) | Fix the comments |
| FC-10 | `01-03-f-themes.html#f-themes-brand` | Brand-following member tokens resolve at `:root`; moving `data-brand` to a descendant breaks them | `data-brand` only on `<html>` | Declare them per brand block |
| FC-11 | `01-04-f-typography.html#f-typography-loaders` | Montserrat loads only 700/800 and Be Vietnam Pro only 400/600/700; other weights are synthesised or snapped | Exact loader weights | Add weights |
| FC-12 | `01-04-f-typography.html#f-typography-cascade` | globals.css comment "Headings inherit the body face" is wrong; UA heading sizes apply where no size is set | No preflight (ADR-003), so UA `h1 { font-size: 2em }` survives | Set heading sizes |
| FC-13 | `01-06-f-reset.html#f-reset-loading` | Root loading.tsx shows a home-shaped skeleton on every route without its own loader (/vip, /khuyen-mai, /cua-hang, /tier; inference) | Only the 7 listed `loading.tsx` files exist | Per-route loaders |
| FC-14 | `01-07-f-root-layout.html#f-root-layout-providers`, `00-03`, `00-05` (1) | Every load boots signed in as `tiered` (Nguyễn Văn An, VIP 3 Bạch Kim) | `initialState="tiered"` | Default to guest |
| FC-15 | `01-09-f-lib.html#f-lib-format` | `formatVnd(-0.4)` -> `-0 ₫`; relativeTime rounds (30 s -> `1 phút trước`, 1439 min -> `1 ngày trước`); odds use `.` and percent uses `,`; no date formatter | format.ts verbatim; checks in F2 | Truncate before sign; floor |
| FC-16 | `01-09-f-lib.html#f-lib-i18n` | Header claims no hard-coded VN strings (false: src/ui has 13); duplicate keys; vip copy twin in lib/vip/copy.ts | i18n.ts verbatim | Consolidate |
| FC-17 | `01-09-f-lib.html#f-lib-auth` | `consumeResumeIntent` reads inside a setState updater and may return `{action:"none"}` | modal.tsx verbatim | Read from state/ref |
| FC-18 | `01-09-f-lib.html#f-lib-mock` (last callout) | lib/vip, lib/collection, lib/store are not documented in f-lib | Scope note: lease them to track R (G1) | n/a |
| FC-19 | `01-10-f-assets.html#f-assets` | Three `(1)` duplicates, unreferenced (baccarat byte-identical; keno and taixiu differ) | Copy all 36 files as-is | Delete |
| FC-20 | `01-10-f-assets.html#f-assets` | Two logos; `/assets/brand/logo.svg` never renders | Copy both | Unify |
| FC-21 | `01-10-f-assets.html#f-assets` | `public/assets/README.md` is stale (old palette, `<Image>`, "no J9 art") | Copy verbatim | Rewrite |
| FC-22 | `01-10-f-assets.html#f-assets` | `placeholders/product.svg` unused | Copy | Delete |
| FC-23 | `00-05-i-discrepancies.html#i-discrepancies` (15), data in `lib/mock/lottery.ts:54`, `:218` | Consolation `dust` on every card; losers built as near-misses | lottery.ts verbatim; `makeScratchCard(undefined, 1).id === "sc-v7zqd9py"` | Owner (track R spec) |
| FC-24 | `00-05` (2), data in `lib/mock/lobby.ts:34` | Every vertical `href` is `/?v=<id>`, which home ignores | lobby.ts verbatim | Point to `/<id>` |

Other `00-05` items are reproduced by their owning tracks: 3, 4 and 10 by S; 7, 8 and 9 by M; 12, 13, 14 and 16 by R; 11 applies to all.

## 5. Gaps and contradictions

| # | gap | guide quote | resolution proposed |
|---|---|---|---|
| G1 | "VIP maths" is not in f-lib | "Out of this track: src/lib/vip/* (tiers, formulas, copy), src/lib/collection/* … and src/lib/store/escalation.ts … Not documented here." | Carve `src/lib/vip/**`, `src/lib/collection/**`, `src/lib/store/**` out of the foundations lease and give them to track R (`04-01-r-vip.html`, `04-31-r-collection-lib.html`, `04-18-r-store.html`) |
| G2 | i18n.ts is not verbatim, only key tables; `t()` body not given | "export const vi = {…} as const holds 398 string leaves in 20 namespaces." | Builder copies `Igaming-Agent-1/apps/web/src/lib/i18n.ts` (691 lines, NFC) read-only. The tables confirm 398 leaves (sum of the 20 namespace counts) |
| G3 | notification-feed.ts (387 lines) is not verbatim; only the 34-row table | "notification-feed.ts (387 lines) — all 34 rows" | Copy the original read-only; the table is the acceptance oracle |
| G4 | File count mismatch | "mock/ (19 fixture modules + index barrel)" | Source has 19 files including index.ts (verified with `ls`); rebuild those 19 |
| G5 | next.config.ts must not stay empty for Tailwind; the archived repo adds `cacheComponents: true` and `partialPrefetching: true` | "The file is empty (the create-next-app default)." | Empty config plus only `turbopack.rules["*.css"] = { loaders: ["@tailwindcss/turbopack"], as: "*.css" }`. Drop `cacheComponents` (inference: Next 16 cacheComponents rejects `new Date()` during prerender, which every mock `nowIso()` does) |
| G6 | Version pins | guide `next 16.2.9`, `react 19.2.4` | DECISIONS keeps 16.4.5 / 19.3.0; `eslint-config-next` follows next |
| G7 | `playwright` is a guide devDependency but is absent from the current package.json | "playwright ^1.61.1 … dev" | New dependency: needs explicit user approval before F0 adds it; required by verify-app-ds and the capture recipe |
| G8 | Guide says copy token-lint byte-for-byte; D2 says re-specify | "Rebuild: copy scripts/token-lint.mjs byte-for-byte" | ADR-002 (3.7) supersedes per DECISIONS D2. Also: the original self-test message "a clean tree passes" was never checked; seed S7 now checks clean content |
| G9 | Root loading.tsx imports `@/components/home/Home.module.css` (`.page .main .skelRow .skelGrid`), which does not exist under Tailwind | "It reuses classes from src/components/home/Home.module.css … track S documents those rules" | Track S's home leaf owns `src/app/loading.tsx` and the shared class strings |
| G10 | stub.module.css lives in `src/app` and is shared by 5 track M routes | "Used by 5 placeholder routes" | Foundations ships `stub-page/stub-heading/stub-body` `@utility` in `src/styles/stub.css`; track M uses them |
| G11 | Capture script couples to CSS-Module class substrings | "keep the module class named cycle … or change the selector" | Literal classes `cycle`, `stateLabel` (3.9) |
| G12 | 5 empty asset folders cannot exist in git | "Empty asset folders (no files): /assets/games, /assets/medals, /assets/perks, /assets/promos, /assets/tiers." | Skip; no runtime effect (do not invent `.gitkeep` content in public) |
| G13 | Favicon description is partial | "MS Windows icon resource with 4 icons (16×16, 32×32, …)" | Binary copy of `src/app/favicon.ico` (25,931 bytes, verified) |
| G14 | Two harness ports | verify-app-ds uses `http://localhost:3000`; capture uses `next dev -p 3107` | Gate runs both against the port each script hard-codes |
| G15 | Capture script uses `window.next.router.push` | "await p.evaluate(() => window.next.router.push('/'))" | Assumption: Next 16.4.5 dev still exposes `window.next.router`; verify in the F5 gate |
| G16 | Mock timestamps in tables are a run snapshot | "the rebuild must keep the relative offsets (in the verbatim source), not these absolute values" | isoAgo/isoIn offsets only |
| G17 | `fold()` regex holds literal combining marks | `.replace(/[̀-ͯ]/g, "")` (U+0300–U+036F, verified in source bytes) | Copy bytes exactly, or write the equivalent `/[̀-ͯ]/g` |
| G18 | HTML entities in copy | e.g. `vi.rg.terms` holds `&` encoded as `&amp;` in the section HTML (13 `&amp;` in 01-09) | Copy from decoded text or the original source, never raw HTML |
| G19 | Verbatim comments contain plan/audit tags (`Wave 1.3`, `SPEC-02 §0.3`, `GC-101`) that the harness forbids in code comments | tokens.css / brands.css / eslint headers | Keep code byte-exact; drop the tag tokens from comments (no runtime effect; the lint strips comments) |
| G20 | Archived files in this repo contradict the guide | "No error.tsx, global-error.tsx … exist (not found in source)" | Wave 0 deletes `src/app/{error,global-error,not-found}.tsx`, `src/app/sanh-game`, `scripts/verify-*.mjs` (old px-literal rule would fail exact arbitrary px), and `public/assets/images/**`, `public/placeholders/**` (D4) |
| G21 | Stock utilities silently emit nothing after `--*: initial` | (probe: `p-4`, `text-sm`, `shadow-md` -> no CSS) | Optional F0 gate `scripts/tw-unknown-classes.mjs` (under 100 lines, tailwindcss `compile().build([cls])` per className token; flag empty output). PM decides |
| G22 | lottery self-test command needs `tsx` (not installed) | "npx tsx -e 'import(\"./src/lib/mock/lottery.ts\")…'" | Gate compiles with `tsc --module commonjs` to scratch and runs `node` (F3b) |
| G23 | Hover semantics | Tailwind v4 default `hover:` is `@media (hover:hover)`; guide uses plain `:hover` | `@custom-variant hover (&:hover)` in globals (probe) |

## 6. Assets

All copied byte-identical from `Igaming-Agent-1/apps/web/public/` (36 files, verified with `find -type f | wc -l`). Dimensions and bytes are quoted from `01-10-f-assets.html#f-assets`.

| public path | size | bytes | used by |
|---|---|---|---|
| /assets/README.md | - | 2,327 | unused |
| /assets/banners/hero-banner-1.jpg | 1556×620 | 755,416 | lib/mock/promos.ts |
| /assets/banners/pc-banner-vpn.jpg | 1556×620 | 759,562 | lib/mock/promos.ts |
| /assets/banners/pc-hero-banner-UCLfinal.jpg | 1556×620 | 1,031,681 | QuickActionRail, promos.ts |
| /assets/brand/emerald-logo.svg | 140×36 | 412 | brands.css (never rendered) |
| /assets/brand/logo.svg | 140×36 | 410 | brands.css, tokens.css (never rendered) |
| /assets/casino/keno_vietlott (1).png | 234×160 | 72,266 | unused |
| /assets/casino/keno_vietlott.png | 234×160 | 71,825 | games.ts |
| /assets/casino/mg_baccarat_landscape (1).png | 702×480 | 452,392 | unused |
| /assets/casino/mg_baccarat_landscape.png | 702×480 | 452,392 | Footer, games.ts |
| /assets/casino/mg_roulette_landscape.png | 702×480 | 443,447 | games.ts |
| /assets/casino/mg_sicbo_landscape.png | 702×480 | 469,368 | games.ts |
| /assets/casino/sunwin_taixiu-live-landscape (1).png | 234×160 | 68,116 | unused |
| /assets/casino/sunwin_taixiu-live-landscape.png | 234×160 | 68,102 | games.ts |
| /assets/logo.svg | 2914×623 | 5,859 | AuthModal, Header |
| /assets/placeholders/medal.svg | 120×120 | 636 | medals.ts |
| /assets/placeholders/perk.svg | 200×140 | 641 | vip.ts |
| /assets/placeholders/poster.svg | 300×400 | 634 | InviteTools, referral.ts |
| /assets/placeholders/product.svg | 240×240 | 640 | unused |
| /assets/placeholders/promo.svg | 343×160 | 640 | promos.ts |
| /assets/placeholders/tier-badge.svg | 120×120 | 632 | vip.ts |
| /assets/placeholders/tile.svg | 240×160 | 635 | games.ts |
| /assets/players/dowman.jpeg | 399×501 | 29,901 | lib/collection/fixtures/epl.ts |
| /assets/players/elliott.jpeg | 554×554 | 31,694 | epl.ts |
| /assets/players/gabriel.jpeg | 399×501 | 31,997 | epl.ts |
| /assets/players/gyokeres.jpeg | 399×501 | 28,209 | epl.ts |
| /assets/players/konate.jpeg | 739×415 | 26,641 | epl.ts |
| /assets/players/rice.jpeg | 399×501 | 25,902 | epl.ts |
| /assets/players/saka.jpeg | 400×500 | 25,451 | epl.ts |
| /assets/players/salah.jpeg | 201×251 | 8,681 | epl.ts |
| /assets/players/vandijk.jpeg | 683×449 | 34,689 | epl.ts |
| /assets/sports/Betgming_football_grid.png | 702×480 | 526,809 | SportsLifestyle |
| /assets/sports/e-vitualsports.png | 702×480 | 451,649 | SportsLifestyle |
| /assets/sports/k-sports.png | 468×320 | 253,155 | SportsLifestyle, Footer, lobby.ts |
| /assets/sports/saba-sports.png | 702×480 | 465,023 | SportsLifestyle, Footer, lobby.ts |
| /assets/store/reward-coins.jpg | 524×416 | 176,608 | store.ts |
| src/app/favicon.ico (App Router icon) | 4 icons, largest 256×256 | 25,931 (verified) | /favicon.ico |

Images render with plain `<img>` in 8 files; `next/image` is used only in `components/referral/InviteTools.tsx` (track M). No `images` config is needed. The `(1)` file names hold spaces and parentheses; URL-encode them if they are ever referenced. There is no `fonts/` folder.

## 7. Proposed leaves

All leaves are disjoint. Order: F0 -> F1 -> F2 -> F3a -> F3b, with F4 in parallel; F5 last, after track S's shell leaf.

| leaf | allowed_files | implements | needs | acceptance (mechanical) |
|---|---|---|---|---|
| F0 stack-and-gates | `package.json`, `package-lock.json`, `next.config.ts`, `tsconfig.json`, `eslint.config.mjs`, `scripts/token-lint.mjs`, `scripts/verify-*.mjs` (delete), `verify-app-ds.mjs` | `01-01-f-stack.html#f-stack-*`, ADR-002, G5, G7, G20 | user approval for `playwright` (G7); PM approval (root config is outside the suggested lease) | `npm run lint:tokens:self-test` exits 0 and prints 8 `seed` lines + `SELF-TEST OK`; `jq -r '.scripts["lint:tokens"]' package.json` = `node scripts/token-lint.mjs`; `rg -c cacheComponents next.config.ts` = 0; `rg -c '@tailwindcss/turbopack' next.config.ts` = 1; `rg -c 'Collection components import the ports barrel' eslint.config.mjs` = 1; `fd -e mjs verify- scripts` empty |
| F1 styles-foundation | `src/app/globals.css`, `src/styles/reset.css`, `src/styles/tokens.css`, `src/styles/themes.css`, `src/styles/brands.css`, `src/styles/typography.css`, `src/styles/motion.css`, `src/styles/keyframes.css`, `src/styles/tw-theme.css`, `src/styles/stub.css` (and delete `src/styles/brand.yaobet.css`, `src/styles/components.css`) | `01-02` to `01-06`, ADR-003, 3.2 to 3.6 | F0 | `npm run lint:tokens` exits 0 and prints the exact OK line; `rg -c '^\s*--[a-z0-9-]+\s*:' src/styles/tokens.css` = 163; `rg -c -- '--brand-' src/styles/brands.css` >= 24; `rg -c 'layer\(base\)' src/app/globals.css` = 6; `rg -c 'tailwindcss/preflight\|@import "tailwindcss"' src/app/globals.css` = 0; `rg -c '@keyframes ui-' src/styles/keyframes.css` = 7; `rg -c -- '--color-\|--spacing-\|--text-t-\|--leading-\|--font-weight-\|--font-brand-\|--radius-\|--ease-' src/styles/tw-theme.css` totals 115 keys; after build: `rg -l -- '--canvas:#0a0a0a' .next/static` non-empty and `rg -c 'var\(--spacing\)' .next/static -g '*.css'` = 0 |
| F2 lib-core-and-providers | `src/lib/format.ts`, `src/lib/i18n.ts`, `src/lib/rg.ts`, `src/lib/types.ts`, `src/lib/auth/session.tsx`, `src/lib/auth/modal.tsx`, `src/lib/auth/guard.ts`, `src/lib/auth/fixtures.ts`, `src/lib/auth/index.ts`, `src/app/providers.tsx` | `01-09-f-lib.html#f-lib-format`, `#f-lib-i18n`, `#f-lib-rg`, `#f-lib-types`, `#f-lib-auth`; `01-07#f-root-layout-providers` | F0 | `npx tsc --noEmit` exits 0. Compile `format.ts i18n.ts types.ts` with `tsc --module commonjs` into scratch, then node asserts: `formatVnd(1234567)` = `1.234.567 ₫`, `formatVnd(-0.4)` = `-0 ₫`, `formatSignedVnd(1234567)` = `+1.234.567 ₫`, `formatOdds(3.6)` = `3.60`, `formatPercent(12.5,1)` = `12,5%`, `formatPresetChip(6888000)` = `6.888K`, relativeTime at 0.5/90/1439 min = `1 phút trước`/`2 giờ trước`/`1 ngày trước`; i18n leaf count = 398; `rg -c 'initialState="tiered"' src/app/providers.tsx` = 1; `rg -c 'initialState = "guest"' src/lib/auth/session.tsx` = 1; `rg -c 'useAuth must be used within <MockAuthProvider>' src/lib/auth/session.tsx` = 1 |
| F3a mock-data-1 | `src/lib/mock/helpers.ts`, `types.ts`, `lobby.ts`, `games.ts`, `vip.ts`, `wallet.ts`, `promos.ts`, `store.ts`, `referral.ts`, `cashback.ts` (all under `src/lib/mock/`) | `01-09-f-lib.html#f-lib-mock` | F2 | `tsc` to scratch, then node: getVerticals length 9 and `[0].href` = `/?v=casino`; getGames 16; getProviders 6; getPromos ids `pr1,pr2,pr3,pr7,pr8,pr4,pr5,pr6`; getProducts 11; getPointsBalance 3250; getLeaderboard ranks `1,2,3,5,6,7,8`; getJackpot pool 28686888000 freshness 15000; getVipProgress current 18600000 |
| F3b mock-data-2 | `src/lib/mock/records.ts`, `messages.ts`, `notification-feed.ts`, `profile.ts`, `deposit.ts`, `medals.ts`, `contribution.ts`, `lottery.ts`, `index.ts` | `01-09-f-lib.html#f-lib-mock` | F3a | node: getNotificationBell 34 rows, 6 unread, first id `f01`; getContributionCatalogue 240; deriveProviders 19, first `BTi`; getRestrictedGames().games 30; getSecurityIndex score 40; lottery `selfTest()` does not throw; `makeScratchCard(undefined,1).id` = `sc-v7zqd9py`, `.dust` = 8000; SCRATCH_ODDS.rungCost = `2.541,70 ₫` |
| F4 public-assets | `public/**`, `src/app/favicon.ico` | `01-10-f-assets.html#f-assets` | none | `find public -type f \| wc -l` = 36; every file `cmp -s` equal to the original; `stat -f%z public/assets/logo.svg` = 5859; `stat -f%z src/app/favicon.ico` = 25931; `public/assets/images` and `public/placeholders` are absent |
| F5 root-composition | `src/app/layout.tsx` | `01-07-f-root-layout.html#f-root-layout-*`, `01-04#f-typography-loaders`, 3.8, 3.9 | F1, F2, track S shell leaf (AppShell, Footer, QuickActionRail), track S home leaf (DevAuthToggle, loading.tsx) | `rg -c 'subsets: \["latin", "vietnamese"\]' src/app/layout.tsx` = 2; `curl -s :3107/` matches `lang="vi" data-brand="yaobet" data-theme="obsidian"`, `<title>Yaobet</title>`, `Yaobet — nhà cái trực tuyến.`, `content="#0a0a0a"`; `/` returns 200; production `next start -p 3108` home has 0 matches for `Mở bảng chuyển trạng thái đăng nhập`; the 05-01 capture `setState('Khách')` and `checkState` pass |

Not leased here: `src/app/loading.tsx` (track S, G9); `src/lib/vip/**`, `src/lib/collection/**`, `src/lib/store/**` (track R, G1); the DevAuthToggle component (track S, contract in 3.9).

## 8. Risks

1. **Silent Tailwind no-ops and lookalikes**: stock utilities emit nothing after `--*: initial`; `max-[639px]`, `scale-*`, `/NN` opacity, `bg-(--x)`, `transition-colors` and `rounded-full` each emit something that is close but not exact (probe). Mitigation: publish R1 to R18 to every builder prompt; optional class gate (G21); frontend-qc visual diff.
2. **Cascade inversion**: preflight, or any guide sheet left unlayered, changes heading sizes, img height, borders or the reduced-motion zeroing. Mitigation: ADR-003 import block; F1 greps (`layer(base)` = 6, no preflight).
3. **Shorthand loss on `background:`**: the emerald gradient defect (FC-07) and `--page-bloom`/`--header-card-grad` (colour layer last) need `[background:var(--x)]`. Mitigation: R3; FC-07 devtools check.
4. **Non-verbatim lib files**: i18n.ts (398 strings) and notification-feed.ts are tables only, so reconstruction can drift in nesting, order or diacritics. Mitigation: copy the original read-only (G2, G3); NFC and entity rules (G17, G18); leaf-count oracle.
5. **next.config / build environment**: archived `cacheComponents` can break mock `Date` use at prerender (inference); next/font/google downloads fonts at build (offline CI fails); playwright needs user approval (G7).
6. **Lint blind spots**: A2 cannot see dynamically built var names or raw ramp read via `getPropertyValue`. Accept and document (ADR-002).
7. **Ownership gaps**: lib/vip, lib/collection, lib/store (G1) and root loading.tsx (G9) fall between tracks unless the PM assigns them explicitly.
8. **Capture-script coupling**: losing the literal `cycle`/`stateLabel` classes or `window.next.router` (G11, G15) breaks the reference screenshot workflow, not the UI.

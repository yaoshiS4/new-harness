# Wine-Gold token mapping

Status: approved, 2026-11-07. The owner approved the overlay (D-DS6) and answered the open questions (D-DS5..D-DS8, review §5). Builds may start from this file.
Inputs: `docs/design/DS-WINE-GOLD-REVIEW.md` (defects §3, decisions §5), `docs/design/wine-gold/*.json` (the DS, 210 tokens), `overlay.proposal.json` (109 tokens: the 108 approved in D-DS6 plus the D-DS5 primitive `red.300`), `src/styles/{tokens,tw-theme,brands,themes,typography,motion}.css` at main 635a4dc.
Notation: `DS x.y` is a delivered token (refs drop the category prefix, as in the JSON). `OV x.y` is an overlay token. `keep` = Yaobet-owned structural token, no DS equivalent, value unchanged. Contrast = WCAG 2 ratio.

## 1. CSS custom-property naming

| Tier | CSS pattern | Example | Declared in | Read by |
|---|---|---|---|---|
| Primitive | `--wg-<category>-<path>` | `--wg-color-gold-500`, `--wg-space-16` | new `src/styles/brand.wine-gold.css` `:root` | semantic tier only (lint A2) |
| Brand seam | `--brand-*` (kept) | `--brand-accent` | `tokens.css`, `brands.css` | semantic tier |
| Semantic | `--<role>[-<variant>][-<state>]`, no Tailwind prefix | `--surface-raised`, `--fg-muted`, `--line-default` | `tokens.css` | components, utilities |
| Component | `--<component>-<property>[-<state>]` | `--input-helper`, `--odds-up` | `tokens.css` (component section) | that component only |

Primitive names drop `primitive` and the repeated category word: `primitive.spacing.scale.16` -> `--wg-space-16`; `primitive.type.size.h1` -> `--wg-type-size-h1`; `primitive.radius.surface` -> `--wg-radius-surface`; `primitive.elevation.shadow.2` -> `--wg-shadow-2`; `primitive.motion.duration.fast` -> `--wg-duration-fast`; `primitive.motion.easing.standard` -> `--wg-ease-standard`; `primitive.color.alpha.scrim.modal` -> `--wg-color-scrim-modal`.

Semantic colour roles follow TOKENS.md §2 rule 5 (no `bg`, `text` or `border` role, so no `bg-bg-*` or `text-text-*`):

| DS semantic group | Repo semantic name | Utility |
|---|---|---|
| `bg.page` | `--surface-canvas` | `bg-surface-canvas` |
| `surface.1` / `.2` / `.3` | `--surface-base` / `-raised` / `-overlay` | `bg-surface-raised` |
| `surface.wine.panel` / `.header` / `.deep` | `--surface-wine` / `-wine-header` / `-wine-deep` | `bg-surface-wine` |
| `overlay.scrim.modal` / `.art` | `--surface-scrim` / `-scrim-art` | `bg-surface-scrim` |
| `text.primary` / `secondary` / `muted` | `--fg-primary` / `-secondary` / `-muted` | `text-fg-muted` |
| `OV text.muted-raised` | `--fg-muted-raised` | `text-fg-muted-raised` |
| `text.accent` / `text.on-action` | `--fg-accent` / `--fg-on-accent` | `text-fg-accent` |
| `border.hairline` / `control` / `frame` | `--line-subtle` / `-default` / `-strong` | `border-line-default` |
| `action.primary.bg.rest` / `hover` / `pressed` | `--accent-primary` / `-hover` / `-press` | `bg-accent-primary` |
| `action.primary.sheen` | `--accent-sheen` (gradient, no namespace) | `bg-(image:--accent-sheen)` |
| `action.secondary.border` / `hover` / `pressed` / `OV text` | `--accent-secondary-line` / `-hover` / `-press` / `-fg` | `border-accent-secondary-line` |
| `action.ghost.hover.bg` | `--state-hover` | `bg-state-hover` |
| `focus.ring` / `focus.gap` | `--state-focus-ring` / `-focus-gap` | `ring-state-focus-ring` |
| `feedback.<x>` / `feedback.tint.<x>` (+ OV paused) | `--status-<x>-fg` / `--status-<x>-bg` | `text-status-danger-fg` |
| `feedback.win` / `OV feedback.loss` | `--money-positive` / `--money-negative` | `text-money-negative` |

Non-colour semantic names: `--space-N`, `--gutter`, `--gap-xs|sm|md`, `--band`, `--inset-sm|md`, `--field`, `--touch-min`, `--touch-gap`, `--control-h`, `--icon-sm|lg`; `--type-<role>-family|size|leading|weight`, `--weight-strong`; `--radius-control|surface|pill`; `--motion-duration-<x>`, `--ease-standard|enter|exit|ambient`; `--elevation-<n>-shadow`, `--elevation-<n>-surface`.

### 1.1 `tw-theme.css` `@theme inline reference`

Keep the current shape (`--*: initial;` first, then one line per utility; tw-theme.css:2-3). The utility var names a token in a Tailwind namespace and points at the semantic var, as today (`--color-canvas: var(--canvas)`, tw-theme.css:5):

```css
@theme inline reference {
  --*: initial;
  --color-surface-canvas: var(--surface-canvas);   /* bg-surface-canvas */
  --color-fg-primary: var(--fg-primary);           /* text-fg-primary */
  --color-line-default: var(--line-default);       /* border-line-default */
  --color-money-positive: var(--money-positive);   /* text-money-positive */
  --color-status-paused-bg: var(--status-paused-bg);
  --font-body: var(--type-family-body);            /* font-body; also -display, -numeric */
  --text-h1: var(--type-h1-size);                  /* text-h1 sets size + leading + weight */
  --text-h1--line-height: var(--type-h1-leading);
  --text-h1--font-weight: var(--type-h1-weight);
  --font-weight-strong: var(--weight-strong);
  --radius-surface: var(--radius-surface);         /* rounded-surface; same self-map as tw-theme.css:116 */
  --shadow-1: var(--elevation-1-shadow);           /* shadow-1 .. shadow-3 */
  --ease-enter: var(--ease-enter);
  --spacing-space-4: var(--space-4);               /* p-space-4, as today (tw-theme.css:64-90) */
  --spacing-inset-md: var(--inset-md);
}
```

Durations, z-index and icon sizes have no Tailwind namespace: use the variable shorthand (`duration-(--motion-duration-fast)`, `z-(--z-modal)`, `size-(--icon-sm)`), TOKENS.md §2 rule 3. Components never use `--wg-*` or a `--brand-*` var directly.

## 2. Colour

Values: "now" is the current literal; "new" is the resolved Wine-Gold value. Ratios from `$S/wg-overlay-check.out`.

| Current token (tokens.css) | Now | Maps to | New | Note |
|---|---|---|---|---|
| `--canvas` :35 | #0a0a0a | DS bg.page -> `--surface-canvas` | #1C1A17 | page |
| `--shell` :36 | #050505 | DS bg.page -> `--surface-shell` | #1C1A17 | own slot so obsidian keeps #050505 |
| `--surface` :37 | #141414 | DS surface.1 -> `--surface-base` | #26221D | |
| `--surface-2` :38 | #1a1a1a | DS surface.2 -> `--surface-raised` | #2E2A24 | |
| `--surface-3` :39 | #212121 | DS surface.3 -> `--surface-overlay` | #38332C | muted text needs `--fg-muted-raised` here |
| `--tile` :40 | #171717 | DS game.caption.bg -> `--surface-tile` | #26221D | |
| `--surface-hover` :41 | #262626 | DS action.ghost.hover.bg -> `--state-hover` | #38332C | |
| `--surface-disabled` :42 | #303030 | DS button.disabled.bg -> `--surface-disabled` | #2E2A24 | |
| `--scrim` :43 | rgba(0,0,0,.7) | DS overlay.scrim.modal -> `--surface-scrim` | rgba(28,26,23,.72) | |
| `--win` :46 | #45c9a5 | DS feedback.win -> `--money-positive` | #4CC38F | L 0.425 |
| `--loss` :47 | #f53f55 | OV feedback.loss -> `--money-negative` | #F2968E | OV primitive red.300 (D-DS5): L 0.426, 0.2% from win |
| `--error` :48 | #e42946 | DS feedback.danger -> `--status-danger-fg` | #EF7B71 | validation, never an outcome |
| `--green` :49 | #31bc69 | DS feedback.success -> `--status-success-fg` | #4CC38F | |
| `--info` :50 | #018fff | DS feedback.info -> `--status-info-fg` | #6FA8E0 | |
| `--caution` :51 | #f5a623 | DS feedback.warning -> `--status-warning-fg` | #F2894A | |
| `--on-caution` :52 | #2a1a00 | retired: solid warning fills become fg on DS feedback.tint.warning | #3D2312 bg | warning on tint 5.84 |
| `--focus-ring` :53 | #6ea8ff | DS focus.ring -> `--state-focus-ring` (+ `--state-focus-gap`) | #F4EFE6 | gap #1C1A17 |
| `--text-hi` :60 | #f2f0e4 | DS text.primary -> `--fg-primary` | #F4EFE6 | |
| `--text` :61 | #d6d3c7 | DS text.secondary -> `--fg-secondary` | #B8B0A3 | |
| `--text-mid` :62 | #888888 | DS text.muted -> `--fg-muted` | #9A9387 | 4.11 on surface.3: use muted-raised there |
| `--text-dim` :63 | #6f6f6f | DS text.muted -> `--fg-faint` (alias of `--fg-muted`) | #9A9387 | decorative step promoted to AA; slot kept for obsidian |
| `--border` :71 | gold rgba .55 | DS card.border -> `--line-subtle` | #3A352E | 1.30 on card.bg; shadow + step carry the edge now |
| `--tint` :72 | ivory rgba .05 | DS surface.2 -> `--state-tint` | #2E2A24 | alpha film becomes an opaque step |
| `--header-bg` :135 | #0a0a0a | DS surface.wine.header -> `--surface-header` | #4A1424 | D-DS7; fg-primary 12.94, fg-accent 9.15 |
| `--page-bloom` :181 | composite | keep, re-key inner refs (`--brand-accent`, `--surface-canvas`); D-DS8 stops | composite | `rgba(10,10,10,0)` -> `transparent`; cool lift `rgba(30,61,89,.25)` -> `color-mix(in srgb, var(--wg-color-blue-900) 25%, transparent)` |
| `--member-canvas` :186 | var(--canvas) | alias of `--surface-canvas` | #1C1A17 | |
| `--header-card-grad` :189 | composite | keep, re-key inner refs; D-DS8 stops | composite | `rgba(20,20,20,0)` -> `transparent` |
| `--wallet-sheen-grad` :194 | composite | keep; D-DS8 ivory stops | composite | champagne `rgba(242,240,228,a)` -> `color-mix(in srgb, var(--wg-color-ivory-100) a, transparent)`, a = 5% / 1.2% |
| `--card-sheen-grad` :197 | composite | keep; D-DS8 ivory stops | composite | same re-tint, a = 4% / 1% |
| `--qr-surface` :204 | #ffffff | keep (no DS equivalent) | #ffffff | a QR must sit on white |
| `--balance-text` :207 | var(--text-hi) | DS text.primary -> `--fg-primary` | #F4EFE6 | money is never gold (one exception: the right-rail jackpot, D-DS25) |
| `--progress-track` :212 | white .12 | DS vip.track -> `--vip-track` | #3A0F1C | |
| `--progress-fill` :213 | brand-accent | DS vip.fill -> `--vip-fill` | #E8C877 | thin gold line (BRAND.md §4) |
| `--progress-fill-grad` :219 | 2-stop gradient | keep syntax, both stops `var(--vip-fill)` | #E8C877 | only `background-image:` site |
| `--progress-dot` :220 | #ffffff | DS text.primary -> `--fg-primary` | #F4EFE6 | |
| `--progress-tag-bg` :224 | var(--surface-3) | DS surface.3 -> `--surface-overlay` | #38332C | |
| `--progress-tag-text` :225 | brand-accent | DS text.accent -> `--fg-accent` | #E8C877 | 7.72 on surface.3 |
| `--progress-tag-border` :226 | accent 32% mix | DS border.hairline -> `--line-subtle` | #3A352E | decorative |
| `--status-locked-bg` :230 | green 12% mix | DS feedback.tint.success -> `--status-success-bg` | #16372B | |
| `--status-locked-text` :231 | var(--green) | DS feedback.success -> `--status-success-fg` | #4CC38F | 5.89 on tint |
| `--gold-500` :241 | #d4af37 | DS primitive -> `--wg-color-gold-500` | #D4AF5A | |
| `--gold-600` :242 | #b4952f | DS primitive -> `--wg-color-gold-600` | #C29A3A | |
| `--gold-grad` :252 | #d4af37 | DS action.primary.fallback (flat); button uses `--accent-sheen` | #D4AF5A | |
| `--gold-hairline` :253 | gold rgba .55 | DS primitive gold.800 -> `--wg-color-gold-800` | #6A5521 | 2.21 on surface.1, decorative; uses an orphan (defect 7) |
| `--text-on-gold` :254 | #0a0a0a | DS text.on-action -> `--fg-on-accent` | #3A0F1C | 7.97 rest, 9.15 hover, 6.31 pressed |
| `--cta` :262 | #5e97c9 | DS text.accent (links, auth focus border) | #E8C877 | |
| `--cta-grad` :263 | #1e3d59 | DS action.primary.bg.rest (D-DS7: `.ui-btn-primary` is the gold primary) | #D4AF5A | label `--fg-on-accent` 7.97; ui.css:200 ink and :203 hover mix move to `--fg-on-accent` / `--accent-primary-hover` |
| `--cta-accent` :264 | #f53f55 | DS action.primary.bg.rest (D-DS7, Register) | #D4AF5A | `.ui-btn-danger` ink `--shell` on gold 8.33 |
| `--blue-soft` :265 | #8fb4d6 | DS text.secondary -> `--fg-secondary` | #B8B0A3 | |
| `--brand-accent` :282 | gold-500 | `--accent-primary` reads it; = DS action.primary.bg.rest | #D4AF5A | fills only |
| `--brand-accent-fg` (new seam) | n/a | `--fg-accent` reads it; = DS text.accent | #E8C877 | DS splits fill (500) and text (300) |
| `--brand-accent-2` :283 | gold-600 | `--accent-primary-press` | #C29A3A | |
| `--brand-accent-grad` :284 | gold-grad | `--accent-sheen` | gold.400 -> sheen.end | primary button only |
| `--brand-accent-hairline` :285 | gold-hairline | `--wg-color-gold-800` | #6A5521 | |
| `--brand-on-accent` :286 | text-on-gold | `--fg-on-accent` | #3A0F1C | |
| `--brand-cta` :287 | cta | `--fg-accent` | #E8C877 | |
| `--brand-cta-grad` :288 | cta-grad | `--accent-primary` (D-DS7) | #D4AF5A | |
| `--brand-cta-accent` :289 | cta-accent | `--accent-primary` (D-DS7) | #D4AF5A | fix: shell.css:1307 ink `--text-hi` -> `--fg-on-accent` (ivory on gold 1.82 -> wine.700 7.97) |

New component colour tokens from the overlay (no current token): `--card-bg`, `--button-secondary-text`, `--control-checked-mark`, `--input-text|label|helper|error-text`, `--tab-text-rest|active`, `--odds-up|down`, `--vip-bg`, `--vip-header-bg`, `--modal|toast|tooltip-border`, `--modal|toast|tooltip-meta`, `--feedback-bg-paused`; semantic `--status-paused-fg|bg`.

Switch versus checkbox (defect 9): checkbox = `--control-checked-bg` (gold.500) + `--control-checked-mark` (wine.700, 7.97). Switch = `--control-checked-track` (surface.3) + `--control-checked-knob` (gold.300, 7.72 on the track). The knob never sits on the gold fill (1.29). The gold checkbox fill is allowed as a mark: a named exception to TOKENS.md rule 4.2 (D-DS8).

## 3. Brands, themes and the VIP palette (D-DS4: re-keyed names, values unchanged)

`[data-brand="yaobet"]` (brands.css:19-32): same names, re-pointed exactly as the `--brand-*` rows of §2, plus `--brand-accent-fg: var(--wg-color-gold-300)`.

`[data-brand="emerald"]` (brands.css:36-52), values unchanged:

| Current | Value (unchanged) | New key |
|---|---|---|
| `--brand-accent` brands.css:37 | #1fbf73 | `--brand-accent` |
| (none) | #1fbf73 (same value as :37) | `--brand-accent-fg` |
| `--brand-accent-2` brands.css:38 | #169a5b | `--brand-accent-2` |
| `--brand-accent-grad` brands.css:39 | linear-gradient(90deg, #1fbf73, #7ff0bf) | `--brand-accent-grad` |
| `--brand-accent-hairline` brands.css:40 | rgba(31,191,115,.32) | `--brand-accent-hairline` |
| `--brand-on-accent` brands.css:41 | #04140c | `--brand-on-accent` |
| `--brand-cta` brands.css:42 | #2f6bff | `--brand-cta` |
| `--brand-cta-grad` brands.css:43 | linear-gradient(90deg, #3b7bff, #2f6bff) | `--brand-cta-grad` |
| `--brand-cta-accent` brands.css:44 | #ff3d57 | `--brand-cta-accent` |
| `--brand-font-body` brands.css:49 | var(--font-be-vietnam), ... | `--brand-font-body` |
| `--brand-font-num` brands.css:50 | var(--font-be-vietnam), ... | `--brand-font-num` |
| `--brand-font-head` brands.css:51 | var(--font-montserrat), ... | `--brand-font-head` (D-DS8: emerald keeps Montserrat, so the `--font-montserrat` loader var stays) |
| `--brand-logo` brands.css:52 | url(/assets/brand/emerald-logo.svg) | `--brand-logo` |

`[data-theme="obsidian"]` (themes.css:19, today a no-op because obsidian equals `:root`). Once Wine-Gold is `:root`, obsidian carries the old ladder on the new names: `--surface-canvas` #0a0a0a, `--surface-shell` #050505, `--surface-base` #141414, `--surface-raised` #1a1a1a, `--surface-overlay` #212121, `--surface-tile` #171717, `--state-hover` #262626, `--surface-disabled` #303030, `--surface-scrim` rgba(0,0,0,.7), `--fg-primary` #f2f0e4, `--fg-secondary` #d6d3c7, `--fg-muted` #888888, `--fg-faint` #6f6f6f, `--line-subtle` rgba(212,175,55,.55), `--state-tint` rgba(242,240,228,.05), `--surface-header` #0a0a0a. D-DS8: obsidian also keeps its old win/loss/error/focus values: `--money-positive` #45c9a5, `--money-negative` #f53f55, `--status-danger-fg` #e42946, `--state-focus-ring` #6ea8ff. These are PINNED today (lint A3), so themes.css needs a named obsidian exception. Measured: that legacy pair is L 0.458 vs 0.236, 48.4% apart, outside rule 4.1. It is kept by owner decision and recorded here.

VIP page palette (tokens.css:307-345), values unchanged, re-keyed so it cannot be confused with the DS component `--vip-bg|header-bg|text|meta|title|fill|frame|track`:

| Current | New key | Current | New key |
|---|---|---|---|
| `--vip-page-bg` :307 | `--vip-pal-page-bg` | `--vip-gold-tint` :323 | `--vip-pal-gold-tint` |
| `--vip-panel-bg` :308 | `--vip-pal-panel-bg` | `--vip-positive` :326 | `--vip-pal-positive` |
| `--vip-panel-alt` :309 | `--vip-pal-panel-alt` | `--vip-negative` :327 | `--vip-pal-negative` |
| `--vip-inner-bg` :310 | `--vip-pal-inner-bg` | `--vip-hairline` :328 | `--vip-pal-hairline` |
| `--vip-text-primary` :311 | `--vip-pal-fg-primary` | `--vip-tier-bronze-grad` :331 | `--tier-bronze-grad` |
| `--vip-text-secondary` :312 | `--vip-pal-fg-secondary` | `--vip-tier-bronze-acc` :332 | `--tier-bronze-accent` |
| `--vip-text-muted` :313 | `--vip-pal-fg-muted` | `--vip-tier-silver-grad` :333 | `--tier-silver-grad` |
| `--vip-text-faint` :314 | `--vip-pal-fg-faint` | `--vip-tier-silver-acc` :334 | `--tier-silver-accent` |
| `--vip-text-disabled` :315 | `--vip-pal-fg-disabled` | `--vip-tier-gold-grad` :335 | `--tier-gold-grad` |
| `--vip-gold-start` :318 | `--vip-pal-gold-start` | `--vip-tier-gold-acc` :336 | `--tier-gold-accent` |
| `--vip-gold-mid` :319 | `--vip-pal-gold-mid` | `--vip-tier-platinum-grad` :337 | `--tier-platinum-grad` |
| `--vip-gold-end` :320 | `--vip-pal-gold-end` | `--vip-tier-platinum-acc` :338 | `--tier-platinum-accent` |
| `--vip-gold-ink` :321 | `--vip-pal-gold-ink` | `--vip-tier-diamond-grad` :339 | `--tier-diamond-grad` |
| `--vip-gold-grad` :322 | `--vip-pal-gold-grad` | `--vip-tier-diamond-acc` :340 | `--tier-diamond-accent` |

VIP radii are in §6; `--brand-font-display` is in §4.

## 4. Type

| Current token | Now | Maps to | New | Note |
|---|---|---|---|---|
| `--t-micro` :75 | 12px | OV role caption | 12px | |
| `--t-sm` :76 | 14px | OV role body-sm | 14px | |
| `--t-body` :77 | 16px | OV role body | 16px | |
| `--t-h3` :78 | 18px | OV role h4 | 19-22px | |
| `--t-h2` :79 | 20px | OV role h3 | 22-28px | |
| `--t-h1` :80 | 24px | OV role h2 | 26-36px | |
| `--t-display` :81 | 32px | OV role h1 | 30-44px | |
| `--t-hero` :82 | 40px | OV role display | 36-56px | |
| `--t-num` :83 | 16px | OV role num-sm | 16px | |
| `--t-num-lg` :84 | 32px | OV role num-lg | 28-36px | |
| `--t-balance` :208 | 28px | OV role num-lg | 28-36px | |
| `--lh-body` :85 | 1.5 | DS leading.body | 1.6 | |
| `--lh-tight` :86 | 1.3 | DS leading.heading | 1.3 | |
| `--weight-reg` :87 | 400 | DS weight.regular | 400 | |
| `--weight-semi` :88 | 600 | DS weight.semibold | 600 | |
| `--weight-bold` :89 | 700 | OV type.weight.strong | 600 | 128 call sites; D-DS3 loads no 700 |
| `--font-body` :273 | Be Vietnam | DS family.body | Be Vietnam Pro | |
| `--font-num` :274 | Be Vietnam | DS family.numeric | Inter | new face |
| `--font-head` :276 | Montserrat | DS family.display (display, h1, h2 only) | Playfair Display | h3, h4, labels use family.body |
| `--brand-font-body` :290 | font-body | `--type-family-body` | Be Vietnam Pro | |
| `--brand-font-num` :291 | font-num | `--type-family-numeric` | Inter | |
| `--brand-font-head` :292 | font-head | `--type-family-display` | Playfair Display | |
| `--brand-font-display` :362 | font-head | `--type-family-display` | Playfair Display | /vip headings |
| `letter-spacing` typography.css:47 | -0.02em | keep (no DS equivalent) | 0 | D-DS8; TOKENS.md 3.6: never negative on VN text |
| `font-weight` typography.css:60 | 800 | OV type.weight.strong | 600 | `.u-label` |
| `letter-spacing` typography.css:62 | 0.06em | keep (no DS equivalent) | 0.06em | uppercase labels |
| `font-feature` typography.css:70 | tabular-nums | DS type.feature.tabular | 'tnum' 1 | |

Role ramp (overlay `semantic.type.role.*`):

| Role | Family | Size | Leading | Weight |
|---|---|---|---|---|
| display | Playfair Display | 36-56px | 1.3 | 600 |
| h1 | Playfair Display | 30-44px | 1.3 | 600 |
| h2 | Playfair Display | 26-36px | 1.3 | 600 |
| h3 | Be Vietnam Pro | 22-28px | 1.3 | 600 |
| h4 | Be Vietnam Pro | 19-22px | 1.3 | 600 |
| body-lg | Be Vietnam Pro | 18-19px | 1.6 | 400 |
| body | Be Vietnam Pro | 16px | 1.6 | 400 |
| body-sm | Be Vietnam Pro | 14px | 1.6 | 400 |
| caption | Be Vietnam Pro | 12px | 1.4 | 500 |
| num-lg | Inter, tabular | 28-36px | 1.25 | 600 |
| num-md | Inter, tabular | 20-24px | 1.25 | 600 |
| num-sm | Inter, tabular | 16px | 1.4 | 500 |

Vietnamese headroom rule: no leading under 1.3 on text >= 20px, except single-line numerals (num-lg, num-md). That is why display uses 1.3, not the DS `leading.display` 1.25. Playfair stops at h2 (26px at 375) so stacked marks never render in the thin serif below that size (defect 13). `leading.truncate` (1.65) is not used by any role.

Loader note: the DS family strings name `'Be Vietnam Pro'` literally, but next/font injects generated family names (brands.css:45-48), so the real family goes first and the loader var, with its size-adjusted fallback, follows. Declare `--wg-type-family-body: 'Be Vietnam Pro', var(--font-be-vietnam), 'Noto Sans', 'Noto Sans Vietnamese', system-ui, ...` and add `--font-playfair` and `--font-inter` loader vars, `vietnamese` subset, weights 400/500/600 (D-DS3).

## 5. Spacing and layout

| Current token | Now | Maps to | New | Note |
|---|---|---|---|---|
| `--space-1` :92 | 4px | OV spacing.space.1 | 4px | |
| `--space-2` :93 | 8px | OV spacing.space.2 | 8px | |
| `--space-3` :94 | 12px | OV spacing.space.3 | 12px | |
| `--space-4` :95 | 16px | OV spacing.space.4 | 16px | |
| `--space-5` :96 | 24px | OV spacing.space.5 | 24px | 76 uses; TOKENS.md says 20, repo is 24 |
| `--space-6` :97 | 32px | OV spacing.space.6 | 32px | |
| `--space-7` :98 | 40px | OV spacing.space.6 | 32px | off the DS scale; 3 call sites: ui.css x2 (incl. :580), shell.css:1180 |
| `--space-8` :99 | 48px | OV spacing.space.8 | 48px | |
| `--gutter` :100 | 16px | OV spacing.gutter | 16px | |
| `--field-rhythm` :101 | 24px | OV spacing.field | 24px | |
| `--band-gap` :142 | 16px | OV spacing.band | 16px | owner may take 32 |
| `--gap` :143 | 16px | OV spacing.gap.md | 16px | |
| `--gap-sm` :144 | 8px | OV spacing.gap.sm | 8px | |
| `--gap-xs` :145 | 4px | OV spacing.gap.xs | 4px | |
| `--card-pad` :150 | 24px | OV spacing.inset.md | 24px | |
| `--card-pad-sm` :151 | 16px | OV spacing.inset.sm | 16px | |
| `--banner-mb` :152 | 22px | OV spacing.space.5 | 24px | off grid |
| `--header-h` :132 | 72px | keep (no DS equivalent) | 72px | |
| `--nav-h` :133 | 48px | keep (no DS equivalent) | 48px | |
| `--logo-h` :134 | 44px | keep (no DS equivalent) | 44px | |
| `--rail-w` :136 | 304px | keep (no DS equivalent) | 304px | |
| `--frame-w` :137 | 1424px | keep (no DS equivalent) | 1424px | |
| `--frame-min` :138 | 1150px | keep (no DS equivalent) | 1150px | |
| `--bottombar-h` :139 | 56px | keep (no DS equivalent) | 56px | |
| `--feature-w` :146 | 418px | keep (no DS equivalent) | 418px | |
| `--tile-h` :147 | 205px | keep (no DS equivalent) | 205px | |
| `--provider-w` :148 | 128px | keep (no DS equivalent) | 128px | |
| `--provider-h` :149 | 48px | keep (no DS equivalent) | 48px | |

The repo has no 20px spacing token; the only off-scale steps are 40px (`--space-7`, 3 call sites) and 22px (`--banner-mb`, 1 use), both above. DS `spacing.frame.gap` (3px) is not mapped: no Yaobet consumer.

## 6. Radius

| Current token | Now | Maps to | New | Uses that change |
|---|---|---|---|---|
| `--radius-sm` :104 | 4px | OV radius.control | 4px | none |
| `--radius-md` :105 | 8px | OV radius.surface | 8px | none |
| `--radius-lg` :106 | 12px | OV radius.surface | 8px | ui.css 1, promo 1, home 1, collection 1, shell 3, tsx `rounded-lg` 16 |
| `--radius-card` :107 | 16px | OV radius.surface | 8px | ui.css 7, shell 4, home 2, vertical 1, Card/Modal/Sheet.tsx 3, tsx `rounded-card` 21 |
| `--radius-pill` :108 | 9999px | OV radius.pill | 999px | none visible |
| `--vip-radius-table` :343 | 14px | OV radius.surface | 8px | tsx `rounded-vip-radius-table` 2 |
| `--vip-radius-control` :344 | 12px | OV radius.control | 4px | tsx `rounded-vip-radius-control` 4 |
| `--vip-radius-gem` :345 | 8px | OV radius.surface | 8px | tsx `rounded-vip-radius-gem` 4 |

Rule: controls (button, input, chip, tag) take 4px; anything that holds content (card, sheet, modal, tile, table) takes 8px. Sheets keep square bottom corners at the screen edge. Defect 12 visual change accepted: 12/16px -> 8px (D-DS8).

## 7. Elevation

| Current token | Now | Maps to | New | Note |
|---|---|---|---|---|
| `--lift` :118 | none | DS elevation.level.1.shadow -> `--elevation-1-shadow` | 0 1px 2px rgba(12,10,8,.45) | cards; surface OV level.1.surface |
| `--shadow-2` :122 | none | DS elevation.level.2.shadow -> `--elevation-2-shadow` | 0 4px 12px rgba(12,10,8,.5) | menus, QuickActionRail |
| `--halo` :117 | none | DS elevation.level.3.shadow -> `--elevation-3-shadow` | 0 12px 32px rgba(12,10,8,.6) | modal, toast, hero |
| `--glow-gold` :116 | none | retired: active state = `--line-strong` border | gold.300 line | DS has no glow |
| `--progress-dot-glow` :223 | none | retired | none | |

Shadows return (the flat ban in tokens.css:110-115 ends). One shadow level per branch of the tree (L-01). Confirmed by D-DS8.

## 8. Motion

| Current token | Now | Maps to | New | Note |
|---|---|---|---|---|
| `--dur-fast` :158 | 200ms | OV motion.duration.fast | 150ms | hover, press, focus |
| `--dur-base` :159 | 200ms | OV motion.duration.base | 250ms | reveals, tabs, sheet enter |
| `--dur-slow` :160 | 300ms | OV motion.duration.slow | 400ms | page-level only |
| `--dur-header` :161 | 300ms | OV motion.duration.base | 250ms | header collapse |
| `--ease-standard` :162 | (.645,.045,.355,1) | OV motion.easing.standard | (0.2,0,0,1) | |
| `--ease-entrance` :163 | (.23,1,.32,1) | OV motion.easing.enter | (0,0,0,1) | |
| (none) | | OV motion.duration.exit / easing.exit | 150ms / (0.3,0,1,1) | exits 0.6x entrance |
| (none) | | OV motion.duration.instant / ambient | 80ms / 650ms | state swap / skeleton |
| motion.css:16-18 (reduced motion) | 0ms x3 | zero every `--motion-duration-*` | 0ms | ambient shimmer becomes static |

Transform and opacity only. motion.css:25-32 stays as is.

## 9. Z-index

| Current token | Now | Maps to | New |
|---|---|---|---|
| `--z-content` :125 | 1 | keep (no DS equivalent) | 1 |
| `--z-sticky` :126 | 100 | keep (no DS equivalent) | 100 |
| `--z-dropdown` :127 | 1000 | keep (no DS equivalent) | 1000 |
| `--z-modal` :128 | 2000 | keep (no DS equivalent) | 2000 |
| `--z-toast` :129 | 3000 | keep (no DS equivalent) | 3000 |

Local stacking literals (`z-index` 2 x4, 1 x2, -1 x2, 0 x1 in `src/`) stay local. The DS has no z primitive, so the overlay cannot add one (defect 10, not fixable with existing primitives).

## 10. Breakpoints, touch and icon sizes

Breakpoints are not tokenised today; they are literal media queries. Keep all (no DS equivalent).

| Width | CSS `@media` uses | tsx `min-[..]:` uses | Map |
|---|---|---|---|
| 420 / 480 / 560 | 1 / 1 / 1 | 0 / 10 / 2 | keep |
| 640 (and 639 max) | 3 min, 5 max, 2 max-639 | 11 | keep |
| 768 (and 767 max) | 14 min, 2 max-767 | 55 | keep; TOKENS.md `--breakpoint-md` |
| 880 / 900 | 0 / 1 min, 19 max | 1 / 6 | keep |
| 992 | 4 | 10 | keep |
| 1024 (and 1023 max) | 4 min, 2 max | 11 | keep; TOKENS.md `--breakpoint-lg` |
| 1240 / 1424 / 1600 | 1 / 5 / 2 | 0 | keep |

| Current token | Now | Maps to | New | Note |
|---|---|---|---|---|
| `--tap-min` :166 | 44px | DS spacing.touch.min -> `--touch-min` | 44px | 122 uses |
| `--tap-bar` :167 | 48px | DS spacing.control.height -> `--control-h` | 48px | bottom bar |
| (none) | | OV spacing.touch.gap -> `--touch-gap` | 8px | |
| (none) | | OV spacing.icon.sm -> `--icon-sm` | 16px | |
| (none) | | OV spacing.icon.lg -> `--icon-lg` | 24px | icon md 20px has no primitive |
| `--brand-logo` :293 | url(logo.svg) | keep (asset slot) | url(logo.svg) | |

## 11. Defects: status after this overlay

| # | Status | How |
|---|---|---|
| 1 | fixed | OV text.muted-raised (5.83 surface.3, 6.03 wine.panel) + modal/toast/tooltip.meta, input.helper |
| 2 | fixed | modal/toast/tooltip.border -> border.control, 3.08 |
| 3 | Resolved (D-DS5) | loss -> new OV primitive red.300 #F2968E: L 0.426 vs win 0.425, 0.2% (was 20.8%); 7.88 page, 7.17 s1, 6.47 s2, 5.68 s3; the check asserts <= 5% |
| 4 | fixed | 17 of 20 pruned tokens restored; left out: button.primary.bg.rest (DS action.primary.bg.rest covers it), slip.row.bg and text.on-feedback (no Yaobet consumer) |
| 5 | fixed | feedback.paused 5.66 on feedback.tint.paused |
| 6 | fixed | semantic spacing, type roles, radius, motion, elevation surfaces |
| 9 | fixed by rule | checkbox mark 7.97; knob on track 7.72 |
| 10 | Resolved (D-DS6, D-DS8) | weight.strong (600), touch.gap, icon sm/lg in the approved overlay; heading letter-spacing set to 0 (D-DS8); z-index and breakpoints stay Yaobet-owned structural tokens (§9, §10); icon md (20px) stays absent, no primitive |
| 12 | mapped | §6, visual change |
| 13 | partial | Playfair limited to >= 26px; FOUT handled by next/font, not tokens |
| 14 | mapped | §3 |

## 12. Resolved (D-DS5..8)

| # | Question | Decision | Applied in |
|---|---|---|---|
| 1 | Win/loss within 5% | D-DS5: one new loss primitive, red.300 #F2968E (0.2%) | overlay `primitive.color.red.300`, `feedback.loss`; §2, §11 |
| 2 | Approve the overlay | D-DS6: the 108 tokens approved; red.300 added under D-DS5 (109) | overlay |
| 3 | Header bar | D-DS7: `surface.wine.header` (wine.600) | §2 `--header-bg` |
| 4 | `.ui-btn-primary` | D-DS7: gold primary, label `--fg-on-accent` | §2 `--cta-grad`, `--brand-cta-grad` |
| 5 | Register CTA | D-DS7: gold primary; shell.css:1307 ink -> `--fg-on-accent` | §2 `--cta-accent`, `--brand-cta-accent` |
| 6 | Gradient stops | D-DS8: champagne -> ivory.100 via `color-mix`, no new literal | §2 composites |
| 7 | Emerald fonts | D-DS8: emerald keeps Montserrat | §3 |
| 8 | Obsidian money/status/focus | D-DS8: keeps its old win/loss/error/focus values | §3 |
| 9 | Heading letter-spacing | D-DS8: 0 | §4 |
| 10 | Radius 12/16 | D-DS8: becomes 8px | §6 |
| 11 | Shadows | D-DS8: return | §7 |
| 12 | Gold checkbox fill | D-DS8: allowed as a mark, named exception to rule 4.2 | §2 switch/checkbox note |

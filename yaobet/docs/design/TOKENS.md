# Yaobet design tokens — abstract contract v0.1

Status: proposed · Date: 2026-11-04 · Governed by `docs/design/ADR-001-design-direction.md` §2.1–2.3.
This file names every token. It fixes no brand value. `TBD (owner)` = only the owner may choose; `default` = structural value a builder may rely on and the owner may override. Source files: `src/styles/brand.yaobet.css` (primitives), `src/styles/tokens.css` (semantic), `src/styles/components.css` (component). SOT = `docs/biz/BUSINESS_CONTEXT_SOT.md`.

## 1. Layers and naming grammar

| Layer | Pattern | Example | Where declared | Who consumes |
|---|---|---|---|---|
| Primitive | `--raw-<family>-<step>` | `--raw-neutral-900`, `--raw-gold-500` | `brand.yaobet.css` `:root` | semantic layer only |
| Semantic | `--<category>-<role>[-<variant>][-<state>]` | `--color-surface-raised`, `--motion-duration-fast` | `tokens.css` | components (utilities) |
| Component | `--<component>-<property>[-<state>]` | `--button-bg-hover`, `--money-fg-stale` | `components.css` | that component only |

Rules: lowercase kebab-case; role before variant before state; no numbers in semantic colour names (numbers belong to primitives); a component token always resolves to a semantic token, never to a primitive or a literal.

## 2. Tailwind v4 `@theme` mapping rule

1. Semantic tokens whose category is a Tailwind namespace are declared inside `@theme { … }` (not `@theme inline`): `--color-*` → `bg-*`, `text-*`, `border-*`, `ring-*`; `--font-*` → `font-*`; `--text-*` → `text-*` (size); `--font-weight-*`; `--leading-*`; `--radius-*` → `rounded-*`; `--shadow-*`; `--ease-*`; `--breakpoint-*`; `--animate-*`.
2. Tailwind defaults are disabled at the top of the block: `--color-*: initial; --breakpoint-*: initial; --shadow-*: initial; --radius-*: initial; --font-*: initial;` so only named tokens generate utilities.
3. Tokens with no Tailwind namespace (`--space-*` aliases, `--z-*`, `--motion-duration-*`, `--size-*`, `--state-*`, `--ring-*`) are declared in `:root` and consumed with the variable shorthand: `z-(--z-overlay)`, `duration-(--motion-duration-fast)`, `min-h-(--size-touch-min)`.
4. `--spacing` keeps the structural default `0.25rem`, so Tailwind numeric utilities (`p-4` = 16 px) equal `--space-4`; builders use only the steps listed in §3.5.
5. Colour roles are named so the utility prefix is not doubled: `surface` for fills (`bg-surface-canvas`, `bg-surface-raised`), `fg` for text (`text-fg-primary`), `line` for borders (`border-line-subtle`); `accent`, `money`, `status`, `state` keep their names (`text-money-positive`, `ring-state-focus-ring`). Never introduce a `bg`, `text` or `border` role (ADR-001 §4).

## 3. Token groups

### 3.1 Colour — background and surface (`TBD (owner)` unless noted)

`--color-surface-canvas` page background · `--color-surface-base` default panel · `--color-surface-raised` one step up (ADR-001 §3.5: hierarchy comes from steps, not nested cards) · `--color-surface-sunken` inputs, wells · `--color-surface-overlay` sheets, menus · `--color-surface-inverse` · `--color-surface-scrim` modal backdrop (alpha) · `--color-surface-accent` filled accent areas · `--color-surface-gold` scarce highlight fill.

### 3.2 Colour — text, border, accent

| Token | Role | Value |
|---|---|---|
| `--color-fg-primary` / `-secondary` / `-muted` | 3-step text hierarchy, AA on canvas and surface | TBD (owner) |
| `--color-fg-inverse`, `--color-fg-on-accent`, `--color-fg-on-gold` | text on inverse/accent/gold fills | TBD (owner) |
| `--color-fg-link` | links, no underline removal without colour + weight | TBD (owner) |
| `--color-line-subtle` / `-default` / `-strong` | dividers → inputs → emphasis | TBD (owner) |
| `--color-accent-primary` / `-hover` / `-press` | the one call-to-action colour | TBD (owner) |
| `--color-accent-secondary` | secondary actions, selected tabs | TBD (owner) |
| `--color-accent-gold` / `--color-accent-gold-muted` | gold accent family per rule §4.2 (text, lines, marks, focus); fills only the primary button and VIP hero | BRAND.md §1 (`gold-300` / `gold-500`) |

### 3.3 Colour — money (SOT §2 line 39; §6 rule 12)

| Token | Use | Value |
|---|---|---|
| `--color-money-positive` | wins, credits, cashback paid | TBD (owner); luminance-matched to negative (rule §4.1) |
| `--color-money-negative` | losses, debits, fees | TBD (owner); luminance-matched to positive |
| `--color-money-neutral` | balances, pending, amounts without direction | TBD (owner); usually `--color-fg-primary` |
| `--color-money-stale` | "tạm dừng" value shown when data is stale | TBD (owner); must read as muted, never as loss |

### 3.4 Colour — status and state

Status pairs, each with `-fg` and `-bg`: `--color-status-info-*`, `--color-status-success-*`, `--color-status-warning-*`, `--color-status-danger-*`, `--color-status-paused-*` (the "tạm dừng" state, distinct from danger). Withdrawal status model (SOT §2 line 32) maps requested → info, checking → warning, paid → success, needs action → danger.
State tokens: `--color-state-skeleton-base`, `--color-state-skeleton-highlight`, `--color-state-disabled-fg`, `--color-state-disabled-bg`, `--color-state-focus-ring`, `--color-state-hover-overlay` (alpha), `--color-state-press-overlay` (alpha), `--color-state-selected-bg`. All `TBD (owner)`.

### 3.5 Spacing (default: 4 px base, owner may retune the base only)

`--space-0` 0 · `--space-1` 4 · `--space-2` 8 · `--space-3` 12 · `--space-4` 16 · `--space-5` 20 · `--space-6` 24 · `--space-8` 32 · `--space-10` 40 · `--space-12` 48 · `--space-16` 64 · `--space-20` 80.
Layout aliases: `--space-page-x` page gutter (default `--space-4` at 375, `--space-8` ≥ 1024) · `--space-section` vertical rhythm between sections (default `--space-8`, `--space-12` ≥ 1024) · `--space-stack` default gap inside a surface (default `--space-3`) · `--size-container` max content width at 1440 (default 1280 px; owner may override).

### 3.6 Typography

| Token | Value |
|---|---|
| `--font-sans` body; must be loaded with the `vietnamese` subset via `next/font` | TBD (owner) |
| `--font-display` headlines and hero; same subset rule | TBD (owner); may equal `--font-sans` |
| `--font-weight-regular` 400 · `-medium` 500 · `-semibold` 600 · `-bold` 700 | default; drop weights the chosen font does not ship |
| `--text-xs` 12 · `-sm` 14 · `-base` 16 · `-lg` 18 · `-xl` 20 · `-2xl` 24 · `-3xl` 30 · `-4xl` 36 · `-display` 44 (px) | default modular scale; owner may replace |
| `--leading-tight` 1.25 · `-snug` 1.4 · `-normal` 1.55 · `-loose` 1.7 | default |
| `--tracking-display` | TBD (owner); never negative on Vietnamese text |

Vietnamese diacritics note: stacked marks (ấ, ệ, ỡ, ữ) extend above the cap height and below the baseline. Minimum `--leading-snug` on any text ≥ `--text-xl`; `--leading-tight` only for single-line numerals; no `leading-none`; uppercase display text keeps diacritics (no `text-transform` that strips them). Money numerals use `font-variant-numeric: tabular-nums` (`--money-numeric` component token).

### 3.7 Radius and elevation

Radius: `--radius-none` 0 · `--radius-sm` · `--radius-md` · `--radius-lg` · `--radius-xl` · `--radius-full` 9999px. Values `TBD (owner)` except none and full; the scale order is fixed.
Elevation (dark-first: surface steps carry depth; shadows are optional): `--shadow-raised` · `--shadow-overlay` · `--shadow-glow-accent` (hero and CTA only) · `--shadow-glow-gold` (VIP hero only, rule §4.2). All `TBD (owner)`; a value of `none` is valid.

### 3.8 Z-index ladder (default, structural)

`--z-base` 0 · `--z-raised` 10 · `--z-sticky` 100 (section headers) · `--z-nav` 200 (bottom nav, side nav, top bar) · `--z-overlay` 300 (sheets, menus) · `--z-modal` 400 · `--z-toast` 500 · `--z-tooltip` 600. No other z values may appear in `src/`.

### 3.9 Motion

| Token | Default | Note |
|---|---|---|
| `--motion-duration-instant` | 0 ms | state swaps |
| `--motion-duration-fast` | 120 ms | hover, press, focus |
| `--motion-duration-base` | 200 ms | reveal, tab change, sheet |
| `--motion-duration-slow` | 320 ms | page-level transitions |
| `--motion-duration-celebrate` | TBD (owner) | only on the `money-landed` event (ADR-001 §2.7) |
| `--motion-duration-hero` | TBD (owner) | the single autonomous home animation |
| `--ease-standard` / `--ease-enter` / `--ease-exit` / `--ease-emphasis` | default cubic-beziers (standard `0.2,0,0,1`; enter `0,0,0.2,1`; exit `0.4,0,1,1`; emphasis `0.3,0,0,1`) | owner may retune |
| `--animate-skeleton` | default 1.4 s linear shimmer | becomes static under reduced motion |

Reduced-motion rule (structural, binding): under `@media (prefers-reduced-motion: reduce)` every `--motion-duration-*` becomes 0 ms except opacity-only fades, which are capped at `--motion-duration-fast`; `--animate-skeleton` is replaced by a static two-tone block; the hero animation shows its final frame.

### 3.10 Breakpoints (default, structural; 375 is the base, not a breakpoint)

`--breakpoint-md` 768 px · `--breakpoint-lg` 1024 px · `--breakpoint-xl` 1440 px. Tailwind defaults are reset; `sm` does not exist. Every surface is specified at 375 and 1440 first (ADR-001 §2.8).

### 3.11 Touch targets and hit areas (default, structural)

`--size-touch-min` 44 px · `--size-touch-comfortable` 48 px · `--size-hit-gap` 8 px minimum between adjacent targets · `--size-icon-sm` 16 · `--size-icon-md` 20 · `--size-icon-lg` 24 · `--size-thumb-tile` lobby tile min width at 375 (TBD (owner), default 104 px).

### 3.12 Interaction state tokens

`--state-hover-overlay` → `--color-state-hover-overlay` · `--state-press-overlay` → `--color-state-press-overlay` · `--state-press-scale` default 0.98 · `--state-disabled-opacity` default 0.5 · `--ring-focus-width` default 2 px · `--ring-focus-offset` default 2 px · `--ring-focus-color` → `--color-state-focus-ring` · `--state-loading-min-duration` default 300 ms (skeleton shows at least this long to avoid flicker).

### 3.13 Component tokens (phase 1 set; each resolves to a semantic token)

`--button-*` (bg, fg, border × primary/secondary/ghost × rest/hover/press/disabled) · `--surface-*` (bg, border, radius × base/raised/sunken/overlay) · `--money-*` (fg × positive/negative/neutral/stale, `--money-numeric`) · `--skeleton-*` (base, highlight, radius) · `--state-block-*` (bg, fg, icon × error/paused/empty). New component tokens require an ADR amendment, not a builder decision.

## 4. Rules

1. **Luminance-matched money.** `--color-money-positive` and `--color-money-negative` must have equal relative luminance (within 5%) so a loss is never visually quieter than a win; direction is also carried by sign and label, never colour alone.
2. **Gold is the accent, never the surface** (owner direction 2026-11-04, `docs/design/BRAND.md` §4, supersedes "one gold element per viewport"). Gold goes on primary CTAs, key lines, hero and VIP headings, the active nav item, the current tier mark and focus rings; gold fills only the primary button and the VIP hero; money is never gold.
3. **Skeleton, error and "tạm dừng" are tokens.** Loading uses `--skeleton-*`; error and paused use `--state-block-*` with `--color-status-danger-*` / `--color-status-paused-*`; no ad-hoc greys, spinners or inline text colours.
4. **No builder chooses a value.** Any token marked `TBD (owner)` ships as a neutral placeholder generated by the PM (a greyscale ramp) until the owner fills it; a builder who needs a token that does not exist stops and reports `Fail: TOKENS.md | Expected: <token> | Got: none` rather than inventing one.
5. **No literals in components.** No hex, rgb, px font sizes, raw z-index or raw durations in `.tsx`; gate: `rg -n "#[0-9a-fA-F]{3,8}|z-\[|duration-\[" src/components src/app` returns nothing.
6. **Anti-slop mapping.** L-01 nested cards → only one `--surface-*` level per branch of the tree; L-13 card soup → sections use `--space-section`, not surfaces, to separate content; D-09 badges → one status pair per element; L-16 clipping → money and Vietnamese labels never `truncate`; T-12 icons → `--size-icon-*` only next to a label or inside a ≥ 44 px target; W-07 category → one device per category (label + tile).

## 5. How a builder uses this

1. Import nothing from `src/styles/` in a component; use utilities: `bg-surface-raised text-fg-primary border-line-subtle rounded-md p-4 gap-(--space-stack)`.
2. For money: `<Money value={n} direction="positive|negative|neutral" state="ready|loading|error|stale" />` from `src/components/ui/money.tsx`; never style amounts directly.
3. For states: render the fixture variant (`ready|loading|error|stale`) through `Skeleton` and `StateBlock`; never hand-write a loading or error look.
4. Need a value not listed here: stop, report the missing token name, continue with the next task. Do not add a primitive.
5. Verification before return: `npm run lint && npx tsc --noEmit && npm run build` plus the rule §4.5 `rg` gate, fresh exit codes in the receipt.

## 6. How the owner fills values

1. Edit only `src/styles/brand.yaobet.css`: set each `--raw-*` primitive, then point each `TBD (owner)` semantic token in `tokens.css` at a primitive (fonts, radii, elevation, celebrate/hero durations, gold).
2. Check: text 4.5:1 and UI 3:1 contrast against canvas, surface and raised; money positive/negative luminance within 5% (rule §4.1); `vietnamese` subset present for both fonts.
3. Run the app at 375 and 1440 on the home and lobby; judge first-sight pull (SOT §2 line 37). Mark this file `accepted` with the date; the PM records the fill as an ADR-001 amendment.
4. A sibling brand later copies `brand.yaobet.css` to `brand.<name>.css` and scopes it under `[data-brand="<name>"]`; nothing under `src/components/` changes.

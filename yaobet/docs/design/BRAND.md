# Yaobet brand values v0.2 (owner palette, 2026-11-04)

Fills the `TBD (owner)` primitives in `docs/design/TOKENS.md`. Six values are the owner's `[OWNER 2026-11-04]`; every derived value is a pm default `[DEFAULT]` the owner may retune in `src/styles/brand.yaobet.css` without touching components. Direction stated by the owner: a golden dark theme that feels luxury.

## 1. Owner palette (binding)

| Primitive | Hex | Role proposal |
|---|---|---|
| `--raw-gold-700` | `#654922` | deep gold: press state, gold line on dark |
| `--raw-gold-500` | `#956E2F` | mid gold: hover, muted gold text, strong lines |
| `--raw-gold-300` | `#B68B4B` | bright gold: primary CTA fill, gold accent text, VIP marks |
| `--raw-neutral-600` | `#4D574E` | sage grey: raised surfaces, default lines, secondary accent |
| `--raw-neutral-800` | `#303531` | surface |
| `--raw-neutral-900` | `#202221` | canvas |

## 2. Derived primitives (pm defaults, owner may retune)

| Primitive | Hex | Note |
|---|---|---|
| `--raw-neutral-950` | `#191A19` | sunken wells, darker than canvas |
| `--raw-neutral-700` | `#3A3F3B` | subtle lines |
| `--raw-cream-100` | `#F3EDE2` | primary text, warm off-white (AA on canvas 12.6:1, on surface 10.9:1) |
| `--raw-cream-300` | `#CFC7B8` | secondary text |
| `--raw-cream-500` | `#ADA79B` | muted text, stale money (5.2:1 on surface, 7.3:1 on sunken; only 3.2:1 on raised, so muted text never sits on a raised surface) |
| `--raw-gold-200` | `#CBA366` | primary-button hover fill (6.8:1 with canvas-coloured text) |
| `--raw-green-400` | `#7FB58A` | money positive, success (WCAG relative luminance 0.394; 6.8:1 on canvas) |
| `--raw-rose-400` | `#D89898` | money negative (relative luminance 0.393, 0.2% from green; 6.8:1 on canvas). Rule: `abs(L_pos − L_neg) / max(L_pos, L_neg) <= 0.05`, verified by leaf 1.1.1 G6 |
| `--raw-rose-500` | `#E39591` | danger (5.3:1 on surface) |
| `--raw-amber-400` | `#E0B35C` | warning (distinct from gold by saturation and use; never on CTAs) |
| `--raw-blue-400` | `#8FAACB` | info (withdrawal "requested") |

## 3. Semantic mapping (what `tokens.css` points at)

- Surfaces: canvas `neutral-900`, surface `neutral-800`, raised `neutral-600` at 100% for cards that must stand out and `neutral-700` for quiet raised panels (builder picks `raised` only; the two steps are `--color-surface-raised` and `--color-surface-raised-quiet`), sunken `neutral-950`, overlay `neutral-800` + `--shadow-overlay`, inverse `cream-100`, scrim `rgb(0 0 0 / 0.6)`, `surface-accent` `gold-300` (the primary-button fill only), `surface-gold` `gold-300` (the VIP hero fill only).
- Text: primary `cream-100`, secondary `cream-300`, muted `cream-500`, inverse `neutral-900`, on-accent `neutral-900`, on-gold `neutral-900`, link `gold-300`.
- Lines: subtle `neutral-700`, default `neutral-600`, strong `gold-500`.
- Accent: primary `gold-300`, hover `gold-200` (lighter, keeps canvas text at 6.8:1), press `gold-500` (transient); secondary `neutral-600`; gold `gold-300`, gold-muted `gold-500`.
- Money: positive `green-400`, negative `rose-400`, neutral `cream-100`, stale `cream-500`.
- Status fg/bg pairs: info `blue-400` on `neutral-800`; success `green-400`; warning `amber-400`; danger `rose-500`; paused `cream-300` on `neutral-700` (6.4:1; the "Đang cập nhật" pill is the most frequent small text in phase 1).
- State: skeleton base `neutral-800`, highlight `neutral-700`; disabled fg `cream-500` at 0.5; focus ring `cream-100` (>= 6.4:1 on every surface; on the gold primary button it reads through the 2 px offset gap); hover overlay `rgb(255 255 255 / 0.06)`; press overlay `rgb(0 0 0 / 0.18)`; selected bg `neutral-700`.
- Elevation: `--shadow-raised` `0 1px 0 rgb(255 255 255 / 0.04), 0 8px 24px rgb(0 0 0 / 0.35)`; `--shadow-overlay` `0 16px 48px rgb(0 0 0 / 0.5)`; `--shadow-glow-accent` `0 0 0 1px #956E2F, 0 8px 32px rgb(182 139 75 / 0.25)`; `--shadow-glow-gold` same as glow-accent (VIP hero only).
- Radius (pm default): sm 6, md 10, lg 16, xl 24 px. Fonts: unchanged placeholder Geist with the `vietnamese` subset until the owner names a display face; a serif or high-contrast display for `--font-display` is recommended for the luxury register `[OWNER DATA]`.

## 4. Gold usage rule (owner direction, pm interpretation, recorded per SOT rule 10)

The v1.0 rule "gold is scarce, one element per viewport" was written for the previous trust-first restraint brief. The owner's golden-luxury direction reopens it. In force now:
- Gold is the accent family: primary CTAs, key lines, hero and VIP headings, the active nav item, the current VIP tier mark, focus rings.
- Gold is never a surface fill except the VIP hero and the primary button; large gold areas read as cheap, thin gold on deep neutrals reads as luxury.
- Still binding: money colours are never gold (positive green, negative rose, luminance-matched); win and loss are equally loud; celebration only on `money-landed`; no fabricated activity.
- Thin gold strokes up to 8 px (progress-bar fill, underlines, dividers) count as lines, not fills.
- Contrast rule for every default: text pairs >= 4.5:1 and UI pairs >= 3:1 on the surface they are designed for; the QC pass of 2026-11-04 set the values above.

## 5. Assets supplied by the owner

Owner-supplied images live under `public/assets/` and are referenced as `/assets/...`. Logo: `/assets/images/logo.png` (use first; a wordmark fallback stays in the shell). Inventory, dimensions and usage map: `docs/design/ASSETS.md`. Provider and game art in `public/assets/images/casino` and `sports` are third-party marks supplied by the owner; rights clearance is the owner's confirmation `[OWNER DATA]` and is logged in ASSETS.md, not assumed.

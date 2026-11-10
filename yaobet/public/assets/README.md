# `public/assets/` — the SLOT convention (SPEC-04 PART 5)

Every art reference in the app is a **SLOT**, never a hardcoded final image. A slot is a typed
entry in a `lib/mock` fixture (`{ id, imageSrc, alt, width, height }`-shaped) pointing at either:

1. a real licensed / Yaobet-supplied asset already placed under `public/assets/<category>/`, or
2. the generic token-derived placeholder under `public/assets/placeholders/`.

Swapping a placeholder for final art is a **one-line fixture edit** — no component changes.

## Folders (one per asset class, mirroring the feature folders)

| Folder | Holds | Default placeholder |
|---|---|---|
| `brand/` | Yaobet logo lockups (`logo.svg`) + alt-brand logos (`emerald-logo.svg`) | self (real slot art) |
| `tiers/` | per-VIP-tier badge/card art (1 per tier) | `placeholders/tier-badge.svg` |
| `perks/` | whale-club perk illustrations (~1 per perk) | `placeholders/perk.svg` |
| `medals/` | honor/medal art (families trimmed to 1–2) | `placeholders/medal.svg` |
| `games/` | game / brand thumbnails | `placeholders/tile.svg` |
| `promos/` | promo banner + card images | `placeholders/promo.svg` |
| `store/` | points-mall product images | `placeholders/product.svg` |
| `placeholders/` | the generic token-derived gradients used until real art lands | — |
| `fonts/` (future) | self-hosted ≤120KB VN subset of "Be Vietnam Pro" (woff2, 400/600/700) | — |

## Placeholder design

The placeholders are **token-derived**: a `--surface → --surface-3` gradient fill, a
`--gold-hairline` (rgba(244,183,64,.32)) border, and a gold (`--gold-500` #f4b740) label —
the same brand values as `tokens.css`. They are deliberately plain so a real asset reads as an
upgrade. (SVGs in `public/` cannot read CSS vars, so the brand hex is baked in to match the tokens.)

Aspect ratios match the J9 anatomy so layout is stable before real art arrives:
`tile` 240×160 · `tier-badge` 120×120 · `perk` 200×140 · `promo` 343×160 · `product` 240×240 ·
`medal` 120×120 · `poster` 300×400.

## Hard rule

**No J9 art, logos, or game art** enters `public/assets/`. Yaobet brand lockups go in `brand/`;
everything else is a placeholder until the user supplies licensed assets. Render with Next
`<Image>` (explicit width/height + lazy-load) so the asset-hungry galleries lazy-load.

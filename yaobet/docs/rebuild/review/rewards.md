# Review: track "rewards" (sections 04-01 … 04-40)

Reviewer: sa (read-only plus this one file). Date: 2026-11-05. Binding inputs: `docs/rebuild/DECISIONS.md` (D1-D4), `docs/rebuild/REVIEW-BRIEF.md`, `sections/00-0*`, `sections/05-01-v-checklist.html`.
Scope: VIP (`/vip`, `/tier`, `/cau-lac-bo`), points store (`/cua-hang`), scratch card (`/ve-so`), collection (`/bo-suu-tap`, `/bo-suu-tap/cua-toi`, `/dev/collection-ports`), and track R dead code.
Other reviews referenced by name: **foundations** (tokens incl. `--vip-*` luxury palette, themes, typography, motion.css, `src/lib/{format,i18n,rg,types,auth,mock}`, i.e. `lib/mock/vip.ts`, `lib/mock/store.ts`, `lib/mock/lottery.ts`), **ui-member** (the 17 `src/ui` primitives), **shell** (`components/layout/_internal/Overlay`, `usePrefersReducedMotion`, QuickActionRail).
Original source, read only to settle gaps: `/Users/maxime/Documents/Projects/Antigravity/Igaming-Agent-1/apps/web/src/**` (cited below as `orig:<path>:<line>`).

## 1. Coverage

| Section file | h3 | Read fully | Components / routes covered |
|---|---|---|---|
| 04-01-r-vip.html | 6 | yes | shared tokens, `--vip-*` palette, lib/vip, routes /vip, /tier, /cau-lac-bo |
| 04-02-r-vip-program.html | 0 | yes | VipProgram + language toggle |
| 04-03-r-vip-section-heading.html | 0 | yes | VipSectionHeading |
| 04-04-r-vip-hero-guest.html | 0 | yes | VipHeroGuest |
| 04-05-r-vip-hero-member.html | 0 | yes | VipHeroMember |
| 04-06-r-vip-level-ring.html | 0 | yes | LevelRing (SVG) |
| 04-07-r-vip-tier-deck.html | 0 | yes | TierDeck (coverflow) |
| 04-08-r-vip-privilege-comparison.html | 0 | yes | PrivilegeComparison |
| 04-09-r-vip-privilege-matrix.html | 0 | yes | PrivilegeMatrix (+ CheckIcon, LockIcon) |
| 04-10-r-vip-level-table.html | 0 | yes | LevelTable |
| 04-11-r-vip-faq.html | 0 | yes | VipFaq + FAQ_ITEMS |
| 04-12-r-vip-current-tier-card.html | 0 | yes | CurrentTierCard (+ ProgressBar) |
| 04-13-r-vip-tier-ladder.html | 0 | yes | TierLadder |
| 04-14-r-vip-privilege-table.html | 0 | yes | PrivilegeTable |
| 04-15-r-vip-perk-gallery.html | 0 | yes | PerkGallery |
| 04-16-r-vip-rules.html | 0 | yes | VipRules |
| 04-17-r-vip-section.html | 0 | yes | VipSection |
| 04-18-r-store.html | 2 | yes | route /cua-hang, lib/store/escalation, mock catalogue |
| 04-19-r-store-points-header.html | 0 | yes | PointsHeader |
| 04-20-r-store-product-grid.html | 0 | yes | ProductGrid + filter tabs |
| 04-21-r-store-product-card.html | 0 | yes | ProductCard |
| 04-22-r-store-redeem-dialog.html | 0 | yes | RedeemDialog (+ ItemHeader) |
| 04-23-r-store-terms.html | 0 | yes | StoreTerms |
| 04-24-r-lottery.html | 0 | yes | route /ve-so |
| 04-25-r-lottery-root.html | 0 | yes | LotteryRoot (+ ScratchTicketArt) |
| 04-26-r-lottery-engine.html | 0 | yes | outcome engine (lib/mock/lottery.ts, foundations-owned) |
| 04-27-r-lottery-scratch-card.html | 0 | yes | ScratchCardGame / ScratchCardStage / ScratchCardBody |
| 04-28-r-lottery-scratch-surface.html | 0 | yes | ScratchSurface (canvas) + coverArt |
| 04-29-r-lottery-outcome.html | 0 | yes | OutcomeFrame + useCountUp |
| 04-30-r-collection.html | 3 | yes | routes /bo-suu-tap, /bo-suu-tap/cua-toi, /dev/collection-ports |
| 04-31-r-collection-lib.html | 0 | yes | lib/collection (sets, cards, rates, draw + exchange machines) |
| 04-32-r-collection-app.html | 0 | yes | CollectionApp (+ Tile) |
| 04-33-r-collection-pack-stage.html | 0 | yes | PackStage (+ Stadium, Foil) |
| 04-34-r-collection-card-art.html | 0 | yes | CardArt + rarity styling |
| 04-35-r-collection-ceremony.html | 0 | yes | RewardCeremony |
| 04-36-r-collection-terms.html | 0 | yes | CollectionTerms |
| 04-37-r-collection-history.html | 0 | yes | CollectionHistory |
| 04-38-r-collection-my-cards.html | 0 | yes | MyCards (+ CardTile, EmptyHolding) |
| 04-39-r-collection-card-detail.html | 0 | yes | CardDetail |
| 04-40-r-unused.html | 2 | yes | dead code, discrepancy index |

Totals: 40 files, 13 h3, 31 amber callouts. Method: each file converted tag-stripped to text and read in slices of 250 lines or fewer; h3 and amber counts taken with `rg -c '<h3'` and `rg -c 'callout warn'` on the HTML.

## 2. Inventory

### 2.1 Routes (8)

| Route | Original page file | Anchor | Depends on |
|---|---|---|---|
| /vip | src/app/vip/page.tsx (server, returns `<VipProgram/>`, no metadata) | 04-01#r-vip-route-vip | VipProgram |
| /tier | src/app/tier/page.tsx (async; `Promise.all([getVipTiers(), getPerks(), getVipProgress()])`, no metadata) | 04-01#r-vip-route-tier | lib/mock/vip.ts (foundations), CurrentTierCard, VipSection, TierLadder, PrivilegeTable, PerkGallery, VipRules |
| /cau-lac-bo | src/app/cau-lac-bo/page.tsx, metadata "Câu lạc bộ đại lý — Yaobet" | 04-01#r-vip-route-club | none (stub text) |
| /cua-hang | src/app/cua-hang/page.tsx + cua-hang.module.css, metadata "Cửa hàng điểm — Yaobet" | 04-18#r-store | lib/mock/store.ts, PointsHeader, ProductGrid, StoreTerms |
| /ve-so | src/app/ve-so/page.tsx, metadata "Vé số — Yaobet" | 04-24#r-lottery | LotteryRoot |
| /bo-suu-tap | src/app/bo-suu-tap/page.tsx + CollectionRoot.tsx, metadata "Bộ sưu tập — Yaobet" | 04-30#r-collection-route-main | FixtureCollectionAdapters, CollectionApp |
| /bo-suu-tap/cua-toi (+ `?tab=lich-su`) | cua-toi/page.tsx (`<Suspense fallback={null}>`) + MyCardsRoot.tsx, metadata "Thẻ của tôi — Yaobet" | 04-30#r-collection-route-mine | MyCards |
| /dev/collection-ports | src/app/dev/collection-ports/page.tsx (client, no metadata) + page.module.css | 04-30#r-collection-route-dev | lib/collection adapters (default config) |

### 2.2 Components (36 top level, 10 inline)

| Component | Original source | Anchor | Depends on |
|---|---|---|---|
| VipProgram | components/vip/VipProgram.tsx | 04-02#r-vip-program | lib/vip, useRequireAuth (foundations auth), all /vip children |
| VipSectionHeading | components/vip/VipSectionHeading.tsx | 04-03#r-vip-section-heading | `--brand-font-display`, `--vip-gold-mid` |
| VipHeroGuest | components/vip/VipHeroGuest.tsx | 04-04#r-vip-hero-guest | copy bag |
| VipHeroMember | components/vip/VipHeroMember.tsx | 04-05#r-vip-hero-member | LevelRing, TIERS, CURRENT_USER |
| LevelRing | components/vip/LevelRing.tsx | 04-06#r-vip-level-ring | none |
| TierDeck | components/vip/TierDeck.tsx | 04-07#r-vip-tier-deck | TIERS, getVipCopy |
| PrivilegeComparison | components/vip/PrivilegeComparison.tsx | 04-08#r-vip-privilege-comparison | TIERS, PRIVILEGES |
| PrivilegeMatrix (+ CheckIcon, LockIcon) | components/vip/PrivilegeMatrix.tsx | 04-09#r-vip-privilege-matrix | TIERS, PRIVILEGES |
| LevelTable | components/vip/LevelTable.tsx | 04-10#r-vip-level-table | giftAt, rate, fmtGift/fmtRate/fmtCash |
| VipFaq | components/vip/VipFaq.tsx | 04-11#r-vip-faq | FAQ_ITEMS |
| CurrentTierCard (+ ProgressBar) | components/vip/CurrentTierCard.tsx | 04-12#r-vip-current-tier-card | ui: Card, Button, Badge, Skeleton, ErrorState, MoneyValue, Icon; useAuth; openAuthModal |
| TierLadder | components/vip/TierLadder.tsx | 04-13#r-vip-tier-ladder | ui: Scroller, Card, Badge, Icon |
| PrivilegeTable | components/vip/PrivilegeTable.tsx | 04-14#r-vip-privilege-table | ui: Scroller (freezeFirstColumn), Icon |
| PerkGallery | components/vip/PerkGallery.tsx | 04-15#r-vip-perk-gallery | ui: Card, Badge, Icon, EmptyState |
| VipRules | components/vip/VipRules.tsx | 04-16#r-vip-rules | ui: Card, Icon |
| VipSection | components/vip/VipSection.tsx | 04-17#r-vip-section | ui: Icon |
| PointsHeader | components/store/PointsHeader.tsx | 04-19#r-store-points-header | ui: Card, Button, Icon; useRequireAuth |
| ProductGrid | components/store/ProductGrid.tsx | 04-20#r-store-product-grid | ProductCard, RedeemDialog, ui: ErrorState, EmptyState, TileSkeleton, useGridCols, computeGridFill (orig:components/store/ProductGrid.tsx:26-28) |
| ProductCard | components/store/ProductCard.tsx | 04-21#r-store-product-card | escalation.resolveBranch/isCooldownRunning, ui: Card, Button, Countdown, Icon; formatVnd, formatCount |
| RedeemDialog (+ ItemHeader) | components/store/RedeemDialog.tsx | 04-22#r-store-redeem-dialog | escalation.pointsAtStep, ui: Modal (size sm), Button, Countdown, Icon |
| StoreTerms | components/store/StoreTerms.tsx | 04-23#r-store-terms | ui: Icon |
| LotteryRoot (+ ScratchTicketArt) | components/lottery/LotteryRoot.tsx | 04-25#r-lottery-root | ScratchCardStage, SCRATCH_ODDS |
| ScratchCardGame / ScratchCardStage / ScratchCardBody | components/lottery/ScratchCardGame.tsx | 04-27#r-lottery-scratch-card | shell Overlay, shell usePrefersReducedMotion (orig:components/lottery/ScratchCardGame.tsx:63), makeScratchCard, LADDER, ScratchSurface, OutcomeFrame, ui: Button, Icon |
| ScratchSurface (+ coverArt.ts) | components/lottery/_internal/ScratchSurface.tsx, coverArt.ts | 04-28#r-lottery-scratch-surface | `[data-token]` children; tokens `--brand-accent`, `--brand-accent-2`, `--canvas`, `--text-hi` read at runtime |
| OutcomeFrame | components/lottery/_internal/OutcomeFrame.tsx | 04-29#r-lottery-outcome | useCountUp, formatVnd, ui: Icon |
| CollectionApp (+ Tile) | components/collection/CollectionApp.tsx | 04-32#r-collection-app | PackStage, CardArt, RewardCeremony, CollectionTerms, CollectionHistory, shell Overlay, lib/collection |
| PackStage (+ Stadium, Foil) | components/collection/PackStage.tsx | 04-33#r-collection-pack-stage | CardArt, cardById, ui: Icon |
| CardArt | components/collection/CardArt.tsx | 04-34#r-collection-card-art | CLUB_ACCENT, DemoCard |
| RewardCeremony | components/collection/RewardCeremony.tsx | 04-35#r-collection-ceremony | shell Overlay, CardArt, formatVnd |
| CollectionTerms | components/collection/CollectionTerms.tsx | 04-36#r-collection-terms | DEMO_TIERS, DEMO_PITY_BACKSTOP, next/link |
| CollectionHistory | components/collection/CollectionHistory.tsx | 04-37#r-collection-history | ports (audit page), cardById, setById |
| MyCards (+ CardTile, EmptyHolding) | components/collection/MyCards.tsx | 04-38#r-collection-my-cards | ui: Tabs, CardArt, CollectionHistory, CardDetail, useSearchParams, router.replace |
| CardDetail | components/collection/CardDetail.tsx | 04-39#r-collection-card-detail | shell Overlay, CardArt, ratesBySet, formatPercent |
| CollectionRoot | app/bo-suu-tap/CollectionRoot.tsx | 04-30#r-collection-route-main | FixtureCollectionAdapters, ensureSeeded(3) |
| MyCardsRoot | app/bo-suu-tap/cua-toi/MyCardsRoot.tsx | 04-30#r-collection-route-mine | FixtureCollectionAdapters (never seeds) |
| CollectionPortsPage | app/dev/collection-ports/page.tsx | 04-30#r-collection-route-dev | FixtureCollectionAdapters default config |

### 2.3 Token groups

| Group | Source | Anchor | Owner / depends on |
|---|---|---|---|
| Shared resolved tokens (`--space-*`, `--t-*`, `--radius-*`, `--dur-*`, `--ease-*`, surfaces, text, `--win/--loss/--error/--caution/--info/--focus-ring`, brand fonts) | src/styles/tokens.css | 04-01#r-vip-shared-tokens | foundations |
| Luxury palette `--vip-*` (31 vars incl. 5 tier grad + 5 tier acc, 3 radii) and `--brand-font-display: var(--font-head)` | src/styles/tokens.css lines 294-362 | 04-01#r-vip-palette | foundations (consumed only inside `.vipPalette`) |
| Local custom props set by components | `--rail-pad`, `--i`, `--n`, `--k`, `--len`, `--accent` | 04-32, 04-33, 04-35, 04-27, 04-34 | this track |

### 2.4 Hooks and lib modules

| Module | Source | Anchor | Owner / depends on |
|---|---|---|---|
| lib/vip (tiers.ts, formulas.ts, copy.ts, types.ts, index.ts) | src/lib/vip/* | 04-01#r-vip-lib | this track (foundations explicitly excludes it: 01-09-f-lib, "Out of this track: src/lib/vip/* …") |
| components/vip/copy.ts (legacy /tier copy, 74 lines) | src/components/vip/copy.ts | 04-40#r-unused-dead | this track |
| lib/store/escalation.ts | src/lib/store/escalation.ts | 04-18#r-store-lib | this track |
| lib/collection (index, math, ports, types, adapters/{clock,fixtures,runtime,store}, fixtures/epl) | src/lib/collection/** | 04-31#r-collection-lib | this track (excluded by foundations) |
| useCountUp | components/lottery/_internal/useCountUp.ts | 04-29#r-lottery-outcome | none |
| usePrefersReducedMotion | components/layout/_internal/usePrefersReducedMotion | 04-27 | shell |
| useRequireAuth / useAuth / openAuthModal / promptAuth | src/lib/auth/* | 04-02, 04-12, 04-20 | foundations |
| useGridCols / computeGridFill / TileSkeleton | `@/ui` (orig:components/store/ProductGrid.tsx:26-28) | 04-20 | ui-member |

### 2.5 Mock datasets

| Dataset | Source | Anchor | Owner |
|---|---|---|---|
| TIERS, PRIVILEGES, CURRENT_USER, FAQ_ITEMS, copy bag VI/EN | src/lib/vip/* | 04-01#r-vip-lib, 04-11 | this track |
| Legacy VIP ladder, perks, progress envelope (TIERED_USER.vipLevel 3) | src/lib/mock/vip.ts | 04-13, 04-15, 04-12 | foundations |
| Store catalogue (11 products), balance 3,250, DEMO_* switches | src/lib/mock/store.ts | 04-18#r-store-data | foundations |
| Scratch engine: LADDER, SCRATCH_ODDS, makeScratchCard, DUST_STEPS | src/lib/mock/lottery.ts | 04-26#r-lottery-engine | foundations |
| DEMO_SETS (3), DEMO_CARDS (18), DEMO_TIERS, CLUB_ACCENT, DEMO_PITY_BACKSTOP 12 | src/lib/collection/fixtures/epl.ts | 04-31#r-collection-lib | this track |
| Persisted collection state `localStorage["yaobet.collection.v1.demo-a"]` | src/lib/collection/adapters/store.ts | 04-31 | this track |

## 3. Tailwind translation notes

### 3.1 Rules that apply to every leaf in this track

- **T1, token syntax.** Read tokens as `utility-(--token)`. Font sizes must carry a type hint, because `text-(--t-h2)` is ambiguous between color and size: write `text-(length:--t-h2)`. Gradient tokens: `bg-(image:--x)`. Never use the default numeric spacing scale for `--space-5..8`: `p-5` is 20px, `p-6` 24px and `p-8` 32px, but `--space-5` is 24px, `--space-6` 32px, `--space-7` 40px and `--space-8` 48px (04-01#r-vip-shared-tokens). `p-1..p-4` happen to match `--space-1..4`, but use the token form anyway so the ADR-002 token lint can see it.
- **T2, transforms.** Every guide `transform:` becomes `[transform:…]`, or a component class. Do not use `scale-*`, `rotate-*` or `translate-*` utilities. In Tailwind v4 those set the individual `scale` / `rotate` / `translate` properties, which causes three problems: (a) the guide's `transition: transform …` lists (langBtn, CTAs, FAQ chevron, tabs, rails, packs, ceremony cards) would not animate them; (b) PackStage `@keyframes bob` animates the individual `translate` property on purpose, so that it composes with the inline-var `transform` (04-33), and a `translate-x-*` utility would stack on top of it; (c) computed-style checks would differ. Write transition lists verbatim as `[transition:transform_var(--dur-fast)_var(--ease-standard),…]`.
- **T3, hover.** Tailwind v4's `hover:` only applies under `@media (hover: hover)`. The guide's `:hover` has no media gate. Exact parity needs `@custom-variant hover (&:hover);` in the Tailwind entry. That entry belongs to foundations, so it is flagged under Risks.
- **T4, breakpoints.** `@media (max-width: N)` is inclusive, while Tailwind `max-[N]` compiles to `width < N`. Use `[@media(max-width:900px)]:` or named custom variants. Breakpoints in this track: max 900 (VIP), max 560 (TierDeck), max 640 (LotteryRoot), max 1023 (CollectionApp zone2Head). Min-width rules map exactly to `min-[N]:` or the defaults (`sm` 640, `md` 768, `lg` 1024): min 480, min 560 (scratch card, OutcomeFrame), min 640 (PerkGallery), min 768 (CurrentTierCard, TierLadder, PrivilegeTable, VipRules, ProductGrid), min 900 (collection), min 1024 (ProductGrid, PerkGallery).
- **T5, reduced motion.** Use `motion-reduce:`. Foundations' motion.css also zeroes durations globally with `!important` (04-01#r-vip-shared-tokens). JS flags `data-motion="off"` (ScratchCardBody) map to `in-data-[motion=off]:` or to component-CSS selectors.
- **T6, state selectors.** Compute exclusive class sets in JSX from the same state, and keep the spec's data attributes in the DOM (`data-tone`, `data-open`, `data-beat`, `data-ready`, `data-hit`, `data-token`, `data-clearing`, `data-revealed`, `data-motion`, `data-outcome`, `data-active`, `data-playing`, `data-truthful`). No class-merge library is installed (`package.json` lists only next, react, react-dom and tailwind), so never put two conflicting utilities on one element. Tailwind orders utilities by its own sort, not by class order. Example: LevelTable `.td.rowHead` must get the panel-alt background only, not both.
- **T7, pseudo-elements.** `before:content-['']`, `after:content-['']` (VipFaq bar, scratch medallion bevel and milled rings, perforation dots).
- **T8, color-mix and gradients.** Single values go inline as arbitrary values (`bg-[color-mix(in_srgb,var(--vip-gold-mid)_8%,transparent)]`). Any multi-layer `background:` (2+ radial or linear layers) becomes a named `@utility` in the area CSS file, copied verbatim from the guide's CSS block.
- **T9, keyframes.** Global `@keyframes` live in the area CSS. **Collision:** CardArt `@keyframes sweep` (04-34) clashes with the Skeleton primitive's `@keyframes sweep` (01-08-f-ui, Skeleton.module.css). CSS Modules hid this by hashing names; global CSS would let the last definition win. Rename ours to `card-foil-sweep` (names are not user-visible). No other track-R name collides with any section (`rg '@keyframes' sections/*.html`).
- **T10, inline style for computed values.** Copy these from the source as `style` props, unchanged: TierDeck `backgroundColor`, `transform`, `zIndex`, `opacity`; VipHeroMember `.fill` width, `.knob` left, tierPill background, nextChip `borderColor`/`color`; PrivilegeComparison and PrivilegeMatrix gem background and title color; LevelRing SVG attributes; CurrentTierCard fill width; scratch `--k`; PackStage `--i`; ceremony `--i`/`--n`; CardArt `--accent`; CollectionApp `.bar span` width.
- **T11, utilities that exist.** `line-clamp-2`, `text-balance`, `tabular-nums`, `wrap-anywhere`, `isolate`, `mix-blend-screen`, `perspective-[900px]`, `aspect-[3/2]`, `aspect-[300/420]`, `aspect-square`, `select-none`, `touch-none`, `touch-pan-y`, `sr-only`. Arbitrary properties: `[font-variant-caps:small-caps]`, `[-webkit-overflow-scrolling:touch]`, `[stop-color:var(--vip-gold-mid)]`, `[stroke:url(#vipRingGrad)]`.
- **T12, Preflight.** If foundations keeps Preflight, its `svg,img{display:block}`, `h1-h6{font-size:inherit}`, button/list resets and `table{border-collapse:collapse}` sit underneath every element here. All track-R elements set these properties explicitly in the guide, so writing every guide declaration (including `margin: 0`, `list-style: none`, `border-collapse: separate`) keeps parity.

### 3.2 Per item

| Item | Plain utilities | Needs area CSS (`@layer components` / `@utility` / keyframes) | Exact-preserving method |
|---|---|---|---|
| VipProgram, langToggle | layout, pill, colours, `[@media(max-width:900px)]:max-w-full` | none | T2 for `scale(1.05)`; `motion-reduce:[transform:none]` |
| VipSectionHeading | yes | none | `[font-variant-caps:small-caps]` |
| VipHeroGuest | badge, CTAs | `@utility vip-hero-guest-bg` (radial + panel) | clamp font-size as arbitrary `text-[clamp(var(--t-h1),4.5vw,calc(var(--t-display)*1.35))]` |
| VipHeroMember | yes | `@utility vip-hero-member-bg` (2 radials + panel) | inline width/left; `[@media(max-width:900px)]:order-[-1]` on nextChip |
| LevelRing | SVG | `.vip-ring-arc{stroke:url(#vipRingGrad)}` + stop classes | keep fixed id `vipRingGrad` (single instance) |
| TierDeck | stage, dots | none | inline transform string verbatim (04-07 lines 263-265); `touch-pan-y`; no transform transition |
| PrivilegeComparison | yes | none | `[@media(max-width:900px)]:[transform:rotate(90deg)]` on arrow |
| PrivilegeMatrix | yes, `table-fixed`, sticky col | none | thead and tbody cells get distinct class sets (T6); `.colSelected .tierName` becomes a conditional class |
| LevelTable | yes | none | sticky header/col/corner z values `z-(--z-content)`, `z-(--z-sticky)`, `z-[calc(var(--z-sticky)+1)]`; `last:` row border-bottom none via `[tbody_tr:last-child_&]:border-b-0` or JSX flag |
| VipFaq | yes | none | `before:` bar; `group` on question, `group-hover:[transform:scale(1.1)]`; open state from JSX; `max-h-0` to `max-h-[520px]` with `[transition:max-height_var(--dur-slow)_var(--ease-standard)]` |
| CurrentTierCard | yes | none | `md:[&_button]:w-auto md:[&_button]:flex-[0_0_auto]` (replaces `:global(button)`) |
| TierLadder | yes | none | `md:[&>div]:w-full md:[&>div]:pr-0` on the Scroller className (needs the Scroller DOM contract, see Gap G7) |
| PrivilegeTable | yes | none | `md:[&>div]:w-full`; label column vs tier column class sets are explicit, no `:not(.labelCol)` |
| PerkGallery, VipRules, VipSection | yes | none | reproduce the redundant `lg:grid-cols-2` (REWARDS-15) |
| PointsHeader | yes | none | none |
| ProductGrid tabs/grid | yes | none | T2 tab hover scale; `grid-cols-2 md:grid-cols-3 lg:grid-cols-4` |
| ProductCard | yes, `line-clamp-2`, `aspect-[3/2]` | none | sold-out `.mediaSoldOut .img` becomes `opacity-40` on the img via JSX; dead classes not emitted |
| RedeemDialog | yes | none | `data-tone` stays in the DOM, costValue colour chosen in JSX; `*:flex-[1_1_0]` on actions; the second and third costRow get `mt-(--space-2)` |
| StoreTerms | yes | none | chevron classes chosen by open state in JSX (rotate vs `group-hover/trigger` scale); answer padding `pl-[calc(var(--space-4)+34px+var(--space-3))]` |
| LotteryRoot | yes | none | T2 for 1.02 / 1.05 scale; `[@media(max-width:640px)]:` variants; `contents` for gameMount |
| ScratchCardGame | header, foot, dev bar | yes: `.sc-ticket` bg (3 layers), `.sc-band-well` bg, `.sc-coin-band`, `.sc-coin-field`, `[data-hit]` gold coin, `::before/::after` rings, `.sc-perf` dots, `@keyframes token-pulse`, `data-motion="off"` overrides | port module selectors verbatim under the `sc-` prefix in `@layer components` (descendant `.fieldCell[data-hit] .fieldCoin`, delay `calc(var(--k,0)*var(--dur-fast)/4)`); keep `data-token` on coins |
| ScratchSurface + coverArt | canvas classes: `absolute inset-0 block size-full rounded-[inherit] touch-none select-none cursor-grab active:cursor-grabbing` | `data-[clearing]:opacity-0 data-[clearing]:pointer-events-none`, `[transition:opacity_var(--dur-slow)_var(--ease-standard)]`, `motion-reduce:transition-none`, `in-data-[motion=off]:transition-none` | canvas painting is TS, ported verbatim (04-28 lines 290-610); no Tailwind involvement |
| OutcomeFrame | text and layout | `@keyframes frame-in`, `total-settle`; `.frame[data-outcome=…]` border/bg | outcome-specific classes chosen in JSX; animation via component class so the `data-motion` and reduced-motion overrides keep their specificity |
| CollectionApp | most | `.cl-rail` (`--rail-pad` var, hover 1.02), plate wings (gradients, `:last-child` reversed) | `[--rail-pad:var(--space-4)] min-[900px]:[--rail-pad:var(--space-5)]`, children `px-(--rail-pad)`; `enabled:hover:` for `:hover:not(:disabled)`; `[@media(max-width:1023px)]:pr-[calc(48px+var(--space-2))]` |
| PackStage | chrome, CTA, turns | yes, the whole `pack.module.css` (`.stage>*:not(...)`, `--i` calc transforms, filters, `bob`/`sheen`/`tear`/`rise`, `.picked`/`.tear`/`.dim`, ≥900 overrides incl. the dead `.info{right:max()}` rule) | port verbatim under the `pk-` prefix; full-bleed `w-screen ml-[calc(50%-50vw)]` stays (REWARDS-23) |
| CardArt | wrap | `.ca-foil` (`card-foil-sweep`), `.ca-ghost` filter, `.ca-rare` outline, unused `.ca-back`/`.ca-dealt`/`dealIn` optional | SVG verbatim; gradient ids `c-{cardId}-*` duplicated across rails (REWARDS-27) |
| RewardCeremony | panel, copy, buttons | `.rc-card` (`--i` transforms, origin 50% 120%), `.rc-seal`, `.rc-ring`/`.rc-tick` (`--len` dash), `@keyframes draw`, `.panel[data-beat=…]` and `.receipt[data-ready=true]` | port the state-descendant selectors verbatim (data-beat drives transitions); `[&_svg]:size-full [&_svg]:rounded-(--radius-md)` |
| CollectionTerms | `[&_h3]`, `[&_ul]`, `[&_li]`, `[&_strong]` arbitrary variants | none | sticky footer `sticky bottom-0 bg-(--surface)` |
| CollectionHistory | yes | none | badge colour map `{earn,draw,dupe,reward,info}` becomes a literal class map (the source warns these are resolved dynamically) |
| MyCards | yes | none | `grid-cols-[repeat(auto-fill,minmax(140px,1fr))] min-[900px]:grid-cols-6` |
| CardDetail | yes | none | none |
| /dev/collection-ports | yes | none | state pill colour map |

### 3.3 Tradeoffs and ADRs (proposed, need PM approval)

```yaml
tradeoffs:
  - option: A-utilities-only (every rule as utilities/arbitrary values in JSX)
    yagni_rung: 1
    pros: [single styling mechanism, lint sees every token]
    cons: [descendant/state selectors (data-beat, data-motion, data-hit, .stage>*:not()) lose source specificity, keyframes still need global CSS, multi-layer gradients unreadable]
    risk: high (silent visual drift in PackStage, ScratchCard, Ceremony)
  - option: B-hybrid (utilities for layout/simple state; per-area CSS in @layer components for art)
    yagni_rung: 4 (Tailwind platform feature, D2 explicitly allows @layer components/@utility)
    pros: [complex selectors ported verbatim, so exact parity; area files are disjoint leases]
    cons: [four area CSS files to import from the Tailwind entry]
    risk: low
  - option: C-css-modules
    yagni_rung: 4
    pros: [verbatim copy]
    cons: [rejected by owner decision D2]
    risk: n/a
adr:
  - id: ADR-R1
    title: Hybrid Tailwind + area component CSS for track R art
    status: proposed
    yagni_rung_selected: "4; rung 1 (utilities only) cannot keep descendant-state specificity"
    context: "04-33 pack.module.css, 04-27 ScratchCardGame.module.css and 04-35 ceremony.module.css use descendant data-attribute selectors, --i/--k calc transforms and keyframes; D2 allows @layer components/@utility."
    decision: "Foundations creates empty src/styles/areas/{vip,store,lottery,collection}.css and imports them from the Tailwind entry; each R leaf then owns one area file. Area classes are prefixed (vip-, st-, sc-, pk-, ca-, rc-, cl-)."
    consequences: {positive: "exact selectors and keyframes", negative: "a lease handoff from foundations to the area leaf", neutral: "the token lint must also scan src/styles/areas"}
    alternatives_considered: [A-utilities-only, C-css-modules]
  - id: ADR-R2
    title: Port non-visual feature libraries verbatim from the original source
    status: proposed (needs owner OK)
    context: "The guide elides lib/collection (04-31 line 568 is a literal '…'). Original sizes: math.ts 298, ports.ts 245, types.ts 273, adapters/fixtures.ts 746, runtime.ts 164, clock.ts 55, index.ts 78 lines (wc on orig)."
    decision: "Copy src/lib/collection/**, src/lib/vip/** and src/lib/store/escalation.ts byte-for-byte from orig (read-only), then typecheck."
    consequences: {positive: "defects REWARDS-25/26 reproduce exactly", negative: "copies the comments too, including plan tags"}
    alternatives_considered: ["re-derive from the guide prose (high drift risk)"]
```

## 4. Defects to reproduce

D3 applies: reproduce each defect as built; every fix below is a later candidate for `docs/rebuild/FIX-LIST.md`.

| Id | Anchor | Defect | Reproduce | Proposed later fix |
|---|---|---|---|---|
| REWARDS-01 | 04-01#r-vip-palette | Per-tier metallic gradients declared (`--vip-tier-*-grad`, `TIERS[i].grad`) but never painted | keep the tokens and `grad` data; paint flat `tier.acc` everywhere | delete the inert tokens or decide to paint them |
| REWARDS-02 | 04-01#r-vip-lib | `tier.gift` (50/99/199/399/799) never rendered; `unlock` strings use en-US commas ("500,000") | keep the field; the level table uses `giftAt()`; strings verbatim | drop `gift`; VN grouping |
| REWARDS-03 | 04-01#r-vip-lib | Rates "0.61%" and gifts "$50" (en-US) on a VI page; /vip 25% weekly cashback vs /tier 0.6-1.5% | `fmtRate`/`fmtGift`/`fmtCash` verbatim | VN formatters; unify the two VIP economies |
| REWARDS-04 | 04-01#r-vip-route-vip | `.vipPalette` #0b0a07 fills only the content column; shell canvas #0a0a0a leaves a seam | bg on the wrapper only | extend the palette or align the colours |
| REWARDS-05 | 04-01#r-vip-route-tier | QuickActionRail links /tier with aria-label "Giải đấu"; `.detailLink`/"Xem bậc thang chi tiết" unused, so /vip never links /tier | do not render detailLink (rail is shell's) | relabel; add the /vip to /tier link |
| REWARDS-06 | 04-02#r-vip-program | "Đăng ký ngay" opens the auth modal in login mode | `onRegister = onLogin = promptAuth()` | `openAuthModal({mode:"register"})` |
| REWARDS-07 | 04-03#r-vip-section-heading | CSS comment says Cinzel, face is Montserrat | Montserrat via `--brand-font-display` | comment only (no visual) |
| REWARDS-08 | 04-05#r-vip-hero-member | Member hero always shows the demo "Jordan Rivera / VÀNG"; en-US "86,880" | render `CURRENT_USER` | bind to the session user |
| REWARDS-09 | 04-07#r-vip-tier-deck | Dots `role=tab` with no tabpanel; cards repeat the selection with aria-pressed | markup as specified | radiogroup or `aria-controls` |
| REWARDS-10 | 04-08#r-vip-privilege-comparison | Comment says "always an upgrade"; Đồng/Bạc puts a lower tier in the gold "target" card | `cmpT = (sel===cur && cur<4) ? cur+1 : sel` | clamp the target to at least cur+1, or relabel |
| REWARDS-11 | 04-11#r-vip-faq | FAQ #5 says a host comes "from Bạch Kim" but `bnHost` unlocks at Kim Cương; /tier ranks on total turnover | copy verbatim | align copy and data |
| REWARDS-12 | 04-12#r-vip-current-tier-card | Progress envelope not user-aware (a level-0 user still sees "Còn 11.400.000 ₫ … Kim Cương") | fixture envelope | derive progress from the user |
| REWARDS-13 | 04-13#r-vip-tier-ladder | "Hoàn trả 1%" next to the perk "Hoàn trả 1,0%" | `1.0.toString()` behaviour | one formatter |
| REWARDS-14 | 04-14#r-vip-privilege-table | Perks non-cumulative (higher tiers show "—"); `colPerks` unused | per-tier perks only | cumulative perks |
| REWARDS-15 | 04-15#r-vip-perk-gallery | ≥1024 rule repeats `1fr 1fr` | emit the redundant `lg:grid-cols-2` | delete |
| REWARDS-16 | 04-18#r-store-data | Cooldown expiries computed once at server module load, so states decay with uptime | module-level `isoIn()` (see Gap G4) | compute per request |
| REWARDS-17 | 04-20#r-store-product-grid | Loading/error unreachable (status starts "ready"); fetch failure shows "Cửa hàng trống"; tabs without tabpanel | `getProducts().catch(()=>[])`, initial "ready" | real loading/error; tabpanel |
| REWARDS-18 | 04-21#r-store-product-card | `paused` ignored by cards; dead `.rollingSlot`/`.limit*` CSS | do not destructure `paused`; dead CSS not emitted (no visual) | honour paused |
| REWARDS-19 | 04-22#r-store-redeem-dialog | Balance not decremented after success; at_floor/unlimited disclosures never rendered; StoreTerms promises points "on the button" | `points` prop static | lift balance state; render disclosures |
| REWARDS-20 | 04-24#r-lottery | "Mua một tấm" with no purchase; "Đã cộng vào số dư" with no wallet call; nested `<main>` (also /dev/collection-ports per 04-40) | `main.page` inside the shell main | owner review of copy; use `div` |
| REWARDS-21 | 04-26#r-lottery-engine | Dust consolation on every card incl. wins; losers built with a near-miss lure | engine verbatim (foundations' lib/mock/lottery.ts) | owner review |
| REWARDS-22 | 04-27#r-lottery-scratch-card | `shortVnd` comment says 480px, CSS switches at 560px; viewport breakpoints in a ≤560px dialog; dev force bar ships to players | 560px viewport rule; dev bar always rendered | container queries; gate the dev bar |
| REWARDS-23 | 04-30#r-collection-route-main | Full-bleed stage `100vw; margin-left: calc(50% - 50vw)` shifts ~30px left between 1024-1599px and includes the scrollbar | keep the 100vw formula | container-relative bleed |
| REWARDS-24 | 04-30#r-collection-route-dev | Dev harness writes into the player's "demo-a" store ("probe-set" history rows, bogus priority ["s1","s2"], real mints); stale "refuse on purpose" note | same account key | separate account key |
| REWARDS-25 | 04-31#r-collection-lib | Published 12-open rare guarantee not enforced (`backstopDue` never called) | draw by weight only | enforce the backstop in `outcome.draw` |
| REWARDS-26 | 04-31#r-collection-lib | Re-entry: in-memory `accumulated`/`seq` reset while entitlements persist, so "+1 lượt mở" stalls and `ent-1` ids collide ("Lượt mở này đã được sử dụng.") | adapter verbatim | persist seq/accumulated |
| REWARDS-27 | 04-32#r-collection-app | Rail order "frozen" yet recomputed on every nonce remount; toast comment says txn id; "five fields" comment; duplicate CardArt SVG ids | key = nonce remount; ids `c-{cardId}-*` | `useId`; real freeze |
| REWARDS-28 | 04-33#r-collection-pack-stage | `filter` on packs and ghosts despite the house ban; dead ≥900 `.info{right}`; `:not(.info)` gives `.chrome` max-width 780px; Foil ids `pk`/`pkSheen` repeated ×5; raw HSL literals | port pack CSS verbatim | tokens; unique ids |
| REWARDS-29 | 04-34#r-collection-card-art | Rare-only infinite foil sweep vs "no rarity-differentiated motion" | `.ca-foil` on rare only | owner decision |
| REWARDS-30 | 04-35#r-collection-ceremony | Beat timers (900 + 700ms) run during the confirm step, so a slow confirm skips the animation and may read "lần đổi thứ 0"; "returns to 0/N" wrong with spares | effect on `[beat, reduced]` with no impact check | start the timers on confirm |
| REWARDS-31 | 04-36#r-collection-terms | "1.8" decimal point; opens "from settled sports bets" vs the demo button; backstop not implemented | `(COMMON/RARE).toFixed(1)` | VN format; align copy |

## 5. Gaps and contradictions

| Id | Where | Guide quote / issue | Resolution or decision needed |
|---|---|---|---|
| G1 | 04-31 | Adapter listing elided: "`…`" (line 568). math.ts, ports.ts, types.ts, runtime.ts, clock.ts and index.ts are described, not given verbatim. The 11 probe ports on /dev/collection-ports are not named ("11 probe rows") | Builder would guess. Needs ADR-R2 (verbatim port from orig, about 1,700 lines). Decision: PM/owner |
| G2 | 04-18#r-store-data | "A rebuild should reproduce the states by computing expiries per request (or document the drift)" contradicts D3 "Reproduce defects as built" | Recommend D3: module-load `isoIn` plus a FIX-LIST entry. Decision: PM |
| G3 | 04-01, 04-40 | `components/vip/copy.ts` keys `pageTitle`, `detailLink`, `colPerks` only partly quoted; lib/vip `types.ts`/`index.ts` not verbatim | Covered by ADR-R2 (copy from orig) |
| G4 | 04-20 | `useGridCols`, `computeGridFill`, `TileSkeleton` used but not specified in track R | From `@/ui` (orig:components/store/ProductGrid.tsx:26-28). ui-member must export them or the store leaf fails typecheck |
| G5 | 04-27, 04-32, 04-35, 04-39 | Overlay props (`presentation="auto"`, `desktopMaxWidth=560`, `swipeDismiss=false`, `labelledBy`, `open`, `onClose`) defined by the shell track | Contract dependency on shell; confirm prop names in the shell review |
| G6 | 04-27 | `usePrefersReducedMotion` imported from `../layout/_internal/` (orig:components/lottery/ScratchCardGame.tsx:63); RewardCeremony uses `matchMedia` directly (orig:components/collection/RewardCeremony.tsx:105) | Shell must export the hook; ceremony keeps its inline matchMedia |
| G7 | 04-13, 04-14 | `.scroller > div { width: 100% }`: "the Scroller renders `<outer><rail/></outer>`; .scroller is on outer" | ui-member Scroller must keep that DOM and accept `className` on outer, plus props `snap`, `peek`, `label`, `freezeFirstColumn` |
| G8 | 04-12..04-23, 04-38 | Primitive variants used: Card `vip`/`tile`/`product`/`default` + `active`; Button `gold`/`ghost`/`primary`, sizes `sm`/`md`/`lg`, `fullWidth`, `loading`; Badge tone `gold`/`neutral`, variant `subtle`/`solid`; Tabs `items`/`scrollable`/`label` with ids `tab-*`/`panel-*`; Countdown `endsAt`, `zeroLabel`, `onZeroState`/`onZero`, `className`; Modal `size="sm"` | ui-member contract; list it in their leaf acceptance |
| G9 | 04-12, 04-13 | "Hoàn trả {pct}%" with a VN comma (1.2 → "1,2"; 1.0 → "1"): the formatter is not named | Builder must not invent; read from orig (ADR-R2 scope extends to components/vip read for the formatter) |
| G10 | 04-37, 04-39 | Times "DD/MM HH:mm" in local timezone; the formatter is not given | orig:components/collection/CollectionHistory.tsx:192-193 (`padStart` on getDate/getMonth+1/getHours/getMinutes) |
| G11 | 04-32, 04-38 | Ownership sentence thresholds not stated | orig:components/collection/CollectionApp.tsx:542-544: 0 → "{name} — chưa có", 1 → "{name} — đang giữ", ≥2 → "{name} — đang giữ {n} thẻ" (same in MyCards.tsx:365-367) |
| G12 | 04-34 | Hash "fold(h·31 + charCode) >>> 0" is ambiguous | orig:components/collection/CardArt.tsx:32-43: `h = (h*31 + code) >>> 0`, `(h % 32)+1`; rating multiplier 17, `rare ? 88+(h%8) : 78+(h%10)` |
| G13 | 04-29 | "Kèm {dust} tiền bù" does not state the format | orig:components/lottery/_internal/OutcomeFrame.tsx:119 uses `formatVnd(card.dust)` |
| G14 | 04-01#r-vip-route-tier | Back link "‹ Hạng VIP": href not given | orig:app/tier/page.tsx:40 `href="/vip"` |
| G15 | 04-18 | "lazy RedeemDialog" | No `next/dynamic`/`React.lazy` in orig components/store (rg returned none); it is conditionally mounted when `selected` is set |
| G16 | 04-25, 04-40 | `.soonCard:focus-visible` rule targets disabled, unfocusable buttons | Reproduce the dead rule; no builder guess needed |
| G17 | 04-40 note | "Not determinable from source: Card/Button/Badge/Modal/Overlay/Tabs/Scroller visual chrome …; native `<select>` metrics; image licensing" | Carried forward: chrome comes from the ui-member/shell reviews; `<select>` metrics are browser-native |
| G18 | 05-01#v-capture | The capture recipe locates the DEV toggle via `[class*="cycle"]` / `[class*="stateLabel"]` | Not this track, but Tailwind removes module class names. Foundations/shell must keep literal `cycle`/`stateLabel` classes or the visual gate cannot set the state for /vip, /cua-hang and /ve-so guest shots |

## 6. Assets

All under `public/`; copying them read-only is allowed by DECISIONS (old app `apps/web/public/**`). Sizes are pixels from the guide, bytes from `ls -la` on orig.

| Public path | Size | Used by |
|---|---|---|
| /assets/store/reward-coins.jpg | 524×416 JPEG, 176,608 B | every store product (mockProduct default) |
| /assets/players/salah.jpeg | 201×251, 8,681 B | CardArt |
| /assets/players/vandijk.jpeg | 683×449, 34,689 B | CardArt |
| /assets/players/konate.jpeg | 739×415, 26,641 B | CardArt |
| /assets/players/elliott.jpeg | 554×554, 31,694 B | CardArt |
| /assets/players/gabriel.jpeg | 399×501, 31,997 B | CardArt |
| /assets/players/saka.jpeg | 400×500, 25,451 B | CardArt |
| /assets/players/gyokeres.jpeg | 399×501, 28,209 B | CardArt |
| /assets/players/rice.jpeg | 399×501, 25,902 B | CardArt |
| /assets/players/dowman.jpeg | 399×501, 29,901 B | CardArt |
| /assets/placeholders/tier-badge.svg | 632 B | in mock data (`badgeSrc`), not rendered |
| /assets/placeholders/perk.svg | 641 B | in mock data (`illustrationSrc`), not rendered |

The other 9 cards use drawn art (`artSrc: ""`). Ticket art, stadium, foil packs, card faces, LevelRing and seal are inline SVG; the scratch coating is painted on canvas. None needs a file.
Reference shots (28) in `.hc/ui-rebuild-guide/shots/`: `{m375,d1440}-tiered-{vip,tier,cau-lac-bo,cua-hang,ve-so,bo-suu-tap,bo-suu-tap__cua-toi,dev__collection-ports}.jpg` (16) and `{m375,d1440}-guest-{vip,cua-hang,ve-so}.jpg` (6). The remaining 6 tiered shots cover routes outside this track.

## 7. Proposed leaves

Prerequisites (other tracks): foundations (tokens incl. `--vip-*` as real `:root` custom properties; `src/styles/areas/{vip,store,lottery,collection}.css` empty stubs imported from the Tailwind entry per ADR-R1; lib/format, lib/auth, lib/mock/{vip,store,lottery}); ui-member (17 primitives + TileSkeleton/useGridCols/computeGridFill); shell (Overlay, usePrefersReducedMotion). Common gate for every leaf: `npx tsc --noEmit` exit 0, `npm run lint` exit 0, token lint (ADR-002) exit 0.

| Leaf | allowed_files | Implements | Needs | Mechanical acceptance |
|---|---|---|---|---|
| R1 rewards-libs (6 files) | `src/lib/vip/**`, `src/lib/store/escalation.ts` | 04-01#r-vip-lib, 04-18#r-store-lib | foundations | `rg -F 'Đặc quyền dành riêng cho hội viên VIP' src/lib/vip/copy.ts`; `rg -F 'GIFT_MULT = [0.6, 0.8, 1.0, 1.4, 2.0]' src/lib/vip/formulas.ts`; `rg -F 'RG_UNLIMITED_WARN_STEP = 4' src/lib/store/escalation.ts`; a unit check that `pointsAtStep(1000,0.7,k,null)` for k=1..6 gives 1000,1429,2041,2916,4165,5950 and `giftAt(2,1)` is 50 |
| R2 collection-lib (9 files) | `src/lib/collection/**` | 04-31#r-collection-lib | R1 none; foundations lib/types | `rg -F 'yaobet.collection.v1' src/lib/collection/adapters/store.ts`; `rg -F 'DEMO_PITY_BACKSTOP = 12'`; `rg -F 'Không tìm thấy lượt mở.'`; a unit check of `rateInSet("vandijk","set-defenders")` (about 0.1212) and per-set sums of 1 |
| R3 vip-program (12 files) | `src/components/vip/{VipProgram,VipSectionHeading,VipHeroGuest,VipHeroMember,LevelRing,TierDeck,PrivilegeComparison,PrivilegeMatrix,LevelTable,VipFaq}.tsx`, `src/app/vip/page.tsx`, `src/styles/areas/vip.css` | 04-01..04-11 | R1, foundations, ui-member | `GET /vip` returns 200 (guest and tiered); grep "Hành trình VIP", "Bạn ở đây", "Cược tuần", "Làm sao để thăng hạng VIP?"; `rg -F 'vipRingGrad'`; `rg -F 'DRAG_PER_CARD = 120'`; `rg -F 'vip-page-bg'` in the tokens file; shots m375/d1440 tiered and guest vip |
| R4 vip-tier-club (10 files) | `src/components/vip/{CurrentTierCard,TierLadder,PrivilegeTable,PerkGallery,VipRules,VipSection}.tsx`, `src/components/vip/copy.ts`, `src/components/vip/index.ts`, `src/app/tier/page.tsx`, `src/app/cau-lac-bo/page.tsx` | 04-01#r-vip-route-tier, #r-vip-route-club, 04-12..04-17 | R3 (index barrel), ui-member Scroller/Card/Badge | `GET /tier` and `GET /cau-lac-bo` return 200; grep "Bậc thang VIP", "Vòng cược lên hạng kế tiếp", "Chương trình câu lạc bộ đại lý sẽ sớm ra mắt.", "Tích lũy bằng vòng cược"; `rg -F 'href="/vip"' src/app/tier/page.tsx`; shots tier, cau-lac-bo |
| R5 store (8 files) | `src/components/store/**`, `src/app/cua-hang/page.tsx`, `src/styles/areas/store.css` | 04-18..04-23 | R1, foundations mock/store, ui-member Modal/Countdown/Button/Card | `GET /cua-hang` returns 200; grep "Điểm tích lũy của bạn", "Thiếu", "Hết lượt đổi", "Xác nhận đổi quà", "Đổi quà thành công", "Cập nhật lần cuối · —"; `rg -F 'setTimeout' src/components/store/RedeemDialog.tsx` (600ms); shots cua-hang tiered and guest |
| R6 lottery (8 files) | `src/components/lottery/**`, `src/app/ve-so/page.tsx`, `src/styles/areas/lottery.css` | 04-24..04-29 | foundations mock/lottery, shell Overlay and usePrefersReducedMotion, ui Button/Icon | `GET /ve-so` returns 200; grep "Tỷ lệ công bố", "Cào để mở", "Mở tất cả", "Buộc kết quả", "Bù thẻ không trúng"; `rg -F 'CLEAR_THRESHOLD = 0.58'`; `rg -F 'data-token'`; `rg -F '@keyframes token-pulse' src/styles/areas/lottery.css`; shots ve-so tiered and guest; a manual canvas check that the scratch erases and the section opens past 58% |
| R7 collection-surface (9 files) | `src/components/collection/{CollectionApp,PackStage,CardArt,RewardCeremony,CollectionTerms,CollectionHistory}.tsx`, `src/app/bo-suu-tap/{page,CollectionRoot}.tsx`, `src/styles/areas/collection.css` | 04-30#r-collection-route-main, 04-32..04-37 | R2, shell Overlay, ui Icon | `GET /bo-suu-tap` returns 200; grep "BỘ SƯU TẬP", "Lượt mở còn lại: ", "MỞ TIẾP", "Xác nhận · dùng", "Đang chuyển vào ví…"; `rg -F '@keyframes card-foil-sweep'` and **no** `@keyframes sweep` in collection.css; `rg -F '@keyframes bob'`; shots bo-suu-tap |
| R8 collection-mine-dev (5 files) | `src/components/collection/{MyCards,CardDetail}.tsx`, `src/app/bo-suu-tap/cua-toi/{page,MyCardsRoot}.tsx`, `src/app/dev/collection-ports/page.tsx` | 04-30#r-collection-route-mine, #r-collection-route-dev, 04-38, 04-39 | R2, R7 (CardArt, CollectionHistory), ui Tabs | `GET /bo-suu-tap/cua-toi`, `GET /bo-suu-tap/cua-toi?tab=lich-su` and `GET /dev/collection-ports` return 200; grep "Bạn đang giữ", "Chưa có thẻ nào", "Tỷ lệ ra thẻ khi mở cho bộ:", "Collection ports — harness"; `rg -F 'Suspense'` in cua-toi/page.tsx; shots bo-suu-tap__cua-toi, dev__collection-ports |

The leaves are disjoint. R3 and R4 split `src/components/vip/**` by explicit file lists. R7 and R8 split `src/components/collection/**` the same way. Area CSS files pass from foundations (stub) to R3, R5, R6 and R7 sequentially. Waves: {R1, R2} then {R3, R5, R6} then {R4, R7} then {R8}.

## 8. Risks

1. **Tailwind v4 semantics drift** (T1-T4): media-gated `hover:`, exclusive `max-*`, individual transform properties (which break `transition: transform` and stack with PackStage `bob`), the default spacing scale differing from `--space-5..8`, and the `text-(--t-*)` type ambiguity. Each one is silent at build time and only shows in screenshots or interaction.
2. **Selector-specificity and keyframe collisions:** flattening `data-beat`/`data-motion`/`data-hit`/`data-tone` descendant rules into utilities changes cascade order. The `sweep` keyframe collides with the Skeleton primitive. Mitigation: ADR-R1 area CSS and the rename to `card-foil-sweep`.
3. **Under-specified lib/collection** (G1): about 1,700 original lines are not verbatim in the guide. The re-entry and pity defects (REWARDS-25/26) depend on exact adapter internals (in-memory `seq`/`accumulated`, mulberry32 seed `20260813 ^ 0x5eed`, idempotency keys). Mitigation: ADR-R2 verbatim port.
4. **Canvas coating bound to literal custom-property names:** `readCoverPalette` reads `--brand-accent`, `--brand-accent-2`, `--canvas` and `--text-hi` from computed style, and coin centres from `[data-token]`. If foundations emits tokens only under `@theme` names (for example `--color-*`), the coating silently falls back to identical literals. That hides the break until a brand switch. Acceptance must assert those four names exist on `:root`.
5. **Cross-track contracts:** Overlay props (G5), Scroller DOM (G7), primitive variants (G8), the DEV-toggle class names needed by the screenshot recipe (G18), and the time-based store mock (G2) all decide whether /vip, /tier, /cua-hang, /ve-so and the collection routes pass the visual gate. They are owned by the shell, ui-member and foundations leaves.

# Guide review — track `shell-home` (S1–S7)

Reviewer: `sa` · Date: 2026-11-05 · Binding inputs: `docs/rebuild/REVIEW-BRIEF.md`, `docs/rebuild/DECISIONS.md` (D1–D4), `sections/00-0*`, `sections/05-01-v-checklist.html`.
Scope: `sections/02-01` … `02-07`. Foundations (tokens, themes, typography, motion, reset, root layout, `src/lib/**`, mock data) and ui-member (17 `src/ui` primitives, member area) are referenced by anchor, not re-specified.
Anchor notation: `02-01#s-header` = `docs/rebuild/sections/02-01-s-shell-h.html#s-header`. `SRC:` = original source `Igaming-Agent-1/apps/web/src/` (read-only, used only to close gaps).

---

## 1. Coverage

Method: each HTML file was converted to text (tags stripped, `<pre>` blocks kept verbatim, table rows kept as pipe rows) and every line was read in slices of 250 lines or fewer. No file was skipped or sampled.

| Section file | h3 | Read fully | Components / routes covered |
|---|---|---|---|
| 02-01-s-shell-h.html (3855 lines, 287 KB) | 17 | yes | Root tree, shell grid, AppShell, ShellChrome, Header, NavDropdown, MemberMenu, NotificationBell, CategorySheet, Overlay + useFocusTrap, BottomTabBar, Footer, QuickActionRail, RightRail, Countdown (shell), Money (shell), Logo usage |
| 02-02-s-auth-h.html (781) | 3 | yes | Mock session + modal state machine, AuthModal, AuthField |
| 02-03-s-home-h.html (1763) | 8 | yes | Route `/` + `loading.tsx`, HeroBand, CategoryLauncher, StatsBar, ProviderGameGrid, SportsLifestyle, SportsMatchCard, DevAuthToggle |
| 02-04-s-vertical-h.html (603) | 5 | yes | Route `/[vertical]` + loading + not-found, CategoryPage, CategoryBanner, CategoryGrid, LiveOddsBoard |
| 02-05-s-promo-h.html (525) | 5 | yes | Route `/khuyen-mai`, PromoHero, PromoGrid, route `/khuyen-mai/[id]`, PromoDetail |
| 02-06-s-nav-map-h.html (35) | 0 (h2 only) | yes | Sitemap: every URL × nav surface × verbatim label × icon |
| 02-07-s-unused-h.html (726) | 6 | yes | Dead inventory + specs for AuthCluster, PromoChips, LiveGamesBand/JackpotTicker/LiveMatchCard, VipAisle, PartnerBand, HomeFooter |
| **Total** | **44** | | 22 amber callouts, 1 note callout (nav-map), 58 `<pre>` blocks |

---

## 2. Inventory

Paths in column 2 are original source paths. The target path is in the leaf (section 7). `ui:` = ui-member primitive. `lib:` = foundations lib.

### 2a. Routes

| Name | Original source | Guide anchor | Depends on |
|---|---|---|---|
| `/` Home (async SC) | `app/page.tsx` | 02-03#s-home-route | getPromos, getVerticals, getJackpot, getMemberDayCountdown, getLeaderboard, getSportsMatches, getProviders, getGames; HeroBand, CategoryLauncher, StatsBar, ProviderGameGrid, SportsLifestyle, RightRail, DevAuthToggle |
| Root loading (also used by every route with no loading file, including `/khuyen-mai` and `/khuyen-mai/[id]`) | `app/loading.tsx` | 02-03#s-home-route ("Loading state") | ui:Skeleton, home layout CSS |
| `/[vertical]` (9 slugs) + `generateMetadata` | `app/[vertical]/page.tsx` | 02-04#s-vertical-route | resolveVertical, getCategoryPayload, CategoryPage |
| `/[vertical]` loading | `app/[vertical]/loading.tsx` | 02-04#s-vertical-route ("Loading") | ui:Skeleton |
| `/[vertical]` not-found (client) | `app/[vertical]/not-found.tsx` | 02-04#s-vertical-route ("Not found") | ui:Button (gold, icon home), useRouter |
| Vertical route CSS | `app/[vertical]/Route.module.css` | 02-04#s-vertical-route | tokens |
| `/khuyen-mai` | `app/khuyen-mai/page.tsx` + `khuyen-mai.module.css` | 02-05#s-promo-route | getPromos, PromoHero, PromoGrid |
| `/khuyen-mai/[id]` (pr1–pr8; unknown → default Next 404) | `app/khuyen-mai/[id]/page.tsx` | 02-05#s-promo-detail-route | getPromos, PromoDetail |

### 2b. Shell components (`components/layout/**`)

| Name | Original source | Guide anchor | Depends on |
|---|---|---|---|
| Root layout + Providers (reference only, foundations leaf) | `app/layout.tsx`, `app/providers.tsx`, `app/globals.css` | 02-01#s-shell-root; 01-07 root layout | MockAuthProvider `initialState="tiered"` > AuthModalProvider; AppShell; QuickActionRail as a sibling after AppShell |
| AppShell (async SC, no DOM) | `components/layout/AppShell.tsx` | 02-01#s-app-shell | getVerticals, getBalance (`lib/mock/wallet.ts:20`), ShellChrome |
| ShellChrome (client) | `ShellChrome.tsx` + `.module.css` | 02-01#s-shell-chrome | Header, CategorySheet, BottomTabBar, AuthModal, useRouter |
| Header (two-tier; BalanceChip inline) | `Header.tsx` + `.module.css` | 02-01#s-header | Money, NavDropdown, verticalIcon, MemberMenu, NotificationBell, ui:Button/Icon/Skeleton, useAuth, useAuthModal |
| NavDropdown (Tier-2 cell, the "CategoryRail") | `_internal/NavDropdown.tsx` + `.module.css` | 02-01#s-nav-dropdown | ui:Icon; 120 ms hover intent |
| verticalIcon map | `_internal/verticalIcon.ts` | 02-01#s-nav-dropdown | ui:Icon names |
| MemberMenu | `MemberMenu.tsx` + `.module.css` | 02-01#s-member-menu | useAuth (user, signOut), ui:Icon |
| NotificationBell + panel | `NotificationBell.tsx` + `.module.css` | 02-01#s-notification-bell | getNotificationBell (`lib/mock/notification-feed.ts:385`), relativeTime, ui:Icon |
| CategorySheet | `CategorySheet.tsx` + `.module.css` | 02-01#s-category-sheet | Overlay (sheet), verticalIcon |
| Overlay | `_internal/Overlay.tsx` + `.module.css` | 02-01#s-overlay | useFocusTrap |
| useFocusTrap (hook) | `_internal/useFocusTrap.ts` | 02-01#s-overlay ("Behaviour") | — |
| BottomTabBar | `BottomTabBar.tsx` + `.module.css` | 02-01#s-bottom-tab-bar | usePathname, useAuth, useAuthModal, ui:Icon |
| Footer (4 columns) | `Footer.tsx` + `.module.css` | 02-01#s-footer | 4 inline social SVG paths (verbatim lines 50–97), ui:Icon shield |
| QuickActionRail | `QuickActionRail.tsx` + `.module.css` | 02-01#s-quick-action-rail | 7 inline SVG glyphs (verbatim lines 269–402), sessionStorage, useSyncExternalStore, usePathname |
| RightRail (home only, SC) | `RightRail.tsx` + `.module.css` | 02-01#s-right-rail | Countdown, Money, ui:Skeleton, formatVnd |
| Countdown (shell-local) | `_internal/Countdown.tsx` + `.module.css` | 02-01#s-shell-countdown | usePrefersReducedMotion (shell copy) |
| Money (shell-local) | `_internal/Money.tsx` + `.module.css` | 02-01#s-shell-money | formatVnd / formatSignedVnd (`lib/format.ts:28,34`) |
| usePrefersReducedMotion (shell copy) | `_internal/usePrefersReducedMotion.ts:11` | 02-07#s-unused-h (duplicate row) | — (twin of `lib/rg.ts:13`) |
| Barrel | `components/layout/index.ts` | (implied) | — |
| Logo usage | `/assets/logo.svg` | 02-01#s-logo | — |

### 2c. Auth

| Name | Original source | Guide anchor | Depends on |
|---|---|---|---|
| MockAuthProvider / useAuth | `lib/auth/session.tsx:74` (lib, foundations) | 02-02#s-auth-state | fixtures |
| AuthModalProvider / useAuthModal | `lib/auth/modal.tsx:91` (lib) | 02-02#s-auth-state | — |
| useRequireAuth | `lib/auth/guard.ts:29` (lib) | 02-02#s-auth-state | useAuth, useAuthModal |
| Auth fixtures (u_new, u_vip) | `lib/auth/fixtures.ts` (lib) | 02-02#s-auth-state | — |
| AuthModal (+ AuthModalBody `key={mode}`) | `components/auth/AuthModal.tsx` + `.module.css` | 02-02#s-auth-modal | Overlay (auto, desktopMaxWidth 720), AuthField, ui:Button gold lg, ui:Icon |
| AuthField | `components/auth/AuthField.tsx` + `.module.css` | 02-02#s-auth-field | ui:Icon |

### 2d. Home

| Name | Original source | Guide anchor | Depends on |
|---|---|---|---|
| Home layout CSS (`.page`, `.main`, skeleton scaffolds) | `components/home/Home.module.css` | 02-03#s-home-route | tokens |
| HeroBand | `HeroBand.tsx` + `.module.css` | 02-03#s-hero-band | usePrefersReducedMotion (`lib/rg.ts:13`); 5 promo slides |
| CategoryLauncher | `CategoryLauncher.tsx` + `.module.css` | 02-03#s-category-launcher | verticalIcon, ui:Icon |
| StatsBar (always receives absent) | `StatsBar.tsx` + `.module.css` | 02-03#s-stats-bar | ui:Skeleton, formatVnd, formatCount (`lib/format.ts:46`) |
| ProviderGameGrid | `ProviderGameGrid.tsx` + `.module.css` | 02-03#s-provider-game-grid | ui:Tabs, Tile, ComingSoonTile, EmptyState; useGridCols/computeGridFill (`ui/Skeleton/useGridFill.ts:24,73`); useRequireAuth |
| SportsLifestyle | `SportsLifestyle.tsx` + `.module.css` | 02-03#s-sports-lifestyle | ui:Card (promo, interactive, href), ui:Skeleton, SportsMatchCard |
| SportsMatchCard | `SportsMatchCard.tsx` + `.module.css` | 02-03#s-sports-match-card | — |
| DevAuthToggle (non-production) | `DevAuthToggle.tsx` + `.module.css` | 02-03#s-dev-auth-toggle | useAuth.cycleDevState |
| Barrel | `components/home/index.ts` | (implied) | export only live components |

### 2e. Vertical (`components/category/**`)

| Name | Original source | Guide anchor | Depends on |
|---|---|---|---|
| data (resolveVertical, getCategoryPayload) | `components/category/data.ts:45,51` | 02-04#s-vertical-route | getVerticals, getProviders, getGames, getLiveMatch (`lib/mock/index.ts:18`) |
| CategoryPage | `CategoryPage.tsx` + `.module.css` | 02-04#s-category-page | CategoryBanner, LiveOddsBoard, CategoryGrid |
| CategoryBanner (own icon map `resolveIcon`, `KICKERS`) | `CategoryBanner.tsx` + `.module.css` | 02-04#s-category-banner | ui:Icon |
| CategoryGrid | `CategoryGrid.tsx` + `.module.css` | 02-04#s-category-grid | ui:Tabs, Tile, ComingSoonTile, Pill, EmptyState, Icon; useGridFill; useRequireAuth |
| LiveOddsBoard (sports only) | `LiveOddsBoard.tsx` + `.module.css` | 02-04#s-live-odds-board | ui:Card, MoneyValue kind="odds", Skeleton, ErrorState, Icon; router.refresh |

### 2f. Promo

| Name | Original source | Guide anchor | Depends on |
|---|---|---|---|
| PromoHero | `components/promo/PromoHero.tsx` + `.module.css` | 02-05#s-promo-hero | ui:Card promo, Badge gold, Countdown (ui), Icon |
| PromoGrid | `PromoGrid.tsx` + `.module.css` | 02-05#s-promo-grid | ui:Tabs, Tile (aspect "16 / 9", href, badge), Badge, Countdown, EmptyState |
| PromoDetail | `PromoDetail.tsx` + `.module.css` | 02-05#s-promo-detail | ui:Card, Badge, Countdown, Button gold lg fullWidth, Icon; useRequireAuth |

### 2g. Mock datasets and lib read by this track (foundations owns them; listed for contract)

| Dataset / module | Original source | Guide anchor | Shape facts this track depends on |
|---|---|---|---|
| Verticals (9) | `lib/mock/lobby.ts:34-45` | 02-04#s-vertical-route, 02-01#s-app-shell | `{id,label,iconId,href:"/?v={id}"}` |
| Balance | `lib/mock/wallet.ts:20` | 02-01#s-app-shell | live 6 886 000 VND, freshnessMs 20000; DEMO_EMPTY false |
| Jackpot / member day / leaderboard | `lib/mock/lobby.ts:51,81,95` | 02-01#s-right-rail | 28 686 888 000; next 9th/19th/29th 00:00 local; 7 rows, no rank 4 |
| Sports matches (4) | `lib/mock/lobby.ts:121` | 02-03#s-sports-match-card | markets[0] only rendered |
| Live match m1 | via `lib/mock/index.ts:18` | 02-04#s-live-odds-board | freshnessMs 10000 |
| Providers (6) / games (16) | `lib/mock/games.ts:71,75` | 02-03#s-provider-game-grid | ART map `games.ts:18-22` |
| Promos (8) | `lib/mock/promos.ts:41` | 02-05#s-promo-route | endsAt is now-relative (48h, 24h, 11h) |
| Notification feed (34) | `lib/mock/notification-feed.ts:385` | 02-01#s-notification-bell | 6 unread; destination `ctaHref ?? url ?? null` |
| Formatters | `lib/format.ts:28,34,46` | 02-01#s-shell-money | "6.886.000 ₫" (space, then ₫) |
| Reduced-motion hook | `lib/rg.ts:13` | 02-03#s-hero-band | used by HeroBand |

### 2h. Token groups consumed (values in 01-02 tokens, foundations)

Colour: `--shell --canvas --surface --surface-2 --surface-3 --surface-hover --header-bg --tile --border --tint --scrim --progress-track --text-hi --text --text-mid --text-dim --brand-accent --brand-accent-2 --brand-accent-hairline --brand-on-accent --brand-accent-grad --brand-cta --brand-cta-accent --win --loss --error --info --focus-ring`.
Space/layout: `--space-1..8 --gap-xs --gap-sm --gutter --band-gap --frame-w --header-h --nav-h --bottombar-h --rail-w --tile-h --logo-h --tap-min --tap-bar` (unused but defined: `--frame-min --feature-w --provider-w --provider-h --card-pad-sm --brand-logo`).
Radius: `--radius-sm --radius-md --radius-lg --radius-card --radius-pill`. Type: `--t-micro --t-sm --t-body --t-h3 --t-h2 --t-h1 --t-display --t-hero --t-num --t-num-lg --weight-reg --weight-semi --weight-bold --lh-tight --lh-body --brand-font-body --brand-font-head --brand-font-num`. Motion: `--dur-fast --dur-base --dur-slow --ease-standard --ease-entrance`. Z: `--z-content(1) --z-sticky(100) --z-dropdown(1000) --z-modal(2000) --z-toast(3000)`.

### 2i. Dead code (02-07): do not build

AuthCluster, PromoChips, LiveGamesBand, JackpotTicker, LiveMatchCard, VipAisle, PartnerBand, HomeFooter; `.aaLine`, `.featureWide`, `.footerFull/.section/.sectionHead/.sectionTitle/.sectionLink` (Home.module.css), `--rail-overhang`, HeroBand `.slot` on slides, AppShell `rightRail` prop (keep the prop, never pass it). Specs exist in 02-07 for an owner-requested restore only. `NavDropdown .active` is reachable through a prop that is never set, so implement the class but never pass `active`.

---

## 3. Tailwind translation notes

### 3a. Global translation rules (apply to every leaf)

| # | Hazard | Exact-preserving method |
|---|---|---|
| T1 | `reset.css` sets `html{font-size:14px}` (02-01#s-shell-root). Tailwind's default spacing and text scales are rem-based (`p-4` = 14 px here, not 16). | Never use default-scale spacing or text utilities. Read tokens: `p-(--space-4)`, `gap-(--band-gap)`, `text-(length:--t-sm)`. Foundations must either set `--spacing` in px or lint against bare scale utilities. Media queries are unaffected (rem in media queries uses the 16 px initial value). |
| T2 | Ambiguous `(--var)` shorthands. `text-(--x)` resolves to colour; `font-(--x)` resolves to font-family; `bg-(--x)` resolves to colour. | Use type hints: `text-(length:--t-h1)`, `font-[number:var(--weight-semi)]` (or a foundations alias), `bg-(image:…)`. A bad hint emits invalid CSS without any error. |
| T3 | Tailwind v4 `scale-*`, `translate-*` and `rotate-*` write the individual `scale`/`translate`/`rotate` properties, not `transform`. The guide's reduced-motion rules say `transform:none`. | Pick one house style per ADR-SH-01 below. Recommended: arbitrary `hover:[transform:scale(1.05)]` + `motion-reduce:[transform:none]`, so the computed `transform` matches the guide. Inline JSX `transform` (HeroBand track, Overlay swipe) stays inline. |
| T4 | Opacity modifiers (`bg-(--brand-accent)/15`) compile to `color-mix(in oklab, …)`; the source uses `in srgb`. | Use arbitrary values: `bg-[color-mix(in_srgb,var(--brand-accent)_15%,transparent)]`. Affects `.rightNavVip` (15/24 %), `.rowUnread` (6 %), `.trustIcon` (14 %), `.brandArt` (13 %). |
| T5 | Default `transition` is 150 ms `cubic-bezier(0.4,0,0.2,1)`. | Always pair a transition with `duration-(--dur-fast)` (or base/slow) and `ease-(--ease-standard)`. motion.css zeroes these and forces `0.001ms !important` under reduced motion (02-01#s-shell-h intro). |
| T6 | `font: inherit` on buttons and inputs, then `font-size` (NavDropdown, MemberMenu, BottomTabBar, AuthModal, NotificationBell). An arbitrary `[font:inherit]` utility has no guaranteed order against `text-(length:…)`. | Rely on the base reset (Tailwind preflight already sets `font: inherit` on form controls, or the foundations reset does), and emit only the font-size utility. Confirm with foundations (G-04). |
| T7 | Multi-layer gradients (HeroBand `.slot/.slotEmpty`, CategoryBanner `.slot`, PromoHero/PromoDetail `.media`, SportsLifestyle `.lifeOverlay`, AuthModal `.brandArt`). | Do not inline them as arbitrary values (comma and underscore escaping is error-prone). Put each one verbatim in the area partial under `@layer components` (ADR-SH-01). |
| T8 | Keyframes: `panel-in`, `menu-in`, `notif-in` (same bodies, separate names), `scrim-in`, `sheet-up`, `dialog-in`, `bell-swing`, `badge-pulse`, `heroSeg`, `heroSegGrid`. | Verbatim `@keyframes` in the area partial. Use them through `animate-[panel-in_var(--dur-fast)_var(--ease-entrance)]`, or through `--animate-*` in `@theme` if foundations allows it. Keep the names (diffable against the guide). |
| T9 | Breakpoints 640/768/1024 equal Tailwind `sm/md/lg`. 992, 1240, 1424 and 1600 are not defaults. Max queries: `(max-width:767px)` → `max-md:`, `(max-width:1023px)` → `max-lg:`. | Foundations adds `--breakpoint-*` for 992/1240/1424/1600 in px, with every breakpoint in one unit so the variants sort correctly. Fallback: `min-[992px]:`. `max-md` is `width < 48rem`; it differs from `max-width:767px` only at fractional widths, which is acceptable. |
| T10 | Descendant and state selectors: `.trigger:hover .navIcon`, `.item:hover .iconWrap`, `.rightNavVip .rightNavLink`, `.rowRead .rowTitle`, `.navItemOn .navTitle`, `.nodeOn .dot`, `.logout .itemIcon`. | Use `group` + `group-hover:` / `group-[.on]:`, or conditional classes on the child. `.active` selectors become `group-[.active]:` (the `.active` class must still appear on the trigger). |
| T11 | Attribute selectors: `[aria-expanded="true"]`, `[data-suspended]`, `[data-side="away"]`, `.rail > *`, `.list > li`, `.matchSlot > *`, `.cell > *`, `.qrBox svg`, `.closeBtn svg`, `.eye svg`, `.navThumb img`. | `aria-expanded:`, `data-suspended:`, `data-[side=away]:`, `*:` and `[&>li]:`, `[&_svg]:`. |
| T12 | Pseudo-elements and webkit extras: `.rowUnread::before`, `::placeholder`, `.nav::-webkit-scrollbar`, `scrollbar-width:none`, `-webkit-overflow-scrolling`, `-webkit-line-clamp`. | `before:content-[''] before:absolute …`, `placeholder:`, `[&::-webkit-scrollbar]:hidden [scrollbar-width:none]`, `[-webkit-overflow-scrolling:touch]`, `line-clamp-2` (this emits the same four declarations). Tailwind `sr-only` equals `.srOnly` exactly (clip-path inset(50%)). |
| T13 | Inline CSS custom properties: HeroBand `--n --seg-i --seg-dur`; Overlay `--overlay-desktop-max`. | Keep them in the inline `style` and consume them in the partial CSS or in arbitrary values (`max-w-[var(--overlay-desktop-max,420px)]`). |
| T14 | `env(safe-area-inset-bottom, 0px)` in `.frame`, `.bar` and the sheet. | `pb-[calc(var(--bottombar-h)+env(safe-area-inset-bottom,0px)+var(--space-4))]` etc. Write operators with explicit `_` spaces inside `calc`. |
| T15 | Container query in RightRail: `.card{container-type:inline-size}` + `clamp(var(--t-h2),9cqi,var(--t-h1))`. | `@container` on the card, `text-[length:clamp(var(--t-h2),9cqi,var(--t-h1))]!` on the jackpot (see T16). |
| T16 | Override specificity. The source deliberately uses `.card .jackpot` (two classes) to beat Money's `.num-lg`, and passes className overrides into ui:Card (`.lifeCard`, PromoHero `.hero{padding:0}`). In Tailwind, two utilities for the same property resolve by generated CSS order, not by intent. tailwind-merge is a new dependency (rung 6) and needs the owner's approval. | For each override, use the `!` important modifier on the caller side (`p-0!`, `text-[…]!`). Alternatively ui-member exposes a documented `className` precedence contract. List the overrides in G-16. |
| T17 | `position:sticky` header + `overflow-x:hidden` on html and body. Tier-1 overflow is clipped, not scrollable. | Put `overflow-x-hidden` on html and body in the foundations base layer. Do not add `overflow-hidden`, `min-w-0`, `shrink` or `flex-wrap` to Tier-1/Tier-2 (SH-02 reproduction). |

```yaml
tradeoffs:
  - option: A — per-area CSS partial under @layer components for complex art; utilities elsewhere
    yagni_rung: 4   # platform feature: Tailwind v4 @layer/@utility + plain CSS
    pros: [verbatim CSS for gradients/keyframes/HeroBand maths, diffable against guide, one file per leaf (disjoint leases)]
    cons: [two styling idioms per component, partials must be @imported by foundations globals.css]
    blast_radius: "src/styles/components/{shell,auth,home,vertical,promo}.css + 1 @import line each in globals.css"
    risk: low
    cost: "~1 h per area"
  - option: B — everything as arbitrary-value utilities in TSX
    yagni_rung: 4
    pros: [single idiom, no extra CSS files]
    cons: [escaping errors in multi-gradient/calc values, keyframes still need global CSS, unreadable HeroBand var maths]
    blast_radius: "all ~45 TSX files"
    risk: medium (silent invalid CSS)
    cost: "same build time, higher review cost"
  - option: C — keep CSS Modules for complex components
    yagni_rung: 1
    pros: [zero translation]
    cons: [violates D2 (keep Tailwind, not CSS Modules)]
    risk: rejected by owner decision D2
adr:
  id: ADR-SH-01 (proposed; PM/foundations to ratify alongside ADR-002)
  title: Complex shell/home art lives in per-area @layer components partials
  status: proposed
  date: 2026-11-05
  yagni_rung_selected: "4 — rung 1 (CSS Modules) is barred by D2; rungs 2-3 do not express keyframes/gradients"
  context: "Verbatim CSS blocks hold multi-layer gradients, 10 keyframes and CSS-var calc chains (02-03#s-hero-band, 02-01#s-overlay, 02-01#s-notification-bell); precedence rule (00-01#i-how-to-use) ranks verbatim CSS highest."
  decision: "Each area leaf owns one partial src/styles/components/<area>.css with @layer components classes (kebab names, e.g. .hero-rail-fill) + verbatim @keyframes; all other declarations are token-reading utilities; transforms use [transform:…] arbitrary properties."
  consequences:
    - positive: exact computed styles for art; disjoint file ownership
    - negative: foundations must pre-add 5 @import lines; two idioms
    - neutral: token-lint A2 (ADR-002) must scan partials and TSX class strings
  alternatives_considered: [B all-utilities, C CSS Modules]
```

### 3b. Per-item notes ("U" = plain token-reading utilities; "P" = needs the area partial)

| Item | Mapping | Cannot express as plain utilities → method |
|---|---|---|
| ShellChrome `.frame` / `.content` | U: `mx-auto max-w-(--frame-w) min-w-0 flex gap-(--band-gap) items-start pt-(--space-2) px-(--gutter)`; `md:pb-(--space-6)`; `lg:pr-[calc(60px+var(--space-2)*2)]`; `min-[1600px]:pr-(--gutter)` | Base `padding-bottom` calc with env() → arbitrary (T14) |
| Header tiers | U throughout; `md:hidden` (menuBtn), `md:flex` (rightNav), `md:block` (tier2) | VIP cell colour-mix (T4). goPay must use `bg-(--brand-accent)` (background-color only), never a gradient shorthand (02-01#s-header comment). `motion-reduce:[transform:none] motion-reduce:transition-none` |
| NavDropdown | U + `group`; panel `absolute top-full left-0 mt-(--space-1) min-w-[220px] z-(--z-dropdown)` | `panel-in` keyframe (P). `.active` stays a real class |
| MemberMenu | U; `w-[260px] right-0 top-full mt-(--space-2)`; logout `text-(--loss)` | `menu-in` keyframe (P) |
| NotificationBell | U; `max-w-[calc(100vw-2*var(--gutter))]`; `max-md:fixed max-md:top-(--header-h) max-md:inset-x-(--gutter) max-md:w-auto max-md:max-w-none`; list `max-h-[min(70vh,440px)] overflow-y-auto`; rowDetail `line-clamp-2`; rowDelete `mt-[calc(var(--space-2)_-_(var(--tap-min)_-_var(--t-sm))_/_2)]` | `bell-swing`, `badge-pulse` (4500 ms = `calc(var(--dur-slow)*15)`), `notif-in` keyframes (P); `::before` accent edge via `before:`; colour-mix 6 % (T4) |
| CategorySheet | U; `grid grid-cols-4 gap-x-(--space-2) gap-y-(--space-4)`; tile `hover:[transform:scale(1.02)] active:[transform:scale(0.98)]` | — |
| Overlay | U for scrim/panel; `sm:items-center`; `.auto` variants with `sm:`; `max-h-[92vh]` | `scrim-in`, `sheet-up`, `dialog-in` (P). The variant classes `.sheet/.auto/.dialog` should be partial classes because the 640 px switch is variant-specific (keeps SH-08 exact) |
| BottomTabBar | U; `fixed inset-x-0 bottom-0 z-(--z-sticky) md:hidden`; disc `size-[52px] -mt-[22px] border-[3px] border-(--surface) bg-(--brand-cta-accent)` | env() heights (T14) |
| Footer | U; `max-md:flex-col max-md:gap-(--space-5)`; `lg:pr-[calc(60px+var(--space-2)*2)] min-[1600px]:pr-(--gutter)`; partner `h-9 …` → use `h-[36px]` (T1) | Social SVG paths verbatim in TSX |
| QuickActionRail | U; `fixed right-(--space-2) top-1/2 [transform:translateY(-50%)] z-[calc(var(--z-modal)-1)] w-[60px] pointer-events-none *:pointer-events-auto *:w-full max-lg:hidden`; 9 px labels `text-[length:9px]` | QrGlyph raw `#fff` / `#171a21` must stay as SVG attributes (SH-11). Exempt them from lint A2 by explicit allow-list, not by weakening the lint |
| RightRail | U; `hidden min-[1240px]:block min-[1240px]:w-(--rail-w) min-[1240px]:flex-none`; card `@container` | jackpot clamp + `!` (T15/T16) |
| Countdown (shell) | U; seg `px-(--space-2) py-[4px]`, the final value of the duplicated padding (SH-12); `tabular-nums [font-feature-settings:"tnum"_1]` | — |
| Money (shell) | U; size map `num` 16/600, `num-lg` 32/700; win/loss/neutral colours; `data-truthful=""` attribute kept | — |
| AuthModal | U; `sm:flex-row`, `sm:flex` brand zone `w-[280px]`; title `text-(length:--t-h2)` | `.brandArt` radial gradient + colour-mix 13 %, `.trustIcon` colour-mix 14 % (P/T4); brandArtMark `w-[clamp(84px,46%,156px)]` |
| AuthField | U; `focus-within:border-2 focus-within:border-(--focus-ring) focus-within:px-(--space-3) focus-within:py-0`; base `py-px px-[calc(var(--space-3)+1px)]`; error border stays on focus | Order: the error variant must beat `focus-within` (`focus-within:border-(--error)` emitted when `error` is set) |
| Home `.page/.main` | U; `min-[1424px]:grid min-[1424px]:grid-cols-[minmax(0,1fr)_var(--rail-w)]` | — |
| HeroBand | U for viewport, cell, slide, nav, thumbs (`aspect-[5/2] md:aspect-[1556/620]`, `touch-pan-y cursor-grab active:cursor-grabbing select-none`) | Progress row, rail, railFill, node grid, every CSS-var calc, `heroSeg` and `heroSegGrid` → verbatim in the partial (P). This is the highest-risk block |
| CategoryLauncher | U; `grid-cols-5 gap-x-(--space-2) gap-y-(--space-3) md:hidden`; `group-hover:[transform:scale(1.1)]` | — |
| StatsBar | U | — |
| ProviderGameGrid | U; `grid grid-cols-3 auto-rows-(--tile-h) grid-flow-row-dense gap-(--band-gap) md:grid-cols-4 min-[992px]:grid-cols-6 min-[1424px]:grid-cols-8`; feature `col-span-2 md:row-span-2` | useGridCols reads the computed `grid-template-columns`, which works unchanged with utilities |
| SportsLifestyle | U; `aspect-video`, matchSlot flex | `.lifeOverlay` gradient (P) |
| SportsMatchCard | U; `grid-cols-[1fr_auto_1fr]`; `data-[side=away]:flex-row-reverse`; `data-suspended:opacity-60`; CTA `bg-(--brand-accent-grad)` (background shorthand, so a brand gradient applies under emerald) | `text-[length:10px]` cell label |
| DevAuthToggle | U; `fixed top-[calc(var(--header-h)+var(--space-2))] left-(--space-2) z-(--z-toast) border-dashed` | Must keep literal classes `cycle` and `stateLabel` (G-03) |
| CategoryBanner | U; `isolate`, slot `-z-1` | slot gradient (P) |
| CategoryGrid | U (same search-box focus compensation as AuthField; `md:basis-[320px] md:grow-0 md:shrink`) | — |
| LiveOddsBoard | U; `.up` `[transform:rotate(-90deg)]` on the Icon | — |
| PromoHero / PromoDetail | U; `md:flex-row`, media `md:w-[48%] md:aspect-auto`; detail CTA `sticky bottom-(--space-3) md:static md:max-w-[320px]` | `.media` gradient (P); Card padding override `p-0!` (T16) |
| PromoGrid | U; `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` | — |
| Not-found (vertical) | U; `py-(--space-8) px-(--gutter)`, `max-w-[36ch]` | — |

---

## 4. Defects to reproduce

Amber callouts are numbered in document order (SH-01 … SH-22). SH-23 onward are defects stated in the guide's prose, not in a callout. They are reproduced under the same rule (D3, 00-05#i-discrepancies). Every row goes into `docs/rebuild/FIX-LIST.md`.

| ID | Anchor | What it is | How to reproduce | Proposed later fix |
|---|---|---|---|---|
| SH-01 | 02-01#s-shell-root | Layout comments name "SupportWidget" and "CategoryRail" (not found in source). AppShell `rightRail` slot is never passed; home renders RightRail inside its own grid | Build no such components. Keep the `rightRail` prop; no route passes it | Remove the prop or adopt it for home |
| SH-02 | 02-01#s-shell-grid (warn 1) | Header overflow: Tier-1 scrollWidth 623 px at 375 and 1023 px at 768 (bell x=527, avatar x=579 off-screen, clipped by `html{overflow-x:hidden}`). Tier-2 1384 px, clipped at 768/1024/1300. `--frame-min` 1150 is unused | Exact DOM/CSS of 02-01#s-header: logo `flex:none` 205.8×44, nothing shrinks or wraps, no `min-w-0` or overflow on tiers, 9 × 152 px cells with `justify-between`. Validate with the guide's measured boxes table | Collapse the identity cluster on mobile; make Tier-2 scroll or wrap; use `--frame-min` |
| SH-03 | 02-01#s-shell-grid (warn 2) | RightRail shows from 1240 px, but the home 2-column grid starts at 1424 px. At 1300 the 304 px rail stacks below main (x=16, y=2085) | `min-[1240px]:block` on the rail, `min-[1424px]:grid` on `.page` | Align both to one breakpoint |
| SH-04 | 02-01#s-shell-grid (warn 3) | QAR (z 1999, root level) paints over the right edge of MemberMenu (260 px) and the notification panel (360 px) at 1372–1432 px. Header popovers (z 100 context) never cover the BottomTabBar (z 100, later in the DOM) | Keep QAR as a root sibling after AppShell with `z-[calc(var(--z-modal)-1)]`. Keep the header `z-(--z-sticky)` stacking context | Lower QAR under the header's dropdowns, or portal the popovers |
| SH-05 | 02-01#s-header | The comment says 5 utility items; there are 6. "CLB" goes to `/dai-ly` while MemberMenu "Đại lý/CLB" goes to `/cau-lac-bo`. `/assets/logo.svg` is a 2914×623 multicolour wordmark; `--brand-logo` (140×36) is never read | RIGHT_NAV with 6 rows as tabled. Hard-code `/assets/logo.svg` in Header and AuthModal | Unify the club target; read `--brand-logo` |
| SH-06 | 02-01#s-member-menu | "Hỗ trợ" links to `/` (not `/ho-tro`). Three links are redirect stubs (`/hoan-tra`, `/lich-su`, `/bao-mat`). No mobile sheet exists despite the comment | Use the hrefs exactly as tabled; the same dropdown at every width | Point to `/ho-tro` and real destinations |
| SH-07 | 02-01#s-notification-bell | The bell uses the `message` glyph (no bell icon in the set). The mobile fixed panel sits inside the header stacking context, so it can never cover the BottomTabBar | `Icon message 24`; keep the panel inside the header DOM | Add a bell glyph; portal the panel |
| SH-08 | 02-01#s-category-sheet | At 640–767 px the Overlay scrim centres every presentation, so the sheet (top-only radius) floats mid-screen | Scrim `sm:items-center` applies to all variants; `.sheet` keeps `rounded-t-(--radius-card)` | Scope the centring to `.auto/.dialog` |
| SH-09 | 02-01#s-bottom-tab-bar | The comment says member NẠP goes to `/nap-tien`; the code goes to `/vi-tien`. The NẠP disc uses `--brand-cta-accent` #f53f55, the same hue as `--loss` | `router.push("/vi-tien")`; `bg-(--brand-cta-accent)` | Separate the CTA hue from the outcome hue |
| SH-10 | 02-01#s-footer | Comments say 3 columns; there are 4. Two column-4 links have placeholder targets (`/khuyen-mai`, `/tai-khoan`; labels verbatim at the anchor). At 768–1023 the nowrap 16 px links can overflow their ~160 px columns | 4 equal `flex-1` columns, `whitespace-nowrap` links, hrefs as tabled | Real targets; wrap or stack at the md band |
| SH-11 | 02-01#s-quick-action-rail | The TSX says the rail collapses on mobile; the CSS hides it below 1024 px. QR glyph raw hex `#fff`/`#171a21`. Rail jackpot 8.688.888.000 ₫ vs home 28.686.888.000 ₫ for the same "Hũ vàng". "Giải đấu" goes to `/tier` | `max-lg:hidden`; QrGlyph verbatim; `JACKPOT_POOL = 8_688_888_000` (falls back to 8_888_888_000 when it contains a 4); href `/tier` | Tokenise the QR, use one jackpot source, a tournament route |
| SH-12 | 02-01#s-shell-countdown | `.seg` declares padding twice; the second (4px 8px) wins | Emit only `py-[4px] px-(--space-2)` (computed result identical) | Delete the dead declaration |
| SH-13 | 02-02#s-auth-modal | The comment lists 2 modes; there are 3. In the deposit handoff `submitting` never resets (the body unmounts). `skipReturnFocus` stays true until the next `handleClose` (inference: the first close after a later reopen may skip focus return) | Port the state machine as specified, including the stale `skipReturnFocus` | Reset both flags on open |
| SH-14 | 02-02#s-auth-field | The top comment says the focus border is the accent; the code is blue `--focus-ring`. The CategoryGrid comment says the opposite. "Rebuild with blue" | `focus-within:border-(--focus-ring)` | Fix the comments only |
| SH-15 | 02-03#s-home-route | Comments list dead bands (PromoChips, AuthCluster, LiveGamesBand, VipAisle). The loading skeleton draws 5 × 64 px pills (the launcher has 9 × 56 px) and 6 × 120 px blocks (tiles are 205 px; the inline Skeleton height beats `.skelGrid > *`) | `loading.tsx` exactly as listed. Pass `height=120` to Skeleton (inline style), and keep a `*:h-(--tile-h)` rule that loses to it | Match the skeleton to the real bands |
| SH-16 | 02-03#s-hero-band | Comments say 3 slides; there are 5 (reusing 3 JPGs). The comments say a blue segment; the code is gold. `--rail-overhang` is unused. `.slot` is unreachable | 5 slides filtered by `imageSrc.startsWith("/assets/banners/")`; gold fill; declare `--rail-overhang:18px` at ≥768 (unused) | Unique art; drop dead vars |
| SH-17 | 02-03#s-provider-game-grid | Comment column ladder is stale. Tiles are 112.5 px at 1440 (not 164). `.featureWide` is never applied. 234×160 art is upscaled into large tiles | 3/4/6/8 ladder; feature `col-span-2 md:row-span-2`; ART map as source | Higher-resolution art |
| SH-18 | 02-03#s-sports-match-card | The comment says "Live"; the UI says "TRỰC TIẾP". The England flag is an emoji tag sequence (renders black on unsupported platforms) | Use the emoji literals from the data | Use crest images |
| SH-19 | 02-04#s-vertical-route | `/[vertical]` is unreachable from the UI (all nav goes to `/?v={id}`, which home ignores). Member tile goes to `/{id}?game={gameId}` (same page). CategoryBanner icon map disagrees with verticalIcon. `data-vertical` is unused by CSS. All verticals show the same 16 games | Keep hrefs `/?v={id}` in lobby data; keep both icon maps; emit `data-vertical` | Link `/{id}`; per-vertical data |
| SH-20 | 02-04#s-category-grid | The comment says focus moved to the accent; the code is blue. The header says "6/4/3"; the CSS is 3/4/6/8 | Blue focus border; 3/4/6/8 | Comment fix |
| SH-21 | 02-05#s-promo-hero | Hero media is always the gradient placeholder although pr2 has a JPG. The only h1 is the promo title | `.media` gradient span; `h1.title` | Render `imageSrc`; add a page h1 |
| SH-22 | 02-05#s-promo-detail | Below 768 px the sticky CTA (`bottom:12px`) sits under the fixed BottomTabBar until the page end. `title.toLowerCase()` lowercases the whole title in the body text | `sticky bottom-(--space-3) md:static`; JS `toLowerCase()` | Offset by `--bottombar-h`; locale-aware copy |
| SH-23 | 02-01#s-nav-dropdown | Tier-2 triggers are raw `<a>`. A click both toggles the panel and full-page-navigates (this resets mock auth to tiered). The panel holds one link that duplicates the cell. Focus opens the panel | Raw `<a href>` for the trigger (not Link); `megaItem` is a Link | Use Link; drop the single-item panel |
| SH-24 | 02-03#s-hero-band, #s-sports-match-card, #s-provider-game-grid | Hero slides and the "Cược ngay" CTA are raw `<a>` (full load, auth resets). Member tile tap `router.push("/?game={id}")` is a no-op | Raw `<a>` exactly where the guide says "raw"; Link where it says "Link" | Use client navigation to real targets |
| SH-25 | 02-01#s-shell-countdown, 02-04#s-live-odds-board | Under reduced motion the Countdown is frozen at mount. LiveOddsBoard staleness is evaluated once per render (no timer) | No interval when reduced; `isStale` computed in render only | Tick without animation; staleness timer |
| SH-26 | 02-01#s-quick-action-rail | QR/CSKH popovers do not close on Escape or on outside click | Hover/click toggle only, shared `openPanel` state | Add dismiss handlers |
| SH-27 | 02-01#s-member-menu, 02-03#s-hero-band | `role="menu"` without arrow-key roving. Two `role="tablist"` rows share one label with no arrow keys | Tab order only | ARIA keyboard patterns |
| SH-28 | 02-04#s-vertical-route | Vertical loading grid blocks render 160 px (the inline Skeleton height beats `.gridSkel > *`) | As SH-15 with `height=160`, 12 blocks | Match the tile height |
| SH-29 | 02-05#s-promo-detail-route | Unknown promo id → default Next.js 404 (no not-found file). The detail page has no metadata (title "Yaobet") | No `not-found.tsx` in `khuyen-mai/**` and none at the root; no `metadata` export | Promo not-found + metadata |
| SH-30 | 02-01#s-overlay | Swipe-to-dismiss also applies to the centred dialog presentation | Attach touch handlers regardless of presentation | Sheet only |
| SH-31 | 02-03#s-dev-auth-toggle | The comment says a "60px header band"; the header is 72 px (the toggle sits at top 80 px) | `top-[calc(var(--header-h)+var(--space-2))]` | Comment fix |
| SH-32 | 02-05#s-promo-route | `promo.svg` (pr4–pr6) carries raw hex `#1f222e→#25282f`, `#f4b740` outside the palette | Copy the asset byte-for-byte | Re-export the SVG with tokens |
| SH-33 | 02-02#s-auth-state | Every full reload returns to tiered (in-memory state). Raw-anchor navigations (SH-23/24) therefore silently sign a guest back in | `initialState="tiered"` (foundations Providers) | Persist the session |

---

## 5. Gaps and contradictions

| ID | Quote / location | Problem | Recommended resolution |
|---|---|---|---|
| G-01 | 02-01#s-shell-grid: "Do NOT copy this overflow when rebuilding; flag it to the owner." | Contradicts D3 ("Reproduce defects as built") and the PM brief | D3 wins. Reproduce SH-02 and record it in FIX-LIST. Sticky: overridden only by an owner decision |
| G-02 | Guide sources `components/layout/**`, `components/category/**`; PM target `src/components/shell/**`, `src/components/vertical/**` | Directory rename; import paths differ | Accept the PM names (no visual effect). Keep `_internal/` under `shell/`. Lock the mapping in the plan so the ui-member and foundations leaves import the right paths |
| G-03 | 05-01#v-capture: `button[class*="cycle"]`, `[class*="stateLabel"]`; note: "keep the module class named cycle" | Tailwind leaves no module class names. The capture script breaks | Add literal marker classes `cycle` and `stateLabel` (unstyled) on DevAuthToggle; keep the aria-labels and the "Đóng" button verbatim |
| G-04 | 02-01#s-shell-root: "reset.css sets html{font-size:14px} and *{box-sizing:border-box}"; h1–h6 Montserrat 700 | Tailwind preflight differs (img `max-width:100%; height:auto; display:block`, headings `font-size/weight: inherit`, list and button resets). Shell headings (CategorySheet h2, AuthModal h2, Footer) rely on the global heading weight | Foundations decides: preflight off plus the guide's reset, or preflight plus overrides. The shell leaves assume 01-06 semantics |
| G-05 | `html{font-size:14px}` | rem-based Tailwind scale (T1) | Foundations ADR: px `--spacing` or a lint ban; every leaf check greps for bare scale utilities |
| G-06 | Breakpoints used: 640, 768, 992, 1024, 1240, 1424, 1600; max 767, 1023 | Not all are Tailwind defaults | Foundations adds the `@theme` breakpoints `grid6:992px`, `rail:1240px`, `frame:1424px`, `wide:1600px` (names illustrative). Leaves may use `min-[Npx]:` until then |
| G-07 | 02-02#s-auth-state specifies `src/lib/auth/{session,modal,guard,fixtures}` | Spec sits in this track, but the path is `src/lib` (foundations scope) | Foundations lib leaf owns `src/lib/auth/**` to this contract: `useAuth(): {authState, user, signIn(as="tiered"), signOut, cycleDevState}`, `useAuthModal(): {open, mode, resumeIntent, openAuthModal({mode="login", resumeIntent={action:"none"}}), closeAuthModal(), consumeResumeIntent()}`, `useRequireAuth(): {authState, allowed, promptAuth(intent?)}` |
| G-08 | 02-03#s-home-route: "No page-level error boundary ((not found in source))"; 02-05: no not-found file | The current repo `src/app` still has `not-found.tsx`, `error.tsx`, `global-error.tsx` (old code). A root not-found would replace the default Next 404 that SH-29 requires | Delete those three files (L6). The only boundary is `[vertical]/not-found.tsx`. Every unknown single-segment URL resolves through `/[vertical]` and shows the vertical 404. Multi-segment unknown URLs show the default Next 404 |
| G-09 | 02-01#s-shell-grid: Tier-2 "1384px (9 × 152px cells + 16px padding)" while `.tier2Inner` has `padding: 0 16px` on both sides | 9×152+32 = 1400. The measured 1384 (and Tier-1 623 = content end x 623.1) shows the browser excludes the inline-end padding from scrollWidth | Do not hand-tune widths to hit the numbers. Reproduce the CSS; accept the browser's scrollWidth. The gate compares boxes (x/width), not scrollWidth |
| G-10 | 02-01#s-shell-grid measured boxes depend on the identity cluster width 321.3 px | Width depends on Be Vietnam Pro 600 tabular metrics for "6.886.000 ₫" + "Nạp" | The gate runs only after the fonts load (`document.fonts.ready`). Tolerance ±1 px |
| G-11 | 02-01#s-notification-bell: "f01 … 4 min ago" | Are the fixture `at` values now-relative or absolute ISO? Relative-time copy depends on it | Foundations confirms from `notification-feed.ts`. If absolute, screenshots drift ("ngày trước"). Acceptable as time-based per 05-01#v-visual |
| G-12 | 02-01#s-notification-bell: "The eight type strings are marked in source as placeholder copy" | Owner wording is pending | Ship verbatim; FIX-LIST note only |
| G-13 | Shell Money vs ui:MoneyValue; two usePrefersReducedMotion hooks (02-07) | Duplicates on the render path | Build both (each renders). Shell copies stay in `shell/_internal`; HeroBand imports `lib/rg` |
| G-14 | Icon names used here: grid, user, wallet, message, chevronDown, chevronRight, chevronLeft, close, support, cashback, history, referral, shield, trophy, vip, card, gift, ticket, home, promo, deposit, account, chip, slots, sports, fish, rooster, table, fast, live, info, check, lock, phone, mail, eye, eyeOff, search | Must all exist in the ui:Icon set (01-08) | ui-member confirms the list; a missing name is a blocker, not a substitution |
| G-15 | Primitive props used: Button {variant danger/primary/gold, size sm/lg, fullWidth, loading, icon}; Tile {label, caption, imageSrc, fill, onClick, aspect, href, badge}; Card {variant promo, interactive, href, className}; EmptyState {message, title, icon, variant filtered, onReset}; Countdown(ui) {endsAt, zeroLabel}; MoneyValue {kind odds}; Tabs {items, active, onChange, label}; Pill {active, onClick}; Badge {tone gold}; Skeleton {width, height, label, shape block/pill/text} | Contract with ui-member | Cross-check against 01-08 before L5–L8 start |
| G-16 | className overrides into primitives: SportsLifestyle `.lifeCard` on Card; PromoHero/PromoDetail `.hero{padding:0; overflow:hidden; flex column}` on Card; RightRail `.jackpot` on Money | Cascade order in Tailwind is not intent (T16) | Caller-side `!` on conflicting properties; ui-member documents which Card properties are overridable |
| G-17 | 02-01#s-shell-root tree: QuickActionRail is a sibling AFTER AppShell, inside Providers | Mounted by `src/app/layout.tsx` (foundations) | Root layout imports `QuickActionRail`, `AppShell`, `Footer` from `@/components/shell`; the barrel signature is fixed in L3 |
| G-18 | 02-03#s-home-route: root loading is "also used by every route without its own loading file" | Cross-track: member and reward routes without a loading file show the home skeleton | Owned by L6; other tracks must not add a root loading |
| G-19 | 02-03#s-dev-auth-toggle "renders nothing when NODE_ENV === 'production'" | The check location (component vs page) is not stated | Gate inside the component (`process.env.NODE_ENV === "production"` → `null`); acceptance via `next build && next start` grep |
| G-20 | 02-01#s-quick-action-rail: server snapshot "not dismissed" | First paint always shows both cards, then hides after hydration if dismissed | Reproduce (useSyncExternalStore, server snapshot false) |
| G-21 | Routes `/?v=…`, `/?game=…` | Home must ignore `searchParams` | Do not read `searchParams` in `page.tsx` (acceptance: grep) |
| G-22 | 02-01#s-footer partner image 3 `/assets/casino/mg_baccarat_landscape.png` alt "Microgaming" | A casino tile image used as a partner logo (as built) | Reproduce as listed; FIX-LIST (cosmetic) |

---

## 6. Assets

Copy read-only from `Igaming-Agent-1/apps/web/public/` (D4). Sizes measured with `stat`/`sips` on 2026-11-05.

| Public path | Used by | Pixels | Bytes |
|---|---|---|---|
| `/assets/logo.svg` | Header logo (h 44 → ~205.8 w), AuthModal brand (w 132) | 2914×623 | 5 859 |
| `/assets/brand/logo.svg` | `--brand-logo` token only (never read) | 140×36 | 410 |
| `/assets/brand/emerald-logo.svg` | emerald `--brand-logo` (never read) | 140×36 | 412 |
| `/assets/banners/hero-banner-1.jpg` | HeroBand pr1 (eager), pr7; promos pr1, pr7 | 1556×620 | 755 416 |
| `/assets/banners/pc-hero-banner-UCLfinal.jpg` | HeroBand pr2, pr8; QAR promo thumb (64×48 attrs, h 48 cover) | 1556×620 | 1 031 681 |
| `/assets/banners/pc-banner-vpn.jpg` | HeroBand pr3 | 1556×620 | 759 562 |
| `/assets/sports/saba-sports.png` | SportsLifestyle 1; Footer partner 1 | 702×480 | 465 023 |
| `/assets/sports/k-sports.png` | SportsLifestyle 2; Footer partner 2 | 468×320 | 253 155 |
| `/assets/sports/Betgming_football_grid.png` | SportsLifestyle 3 | 702×480 | 526 809 |
| `/assets/sports/e-vitualsports.png` | SportsLifestyle 4 | 702×480 | 451 649 |
| `/assets/casino/mg_baccarat_landscape.png` | games g1/g6/g11/g16; Footer partner 3 | 702×480 | 452 392 |
| `/assets/casino/sunwin_taixiu-live-landscape.png` | games g2/g7/g12 | 234×160 | 68 102 |
| `/assets/casino/mg_roulette_landscape.png` | games g3/g8/g13 | 702×480 | 443 447 |
| `/assets/casino/mg_sicbo_landscape.png` | games g4/g9/g14 | 702×480 | 469 368 |
| `/assets/casino/keno_vietlott.png` | games g5/g10/g15 | 234×160 | 71 825 |
| `/assets/placeholders/promo.svg` | promos pr4–pr6 (PromoGrid tiles) | 343×160 | 640 |
| `/assets/placeholders/tile.svg` | provider `logoSrc` (never rendered) | 240×160 | 635 |
| `src/app/favicon.ico` | favicon (app-dir file, not public) | — | — |

Do not copy the duplicate `* (1).png` files in `/assets/casino/`; nothing references them. Inline SVG (no file): 4 Footer socials, 7 QAR glyphs, QrGlyph.

---

## 7. Proposed leaves

Target layout follows the PM: `src/components/<area>/**`, `src/app/<route>/**`, plus one style partial per area under `src/styles/components/` (ADR-SH-01). Foundations pre-adds the `@import` lines for those partials. Leaves are disjoint. Order: L1 → L2 ∥ L3 → L4 → L5 → L6; L7 ∥ L8 after L1.
Common gate for every leaf: `npx tsc --noEmit` exit 0; `npm run lint` exit 0; `rg --files src -g '*.module.css'` returns nothing for the leaf globs; no bare default-scale utilities (`rg -n '\b(p|px|py|m|mx|my|gap|text)-[0-9]+\b' <globs>` → 0 hits, T1); all transitions read `--dur-*`.
Upstream needs (not in this track): **F-tokens** (tokens, brands, themes, `@theme` breakpoints, reset/preflight decision, motion.css), **F-root** (`src/app/layout.tsx`, `providers.tsx`), **F-lib** (`src/lib/format.ts`, `src/lib/rg.ts`, `src/lib/mock/**`, `src/lib/auth/**`), **UI** (`src/ui/**` incl. `useGridFill`).

### L1 `shell-internal` (8 files)
- allowed_files: `src/components/shell/_internal/{Overlay.tsx,useFocusTrap.ts,usePrefersReducedMotion.ts,Countdown.tsx,Money.tsx,NavDropdown.tsx,verticalIcon.ts}`, `src/styles/components/shell.css`
- Implements: 02-01#s-overlay, #s-shell-countdown, #s-shell-money, #s-nav-dropdown (cell + panel), verticalIcon map; keyframes `scrim-in sheet-up dialog-in panel-in menu-in notif-in bell-swing badge-pulse` (all shell keyframes live in this one partial).
- Needs: F-tokens, F-lib (format), UI (Icon).
- Acceptance: `rg -c '@keyframes (scrim-in|sheet-up|dialog-in|panel-in|menu-in|notif-in|bell-swing|badge-pulse)' src/styles/components/shell.css` = 8; `rg -F 'Đã kết thúc' src/components/shell/_internal/Countdown.tsx`; `rg -F 'role="timer"'`; verticalIcon contains all 9 pairs (`rg -c 'casino|slots|sports|fishing|card|lottery|cockfight|table|arcade'`); Overlay swipe threshold `96` and HOVER_INTENT_MS `120` present.

### L2 `shell-header-nav` (5 files)
- allowed_files: `src/components/shell/{Header.tsx,MemberMenu.tsx,NotificationBell.tsx,BottomTabBar.tsx,CategorySheet.tsx}`
- Implements: 02-01#s-header, #s-member-menu, #s-notification-bell, #s-bottom-tab-bar, #s-category-sheet; defects SH-02, 04–09, 23, 27.
- Needs: L1, F-lib (auth, notification feed), UI (Button, Icon, Skeleton).
- Acceptance (dev server, tiered SSR): `curl -s :3107/ | rg -F -c` for each of `aria-label="Danh mục"`, `aria-label="Tiện ích"`, `aria-label="Ví tiền"`, `Danh mục trò chơi`, `Điều hướng chính`, `Trang chủ`, `Tài khoản`, `Bộ sưu tập`, `Phong cách`, `CLB`, `Nạp` ≥1; `href="/dai-ly"` and `href="/cau-lac-bo"` both present; Tier-2 triggers are `<a href="/?v=` ×9 (raw anchors). Playwright box checks at 375/768/1024/1440 against 02-01#s-shell-grid "Measured boxes" (header height 72/121; logo 205.8×44; identity x 301.8 @375, 1094.7 @1440, ±1 px).

### L3 `shell-frame-footer-rails` (6 files)
- allowed_files: `src/components/shell/{AppShell.tsx,ShellChrome.tsx,Footer.tsx,QuickActionRail.tsx,RightRail.tsx,index.ts}`
- Implements: 02-01#s-app-shell, #s-shell-chrome, #s-footer, #s-quick-action-rail, #s-right-rail, #s-shell-grid frame padding; defects SH-01, 03, 10, 11, 26.
- Needs: L1, L2 (ShellChrome composes them), L4 (AuthModal import; stub-safe), F-lib, UI.
- Contract: `index.ts` exports `AppShell`, `Footer`, `QuickActionRail`, `RightRail`; AppShell props `{children, rightRail?, footer?}`.
- Acceptance: `curl -s :3107/ | rg -F` for `Đối tác`, `Về chúng tôi`, `Tải ứng dụng`, `Thao tác nhanh`, `8.688.888.000 ₫`, `Quay ngay`, `Thông tin trực tiếp`, `Bảng xếp hạng`; `curl -s :3107/cuoc-hop-le | rg -c 'Thao tác nhanh'` = 0 (rail suppressed); `rg -n '#fff|#171a21' src/components/shell` hits only QuickActionRail QrGlyph; sessionStorage keys `yb.rail.promo.dismissed`, `yb.rail.jackpot.dismissed` present.

### L4 `auth-modal` (3 files + partial)
- allowed_files: `src/components/auth/{AuthModal.tsx,AuthField.tsx,index.ts}`, `src/styles/components/auth.css`
- Implements: 02-02#s-auth-modal, #s-auth-field (state machine per 02-02#s-auth-state); defects SH-13, 14.
- Needs: L1 (Overlay), F-lib (auth), UI (Button, Icon).
- Acceptance: grep verbatim in `AuthModal.tsx`: `Nạp nhanh · Rút nhanh · Hoàn trả mỗi ngày`, `Mật khẩu xác nhận không khớp`, `Đã gửi hướng dẫn đặt lại mật khẩu. Vui lòng kiểm tra email hoặc tin nhắn.`, `Mã giới thiệu (tùy chọn)`, timers `600` and `700`, `desktopMaxWidth={720}`; `rg -F 'Hiện mật khẩu' src/components/auth/AuthField.tsx`. Playwright: guest "Đăng ký" → submit → header shows the member chrome (level-0, MemberMenu meta "Tân thủ · YB-668812"); login → "Bạch Kim · YB-880066"; Esc closes and focus returns to the trigger.

### L5 `home-bands` (5 files + partial)
- allowed_files: `src/components/home/{HeroBand.tsx,CategoryLauncher.tsx,StatsBar.tsx,DevAuthToggle.tsx,Home.tsx}`, `src/styles/components/home.css`
- Implements: 02-03#s-hero-band, #s-category-launcher, #s-stats-bar, #s-dev-auth-toggle, home layout (`Home.tsx` = page/main grid wrapper); `heroSeg`/`heroSegGrid` + progress-line verbatim CSS + slot gradient + lifeOverlay gradient in `home.css`; defects SH-03 (page grid), 16, 31.
- Needs: L1 (verticalIcon), F-lib (`rg.ts`), UI.
- Acceptance: `rg -c '@keyframes heroSeg(Grid)?' src/styles/components/home.css` = 2; `rg -n '\bcycle\b' src/components/home/DevAuthToggle.tsx` and `\bstateLabel\b` ≥1 (G-03); `DWELL_MS = 6000`, `SWIPE_THRESHOLD = 48`; prod: `npm run build && npx next start -p 3108 & curl -s :3108/ | rg -c 'chuyển trạng thái đăng nhập'` = 0; dev `= 1`.

### L6 `home-route-grid` (7 files + 3 deletions)
- allowed_files: `src/components/home/{ProviderGameGrid.tsx,SportsLifestyle.tsx,SportsMatchCard.tsx,index.ts}`, `src/app/page.tsx`, `src/app/loading.tsx`; delete `src/app/{not-found.tsx,error.tsx,global-error.tsx}` (G-08, PM to confirm D4 has not already wiped them)
- Implements: 02-03#s-home-route (section order, data fetch), #s-provider-game-grid, #s-sports-lifestyle, #s-sports-match-card, root loading; defects SH-15, 17, 18, 24.
- Needs: L3 (RightRail), L5, UI (Tabs, Tile, ComingSoonTile, EmptyState, Card, Skeleton, useGridFill), F-lib.
- Acceptance: `curl -o /dev/null -w '%{http_code}' :3107/` = 200 and `/?v=casino` = 200 with identical `<main>` markup; `rg -c 'searchParams' src/app/page.tsx` = 0; SSR grep: `Khuyến mãi nổi bật`, `Chọn khuyến mãi`, `Tất cả`, `PG Soft`, `Baccarat Kim Cương`, `Thể thao`, `Kèo bóng đá trực tiếp`, `TRỰC TIẾP`, `Cược ngay`, `href="/?v=sports&amp;m=sm-live-1"`; loading: `rg -F 'Đang tải trang chủ' src/app/loading.tsx`; filler count at 1440 for "Tất cả" = 5 ComingSoonTiles (Playwright); `test ! -e src/app/not-found.tsx`.

### L7 `vertical-route` (10 files + partial)
- allowed_files: `src/components/vertical/{CategoryPage.tsx,CategoryBanner.tsx,CategoryGrid.tsx,LiveOddsBoard.tsx,data.ts,index.ts}`, `src/app/[vertical]/{page.tsx,loading.tsx,not-found.tsx}`, `src/styles/components/vertical.css`
- Implements: 02-04 all five h3; defects SH-19, 20, 25 (odds), 28.
- Needs: L1 (not for icons: CategoryBanner keeps its own map), F-lib, UI (Tabs, Tile, ComingSoonTile, Pill, EmptyState, ErrorState, Card, MoneyValue, Skeleton, Button, Icon, useGridFill).
- Acceptance: for s in casino slots sports fishing card lottery cockfight table arcade → HTTP 200 and `<title>{label} — Yaobet</title>`; `/sports` contains `Trận đấu trực tiếp`, other slugs do not; `/foo` → HTTP 404 and contains `Không tìm thấy hạng mục` and `<title>Không tìm thấy — Yaobet</title>`; grep `Tìm trò chơi`, `Tên A→Z`, `Không tìm thấy trò chơi phù hợp.`; kickers ×9 verbatim in CategoryBanner.tsx; `rg -F 'Đang tải hạng mục' src/app/[vertical]/loading.tsx`.

### L8 `promo-routes` (6 files + partial)
- allowed_files: `src/components/promo/{PromoHero.tsx,PromoGrid.tsx,PromoDetail.tsx,index.ts}`, `src/app/khuyen-mai/page.tsx`, `src/app/khuyen-mai/[id]/page.tsx`, `src/styles/components/promo.css`
- Implements: 02-05 all five h3; defects SH-21, 22, 29, 32.
- Needs: L1 (none directly), F-lib (promos), UI (Card, Badge, Countdown, Tabs, Tile, EmptyState, Button, Icon).
- Acceptance: `/khuyen-mai` 200, `<title>Khuyến mãi — Yaobet</title>`, contains `Tất cả khuyến mãi`, `Xem chi tiết`, `Lọc khuyến mãi theo danh mục`, `Kết thúc sau`; `/khuyen-mai/pr1`…`pr8` → 200 with `<title>Yaobet</title>`; `/khuyen-mai/pr9` → 404 containing Next's default `This page could not be found.`; `test ! -e 'src/app/khuyen-mai/[id]/not-found.tsx'`; detail SSR as tiered contains `Tham gia ngay` and `Thông tin chương trình`; `ls src/app/khuyen-mai/loading.tsx` absent (root loading applies).

Track-wide visual gate (after L1–L8 + upstream): run 05-01#v-capture for `/`, `/casino`, `/slots`, `/sports`, `/khuyen-mai`, `/khuyen-mai/pr1` at m375/d1440 × tiered (+ guest for `/`, `/khuyen-mai`) and diff against the 16 reference shots listed in `shots/` (e.g. `m375-tiered-home.jpg`, `d1440-guest-khuyen-mai.jpg`); check 768/1024 for header, rail and footer breakpoints.

---

## 8. Risks

1. **rem base + utility vocabulary (T1/T2, G-05).** One unhinted `text-(--t-sm)` or a default `p-4` silently renders wrong sizes on every screen. This needs a foundations ADR and a lint before L1 starts.
2. **SH-02 overflow depends on fonts and on no defensive CSS.** Builders tend to add `min-w-0`, `overflow-hidden` or `flex-wrap` and "fix" the reproduction. The numbers also depend on Be Vietnam Pro metrics (G-10) and on the browser's scrollWidth (G-09). Gate on boxes after `document.fonts.ready`.
3. **Preflight vs the guide reset (G-04).** `img{max-width:100%}`, heading `inherit` and button resets change logo, heading and footer rendering. This is undecided upstream.
4. **Cascade order of className overrides on ui primitives (T16, G-16).** Card/Money overrides are order-dependent in Tailwind without tailwind-merge (a new dependency needs the owner's OK). The rule is `!` on the caller side.
5. **Navigation semantics reset mock auth (SH-23/24/33).** Using `Link` where the guide says raw `<a>` (or the reverse) changes whether a guest stays a guest, which breaks the guest screenshot runs and the 05-01#v-states auth checks.
6. **HeroBand progress maths (02-03#s-hero-band).** CSS-var calc chains plus width-animating keyframes. Any utility rewrite risks off-by-pitch fills. Keep it verbatim in `home.css`.
7. **Capture-script coupling (G-03).** Without the literal `cycle`/`stateLabel` classes the whole visual gate cannot set state.
8. **Stale root boundaries in the repo (G-08).** Leftover `not-found.tsx`, `error.tsx` and `global-error.tsx` would mask SH-29 and change 404 behaviour across tracks.

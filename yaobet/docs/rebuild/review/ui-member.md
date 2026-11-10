# Review — track `ui-member` (UI primitives + member area)

Reviewer: `sa` · Date: 2026-11-05 · Binding inputs: `docs/rebuild/REVIEW-BRIEF.md`, `docs/rebuild/DECISIONS.md` (D1 exact, D2 Tailwind, D3 reproduce defects, D4 replace), `sections/00-*`, `sections/05-01-v-checklist.html`.
Anchors are written `file#id` relative to `docs/rebuild/sections/`. Tokens are named, never re-specified (foundations track owns them); lib modules are named by path (foundations track owns them). Header, rails, tab bar, footer, auth modal are the shell/home track's.

## 1. Coverage

| Section file | h3 | Read fully | Components / routes covered |
| --- | --- | --- | --- |
| 01-08-f-ui.html | 21 | yes (4,393 text lines, 18 slices) | barrel `src/ui/index.ts`; Badge, Button, Card, Countdown, Dropdown, EmptyState, ErrorState, Icon (44 glyphs), Modal, MoneyValue + DeltaAmount, Odometer, Pill, Scroller, Sheet, Skeleton, TileSkeleton, useGridFill/useGridCols/computeGridFill, Tabs, Tile, ComingSoonTile |
| 03-01-m-overview.html | 2 | yes | token quick-ref (lookup only), auth model (`useRequireAuth`, fixtures, `DEMO_EMPTY`) |
| 03-02-m-member-layout.html | 4 | yes | `(member)/layout.tsx` + `member.module.css`; MemberSidebar; ProgressBar (inner); LogoutButton / LogoutModal |
| 03-03-m-account.html | 6 | yes | `/tai-khoan` (+ loading), `/bao-mat` redirect, AccountSections, ProfileBasic, SecurityCenter, BankAccounts + CryptoAddresses |
| 03-04-m-wallet.html | 7 | yes | `/vi-tien` (+ loading), WalletTabs, WalletBalanceHeader, DepositPanel, WithdrawPanel, FundTransferPanel, WalletHistory |
| 03-05-m-messages.html | 2 | yes | `/tin-nhan` (+ loading), MessageCenter (+ MessageItem) |
| 03-06-m-referral.html | 7 | yes | `/gioi-thieu` (+ loading), `/dai-ly`, ReferralKpiHeader, InviteTools, CommissionPanel, StepExplainer, AgentTiers |
| 03-07-m-contribution.html | 14 | yes | `/cuoc-hop-le` (+ loading), ContributionTabs, PageIntro, ContributionRoot, RateFilters + SelectFilter, SearchField + foldQuery, ResultStatus, NotFoundResolver, FilterNotice, RateTable, RateCell, Pager, TableFoot, RateTableSkeleton |
| 03-08-m-restricted.html | 5 | yes | `/game-han-che` redirect, RestrictedIntro, RestrictedRoot, RestrictedFilters, RestrictedTable + RestrictedFoot |
| 03-09-m-utility.html | 2 | yes | redirects `/hoan-tra`, `/lich-su` (+ `/bao-mat`, `/game-han-che` cross-ref); stub pattern `/ho-tro`, `/tro-giup`, `/tai-app`, `/phong-cach` |
| 03-10-m-unused.html | 0 (h2 only) | yes | dead code list (ProfileHeader, QuickActions, AccountMenu, LogoutMenuItem, dead CSS, unused data/i18n/tokens) |
| 03-11-m-discrepancies.html | 0 (h2 only) | yes | roll-up of track-M contradictions |
| Context read: 00-01..00-05, 05-01 | — | yes | precedence rule, rebuild order, mock auth, route inventory, discrepancies, acceptance checklist |

Total h3 read: 70. Method note: each HTML file was converted to compact text (tags stripped, `<pre>` blocks kept byte-verbatim) and read in slices of 250 lines or fewer; no slice skipped.

## 2. Inventory

### 2.1 UI primitives (`src/ui`, track F, consumed by every route)

| Name | Original source path | Guide anchor | Depends on |
| --- | --- | --- | --- |
| barrel | `src/ui/index.ts` | 01-08-f-ui.html#f-ui-index | all primitives below |
| Badge | `src/ui/Badge/Badge.tsx` (+ `.module.css`) | 01-08-f-ui.html#f-ui-badge | tokens (surface, text, status, radius, type) |
| Button | `src/ui/Button/Button.tsx` | 01-08-f-ui.html#f-ui-button | Icon; tokens incl. `--brand-cta-grad`, `--brand-cta-accent`, `--surface-disabled`, motion |
| Card | `src/ui/Card/Card.tsx` | 01-08-f-ui.html#f-ui-card | `next/link`; tokens; Icon `[data-icon]` hook |
| Countdown | `src/ui/Countdown/Countdown.tsx` ("use client") | 01-08-f-ui.html#f-ui-countdown | `@/lib/rg` usePrefersReducedMotion |
| Dropdown | `src/ui/Dropdown/Dropdown.tsx` ("use client") | 01-08-f-ui.html#f-ui-dropdown | `--z-dropdown`, motion tokens |
| EmptyState | `src/ui/EmptyState/EmptyState.tsx` | 01-08-f-ui.html#f-ui-empty-state | Icon, Button |
| ErrorState | `src/ui/ErrorState/ErrorState.tsx` ("use client") | 01-08-f-ui.html#f-ui-error-state | Icon, Button |
| Icon (44 glyphs) | `src/ui/Icon/Icon.tsx` | 01-08-f-ui.html#f-ui-icon | none |
| Modal | `src/ui/Modal/Modal.tsx` ("use client") | 01-08-f-ui.html#f-ui-modal | Icon, `@/lib/rg`, `--z-modal`, `--scrim` |
| MoneyValue, DeltaAmount | `src/ui/MoneyValue/MoneyValue.tsx` | 01-08-f-ui.html#f-ui-money-value | `@/lib/format` (formatVnd, formatSignedVnd, formatCount, formatOdds, isStale), `@/lib/types` (isLiveMoney, AnyMoney) |
| Odometer | `src/ui/Odometer/Odometer.tsx` ("use client") | 01-08-f-ui.html#f-ui-odometer | MoneyValue, `@/lib/format`, `@/lib/rg`, `@/lib/types` LiveMoney |
| Pill | `src/ui/Pill/Pill.tsx` | 01-08-f-ui.html#f-ui-pill | Icon |
| Scroller | `src/ui/Scroller/Scroller.tsx` ("use client") | 01-08-f-ui.html#f-ui-scroller | ResizeObserver |
| Sheet (dead, barrel-exported) | `src/ui/Sheet/Sheet.tsx` ("use client") | 01-08-f-ui.html#f-ui-sheet | Icon, `@/lib/rg` |
| Skeleton | `src/ui/Skeleton/Skeleton.tsx` | 01-08-f-ui.html#f-ui-skeleton | tokens |
| TileSkeleton | `src/ui/Skeleton/TileSkeleton.tsx` | 01-08-f-ui.html#f-ui-tile-skeleton | `--tile`, `--tile-h` |
| useGridCols / useGridFill / computeGridFill | `src/ui/Skeleton/useGridFill.ts` ("use client") | 01-08-f-ui.html#f-ui-use-grid-fill | ResizeObserver |
| Tabs | `src/ui/Tabs/Tabs.tsx` ("use client") | 01-08-f-ui.html#f-ui-tabs | Scroller |
| Tile | `src/ui/Tile/Tile.tsx` | 01-08-f-ui.html#f-ui-tile | Card |
| ComingSoonTile | `src/ui/Tile/ComingSoonTile.tsx` | 01-08-f-ui.html#f-ui-coming-soon-tile | Icon |

### 2.2 Routes (member track)

| Route | Original page file (under `src/app`) | Guide anchor | Depends on |
| --- | --- | --- | --- |
| `(member)` group layout | `(member)/layout.tsx`, `(member)/member.module.css` | 03-02-m-member-layout.html#m-member-area | MemberSidebar; getBalance, getAccountSummary, getVipProgress; `--page-bloom`, `--member-canvas` |
| `/tai-khoan` (+ hashes `#ho-so` `#bao-mat` `#ngan-hang` `#vi-tien-ao`) | `(member)/tai-khoan/page.tsx`, `tai-khoan.module.css`, `loading.tsx` | 03-03-m-account.html#m-route-tai-khoan | AccountSections; getSecurityIndex, getVerification, getBankCards, getCryptoAddresses |
| `/bao-mat` → 307 `/tai-khoan` | `bao-mat/page.tsx` | 03-03-m-account.html#m-route-bao-mat | `next/navigation` redirect |
| `/vi-tien` (hashes `#deposit` `#withdraw` `#history` `#transfer`) | `(member)/vi-tien/page.tsx`, `vi-tien.module.css`, `loading.tsx` | 03-04-m-wallet.html#m-route-vi-tien | WalletTabs; getWallet, getBalance, getRecords, getDepositOffer, getBankTransferMemo |
| `/tin-nhan` | `(member)/tin-nhan/page.tsx`, `loading.tsx` | 03-05-m-messages.html#m-route-tin-nhan | MessageCenter; getMessages |
| `/gioi-thieu` | `(member)/gioi-thieu/page.tsx`, `gioi-thieu.module.css`, `loading.tsx` | 03-06-m-referral.html#m-route-gioi-thieu | ReferralKpiHeader, InviteTools, CommissionPanel, StepExplainer; getReferral, getReferralKpi, getCommissions |
| `/dai-ly` | `(member)/dai-ly/page.tsx`, `dai-ly.module.css` (no loading) | 03-06-m-referral.html#m-route-dai-ly | + AgentTiers |
| `/cuoc-hop-le` (`?tab=ty-le` default, `?tab=han-che`) | `cuoc-hop-le/page.tsx` (NOT in `(member)`), `cuoc-hop-le.module.css`, `loading.tsx` | 03-07-m-contribution.html#m-route-cuoc-hop-le | ContributionTabs, PageIntro, ContributionRoot, RestrictedIntro, RestrictedRoot; getContributionRates, getContributionCatalogue, getRestrictedGames; local `formatStamp` (UTC `DD/MM/YYYY HH:mm`, source `app/cuoc-hop-le/page.tsx:41`) |
| `/game-han-che` → 307 `/cuoc-hop-le?tab=han-che` | `game-han-che/page.tsx` | 03-08-m-restricted.html#m-route-game-han-che | redirect |
| `/hoan-tra` → 307 `/khuyen-mai` | `hoan-tra/page.tsx` | 03-09-m-utility.html#m-redirect-routes | redirect |
| `/lich-su` → 307 `/tai-khoan` | `lich-su/page.tsx` | 03-09-m-utility.html#m-redirect-routes | redirect |
| `/ho-tro`, `/tro-giup`, `/tai-app`, `/phong-cach` | `<route>/page.tsx` + shared `src/app/stub.module.css` | 03-09-m-utility.html#m-stub-pattern | stub pattern (also used by `/cau-lac-bo`, track R/S) |

### 2.3 Member components

| Name | Original source path | Guide anchor | Depends on |
| --- | --- | --- | --- |
| MemberSidebar (+ inner ProgressBar) | `src/components/account/MemberSidebar.tsx` (393 l) + `.module.css` (620 l) | 03-02-m-member-layout.html#m-member-sidebar, #m-sidebar-progress | useAuth, useRequireAuth, usePathname, Button, Icon, LogoutButton, formatVnd, formatCount, vi.* |
| LogoutButton + LogoutModal (LogoutMenuItem unused) | `src/components/account/LogoutButton.tsx` | 03-02-m-member-layout.html#m-logout-button | Modal, Button, signOut |
| AccountSections | `src/components/account/AccountSections.tsx` (no CSS) | 03-03-m-account.html#m-account-sections | the four panels; `hashchange` |
| ProfileBasic | `src/components/account/ProfileBasic.tsx` | 03-03-m-account.html#m-profile-basic | Card, Badge, Button, useAuth |
| SecurityCenter (+ SecurityControl, ChangePasswordForm, EnableNotice, Field) | `src/components/account/SecurityCenter.tsx` | 03-03-m-account.html#m-security-center | Card, Badge, Button, Icon |
| BankAccounts, CryptoAddresses (+ NoBackendNotice) | `src/components/account/LinkedAccounts.tsx` | 03-03-m-account.html#m-linked-accounts | Card, Badge, Button, Icon |
| WalletTabs | `src/components/wallet/WalletTabs.tsx` | 03-04-m-wallet.html#m-wallet-tabs | 5 wallet panels, Icon |
| WalletBalanceHeader | `src/components/wallet/WalletBalanceHeader.tsx` | 03-04-m-wallet.html#m-wallet-balance-header | Card vip, Skeleton, ErrorState, MoneyValue, useRequireAuth, router.refresh |
| DepositPanel | `src/components/wallet/DepositPanel.tsx` | 03-04-m-wallet.html#m-deposit-panel | Tabs, Pill, Button, MoneyValue, formatVnd, formatPresetChip, LUCKY_DEPOSIT_PRESETS |
| WithdrawPanel | `src/components/wallet/WithdrawPanel.tsx` | 03-04-m-wallet.html#m-withdraw-panel | Card, Button (primary), MoneyValue |
| FundTransferPanel | `src/components/wallet/FundTransferPanel.tsx` | 03-04-m-wallet.html#m-fund-transfer-panel | EmptyState, Button, MoneyValue, formatVnd |
| WalletHistory | `src/components/wallet/WalletHistory.tsx` | 03-04-m-wallet.html#m-wallet-history | Tabs, EmptyState, DeltaAmount |
| MessageCenter (+ MessageItem) | `src/components/messages/MessageCenter.tsx` | 03-05-m-messages.html#m-message-center | Card, Button, Dropdown, EmptyState, Icon, relativeTime |
| ReferralKpiHeader (+ StatHead) | `src/components/referral/ReferralKpiHeader.tsx` | 03-06-m-referral.html#m-referral-kpi | Card, ErrorState, Skeleton, MoneyValue, formatCount |
| InviteTools | `src/components/referral/InviteTools.tsx` | 03-06-m-referral.html#m-invite-tools | Card, Button, `next/image`, useRequireAuth |
| CommissionPanel | `src/components/referral/CommissionPanel.tsx` | 03-06-m-referral.html#m-commission-panel | Card, EmptyState, Button, MoneyValue |
| StepExplainer (server) | `src/components/referral/StepExplainer.tsx` | 03-06-m-referral.html#m-step-explainer | Icon |
| AgentTiers (server) | `src/components/referral/AgentTiers.tsx` | 03-06-m-referral.html#m-agent-tiers | Card vip, Badge, Icon |
| ContributionTabs | `src/components/contribution/ContributionTabs.tsx` | 03-07-m-contribution.html#m-contribution-tabs | Tabs, useSearchParams, router.replace |
| PageIntro (server) | `src/components/contribution/PageIntro.tsx` | 03-07-m-contribution.html#m-page-intro | `next/link`, vi.contribution |
| ContributionRoot | `src/components/contribution/ContributionRoot.tsx` | 03-07-m-contribution.html#m-contribution-root | RateFilters, ResultStatus, FilterNotice, NotFoundResolver, RateTable; lib/mock/contribution |
| RateFilters + SelectFilter | `src/components/contribution/RateFilters.tsx` | 03-07-m-contribution.html#m-rate-filters | SearchField, Dropdown (controlled), Pill, Icon |
| SearchField + foldQuery | `src/components/contribution/SearchField.tsx` | 03-07-m-contribution.html#m-search-field | Icon |
| ResultStatus | `src/components/contribution/ResultStatus.tsx` | 03-07-m-contribution.html#m-result-status | — |
| NotFoundResolver | `src/components/contribution/NotFoundResolver.tsx` | 03-07-m-contribution.html#m-not-found-resolver | Pill, `next/link`, Icon |
| FilterNotice (reused by restricted) | `src/components/contribution/FilterNotice.tsx` | 03-07-m-contribution.html#m-filter-notice | Icon, Button |
| RateTable | `src/components/contribution/RateTable.tsx` | 03-07-m-contribution.html#m-rate-table | Scroller (freezeFirstColumn), RateCell, Pager, TableFoot |
| RateCell | `src/components/contribution/RateCell.tsx` | 03-07-m-contribution.html#m-rate-cell | formatPercent, resolveTierRates, coalesceAdjacentEqual (lib) |
| Pager | `src/components/contribution/Pager.tsx` | 03-07-m-contribution.html#m-pager | Icon; local `pageTokens` |
| TableFoot | `src/components/contribution/TableFoot.tsx` | 03-07-m-contribution.html#m-table-foot | — |
| RateTableSkeleton | `src/components/contribution/RateTableSkeleton.tsx` | 03-07-m-contribution.html#m-rate-table-skeleton | Skeleton |
| RestrictedIntro (server) | `src/components/restricted/RestrictedIntro.tsx` | 03-08-m-restricted.html#m-restricted-intro | vi.restricted |
| RestrictedRoot | `src/components/restricted/RestrictedRoot.tsx` | 03-08-m-restricted.html#m-restricted-root | RestrictedFilters, FilterNotice, RestrictedTable |
| RestrictedFilters (own SelectFilter copy) | `src/components/restricted/RestrictedFilters.tsx` | 03-08-m-restricted.html#m-restricted-filters | SearchField, Dropdown |
| RestrictedTable | `src/components/restricted/RestrictedTable.tsx` | 03-08-m-restricted.html#m-restricted-table | Scroller, RateCell, Pager, RestrictedFoot |
| RestrictedFoot | `src/components/restricted/RestrictedFoot.tsx` (separate file, confirmed in source tree) | 03-08-m-restricted.html#m-restricted-table | — |
| Stub page pattern | `src/app/stub.module.css` + per-route page | 03-09-m-utility.html#m-stub-pattern | — |
| Barrels (exist in source, not specified by guide) | `src/components/{account,wallet,messages,referral,contribution,restricted}/index.ts` | (not found in guide; source tree) | — |
| Dead, do not build unless PM decides (see G-10) | ProfileHeader, QuickActions, AccountMenu, LogoutMenuItem | 03-10-m-unused.html#m-unused | — |

### 2.4 Hooks, lib modules, mock datasets, token groups (referenced, owned by foundations)

| Name | Path | Guide anchor | Used by |
| --- | --- | --- | --- |
| MockAuthProvider, useAuth, signOut | `src/lib/auth/session.tsx` | 01-09-f-lib.html#f-lib-auth, 03-01-m-overview.html#m-auth-model | every member island |
| useRequireAuth `{authState, allowed, promptAuth(resumeIntent?)}` | `src/lib/auth/guard.ts` | 03-01-m-overview.html#m-auth-model | sidebar, wallet, referral, messages |
| LEVEL_0_USER, TIERED_USER | `src/lib/auth/fixtures.ts` | 03-01-m-overview.html#m-auth-model | sidebar, ProfileBasic |
| openAuthModal (called by promptAuth) | shell/auth track | 02-02-s-auth-h.html | guest CTAs |
| usePrefersReducedMotion | `src/lib/rg.ts` | 01-09-f-lib.html#f-lib-rg | Countdown, Modal, Sheet, Odometer |
| formatVnd, formatSignedVnd, formatCount, formatOdds, formatPercent, formatPresetChip, isStale, relativeTime | `src/lib/format.ts` | 01-09-f-lib.html#f-lib-format | MoneyValue, sidebar, wallet, messages, RateCell |
| LiveMoney, AnyMoney, isLiveMoney, Envelope | `src/lib/types.ts` | 01-09-f-lib.html#f-lib-types | MoneyValue, Odometer, wallet |
| vi.* strings | `src/lib/i18n.ts` | 01-09-f-lib.html#f-lib-i18n | many (most member strings are hard-coded, see UIM-24) |
| mock barrel + `simulateFetch`, `DEMO_EMPTY=false` | `src/lib/mock/index.ts`, `src/lib/mock/helpers.ts` | 01-09-f-lib.html#f-lib-mock | all pages |
| getBalance, getWallet | `src/lib/mock/wallet.ts` | 01-09-f-lib.html#f-lib-mock | layout, /vi-tien |
| getAccountSummary, getSecurityIndex, getVerification, getBankCards, getCryptoAddresses | `src/lib/mock/profile.ts` | 01-09-f-lib.html#f-lib-mock | layout, /tai-khoan |
| getVipProgress | `src/lib/mock` barrel | 01-09-f-lib.html#f-lib-mock | layout (sidebar progress) |
| getRecords | `src/lib/mock/records.ts` | 01-09-f-lib.html#f-lib-mock | /vi-tien history |
| getDepositOffer, getBankTransferMemo | `src/lib/mock/deposit.ts` | 01-09-f-lib.html#f-lib-mock | /vi-tien |
| getMessages | `src/lib/mock/messages.ts` | 01-09-f-lib.html#f-lib-mock | /tin-nhan |
| getReferral, getReferralKpi, getCommissions | `src/lib/mock/referral.ts` | 01-09-f-lib.html#f-lib-mock | /gioi-thieu, /dai-ly |
| getContributionRates, getContributionCatalogue, getRestrictedGames, BONUS_RESTRICTED_IDS, rateBucket, resolveTierRates, coalesceAdjacentEqual | `src/lib/mock/contribution.ts` (548 l, verbatim in lib section) | 01-09-f-lib.html#f-lib-mock | /cuoc-hop-le |
| LUCKY_DEPOSIT_PRESETS | `src/lib/format.ts` (per lib section) | 01-09-f-lib.html#f-lib-format | DepositPanel |
| Token groups (by name only) | `src/styles/tokens.css` | 01-02-f-tokens.html, quick-ref 03-01-m-overview.html#m-token-quickref | surfaces (`--canvas` `--shell` `--surface*` `--tile` `--tint`), text (`--text*`), brand (`--brand-*`), status (`--win` `--loss` `--error` `--info` `--caution` `--green` `--on-caution`), focus (`--focus-ring`), progress (`--progress-*`), composite gradients (`--page-bloom` `--header-card-grad` `--wallet-sheen-grad` `--card-sheen-grad`), type (`--t-*` `--lh-*` `--weight-*`), space (`--space-1..8` `--gap*` `--gutter` `--card-pad*`), radius (`--radius-*`), sizing (`--tap-min` `--tap-bar` `--rail-w` `--header-h` `--nav-h` `--bottombar-h` `--tile-h`), motion (`--dur-*` `--ease-*`), z (`--z-content` `--z-sticky` `--z-dropdown` `--z-modal`), `--scrim`, `--qr-surface`, `--member-canvas`, `--balance-text` |

## 3. Tailwind translation notes

### 3.1 Verified Tailwind 4.3.4 behaviours that silently break exactness

Each was checked against the installed `node_modules/tailwindcss` (version 4.3.4).

| # | Tailwind default | Guide CSS | Exact-preserving method |
| --- | --- | --- | --- |
| T1 | `hover:` emits `@media (hover: hover) { &:hover }` (found in `dist/lib.js`) | Many hovers are ungated (Button colour shift, Modal/Sheet close, sidebar tiles, wallet tabs, table rows); others gated `(hover: hover) and (pointer: fine)` | Define custom variants (foundations entry CSS, see 3.4): `hover-any` = `&:hover`; `hover-fine` = `@media (hover: hover) and (pointer: fine) { &:hover }`; `touch` = `@media (hover: none)`. Never use bare `hover:`. |
| T2 | `scale-105`, `rotate-180`, `-translate-x-1/2` write the individual `scale` / `rotate` / `translate` properties (`"scale","var(--tw-scale-x) var(--tw-scale-y)"`) | Guide animates and resets `transform` (`transition: transform …`, reduced-motion `transform: none`, keyframes `pulseDot` mixing translate + scale) | Always write `[transform:scale(1.05)]` / `[transform:rotate(180deg)]` / `[transform:translate(-50%,-50%)]`. Otherwise transitions do not run, `transform:none` resets nothing, and pulse keyframes double-translate. |
| T3 | `transition-*` utilities set Tailwind's own property lists and default `150ms cubic-bezier(0.4,0,0.2,1)` (`--default-transition-duration: 150ms`) | Exact lists, e.g. `transform var(--dur-fast) var(--ease-standard), border-color …, background-color …` | Arbitrary `[transition:transform_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),…]`. |
| T4 | `bg-(--x)` emits `background-color: var(--x)` | `background: var(--brand-cta-grad)`, `var(--brand-accent-grad)`, `var(--page-bloom)`, `var(--header-card-grad)`, `var(--*-sheen-grad)` | Use `[background:var(--x)]`. Gradient tokens (emerald brand) and multi-layer composites with a trailing colour layer are lost with `bg-(--x)`. `.fill` needs both `[background:var(--progress-fill)]` and `bg-(image:--progress-fill-grad)` in that order. |
| T5 | Opacity modifiers (`bg-x/8`) emit `color-mix(in oklab, … , transparent)`; gradient utilities interpolate `in oklab` | `color-mix(in srgb, var(--brand-accent) 8%, var(--surface))`; `linear-gradient(90deg, var(--canvas), transparent)` | Arbitrary values only: `bg-[color-mix(in_srgb,var(--brand-accent)_8%,var(--surface))]`, `[background:linear-gradient(90deg,var(--canvas),transparent)]`. No `/NN` modifiers, no `bg-linear-*`. |
| T6 | Breakpoints are rem (`--breakpoint-md: 48rem`); `max-*`/`max-[Npx]` emit `width < N` | `min-width: 768px` (px), `max-width: 420px`, `max-width: 639px`, `max-width: 900px` (inclusive) | Use px: `min-[768px]:`, `min-[880px]:`, `min-[992px]:`, `min-[1024px]:`, `min-[640px]:`. For max: arbitrary `[@media(max-width:420px)]:` (or custom variants `max-420`, `max-639`, `max-900`). `max-[420px]:` is off by one at exactly 420 / 900 px. |
| T7 | `sr-only` uses `clip-path: inset(50%)` | module `.srOnly` uses `clip: rect(0, 0, 0, 0)` | Visually identical; for byte parity add `[clip:rect(0,0,0,0)]`. Acceptable either way (flag only). |
| T8 | `line-clamp-2` sets overflow/display/-webkit-box-orient/-webkit-line-clamp only | Tile `.name` also `line-clamp: 2; text-overflow: ellipsis; overflow-wrap: anywhere` and fixed `height: calc(var(--t-sm) * var(--lh-tight) * 2)` | `line-clamp-2 [line-clamp:2] text-ellipsis wrap-anywhere h-[calc(var(--t-sm)*var(--lh-tight)*2)]`. |
| T9 | Keyframes are global; CSS Modules scoped them (`spin`, `fade`, `pop`, `slideUp`, `drop`, `sweep`, `tileSweep`, `pulseDot`, `progressShimmer`) | Same names reused per module; `slideUp` (Modal) and `pulseDot`/`progressShimmer` (sidebar) are declared inside `@media` | Declare once, prefixed, in plain CSS: `ui-btn-spin`, `ui-modal-pop`, `ui-fade`, `ui-slide-up`, `ui-dropdown-drop`, `ui-skeleton-sweep`, `ui-tile-sweep`, `member-pulse-dot`, `member-progress-shimmer`. Apply via `animate-[ui-modal-pop_var(--dur-base)_var(--ease-entrance)]`, `max-sm:animate-[ui-slide-up_…]`, `motion-safe:animate-[member-pulse-dot_1.6s_var(--ease-standard)_infinite_alternate]`. |
| T10 | Utilities have equal specificity; conflicting utilities resolve by Tailwind's internal sort, not class order | Consumers override primitive styles through `className` and rely on CSS-Module load order (guide: ".panel (on Card) … overrides Card default 16px — inference: module CSS loads after primitive CSS"); primitive internals rely on selector specificity (`.pill:hover:not(:disabled)` 0,3,0 beats `.active` 0,1,0) | ADR-UIM-001 below. |
| T11 | Preflight resets `button`, `img`, `svg` (`display:block; vertical-align:middle`) in `@layer base` | Icon `display:inline-block; vertical-align:-0.125em`, plain `<img>` in Tile | Fine if primitive rules live in `@layer components` or utilities (both beat base). Foundations must state whether Preflight is imported; flag to foundations. |

### 3.2 Decision: how primitives keep CSS-Module cascade semantics

```yaml
tradeoffs:
  - option: A — layered primitives (`@layer components` in src/ui/ui.css) + utilities everywhere else
    yagni_rung: 4   # platform feature: CSS cascade layers, already how Tailwind v4 orders base < components < utilities
    pros:
      - consumer className utilities always beat primitive rules, matching "className appended last" in the guide
      - primitive selectors can be copied from the verbatim CSS blocks with renames only (`.btn` -> `.ui-btn`), so specificity games (`:hover:not(:disabled)` over `.active`, `.btn:disabled` over `.gold`) and media gating are byte-faithful
      - zero new dependencies; lint A2 (ADR-002) can scan ui.css like any CSS
    cons:
      - primitive roots are plain CSS rather than utilities (D2 allows `@layer components`)
      - entry CSS must `@import` src/ui/ui.css (cross-leaf contract with foundations)
    blast_radius: src/ui/** only; every consumer stays utility-only
    risk: low — failure mode is a forgotten import (caught by visual check and the grep gate)
    cost: same as utilities; about 600 lines of CSS ported verbatim
  - option: B — utilities everywhere + tailwind-merge
    yagni_rung: 6   # vetted library, needs the user's OK
    pros: [no hand-written CSS, last-class-wins merging]
    cons:
      - new dependency (needs the user's approval)
      - does not reproduce in-primitive specificity (hover vs active) or ungated hover without custom variants anyway
      - runtime cost on every render of every primitive
    blast_radius: src/ui/** and every consumer that passes className
    risk: medium — arbitrary-property merging edge cases, silent class drops
    cost: low build, ongoing maintenance
  - option: C — utilities everywhere, consumers override with `!` (important)
    yagni_rung: 1
    pros: [no dependency, no CSS file]
    cons:
      - every override site must know it conflicts; important also beats primitive :hover/:focus states, which the original CSS never did
      - impossible to grep-verify completeness
    blast_radius: all consumers
    risk: high — wrong colours/padding with no error
    cost: low upfront, high debugging
adr:
  id: ADR-UIM-001
  title: Primitive root/variant/state rules live in `@layer components`; consumers and inner parts use utilities
  status: proposed
  date: 2026-11-05
  yagni_rung_selected: "4 — rung 1-3 cannot reproduce load-order overrides; rung 6 adds a dependency and still needs custom variants"
  context: "Consumer overrides are load-bearing: ProfileBasic/SecurityCenter/MessageCenter `.panel` padding 24px over Card 16px (03-03-m-account.html#m-profile-basic), AgentTiers `.tier` padding 16px over Card vip 24px (03-06-m-referral.html#m-agent-tiers), MessageCenter `.markAll`/`.deleteAll` colour over Button ghost (03-05-m-messages.html#m-message-center), ErrorState `.icon` colour over Icon `color: inherit` (01-08-f-ui.html#f-ui-error-state), WalletBalanceHeader `.errorState` over ErrorState. Tailwind utilities cannot guarantee these (T10)."
  decision: "src/ui/ui.css holds `@layer components { .ui-<primitive>… }` ported from each verbatim CSS block (class names prefixed, keyframes prefixed per T9). Primitives' TSX joins `ui-*` classes exactly as the original joined module classes, consumer `className` last. Sub-elements nobody overrides may use utilities. Consumers (src/components/**, src/app/**) use utilities and arbitrary values only, applying T1-T9."
  consequences:
    - positive: "cascade parity with CSS Modules by construction; verbatim CSS is diff-able against the guide"
    - negative: "one cross-leaf import contract (entry CSS -> src/ui/ui.css)"
    - neutral: "lint A2 must include src/ui/ui.css in its scan set"
  alternatives_considered: [B tailwind-merge, C important overrides]
```

### 3.3 Per-item notes

Notation: U = plain utilities + token arbitrary values; L = `@layer components` (ADR-UIM-001); K = keyframes in plain CSS; P = pseudo-element; M = media-gated custom variant (T1/T6).

| Item | Method | Notes that cannot be guessed |
| --- | --- | --- |
| Badge | L | `.subtle` border `1px solid color-mix(in srgb, currentColor 35%, transparent)` verbatim; subtle 2px taller than solid (no border on solid). |
| Button | L + K + M | Hover scale only under `(hover: hover) and (pointer: fine)`; colour shifts ungated; variant `:active` rules after the hover rule; `.btn:disabled` (0,2,0) beats variant backgrounds; `[data-loading]` cursor; spinner `ui-btn-spin 700ms linear infinite`, reduced-motion 1400ms; `.primary` must use `background:` shorthand (T4) so emerald gradient reproduces; hover `color-mix(... var(--brand-cta-grad) 80% ...)` becomes invalid under emerald, as in the original. |
| Card | L | `[data-icon]` descendant scale 1.1 on fine hover; press `scale(.98)` only `@media (hover: none)`; reduced motion keeps only border-color transition. |
| Countdown | U | Plain spans; `min-w-[2ch]`, `[font-feature-settings:"tnum"_1]`; JS behaviour verbatim. |
| Dropdown | L + K | `.triggerWrap{display:contents}`; panel `top: calc(100% + var(--space-2))`, `max-width: min(90vw, 360px)`; `ui-dropdown-drop`. |
| EmptyState / ErrorState | L | Root overridable (WalletBalanceHeader passes `align-items:flex-start; text-align:left`). |
| Icon | L (root only) | 44 `<path>` entries byte-verbatim (count gate in L1); `account` and `user` identical; `.icon{color:inherit}` must sit below consumer utilities. |
| Modal | L + K + M | `slideUp` declared inside `@media (max-width: 639px)` in source: declare `ui-slide-up` globally and apply only under the media query; `.root[data-reduced] .panel` selectors; close button hover ungated; no portal; body overflow lock. |
| MoneyValue / DeltaAmount | L | Odometer and consumers recolour it (`.balanceValue`, `.heldValue`, `.commissionVal`, `.balance`). |
| Odometer | L | JS tween 700ms easeOutCubic verbatim. |
| Pill | L + M | Hover rule (0,3,0) beats `.active`: an active pill under hover shows `--text-hi` text and `--brand-accent-hairline` border on the 12% film (derived from verbatim CSS, see G-2). |
| Scroller | L + P | `::before/::after` fades with `linear-gradient(90deg/270deg, var(--canvas), transparent)` (T5); `.rail::-webkit-scrollbar{display:none}` + `scrollbar-width:none`; `.snap > *` and `.freeze > :first-child` child selectors. |
| Sheet | L + K | Built though dead (barrel exports it); swipe handlers stay non-hooks after the early return. |
| Skeleton / TileSkeleton | L + K | Gradient `linear-gradient(100deg, …30%, …50%, …70%)`, `background-size: 200% 100%`, `ui-skeleton-sweep` with `animation-duration:1400ms` override; inline width/height style stays inline. |
| Tabs | L + M | `.tab:hover:not(:disabled)` beats `.active` colour (hovered active tab shows `--text-hi`); focus offset `-2px` + radius 4px. |
| Tile / ComingSoonTile | L (root) + U | Scrim `linear-gradient(180deg, transparent 0%, var(--scrim) 45%, var(--shell) 100%)` (T5); T8 for `.name`; plain `<img loading="lazy">`. |
| (member) layout | U | `.area` `[background:var(--page-bloom)]` (T4); `min-[992px]:flex-row min-[992px]:items-start min-[992px]:gap-(--gap)`; `.column` `min-[992px]:[flex:1_1_0]`. |
| MemberSidebar | U + K + P-free | `.tierTag`/`.nextTag` `[clip-path:polygon(0_0,100%_0,100%_100%,0_100%,6px_50%)]`; hero/wallet/action cards `isolate` + sheen span `-z-1`; sticky `top:calc(var(--header-h)+var(--nav-h)+var(--space-4))` at `min-[992px]`; tile/action hovers ungated (T1 `hover-any`); `.dot` `left` inline style, `[transform:translate(-50%,-50%)]` and pulse keyframes on `transform` (T2); keyframes only under `motion-safe:`. |
| LogoutButton | U | Passes `className` to Button (margin-top) and footer actions to Modal. |
| AccountSections | U | No CSS. |
| ProfileBasic / SecurityCenter / LinkedAccounts | U | Card padding overrides (ADR-UIM-001); `.chevOpen` transition exists only while open (closing snaps); `.controlHead:hover .controlIcon` → parent `group` + `[.group:hover_&]:[transform:scale(1.1)]` (not `group-hover:`, which is media-gated); `placeholder:` colour; input focus = outline + border-color. |
| WalletTabs | U + M | `.tab:hover:not(.active)` → apply colour/bg only on the non-active branch; `[@media(max-width:420px)]:px-2 …:text-(length:--t-sm)`; `[background:var(--brand-accent-grad)]` on active. |
| Deposit / Withdraw / FundTransfer / History | U | `aria-[invalid=true]:border-(--error)`; `.qrSlot` dashed border; `select` `appearance-none` with no chevron; FundTransfer `.route .field` at `min-[768px]` → put `min-[768px]:[flex:1_1_0]` on each field. |
| MessageCenter | U + P | `.itemUnread::before` 3px edge via `before:` utilities with `before:content-['']`; `.filterTrigger svg` → `[&_svg]:` arbitrary variant; ghost Button colour override (ADR-UIM-001). |
| Referral components | U | `.topRow > *{min-width:0}` → `*:min-w-0`; StepExplainer tones and 46px watermark literal; `aspect-[16/9]`. |
| Contribution / Restricted | U | Sticky `th` (`border-collapse: separate`); `tbody tr:last-child` → `[tr:last-child>&]:border-b-0`; row hover `min-[1024px]:[tr:hover>&]:bg-(--surface-hover)` (not `group-hover:`); `[@media(max-width:900px)]:` dense padding; `.error .icon` → `[.error_&]:text-(--caution)`; `.control:focus-within` 2px border + `p-0`; corner `z-[calc(var(--z-sticky)+1)]`; SearchField `<noscript><style>` must target stable hooks (G-5). |
| Stub pages | U | One shared StubPage component replaces `stub.module.css` (G-15). |

### 3.4 Cross-leaf contract with foundations (needs, not owned here)

1. Entry CSS `@import "../ui/ui.css";` (path relative to the entry file) and member keyframes file(s) listed in section 7.
2. Custom variants (exact definitions): `@custom-variant hover-any (&:hover);` · `@custom-variant hover-fine { @media (hover: hover) and (pointer: fine) { &:hover { @slot; } } }` · `@custom-variant touch (@media (hover: none));` · `@custom-variant max-420 (@media (max-width: 420px));` · `@custom-variant max-639 (@media (max-width: 639px));` · `@custom-variant max-900 (@media (max-width: 900px));`. Fallback if foundations declines: arbitrary variants inline (same CSS output).
3. Token names exactly as listed in 2.4 exist as CSS custom properties (not only as `@theme` keys), because every rule here reads `var(--…)`.

## 4. Defects to reproduce

All IDs are `UIM-nn`. "Reproduce" = build exactly as stated. "Later fix" goes to `docs/rebuild/FIX-LIST.md` (D3).

| ID | Anchor | Defect | Reproduce | Proposed later fix |
| --- | --- | --- | --- | --- |
| UIM-01 | 01-08-f-ui.html#f-ui-badge | Literal `padding: 2px …`; subtle vs solid differ 2px in height | Keep 2px literal; no border on solid | Token for 2px; transparent 1px border on solid |
| UIM-02 | #f-ui-button | Literals `52px`, spinner `1.1em/2px/700ms`; under emerald `.primary` reads a gradient | `background: var(--brand-cta-grad)` shorthand | Read a solid CTA token |
| UIM-03 | #f-ui-card | `onClick` without `interactive`/`href` silently dropped | Keep the three-branch render | Warn or render button when onClick set |
| UIM-04 | #f-ui-countdown | `useState(() => Date.now())` hydration drift; reduced motion freezes time | Verbatim hook code | Server-passed now / suppressHydrationWarning |
| UIM-05 | #f-ui-dropdown | Literals 200px / `min(90vw,360px)` / -4px; controlled mode needs parent update | Verbatim | Tokens; document controlled contract |
| UIM-06 | #f-ui-icon | `account` == `user` path; `trash` unused; vertical iconIds not Icon names | Keep all 44 entries | Dedupe; drop trash |
| UIM-07 | #f-ui-modal | Literal sizes/90vh/639px/pop offsets; no portal (transformed ancestor traps fixed overlay) | Render in place | Portal to body |
| UIM-08 | #f-ui-money-value | "gold on large figures" comment with no gold class; `balance`/`countdown` kinds format as money | Verbatim | Remove kinds or implement |
| UIM-09 | #f-ui-odometer | Tween 700ms hard-coded in JS | `const dur = 700` | Motion token |
| UIM-10 | #f-ui-pill | Hover border equals rest border (invisible); comment 8% vs code 12% | 12% film, hairline hover | Distinct hover border |
| UIM-11 | #f-ui-scroller | Fades hard-coded to `--canvas` (band on cards); `.freeze` paints `#212121` | Verbatim | Fade from a surface var |
| UIM-12 | #f-ui-sheet | Dead primitive; literals 36/4/80/90vh | Build and export, no consumer | Delete or adopt |
| UIM-13 | #f-ui-skeleton | Only gradient fill on a primitive; `1400ms` overrides token; comments cite `#262833` | Verbatim | Token duration; fix comments |
| UIM-14 | #f-ui-use-grid-fill | Track count by `split(" ")` | Verbatim | Parse robustly |
| UIM-15 | #f-ui-tabs | Global ids `tab-{id}` / `panel-{id}` | Verbatim | Namespace with useId |
| UIM-16 | #f-ui-tile | No-image tile renders label twice; stale comments; `gap: 2px` | Verbatim | Single label |
| UIM-17 | #f-ui-coming-soon-tile | Docblock teaser default differs; "above the sheen" with no sheen; 44/22 literals | Default `"Thêm trò chơi mới"` | Align comment |
| UIM-18 | 03-02-m-member-layout.html#m-member-area (note callout) | Sticky rail (~950px, inference) taller than 900px viewport; logout reachable only at page end | No max-height/overflow on rail | `max-height` + internal scroll |
| UIM-19 | #m-member-sidebar | Comments promise ID chip / status chip; code renders plain ID + check overlay | Follow code | Fix comments |
| UIM-20 | #m-member-sidebar | Non-live balance shows literal `Số dư: 0 ₫` (fabricated 0) | Literal string at 28px | Honest absent state |
| UIM-21 | #m-member-sidebar | `Trung tâm nhiệm vụ` value hard-coded `"0"`, links `/hoan-tra` → `/khuyen-mai` | Verbatim | Real count/route |
| UIM-22 | #m-member-sidebar | Caption `Nạp tích lũy …` (deposit) for a turnover metric | Verbatim copy | Correct copy |
| UIM-23 | #m-member-sidebar | Level-0 user sees tiered progress (Bạch Kim → Kim Cương) | Same fixture for all states | Per-user progress |
| UIM-24 | #m-member-sidebar, 03-11 | Hard-coded VN strings despite i18n claim (sidebar guest, wallet, logout, linked accounts, agent tiers, stubs) | Hard-code where the guide says so | Move to `lib/i18n` |
| UIM-25 | #m-member-sidebar | Literal px/ms in "tokens only" module (44/18/−2/2/11/6/3/4/86/8px, 1.6s, lh 1.1) | Keep literals | Tokenise |
| UIM-26 | #m-sidebar-progress | `.trackSkeleton` uses a gradient shimmer | Verbatim | Flat skeleton |
| UIM-27 | #m-member-sidebar | Tiles 2+3 share `/hoan-tra`; `Lịch sử` → Hồ sơ; no tile to `#ngan-hang` / `#vi-tien-ao` / `#ho-so` / `/dai-ly` | MENU table verbatim | Real targets |
| UIM-28 | #m-member-sidebar | Unread dot from fixture, never updated by MessageCenter | Read `user.unreadMessages` | Shared store |
| UIM-29 | #m-member-sidebar | `summary.rebate` fetched, never rendered | Pass, do not render | Render or drop |
| UIM-30 | #m-sidebar-progress | Max-tier branch lacks `role="progressbar"` and caption; loading branch has no AT text | Verbatim branches | Add roles/text |
| UIM-31 | #m-logout-button | `Huỷ` vs `Hủy`; `styles.menuIcon` undefined in LogoutMenuItem | `Huỷ` | Normalise spelling |
| UIM-32 | 03-03-m-account.html#m-route-tai-khoan | `loading.tsx` uses missing `styles.heading` (unstyled h1); skeleton footprint of deleted layout; live page has no h1 | Unstyled h1 (inherits global h1), skeletons 112/96/300 | Real heading class, matching skeleton |
| UIM-33 | #m-route-bao-mat | "Permanent" comment but `redirect()` = 307; lands without `#bao-mat` | `redirect("/tai-khoan")` | `/tai-khoan#bao-mat` |
| UIM-34 | #m-profile-basic | Level-0 real-name row shows `Nguyễn Văn An` | Fixture not user-specific | Per-user data |
| UIM-35 | #m-security-center | Dead CSS classes; `.controlIcon` declared twice; factor labels unused; inputs without `name`; hash flash | Panels behave as spec (dead CSS need not be ported) | Clean up |
| UIM-36 | #m-linked-accounts | Add button uses `check` icon; notice hard-coded; `setDefault`/`remove` unrendered; hashes unreachable; crypto shown though wallet says "No crypto" | Verbatim | Fix icon/links |
| UIM-37 | 03-04-m-wallet.html#m-route-vi-tien | No live h1; first-deposit offer unreachable; withdraw destination = house account | Verbatim derivations | Member's linked card |
| UIM-38 | #m-wallet-tabs | Roving tabindex without arrow keys: 3 of 4 tabs keyboard-unreachable; promised fund-password gate missing | No `onKeyDown` | Use ui/Tabs |
| UIM-39 | #m-wallet-balance-header | CSS comment mentions removed "UT-1 chips" | n/a (comment) | Fix comment |
| UIM-40 | #m-deposit-panel | No card provider picker; amount never validated/used; `aria-controls="panel-bank"` dangling; hard-coded strings; QR is a placeholder | Verbatim | Validate; add panels |
| UIM-41 | #m-withdraw-panel | Title `Rút` vs tab `Rút tiền`; primary (navy) CTAs; empty copy points to `mục Bảo mật`; no fund-password step | Verbatim | Align copy/variant |
| UIM-42 | #m-fund-transfer-panel | Double sign `{formatVnd(f.amount)} ₫` → `6.886.000 ₫ ₫` (`FundTransferPanel.tsx:148`); `appearance:none` with no chevron; swap uses `retry` icon | Verbatim option text | Drop extra ₫; add chevron |
| UIM-43 | #m-wallet-history | `Transaction.note` unrendered; tablist without tabpanels; hard-coded strings | Verbatim | Render notes |
| UIM-44 | 03-05-m-messages.html#m-route-tin-nhan | Loading uses inline style object | Inline style verbatim | Utility classes |
| UIM-45 | #m-message-center | Guest sees unread subtitle + bulk actions; `Xóa tất cả` without confirm; unread dot untied; Icon given unsupported `aria-hidden` prop | Gate on `items.length` | Auth gate; confirm |
| UIM-46 | 03-06-m-referral.html#m-route-gioi-thieu | No live h1; comment "2 stats" vs 4; KPI rendered to guests | Verbatim | Auth gate |
| UIM-47 | #m-referral-kpi | 32px `6.800.000 ₫` overflows ~140px cell at 375 (inference) | No wrap/shrink | Fluid size |
| UIM-48 | #m-invite-tools | "Band-width" gate is a 640px viewport query; guests see code/link; `Lưu mã QR` no handler; code equals memo digits | Verbatim | Container query; handler |
| UIM-49 | #m-commission-panel | `Chi tiết hoạt động` is a non-interactive gold span; guest sees held label | Verbatim | Real link |
| UIM-50 | #m-step-explainer | Literals 46/10/−2/214/320px, 1.5; "gradient banner" comment; `--loss` red as decoration | Verbatim | Tokenise |
| UIM-51 | #m-agent-tiers | Levels 1,2,3,5; `currentLevel={0}` so no card active; low-contrast badge; hard-coded; `Bạch kim` lowercase | Verbatim | Fix levels/case |
| UIM-52 | 03-07-m-contribution.html#m-route-cuoc-hop-le | Page bottom reserve doubles ShellChrome's (≈152px <768, inference); both tab panels server-rendered | Page padding verbatim | Remove duplicate reserve |
| UIM-53 | #m-contribution-root | Default page shows 25 rows of 0% casino; i18n order differs; ICU `localeCompare("vi")` vs codepoint claim; ResultStatus always shows count | Verbatim sort/derivation | Product decision |
| UIM-54 | #m-page-intro | Cinzel comments; caveat link to same page | Verbatim | Fix comments |
| UIM-55 | #m-rate-filters | Pill `aria-pressed` on action chips (NotFoundResolver, deposit presets); literal `%` label | Pill unchanged | `pressed` opt-in |
| UIM-56 | #m-search-field | Input has no own outline (focus via `.control:focus-within`); shared id `contribution-search` across tabs | Verbatim | Unique ids |
| UIM-57 | #m-rate-table | `th.rowHead` `display:flex`; legend comment "two lines", one renders | Verbatim | Inner wrapper |
| UIM-58 | #m-pager | Page change does not scroll table into view; pages not deep-linkable | Verbatim | Scroll + `?page=` |
| UIM-59 | #m-table-foot | `huỷ` vs `Hủy` | Verbatim copy | Normalise |
| UIM-60 | #m-rate-table-skeleton | 2-cell rows, 5 pills, no tab strip vs real layout | Verbatim widths `55 + ((i*7) % 35)` | Match real layout |
| UIM-61 | 03-08-m-restricted.html#m-route-game-han-che | "Permanent" comment on 307; `restricted.metaTitle` unused | `redirect("/cuoc-hop-le?tab=han-che")` | Use metaTitle |
| UIM-62 | #m-restricted-root | Docs say rate-free; table shows `Tỷ lệ được tính` (always `0%`) | Render the rate column | Decide one |
| UIM-63 | 03-09-m-utility.html#m-redirect-routes | Redirect targets do not carry cashback/history; `getCashback()` unused | Verbatim redirects | Real routes |
| UIM-64 | #m-stub-pattern | Stub strings hard-coded; `line-height: 1.6` literal; 700 h1 vs 600 h2 elsewhere | Verbatim | Tokenise |

Cross-ref to the guide's top list (00-05-i-discrepancies.html#i-discrepancies): items 7 (UIM-37/40/42/38), 8 (UIM-27/33/63), 9 (UIM-35/36/45/46/48), 10 (UIM-12; dead account components, see G-10), 11 (comment drift, many rows above).

## 5. Gaps and contradictions

| ID | Where | Quote | What a builder would guess | Resolution |
| --- | --- | --- | --- | --- |
| G-1 | 03-03-m-account.html#m-profile-basic | ".panel (on Card) … padding --card-pad 24px (overrides Card default 16px — inference: module CSS loads after primitive CSS)" | Which class wins in Tailwind | ADR-UIM-001 (consumer utilities beat `@layer components`). Same for AgentTiers `.tier`, MessageCenter `.markAll`, ErrorState `.icon`, WalletBalanceHeader `.errorState`. |
| G-2 | #f-ui-pill, #f-ui-tabs | Pill "Hover: border becomes … text #f2f0e4"; "Selected (`.active`) … colour #d4af37" | State of a hovered selected Pill / Tab | Not stated; verbatim CSS (precedence rule 1) gives hover winning (specificity 0,3,0 > 0,1,0). Port selectors verbatim. WalletTabs avoids it with `:not(.active)`. |
| G-3 | #f-ui-button | "The colour shift is not media-gated, so touch devices get it on sticky hover." | Using `hover:` | T1: Tailwind gates `hover:`; custom variant `hover-any`. |
| G-4 | all modules with keyframes | (silent) | Reusing `fade`/`pop`/`spin` names globally | T9 prefixed names; `slideUp` inside `@media (max-width: 639px)` must be hoisted. |
| G-5 | #m-search-field | "noscript → style \".{input}{opacity:.5;pointer-events:none;}.{hintLive}{display:none;}.{hintOffline}{display:block;}\"" | Which selectors to emit without CSS Modules | Give input/hints stable hooks (e.g. `data-search-input`, `data-hint="live"`) and target them in the noscript style; `.hintOffline` default `hidden`. |
| G-6 | #m-member-area, #m-route-cuoc-hop-le | "(inference ≈ 950px)", "(inference: ~800px down)", "(inference: ≈ 152px below 768px)" | Exact heights | Compare against `shots/` only; do not hard-code heights. |
| G-7 | #m-wallet-history | "(inference: renders like \"14:05 05/11\"; exact separator depends on the runtime ICU)" | Formatting | Use `toLocaleString("vi-VN", {...})` verbatim; accept SSR/CSR text drift as in source. |
| G-8 | wallet, messages, referral fixtures | ages "30 min ago", "60 min", "2 h ago" | Static times | Fixtures are `now`-relative (lib); visual diff treats them as time-based. |
| G-9 | 03-02 … 03-08 | Only CSS is verbatim for member components; TSX is given as structure trees + behaviour prose | Exact JSX, handler details | Trees + prose are complete for DOM/copy; read original `apps/web/src/components/**` read-only when a handler detail is missing. |
| G-10 | 00-05 item 10 vs D1 | "Rebuild only what renders, unless the unused sections say otherwise." | Whether to rebuild ProfileHeader, QuickActions, AccountMenu, LogoutMenuItem, dead CSS | 03-10 lists them without asking for a rebuild: do not build (PM to confirm). Sheet IS built (barrel export). |
| G-11 | (source tree) | Component barrels `components/*/index.ts` exist in source; not in the guide | Whether to add | Optional; leaves list them as allowed but not required. |
| G-12 | #m-restricted-root | "notFound → span.srOnly {restricted.notFound}" | The string | Resolved from source `lib/i18n.ts:668-669`: `Chúng tôi chưa khớp được tên bạn gõ. Hãy thử gõ ngắn hơn, không dấu — ví dụ "baccarat".` |
| G-13 | #m-restricted-table | "footer is `RestrictedFoot`" (no file named) | File location | Resolved from source: `src/components/restricted/RestrictedFoot.tsx` (+ css). |
| G-14 | #m-utility | "(inference: the root `app/loading.tsx` — the HOME skeleton — is the fallback …)" | Own loading files | None; home track owns `app/loading.tsx`. |
| G-15 | #m-stub-pattern | "`/cau-lac-bo` (imports `../stub.module.css`; owned by track R/S)" | Shared styling without CSS Modules | `src/components/utility/StubPage.tsx` (leaf UIM-L7); track R/S imports it for `/cau-lac-bo`. |
| G-16 | #f-ui-modal | "a `transform`ed ancestor … would trap the fixed overlay (inference …)" | Add a portal | Do not (UIM-07). LogoutModal sits inside the sidebar; its ancestors have no transform at rest. |
| G-17 | #m-wallet-tabs | ".active … (becomes a gradient under the emerald brand …)" | `bg-(--brand-accent-grad)` | T4: `[background:var(--brand-accent-grad)]` everywhere a `*-grad` token is read (avatar, tierTag, actGold, barFill, wallet active tab, unread edge). |
| G-18 | #m-sidebar-progress | ".dot … transform translate(−50%, −50%) (+ pulse)" | `-translate-x-1/2` | T2: transform property only. |
| G-19 | #m-route-cuoc-hop-le | "ShellChrome's `.frame` ALSO reserves … bottom padding" | Remove the double padding | Reproduce (UIM-52); depends on shell leaf keeping its frame padding. |
| G-20 | 03-01-m-overview.html#m-auth-model | "`promptAuth` calls `openAuthModal({ mode: "login", resumeIntent })` (auth modal = track S)" | Where openAuthModal lives | Shell/auth leaf must export it before member leaves run their guest branches. |
| G-21 | #m-route-gioi-thieu, #m-route-vi-tien, #m-route-tai-khoan | loading h1s exist while live pages have no h1 | Adding h1s | Do not (UIM-32/37/46). |
| G-22 | #m-contribution-root | Provider/category tables show the first 25 catalogue rows only | Hand-typing 240 titles | Generate from `src/lib/mock/contribution.ts` (verbatim in 01-09-f-lib.html#f-lib-mock). |
| G-23 | current repo | `src/app/{tai-khoan,vi-tien,tin-nhan,gioi-thieu,cuoc-hop-le,hoan-tra}` exist from the archived build | Keep both | `(member)/tai-khoan` and `tai-khoan` resolve to the same URL and fail the build. D4 purge (or each leaf deletes its colliding old path) must precede L3-L7. |
| G-24 | #f-ui-empty-state | comment "reset action — shown by default in the filtered variant" vs "only when `onReset` is passed" | Show reset for filtered | Follow code: only with `onReset`. |

## 6. Assets

| Public path | Used by | Size (from 01-10-f-assets.html, confirmed on disk) |
| --- | --- | --- |
| `/assets/placeholders/poster.svg` | InviteTools (`posterSrc` fixture, treated as "no real poster") | svg, viewBox 0 0 300 400, 634 B |
| `/assets/casino/mg_baccarat_landscape.png` | Tile data example (`getGames()`, home track) | png 702×480, 452,392 B |

No other public path is referenced by the 12 assigned sections. Icons are inline SVG (no files). Fonts come from `next/font` (foundations).

## 7. Proposed leaves

Order: L1 → L2 → {L3, L4, L5, L6} (max 2 concurrent) → L7. All leaves also need: foundations tokens + entry CSS contract (3.4), `src/lib/**` (auth, format, types, rg, i18n, mock), and the shell leaf (root layout, ShellChrome, `openAuthModal`). Common gates for every leaf: `npx tsc --noEmit` exit 0; `npm run lint` exit 0; no `tailwind-merge` import; no bare `hover:` in leaf files (`! rg -n '(^|[" ])hover:' <files>`); no `*.module.css` under leaf paths.

| Leaf | allowed_files | Implements | Needs | Acceptance (mechanical) |
| --- | --- | --- | --- | --- |
| UIM-L1 ui-base (10) | `src/ui/ui.css`, `src/ui/Icon/**`, `src/ui/Badge/**`, `src/ui/Button/**`, `src/ui/Card/**`, `src/ui/Pill/**`, `src/ui/MoneyValue/**`, `src/ui/Skeleton/**` | #f-ui-icon, -badge, -button, -card, -pill, -money-value, -skeleton, -tile-skeleton, -use-grid-fill; ADR-UIM-001 | foundations | `rg -c '^\s+[a-zA-Z]+: <path' src/ui/Icon/Icon.tsx` = 44; `rg -q '@layer components' src/ui/ui.css`; `rg -q '\(hover: hover\) and \(pointer: fine\)' src/ui/ui.css`; `rg -q 'ui-btn-spin 700ms linear infinite' src/ui/ui.css`; `rg -q 'color-mix\(in srgb, var\(--brand-accent\) 12%, var\(--surface-2\)\)' src/ui/ui.css`; `rg -q 'Giá trị tạm dừng cập nhật' src/ui/MoneyValue/MoneyValue.tsx`; `rg -q 'tạm dừng'`; `rg -q '"Đang tải"' src/ui/Skeleton/Skeleton.tsx src/ui/Skeleton/TileSkeleton.tsx`; `rg -q 'targetRows \* cols - occupiedCells' src/ui/Skeleton/useGridFill.ts` |
| UIM-L2 ui-composite + overlays + barrel (12) | `src/ui/EmptyState/**`, `src/ui/ErrorState/**`, `src/ui/Countdown/**`, `src/ui/Odometer/**`, `src/ui/Scroller/**`, `src/ui/Tabs/**`, `src/ui/Tile/**`, `src/ui/Modal/**`, `src/ui/Sheet/**`, `src/ui/Dropdown/**`, `src/ui/index.ts` | #f-ui-empty-state, -error-state, -countdown, -odometer, -scroller, -tabs, -tile, -coming-soon-tile, -modal, -sheet, -dropdown, -index | L1 | `rg -c '^export' src/ui/index.ts` = 39 (value + type export statements, counted from the verbatim barrel); strings: `Chưa có dữ liệu`, `Không có kết quả`, `Đặt lại bộ lọc`, `Không tải được dữ liệu`, `Đã xảy ra lỗi. Vui lòng thử lại.`, `Mất kết nối mạng. Kiểm tra kết nối rồi thử lại.`, `Thử lại`, `Đã kết thúc`, `Còn lại `, `Sắp ra mắt`, `Thêm trò chơi mới`, `aria-label="Đóng"` (Modal + Sheet); `rg -q 'const dur = 700' src/ui/Odometer/Odometer.tsx`; `rg -qF 'a[href],button:not([disabled]),textarea,input,select,[tabindex]:not([tabindex="-1"])'` in Modal, Sheet, Dropdown; `rg -q 'tab-\$\{it.id\}' src/ui/Tabs/Tabs.tsx`; `rg -q 'dy > 80' src/ui/Sheet/Sheet.tsx` |
| UIM-L3 member frame + account (13) | `src/app/(member)/layout.tsx`, `src/app/(member)/tai-khoan/**`, `src/app/bao-mat/**`, `src/app/lich-su/**`, `src/components/account/**` | #m-member-area, #m-member-sidebar, #m-sidebar-progress, #m-logout-button, #m-route-tai-khoan, #m-route-bao-mat, #m-account-sections, #m-profile-basic, #m-security-center, #m-linked-accounts, #m-redirect-routes (`/lich-su`) | L1, L2, foundations, shell | Dev server: `curl -s -o /dev/null -w '%{http_code}' localhost:3000/tai-khoan` = 200; `/bao-mat` and `/lich-su` = 307 with `redirect_url` ending `/tai-khoan`. Strings in `src/components/account/`: `Nhận huy hiệu`, `Đã sao chép`, `Nạp tích lũy`, `Số dư: 0 ₫`, `Cửa hàng điểm`, `Trung tâm nhiệm vụ`, `Chờ mở khóa`, `Thăng hạng toàn dân`, `Bạn có chắc muốn đăng xuất khỏi tài khoản?`, `Huỷ`, `Hồ sơ cá nhân`, `Trung tâm an toàn`, `Điểm an toàn`, `Đây là bản giao diện mẫu — chưa kết nối hệ thống.`, `Liên kết thẻ ngân hàng`, `Địa chỉ ví`, `Mặc định`; `rg -q 'Tài khoản — Yaobet' 'src/app/(member)/tai-khoan/page.tsx'`; `rg -q 'polygon\(0[ _]0' src/components/account/MemberSidebar.tsx`; `rg -q 'page-bloom' 'src/app/(member)/layout.tsx'` |
| UIM-L4 wallet (9) | `src/app/(member)/vi-tien/**`, `src/components/wallet/**` | #m-route-vi-tien, #m-wallet-tabs, #m-wallet-balance-header, #m-deposit-panel, #m-withdraw-panel, #m-fund-transfer-panel, #m-wallet-history | L1, L2, L3 (layout), foundations | `/vi-tien` = 200; strings: `Mục ví tiền`, `Chọn hình thức nạp`, `Số tiền gợi ý`, `Tôi đã chuyển`, `Nạp thẻ cào`, `Đang chờ xác nhận`, `Yêu cầu rút tiền`, `Số tiền vượt quá số dư khả dụng.`, `Quỹ nguồn và quỹ đích phải khác nhau.`, `Đổi chiều chuyển`, `Lọc giao dịch`, `Chưa có giao dịch`, `Ví tiền — Yaobet`; defect gates: `rg -qF '{formatVnd(f.amount)} ₫' src/components/wallet/FundTransferPanel.tsx`; `! rg -q onKeyDown src/components/wallet/WalletTabs.tsx`; `rg -q 'wallet-tab-' src/components/wallet/WalletTabs.tsx`; `rg -q 'max-width: ?420px\|max-420' src/components/wallet/WalletTabs.tsx` |
| UIM-L5 messages + referral (14) | `src/app/(member)/tin-nhan/**`, `src/app/(member)/gioi-thieu/**`, `src/app/(member)/dai-ly/**`, `src/components/messages/**`, `src/components/referral/**` | #m-route-tin-nhan, #m-message-center, #m-route-gioi-thieu, #m-route-dai-ly, #m-referral-kpi, #m-invite-tools, #m-commission-panel, #m-step-explainer, #m-agent-tiers | L1, L2, L3 (layout), foundations | `/tin-nhan`, `/gioi-thieu`, `/dai-ly` = 200; strings: `Đánh dấu đã đọc tất cả`, `Xóa tất cả`, `Lọc tin nhắn`, `Đã đọc tất cả`, `Chưa có tin nhắn`, `Tổng quan thưởng`, `Công cụ mời bạn bè`, `Lưu mã QR`, `Hoa hồng giới thiệu`, `Chi tiết hoạt động`, `Cách hoạt động`, `Cấp đại lý`, `Đại lý Bạch kim`, `Hoa hồng theo điều khoản chương trình`; metadata `Tin nhắn — Yaobet`, `Giới thiệu bạn bè — Yaobet`, `Đại lý — Yaobet`; `rg -q 'currentLevel=\{0\}' 'src/app/(member)/dai-ly/page.tsx'`; `rg -q '/assets/placeholders/poster.svg' src/components/referral src/lib` |
| UIM-L6 contribution components (13-14) | `src/components/contribution/**` | #m-contribution-tabs, #m-page-intro, #m-contribution-root, #m-rate-filters, #m-search-field, #m-result-status, #m-not-found-resolver, #m-filter-notice, #m-rate-table, #m-rate-cell, #m-pager, #m-table-foot, #m-rate-table-skeleton | L1, L2, foundations (`lib/mock/contribution.ts`) | strings: `Tỷ lệ tính cược theo trò chơi`, `Tìm tên trò chơi…`, `Gõ không dấu cũng được (vd: no hu)`, `Tìm trò chơi cần có mạng.`, `Xóa nội dung tìm kiếm`, `Chúng tôi chưa khớp được tên bạn gõ.`, `Vẫn chưa rõ? Xem Trợ giúp`, `Không có trò chơi nào khớp với bộ lọc đang chọn.`, `Phân trang danh sách trò chơi`, `Tỷ lệ có thể thay đổi, chúng tôi báo trước 30 ngày.`, `0% — vẫn chơi bình thường, chỉ là cược không cộng vào cược hợp lệ.`; constants `rg -q 'DEBOUNCE_MS = 250'`, `rg -q 'PAGE_SIZE = 25'`, `rg -q 'contribution-search'`, `rg -q '<noscript>'`; `rg -q 'border-collapse:separate\|border-separate' src/components/contribution/RateTable.tsx` |
| UIM-L7 trust routes + restricted + utility (15) | `src/app/cuoc-hop-le/**`, `src/app/game-han-che/**`, `src/app/hoan-tra/**`, `src/app/ho-tro/**`, `src/app/tro-giup/**`, `src/app/tai-app/**`, `src/app/phong-cach/**`, `src/components/restricted/**`, `src/components/utility/**` | #m-route-cuoc-hop-le, #m-route-game-han-che, #m-restricted-intro, #m-restricted-root, #m-restricted-filters, #m-restricted-table, #m-redirect-routes (`/hoan-tra`), #m-stub-pattern | L1, L2, L6, foundations, shell | `/cuoc-hop-le` = 200 and HTML contains `Tỷ lệ tính cược theo trò chơi`; `/cuoc-hop-le?tab=han-che` = 200 and HTML contains `Game hạn chế trong khuyến mãi`; `/game-han-che` = 307 → `/cuoc-hop-le?tab=han-che`; `/hoan-tra` = 307 → `/khuyen-mai`; `/ho-tro` `/tro-giup` `/tai-app` `/phong-cach` = 200 with h1 `Hỗ trợ khách hàng`, `Trung tâm trợ giúp`, `Tải ứng dụng`, `Phong cách`; metadata `Tỷ lệ tính cược theo trò chơi — Yaobet`, `Hỗ trợ — Yaobet`, `Trung tâm trợ giúp — Yaobet`, `Tải ứng dụng — Yaobet`, `Phong cách — Yaobet`; stamps `09/08/2026 09:30` and `08/08/2026 10:00` rendered; `rg -q 'Danh sách game hạn chế — vuốt ngang để xem thêm cột' src/components/restricted` |

Keyframes ownership: L1 writes `src/ui/ui.css` (all `ui-*` keyframes). L3 writes `src/components/account/member.css` (`member-pulse-dot`, `member-progress-shimmer`) and needs the entry CSS to `@import` it (contract 3.4 item 1). No other leaf needs global CSS.

Disjointness check: no glob above overlaps another (src/ui split by folder; each `src/app/<route>` and `src/components/<area>` owned once). `/cau-lac-bo` stays with track R/S and imports `@/components/utility/StubPage`.

## 8. Risks

1. **Cascade parity lost (high).** Without ADR-UIM-001, Tailwind's sort order decides Card padding (16 vs 24px), Icon colour inside ErrorState, ghost Button label colours in MessageCenter, and hovered-selected Pill/Tab colours. These show as screenshot diffs with no build error.
2. **Tailwind v4 silent semantic changes (high).** `hover:` media gate, `scale`/`rotate`/`translate` properties instead of `transform`, 150ms default transitions, `bg-(--var)` = background-color (gradient tokens lost), oklab colour mixing/gradients, rem breakpoints and exclusive `max-*`. Each passes typecheck and fails visual/motion checks. Mitigation: T1-T9 plus the grep gates in section 7.
3. **Keyframe scoping and media-nested keyframes (medium).** Module-scoped names collide globally across tracks (`fade`, `pop`, `spin`, `slideUp`); Modal's `slideUp` and sidebar pulse are declared inside media queries. Mitigation: prefixed global keyframes (T9).
4. **Builders "fixing" the 64 defects (medium).** The defects include a11y holes (wallet tabs keyboard, missing h1s), a double currency sign, guest data leakage and dead links. Grep gates in L4/L5/L7 lock several in; the oracle audit must check the rest against section 4.
5. **Ordering and environment coupling (medium).** Old `src/app/{tai-khoan,vi-tien,tin-nhan,gioi-thieu,cuoc-hop-le,hoan-tra}` routes collide with the `(member)` group (G-23). Member leaves also depend on foundations (verbatim `lib/mock/contribution.ts`, i18n), on shell (`openAuthModal`, ShellChrome padding that UIM-52 doubles), and on time-relative fixtures plus ICU formatting (G-7/G-8), which make visual diffs noisy.
6. **Member TSX not verbatim (low-medium).** Only CSS is verbatim for track-M components; JSX comes from trees and prose (G-9). Builders may read the original source read-only to settle handler details.

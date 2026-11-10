# Fix list (owner approval needed)

Total: 152 defects across 4 tracks.

Per D3, every defect below is **reproduced as built** in the rebuild. Each row's last column is the proposed later fix. Nothing on this list is applied without the owner's approval. Source: §4 of each review in `docs/rebuild/review/` (generated verbatim from those tables; the reviews are the source of truth).

Extra entries from PM rulings:

- PR-04: store cooldown timing is reproduced at module load; the fix is to compute it per request.
- PR-09: header overflow SH-02 is reproduced; the fix is `min-w-0`, or wrapping in the header identity cluster (the guide's own "do not copy" note).
- PR-11: raw `<a>` anchors that reset mock auth are reproduced; the fix is `next/link`.

## foundations-core (24 defects)

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

## shell-home (33 defects)

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

## ui-member (64 defects)

| ID | Anchor | Defect | Reproduce | Proposed later fix |
|---|---|---|---|---|
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

## rewards (31 defects)

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

## Addendum: QC findings during the rebuild (2026-11-06)

These are present in the original app and reproduced as built under D3 unless the line says otherwise; nothing is applied without the owner's approval.

### F1
- contrast tokens.css:62 (5.58 not 5.59)
- :63 --text-dim 3.94/3.46
- --text-mid on --surface-disabled 3.72
- --error #e42946 4.44/4.13
- --text-hi on --error 3.90 / on --info 2.88
- :254 gold 2.10 not 2.11

### F5
- FC-11 loader weight gaps L42/L53 (synthesised weights)
- themeColor "#0a0a0a" literal at L69 duplicates --canvas
- FC-10 data-brand only on <html> L78
- L11 "(§F)" dangling after the SPEC-04 drop
- L9 stale "SupportWidget slot" comment
- L57-58 imports after the loader calls (original order)
- display swap without adjustFontFallback, so a possible swap shift

### S1-S8
- home.css:598 DevAuthToggle close < --tap-min (verbatim, dev-only)
- reproduced: SH-03 comment, SH-15, SH-24, SH-27
- MemberMenu.tsx:38, NotificationBell.tsx:151 Escape no focus return
- NotificationBell.tsx:120,133-137,352 bell loading shows empty state + no error path
- Header.tsx:130 "GATE FIX:" original comment (original Header.tsx:131)
- QAR promo-close 16x16 < 24px
- QAR icon-label 9px
- footer socials 40x40 mobile < 44
- QAR popovers role=dialog hover-only no Escape/outside (SH-26 family)
- home.css:963 CTA min-height 34px
- SportsMatchCard.tsx:115 inert odds divs
- home.css:827/859/946 ellipsis L-16
- SportsMatchCard.tsx:55,:65 aria-label on span
- SportsLifestyle.tsx:40,:47 kicker repeats h2 W-07
- SportsLifestyle.tsx:96-105 null match slot on error
- home.css:926 nested bordered cells L-01
- home.css:939 suspended cell opacity 0.6 contrast
- reproduced: SH-15, SH-17, SH-18 (England flag emoji lobby.ts:185), SH-24, SH-19, SH-01
- CategoryGrid.tsx:93 same-page tap
- CategoryBanner.tsx:34 icon map drift
- CategoryBanner.tsx:54,62 aria-label repeats h1
- vertical.css:217-224 team-name ellipsis
- loading.tsx:28 160px skeleton shift
- LiveOddsBoard.tsx:70 no stale timer
- vertical.css:79-90 placeholder 4.54:1
- no route error.tsx
- stale comments CategoryGrid.tsx:4 and vertical.css:36
- reproduced: SH-19, SH-20, SH-25, SH-28
- PromoGrid.tsx:81 badge repeat
- PromoGrid.tsx:85 timer box in tile
- PromoDetail.tsx:56,65 aria-label vs h2
- PromoDetail.tsx:30 member CTA no-op
- promo.css:79-82 hover without hover media
- khuyen-mai/page.tsx:24 no error state
- PromoGrid.tsx:77 title clamp
- reproduced: SH-21, SH-22, SH-29, SH-32

### U1-U7
- MemberSidebar.tsx:179/209 aside, :317 nav and tai-khoan page section share the accessible name "Tài khoản".
- MemberSidebar.tsx:247 name ellipsis (L-16).
- MemberSidebar.tsx:251 copy-ID and SecurityCenter.tsx:219 reveal targets under 44px.
- MemberSidebar.tsx:255 "Đã sao chép" toast lacks role=status.
- LogoutButton.tsx:63 icon="account" on logout; no aria-haspopup.
- SecurityCenter.tsx:168, LinkedAccounts.tsx:55 bordered items inside a Card (L-01).
- MemberSidebar stacked rail cards (L-13), 12-icon grid (T-12).
- Elements without their own focus rule rely on reset.css:67 focus-visible.
- Contrast (C-06) not measured.
- src/components/wallet/WalletTabs.tsx:114 WalletTabs selected tab reads `--brand-accent-grad`, which is a linear-gradient under the emerald brand (brands.css:39), the same defect FC-07 records for Button (guide 03-04 #m-wallet-tabs; ui-member review G-17; original WalletTabs CSS Module sheet :70)
- src/components/wallet/WalletTabs.tsx:113 no arrow-key handling; 3 of 4 tabs unreachable by keyboard (UIM-38)
- src/components/wallet/WalletTabs.tsx:112 aria-controls points to panels that are not rendered
- src/components/wallet/DepositPanel.tsx:143 dangling panel-bank id (UIM-40)
- src/components/wallet/WalletHistory.tsx:82 tablist without tabpanels; Transaction.note not rendered (UIM-43)
- src/components/wallet/FundTransferPanel.tsx:147 double "₫ ₫" (UIM-42)
- src/components/wallet/FundTransferPanel.tsx:141,168 select has no chevron (UIM-42)
- src/components/wallet/FundTransferPanel.tsx:159 swap button uses the retry icon (T-12)
- src/components/wallet/FundTransferPanel.tsx:155 swap button 40px, under --tap-min 44px
- src/components/wallet/WithdrawPanel.tsx:116 / FundTransferPanel.tsx:194 error text not linked via aria-describedby
- src/components/wallet/WithdrawPanel.tsx:59 vs WalletTabs.tsx:57 "Rút" vs "Rút tiền"; two primary buttons (UIM-41)
- src/app/(member)/vi-tien/page.tsx no live h1; only loading.tsx:13 has one (UIM-37)
- MessageCenter.tsx:225,232 L-01 bordered message cards inside the Card panel.
- MessageCenter.tsx:112,127 hover not media-gated; scale and tint stick on touch.
- MessageCenter.tsx:123-124 role=menuitem with aria-current; selected state needs menuitemradio + aria-checked.
- MessageCenter.tsx:99-107 destructive "Xóa tất cả" has no confirm.
- InviteTools.tsx:75,90 L-16 code and link clipped by ellipsis.
- InviteTools.tsx:122 "Lưu mã QR" is a dead control.
- CommissionPanel.tsx:80 gold span looks like a link but is inert.
- ReferralKpiHeader.tsx:39 T-12 an icon on every stat.
- AgentTiers.tsx:45 low-contrast badge (not measured).
- tin-nhan/, gioi-thieu/, dai-ly/ have no error.tsx (8-state gap).
- Build note: Tailwind emits a solid background:var(--brand-accent) fallback before @supports(color-mix) for the unread wash; browsers without color-mix show solid gold (original build has no fallback).
- RestrictedTable.tsx:101-102: row hover (>=1024px) --text-mid #888 on --surface-hover #262626 is about 4.27:1, below AA.
- RestrictedTable.tsx:95: `th scope="row"` with display:flex can break table semantics for assistive tech.
- RestrictedFilters.tsx:55: long provider names are clipped with an ellipsis in the trigger value (L-16).
- RestrictedFilters.tsx:60-67: menuitemradio items in a plain ul with no role="menu"; trigger has aria-haspopup="true".
- RestrictedTable.tsx:99: rate column is always 0% (W-07).
- SearchField.tsx:133 (reused): id `contribution-search` duplicated across tabs.
- Stub pages ho-tro, tro-giup, tai-app, phong-cach page.tsx:12-14: no primary action, no way forward.

### R3-R8
- LevelTable.tsx:73 corner and header cells tie at z 100; header cells paint over the corner on horizontal scroll.
- LevelTable.tsx:74 empty corner th scope=col has no accessible name.
- LevelTable.tsx:126 dimmed values #565f70 on #17140d = 2.86:1 (C-06); :100 faint level word 4.29:1 at micro size.
- LevelTable.tsx:105 lock glyph aria-hidden; locked state conveyed by colour only.
- TierDeck.tsx:172 tabs without tabpanel (REWARDS-09); :178 dots are 8px targets (< 24px).
- TierDeck.tsx:138 cards rely on default focus ring; no arrow keys (drag is pointer-only).
- VipFaq.tsx:54-59 collapsed answers stay in the accessibility tree (no hidden/inert).
- PrivilegeMatrix.tsx:65,91 nowrap row heads in a fixed 200px column may overflow (L-16, unmeasured).
- Guide errata: 04-10 state table says corner z 101; its own CSS block and the original compute 100.
- LevelTable.tsx:71 thead tr drops the declaration-less headRow class (guide names "thead tr.headRow"); no computed change.
- TierLadder.tsx:43: locked tier card at opacity .66 drops text-mid to about 2.87:1 (C-06).
- PerkGallery.tsx:53: locked note in text-dim at 3.67:1 on surface (C-06).
- PrivilegeTable.tsx:78: the dash uses text-dim; aria-label="Không" sits on a span with no role.
- PrivilegeTable.tsx:33-37: the matrix is divs with no table or row semantics.
- TierLadder.tsx:47: aria-label on a Card div with no role.
- TierLadder.tsx:31: rail stays a tab stop (tabIndex 0) at 768px+ where nothing scrolls (root cause in the Scroller component).
- tier/page.tsx:47,56: "Bậc thang VIP" is both the h1 and a section h2 (W-07).
- VipSection.tsx:19: section aria-label repeats its own h2.
- VipRules.tsx:25: decorative info icon on every rule card (T-12).
- /tier: 15+ stacked cards (L-13).
- TierLadder, PrivilegeTable: no empty state when the tier list is empty.
- REWARDS-05/12/13/14/15 reproduced (detailLink unused; progress not user-aware; "1%" vs "1,0%"; per-tier perks with colPerks unused; redundant 1024px rule).
- ProductGrid.tsx:129 tablist has no tabpanel, no arrow keys or roving tabindex.
- ProductGrid.tsx:136 tabs about 26px tall, under the 44px touch target.
- ProductCard.tsx:155 L-16: "Rút sau N vòng cược" ellipsis-clipped on the 2-column grid at 375px.
- ProductCard.tsx:115-140 D-09: three overlays on the image (tag, points badge, cooldown chip).
- StoreTerms.tsx:61,81 aria-controls targets a panel not rendered while closed; L-01 item cards inside the section card.
- RedeemDialog.tsx:168 L-01 cost card inside the Modal.
- /cua-hang is static: cooldowns computed at module load (lib/mock/store.ts:129, REWARDS-16) freeze at build time.
- OutcomeFrame.tsx:57 + ScratchCardGame.tsx:365: two polite live regions; outcome may be announced twice.
- ScratchCardGame.tsx:425,438: dev buttons min-h-space-6 (32px), under the 44px tap minimum.
- LotteryRoot.tsx:89: hover scale on a non-interactive article implies clickability.
- LotteryRoot.tsx:118: focus-visible styling on a disabled button never shows; aria-disabled duplicates disabled.
- C-06 contrast: text-dim on surface 3.67:1 (LotteryRoot.tsx:153,178); text-dim on surface-2 3.46:1 (OutcomeFrame.tsx:81, ScratchCardGame.tsx:390); text-hi on info 2.88:1 (devTag ScratchCardGame.tsx:418).
- L-01: bordered lose cells inside the bordered frame (OutcomeFrame.tsx:93); wells inside ticket inside dialog.
- D-09: many "Sắp ra mắt" badges plus "Đang mở" and section-state pills.
- REWARDS-20/22 (reproduced, D3): nested main LotteryRoot.tsx:77; shortVnd comment 480px vs min-[560px] ScratchCardGame.tsx:98; viewport not container queries; dev bar always rendered :416.
- Doc conflict: T6 (rewards.md:152) and the ScratchSurface/OutcomeFrame T-rows vs ADR-002 section 2 on data-state placement; ADR-002 governed.
- CollectionApp:363: hover scale on a rail that cannot be clicked.
- CollectionApp:363, RewardCeremony:129: cards inside cards (L-01, L-13).
- CollectionApp:529/533, :344: two corner pills per tile plus a count chip in 9-10px text (D-09; contrast not measured).
- CollectionApp:459 (link), :493 (button): touch targets with no minimum height.
- CollectionApp:493: toast button has no visible focus style.
- PackStage:138: prize reveal is not in a live region.
- RewardCeremony:258: "Đang chuyển vào ví…" receipt is not in a live region.
- REWARDS-23/27/28/29/30/31 reproduced (100vw formula; key={nonce} remount; c-${id} ids; filter decls, dead .info{right}, :not(.info), id="pk", raw HSL; rare-only foil; [beat, reduced] effect; toFixed(1)).
- PM ruling needed: ADR-002:47 descendant-selector wording vs the [&_x]: variant precedent (MessageCenter:112).
- C-06 --text-dim #6f6f6f 3.66:1 on #141414 on functional text: MyCards.tsx:264, dev page:167/177, CardDetail.tsx:96/139
- C-06 --error #e42946 4.13:1 at 12px: dev page:179
- 10px badge text: MyCards.tsx:345, :347
- Touch target: inline set links lack min-height: CardDetail.tsx:118
- L-01 bordered card inside overlay: CardDetail.tsx:91, :103
- REWARDS-20 nested <main>: dev page:127
- REWARDS-24 demo-a adapter + stale "refuse on purpose" note: dev page:32, :134
- PR-32 dev preview renders internal ticket IDs (GC-101, BR-03/04/05)

### Comment policy
- tokens.css:27 `/* §1 — Color: canvas & surfaces — FLAT / DARK-LUXURY (PM "dark")`
- tokens.css:29 `* Obsidian ground #0a0a0a, card #141414. measured that pair at`
- tokens.css:65 `/* shadows AND card gradients are banned, so on a 1.05:1`
- tokens.css:165 `/* §8 — tap targets ---------------------------------------- */`
- tokens.css:210 `/* Membership progress track. The empty groove is a 12% white hairline (`
- tokens.css:353 `*      This is the identical defect that got Outfit rejected in;`
- brands.css:12 `* falsifiable byte-identical property verifies / lints.`
- typography.css:4 `* TWO faces, both Vietnamese-complete (Flat / Dark-Luxury, PM):`
- reset.css:19 `/* base: html{font-size:14px}. All design tokens are absolute px, so this`
- CollectionApp.tsx:39, :334-335 and PackStage.tsx:144: deleting a tag that was the grammatical subject leaves broken sentences ("a universe size has not ruled", "is / and unruled", "support find first"); a later copy pass may reword them (outside the exact-rebuild scope).
- collection.css:326-331: the whole original foil comment sits above `@keyframes card-foil-sweep` while its `.rare` outline rule now lives as utilities in CardArt.tsx.
- R8 broken comment sentences after tag-token deletion: MyCards.tsx:134 "the universe size is and is not published here"; MyCards.tsx:256 "the universe size is."; CardDetail.tsx:126 "The restoration point for."; dev/collection-ports/page.tsx:13 "Deleted when lands."
- R8: tag groups dropped with their bound punctuation (CardDetail:2 "(R3.3 / R6.1)", MyCardsRoot:15 ", R0.5", dev page:119 "GC-102 — ") accepted per R7 CollectionTerms:53 precedent.
- Inconsistency: S3 QuickActionRail.tsx:5 and the S6 rewordings were accepted while later leaves were held to the deletion-only rule.

### Lint warnings
- HeroBand.tsx:172 and :259 no-img-element
- useFocusTrap.ts:84 exhaustive-deps

### Rebuild tooling
- Redirect pages answer 200 + meta refresh, not 307 (PR-41); soft 404 (PR-40).
- genplan.py gate() resets ticked ledger rows on every run.
- wt_prep --resume rsync gap.
- stock zero utilities (min-w-0, p-0, m-0, left-0) emit nothing under --*: initial; use [0].

### Harness
- Suppression lock: shell writes (python/heredoc via Bash) bypass the Edit hook; 7 verbatim eslint-disable lines reached main that way.
- Suppression lock only fires on existing files (os.path.isfile gate at pre_tool_use.py:1326); new files are unchecked.
- Auto-mode classifier blocks hook self-modification even with owner approval; hook changes need an owner-applied patch.

### Runtime version gap (owner decision 2026-11-06: keep Next 16.4.5; recorded as a known runtime difference)
- Under `next start` on Next 16.4.5 the redirect routes /game-han-che and /hoan-tra (and likely /bao-mat, /lich-su) are prerendered static and answer 307 + Location with the refresh meta; the original on Next 16.2.9 answers 200 + refresh meta (PR-41). Dev mode matches the original. Cause: Next version, not page code (page code is identical).

### Guide and original conflicts found by the root audit (2026-11-06)
- Sports lifestyle cards: the guide CSS (02-03-s-home-h.html:1177-1182) puts the card content at the bottom with `flex-end` and 16px padding, but the original's Card module (Card.module.css:1-2,28-29, `display:block; padding:0`) wins, so the running original shows the kicker and title at the top. The rebuild follows the running original (PR-44). Fix: pick one layout and remove the losing rule.
- RedeemDialog: Escape or "Hủy" leaves focus on BODY instead of "Đổi ngay". The dialog mounts with `{selected && (` (ProductGrid.tsx:163) and Modal.tsx:61 only refocuses when `open` turns false, never on unmount. The original has the same code (ProductGrid.tsx:162, Modal.tsx:62). Fix: restore focus on unmount, or keep the Modal mounted and toggle `open`.
- Sports lifestyle cards, dev vs production cascade in the original: the original's `next build` output (`.next/server/app/index.html`) loads the Card chunk before the lifeCard chunk, so in production `.lifeCard` wins (flex-end, 16px padding), while `next dev` (the guide references and the A5 capture) lets the Card base win. The rebuild follows the dev rendering and is the same in both modes, because the conflicting declarations were removed (home.css:1053-1067). Fix: same as the row above.

### Shot pairs justified by framework and original dev-build causes (owner ruling PR-48, 2026-11-06)
Each row is a justify row in `.unlazy/yaobet-rebuild/checks/shot-justify.json`. The rebuild's own source does not cause any of these.
- m375-tiered-tai-khoan (0.682%), m375-tiered-vi-tien (0.795%), m375-tiered-gioi-thieu (0.546%): after `router.push`, Next 16.4.5 scrolls the new segment into view (`node_modules/next/dist/client/components/layout-router.js:100-172`), so the page lands at scrollY 1102 under the 375 px sidebar. The original's Next 16.2.9 uses the old handler (`config-shared.js:180`, `appNewScrollHandler: false`). That handler's `findDOMNode` returns the segment stylesheet link that was hoisted into `<head>`, so it stops without scrolling (`layout-router.js:146-160`, a case Next's own comment calls a bug). On /lich-su both versions scroll. Fix: none in page code; matching would need the old Next version. Decide whether member pages should land at the top after navigation, and do it on purpose in both apps. On /gioi-thieu the block at y 2137-2239, x 48-111 is the commission timestamps: `formatWhen(c.at)` of `isoAgo(120)` and `isoAgo(680)` depends on the clock at capture and sits outside the time mask (rebuild `CommissionPanel.tsx:108`, `src/lib/mock/referral.ts:34-35`; original `CommissionPanel.tsx:109`).
- m375-tiered-tin-nhan (1.451%): the same scroll. Also, the band at y 1194-1239 is the hover state of "Đánh dấu đã đọc tất cả", which sits under the pointer left where "Đóng" was clicked.
- d1440-tiered-hoan-tra (2.783%), d1440-tiered-lich-su (2.301%): after the redirect, the original's Turbopack dev server appends two chunks that repeat the Card module (`ui/Card/Card.module.css:1-2,22-23`). On /lich-su, Card's `display:block` and 16 px padding (`Card.module.css:1-2,22-23`) beat the ProfileBasic panel (`ProfileBasic.tsx:61`). On /khuyen-mai, where /hoan-tra lands, only `display:block` acts: it beats the PromoHero `.hero` `display:flex` and its min-width 768 row rule (original `components/promo/PromoHero.tsx:26`, `PromoHero.module.css:3-4,88-92`; rebuild `PromoHero.tsx:25`). The promo variant's padding 0 (`Card.module.css:28-29`) equals `.hero`'s. The profile card shrinks from 678 to 614 px and the PromoHero media collapses from 221 to 0. The rebuild matches the original's direct landing (0% diff). The original's direct and redirect landings differ by 11.62% and 32.26%. Fix: none in the rebuild; this is the original's dev-only CSS order. In the original, raise the panel and hero rules above the Card base, or drop the Card base from those elements.
- m375-tiered-lich-su (size 623x2528 vs reference 623x2464): the same repeated Card module shrinks the card by 64 px in the reference. `scripts/shot-diff.mjs` now passes a size mismatch only when that pair has a justify row.
- Intermediate widths 768, 992, 1024 and 1300 (no guide shots, so the running original is the reference; 2026-11-07): 136 of 144 tiered and guest pairs are under the threshold. The 8 others are /hoan-tra and /lich-su at each width, where the original shows the same repeated Card sheet after the redirect (4 size mismatches of +31 to +64 px, and 2.0-2.7% on the profile card and PromoHero bands). Against the original's direct landings on /khuyen-mai and /tai-khoan, all 8 rebuild captures are the same size and at most 0.454% outside masks (t768 lich-su; 0.000-0.001% for the rest). Fix: none in the rebuild; same as the row above.

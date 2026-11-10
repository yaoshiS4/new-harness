# ADR-001 — Yaobet phase-1 design direction

Status: accepted by PM 2026-11-04 (owner review pending on §5 dependency options) · Date: 2026-11-04 · Author: sa · Supersedes: Lucky Obsidian token contract (SOT §2, line 39)
Companion: `docs/design/TOKENS.md` (abstract token contract). SOT = `docs/biz/BUSINESS_CONTEXT_SOT.md` v2.1.

## 1. Context

- From-scratch rebuild of the Yaobet player web app, brand name kept, everything re-skinned; the old mock and its token contract are reference only, never copied (SOT §1 lines 19, 21; §5 OQ-01, OQ-07; `docs/STATUS.md:32`). Phase 1 is the complete UI on mock data, no backend (SOT §1 line 20; §5 OQ-04).
- "Hype" is reopened: the design is judged on first-sight pull (SOT §2 line 37; OQ-02) and on cross-genre exploration across the 9 lobby categories (SOT §2 line 38; §1 line 25; OQ-03). What still binds: money shown truthfully (skeleton, error, "tạm dừng"), celebration only after money lands, no fabricated activity, anti-slop L-01, L-13, D-09, L-16, T-12, W-07 (SOT §2 line 39; §6 rule 12 line 137).
- Delivery is responsive web only, Vietnamese everywhere, 375 px first and 1440 px desktop, about 87% mobile (SOT §1 line 23; OQ-12). Token values are the owner's to fill later; the architecture must be abstract first (`docs/STATUS.md:10`; SOT §6 rules 2, 3 lines 127–128). Stack is fixed: Next.js 16 App Router, React 19, Tailwind v4 CSS-first, TypeScript, `src/` layout (`package.json` deps; `CLAUDE.md:13`). The scaffold currently theme-switches on `prefers-color-scheme` with two hex literals and loads Geist with the `latin` subset only under `lang="en"` (`src/app/globals.css:15-19`, `src/app/layout.tsx:8,13,23`).

## 2. Decision

YAGNI rung selected: 4 (platform feature). Tailwind v4 `@theme` plus CSS custom properties already give layered theming, utility generation and runtime re-skin; no token build tool, no CSS-in-JS, no component library is needed to satisfy phase 1. Rungs 1–3 fail: the scaffold has no semantic layer and no repo utility exists (fresh scaffold).

1. **Theming: Tailwind v4 CSS-first.** Tokens are CSS custom properties in `src/styles/`; semantic tokens that match a Tailwind namespace are declared inside `@theme static` (not `@theme inline`; `static` because Tailwind v4 drops unused theme variables from the built CSS, and the owner fill in TOKENS.md §6 targets tokens no utility may reference yet) so utilities emit `var(--token)` and a brand override cascades at runtime (amendment 2026-11-04 after the critical-planner review; verified by leaf 1.1.1 gates G5 and G8). Tailwind's default palette and breakpoints are reset (`--color-*: initial`, `--breakpoint-*: initial`) so a builder physically cannot reach `bg-red-500`; only named semantic tokens produce utilities. Mapping rule and namespaces: `TOKENS.md` §2.
2. **Three token layers.** Primitive (`--raw-*`, brand-owned values, never used in components) → semantic (`--color-*`, `--space-*`, `--radius-*`, `--motion-*`, the only layer builders consume) → component (`--button-*`, `--money-*`, declared next to the component, referencing semantic tokens only). All values are `TBD (owner)` except structural defaults (spacing step, z ladder, breakpoints, touch sizes, motion timings), which the owner may still override.
3. **Dark-first, single scheme in phase 1.** `:root` carries the dark theme; the scaffold `prefers-color-scheme` block is deleted. A future light or sibling-brand theme is an attribute scope (`[data-brand]`) that overrides primitives only (SOT §1 line 21, pm DEFAULT for sibling re-skin).
4. **Components consume tokens through Tailwind utility classes.** No CSS Modules, no inline `style` colour or size, no hex/px literals in `.tsx` (verification: `rg -n "#[0-9a-fA-F]{3,8}|[0-9]+px" src/components src/app` must return only `src/styles/**`). Component-level CSS exists only in `src/styles/components.css` under `@layer components` for the five shared primitives (button, surface, money, skeleton, state-block). Arbitrary-value utilities are allowed only in the `name-(--token)` form.
5. **File layout (proposal for the PM's Story Shards).**
   - `src/app/` — routes, Vietnamese slugs from SOT §4: `/` home, `/sanh-game` lobby and `/sanh-game/[category]` for the 9 category pages (PM decision 2026-11-04; categories from SOT §1 line 25), `/tai-khoan`, `/vi-tien` (deposit, withdraw with status model requested → checking → paid / needs action, SOT §2 line 32), `/vip`, `/hoan-tra`, `/cuoc-hop-le`, `/cua-hang`, `/gioi-thieu`, `/khuyen-mai`, `/bo-suu-tap`, `/ve-so`, `/tin-nhan`, `/ho-tro` support stubs (PM decision 2026-11-04). No `/tier`, no `/dai-ly` agent ladder (SOT §4 4.1, 4.5).
   - `src/styles/` — `tokens.css` (semantic `@theme` + `:root` non-namespaced), `brand.yaobet.css` (primitive values, owner-filled), `components.css`. `src/app/globals.css` only imports these.
   - `src/components/ui/` shared primitives · `src/components/layout/` AppShell, TopBar (bell), BottomNav (mobile), SideNav (≥ 1024) · `src/components/<surface>/` one folder per route.
   - `src/lib/types/` domain types · `src/lib/mock/` typed fixtures · `src/lib/data/` accessors (the swap point) · `src/lib/format/` money and date via `Intl` (rung 2).
6. **Mock-data strategy: one swap point.** Components import only `@/lib/data/*` async accessors (`getWallet()`, `getLobby()`, …) that today return fixtures from `@/lib/mock/*` and later call an API; a `rg -n "lib/mock" src/components src/app` must return nothing. Every fixture exports four variants — `ready`, `loading`, `error`, `stale` — so skeleton, error and "tạm dừng" states are rendered from data, not toggled ad hoc. Money is an integer đồng `number` formatted with `Intl.NumberFormat("vi-VN")`; every đồng figure traces to a tagged SOT §3/§4 line or is `[OWNER DATA]` with a structural placeholder; hand-set reward amounts end in 6 or 8 and contain no 4 (SOT §3 line 57). No fixture carries live-player counts, tickers or "N người đang chơi" (SOT §2 line 39).
7. **Motion budget.** At most one autonomous animation per viewport (the home hero) plus skeleton shimmer; every other motion is user-triggered and ≤ `--motion-duration-base`. Celebration motion is bound to a single `money-landed` fixture event and nowhere else (SOT §2 line 39). `prefers-reduced-motion` collapses durations to 0 except opacity fades (`TOKENS.md` §3.9). Implemented with CSS transitions and keyframes first; a library is an owner decision (§5).
8. **Responsive strategy.** 375 px is the base, not a breakpoint; single column, bottom navigation, thumb-reach primary actions. 768: two-column content, bottom nav stays. 1024: side navigation replaces bottom nav. 1440: page container `--size-container` with the lobby at 4–6 tiles per row. Every surface is designed at 375 and 1440 before 768/1024 are derived.
9. **Accessibility baseline.** `lang="vi"`; fonts loaded with the `vietnamese` subset; line-height never below `--leading-snug` on text with stacked diacritics; touch targets ≥ `--size-touch-min` (44 px); visible focus via `--ring-focus-*`; money never conveyed by colour alone (sign and label always present, L-16 forbids clipping amounts); WCAG 2.2 AA contrast is the acceptance test the owner's colour values must pass (4.5:1 text, 3:1 UI).
10. **Image and asset policy.** No competitor art, logos or pixel UI (SOT §1 line 27); no mascots or invented brand marks (SOT §6 rule 3); game thumbnails, provider logos and promo art are `[OWNER DATA]` rendered as neutral in-repo placeholder tiles (token-coloured, name as text) via `next/image` with explicit dimensions; no hotlinks; any asset added to the repo ships with its source and licence noted in `docs/design/ASSETS.md` (file created when the first asset lands).

## 3. Attraction and exploration principles

Each principle names the truth guardrail (SOT §2 line 39, §6 rule 12) that bounds it.

1. **One hero, real stakes.** Home above the fold is one dominant entry (a real game or a real promotion with its qualifier) and the brand promise "Nạp nhanh · Rút nhanh · Hoàn trả mỗi ngày" (SOT §2 line 33). Guardrail: no fabricated activity; the hero never shows counters, tickers or "đang thắng" feeds.
2. **Nine doors, equally lit.** The lobby exposes all 9 categories (SOT §1 line 25) as first-class entries in one rail, and cross-genre rows ("Thử thêm …") are built from fixed genre adjacency in the fixture, not from invented popularity. Guardrail: W-07, a category is expressed by one device (label + tile art), never badge + colour + icon + label; D-09, no "HOT"/"NEW" badge storms.
3. **Motion earns attention; it never fakes an outcome.** The single hero animation and hover/press feedback create pull; celebration exists only on `money-landed`. Guardrail: celebration only after money has landed; reduced-motion honoured.
4. **Money is the loudest truthful element.** Balance, cashback receipt and withdrawal status use `--color-money-*` and the four data states; "lên tới X%" always carries its category qualifier and no merged percentage is shown (SOT §3 line 52; §4 line 88). Guardrail: skeleton while loading, error on error, "tạm dừng" when stale; no hidden outcome.
5. **Gold is the accent, never the surface; depth comes from surfaces, not boxes.** Gold goes on primary CTAs, key lines, hero and VIP headings, the active nav item, the current tier mark and focus rings; gold fills only the primary button and the VIP hero; money is never gold (`docs/design/BRAND.md` §4, owner direction 2026-11-04, supersedes the earlier "one gold element per viewport"). Hierarchy from canvas → surface → raised steps and imagery. Guardrail: L-01 no nested cards, L-13 no card soup, T-12 no icon fatigue.

## 4. Consequences

- Positive: builders have zero colour or size decisions; the owner fills `brand.yaobet.css` without touching components; sibling brands re-skin by overriding primitives; truth states are guaranteed by fixtures, not by builder discipline; anti-slop checks become mechanical (`rg` gates above).
- Resolved (PM 2026-11-04): colour roles were renamed `bg` → `surface`, `text` → `fg`, `border` → `line` so utilities read `bg-surface-raised`, `text-fg-primary`, `border-line-subtle` without a doubled prefix.
- Negative: until the owner fills values the app renders in placeholder greys, so first-sight pull cannot be judged before the fill step; resetting Tailwind defaults means every needed token must be named up front (`TOKENS.md` is therefore exhaustive).
- Neutral: the `lib/data` swap point adds one indirection per surface; no library is added in phase 1 unless the owner takes an option in §5.

## 5. Alternatives considered

```yaml
tradeoffs:
  - option: A. Scaffold defaults + prefers-color-scheme (rung 1)
    pros: [zero work]
    cons: [no semantic layer, no sibling re-skin, unintended light flip on user OS, builders pick hex values]
    verdict: rejected
  - option: B. Tailwind v4 @theme + 3 token layers, dark-first (rung 4)   # chosen
    pros: [platform feature, runtime re-skin, utilities only emit tokens, defaults can be disabled]
    cons: [verbose utility names, exhaustive naming required before first build]
    verdict: chosen
  - option: C. CSS Modules per component consuming tokens (rung 4)
    pros: [per-component scoping]
    cons: [two styling surfaces to review, anti-slop review slower, duplicates Tailwind]
    verdict: rejected
  - option: D. JSON tokens + Style Dictionary build step (rung 6)
    pros: [multi-platform export]
    cons: [new dependency and build step for a web-only phase 1; CSS file is already the source]
    verdict: deferred until a non-web consumer exists
```

Dependencies left to the owner (not decided here; each is an owner decision (dependency), rung 6):

- UI primitives: (1) none — native elements + Tailwind, recommended for phase 1; (2) a headless primitive set (Radix Primitives or Base UI) only for dialog, tabs, popover accessibility. Icons: (1) hand-made inline SVG sprite, recommended given T-12; (2) `lucide-react`.
- Animation: (1) CSS transitions/keyframes plus the View Transitions API, recommended; (2) `motion` (Framer Motion) for the hero and the money-landed celebration only.

## 6. Verification of this ADR

- Both files exist: `test -f docs/design/ADR-001-design-direction.md docs/design/TOKENS.md`.
- Acceptance: owner marks Status `accepted`; PM turns §2.5 into Story Shards; `critical-planner` runs the adversarial gate before the first builder wave (`docs/STATUS.md:19-20`).

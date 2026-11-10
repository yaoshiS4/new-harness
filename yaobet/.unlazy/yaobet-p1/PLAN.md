# Plan: Yaobet phase-1 UI (complete player web app on mock data)

Scope: yaobet-p1 (this file: .unlazy/yaobet-p1/PLAN.md)
Depth: tree 3
Mode: orchestrated

## Contract

Decide before fan-out:

- Interfaces:
  - Tokens: `docs/design/TOKENS.md` v0.1 names every token; semantic utilities `bg-surface-*`, `text-fg-*`, `border-line-*`, `text-money-*`, `bg-status-*-bg`; non-namespaced vars via `name-(--var)`. Builders never add a token; a missing token is a `Fail:` report.
  - Data: components import only `@/lib/data/<module>` async accessors; every accessor returns `Promise<Fixture<T>>` where `Fixture<T> = { state: "ready"; data: T } | { state: "loading" } | { state: "error"; retry: true } | { state: "stale"; data: T; asOf: string }` (`src/lib/types/core.ts`, leaf 1.1.2). Accessors read `src/lib/mock/<module>.ts`; the `?state=` query is NOT used; fixture variant is picked by the accessor's `variant` argument (default `ready`). Money = integer đồng `number`; `formatDong(n)` in `src/lib/format/money.ts`.
  - Shared data modules (leaf 1.1.2): `core`, `catalog` (9 categories, providers, game tiles), `session` (auth state guest | member, user, balance), `promos`, `notifications`. Surface-specific modules are owned by their surface leaf (`src/lib/{types,mock,data}/<surface>.ts`).
  - Shell slots (leaf 1.2.2): `AppShell` renders `TopBar` (balance, bell, auth cluster), `BottomNav` (< 1024) / `SideNav` (>= 1024), `Footer`; pages render inside `<main>`; pages never render their own header or nav.
  - UI primitives (leaf 1.2.1): `Button`, `Surface`, `Money`, `Skeleton`, `StateBlock`, `Tabs`, `Sheet`, `Tile`, `Field`, `ProgressBar`, `Pill` (one per element), each consuming tokens only.
  - Routes (ADR-001 §2.5): `/`, `/sanh-game`, `/sanh-game/[category]`, `/vi-tien`, `/tai-khoan`, `/tin-nhan`, `/vip`, `/hoan-tra`, `/cuoc-hop-le`, `/cua-hang`, `/gioi-thieu`, `/khuyen-mai`, `/khuyen-mai/[id]`, `/bo-suu-tap`, `/ve-so`, `/ho-tro`. No `/tier`, `/dai-ly`, `/tai-app`, `/cau-lac-bo`.
- Ownership: one complete repository-relative glob set per leaf in the dispatch table; disjoint within every wave. `src/app/layout.tsx` is owned by 1.1.1 in wave 1 and by 1.2.2 in wave 2 (sequential, never concurrent).
- Dependencies: as in the dispatch table `Needs`.
- Host launch mode: Claude background Agents (`Agent` tool, `subagent_type: dev-fe`, `isolation: "worktree"`). The PM merges each verified worktree branch into `main` before releasing the lease.
- Wave policy: at most 2 builders concurrently; 7 planned waves (W1 1.1.1+1.1.2 · W2 1.2.1 · W3 1.2.2+1.3.1 · W4 1.3.2+1.3.3 · W5 1.3.4+1.3.5 · W6 1.3.6+1.3.7 · W7 1.3.8+1.3.9); rolling dispatch allowed once a wave's leaves are VERIFIED and merged.
- Fixture contract additions (critical-planner A4, A5): `Promotion { isFlagship, sections: { info, howTo, reward, conditions, example, terms } }`; `User.vip { tier, level, tierName, remainingToNext, nextLevelLabel }`; `session.recentGameIds`; `/tin-nhan` and the bell both read `getNotifications()` (one list). Wallet CTAs call `requestDeposit()` / `requestWithdrawal()` accessors that return `Fixture<WithdrawalRequest>` in state `ready` whose `data.status` is `"requested"` (the four-state `Fixture<T>` union is never extended); `"paid"` and `"needsAction"` appear only under `src/lib/mock`. `[OWNER DATA]` values never reach the screen as bracket text: they render through the `Pill` variant `pending` ("Đang cập nhật") from leaf 1.2.1, and the literal tag lives in a code comment. Every `page.tsx` exports `metadata.title`; every dynamic segment ships `loading.tsx`.
- Route decisions: `/game-han-che` is not a route; links point to `/cuoc-hop-le#game-han-che`. Lobby `/sanh-game` + `/sanh-game/[category]`.
- In-code provenance vocabulary (the only tags allowed in `src/`): `[OWNER DATA]`, `[PROVISIONAL]`, `[SPEC]`, `[APP]`, `[UNVERIFIED]`, `[DEFAULT]`, `SOT §n`. Never `OQ-nn`, wave or leaf ids.
- Lib-layer rule: files under `src/lib/{types,mock,data,format}` use relative value imports, `import type` for types, no `enum` / `namespace` / parameter properties, so `node --experimental-strip-types` can execute them in gates.
- Literal gate scope: hex only inside `className` / `style` strings; px only as class-scoped arbitrary values; `next/image` `sizes` strings are exempt. Worktrees are created by the PM under `.claude/worktrees/<leaf>` (branch `<leaf>`), with `node_modules` symlinked from the main checkout and `npx next typegen` run once so the global `PageProps` / `LayoutProps` types exist; the PM proves the baseline (`lint` + `tsc`) before dispatch. Builders never run `npm install`.
- Toolchain: Node 24, npm 11, Next 16.4.5 (Turbopack), React 19.3, Tailwind 4.3.4, TypeScript 5. Inside a worktree, Turbopack refuses a `node_modules` symlink ("files outside of the workspace root are not compiled"); the PM therefore bootstraps every worktree with a hard-linked copy, `rsync -a --link-dest="<main>/node_modules/" "<main>/node_modules/" node_modules/` (about 480 MB of links, no install, gitignored), after which the ledger-exact `npm run build` runs in the worktree; `npx next build --webpack` remains the fallback proof if the copy is missing. Root-segment pages (`src/app/page.tsx`) set `metadata.title = { absolute: "<Tên> — Yaobet" }` because Next applies the layout title template only to child segments (proven in wave 1). Checks run from the repository root with the login shell: `npm run lint`, `npx tsc --noEmit`, `npm run build`, `node scripts/verify-tokens.mjs`, `node scripts/verify-routes.mjs`. No new dependencies in phase 1 (ADR-001 §5 options are owner decisions; default none).
- Conventions: Vietnamese UI copy, English identifiers; copy strings live in `src/lib/copy/<surface>.ts` owned by the surface leaf; Server Components by default; `docs/research/NEXT16_TAILWIND4_CONVENTIONS.md` §4 do/do-not list binds; no plan or audit tags in code; no legal or regulatory text anywhere; money rules from `docs/biz/BUSINESS_CONTEXT_SOT.md` §3/§4 only, `[OWNER DATA]` rendered as structural placeholders; anti-slop L-01, L-13, D-09, L-16, T-12, W-07.
- Manual review: PM runs Stage A on every return; `frontend-qc` runs the anti-slop pass per surface leaf (manual gate evidence = its `Fail:`-free report); `oracle-review` + `hallucination-auditor` at root.

## Current contract inventory

Contract revision: 3 (2026-11-04: rev 2 added the owner palette and assets, C17 ACTIVE, C18–C19; rev 3 applied the critical-planner directives A1–A5, B1–B4, C1–C7, D1–D3, E1–E3, F1, G1: seven waves, 1.3.8 split into 1.3.8 + 1.3.9, verify-routes and page.tsx to 1.1.1, verify-content to 1.1.2, typegen in every G2, fixture contract additions, provenance vocabulary, C20–C22).

| ID | Required outcome or constraint | Owner | Observing gate or manual review | Disposition | Revision |
|---|---|---|---|---|---|
| C1 | Abstract token system with `TBD (owner)` values rendered as a neutral greyscale placeholder ramp; Tailwind defaults reset | 1.1.1 | leaf-1.1.1:G1–G5 | ACTIVE | 1 |
| C2 | Typed fixtures with four states and one data swap point; no component imports `lib/mock` | 1.1.2, 1.2.x, 1.3.x | leaf-1.1.2:G4, node-1.3:N3 | ACTIVE | 1 |
| C3 | Shell: top bar with truthful balance, bell with four notification types, bottom nav at 375, side nav at >= 1024, footer; `lang="vi"`, Vietnamese font subset | 1.2.2 | leaf-1.2.2:G1–G6 | ACTIVE | 1 |
| C4 | Every phase-1 route renders at 375 and 1440 with Vietnamese title and no horizontal scroll | 1.3.x, node-1.3 | node-1.3:N3 (`verify-routes.mjs`) | ACTIVE | 1 |
| C5 | Home pulls a first-time visitor: one hero, 9 category doors, one promo, brand promise; no fabricated activity | 1.3.1 | leaf-1.3.1:G1–G5 + frontend-qc | ACTIVE | 1 |
| C6 | Lobby pushes cross-genre exploration: category tabs, rails continue / popular / new / "thử thể loại khác" from fixed adjacency | 1.3.2 | leaf-1.3.2 + frontend-qc | ACTIVE | 1 |
| C7 | Wallet: deposit (5 rails incl. crypto), withdraw with visible status model requested → checking → paid / needs action, history, transfer; never a client-side success | 1.3.3 | leaf-1.3.3 + frontend-qc | ACTIVE | 1 |
| C8 | VIP with provisional ladder (5 tiers × 10 levels), one bar, no percentages on the level card; cashback receipt with "thể thao và nổ hũ" qualifier and the 1.00% base | 1.3.5 | leaf-1.3.5 + frontend-qc | ACTIVE | 1 |
| C9 | Points store per SOT §4 4.4 (full package, cooldown, escalation as points); contribution page browsable per-game table + "Game hạn chế" tab | 1.3.6 | leaf-1.3.6 + frontend-qc | ACTIVE | 1 |
| C10 | Referral single-level with resolved rate; promotions list + detail; no Lucky Wheel, no agent ladder | 1.3.7 | leaf-1.3.7 + frontend-qc | ACTIVE | 1 |
| C11 | Collection as a transparent album; scratch card hub with earned-and-bought cards and no consolation payment; support stub | 1.3.8 | leaf-1.3.8 + frontend-qc | ACTIVE | 1 |
| C12 | Account (profile, security centre, bank cards, crypto addresses) and messages | 1.3.4 | leaf-1.3.4 + frontend-qc | ACTIVE | 1 |
| C13 | Zero literals in components (hex, px font sizes, raw z, raw durations), zero `lib/mock` imports outside `lib/data` | all | leaf-1.1.1:G4 script reused by every leaf | ACTIVE | 1 |
| C14 | No new npm dependency; no legal text; no plan tags; no competitor art | all | root GATES.md G3–G5 | ACTIVE | 1 |
| C15 | Engagement metric for "play more" | owner | — | DEFERRED (OQ-03) | 1 |
| C16 | Withdrawal SLA figures | owner | — | DEFERRED (OQ-05) | 1 |
| C17 | Brand token values: six owner palette values (`docs/design/BRAND.md` §1) implemented as primitives; derived values as pm defaults; fonts, celebrate/hero durations still owner-pending | 1.1.1 | leaf-1.1.1:G6 | ACTIVE | 2 |
| C18 | Owner-supplied assets under `public/assets/` are used where they exist (logo source `/assets/images/logo.png`, rendered in the shell via the web-sized copy `/placeholders/logo-240.png` that 1.2.1 derives and logs in ASSETS.md; banners on home and promos; casino and sports art on lobby tiles); placeholders remain only as fallbacks; inventory in `docs/design/ASSETS.md` | 1.2.1, 1.2.2, 1.3.1, 1.3.2, 1.3.7 | root GATES.md G5, leaf gates G5 | ACTIVE | 2 |
| C19 | Golden-luxury gold rule per BRAND.md §4 replaces "one gold element per viewport" (money never gold; gold fill only on primary button and VIP hero) | all surfaces | frontend-qc manual gates | ACTIVE | 2 |
| C20 | Attraction: one hero with the single autonomous animation inside the motion budget (ADR-001 §2.7, §3.1) | 1.3.1 | leaf-1.3.1:G6, root G7 | ACTIVE | 2 |
| C21 | "Recommendations" for more genres = fixed adjacency rails from the catalog; the "Nổi bật" rail is an editorial `isFeatured` pick with no numbers; no popularity claims or personalisation in phase 1 (deliberate interpretation of OQ-03) | 1.1.2, 1.3.1, 1.3.2 | leaf-1.1.2:G5, leaf-1.3.2:G5 | ACTIVE | 3 |
| C22 | Footer carries "Tự đặt giới hạn" and the support link; an age line is an owner decision, not a builder default (rule 1) | 1.2.2 | leaf-1.2.2:G6 | OWNER_DECISION | 2 |
| C23 | Game launch route (`/game/[id]`) is out of phase 1: lobby tiles link to category hubs, category-grid tiles are non-interactive cards; recorded as a deliberate gap for the backend phase | 1.3.2 | wave-4 QC-06 | DEFERRED | 4 |

## State vocabulary

Leaf state is exactly one of WAITING, READY, IN-FLIGHT, VERIFIED, ABANDONED (see template). Branch state is OPEN, VERIFIED, or ABANDONED, derived from ledgers.

## Tree

- 1 Yaobet phase-1 UI .................. GATES.md
  - 1.1 Foundation ...................... gates/node-1.1.md
    - 1.1.1 Tokens and styles ........... gates/leaf-1.1.1.md
    - 1.1.2 Domain types, fixtures, data  gates/leaf-1.1.2.md
  - 1.2 Shell ........................... gates/node-1.2.md
    - 1.2.1 UI primitives ............... gates/leaf-1.2.1.md
    - 1.2.2 App shell and notifications . gates/leaf-1.2.2.md
  - 1.3 Surfaces ........................ gates/node-1.3.md
    - 1.3.1 Home ........................ gates/leaf-1.3.1.md
    - 1.3.2 Lobby ....................... gates/leaf-1.3.2.md
    - 1.3.3 Wallet ...................... gates/leaf-1.3.3.md
    - 1.3.4 Account and messages ........ gates/leaf-1.3.4.md
    - 1.3.5 VIP and cashback ............ gates/leaf-1.3.5.md
    - 1.3.6 Store and contribution ...... gates/leaf-1.3.6.md
    - 1.3.7 Referral and promotions ..... gates/leaf-1.3.7.md
    - 1.3.8 Collection and support ...... gates/leaf-1.3.8.md
    - 1.3.9 Scratch card ................ gates/leaf-1.3.9.md

## Leaf dispatch table

| Leaf | Owns | Needs | Tier | Planned wave | State |
|---|---|---|---|---|---|
| 1.1.1 | src/styles/**, src/app/globals.css, src/app/layout.tsx, src/app/page.tsx, scripts/verify-tokens.mjs, scripts/verify-routes.mjs | - | judgment | 1 | VERIFIED |
| 1.1.2 | src/lib/types/core.ts, src/lib/types/catalog.ts, src/lib/types/session.ts, src/lib/types/promos.ts, src/lib/types/notifications.ts, src/lib/mock/catalog.ts, src/lib/mock/session.ts, src/lib/mock/promos.ts, src/lib/mock/notifications.ts, src/lib/data/_fixture.ts, src/lib/data/catalog.ts, src/lib/data/session.ts, src/lib/data/promos.ts, src/lib/data/notifications.ts, src/lib/format/**, scripts/verify-format.mjs, scripts/verify-content.mjs | - | judgment | 1 | VERIFIED |
| 1.2.1 | src/components/ui/**, public/** (never public/assets/**), docs/design/ASSETS.md | 1.1.1, 1.1.2 | judgment | 2 | VERIFIED |
| 1.2.2 | src/components/layout/**, src/components/notifications/**, src/app/layout.tsx, src/app/not-found.tsx, src/app/error.tsx, src/app/global-error.tsx, src/app/loading.tsx, src/lib/copy/shell.ts | 1.2.1 | judgment | 3 | VERIFIED |
| 1.3.1 | src/app/page.tsx, src/components/home/**, src/lib/copy/home.ts | 1.2.1 | judgment | 3 | VERIFIED |
| 1.3.2 | src/app/sanh-game/**, src/components/lobby/**, src/lib/copy/lobby.ts | 1.2.2 | judgment | 4 | VERIFIED |
| 1.3.3 | src/app/vi-tien/**, src/components/wallet/**, src/lib/copy/wallet.ts, src/lib/types/wallet.ts, src/lib/mock/wallet.ts, src/lib/data/wallet.ts | 1.2.2 | judgment | 4 | VERIFIED |
| 1.3.4 | src/app/tai-khoan/**, src/app/tin-nhan/**, src/components/account/**, src/components/messages/**, src/lib/copy/account.ts, src/lib/copy/messages.ts, src/lib/types/account.ts, src/lib/mock/account.ts, src/lib/data/account.ts | 1.2.2 | judgment | 5 | VERIFIED |
| 1.3.5 | src/app/vip/**, src/app/hoan-tra/**, src/components/vip/**, src/components/cashback/**, src/lib/copy/vip.ts, src/lib/copy/cashback.ts, src/lib/types/vip.ts, src/lib/types/cashback.ts, src/lib/mock/vip.ts, src/lib/mock/cashback.ts, src/lib/data/vip.ts, src/lib/data/cashback.ts | 1.2.2 | judgment | 5 | VERIFIED |
| 1.3.6 | src/app/cua-hang/**, src/app/cuoc-hop-le/**, src/components/store/**, src/components/contribution/**, src/lib/copy/store.ts, src/lib/copy/contribution.ts, src/lib/types/store.ts, src/lib/types/contribution.ts, src/lib/mock/store.ts, src/lib/mock/contribution.ts, src/lib/data/store.ts, src/lib/data/contribution.ts | 1.2.2 | judgment | 6 | VERIFIED |
| 1.3.7 | src/app/gioi-thieu/**, src/app/khuyen-mai/**, src/components/referral/**, src/components/promos/**, src/lib/copy/referral.ts, src/lib/copy/promos.ts, src/lib/types/referral.ts, src/lib/mock/referral.ts, src/lib/data/referral.ts | 1.2.2 | judgment | 6 | VERIFIED |
| 1.3.8 | src/app/bo-suu-tap/**, src/app/ho-tro/**, src/components/collection/**, src/components/support/**, src/lib/copy/collection.ts, src/lib/copy/support.ts, src/lib/types/collection.ts, src/lib/mock/collection.ts, src/lib/data/collection.ts | 1.2.2 | judgment | 7 | WAITING |
| 1.3.9 | src/app/ve-so/**, src/components/scratch/**, src/lib/copy/scratch.ts, src/lib/types/scratch.ts, src/lib/mock/scratch.ts, src/lib/data/scratch.ts | 1.2.2 | judgment | 7 | WAITING |

**Owner hold (2026-11-05):** UI building is paused until the owner updates the design guideline. Wave 7 (1.3.8, 1.3.9) stays WAITING; the wave-5 QC fix shard is parked as unverified WIP on branch `qc5-fix` (2b0edb7, 7 files, QC-01..QC-10 partly applied, verification_cmd not yet green). G6 (frontend-qc) is open for 1.3.4-1.3.7. Resume: re-read the updated guideline, rebase `qc5-fix` on main, rerun its verification_cmd, then dispatch wave 7.

PM-owned, builder read-only: `eslint.config.mjs`, `next.config.ts`, `tsconfig.json`, `package.json`, `.gitignore`, `docs/**` except `docs/design/ASSETS.md` (1.2.1 appends rows), `.unlazy/**`. `src/app/layout.tsx` is owned by 1.1.1 in wave 1 and by 1.2.2 in wave 3; `src/app/page.tsx` by 1.1.1 in wave 1 and 1.3.1 in wave 3 (sequential handoffs, never concurrent).

`Owns` mirrors each leaf ledger's `OWNS:` header; reconcile before READY and before each claim.

## Status log

Append events to `.unlazy/yaobet-p1/status.log` via `node ~/.claude/skills/unlazy/scripts/gate-check.mjs --scope yaobet-p1 --log "<event>"`.

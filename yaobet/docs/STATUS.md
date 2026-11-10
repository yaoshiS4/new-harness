# Yaobet — Project Status

Single source of truth for where the project stands. The PM updates this file at every teardown; agents read it first on every task.

## Current State

- 2026-11-04: repository created. Next.js (App Router, TypeScript, Tailwind, `src/` layout) scaffolded with `create-next-app`; no application screens yet.
- Business SOT adopted: `docs/biz/BUSINESS_CONTEXT_SOT.md` v2.1 (owner answered all 16 open questions on 2026-11-04). Review record: `docs/biz/BUSINESS_CONTEXT_REVIEW.md`.
- Phase 1 scope (owner, OQ-04): the complete UI layout on mock data, no backend. Surfaces: home, game lobby, profile and account, deposit and withdraw, VIP, notifications, points and store, referral, promotions, cashback receipt, collection, messages, support stubs.
- Design direction: brand name Yaobet, everything re-skinned; "hype" = first-sight attraction; "play more" = more games and more genres. Token architecture: `docs/design/TOKENS.md` v0.1 (abstract) + `docs/design/BRAND.md` v0.2 (owner's six-value golden-dark palette, 2026-11-04; derived values are pm defaults). Gold rule: accent, never surface (BRAND.md §4).
- Owner assets (26 files, 9.1 MB) moved from the harness repo root to `public/assets/` and served as `/assets/...`; logo at `/assets/images/logo.png`; inventory and usage map in `docs/design/ASSETS.md`.
- 2026-11-05 to 2026-11-07: **UI rebuild delivered.** The UI was rebuilt exactly from the reference guide (`Igaming-Agent-1/.hc/ui-rebuild-guide`) under owner decisions D1 (exact rebuild of the running original), D2 (Tailwind with the ADR-002 token lint), D3 (reproduced defects go to `docs/rebuild/FIX-LIST.md`) and D4 (code replaced; the earlier build is kept at tag `archive/tailwind-v1`; branch `qc5-fix` stays parked). Plan and ledgers: `.unlazy/yaobet-rebuild/` (36 leaf ledgers plus integration I1, all merged). Rulings: `docs/rebuild/PM-RULINGS.md` (PR-01 to PR-48).
- 2026-11-07: root audit `.unlazy/yaobet-rebuild/GATES.md` A1-A12 all ticked with evidence on main 18091c9 (16/16 gates).
- 2026-11-10: **Wine-Gold design-system update delivered** (owner request: colour tokens, spacing/type/font rules, components). Review and owner decisions D-DS1 to D-DS25: `docs/design/DS-WINE-GOLD-REVIEW.md` §5; decision record `docs/design/ADR-003-wine-gold.md`; token mapping `docs/design/wine-gold/MAPPING.md`; decision trace `docs/design/wine-gold/G22-TRACE.md`; plan and shard ledger `.unlazy/yaobet-ds/` (`PLAN.md`, `task.md`). The last source change is the merge de4102c (class-rule fixes for the referral KPI grid and the product-card label). Root audit `.unlazy/yaobet-ds/GATES.md` G1-G25 all ticked with evidence; G23 oracle-review APPROVE, G24 hallucination audit PASS 86/86. Local only: nothing is pushed.

## In Progress

- Nothing in progress.

## Next Actions

1. Owner: approve removing the 22 Wine-Gold worktrees under `.claude/worktrees/` (`ds-*` plus one locked agent worktree) and their branches, plus the leftover `rb-F0` branch (all merged).
2. Owner: choose a follow-up fix shard from the Wine-Gold backlog in `.unlazy/yaobet-ds/task.md`. These issues predate the update (found by the G21 frontend-qc review on 635a4dc): P-1, a nested list card (L-01) in SecurityCenter.tsx and LinkedAccounts.tsx; P-2, ellipsis clipping (L-16) at 6 sites; P-3, per-row icons (T-12) in LinkedAccounts.tsx; P-4, the VipFaq `⌄` glyph; P-5, tap targets under 44 px in MemberSidebar.tsx and SecurityCenter.tsx. The task.md backlog also lists the referral link wrapping mid-token at 1440 px, the off-palette StepExplainer tiles (W-07) and the empty KPI band at 1440 px.
3. Owner: decide whether member pages should land at the top after client navigation (Next 16.4.5 scrolls to the new segment; the original's 16.2.9 does not). See FIX-LIST, PR-48 section.
4. Owner: work through `docs/rebuild/FIX-LIST.md` (defects reproduced from the original on purpose under D3) when a fix phase starts.
5. Owner data still open: real values for every `[PROVISIONAL]`/`[DEFAULT]` fixture (VIP ladder, referral rates, store ladder and balance, restricted-game list).

## Verification

- Authoritative commands: `npm run lint`, `npx tsc --noEmit`, `npm run build`.
- Delivery audit: run the CHECK lines of `.unlazy/yaobet-rebuild/GATES.md` from a clean `main`. The A5 screenshot gate expects `SHOTS OK 72/72`, using the justify rows in `.unlazy/yaobet-rebuild/checks/shot-justify.json` (owner ruling PR-48).
- Wine-Gold audit: run the VERIFY lines of `.unlazy/yaobet-ds/GATES.md` (G1-G25) one at a time from a clean `main`. G17 expects `SHOTS OK 72/72` against the baseline in `~/.cache/yaobet-ds/baseline`.
- Every builder return must carry fresh output with `exit_code: 0` from its `verification_cmd`; `frontend-qc` runs the anti-slop pass on every UI change.

## Risks

- Runtime version gap: the rebuild runs Next 16.4.5, the original 16.2.9 (owner: keep 16.4.5). Known effects: the scroll after client navigation on m375 member pages, and 307 instead of 200 plus a meta refresh for the redirect stubs under `next start` (dev matches the original).
- Clock-dependent elements outside the shot masks (commission timestamps, store cooldown chips) can push a future capture over the threshold.
- At 768 px the stacked member pages differ from the original by 0.39-0.45% in the same two bands. This is under the threshold, and the scroll cause is inferred, not probed.
- No engagement metric is defined yet (OQ-03 deferred); "play more" is a design goal without a number.
- Money figures in mock data must follow `docs/biz/BUSINESS_CONTEXT_SOT.md` §3 tags; live production values are `[UNVERIFIED]` (OQ-09 deferred).
- The UI is an exact rebuild of `Igaming-Agent-1/apps/web` by owner decision D1. Its defects are reproduced on purpose and listed in FIX-LIST.

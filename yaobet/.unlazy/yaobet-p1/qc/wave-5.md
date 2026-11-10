# QC round: wave 5 (account, messages, VIP, cashback)

Source: frontend-qc static audit of main dae5e1c / 8628c21. Verdict PASS-WITH-FIXES. PM decisions recorded 2026-11-05; fix shard runs on main once a wave-6 builder slot frees (<= 2 builders).

## Fix shard (dev-fe, main)

allowed_files:
- src/components/cashback/**
- src/components/vip/vip-hero.tsx
- src/components/messages/message-list.tsx
- src/app/tin-nhan/page.tsx
- src/app/tin-nhan/loading.tsx
- src/lib/copy/account.ts
- src/lib/copy/cashback.ts
- src/components/ui/money.tsx

| Id | Decision | Fix |
|---|---|---|
| QC-01 | FIX (blocker) | estimator on `level="base"`; muted strings stay muted only on base. Do not retune cream-500 |
| QC-02 | FIX (blocker) | vip-hero TITLE `leading-tight` -> `leading-snug` |
| QC-03 | FIX (blocker) | message-list action row `gap-x-(--size-hit-gap)`, drop `px-2` override on Button |
| QC-04 | FIX | remove `max-w-3xl` from /tin-nhan page and loading roots (shell owns width) |
| QC-05 | FIX | account hints reworded without digits (owner rule: no invented numbers); form unchanged |
| QC-06 | FIX | cashback header error renders `StateBlock kind="error"` (or Money state error) + retry, never muted text |
| QC-07 | FIX (primitive) | Money gains `staleLabel?: boolean` (default true, behaviour unchanged elsewhere); receipt and history pass `staleLabel={false}` because a region-level `role="status"` paused line exists |
| QC-08 | FIX | receipt column gets an h2 + `<section aria-labelledby>` like its siblings |
| QC-09 | FIX | cashback h2 -> `text-fg-primary` (BRAND §4 sanctions gold headings on hero and VIP only) |
| QC-10 | FIX | copy: "Hạng {tier} · cộng thêm, tính riêng." |
| QC-11 | DEFER | "Xóa" with no undo is acceptable for the phase-1 mock; backend wave adds confirm/undo |

Residual (eyeball at 375/1440 after the fix): 2FA factor row wrap, VIP benefits right cell nowrap; keep fg-link off raised-quiet.

verification_cmd: npm run lint && npx tsc --noEmit && npm run build && node scripts/verify-tokens.mjs && node scripts/verify-content.mjs && node scripts/verify-routes.mjs /tai-khoan /tin-nhan /vip /hoan-tra && ! rg -n "leading-tight" src/components/vip/vip-hero.tsx && ! rg -n "max-w-3xl" src/app/tin-nhan && ! rg -n "px-2" src/components/messages/message-list.tsx && ! rg -n '\d ký tự|\d chữ số' src/lib/copy/account.ts && echo QC5_FIX_OK

## Parked state (owner UI hold, 2026-11-05)

Branch `qc5-fix` at 2b0edb7, unverified (verification_cmd never run).
- Applied: QC-02, QC-03 (also dropped `-ml-2` and `px-2` on LINK), QC-04, QC-05, QC-10.
- Partial: QC-07 (Money `staleLabel` prop only; receipt/history call sites missing; history also needs its own role="status" paused line + copy key `history.paused`). QC-08 (copy key `CASHBACK.receipt.title` only; section + h2 missing).
- Open: QC-01, QC-06, QC-09.
- Incident: the worktree was removed mid-run; the builder's later edits fell into the main checkout (5 cashback files) and were reversed by it (patch at scratchpad accidental-main.patch). PM verified main clean at 7090211.
- Resume: new worktree from `qc5-fix` rebased on main; every builder Bash call guarded with `cd <worktree> || exit 1`.

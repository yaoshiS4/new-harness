# Yaobet — Workspace Guidelines (Claude Code SOTA Harness)

Vietnamese-language, mobile-first iGaming player web app, rebuilt from scratch. Phase 1 is the complete UI layout on mock data with no backend.

## Read first (SOT order)

1. `docs/STATUS.md` — current state, in-progress work, next actions.
2. `docs/biz/BUSINESS_CONTEXT_SOT.md` — the business SOT (v2.1). Every money figure, persona, product status and owner rule lives there. Never invent numbers, names or mascots; use `[OWNER DATA]`.
3. `docs/design/` — design-direction ADR and the token contract (abstract first; values filled later).

## Stack and commands

- Next.js (App Router) + React + TypeScript, Tailwind CSS, `src/` layout, import alias `@/*`.
- Dev: `npm run dev` · Lint: `npm run lint` · Types: `npx tsc --noEmit` · Build: `npm run build`.
- Authoritative verification for any UI change: `npm run lint && npx tsc --noEmit && npm run build`.

## Harness rules in this repo

- Root thread is the PM: plans, Story Shards, docs, configs. It never edits `src/**` (`root_may_edit_code: false` in `.claude/harness/guardrails.json`).
- Builders (`dev-fe`, `designer`, `debugger`) edit only inside their `allowed_files` lease; at most 2 concurrent, in separate worktrees.
- Every UI change passes `frontend-qc` (anti-slop: no nested cards L-01, card soup L-13, badge proliferation D-09, ellipsis clipping L-16, icon fatigue T-12, category over-expressing W-07) and `test-runner` with fresh exit codes before `oracle-review`.
- Vietnamese UI copy, English code. 375 px first, 1440 px desktop. Money is shown truthfully: skeleton while loading, error state on error, "tạm dừng" when stale; celebration only after a real outcome; no fabricated activity.
- No legal or regulatory content in any file (owner standing rule 1). No plan or audit tags in code comments.
- Update `docs/STATUS.md` at every teardown.

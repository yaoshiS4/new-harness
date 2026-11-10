# Gates: 1.3.6 Points store and contribution page

OWNS: src/app/cua-hang/**, src/app/cuoc-hop-le/**, src/components/store/**, src/components/contribution/**, src/lib/copy/store.ts, src/lib/copy/contribution.ts, src/lib/types/store.ts, src/lib/types/contribution.ts, src/lib/mock/store.ts, src/lib/mock/contribution.ts, src/lib/data/store.ts, src/lib/data/contribution.ts

Scope: the points store `/cua-hang` per the SPEC-FINAL point-exchange rulings and the public game-contribution page `/cuoc-hop-le` with its "Game hạn chế" tab, on mock data, at 375 and 1440.

Deliverable detail (read SOT §3 (points 1 = 1.000 ₫, lucky numbers, weights live: sports 100%, slots 15% / 20% by tier, others 0%), §4 4.3 (browsable per-game table, filters, tier values always visible, "tỷ lệ được tính" framing, no đồng figures, versioned with effective date, Game hạn chế tab orthogonal), §4 4.4 (full package every claim, escalation is a point cost, non-zero cooldown, no expiry, never the archived constants), §5 OQ-13; REFERENCE_APP_INVENTORY.md §2 Store, Contribution (copy); TOKENS.md §3.4):
- Store: `PointsHeader` with the points balance ("điểm", 1 điểm = 1.000 ₫ shown once), package grid on the 1-2-5 ladder generated from (P_min, P_max, n) per SOT §4 points-store bullet (example run 100.000 / 200.000 / 500.000 / 1.000.000 ₫ from `docs/biz/BUSINESS_CONTEXT_REVIEW.md` §2 §4.4 note; P_min, P_max, n, q are `[OWNER DATA]`, so the fixture tags the run `[DEFAULT]`; generated amounts are exempt from the lucky rule per OQ-13), each `Tile` with face value, base points, cooldown state ("Có thể đổi ngay" / "Thời gian chờ: hh:mm"), escalated cost when cooling ("Đổi sớm: N điểm") and three player states only: redeem as usual, redeem early, not enough points ("Thiếu N điểm"); `RedeemDialog` `Sheet` confirming "Nhận trọn gói" and the cooldown restart; terms list from the ruling; no vouchers with playthrough, no goods catalogue, no "Rút sau n vòng cược".
- Contribution: intro "Tỷ lệ được tính vào cược hợp lệ" with a version and effective-date line rendered as the pending `Pill` (values are `[OWNER DATA]`); `Tabs` "Tỷ lệ tính cược" / "Game hạn chế"; table rows per game (>= 24 from the catalog) with columns Trò chơi, Danh mục, Nhà cung cấp, Hạng 1–2, Hạng 3–5; values Thể thao 100%, Nổ hũ 15% / 20%, all others 0% (sub-products virtual sport, e-sports, baccarat, Tài Xỉu, Xóc Đĩa listed at 0%); search, category / provider / rate-bucket filters including a "0%" bucket, pagination 20 per page; note "Trò chơi 0% vẫn trả thưởng bình thường"; "Game hạn chế" tab: one list of about 30 games "chỉ áp dụng khi đang giữ khuyến mãi hoặc mã quà tặng", never marked on the rate table. No đồng figures, no climb weights, no "best value" ranking.
- Fixtures with four variants; no constants from the old app; the printed weights (Thể thao 100%, Nổ hũ 15% at Tier 1–2 / 20% at Tier 3–5, others 0%) are the owner-signed published page values and carry `[OWNER] published page (SOT §3 Weights live)` in the fixture; the production-code 0.20 note stays in a fixture comment tagged `[UNVERIFIED]` and is never printed; the "Game hạn chế" tab is reachable at `/cuoc-hop-le#game-han-che` (no separate route); the version stamp renders through the `Pill` variant `pending` ("Đang cập nhật") for the `[OWNER DATA]` version and date.

- [ ] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: 2026-11-05 dev-fe, branch leaf-1.3.6: "> yaobet@0.1.0 lint > eslint" (no findings) then "LINT_OK", exit 0

- [ ] G2: typecheck passes
  CHECK: npx next typegen && npx tsc --noEmit && echo TSC_OK
  EXPECT: TSC_OK
  EVIDENCE: 2026-11-05 dev-fe: "Generating route types... ✓ Types generated successfully", tsc --noEmit silent, then "TSC_OK", exit 0

- [ ] G3: production build passes
  CHECK: npm run build && echo BUILD_OK
  EXPECT: BUILD_OK
  EVIDENCE: 2026-11-05 dev-fe: Next.js 16.4.5 "✓ Compiled successfully", "✓ Generating static pages using 13 workers (21/21)", routes "◐ /cua-hang" and "◐ /cuoc-hop-le" (Partial Prerender), then "BUILD_OK", exit 0

- [ ] G4: token and import gates pass
  CHECK: node scripts/verify-tokens.mjs && node scripts/verify-content.mjs
  EXPECT: content verification passed
  EVIDENCE: 2026-11-05 dev-fe: "tokens verification passed" / "content verification passed", exit 0

- [ ] G5: both routes render; store has no playthrough voucher copy and no archived constants; contribution has the framing, both tabs, the live weights and a 0% bucket
  CHECK: node scripts/verify-routes.mjs /cua-hang /cuoc-hop-le && node -e "const fs=require('fs');const s=fs.readFileSync('src/lib/copy/store.ts','utf8')+fs.readFileSync('src/lib/mock/store.ts','utf8');if(/vòng cược|688[._ ]?000|0\.8\b|haircut|voucher/i.test(s)){console.log('store forbidden content');process.exit(1)}for(const k of ['Thiếu','Có thể đổi ngay','Thời gian chờ']){if(!s.includes(k)){console.log('missing store copy',k);process.exit(1)}}const c=fs.readFileSync('src/lib/copy/contribution.ts','utf8')+fs.readFileSync('src/lib/mock/contribution.ts','utf8');for(const k of ['tỷ lệ được tính','Game hạn chế','100%','15%','20%','0%']){if(!c.toLowerCase().includes(k.toLowerCase())){console.log('missing contribution',k);process.exit(1)}}if(/loại trừ|₫\s*\d|\d\s*₫/.test(fs.readFileSync('src/lib/copy/contribution.ts','utf8'))){console.log('contribution forbidden content');process.exit(1)}console.log('store and contribution verified')"
  EXPECT: store and contribution verified
  EVIDENCE: 2026-11-05 dev-fe: "ok /cua-hang -> 200 "Cửa hàng điểm — Yaobet"" / "ok /cuoc-hop-le -> 200 "Tỷ lệ tính cược theo trò chơi — Yaobet"" / "routes verification passed" / "store and contribution verified", exit 0

- [ ] G6: frontend-qc anti-slop pass at 375 and 1440 (table readable at 375 via stacked rows, one pill per package, filters as one control row) with zero open Fail items
  EVIDENCE: pending

# Gates: 1.3.7 Referral and promotions

OWNS: src/app/gioi-thieu/**, src/app/khuyen-mai/**, src/components/referral/**, src/components/promos/**, src/lib/copy/referral.ts, src/lib/copy/promos.ts, src/lib/types/referral.ts, src/lib/mock/referral.ts, src/lib/data/referral.ts

Scope: the single-level referral page `/gioi-thieu` and the promotions list `/khuyen-mai` with detail `/khuyen-mai/[id]`, on mock data, at 375 and 1440.

Deliverable detail (read SOT §4 4.5 (single level, resolved rate never "up to", no countdown nudges, never the friend's deposits / losses / game mix, reward set shape with caps TBD), §4 4.10 (campaign spec sections, one flagship), §3 (lucky numbers), §5 OQ-10 (campaign content is mock); REFERENCE_APP_INVENTORY.md §2 Referral, Promotions; shared `promos` fixture from leaf 1.1.2; NEXT16 brief (async params, notFound)):
- Referral: header with the member's resolved weekly rate as one line ("Bạn nhận 0,15% cược hợp lệ của bạn bè mỗi tuần", tier-dependent, tagged `[OWNER-directed shape]` in a fixture comment), invite tools (code, link, "Sao chép liên kết" / "Đã sao chép", share placeholder), KPI strip (số bạn bè hợp lệ, cược hợp lệ tuần này, hoa hồng dự kiến) as `Money` rows, per-friend list showing only masked name, metered eligible turnover and the referrer's own commission, three-step explainer "Mời → Bạn chơi → Bạn nhận", gift-code reward card for the first deposit with "[OWNER DATA]" conditions line (KYC trong 5 ngày, nạp tối thiểu, cược khoảng 3×), history. No agent ladder, no levels, no downline, no "lên tới", no countdowns.
- Promotions: hero of the one flagship promo, grid of promos with `Tile` (category `Pill` only), filters by category; detail page `await props.params`, `notFound()` on unknown id, sections "Thông tin chương trình", "Cách tham gia", "Phần thưởng", "Điều kiện", "Ví dụ" (worked example from the fixture), "Điều khoản & điều kiện"; every "lên tới X%" has its qualifier; no Lucky Wheel; `generateStaticParams` for the fixture ids; `loading.tsx` inside `[id]` (runtime params under Cache Components need a Suspense boundary).
- Referral fixtures with four variants; copy files for both.

- [ ] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: 2026-11-05 exit 0 | `> eslint` → LINT_OK

- [ ] G2: typecheck passes (dynamic promo route types regenerated)
  CHECK: npx next typegen && npx tsc --noEmit && echo TSC_OK
  EXPECT: TSC_OK
  EVIDENCE: 2026-11-05 exit 0 | ✓ Types generated successfully → TSC_OK

- [ ] G3: production build passes
  CHECK: npm run build && echo BUILD_OK
  EXPECT: BUILD_OK
  EVIDENCE: 2026-11-05 exit 0 | ✓ Generating static pages (27/27); ◐ /gioi-thieu, ◐ /khuyen-mai, /khuyen-mai/[id] (6 ids prerendered) → BUILD_OK

- [ ] G4: token and import gates pass
  CHECK: node scripts/verify-tokens.mjs && node scripts/verify-content.mjs
  EXPECT: content verification passed
  EVIDENCE: 2026-11-05 exit 0 | tokens verification passed · content verification passed

- [ ] G5: routes render (list, one detail, referral); referral copy has no agent ladder, "lên tới" or countdown; promo detail has the required sections
  CHECK: node scripts/verify-routes.mjs /gioi-thieu /khuyen-mai "/khuyen-mai/$(node --experimental-strip-types -e "import('./src/lib/mock/promos.ts').then(m=>console.log((m.PROMOS??m.promos)[0].id))")" /khuyen-mai/khong-co-404 && node -e "const fs=require('fs');if(!fs.existsSync('src/app/khuyen-mai/[id]/loading.tsx')){console.log('missing loading.tsx');process.exit(1)}const r=fs.readFileSync('src/lib/copy/referral.ts','utf8')+fs.readFileSync('src/lib/mock/referral.ts','utf8');if(/đại lý|cấp 2|tuyến dưới|lên tới|còn \d+ ngày|countdown/i.test(r)){console.log('referral forbidden content');process.exit(1)}for(const k of ['Sao chép liên kết','mỗi tuần']){if(!r.includes(k)){console.log('missing referral copy',k);process.exit(1)}}const p=fs.readFileSync('src/lib/copy/promos.ts','utf8');for(const k of ['Thông tin chương trình','Cách tham gia','Phần thưởng','Điều kiện','Ví dụ','Điều khoản & điều kiện']){if(!p.includes(k)){console.log('missing promo section',k);process.exit(1)}}const d=fs.readFileSync('src/app/khuyen-mai/[id]/page.tsx','utf8');if(!d.includes('notFound')||!d.includes('await')){console.log('detail page contract');process.exit(1)}console.log('referral and promos verified')"
  EXPECT: referral and promos verified
  EVIDENCE: 2026-11-05 exit 0 | ok /gioi-thieu -> 200 "Giới thiệu bạn bè — Yaobet" · ok /khuyen-mai -> 200 "Khuyến mãi — Yaobet" · ok /khuyen-mai/thuong-nap-dau -> 200 "Thưởng 100% nạp đầu — Yaobet" · ok /khuyen-mai/khong-co-404 -> 404 · routes verification passed · referral and promos verified

- [ ] G6: frontend-qc anti-slop pass at 375 and 1440 (one pill per promo tile, no badge storms, KPI strip as rows not cards) with zero open Fail items
  EVIDENCE: pending

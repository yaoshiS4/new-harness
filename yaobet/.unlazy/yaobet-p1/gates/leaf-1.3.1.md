# Gates: 1.3.1 Home

OWNS: src/app/page.tsx, src/components/home/**, src/lib/copy/home.ts

Scope: the home page that pulls a first-time visitor in at first sight and opens the nine genre doors, on mock data, at 375 and 1440.

Deliverable detail (read ADR-001 §3 (all five principles), §2.7 motion budget; SOT §1 (categories), §2 (attraction goal, promise, truth guardrails); REFERENCE_APP_INVENTORY.md §2 Home; PLAN.md Interfaces):
- Above the fold at 375: one hero (the single autonomous animation of the app, `--motion-duration-hero`, final frame under reduced motion) showing one real promotion from `getPromos()` with its qualifier, one primary CTA "Chơi ngay" to `/sanh-game` and one secondary "Xem khuyến mãi"; directly below, the nine category doors in one scrollable rail (label + placeholder tile art, W-07: one device per category) linking to `/sanh-game/[category]`.
- Below: "Tiếp tục chơi" row (member fixture only; guest sees "Bắt đầu với" + three doors), "Nổi bật" rail from `isFeatured` (editorial, no numbers), "Mới" rail from `isNew`, a VIP teaser that shows the member's real tier and next concrete đồng target (from `User.vip.remainingToNext`) or the guest line "Tham gia hạng VIP Yaobet" (gold per BRAND.md §4: accent text and lines, no gold fill), and the brand promise strip "Nạp nhanh · Rút nhanh · Hoàn trả mỗi ngày" with the qualifier.
- 1440: hero and doors in a two-column composition, rails at 4–6 tiles per row inside `--size-container`.
- Forbidden: jackpot counters, live-win tickers, player counts, countdown pressure, "đang thắng" feeds, infinite scroll, gold surface fills other than the primary button (BRAND.md §4).
- All reads via `@/lib/data/*` inside `<Suspense>` with Skeleton fallbacks sized to the final layout.
- `page.tsx` keeps `metadata.title = { absolute: "Trang chủ — Yaobet" }` (the layout template does not apply to the root segment; wave-1 finding). `globals.css` already scopes the Tailwind scan with `source("../")`; do not change it.

- [ ] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: pending

- [ ] G2: typecheck passes
  CHECK: npx next typegen && npx tsc --noEmit && echo TSC_OK
  EXPECT: TSC_OK
  EVIDENCE: pending

- [ ] G3: production build passes
  CHECK: npm run build && echo BUILD_OK
  EXPECT: BUILD_OK
  EVIDENCE: pending

- [ ] G4: token and import gates pass
  CHECK: node scripts/verify-tokens.mjs && node scripts/verify-content.mjs
  EXPECT: content verification passed
  EVIDENCE: pending

- [ ] G5: home renders in the route sweep and contains the nine door slugs and the qualified promise; no forbidden activity strings
  CHECK: node scripts/verify-routes.mjs / && node -e "const fs=require('fs');const s=fs.readdirSync('src/components/home').map(f=>fs.readFileSync('src/components/home/'+f,'utf8')).join('')+fs.readFileSync('src/lib/copy/home.ts','utf8')+fs.readFileSync('src/app/page.tsx','utf8');for(const r of [/người đang chơi/i,/đang thắng/i,/jackpot/i,/countdown/i,/setInterval/]){if(r.test(s)){console.log('forbidden',r);process.exit(1)}}if(!s.includes('thể thao và nổ hũ')||!s.includes('/sanh-game/')){console.log('home contract');process.exit(1)}console.log('home contract verified')"
  EXPECT: home contract verified
  EVIDENCE: pending

- [ ] G6: frontend-qc anti-slop pass at 375 and 1440 with zero open Fail items; BRAND.md §4 gold rule confirmed (gold fill only on the primary button); hero motion within budget
  EVIDENCE: pending

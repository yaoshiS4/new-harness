# Gates: 1.3.5 VIP and cashback receipt

OWNS: src/app/vip/**, src/app/hoan-tra/**, src/components/vip/**, src/components/cashback/**, src/lib/copy/vip.ts, src/lib/copy/cashback.ts, src/lib/types/vip.ts, src/lib/types/cashback.ts, src/lib/mock/vip.ts, src/lib/mock/cashback.ts, src/lib/data/vip.ts, src/lib/data/cashback.ts

Scope: the VIP programme page `/vip` with the provisional ladder and the cashback receipt `/hoan-tra`, on mock data that follows the SOT money invariants exactly, at 375 and 1440.

Deliverable detail (read SOT §3 (cashback two lines, 1.00% flat base `[OWNER]`, apex rates, no merged percentage, points, lucky numbers), §4 VIP ruling bullet (one bar, concrete đồng targets, no weights or percentages on the level card; 5 tiers × 10 levels; entry 30M đ `[OWNER]`; tier names: specs Tier 1–5, app Đồng / Bạc / Vàng / Bạch Kim / Kim Cương `[APP]`; crossing cash 888K / 6.888M / 68.888M / 288.888M đ `[SPEC placeholder]`; tier benefits host, withdrawal-speed pass from Tier 3, loss-secure from Tier 3 `[SPEC]`), §4 4.2 (receipt), §5 OQ-11, OQ-14; REFERENCE_APP_INVENTORY.md §2 VIP, Cashback; BRAND.md §4 gold rule (the VIP hero is the one surface allowed a gold fill)):
- `/vip` member view: `ProgressBar` "Vòng cược lên hạng kế tiếp" with the current tier + level and a concrete đồng remaining ("Còn 1.888.000 ₫ để lên Cấp 12"), gold on the current tier mark, headings and lines, gold fill only on the hero; "Bậc thang VIP" as five tier rows each with 10 levels (collapsed): Tier 1 Level 1 entry = 30.000.000 ₫ `[OWNER]`, the other 49 thresholds `[PROVISIONAL]` re-anchored placeholders (never the SHBET production anchors as targets); crossing cash at L11 / L21 / L31 / L41 with the `[SPEC placeholder]` amounts; "Quyền lợi theo hạng" table with the three SOT benefits (host, withdrawal-speed pass from Tier 3 worded without any time figure, loss-secure from Tier 3) `[SPEC]`; "Câu hỏi thường gặp" three items. Guest view: "Tham gia hạng VIP Yaobet" + "Đăng ký ngay". No cashback percentage anywhere on the level card; no second ladder.
- `/hoan-tra`: today's receipt: "Hoàn trả hôm nay" `Money` (base line 1.00% of eligible turnover, shown as amount), period selector (Hôm nay / 7 ngày / Tháng này), lines "Cơ bản 1,00%" and "Khuyến mãi theo hạng (thể thao, nổ hũ)" as separate rows never summed into one percentage, per-category rows Thể thao / Nổ hũ with "Cược hợp lệ" and amount, other categories "0% hiện tại"; estimator: input a stake per category → shows the eligible turnover and the base cashback only; headline "Hoàn trả mỗi ngày — thể thao và nổ hũ"; history list; empty "Chưa có hoàn trả".
- Fixtures: amounts hand-set follow the lucky-number rule; rates limited to 1.00% base and the tier promo ladder from SOT §3; every printed figure carries its provenance tag in the fixture (`[OWNER]` 1.00% base and 30M entry, `[PROVISIONAL]` ladder thresholds, `[SPEC]` crossing cash and promo ladder, `[APP]` tier names); nothing tagged `[UNVERIFIED]` is printed; four variants.

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

- [ ] G5: both routes render; tier names are the app's five names tagged `[APP]`; no cashback percentage on the VIP page copy; receipt carries the qualifier and separate lines; no old-app rates
  CHECK: node scripts/verify-routes.mjs /vip /hoan-tra && node -e "const fs=require('fs');const v=fs.readFileSync('src/lib/copy/vip.ts','utf8')+fs.readFileSync('src/lib/mock/vip.ts','utf8');for(const t of ['Đồng','Bạc','Vàng','Bạch Kim','Kim Cương']){if(!v.includes(t)){console.log('missing tier',t);process.exit(1)}}if(/Tân thủ|0[.,]6\s*%|0[.,]8\s*%|1[.,]5\s*%/.test(v)){console.log('old-app rate or tier present');process.exit(1)}const mk=fs.readFileSync('src/lib/mock/vip.ts','utf8');for(const tag of ['[OWNER]','[PROVISIONAL]','[SPEC]','[APP]']){if(!mk.includes(tag)){console.log('missing provenance tag',tag);process.exit(1)}}if(/%/.test(fs.readFileSync('src/lib/copy/vip.ts','utf8'))){console.log('percentage on vip copy');process.exit(1)}const c=fs.readFileSync('src/lib/copy/cashback.ts','utf8');if(/\d\s*%\s*\+\s*\d\s*%|tổng cộng\s*\d/i.test(c)){console.log('summed percentage in cashback copy');process.exit(1)}if(!c.includes('thể thao và nổ hũ')||!c.includes('1,00%')||!c.includes('Chưa có hoàn trả')){console.log('cashback contract');process.exit(1)}console.log('vip contract verified')"
  EXPECT: vip contract verified
  EVIDENCE: pending

- [ ] G6: frontend-qc anti-slop and money-truth pass at 375 and 1440 (BRAND.md §4 gold rule: fill only on the hero, money never gold; one bar; no badge storms on the ladder; receipt lines never merged) with zero open Fail items
  EVIDENCE: pending

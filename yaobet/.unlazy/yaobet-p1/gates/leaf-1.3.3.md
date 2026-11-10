# Gates: 1.3.3 Wallet

OWNS: src/app/vi-tien/**, src/components/wallet/**, src/lib/copy/wallet.ts, src/lib/types/wallet.ts, src/lib/mock/wallet.ts, src/lib/data/wallet.ts

Scope: the wallet `/vi-tien` with deposit, withdraw, history and transfer tabs on mock data, showing money truthfully and a visible withdrawal status model, at 375 and 1440.

Deliverable detail (read SOT §1 (deposit rails incl. crypto), §2 (withdrawal promise, status model requested → checking → paid / needs action, trust beats), §3 (lucky numbers), §4 4.14, §6 rule 12; REFERENCE_APP_INVENTORY.md §2 Wallet (copy strings to reuse); TOKENS.md §3.3–§3.4; ADR-001 §2.6):
- Header: `Money` balance (ready / loading / error "Không tải được số dư" / stale "tạm dừng") and "Lần nạp đầu" hint when `isFirstDeposit`.
- `Tabs` "Nạp tiền" / "Rút tiền" / "Lịch sử" / "Chuyển quỹ" with `#nap`, `#rut`, `#lich-su`, `#chuyen-quy` deep links.
- Deposit: five rails Ngân hàng, MoMo, ViettelPay, Thẻ cào, Crypto (USDT, converted to đồng, shown as "Quy đổi sang ₫ theo tỷ giá tại thời điểm xác nhận" placeholder, no rate number); amount `Field` with eight lucky preset chips (all pass `isLuckyAmount`); rail-specific blocks (bank memo with "Sao chép nội dung" / "Đã sao chép"; QR slot for MoMo/ViettelPay; serial + code for Thẻ cào; address + network for crypto); first-deposit card "Ưu đãi lần nạp đầu" with "Tối thiểu để đủ điều kiện:" followed by the `Pill` variant `pending` ("Đang cập nhật") for the `[OWNER DATA]` minimum (no number; the old app's value is `[APP]` and not a business decision; the tag stays in a comment in `copy/wallet.ts`); CTA "Tôi đã chuyển" calls `requestDeposit()` from `src/lib/data/wallet.ts`, which returns `Fixture<DepositRequest>` in state `ready` with `data.status === "requested"` → pending screen "Đang chờ xác nhận" with the inventory body copy and "Quay lại". Never a client-side success.
- Withdraw: amount `Field`, "Tài khoản nhận" (bank · masked account) or "Chưa có tài khoản nhận — thêm trong mục Bảo mật trước khi rút.", error "Số tiền vượt quá số dư khả dụng.", CTA "Yêu cầu rút tiền" calls `requestWithdrawal()` which returns `Fixture<WithdrawalRequest>` in state `ready` with `data.status === "requested"` → status timeline component with the four states requested ("Đã gửi yêu cầu") → checking ("Đang kiểm tra") → paid ("Đã chuyển") / needs action ("Cần bổ sung thông tin"), each mapped to the TOKENS §3.4 status pair; the `paid` and `needsAction` states exist only as fixture variants under `src/lib/mock/wallet.ts`, never set by a component; "vài phút" appears only as copy, no SLA numbers.
- `src/lib/mock/wallet.ts` exports `WALLET_PRESETS: readonly Dong[]` (eight lucky amounts) and `WITHDRAWAL_STATES`.
- History: filters Tất cả / Tiền vào / Tiền ra, rows type + signed `Money` + time + note; empty and filter-empty copy from the inventory. Transfer: product funds list, "Đổi chiều chuyển", pending "Đang chờ xử lý".
- `wallet` fixtures: balance, rails, presets, destinations, transactions, withdrawal statuses, with four variants.

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

- [ ] G5: wallet route renders; five rails, four withdrawal states and the no-success rule are present; presets are lucky amounts
  CHECK: node scripts/verify-routes.mjs /vi-tien && node --experimental-strip-types -e "import('./src/lib/mock/wallet.ts').then(m=>{const fs=require('fs');const c=fs.readFileSync('src/lib/copy/wallet.ts','utf8');for(const k of ['Nạp tiền','Rút tiền','Lịch sử','Chuyển quỹ','Ngân hàng','MoMo','ViettelPay','Thẻ cào','Crypto','Đang chờ xác nhận','Yêu cầu rút tiền','Đã gửi yêu cầu','Đang kiểm tra','Đã chuyển','Cần bổ sung thông tin','[OWNER DATA]']){if(!c.includes(k))throw new Error('missing copy '+k)}if(/thành công/i.test(c))throw new Error('client-side success copy');const p=m.WALLET_PRESETS;if(!Array.isArray(p)||p.length!==8)throw new Error('presets');for(const n of p){const v=String(n);if(v.includes('4')||!/[68]$/.test(v))throw new Error('unlucky preset '+v)}const comp=fs.readdirSync('src/components/wallet').map(f=>fs.readFileSync('src/components/wallet/'+f,'utf8')).join('');if(/[\"']paid[\"']/.test(comp))throw new Error('component sets paid');if(!comp.includes('requestWithdrawal')||!comp.includes('requestDeposit'))throw new Error('accessors not used');console.log('wallet contract verified')}).catch(e=>{console.log(e.message);process.exit(1)})"
  EXPECT: wallet contract verified
  EVIDENCE: pending

- [ ] G6: frontend-qc anti-slop and money-truth pass at 375 and 1440 (no nested surfaces in panels, Money states visible, status timeline readable, one CTA per panel) with zero open Fail items
  EVIDENCE: pending

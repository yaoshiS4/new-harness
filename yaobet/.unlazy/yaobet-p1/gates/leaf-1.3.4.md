# Gates: 1.3.4 Account and messages

OWNS: src/app/tai-khoan/**, src/app/tin-nhan/**, src/components/account/**, src/components/messages/**, src/lib/copy/account.ts, src/lib/copy/messages.ts, src/lib/types/account.ts, src/lib/mock/account.ts, src/lib/data/account.ts

`/tin-nhan` reads the shared `getNotifications()` (leaf 1.1.2): one list serves the bell and the page, so unread counts never diverge. No separate messages fixture.

Scope: the account page `/tai-khoan` (profile, security centre, bank cards, crypto addresses) and the message centre `/tin-nhan`, on mock data, at 375 and 1440.

Deliverable detail (read SOT §4 4.14; REFERENCE_APP_INVENTORY.md §2 Account, Messages; TOKENS.md §3.4 state tokens; PLAN.md Interfaces):
- Account: `ProfileHeader` (display name, member id, VIP tier name from session), "Hồ sơ cá nhân" basics, "Trung tâm bảo mật" with the five factors (name, phone, email, 2FA, withdrawal password) each with status unset / pending / verified / error as one `Pill` and a score line "Mức bảo mật: N/5"; sections "Mật khẩu đăng nhập", "Mật khẩu rút tiền", "Mã xác thực động (2FA)"; "Liên kết thẻ ngân hàng" list + "Thêm thẻ ngân hàng" (empty "Chưa liên kết thẻ ngân hàng"); "Địa chỉ ví" list (asset, network TRC20 / ERC20 / BEP20, masked) + "Thêm địa chỉ ví" (empty "Chưa thêm địa chỉ ví"). Actions open a `Sheet` with a `Field` form that ends in a pending state; no auth logic.
- Messages: list with filters Tất cả / Chưa đọc / Đã đọc, "N tin nhắn chưa đọc", "Đã đọc tất cả", per-row mark read and delete, empty "Chưa có tin nhắn" / "Các tin nhắn mới sẽ xuất hiện tại đây.", guest "Đăng nhập để xem tin nhắn của bạn.".
- Account fixtures with four variants; masked values only, no real-looking personal data. Messages page = the notification list with the filters above, read state toggled client-side.

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

- [ ] G5: both routes render and the contract strings and the four security statuses are present
  CHECK: node scripts/verify-routes.mjs /tai-khoan /tin-nhan && node -e "const fs=require('fs');const a=fs.readFileSync('src/lib/copy/account.ts','utf8');for(const k of ['Hồ sơ cá nhân','Mật khẩu rút tiền','Mã xác thực động (2FA)','Liên kết thẻ ngân hàng','Chưa liên kết thẻ ngân hàng','Địa chỉ ví','Chưa thêm địa chỉ ví']){if(!a.includes(k)){console.log('missing copy',k);process.exit(1)}}const t=fs.readFileSync('src/lib/types/account.ts','utf8');for(const s of ['unset','pending','verified','error']){if(!t.includes(s)){console.log('missing status',s);process.exit(1)}}const m=fs.readFileSync('src/lib/copy/messages.ts','utf8');for(const k of ['Chưa đọc','Đã đọc tất cả','Chưa có tin nhắn']){if(!m.includes(k)){console.log('missing message copy',k);process.exit(1)}}console.log('account contract verified')"
  EXPECT: account contract verified
  EVIDENCE: pending

- [ ] G6: frontend-qc anti-slop pass at 375 and 1440 (D-09: one status pill per factor; L-01: sections separated by spacing, not nested surfaces) with zero open Fail items
  EVIDENCE: pending

# Gates: 1.2.2 App shell and notifications

OWNS: src/components/layout/**, src/components/notifications/**, src/app/layout.tsx, src/app/not-found.tsx, src/app/error.tsx, src/app/global-error.tsx, src/app/loading.tsx, src/lib/copy/shell.ts

Scope: the responsive application shell mounted in the root layout: top bar with the owner logo, truthful balance, auth cluster and the notification bell panel; bottom navigation at < 1024 and side navigation at >= 1024; footer; root loading, not-found, error and global-error boundaries. Depends on the primitives from leaf 1.2.1 (wave 2) and runs in wave 3 alongside 1.3.1.

Deliverable detail (read ADR-001 §2.5, §2.8, §2.9, §3; SOT §4 4.9 (notifications), §2 (brand promise); REFERENCE_APP_INVENTORY.md §2 Messages and bell, §4; NEXT16 brief §2 (error.tsx props, Suspense); TOKENS.md §3.8 z ladder):
- `AppShell` wraps `children` in `<main>`; `TopBar`: the owner logo (`/placeholders/logo-240.png` from 1.2.1, `next/image` with explicit dimensions, `preload`, `alt="Yaobet"`), `Money` balance from `getBalance()` inside `<Suspense>` with a Skeleton, deposit `Button` ("Nạp tiền", gold primary), bell, member menu or guest cluster ("Đăng ký" / "Đăng nhập", no auth logic, links only). `BottomNav` renders the exported `BOTTOM_NAV` array from `src/lib/copy/shell.ts` in order: Trang chủ `/`, Sảnh game `/sanh-game`, Nạp (centre, `/vi-tien#nap`), Khuyến mãi `/khuyen-mai`, Tài khoản `/tai-khoan`; label-first, icon optional inside the 44 px target; active item in gold text. `SideNav` (>= 1024): the same five plus VIP, Hoàn trả, Cửa hàng điểm, Giới thiệu, Bộ sưu tập, Vé số, Tin nhắn, Hỗ trợ. `Footer`: logo, brand promise "Nạp nhanh · Rút nhanh · Hoàn trả mỗi ngày (thể thao và nổ hũ)", links Tỷ lệ tính cược `/cuoc-hop-le`, Game hạn chế `/cuoc-hop-le#game-han-che`, Hỗ trợ `/ho-tro`, and "Chơi có trách nhiệm" with "Tự đặt giới hạn" (no age line, no legal terms; C22 is an owner decision).
- `NotificationBell` + `NotificationPanel` (Sheet): list from `getNotifications()`, each row category icon, one-line title, <= 2 lines body, relative time, optional CTA "Xem chi tiết"; tap marks read; "Đánh dấu đã đọc tất cả"; unread pill capped "9+"; empty "Chưa có thông báo".
- `src/app/layout.tsx`: mounts `AppShell`; keeps `lang="vi"`, the font and the metadata from 1.1.1. `src/app/loading.tsx`: root Skeleton.
- `not-found.tsx` (metadata title "Không tìm thấy", one action "Về trang chủ"), `error.tsx` (`"use client"`, `{ error, retry }`, StateBlock with "Thử lại", root element carries `data-boundary="error"`), `global-error.tsx` with its own html/body and the same sentinel.
- `src/lib/copy/shell.ts`: every shell string, plus `export const BOTTOM_NAV = [...]` in render order.

- [ ] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: pending

- [ ] G2: typecheck passes
  CHECK: npx next typegen && npx tsc --noEmit && echo TSC_OK
  EXPECT: TSC_OK
  EVIDENCE: pending

- [ ] G3: production build passes with the shell mounted
  CHECK: npm run build && echo BUILD_OK
  EXPECT: BUILD_OK
  EVIDENCE: pending

- [ ] G4: token and import gates pass across layout and notifications
  CHECK: node scripts/verify-tokens.mjs && node scripts/verify-content.mjs
  EXPECT: content verification passed
  EVIDENCE: pending

- [ ] G5: route sweep passes on home and the not-found control with the shell mounted
  CHECK: node scripts/verify-routes.mjs / /khong-ton-tai-404
  EXPECT: routes verification passed
  EVIDENCE: pending

- [ ] G6: shell contract markers present (BOTTOM_NAV exported in order, four notification categories in the panel, error boundaries use retry and the sentinel, footer carries the qualified promise and no age line, logo used)
  CHECK: node --experimental-strip-types -e "import('./src/lib/copy/shell.ts').then(m=>{const fs=require('fs');const nav=(m.BOTTOM_NAV||[]).map(x=>x.label);const want=['Trang chủ','Sảnh game','Nạp','Khuyến mãi','Tài khoản'];if(JSON.stringify(nav)!==JSON.stringify(want))throw new Error('bottom nav '+JSON.stringify(nav));const b=fs.readFileSync('src/lib/copy/shell.ts','utf8');if(!b.includes('thể thao và nổ hũ'))throw new Error('promise qualifier');if(/18 tuổi/.test(b))throw new Error('age line present');const e=fs.readFileSync('src/app/error.tsx','utf8');if(!e.includes('retry')||!e.includes('use client')||!e.includes('data-boundary=\"error\"'))throw new Error('error.tsx contract');const n=fs.readdirSync('src/components/notifications').map(f=>fs.readFileSync('src/components/notifications/'+f,'utf8')).join('');for(const c of ['balance','reward','announcement','profile']){if(!n.includes(c))throw new Error('bell category '+c)}const l=fs.readdirSync('src/components/layout').map(f=>fs.readFileSync('src/components/layout/'+f,'utf8')).join('');if(!l.includes('logo-240'))throw new Error('logo not used');console.log('shell contract verified')}).catch(e=>{console.log(e.message);process.exit(1)})"
  EXPECT: shell contract verified
  EVIDENCE: pending

- [ ] G7: frontend-qc anti-slop pass on the shell at 375 and 1440 (label-first nav, one unread pill, no nested surfaces, no horizontal scroll) with zero open Fail items
  EVIDENCE: pending

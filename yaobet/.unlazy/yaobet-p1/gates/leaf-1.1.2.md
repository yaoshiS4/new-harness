# Gates: 1.1.2 Domain types, shared fixtures, data accessors, formatting, content gate

OWNS: src/lib/types/core.ts, src/lib/types/catalog.ts, src/lib/types/session.ts, src/lib/types/promos.ts, src/lib/types/notifications.ts, src/lib/mock/catalog.ts, src/lib/mock/session.ts, src/lib/mock/promos.ts, src/lib/mock/notifications.ts, src/lib/data/_fixture.ts, src/lib/data/catalog.ts, src/lib/data/session.ts, src/lib/data/promos.ts, src/lib/data/notifications.ts, src/lib/format/**, scripts/verify-format.mjs, scripts/verify-content.mjs

Scope: the shared domain layer every surface consumes (Fixture contract, money and date formatting, modules catalog, session, promos, notifications with four-state fixtures and async accessors) plus the repo-owned content gate script.

Lib-layer rule (binding for this leaf and every surface leaf's `src/lib/**` files): files under `src/lib/{types,mock,data,format}` use relative value imports, `import type` for type-only imports, and no `enum`, `namespace` or parameter-property syntax, so `node --experimental-strip-types` can execute them in gate scripts.

Deliverable detail (read PLAN.md Interfaces and Conventions; SOT §1 (categories, rails), §3 (money rules, lucky numbers), §4 4.9 (notification types), §4 4.10 (campaign spec sections); docs/research/REFERENCE_APP_INVENTORY.md §2 Home, Messages and bell, §3; ADR-001 §2.6; BRAND.md §5 for asset paths):
- `src/lib/types/core.ts`: `Fixture<T>` union (`ready | loading | error | stale`), `Dong = number` (integer đồng), `IsoDate`, `Variant`.
- `src/lib/data/_fixture.ts`: `pick<T>(variants, variant = "ready")` returning `Promise<Fixture<T>>` with <= 50 ms simulated latency and no randomness.
- `src/lib/format/money.ts`: `formatDong(n)` via `Intl.NumberFormat("vi-VN")` + ` ₫`; `isLuckyAmount(n)` (ends in 6 or 8, no digit 4); `signedDong(n, direction)`. `src/lib/format/date.ts`: `formatRelative(iso)` → "Vừa xong", "N phút trước", "N giờ trước", "N ngày trước"; `formatDateTime(iso)` → dd/mm/yyyy hh:mm.
- `catalog`: 9 categories in SOT order with slugs `the-thao`, `casino`, `no-hu`, `ban-ca`, `game-bai`, `xo-so`, `da-ga`, `ban-choi`, `game-nhanh`, label, gloss, iconId, and a fixed `adjacent: slug[]` list per category; providers (names only); >= 24 game tiles across categories with `isNew`, `isFeatured` (editorial "Nổi bật" pick, never a popularity claim), and `art` = an owner asset path under `/assets/images/casino` or `/assets/images/sports` where one fits (see `docs/design/ASSETS.md`) else a placeholder key. No RTP, no odds, no live counts.
- `session`: `AuthState = "guest" | "member"`; `User { displayName, memberId, vip: { tier (1–5), level (1–50), tierName (Đồng | Bạc | Vàng | Bạch Kim | Kim Cương), remainingToNext: Dong, nextLevelLabel: string } }`; `recentGameIds: string[]`; `Balance { available: Dong, asOf }` as a Fixture; `isFirstDeposit`.
- `promos`: >= 6 promotions with `isFlagship` (exactly one true), `category` (Thành viên mới | Thể thao | Sự kiện | Hoàn trả | Nạp tiền), `title`, `summary`, `qualifier` (mandatory on any "lên tới X%"), `endsAt | null`, `art` (owner banner path or placeholder), and `sections: { info, howTo, reward, conditions, example, terms }` each a string[]; no Lucky Wheel, no "28%"; hand-set amounts follow the lucky-number rule and carry a `// [SPEC]` or `// [OWNER DATA]` provenance comment.
- `notifications`: the four owner categories (balance: deposit, withdrawal · reward: point, money, giftCode · announcement: event, general · profile: levelUp) with `slots`, `read`, `at`, optional `ctaHref`; 8 items ordered by `at` desc; `unreadCount` capped at "9+" by the accessor. This one list serves both the bell and `/tin-nhan`.
- `scripts/verify-format.mjs`: runs the format functions via `node --experimental-strip-types` and asserts formatDong(1888000) contains "1.888.000", isLuckyAmount(888000) true, isLuckyAmount(400000) false, formatRelative(now) is "Vừa xong"; prints `format verification passed`.
- `scripts/verify-content.mjs`: zero-dependency global forbidden-content gate over `src/lib/copy`, `src/lib/mock`, `src/components`, `src/app`: fails on `vòng quay|lucky wheel|người đang chơi|đang thắng|jackpot|28\s*%|đại lý|tuyến dưới|an ủi|Tân thủ|0[.,]6\s*%|0[.,]8\s*%|1[.,]5\s*%` anywhere, on `1[.,]4\s*%` outside `src/lib/mock`, on `lên tới` lines lacking a qualifier word (thể thao | nổ hũ | qualifier), on `OQ-[0-9]|Wave [0-9]|leaf-1\.|UG-[0-9]` (plan tags), and on `nghị định|decree|giấy phép|licen[cs]e|statute|regulat` (owner rule 1); prints `content verification passed`. `--self-test` plants each pattern and must detect every one; prints `self-test passed`.

- [ ] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: pending

- [ ] G2: typecheck passes after route typegen
  CHECK: npx next typegen && npx tsc --noEmit && echo TSC_OK
  EXPECT: TSC_OK
  EVIDENCE: pending

- [ ] G3: production build passes
  CHECK: npm run build && echo BUILD_OK
  EXPECT: BUILD_OK
  EVIDENCE: pending

- [ ] G4: content gate passes on the tree and its self-test catches every planted pattern
  CHECK: node scripts/verify-content.mjs && node scripts/verify-content.mjs --self-test
  EXPECT: self-test passed
  EVIDENCE: pending

- [ ] G5: shared modules load and satisfy the contract when executed (9 categories with adjacency, exactly one flagship promo with six sections, four notification categories, User.vip fields, recentGameIds)
  CHECK: node --experimental-strip-types -e "import('./src/lib/mock/catalog.ts').then(async c=>{const cats=c.CATEGORIES??c.categories;if(!cats||cats.length!==9)throw new Error('categories');for(const s of ['the-thao','casino','no-hu','ban-ca','game-bai','xo-so','da-ga','ban-choi','game-nhanh']){if(!cats.some(x=>x.slug===s))throw new Error('slug '+s)}if(!cats.every(x=>Array.isArray(x.adjacent)&&x.adjacent.length))throw new Error('adjacency');const p=await import('./src/lib/mock/promos.ts');const promos=p.PROMOS??p.promos;if(promos.filter(x=>x.isFlagship).length!==1)throw new Error('flagship');for(const k of ['info','howTo','reward','conditions','example','terms']){if(!promos.every(x=>Array.isArray(x.sections?.[k])))throw new Error('section '+k)}const n=await import('./src/lib/mock/notifications.ts');const items=n.NOTIFICATIONS??n.notifications;const cat=new Set(items.map(x=>x.category));for(const k of ['balance','reward','announcement','profile']){if(!cat.has(k))throw new Error('notification '+k)}const s=await import('./src/lib/mock/session.ts');const u=s.MEMBER_USER??s.memberUser;if(!u?.vip||typeof u.vip.remainingToNext!=='number'||!u.vip.tierName)throw new Error('user.vip');if(!Array.isArray(s.RECENT_GAME_IDS??s.recentGameIds))throw new Error('recentGameIds');console.log('shared modules verified')}).catch(e=>{console.log(e.message);process.exit(1)})"
  EXPECT: shared modules verified
  EVIDENCE: pending

- [ ] G6: formatting functions verified by the repo-owned check
  CHECK: node scripts/verify-format.mjs
  EXPECT: format verification passed
  EVIDENCE: pending

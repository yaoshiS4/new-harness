# Gates: 1.3.8 Collection and support

OWNS: src/app/bo-suu-tap/**, src/app/ho-tro/**, src/components/collection/**, src/components/support/**, src/lib/copy/collection.ts, src/lib/copy/support.ts, src/lib/types/collection.ts, src/lib/mock/collection.ts, src/lib/data/collection.ts

Scope: the collection as a transparent album `/bo-suu-tap` and the support stub `/ho-tro`, on mock data, at 375 and 1440.

Deliverable detail (read the SOT §4 collection ruling bullet (per-collection theme, opens minted only by settled wagers, never purchasable `[OWNER]`; mechanic: duplicates become shards that buy missing cards at a published price, set completion pays cash with no rollover `[SPEC, v1.0 §4.8]`; set rewards and shard prices `[OWNER DATA]`; shard ◈ in SOT §9; EPL demo theme needs image rights, so use the owner's player images under `/assets/players/` only as neutral card art named by position, see `docs/design/ASSETS.md`), §5 OQ-15 (transparent album), §2 (celebration only on money-landed); REFERENCE_APP_INVENTORY.md §2 Collection, stubs; ADR-001 §2.7; PLAN.md Conventions (lib-layer rule, provenance vocabulary)):
- Album view per collection (one demo collection, 11 slots, deterministic progress "7/11"), "Lượt mở" counter earned from settled wagers with the explanation "Chỉ cược đã thanh toán mới tạo lượt mở; không thể mua lượt mở", an open action that reveals the next card from a published, visible sequence (no randomness, no rarity odds), duplicates → shards "◈" with a shard price per missing card and a set reward row, both `[OWNER DATA]` rendered through the pending `Pill` ("Đang cập nhật") next to the label "Không yêu cầu vòng cược", history sheet, "Thẻ của tôi" tab, terms sheet. No pity counters, no "rare 3.5%", no purchase action for opens (no `buyOpen` / `purchaseOpen` handler, no price on an open).
- Support `/ho-tro`: "Hỗ trợ khách hàng", contact list placeholder (chat 24/7, email), FAQ links to `/cuoc-hop-le` and `/vip`; no legal content.
- Fixtures with four variants; copy files for both; every page exports `metadata.title`.

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

- [ ] G4: token, import and content gates pass
  CHECK: node scripts/verify-tokens.mjs && node scripts/verify-content.mjs
  EXPECT: content verification passed
  EVIDENCE: pending

- [ ] G5: both routes render; the album has no randomness and no purchase action for opens, and carries the no-rollover line and the no-purchase explanation
  CHECK: node scripts/verify-routes.mjs /bo-suu-tap /ho-tro && node -e "const fs=require('fs');const comp=fs.readdirSync('src/components/collection').map(f=>fs.readFileSync('src/components/collection/'+f,'utf8')).join('');const all=fs.readFileSync('src/lib/copy/collection.ts','utf8')+fs.readFileSync('src/lib/mock/collection.ts','utf8')+comp;if(/Math\.random|pity|3[.,]5\s*%|rarity/i.test(all)){console.log('collection forbidden content');process.exit(1)}if(/buyOpen|purchaseOpen|muaLuotMo/i.test(comp)){console.log('purchase action present');process.exit(1)}if(!/không thể mua lượt mở/i.test(all)||!all.includes('Không yêu cầu vòng cược')){console.log('missing required explanation');process.exit(1)}console.log('collection verified')"
  EXPECT: collection verified
  EVIDENCE: pending

- [ ] G6: frontend-qc anti-slop pass at 375 and 1440 (album slots as one grid not nested cards, no badge storms, BRAND.md §4 gold rule) with zero open Fail items
  EVIDENCE: pending

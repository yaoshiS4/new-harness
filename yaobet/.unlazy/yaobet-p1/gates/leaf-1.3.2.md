# Gates: 1.3.2 Lobby

OWNS: src/app/sanh-game/**, src/components/lobby/**, src/lib/copy/lobby.ts

Scope: the game lobby `/sanh-game` and the nine category pages `/sanh-game/[category]` that push cross-genre exploration, on the catalog fixture, at 375 and 1440.

Deliverable detail (read ADR-001 §3.2, §2.8; SOT §1 (9 categories), §2 (play more = more games and more genres); REFERENCE_APP_INVENTORY.md §2 Lobby; NEXT16 brief §2 (async params, PageProps, notFound); PLAN.md Interfaces):
- `/sanh-game`: sticky category `Tabs` (all nine, label-first), always-visible search `Field` ("Tìm trò chơi", filters the fixture client-side), rails in order: "Tiếp tục chơi" (member only, from `recentGameIds`), "Nổi bật" (editorial `isFeatured`, no numbers), "Mới", then one "Thử thể loại khác" rail per adjacent genre from the catalog `adjacent` list; provider rail below the categories.
- `/sanh-game/[category]`: `await props.params`, `notFound()` on an unknown slug, metadata title `"<Label> — Yaobet"`, category banner (placeholder art + label + one line), grid of that category's tiles (2 per row at 375, 4–6 at 1440), and the "Thử thể loại khác" rail for its adjacent genres; `generateStaticParams` for the nine slugs.
- Tiles use `Tile` with at most one `Pill` ("Mới" or "Nổi bật", never both); labels never truncated; press feedback `--state-press-scale`.
- Loading state via `loading.tsx` with Skeleton tiles of the final aspect ratio; all reads via `@/lib/data/catalog` inside `<Suspense>`.
- Forbidden: popularity numbers, player counts, "hot" badge storms, infinite scroll, provider-first ordering.

- [ ] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: pending

- [ ] G2: typecheck passes (including generated route types for the dynamic segment)
  CHECK: npx next typegen && npx tsc --noEmit && echo TSC_OK
  EXPECT: TSC_OK
  EVIDENCE: pending

- [ ] G3: production build passes with the nine static params
  CHECK: npm run build && echo BUILD_OK
  EXPECT: BUILD_OK
  EVIDENCE: pending

- [ ] G4: token and import gates pass
  CHECK: node scripts/verify-tokens.mjs && node scripts/verify-content.mjs
  EXPECT: content verification passed
  EVIDENCE: pending

- [ ] G5: lobby and three category routes render, an unknown slug returns 404, and the cross-genre rail label is present
  CHECK: node scripts/verify-routes.mjs /sanh-game /sanh-game/the-thao /sanh-game/casino /sanh-game/no-hu /sanh-game/ban-ca /sanh-game/game-bai /sanh-game/xo-so /sanh-game/da-ga /sanh-game/ban-choi /sanh-game/game-nhanh /sanh-game/khong-co-404 && node -e "const fs=require('fs');if(!fs.existsSync('src/app/sanh-game/[category]/loading.tsx')){console.log('missing loading.tsx');process.exit(1)}const s=fs.readFileSync('src/lib/copy/lobby.ts','utf8');for(const k of ['Thử thể loại khác','Nổi bật','Mới','Tìm trò chơi']){if(!s.includes(k)){console.log('missing copy',k);process.exit(1)}}const p=fs.readFileSync('src/app/sanh-game/[category]/page.tsx','utf8');if(!p.includes('notFound')||!p.includes('generateStaticParams')||!p.includes('await')){console.log('category page contract');process.exit(1)}console.log('lobby contract verified')"
  EXPECT: lobby contract verified
  EVIDENCE: pending

- [ ] G6: frontend-qc anti-slop pass at 375 and 1440 with zero open Fail items (one pill per tile, labels unclipped, sticky tabs reachable one-handed)
  EVIDENCE: pending

# Gates: 1.2.1 UI primitives

OWNS: src/components/ui/**, public/**, docs/design/ASSETS.md

Never modify or delete anything under `public/assets/**` (owner-supplied). Delete the scaffold SVGs in `public/` (file, globe, next, vercel, window). Append a row to `docs/design/ASSETS.md` for every generated placeholder.

Scope: the shared primitive set every surface composes from, consuming tokens only: Button, Surface, Money, Skeleton, StateBlock, Tabs, Sheet, Tile, Field, ProgressBar, Pill, plus neutral placeholder images (fallbacks only, used where `docs/design/ASSETS.md` has no owner asset) for game art, provider logos, promo art and avatars, and a web-sized copy of the owner logo.

Deliverable detail (read ADR-001 §2.4, §2.7, §2.9, §3; TOKENS.md §3.12–§3.13, §4, §5; NEXT16 brief §4):
- `Button` (primary / secondary / ghost; rest, hover, press, focus-visible, disabled, loading; min height `--size-touch-min`); `Surface` (base / raised / sunken / overlay; never nests another Surface of the same level: enforce with a `level` prop and a dev warning); `Money` (`value`, `direction`, `state` → ready / loading / error / stale with "tạm dừng"; tabular numerals; sign + label; never colour alone); `Skeleton` (fixed aspect boxes, shimmer via `--animate-skeleton`, static under reduced motion); `StateBlock` (error / paused / empty with one message and one action: "Thử lại", "Đặt lại"); `Tabs` (keyboard, `aria-selected`, sticky option); `Sheet` (bottom sheet at < 1024, dialog at >= 1024, scrim, focus trap, Escape); `Tile` (game / promo tile with fixed aspect ratio, one optional `Pill` max, label never truncated); `Field` (label, input, hint, error); `ProgressBar` (one bar, concrete labels, no percentages unless passed); `Pill` (one status pair per element; includes the variant `pending` with the text "Đang cập nhật", used wherever a value is `[OWNER DATA]` so bracket text never reaches the screen).
- `public/placeholders/`: generated neutral SVG tiles (canvas/surface greys from BRAND.md, name as text) for game art 4:3, provider logo 3:1, promo art 16:9, avatar 1:1; plus `logo-240.png` (a 240 px wide resize of `/assets/images/logo.png` made with `sips`, logged in ASSETS.md); no external assets.
- `Tile` and the image-bearing primitives accept an `art` path and fall back to the placeholder family when the path is empty.
- Each primitive has a short usage comment at the top of its file. No examples route and no storybook in phase 1.

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

- [ ] G4: token and import gates pass across the primitives
  CHECK: node scripts/verify-tokens.mjs && node scripts/verify-content.mjs
  EXPECT: content verification passed
  EVIDENCE: pending

- [ ] G5: all eleven primitives and the four placeholder image families exist, Money renders the stale label, and Tile allows at most one Pill
  CHECK: node -e "const fs=require('fs');for(const c of ['button','surface','money','skeleton','state-block','tabs','sheet','tile','field','progress-bar','pill']){if(!fs.existsSync('src/components/ui/'+c+'.tsx')){console.log('missing primitive',c);process.exit(1)}}for(const p of ['game','provider','promo','avatar','logo']){if(!fs.readdirSync('public/placeholders').some(f=>f.startsWith(p))){console.log('missing placeholder family',p);process.exit(1)}}if(['file.svg','globe.svg','next.svg','vercel.svg','window.svg'].some(f=>fs.existsSync('public/'+f))){console.log('scaffold svg remains');process.exit(1)}if(!fs.existsSync('public/assets/images/logo.png')){console.log('owner assets touched');process.exit(1)}const m=fs.readFileSync('src/components/ui/money.tsx','utf8');if(!m.includes('tạm dừng')||!m.includes('tabular-nums')){console.log('money contract');process.exit(1)}const t=fs.readFileSync('src/components/ui/tile.tsx','utf8');if(!/pill\??:/i.test(t)){console.log('tile pill prop');process.exit(1)}const pl=fs.readFileSync('src/components/ui/pill.tsx','utf8');if(!pl.includes('pending')||!pl.includes('Đang cập nhật')){console.log('pill pending variant');process.exit(1)}console.log('primitives verified')"
  EXPECT: primitives verified
  EVIDENCE: pending

- [ ] G6: frontend-qc review of the primitives (focus rings visible on every variant including the gold primary button, where the ring reads through `--ring-focus-offset`; touch targets >= 44 px, Vietnamese diacritics not clipped at `--text-xl`, reduced-motion honoured) with zero open Fail items
  EVIDENCE: pending

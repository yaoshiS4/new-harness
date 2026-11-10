# Gates: 1.1.1 Tokens, styles, root layout, verification scripts

OWNS: src/styles/**, src/app/globals.css, src/app/layout.tsx, src/app/page.tsx, scripts/verify-tokens.mjs, scripts/verify-routes.mjs

Scope: implement `docs/design/TOKENS.md` v0.1 as the three-layer Tailwind v4 token system using the owner's golden-dark palette from `docs/design/BRAND.md` v0.2, dark-first, defaults reset, `lang="vi"` root layout with the Vietnamese font subset, a minimal token-only placeholder home page, and the two repo-owned gate scripts (tokens, routes).

Deliverable detail (read ADR-001 §2.1–2.4, §2.9; TOKENS.md all; BRAND.md all; docs/research/NEXT16_TAILWIND4_CONVENTIONS.md §3–§4; PLAN.md Conventions):
- `src/styles/brand.yaobet.css`: `:root` primitives `--raw-*` exactly as BRAND.md §1 (owner, `/* [OWNER] */`) and §2 (pm defaults, `/* [DEFAULT] */`); the money positive (`#7FB58A`) and negative (`#D89898`) primitives already satisfy the tolerance `|L_pos − L_neg| / max(L_pos, L_neg) <= 0.05` (WCAG 2.x relative luminance, sRGB linearised); the gate recomputes it, and the builder never retunes a BRAND.md value. No other colour literal anywhere in the repo.
- `src/styles/tokens.css`: `@theme static` block (static so unused tokens survive tree-shaking for the owner fill) that resets `--color-*: initial; --breakpoint-*: initial; --shadow-*: initial; --radius-*: initial; --font-*: initial;` then declares every semantic token from TOKENS.md §3 (surface incl. `raised-quiet`, fg, line, accent, money, status, state, typography, radius, shadow, breakpoints md/lg/xl, animate-skeleton) mapped per BRAND.md §3; `@theme inline` for tokens that alias a `var()` (fonts); `:root` for non-namespaced vars (`--space-*` aliases, `--z-*`, `--motion-duration-*`, `--ease-*`, `--size-*`, `--state-*`, `--ring-*`); the reduced-motion block from TOKENS.md §3.9.
- `src/styles/components.css`: `@layer components` base classes for the five shared primitives only (button, surface, money, skeleton, state-block), tokens only.
- `src/app/globals.css`: imports `tailwindcss` then the three files; `body` uses `bg-surface-canvas text-fg-primary font-sans`; the scaffold `prefers-color-scheme` block and `font-family: Arial` are removed.
- `src/app/layout.tsx`: `<html lang="vi">`, Geist via `next/font/google` with `subsets: ["latin", "vietnamese"]` and `variable: "--font-geist-sans"`, metadata `title: { default: "Yaobet", template: "%s — Yaobet" }`. No shell yet (leaf 1.2.2 mounts it).
- `src/app/page.tsx`: replace the scaffold page with a token-only placeholder: `export const metadata = { title: "Trang chủ" }`, a `<main>` with the brand promise text from SOT §2 and nothing else; no scaffold SVGs, no literals. Leaf 1.3.1 replaces it in wave 3.
- `scripts/verify-tokens.mjs`: zero-dependency Node script. Default mode fails (exit 1) on, inside `src/components` and `src/app` (`src/styles` excluded): a hex colour inside a `className` string or a `style` prop (`#[0-9a-fA-F]{3,8}` within quotes of `className=`/`class=`/`style=`); class-scoped px literals `\b(text|leading|tracking|w|h|p|m|gap)-\[[0-9.]+px\]`; `z-\[`, `duration-\[`, `bg-\[`, `text-\[#`; any import of `@/lib/mock` or `lib/mock` outside `src/lib/data`; any `bg-bg-`, `text-text-`, `border-border-` utility; any `prefers-color-scheme` outside `src/styles`. Prints `tokens verification passed`. `--brand`: reads `src/styles/brand.yaobet.css`, asserts `#654922 #956E2F #B68B4B #4D574E #303531 #202221` are present (case-insensitive), computes WCAG relative luminance of the money positive and negative primitives and fails if `|L_pos − L_neg| / max(L_pos, L_neg) > 0.05`; prints `brand verification passed`. `--built`: reads every `.next/static/**/*.css` after a build and asserts each TOKENS.md §3 semantic token name listed in the script appears; prints `built css verification passed`. `--self-test`: plants each forbidden pattern in a temp dir and must detect every one; prints `self-test passed`.
- `scripts/verify-routes.mjs`: zero-dependency Node script. Picks a free port at runtime, starts `next start` on the existing `.next` build in the current directory, reads `.next/BUILD_ID` and asserts the served HTML carries that build id (via the `x-nextjs-build-id` header or the `buildId` marker in the HTML); fetches each route argument; a route ending in `-404` (the control `/khong-ton-tai-404`, `/sanh-game/khong-co-404`, `/khuyen-mai/khong-co-404`) must return 404 with `lang="vi"`; every other route must return 200, `lang="vi"`, `— Yaobet` in `<title>`, and no `data-boundary="error"` and no "Application error"; kills the server; prints `routes verification passed`. `--self-test`: asserts that a fabricated failing response (injected via an env flag that makes the checker treat a known good route as expecting 404) is detected; prints `self-test passed`.

- [ ] G1: lint passes
  CHECK: npm run lint && echo LINT_OK
  EXPECT: LINT_OK
  EVIDENCE: pending

- [ ] G2: typecheck passes after route typegen
  CHECK: npx next typegen && npx tsc --noEmit && echo TSC_OK
  EXPECT: TSC_OK
  EVIDENCE: pending

- [ ] G3: production build passes with the new token files and the placeholder home
  CHECK: npm run build && echo BUILD_OK
  EXPECT: BUILD_OK
  EVIDENCE: pending

- [ ] G4: token gate passes on the tree and its self-test catches every planted violation
  CHECK: node scripts/verify-tokens.mjs && node scripts/verify-tokens.mjs --self-test
  EXPECT: self-test passed
  EVIDENCE: pending

- [ ] G5: every TOKENS.md §3 semantic token survives into the built CSS, scaffold defaults are gone, the root layout is Vietnamese
  CHECK: node scripts/verify-tokens.mjs --built && node -e "const fs=require('fs');if(/prefers-color-scheme|Arial|#ffffff|#171717/.test(fs.readFileSync('src/app/globals.css','utf8'))){console.log('scaffold defaults remain');process.exit(1)}const l=fs.readFileSync('src/app/layout.tsx','utf8');if(!l.includes('lang=\"vi\"')||!l.includes('vietnamese')||!l.includes('— Yaobet')){console.log('layout lang/subset/title missing');process.exit(1)}const p=fs.readFileSync('src/app/page.tsx','utf8');if(/svg|#[0-9a-fA-F]{3,8}|\[\d+px\]/.test(p)||!p.includes('Trang chủ')){console.log('placeholder home contract');process.exit(1)}console.log('layout verified')"
  EXPECT: layout verified
  EVIDENCE: pending

- [ ] G6: brand primitives match BRAND.md and money colours are luminance-matched
  CHECK: node scripts/verify-tokens.mjs --brand
  EXPECT: brand verification passed
  EVIDENCE: pending

- [ ] G7: route sweep passes on the placeholder home and the 404 control with build-id assertion, and its self-test catches a planted failure
  CHECK: node scripts/verify-routes.mjs / /khong-ton-tai-404 && node scripts/verify-routes.mjs --self-test
  EXPECT: self-test passed
  EVIDENCE: pending

- [ ] G8: runtime cascade probe: with `data-brand="probe"` set on `<html>` and one primitive overridden under `[data-brand="probe"]`, the computed colour of a `bg-surface-canvas` element changes in the built app; record the probe method and result as manual evidence, then remove the probe
  EVIDENCE: pending

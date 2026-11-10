# Next.js 16.4 + Tailwind 4.3 conventions for this install (builder brief)

Captured 2026-11-04 by `research-explorer` from the vendored docs at `node_modules/next/dist/docs/01-app` (cited as `D/...`), `node_modules/tailwindcss/{index.css,theme.css,dist/lib.js}`, and tailwindcss.com. Versions: next 16.4.5, react 19.3.0, tailwindcss 4.3.4, `@tailwindcss/turbopack` 4.3.4, Node >= 20.9, TS >= 5.1. The generated `AGENTS.md` is right: this version differs from training data. Read this before writing any code.

## 1. Repo config facts

- `next.config.ts` sets `cacheComponents: true`, `partialPrefetching: true`, and a Turbopack rule `"*.css"` → `@tailwindcss/turbopack` (scaffold default; Next's own CSS doc describes the PostCSS route instead, `D/01-getting-started/11-css.md:28-45`). Keep the scaffold's loader; `npm run build` is the proof.
- `typedRoutes` is not enabled. `<Link href>` is a plain string. Do not enable it unless asked.
- `src/app/globals.css` already uses `@import "tailwindcss"; @theme inline { ... }`. `src/app/layout.tsx` uses the global `LayoutProps<"/">` type and Geist with `subsets: ["latin"]` under `lang="en"`; both change in the foundation leaf.

## 2. App Router essentials (breaking changes first)

- `params` and `searchParams` are Promises everywhere: `const { slug } = await props.params` (`D/02-guides/upgrading/version-16.md:259-282`, `page.md:13-14, 64`). Typed helpers need no import: `PageProps<'/sanh-game/[category]'>`, `LayoutProps<'/'>`; regenerate with `npx next typegen` after adding routes (`02-typescript.md:102-108`).
- Cache Components is ON: data fetching is dynamic by default (`cacheComponents.md:12`). Any uncached async read or runtime API (`cookies`, `headers`, `params`, `searchParams`) must sit inside `<Suspense>` or dev raises a blocking-route error (`08-caching.md:103-201`). Synchronous mock reads need no Suspense; async accessors from `@/lib/data/*` do. Opt-in caching is `'use cache'` + `cacheLife` / `cacheTag` (`08-caching.md:51-101`).
- Removed with Cache Components: route segment exports `dynamic`, `dynamicParams`, `revalidate`, `fetchCache`, `experimental_ppr` (`route-segment-config/index.md:25-26`). Never export them.
- `middleware.ts` is now `proxy` (`version-16.md:596-598`). Phase 1 needs neither.
- `error.tsx` is a client component with props `{ error, retry }`; `retry()` is the recovery, `reset()` still exists (`error.md:21-45, 117-157`). `global-error.tsx` defines its own `<html>`/`<body>` (`10-error-handling.md:401-414`).
- `next/image`: `priority` is deprecated, use `preload` (`image.md:292-294`); `width`/`height` required unless static import or `fill` + `sizes` (`image.md:108-113`); `alt` required, `alt=""` for decorative; `qualities` default `[75]` only; `next/legacy/image` and `images.domains` deprecated. Local placeholder tiles live in `public/` and are referenced from `/`.
- `next/link` extends `<a>`; never nest an `<a>`; prefetch runs in production only (`link.md:298-302`).
- `metadata` / `generateMetadata` exports are Server Component only (`14-metadata-and-og-images.md:27-60`).
- File conventions: `layout`, `page`, `loading` (Suspense-backed), `error` (client), `not-found` (+ `global-not-found`), `template`, route groups `(folder)`, dynamic `[slug]` / `[...slug]`. Root layout must render `<html>` and `<body>`.
- Server vs client: default Server Component; put `"use client"` above the imports only in leaf interactive files (hooks, handlers, browser APIs); everything a client file imports joins the client bundle (`05-server-and-client-components.md:142-188`).
- Fonts: `next/font/google` with `subsets`, `variable`, `display`; weight unnecessary for variable fonts (`font.md:20-158`). The font table at `node_modules/next/dist/compiled/@next/font/dist/google/font-data.json` lists `vietnamese` for Be Vietnam Pro and Inter. Use `subsets: ["latin", "vietnamese"]`, expose `variable: "--font-<name>"`, map it in `@theme inline`. Set `lang="vi"` on `<html>`.
- Dev and build: Turbopack is the default for both; no flags; a custom webpack config breaks `next build` (`version-16.md:102-143`). `next dev` writes `.next/dev`. Route types land in `.next/types/` (`routes.d.ts`, `validator.ts`); `next-env.d.ts` imports them. ESLint flat config is default; `next lint` is gone.

## 3. Tailwind v4 facts that bind the token contract

- `@import "tailwindcss"` defines layers `theme, base, components, utilities` and the default theme (`index.css:1-4`). `--spacing: 0.25rem` (`theme.css:325`), so `p-4` = `calc(var(--spacing) * 4)` = 16 px. Confirmed.
- `@theme` vs `@theme inline`: a non-inline token makes the utility reference `var(--token)`; `inline` makes the utility use the value. A token whose value is itself `var(--x)` must be declared `inline` (so `.font-sans { font-family: var(--font-be-vietnam) }` works) and runtime overrides then target `--x`. Confirmed on tailwindcss.com/docs/theme. The runtime cascade of non-inline tokens is NOT documented: the foundation leaf proves it with a compiled probe before anything depends on it (gate G5 in `leaf-1.1.1`).
- Unused theme tokens are tree-shaken from `:root` unless `@theme static`. Tokens consumed only through `name-(--var)` shorthand must be declared in `:root` (or `static`). Confirmed.
- Namespace reset: `@theme { --color-*: initial; }` removes every default utility in that namespace; `--*: initial` clears all. `dist/lib.js` accepts only `initial` for wildcard keys. Confirmed. After the reset `bg-white` and `bg-black` do not exist.
- Shorthand `z-(--z-overlay)` → `z-index: var(--z-overlay)`; `duration-(--motion-duration-fast)`; `p-(--space-stack)`; ambiguous names take a type hint `text-(length:--x)` / `text-(color:--x)`. Confirmed. Theme keys for z-index and duration are `--z-index-*` and `--transition-duration-*`; a plain `--z-overlay` variable never becomes a `z-overlay` utility, which is the intended design.
- `@layer components { .card { ... } }` stays overridable by utilities; `@custom-variant` for attribute scopes (`[data-brand]`); `@utility` for custom utilities. `motion-safe:` / `motion-reduce:` variants exist, and a plain `@media (prefers-reduced-motion: reduce)` block works in CSS. Confirmed.

## 4. Do / do not (every builder)

1. DO `await props.params` / `await props.searchParams`; DO NOT read them synchronously.
2. DO use global `PageProps<'/route'>` / `LayoutProps<'/route'>` and run `npx next typegen` after adding a route.
3. DO keep pages and layouts as Server Components; `"use client"` only on leaf interactive files; DO NOT export `metadata` from a client file.
4. DO wrap async accessor reads in `<Suspense>` with a token-built skeleton fallback; DO NOT export `dynamic`, `revalidate`, `dynamicParams`, `fetchCache`, `experimental_ppr`.
5. DO write `error.tsx` as `"use client"` with `{ error, retry }`.
6. DO use `next/image` with explicit dimensions (or static import, or `fill` + `sizes`) and meaningful `alt`; `preload` for the LCP image; DO NOT use `priority`, `next/legacy/image`, `images.domains`, or non-75 `quality`.
7. DO load the font with `subsets: ["latin", "vietnamese"]` and `variable`; DO NOT hard-code a `font-family` in CSS (the scaffold's `body { font-family: Arial }` is removed by the foundation leaf).
8. DO declare `var()`-aliasing tokens with `@theme inline` and literal tokens with plain `@theme`; DO NOT put `@theme` inside a selector or media query.
9. DO use `bg-surface-raised`, `text-fg-primary`, `z-(--z-overlay)`, `duration-(--motion-duration-fast)`, `p-4`; DO NOT use v3 syntax (`tailwind.config.js`, `@tailwind base`, `bg-[--x]`) or any hex, px font size, raw z-index or raw duration in `.tsx` (TOKENS §4.5 gate).
10. DO NOT run `npm install` or add a dependency, add `middleware.ts`, add a `webpack` config, or enable `typedRoutes` unless the Story Shard says so.

# Review brief (binding on every guide reviewer)

Read first: `docs/rebuild/DECISIONS.md`, then `docs/rebuild/sections/00-*` (intro, routes, discrepancies) and `05-01-v-checklist.html`.

Your job: an EXHAUSTIVE review of your assigned section files, so the PM can plan leased builder leaves that rebuild the UI exactly in Next.js 16 + Tailwind v4. Read every assigned file completely (slices <= 250 lines; never skip). You may read the original source `/Users/maxime/Documents/Projects/Antigravity/Igaming-Agent-1/apps/web/**` read-only to resolve a gap. Edit nothing except your one output file. No legal/regulatory content. Never invent: where the guide says "(not found in source)", carry that forward.

Write ONE markdown file `docs/rebuild/review/<track>.md` with these sections, in order:

1. **Coverage** — table: section file · h3 count · read fully (yes) · components/routes covered.
2. **Inventory** — every component, route, token group, hook, lib module and mock dataset: name · original source path · guide anchor (`file#id`) · depends on.
3. **Tailwind translation notes** — per item, how the CSS maps: plain utilities, `@theme` tokens, or needs `@layer components` / `@utility` / global CSS (keyframes, masks, clip-path, canvas, complex gradients, `:has`, container queries, pseudo-elements). Flag anything that cannot be expressed exactly and give the exact-preserving method.
4. **Defects to reproduce** — every amber callout: id (`<TRACK>-nn`), anchor, what it is, how to reproduce it, proposed later fix.
5. **Gaps and contradictions** — anything a builder would have to guess; quote the guide.
6. **Assets** — every public path used, with size if given.
7. **Proposed leaves** — builder-sized units (aim 6-15 files each), each with: name, `allowed_files` globs under `src/` (target layout: `src/styles/**`, `src/ui/**`, `src/lib/**`, `src/components/<area>/**`, `src/app/<route>/**`), guide sections it implements, needs (other leaves), and acceptance checks a gate can run mechanically (routes that must answer 200/307, verbatim copy strings to grep, tokens that must exist). Keep leaves disjoint.
8. **Risks** — top risks for an exact rebuild of this track.

Return to the PM (<= 20 lines): output path, counts (components, routes, defects, gaps, leaves), top 5 risks. End with a `### Telemetry Receipt` (cp1_lease H_env plus your one doc write; files_touched; verification_cmd; exit_code; residual_risks).

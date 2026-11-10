# UI rebuild — owner decisions (2026-11-05)

Source guide: `/Users/maxime/Documents/Projects/Antigravity/Igaming-Agent-1/.hc/ui-rebuild-guide/` (UI-REBUILD-GUIDE.html, 72 reference shots in `shots/`, manifest `shots/manifest.json`). It is an as-built spec of `Igaming-Agent-1/apps/web`. Split copy for agents: `docs/rebuild/sections/` (75 sections, `INDEX.json`).

| # | Decision | Effect |
|---|---|---|
| D1 | Rebuild the UI exactly per the guide ("1000%"). | The guide supersedes earlier SOT UI decisions (re-skin, owner palette, route set). Routes, copy, tokens, themes (obsidian + VIP luxury), components, states, motion and mock auth follow the guide. `/dai-ly`, `/tai-app`, `/phong-cach`, `/dev/collection-ports` and the four redirects are in scope. |
| D2 | Keep Tailwind (not CSS Modules). | Every guide CSS value is translated exactly into Tailwind v4 (`@theme` tokens, utilities, `@layer components` / `@utility` for complex art such as gradients, masks, keyframes). The guide's token-lint assertions A1-A3 are re-specified for Tailwind (ADR-002) so the acceptance checklist still runs. |
| D3 | Reproduce defects as built; list fixes. | Every amber-callout defect is reproduced; each goes into `docs/rebuild/FIX-LIST.md` for later owner approval. |
| D4 | Replace current code. | Waves 1-6 archived as tag `archive/tailwind-v1` (main 7090211; branch `qc5-fix` parked). `src/` is rebuilt from the guide. |

Audit = the guide's acceptance checklist (`sections/05-01-v-checklist.html`) with the Tailwind token-lint substitution, plus the harness gates (frontend-qc, oracle-review, hallucination-auditor). Stack pins stay as installed (Next 16.4.5, React 19.3, Tailwind 4.3.4); the guide's 16.2.9 / 19.2.4 differ by minor version only. The old app's `apps/web/public/**` assets may be copied read-only.

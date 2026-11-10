# Wine-Gold design system: intake review

Status: PM review, 2026-11-07. Source: `/Users/maxime/Downloads/files` (owner delivery).
Checks: `$S/ds-check.py.txt`, output `$S/ds-check.out` (S = session scratchpad).

## 1. What was delivered

- 9 files. The root copies, `tokens/` and `wine-gold-design-tokens.zip` are byte-identical (sha1 checked). `design-tokens.all.json` equals the union of the 6 category files: 210 tokens, 0 value differences.
- DTCG-style JSON (`$value`, `$type`, `{ref}` aliases), three tiers: primitive -> semantic -> component.
- Colour: warm near-black neutrals (`neutral.900` #1C1A17 page), ivory text (#F4EFE6), gold ramp (`gold.500` #D4AF5A primary), wine ramp (`wine.500-700` panels), four feedback hues each with a dark tint.
- Type: Be Vietnam Pro (body), Playfair Display (display), Inter (numerals); fluid `clamp()` sizes from 12 px caption to 56 px display; weights 400/500/600.
- Spacing 4-128 px (10 steps), radius 4/8/999, 3 shadows, 5 durations and 4 easings.
- `_removed-orphans.json`: 20 tokens pruned because the generator found no consumer.

## 2. Strengths

1. No dangling references: every `{ref}` resolves.
2. Text contrast is strong: primary 10.9-15.2:1, secondary 5.8-8.1:1, accent 7.7-10.7:1 on every surface. The primary button label (wine.700 on gold) is 6.3-9.2:1 across rest, hover and pressed.
3. Each feedback hue passes on its own tint (5.7-6.0:1).
4. Clean naming and a real component tier, so components can bind to component tokens instead of raw colours.
5. Every font family carries Vietnamese fallbacks; the fluid sizes clamp to fixed px at 375 and 1440.

## 3. Defects (brutal list)

| # | Defect | Evidence | Severity |
|---|---|---|---|
| 1 | `text.muted` fails AA on `surface.3`, which is the background of modal, toast and tooltip | 4.11:1 (also 4.25 on wine.panel) | High |
| 2 | `modal.border` = hairline on `modal.bg` = surface.3 is invisible | neutral.700 vs 750: 1.03:1 | High |
| 3 | Win and loss are not luminance-matched (TOKENS.md rule 4.1, within 5%) | success L 0.424 vs danger L 0.336, 21% apart | High |
| 4 | Pruned tokens that our components need: card bg, input text/label/helper/error text, tab text rest/active, secondary button text, checkbox mark, odds up/down, VIP bg/header | `_removed-orphans.json` | High |
| 5 | No "paused / tạm dừng" status (CLAUDE.md money rule; TOKENS.md 3.4) | absent | High |
| 6 | Spacing, type, radius, motion and elevation have **no semantic tier** (`semantic: {}`), so components would bind to primitives, breaking the tier rule the file itself declares | spacing/type/radius/motion `semantic` | Medium |
| 7 | 12 colour primitives are unused (gold 50/100/700/800/900, wine 50-400/800/900) while `ramps.reserve.json` claims the reserve is empty | ds-check | Low |
| 8 | Near-duplicate neutrals: neutral.700 #3A352E vs neutral.750 #38332C (1.03:1) | ds-check | Low |
| 9 | `control.checked.bg` (gold.500) and `control.checked.track` (surface.3) overlap in meaning; the knob is gold.300 on a gold fill | color.json component tier | Medium |
| 10 | No weight 700, letter-spacing, z-index, breakpoint, icon-size or touch-gap tokens; the repo uses all of them today | type.json, TOKENS.md 3.8-3.11 | Medium |
| 11 | `leading.truncate` 1.65 is larger than body leading and the name does not describe a role; `spacing.frame.gap` 3 px is off the 4 px grid | type.json, spacing.json | Low |
| 12 | Radius drops 12 and 16 px; every card and sheet goes to 8 px or 4 px | radius.json | Medium (visual change) |
| 13 | Three web fonts (two new) add load and FOUT risk; Playfair is a high-contrast serif, so stacked Vietnamese marks get thin at h4 (19 px) | type.json | Medium |
| 14 | One theme only: no answer for the existing `emerald` brand, `obsidian` theme or VIP tier palettes (brands.css, themes.css) | src/styles | Medium |
| 15 | Hairline border is decorative only (1.03-1.43:1): fine for dividers, but it must never be the only edge of an input or control (border.control at 3.08-4.27:1 covers that) | ds-check | Note |

## 4. Impact on the repo

- Current token source: `src/styles/tokens.css` (363 lines), `tw-theme.css`, `brands.css`, `themes.css`, `typography.css`, plus 5,342 lines of area CSS in `src/styles/areas/` and 141 `.tsx` files with classes.
- The audited rebuild's screenshot gate (A5, 72 pairs against the original app) will fail by design once the colours change, so the visual baseline has to be redefined.
- Fonts move from Be Vietnam Pro + Montserrat to Be Vietnam Pro + Playfair Display + Inter (next/font/google, no npm dependency).

## 5. Owner decisions (2026-11-07)

- D-DS1 Baseline: retire pixel parity with the original. Keep the routes, layout-box (A5b), auth-flow and hygiene gates. Screenshots captured after the update, reviewed by designer and frontend-qc, become the new reference.
- D-DS2 Gaps: Yaobet overlay. Ship the delivered values; fixes and missing tokens go in a small overlay that only re-points to existing DS primitives (no new hex). Designer proposes it; the owner approves the list before any build.
- D-DS3 Fonts: adopt all three (Be Vietnam Pro, Playfair Display, Inter) through next/font/google, Vietnamese subset, weights 400/500/600.
- D-DS4 Themes: Wine-Gold replaces the yaobet default. Emerald, obsidian and the VIP tier palettes keep their values, re-keyed to the new token names.

Second round (2026-11-07, after the designer's `docs/design/wine-gold/MAPPING.md` and `overlay.proposal.json`):

- D-DS5 Win/loss: one exception to D-DS2. Add a single new loss primitive tuned to within 5% of green.400 luminance (rule 4.1 stays intact). No other new hex.
- D-DS6 Overlay: the 108 overlay tokens are approved. The checks that pin old values (F1.sh counts, built-css.sh canvas, U1.sh strings, token-lint names) are updated only at those pins, with the evidence logged.
- D-DS7 Components: login/submit (`.ui-btn-primary`) and Register (`--cta-accent`) become the gold primary button; the header bar uses `surface.wine.header` (wine.600).
- D-DS8 Defaults: gradients re-tinted to ivory; emerald keeps Montserrat; obsidian keeps its old win/loss/error/focus values; heading letter-spacing 0; radius 12/16 becomes 8 px; shadows return; the checkbox may use a gold fill as a mark (a named exception to rule 4.2).

Third round (2026-11-07, after ADR-003 and .unlazy/yaobet-ds/PLAN.md):

- D-DS9 Extra pins: S0 may update built-css.sh:13 (font hashes), I1.sh:10 (theme attribute) and I1.sh:13 (theme-color) at the pin only, logging before and after.
- D-DS10 Obsidian: remove data-theme="obsidian" from <html> (src/app/layout.tsx:79). Wine-Gold is the default; obsidian's values stay in themes.css, unused.
- D-DS11 Baseline: the new screenshots live in ~/.cache/yaobet-ds/baseline, outside git; only the sha256 manifest is committed.

Fourth round (2026-11-07, after the critical-planner gate on PLAN.md):

- D-DS12 Box check: after S0, log every A5b box that moved and by how much. The designer and frontend-qc review the list, then boxes.json is re-pinned to the new sizes, with before/after logged. The check stays at its tolerance from then on.
- D-DS13 Card art: the hsl() illustration colours in src/components/collection/CardArt.tsx and PackStage.tsx are a named exception and stay as they are. Their #fff lines still move to tokens.
- D-DS14 Extra pins: F5.sh:7 (font-loader count) and S3.sh:7 (QuickActionRail literals) may be updated at the pin only, with before/after logged.
- D-DS15 Docs commit: one local commit on main (no push) holding only the plan and design docs, so the worktrees can see them.

Fifth round (2026-11-08, after SP):

- D-DS16 Fonts self-hosted: Google Fonts rotates the font bytes (Playfair Display moved to v40; two clean builds differed on 7 of 25 WOFF2 hashes), so the built-css.sh:13 hash pin only passed from a warm `.next` cache. The four families move to next/font/local with the WOFF2 files and their OFL licences committed under `src/app/fonts/`. Three check pins change at the pin only, with before and after logged: `.unlazy/yaobet-ds/checks/fonts.sh:33-38` (the import assertion), `.unlazy/yaobet-rebuild/checks/F5.sh:7` (the subset count) and `.unlazy/yaobet-rebuild/checks/built-css.sh:13` (the hashes). The PM makes the pin edits; builders never open check files.
- D-DS17 Font licence files (2026-11-08, after SF): the four `src/app/fonts/<family>/OFL.txt` files stay beside the fonts they cover. They are a narrow exception to standing rule 1 (no legal content), for third-party font licences only. The PM lists their hygiene hits in `.unlazy/yaobet-rebuild/checks/a11-allow.txt`, which genplan.py writes once and the PM fills, and appends its pins.txt row, logging before and after. In next 16.4.5 the localFont `declarations` font-family renames only the @font-face rules, so `<html>` also carries an inline style that puts each real family first in its `--font-*` variable (PM-approved).
- D-DS18 (owner 2026-11-08) Compact jackpot figure: the quick-action rail jackpot card (60px column, 50px content) shows the jackpot in a compact Vietnamese unit format, e.g. `8,69 tỷ ₫` (two decimals, comma decimal separator, `tỷ` from 1e9, `triệu` from 1e6, the full figure below that). The exact full figure stays the accessible name. Digits are never split inside a number; a break is allowed only between the number and its unit. Scope: that card only; every other money display keeps the full figure.
- D-DS19 (owner 2026-11-08) Destructive button: S1 adds a `.ui-btn-destructive` variant on existing tokens only: `--error` label and border, a light `--error` tint on hover. The danger callers (LogoutButton.tsx:40, Header.tsx:152, MessageCenter.tsx:103) switch to it after ds-s1 merges, each in the shard that leases its file. This supersedes PLAN "## Risks" item 6.
- D-DS20 (owner 2026-11-08) Ghost button: ivory label (the `--text-hi` family) with no edge, per the DS `button.ghost`. Gold stays reserved for the primary fill and the secondary label and border. This supersedes PLAN "### S1" "secondary and ghost use the secondary tokens" for ghost only.
- D-DS21 (owner 2026-11-08) Emerald primary: under the emerald brand, `.ui-btn-primary` keeps its `--brand-cta-grad` look (D-DS4 literal). Wine-Gold is unaffected.
- R13 (PM): `compactVnd()` picks the unit with `amount >= size`, and only then rounds half up to two decimals. That keeps the D-DS18 example (`8,69 tỷ ₫`) and the exact 1e6/1e9 boundaries; truncation is rejected because it shows `8,68`.
- D-DS22 (owner 2026-11-09) Emerald primary, revised: no existing ink reaches 4.5:1 on both `--brand-cta-grad` stops (ivory 3.36, #04140c 4.92/4.20). So under emerald `.ui-btn-primary` keeps its current green fill with the #04140c ink (7.89:1). This supersedes D-DS21.
- D-DS23 (owner 2026-11-09) Destructive hover: the 12% `--error` tint drops the label to 3.85:1 on --surface-3. So on hover `.ui-btn-destructive` fills solid `--error`, with the `--shell` ink (about 6.4:1). This supersedes the hover clause of D-DS19.
- R14 (PM): after R13 rounds, a result of 1000 or more in a unit promotes to the next larger unit when there is one. 999_995_000 shows `1,00 tỷ ₫`, not `1.000,00 triệu ₫`. Values below 1e6 still show the full figure.
- D-DS24 (owner 2026-11-09) Header Register: the shell header Register button uses the primary style (`.ui-btn-primary`), not the destructive style.
- D-DS25 (owner 2026-11-09) Jackpot figure: the jackpot figure keeps gold ink on the right rail and on the quick-action rail (`src/styles/areas/shell.css:1855`, R12). This is the one named exception to MAPPING:103 "money is never gold"; every other money figure stays ivory. (Extended by the owner on 2026-11-09, at the G19 review.)
- D-DS26 (owner 2026-11-10, supersedes the header half of D-DS7) Header bar: the sticky header goes back to the page background (`--header-bg: var(--canvas)`, neutral.900), as before the update. The owner found the wine header unattractive. The gold primary buttons from D-DS7 stay, and wine stays on the VIP card, the progress track and the modals.
- R15 (PM 2026-11-09) Header pair: with Register on `.ui-btn-primary` (D-DS24), the header Login button moves to the existing ghost variant, so the header shows one primary action. No new variant or token. The owner can reverse this.

PM rulings (inside the owner decisions, no new scope):

- R1: D-DS4 "re-keyed to the new token names" means the existing names that components read (alias strategy, ADR-003 §3.5).
- R2: MAPPING's semantic names (--surface-canvas, --fg-primary ...) are not introduced. Only the overlay colour names with no current token are added (ADR-003 §3.4).
- R3: The checkbox mark token stays in the overlay. No checkbox component is built (none exists; no invented UI).
- R4: S7 may split into S7a and S7b at the area boundary if the builder's lease runs past one context; the leases stay disjoint.
- R5: The overlay tokens with no current name (10 type-role tokens, 5 motion steps) are declared under the MAPPING.md:38 names: `--type-<role>-family|size|leading|weight`, and `--dur-*` or `--motion-duration-<x>` and `--ease-<x>`. They are part of the approved overlay (D-DS6), so no new scope is added.
- R6: The coverArt.ts:75 format doc comment names two hex forms (`#abc`, `#aabbcc`). The G9 allow count is the number of pattern hits, so that row is 2, not 1.
- R7: An approved overlay component token that resolves to a DS semantic no existing name holds reads a semantic alias, named per MAPPING.md:24/:29. It never reads `--wg-*` (tier rule). Exactly two aliases are added: `--line-default` (border.control, for `--modal|toast|tooltip-border`) and `--surface-wine-deep` (surface.wine.deep, for `--vip-bg`). R2 still bars every other MAPPING semantic name. `--vip-bg` no longer borrows `--progress-track` (that is DS vip.track, MAPPING.md:104).
- R9: PLAN.md S0 step 4 ("display, h1 and h2 use the display face") means type roles, not HTML elements (ADR-003 §3.6, MAPPING.md:203, :230, defect 13: Playfair never below 26 px at 375). In typography.css only the `h1` element defaults to the display face, because page titles read the h1 role. `h2`-`h6` default to the body face. Any heading that reads the display, h1 or h2 role at its role size takes the face from its `--type-<role>-family` token in the owning shard. A component that asks for the display face below 26 px (for example ScratchCardGame.tsx:233) is fixed in its owning shard.
- R10 (doc corrections, no new scope): R5's "10 type-role tokens" reads "12 roles x 4 properties = 48 `--type-*` tokens", which is the overlay count. The ADR-003 §3.4 list also includes the approved overlay rows `--touch-gap` and `--icon-sm|lg` (MAPPING.md:38, :342-343). A primitive that no semantic token reads may still be declared when a G6 contrast pair needs it in the built CSS: `--wg-color-wine-500` (muted-raised on wine.panel, 6.03).
- R8: "The VIP palette keeps its values" (D-DS4, ADR-003 §3.5) covers the colour lines of tokens.css:307-342. The radius rows `--vip-radius-table|control|gem` (:343-345) follow MAPPING.md:278-280 under D-DS8: table 8px, control 4px, gem 8px.
- R11 (box re-pin routing, inside D-DS12): SP re-pins in `boxes.json` only the moved boxes that both the designer and frontend-qc ACCEPT, logging before and after. A box either reviewer REJECTs keeps its old pin. The shard that owns the fix re-pins it once both reviewers accept it, again logging before and after. Until then, BOX in later shards may fail only on those boxes, and each one is listed by id with its owning shard. This names and owns each failure; it does not widen the tolerance. Routing after S0: rightRail@1440 goes to S2 (shell.css:265 reads `--t-h1`; Fix: read `--type-num-md-*`). identity@375/768 goes to S2 (pre-existing header overflow). quickActionRail@1024/1440 goes to S3 (pre-existing money split, shell.css:1806).
- R12 (ownership routing, no new scope): the quickActionRail money split (shell.css:1806 `word-break`) and the jackpot figure ink (shell.css:1804 `--brand-accent`; Fix: `--brand-accent-fg`, MAPPING.md:123) live in `src/styles/areas/shell.css`, which only S2 leases. They move from S3 to S2, together with the quickActionRail@1024/1440 box fix. S2 therefore owns all five R11 boxes. Check-file pins in a builder's PLAN lease (U1.sh:10-11 for S1, S3.sh:7 for S2) are edited by the PM by script after review, as in SP and SF, because builders may run but not read `checks/` (owner rule).

Vendored source: `docs/design/wine-gold/` (copy of `/Users/maxime/Downloads/files/tokens/`, sha1 of the all file d71e1c66).

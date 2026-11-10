# G22 trace: owner decisions and PM rulings on `main`

This file traces each owner decision D-DS1..D-DS25 (DS-WINE-GOLD-REVIEW.md §5) and each PM ruling R1..R16 to a code or doc line on `main` 4a66d3e, plus the gate that proves it. The lines were collected read-only and spot-checked by the PM: 8 citations were re-read on main and all matched. Pin edits live in check files that builders and auditors may run but not read, so those rows cite the docs that record them.

Abbreviations:
- T: src/styles/tokens.css
- TH: src/styles/themes.css
- BR: src/styles/brands.css
- L: src/app/layout.tsx
- UI: src/ui/ui.css
- SH: src/styles/areas/shell.css
- QAR: src/components/layout/QuickActionRail.tsx
- TY: src/styles/typography.css
- TK: .unlazy/yaobet-ds/task.md
- RV: docs/design/DS-WINE-GOLD-REVIEW.md

| Id | Lands at | Gate |
|---|---|---|
| D-DS1 | scripts/box-check.mjs:82; scripts/auth-flow.mjs:115; scripts/verify-routes.mjs:145 | G12-G19 |
| D-DS2 | T:66 (the only new primitive); T:173 | G8 |
| D-DS3 | L:42-45; L:78; L:96-99; L:150 | G10 |
| D-DS4 | BR:19; BR:37; TH:16; T:484-529 (VIP colours unchanged) | G5, G7 |
| D-DS5 | T:66; T:155-156 | G6, G8 |
| D-DS6 | T:201-221; T:313-322; T:328-330; TK:24 | G4b, G5 |
| D-DS7 | UI:194-197; T:289; T:450; SH:352; AuthModal.tsx:252, :349; Header.tsx:152-158 | G19 |
| D-DS8 | T:355-360 (ivory); BR:53, :56 (emerald Montserrat); TH:33-36 (obsidian); TY:47, :56, :84 (letter-spacing 0); T:110-111, :263-266 (radius); T:115-117, :276 (shadows); T:405 (checkbox mark) | G5, G10, G19, G21 |
| D-DS9 | RV:65; ADR-003:62, :83; TK:24 (docs only) | G4b, G14 |
| D-DS10 | L:285-290 (no data-theme); TH:16 | G14 |
| D-DS11 | scripts/capture-shots.mjs:7; GATES.md:86 | G16 |
| D-DS12 | TK:24 and TK:37 (the re-pin log; the pinned boxes live in a check file) | G12 |
| D-DS13 | CardArt.tsx:52, :58-60; PackStage.tsx:184-185 | G9 |
| D-DS14 | RV:73; ADR-003:88; TK:28 (docs only) | G4a, G4b |
| D-DS15 | tag `ds-base` = 2dc3b92 (docs-only commit); PLAN.md:5 | — |
| D-DS16 | L:16 (next/font/local); src/app/fonts/SOURCE.md:1; RV:78 | G4b, G10 |
| D-DS17 | src/app/fonts/*/OFL.txt (4 families); L:270-278, :289 | G15 |
| D-DS18 | QAR:46-49, :55, :198, :200-201; SH:1859-1861 | G12, G18 |
| D-DS19 | UI:230-234; LogoutButton.tsx:40; MessageCenter.tsx:101 | G19 |
| D-DS20 | UI:249-252 | G19 |
| D-DS21 | superseded by D-DS22; no code | — |
| D-DS22 | BR:41, :43; UI:194-197 | G6 |
| D-DS23 | UI:235-239 | G6, G19 |
| D-DS24 | Header.tsx:152-158 | G19 |
| D-DS25 | SH:1855 (quick-action rail); SH:2063-2064 (right rail); TK:64 | G19, G21 |
| D-DS26 | T:289 (`--header-bg: var(--canvas)`); replaces the T:289 wine value cited under D-DS7 | G19 |
| R1 | T:143-177 (existing names point at `--wg-*`) | G7 |
| R2 | `rg surface-canvas src` returns 0 hits; nearest token T:143 | G5, G7 |
| R3 | no checkbox component; token at T:405 | G5 |
| R4 | branches ds-s7a and ds-s7b, both merged into main; TK:67, :72 | G1 |
| R5 | T:201-221; T:313-324 | G5 |
| R6 | src/components/lottery/_internal/coverArt.ts:75 | G9 |
| R7 | T:152; T:178; T:416-422 | G7 |
| R8 | T:531-533 (VIP radii); T:484-529 (VIP colours unchanged) | G5 |
| R9 | TY:45-47 (h1, display face); TY:50-56 (h2-h6, body face); T:209 | G19 |
| R10 | T:59; T:201-221; T:328-330 | G5, G6 |
| R11 | TK:24; TK:37 (docs only) | G12 |
| R12 | SH:1855; SH:1859-1861; TK:28 | G12, G19 |
| R13 | QAR:55-59 | G18 |
| R14 | QAR:51-53, :60-63 | G18 |
| R15 | Header.tsx:159-165 (Login is ghost) | G19 |
| R16 | TK:72-73 (logged to the backlog) | — |

All 42 rows are traced (D-DS26 added 2026-11-10). D-DS12 is traced only through the task log, because the box pins sit in a check file.

Stale citations in the decision docs. The code on main is correct, and these are line references only:
- RV:81 lists Header.tsx:152 as a danger caller. On main, Header.tsx:152 is the Register primary (D-DS24), and the header has no destructive button. The G19 checklist (GATES.md:104) was corrected on 2026-11-09.
- RV:105 (R12) cites shell.css:1804 and :1806 and `word-break`. On main, the ink is at SH:1855 and the guard is `white-space: nowrap` at SH:1859-1861.
- RV:99-100 (R8) cites tokens.css:307-345. On main, the VIP block is at T:484-533.
- D-DS3 says next/font/google. D-DS16 supersedes it with next/font/local (L:16).
- R5 counts 10 type and 5 motion tokens. R10 corrects this to 48 `--type-*` tokens, and main declares 7 `--dur-*` and 4 `--ease-*` tokens (T:313-324).

# Plan gate: yaobet-rebuild (critical-planner, 2026-11-05)

Scope: `.unlazy/yaobet-rebuild/PLAN.md`, `GATES.md`, 30 leaf ledgers, against `DECISIONS.md`, `PM-RULINGS.md`, `ADR-002.md`, the four reviews, the guide sections, and the original `Igaming-Agent-1/apps/web` (read-only). Severity: **BLOCKER** = dispatching as written stalls the plan or yields a false PASS; **MAJOR** = a certain late failure or a significant fidelity risk, fix before the affected wave; **MINOR** = hygiene.

Method notes. (1) Import graph: all 380 original `src/` files were mapped to leaves by the plan's OWNS rules and every `@/`, relative and CSS import was resolved (scratch script, not committed). (2) Tailwind behaviour was probed with the installed `tailwindcss` 4.3.4 `compile()` API. (3) The lease matcher was probed with `.claude/hooks/harness_lib.py:matches_allowed_file`. (4) `scripts/verification/verify-oracle.sh` does not exist in this repo or the harness root, so the oracle pass below is reasoned, not scripted. (5) `gate-lint` on GATES.md + 30 ledgers: exit 0, `LINT OK (146 warning(s))`, all `manual-gate` / `unmeasured-number`.

## 0. Claims tested and found sound (no directive)

- `window.next.router` exists in the installed Next 16.4.5, not dev-gated: `node_modules/next/dist/client/components/app-router-instance.js:253-254`.
- No original import crosses into a same or later wave under the plan's mapping (0 hits). `src/ui/**` imports only `lib/rg`, `lib/format`, `lib/types` (never `lib/mock`). The root layout imports only the shell barrel and `QuickActionRail` (orig `app/layout.tsx:57-58`); DevAuthToggle comes from `app/page.tsx:44,76`; `app/loading.tsx` imports nothing the layout needs.
- Coverage: every original file maps to exactly one leaf except the 16 dead home files (shell-home.md:134, PR-19) and 2 orphans (item 35). Mock files 19/19, lib 34/34, ui 31/31, assets 36/36. No double owner inside a wave; cross-wave handoffs are F1 -> area partials and F1 -> U1 (`src/ui/ui.css`).
- PR-16 holds on 4.3.4: with `@custom-variant hover (&:hover)`, `hover:` emits `.x:hover`, `group-hover:` emits `:is(:where(.group):hover .x)`, no media gate.
- `translate-` does not match `[transform:translate(`; `sm:` matching inside `max-sm:` is harmless (both banned).
- TypeScript 5.9.3: `noUncheckedSideEffectImports` is off, so `next-env.d.ts`'s `import "./.next/types/routes.d.ts"` does not break `tsc` in a fresh worktree; no page uses `PageProps<>`. `tsc`/`lint` pass on a partial tree as long as imports resolve, which they do (first bullet).
- Owner approved Playwright (commit b119361, PR-14).

## 1. Pre-mortem: the five most likely causes of failure

1. W2 stalls: the lease hook denies every edit in the 14 brace-glob leases (item 2).
2. F0's gate scripts reject valid code: the rule gate fires on verbatim guide tokens and the unknown-class gate demands removal of `cycle`/`stateLabel`/`ui-*` (items 6, 7).
3. Path drift: `components/shell` and `components/vertical` instead of the guide's `layout` and `category`; the verbatim root layout no longer typechecks (item 1).
4. W8 deadlock (F5 needs S6's page, S6 needs F5's layout) plus G5 rows that cannot run at their wave, so leaves get marked VERIFIED on checks nobody ran (items 3, 11).
5. Late audit failures with no owner: A11 trips on `Decree-174` comments in ported code, A5 reads the wrong folder, R3's `@utility` breaks the CSS build, and the SH-02 box and auth-flow checks are not gated at all (items 8, 9, 16, 18).

## 2. Directives

### BLOCKER

**1. BLOCKER: PR-05 path parity is violated by the plan.**
Evidence: `docs/rebuild/PM-RULINGS.md:11` (keep `layout` and `category`) vs `.unlazy/yaobet-rebuild/PLAN.md:41,42,44,48` and `gates/leaf-S1.md:3`, `leaf-S2.md:3`, `leaf-S3.md:3`, `leaf-S7.md:3` (`src/components/shell/**`, `src/components/vertical/**`). The guide's verbatim root layout imports `@/components/layout` and `@/components/layout/QuickActionRail` (`sections/01-07-f-root-layout.html:86-87`); `02-01-s-shell-h.html` has 41 `components/layout/` references and 0 `components/shell`; ScratchCardGame imports `../layout/_internal/usePrefersReducedMotion` (`review/rewards.md:281`). The shell-home §7 rows still carry the overruled names (`review/shell-home.md:281,341,347,353,378`).
Impact: F5 fails `tsc` if it copies the guide; R6/R7 imports diverge; A12 sees paths that match no guide anchor.
Fix: OWNS S1 `src/components/layout/_internal/**`; S2 `src/components/layout/Header.tsx` … `CategorySheet.tsx`; S3 `src/components/layout/{AppShell…RightRail}.tsx` + `src/components/layout/index.ts` (written brace-free, item 2); S7 `src/components/category/**`. Partials keep `src/styles/areas/shell.css` and `vertical.css` (new files under PR-01). Leaf note on S1-S3, S7: "shell-home §5 G-02 and every `components/shell|vertical` path in §7 are superseded by PR-05."

**2. BLOCKER: brace globs in OWNS are denied by the lease hook.**
Evidence: `PLAN.md:14` (allowed_files = the OWNS line). `.claude/hooks/harness_lib.py:852-860` uses `fnmatch` (no brace expansion) and, for `**`, `re.escape` (braces become literals); `harness_lib.py:814` splits inline lists on commas, cutting `{Header,MemberMenu}` in two. Probe: `src/components/shell/{Header,MemberMenu}.tsx`, `src/app/(member)/{tin-nhan,gioi-thieu,dai-ly}/**`, `src/ui/{Icon,Badge}/**`, `src/lib/mock/{helpers,types,lobby}.ts` all return `False` for a file they name; `src/app/[vertical]/**` and `src/app/(member)/layout.tsx` return `True`.
Affected ledgers (14): F3a, F3b, U1, U2, S2, S3, S5, S6, U5, U7, R3, R4, R7, R8.
Fix: rewrite each OWNS line as a brace-free list (one exact path or one `dir/**` per entry) and pass `allowed_files:` as a YAML bullet list. Generate the G4 file arguments from the same list.

**3. BLOCKER: F5 and S6 share W8 but each needs the other.**
Evidence: `PLAN.md:46-47`. `leaf-F5.md:39-41` runs `verify-routes --only /`, but `src/app/page.tsx` belongs to S6; `foundations-core.md:690` (F5 acceptance) also runs the capture `setState('Khách')`, which loads `/`. `leaf-S6.md:34-36` runs `npm run build` without `src/app/layout.tsx` (F5): `next build` fails with no root layout, and `next dev` writes a generated `app/layout.tsx` into the worktree (a lease breach and a merge conflict with F5).
Fix: W8 = F5 alone; new W8b = S6 with Needs F5; S7/S8 need S6 as before. Move F5's G7 and its capture check to S6 (or to the integration ledger, item 11).

**4. BLOCKER: U2 has no lease on `src/ui/ui.css`, where its rules must live.**
Evidence: PR-15 (`PM-RULINGS.md:21`) puts primitive rules in `src/ui/ui.css`; `review/ui-member.md:219-229` marks Dropdown, EmptyState/ErrorState, Modal, Scroller (pseudo-elements), Sheet, Tabs, Tile as method L (ui.css) and K (keyframes); `leaf-U1.md:3` owns ui.css, `leaf-U2.md:3` does not; `ui-member.md:367` (L2 allowed_files) omits it too.
Fix: add `src/ui/ui.css` to U2's OWNS and G4 arguments (a cross-wave handoff U1 W4 -> U2 W5, as `PLAN.md:13` allows). U1 note: "write the base-primitive rules only; U2 appends the composite rules below them."

**5. BLOCKER: route gates assume an unmanaged, shared dev server on :3107, which allows a false PASS.**
Evidence: every UI leaf's G7 (e.g. `leaf-S7.md` and `leaf-S8.md`, both W9, both `--base http://localhost:3107`); `PLAN.md:14` runs 2 builders at once in separate worktrees; no CHECK starts or stops a server. `GATES.md:6` (A1 `--reverify`) reruns every G7 from the root with no server.
Impact: the second worktree's check answers from the first worktree's server (wrong tree, false PASS), or cannot bind; A1 cannot reach ALL MET.
Fix: F0 writes `scripts/with-dev-server.mjs` (zero deps: start `next dev -p <port>` in cwd, exit 1 if the port is already bound, wait for readiness, run the wrapped command, kill the server). Each G7 becomes `node scripts/with-dev-server.mjs --port <leaf port> -- node scripts/verify-routes.mjs --base http://localhost:<leaf port> --only …`, with a unique port per leaf (3110-3139). Keep 3107 for A4/A5 only, wrapped the same way.

**6. BLOCKER: `tw-unknown-classes` as specified rejects classes the plan requires.**
Evidence: PR-23 (`PM-RULINGS.md:29`): "flags any className token that compiles to empty CSS". Probe on 4.3.4: `group`, `cycle` and `ui-btn` each compile to empty CSS. PR-08 (`PM-RULINGS.md:14`) requires literal `cycle` and `stateLabel`; PR-15 requires `ui-*` class names; area partial classes (`sc-*`, `pk-*`, `rc-*`, `review/rewards.md:184-190`) and NavDropdown's real `.active` class (`review/shell-home.md:204`) are also non-utilities.
Impact: S5 G4 can pass only by deleting `cycle`/`stateLabel`, which breaks the 05-01 capture recipe; every primitive and area leaf fails G4.
Fix: the allow-list is every class selector parsed from `src/ui/ui.css` and `src/styles/**/*.css`, plus the fixed set `group`, `group/<name>`, `peer`, `cycle`, `stateLabel`, `active`. Self-test: `cycle` and `ui-btn` (declared in a seed CSS) are clean; `p-4`, `text-sm`, `h-9`, `hover-any:x` are positives.

**7. BLOCKER: `rebuild-rules` as specified is substring-based and fires on verbatim guide CSS.**
Evidence: banned list at `ADR-002.md:58`; F1's G4 scans `'src/styles/**'` (`leaf-F1.md:27`) and A3 scans `'src/**'` (`GATES.md:16`). The original `src/styles/tokens.css` contains `--t-sm:` (line 76), `--t-num-lg:` (84), `--radius-sm:` / `--radius-md:` / `--radius-lg:` (104-106), `--shadow-2:` (122), `--gap-sm:` (144) and `--card-pad-sm:` (151), which hit `sm:`, `md:`, `lg:` and `shadow-`. `transition:` is a valid CSS property in every partial. A bare `/[0-9]+` also hits `aspect-[16/9]` and `top-1/2`.
Impact: F1 cannot pass G4 without editing verbatim tokens, and A3 cannot pass at all.
Fix: tokenise. Apply the class rules only to class tokens extracted from `className`/`class` strings in `.ts`/`.tsx`, anchored at token boundaries (`(^|\s)(max-)?(sm|md|lg|xl|2xl):`, `(^|\s)-?(scale|rotate|translate|skew)-`, `(^|\s)transition(\s|$)`, and `/[0-9]+` only after a colour-utility prefix). Use separate CSS rules for `.css` files (items 8, 13). The self-test's clean seeds include the seven token lines above verbatim, plus `[transform:translate(-50%,-50%)]`, `[transform:scale(1.02)]`, `aspect-[16/9]`, `top-1/2`, `max-639:` and `min-[768px]:`.

**8. BLOCKER: `@utility` inside an area partial is a compile error under the layered import.**
Evidence: `DECISIONS.md:9` (D2 mentions `@utility`); `review/rewards.md:154` (T8: "a named `@utility` in the area CSS file") and `:166-167` (`@utility vip-hero-guest-bg`, `vip-hero-member-bg`); `ADR-002.md:11` imports the partials into `layer(components)`. Probe on 4.3.4: `@import "./areas/vip.css" layer(components);` with an `@utility` inside fails with "`@utility` cannot be nested." (the same with `@layer components { @import … }`).
Impact: R3 breaks the CSS build for every route at W12.
Fix: add to ADR-002 §2: "Area partials and `src/ui/ui.css` contain plain class rules and `@keyframes` only: no `@utility`, `@apply`, `@custom-variant` or `@theme`, and no `@layer` wrapper of their own." Rewrite rewards T8 as plain classes (`.vip-hero-guest-bg{…}`). `rebuild-rules` enforces this on `.css` files.

**9. BLOCKER: F0's gate-script spec contradicts the root gates and the review row.**
Evidence: (a) A3 calls `verify-routes --build-log` (`GATES.md:16`), but `leaf-F0.md:9` specifies only `--base` and `--only`; if an unknown flag is ignored and the script exits 0, A3 passes vacuously. (b) The 05-01 recipe, which `PLAN.md:21` says is copied verbatim, writes to `OUT = './shots'`, while A5 diffs `--got ./.shots` (`GATES.md:26`), so A5 finds 0 pairs. `/shots/` is also not in `.gitignore`, which A11 needs. (c) The F0 row demands that `fd -e mjs verify- scripts` comes back empty (`review/foundations-core.md:684`), while `leaf-F0.md:9` writes `scripts/verify-routes.mjs`. `fd` is also not installed on this host ("fd not found").
Fix: F0 notes are amended as follows. `verify-routes` accepts `--build-log <file>` (asserts every inventory route appears in the build's route table), prints `ROUTES OK n/n` or `INVENTORY OK n/n`, and exits 1 on an unknown flag or an `--only` URL outside the inventory. `capture-shots` stays verbatim except that `OUT` is read from `SHOTS_OUT` (default `./.shots`), and `.gitignore` gains `/.shots/` and `/shots/`. The F0 check becomes `rg --files scripts -g 'verify-*.mjs' | rg -v '^scripts/verify-routes\.mjs$'`, which must print nothing.

### MAJOR

**10. MAJOR: no G5 has a mechanical CHECK, and the rows it points at contain stale values.**
Evidence: every ledger's G5 has no CHECK (`gate-lint`: `manual-gate` plus `unmeasured-number` on each G5). The rows still carry overruled values: `src/styles/components/*.css` (`shell-home.md:341-384`), `src/components/shell|vertical` (item 1), `localhost:3000` (`ui-member.md:368`), `ui-btn-spin` (`ui-member.md:366`), `src/components/account/member.css` (`ui-member.md:374`), the common gate `! rg '(^|[" ])hover:'` (`ui-member.md:362`, contradicts PR-16), `fd` (`foundations-core.md:684`), F4's favicon check (`:689`, the file moved to F5), and `tsc --module commonjs` followed by `node` on files that import `@/…` (`:686-688`; for example orig `lib/mock/index.ts` has 2 `@/` imports), which fails to resolve.
Fix: see §3. Each G5 becomes `CHECK: bash .unlazy/yaobet-rebuild/checks/<leaf>.sh` with `EXPECT: CHECKS_OK`.

**11. MAJOR: some G5 rows cannot run in the wave where the leaf is verified.**
Evidence: F1's row needs `.next/static` after a build (`foundations-core.md:685`), but there is no root layout until W8. S2 needs `curl :3107/` and Playwright box checks (`shell-home.md:350`); S4 needs Playwright auth flows (`:363`); S5 needs a production build and start (`:369`); F5 needs the capture `setState` (`foundations-core.md:690`). Only S3 has a deferral note (`leaf-S3.md:9`).
Fix: split each G5 into G5a (static, runs now) and G5b (deferred). Collect every G5b in a new integration ledger `gates/leaf-I1.md` (OWNS: none; Needs: S6 from item 3) with real CHECK lines. Add I1 to the dispatch table and to A1.

**12. MAJOR: builders are told to read review §2-§5, but parts of review §3 contradict the binding rules.**
Evidence: `leaf-*.md:7` reads "§2-§5 entries". Superseded statements:
- shell-home: T6 relies on preflight for `font: inherit` (`shell-home.md:149`); T9 uses `md:`, `lg:`, `max-md:`, `max-lg:` and new `--breakpoint-*` keys (`:152`); T16 uses `!` (`:159`); §3b uses `md:`, `sm:`, `lg:`, `max-md:` throughout; `bg-(--brand-accent-grad)` claims "background shorthand" (`:223`), which is wrong and emits `background-color` (`ADR-002.md:21`); ADR-SH-01 paths (`:190`); G-02 (`:281`); §6 "Do not copy the duplicate" (`:330`) against PR-28.
- ui-member: T1 `hover-any` and "never bare `hover:`" (`ui-member.md:147`); T9 names `ui-btn-spin`, `ui-modal-pop`, `ui-dropdown-drop`, `ui-skeleton-sweep` and `max-sm:animate-[…]` (`:155`) against PR-18; G-15 StubPage (`:340`).
- rewards: T4 "the defaults `sm` 640, `md` 768, `lg` 1024" (`rewards.md:150`); T8 `@utility` (`:154`, item 8); §3.2 `md:`/`lg:` and `grid-cols-N` (`:174-193`, item 14).
Fix: add a "Superseded review statements" table to ADR-002 with the list above, and change each ledger's line 7 to "… §2-§5, except the statements ADR-002 lists as superseded".

**13. MAJOR: PR-01's keyframe-prefix rule contradicts the review checks.**
Evidence: `PM-RULINGS.md:7` ("Keyframe names get an area prefix") against `shell-home.md:342,344` (8 unprefixed shell names), `:369` (`heroSeg(Grid)?`), `rewards.md:328` (`token-pulse`) and `:329` (`bob`; PR-01's own example `card-foil-sweep` is not `collection-` prefixed). A census of the original's keyframes finds only 3 colliding names: `sweep` (Skeleton and CardArt), `slideUp` and `fade` (primitives, already covered by PR-18).
Fix: amend PR-01: "Keep the guide's keyframe names. Rename only the colliding ones: the primitives per PR-18, and CardArt `sweep` -> `card-foil-sweep`." `rebuild-rules` asserts that every `@keyframes` name in `src/**` is unique.

**14. MAJOR: the banned list misses lookalike utilities that emit wrong CSS, so neither gate catches them.**
Evidence: probe on 4.3.4 with `--*: initial`: `duration-150`, `transition-transform`, `transition-all`, `transition-opacity`, `from-(--x)`, `bg-conic-(--x)`, `skew-x-3` and `divide-y` all emit CSS (so `tw-unknown-classes` passes them), and each changes the computed value. `grid-cols-3` emits `repeat(3, minmax(0, 1fr))`, while the original has 32 `repeat(N, 1fr)` declarations (e.g. `ProviderGameGrid.module.css:21,46,55,61`); the reviews recommend `grid-cols-3 md:grid-cols-4` (`shell-home.md:221`) and `grid-cols-2 md:grid-cols-3 lg:grid-cols-4` (`rewards.md:179`). `!` is forbidden by `ADR-002.md:37` but is not on the §4 list.
Fix: add class-token rules `transition-(all|colors|opacity|shadow|transform)`, `(duration|delay)-[0-9]`, `ease-(in|out|in-out|linear)`, `(from|via|to)-`, `bg-conic-`, `-?skew-`, `divide-`, `grid-(cols|rows)-[0-9]+`, and a leading or trailing `!` (a per-file allow-list only where the guide has `!important`). Add an ADR-002 §2 row: `repeat(N, 1fr)` -> `grid-cols-[repeat(N,1fr)]`.

**15. MAJOR: several leaves need CSS beyond utilities but own no partial.**
Evidence: `ADR-002.md:38` sends pseudo-elements and descendant or compound selectors to "the leaf's own partial". S2 and S3 have none (S1 owns shell.css); U4-U7 have none (U3 owns member.css); R4 has none (R3 owns vip.css); R8 has none (R7 owns collection.css). Cases: NotificationBell `::before` (`shell-home.md:206`), MessageCenter `.itemUnread::before` (`ui-member.md:238`), the SearchField noscript hooks (`ui-member.md:330`).
Fix: amend the ADR-002 row: "pseudo-elements with at most 3 declarations use `before:`/`after:` utilities with `content-['']`". Where a partial is still needed, add a cross-wave handoff line to OWNS (S2 and S3 -> shell.css, R4 -> vip.css, R8 -> collection.css, U4 and U5 -> member.css). Add a census gate to every leaf G4: `rg --files src -g '*.css' | sort` must equal the fixed list (globals.css, the 6 guide sheets, keyframes.css, tw-theme.css, stub.css, ui.css, the 10 areas), so an unimported stray CSS file fails.

**16. MAJOR: the hygiene regex misses most tag families and the regulatory comments in verbatim code.**
Evidence: A11's regex (`GATES.md:48`). Tag census of the original `src/`: `J<n>` 311 times, `SPEC-` 183, `BR-` 36, `Wave` 29, `GC-` 26, `UT-` 23, `ruling A<n>` 17, `ST-` 15, `FR-` 13. The term "Decree-174" appears on 25 lines in 23 files (e.g. `lib/rg.ts:5`, `lib/format.ts:7`, `ui/Odometer/Odometer.tsx:2,7,54`) and in a verbatim guide CSS comment (`sections/02-03-s-home-h.html:93`). PR-03 and PR-26 ports carry these comments, so A11 (`decree`) fails only at the end. `YB-668812` and `YB-880066` are rendered copy (`shell-home.md:363`), so a naive `[A-Z]{2}-[0-9]+` would be a false positive.
Fix: extend PR-27 to strip regulatory references from comments (comment-only, no runtime effect). In `rebuild-rules`, scan comments only for `\b(SPEC|GC|BR|UT|ST|FR|DEFECT|CASE|UC|NFR|AC|OD)-[0-9]+\b|\bJ[0-9]+\b|\bWave [0-9]|\bruling [A-Z][0-9]+|\bPR-[0-9]{2}\b|decree|nghị định|giấy phép|statute|regulat`, run it in every leaf's G4 (catch it at the leaf), and widen A11 to the same regex.

**17. MAJOR: A5 counts pairs instead of measuring fidelity, and time-based values make a raw pixel diff noisy.**
Evidence: A5 EXPECT is "72 pairs compared, 0 missing" (`GATES.md:27`). The recipe saves JPEG at quality 72, full page. Time-based values: countdowns (`role="timer"`), the member-day countdown, now-relative promo `endsAt` (`shell-home.md:121`), store cooldowns (PR-04, REWARDS-16), and the wallet and collection times (`ui-member.md:332`, `rewards.md:285`). The reference set was captured on 2026-11-05 10:41 (`shots/manifest.json` mtime).
Fix: `shot-diff` reports per pair: size equal, mismatch % at a per-channel threshold of 16/255 (absorbs JPEG noise), and the mismatch outside masks. Masks are the boxes of the selectors in `checks/shot-masks.json`, recorded by an extra `page.evaluate` after each screenshot (pixels unchanged, recipe otherwise verbatim). EXPECT: `72 pairs, 0 missing, 0 size-mismatch`; each pair over the threshold outside masks needs an A6 justification row.

**18. MAJOR: checks the plan promises are not gated anywhere.**
Evidence: `leaf-S2.md:9` says "box checks run in the root visual gate", but GATES.md has no box gate. A9's CHECK covers only the DEV-toggle absence (`GATES.md:40`), not register -> level-0 -> login -> reload. The PR-13 gate ("grep … in the built CSS", `PM-RULINGS.md:19`) is in no ledger. `leaf-F1.md:9` says "add a gate that proves `group-hover:`" without a CHECK. A7's font subset has no CHECK. The L6 filler count (5 ComingSoonTiles at 1440, `shell-home.md:375`) is Playwright-only.
Fix: add A5b `node scripts/box-check.mjs` (02-01 measured boxes at 375/768/1024/1440 after `document.fonts.ready`, ±1 px); add `scripts/auth-flow.mjs` to A9; in I1 add `rg -l 'U\+1EA0-1EF9' .next/static` and, for each name in `--brand-accent`, `--brand-accent-2`, `--canvas`, `--text-hi`, `rg -l -- '<name>:' .next/static`; give F1 a CHECK that compiles `group-hover:x` and asserts there is no `@media (hover`.

**19. MAJOR: the Playwright range can pull in a different Chromium.**
Evidence: `PLAN.md:21` and PR-14 specify `^1.61.1`. The cached browsers are `chromium-1228`, which is Playwright 1.61.1 (orig `apps/web/node_modules/playwright-core/browsers.json`). The reference shots were rendered with that build.
Fix: pin exactly `"playwright": "1.61.1"`; A11 asserts the exact version.

**20. MAJOR: every build gate from W8 on depends on Google Fonts network access.**
Evidence: `next/font/google` (orig `app/layout.tsx:15`; `foundations-core.md:700`, risk 5). From this sandbox, `curl https://fonts.googleapis.com/css2?family=Montserrat` returned `000` (LOW-CONFIDENCE ASSUMPTION about the builders' network). A newer font version also shifts the SH-02 ±1 px boxes.
Fix: before W8 the PM runs a preflight that must return `200`. I1 compares the sha256 set of `.next/static/media/*.woff2` with the original build's 15 files (`Igaming-Agent-1/apps/web/.next/static/media`).

**21. MAJOR: F2's token-lint gate has nothing to read in W1.**
Evidence: `leaf-F2.md:21-24` runs `npm run lint:tokens` in W1, in parallel with F1, which creates `brands.css` and `tokens.css`; A1 and A3 read those files (`ADR-002.md` §3). The result is either a crash or a vacuous pass.
Fix: `token-lint` exits 1 with `definition files missing` and never passes vacuously. Drop G3 from F2 and run it in the PM's post-merge check after W1.

**22. MAJOR: rule-gate glob arguments can match zero files and pass vacuously.**
Evidence: `'src/app/[vertical]/**'` in `leaf-S7.md` G4 is a character class in glob syntax. Brace arguments (`leaf-S2.md` G4 and others) need expansion.
Fix: both scripts expand braces, treat `[` and `]` as literals, and exit 1 when any argument matches 0 files. The self-test seeds both cases.

**23. MAJOR: the plan adds two files the original never had.**
Evidence: `src/components/home/Home.tsx` (`leaf-S5.md:3`) does not exist in the original: there `Home.module.css` is imported directly by `app/page.tsx:46` and `app/loading.tsx:12`. `src/components/utility/StubPage.tsx` (`leaf-U7.md:3`, `leaf-R4.md:9`) does not exist either: there each stub page imports `../stub.module.css` (`app/cau-lac-bo/page.tsx:6`, plus 4 more pages). A12 requires "no fabricated … files".
Fix: drop both. `page.tsx` and `loading.tsx` use the `home.css` classes from S5. The stub pages, `/cau-lac-bo` included, use F1's `stub-*` classes from `src/styles/stub.css` (`foundations-core.md:685`). Remove U7 from R4's Needs.

**24. MAJOR: nobody can fix a gate script after W0.**
Evidence: `scripts/**` is only in F0's lease (`leaf-F0.md:3`). A false positive found at W5 would stall every later leaf.
Fix: add a standing hot-fix lease (`debugger`, `allowed_files: scripts/**, .unlazy/yaobet-rebuild/checks/**`), used only on the PM's order. After each fix, rerun G4 for every merged leaf.

### MINOR

25. MINOR: `leaf-F5.md:27` passes the binary `favicon.ico` to the text gates. Fix: drop it from the G4 arguments.
26. MINOR: every G6 writes to the same `/tmp/yb-build.log` while 2 worktrees run at once. Fix: use `/tmp/yb-build-<leaf>.log`.
27. MINOR: A9 leaves `next start -p 3108` running (`GATES.md:40`), and A3 reads A2's log file (`GATES.md:16` and `:11`). Fix: wrap A9 with `with-dev-server.mjs` (start mode), and let A3 build or check that the log exists.
28. MINOR: F4 has three conflicting sources on the 3 `(1)` duplicates (`shell-home.md:330` against PR-28, `foundations-core.md:689` and `01-10-f-assets.html`, which list 36 files including them). Fix: F4 note: "36 files including the 3 duplicates; shell-home §6 last line superseded".
29. MINOR: F0 must keep the `.claude/**` ignore in `eslint.config.mjs` (it is there now) and add the collection ports-barrel rule its row checks (`foundations-core.md:684`). Neither is in `leaf-F0.md:9`.
30. MINOR: `src/styles/stub.css` (F1 row) is not in ADR-002 §1's import order (`ADR-002.md:11`). Fix: name its import position.
31. MINOR: if `ui.css` or a partial wraps itself in `@layer components`, it becomes the nested sublayer `components.components`, and its rules lose to the unwrapped partial rules whatever the import order. Yet UIM-L1 checks `rg -q '@layer components' src/ui/ui.css` (`ui-member.md:366`). Fix: no wrapper of their own (item 8); move that check to the import line in `globals.css`.
32. MINOR: `verify-routes` must print `ROUTES OK n/n` and fail on an empty `--only` match, so the substring EXPECT cannot pass on 0 checks.
33. MINOR: the reference shots come from `next dev` 16.2.9; the 16.4.5 dev indicator may look different (LOW-CONFIDENCE). Fix: add its box to `shot-masks.json`.
34. MINOR: gate-lint's `unmeasured-number` warnings come from "§7" in the G5/G9 titles. Fix: reword those titles.
35. MINOR: orphan inventory: `components/vip/VipPage.module.css` (used only by `app/tier/page.tsx`) has no named owner; `app/stub.module.css` is covered only implicitly. Fix: R4 note "VipPage styles as utilities"; F1 note "stub.css replaces `stub.module.css`".

## 3. Making G5 mechanical: `.unlazy/yaobet-rebuild/checks/`

- Author: the PM, or a QC role. Never the leaf's builder (generator-evaluator separation). The checks are committed before the leaf is dispatched; the builder only runs them.
- Layout: `checks/lib.sh` (helpers `expect_count <n> <cmd>`, `expect_match <pattern> <file>`, `fail <id> <expected> <got>`); `checks/ts-run.mjs` (Node 24 type stripping plus a `module.register` resolve hook mapping `@/` to `src/` and extensionless imports to `.ts`, `.tsx` or `index.ts`; zero dependencies; replaces the `tsc --module commonjs` steps); `checks/shot-masks.json` (item 17); one `checks/<leaf>.sh` per leaf.
- Contract: print `Fail: <check-id> | Expected: <A> | Got: <B>` for each failure, end with `CHECKS_OK <leaf> <n>/<n>` only when every check passed, and exit non-zero otherwise. G5: `CHECK: bash .unlazy/yaobet-rebuild/checks/<leaf>.sh`, `EXPECT: CHECKS_OK`.
- Normalisations applied once in the scripts:
  - paths per PR-05 (item 1);
  - `src/styles/components/` -> `src/styles/areas/`, and `src/components/account/member.css` -> `src/styles/areas/member.css`;
  - ports through `with-dev-server.mjs` (item 5);
  - `ui-btn-spin 700ms linear infinite` -> `ui-spin 700ms linear infinite`;
  - keyframe names per the amended PR-01 (item 13);
  - `fd` -> `rg --files`;
  - F4's favicon check moved to F5;
  - the bare-`hover:` ban dropped (PR-16);
  - the L6 deletions dropped (the F0 wipe);
  - deferred checks moved to I1 (item 11).
- Ledgers that need this most, by blast radius:
  1. F1 (163 tokens, 115 theme keys, `layer(base)` = 6, 7 `ui-*` keyframes, no preflight);
  2. F2 (formatter oracle; every money string depends on it);
  3. F3a and F3b (dataset oracles);
  4. U1 (44 icon paths) and U2 (39 barrel exports);
  5. F0 (8 seeds, `cacheComponents` = 0);
  6. F4 (36 files `cmp`);
  7. R1 and R2 (unit maths);
  8. R6 (`CLEAR_THRESHOLD`, PR-13 names);
  9. then S1-S8, U3-U7 and R3-R8 (copy greps and route checks).

## 4. Audit reachability (A1-A12) as written, and after the directives

| Gate | Now | After |
|---|---|---|
| A1 reverify | No (no server, items 5, 11) | Yes |
| A2 static | Yes, needs fonts (20) | Yes |
| A3 inventory | No (items 7, 9) | Yes |
| A4 routes | Server not managed | Yes |
| A5 72 shots | No (dir mismatch, 9) | Yes, masked (17) |
| A6 visual | Judgement only | Has a report |
| A7 copy/fonts | Manual | Font CHECK (18) |
| A8 states | Manual | Manual |
| A9 mock auth | Toggle only | Full flow (18) |
| A10 FIX-LIST | Manual sample | Manual sample |
| A11 hygiene | Fails late (16) | Fails early |
| A12 oracle | Rejects paths (1, 23) | Can pass |

What an Oracle would reject at the end as written: paths that differ from the guide (1); `StubPage.tsx` and `Home.tsx` with no anchor (23); `Decree-174` and tag comments in ported files (16); A5 "passing" with 0 compared pairs or with an uncalibrated diff (9, 17); route evidence from another worktree's server (5); no box-check evidence for SH-02 (18).

## 5. Verdict

**REJECT** in its current form: 9 BLOCKER, 15 MAJOR, 11 MINOR. The wave structure, coverage and ownership model are sound, and no redesign is needed. The BLOCKERs are plan-text and F0-spec corrections (items 1-9), and all of them must land before F0 is dispatched, because F0 writes every gate script. After that, re-gate as a delta review of items 1-24 only.

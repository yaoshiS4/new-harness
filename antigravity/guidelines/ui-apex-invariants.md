# UI Apex Invariants (Anti-Slop)

Field-tested UI review invariants. Cited sources are real (NN/g heuristics, Bastien & Scapin concision, Apple HIG, Material 3, WCAG 2.2).

## Rule Precedence

1. **Accessibility & functional correctness** (WCAG, platform requirements)
2. **Product/brand/domain requirements** (existing design system, brand guidelines)
3. **Design system constraints** (project tokens, component library)
4. **Anti-slop heuristics** (see `anti-slop-taxonomy.md`)
5. **Stylistic preferences** (taste, trends)

Higher layers override lower. Anti-slop rules are conditional heuristics unless marked HARD BAN.

## Navigation & Flow
- Every computed/result or deep-dive state MUST show an explicit Back/Return trigger at the top of the viewport. Zero dead-end screens (NN/g #3).
- Primary re-run/recalculate actions and mode selectors sit within the initial fold or docked thumb zone; never below large content cards.

## Information Density
- No echoey subtitle padding under section titles; eyebrow + title stands alone (NN/g #8, Bastien & Scapin concision).
- Compound strings (`·`, `/`, `&`, parentheticals) get deliberate line-break planning to avoid mid-clause wraps on narrow viewports.

## Controls & Touch
- Auxiliary pickers/settings adjacent to a primary CTA use circular or pill icon buttons, never text buttons with dropdown glyphs.
- Touch targets: Apple HIG >= 44pt; Android M3 >= 48dp; >= 44x44 minimum elsewhere. Touch target gap >= 8dp.
- Multi-button rows: >= 12dp gap, prefer 16dp spacing token. Safe-area buffer >= 34pt iOS / >= 20dp Android.
- Thumb-Zone Reachability (Fitts's Law 2.0 / Law 36): Primary interactive controls, date steppers, triage lenses, and critical CTAs sit within the bottom 40% of the mobile viewport; never desert the thumb zone (L-21).
- 3-Tier Sensory Tactile Hierarchy (Apple HIG / Law 39): Selection ticks for wheels/tabs, impact (light/medium/heavy) for drawer snaps and ritual actions, notification for task completion or conflict alerts. Zero gratuitous vibration on passive scrolling (G-11).

## Layout & Tokens
- Horizontal toolbars, headers, and action rows enforce bilateral visual balance across the central vertical axis (Law 34 / Gestalt Symmetry).
- Second-layer segmented tabs use the canonical pill-tab design tokens (full pill geometry, border-free, semibold typography). Never invent custom boxed stepper/node rows.
- Colors and type come from design tokens only; zero speculative hex values (anti-hallucination rule AP-03).
- Depth & Elevation (Apple HIG / M3): 5 standardized elevation tiers (`elevation.ts`) using warm soot ink diffusion (`rgba(42, 36, 33, ...)`) and tonal parchment shifts; zero raw black drop-shadows (D-13).
- Stacking Context Scale (Law 42): Z-indices strictly consume canonical tokens (`base: 0`, `card: 1`, `stickyHeader: 10`, `floatingBar: 20`, `backdrop: 50`, `drawer: 100`, `modal: 200`, `toast: 300`). Zero arbitrary z-index arms races (M-10).
- Cognitive Chunking & Density (Miller's Law & Sweller / Law 37): Max 4-5 items per scannable cluster; enforce >= 32dp vertical breathing across section dividers (`spacing.sectionGap`, L-20).

## Anti-Slop Hard Bans (Always Defects)

These patterns are never acceptable regardless of context:

- **Stacking Context Collision / Z-Index Arms Race** (M-10): Arbitrary high z-index numbers (`9999`, `1000`) breaking stacking order or causing phantom tap interception. Use canonical zIndex scale (`zIndex.ts`).

- **Careless Ellipsis Truncation / Mid-Word Clipping** (L-16): Slicing proper nouns or short data labels into mid-word stubs (e.g. `"Thanh Lo..."` for `"Thanh Long"`) with uncalculated `numberOfLines={1}`. Strip redundant category words, right-size type, or permit clean multi-line wrapping.
- **Card Inception / Nested Cards** (L-01): Bordered or elevated cards nested inside another card or bordered container. Single containment layer only; inner levels use whitespace or hairlines.
- **Tag-Left / Header-Right Two-Column Head** (L-14): Eyebrow/label in a left column beside the section heading. Vertical single-column stack only (`flex-direction: column`).
- **Wrapping Clickable Affordances** (L-15): Button, chip, or CTA text breaking onto two lines. Clickable text must fit a single line (`white-space: nowrap`).
- **Asymmetrical Multicolumn Telemetry Alignment** (L-17): Multi-column analytical or horology strips (e.g. 3-column Tam Sát, 12 Canh Giờ) having uneven column heights, mismatched glyph baselines, or irregular label widths. Must enforce identical vertical baselines, uniform directional prefixes, and fixed label column widths for perfect bilateral symmetry.
- **Re-Drawn UI Chrome** (I-05): Hand-built browser URL bars, OS traffic-light dots, or simulated device notch frames in code. Use real screenshots or borderless component previews.
- **State Geometry Jitter** (M-07): Shifting `border-width` between states (e.g. 1px to 2px on focus/active). Keep 1px constant; express state via `outline`, `border-color`, or `box-shadow`.
- **Directional Motion Inversion (Counter-Clockwise Refresh Spin)** (M-08): Functional refresh/reload indicators and rotation transforms rotating counter-clockwise (`0deg` to `-360deg`). Refresh affordances must strictly rotate clockwise (`motion.rotation.fullClockwise` `['0deg', '360deg']`), utilizing Apple gold standard spring curves without jitter.
- **Fragmented Metric Typography (Split Font-Scale in Compound Pairs)** (T-15): Splitting font size or variant between a qualifying noun/label and its numerical score (e.g. `'Hợp '` in 12px with `'58'` in 10px). Must consume a single canonical text variant to preserve baseline integrity and eliminate visual stutter.
- **Awkward Mid-Phrase Word Wrapping / Vietnamese Compound & General Punctuation Splitting** (W-08): Slicing compound terms (Can Chi, directions like `Đông Bắc`, `Hỷ thần`, coordinates, percentage scores `Hợp 88%`) or leaving dangling/orphaned punctuation marks (`·`, `•`, `,`, `/`, `\`, `()`, `[]`, `:`, `;`, `-`, `–`, `|`) across line wraps. Deliberate non-breaking space (`\u00A0`) or discrete structural rows must be used around all general punctuation (`\u00A0·\u00A0`, `\u00A0/\u00A0`, `\u00A0–\u00A0`, `\u00A0(`); line breaks must strictly occur only immediately after natural clause delimiters (only following `,`, `;`, or line-breaks between key-value pairs).
- **Dual-Segment Lens Parity** (D-11): Primary 2-option view switchers (e.g. [ Chung | Cá nhân hóa ], [ Cơ bản | Nâng cao ]) across all primary screens and modal drawers must enforce identical height (`spacing.pillHeightMd: 32dp`), unified typography (`typography.tabLabel`), and centered max width constraint (`maxWidth: 320`).
- **Multi-Modal Redundancy & Signal Stutter (Poly-Encoding)** (D-12 / AP-08, cross-ref D-11): Over-stating or repeating a single semantic polarity or attribute across $\ge 3$ simultaneous modalities on one node (e.g. indicator dot + parenthetical tag `(Cát)` + descriptive evaluation text `Tốt vừa` + icon). Enforce **Singular Modality**: max 1 subtle visual indicator (5–6px dot) + 1 descriptive textual assessment. Strip parenthetical tags (`(Cát)`/`(Hung)`) whenever a rating phrase (`Tốt vừa`, `Rất tốt`, `Đại hung`) or dedicated description is present. Never stack `dot + (Tag) + Description`.
- **Tautological Helper Microcopy & Empty Echoes (Obvious-Action Subtitles)** (W-09): Generating helper subtitles, hints, or captions that merely paraphrase or narrate the self-evident title or control affordance (e.g. "Chuyển nhanh đến ngày bạn cần tra cứu" under "Chọn ngày tháng năm"). Subtitles must strictly provide dynamic domain metadata (concrete dates, location coordinates, item counts, technical qualifiers); otherwise omit entirely.
- **Compound State Erasure / Anchor Obliteration** (L-22): Overwriting an immutable temporal anchor (such as "Today") when applying an interactive selection state. In calendar grids and date pickers, when today is unselected, render in a clean circle with a thin black border (`borders.thin` $1\text{dp}$) and no background color; when any day (today or another day) is selected, render in a solid black circle with no border and white text (`textInverse`). Never introduce conflicting yellow or bronze accent borders on today that clash with gold holiday markers.
- **Singular Polarity & De-Echoed Rating Typography** (D-14): Stacking redundant category pills (e.g. `Hắc đạo` pill) alongside composite evaluation scores (`Đại hung 30%`), or placing pulsing dots on passive navigation text (`"Đang diễn ra ›"`). Place a single 5–6px `PulseDot` (green/red) directly preceding the rating compound. Eliminate redundant category pills (`Hắc đạo`/`Hoàng đạo`). Passive navigation affordances must use neutral ink text with `›` chevron and zero pulsing.
- **Calendar Milestone Ambiguity & Anti-Overexpression** (T-17): In calendar grids, lunar month suffixes (`/tháng`) are strictly restricted to actual lunar milestones (Mùng 1 Sóc and Rằm 15). In detail snapshot cards and brief headers, avoid echoing verbose parenthetical tags (`(Mùng 1)` / `(Rằm)`) or Can Chi day suffixes when date context is already clear or accessible in dedicated full views, avoiding visual clutter and redundant noun echoes.
- **IME Pre-Edit Racing & Simulated State Resets** (F-05 / G-12 / AP-17): Executing synchronous string masking/formatting while text composition is active (causing character duplication like `HHàà NNội` or cursor jumping), or restoring hardcoded mock data on form reset. Defer input masking until composition ends. Reset actions must strictly set form fields to empty strings/defaults, never restoring developer test profiles.
- **Ephemeral Cache Cascading Invalidation & Zero-Flicker Hydration** (G-13): Domain event listeners (e.g. GPS resolve, setting change) must strictly invalidate calculation caches (`calendarInvalidationListeners`) without wiping unrelated temporal UI caches (location names, weather). Hydrate synchronously on frame 0 from persistent or in-memory caches to eliminate visual pop-in or reload flashing on tab navigation.
- **Fabricated Proof & Cliché Metrics** (W-06): Inventing quantitative claims ("10x faster", "50,000+ teams") without evidence.
- **Emoji as functional icons** (T-04): Use SVG icon library. Emojis fail accessibility and render inconsistently.
- **Contrast mud** (C-03): Gray text on colored backgrounds. Verify ≥ 4.5:1 contrast.
- **Low-contrast labels** (C-06): Text < 4.5:1 on background. Meet WCAG AA minimum.
- **Cartoon easing** (M-01): Bounce/elastic on UI transitions. Use ease-out/ease-in.
- **Layout repaints** (M-02): Animating width/height/margin. Use transform/opacity only.
- **Missing interactive states** (M-03): Define all 8 states (default, hover, focus, active, disabled, loading, empty, error).
- **Missing reduced motion** (M-06): Provide fallback for `prefers-reduced-motion`.
- **Div-based fake screenshots** (I-01): Use real screenshots or actual component previews.
- **Placeholder assets shipping** (I-03): Replace all placeholders before shipping.
- **Missing empty/error/loading states** (G-04, G-05, G-06): Every list/form/action needs all three.
- **Inaccessible focus** (G-07): Visible focus ring on all interactive elements.
- **Form wipe on error** (G-08): Preserve user input on validation failure.
- **No keyboard navigation** (G-09): All interactive elements must be keyboard-accessible.
- **Silent failures** (G-10): Toast/alert for all async outcomes.
- **Dead-end screens** (L-12): Every screen needs an escape route.
- **Touch target crowding** (L-11): Minimum 8dp between interactive elements.
- **Overflowing content** (L-10): Never clip text with fixed height.
- **Dense desktop on mobile** (L-07): Explicit mobile layout with ≤ 2 columns.

## Anti-Slop Conditional Heuristics (Avoid by Default)

These patterns should be avoided unless justified by the design contract, product requirements, or accessibility needs. See `anti-slop-taxonomy.md` for full catalog with IDs, detection signals, and exceptions.

**Typography**: Invisible defaults (T-01), fake dev vibes (T-02), icon-header crutch (T-03), single-weight hierarchy (T-05), ransom note > 3 families (T-07), gradient text without meaning (T-10), orphaned eyebrow numbers (T-11), icon-as-bullet fatigue (T-12), italicized heading word (T-13), eyebrow proliferation / chapter tic (T-14).

**Color**: AI palette defaults (C-01), dead grays without tinting (C-02, C-05), hue chaos (C-04), semantic color overload (C-07).

**Layout**: Card inception (L-01), 3-column clone grid (L-02), arbitrary spacing (L-03), centered everything (L-04), scaffolding first (L-05), copy-paste layouts (L-06), zero-breathing containers (L-08), carditis/card soup (L-13), tag-left/header-right split (L-14), wrapping affordances (L-15), careless ellipsis truncation (L-16), buried telemetry (L-23), monolithic spacing rhythm (L-24), sibling analytical list inconsistency (L-25).

**Decoration**: Signal overload (D-01), dead backgrounds (D-02), gratuitous accents (D-03), glassmorphism overuse (D-04), neon glow defaults (D-05), thick side-tab borders (D-06), decorative dots (D-08), badge & pill proliferation / capsule quilt (D-09), unmotivated ambient decoration / floating orbs (D-10).

**Motion**: Motion without meaning (M-04), uninterruptible animations (M-05), state geometry jitter (M-07).

**Copy**: Redundant UX writing (W-01), filler verbs (W-02), generic CTAs (W-03), fake personalization (W-04), parenthetical explanations (W-05), fabricated proof (W-06), over-expressing & redundant category prefixes (W-07), tautological helper microcopy (W-09), destination navigation duplication & verbose row titles (W-10).

**Imagery**: Stock photo defaults (I-02), hand-rolled decorative SVGs (I-04), re-drawn UI chrome (I-05).

**General**: No design contract (G-01), no finish gate (G-02), visual language reuse (G-03), sensory feedback stutter (G-11), userflow coherence & segment misalignment (G-14).

## Design Contract & Finish Gate

**Before building UI**, define:
- Screen job (what problem does this solve?)
- Primary user and context
- Primary action (what does the user DO?)
- Required states (default, hover, focus, active, disabled, loading, empty, error)
- Negative constraints (what AI defaults to avoid?)
- Accessibility targets (WCAG level, keyboard navigation, reduced motion)
- Responsive behavior (mobile layout, touch targets, breakpoint strategy)

**Before shipping UI**, verify finish gate:
- Screen purpose obvious within 3 seconds
- One primary action clearly leads hierarchy
- Every visible control has real outcome
- Content belongs specifically to this product
- All required states implemented and reachable
- Responsive behavior intentional
- No HARD BAN patterns present
- AVOID patterns have explicit rationale if used

## UI Skill Family Priority
Pick the appropriate active skill for each stage of UI work:
1. `ui-ux-craft` - design contract, style, palette, token decisions, flow specifications, and building screens/components (implementation).
2. `animation-mastery` - spring physics, curves, duration guidelines, and motion engineering.
3. `ui-ux-audit` - read-only QC and anti-slop audit pass on finished UI (`Role: "frontend-qc"`, run after build).
Do not co-load overlapping UI skills simultaneously during implementation.

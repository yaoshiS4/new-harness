# Anti-Slop Taxonomy

Compact reference of AI-generated UI anti-patterns with stable IDs, severity, detection signals, and conditional fix directives.

**Source**: Adapted from [Impeccable](https://impeccable.style/) by Paul Bakaus (Apache 2.0), [UIZZE anti-ui-slop](https://github.com/uizze/uizze/tree/main/skills/anti-ui-slop), and field-tested agent review patterns.
**Version**: 2026-09-07 · Impeccable v64k catalog baseline.

## Rule Precedence

1. **Accessibility & functional correctness** (WCAG, platform requirements)
2. **Product/brand/domain requirements** (existing design system, brand guidelines)
3. **Design system constraints** (project tokens, component library)
4. **Anti-slop heuristics** (this taxonomy)
5. **Stylistic preferences** (taste, trends)

Higher layers override lower. Anti-slop rules are **conditional heuristics**: avoid by default unless justified by layers 1-3.

## Severity Legend

- **HARD BAN**: Always a defect. No exceptions.
- **AVOID**: Default to avoiding. Override with explicit design rationale.
- **CHECK**: Verify contextually. May be correct or incorrect depending on intent.

---

## T: Typography

| ID | Pattern | Severity | Detection Signal | Fix Directive |
|----|---------|----------|-----------------|---------------|
| T-01 | **Invisible Defaults** — Inter/Roboto/Arial/Open Sans for every text layer without intentional selection | AVOID | Single `font-family` across all weights/roles | Require explicit font rationale in design brief. System-UI is acceptable when justified for platform-native feel. |
| T-02 | **Fake Dev Vibes** — Monospace on headings as lazy "technical" shorthand | AVOID | `font-family: mono` on `h1`-`h3` or display text | Use monospace only for code, data, or when the product IS a developer tool. |
| T-03 | **Icon-Header Crutch** — Large colored icon above every section heading | AVOID | Icon container > heading text size, repeated per section | Create visual interest with type scale, weight, and spacing. Max 1 icon per interactive element; 0 on static telemetry. |
| T-04 | **Emoji as Icons** — Unicode emojis as functional UI icons | HARD BAN | `✅⚡🔥📅📍` in interactive controls or navigation | Use SVG icon library (Lucide, Phosphor) with explicit bounding boxes. Emojis render inconsistently and fail accessibility. |
| T-05 | **Single-Weight Typography** — One font weight for all hierarchy | AVOID | All text `font-weight: 400` or `500` | Use ≥ 3 distinct weights for display/heading/body hierarchy. |
| T-06 | **Micro Text** — Body text < 14px or line-height < 1.4 | CHECK | `font-size < 14px` or `line-height < 1.4` on body | Minimum 14px body, 1.4 line-height. Adjust for language (Vietnamese diacritics need ≥ 1.45). |
| T-07 | **Ransom Note Typography** — > 3 font families on one page | AVOID | Count distinct `font-family` declarations | Max 2 families (display + body) unless product requires more (e.g., code + prose). |
| T-08 | **Decorative Italics Abuse** — Italicized display text with descender clipping | CHECK | `font-style: italic` on `h1`-`h2` with `y/g/j/p/q` | Ensure sufficient line-height and padding for descenders. |
| T-09 | **All-Caps Overuse** — Entire paragraphs in uppercase | AVOID | `text-transform: uppercase` on > 20 words | Reserve all-caps for labels, badges, and short headings (≤ 5 words). |
| T-10 | **Gradient Text on Headings** — Gradient fill purely for "pop" | AVOID | `background: linear-gradient` on text without semantic purpose | Use gradient text only when it communicates brand or content meaning, not decoration. |
| T-11 | **Orphaned Eyebrow Numbers** — "01 / 02 / 03" in non-sequential headings | AVOID | Numbered headings without sequential content | Remove decorative numbering unless content is genuinely sequential. |
| T-12 | **Icon-as-Bullet Crutch (Icon Fatigue)** — Repeating checkmarks, crosses, or arrows on every list item | AVOID | Same icon repeated on > 2 list items where the section/column header already states the polarity | Remove repetitive bullet icons. Rely on typographic hierarchy, clean spacing, and column headers. Reserve icons for interactive controls or singular state indicators. |
| T-13 | **Italicized Heading Word** — Single word italicized inside an upright headline or all-italic display type | AVOID | `font-style: italic` on `h1`-`h6`, display headings, or `<em>` in titles | Headings must be roman (`font-style: normal`). Express emphasis with font-weight or accent color. Reserve italics strictly for running prose. |
| T-14 | **Eyebrow Proliferation (Chapter Tic)** — Uppercase mono-cap labels (`01 / OVERVIEW`) on every section | AVOID | Numbered or mono eyebrows on > 2 non-sequential sections | Default OFF. Use eyebrows only when content is genuinely sequential (steps/chapters) and cap at 1–2 per page. |
| T-15 | **Fragmented Metric Typography** — Splitting font scale/variant between a qualifying noun and its numerical metric (e.g. `"Hợp "` in 12px with `"58"` in 10px) | HARD BAN | Nested `<Text>` nodes with unequal `fontSize` inside a metric/score phrase | Consume a single canonical typography variant. Preserve uniform baselines and avoid illegible micro-numerals on mobile. |
| T-16 | **Classical Horological Citation Over-Ornamentation** — Prepending redundant decorative headings (e.g. "Cổ thư di huấn") to traditional aphorisms | AVOID | Ornamental framing text above traditional verses | Present the original Hán-Việt text in italic, with contemporary translation on a discrete secondary row without redundant titles. |
| T-17 | **Calendar Milestone Ambiguity & Anti-Overexpression** — Displaying identical lunar and solar day numbers without milestone qualifiers, or stripping month indicators on primary lunar milestones | HARD BAN | Sóc ($1\text{st}$) or Rằm ($15\text{th}$) lunar days displayed without explicit milestone text in detail cards, or regular days showing `/tháng` in grid cells | In calendar grids, lunar month suffixes (`/tháng`) are strictly restricted to actual milestones (days 1 and 15). Detail snapshot / brief cards must avoid echoing verbose parenthetical tags (`(Mùng 1)`, `(Rằm)`) or Can Chi day suffixes when date context is already clear or accessible in dedicated full views, avoiding clutter and redundant noun echoes. |

---

## C: Color & Contrast

| ID | Pattern | Severity | Detection Signal | Fix Directive |
|----|---------|----------|-----------------|---------------|
| C-01 | **The AI Palette** — Cyan-on-dark, purple-to-blue gradients, neon accents as default | AVOID | `#7C3AED`, `#38BDF8`, `#06B6D4` as primary without brand rationale | Derive palette from product/brand, not AI statistical defaults. |
| C-02 | **Dead Grays** — Pure `#000`, `#FFF`, or `#888` without tinting | CHECK | Exact `#000000`, `#FFFFFF`, `#888888` in palette | Tint neutrals toward brand hue for visual harmony. Pure values acceptable for high-contrast accessibility needs. |
| C-03 | **Contrast Mud** — Gray text on colored backgrounds | HARD BAN | Gray text (`#666`-`#999`) on non-white/non-black backgrounds | Text on color must be a darker/lighter shade of that hue, or verified ≥ 4.5:1 contrast. |
| C-04 | **Hue Chaos** — > 1 primary + 1 neutral + 1 accent on one surface | CHECK | Count distinct hue families in visible viewport | Limit to 1 primary, 1 neutral, 1 accent unless product requires semantic colors (status, data viz). |
| C-05 | **Untinted Neutrals** — Mathematically perfect grays (`#808080`) in palette | AVOID | Neutral colors with 0 chroma in OKLCH | Tint neutrals 2-5 chroma toward brand hue for warmth/coolness consistency. |
| C-06 | **Low-Contrast Labels** — Text < 4.5:1 on background | HARD BAN | Contrast ratio < 4.5:1 for normal text | Meet WCAG AA minimum. Use contrast checker before finalizing. |
| C-07 | **Semantic Color Overload** — Success-green + warning-yellow + danger-red all visible simultaneously | CHECK | Multiple semantic colors in one viewport | Use semantic colors for actual status, not decoration. Mute or hide non-active states. |

---

## L: Layout & Space

| ID | Pattern | Severity | Detection Signal | Fix Directive |
|----|---------|----------|-----------------|---------------|
| L-01 | **Card Inception / Nested Cards** — Bordered or elevated cards nested inside another card or framed container | HARD BAN | Card container (border/shadow/bg) nested inside another card or bordered section box | Single containment layer only. Remove the outer card enclosure or flatten inner cards into unbordered rows, hairlines, or whitespace columns. |
| L-02 | **3-Column Clone Grid** — Identical 3-column feature grids repeated | AVOID | Same `grid-template-columns: repeat(3, 1fr)` pattern with identical card structure | Vary column counts, use asymmetric layouts, or switch to list format. |
| L-03 | **Arbitrary Spacing** — Non-scale padding/margin values (13px, 27px) | CHECK | Spacing values not in 4px/8px base scale | Use strict 4px or 8px base scale (4, 8, 16, 24, 32, 48). Exception: existing project scale. |
| L-04 | **Centered Everything** — All text and layouts center-aligned by default | CHECK | `text-align: center` on body/content, centered grid layouts | Left-align content-heavy pages. Center only for focused flows (landing hero, empty state, modal). |
| L-05 | **Scaffolding First** — Empty header/footer before user intent | AVOID | Generic nav + footer with empty or placeholder main content | Define user intent and primary action before building chrome. |
| L-06 | **Copy-Paste Layouts** — Same hero-metric-features template repeated | AVOID | Identical section structure with different content | Vary section layouts, density, and visual rhythm across a page. |
| L-07 | **Dense Desktop on Mobile** — Desktop layout shrunk to mobile viewport | HARD BAN | Multi-column layout at < 640px without responsive reflow | Explicit mobile layout with ≤ 2 columns, stacked navigation, and touch-appropriate targets. |
| L-08 | **Zero-Breathing Containers** — Padding < 12px on content cards | CHECK | `padding < 12px` on cards containing text | Minimum 16px padding on content cards. 12px acceptable for compact data-dense UIs. |
| L-09 | **Grid Gap Inconsistency** — Mixed gap values without rhythm | AVOID | Multiple `gap` values not in scale | Use consistent gap from spacing scale across a surface. |
| L-10 | **Overflowing Content** — Fixed-height containers clipping text | HARD BAN | `height: <px>` on text containers, `overflow: hidden` clipping labels | Use `min-height` + padding. Never clip text content. |
| L-11 | **Touch Target Crowding** — Interactive elements < 8dp apart | HARD BAN | Adjacent buttons/links with `gap < 8px` or overlapping hit areas | Minimum 8dp between touch targets. 12dp preferred for multi-button rows. |
| L-12 | **Dead End Screens** — No back/return trigger on result screens | HARD BAN | Modal/sheet/result screen without close or back control | Every screen must have an explicit escape route (back button, close, or drag-to-dismiss). |
| L-13 | **Carditis / Card Soup** — Wrapping homogeneous sibling items or metrics in individual bordered cards | AVOID | > 2 sibling cards displaying parallel data without distinct elevation or state | Remove individual card frames. Use airy whitespace, hairline separators, or tabular alignment. Reserve card containers strictly for elements requiring primary focus or elevation. |
| L-14 | **Tag-Left / Header-Right Two-Column Head** — Eyebrow or label rendered in a left column beside the heading | HARD BAN | Two-column split between eyebrow/number and section title | Single column vertical stack only (`flex-direction: column`). Eyebrow sits directly above the heading. |
| L-15 | **Wrapping Clickable Affordances** — Button or CTA text breaking across two or more lines | HARD BAN | Button, tab, or chip label wrapping on narrow viewports | Use concise copy, `white-space: nowrap`, and responsive auto-sizing. Never ship two-line action buttons. |
| L-16 | **Careless Ellipsis Truncation (Mid-Word Clipping)** — Truncating proper nouns or short data labels mid-syllable with uncalculated ellipses | HARD BAN | `numberOfLines={1}` or `text-overflow: ellipsis` slicing short proper names into stubs (e.g. `"Thanh Lo..."` for `"Thanh Long"`) | Strip redundant category prefixes, right-size typography, or allow clean wrapping. Never ship sliced mid-word stubs for essential domain entities. |
| L-17 | **Asymmetrical Multicolumn Telemetry Alignment** — Uneven column heights, mismatched baselines, or jagged widths in multi-column analytical strips | AVOID | Multi-column technical cards (e.g. 3-column Tam Sát, 12 Canh Giờ) with divergent item baselines or label widths | Enforce identical vertical baselines for primary glyphs, consistent directional prefixes, and fixed label column widths for perfect bilateral symmetry. |
| L-18 | **Warning Banner Ellipsis Truncation** — Clamping compound warning alerts with single-line limits | HARD BAN | `numberOfLines={1}` on alert or taboo banners with multiple clauses | Remove single-line clamping, allow multi-line wrapping with centered balance or vertical stacking. Critical warnings must never be cut off. |
| L-21 | **Thumb-Zone Desertion / Top-Heavy Control Placement** — Placing primary interactive triage controls, date jump steppers, or main CTAs in the top 25% of the viewport on mobile devices | AVOID | Primary interactive control situated > 60% viewport height from the bottom edge on screens > 5.5 inches | Situate primary controls in the bottom 40% natural thumb reach zone (Fitts's Law 2.0 / Law 36). Top 20% reserved strictly for orientation headers and passive telemetry. |
| L-22 | **Compound State Erasure / Anchor Obliteration** — Overwriting an immutable temporal anchor (such as "Today") when applying an interactive selection state | HARD BAN | `isSelected` completely removing or replacing the visual presence of `isToday` in date pickers or calendar grids | Selection highlight (`isSelected`) must never erase or completely obliterate the "Today" anchor (`isToday`). When today is unselected, render in a clean circle with a thin black border ($1\text{dp}$) and no background color; when any day (today or another day) is selected, render in a solid black circle with no border and white text (`textInverse`). Never introduce conflicting yellow/bronze accent borders that clash with holiday markers. |
| L-23 | **Buried Telemetry in Chronological Views** — Placing real-time status anchors (current live hour, active triage countdown, sticky filters) inside scrollable lists | AVOID | Real-time telemetry card scrolling out of view while browsing chronological tables | Dock dynamic telemetry above the `ScrollView` using `getElevationStyle('overlay')` with warm soot ink shadow diffusion and standard z-index (`zIndex.stickyHeader` or `zIndex.floatingBar`). |
| L-24 | **Monolithic Spacing Rhythm Misalignment** — Applying identical vertical spacing across contemplative reading surfaces and high-density tabular matrices | AVOID | Dead scrolling on compact mobile screens or cramped collision between sticky controls and tabular data | Contemplative paper bloc pages (`DayScreen`) cap section dividers at `spacing.lg` ($16\text{dp}$, total $52\text{dp}$ separation). Tabular schedule matrices (`GioTotScreen`, `DungSuScreen`) must provide dedicated wrapper gaps (`paddingVertical: spacing.xs/sm`) between stacked sticky controls and scrollable rows. |
| L-25 | **Sibling Analytical List Inconsistency** — Asymmetrical column widths, mismatched glyph baselines, or divergent dividers across sibling row lists | AVOID | Date rows in Dụng Sự, hour rows in Giờ Tốt, and Holiday rows in Lịch Tháng using differing column splits or alignments | Enforce standard 3-part layout: Left ($56\text{dp}$ fixed) temporal anchor in Serif semi-bold + `bodySmall` secondary; Center semantic proper noun without pill wraps; Right ($72\text{dp}$ fixed) standardized polarity score / tag or chevron, separated by vertical hairline dividers. |

---

## D: Decoration & Hierarchy

| ID | Pattern | Severity | Detection Signal | Fix Directive |
|----|---------|----------|-----------------|---------------|
| D-01 | **Signal Overload** — Border + shadow + background on same element | AVOID | Element with `border` + `box-shadow` + `background-color` all distinct | Use max 2 visual signals per hierarchy level. Prefer one: border OR shadow OR background. |
| D-02 | **Dead Backgrounds** — Flat solid color across massive desktop viewports | CHECK | Single `background-color` on `body` or full-page container with no texture | Add subtle atmosphere (grain, noise, soft gradient) for premium feel on large viewports. Acceptable for data-dense product UI. |
| D-03 | **Gratuitous Accents** — Random 4px colored borders on cards without meaning | AVOID | Decorative `border-left: 4px solid` without semantic purpose | Use accent borders only for semantic meaning (status, category, priority). |
| D-04 | **Glassmorphism Overuse** — Blur + transparency on every container | AVOID | `backdrop-filter: blur()` on > 2 elements | Reserve glassmorphism for 1-2 hero elements. Overuse destroys readability. |
| D-05 | **Neon Glow Defaults** — `box-shadow` glow on every interactive element | AVOID | Multiple elements with `box-shadow: 0 0 20px <color>` | Limit glow to primary CTA or active state. Static elements should not glow. |
| D-06 | **Thick Side-Tab Borders** — 4px+ colored border on one card side | AVOID | `border-left` or `border-right` > 3px as decoration | Use hairlines (1px) or tonal elevation for card separation. |
| D-07 | **Shadow Stacking** — Multiple conflicting shadow directions | AVOID | Elements with different `box-shadow` angles/offsets | One shadow direction per surface. Consistent elevation system. |
| D-08 | **Decorative Dots/Lines** — Status dots, dividers without information | AVOID | Colored dots or lines that don't encode state or meaning | Every visual element must convey information. Remove purely decorative separators. |
| D-09 | **Badge & Pill Proliferation (Capsule Quilt)** — Wrapping every label, date piece, metric, and chip in bordered pill containers | AVOID | > 2 non-interactive badges/pills in a single viewport fold | Reserve pills strictly for high-salience status polarity (e.g. Hoàng/Hắc Đạo) or active interactive filters. Render supporting metadata as clean typographic text. |
| D-10 | **Unmotivated Ambient Decoration** — Floating 3D orbs, mesh aurora blobs, scanlines, or floating cursors | AVOID | Floating blurred spheres, multi-color mesh blobs, or faux stickers with no semantic role | Remove ambient decorative clutter. Rely on strong typographic anchor and subtle tinted surfaces. |
| D-11 | **Dual-Segment Lens Asymmetry & Size Drift** — Divergent heights, mismatched typography, or unconstrained widths across primary 2-option view switchers | AVOID | Sibling 2-segment switchers (e.g. [ Chung | Cá nhân hóa ], [ Cơ bản | Nâng cao ]) rendering with differing heights, tab font sizes, or uncontrolled widths | Enforce Dual-Segment Lens Parity: identical height (`spacing.pillHeightMd: 32dp`), unified typography (`typography.tabLabel`), and centered max width constraint (`maxWidth: 320`). |
| D-12 / AP-08 | **Multi-Modal Redundancy & Signal Stutter (Poly-Encoding)** (cross-ref D-11) — Over-stating or repeating a single semantic polarity or attribute across 3+ simultaneous modalities (e.g. colored dot + parenthetical tag `(Cát)` + descriptive evaluation text `Tốt vừa` + icon) | HARD BAN | Status indicator dot + parenthetical polarity tag + descriptive evaluation text representing the same quality within one node | Rule of Singular Modality: Max 1 subtle visual indicator (5–6px dot) + 1 descriptive textual assessment. Strip parenthetical tags (`(Cát)`/`(Hung)`) whenever a rating phrase (`Tốt vừa`, `Rất tốt`, `Đại hung`) or dedicated description is present. Never stack `dot + (Tag) + Description`. |
| D-13 | **Phantom Depth & Shadow Chaos** — Mixing divergent shadow angles, heavy black drop-shadows on parchment canvases, or arbitrary elevation integers | AVOID | Inconsistent box-shadow directions or elevation values not mapped to 5-tier elevation scale | Enforce 5 standardized elevation tiers (`elevation.ts`) with warm soot ink diffusion (`rgba(42, 36, 33, ...)`) and tonal parchment shifts. |
| D-14 | **Singular Polarity & De-Echoed Rating Typography** — Stacking redundant category pills (e.g. `Hắc đạo` pill) alongside composite evaluation scores (`Đại hung 30%`), or placing pulsing dots on passive navigation text | HARD BAN | Pulsing indicator on passive cues (`"Đang diễn ra ›"`) OR category pill adjacent to score compound | Place a single 5–6px `PulseDot` (green/red) directly preceding the rating compound (`Đại cát 85%` / `Đại hung 30%`). Eliminate redundant category pills (`Hắc đạo`/`Hoàng đạo`). Passive navigation affordances must use neutral ink text with `›` chevron and zero pulsing. |

---

## M: Motion & Interaction

| ID | Pattern | Severity | Detection Signal | Fix Directive |
|----|---------|----------|-----------------|---------------|
| M-01 | **Cartoon Easing** — Bounce/elastic easing on UI transitions | HARD BAN | `cubic-bezier` with overshoot, `spring` with low damping on UI | Use `ease-out` for arrivals, `ease-in` for exits. No bounce on functional UI. |
| M-02 | **Layout Repaints** — Animating width/height/margin/padding | HARD BAN | `transition: width`, `transition: height`, `transition: margin` | Animate only `transform` and `opacity`. Use `scale` instead of `width`/`height`. |
| M-03 | **Static Polish Illusion** — Missing interactive states | HARD BAN | Element with only `default` state defined | Define all 8 states: default, hover, focus-visible, active, disabled, loading, empty, error. |
| M-04 | **Motion Without Meaning** — Animation on every element always | AVOID | > 3 elements animating simultaneously on page load | Animate only primary action and spatial transitions. Ambient motion is progressive enhancement. |
| M-05 | **Uninterruptible Animations** — Animations that can't be cancelled | CHECK | Animation without cancel/interrupt handler on user input | All motion must be interruptible by user gesture. |
| M-06 | **Missing Reduced Motion** — No `prefers-reduced-motion` support | HARD BAN | Animated elements without `@media (prefers-reduced-motion)` fallback | Provide opacity-only fallback when reduced motion is preferred. |
| M-07 | **State Geometry Jitter (Border-Width Shift)** — Shifting `border-width` between states (e.g. 1px to 2px on focus/hover) | HARD BAN | `border-width` declarations differing across default, hover, focus, or active states | Maintain constant 1px `border-width`. Change `border-color`, `outline`, or `box-shadow` without reflowing container geometry. |
| M-08 | **Directional Motion Inversion** — Counter-clockwise rotation or counter-intuitive directional motion on functional controls | HARD BAN | Refresh affordances rotating `['0deg', '-360deg']` or scrolling counter to intent | Functional spin and refresh feedback must strictly rotate clockwise (`['0deg', '360deg']`), utilizing Apple gold-standard spring curves without jitter. |
| M-10 | **Stacking Context Collision / Z-Index Arms Race** — Arbitrary high z-index declarations (9999, 1000) breaking drawer stacking or intercepting taps | HARD BAN | `zIndex` values not in canonical scale (`base: 0`, `card: 1`, `stickyHeader: 10`, `floatingBar: 20`, `backdrop: 50`, `drawer: 100`, `modal: 200`, `toast: 300`) | Strictly consume canonical `zIndex` tokens (`zIndex.ts`). Zero speculative z-index numbers. |


---

## W: Copy & Content

| ID | Pattern | Severity | Detection Signal | Fix Directive |
|----|---------|----------|-----------------|---------------|
| W-01 | **Redundant UX Writing** — Label + sublabel + helper all saying same thing | AVOID | Multiple text elements with semantic overlap | Say it once. Remove redundant explanations. |
| W-02 | **Filler Verbs** — "Unlock", "Elevate", "Supercharge" without substance | AVOID | Marketing buzzwords without specific meaning | Use action-oriented, specific verbs. "Create project" not "Unlock your potential". |
| W-03 | **Generic CTAs** — "Learn More", "Click Here", "Submit" | AVOID | CTA text that doesn't describe the destination or action | CTA must describe outcome: "View pricing", "Start trial", "Download report". |
| W-04 | **Fake Personalization** — "Welcome back, User" without real data | AVOID | Placeholder names or "User" in greeting | Use real data or remove personalization. Never show placeholder names. |
| W-05 | **Parenthetical Explanations** — "Feature (Explanation)" pattern | AVOID | Headings or labels with parenthetical definitions | Integrate explanation into label or remove if label is clear. |
| W-06 | **Fabricated Proof & Cliché Metrics** — Inventing quantitative claims ("10x faster", "50,000+ teams") without evidence | HARD BAN | Stat cards or proof bars with unverified numbers | Use real metrics or remove proof containers. Never fabricate statistics. |
| W-07 | **Over-Expressing & Redundant Category Prefixes (Noun-Echo)** — Prepending redundant category nouns to proper names or domain values | AVOID | Category noun immediately prepended to an entity already contextualized by the container (e.g. `"sao Thanh Long"`, `"ngày Thứ Hai"`, `"nhiệt độ 28°"`) | Strip redundant category nouns. Render the authoritative proper name or metric directly (`"Thanh Long"`, `"28°"`). Eliminates horizontal bloat and prevents ellipsis clipping. |
| W-08 | **Awkward Mid-Phrase Word Wrapping & Dangling Punctuation (Vietnamese Compound & General Punctuation Splitting)** — Slicing compound terms mid-word or leaving dangling punctuation marks (`·`, `•`, `,`, `/`, `\`, `()`, `[]`, `:`, `;`, `-`, `–`, `|`) across line wraps | HARD BAN | Line break splitting compound words (e.g. "Hỷ" on line 1, "thần" on line 2; or splitting coordinates, or orphaned delimiter dot `·` / bracket / slash at start or end of line) | Use non-breaking spaces (`\u00A0`) around all general punctuation (`\u00A0·\u00A0`, `\u00A0/\u00A0`, `\u00A0–\u00A0`, `\u00A0(`) or discrete structural rows. Line breaks must strictly follow natural clause delimiters (only immediately following `,`, `;`, or line breaks between key-value pairs). |
| W-09 | **Tautological Helper Microcopy & Empty Echoes (Obvious-Action Subtitles)** — Adding helper subtitles that merely paraphrase or narrate the self-evident title or control affordance (e.g. "Chuyển nhanh đến ngày bạn cần tra cứu" under "Chọn ngày tháng năm") | AVOID | Subtitle or helper text whose predicate paraphrases the imperative verb of the title or control without providing tangible metadata | Remove subtitle completely if the title/action is self-explanatory. Subtitles must strictly provide dynamic domain metadata (dates, locations, counts, technical qualifiers); otherwise omit. |
| W-10 | **Destination Navigation Duplication & Verbose Row Titles** — Presenting multiple distinct summary rows that navigate to the exact same sub-page, or using row titles $> 24$ characters that cause value clipping | AVOID | Multiple list items sharing identical navigation routes OR setting row title causing right-hand value to clip with ellipsis | Consolidate identical destinations into a single descriptive row. Restrict primary row titles to $\le 24$ characters so secondary selection values are fully visible without truncation. |

---

## I: Imagery & Assets

| ID | Pattern | Severity | Detection Signal | Fix Directive |
|----|---------|----------|-----------------|---------------|
| I-01 | **Div-Based Fake Screenshots** — Styled rectangles pretending to be product UI | HARD BAN | `<div>` elements styled to look like app screenshots | Use real screenshots, generated images, or actual component previews. |
| I-02 | **Stock Photo Defaults** — Generic stock photos without brand relevance | AVOID | Unsplash/Pexels photos without product context | Use product-specific imagery, illustrations, or omit. |
| I-03 | **Placeholder Assets Shipping** — "Lorem ipsum" or placeholder images in production | HARD BAN | `placeholder`, `lorem`, `temp`, `TODO` in shipped content | Replace all placeholders before shipping. |
| I-04 | **Hand-Rolled Decorative SVGs** — Custom SVGs that look amateur | CHECK | Inline SVG with poor path quality or inconsistent style | Use icon library or professional illustration. Match existing style. |
| I-05 | **Re-Drawn UI Chrome** — Hand-building browser address bars, OS traffic-light dots, or simulated device frames in code | HARD BAN | CSS/SVG mock browser frames, faux window dots, mock phone notches | Use real screenshots in `<figure>` or present borderless content directly. Do not hand-build faux OS chrome. |

---

## G: General Quality

| ID | Pattern | Severity | Detection Signal | Fix Directive |
|----|---------|----------|-----------------|---------------|
| G-01 | **No Design Contract** — Building UI without defining purpose, audience, density | AVOID | No design brief or rationale before implementation | Require design contract: screen job, primary user, primary action, required states, negative constraints. |
| G-02 | **No Finish Gate** — Declaring UI "done" without verification | AVOID | No checklist or audit before shipping | Run finish gate: purpose obvious, primary action clear, states implemented, responsive, no generic tells. |
| G-03 | **Visual Language Reuse** — UI that could belong to another product | CHECK | No product-specific visual decisions | Every surface must have ≥ 1 memorable, product-specific quality. |
| G-04 | **Missing Empty States** — Blank screen when no data | HARD BAN | No empty state component or message | Every list/grid must have a calm, actionable empty state. |
| G-05 | **Missing Error States** — No error handling UI | HARD BAN | No error state component or recovery path | Every form/action must have error state with explanation and remedy. |
| G-06 | **Missing Loading States** — Blank during async operations | HARD BAN | No skeleton or spinner during data fetch | Show skeleton/progress for any operation > 100ms. |
| G-07 | **Inaccessible Focus** — No visible focus indicator | HARD BAN | `outline: none` without alternative focus style | Visible focus ring on all interactive elements. |
| G-08 | **Form Wipe on Error** — Clearing inputs on validation failure | HARD BAN | Form reset on validation error | Preserve user input. Highlight invalid fields only. |
| G-09 | **No Keyboard Navigation** — Interactive elements not focusable | HARD BAN | Controls without `tabIndex` or semantic HTML | All interactive elements must be keyboard-accessible. |
| G-10 | **Silent Failures** — No feedback on async operations | HARD BAN | `catch {}` or missing toast/alert on error | Toast/alert for all async outcomes (success, error, timeout). |
| G-11 | **Sensory Feedback Stutter / Gratuitous Vibration** — Emitting uncalibrated haptics on passive scrolling, non-actionable reads, or using identical buzz for everything | AVOID | Vibrate calls triggered on scroll events or static card renders | Enforce 3-tier sensory tactile hierarchy (selection ticks, impact collisions, notification alerts). Zero vibration on passive reads. |
| F-05 / G-12 / AP-17 | **IME Pre-Edit Racing & Simulated State Resets** — Executing synchronous string masking/formatting while text composition is active, or restoring hardcoded mock data on form reset | HARD BAN | Character duplication (e.g. `HHàà NNội`), jumping cursor during input, or reset button filling dummy user profiles | Defer input masking until composition ends. Reset actions must strictly set form fields to empty strings/defaults, never restoring developer test profiles. |
| G-13 | **Ephemeral Cache Cascading Invalidation / Synchronous Hydration Flashing** — Invalidation listeners wiping unrelated temporal UI caches (location names, weather) on domain events, causing visual flashes or cold reloads on tab navigation | HARD BAN | Location/weather reloading or showing spinners upon switching tabs, or cache reset cascading across unrelated features | Domain event listeners (e.g. GPS resolve, setting change) must strictly invalidate calculation caches (`calendarInvalidationListeners`) without clearing unrelated temporal UI caches. Hydrate synchronously on frame 0 from persistent or in-memory caches. |
| G-14 | **Userflow Coherence & Segment Misalignment** — Deep links or action triggers navigating to generic secondary views instead of the specific destination matching user intent | AVOID | Quick links from overview surfaces (e.g. "Sổ tay Dụng sự" on Home) landing on generic filter setup rather than the date analysis tab | Deep links and cross-feature action CTAs must navigate directly to the specific destination subtab corresponding to user intent (e.g. "Xem ngày" for day evaluation), with sibling segmented tabs ordered logically. |

---

## Applicability Matrix

| Skill / Role | Consumes | Depth |
|--------------|----------|-------|
| `ui-ux-craft` | T, C, L, D, M, W, I, G | Full design contract + token/layout/color implementation |
| `animation-mastery` | M | Full spring physics, easing curves, and reduced-motion compliance |
| `ui-ux-audit` (`Role: "frontend-qc"`) | All categories | Full checklist + finish gate verification |

---

## Finish Gate (Pre-Ship Verification)

Ship only when ALL pass:

- [ ] Screen purpose is obvious within 3 seconds
- [ ] One primary action clearly leads the hierarchy
- [ ] Every visible control has a real outcome
- [ ] Content and labels belong specifically to this product
- [ ] Required states implemented: default, hover, focus, active, disabled, loading, empty, error
- [ ] Responsive behavior is intentional (mobile ≤ 2 columns, touch targets ≥ 44px)
- [ ] Existing design system rules are respected
- [ ] No HARD BAN patterns present
- [ ] AVOID patterns have explicit design rationale if used
- [ ] Accessibility: WCAG AA contrast, keyboard navigation, focus visible, reduced motion

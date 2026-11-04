# Full protocol: ui-ux-craft

Loaded on demand; see SKILL.md for triggers and core rules.

### 2. Color Science & Design Tokens (OKLCH & SLDS 3-Tier Architecture)
- **Perceptual Uniformity**: Use OKLCH color space for palette generation to ensure consistent perceptual lightness and chroma.
- **3-Tier Design Token Architecture (SLDS & W3C DTCG Standard)**:
  - *Tier 1: Global / Primitive Tokens*: Raw foundational constants (`#DFC15D`, `8px`, `16px`).
  - *Tier 2: Alias / Semantic Tokens*: Intent-driven tokens (`colors.primary`, `surface-base`, `text-secondary`, `spacing.md`).
  - *Tier 3: Component Tokens*: Component-scoped contracts (`button-primary`, `bottom-drawer`, `docked-action-bar`, `undo-toast`).
- **Zero-Contradiction Token Mandate**: Every design token (color, spring physics, spacing, radius) must have exactly **one authoritative definition** in the codebase. Code (`src/theme/`) is the single source of truth; documentation and skills must cite token names rather than ad-hoc raw values. Project-specific tokens supersede generic defaults.
- **Contrast & Theme Harmony**: Ensure WCAG AA (4.5:1 for body) and AAA (7:1 for fine text) contrast ratios in both light and dark modes. Avoid naive color inversion.

### 3. Responsive, Adaptive & Foldable Layouts (Effortless & IBM Carbon Dual Rhythm)
- **Fluid Breakpoints**: Support mobile (< 640px), tablet (640-1024px), desktop (> 1024px), and ultra-wide displays.
- **IBM Carbon Dual Spatial Rhythm (Productive vs. Expressive Mode)**:
  - *Expressive Mode*: Hero cards, contemplative zen negative space (*Ma* 36–48px), large scholar serif titles. Tailored for Layer 1 (Glance & Hook) and ritual casting.
  - *Productive Mode*: High-density scannable data, 2-column mobile telemetry grids, baseline-aligned mono coordinates, compact 1px hairlines. Tailored for Layer 3 (Deep-Dive & Mastery).
- **Foldable & Dual-Screen Ergonomics**: Adapt to foldable inner/outer aspect ratios; respect hinge safe areas and window manager split-screen bounds.
- **Dynamic Type & Character Budget Resilience**: Layouts must gracefully accommodate ≥ 200% system font scaling without clipping, overlapping, or horizontal overflow. Components with character budgets (e.g. tabs ≤ 10 characters) must provide defensive wrapping (`flexWrap: 'wrap'`), auto-scaling, or truncated tooltips rather than overflowing boundaries.
- **Thumb-Zone Reachability (Fitts's Law 2.0 & One-Handed Ergonomics)**: Place primary interactive controls, date selectors, triage filters, and critical CTAs within the bottom 40% of the mobile viewport (Natural Thumb Reach Zone). Reserve the top zone for glanceable telemetry and orientation headers. Prefer bottom sheets over centered modal dialogs on mobile.

### 4. Micro-Interactions, Motion Correctness & Friction by Design
- **Curve Correctness**: Prefer `ease-out` (`cubic-bezier(0.2, 0, 0, 1)`) for arrivals (decelerate into rest). Exits use `ease-in`. Interactive drags use spring physics (`stiffness: 300, damping: 25, mass: 1`).
- **Material 3 Shared-Axis Choreography**: Page/tab transitions follow consistent directional semantics:
  - **Shared X-Axis**: Horizontal slide for peer tabs, timeline navigation (yesterday/tomorrow), or sequential wizard steps.
  - **Shared Y-Axis**: Vertical elevation/drop for hierarchical navigation (drill-down into detail / up to parent overview).
  - **Shared Z-Axis (Scale/Fade)**: Depth transitions for bottom sheets, dialog modals, and full-screen reveals.
- **Friction by Design (Ritual & High-Stakes UX)**: In domain contexts requiring solemnity, accuracy verification, or emotional reassurance (divination, financial transfers, encryption keys, medical assessments), instantaneous 0ms calculation degrades perceived quality. Use deliberate tactile steps, resonant haptic feedback, and a calm 1.8s–2.5s breathing delay before revealing sensitive results.
- **Reduced-Motion First**: Design the static layout first. Motion is a progressive enhancement layer. Honor `@media (prefers-reduced-motion)`.

### 5. Google DESIGN.md, Bastien & Scapin & Anti-Slop Invariants (Brain Relax & Calm)
- **DESIGN.md First**: Always check for root `DESIGN.md` (Google/W3C DTCG Token Contract) before generating or editing UI.
- **Bastien & Scapin (INRIA) Ergonomic & NN/g Heuristic #8 Enforcement**:
  - *Guidance (Guidage)*: Action-oriented scholar verbs; clear semantic distinction between Auspicious and Inauspicious states.
  - *Workload Concision (Charge de travail)*: Banned redundant section subtitles; single-channel compound indicators (`★ Giờ Vàng · 70%`); disciplined pill budget ($\le 2$ per card).
  - *Explicit Control (Contrôle explicite)*: On-demand casting calculations; connected non-trapping flows with explicit Back/Return triggers.
  - *Error Management (Gestion des erreurs)*: Input format constraints before submission; zero-wipe form retention; 5-second non-destructive undo toast.
- **Law of Icon Frugality & NN/g Icon Usability**:
  - Max 1 functional icon per interactive element (CTA/Button).
  - 0 icons on pure telemetry/metric cards when typography already defines the label.
  - CẤM 100% Emoji as UI icons. Use Vector SVGs with explicit 16-20dp bounding boxes.
  - CẤM Icon-Noun Redundancy (never place a pin icon next to "Location" or calendar icon next to "Date").
- **Google PAIR Explainability & Calibrated Confidence (Anti-Fake-Precision)**:
  - **Zero Fake Decimal Precision**: In heuristic or estimation domains, never display decimals in scores/percentages (e.g. "84.37% Cát", "91.2% Hoàng Đạo"). Round to 5% or 10% integer buckets, or qualitative semantic tiers (Đại Cát / Thứ Cát).
  - **Causal Attribution Anchors**: Every algorithmic recommendation or composite score must provide a causal explanation anchor ("Vì sao có kết quả này?"), explicitly citing the underlying contributing rules or factors.
- **Law of Viewport Density & Breathing Room**:
  - Telemetry grids on mobile viewports (≤ 412dp) must use a maximum of **2 columns**.
  - Minimum card padding ≥ 16dp, grid gap ≥ 12dp. Zero nested box-in-a-box caging.
- **Law of Vietnamese Diacritics & Defensive Flexbox**:
  - Body/Reading text: `lineHeight ≥ 1.45×` font-size.
  - Display/Headline text: `lineHeight ≥ 1.25×` font-size.
  - Technical/Mono labels: `lineHeight ≥ 1.20×` font-size.
  - Zero fixed-height on text containers. Use `minHeight` + `paddingVertical`.
  - All chip/badge/tag groups must declare `flexWrap: 'wrap'` and `gap: 8`.
- **Golden Metric Ratio (2:1)**:
  - Quantitative metrics (e.g. `28°C`, `83%`) must render numerals ≈ 2× the size of unit labels and baseline-aligned (`alignItems: 'baseline'`).
- **4-Tier Latency Feedback Matrix (Tognazzini / IxD Standard)**:
  - `< 100ms`: Visual feedback only (immediate press/active state change); no spinner or skeleton needed.
  - `100ms – 1.0s`: Inline skeleton loader or contextual spinner; never leave the container blank.
  - `1.0s – 10.0s`: Determinate progress indicator or step checklist with percentage / estimated time.
  - `> 10.0s`: Move to asynchronous background processing; notify user with push or in-app toast on completion.
- **Law of Protecting User Work (Zero-Wipe & State Continuity)**:
  - Never clear or reset form fields upon validation failure; highlight invalid fields while preserving entered inputs.
  - Auto-save drafts and user selections continuously across session reloads.
  - Destructive actions (delete, wipe) require confirmation or a non-destructive undo window (≥ 5s).

### 6. Apple HIG, Google M3 & Cross-Platform Ergonomics Matrix
- **Principle of Deference (Content is the Hero)**:
  - UI chrome (bars, tabs, borders) must visually recede to let spiritual and astronomical content shine.
  - Avoid heavy card frames, excessive dividers, or loud navigation bars. Use subtle 1px hairlines (`rgba(255, 255, 255, 0.08)`) and tonal elevation.
- **Cross-Platform Touch & Spatial Ergonomics Matrix (Apple HIG, Google M3, WCAG 2.2)**:
  - *Apple HIG Minimum Touch Target*: $\ge 44 \times 44\text{pt}$ (iOS).
  - *Google Material Design 3 Floor*: $\ge 48 \times 48\text{dp}$ (Android).
  - *Universal Comfort Target*: $\ge 48 \times 48\text{dp}$ across mobile platforms.
  - *WCAG 2.2 Criterion 2.5.8 Baseline*: $\ge 24 \times 24\text{px}$ on web with spacing buffer; recommended $\ge 44\text{px}$ (AAA).
  - *Adjacent Button Separation*: $\ge 8\text{dp}$ general separation; multi-button rows maintain $\ge 12\text{dp}$ gap (ideally $16\text{dp}$).
  - *Safe Area & Home Indicator Buffer*: $\ge 34\text{pt}$ iOS Home Indicator clearance; $\ge 20\text{dp}$ Android gesture bar buffer.
- **Sensory Tactile Hierarchy (Calibrated Haptics)**:
  - **Selection Haptics**: Ultra-light crisp tick (`selection`) for picker wheel columns, tab switching, and segmented buttons.
  - **Impact Haptics**: Mechanical physical collisions — `impact.light` for drawer detent snap; `impact.medium` for ritual actions (casting Yao line, turning tarot card); `impact.heavy` reserved for major milestone reveals.
  - **Notification Haptics**: Rhythmic feedback for task conclusions (`notification.success`) or astrological conflict warnings (`notification.warning`). CẤM generic random vibrations.
- **Home Indicator & Safe Area Exclusion Zone**:
  - Interactive controls must NEVER hug the screen floor. Always apply `paddingBottom: insets.bottom + 12` (minimum ≥ 34pt on iOS / ≥ 20dp on Android gesture navigation) to prevent mis-swipes against the system Home Indicator.
- **Sheet Detents & Non-Destructive Undo (The 5-Item Threshold - Law 35)**:
  - Bottom sheets support fluid detents (`sheetDetents.medium: 0.52` for quick action/triage, `sheetDetents.large: 0.90` for full academic deep-dive).
  - Repetitive datasets $> 5$ items (12 Thời Thần, 28 Tú, 30+ Dụng Sự, 8 Cung Bát Trạch) MUST be offloaded to a Bottom Drawer Card rather than stretching primary screens.
  - Never interrupt user flow with blocking "Are you sure?" dialogs for routine operations. For destructive actions, present an anchored Action Sheet with semantic crimson accent, paired with an immediate 5-second Undo Toast bar.


---
## UI Quality Checklist
- [ ] Root `DESIGN.md` checked and followed (**Google DESIGN.md Spec**).
- [ ] Semantic tokens used throughout; zero hardcoded raw hex colors (**Design Tokens**).
- [ ] Icon Budget satisfied: ≤ 1 icon per CTA, 0 emoji icons, no icon-noun redundancy (**Icon Frugality**).
- [ ] Density limits respected: max 2 columns on mobile, padding ≥ 16dp (**Viewport Density**).
- [ ] Vietnamese diacritic line-height floor (≥ 1.45× body, ≥ 1.25× display) and no fixed-height text boxes (**Diacritic Safety**).
- [ ] Thumb-Zone Reachability: Primary actions and date controls situated in bottom 40% reach zone (**Fitts's Law 2.0**).
- [ ] Calibrated Confidence & Explainability: Zero fake decimal precision (`/\d+\.\d+%/`), causal attribution provided (**PAIR Explainability**).
- [ ] Dynamic Type Resilient: Survives ≥ 200% font scaling with flexWrap and minHeight (**Accessibility**).
- [ ] Apple Deference & Minimal Chrome: UI chrome recedes behind hero content, zero thick box cages (**Apple HIG Deference**).
- [ ] Sensory Tactile Hierarchy: 3-tier calibrated haptics (Selection for wheels/tabs, Impact for ritual collisions, Notification for outcomes) (**Apple Haptics**).
- [ ] Home Indicator Exclusion: Docked buttons maintain ≥ 34pt iOS / ≥ 20dp Android bottom safe buffer (**Safe Area**).
- [ ] Non-Destructive Undo: 5-second undo toast provided for reversible actions; no anxious confirmation spam (**Apple HIG Undo**).
- [ ] Latency Feedback matrix respected: press states < 100ms, skeletons for 100ms-1s, progress for > 1s (**Latency Tiers**).
- [ ] User work protected: no form wiping on error, auto-save state, undo for destructive actions (**Protect User Work**).
- [ ] All 8 states defined: `default`, `hover`, `focus-visible`, `active`, `disabled`, `loading`, `empty`, `error` (**Variants & States**).
- [ ] Empty states have clear explanation + next action CTA (**Zero Hesitation**).
- [ ] First-run / onboarding flow exists for new users (**Effortless**).
- [ ] Skeletons/indicators displayed during async data loading (**Feels Instant**).
- [ ] Cumulative Layout Shift (CLS) verified at 0 (**Calm & Trust**).
- [ ] Touch target bounds ≥ 48 × 48dp (Android M3) / ≥ 44 × 44dp (iOS/Web).
- [ ] Adjacent interactive elements separated by ≥ 8dp to prevent accidental mis-taps (**Atomic Tap Spacing**).
- [ ] Zero Dead-Ends & Connected Navigation: Every computed/result screen, modal, or sheet drawer has an intuitive, immediately visible escape route / back button (`‹`, origin label) at the top of the viewport (**Law 31**).
- [ ] Above-the-Fold Action Reachability: Primary action buttons (re-calculate/re-run) and mode selectors sit within the initial viewport fold (≤ 240dp from top or docked in thumb zone), never below tall content cards (**Law 32**).
- [ ] Compact Icon Triggers over Text Bloat: Auxiliary options, settings, and modal pickers adjacent to primary CTAs use circular/pill icon buttons (≥ 44×44dp touch target with vector/phosphor icon), never clunky text with dropdown arrows (**Law 33**).
- [ ] Bilateral Visual Symmetry: Horizontal toolbars, headers, and action rows enforce strict bilateral visual balance across the central vertical axis (**Law 34**).
- [ ] Button Breathability & Spacing Floor: Multi-button rows maintain gap ≥ 12dp (ideally 16dp spacing.md); touch targets ≥ 44dp iOS / ≥ 48dp Android.
- [ ] Multi-Level Navigation Token Adherence: Level 1 tabs use tab-level-1-underline (2.5px, transparent container, zero border); Level 2 tabs strictly use canonical tab-level-2-pill tokens (PillTab, full pill geometry, transparent container, border-free, active-only warm gold fill `rgba(223, 193, 93, 0.18)`). Never use custom boxed stepper rows or container backgrounds.
- [ ] 5-Item Threshold & Canonical Drawer Offloading: Repetitive or canonical datasets > 5 items (12 hours, 28 stars, 30+ affairs) are never inlined on the primary canvas. Curate ≤ 3-5 highlights for Layer 2; offload full ledgers to a Bottom Drawer Card (detents: 0.52 / 0.90) or dedicated Sub-Page tab (**Law 35**).
- [ ] No Modal Inception: Never open a modal over an existing active modal; use in-place transitions (**Userflow Ergonomics**).
- [ ] Zero Redundant Section Subtitles: Section headers stand authoritative with Eyebrow + Title alone (**Anti-Slop Cleanliness**).
- [ ] Clean Compound String Wrapping: Strings with dividers (`·`, `*`, `()`, `-`, `&`) break at divider (`\n`), never mid-phrase in 2nd clause (**Law 24**).
- [ ] Screen reader affordances (`aria-label`, semantic landmarks, proper heading hierarchy).

# Cherry-picked from: emilkowalski/skills @ 2026-08-30, Google DESIGN.md Spec @ 2026-09-01, DESIGN.md Audit @ 2026-09-02, rastian/interaction-design-skills @ 2026-09-02, Google PAIR & M3 Ergonomics @ 2026-09-05, Apple Human Interface Guidelines (HIG) @ 2026-09-05, Bastien & Scapin INRIA Criteria & NN/g Usability Heuristics @ 2026-09-05, IBM Carbon Dual Spatial Rhythm & SLDS 3-Tier Tokens @ 2026-09-05, W3C DTCG & WCAG 2.2 @ 2026-09-05

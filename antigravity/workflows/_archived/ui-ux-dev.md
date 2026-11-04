---
name: ui-ux-dev
summary: Authoritative 6-phase UI/UX Engineering Lifecycle spanning Request Enrichment, User Flow Architecture, Wireframing, Pre-UI Anti-Slop Audit, Craft Implementation, and Post-UI QC Verification.
---

# UI/UX Development Lifecycle (6-Phase Workflow)

## Purpose
Govern the end-to-end design and engineering of user interfaces, screen architectures, interaction funnels, and visual components. Guarantees that temporal user flows, state completeness, cognitive pacing, and ergonomic line budgets are formalized **BEFORE** touching JSX, component layouts, or design tokens.

## The 6-Phase Execution Sequence

```
1. Request Enrichment ──> 2. User Flow & Contract ──> 3. Wireframe & Budget ──> 4. Pre-UI Audit ──> 5. Craft Build ──> 6. QC & Verification
```

---

### Phase 1: Request Enrichment & JTBD Framing
- **Goal:** Extract core functional intent, emotional tone, and physical context before any architectural or visual assumptions are made.
- **Actions:**
  1. Parse the user request to isolate the primary **Job-to-be-Done (JTBD)** ("What progress is the user trying to make?").
  2. De-risk ambiguous terminology (e.g., "redesign", "clean up", "modernize"). Clarify scope boundaries explicitly.
  3. Calibrate user motivation level $M$ (Fogg Behavior Model $B = MAP$) and physical context of use:
     - *Calm / Contemplative / Ritual*: Requires friction by design, sacred pacing, serene negative space (*Ma*).
     - *On-the-go / High Velocity*: Requires glanceable Layer 1 telemetry, large touch hitboxes, immediate triage.
     - *Productive / High Density*: Requires 2:1 golden metric typography, 2-column mobile limits, mono coordinates.
  4. Identify target device endpoints: Mobile touch, tablet, responsive desktop web, or embedded surfaces.
- **Skills:** `request-enrichment`, `requirement-interviewer`.
- **Exit Gate:** Validated Request Enrichment Brief with explicit in-scope and out-of-scope bounds.

---

### Phase 2: User Flow Architecture & State Modeling
- **Goal:** Design the continuous temporal sequence of interactions, decisions, and system responses before opening any `.tsx` or styling files.
- **Actions:**
  1. Invoke the **`userflow-architecture`** skill.
  2. Map the interaction into the **3-Layer Cognitive Model**:
     - *Layer 1: Glance & Hook (< 3s)*: Maximum 1–3 focal points. Immediate answer to the primary question.
     - *Layer 2: Action & Triage (< 30s)*: High-leverage decision tools, Top 3 priority items, segmented level-2 pill tabs.
     - *Layer 3: Deep-Dive & Mastery (On-Demand)*: Comprehensive technical ledgers, strictly located in Sub-Pages or Bottom Drawers (`expandOnScroll`, `collapseOnScrollTop`).
  3. Model the **5 Operational States** for every flow node:
     - *State 1: Ideal Path (Happy Path)*
     - *State 2: Alternative Paths (Branching)*
     - *State 3: Error & Recovery States (Inline, zero-wipe)*
     - *State 4: Interruption & Resumption (Session persistence, background rehydration)*
     - *State 5: Terminal & Emergency Exit (Unambiguous receipt, visible return trigger `‹`)*
  4. Guarantee Non-Destructive Reversibility (NN/g Heuristic #3) and Information Scent (Pirolli & Card).
- **Skills:** `userflow-architecture`.
- **Exit Gate:** Emitted and approved **Flow Contract Handover Specification** (Section 3).

---

### Phase 3: Wireframing & Component Topology Budgeting
- **Goal:** Ground spatial hierarchy, single-gutter layouts, and enforce component line budgets **upfront** to prevent the cascading refactor trap.
- **Actions:**
  1. Produce an ASCII / structural wireframe illustrating visual balance, bilateral symmetry, and element positioning.
  2. Enforce **Cardless-First Architecture**: Content streams directly on the canvas with single gutter (`spacing.gutter: 20-24dp`) and 1px hairlines (`rgba(255, 255, 255, 0.08)`). Zero nested box-in-a-box panel caging.
  3. Partition the component tree and assign strict file line-budget targets:
     - *Screen Container (`*Screen.tsx`)*: Target $\le 200$ lines (CI hard ceiling $\le 220$). Holds state selectors, safe areas, routing.
     - *Primary Organism / Card (`*Card.tsx`)*: Target $\le 250$ lines (CI hard ceiling $\le 275$). Holds Layer 1 hook and primary CTA.
     - *Sub-Components (`organisms/sub/*`)*: Target $\le 200$ lines each. Holds segmented tabs, tables, or visuals.
     - *On-Demand Drawer (`*Drawer.tsx`)*: Target $\le 250$ lines. Holds Layer 3 on-demand ledger.
  4. Map touch targets: Apple HIG $\ge 44 \times 44$pt, Android M3 $\ge 48 \times 48$dp, adjacent button gap $\ge 8$dp (ideally $12$–$16$dp).
  5. Enforce Thumb-Zone reachability: Primary actions within bottom 40% viewport or top fold $\le 240$dp.
- **Skills:** `design-brief`, `brand-guidelines`.
- **Exit Gate:** Structural Wireframe and Component Topology Plan with assigned line budgets.

---

### Phase 4: Pre-UI Forensic Audit (Annoyance, Disruption & AI Slop Gate)
- **Goal:** Audit the wireframe and flow contract against the 8 Battlefield Anti-Patterns **BEFORE** writing a single line of component code.
- **Checklist:**
  - [ ] **Unbroken Flow Check:** No action button or foreign component inserted between segmented tabs and their active content card (Law 32).
  - [ ] **State Preservation Check:** Browsing auxiliary, calendar, or future list items DOES NOT mutate or hijack the active workstation state (Law 21). Auxiliary details open non-destructively in Bottom Drawers.
  - [ ] **Connected Navigation Check:** Every computed result or detail state provides an explicit, reachable, prominent Back trigger (`‹`, `radii.full`) in the upper fold (Law 31). Zero dead-end screens.
  - [ ] **On-Demand Calculation Check:** No premature computation or fake verdict badges prior to explicit user invocation (Law 26).
  - [ ] **Single Authoritative Scent:** Zero duplicate links or conflicting triggers doing the same thing across header, body, and footer (Law 11).
  - [ ] **Zero Box Caging:** Zero nested `Surface variant="panel"` or card-in-a-card caging (Law 7 & 23).
  - [ ] **Above-the-Fold Reachability:** Primary CTA lives $\le 240$dp from top or docked in the thumb zone; never buried below tall illustrations ($\ge 300$dp) (Law 32).
  - [ ] **Calibrated Friction:** Sacred or high-stakes workflows incorporate deliberate tactile friction (2.0s–2.5s ritual animation, haptic pulses) rather than cheap 0ms computation.
  - [ ] **Anti-Slop Cleanliness:** Zero icon-noun redundancy (no calendar icon next to "Date"), zero screaming ALL-CAPS titles, zero `▾` text dropdowns, zero emojis as UI icons.
- **Skills:** `userflow-architecture`, `critique`.
- **Exit Gate:** Pre-UI Forensic Audit Pass.

---

### Phase 5: Craft Implementation & Token Grounding
- **Goal:** Build the interface with ruthless precision, zero frame drops, strict typing, and 100% design token compliance.
- **Actions:**
  1. Implement components strictly adhering to the assigned Component Topology from Phase 3.
  2. Ground 100% of styles in semantic design tokens (Google/W3C DTCG `DESIGN.md`):
     - *Colors*: 60-30-10 palette (Midnight foundation `#0B0E14`, Aged parchment `#E1E2EB`, Imperial gold accent `#DFC15D`). Zero raw `#hex` leaks.
     - *Typography*: Classical Scholar's Serif for titles, crisp Sans-Serif for controls, Data-Mono for telemetry. Enforce Vietnamese diacritic line-height floors ($\ge 1.45\times$ body, $\ge 1.25\times$ display).
     - *Spacing*: Canonical tokens (`spacing.gutter: 20-24dp`, `spacing.zenSection: 40dp`).
  3. Implement native driver motion: `useNativeDriver: true`, `motion.tabGlide` or `motion.spring.snappy`, zero cartoonish bounce (overshoot = 0%).
  4. Ensure defensive flexbox: `minHeight` instead of fixed `height` on text containers; `flexWrap: 'wrap'` on chip groups; adaptive scaling up to 200% font size without clipping.
- **Skills:** `ui-ux-craft`, `frontend-design`, `animation-mastery`.
- **Exit Gate:** Clean, type-safe implementation matching the Flow Contract.

---

### Phase 6: Post-UI QC, Accessibility & Visual Verification
- **Goal:** Verify deterministic behavior, accessibility compliance, visual stability, and hardware execution.
- **Actions:**
  1. Run automated anti-slop regression test suite:
     ```bash
     npx vitest run test/theme/uiUxAntiSlop.test.ts
     ```
  2. Run targeted component test suites (`@testing-library/react-native`):
     ```bash
     npx vitest run <path_to_component_test>
     ```
  3. Validate TypeScript strictness with 0 errors:
     ```bash
     npm run typecheck
     ```
  4. Verify hard line-budget compliance: Screen files $\le 220$ lines, Component files $\le 275$ lines.
  5. Verify live device/emulator rendering: Confirm 0ms tab switching, no layout shifts (CLS=0), light/dark mode contrast parity, and safe area clearance.
- **Skills:** `ui-ux-audit`, `frontend-qc`, `e2e_testing`.
- **Exit Gate:** 100% Green Test Evidence and Final Walkthrough Artifact.

# Full protocol: animation-mastery

Loaded on demand; see SKILL.md for triggers and core rules.

## 2. Curve Correctness & Easing Defaults

- **Entrances / Arrivals**: Prefer `ease-out` (`cubic-bezier(0.2, 0, 0, 1)` or custom strong curve) — elements decelerate into rest. Never `ease-in` on UI entry.
- **Exits / Departures**: Prefer `ease-in` or fast `ease-out` — elements accelerate away.
- **State Toggles**: Use `ease-in-out` for symmetric transitions (accordions, tabs).
- **Gestures & Drags**: Use spring physics (`stiffness: 300, damping: 25, mass: 1`).
- **Project Token Precedence**: When a project defines dedicated motion tokens (e.g. `src/theme/motion.ts`), project-calibrated tokens (`motion.tabGlide`, `motion.sheetDetentSnap`, `motion.spring.snappy`, `motion.durations.drawerSlide`) strictly supersede the generic defaults listed here. Always reference token names rather than raw numbers.
- **Physical Scale**: Never scale from `0`. Scale from `0.92–0.97` + opacity. Set `transform-origin` to the trigger element.
- **Anti-patterns**: Avoid `linear` on UI. Avoid bounce/elastic (feels dated, breaks Calm & Trust).


---
## 3. Duration Guidelines (Feels Instant Invariant)

- **Micro-feedback** (button click, toggle switch): **100–180ms** — instant acknowledgment.
- **Hover & Tooltip**: **150–250ms**.
- **Sheet / Dialog / Drawer**: **250–350ms**.
- **Page choreography / Stagger**: **300–600ms** total (child stagger: 30–50ms).
- *Rule*: If the user consciously waits for motion to finish before acting, the duration is too long.

## 4. State Transitions & GPU Performance

- **Animate `transform` and `opacity` only**. Never animate `width`, `height`, `top`, `left`, `margin`, `padding` (triggers layout/paint).
- **Tool selection**: CSS transitions for hover/state classes; CSS `@starting-style` for mount transitions; CSS keyframes for background load; Web Animations API (WAAPI) for programmatic; `motion` (`motion.dev`) for springs/drags.
- **Document state transitions**:
  `default → hover`: `transform 150ms ease-out, opacity 150ms ease-out`
  `default → disabled`: `opacity 200ms ease-out (0.4)`
  `loading → success`: `scale 250ms spring(300, 25, 1)`

## 5. Accessibility & Apple Spatial Design

- **Reduced Motion**: `@media (prefers-reduced-motion: reduce)` must soften motion to simple opacity/color cross-fades — never jarring jumps.
- **Hover Gating**: Gate hover effects behind `@media (hover: hover) and (pointer: fine)` to avoid sticky mobile states.
- **Spatial Continuity**: Contextual transitions indicate where an element originated.

## 6. Asymmetric In/Out Invariant (Enter > Exit)

- **Entrance Durations**: Must be **30–50% longer** than exit durations.
  - Users require time and spatial context to orient to newly presented UI content.
  - Users want dismissals, cancellations, and closes to feel instant and friction-free.
- **Formula**: `Exit_Duration ≈ 0.60–0.65 × Entrance_Duration`.
- **Examples**:
  - Modal Enter: `300ms–350ms` (ease-out deceleration) ──> Modal Exit: `180ms–220ms` (fast ease-in acceleration).
  - Drawer Slide-in: `350ms` ──> Drawer Slide-out: `200ms–220ms`.

## 7. Distance-Scaled Duration Formula

Scale transition duration by pixel travel distance so small badge shifts do not drag and full-screen transitions do not snap jarringly:
- **Base Distance (≤ 100px)**: $1.0\times$ base duration (e.g. 200ms).
- **Medium Distance (200px)**: $1.3\times$ base duration (e.g. 260ms).
- **Large Distance (≥ 400px / Full Screen)**: $1.6\times$ base duration (e.g. 320ms).

## 8. The 3 Motion Layers (Choreography Taxonomy)

Every rich, believable UI motion scene coordinates across three distinct layers (flat animation = missing layers):
1. **Primary Layer**: The hero action the user tracks (modal container expanding, card entering viewport).
2. **Secondary Layer**: Accompanying physical reactions (tonal shadow spreading, icon subtly orienting, border hairline fading in).
3. **Ambient Layer**: Resting rhythm that signals system liveness (gentle gradient breath, subtle pulse, celestial glow).

## 9. Apple HIG Gesture-Driven Motion & Fluid Interruptibility

- **Interactive Gesture Tracking**: Dragging or swiping (e.g. dismissing a sheet, panning a carousel) must link 1:1 with user touch coordinates without artificial lag or easing during the gesture.
- **Fluid Interruptibility**: A gesture or spring transition must be 100% interruptible mid-flight. If a user touches a closing drawer or an opening card while it is still animating, the animation must smoothly retarget from its current instantaneous velocity rather than snapping to state 0 or state 1.
- **Sheet Detent Snapping**: When dragging a modal bottom sheet between fractional detents (e.g. 50% medium vs 90% large):
  - Pass gesture velocity to the spring solver (`useNativeDriver: true` or Reanimated `withSpring`).
  - Play an ultra-light `Impact.Light` haptic pulse precisely at the detent threshold transition.

# Cherry-picked from: emilkowalski/skills @ 2026-08-30, LottieFiles motion-design-skill @ 2026-09-02, Apple Human Interface Guidelines (HIG) Motion & Gestures @ 2026-09-05

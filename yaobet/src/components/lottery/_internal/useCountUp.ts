/* ============================================================================
 * useCountUp — a ONE-SHOT tween from 0 to a KNOWN, already-settled figure.
 *
 * Deliberately NOT the ui/Odometer: Odometer is the live-jackpot primitive and
 * is type-gated to a server-bound LiveMoney it must never extrapolate past.
 * This one animates a value that is already final and local (the prize on a
 * card whose outcome was fixed before the first panel was touched), so there is
 * nothing to fabricate — it starts at 0, decelerates INTO the target, stops.
 *
 * `active=false` or reduced-motion → the target, immediately, no tween (the
 * posture: the truthful figure is shown, the movement is absent).
 * The non-animating answer is DERIVED, not written back through an effect, so
 * there is no cascading-render path at all.
 * ==========================================================================*/

"use client";

import { useEffect, useState } from "react";

/** ms — JS-side only; the CSS motion contract owns the --dur-* tokens. */
const COUNT_MS = 900;

export function useCountUp(target: number, active: boolean, reduced: boolean): number {
  const [tween, setTween] = useState(0);

  useEffect(() => {
    if (!active || reduced) return; // nothing to run — the value is derived below
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / COUNT_MS);
      const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic — decelerates in
      // setState from inside the rAF callback, never from the effect body
      setTween(t < 1 ? Math.round(target * eased) : target);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, active, reduced]);

  // reduced motion / inactive → the truthful figure straight away, no movement.
  // Clamped so a stale tween can never read above the real total.
  return active && !reduced ? Math.min(tween, target) : target;
}

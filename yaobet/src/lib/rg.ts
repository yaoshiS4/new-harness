/* ============================================================================
 * Yaobet — lib/rg : RG helpers (lib/rg/)
 * ----------------------------------------------------------------------------
 * The reduced-motion hook + equal-salience win/loss helper. These centralise
 * the motion/salience posture so components don't each re-derive it.
 * ==========================================================================*/

"use client";

import { useEffect, useState } from "react";

/** Subscribes to prefers-reduced-motion. SSR-safe: false until mounted. */
export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const onChange = () => setReduced(mq.matches);
    onChange();
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  return reduced;
}

/** The win/loss CSS var for an outcome. Equal salience — NEVER dims loss,
 *  NEVER uses red as anything but loss/error. Returns a var(--…) reference. */
export function outcomeColorVar(amount: number): string {
  return amount >= 0 ? "var(--win)" : "var(--loss)";
}

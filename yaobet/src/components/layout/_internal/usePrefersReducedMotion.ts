/* ============================================================================
 * usePrefersReducedMotion — SSR-safe hook reading the OS reduced-motion pref.
 * Returns false on the server / first paint, then syncs to the media query.
 * Shell-local until the shared lib/rg hook is wired into ui/*.
 * ==========================================================================*/

"use client";

import { useEffect, useState } from "react";

export function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);
  return reduced;
}

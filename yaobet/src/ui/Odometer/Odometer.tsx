/* ============================================================================
 * Odometer — number reel. The structural fabricated-number guard:
 * it MOUNTS ONLY on a real, server-bound `LiveMoney` value, and it runs a
 * ONE-SHOT tween toward that value and STOPS there. It NEVER extrapolates past
 * the last server figure (no "probable current" interpolation, no continued
 * climbing) — an Odometer animating past its last server value is a
 * fabricated number.
 *
 * reduced-motion → static final figure, no reel. A stale value (past its
 * freshness window) defers to MoneyValue's "tạm dừng" rather than reeling.
 * ==========================================================================*/

"use client";

import { useEffect, useRef, useState } from "react";
import { formatVnd, isStale } from "@/lib/format";
import { usePrefersReducedMotion } from "@/lib/rg";
import type { LiveMoney } from "@/lib/types";
import { MoneyValue } from "../MoneyValue/MoneyValue";

export interface OdometerProps {
  /** REQUIRED LiveMoney — the type system gates this to a server-issued value */
  value: LiveMoney;
  /** server-declared freshness window; past it → stale, not reeling */
  freshnessMs?: number;
  size?: "num" | "num-lg";
  className?: string;
}

export function Odometer({ value, freshnessMs, size = "num-lg", className }: OdometerProps) {
  const reduced = usePrefersReducedMotion();
  const target = value.amount;
  const prevTarget = useRef(target);
  // `display` is null except while a tween is in flight; at rest we render the
  // exact server target (never an interpolated/extrapolated figure).
  const [display, setDisplay] = useState<number | null>(null);
  const raf = useRef<number | null>(null);

  const stale = freshnessMs != null && isStale(value.sourcedAt, freshnessMs);
  const animatable = !reduced && !stale;

  useEffect(() => {
    // No animation path: pin to the server value, no reel (reduced/stale).
    if (!animatable) {
      prevTarget.current = target;
      return;
    }
    const from = prevTarget.current;
    const to = target;
    if (from === to) return; // already at the server value — nothing to reel

    // One-shot tween toward the server value. STOPS at it; never overshoots,
    // never continues past the last server figure.
    const start = performance.now();
    const dur = 700;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - t, 3); // easeOutCubic — decelerates INTO target
      if (t < 1) {
        setDisplay(Math.round(from + (to - from) * eased));
        raf.current = requestAnimationFrame(tick);
      } else {
        setDisplay(null); // settle: render the exact server target
        prevTarget.current = to;
      }
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current != null) cancelAnimationFrame(raf.current);
    };
  }, [target, animatable]);

  // Stale: hand off to MoneyValue's explicit "tạm dừng" (never reel a stale #).
  if (stale) {
    return <MoneyValue value={value} kind="balance" size={size} freshnessMs={freshnessMs} className={className} />;
  }

  // At rest, display === null → render the exact server target.
  const shown = display ?? target;

  return (
    <span
      className={["ui-odometer", `ui-odometer-${size}`, className].filter(Boolean).join(" ")}
      data-truthful="true"
      aria-label={formatVnd(target)}
    >
      {formatVnd(shown)}
    </span>
  );
}

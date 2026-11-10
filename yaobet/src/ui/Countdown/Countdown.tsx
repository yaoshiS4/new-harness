/* ============================================================================
 * Countdown — truthful, server-deadline-bound timer. It
 * counts toward a real server `endsAt` and HALTS at the boundary: at the
 * deadline it resolves to its real next-state ("Đã kết thúc" or a server-issued
 * label) and STOPS — it does NOT cross zero, count negative, loop, or reset.
 * A countdown ticking past its deadline is a fabricated number.
 *
 * reduced-motion → static remaining/next-state text, not a per-second tick.
 * Renders against the server clock value passed in; it does not invent time.
 * ==========================================================================*/

"use client";

import { useEffect, useRef, useState } from "react";
import { usePrefersReducedMotion } from "@/lib/rg";

export interface CountdownProps {
  /** real server ISO deadline (Deadline envelope's deadlineAt) */
  endsAt: string;
  /** text shown at/after the deadline — the real next-state, never a reset */
  zeroLabel?: string;
  /** optional callback when the deadline is reached */
  onZeroState?: () => void;
  className?: string;
}

function segments(msRemaining: number) {
  const total = Math.max(0, Math.floor(msRemaining / 1000));
  const days = Math.floor(total / 86400);
  const hours = Math.floor((total % 86400) / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const seconds = total % 60;
  return { days, hours, minutes, seconds };
}

const pad = (n: number) => n.toString().padStart(2, "0");

export function Countdown({
  endsAt,
  zeroLabel = "Đã kết thúc",
  onZeroState,
  className,
}: CountdownProps) {
  const reduced = usePrefersReducedMotion();
  const deadline = new Date(endsAt).getTime();
  const [now, setNow] = useState(() => Date.now());

  // keep the latest callback without making it a tick-effect dependency
  const zeroCb = useRef(onZeroState);
  useEffect(() => {
    zeroCb.current = onZeroState;
  }, [onZeroState]);

  useEffect(() => {
    // At/after deadline: HALT — fire once, never schedule another tick.
    if (Date.now() >= deadline) {
      zeroCb.current?.();
      return;
    }
    // Reduced-motion: no per-second visible tick. Re-evaluate at the deadline
    // only (single timeout), so the static text flips to the next-state once.
    if (reduced) {
      const id = setTimeout(() => {
        setNow(Date.now());
        zeroCb.current?.();
      }, deadline - Date.now());
      return () => clearTimeout(id);
    }
    // Motion path: tick once per second, but STOP at the deadline.
    const id = setInterval(() => {
      const t = Date.now();
      setNow(t);
      if (t >= deadline) {
        clearInterval(id);
        zeroCb.current?.();
      }
    }, 1000);
    return () => clearInterval(id);
  }, [deadline, reduced]);

  const remaining = deadline - now;

  // HALTED — real next-state, no negative count, no loop/reset.
  if (remaining <= 0) {
    return (
      <span className={["ui-countdown", "ui-countdown-ended", className].filter(Boolean).join(" ")} data-ended="true">
        {zeroLabel}
      </span>
    );
  }

  const { days, hours, minutes, seconds } = segments(remaining);
  const label =
    days > 0
      ? `${days} ngày ${pad(hours)}:${pad(minutes)}:${pad(seconds)}`
      : `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;

  return (
    <time
      className={["ui-countdown", className].filter(Boolean).join(" ")}
      dateTime={endsAt}
      aria-label={`Còn lại ${label}`}
    >
      {days > 0 && <span className="ui-countdown-seg">{days} ngày</span>}
      <span className="ui-countdown-seg">{pad(hours)}</span>
      <span className="ui-countdown-colon">:</span>
      <span className="ui-countdown-seg">{pad(minutes)}</span>
      <span className="ui-countdown-colon">:</span>
      <span className="ui-countdown-seg">{pad(seconds)}</span>
    </time>
  );
}

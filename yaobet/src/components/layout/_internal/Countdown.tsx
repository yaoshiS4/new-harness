/* ============================================================================
 * Countdown (shell-local) — truthful, server-deadline-bound timer.
 * Renders against the server `deadlineAt`; HALTS at the deadline and
 * resolves to its real next-state ("Đã kết thúc") — it does NOT cross zero,
 * count negative, loop, or reset. A countdown past its deadline would display
 * time the server never issued = a fabricated number.
 *
 * Reduced-motion: renders the static remaining text (no per-second visible
 * tick) — the resting value, identical to the motion path's value.
 * ==========================================================================*/

"use client";

import { useEffect, useState } from "react";
import { vi } from "@/lib/i18n";
import { usePrefersReducedMotion } from "./usePrefersReducedMotion";

function remaining(deadlineMs: number, now: number) {
  // clamp at the server boundary — never negative.
  const ms = Math.max(0, deadlineMs - now);
  const total = Math.floor(ms / 1000);
  const d = Math.floor(total / 86_400);
  const h = Math.floor((total % 86_400) / 3600);
  const m = Math.floor((total % 3600) / 60);
  const s = total % 60;
  return { ended: ms <= 0, d, h, m, s };
}

const pad = (n: number) => n.toString().padStart(2, "0");

export function Countdown({ deadlineAt }: { deadlineAt: string }) {
  const deadlineMs = new Date(deadlineAt).getTime();
  const reduced = usePrefersReducedMotion();
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (reduced) return; // no per-second tick under reduced-motion
    const { ended } = remaining(deadlineMs, Date.now());
    if (ended) return; // already past — never start a ticking interval
    const id = setInterval(() => {
      const t = Date.now();
      setNow(t);
      if (t >= deadlineMs) clearInterval(id); // HALT at the server boundary
    }, 1000);
    return () => clearInterval(id);
  }, [deadlineMs, reduced]);

  // `now` is seeded with Date.now() in the useState initializer and only
  // advances via the interval (which is disabled under reduced-motion). Reading
  // it here keeps render pure — no impure Date.now() call during render.
  const { ended, d, h, m, s } = remaining(deadlineMs, now);

  if (ended) {
    return <span className="shell-countdown-ended">{vi.state.ended}</span>;
  }

  const segments: { value: number; label: string }[] = [
    { value: d, label: "Ngày" },
    { value: h, label: "Giờ" },
    { value: m, label: "Phút" },
    { value: s, label: "Giây" },
  ];

  return (
    <span
      className="shell-countdown-clock"
      role="timer"
      aria-label={`Còn ${d} ngày ${h} giờ ${m} phút ${s} giây`}
    >
      {segments.map((seg) => (
        <span key={seg.label} className="shell-countdown-unit">
          <span className="shell-countdown-seg">{pad(seg.value)}</span>
          <span className="shell-countdown-unit-label">{seg.label}</span>
        </span>
      ))}
    </span>
  );
}

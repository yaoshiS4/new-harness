/* ============================================================================
 * Badge — small status/label marker. Tones map to semantic vars;
 * `win`/`loss` stay luminance-matched (equal salience) and `danger` reads the
 * error/CTA-accent — red is status-critical/CTA only, never an outcome reward.
 * ==========================================================================*/

import type { ReactNode } from "react";

export type BadgeTone =
  | "neutral"
  | "gold"
  | "info"
  | "win"
  | "loss"
  | "caution"
  | "danger";

export interface BadgeProps {
  tone?: BadgeTone;
  /** subtle (tinted bg) | solid (filled) */
  variant?: "subtle" | "solid";
  children: ReactNode;
  className?: string;
}

export function Badge({ tone = "neutral", variant = "subtle", children, className }: BadgeProps) {
  return (
    <span
      className={["ui-badge", `ui-badge-${tone}`, `ui-badge-${variant}`, className]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </span>
  );
}

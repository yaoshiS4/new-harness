/* ============================================================================
 * Skeleton — loading placeholder (the MANDATORY loading state).
 * Branded gradient sweep (NEVER generic gray); reduced-motion → static tint
 * (handled in motion.css zeroing --dur-*; the sweep animation also disables
 * under the media query in the module). Reserves the figure's footprint so the
 * real value swaps in with no layout shift.
 * ==========================================================================*/

export interface SkeletonProps {
  /** css width — e.g. "100%", 120, "8ch" (tabular-num width for Money slots) */
  width?: number | string;
  /** css height — defaults to 1em line */
  height?: number | string;
  /** pill | text(rounded) | block(card radius) */
  shape?: "pill" | "text" | "block";
  className?: string;
  /** accessible busy label; defaults to a generic VN loading hint */
  label?: string;
}

export function Skeleton({
  width = "100%",
  height = "1em",
  shape = "text",
  className,
  label = "Đang tải",
}: SkeletonProps) {
  return (
    <span
      className={["ui-skeleton", `ui-skeleton-${shape}`, className].filter(Boolean).join(" ")}
      style={{
        width: typeof width === "number" ? `${width}px` : width,
        height: typeof height === "number" ? `${height}px` : height,
      }}
      role="status"
      aria-busy="true"
      aria-label={label}
    />
  );
}

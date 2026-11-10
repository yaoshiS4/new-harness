/* ============================================================================
 * Yaobet — [vertical] route loading UI (App Router Suspense fallback).
 * Shown while page.tsx's server fetches (providers / games / live-odds) are in
 * flight. This is the MANDATORY loading state: branded Skeletons in each
 * band's reserved footprint — NEVER a placeholder digit, a "0", or a last-known
 * number dressed as live. Reduced-motion → the Skeleton sweep falls back to a
 * static tint via motion.css (the sweep reads --dur-* which is zeroed there).
 * ==========================================================================*/

import { Skeleton } from "@/ui";

export default function VerticalLoading() {
  return (
    <div className="vertical-route-page" aria-busy="true" aria-label="Đang tải hạng mục">
      {/* banner */}
      <Skeleton shape="block" width="100%" height={140} />
      {/* provider tab strip */}
      <div className="vertical-route-toolbar-skel">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} shape="pill" width={72} height={36} />
        ))}
      </div>
      {/* filter/sort bar */}
      <Skeleton shape="block" width="100%" height={44} />
      {/* game grid */}
      <div className="vertical-route-grid-skel">
        {Array.from({ length: 12 }).map((_, i) => (
          <Skeleton key={i} shape="block" width="100%" height={160} />
        ))}
      </div>
    </div>
  );
}

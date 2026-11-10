/* ============================================================================
 * Yaobet — HOME route loading UI (App Router Suspense fallback).
 * ----------------------------------------------------------------------------
 * Shown while page.tsx's server fetches (jackpot/leaderboard/games/…) are in
 * flight. Per the §F dynamic-data contract this is the MANDATORY loading state:
 * branded Skeletons in each band's reserved footprint — NEVER a placeholder
 * digit, a "0", or a last-known number dressed as live. Reduced-motion → the
 * Skeleton sweep falls back to a static tint via motion.css.
 * ==========================================================================*/

import { Skeleton } from "@/ui";

export default function HomeLoading() {
  return (
    <div className="home-page" aria-busy="true" aria-label="Đang tải trang chủ">
      <div className="home-main">
        {/* hero */}
        <Skeleton shape="block" width="100%" height={200} />
        {/* category launcher row */}
        <div className="home-skel-row">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} shape="pill" width={64} height={64} />
          ))}
        </div>
        {/* live band */}
        <Skeleton shape="block" width="100%" height={140} />
        {/* game grid */}
        <Skeleton shape="text" width="40%" height="1.6em" />
        <div className="home-skel-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} shape="block" width="100%" height={120} />
          ))}
        </div>
        {/* vip aisle */}
        <Skeleton shape="block" width="100%" height={160} />
      </div>
    </div>
  );
}

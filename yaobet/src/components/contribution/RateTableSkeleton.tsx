/* ============================================================================
 * RateTableSkeleton — the loading shape (prototype §4.7). Filter-control
 * placeholders + a head row + 8 rows at the REAL row height, so nothing
 * shifts when data lands (CLS ≈ 0). Built on ui/Skeleton (branded sweep) — there
 * is NO spinner anywhere in this feature. role="status" + aria-busy + a visually-
 * hidden `loadingSr`; the shimmer freezes to a static fill under
 * prefers-reduced-motion (ui/Skeleton + motion.css handle it — no per-component
 * opt-out needed).
 * ==========================================================================*/

import { Skeleton } from "@/ui/Skeleton/Skeleton";
import { vi } from "@/lib/i18n";

export function RateTableSkeleton({ rows = 8 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-space-4 min-w-[0]" role="status" aria-busy="true">
      <span className="absolute w-[1px] h-[1px] p-[0] m-[-1px] overflow-hidden [clip:rect(0,0,0,0)] whitespace-nowrap [border:0]">{vi.contribution.loadingSr}</span>

      {/* filter-control placeholders */}
      <div className="flex flex-col gap-space-3" aria-hidden="true">
        <Skeleton shape="block" height="var(--tap-bar)" width="100%" />
        <div className="flex gap-space-2 overflow-hidden">
          {[72, 88, 64, 120, 80].map((w, i) => (
            <Skeleton key={i} shape="pill" height="var(--tap-min)" width={w} />
          ))}
        </div>
      </div>

      {/* table footprint — head row + N rows at the real row height */}
      <div className="[border:1px_solid_var(--border)] rounded-card [background:var(--canvas)] overflow-hidden" aria-hidden="true">
        <div className="flex gap-space-4 items-center py-space-3 px-space-4 [border-bottom:1px_solid_var(--border)] text-t-sm last:[border-bottom:none] [@media(max-width:900px)]:py-space-2 [@media(max-width:900px)]:px-space-3 [background:var(--surface-3)]">
          <span className="flex-[1_1_60%] min-w-[0]">
            <Skeleton width="60%" />
          </span>
          <span className="flex-[1_1_40%] min-w-[0]">
            <Skeleton width="50%" />
          </span>
        </div>
        {Array.from({ length: rows }).map((_, i) => (
          <div className="flex gap-space-4 items-center py-space-3 px-space-4 [border-bottom:1px_solid_var(--border)] text-t-sm last:[border-bottom:none] [@media(max-width:900px)]:py-space-2 [@media(max-width:900px)]:px-space-3" key={i}>
            <span className="flex-[1_1_60%] min-w-[0]">
              <Skeleton width={`${55 + ((i * 7) % 35)}%`} />
            </span>
            <span className="flex-[1_1_40%] min-w-[0]">
              <Skeleton width="40%" />
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

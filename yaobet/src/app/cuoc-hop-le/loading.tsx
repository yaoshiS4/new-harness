/* ============================================================================
 * /cuoc-hop-le — route-level loading UI (prototype §4.7).
 * Next shows this instantly on a route transition. It reuses the page shell +
 * the real (static, instant) PageIntro and reserves the table footprint with
 * RateTableSkeleton so there is no layout shift when the data lands. No spinner
 * exists anywhere in this feature — skeletons only.
 * ==========================================================================*/

import { PageIntro, RateTableSkeleton } from "@/components/contribution";

export default function Loading() {
  return (
    <div className="[background:var(--canvas)] flex flex-col gap-space-5 min-w-[0] pb-[calc(var(--bottombar-h)+env(safe-area-inset-bottom)+var(--space-5))] min-[768px]:pb-space-6">
      <PageIntro />
      <RateTableSkeleton />
    </div>
  );
}

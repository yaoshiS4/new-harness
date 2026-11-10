/* ============================================================================
 * RestrictedFoot — the freshness stamp rendered INSIDE the table's own border
 * (sibling of the contribution TableFoot) so any crop of the list self-dates.
 * The restricted list has no settlement/rate notes — only the update stamp
 * (effective-from, to the minute) + the published version. Reuses the generic
 * contribution.updateStamp template.
 * ==========================================================================*/

import { t, vi } from "@/lib/i18n";

export function RestrictedFoot({
  stampDate,
  version,
}: {
  /** effective-from, already formatted to the minute (DD/MM/YYYY HH:mm) */
  stampDate: string;
  version: string;
}) {
  return (
    <div className="[border-top:1px_solid_var(--border)] [background:var(--surface-2)] py-space-3 px-space-4 text-text-mid text-t-sm leading-lh-body flex flex-col gap-space-3 min-[768px]:flex-row min-[768px]:justify-end min-[768px]:items-start">
      <p className="text-text-mid min-[768px]:whitespace-nowrap min-[768px]:text-right" data-numeric>
        {t(vi.contribution.updateStamp, { date: stampDate, version })}
      </p>
    </div>
  );
}

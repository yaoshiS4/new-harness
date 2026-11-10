/* ============================================================================
 * TableFoot — the settlement sentence + the freshness stamp, rendered INSIDE
 * the table's own border (prototype §3.3) so any crop of the
 * table self-dates and self-explains. Carries:
 *   · settleNote  — winnings/losses settle as normal, including 0% types
 *   · sportCaveat — a bet can still not count even where the game has a rate
 *   · changeNotice — 30-day change notice
 *   · the stamp = updateStamp with version + effective-from + timestamp-to-minute
 * Stacks (notes then stamp) <768; two columns (notes left, stamp right) ≥768.
 * ==========================================================================*/

import { t, vi } from "@/lib/i18n";

export function TableFoot({
  stampDate,
  version,
}: {
  /** effective-from, already formatted to the minute (DD/MM/YYYY HH:mm) */
  stampDate: string;
  version: string;
}) {
  return (
    <div className="[border-top:1px_solid_var(--border)] [background:var(--surface-2)] py-space-3 px-space-4 text-text-mid text-t-sm leading-lh-body flex flex-col gap-space-3 min-[768px]:flex-row min-[768px]:justify-between min-[768px]:items-start min-[768px]:gap-space-5">
      <div className="flex flex-col gap-space-1 min-w-[0]">
        <p className="text-text-mid">{vi.contribution.settleNote}</p>
        <p className="text-text-mid">{vi.contribution.sportCaveat}</p>
        <p className="text-text-mid">{vi.contribution.changeNotice}</p>
      </div>
      <p className="text-text-mid min-[768px]:whitespace-nowrap min-[768px]:text-right" data-numeric>
        {t(vi.contribution.updateStamp, { date: stampDate, version })}
      </p>
    </div>
  );
}

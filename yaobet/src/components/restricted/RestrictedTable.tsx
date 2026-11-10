/* ============================================================================
 * RestrictedTable — the frame + the a11y <table> + the frozen name column + the
 * numbered pager for the bonus-restricted list (/game-han-che). It matches the
 * rate table's column set + order — Tên trò chơi · Tỷ lệ được tính · Loại trò
 * chơi · Nhà cung cấp — with the rate as column 2, right after the frozen name.
 * Each row's rate resolves via its category (a title carries no rate); for the
 * curated restricted set every category resolves to a bare "0%", rendered by the
 * SAME RateCell the rate tab uses (never a hardcoded string). It renders WHATEVER
 * ROWS IT IS GIVEN, IN THE ORDER GIVEN — the current page of the list. It holds
 * zero business logic: the island computes the rows and the page slice.
 *
 * FROZEN COLUMN (mirrors RateTable):
 *   1. Scroller `freezeFirstColumn` targets the rail's first flex child (the
 *      <table>) — pass it (it also sets scroll-snap-type:none) but the pin comes
 *      from `.rowHead`.
 *   2. EVERY cell sets its own opaque background or the frozen column won't
 *      occlude the scrolling body.
 *   3. No sticky <thead>; no zebra (rows separate on a --border hairline).
 *      Head cells sit on --surface-3, so their muted ink is --fg-muted-raised.
 * The Pager AND RestrictedFoot sit INSIDE the frame but OUTSIDE the Scroller —
 * they never scroll sideways. The stamp lives in RestrictedFoot, inside the crop
 * region, so any crop of the table self-dates.
 * ==========================================================================*/

import type { CategoryRate } from "@/lib/mock";
import { Scroller } from "@/ui/Scroller/Scroller";
import { t, vi } from "@/lib/i18n";
import { Pager, RateCell } from "@/components/contribution";
import { RestrictedFoot } from "./RestrictedFoot";

/** One rendered restricted-game row. The rate always resolves from a category,
 *  never authored on a title (mirrors the rate table). */
export interface RestrictedRow {
  key: string;
  /** column 1 — the frozen <th scope="row"> (the game title) */
  name: string;
  /** column 2 — the rate (via RateCell); the curated set resolves to "0%" */
  rate: CategoryRate;
  /** column 3 — the game type (category name) */
  category: string;
  /** column 4 — the provider */
  provider: string;
}

export function RestrictedTable({
  rows,
  stampDate,
  version,
  page,
  pageCount,
  onPage,
}: {
  /** the CURRENT PAGE of rows, already in display order */
  rows: RestrictedRow[];
  /** effective-from, formatted to the minute (DD/MM/YYYY HH:mm) */
  stampDate: string;
  version: string;
  /** active 1-based page */
  page: number;
  /** total pages across the filtered set */
  pageCount: number;
  /** request a page change */
  onPage: (n: number) => void;
}) {
  return (
    <div className="[border:1px_solid_var(--border)] rounded-card [background:var(--canvas)] overflow-hidden">
      <Scroller
        freezeFirstColumn
        snap={false}
        peek={false}
        label={vi.restricted.scrollerLabel}
      >
        <table className="border-separate [border-spacing:0] w-full min-w-[360px] font-brand-font-num [font-variant-numeric:tabular-nums]">
          <caption className="absolute w-[1px] h-[1px] p-[0] m-[-1px] overflow-hidden [clip:rect(0,0,0,0)] whitespace-nowrap [border:0]">
            {t(vi.restricted.tableCaption, { date: stampDate, version })}
          </caption>
          <thead>
            <tr>
              <th scope="col" className="py-space-3 px-space-4 [border-bottom:1px_solid_var(--border)] whitespace-nowrap text-t-sm text-left align-top [@media(max-width:900px)]:py-space-2 [@media(max-width:900px)]:px-space-3 [background:var(--surface-3)] text-fg-muted-raised font-weight-semi sticky left-[0] z-[calc(var(--z-sticky)+1)]">
                {vi.contribution.colGame}
              </th>
              <th scope="col" className="py-space-3 px-space-4 [border-bottom:1px_solid_var(--border)] whitespace-nowrap text-t-sm text-left align-top [@media(max-width:900px)]:py-space-2 [@media(max-width:900px)]:px-space-3 [background:var(--surface-3)] text-fg-muted-raised font-weight-semi">
                {vi.contribution.colRate}
              </th>
              <th scope="col" className="py-space-3 px-space-4 [border-bottom:1px_solid_var(--border)] whitespace-nowrap text-t-sm text-left align-top [@media(max-width:900px)]:py-space-2 [@media(max-width:900px)]:px-space-3 [background:var(--surface-3)] text-fg-muted-raised font-weight-semi">
                {vi.contribution.colCategory}
              </th>
              <th scope="col" className="py-space-3 px-space-4 [border-bottom:1px_solid_var(--border)] whitespace-nowrap text-t-sm text-left align-top [@media(max-width:900px)]:py-space-2 [@media(max-width:900px)]:px-space-3 [background:var(--surface-3)] text-fg-muted-raised font-weight-semi">
                {vi.contribution.colProvider}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.key}>
                <th scope="row" className="sticky left-[0] z-(--z-content) flex flex-col items-start gap-space-1 py-space-3 px-space-4 [background:var(--surface-2)] [border-right:1px_solid_var(--border)] [border-bottom:1px_solid_var(--border)] text-text-hi font-brand-font-body font-weight-semi text-t-sm text-left align-top whitespace-normal wrap-anywhere [@media(max-width:900px)]:py-space-2 [@media(max-width:900px)]:px-space-3 [tr:last-child>&]:[border-bottom:none] min-[1024px]:[tr:hover>&]:[background:var(--surface-hover)]">
                  <span className="wrap-anywhere">{row.name}</span>
                </th>
                <td className="py-space-3 px-space-4 [border-bottom:1px_solid_var(--border)] whitespace-nowrap text-t-sm text-left align-top [@media(max-width:900px)]:py-space-2 [@media(max-width:900px)]:px-space-3 [background:var(--canvas)] [tr:last-child>&]:[border-bottom:none] min-[1024px]:[tr:hover>&]:[background:var(--surface-hover)] text-text" data-numeric>
                  <RateCell rate={row.rate} />
                </td>
                <td className="py-space-3 px-space-4 [border-bottom:1px_solid_var(--border)] whitespace-nowrap text-t-sm text-left align-top [@media(max-width:900px)]:py-space-2 [@media(max-width:900px)]:px-space-3 [background:var(--canvas)] [tr:last-child>&]:[border-bottom:none] min-[1024px]:[tr:hover>&]:[background:var(--surface-hover)] text-text-mid min-[1024px]:[tr:hover>&]:text-fg-muted-raised">{row.category}</td>
                <td className="py-space-3 px-space-4 [border-bottom:1px_solid_var(--border)] whitespace-nowrap text-t-sm text-left align-top [@media(max-width:900px)]:py-space-2 [@media(max-width:900px)]:px-space-3 [background:var(--canvas)] [tr:last-child>&]:[border-bottom:none] min-[1024px]:[tr:hover>&]:[background:var(--surface-hover)] text-text-mid min-[1024px]:[tr:hover>&]:text-fg-muted-raised">{row.provider}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Scroller>

      {/* numbered pager — inside the frame, OUTSIDE the Scroller (never scrolls
          sideways). Reused verbatim from the contribution feature. */}
      <Pager page={page} pageCount={pageCount} onPage={onPage} />

      <RestrictedFoot stampDate={stampDate} version={version} />
    </div>
  );
}

/* ============================================================================
 * ResultStatus — the single aria-live line above the table (prototype §2/§9).
 * It states what the table currently shows:
 *   · a filtered / searched set → the visible count `{n} trò chơi`
 *   · not-found → it announces the FULL resolving sentence (never a bare "0 kết
 *     quả"); the sentence is visually carried by NotFoundResolver, so here it is
 *     sr-only — the live region still speaks it.
 * The region is always mounted so a change is announced; nothing announces on the
 * default view, and nothing announces while the user is mid-composition (the
 * committed query simply does not change).
 * ==========================================================================*/

import { t, vi } from "@/lib/i18n";

export function ResultStatus({
  count,
  notFound,
}: {
  /** the count of the active filtered/searched set; null on the default view */
  count: number | null;
  notFound: boolean;
}) {
  return (
    <p className="text-text-mid text-t-sm leading-lh-tight min-h-(--t-sm)" aria-live="polite">
      {notFound ? (
        <span className="absolute w-[1px] h-[1px] p-[0] m-[-1px] overflow-hidden [clip:rect(0,0,0,0)] whitespace-nowrap [border:0]">
          {`${vi.contribution.notFoundTitle} ${vi.contribution.notFoundResolve}`}
        </span>
      ) : count != null ? (
        <span>{t(vi.contribution.resultCount, { n: count })}</span>
      ) : null}
    </p>
  );
}

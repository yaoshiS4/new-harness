/* ============================================================================
 * Pager — the client-side numbered pager over the per-game rows (owner
 * conventional-table override, decisions/2026-08-10). It REPLACES the old
 * "Xem thêm / Xem tất cả" progressive-reveal controls. It owns no data: the
 * island computes the filtered rows + the page count and slices the current
 * page; this component only renders the control and forwards a page request.
 *
 *   · a labelled <nav> (aria-label) wrapping Prev / numbered pages / Next.
 *   · aria-current="page" on the active page button; a disabled Prev at page 1
 *     and a disabled Next at the last page (unfocusable, unclickable).
 *   · ellipsis (…) collapses long ranges to first · current±1 · last.
 *   · pages are NOT deep-linkable (no ?page= URL param) — page state lives in the
 *     island only, which limits scrape-addressability per the decision doc.
 * Renders nothing when there is a single page (or none).
 * ==========================================================================*/

"use client";

import { Icon } from "@/ui/Icon/Icon";
import { t, vi } from "@/lib/i18n";

/** The visible page-token list: always page 1, the last page and the current
 *  page ±1; any gap between kept pages collapses to one "ellipsis" token. Pure. */
export function pageTokens(
  page: number,
  pageCount: number,
): (number | "ellipsis")[] {
  const wanted = new Set<number>([1, pageCount, page - 1, page, page + 1]);
  const shown = [...wanted]
    .filter((p) => p >= 1 && p <= pageCount)
    .sort((a, b) => a - b);
  const out: (number | "ellipsis")[] = [];
  let prev = 0;
  for (const p of shown) {
    if (p - prev > 1) out.push("ellipsis");
    out.push(p);
    prev = p;
  }
  return out;
}

export function Pager({
  page,
  pageCount,
  onPage,
}: {
  /** the active 1-based page */
  page: number;
  /** total pages (rows / pageSize, ceil) */
  pageCount: number;
  /** request a page change (island clamps + re-slices) */
  onPage: (n: number) => void;
}) {
  if (pageCount <= 1) return null;
  const tokens = pageTokens(page, pageCount);
  const atFirst = page <= 1;
  const atLast = page >= pageCount;

  return (
    <nav className="flex items-center justify-center flex-wrap gap-space-2 [border-top:1px_solid_var(--border)] p-space-3 min-w-[0]" aria-label={vi.contribution.pagerLabel}>
      <button
        type="button"
        className="inline-flex items-center justify-center w-tap-min h-tap-min flex-[0_0_auto] [background:var(--surface-2)] [border:1px_solid_var(--border)] rounded-md text-text-hi cursor-pointer [transition:background-color_var(--dur-fast)_var(--ease-standard),transform_var(--dur-fast)_var(--ease-standard)] hover:not-disabled:[background:var(--surface-hover)] hover:not-disabled:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 disabled:[background:var(--surface-disabled)] disabled:text-text-mid disabled:cursor-not-allowed motion-reduce:[transition:none] motion-reduce:hover:not-disabled:[transform:none]"
        onClick={() => onPage(page - 1)}
        disabled={atFirst}
        aria-label={vi.contribution.pagerPrev}
      >
        <Icon name="chevronLeft" aria-hidden />
      </button>

      <ol className="flex items-center flex-wrap justify-center gap-space-1 list-none m-[0] p-[0] min-w-[0]">
        {tokens.map((tok, i) =>
          tok === "ellipsis" ? (
            <li key={`gap-${i}`} className="inline-flex items-center justify-center min-w-space-4 h-tap-min text-text-mid text-t-sm" aria-hidden="true">
              …
            </li>
          ) : (
            <li key={tok}>
              <button
                type="button"
                className={`inline-flex items-center justify-center min-w-tap-min h-tap-min py-[0] px-space-2 rounded-md font-brand-font-num [font-variant-numeric:tabular-nums] text-t-sm font-weight-semi cursor-pointer [transition:background-color_var(--dur-fast)_var(--ease-standard),transform_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:text-text-hi hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 motion-reduce:[transition:none] motion-reduce:hover:[transform:none] ${tok === page ? "[background:var(--surface-3)] [border:1px_solid_var(--border)] text-text-hi" : "[background:transparent] [border:1px_solid_transparent] text-text-mid"}`}
                onClick={() => onPage(tok)}
                aria-label={t(vi.contribution.pagerPage, { n: tok })}
                aria-current={tok === page ? "page" : undefined}
              >
                {tok}
              </button>
            </li>
          ),
        )}
      </ol>

      <button
        type="button"
        className="inline-flex items-center justify-center w-tap-min h-tap-min flex-[0_0_auto] [background:var(--surface-2)] [border:1px_solid_var(--border)] rounded-md text-text-hi cursor-pointer [transition:background-color_var(--dur-fast)_var(--ease-standard),transform_var(--dur-fast)_var(--ease-standard)] hover:not-disabled:[background:var(--surface-hover)] hover:not-disabled:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 disabled:[background:var(--surface-disabled)] disabled:text-text-mid disabled:cursor-not-allowed motion-reduce:[transition:none] motion-reduce:hover:not-disabled:[transform:none]"
        onClick={() => onPage(page + 1)}
        disabled={atLast}
        aria-label={vi.contribution.pagerNext}
      >
        <Icon name="chevronRight" aria-hidden />
      </button>
    </nav>
  );
}

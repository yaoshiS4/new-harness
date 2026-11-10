/* ============================================================================
 * RestrictedRoot — THE ONE client island for the bonus-restricted list
 * (/game-han-che). Sibling of ContributionRoot, minus the rate dimension. It
 * receives the restricted `list` from the server page, owns a small piece of
 * state — { query, categoryId, provider, page } (plus the network flag + a
 * search-index error flag) — and derives everything else. It NEVER fetches.
 *
 * THE MODEL IS A FLAT, FILTERABLE, PAGINATED, RATE-FREE TABLE:
 *   · `base` builds ONE flat list of rows from the restricted games, sorted
 *     lobby(category) → provider → title with pure codepoint comparisons so SSR
 *     and the client hydrate byte-identical order.
 *   · Search + TWO filters (category · provider) COMBINE (AND); the numbered
 *     pager (25 / page) pages the result. There is NO rate-bucket filter.
 *   · Empty handling: a search that matches nothing → a neutral notFound strip
 *     (never "excluded"); a filter combo that matches nothing → a neutral
 *     FilterNotice with a reset. Both reuse the shared FilterNotice.
 *
 * PROGRESSIVE ENHANCEMENT: the default state (no query, no filter) renders page 1
 * of the full list server-side, so a JavaScript-off visitor still gets a real
 * table (the pager + live filters are the enhancement).
 * ==========================================================================*/

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type { CategoryRate, RestrictedList } from "@/lib/mock";
import { t, vi } from "@/lib/i18n";
import { FilterNotice, foldQuery } from "@/components/contribution";
import { RestrictedFilters } from "./RestrictedFilters";
import { RestrictedTable, type RestrictedRow } from "./RestrictedTable";

const PAGE_SIZE = 25; // rows per page (matches the rate page)

/* ---- pure matching helpers (not components) -------------------------------- */

const tokenize = (folded: string): string[] =>
  folded.split(" ").filter(Boolean);

/** every query token is a prefix of at least one target token */
const everyPrefix = (q: string[], target: string[]): boolean =>
  q.every((qt) => target.some((tt) => tt.startsWith(qt)));

/** codepoint comparison (deterministic on server AND client — no ICU/locale) */
const cp = (a: string, b: string): number => (a < b ? -1 : a > b ? 1 : 0);

/** An enriched, filterable row (base data — independent of search). */
interface Row {
  key: string;
  name: string;
  categoryId: string;
  category: string;
  /** resolved category rate (via categoryId — carried through to RateCell) */
  rate: CategoryRate;
  provider: string;
  /** folded key for a deterministic, locale-free title sort */
  sortKey: string;
}

/** Per-row folded search tokens (the fallible index — a build failure disables
 *  search but never the base table). */
interface RowTokens {
  name: string[];
  prev: string[][];
  provider: string[];
  /** folded category-name tokens (so typing a category surfaces its games) */
  category: string[];
}

export function RestrictedRoot({
  list,
  stampDate,
  version,
}: {
  list: RestrictedList;
  stampDate: string;
  version: string;
}) {
  /* ---- owned state ---- */
  const [rawQuery, setRawQuery] = useState("");
  const [query, setQuery] = useState(""); // folded + debounced (from SearchField)
  const [categoryId, setCategoryId] = useState("all");
  const [provider, setProvider] = useState("all");
  const [page, setPage] = useState(1);
  const [online, setOnline] = useState(true);
  const [errorNonce, setErrorNonce] = useState(0);

  /* network awareness — disables the search field + swaps its hint offline. */
  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    update();
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  /* ---- ALWAYS-SAFE base: the sorted flat rows + chips + providers ----
   * Ordered lobby(category) → provider → title, pure codepoint comparisons (no
   * locale) so SSR and hydration produce the identical row order. */
  const base = useMemo(() => {
    const catOrder = new Map(list.categories.map((c, i) => [c.id, i] as const));
    const rows: Row[] = list.games.map((g) => ({
      key: g.id,
      name: g.name,
      categoryId: g.categoryId,
      category: g.category,
      rate: g.rate,
      provider: g.provider,
      sortKey: g.searchKey,
    }));
    rows.sort((a, b) => {
      const ci = (catOrder.get(a.categoryId) ?? 0) - (catOrder.get(b.categoryId) ?? 0);
      if (ci !== 0) return ci;
      const pi = cp(a.provider, b.provider);
      if (pi !== 0) return pi;
      const ti = cp(a.sortKey, b.sortKey);
      if (ti !== 0) return ti;
      return cp(a.key, b.key);
    });
    const providers = [...new Set(list.games.map((g) => g.provider))].sort(
      (a, b) => a.localeCompare(b, "vi"),
    );
    return { rows, chips: list.categories, providers };
  }, [list]);

  /* ---- FALLIBLE search index: per-row folded tokens. A failure disables search
   * (an error notice shows) but the base table still paginates. `errorNonce`
   * (bumped by retry) re-runs the build. */
  const index = useMemo(() => {
    try {
      const tokensByKey = new Map<string, RowTokens>();
      for (const g of list.games) {
        tokensByKey.set(g.id, {
          name: tokenize(g.searchKey),
          prev: (g.prevNames ?? []).map(tokenize),
          provider: tokenize(foldQuery(g.provider)),
          category: tokenize(foldQuery(g.category)),
        });
      }
      return { ok: true as const, tokensByKey };
    } catch {
      return { ok: false as const };
    }
    // errorNonce is an intentional dependency (retry re-runs the build).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [list, errorNonce]);

  const retry = useCallback(() => setErrorNonce((n) => n + 1), []);
  const resetFilters = useCallback(() => {
    setCategoryId("all");
    setProvider("all");
    setPage(1);
  }, []);
  const resetAll = useCallback(() => {
    setRawQuery("");
    setQuery("");
    setCategoryId("all");
    setProvider("all");
    setPage(1);
  }, []);

  /* ---- handlers: filters COMBINE; each resets the page to 1 ---- */
  const onQueryChange = useCallback((raw: string) => setRawQuery(raw), []);
  const onCommit = useCallback((folded: string) => {
    setQuery(folded);
    setPage(1);
  }, []);
  const onCategory = useCallback((id: string) => {
    setCategoryId(id);
    setPage(1);
  }, []);
  const onProvider = useCallback((name: string) => {
    setProvider(name);
    setPage(1);
  }, []);

  /* ---- the view: filter → paginate ---- */
  const view = useMemo(() => {
    const q = query ? tokenize(query) : null;
    const searchOk = index.ok;

    const filtered = base.rows.filter((r) => {
      if (categoryId !== "all" && r.categoryId !== categoryId) return false;
      if (provider !== "all" && r.provider !== provider) return false;
      if (q && searchOk) {
        const tk = index.tokensByKey.get(r.key);
        if (!tk) return false;
        const hit =
          everyPrefix(q, tk.name) ||
          tk.prev.some((p) => everyPrefix(q, p)) ||
          everyPrefix(q, tk.provider) ||
          everyPrefix(q, tk.category);
        if (!hit) return false;
      }
      return true;
    });

    const total = filtered.length;
    const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
    const safePage = Math.min(Math.max(1, page), pageCount);
    const start = (safePage - 1) * PAGE_SIZE;
    const rows: RestrictedRow[] = filtered
      .slice(start, start + PAGE_SIZE)
      .map((r) => ({
        key: r.key,
        name: r.name,
        rate: r.rate,
        category: r.category,
        provider: r.provider,
      }));

    const notFound = total === 0 && query !== "";
    const emptyFilter = total === 0 && query === "";

    return { rows, total, pageCount, safePage, notFound, emptyFilter };
  }, [base, index, query, categoryId, provider, page]);

  return (
    <div className="flex flex-col gap-space-4 min-w-[0]">
      <RestrictedFilters
        categories={base.chips}
        providers={base.providers}
        categoryId={categoryId}
        provider={provider}
        rawQuery={rawQuery}
        offline={!online}
        onQueryChange={onQueryChange}
        onCommit={onCommit}
        onCategory={onCategory}
        onProvider={onProvider}
      />

      {/* single aria-live line — the visible count, or the not-found sentence
          (sr-only; the neutral strip below carries it visually) */}
      <p className="text-text-mid text-t-sm leading-lh-tight min-h-(--t-sm)" aria-live="polite">
        {view.notFound ? (
          <span className="absolute w-[1px] h-[1px] p-[0] m-[-1px] overflow-hidden [clip:rect(0,0,0,0)] whitespace-nowrap [border:0]">{vi.restricted.notFound}</span>
        ) : (
          <span>{t(vi.contribution.resultCount, { n: view.total })}</span>
        )}
      </p>

      {!index.ok && (
        <FilterNotice
          variant="error"
          message={vi.restricted.searchError}
          action={{ label: vi.state.retry, onClick: retry }}
        />
      )}

      {view.notFound && (
        <FilterNotice
          variant="empty"
          message={vi.restricted.notFound}
          action={{ label: vi.state.reset, onClick: resetAll }}
        />
      )}

      {view.emptyFilter && (
        <FilterNotice
          variant="empty"
          message={vi.contribution.emptyFilter}
          action={{
            label: vi.contribution.emptyFilterReset,
            onClick: resetFilters,
          }}
        />
      )}

      <RestrictedTable
        rows={view.rows}
        stampDate={stampDate}
        version={version}
        page={view.safePage}
        pageCount={view.pageCount}
        onPage={setPage}
      />
    </div>
  );
}

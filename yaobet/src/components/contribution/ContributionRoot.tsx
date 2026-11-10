/* ============================================================================
 * ContributionRoot — THE ONE client island for the conventional per-game table
 * (owner override, decisions/2026-08-10-owner-override-conventional-table.md). It
 * receives `rates` + `catalogue` from the server page, owns a small piece of
 * state — { query, categoryId, provider, bucket, page } (plus the network flag
 * and a search-index error flag) — and derives everything else. It NEVER fetches.
 *
 * THE MODEL IS A FLAT, FILTERABLE, PAGINATED TABLE:
 *   · `base` (always-safe) builds ONE flat list of per-game rows from the
 *     catalogue, each resolving its rate via categoryId → category.rate (a title
 *     NEVER carries a rate) and its rate BUCKET (100% / một phần / không tính).
 *     Rows are sorted lobby(category) → provider → title with pure codepoint
 *     comparisons so the SSR and the client hydrate byte-identical order.
 *   · Search + the three filters (category · provider · rate-bucket) COMBINE (AND)
 *     to narrow the list; the client-side numbered pager (25 / page) pages it.
 *   · Empty handling: a search that matches nothing → NotFoundResolver ("no
 *     match", never "excluded"); a filter combo that matches nothing (no search)
 *     → a neutral FilterNotice with a clear-filters reset.
 *
 * PROGRESSIVE ENHANCEMENT: the default state (no query, no filter) renders page 1
 * of the full per-game table server-side, so a JavaScript-off visitor still gets
 * a real table (the pager + live filters are the enhancement).
 * ==========================================================================*/

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import type {
  CategoryRate,
  ContributionCategory,
  ContributionRates,
  ContributionTitle,
  RateBucket,
} from "@/lib/mock";
import { deriveProviders, rateBucket } from "@/lib/mock";
import { vi } from "@/lib/i18n";
import { RateFilters, type BucketValue } from "./RateFilters";
import { ResultStatus } from "./ResultStatus";
import { NotFoundResolver } from "./NotFoundResolver";
import { FilterNotice } from "./FilterNotice";
import { RateTable, type RateRow } from "./RateTable";
import { foldQuery } from "./SearchField";

const PAGE_SIZE = 25; // per-game rows per page (owner default)

/* ---- pure matching helpers (not components) -------------------------------- */

const tokenize = (folded: string): string[] =>
  folded.split(" ").filter(Boolean);

/** every query token is a prefix of at least one target token */
const everyPrefix = (q: string[], target: string[]): boolean =>
  q.every((qt) => target.some((tt) => tt.startsWith(qt)));

/** pooled folded tokens of a category — its search key + every alias token */
function poolTokens(cat: ContributionCategory): string[] {
  return [...tokenize(cat.searchKey), ...cat.aliases.flatMap((a) => tokenize(a))];
}

/** codepoint comparison (deterministic on server AND client — no ICU/locale) */
const cp = (a: string, b: string): number => (a < b ? -1 : a > b ? 1 : 0);

/** An enriched, filterable per-game row (base data — independent of search). */
interface Row {
  key: string;
  name: string;
  rate: CategoryRate;
  categoryId: string;
  categoryName: string;
  provider: string;
  bucket: RateBucket;
  /** folded key for a deterministic, locale-free title sort */
  sortKey: string;
}

/** Per-row folded search tokens (the fallible index — a build failure disables
 *  search but never the base table). */
interface RowTokens {
  name: string[];
  prev: string[][];
  provider: string[];
  /** pooled category tokens (so typing a category / alias surfaces its games) */
  category: string[];
}

export function ContributionRoot({
  rates,
  catalogue,
  stampDate,
  version,
}: {
  rates: ContributionRates;
  catalogue: ContributionTitle[];
  stampDate: string;
  version: string;
}) {
  /* ---- owned state ---- */
  const [rawQuery, setRawQuery] = useState("");
  const [query, setQuery] = useState(""); // folded + debounced (from SearchField)
  const [categoryId, setCategoryId] = useState("all");
  const [provider, setProvider] = useState("all");
  const [bucket, setBucket] = useState<BucketValue>("all");
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

  /* ---- ALWAYS-SAFE base: the sorted flat per-game rows + chips + providers ----
   * Ordered lobby(category) → provider → title, with pure codepoint comparisons
   * (no locale) so SSR and hydration produce the identical row order. */
  const base = useMemo(() => {
    const catOrder = new Map(rates.categories.map((c, i) => [c.id, i] as const));
    const catById = new Map(rates.categories.map((c) => [c.id, c] as const));
    const rows: Row[] = [];
    for (const ttl of catalogue) {
      const cat = catById.get(ttl.categoryId);
      if (!cat) continue; // defensive: skip an orphan title (never in the fixture)
      rows.push({
        key: ttl.id,
        name: ttl.name,
        rate: cat.rate,
        categoryId: cat.id,
        categoryName: cat.name,
        provider: ttl.provider,
        bucket: rateBucket(cat.rate),
        sortKey: ttl.searchKey,
      });
    }
    rows.sort((a, b) => {
      const ci = (catOrder.get(a.categoryId) ?? 0) - (catOrder.get(b.categoryId) ?? 0);
      if (ci !== 0) return ci;
      const pi = cp(a.provider, b.provider);
      if (pi !== 0) return pi;
      const ti = cp(a.sortKey, b.sortKey);
      if (ti !== 0) return ti;
      return cp(a.key, b.key);
    });
    return {
      rows,
      chips: rates.categories.map((c) => ({ id: c.id, name: c.name })),
      providers: deriveProviders(catalogue),
    };
  }, [rates, catalogue]);

  /* ---- FALLIBLE search index: per-row folded tokens. A failure disables search
   * (an error notice shows) but the base table still paginates. `errorNonce`
   * (bumped by retry) re-runs the build. */
  const index = useMemo(() => {
    try {
      const poolByCat = new Map<string, string[]>();
      for (const cat of rates.categories) poolByCat.set(cat.id, poolTokens(cat));
      const tokensByKey = new Map<string, RowTokens>();
      for (const ttl of catalogue) {
        tokensByKey.set(ttl.id, {
          name: tokenize(ttl.searchKey),
          prev: (ttl.prevNames ?? []).map(tokenize),
          provider: tokenize(foldQuery(ttl.provider)),
          category: poolByCat.get(ttl.categoryId) ?? [],
        });
      }
      return { ok: true as const, tokensByKey };
    } catch {
      return { ok: false as const };
    }
    // errorNonce is an intentional dependency (retry re-runs the build).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rates, catalogue, errorNonce]);

  const retry = useCallback(() => setErrorNonce((n) => n + 1), []);
  const resetFilters = useCallback(() => {
    setCategoryId("all");
    setProvider("all");
    setBucket("all");
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
  const onBucket = useCallback((b: BucketValue) => {
    setBucket(b);
    setPage(1);
  }, []);
  // NotFoundResolver: picking a category RESOLVES the miss — it clears the search
  // and browses that category (a search + category combo would stay empty).
  const onResolveCategory = useCallback((id: string) => {
    setRawQuery("");
    setQuery("");
    setBucket("all");
    setCategoryId(id);
    setProvider("all");
    setPage(1);
  }, []);

  /* ---- the view: filter → paginate ---- */
  const view = useMemo(() => {
    const q = query ? tokenize(query) : null;
    const searchOk = index.ok;

    const filtered = base.rows.filter((r) => {
      if (categoryId !== "all" && r.categoryId !== categoryId) return false;
      if (provider !== "all" && r.provider !== provider) return false;
      if (bucket !== "all" && r.bucket !== bucket) return false;
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
    const rows: RateRow[] = filtered
      .slice(start, start + PAGE_SIZE)
      .map((r) => ({
        key: r.key,
        name: r.name,
        rate: r.rate,
        category: r.categoryName,
        provider: r.provider,
      }));

    const notFound = total === 0 && query !== "";
    const emptyFilter = total === 0 && query === "";

    return { rows, total, pageCount, safePage, notFound, emptyFilter };
  }, [base, index, query, categoryId, provider, bucket, page]);

  return (
    <div className="flex flex-col gap-space-4 min-w-[0]">
      <RateFilters
        categories={base.chips}
        providers={base.providers}
        categoryId={categoryId}
        provider={provider}
        bucket={bucket}
        rawQuery={rawQuery}
        offline={!online}
        onQueryChange={onQueryChange}
        onCommit={onCommit}
        onCategory={onCategory}
        onProvider={onProvider}
        onBucket={onBucket}
      />

      <ResultStatus
        count={view.notFound ? null : view.total}
        notFound={view.notFound}
      />

      {!index.ok && (
        <FilterNotice
          variant="error"
          message={`${vi.contribution.errorTitle} ${vi.contribution.errorBody}`}
          action={{ label: vi.contribution.retry, onClick: retry }}
        />
      )}

      {view.notFound && (
        <NotFoundResolver categories={base.chips} onPick={onResolveCategory} />
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

      <RateTable
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

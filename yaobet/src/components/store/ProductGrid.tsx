/* ============================================================================
 * ProductGrid — points-store catalog host. A thin
 * client island: it owns the redeem-dialog state, the auth gate, and the four
 * fetch surfaces — loading · error · empty · populated. It renders NO card
 * markup itself; each item is a <ProductCard/> (the full escalation machine
 * lives in the lazy RedeemDialog). Grid ramp: 2-up (base) → 3-up (@768) →
 * 4-up (@1024). Tapping a card's CTA opens the RedeemDialog for a member, or
 * the auth modal for a guest.
 *
 * Fetch model: seeded from the RSC-fetched `products` (keeps the server fetch),
 * but the island owns a client re-fetch so the loading + error(onRetry) paths
 * are real and reviewable (DEMO_ERROR exercises the failure). All data is MOCK.
 * ==========================================================================*/

"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import type { Product } from "@/lib/types";
import { getProducts } from "@/lib/mock";
import { DEMO_PAUSED } from "@/lib/mock/store";
import { vi } from "@/lib/i18n";
import { useRequireAuth } from "@/lib/auth";
import {
  EmptyState,
  ErrorState,
  TileSkeleton,
  useGridCols,
  computeGridFill,
} from "@/ui";
import { ProductCard } from "./ProductCard";
import { RedeemDialog } from "./RedeemDialog";

export interface ProductGridProps {
  /** RSC-fetched catalog — seeds the island's initial data (server fetch kept). */
  products: Product[];
  /** member's redeemable points — gates affordability (truthful). */
  points: number;
}

type FetchState = "ready" | "loading" | "error";

/** Client filter tabs — filter by product.category, no refetch. */
type TabKey = "all" | "voucher" | "product";
const TABS: { key: TabKey; label: string }[] = [
  { key: "all", label: vi.store.tabAll },
  { key: "voucher", label: vi.store.tabVoucher },
  { key: "product", label: vi.store.tabProduct },
];

export function ProductGrid({ products, points }: ProductGridProps) {
  const { allowed, promptAuth } = useRequireAuth();
  const [selected, setSelected] = useState<Product | null>(null);
  const [tab, setTab] = useState<TabKey>("all");

  // A guest never has affordability computed from a balance the header hides.
  const effectivePoints = allowed ? points : 0;
  // Program-budget breaker (mock demo flag) — pauses claims store-wide.
  const paused = DEMO_PAUSED;

  const [items, setItems] = useState<Product[]>(products);
  const [status, setStatus] = useState<FetchState>("ready");

  const gridRef = useRef<HTMLUListElement>(null);
  const cols = useGridCols(gridRef);

  // Client-side category filter — no refetch; 'all' shows everything.
  const visible = useMemo(
    () => (tab === "all" ? items : items.filter((p) => p.category === tab)),
    [items, tab],
  );

  const onRedeem = (p: Product) => {
    if (!allowed) {
      promptAuth();
      return;
    }
    setSelected(p);
  };

  // Client re-fetch — the island's own error/retry seam over the mock accessor.
  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const fresh = await getProducts();
      setItems(fresh);
      setStatus("ready");
    } catch {
      setStatus("error");
    }
  }, []);

  if (status === "loading") {
    // Fill a couple of full rows so the grid never shows ragged trailing space.
    const fillers = Math.max(cols || 2, computeGridFill(cols, 1, 2) + 1);
    return (
      <ul className="grid grid-cols-[repeat(2,1fr)] gap-gutter list-none m-[0] p-[0] min-[768px]:grid-cols-[repeat(3,1fr)] min-[1024px]:grid-cols-[repeat(4,1fr)]" ref={gridRef} aria-busy="true">
        {Array.from({ length: fillers }).map((_, i) => (
          <li key={i} className="flex min-w-[0]">
            <TileSkeleton />
          </li>
        ))}
      </ul>
    );
  }

  if (status === "error") {
    return (
      <ErrorState
        title="Không tải được cửa hàng"
        message="Không tải được danh sách quà đổi điểm. Vui lòng thử lại."
        onRetry={load}
      />
    );
  }

  if (items.length === 0) {
    return (
      <EmptyState
        icon="gift"
        title="Cửa hàng trống"
        message="Hiện chưa có sản phẩm nào để đổi điểm."
      />
    );
  }

  return (
    <>
      {/* Client filter tabs — pill row above the grid; filter by category. */}
      <div className="flex gap-space-2 mb-space-4 flex-wrap" role="tablist" aria-label={vi.store.title}>
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={tab === t.key}
            className={`inline-flex items-center min-h-tap-min py-[6px] px-space-3 rounded-pill border text-t-sm font-weight-semi leading-[1] cursor-pointer [transition:color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),transform_var(--dur-fast)_var(--ease-standard)] hover:text-text-hi hover:[transform:scale(1.05)] motion-reduce:[transition:none] motion-reduce:hover:[transform:none] ${
              tab === t.key
                ? "text-tab-text-active [background:var(--surface-2)] border-brand-accent-hairline"
                : "text-tab-text-rest [background:transparent] border-border"
            }`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <ul className="grid grid-cols-[repeat(2,1fr)] gap-gutter list-none m-[0] p-[0] min-[768px]:grid-cols-[repeat(3,1fr)] min-[1024px]:grid-cols-[repeat(4,1fr)]" ref={gridRef}>
        {visible.map((p) => (
          <li key={p.id} className="flex min-w-[0]">
            <ProductCard
              product={p}
              points={effectivePoints}
              allowed={allowed}
              paused={paused}
              onRedeem={onRedeem}
            />
          </li>
        ))}
      </ul>

      {/* lazy-mounted: only present when a product is selected */}
      {selected && (
        <RedeemDialog
          product={selected}
          points={effectivePoints}
          paused={paused}
          onClose={() => setSelected(null)}
        />
      )}
    </>
  );
}

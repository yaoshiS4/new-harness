/* ============================================================================
 * PromoGrid — filterable promo-card grid.
 * A client island: it owns the category tab/filter state and renders the
 * matching promo Cards (image SLOT + truthful title/category + real-or-static
 * Countdown). NO hardcoded bonus % — only the truthful promo fields render.
 * States: populated · empty(honest) · filtered-empty(reset). Loading is the
 * page-level Skeleton scaffold (loading.tsx); this island receives resolved
 * fixtures.
 * ==========================================================================*/

"use client";

import { useMemo, useState } from "react";
import type { Promo } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { Tabs, Tile, Badge, Countdown, EmptyState } from "@/ui";

export interface PromoGridProps {
  promos: Promo[];
}

const ALL = "all";

export function PromoGrid({ promos }: PromoGridProps) {
  const [active, setActive] = useState<string>(ALL);

  // category tabs derived from the truthful fixture (no fabricated buckets)
  const categories = useMemo(() => {
    const seen = new Set<string>();
    const out: { id: string; label: string }[] = [{ id: ALL, label: "Tất cả" }];
    for (const p of promos) {
      if (!seen.has(p.category)) {
        seen.add(p.category);
        out.push({ id: p.category, label: p.category });
      }
    }
    return out;
  }, [promos]);

  const filtered = useMemo(
    () => (active === ALL ? promos : promos.filter((p) => p.category === active)),
    [promos, active],
  );

  // honest empty — no promos exist at all
  if (promos.length === 0) {
    return (
      <EmptyState
        icon="gift"
        title="Chưa có khuyến mãi"
        message="Hiện chưa có chương trình khuyến mãi nào đang diễn ra."
      />
    );
  }

  return (
    <div className="promo-grid-wrap">
      <Tabs
        items={categories}
        active={active}
        onChange={setActive}
        label="Lọc khuyến mãi theo danh mục"
      />

      {filtered.length === 0 ? (
        <EmptyState
          variant="filtered"
          icon="gift"
          message="Không có khuyến mãi trong danh mục này."
          onReset={() => setActive(ALL)}
        />
      ) : (
        <ul className="promo-grid-grid">
          {filtered.map((p) => (
            <li key={p.id} className="promo-grid-cell">
              <Tile
                label={p.title}
                imageSrc={p.imageSrc}
                aspect="16 / 9"
                href={p.href}
                badge={<Badge tone="gold">{p.category}</Badge>}
              />
              {/* real, server-deadline-bound countdown — static when evergreen */}
              {p.endsAt ? (
                <div className="promo-grid-timer">
                  <span className="promo-grid-timer-label">Kết thúc sau</span>
                  <Countdown endsAt={p.endsAt} zeroLabel={vi.state.ended} />
                </div>
              ) : (
                <span className="promo-grid-evergreen">Đang diễn ra</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

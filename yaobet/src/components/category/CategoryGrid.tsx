/* ============================================================================
 * CategoryGrid — the vertical landing's interactive core (home game-grid;
 * [vertical] route). Provider tab strip → filter/sort bar →
 * game grid (image SLOTS, 6/4/3 responsive) → honest EmptyState.
 *
 * Auth-aware (the FTD seam entry): browsing is always open; only the LAUNCH
 * gates. A guest tapping a game tile opens the auth modal via
 * useRequireAuth.promptAuth; a member tap routes to the game (UI-only mock).
 *
 * Truthful-only: there is no fabricated game count. A search/provider filter
 * that matches nothing renders the `filtered` EmptyState with a reset — never
 * filler tiles. Sort is a pure client reorder of the handed list (no invented
 * popularity/win numbers).
 * ==========================================================================*/

"use client";

import { useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { GameTile, Provider } from "@/lib/types";
import { useRequireAuth } from "@/lib/auth";
import { Tabs, Tile, ComingSoonTile, Pill, EmptyState, Icon, useGridFill } from "@/ui";

export interface CategoryGridProps {
  verticalId: string;
  providers: Provider[];
  games: GameTile[];
}

const ALL = "all";

type SortKey = "default" | "name" | "provider";

const SORTS: { id: SortKey; label: string }[] = [
  { id: "default", label: "Mặc định" },
  { id: "name", label: "Tên A→Z" },
  { id: "provider", label: "Nhà cung cấp" },
];

export function CategoryGrid({ verticalId, providers, games }: CategoryGridProps) {
  const { allowed, promptAuth } = useRequireAuth();
  const router = useRouter();
  const gridRef = useRef<HTMLUListElement>(null);
  const [active, setActive] = useState(ALL);
  const [sort, setSort] = useState<SortKey>("default");
  const [query, setQuery] = useState("");

  const tabItems = useMemo(
    () => [
      { id: ALL, label: "Tất cả" },
      ...providers.map((p) => ({ id: p.name, label: p.name })),
    ],
    [providers],
  );

  const filtered = useMemo(() => {
    let list = active === ALL ? games : games.filter((g) => g.provider === active);
    const q = query.trim().toLowerCase();
    if (q) list = list.filter((g) => g.name.toLowerCase().includes(q));
    if (sort === "name") {
      list = [...list].sort((a, b) => a.name.localeCompare(b.name, "vi"));
    } else if (sort === "provider") {
      list = [...list].sort((a, b) => a.provider.localeCompare(b.provider, "vi"));
    }
    return list;
  }, [active, games, query, sort]);

  const isFiltered = active !== ALL || query.trim() !== "";

  // Pad the grid so it (a) completes its last partial row AND (b) fills to at
  // least 2 full rows — a short provider tab never leaves a large dead void
  // below the first filler row and the layout never shifts on a tab
  // switch. Every CategoryGrid cell is a uniform 1×1 → occupiedCells ==
  // filtered.length; useGridFill resolves the LIVE column count and returns the
  // pad needed to reach the 2-row minimum. The pad cells are PREMIUM "Sắp ra
  // mắt" coming-soon cards — gold-on-obsidian placeholders sized identically to
  // a real tile, never a dark void or a cloned game.
  const fillerCount = useGridFill(gridRef, filtered.length, 2);

  const reset = () => {
    setActive(ALL);
    setQuery("");
    setSort("default");
  };

  const onTile = (g: GameTile) => {
    if (!allowed) {
      // guest → auth modal (FTD seam entry). Browsing stays open; launch gates.
      promptAuth({ action: "none" });
      return;
    }
    // member: UI-only mock launch → route into the vertical with the game id.
    router.push(`/${verticalId}?game=${encodeURIComponent(g.id)}`);
  };

  return (
    <section className="vertical-category-grid-section" aria-label="Trò chơi">
      {/* provider tab strip — scrolls @375 via the Scroller-backed Tabs */}
      <Tabs
        items={tabItems}
        active={active}
        onChange={setActive}
        label="Nhà cung cấp"
      />

      {/* filter / sort bar */}
      <div className="vertical-category-grid-toolbar">
        <label className="vertical-category-grid-search">
          <Icon name="search" size={18} className="vertical-category-grid-search-icon" label="Tìm" />
          <input
            type="search"
            inputMode="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Tìm trò chơi"
            className="vertical-category-grid-search-input"
            aria-label="Tìm trò chơi"
          />
        </label>
        <div className="vertical-category-grid-sorts" role="group" aria-label="Sắp xếp">
          {SORTS.map((s) => (
            <Pill
              key={s.id}
              active={sort === s.id}
              onClick={() => setSort(s.id)}
            >
              {s.label}
            </Pill>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <EmptyState
          variant={isFiltered ? "filtered" : "default"}
          message={
            isFiltered
              ? "Không tìm thấy trò chơi phù hợp."
              : "Chưa có trò chơi cho hạng mục này."
          }
          onReset={isFiltered ? reset : undefined}
        />
      ) : (
        <ul className="vertical-category-grid-grid" ref={gridRef}>
          {filtered.map((g) => (
            <li key={g.id} className="vertical-category-grid-cell">
              <Tile
                label={g.name}
                caption={g.provider}
                imageSrc={g.imageSrc}
                fill
                onClick={() => onTile(g)}
              />
            </li>
          ))}
          {Array.from({ length: fillerCount }, (_, i) => (
            <li key={`fill-${i}`} className="vertical-category-grid-cell">
              <ComingSoonTile />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

/* ============================================================================
 * ProviderGameGrid — provider tab strip + game grid. A provider `Tabs` strip
 * (scrolls @375 via the Scroller-backed Tabs) filters the game grid; the grid
 * is 3-col @375 → 6-col desktop. Each tile is an IMAGE SLOT (token-derived
 * gradient + game label, Part 5) awaiting art — no fabricated thumbnail.
 *
 * Guest vs member (auth-aware): a guest tapping a game tile opens the auth modal
 * (the FTD seam entry — openAuthModal via useRequireAuth.promptAuth); a member
 * tap launches the game (UI-only mock → routes to the vertical). Gating never
 * blocks browsing — only the launch.
 * ==========================================================================*/

"use client";

import { useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { GameTile, Provider } from "@/lib/types";
import { useRequireAuth } from "@/lib/auth/guard";
import { Tabs, Tile, ComingSoonTile, EmptyState, useGridCols, computeGridFill } from "@/ui";

export interface ProviderGameGridProps {
  providers: Provider[];
  games: GameTile[];
}

const ALL = "all";

export function ProviderGameGrid({ providers, games }: ProviderGameGridProps) {
  const { allowed, promptAuth } = useRequireAuth();
  const router = useRouter();
  const gridRef = useRef<HTMLDivElement>(null);
  const cols = useGridCols(gridRef);
  const [active, setActive] = useState(ALL);

  const tabItems = useMemo(
    () => [
      { id: ALL, label: "Tất cả" },
      ...providers.map((p) => ({ id: p.name, label: p.name })),
    ],
    [providers],
  );

  const filtered = useMemo(
    () => (active === ALL ? games : games.filter((g) => g.provider === active)),
    [active, games],
  );

  // ONLY the first tile is the 2×2 hero feature; EVERY other tile is a uniform
  // 164×205 fixed tile (no 2-wide strips) so all non-feature tiles in a row are
  // identical size. Precomputed so the row-fill math can count track-cells.
  const spans = useMemo(
    () => filtered.map((_, i) => (i === 0 ? "big" : "normal")),
    [filtered],
  ) as ("big" | "normal")[];

  // TOTAL occupied track-cells (colSpan × rowSpan summed over EVERY child), per
  // the LIVE breakpoint: the 2×2 hero takes 4 cells once the grid is ≥4-up
  // (row-span engages at 768) and 2 cells on the narrow 3-up ladder; a 2-wide
  // strip takes 2; a normal tile takes 1. computeGridFill then pads the grid so
  // it (a) completes its last partial row AND (b) fills to at least 2 full rows
  // — so a short tab (e.g. PG Soft with a few games) never leaves a large
  // dead void BELOW the first filler row; the whole remaining grid becomes a
  // run of premium "Sắp ra mắt" cards. With `auto-flow: row dense` the result
  // lands on a COMPLETE rectangle, no gap.
  const fillerCount = useMemo(() => {
    if (cols <= 0 || filtered.length === 0) return 0;
    const totalOccupiedCells = spans.reduce((sum, kind) => {
      if (kind === "big") return sum + (cols >= 4 ? 4 : 2); // 2×2 hero (or 2×1 @3-up)
      return sum + 1; // every other tile is a uniform 1×1
    }, 0);
    return computeGridFill(cols, totalOccupiedCells, 2);
  }, [cols, filtered.length, spans]);

  const onTile = (g: GameTile) => {
    if (!allowed) {
      // guest → auth modal (FTD seam entry). Browsing stays open; launch gates.
      promptAuth({ action: "none" });
      return;
    }
    // member: UI-only mock launch → route to the game's vertical surface.
    router.push(`/?game=${encodeURIComponent(g.id)}`);
  };

  return (
    <section className="home-provider-game-grid-section" aria-label="Trò chơi">
      <Tabs
        items={tabItems}
        active={active}
        onChange={setActive}
        label="Nhà cung cấp"
      />

      {filtered.length === 0 ? (
        <EmptyState
          message="Chưa có trò chơi cho nhà cung cấp này."
        />
      ) : (
        <div className="home-provider-game-grid-grid" ref={gridRef}>
          {filtered.map((g, i) => {
            const span = spans[i] === "big" ? "home-provider-game-grid-feature-big" : "";
            return (
              <div key={g.id} className={["home-provider-game-grid-cell", span].filter(Boolean).join(" ")}>
                <Tile
                  label={g.name}
                  caption={g.provider}
                  imageSrc={g.imageSrc}
                  fill
                  onClick={() => onTile(g)}
                />
              </div>
            );
          })}
          {/* pad the remaining grid (to a complete row AND at least 2 full rows)
           * with PREMIUM "Sắp ra mắt" coming-soon cards so a short tab shows NO
           * dead void below the first filler row, the grid lands on complete
           * rows, and the layout never shifts on a tab switch. Each
           * pad is a 1×1 cell (never a span) sized identically to a regular tile,
           * inert + aria-hidden — a gold-on-obsidian placeholder, not a dark void
           * or a cloned game. */}
          {Array.from({ length: fillerCount }, (_, i) => (
            <div key={`fill-${i}`} className="home-provider-game-grid-cell">
              <ComingSoonTile />
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

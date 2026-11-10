/* ============================================================================
 * CategoryPage — the vertical-landing composition (home game-grid;
 * [vertical] route). Composes, in authored order:
 *   CategoryBanner → provider tabs + filter/sort + game grid (CategoryGrid) →
 *   inline LiveOddsBoard (sports/esports only) → honest EmptyState (in grid).
 *
 * A plain composition (no own data fetch) — the route Server Component fetches
 * the typed payload (data.ts) and passes it here, so the truthful-only seam
 * stays at the server boundary. The shared shell (Header + CategoryRail/Sheet +
 * BottomTabBar) is mounted by the ROOT layout; this is only the content column.
 *
 * The live-odds board is placed ABOVE the grid for odds-bearing verticals
 * (the live match is the headline draw on a sports landing); for all other
 * verticals `odds` is null and the board is not rendered.
 * ==========================================================================*/

import type { CategoryPayload } from "./data";
import { CategoryBanner } from "./CategoryBanner";
import { CategoryGrid } from "./CategoryGrid";
import { LiveOddsBoard } from "./LiveOddsBoard";

export interface CategoryPageProps {
  payload: CategoryPayload;
}

export function CategoryPage({ payload }: CategoryPageProps) {
  const { vertical, providers, games, odds } = payload;

  return (
    <div className="vertical-category-page-page">
      <CategoryBanner vertical={vertical} />

      {/* sports/esports → inline truthful live-odds board (else null) */}
      {odds && <LiveOddsBoard odds={odds} />}

      <CategoryGrid
        verticalId={vertical.id}
        providers={providers}
        games={games}
      />
    </div>
  );
}

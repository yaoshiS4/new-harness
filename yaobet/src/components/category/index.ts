/* ============================================================================
 * Yaobet — category page-group barrel (home game-grid; [vertical] route). The
 * vertical-landing feature set owned by @dev-fe. The
 * [vertical] route + its loading/not-found import from "@/components/category".
 * ==========================================================================*/

export { CategoryBanner } from "./CategoryBanner";
export type { CategoryBannerProps } from "./CategoryBanner";

export { CategoryGrid } from "./CategoryGrid";
export type { CategoryGridProps } from "./CategoryGrid";

export { LiveOddsBoard } from "./LiveOddsBoard";
export type { LiveOddsBoardProps } from "./LiveOddsBoard";

export {
  resolveVertical,
  getCategoryPayload,
  ODDS_VERTICALS,
} from "./data";
export type { CategoryPayload } from "./data";

export { CategoryPage } from "./CategoryPage";
export type { CategoryPageProps } from "./CategoryPage";

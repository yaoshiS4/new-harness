/* ============================================================================
 * components/contribution — the game-contribution feature barrel (/cuoc-hop-le).
 * Named exports only. Static SSR core: PageIntro · RateTable · RateCell ·
 * TableFoot. Interactive + states: ContributionRoot · RateFilters · SearchField ·
 * Pager · ResultStatus · NotFoundResolver · FilterNotice · RateTableSkeleton.
 * Nothing is added to apps/web/src/ui/ this round.
 * ==========================================================================*/

export { PageIntro } from "./PageIntro";
export { RateTable, type RateRow } from "./RateTable";
export { RateCell } from "./RateCell";
export { TableFoot } from "./TableFoot";

export { ContributionRoot } from "./ContributionRoot";
export { ContributionTabs, type ContributionTab } from "./ContributionTabs";
export { RateFilters, type BucketValue } from "./RateFilters";
export { SearchField, foldQuery } from "./SearchField";
export { Pager } from "./Pager";
export { ResultStatus } from "./ResultStatus";
export { NotFoundResolver } from "./NotFoundResolver";
export { FilterNotice } from "./FilterNotice";
export { RateTableSkeleton } from "./RateTableSkeleton";

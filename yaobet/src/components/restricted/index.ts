/* ============================================================================
 * components/restricted — the bonus-restricted games list feature
 * (/game-han-che). Named exports only. Static SSR core: RestrictedIntro ·
 * RestrictedTable · RestrictedFoot. Interactive: RestrictedRoot ·
 * RestrictedFilters. Search / pager / empty-state primitives are reused from
 * components/contribution (SearchField, Pager, FilterNotice, foldQuery).
 * ==========================================================================*/

export { RestrictedIntro } from "./RestrictedIntro";
export { RestrictedRoot } from "./RestrictedRoot";
export { RestrictedFilters } from "./RestrictedFilters";
export { RestrictedTable, type RestrictedRow } from "./RestrictedTable";
export { RestrictedFoot } from "./RestrictedFoot";

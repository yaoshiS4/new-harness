/* ============================================================================
 * Yaobet — store feature barrel (§store). The points
 * store (cua-hang): points header + product grid (image SLOTS) + lazy redeem
 * dialog. Composes ui/* primitives over the token layer; auth-aware (guest →
 * openAuthModal on redeem). All figures are truthful fixtures.
 * ==========================================================================*/

export { PointsHeader } from "./PointsHeader";
export type { PointsHeaderProps } from "./PointsHeader";

export { ProductGrid } from "./ProductGrid";
export type { ProductGridProps } from "./ProductGrid";

export { RedeemDialog } from "./RedeemDialog";
export type { RedeemDialogProps } from "./RedeemDialog";

export { StoreTerms } from "./StoreTerms";

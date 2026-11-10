/* ============================================================================
 * Yaobet — referral / Đại lý feature barrel (§referral).
 * The affiliate dashboard (dai-ly): KPI header (real-or-omitted) + invite
 * tools (code/link/copy + poster SLOT) + agent tier ladder + commission panel
 * (honest EmptyState) + 4-step explainer. Composes ui/* over the token layer;
 * auth-aware (guest → openAuthModal). All figures truthful; no fabricated %.
 * ==========================================================================*/

export { ReferralKpiHeader } from "./ReferralKpiHeader";
export type { ReferralKpiHeaderProps } from "./ReferralKpiHeader";

export { InviteTools } from "./InviteTools";
export type { InviteToolsProps } from "./InviteTools";

export { CommissionPanel } from "./CommissionPanel";
export type { CommissionPanelProps } from "./CommissionPanel";

export { StepExplainer } from "./StepExplainer";

export { AgentTiers } from "./AgentTiers";
export type { AgentTiersProps } from "./AgentTiers";

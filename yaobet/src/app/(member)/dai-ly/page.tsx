/* ============================================================================
 * Yaobet — ĐẠI LÝ / AFFILIATE (route "/dai-ly") — §referral.
 * ----------------------------------------------------------------------------
 * A Server Component in the (member) route group: fetches the referral fixtures
 * server-side as typed values/§F envelopes (KPI is real-or-omitted) and passes
 * them to the affiliate-dashboard bands. Mounts inside the shared shell (root
 * <AppShell> → header + category nav + bottom tab bar) and the (member) layout.
 *
 * Bands: ReferralKpiHeader (real-or-omitted, Skeleton/ErrorState/absent per §F)
 * → AgentTiers (tier ladder, no fabricated %) → InviteTools (code/link/copy +
 * poster SLOT) → CommissionPanel (earnings, honest EmptyState) → StepExplainer.
 * Auth-aware: guests get honest prompts + openAuthModal; members see data.
 * ==========================================================================*/

import { getReferral, getReferralKpi, getCommissions } from "@/lib/mock";
import {
  ReferralKpiHeader,
  AgentTiers,
  InviteTools,
  CommissionPanel,
  StepExplainer,
} from "@/components/referral";

export const metadata = {
  title: "Đại lý — Yaobet",
};

export default async function AffiliatePage() {
  const [referral, kpi, commissions] = await Promise.all([
    getReferral(),
    getReferralKpi(),
    getCommissions(),
  ]);

  return (
    <div className="flex flex-col gap-space-5 min-w-[0]">
      {/* KPI — real-or-omitted (§F): Skeleton loading / ErrorState / absent */}
      <ReferralKpiHeader kpi={kpi} />

      {/* affiliate tier ladder — current level honest default (not yet an agent) */}
      <AgentTiers currentLevel={0} />

      {/* invite tools — code/link/copy + poster slot (auth-gated copy) */}
      <InviteTools referral={referral} />

      {/* earnings — honest EmptyState when none */}
      <CommissionPanel commissions={commissions} />

      {/* how it works — static truthful copy */}
      <StepExplainer />
    </div>
  );
}

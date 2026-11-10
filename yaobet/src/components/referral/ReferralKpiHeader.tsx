/* ============================================================================
 * ReferralKpiHeader — affiliate KPI header
 * Renders today's referred turnover + current commission as
 * REAL-OR-OMITTED figures, driven by the Envelope contract:
 *   loading → Skeleton (reserved footprint, no layout shift, never a "0")
 *   error   → ErrorState + retry (router.refresh re-issues the server fetch)
 *   absent  → the strip is OMITTED (no fabricated social-proof)
 *   live    → MoneyValue, equal-salience, never massaged
 * A client island so the error retry can re-issue the server fetch.
 * ==========================================================================*/

"use client";

import { useRouter } from "next/navigation";
import type { Envelope, ReferralKpi } from "@/lib/types";
import { vi } from "@/lib/i18n";
import { formatCount } from "@/lib/format";
import { Card, MoneyValue, Skeleton, ErrorState, Icon, type IconName } from "@/ui";

export interface ReferralKpiHeaderProps {
  kpi: Envelope<ReferralKpi>;
}

const t = vi.referral;

/* icon + label per KPI (shows an icon beside each stat). Shared by the
 * loading + live renders. Order matches 奖励总览: count · my-bets ·
 * friends-bets · forecast-commission. */
const STAT_META: { icon: IconName; label: string }[] = [
  { icon: "referral", label: t.kpiStat1 },
  { icon: "chip", label: t.kpiStat2 },
  { icon: "history", label: t.kpiStat3 },
  { icon: "cashback", label: t.kpiStat4 },
];

function StatHead({ icon, label }: { icon: IconName; label: string }) {
  return (
    <span className="flex items-center gap-space-1 min-w-[0]">
      <Icon name={icon} size={16} className="flex-[0_0_auto] text-brand-accent-fg" />
      <span className="text-t-sm text-text-mid leading-lh-tight min-w-[0]">{label}</span>
    </span>
  );
}

export function ReferralKpiHeader({ kpi }: ReferralKpiHeaderProps) {
  const router = useRouter();

  // absent → omit the strip entirely (truthful posture, never fabricated)
  if (kpi.status === "absent") return null;

  if (kpi.status === "error") {
    return (
      <Card variant="default" className="flex flex-col p-card-pad">
        <h2 className="promo-type-h2 text-text-hi mb-space-5">{t.kpiPanelTitle}</h2>
        <ErrorState
          title="Không tải được số liệu giới thiệu"
          onRetry={() => router.refresh()}
        />
      </Card>
    );
  }

  if (kpi.status === "loading") {
    return (
      <Card variant="default" className="@container flex flex-col p-card-pad">
        <h2 className="promo-type-h2 text-text-hi mb-space-5">{t.kpiPanelTitle}</h2>
        <div className="grid grid-cols-[1fr_1fr] @max-[33rem]:grid-cols-[minmax(0,1fr)] gap-y-space-5 gap-x-space-4">
          {STAT_META.map((m) => (
            <div key={m.label} className="flex flex-col gap-space-1 min-w-[0]">
              <StatHead icon={m.icon} label={m.label} />
              <Skeleton width="8ch" height="1.6em" />
            </div>
          ))}
        </div>
      </Card>
    );
  }

  // live — real figures only. #1 (本月截至今日有效新增) is a COUNT of valid new
  // referrals; #2–4 are money. Numbers near-WHITE (text-hi); gold is chrome only.
  const money = [
    kpi.value.myValidBetsToday,
    kpi.value.friendsTurnoverToday,
    kpi.value.forecastTomorrow,
  ];
  return (
    <Card variant="default" className="@container flex flex-col p-card-pad">
      <h2 className="promo-type-h2 text-text-hi mb-space-5">{t.kpiPanelTitle}</h2>
      <div className="grid grid-cols-[1fr_1fr] @max-[33rem]:grid-cols-[minmax(0,1fr)] gap-y-space-5 gap-x-space-4">
        {/* #1 — a COUNT (valid new referrals), rendered as a plain number, NOT ₫ */}
        <div className="flex flex-col gap-space-1 min-w-[0]">
          <StatHead icon={STAT_META[0].icon} label={STAT_META[0].label} />
          <span className="promo-type-num-lg text-text-hi">
            {formatCount(kpi.value.effectiveInvites)}
          </span>
        </div>
        {money.map((v, i) => (
          <div key={STAT_META[i + 1].label} className="flex flex-col gap-space-1 min-w-[0]">
            <StatHead icon={STAT_META[i + 1].icon} label={STAT_META[i + 1].label} />
            <MoneyValue value={v} kind="balance" size="num-lg" className="text-text-hi" />
          </div>
        ))}
      </div>
    </Card>
  );
}

/* Yaobet mock — referral. Honest empty commission state. */

import type { Commission, Envelope, Referral, ReferralKpi } from "../types";
import { DEMO_EMPTY, isoAgo, nowIso, simulateFetch } from "./helpers";

export async function getReferral(): Promise<Referral> {
  return simulateFetch<Referral>({
    code: "YB668812",
    link: "https://yaobet.example/r/YB668812",
    posterSrc: "/assets/placeholders/poster.svg",
  });
}

/** KPI header — real-or-omitted (RG). */
export async function getReferralKpi(): Promise<Envelope<ReferralKpi>> {
  if (DEMO_EMPTY) return simulateFetch({ status: "absent" });
  return simulateFetch<Envelope<ReferralKpi>>({
    status: "live",
    value: {
      effectiveInvites: 2,
      myValidBetsToday: { amount: 1_250_000, currency: "VND" },
      friendsTurnoverToday: { amount: 6_800_000, currency: "VND" },
      forecastTomorrow: { amount: 42_000, currency: "VND" },
    },
    sourcedAt: nowIso(),
    freshnessMs: 60_000,
  });
}

/** Commission list — honest EmptyState when none. */
export async function getCommissions(): Promise<Commission[]> {
  if (DEMO_EMPTY) return simulateFetch([]);
  return simulateFetch<Commission[]>([
    { id: "c1", referredName: "Trần***", turnover: { amount: 3_800_000, currency: "VND" }, commission: { amount: 88_000, currency: "VND" }, at: isoAgo(120) },
    { id: "c2", referredName: "Lê***", turnover: { amount: 3_000_000, currency: "VND" }, commission: { amount: 80_000, currency: "VND" }, at: isoAgo(680) },
  ]);
}

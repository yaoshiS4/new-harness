/* Yaobet mock — VIP ladder + progress + club perks.
 * Economics are Yaobet-canonical placeholders, NOT a competitor's 0.40–1.00% rates. */

import type {
  ClubTier,
  Envelope,
  Perk,
  VipProgress,
  VipTier,
} from "../types";
import { DEMO_EMPTY, nowIso, simulateFetch } from "./helpers";

const BADGE = "/assets/placeholders/tier-badge.svg";
const PERK_ART = "/assets/placeholders/perk.svg";

/* 5×N tiers (geometric interior per memory); rates are %-of-play placeholders. */
const VIP_TIERS: VipTier[] = [
  { id: "t0", name: "Tân thủ", level: 0, cashbackRate: 0.6, badgeSrc: BADGE, perks: ["Hoàn trả cơ bản"] },
  { id: "t1", name: "Đồng", level: 1, cashbackRate: 0.8, badgeSrc: BADGE, perks: ["Hoàn trả 0,8%", "Quà sinh nhật"] },
  { id: "t2", name: "Bạc", level: 2, cashbackRate: 1.0, badgeSrc: BADGE, perks: ["Hoàn trả 1,0%", "Rút nhanh"] },
  { id: "t3", name: "Bạch Kim", level: 3, cashbackRate: 1.2, badgeSrc: BADGE, perks: ["Hoàn trả 1,2%", "Quản lý riêng"] },
  { id: "t4", name: "Kim Cương", level: 4, cashbackRate: 1.5, badgeSrc: BADGE, perks: ["Hoàn trả 1,5%", "Sự kiện VIP"] },
];

const CLUB_TIERS: ClubTier[] = VIP_TIERS.map((t) => ({
  id: t.id,
  name: t.name,
  level: t.level,
}));

/* Toxic perks (hostess / loss-as-status / aspirational-luxury) are CUT. */
const PERKS: Perk[] = [
  { id: "p1", name: "Hoàn trả nâng cao", description: "Tỷ lệ hoàn trả cao hơn theo hạng.", illustrationSrc: PERK_ART, unlocksAtLevel: 1 },
  { id: "p2", name: "Rút tiền ưu tiên", description: "Xử lý rút tiền nhanh hơn.", illustrationSrc: PERK_ART, unlocksAtLevel: 2 },
  { id: "p3", name: "Quản lý tài khoản riêng", description: "Hỗ trợ chuyên biệt 24/7.", illustrationSrc: PERK_ART, unlocksAtLevel: 3 },
  { id: "p4", name: "Quà sinh nhật", description: "Ưu đãi dịp sinh nhật.", illustrationSrc: PERK_ART, unlocksAtLevel: 1 },
];

export async function getVipTiers(): Promise<VipTier[]> {
  return simulateFetch(VIP_TIERS);
}

export async function getClubTiers(): Promise<ClubTier[]> {
  return simulateFetch(CLUB_TIERS);
}

export async function getPerks(): Promise<Perk[]> {
  return simulateFetch(PERKS);
}

/** Turnover-to-next-tier — Live envelope; fill = real current/target. */
export async function getVipProgress(): Promise<Envelope<VipProgress>> {
  if (DEMO_EMPTY) return simulateFetch({ status: "absent" });
  return simulateFetch<Envelope<VipProgress>>({
    status: "live",
    value: {
      current: 18_600_000,
      target: 30_000_000,
      currentTierName: "Bạch Kim",
      nextTierName: "Kim Cương",
    },
    sourcedAt: nowIso(),
    freshnessMs: 60_000,
  });
}

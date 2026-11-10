/* ============================================================================
 * Yaobet — LUXURY VIP program — bilingual copy (VI source of truth / EN mirror).
 * ----------------------------------------------------------------------------
 * getVipCopy(lang) returns the resolved flat label bag every VIP component
 * reads. VI strings match the guideline verbatim; EN mirrors them. A lang state
 * lives in <VipProgram> so the VI/EN re-render is demonstrable.
 *
 * NOTE: the app's global catalog (src/lib/i18n.ts) also carries the VI VIP keys
 * under `vi.vip` (single-locale, per that file's contract). This module is the
 * BILINGUAL source the client island consumes; keep the two VI sets in sync.
 * ==========================================================================*/

import type { FaqItem, Lang } from "./types";

/** Every copy key → { vi, en }. VI is the source of truth. */
export const VIP_COPY = {
  // section titles
  allTiers: { vi: "Hành trình VIP", en: "Your VIP journey" },
  tierSectionTitle: { vi: "So sánh đặc quyền", en: "Compare privileges" },
  lvlSectionTitle: { vi: "Các cấp độ hội viên", en: "Membership levels" },
  tierMatrixTitle: { vi: "Đặc quyền theo hạng", en: "Privileges by tier" },
  faqTitle: { vi: "Câu hỏi thường gặp", en: "FAQ" },

  // labels / units
  needWager: { vi: "Cược tuần", en: "Weekly wager" },
  newTag: { vi: "MỚI", en: "NEW" },
  levelWord: { vi: "CẤP", en: "LEVEL" },
  statPoints: { vi: "Điểm", en: "Points" },
  youAreHere: { vi: "Bạn ở đây", en: "You are here" },
  progressLabel: {
    vi: "Tiến độ cược lên hạng sau",
    en: "Wager progress to next tier",
  },
  /** caption suffix: `${pointsToNextTier} ${pointsToNextSuffix} ${nextTierName}` */
  pointsToNextSuffix: { vi: "điểm để lên", en: "points to reach" },

  // rebate row labels
  rbGift: { vi: "Quà thăng cấp", en: "Promotion gift" },
  rbLive: { vi: "Hoàn cược Live", en: "Live rebate" },
  rbSports: { vi: "Hoàn cược Thể thao", en: "Sports rebate" },
  rbSlots: { vi: "Hoàn cược Nổ hũ", en: "Slots rebate" },
  rbTable: { vi: "Hoàn cược Game bàn", en: "Table rebate" },
  rbCashback: { vi: "Hoàn tiền tuần", en: "Weekly cashback" },

  // privilege labels
  bnPoints: { vi: "Đổi điểm ưu đãi", en: "Bonus point exchange" },
  bnShop: { vi: "Chọn quà cửa hàng", en: "Store gift selection" },
  bnEvent: { vi: "Ưu tiên sự kiện", en: "Event priority" },
  bnHost: { vi: "Quản lý VIP riêng", en: "Personal VIP host" },

  // tier names
  tBronze: { vi: "Đồng", en: "Bronze" },
  tSilver: { vi: "Bạc", en: "Silver" },
  tGold: { vi: "Vàng", en: "Gold" },
  tPlatinum: { vi: "Bạch Kim", en: "Platinum" },
  tDiamond: { vi: "Kim Cương", en: "Diamond" },

  // guest hero
  guestBadge: { vi: "Chương trình VIP", en: "VIP program" },
  guestH1: {
    vi: "Đặc quyền dành riêng cho hội viên VIP",
    en: "Privileges reserved for VIP members",
  },
  guestSub: {
    vi: "Chơi càng nhiều, hạng càng cao. Mở khóa hoàn tiền, quà thăng cấp và quản lý VIP riêng qua 5 hạng và 50 cấp độ.",
    en: "The more you play, the higher you climb. Unlock cashback, promotion gifts and a personal VIP host across 5 tiers and 50 levels.",
  },
  ctaRegister: { vi: "Đăng ký ngay", en: "Register now" },
  ctaLogin: { vi: "Đăng nhập", en: "Log in" },
} as const;

export type VipCopyKey = keyof typeof VIP_COPY;

/** Resolved flat label bag for one locale. */
export type VipCopy = Record<VipCopyKey, string>;

/** Resolve every copy key for a locale (VI default). */
export function getVipCopy(lang: Lang): VipCopy {
  const out = {} as VipCopy;
  (Object.keys(VIP_COPY) as VipCopyKey[]).forEach((k) => {
    out[k] = VIP_COPY[k][lang];
  });
  return out;
}

/** FAQ accordion (single-open). Answers are VIP-policy placeholder stubs. */
export const FAQ_ITEMS: FaqItem[] = [
  {
    q: { vi: "Làm sao để thăng hạng VIP?", en: "How do I rank up in VIP?" },
    a: {
      vi: "Cược hợp lệ tích lũy theo tuần sẽ nâng cấp độ và hạng của bạn. Khi đạt mức cược tuần yêu cầu của hạng kế tiếp, bạn được thăng hạng tự động.",
      en: "Valid weekly wagering raises your level and tier. When you reach the next tier's required weekly wager, you are promoted automatically.",
    },
  },
  {
    q: {
      vi: "Điểm thưởng được tính như thế nào?",
      en: "How are reward points calculated?",
    },
    a: {
      vi: "Điểm thưởng được cộng theo cược hợp lệ trên từng sản phẩm. Tỷ lệ quy đổi tăng dần theo cấp độ trong hạng của bạn.",
      en: "Points accrue from valid wagering on each product. The conversion rate scales up with your level within a tier.",
    },
  },
  {
    q: {
      vi: "Khi nào tôi nhận được hoàn tiền tuần?",
      en: "When do I receive weekly cashback?",
    },
    a: {
      vi: "Hoàn tiền tuần được kết toán vào đầu mỗi tuần dựa trên cược tuần trước và tỷ lệ theo hạng/cấp độ của bạn.",
      en: "Weekly cashback is settled at the start of each week based on the prior week's wagering and your tier/level rate.",
    },
  },
  {
    q: {
      vi: "Xuống hạng có mất đặc quyền không?",
      en: "Do I lose privileges if I drop a tier?",
    },
    a: {
      vi: "Nếu không duy trì mức cược tuần yêu cầu, bạn có thể xuống hạng và các đặc quyền tương ứng sẽ được điều chỉnh theo hạng mới.",
      en: "If you do not maintain the required weekly wager you may drop a tier, and the matching privileges adjust to your new tier.",
    },
  },
  {
    q: { vi: "Quản lý VIP riêng là gì?", en: "What is a personal VIP host?" },
    a: {
      vi: "Từ hạng Bạch Kim trở lên, bạn được phân bổ một quản lý VIP riêng hỗ trợ ưu tiên, ưu đãi cá nhân và xử lý yêu cầu nhanh.",
      en: "From Platinum upward you are assigned a personal VIP host for priority support, tailored offers and faster request handling.",
    },
  },
  {
    q: {
      vi: "Làm sao đổi điểm lấy ưu đãi?",
      en: "How do I redeem points for offers?",
    },
    a: {
      vi: "Vào cửa hàng điểm để đổi điểm lấy voucher tiền hoặc quà. Tỷ lệ đổi ưu đãi hơn khi hạng của bạn cao hơn.",
      en: "Visit the points store to redeem points for cash vouchers or gifts. Redemption rates improve at higher tiers.",
    },
  },
  {
    q: {
      vi: "Giới hạn rút tiền theo hạng ra sao?",
      en: "How do withdrawal limits vary by tier?",
    },
    a: {
      vi: "Hạng càng cao thì hạn mức và tốc độ rút càng ưu tiên. Chi tiết hạn mức theo hạng được hiển thị khi bạn thực hiện lệnh rút.",
      en: "Higher tiers receive higher limits and prioritized withdrawal speed. Exact per-tier limits are shown when you request a withdrawal.",
    },
  },
];

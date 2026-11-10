/* ============================================================================
 * VIP page-group copy — plain Vietnamese, single source for the vip/ feature
 * components (mirrors lib/i18n's posture; VIP-specific strings live here since
 * the shared catalog is owned elsewhere). Whale-aspiration but TRUTHFUL — no
 * fabricated numbers, no loss-as-status framing, equal-salience tone.
 * ==========================================================================*/

/** %-of-play rate as VN marketing copy: 1.5 → "Hoàn trả 1,5%". Avoids the
 *  EN decimal point; this is a tier marketing rate, never a ledger figure. */
function rate(pct: number): string {
  return `Hoàn trả ${pct.toString().replace(".", ",")}%`;
}

export const vipCopy = {
  // page-level
  pageTitle: "Hạng VIP",
  pageIntro:
    "Càng chơi càng được hoàn trả. Mọi hạng đều nhận hoàn trả theo % vòng cược — minh bạch, không điều kiện ẩn.",
  ladderHeading: "Bậc thang VIP",
  perksHeading: "Quyền lợi theo hạng",
  rulesHeading: "Quy tắc lên hạng & hoàn trả",
  privilegeHeading: "Bảng quyền lợi",
  detailLink: "Xem bậc thang chi tiết",
  backToVip: "Hạng VIP",

  // current-tier card
  currentTier: "Hạng hiện tại",
  turnoverToNext: "Vòng cược lên hạng kế tiếp",
  remainingPrefix: "Còn",
  remainingSuffix: "vòng cược để lên",
  atMaxTier: "Bạn đang ở hạng cao nhất — cảm ơn bạn.",
  progressError: "Không tải được tiến độ lên hạng",
  cashbackRate: rate,

  // guest
  guestTitle: "Tham gia hạng VIP Yaobet",
  guestCopy:
    "Đăng ký để bắt đầu tích lũy vòng cược và nhận hoàn trả theo hạng.",
  joinCta: "Đăng ký ngay",

  // ladder
  levelLabel: (lvl: number) => `Hạng ${lvl}`,
  currentBadge: "Hiện tại",
  lockedBadge: "Chưa mở",

  // privilege table
  colTier: "Hạng",
  colCashback: "Hoàn trả",
  colPerks: "Quyền lợi nổi bật",

  // perks
  perkUnlockAt: (lvl: number) => `Mở từ hạng ${lvl}`,
  perkLockedNote: "Lên hạng để mở quyền lợi này.",

  // rules
  rules: [
    {
      title: "Tích lũy bằng vòng cược",
      body: "Hạng VIP được tính theo tổng vòng cược thực tế. Số liệu lên hạng luôn lấy từ hệ thống — không có con số dựng sẵn.",
    },
    {
      title: "Hoàn trả theo % vòng cược",
      body: "Mỗi hạng có một tỷ lệ hoàn trả cố định, áp dụng trên vòng cược hợp lệ. Thắng hay thua đều được hoàn trả như nhau.",
    },
    {
      title: "Lên hạng tự động",
      body: "Khi đạt đủ vòng cược, hạng của bạn được nâng tự động. Quyền lợi hạng mới có hiệu lực ngay.",
    },
    {
      title: "Minh bạch & có trách nhiệm",
      body: "Chơi game chỉ dành cho người từ 18 tuổi. Hãy đặt giới hạn chi tiêu phù hợp; hỗ trợ luôn sẵn sàng.",
    },
  ],
} as const;

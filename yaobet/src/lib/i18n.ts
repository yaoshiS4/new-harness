/* ============================================================================
 * Yaobet — lib/i18n — single source of plain-VN labels.
 * Vietnamese-first, single-locale v1 (no locale segment). No component holds a
 * hardcoded VN string; they read from this catalog.
 * ==========================================================================*/

export const vi = {
  brand: "Yaobet",

  nav: {
    home: "Trang chủ",
    promo: "Khuyến mãi",
    deposit: "Nạp",
    wallet: "Ví",
    account: "Tài khoản",
    categories: "Danh mục",
  },

  auth: {
    register: "Đăng ký",
    login: "Đăng nhập",
    logout: "Đăng xuất",
    registerSuccess: "Đăng ký thành công",
    /* forgot-password flow (reset by email OR phone — no OTP, mock send). */
    forgot: "Quên mật khẩu?",
    forgotTitle: "Đặt lại mật khẩu",
    forgotPrompt:
      "Nhập email hoặc số điện thoại đã đăng ký để nhận liên kết đặt lại mật khẩu.",
    forgotSubmit: "Gửi liên kết",
    forgotSuccess: "Đã gửi hướng dẫn đặt lại mật khẩu. Vui lòng kiểm tra email hoặc tin nhắn.",
    backToLogin: "Quay lại đăng nhập",
    /** login identifier accepts phone OR username (icon swaps to match). */
    loginIdentifier: "Số điện thoại / Tên đăng nhập",
    resetIdentifier: "Email / Số điện thoại",
    /* NOTE: the "Mật khẩu / Mã đăng nhập" tab labels were removed with the OTP
     *       tab switcher (defect 3) — the modal is password-only. */
    /** brand-panel tagline + trust bullets (password-only modal, no OTP). */
    brandTag: "Nạp nhanh · Rút nhanh · Hoàn trả mỗi ngày",
    trust: {
      payout: "Rút tiền trong vài phút",
      cashback: "Hoàn trả mỗi ngày, không giới hạn",
      secure: "Bảo mật chuẩn ngân hàng",
      support: "Hỗ trợ 24/7",
    },
  },

  wallet: {
    title: "Ví tiền",
    balance: "Số dư",
    deposit: "Nạp",
    withdraw: "Rút",
    history: "Lịch sử",
    transfer: "Chuyển quỹ",
    zeroBalance: "Số dư: 0 ₫",
  },

  member: {
    cashback: "Hoàn trả",
    history: "Lịch sử",
    messages: "Tin nhắn",
    referral: "Giới thiệu",
    security: "Bảo mật",
    agentClub: "Đại lý/CLB",
    support: "Hỗ trợ",
    vip: "VIP",
    nextTier: "Hạng tiếp theo",
    profile: "Hồ sơ",
    bank: "Ngân hàng",
    crypto: "Ví tiền ảo",
    promo: "Khuyến mãi",
    wallet: "Ví của tôi",
    /* 12-tile hub grid — tile labels mapped to our real routes. */
    yield: "Sinh lời",
    sellCoin: "Bán xu",
    universalUpgrade: "Thăng hạng toàn dân",
    tutorial: "Hướng dẫn",
    honor: "Vinh danh",
  },

  account: {
    points: "Điểm",
    rebate: "Hoàn trả",
    /* ---- member-hub hero + action cards + progress bar (rebuild) ---------- */
    newMember: "Thành viên mới",
    getBadge: "Nhận huy hiệu",
    activated: "Đã kích hoạt",
    notActivated: "Chưa kích hoạt",
    pointsStore: "Cửa hàng điểm",
    taskCenter: "Trung tâm nhiệm vụ",
    myPoints: "Điểm của tôi",
    waitingUnlock: "Chờ mở khóa",
    progressPrefix: "Nạp tích lũy",
    progressSuffix: "để lên thẻ",
    progressUpdating: "Đang cập nhật",
    securityCenter: "Trung tâm an toàn",
    securityScore: "Điểm an toàn",
    securityScoreLow: "Thấp",
    securityScoreMedium: "Trung bình",
    securityScoreHigh: "Cao",
    tabVerify: "Thông tin xác minh",
    tabOther: "Khác",
    basicInfo: "Thông tin cơ bản",
    realName: "Họ tên thật",
    phone: "Số điện thoại",
    email: "Địa chỉ Email",
    fundPassword: "Mật khẩu rút tiền",
    dynamicCode: "Mã xác thực động",
    setupNow: "Thiết lập ngay",
    edit: "Chỉnh sửa",
    statusVerified: "Đã xác minh",
    statusPending: "Đang chờ",
    statusUnset: "Chưa thiết lập",
    changeLoginPassword: "Đổi mật khẩu đăng nhập",
    oldPassword: "Mật khẩu cũ",
    newPassword: "Mật khẩu mới",
    confirmPassword: "Xác nhận mật khẩu mới",
    save: "Lưu thay đổi",
    /* ---- section titles + subtitles (one section per member-menu item) ---- */
    profileTitle: "Hồ sơ cá nhân",
    profileSubtitle: "Thông tin cơ bản của tài khoản",
    bankSubtitle: "Liên kết thẻ ngân hàng để nạp và rút tiền",
    cryptoSubtitle: "Quản lý địa chỉ ví tiền điện tử để rút",
    avatar: "Ảnh đại diện",
    avatarChange: "Đổi ảnh đại diện",
    displayName: "Tên hiển thị",
    memberId: "Mã thành viên",
    /* ---- security section (đổi MK đăng nhập · MK rút tiền · 2FA) ---- */
    securitySubtitle: "Bảo vệ tài khoản bằng mật khẩu mạnh và xác thực động",
    loginPasswordSub: "Dùng để đăng nhập vào tài khoản",
    fundPasswordTitle: "Mật khẩu rút tiền",
    fundPasswordSub: "Yêu cầu khi rút tiền và đổi thông tin nhạy cảm",
    dynamicCodeTitle: "Mã xác thực động (2FA)",
    dynamicCodeSub: "Xác thực hai lớp bằng ứng dụng tạo mã",
    confirmFundPassword: "Xác nhận mật khẩu rút tiền",
    enable: "Bật",
    change: "Thay đổi",
    showPassword: "Hiện mật khẩu",
    hidePassword: "Ẩn mật khẩu",
    uiOnlyNotice: "Đây là bản giao diện mẫu — chưa kết nối hệ thống.",
    bankTitle: "Liên kết thẻ ngân hàng",
    bankAdd: "Thêm thẻ ngân hàng",
    bankEmpty: "Chưa liên kết thẻ ngân hàng",
    bankHolder: "Chủ thẻ",
    cryptoTitle: "Địa chỉ ví",
    cryptoAdd: "Thêm địa chỉ ví",
    cryptoEmpty: "Chưa thêm địa chỉ ví",
    cryptoNetwork: "Mạng",
    default: "Mặc định",
    setDefault: "Đặt mặc định",
    remove: "Gỡ liên kết",
  },

  state: {
    loading: "Đang tải…",
    empty: "Chưa có dữ liệu",
    noResults: "Không có kết quả",
    error: "Đã xảy ra lỗi",
    retry: "Thử lại",
    reset: "Đặt lại",
    stale: "Tạm dừng",
    ended: "Đã kết thúc",
    live: "TRỰC TIẾP",
  },

  /* Points store — card-face gates & micro-copy (plan §3; NEW store.* keys).
   * ITEM analog of the PRD points→cash mechanic: never imply reduced value —
   * only the POINT cost rises for an early redeem; the item/face is unchanged. */
  store: {
    title: "Cửa hàng điểm",
    /** points-required corner badge unit — rendered as `${n} điểm` (COUNT, never ₫). */
    pointsUnit: "điểm",
    /** filter tabs above the grid (client-side, filter by product.category). */
    tabAll: "Tất cả",
    tabVoucher: "Voucher tiền",
    tabProduct: "Sản phẩm",
    /** top-left card tag by family. */
    categoryVoucher: "Voucher tiền",
    categoryProduct: "Sản phẩm",
    /** withdrawal condition (info only): `{n}` = rolling multiplier to wager before withdrawing.
     *  VOUCHER cards only — physical products hide this line. */
    rollingLine: "Rút sau {n} vòng cược",
    /** GLOBAL redemption tally (social proof) — `{n}` = total redeems across all users. */
    redeemedCount: "Đã đổi {n} lượt",
    /** breaker reopen-time value for the paused dialog `{when}` slot (mock). */
    pausedReopen: "ít phút nữa",
    /** RUNNING-cooldown label — precedes the live countdown ("wait FOR full rate"). */
    fullRateAfter: "Thời gian chờ",
    /** cooldown ZERO-state label — only shown once the timer hits zero. */
    fullRateReady: "Có thể đổi ngay",
    /* terse card-face CTAs (verbose both-numbers button lives in the dialog). */
    ctaRedeem: "Đổi ngay",
    /** disabled CTA when cost > balance; `{short}` = formatCount(basePoints − balance). */
    ctaInsufficient: "Thiếu {short} điểm",
    ctaSoldOut: "Tạm hết hàng",
    /** single top-left tag on a sold-out card (ONE sold-out signal set). */
    soldOutTag: "Tạm hết",
    ctaLoginToRedeem: "Đăng nhập để đổi",
    /* TEMPORARY limit-lock (at_floor) card state — distinct from permanent Hết hàng.
     * The member hit the escalation cap; a clean wait returns them to base/100%. */
    ctaLimitReached: "Hết lượt đổi", // disabled CTA at the redemption cap; the cooldown chip stays visible
    /* dialog EARLY-state label for the passive-alternative countdown (frames the
     * timer as the ALTERNATIVE to claiming now, not a promise on this claim). */
    waitForBaseLabel: "Chờ hết giờ để về mức thường",
  },

  /* Claim dialog — VERBATIM from PRD §7.3.1. Critical: no string may
   * imply reduced value for an early claim (only more points, same item/face);
   * the escalated button shows BOTH points and face; every escalated/at-cap/
   * unlimited/insufficient state carries a "Chờ để được full rate" action. */
  claim: {
    fullRate:
      "Điểm cần dùng {points} · Bạn nhận {cash} · Tỷ lệ 100% ✓ · Thời gian chờ đã đặt lại hoàn toàn.",
    earlyEscalated:
      "⚠️ Bạn đang đổi sớm — trả nhiều điểm hơn cho cùng số tiền. Điểm {points} · Bạn nhận {cash} (không đổi) · Tỷ lệ {pct}% (bước {k}) · Thời gian chờ bắt đầu lại từ đầu.",
    atFloor:
      "⚠️ Tỷ lệ thấp nhất cho gói này — bạn đang trả nhiều điểm nhất cho số tiền này và sẽ không tăng thêm. Điểm {points} · Bạn nhận {cash} (không đổi). Đổi tiếp giữ nguyên mức này và đặt lại thời gian chờ. Chờ hết chu kỳ chờ để về {base_points} điểm.",
    unlimitedDeep:
      "⚠️ Gói này không giới hạn số lần đổi. Mỗi lần đổi sớm tốn nhiều điểm hơn cho cùng {cash} — không có mức sàn. Điểm hiện tại {points} · Bạn đã dùng {cycle_points} điểm trong chu kỳ này. Chờ hết thời gian để đặt lại về {base_points} điểm.",
    insufficient:
      "Bạn không đủ điểm cho lần đổi sớm (tăng cấp) này — nó tốn nhiều điểm hơn. Chờ về full rate để tốn ít điểm hơn ({base_points}).",
    paused:
      "Đổi thưởng tạm dừng và sẽ mở lại sau {when}. Tỷ lệ và thời gian chờ của bạn không thay đổi — vị trí của bạn giữ nguyên trong lúc tạm dừng.",
    resetConfirm:
      "Đã khôi phục full rate ✓ — bạn đã trả {points} điểm cho {cash}.",
    committedEscalated:
      "Đã đổi ✓ — {points} điểm → {cash}. Chờ hết thời gian chờ để lần sau được full rate (ít điểm hơn).",
    /* Buttons, controls (PRD §7.3.1). */
    btnFullRate: "Đổi {cash}",
    btnEscalated: "Đổi ngay ({points} điểm → {cash})",
    btnWait: "Chờ để được full rate",
    btnCancel: "Hủy",
    btnConfirm: "Xác nhận đổi",
    /* gold confirm label in the EARLY dialog (immediate-claim choice vs the wait). */
    btnEarlyConfirm: "Đổi ngay",
    /* ---- dialog copy (extracted from hardcoded JSX + the case-2 disclosure fix) ---- */
    /** modal title (base + early). */
    dialogTitle: "Xác nhận đổi quà",
    /** header muted label before the gold face-value amount. */
    valueLabel: "Trị giá",
    /** hero cost label in the dialog (same base + early). */
    costLabel: "Điểm cần dùng",
    /** small unit beside the hero numeral (styled independently of store.pointsUnit). */
    costUnit: "điểm",
    /** Line A — costs-more only (line B owns the reset fact; no overlap). */
    earlyWarn: "Bạn đang đổi sớm nên cần nhiều điểm hơn mức thường.",
    /** Line B — the explicit cooldown-RESET fact (the disclosure gap fix). */
    earlyResetWarn: "Đổi bây giờ sẽ đặt lại thời gian chờ về từ đầu.",
    /** honest base-cost comparison under the escalated hero numeral; `{points}` = `N điểm`. */
    /** quiet subline under the hero cost in the BASE dialog only. */
    baseSubline: "Mức thường · Tỷ lệ 100%",
    /* cost-card breakdown rows (under a divider). */
    rowBalanceNow: "Số dư hiện tại",
    rowBalanceAfter: "Sau khi đổi",
    rowRolling: "Điều kiện rút",
    /** rolling row value — `{n}` = rolling multiplier (voucher only). */
    rollingValue: "{n} vòng cược",
    /** amber caution callout in the EARLY dialog — names BOTH point figures + reset.
     *  `{time}` = live countdown to the running cooldown. */
    earlyCallout:
      "Thời gian chờ còn {time}. Nếu đổi ngay, bạn sẽ cần dùng nhiều điểm hơn và thời gian chờ bị đặt lại từ đầu.",
    /** neutral hint under the (red) hero cost when unaffordable (replaces blue banner). */
    insufficientHint: "Chờ về mức thường để cần ít điểm hơn.",
    /* success receipt (extracted from hardcoded JSX). */
    successTitle: "Đổi quà thành công",
    /** success subline — `{name}` = the redeemed product name (bold in JSX). */
    successSub: "{name} đã được thêm vào ví quà của bạn.",
    successPointsRow: "Điểm đã dùng",
    /** remaining-balance pill label after a successful redeem (number = balance − charged). */
    successBalanceLeft: "Số dư còn lại",
    btnClose: "Xong",
  },

  cashback: {
    title: "Hoàn trả",
    claimable: "Có thể nhận",
    accrued: "Đã tích lũy",
    claim: "Nhận hoàn trả",
    claimed: "Đã nhận hoàn trả",
    none: "Chưa có hoàn trả",
  },

  rg: {
    columnTitle: "Chơi game có trách nhiệm",
    ageLimit: "Chỉ dành cho người từ 18 tuổi trở lên",
    selfExclusion: "Tự loại trừ",
    hotline: "Đường dây nóng hỗ trợ",
    limits: "Giới hạn nạp / thua",
    terms: "Điều khoản & Điều kiện",
  },

  deposit: {
    title: "Nạp tiền",
    railBank: "Ngân hàng",
    railMomo: "Momo",
    railViettel: "ViettelPay",
    railCard: "Thẻ cào",
    amount: "Số tiền",
    iHaveTransferred: "Tôi đã chuyển",
    copyMemo: "Sao chép nội dung",
    pending: "Đang chờ xác nhận",
  },

  /* Exact header (tier-1 utility cluster + tier-2 category nav). */
  header: {
    vip: "VIP",
    promo: "Khuyến mãi",
    store: "Cửa hàng",
    glamor: "Phong cách",
    club: "CLB",
    collection: "Bộ sưu tập",
  },

  /* Notifications — the header bell's PANEL CHROME. The bell is the ONLY
   * notification surface: /thong-bao and its list are
   * deleted, so `seeAll` went with the destination it pointed at.
   *
   * The four `kind*` labels that used to sit here ("Khuyến mãi", "Nạp tiền",
   * "Sự kiện", "Hệ thống") are GONE with the legacy four-kind model. The
   * owner's eight type names live in feed.typeName below. */
  notifications: {
    title: "Thông báo",
    open: "Mở thông báo",
    unreadOne: "1 thông báo chưa đọc",
    unreadMany: "thông báo chưa đọc",
    allRead: "Đã đọc tất cả",
    markAllRead: "Đánh dấu đã đọc tất cả",
    /** Used by the message center (/tin-nhan) only. A NOTIFICATION has no
     *  per-row mark-read control any more: tapping the row marks it. */
    markRead: "Đánh dấu đã đọc",
    /** The row's one control. Prefixed onto the notification's own title
     *  so the accessible name says WHICH notification it removes. Delete is
     *  permanent and singular — there is deliberately no "xóa tất cả" here. */
    deleteOne: "Xóa thông báo",
    empty: "Chưa có thông báo",
    emptyHint: "Các thông báo mới sẽ xuất hiện tại đây.",
    /* relative-time units (plain VN) — used by relativeTime() for BOTH the
     * message center and the bell's row time ("18 phút trước"), which is the
     * form the owner approved. */
    justNow: "Vừa xong",
    minutesAgo: "phút trước",
    hoursAgo: "giờ trước",
    daysAgo: "ngày trước",

    /* ======================================================================
     * FEED — the eight types' copy. Read by the header
     * bell, which is the only notification surface.
     *
     * ⚠ PLACEHOLDER COPY — AWAITING THE OWNER'S FINAL WORDING.
     * What is below is plausible plain-VN written ONLY so the screen is
     * readable in review. None of it is approved copy; all of it is expected to
     * be replaced wholesale once the owner supplies theirs.
     *
     * `{amount}` `{status}` `{name}` `{date}` `{level}` are the value slots.
     * They are filled from the notification's own data — a component never
     * invents a value for one.
     * ==================================================================== */
    feed: {
      /** The row's TITLE line — one per type. It is also the leading icon's
       *  accessible name, and it is what `deleteOne` names so the delete
       *  control says which notification it removes. */
      typeName: {
        deposit: "Nạp tiền",
        withdrawal: "Rút tiền",
        rewardPoint: "Thưởng điểm",
        rewardMoney: "Thưởng tiền",
        rewardGiftCode: "Mã quà tặng",
        announcementEvent: "Sự kiện & khuyến mãi",
        announcementGeneral: "Thông báo chung",
        profileLevelUp: "Thăng hạng",
      },

      /** The row's DETAIL line — one short line per type, with value slots.
       *  `announcementGeneral` is deliberately over-length so the row's
       *  two-line clamp is visible in review. */
      content: {
        deposit: "Yêu cầu nạp {amount} của bạn {status}.",
        withdrawal: "Yêu cầu rút {amount} của bạn {status}.",
        rewardPoint: "Bạn vừa nhận {amount} điểm thưởng vào tài khoản.",
        rewardMoney: "Bạn vừa nhận {amount} tiền thưởng vào ví.",
        rewardGiftCode: "Bạn vừa nhận mã quà tặng {name}.",
        announcementEvent: "{name} bắt đầu từ {date}. Xem ngay để tham gia.",
        announcementGeneral:
          "Chúng tôi vừa cập nhật một số thông tin dành cho bạn, bao gồm thay đổi về thời gian hỗ trợ và một vài điều chỉnh nhỏ khác trong tài khoản của bạn.",
        profileLevelUp: "Bạn đã lên hạng {level}. Quyền lợi mới đã được mở.",
      },

      /** The `{status}` slot — a failed deposit and a rejected
       *  withdrawal are the SAME two types wearing a different status. */
      status: {
        depositSuccess: "đã được cộng vào ví",
        depositFailed: "không thành công",
        withdrawApproved: "đã được duyệt",
        withdrawRejected: "đã bị từ chối",
        withdrawPending: "đang được xử lý",
      },

      /** Screen-reader-only label for the unread dot. */
      unreadMark: "Chưa đọc",
    },
  },

  /* Member message center (/tin-nhan). Reuses notifications.markAllRead +
   * markRead + the relative-time units above (no duplication). */
  messages: {
    title: "Tin nhắn",
    /** subtitle unit; rendered as `${n} tin nhắn chưa đọc`. */
    subtitleUnread: "tin nhắn chưa đọc",
    subtitleAllRead: "Đã đọc tất cả",
    filterAll: "Tất cả",
    filterUnread: "Chưa đọc",
    filterRead: "Đã đọc",
    filterLabel: "Lọc tin nhắn",
    deleteAll: "Xóa tất cả",
    empty: "Chưa có tin nhắn",
    emptyHint: "Các tin nhắn mới sẽ xuất hiện tại đây.",
    guestPrompt: "Đăng nhập để xem tin nhắn của bạn.",
  },

  /* Referral / Giới thiệu page (/gioi-thieu) + shared Đại lý (/dai-ly) bands.
   * Plain-VN labels for the refer-page rebuild. Truthful-only: no fabricated
   * percent or reward figure lives here — only field/section labels. */
  referral: {
    pageHeading: "Giới thiệu bạn bè",
    kpiPanelTitle: "Tổng quan thưởng",
    /* 奖励总览 — exact labels (#1 is a COUNT of valid new referrals). */
    kpiStat1: "Giới thiệu hợp lệ trong tháng",
    kpiStat2: "Cược hợp lệ của tôi hôm nay",
    kpiStat3: "Bạn bè cược tích lũy hôm nay",
    kpiStat4: "Hoa hồng dự kiến ngày mai",
    invitePanelTitle: "Công cụ mời bạn bè",
    inviteCodeLabel: "Mã giới thiệu",
    inviteLinkLabel: "Liên kết giới thiệu",
    inviteCopy: "Sao chép",
    inviteCopied: "Đã sao chép",
    inviteSaveQr: "Lưu mã QR",
    invitePosterTitle: "Ảnh mời / mã QR",
    invitePosterHint: "Ảnh chia sẻ sẽ hiển thị tại đây khi sẵn sàng.",
    inviteGuestNote: "Đăng nhập để lấy mã giới thiệu của riêng bạn.",
    commissionPanelTitle: "Hoa hồng giới thiệu",
    commissionHeldLabel: "Hoa hồng hiện có",
    commissionDetailsLink: "Chi tiết hoạt động",
    commissionRowTurnover: "Doanh thu",
    commissionRowCommission: "Hoa hồng",
    commissionGuestPrompt: "Đăng nhập để xem hoa hồng giới thiệu của bạn.",
    commissionEmptyTitle: "Chưa có hoa hồng",
    commissionEmptyMessage:
      "Khi bạn bè được giới thiệu phát sinh doanh thu, hoa hồng sẽ hiển thị tại đây.",
    stepsHeading: "Cách hoạt động",
    stepsIntro:
      "Bạn chưa có bạn bè được giới thiệu — hãy mời bạn bè hoàn thành các bước để nhận thưởng.",
    step1: "Gửi mã QR hoặc liên kết mời",
    step2: "Bạn bè đăng ký và đăng nhập",
    step3: "Bạn bè tham gia chơi",
    step4: "Nhận hoa hồng theo điều khoản",
  },

  /* Luxury VIP program (/vip rebuild). VI source-of-truth copy keys. The
   * BILINGUAL source the client island actually consumes lives in
   * src/lib/vip/copy.ts (getVipCopy) since this catalog is single-locale VI;
   * keep the two VI sets in sync. */
  vip: {
    allTiers: "Hành trình VIP",
    tierSectionTitle: "So sánh đặc quyền",
    lvlSectionTitle: "Các cấp độ hội viên",
    tierMatrixTitle: "Đặc quyền theo hạng",
    faqTitle: "Câu hỏi thường gặp",
    needWager: "Cược tuần",
    newTag: "MỚI",
    levelWord: "CẤP",
    statPoints: "Điểm",
    youAreHere: "Bạn ở đây",
    progressLabel: "Tiến độ cược lên hạng sau",
    pointsToNextSuffix: "điểm để lên",
    rbGift: "Quà thăng cấp",
    rbLive: "Hoàn cược Live",
    rbSports: "Hoàn cược Thể thao",
    rbSlots: "Hoàn cược Nổ hũ",
    rbTable: "Hoàn cược Game bàn",
    rbCashback: "Hoàn tiền tuần",
    bnPoints: "Đổi điểm ưu đãi",
    bnShop: "Chọn quà cửa hàng",
    bnEvent: "Ưu tiên sự kiện",
    bnHost: "Quản lý VIP riêng",
    tBronze: "Đồng",
    tSilver: "Bạc",
    tGold: "Vàng",
    tPlatinum: "Bạch Kim",
    tDiamond: "Kim Cương",
    guestBadge: "Chương trình VIP",
    guestH1: "Đặc quyền dành riêng cho hội viên VIP",
    guestSub:
      "Chơi càng nhiều, hạng càng cao. Mở khóa hoàn tiền, quà thăng cấp và quản lý VIP riêng qua 5 hạng và 50 cấp độ.",
    ctaRegister: "Đăng ký ngay",
    ctaLogin: "Đăng nhập",
  },

  /* Exact footer — 3-column band + copyright. */
  footer: {
    partners: "Đối tác",
    aboutUs: "Về chúng tôi",
    brandCol: "Yaobet",
    appDownload: "Tải ứng dụng",
    glamor: "Phong cách Yaobet",
    about: "Giới thiệu",
    helpCenter: "Trung tâm trợ giúp",
    copyright: "Bản quyền © 2026 Tập đoàn Yaobet. Mọi quyền được bảo lưu.",
  },

  /* Game-contribution rate table (/cuoc-hop-le). LEGALLY-GATED published-rate
   * copy — every string here is a rate claim under the Vietnamese-counsel gate,
   * so it lives in this one catalog the whole app reads (no component holds a
   * hardcoded VN string). Copy fences (prototype §6 + fix-list): every rate
   * NUMERAL in the table is produced by lib/format formatPercent() (a ledger
   * value, never authored as copy), so the tier-label and zero-note keys below
   * spell their meaning in words. A literal `%` appears ONLY in the plain-language
   * EXPLAINER keys — `howToRead`, `settleNote`, `legendZero` (the mandated 0%-rate
   * settlement + read-the-table reassurance) and the rate-bucket filter labels; no
   * per-row rate cell is ever authored as copy. NO exclusion
   * framing (loại trừ / bị loại / bị cấm); NO range dash between two rate values
   * and NO `/` rate separator (the cell uses a middot `·`); `chưa` only where
   * the subject is OUR list / OUR matching; NO glyphs embedded in a string
   * (icons are aria-hidden <Icon> siblings). */
  contribution: {
    /* page furniture — the lifted lead + the "how to read" line (PageIntro).
     * lead frames WHAT the % is FOR (the valid-turnover that funds daily cashback
     * / VIP / weekly-monthly activity bonus); howToRead is the read-the-table key.
     * Neither says "hoa hồng" (that word = the referral payout, a different thing). */
    title: "Tỷ lệ tính cược theo trò chơi",
    lead:
      "Với những người chơi đang tham gia khuyến mãi hoàn trả hằng ngày: số tiền hoàn trả của bạn dựa trên phần cược được tính từ các game bạn chơi — mà mỗi game tính khác nhau. Ví dụ: game 100% tính toàn bộ tiền cược, game 20% chỉ tính 1/5, game 0% thì không tính. Xem bảng để biết game bạn chơi tính bao nhiêu.",
    howToRead:
      "0% nghĩa là không cộng cược, nhưng bạn vẫn chơi bình thường. Phần cược được tính còn dùng cho quyền lợi VIP và thưởng tuần/tháng. Dùng ô tìm kiếm hoặc bộ lọc để tra từng game.",

    /* the plain-language caveats paragraph (owner override 2026-08-11: the old
     * bordered "Cần biết" fence block is replaced by ONE muted paragraph). The
     * promo clause ends with `fencePromoLinkText`, which PageIntro renders as an
     * inline next/link to the Game-hạn-chế tab (/cuoc-hop-le?tab=han-che). */
    caveats:
      "Cấp VIP được xét theo cách riêng, không dựa trên tỷ lệ ở trang này. Khi tỷ lệ thay đổi, mức mới chỉ áp dụng cho cược đặt từ ngày hiệu lực. Mỗi khuyến mãi cũng có thể có điều kiện cược riêng — xem danh sách game hạn chế trong khuyến mãi.",
    /* Caveat — a game can carry a rate yet a specific bet still not count.
     * Read by TableFoot (single-sourced). */
    sportCaveat:
      "Một số cược không được tính dù trò chơi có tỷ lệ — ví dụ kèo thể thao dưới 1.50, cược bị huỷ hoặc rút sớm.",
    /** the exact phrase inside `caveats` rendered as an inline link to the
     * Game-hạn-chế tab (/cuoc-hop-le?tab=han-che) */
    fencePromoLinkText: "danh sách game hạn chế trong khuyến mãi",
    /* footer T&C / reference-surface link label */
    footerLink: "Tỷ lệ tính cược theo trò chơi",

    /* the two-tab strip on /cuoc-hop-le — the rate table + the restricted list
     * now live on ONE page (ContributionTabs). Labels are the tab captions. */
    tabsLabel: "Chọn bảng để xem",
    tabRate: "Tỷ lệ tính cược",
    tabRestricted: "Game hạn chế",

    /* search (built in a later wave; labels present now for the seam) */
    searchLabel: "Tìm tên trò chơi",
    searchPlaceholder: "Tìm tên trò chơi…",
    searchHint: "Gõ không dấu cũng được (vd: no hu)",
    searchClear: "Xóa nội dung tìm kiếm",
    searchOffline: "Tìm trò chơi cần có mạng.",

    /* filters — search is the PRIMARY control; category + provider + rate-bucket
     * are the three secondary filters that narrow the per-game table */
    filterCategoryLabel: "Lọc theo loại trò chơi",
    categoryFilterLabel: "Loại trò chơi",
    filterAll: "Tất cả",
    providerLabel: "Nhà cung cấp",
    providerAll: "Tất cả nhà cung cấp",
    /* contribution-% quick filter (segmented pills) */
    bucketGroupLabel: "Lọc theo tỷ lệ được tính",
    bucketAll: "Tất cả",
    bucketFull: "100%",
    bucketPartial: "Một phần",
    bucketNone: "Không tính",
    /* client-side numbered pager */
    pagerLabel: "Phân trang danh sách trò chơi",
    pagerPrev: "Trang trước",
    pagerNext: "Trang sau",
    pagerPage: "Trang {n}",
    pagerStatus: "Trang {page} / {total}",

    /* table columns */
    colGame: "Tên trò chơi",
    colRate: "Tỷ lệ được tính",
    colCategory: "Loại trò chơi",
    colProvider: "Nhà cung cấp",

    /* rate cell — every numeral is formatted by lib/format formatPercent(); the
     * copy below is the WORD scaffolding around it and carries no `%`. */
    /* per-tier group ordinal labels (the one --caution element in the cell) */
    tierOneLabel: "Hạng {n}",
    tierRangeLabel: "Hạng {a}–{b}",
    /* spoken enumeration of each tier group (srOnly; spells "phần trăm") */
    srTierOne: "{p} phần trăm ở hạng {n}",
    srTierRange: "{p} phần trăm từ hạng {a} đến hạng {b}",
    /* the local tier vocabulary's display names (CONTRIB_TIERS nameKey) */
    tierBronze: "Đồng",
    tierSilver: "Bạc",
    tierGold: "Vàng",
    tierPlatinum: "Bạch Kim",
    tierDiamond: "Kim Cương",

    /* table foot + freshness. */
    settleNote:
      "Ở mọi trò chơi trong bảng (kể cả mức 0%), tiền thắng và tiền thua vẫn được thanh toán bình thường.",
    updateStamp: "Cập nhật {date} · Phiên bản {version}",
    changeNotice: "Tỷ lệ có thể thay đổi, chúng tôi báo trước 30 ngày.",

    /* legend under the table — explains the one non-standard marker, a bare 0% */
    legendZero: "0% — vẫn chơi bình thường, chỉ là cược không cộng vào cược hợp lệ.",

    /* states */
    resultCount: "{n} trò chơi",
    notFoundTitle: "Chúng tôi chưa khớp được tên bạn gõ.",
    notFoundResolve:
      "Trò chơi nào cũng thuộc một loại, và loại nào cũng có tỷ lệ riêng. Chọn loại của bạn:",
    notFoundTip: "Mẹo: gõ ngắn hơn, không dấu — ví dụ \"no hu\".",
    notFoundHelp: "Vẫn chưa rõ? Xem Trợ giúp",
    /* empty (filters yield nothing, no search) — neutral, never "excluded" */
    emptyFilter: "Không có trò chơi nào khớp với bộ lọc đang chọn.",
    emptyFilterReset: "Xóa bộ lọc",
    errorTitle: "Không tải được danh sách trò chơi.",
    errorBody: "Tỷ lệ theo loại vẫn xem được trong bảng bên dưới.",
    retry: "Thử lại",

    /* a11y */
    loadingSr: "Đang tải bảng tỷ lệ",
    tableCaption:
      "Tỷ lệ cược được tính theo loại trò chơi và theo trò chơi. Cập nhật {date}, phiên bản {version}.",
    scrollerLabel: "Bảng tỷ lệ được tính — vuốt ngang để xem thêm cột",

    /* category names (also the chip labels, lobby order) */
    catSports: "Thể thao",
    catSlots: "Nổ hũ",
    catCasino: "Casino / Bàn chơi",
    catFishing: "Bắn cá",
    catCard: "Game bài đối kháng",
    catLottery: "Xổ số",
    catCockfight: "Đá gà",
    catArcade: "Game nhanh",
  },

  /* Bonus-restricted games list (/game-han-che). The ONE common, PUBLISHED list
   * of games restricted WHILE a player is clearing a promotion / gift-code bonus
   * (an anti-abuse rule). It is ORTHOGONAL to the game-contribution rate — a game
   * can count 100% AND be bonus-restricted, or 0% and not restricted — so this
   * page never shows a rate. Framed as "hạn chế trong khuyến mãi /
   * không được tính cho khuyến mãi" — NEVER cấm / loại trừ / bị loại; no đồng.
   * The `note` line is load-bearing: it prevents the "I can never play these"
   * confusion. Search + column + pager + filter labels REUSE the generic
   * contribution.* keys; only the page-specific copy lives in this namespace. */
  restricted: {
    metaTitle: "Game hạn chế trong khuyến mãi — Yaobet",
    title: "Game hạn chế trong khuyến mãi",
    lead:
      "Với những người chơi đang tham gia một khuyến mãi, sự kiện hoặc dùng mã quà tặng: một số game sẽ bị giới hạn để tránh lạm dụng. Trong thời gian nhận ưu đãi, cược ở các game này không được tính cho điều kiện của ưu đãi (ví dụ điều kiện vòng cược). Xong ưu đãi, bạn chơi lại bình thường.",
    noteLabel: "Lưu ý",
    note: "Danh sách này dùng chung cho các ưu đãi có quy định đó.",
    /* footer T&C / reference-surface link label (next to the rate-table link) */
    footerLink: "Game hạn chế khuyến mãi",
    /* a11y — table caption + scroller hint (names the rate column) */
    tableCaption:
      "Danh sách game hạn chế trong khuyến mãi, kèm tỷ lệ cược được tính theo từng trò chơi. Cập nhật {date}, phiên bản {version}.",
    scrollerLabel: "Danh sách game hạn chế — vuốt ngang để xem thêm cột",
    /* neutral states (never "excluded / banned") — the contribution notFound /
     * error copy names the rate, so this page carries its own rate-free wording */
    notFound:
      "Chúng tôi chưa khớp được tên bạn gõ. Hãy thử gõ ngắn hơn, không dấu — ví dụ \"baccarat\".",
    searchError:
      "Không tải được tìm kiếm. Danh sách vẫn xem được đầy đủ trong bảng bên dưới.",
  },
} as const;

export type Vi = typeof vi;

/* ----------------------------------------------------------------------------
 * t() — the tiny interpolation helper. This catalog is a frozen object
 * with no interpolation; the contribution surface needs {n} {date} {version}
 * {provider} {category} {a} {b} {p}. `t(template, vars)` substitutes every
 * `{token}` present in `vars`; a token with NO matching var is left UNTOUCHED
 * (never blanked, never a crash) so a missing value is visible, not silent.
 * --------------------------------------------------------------------------*/
export function t(
  template: string,
  vars: Record<string, string | number> = {},
): string {
  return template.replace(/\{(\w+)\}/g, (token, key: string) =>
    key in vars ? String(vars[key]) : token,
  );
}

/* ============================================================================
 * Yaobet mock — NOTIFICATIONS, the header bell's inventory.
 * ----------------------------------------------------------------------------
 * The ONE notification source in the app. The bell is the whole product
 * — /thong-bao and its paged list are deleted, so the bell
 * shows this feed ENTIRE and scrolls, rather than a "newest six" slice behind a
 * "see all" link that now has nowhere to go. One surface, one inventory.
 *
 * TRUTHFUL-ONLY. A row carries a TYPE and its VALUE SLOTS; every player-facing
 * word (title, detail line, status wording) is resolved from
 * vi.notifications.feed at render time. No copy lives in this file, so a fixture
 * cannot smuggle wording past i18n while the owner still owes us the real
 * strings.
 *
 * The amounts, names, dates and levels below are OBVIOUS DEMO VALUES chosen to
 * exercise the eight types — not measured figures, not a real player's ledger.
 * Money is put through lib/format so it renders the same way as everywhere else.
 *
 * Coverage the fixture is built to prove:
 *   • all eight types, each appearing several times;
 *   • THE FIRST SCREENFUL IS THE SAMPLE. All four categories, all eight types,
 *     both read states and both tap kinds appear inside the first ten rows —
 *     a reviewer must never have to scroll to see what the feature does;
 *   • a FAILED deposit, and a REJECTED / PENDING withdrawal, as the SAME two
 *     types wearing a different {status} — not extra types;
 *   • rows that lead somewhere and rows that lead nowhere, on more than one
 *     type, so where a row goes is visibly a property of the ROW, not of the
 *     category — and a "leads nowhere" row still marks itself read on tap;
 *   • read and unread INTERLEAVED in time order, so it is visible that reading
 *     a row never moves it;
 *   • two notifications at the same instant (the tie-order edge case);
 *   • 34 items — comfortably more than one panel height, so the panel's scroll
 *     is exercised in review.
 * ==========================================================================*/

import type { NotificationFeedItem } from "../types";
import { formatCount, formatVnd } from "../format";
import { DEMO_EMPTY, isoAgo, simulateFetch } from "./helpers";

/* Newest first — the accessor re-sorts defensively, but the fixture is authored
 * in the order it is meant to read so a reviewer can check it by eye. */
const FEED: NotificationFeedItem[] = [
  /* ---- batch 1 — THE SAMPLE PAGE ---------------------------------------
   * Every category (balance · reward · announcement · profile), every one of
   * the eight types, a gift code, a reward, a withdrawal and a deposit, four
   * unread among six read, and all three tap kinds. Nothing below this line is
   * needed to see the full shape of the feature.
   * --------------------------------------------------------------------- */
  {
    // Reward / Gift Code — up front, because it is what the owner asked to see.
    id: "f01",
    category: "reward",
    type: "rewardGiftCode",
    slots: { name: "TANG500K" },
    read: false,
    at: isoAgo(4),
    ctaHref: "/cua-hang",
  },
  {
    id: "f02",
    category: "balance",
    type: "deposit",
    slots: { amount: formatVnd(1_688_000), status: "depositSuccess" },
    read: false,
    at: isoAgo(6),
    ctaHref: "/vi-tien",
  },
  {
    // same instant as f02 — the "two arrive at the same moment" edge case, and
    // a FAILED deposit sitting beside a credited one on the same type
    id: "f03",
    category: "balance",
    type: "deposit",
    slots: { amount: formatVnd(500_000), status: "depositFailed" },
    read: false,
    at: isoAgo(6),
    ctaHref: "/vi-tien",
  },
  {
    id: "f04",
    category: "reward",
    type: "rewardMoney",
    slots: { amount: formatVnd(68_000) },
    read: true,
    at: isoAgo(42),
    url: "/vi-tien", // no CTA, URL only
  },
  {
    // withdrawal #1 of 3 in this batch — PENDING
    id: "f05",
    category: "balance",
    type: "withdrawal",
    slots: { amount: formatVnd(2_000_000), status: "withdrawPending" },
    read: false,
    at: isoAgo(95),
    url: "/vi-tien",
  },
  {
    id: "f06",
    category: "announcement",
    type: "announcementGeneral",
    slots: {},
    read: false,
    at: isoAgo(150),
    // neither a CTA nor a URL
  },
  {
    // withdrawal #2 — APPROVED
    id: "f07",
    category: "balance",
    type: "withdrawal",
    slots: { amount: formatVnd(5_000_000), status: "withdrawApproved" },
    read: true,
    at: isoAgo(210),
    ctaHref: "/vi-tien",
  },
  {
    id: "f08",
    category: "reward",
    type: "rewardPoint",
    slots: { amount: formatCount(1_500) },
    read: true,
    at: isoAgo(300),
    ctaHref: "/cua-hang",
  },
  {
    id: "f09",
    category: "announcement",
    type: "announcementEvent",
    slots: { name: "Vòng quay may mắn", date: "03/09" },
    read: false,
    at: isoAgo(420),
    ctaHref: "/khuyen-mai",
  },
  {
    id: "f10",
    category: "profile",
    type: "profileLevelUp",
    slots: { level: "VIP 3" },
    read: true,
    at: isoAgo(560),
    url: "/vip",
  },

  /* ---- batch 2 --------------------------------------------------------- */
  {
    // withdrawal #3 — REJECTED
    id: "f11",
    category: "balance",
    type: "withdrawal",
    slots: { amount: formatVnd(300_000), status: "withdrawRejected" },
    read: true,
    at: isoAgo(700),
    ctaHref: "/vi-tien",
  },
  {
    id: "f12",
    category: "reward",
    type: "rewardGiftCode",
    slots: { name: "CHAOMUNG88" },
    read: true,
    at: isoAgo(900),
    ctaHref: "/cua-hang",
  },
  {
    id: "f13",
    category: "balance",
    type: "deposit",
    slots: { amount: formatVnd(288_000), status: "depositSuccess" },
    read: true,
    at: isoAgo(1_100),
    url: "/vi-tien",
  },
  {
    id: "f14",
    category: "announcement",
    type: "announcementEvent",
    slots: { name: "Mini game đua top tuần", date: "28/08" },
    read: true,
    at: isoAgo(1_400),
    ctaHref: "/khuyen-mai",
  },
  {
    id: "f15",
    category: "reward",
    type: "rewardMoney",
    slots: { amount: formatVnd(188_000) },
    read: true,
    at: isoAgo(1_700),
    ctaHref: "/vi-tien",
  },
  {
    id: "f16",
    category: "balance",
    type: "deposit",
    slots: { amount: formatVnd(1_000_000), status: "depositFailed" },
    read: true,
    at: isoAgo(2_050),
    ctaHref: "/vi-tien",
  },
  {
    id: "f17",
    category: "reward",
    type: "rewardPoint",
    slots: { amount: formatCount(600) },
    read: true,
    at: isoAgo(2_400),
    url: "/cua-hang",
  },
  {
    id: "f18",
    category: "announcement",
    type: "announcementGeneral",
    slots: {},
    read: true,
    at: isoAgo(2_900),
  },
  {
    id: "f19",
    category: "balance",
    type: "withdrawal",
    slots: { amount: formatVnd(6_800_000), status: "withdrawApproved" },
    read: true,
    at: isoAgo(3_400),
    url: "/vi-tien",
  },
  {
    id: "f20",
    category: "profile",
    type: "profileLevelUp",
    slots: { level: "VIP 2" },
    read: true,
    at: isoAgo(4_100),
    url: "/vip",
  },

  /* ---- batch 3 --------------------------------------------------------- */
  {
    // a gift code with only a URL — the tap kind is a property of the ROW
    id: "f21",
    category: "reward",
    type: "rewardGiftCode",
    slots: { name: "LOCPHAT68" },
    read: true,
    at: isoAgo(4_900),
    url: "/cua-hang",
  },
  {
    id: "f22",
    category: "balance",
    type: "deposit",
    slots: { amount: formatVnd(168_000), status: "depositSuccess" },
    read: true,
    at: isoAgo(6_000),
    url: "/vi-tien",
  },
  {
    id: "f23",
    category: "balance",
    type: "withdrawal",
    slots: { amount: formatVnd(1_200_000), status: "withdrawPending" },
    read: true,
    at: isoAgo(7_200),
    url: "/vi-tien",
  },
  {
    id: "f24",
    category: "reward",
    type: "rewardMoney",
    slots: { amount: formatVnd(18_000) },
    read: true,
    at: isoAgo(8_600),
    url: "/vi-tien",
  },
  {
    id: "f25",
    category: "announcement",
    type: "announcementEvent",
    slots: { name: "Khuyến mãi nạp lần đầu", date: "20/08" },
    read: true,
    at: isoAgo(10_100),
    ctaHref: "/khuyen-mai",
  },
  {
    id: "f26",
    category: "reward",
    type: "rewardPoint",
    slots: { amount: formatCount(12_000) },
    read: true,
    at: isoAgo(11_800),
    ctaHref: "/cua-hang",
  },
  {
    id: "f27",
    category: "balance",
    type: "withdrawal",
    slots: { amount: formatVnd(450_000), status: "withdrawRejected" },
    read: true,
    at: isoAgo(13_500),
    url: "/vi-tien",
  },
  {
    id: "f28",
    category: "announcement",
    type: "announcementGeneral",
    slots: {},
    read: true,
    at: isoAgo(15_400),
  },
  {
    id: "f29",
    category: "balance",
    type: "deposit",
    slots: { amount: formatVnd(2_500_000), status: "depositSuccess" },
    read: true,
    at: isoAgo(17_600),
    ctaHref: "/vi-tien",
  },
  {
    id: "f30",
    category: "profile",
    type: "profileLevelUp",
    slots: { level: "VIP 1" },
    read: true,
    at: isoAgo(20_000),
    url: "/vip",
  },

  /* ---- batch 4 (short — then the list ends) ----------------------------- */
  {
    // a gift code with neither a CTA nor a URL (on a Reward type)
    id: "f31",
    category: "reward",
    type: "rewardGiftCode",
    slots: { name: "HELLO2026" },
    read: true,
    at: isoAgo(22_800),
  },
  {
    id: "f32",
    category: "announcement",
    type: "announcementEvent",
    slots: { name: "Giải đấu Slots tháng 8", date: "05/08" },
    read: true,
    at: isoAgo(25_900),
    url: "/khuyen-mai",
  },
  {
    id: "f33",
    category: "reward",
    type: "rewardMoney",
    slots: { amount: formatVnd(500_000) },
    read: true,
    at: isoAgo(29_400),
    ctaHref: "/vi-tien",
  },
  {
    id: "f34",
    category: "balance",
    type: "deposit",
    slots: { amount: formatVnd(88_000), status: "depositFailed" },
    read: true,
    at: isoAgo(33_000),
    url: "/vi-tien",
  },
];

/** Newest first. Ties keep their authored order, so two notifications at the
 *  same instant both appear, one above the other. */
const ORDERED: NotificationFeedItem[] = [...FEED].sort(
  (a, b) => new Date(b.at).getTime() - new Date(a.at).getTime(),
);

/**
 * The header bell's list — the WHOLE feed, newest first.
 *
 * It is not a slice: with /thong-bao deleted the bell is the only way to reach
 * a notification, so handing it six rows would put the rest out of the player's
 * reach entirely. The panel scrolls instead.
 *
 * The caller owns read state and deletion locally (UI-only / mock — no BE
 * write-back), so the unread count is simply what is left unread in this list.
 * The real-API migration replaces this body, not the call site.
 */
export async function getNotificationBell(): Promise<NotificationFeedItem[]> {
  return simulateFetch(DEMO_EMPTY ? [] : ORDERED);
}

/* Yaobet mock — lobby / verticals / home dynamic surfaces.
 *
 * RICH, TRUTHFUL-SHAPED DATA: the home must
 * read as lively — a big lucky-safe jackpot pool with an as-of stamp, a
 * live-ish leaderboard of masked names + amounts, and live odds rows with real
 * teams/odds + kickoff. These are mock 'SERVER' values delivered through the
 * §F Live envelopes (the Dynamic-data contract renders them); they are NOT
 * client-fabricated. DEMO_EMPTY still forces every band to its honest absent
 * state for the truthful-only QA pass.
 *
 * Lucky discipline: payout figures favour 6/8, avoid the digit 4. */

import type {
  Envelope,
  DeadlineEnvelope,
  Jackpot,
  LeaderRow,
  LiveMatch,
  SportsMatch,
  Vertical,
} from "../types";
import { DEMO_EMPTY, isoIn, liveMoney, nowIso, simulateFetch } from "./helpers";

/* Team crests: no per-club crest asset ships, but the user's sports key-art is
 * the closest real art (vs a grey slot) for the live-odds echo. */
const CREST = {
  football: "/assets/sports/saba-sports.png",
  kSports: "/assets/sports/k-sports.png",
} as const;

/* The 9-vertical taxonomy is a Yaobet IA decision, NOT a competitor
 * teardown. esports is a sub-tab under sports, not a peer category. */
const VERTICALS: Vertical[] = [
  { id: "casino", label: "Casino", iconId: "casino", href: "/?v=casino" },
  { id: "slots", label: "Nổ hũ", iconId: "slots", href: "/?v=slots" },
  { id: "sports", label: "Thể thao", iconId: "sports", href: "/?v=sports" },
  { id: "fishing", label: "Bắn cá", iconId: "fishing", href: "/?v=fishing" },
  { id: "card", label: "Game bài", iconId: "card", href: "/?v=card" },
  { id: "lottery", label: "Xổ số", iconId: "lottery", href: "/?v=lottery" },
  { id: "cockfight", label: "Đá gà", iconId: "cockfight", href: "/?v=cockfight" },
  { id: "table", label: "Bàn chơi", iconId: "table", href: "/?v=table" },
  { id: "arcade", label: "Game nhanh", iconId: "arcade", href: "/?v=arcade" },
];

export async function getVerticals(): Promise<Vertical[]> {
  return simulateFetch(VERTICALS);
}

/** Jackpot — live-bound only; no feed → absent (band omitted).
 *  Big lucky-safe pool (6/8-heavy, no digit-4) with a server as-of stamp. */
export async function getJackpot(): Promise<Envelope<Jackpot>> {
  if (DEMO_EMPTY) return simulateFetch({ status: "absent" });
  return simulateFetch<Envelope<Jackpot>>({
    status: "live",
    value: { pool: liveMoney(28_686_888_000), label: "Hũ vàng Yaobet" },
    sourcedAt: nowIso(),
    freshnessMs: 15_000,
  });
}

/** Next monthly member-day draw — the recurring 9th / 19th / 29th of the month.
 *  Returns the next such date (at 00:00 local) strictly after `from`, rolling
 *  into the following month when the 29th has passed. Real API supplies its own
 *  server-issued deadline; this fixture mirrors that contract. */
function nextMemberDayDraw(from: Date = new Date()): Date {
  const DRAW_DAYS = [9, 19, 29];
  for (let monthOffset = 0; monthOffset < 2; monthOffset++) {
    const y = from.getFullYear();
    const m = from.getMonth() + monthOffset;
    for (const d of DRAW_DAYS) {
      const candidate = new Date(y, m, d, 0, 0, 0, 0);
      if (candidate.getTime() > from.getTime()) return candidate;
    }
  }
  // unreachable in practice (the next month always has a 9th) — defensive.
  return new Date(from.getFullYear(), from.getMonth() + 1, DRAW_DAYS[0]);
}

/** Member-day countdown — server deadline; halts at deadlineAt (never loops).
 *  The deadline is the next monthly draw (9th / 19th / 29th). */
export async function getMemberDayCountdown(): Promise<DeadlineEnvelope> {
  if (DEMO_EMPTY) return simulateFetch({ status: "absent" });
  return simulateFetch<DeadlineEnvelope>({
    status: "live",
    value: undefined,
    deadlineAt: nextMemberDayDraw().toISOString(),
    sourcedAt: nowIso(),
    freshnessMs: 60_000,
  });
}

/** Leaderboard — opt-in; absent → omitted (never fabricated ranks).
 *  Lively masked-name board so the rail reads alive; amounts are
 *  net-framed, equal-salience MoneyValue (lucky-safe figures, no digit-4). */
export async function getLeaderboard(): Promise<Envelope<LeaderRow[]>> {
  if (DEMO_EMPTY) return simulateFetch({ status: "absent" });
  return simulateFetch<Envelope<LeaderRow[]>>({
    status: "live",
    value: [
      { rank: 1, displayName: "Minh***", amount: { amount: 868_000_000, currency: "VND" } },
      { rank: 2, displayName: "Hoa***", amount: { amount: 666_800_000, currency: "VND" } },
      { rank: 3, displayName: "Tuan***", amount: { amount: 286_600_000, currency: "VND" } },
      { rank: 5, displayName: "Phuc***", amount: { amount: 188_600_000, currency: "VND" } },
      { rank: 6, displayName: "Linh***", amount: { amount: 126_800_000, currency: "VND" } },
      { rank: 7, displayName: "Quang***", amount: { amount: 98_680_000, currency: "VND" } },
      { rank: 8, displayName: "Nga***", amount: { amount: 66_800_000, currency: "VND" } },
    ],
    sourcedAt: nowIso(),
    freshnessMs: 30_000,
  });
}

/** Sports match cards ("Thể thao" home card) — truthful-only.
 *  FOUR compact cards, one rendered UNDER each sports lifestyle card (SABA,
 *  K-Sports, football, esports). A mix of LIVE cards (TRỰC TIẾP + real score)
 *  and PRE cards (centre "VS", no score). Each carries the two markets:
 *  "Kèo chấp" (handicap, 3 cells) and "Kèo tài xỉu" (over/under, 3 cells). A
 *  null cell price renders a dash, never a fabricated number. No feed → absent
 *  → the cards are omitted. Lucky discipline: lines/labels favour 6/8 and avoid
 *  the digit 4. */
export async function getSportsMatches(): Promise<Envelope<SportsMatch[]>> {
  if (DEMO_EMPTY) return simulateFetch({ status: "absent" });
  return simulateFetch<Envelope<SportsMatch[]>>({
    status: "live",
    value: [
      // 1 — under SABA Sports (live)
      {
        id: "sm-live-1",
        league: "V-League 1",
        home: { name: "Hà Nội FC", crestSrc: CREST.football, flag: "🇻🇳" },
        away: { name: "Bình Dương", crestSrc: CREST.kSports, flag: "🇻🇳" },
        phase: "live",
        score: [1, 0],
        startsAt: isoIn(-18),
        markets: [
          {
            name: "Kèo chấp",
            cells: [
              { label: "Hà Nội", price: 1.86 },
              { label: "Hòa", price: 3.6 },
              { label: "Bình Dương", price: 3.8 },
            ],
          },
          {
            name: "Kèo tài xỉu",
            cells: [
              { label: "Tài 2.5", price: 1.96 },
              { label: "2.5", price: null },
              { label: "Xỉu 2.5", price: 1.86 },
            ],
          },
        ],
      },
      // 2 — under K-Sports (pre)
      {
        id: "sm-pre-1",
        league: "AFC Champions League",
        home: { name: "Công An Hà Nội", crestSrc: CREST.football, flag: "🇻🇳" },
        away: { name: "Buriram United", crestSrc: CREST.kSports, flag: "🇹🇭" },
        phase: "pre",
        startsAt: isoIn(168),
        markets: [
          {
            name: "Kèo chấp",
            cells: [
              { label: "CAHN", price: 2.06 },
              { label: "Hòa", price: 3.18 },
              { label: "Buriram", price: 3.68 },
            ],
          },
          {
            name: "Kèo tài xỉu",
            cells: [
              { label: "Tài 2.5", price: 1.88 },
              { label: "2.5", price: null },
              { label: "Xỉu 2.5", price: 1.96 },
            ],
          },
        ],
      },
      // 3 — under Kèo bóng đá trực tiếp / football (live)
      {
        id: "sm-live-2",
        league: "Ngoại Hạng Anh",
        home: { name: "Liverpool", crestSrc: CREST.football, flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
        away: { name: "Chelsea", crestSrc: CREST.football, flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
        phase: "live",
        score: [2, 1],
        startsAt: isoIn(-36),
        markets: [
          {
            name: "Kèo chấp",
            cells: [
              { label: "Liverpool", price: 1.68 },
              { label: "Hòa", price: 3.8 },
              { label: "Chelsea", price: 5.6 },
            ],
          },
          {
            name: "Kèo tài xỉu",
            cells: [
              { label: "Tài 3.5", price: 1.86 },
              { label: "3.5", price: null },
              { label: "Xỉu 3.5", price: 1.98 },
            ],
          },
        ],
      },
      // 4 — under Esports (pre)
      {
        id: "sm-pre-2",
        league: "LMHT — VCS",
        home: { name: "GAM Esports", crestSrc: CREST.kSports, flag: "🇻🇳" },
        away: { name: "Team Whales", crestSrc: CREST.kSports, flag: "🇻🇳" },
        phase: "pre",
        startsAt: isoIn(96),
        markets: [
          {
            name: "Kèo chấp",
            cells: [
              { label: "GAM", price: 1.66 },
              { label: "Hòa", price: null },
              { label: "Whales", price: 2.18 },
            ],
          },
          {
            name: "Kèo tài xỉu",
            cells: [
              { label: "Tài 2.5", price: 1.86 },
              { label: "2.5", price: null },
              { label: "Xỉu 2.5", price: 1.86 },
            ],
          },
        ],
      },
    ],
    sourcedAt: nowIso(),
    freshnessMs: 30_000,
  });
}

/** Live match — odds tick equal-salience; >10s stale → "tạm dừng".
 *  Real teams + decimal odds + a kickoff that is already underway (live). */
export async function getLiveMatch(): Promise<Envelope<LiveMatch>> {
  if (DEMO_EMPTY) return simulateFetch({ status: "absent" });
  return simulateFetch<Envelope<LiveMatch>>({
    status: "live",
    value: {
      id: "m1",
      home: { name: "Hà Nội FC", crestSrc: CREST.football },
      away: { name: "Bình Dương", crestSrc: CREST.kSports },
      phase: "live",
      homeOdds: { value: 1.86, direction: "up" },
      awayOdds: { value: 1.98, direction: "down" },
      startsAt: isoIn(-12),
    },
    sourcedAt: nowIso(),
    freshnessMs: 10_000,
  });
}

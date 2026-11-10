/* ============================================================================
 * Yaobet — domain types
 * ----------------------------------------------------------------------------
 * The money value types come FIRST: the `Money` primitive imports them and
 * cannot compile without them. The MoneyValue | LiveMoney union is the
 * mechanism that REPLACES the old hand-passed `truthful` boolean —
 * truthfulness is a property of the value's TYPE, not a prop a caller can lie
 * with. Then the dynamic-data envelopes, then the domain types.
 *
 * NOTE on import path: the spec places types at lib/mock/types.ts. The dev-fe
 * brief places them at lib/types.ts. This file is the canonical source; a
 * thin re-export lives at lib/mock/types.ts so both import paths resolve.
 * ==========================================================================*/

/* ----------------------------------------------------------------------------
 * 1. MONEY VALUE TYPES (FIRST — Money primitive depends on these)
 * --------------------------------------------------------------------------*/

/** A static, truthful ledger/marketing figure. Renders static — no tween,
 *  no data-truthful set by itself. */
export interface MoneyValue {
  amount: number;
  currency: "VND";
}

/** A server-bound figure that may animate toward a polled/settled value.
 *  The `Money` primitive sets data-truthful on it and enables the one-shot
 *  tween (reduced-motion → instant final). `sourcedAt` is the server clock. */
export interface LiveMoney {
  amount: number;
  currency: "VND";
  live: true;
  sourcedAt: string; // ISO, server clock
}

/** The union consumed by the `Money` primitive's `value` prop. */
export type AnyMoney = MoneyValue | LiveMoney;

/** Narrowing helper — true iff the value is a server-issued live figure. */
export function isLiveMoney(v: AnyMoney): v is LiveMoney {
  return (v as LiveMoney).live === true;
}

/* ----------------------------------------------------------------------------
 * 2. DYNAMIC-DATA ENVELOPES (the server→island truthful seam)
 * Every dynamic surface is fetched as one of these. The server's own
 * timestamp travels with the value so the island renders against server time,
 * never Date.now() guesses. No real source → `absent` → band OMITTED.
 * --------------------------------------------------------------------------*/

/** Server-issued freshness metadata. */
export interface AsOf {
  sourcedAt: string; // ISO, server clock
  freshnessMs: number; // server-declared validity window
}

/** A real, server-issued figure. */
export type Live<T> = { status: "live"; value: T } & AsOf;

/** Countdown-shaped: carries a server deadline; renders against deadlineAt. */
export type Deadline<T = void> = {
  status: "live";
  value: T;
  deadlineAt: string; // ISO, server clock
} & AsOf;

/** Fetch in flight → Skeleton. */
export type Loading = { status: "loading" };

/** Fetch failed → ErrorState + retry. */
export type Failed = { status: "error"; canRetry: true };

/** No real source → band OMITTED. */
export type Absent = { status: "absent" };

/** The full envelope union for a live figure surface. */
export type Envelope<T> = Live<T> | Loading | Failed | Absent;
/** The full envelope union for a deadline surface. */
export type DeadlineEnvelope<T = void> = Deadline<T> | Loading | Failed | Absent;

/* ----------------------------------------------------------------------------
 * 3. AUTH / SESSION
 * --------------------------------------------------------------------------*/

/** The three view-states the source actually exhibits. */
export type AuthState = "guest" | "level-0" | "tiered";

export interface User {
  id: string;
  displayName: string;
  /** masked/short id shown with a copy affordance */
  memberId: string;
  avatarSrc?: string;
  /** 0 = level-0 new member; 1..N = tiered */
  vipLevel: number;
  vipTierName: string;
  verified: boolean;
  unreadMessages: number;
}

export interface Session {
  state: AuthState;
  user: User | null;
}

/** Resume-intent carried across the FTD auth→deposit seam. */
export interface ResumeIntent {
  action: "deposit" | "withdraw" | "none";
  isFirstDeposit?: boolean;
}

/* ----------------------------------------------------------------------------
 * 4. WALLET
 * --------------------------------------------------------------------------*/

export interface ProductWallet {
  productId: string;
  productName: string;
  balance: MoneyValue;
}

export interface Wallet {
  /** main balance — fetched live for the TopBar chip / WalletBalanceHeader */
  balance: LiveMoney;
  products: ProductWallet[];
}

/* ----------------------------------------------------------------------------
 * 5. VIP / CLUB
 * --------------------------------------------------------------------------*/

export interface VipTier {
  id: string;
  name: string;
  level: number;
  /** %-of-play cashback rate, bound to VIP-BRD (NOT the source's 0.40–1.00%) */
  cashbackRate: number;
  badgeSrc: string; // asset slot
  perks: string[];
}

/** Turnover-to-next-tier — fetched as Live<VipProgress>. */
export interface VipProgress {
  current: number;
  target: number;
  currentTierName: string;
  nextTierName: string | null;
}

export interface Perk {
  id: string;
  name: string;
  description: string;
  illustrationSrc: string; // asset slot
  /** minimum club tier level that unlocks this perk */
  unlocksAtLevel: number;
}

export interface ClubTier {
  id: string;
  name: string;
  level: number;
}

/* ----------------------------------------------------------------------------
 * 6. PROMO / STORE / REFERRAL / GAMES / MEDALS
 * --------------------------------------------------------------------------*/

export interface Promo {
  id: string;
  title: string;
  category: string;
  imageSrc: string; // asset slot
  /** ISO deadline if the promo is time-boxed; null = evergreen (static card) */
  endsAt: string | null;
  href: string;
}

/* ----------------------------------------------------------------------------
 * PRODUCT (points store × restart-cooldown, STORE-cuahangdiem plan §1.1)
 * ----------------------------------------------------------------------------
 * Points → ITEM analog of the PRD's points → CASH restart-cooldown mechanic.
 * The house always pays the FULL item/face; only the POINT cost escalates on
 * an early (cooldown-running) claim. `rolling`/`stock` are owner catalog gates
 * rendered as card-face disabled states, NEVER as an in-dialog claim refusal
 * (§0.2). Derived point-cost/branch math lives in lib/store/escalation.ts.
 * --------------------------------------------------------------------------*/
export interface Product {
  // — identity / display —
  id: string;
  name: string;
  imageSrc: string; // asset slot
  /** catalog family — drives the top-left tag AND the rolling disclosure:
   *  'voucher' → shows the "Rút sau {n} vòng cược" card line + the "Điều kiện rút"
   *  dialog row; 'product' (physical goods) → hides BOTH (a phone has no rolling). */
  category: "voucher" | "product";

  // — owner catalog gates (NEW, not in PRD; card-face display gates only) —
  /** withdrawal condition, INFO only: rolling MULTIPLIER the user must wager AFTER
   *  redeeming before they can withdraw (e.g. 3 → "3 vòng cược"). Never a gate. */
  rollingRequired: number;
  /** total units minted for this item */
  stockTotal: number;
  /** units still available; 0 = sold out (item analog of PACKAGE_REMOVED).
   *  Drives the sold-out state ONLY — the remaining count is never displayed. */
  stockRemaining: number;
  /** GLOBAL count of successful redemptions of this item across ALL users
   *  (community social-proof; NOT this user's count). Display-only, guest-safe. */
  redeemedCount: number;

  // — PRD escalation config (§4.2 owner inputs) —
  /** P — the item's face value / reward, paid IN FULL every claim (for disclosure). */
  faceValue: MoneyValue;
  /** base points at full rate = points_1 = P/r0 (step-1 cost). Replaces flat pointsPrice. */
  basePoints: number;
  /** q — repeat fraction, 0 < q ≤ 1. Each early claim costs 1/q× more points. */
  repeatFraction: number;
  /** CD in minutes — fixed cooldown length; restarts the clock on any grant. */
  cooldownMinutes: number;
  /** M — max escalation steps; null = unlimited (no floor). */
  maxSteps: number | null;

  // — PER-USER runtime state (mock the server row; §5 gates) —
  // IMPORTANT: these are per-user fields — in a real API they MUST come from an
  // authenticated endpoint, never the public catalog, and are NEVER rendered on
  // the card face (the card is guest-safe). The dialog consumes them at claim.
  /** esc_step the NEXT claim would land on given the clock: 1 = full rate/BASE. */
  currentStep: number;
  /** ISO absolute expiry of the running cooldown; null = not running → next claim is BASE. */
  cooldownEndsAt: string | null;
  /** how many times THIS user has redeemed it (dialog cap logic only; never on the card). */
  userRedeemedCount: number;
  /** cumulative points burned this cycle — REQUIRED by claim.unlimited_deep. */
  cyclePointsBurned: number;
}

export interface Referral {
  code: string;
  link: string;
  posterSrc: string; // asset slot
}

export interface Commission {
  id: string;
  referredName: string;
  turnover: MoneyValue;
  commission: MoneyValue;
  at: string; // ISO
}

export interface ReferralKpi {
  effectiveInvites: number; // 本月截至今日有效新增 — valid new referrals this month to-date (COUNT, not money)
  myValidBetsToday: MoneyValue; // 我今日有效投注(CN) — my valid bets today
  friendsTurnoverToday: MoneyValue; // 今日好友累计投注(CN) — friends' cumulative bets today
  forecastTomorrow: MoneyValue; // 预计明天佣金(CN) — forecast commission tomorrow
}

export interface Vertical {
  id: string;
  label: string; // plain VN
  iconId: string; // resolves from the inline icon sprite
  href: string;
}

export interface GameTile {
  id: string;
  name: string;
  imageSrc: string; // asset slot
  provider: string;
}

export interface Provider {
  id: string;
  name: string;
  logoSrc: string; // asset slot
}

export interface Medal {
  id: string;
  family: string;
  name: string;
  /** neutral activity metric — NEVER loss-as-status (RG-reframed) */
  metricLabel: string;
  artSrc: string; // asset slot
  earned: boolean;
}

export interface Jackpot {
  /** live pool figure — only ever rendered from a Live envelope */
  pool: LiveMoney;
  label: string;
}

export interface LeaderRow {
  rank: number;
  displayName: string;
  /** net-framed, equal-salience figure */
  amount: MoneyValue;
}

export interface OddsValue {
  /** decimal odds, tabular */
  value: number;
  /** server tick direction for equal-salience flash; never color-only */
  direction: "up" | "down" | "flat";
}

export interface MatchTeam {
  name: string;
  crestSrc: string; // asset slot
  /** optional flag/crest emoji or short code shown beside the name (truthful;
   *  absent → no flag drawn, never a placeholder) */
  flag?: string;
}

export interface LiveMatch {
  id: string;
  home: MatchTeam;
  away: MatchTeam;
  /** "pre" | "live"; live shows a TRỰC TIẾP text label, never color-only */
  phase: "pre" | "live";
  homeOdds: OddsValue;
  awayOdds: OddsValue;
  startsAt: string; // ISO
}

/* ----------------------------------------------------------------------------
 * SPORTS MATCH CARD ("Thể thao" home card) — richer than LiveMatch.
 * Truthful-only: a card with no live feed renders the "VS" centre pill and
 * shows NO score; a live card shows the TRỰC TIẾP label + the real score.
 * Each card carries two odds markets (handicap + over/under), each a 3-cell
 * row, so the markup is fully data-bound (no fabricated price ever rendered).
 * --------------------------------------------------------------------------*/

/** One priced selection inside a market cell (cell = label over a price). */
export interface OddsCell {
  /** short cell label e.g. team short-name, "Hòa", "Tài", "Xỉu", or a line */
  label: string;
  /** decimal odds; null → cell shows a dash (suspended/absent), never a fake */
  price: number | null;
}

/** A 3-cell betting market ("Kèo chấp" handicap | "Kèo tài xỉu" O/U). */
export interface OddsMarket {
  /** market heading shown above the row */
  name: string;
  cells: [OddsCell, OddsCell, OddsCell];
}

export interface SportsMatch {
  id: string;
  /** competition / league name (truthful; e.g. "V-League 1") */
  league: string;
  home: MatchTeam;
  away: MatchTeam;
  /** "pre" → centre pill shows "VS"; "live" → TRỰC TIẾP label + score */
  phase: "pre" | "live";
  /** present ONLY when phase==="live" — the real server score [home, away] */
  score?: [number, number];
  /** ISO kickoff; rendered as a localized date/time label */
  startsAt: string;
  /** the two markets: [0] handicap "Kèo chấp", [1] over/under "Kèo tài xỉu" */
  markets: [OddsMarket, OddsMarket];
}

/* ----------------------------------------------------------------------------
 * 7. CASHBACK (the CORE 1% Hoàn trả surface) / RECORDS / MESSAGES
 * The three formerly-orphaned (member) routes' types.
 * --------------------------------------------------------------------------*/

export type CashbackStatus = "accrued" | "claimable" | "claiming" | "claimed" | "empty";

export interface RebateEntry {
  id: string;
  productName: string;
  /** turnover basis the %-of-play applies to */
  turnoverBasis: MoneyValue;
  /** %-of-play rate (truthful, bound to VIP-BRD) */
  rate: number;
  accrued: MoneyValue;
}

export interface Cashback {
  accrued: MoneyValue;
  claimable: MoneyValue;
  period: string; // e.g. "Tuần này"
  status: CashbackStatus;
  entries: RebateEntry[];
}

export type TransactionType =
  | "deposit"
  | "withdraw"
  | "win"
  | "loss"
  | "transfer"
  | "cashback";

export interface Transaction {
  id: string;
  type: TransactionType;
  /** signed amount; win/loss render on the luminance-matched pair, equal salience */
  amount: MoneyValue;
  at: string; // ISO
  note?: string;
}

export interface Message {
  id: string;
  subject: string;
  body: string;
  read: boolean;
  at: string; // ISO
}

/* ----------------------------------------------------------------------------
 * 7b. NOTIFICATIONS — the owner's model
 * ----------------------------------------------------------------------------
 * ONE model, ONE surface. The header bell IS the notification product —
 * `/thong-bao`, its list and its row are deleted. The bell carries the
 * owner's own inventory, not the legacy four kinds (promo · deposit · event ·
 * system), so that four-kind `Notification` type and its fixture are gone too.
 *
 * COPY IS NOT DATA. A feed item carries its TYPE and its VALUE SLOTS only; the
 * title and the detail line are resolved from vi.notifications.feed by type —
 * the owner writes the final wording later, and a fixture must not be able to
 * smuggle player-facing copy past i18n.
 * --------------------------------------------------------------------------*/

/** The owner's four category names (inventory, left column). Drives the row
 *  icon's TINT — one tint per category, eight glyphs inside it. */
export type NotificationCategory =
  | "balance" // Balance Update
  | "reward" // Reward
  | "announcement" // Announcement
  | "profile"; // Profile

/** The eight types. A failed deposit / rejected withdrawal is NOT a
 *  ninth type — it is `deposit`/`withdrawal` carrying a different status
 *  slot. */
export type NotificationFeedType =
  | "deposit" // Balance Update
  | "withdrawal" // Balance Update
  | "rewardPoint" // Reward
  | "rewardMoney" // Reward
  | "rewardGiftCode" // Reward
  | "announcementEvent" // Announcement — New Event / Promotion / Mini game
  | "announcementGeneral" // Announcement — General
  | "profileLevelUp"; // Profile — Level up / Rank up

/** The `{status}` slot. A KEY, not a phrase: the wording lives in
 *  vi.notifications.feed.status so the owner can rewrite all five at once. */
export type NotificationStatusKey =
  | "depositSuccess"
  | "depositFailed"
  | "withdrawApproved"
  | "withdrawRejected"
  | "withdrawPending";

/** The value slots a content line interpolates (inventory, right column). Which
 *  slots a type uses is fixed by the inventory; unused slots are absent. */
export interface NotificationSlots {
  /** already display-formatted through lib/format (money or point count) */
  amount?: string;
  status?: NotificationStatusKey;
  name?: string;
  date?: string;
  level?: string;
}

/** One row of the feed. A category ICON, a TITLE and a DETAIL line are
 *  MANDATORY on every type — all three are guaranteed structurally, by the
 *  type→icon and type→copy maps, rather than by a field a fixture could leave
 *  blank. Where the row LEADS is optional (the alternate: it may lead
 *  nowhere, and tapping it still marks it read). */
export interface NotificationFeedItem {
  id: string;
  category: NotificationCategory;
  type: NotificationFeedType;
  slots: NotificationSlots;
  read: boolean;
  at: string; // ISO, server clock — the list is ordered on this
  /** Preferred destination for a tap on the row. */
  ctaHref?: string;
  /** Fallback destination when there is no `ctaHref`. */
  url?: string;
}

/* ----------------------------------------------------------------------------
 * 8. SECURITY / KYC
 * --------------------------------------------------------------------------*/

export type SecurityFactorStatus = "unset" | "pending" | "verified" | "error";

export interface SecurityFactor {
  id: string;
  label: string;
  status: SecurityFactorStatus;
}

export interface SecurityIndex {
  factors: SecurityFactor[];
  /** 0–100, computed as verified-factor count × 20 */
  score: number;
}

/** A verification field row in the Security Center (Thông tin xác minh).
 *  `value` is the truthful display value when set (already masked at source);
 *  null = not yet provided → the row shows a "Thiết lập" affordance. */
export interface VerificationItem {
  id: "realName" | "phone" | "email" | "fundPassword" | "dynamicCode";
  /** masked/display value when set; null when unset */
  value: string | null;
  status: SecurityFactorStatus;
}

/** Member account summary surfaced on the left member rail
 *  (points + accrued rebate + masked balance). All truthful. */
export interface AccountSummary {
  points: number;
  rebate: MoneyValue;
}

/* ----------------------------------------------------------------------------
 * 8b. LINKED BANK CARDS / CRYPTO ADDRESSES (member-menu surfaces)
 * --------------------------------------------------------------------------*/

export interface BankCard {
  id: string;
  bankName: string;
  holderName: string;
  /** already masked at source: "•••• •••• 8866" */
  maskedNumber: string;
  isDefault: boolean;
}

export type CryptoNetwork = "TRC20" | "ERC20" | "BEP20";

export interface CryptoAddress {
  id: string;
  /** asset ticker, e.g. "USDT" */
  asset: string;
  network: CryptoNetwork;
  /** already masked at source: "TQ8r…9fAe" */
  maskedAddress: string;
  isDefault: boolean;
}

/* ----------------------------------------------------------------------------
 * 9. DEPOSIT
 * --------------------------------------------------------------------------*/

export type DepositRail = "bank" | "momo" | "viettelpay" | "card";

export interface DepositOffer {
  /** live, server-sourced first-deposit T&C — no hardcoded % */
  title: string;
  body: string;
  minToQualify: MoneyValue;
}

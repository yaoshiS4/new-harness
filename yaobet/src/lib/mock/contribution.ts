/* ============================================================================
 * Yaobet — game-contribution rate fixture (/cuoc-hop-le).
 * ----------------------------------------------------------------------------
 * PROVENANCE — these are OWNER-SIGNED CONTRIBUTION WEIGHTS (the "money weight":
 * the share of a stake counted toward hoàn trả + quyền lợi VIP + thưởng hoạt
 * động). They are NOT derived from, and this file NEVER imports, lib/vip/tiers.ts,
 * lib/vip/formulas.ts or lib/mock/cashback.ts (those publish a VIP rebate ladder
 * — a different number). One category edit here repropagates every row.
 *
 * DATA MODEL (the desync-proof shape): the RATE lives on the CATEGORY. A TITLE
 * carries NO rate — it resolves its rate via `categoryId → category.rate` at
 * render time, so a per-game rate can never be authored, drift or contradict its
 * category. The provider list is DERIVED from the catalogue, never authored.
 *
 * PAYLOAD HYGIENE (a fixture is the shape the real payload copies): no target
 * weight, tier ceiling, go-live state / date, climb weight, detector name,
 * threshold, per-row reason or đồng figure appears anywhere below. Category ids
 * match the lobby verticals (lib/mock/lobby.ts:34-42); "Casino / Bàn chơi"
 * merges the casino + table verticals under the stable id `casino`.
 * ==========================================================================*/

import { vi } from "../i18n";
import { simulateFetch } from "./helpers";

/* ---- tier vocabulary (LOCAL — never imported from lib/vip/tiers.ts) --------
 * The 5-tier ladder this page reasons over. The ORDINAL (Hạng 1..5) is the
 * array index + 1 — that is the only thing the rate cell renders. This
 * vocabulary is authored HERE so the page never reads a number, id or count
 * from the VIP ladder (which publishes a different figure — the rebate rate). */

/** One tier in the local ladder: a stable id + the i18n key of its display name. */
export interface ContribTier {
  /** stable id, ascending bronze→diamond (ordinal = index + 1) */
  id: string;
  /** vi.contribution[nameKey] — the tier's owner-signed VN name */
  nameKey: string;
}

export const CONTRIB_TIERS: ContribTier[] = [
  { id: "bronze", nameKey: "tierBronze" },
  { id: "silver", nameKey: "tierSilver" },
  { id: "gold", nameKey: "tierGold" },
  { id: "platinum", nameKey: "tierPlatinum" },
  { id: "diamond", nameKey: "tierDiamond" },
];

/* ---- types (colocated; re-exported through the mock barrel) ---------------- */

/** One explicit leg of a per-tier rate: a whole percent authored AT a tier. */
export interface TierRateLeg {
  tierId: string;
  p: number;
}

/** A category's current effective contribution rate:
 *   · flat    — one whole percent for every tier.
 *   · perTier — 1..5 legs, authored ASCENDING; a tier with no explicit leg
 *               inherits the nearest lower leg (and, below the lowest leg,
 *               that lowest leg). A `0` is a real value, never an absent state. */
export type CategoryRate =
  | { kind: "flat"; p: number }
  | { kind: "perTier"; rates: TierRateLeg[] };

/** One rendered tier group: a whole percent spanning ordinals `from`..`to`. */
export interface TierGroup {
  p: number;
  /** 1-based tier ordinal (Hạng n) */
  from: number;
  to: number;
}

/** Resolve a rate to one whole percent PER tier, in CONTRIB_TIERS order. A
 *  perTier leg fills its tier; a tier with no leg inherits the nearest lower
 *  leg. Below the lowest authored leg the lowest leg carries upward. Pure. */
export function resolveTierRates(
  rate: CategoryRate,
): { tierId: string; p: number }[] {
  if (rate.kind === "flat") {
    return CONTRIB_TIERS.map((tier) => ({ tierId: tier.id, p: rate.p }));
  }
  const byTier = new Map(rate.rates.map((leg) => [leg.tierId, leg.p] as const));
  // seed with the lowest authored leg so tiers below it inherit that value
  let carry = rate.rates[0]?.p ?? 0;
  return CONTRIB_TIERS.map((tier) => {
    if (byTier.has(tier.id)) carry = byTier.get(tier.id)!;
    return { tierId: tier.id, p: carry };
  });
}

/** Collapse adjacent equal-percent tiers into one ordinal group so equal
 *  neighbours render as a single `(Hạng a–b)` span. Pure. */
export function coalesceAdjacentEqual(
  resolved: { tierId: string; p: number }[],
): TierGroup[] {
  const groups: TierGroup[] = [];
  resolved.forEach((leg, i) => {
    const ordinal = i + 1;
    const last = groups[groups.length - 1];
    if (last && last.p === leg.p) last.to = ordinal;
    else groups.push({ p: leg.p, from: ordinal, to: ordinal });
  });
  return groups;
}

/** The three contribution-rate buckets the quick filter isolates:
 *   · "full"    — the category counts 100% (flat 100).
 *   · "partial" — a tiered rate, OR a flat value strictly between 0 and 100.
 *   · "none"    — the category counts 0% (flat 0). This is the isolate-0% bucket
 *                 the owner accepted as a tradeoff. A
 *                 per-tier rate is ALWAYS "partial" — the 0% bucket only catches
 *                 a flat-zero category (never a tiered one). */
export type RateBucket = "full" | "partial" | "none";

/** Classify a category rate into its quick-filter bucket. Pure; mirrors the
 *  owner rule verbatim (perTier → partial; flat 100 → full; flat 0 → none;
 *  any other flat → partial). */
export function rateBucket(rate: CategoryRate): RateBucket {
  if (rate.kind === "perTier") return "partial";
  if (rate.p === 100) return "full";
  if (rate.p === 0) return "none";
  return "partial";
}

/** Fold a string to the search-index form — the SAME rule as SearchField's
 *  foldQuery (đ→d BEFORE NFD, then strip tone marks / punctuation / collapse
 *  whitespace). Colocated here (a server module cannot import the "use client"
 *  SearchField) so the fixture can author every title's searchKey deterministically
 *  and byte-identically to what the client folds a query to. Pure, SSR-safe. */
function fold(input: string): string {
  return input
    .toLowerCase()
    .replace(/đ/g, "d")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/** A contribution category (a lobby vertical). The rate lives HERE. */
export interface ContributionCategory {
  /** stable id — matches a lobby vertical (lib/mock/lobby.ts) */
  id: string;
  /** VN display name — single-sourced from the i18n catalog */
  name: string;
  /** folded (lowercase, đ→d, no diacritics/punctuation) search key */
  searchKey: string;
  /** folded alias list — what a mass player actually types */
  aliases: string[];
  /** current effective money weight */
  rate: CategoryRate;
}

/** A catalogue title. Carries NO rate — resolves it via `categoryId`. */
export interface ContributionTitle {
  id: string;
  name: string;
  /** folded search key */
  searchKey: string;
  /** folded previous names — a renamed title stays findable by its old name */
  prevNames?: string[];
  provider: string;
  categoryId: string;
}

/** The rate config payload: a version, an effective timestamp, the 8 categories. */
export interface ContributionRates {
  version: string;
  /** ISO, to the minute (formatted for display at the table foot / caption) */
  effectiveAt: string;
  categories: ContributionCategory[];
}

/* ---- config: version + effective stamp ------------------------------------
 * A contribution rate is effective-FROM a fixed date (not a relative "N ago"
 * value); a constant keeps the SSR fully deterministic → byte-identical HTML.
 * Stored UTC and formatted with UTC getters downstream so the stamp never
 * shifts with the server timezone. */
const VERSION = "26.8";
const EFFECTIVE_AT = "2026-08-09T09:30:00.000Z";

/* ---- the 8 categories (authored in LOBBY / taxonomy order; the page renders
 * them in THIS order — never rate-descending) --------------------------------
 * sports = { flat, 100 } · slots = { perTier } 15% (Hạng 1–2) / 20% (Hạng 3–5)
 * · the other six = real { flat, 0 } (identical, undecorated — nothing
 * distinguishes a held category from a permanently 0% one). */
const CATEGORIES: ContributionCategory[] = [
  {
    id: "casino",
    name: vi.contribution.catCasino,
    searchKey: "casino ban choi",
    aliases: [
      "casino",
      "casino truc tuyen",
      "live casino",
      "bau cua",
      "xoc dia",
      "tai xiu",
      "baccarat",
      "bcr",
      "roulette",
      "sicbo",
      "ban choi",
    ],
    rate: { kind: "flat", p: 0 },
  },
  {
    id: "slots",
    name: vi.contribution.catSlots,
    searchKey: "no hu",
    aliases: ["no hu", "nohu", "slot", "slots", "hu", "jackpot"],
    // 15% at Hạng 1–2 (bronze inherits up to silver), 20% at Hạng 3–5 (gold
    // inherits up to platinum + diamond). Authored ascending; two legs only.
    rate: {
      kind: "perTier",
      rates: [
        { tierId: "bronze", p: 15 },
        { tierId: "gold", p: 20 },
      ],
    },
  },
  {
    id: "sports",
    name: vi.contribution.catSports,
    searchKey: "the thao",
    aliases: ["the thao", "bong da", "bd", "keo", "xien", "ca cuoc bong da"],
    rate: { kind: "flat", p: 100 },
  },
  {
    id: "fishing",
    name: vi.contribution.catFishing,
    searchKey: "ban ca",
    aliases: ["ban ca", "ca"],
    rate: { kind: "flat", p: 0 },
  },
  {
    id: "card",
    name: vi.contribution.catCard,
    searchKey: "game bai doi khang",
    aliases: ["game bai", "tien len", "tlmn", "sam loc", "phom", "ta la", "mau binh"],
    rate: { kind: "flat", p: 0 },
  },
  {
    id: "lottery",
    name: vi.contribution.catLottery,
    searchKey: "xo so",
    aliases: ["xo so", "lo de", "de", "so de", "xs"],
    rate: { kind: "flat", p: 0 },
  },
  {
    id: "cockfight",
    name: vi.contribution.catCockfight,
    searchKey: "da ga",
    aliases: ["da ga", "ga choi", "dag"],
    rate: { kind: "flat", p: 0 },
  },
  {
    id: "arcade",
    name: vi.contribution.catArcade,
    searchKey: "game nhanh",
    aliases: ["game nhanh", "mini game", "crash", "tai xiu nhanh"],
    rate: { kind: "flat", p: 0 },
  },
];

/* ---- catalogue: EVERY category now carries per-game rows (conventional table)
 * The default view is a flat, paginated per-game table across all 8 categories
 * (owner override). A game still
 * carries NO rate — it resolves via `categoryId → category.rate` at render time,
 * so this expanded catalogue never authors, drifts or contradicts a per-game
 * rate. ~240 titles total: 21 hand-authored EDGE titles (below) + a deterministic
 * index-derived generator (no Math.random → byte-identical SSR/CSR hydration).
 *
 * Edge coverage (kept verbatim): two titles share a display name under different
 * providers (so the provider column is load-bearing); one carries a previous
 * name; one has no diacritics; one is long enough to wrap the frozen column. */
const CURATED_TITLES: ContributionTitle[] = [
  /* Nổ hũ — categoryId "slots", providers JILI / PG Soft / JDB / Pragmatic Play */
  { id: "s-01", name: "Nổ Hũ Thần Tài", searchKey: "no hu than tai", provider: "JILI", categoryId: "slots" },
  { id: "s-02", name: "Nổ Hũ Thần Tài", searchKey: "no hu than tai", provider: "PG Soft", categoryId: "slots" }, // duplicate name, different provider
  { id: "s-03", name: "Nổ Hũ Long Vương", searchKey: "no hu long vuong", provider: "JILI", categoryId: "slots" },
  { id: "s-04", name: "Vua Săn Hũ", searchKey: "vua san hu", prevNames: ["no hu vang"], provider: "PG Soft", categoryId: "slots" }, // renamed (findable by old name)
  { id: "s-05", name: "Golden Fortune", searchKey: "golden fortune", provider: "JDB", categoryId: "slots" }, // no diacritics
  {
    id: "s-06",
    name: "Nổ Hũ Đại Gia Phát Tài Vô Cực Thịnh Vượng",
    searchKey: "no hu dai gia phat tai vo cuc thinh vuong",
    provider: "Pragmatic Play",
    categoryId: "slots",
  }, // long name — wraps the frozen column at 200% font
  { id: "s-07", name: "Nổ Hũ Rồng Vàng", searchKey: "no hu rong vang", provider: "JDB", categoryId: "slots" },
  { id: "s-08", name: "Nổ Hũ Kim Cương", searchKey: "no hu kim cuong", provider: "JILI", categoryId: "slots" },
  { id: "s-09", name: "Nổ Hũ Phát Lộc", searchKey: "no hu phat loc", provider: "PG Soft", categoryId: "slots" },
  { id: "s-10", name: "Nổ Hũ Tài Lộc", searchKey: "no hu tai loc", provider: "JDB", categoryId: "slots" },
  { id: "s-11", name: "Nổ Hũ May Mắn", searchKey: "no hu may man", provider: "Pragmatic Play", categoryId: "slots" },
  { id: "s-12", name: "Nổ Hũ Bạch Kim", searchKey: "no hu bach kim", provider: "JILI", categoryId: "slots" },
  { id: "s-13", name: "Nổ Hũ Hoàng Gia", searchKey: "no hu hoang gia", provider: "PG Soft", categoryId: "slots" },

  /* Thể thao — categoryId "sports", providers SABA / K-Sports / BTi */
  { id: "t-01", name: "Bóng đá", searchKey: "bong da", provider: "SABA", categoryId: "sports" },
  { id: "t-02", name: "Bóng rổ", searchKey: "bong ro", provider: "K-Sports", categoryId: "sports" },
  { id: "t-03", name: "Tennis", searchKey: "tennis", provider: "SABA", categoryId: "sports" }, // no diacritics
  { id: "t-04", name: "Cầu lông", searchKey: "cau long", provider: "BTi", categoryId: "sports" },
  { id: "t-05", name: "Bóng chuyền", searchKey: "bong chuyen", provider: "K-Sports", categoryId: "sports" },
  { id: "t-06", name: "Đua ngựa", searchKey: "dua ngua", provider: "SABA", categoryId: "sports" },
  { id: "t-07", name: "Esports LOL", searchKey: "esports lol", provider: "BTi", categoryId: "sports" },
  { id: "t-08", name: "Bóng đá ảo", searchKey: "bong da ao", provider: "K-Sports", categoryId: "sports" },
];

/* ---- deterministic per-category generator (payload-hygienic: no rate) --------
 * For each config, title i pairs prefixes[i % P] with suffixes[⌊i / P⌋ % S] — a
 * bijection over i ∈ [0, P·S), so with count ≤ P·S every generated name in a
 * category is unique — and assigns providers[i % N] round-robin. Purely
 * index-derived (NO Math.random) so the SSR and the client hydrate byte-identical
 * rows. searchKey is folded with the SAME rule the client folds a query to. */
interface GenConfig {
  categoryId: string;
  /** id stem → ids read `${idStem}-g{i}`; never collides with a curated id */
  idStem: string;
  count: number;
  prefixes: string[];
  suffixes: string[];
  /** realistic provider roster (existing set reused where it fits the vertical) */
  providers: string[];
}

const GEN_CONFIG: GenConfig[] = [
  {
    categoryId: "slots",
    idStem: "slot",
    count: 35,
    prefixes: ["Kho Báu", "Vua", "Thần", "Rồng", "Hoàng Kim", "Bảo Thạch", "Long Thần", "Phượng Hoàng"],
    suffixes: ["Vàng", "Bạc", "Kim Cương", "Phú Quý", "Thịnh Vượng", "Đế Vương", "Huyền Thoại", "Vô Cực"],
    providers: ["JILI", "PG Soft", "JDB", "Pragmatic Play"],
  },
  {
    categoryId: "sports",
    idStem: "sport",
    count: 20,
    prefixes: ["Bóng Đá", "Bóng Rổ", "Tennis", "Cầu Lông", "Bóng Chuyền", "Esports", "Đua Ngựa", "Bi-a"],
    suffixes: ["Trực Tuyến", "Châu Á", "Châu Âu", "Quốc Tế", "Cúp Quốc Gia", "Giao Hữu", "Vô Địch", "Hạng Nhất"],
    providers: ["SABA", "K-Sports", "BTi"],
  },
  {
    categoryId: "casino",
    idStem: "casino",
    count: 40,
    prefixes: ["Baccarat", "Rồng Hổ", "Xóc Đĩa", "Tài Xỉu", "Roulette", "Sicbo", "Bầu Cua", "Blackjack", "Poker Bàn", "Xì Dách"],
    suffixes: ["Kim Cương", "Hoàng Gia", "Thượng Hạng", "Đại Gia", "Ma Cao", "Thượng Hải", "VIP", "Trực Tuyến"],
    providers: ["Evolution", "WM Casino", "SA Gaming", "Dream Gaming"],
  },
  {
    categoryId: "fishing",
    idStem: "fish",
    count: 26,
    prefixes: ["Bắn Cá", "Săn Cá", "Vua Bắn Cá", "Đại Dương", "Thợ Săn"],
    suffixes: ["Thần Long", "Kim Cương", "Đại Chiến", "Huyền Thoại", "Vàng", "Sâu Thẳm", "Rồng Biển", "Bí Ẩn"],
    providers: ["JILI", "JDB", "CQ9"],
  },
  {
    categoryId: "card",
    idStem: "card",
    count: 30,
    prefixes: ["Tiến Lên", "Phỏm", "Sâm Lốc", "Mậu Binh", "Ba Cây", "Xì Tố", "Poker", "Tá Lả", "Liêng"],
    suffixes: ["Miền Nam", "Đổi Thưởng", "Trực Tuyến", "Đại Chiến", "Vô Địch", "Online"],
    providers: ["KingMaker", "JILI", "V8 Poker"],
  },
  {
    categoryId: "lottery",
    idStem: "lotto",
    count: 22,
    prefixes: ["Xổ Số", "Lô Đề", "Keno", "Xổ Số Nhanh", "Xổ Số Siêu Tốc"],
    suffixes: ["Miền Bắc", "Miền Nam", "Miền Trung", "Truyền Thống", "Điện Toán", "Thần Tài"],
    providers: ["TC Gaming", "GW", "SABA"],
  },
  {
    categoryId: "cockfight",
    idStem: "cock",
    count: 16,
    prefixes: ["Đá Gà", "Đá Gà Cựa Sắt", "Đá Gà Cựa Dao", "Đá Gà Trực Tiếp"],
    suffixes: ["Thomo", "Campuchia", "Philippines", "Bình Thuận", "Cao Lãnh"],
    providers: ["WS168", "SV388"],
  },
  {
    categoryId: "arcade",
    idStem: "arc",
    count: 30,
    prefixes: ["Tài Xỉu Nhanh", "Crash", "Xóc Đĩa Nhanh", "Vòng Quay", "Mini Poker", "Oẳn Tù Tì", "Cò Quay"],
    suffixes: ["May Mắn", "Siêu Tốc", "Vui Nhộn", "Bùng Nổ", "Tức Thì"],
    providers: ["Spribe", "JILI", "KingMaker", "PG Soft"],
  },
];

function generateTitles(cfg: GenConfig): ContributionTitle[] {
  const P = cfg.prefixes.length;
  const S = cfg.suffixes.length;
  const out: ContributionTitle[] = [];
  for (let i = 0; i < cfg.count; i++) {
    const name = `${cfg.prefixes[i % P]} ${cfg.suffixes[Math.floor(i / P) % S]}`;
    out.push({
      id: `${cfg.idStem}-g${i}`,
      name,
      searchKey: fold(name),
      provider: cfg.providers[i % cfg.providers.length],
      categoryId: cfg.categoryId,
    });
  }
  return out;
}

/** The full catalogue: the hand-authored edge titles first, then the generated
 *  spread — ~240 titles across all 8 categories. Row ORDER is imposed at render
 *  time (lobby → provider → title), so authoring order here is not significant. */
const CATALOGUE: ContributionTitle[] = [
  ...CURATED_TITLES,
  ...GEN_CONFIG.flatMap(generateTitles),
];

/* ---- accessors (async — mimic a server fetch; real API swaps the body) ----- */

/** The rate config: version + effective stamp + the 8 category rows. */
export async function getContributionRates(): Promise<ContributionRates> {
  return simulateFetch<ContributionRates>({
    version: VERSION,
    effectiveAt: EFFECTIVE_AT,
    categories: CATEGORIES,
  });
}

/** The flat catalogue of titles (rate resolves via categoryId at render time). */
export async function getContributionCatalogue(): Promise<ContributionTitle[]> {
  return simulateFetch<ContributionTitle[]>(CATALOGUE);
}

/** DERIVED provider list (seam for the search/filter wave) — a provider with no
 *  titles never appears. Never authored; always computed from the catalogue. */
export function deriveProviders(catalogue: ContributionTitle[]): string[] {
  return [...new Set(catalogue.map((ttl) => ttl.provider))].sort((a, b) =>
    a.localeCompare(b, "vi"),
  );
}

/* ---- bonus-restricted games (/game-han-che) --------------------------------
 * ONE common, PUBLISHED list: games restricted WHILE a player is clearing a
 * promotion / gift-code bonus (an anti-abuse rule — you cannot clear wagering on
 * these). The list is the SAME for every promotion; each promotion's T&C links
 * to it. It is ORTHOGONAL to the contribution RATE IN PRINCIPLE — nothing forces
 * a restricted game to count 0% — so membership is authored SEPARATELY here and
 * read ONLY by getRestrictedGames() (the /game-han-che page). The /cuoc-hop-le
 * rate table NEVER reads it, so the shared CATALOGUE stays byte-identical for the
 * rate page.
 *
 * CURATED INVARIANT: this published set is drawn ONLY from titles whose category
 * resolves to a flat 0% rate (Casino / Bàn chơi, Bắn cá, Game bài, Xổ số, Đá gà,
 * Game nhanh — NEVER Nổ hũ or Thể thao, whose categories are non-zero). The
 * restricted table now renders the resolved rate beside each title, so every row
 * reads a truthful, consistent "0%".
 *
 * Realistic anti-abuse targets: low-house-edge live-table games (Baccarat /
 * Blackjack / Roulette / Sicbo / Tài Xỉu / Rồng Hổ / Poker Bàn variants) plus a
 * few card + fast-game titles, spread across providers. Authored as a stable id
 * SET (never a mutation of the shared catalogue objects). */
export const BONUS_RESTRICTED_IDS: ReadonlySet<string> = new Set<string>([
  /* Casino live-table variants (categoryId "casino", flat 0%) — 26 */
  "casino-g0", "casino-g10", "casino-g20", "casino-g30", // Baccarat
  "casino-g1", "casino-g11", "casino-g21", "casino-g31", // Rồng Hổ
  "casino-g3", "casino-g13", "casino-g23", // Tài Xỉu
  "casino-g4", "casino-g14", "casino-g24", "casino-g34", // Roulette
  "casino-g5", "casino-g15", "casino-g25", // Sicbo
  "casino-g7", "casino-g17", "casino-g27", "casino-g37", // Blackjack
  "casino-g8", "casino-g18", "casino-g28", "casino-g38", // Poker Bàn
  /* Card + fast-game variants (categoryId "card" / "arcade", flat 0%) — 4 */
  "card-g0", "card-g6", // Game bài (Tiến Lên / Poker)
  "arc-g1", "arc-g4",   // Game nhanh (Crash / Mini Poker)
]);

/** One restricted-list row for /game-han-che. Carries its RESOLVED category
 *  display NAME and its RESOLVED category RATE — both looked up via `categoryId`,
 *  never authored on the title (the SAME desync-proof rule the rate table uses) —
 *  so the page needs no separate rate config. For every id in the published set
 *  the category resolves to a flat 0%, so the rate column reads a truthful "0%". */
export interface RestrictedGame {
  id: string;
  name: string;
  /** folded search key (same fold rule as the client SearchField) */
  searchKey: string;
  /** folded previous names — a renamed title stays findable by its old name */
  prevNames?: string[];
  provider: string;
  /** stable category id (drives the category filter) */
  categoryId: string;
  /** resolved category display name (the "Loại trò chơi" column) */
  category: string;
  /** resolved category contribution rate (the "Tỷ lệ được tính" column, via
   *  the SAME categoryId → category.rate lookup the rate table uses) */
  rate: CategoryRate;
}

/** The restricted-games payload: a version + effective stamp, the restricted
 *  titles ONLY (never the full catalogue), and the categories present among them
 *  in taxonomy order (the category filter's options). */
export interface RestrictedList {
  version: string;
  effectiveAt: string;
  games: RestrictedGame[];
  categories: { id: string; name: string }[];
}

/* The restricted list is its OWN published document (a separate version + stamp
 * from the rate config — the two are orthogonal). Stored UTC, formatted with UTC
 * getters downstream so the stamp never shifts with the server timezone. */
const RESTRICTED_VERSION = "26.8";
const RESTRICTED_EFFECTIVE_AT = "2026-08-08T10:00:00.000Z";

/** The published bonus-restricted list — the restricted titles ONLY, each
 *  enriched with its category display name, plus the categories present
 *  (taxonomy order) for the filter. Read ONLY by /game-han-che; the rate
 *  page/table never calls this and never renders a restricted marker. */
export async function getRestrictedGames(): Promise<RestrictedList> {
  const nameById = new Map(CATEGORIES.map((c) => [c.id, c.name] as const));
  const rateById = new Map(CATEGORIES.map((c) => [c.id, c.rate] as const));
  const games: RestrictedGame[] = CATALOGUE.filter((ttl) =>
    BONUS_RESTRICTED_IDS.has(ttl.id),
  ).map((ttl) => ({
    id: ttl.id,
    name: ttl.name,
    searchKey: ttl.searchKey,
    prevNames: ttl.prevNames,
    provider: ttl.provider,
    categoryId: ttl.categoryId,
    category: nameById.get(ttl.categoryId) ?? ttl.categoryId,
    // resolved the SAME way the rate table resolves it (categoryId → rate); a
    // missing category can only fall back to a real flat-0 (never a fake state).
    rate: rateById.get(ttl.categoryId) ?? { kind: "flat", p: 0 },
  }));
  const present = new Set(games.map((g) => g.categoryId));
  const categories = CATEGORIES.filter((c) => present.has(c.id)).map((c) => ({
    id: c.id,
    name: c.name,
  }));
  return simulateFetch<RestrictedList>({
    version: RESTRICTED_VERSION,
    effectiveAt: RESTRICTED_EFFECTIVE_AT,
    games,
    categories,
  });
}

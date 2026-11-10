/* ============================================================================
 * Yaobet — COLLECTION demo content: EPL player cards.
 * ----------------------------------------------------------------------------
 * DEMO CONTENT ONLY. Every number in this file is PROVISIONAL and exists so
 * the loop can be seen working. None of it is the shipped economy:
 *   · the pool model,
 *   · the universe size,
 *   · the rate-derivation source.
 * When those land, this file changes and NOTHING else does — that is the point
 * of the ports seam. Card art, names and club marks are CONTENT, swappable
 * with the theme.
 *
 * The three sets are the owner's: 8 same-team, 5 super defenders, 11 super
 * stars — on three overlapping axes, so one card serves several sets.
 * ==========================================================================*/

import type { Card, CollectionSet } from "../types";
import type { MoneyValue } from "@/lib/types";
import type { TierConfig } from "../math";

/**
 * Provisional tier shape. The RARE rate is the authored dial; the COMMON rate
 * is DERIVED from the pool so the published rates always sum to exactly 100%.
 *
 * This is not a style preference. A published rate that does not sum to 1 is a
 * false statement to the player: an earlier draft authored both rates by hand
 * and they summed to 163.5%, so the screen advertised 11.5% on a card whose
 * real probability was 7.03%. The whole trust posture of this feature rests on
 * the published table being the table the engine actually rolls, so the number
 * is computed from the pool rather than typed next to it.
 *
 * `DEMO_TIERS` is defined AFTER the card pool for this reason — see below.
 */
const RARE_RATE = 0.035;

export const SET_TEAM = "set-team";
export const SET_DEFENDERS = "set-defenders";
export const SET_STARS = "set-stars";

/**
 * DEMO reward values. `R` is an owner parameter and has NOT been set — these
 * exist only so the surface can render and be compared, and every screen that
 * shows them also carries the provisional label.
 *
 * They ascend with set size deliberately. Random ordering would make the
 * 5-card set — the fastest to finish — the most valuable, which is the
 * cheapest completion in the catalogue and therefore the one a ring farms.
 * Lucky-number amounts follow the house convention.
 */
const DEMO_REWARD = (amount: number): MoneyValue => ({ amount, currency: "VND" });

export const DEMO_SETS: CollectionSet[] = [
  {
    id: SET_DEFENDERS,
    name: "5 Trung vệ thép",
    classId: "light",
    size: 5,
    endsAt: null,
    reward: DEMO_REWARD(688_000),
  },
  {
    id: SET_TEAM,
    name: "Đội hình Liverpool",
    classId: "standard",
    size: 8,
    endsAt: null,
    reward: DEMO_REWARD(1_888_000),
  },
  {
    id: SET_STARS,
    name: "11 Siêu sao",
    classId: "wide",
    size: 11,
    endsAt: null,
    reward: DEMO_REWARD(6_888_000),
  },
];

interface Seed {
  id: string;
  name: string;
  club: string;
  pos: string;
  tier: "common" | "rare";
  sets: string[];
  /** filename stem under /assets/players. Absent = drawn art. */
  photo?: string;
}

/**
 * The card universe. Membership is a LIST of set ids, which is representable
 * under both readings of the pool model and commits to neither.
 */
const SEEDS: Seed[] = [
  // — Liverpool (8) — four carry supplied photography —
  { id: "salah", name: "Mohamed Salah", club: "Liverpool", pos: "Tiền đạo", tier: "rare", sets: [SET_TEAM, SET_STARS], photo: "salah" },
  { id: "vandijk", name: "Virgil van Dijk", club: "Liverpool", pos: "Trung vệ", tier: "rare", sets: [SET_TEAM, SET_DEFENDERS, SET_STARS], photo: "vandijk" },
  { id: "konate", name: "Ibrahima Konaté", club: "Liverpool", pos: "Trung vệ", tier: "common", sets: [SET_TEAM, SET_DEFENDERS], photo: "konate" },
  { id: "elliott", name: "Harvey Elliott", club: "Liverpool", pos: "Tiền vệ", tier: "common", sets: [SET_TEAM], photo: "elliott" },
  { id: "robertson", name: "Andrew Robertson", club: "Liverpool", pos: "Hậu vệ", tier: "common", sets: [SET_TEAM, SET_DEFENDERS] },
  { id: "szoboszlai", name: "Dominik Szoboszlai", club: "Liverpool", pos: "Tiền vệ", tier: "common", sets: [SET_TEAM] },
  { id: "macallister", name: "Alexis Mac Allister", club: "Liverpool", pos: "Tiền vệ", tier: "common", sets: [SET_TEAM] },
  { id: "gakpo", name: "Cody Gakpo", club: "Liverpool", pos: "Tiền đạo", tier: "common", sets: [SET_TEAM] },

  // — Defenders (5): van Dijk, Konaté and Robertson above, plus two Arsenal —
  { id: "gabriel", name: "Gabriel Magalhães", club: "Arsenal", pos: "Trung vệ", tier: "common", sets: [SET_DEFENDERS, SET_STARS], photo: "gabriel" },
  { id: "saliba", name: "William Saliba", club: "Arsenal", pos: "Trung vệ", tier: "common", sets: [SET_DEFENDERS] },

  // — Stars (11): salah, vandijk, gabriel above + eight —
  { id: "saka", name: "Bukayo Saka", club: "Arsenal", pos: "Tiền đạo", tier: "rare", sets: [SET_STARS], photo: "saka" },
  { id: "gyokeres", name: "Viktor Gyökeres", club: "Arsenal", pos: "Tiền đạo", tier: "rare", sets: [SET_STARS], photo: "gyokeres" },
  { id: "rice", name: "Declan Rice", club: "Arsenal", pos: "Tiền vệ", tier: "common", sets: [SET_STARS], photo: "rice" },
  { id: "dowman", name: "Max Dowman", club: "Arsenal", pos: "Tiền vệ", tier: "common", sets: [SET_STARS], photo: "dowman" },
  { id: "haaland", name: "Erling Haaland", club: "Man City", pos: "Tiền đạo", tier: "rare", sets: [SET_STARS] },
  { id: "palmer", name: "Cole Palmer", club: "Chelsea", pos: "Tiền vệ", tier: "common", sets: [SET_STARS] },
  { id: "son", name: "Son Heung-min", club: "Tottenham", pos: "Tiền đạo", tier: "common", sets: [SET_STARS] },
  { id: "bruno", name: "Bruno Fernandes", club: "Man Utd", pos: "Tiền vệ", tier: "common", sets: [SET_STARS] },
];

/**
 * Club accent, as SPACE-separated HSL components so it composes with modern
 * slash-alpha: `hsl(var(--accent) / 0.5)`. Comma syntax cannot take a slash
 * alpha and silently renders nothing — art is a SLOT, but it still has to
 * actually paint.
 */
export const CLUB_ACCENT: Record<string, string> = {
  Liverpool: "0 74% 46%",
  Arsenal: "355 80% 50%",
  "Man City": "199 72% 52%",
  Chelsea: "222 74% 48%",
  Tottenham: "220 22% 42%",
  "Man Utd": "4 76% 48%",
};

export interface DemoCard extends Card {
  club: string;
  position: string;
}

export const DEMO_CARDS: DemoCard[] = SEEDS.map((s) => ({
  id: s.id,
  name: s.name,
  /**
   * Art is a SLOT. A card with a photo renders it; a card without one renders
   * the drawn face. Both use the identical frame, badge and nameplate, so a
   * mixed pool reads as one set rather than as a bug — and swapping the theme
   * stays a data change.
   */
  artSrc: s.photo ? `/assets/players/${s.photo}.jpeg` : "",
  tierId: s.tier,
  setIds: s.sets,
  club: s.club,
  position: s.pos,
}));

/* ----------------------------------------------------------------------------
 * Derived tier table — the published rates ARE the rolled rates
 * --------------------------------------------------------------------------*/

const RARE_COUNT = DEMO_CARDS.filter((c) => c.tierId === "rare").length;
const COMMON_COUNT = DEMO_CARDS.length - RARE_COUNT;

/** Derived so the whole table sums to exactly 1. Never authored by hand. */
const COMMON_RATE = (1 - RARE_COUNT * RARE_RATE) / COMMON_COUNT;

export const DEMO_TIERS: TierConfig[] = [
  {
    id: "common",
    cardCount: COMMON_COUNT,
    drawRate: COMMON_RATE,
    shardYield: 5,
    craftPrice: 15,
  },
  {
    id: "rare",
    cardCount: RARE_COUNT,
    drawRate: RARE_RATE,
    shardYield: 15,
    craftPrice: 100,
  },
];

/**
 * The published table must sum to 1. If it ever does not, the screen is lying
 * to the player, so fail loudly in development rather than ship a false rate.
 */
const RATE_SUM = COMMON_COUNT * COMMON_RATE + RARE_COUNT * RARE_RATE;
if (process.env.NODE_ENV !== "production" && Math.abs(RATE_SUM - 1) > 1e-9) {
  throw new Error(
    `Published draw rates sum to ${(RATE_SUM * 100).toFixed(2)}%, not 100%. ` +
      `A published rate that does not sum to 1 misstates every card's chance.`,
  );
}

/**
 * The rare-card guarantee, in opens. PROVISIONAL, like every number here.
 *
 * It lives with the content and not in the adapter because it is PUBLISHED:
 * the terms state it and the engine honours it, and those two must be the same
 * constant. A backstop the player is told about but the engine does not run —
 * or runs at a different N — is a false statement with a prize attached, which
 * is the exact failure the derived rate table above exists to prevent.
 */
export const DEMO_PITY_BACKSTOP = 12;

/** Cards belonging to a set, in display order. */
export function cardsInSet(setId: string): DemoCard[] {
  return DEMO_CARDS.filter((c) => c.setIds.includes(setId));
}

/**
 * Per-card draw weights. These already sum to 1 by construction, so no
 * normalisation happens here — normalising after publishing is exactly how the
 * displayed rate and the rolled rate drift apart.
 */
export function drawTable(): { cardId: string; weight: number }[] {
  return DEMO_CARDS.map((c) => ({
    cardId: c.id,
    weight: c.tierId === "rare" ? RARE_RATE : COMMON_RATE,
  }));
}

/**
 * The TRUE probability of drawing `cardId` on an open allocated to `setId`.
 *
 * `drawTable()` publishes WHOLE-POOL weights, but the engine does not roll the
 * whole pool: it resolves an allocation first, then restricts the pool to that
 * set and renormalises (`adapters/fixtures.ts`). So a whole-pool weight is the
 * probability of NO open a player actually receives — publishing it repeats,
 * through allocation rather than through hand-authoring, precisely the defect
 * the derived table above was built to prevent.
 *
 * There is therefore no single "draw rate" per card. There is one rate per set
 * the card belongs to, and which one applies depends on the allocation. Any
 * surface that publishes a rate must publish it SET-SCOPED.
 *
 * Returns null when the card is not reachable from that set.
 */
export function rateInSet(cardId: string, setId: string): number | null {
  const card = cardById(cardId);
  if (!card?.setIds.includes(setId)) return null;

  const pool = drawTable().filter((t) => cardById(t.cardId)?.setIds.includes(setId));
  const total = pool.reduce((s, t) => s + t.weight, 0);
  if (total <= 0) return null;

  return (pool.find((t) => t.cardId === cardId)?.weight ?? 0) / total;
}

/** Every set the card can be drawn from, with the rate that applies there. */
export function ratesBySet(cardId: string): { setId: string; name: string; rate: number }[] {
  const card = cardById(cardId);
  if (!card) return [];
  return card.setIds.flatMap((setId) => {
    const rate = rateInSet(cardId, setId);
    const set = setById(setId);
    return rate === null || !set ? [] : [{ setId, name: set.name, rate }];
  });
}

/**
 * Same contract as the whole-pool check above, applied per set: the rates a
 * player is shown for one set must sum to exactly 1, or the screen misstates
 * every card in it. Fail loudly in development rather than ship a false rate.
 */
if (process.env.NODE_ENV !== "production") {
  for (const set of DEMO_SETS) {
    const sum = cardsInSet(set.id).reduce((s, c) => s + (rateInSet(c.id, set.id) ?? 0), 0);
    if (Math.abs(sum - 1) > 1e-9) {
      throw new Error(
        `Set "${set.id}" publishes rates summing to ${(sum * 100).toFixed(2)}%, not 100%.`,
      );
    }
  }
}

export function tierOf(cardId: string): TierConfig {
  const card = DEMO_CARDS.find((c) => c.id === cardId);
  return card?.tierId === "rare" ? DEMO_TIERS[1] : DEMO_TIERS[0];
}

export function cardById(cardId: string): DemoCard | undefined {
  return DEMO_CARDS.find((c) => c.id === cardId);
}

export function setById(setId: string): CollectionSet | undefined {
  return DEMO_SETS.find((s) => s.id === setId);
}

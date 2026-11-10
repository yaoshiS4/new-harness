/* ============================================================================
 * Yaobet mock — scratch-card outcome engine (Xổ số / "cào" instant-win).
 * ----------------------------------------------------------------------------
 * PURE LOGIC. No React, no DOM, no strings-for-display: every money value this
 * module returns is a NUMBER in VND. The UI formats through `formatVnd`.
 *
 * The one rule that shapes everything below: DECIDE THE OUTCOME FIRST, THEN
 * RENDER A FACE CONSISTENT WITH IT. We never draw twelve panels and hope the
 * result lands somewhere payable — that is how a mock ends up printing a
 * 20.000.000 ₫ match the campaign cannot honour. The outcome is chosen from a
 * published distribution, the matched rungs are drawn from the published rung
 * odds, and only then is a face built around them.
 *
 * FAIRNESS MATH (this is the whole engine in three lines):
 *   • rung odds  qᵢ ∝ 1/Pᵢ  — "flat mass". qᵢ·Pᵢ is then CONSTANT across the
 *     ladder, so every rung costs the house exactly the same and the top prize
 *     is automatically the rarest one. No hand-tuned odds table to drift.
 *   • expected matches per card = 0,48  ⇒  per-rung cost = 0,48 / Σ(1/Pᵢ)
 *     = 2.541,70 ₫ — the figure published in SCRATCH_ODDS.rungCost.
 *   • top rung: 0,48 · q₁₁ = 1/7.869 — SCRATCH_ODDS.topPrize, not a guess.
 *
 * SSR: an unseeded `Math.random()` at MODULE SCOPE would produce a different
 * card on the server than on the client and blow up hydration. Every random
 * draw in this file therefore happens INSIDE makeScratchCard(), never at import
 * time; pass a `seed` for a reproducible card (mulberry32).
 * ==========================================================================*/

import { formatVnd, isLuckySafe } from "../format";

/* ----------------------------------------------------------------------------
 * PUBLIC CONTRACT
 * --------------------------------------------------------------------------*/

export type ScratchOutcome = "lose" | "partial" | "win";

export type ScratchPanel = {
  /** two-digit face number, 0–99 */
  n: number;
  /** prize in VND printed under the panel */
  prize: number;
  /** true when n matches one of the four winning numbers */
  matched: boolean;
};

export type ScratchCard = {
  id: string;
  /** exactly 4 */
  winning: number[];
  /** exactly 12, laid out 4 across × 3 down */
  panels: ScratchPanel[];
  outcome: ScratchOutcome;
  /** sum of matched panel prizes; 0 when outcome === "lose" */
  totalPrize: number;
  /** consolation shown on every card including losers */
  dust: number;
};

/** The published ladder, low → high. 11 rungs, a 1-2-5 series. */
export const LADDER: number[] = [
  10_000, 20_000, 50_000, 100_000, 200_000, 500_000,
  1_000_000, 2_000_000, 5_000_000, 10_000_000, 20_000_000,
];

/** Published odds copy for the fairness strip. BARE VALUES in VN numerals — the
 *  strip supplies its own labels, so these must drop straight into a value slot.
 *  Derived, not decorative: see the FAIRNESS MATH banner. */
export const SCRATCH_ODDS: { hitRate: string; topPrize: string; rungCost: string } = {
  /** share of tickets that pay anything */
  hitRate: "38,7%",
  /** chance at the 20.000.000 ₫ top rung = 0,48 · q₁₁ */
  topPrize: "1 vé trong 7.869",
  /** house cost of ANY one rung — identical across the ladder, by construction */
  rungCost: "2.541,70 ₫",
};

/* ----------------------------------------------------------------------------
 * CARD GEOMETRY
 * --------------------------------------------------------------------------*/

/** 4 across × 3 down. */
const PANEL_COUNT = 12;
const WINNING_COUNT = 4;
/** Face numbers are two-digit: 0–99. */
const FACE_RANGE = 100;
/** Non-winning numbers the face may show. A SMALL pool on purpose: 12 panels
 *  drawn from 8 decoys guarantees repeats, which is what a real scratch face
 *  looks like — and a repeated number that happens to be a WINNING number pays
 *  on both panels (handled naturally: each panel carries its own prize). */
const DECOY_COUNT = 8;

/** "Low rung" = bottom four of the ladder. A single match here is a `partial`. */
const LOW_RUNGS = 4;
/** A single match at rung 5 (index 4 = 200.000 ₫) or above is already a `win`. */
const WIN_RUNG_FLOOR = 4;
/** "High rung" = top four (2M / 5M / 10M / 20M). A loser must show one of these
 *  unmatched — the near-miss IS the format; a face of nothing but 10.000 ₫ has
 *  no story. Decoration only: an unmatched panel never pays. */
const HIGH_RUNG_FLOOR = 7;

/* ----------------------------------------------------------------------------
 * ODDS — all derived from LADDER, no hand-written table anywhere.
 * --------------------------------------------------------------------------*/

const sum = (xs: readonly number[]): number => xs.reduce((a, b) => a + b, 0);

/** FLAT MASS: qᵢ ∝ 1/Pᵢ ⇒ qᵢ·Pᵢ is constant, so every rung costs the house the
 *  same and the top prize is the rarest purely as a consequence of its size. */
const RUNG_ODDS: number[] = (() => {
  const mass = LADDER.map((prize) => 1 / prize);
  const total = sum(mass);
  return mass.map((m) => m / total);
})();

/** Published share of cards that pay something (SCRATCH_ODDS.hitRate). */
const HIT_RATE = 0.387;

/** P(k matches | the card hits), for k = 1, 2, 3. E[k | hit] = 1,24, so
 *  E[k] = 0,387 × 1,24 = 0,48 matches per card — the constant that turns the
 *  flat-mass ladder into the published 2.541,70 ₫ cost per rung. */
const MATCH_COUNT_ODDS: number[] = [0.8, 0.16, 0.04];

/** Mass sitting on the bottom four rungs (≈ 0,953 — the ladder is bottom-heavy
 *  by construction, which is exactly why `partial` is the common hit). */
const LOW_MASS = sum(RUNG_ODDS.slice(0, LOW_RUNGS));

/* Outcome mix, read straight off the semantics:
 *   partial = one match AND that match is low  → HIT · P(k=1) · LOW_MASS
 *   win     = everything else that pays        → HIT − partial
 *   lose    = the rest                                                       */
const P_PARTIAL = HIT_RATE * MATCH_COUNT_ODDS[0] * LOW_MASS;
const P_WIN = HIT_RATE - P_PARTIAL;
const P_LOSE = 1 - HIT_RATE;

const OUTCOMES: ScratchOutcome[] = ["lose", "partial", "win"];
const OUTCOME_ODDS: number[] = [P_LOSE, P_PARTIAL, P_WIN];

/** Inside a win: [single high-rung match, two matches, three matches]. Keeping
 *  these as absolute per-card probabilities (rather than re-normalised guesses)
 *  is what preserves the per-rung marginal 0,48 · qᵢ under `force`-free play. */
const WIN_BRANCH_ODDS: number[] = [
  HIT_RATE * MATCH_COUNT_ODDS[0] * (1 - LOW_MASS),
  HIT_RATE * MATCH_COUNT_ODDS[1],
  HIT_RATE * MATCH_COUNT_ODDS[2],
];

/** Prize weighting for UNMATCHED panels. Deliberately gentler than the payout
 *  odds (1/√Pᵢ instead of 1/Pᵢ) so the face shows a spread of rungs rather than
 *  a wall of 10.000 ₫. Pure decoration — it can never move totalPrize. */
const FACE_ODDS: number[] = (() => {
  const mass = LADDER.map((prize) => 1 / Math.sqrt(prize));
  const total = sum(mass);
  return mass.map((m) => m / total);
})();

/** Consolation dust, in VND. Marketing numerals → lucky-safe (digit-4 taboo);
 *  the filter is the enforcement, not a comment that can rot. */
const DUST_STEPS: number[] = [
  1_000, 1_800, 2_000, 2_600, 3_000, 3_800, 5_000, 6_000, 6_800, 8_000,
].filter(isLuckySafe);

/* ----------------------------------------------------------------------------
 * DETERMINISM — mulberry32, inline, no dependency.
 * --------------------------------------------------------------------------*/

/** mulberry32: 32-bit state, uniform in [0, 1). Same seed → same card, forever. */
function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4_294_967_296;
  };
}

type Rng = () => number;

const randInt = (rng: Rng, bound: number): number => Math.floor(rng() * bound);

function pickOne<T>(rng: Rng, list: readonly T[]): T {
  return list[randInt(rng, list.length)];
}

/** Index into `weights`, drawn proportionally. Weights need not be normalised. */
function pickWeighted(rng: Rng, weights: readonly number[]): number {
  let r = rng() * sum(weights);
  for (let i = 0; i < weights.length; i++) {
    r -= weights[i];
    if (r < 0) return i;
  }
  return weights.length - 1;
}

function shuffle<T>(rng: Rng, list: T[]): T[] {
  for (let i = list.length - 1; i > 0; i--) {
    const j = randInt(rng, i + 1);
    [list[i], list[j]] = [list[j], list[i]];
  }
  return list;
}

/** `count` distinct face numbers in 0–99, avoiding everything in `exclude`. */
function distinctFaces(rng: Rng, count: number, exclude: readonly number[]): number[] {
  const taken = new Set(exclude);
  const out: number[] = [];
  while (out.length < count) {
    const n = randInt(rng, FACE_RANGE);
    if (taken.has(n)) continue;
    taken.add(n);
    out.push(n);
  }
  return out;
}

/** A number one away from a winning number — "you had 47, the card said 48".
 *  Falls back to an ordinary decoy in the (unreachable) fenced-in case. */
function nearMiss(rng: Rng, winning: readonly number[]): number {
  for (const w of shuffle(rng, [...winning])) {
    for (const delta of shuffle(rng, [1, -1])) {
      const n = (w + delta + FACE_RANGE) % FACE_RANGE;
      if (!winning.includes(n)) return n;
    }
  }
  return distinctFaces(rng, 1, winning)[0];
}

const ID_ALPHABET = "0123456789abcdefghjkmnpqrstuvwxyz";

/** Card id. Drawn from the same rng, so a seeded card is byte-identical. */
function makeId(rng: Rng): string {
  let s = "";
  for (let i = 0; i < 8; i++) s += ID_ALPHABET[randInt(rng, ID_ALPHABET.length)];
  return `sc-${s}`;
}

/* ----------------------------------------------------------------------------
 * GENERATION
 * --------------------------------------------------------------------------*/

/** Ladder indices the card will actually PAY. Chosen before any face exists. */
function drawMatchedRungs(rng: Rng, outcome: ScratchOutcome): number[] {
  if (outcome === "lose") return [];
  if (outcome === "partial") {
    // exactly one match, restricted to the bottom four rungs
    return [pickWeighted(rng, RUNG_ODDS.slice(0, LOW_RUNGS))];
  }
  const branch = pickWeighted(rng, WIN_BRANCH_ODDS);
  if (branch === 0) {
    // one match, rung 5 or above
    return [WIN_RUNG_FLOOR + pickWeighted(rng, RUNG_ODDS.slice(WIN_RUNG_FLOOR))];
  }
  // two or three matches; each rung drawn from the full ladder, which is what
  // keeps the per-rung marginal at 0,48 · qᵢ regardless of how many land.
  const k = branch + 1;
  return Array.from({ length: k }, () => pickWeighted(rng, RUNG_ODDS));
}

/**
 * Build one scratch card.
 *
 * Deterministic when `seed` is given; otherwise weighted-random via
 * `Math.random()` — which is why this must only ever be called from an event
 * handler / effect, never during render on both sides of a hydration boundary.
 */
export function makeScratchCard(force?: ScratchOutcome, seed?: number): ScratchCard {
  const rng: Rng = seed === undefined ? Math.random : mulberry32(seed);

  // 1. outcome first.
  const outcome: ScratchOutcome = force ?? OUTCOMES[pickWeighted(rng, OUTCOME_ODDS)];

  // 2. what it pays.
  const matchedRungs = drawMatchedRungs(rng, outcome);

  // 3. the numbers.
  const winning = distinctFaces(rng, WINNING_COUNT, []);
  const decoys = distinctFaces(rng, DECOY_COUNT, winning);

  // 4. the face, built around the payout. Matched panels take a WINNING number
  //    (with replacement — a repeated winner pays twice, and that is the fun);
  //    every other panel takes a decoy, so it can never accidentally match.
  const panels: ScratchPanel[] = matchedRungs.map((rung) => ({
    n: pickOne(rng, winning),
    prize: LADDER[rung],
    matched: true,
  }));
  while (panels.length < PANEL_COUNT) {
    panels.push({
      n: pickOne(rng, decoys),
      prize: LADDER[pickWeighted(rng, FACE_ODDS)],
      matched: false,
    });
  }

  // 5. the lure. A non-winning card must still show real money on the table —
  //    for a loser, sitting one digit off a winning number.
  if (outcome !== "win") {
    const lure = panels[panels.length - 1]; // always unmatched: ≥ 11 blanks here
    lure.prize = LADDER[HIGH_RUNG_FLOOR + pickWeighted(rng, FACE_ODDS.slice(HIGH_RUNG_FLOOR))];
    if (outcome === "lose") lure.n = nearMiss(rng, winning);
  }

  shuffle(rng, panels);

  return {
    id: makeId(rng),
    winning,
    panels,
    outcome,
    totalPrize: panels.reduce((acc, p) => (p.matched ? acc + p.prize : acc), 0),
    dust: pickOne(rng, DUST_STEPS),
  };
}

/* ----------------------------------------------------------------------------
 * INVARIANTS
 * --------------------------------------------------------------------------*/

/** Throw if `card` violates any published invariant. Cheap enough to call on
 *  every card in dev; the self-test calls it 5.000 times. */
export function assertCard(card: ScratchCard): void {
  const fail = (why: string): never => {
    throw new Error(`assertCard(${card.id}) [${card.outcome}]: ${why}`);
  };

  if (card.winning.length !== WINNING_COUNT) fail(`${card.winning.length} winning numbers, want 4`);
  if (new Set(card.winning).size !== WINNING_COUNT) fail("winning numbers are not distinct");
  for (const w of card.winning) {
    if (!Number.isInteger(w) || w < 0 || w >= FACE_RANGE) fail(`winning number ${w} out of 0–99`);
  }

  if (card.panels.length !== PANEL_COUNT) fail(`${card.panels.length} panels, want 12`);

  let matches = 0;
  let paid = 0;
  let unmatchedHigh = 0;
  for (const p of card.panels) {
    if (!Number.isInteger(p.n) || p.n < 0 || p.n >= FACE_RANGE) fail(`face ${p.n} out of 0–99`);
    const rung = LADDER.indexOf(p.prize);
    // the face may never print a figure the campaign cannot pay
    if (rung < 0) fail(`prize ${p.prize} is not a ladder rung`);
    // matched ⟺ the face number really is one of the winning numbers
    if (p.matched !== card.winning.includes(p.n)) {
      fail(`panel ${p.n} matched=${p.matched} but winning=[${card.winning.join(",")}]`);
    }
    if (p.matched) {
      matches++;
      paid += p.prize;
    } else if (rung >= HIGH_RUNG_FLOOR) {
      unmatchedHigh++;
    }
  }

  if (card.totalPrize !== paid) fail(`totalPrize ${card.totalPrize} ≠ matched sum ${paid}`);

  if (card.outcome === "lose") {
    if (matches !== 0) fail(`${matches} matches on a loser`);
    if (card.totalPrize !== 0) fail(`totalPrize ${card.totalPrize} on a loser`);
    if (unmatchedHigh === 0) fail("no high rung on the face — the near-miss is the point");
  }

  if (card.outcome === "partial") {
    if (matches !== 1) fail(`${matches} matches, want exactly 1`);
    const rung = LADDER.indexOf(card.totalPrize);
    if (rung < 0 || rung >= LOW_RUNGS) fail(`match at rung ${rung + 1}, want a bottom-four rung`);
  }

  if (card.outcome === "win") {
    if (matches === 0) fail("a win that pays nothing");
    if (matches === 1) {
      const rung = LADDER.indexOf(card.panels.find((p) => p.matched)!.prize);
      if (rung < WIN_RUNG_FLOOR) fail(`single match at rung ${rung + 1}, want rung 5+`);
    }
  }

  if (!(card.dust > 0)) fail(`dust ${card.dust} must be positive`);
  if (!isLuckySafe(card.dust)) fail(`dust ${card.dust} carries the taboo digit 4`);
}

/* ----------------------------------------------------------------------------
 * SELF-TEST — `npx tsx -e 'import("./src/lib/mock/lottery.ts").then(m =>
 * console.log(m.selfTest().report))'`. Throws on the first violation.
 * --------------------------------------------------------------------------*/

const SELF_TEST_CARDS = 5_000;

export type ScratchSelfTest = {
  cards: number;
  lose: number;
  partial: number;
  win: number;
  hitRate: number;
  avgPrize: number;
  report: string;
};

/** Generate `cards` cards, assert every invariant, and report the outcome mix.
 *  Seeded per card so a failure is reproducible from the index alone. */
export function selfTest(cards: number = SELF_TEST_CARDS): ScratchSelfTest {
  const tally: Record<ScratchOutcome, number> = { lose: 0, partial: 0, win: 0 };
  let paid = 0;

  for (let i = 0; i < cards; i++) {
    const card = makeScratchCard(undefined, i);
    assertCard(card);
    tally[card.outcome]++;
    paid += card.totalPrize;
  }

  // forced outcomes must be honoured exactly, and stay legal while forced
  for (const forced of OUTCOMES) {
    for (let i = 0; i < 500; i++) {
      const card = makeScratchCard(forced, 900_000 + i);
      assertCard(card);
      if (card.outcome !== forced) throw new Error(`force="${forced}" produced "${card.outcome}"`);
    }
  }

  // seeding must be byte-stable, and unseeded play must still be legal
  const a = JSON.stringify(makeScratchCard(undefined, 7));
  const b = JSON.stringify(makeScratchCard(undefined, 7));
  if (a !== b) throw new Error("seeded output is not reproducible");
  if (JSON.stringify(makeScratchCard(undefined, 8)) === a) {
    throw new Error("different seeds produced the same card");
  }
  for (let i = 0; i < 500; i++) assertCard(makeScratchCard());

  const hitRate = (tally.partial + tally.win) / cards;
  const avgPrize = paid / cards;

  return {
    cards,
    lose: tally.lose,
    partial: tally.partial,
    win: tally.win,
    hitRate,
    avgPrize,
    report:
      `${cards} cards — lose ${tally.lose} / partial ${tally.partial} / win ${tally.win}; ` +
      `hit ${(hitRate * 100).toFixed(1)}% (published 38,7%); ` +
      `avg payout ${formatVnd(Math.round(avgPrize))} per card`,
  };
}

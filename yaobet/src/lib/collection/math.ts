/* ============================================================================
 * Yaobet — COLLECTION arithmetic.
 * ----------------------------------------------------------------------------
 * Pure functions. NO React import, no DOM, no clock, no randomness. Every
 * function is verifiable against the economy model in a plain node REPL, which
 * is the point: the economy owner must be able to check the shipped arithmetic
 * without a browser.
 *
 * EVERY economic quantity is an ARGUMENT. Set sizes, universe size, tier
 * masses, shard yields and craft prices are passed in — never literals in this
 * file. `M` and `R` do not appear at all: they are owner parameters and this
 * module never needs them.
 *
 * Open rulings this module deliberately does not resolve:
 *   · universe size and the rate-derivation source
 *   · the recomputed per-set guarantee under catalogue overlap
 *   · the pulls-to-finish convention used for catalogue ordering
 *   · craft ordering default
 * Where a caller needs one of those, it passes it in and the decision stays
 * visible at the call site instead of being buried here.
 * ==========================================================================*/

/* ----------------------------------------------------------------------------
 * Tier configuration — passed in, never assumed
 * --------------------------------------------------------------------------*/

export interface TierConfig {
  id: string;
  /** cards of this tier in the set */
  cardCount: number;
  /** per-card draw probability, as published */
  drawRate: number;
  /** shards minted when a duplicate of this tier is drawn */
  shardYield: number;
  /** shards required to craft one card of this tier */
  craftPrice: number;
}

export interface SetConfig {
  setId: string;
  /** distinct cards required to complete */
  size: number;
  tiers: TierConfig[];
}

/* ----------------------------------------------------------------------------
 * Progress
 * --------------------------------------------------------------------------*/

/** Distinct cards held of a set. Duplicates never advance completion. */
export function distinctHeld(
  heldCardIds: readonly string[],
  setCardIds: readonly string[],
): number {
  const inSet = new Set(setCardIds);
  const distinct = new Set<string>();
  for (const id of heldCardIds) if (inSet.has(id)) distinct.add(id);
  return distinct.size;
}

export function isComplete(held: number, size: number): boolean {
  return size > 0 && held >= size;
}

/**
 * Fraction complete, clamped to [0, 1].
 * Callers must NOT render this as a progress bar over a target the player's
 * own rate cannot reach — reachability is decided by the caller, not here.
 */
export function completionFraction(held: number, size: number): number {
  if (size <= 0) return 0;
  return Math.min(1, Math.max(0, held / size));
}

/* ----------------------------------------------------------------------------
 * Shards and crafting
 * --------------------------------------------------------------------------*/

/** Shards minted by a duplicate of a given tier. */
export function shardsForDuplicate(tier: TierConfig): number {
  return tier.shardYield;
}

/**
 * The cards still missing from a set, ordered RAREST FIRST.
 *
 * Rarest-first is the default because spending cheapest-first silently
 * reproduces the no-craft distribution and destroys the guarantee the player
 * was promised. A caller offering an out-of-order craft must disclose the real
 * cost and mark the guarantee permanently downgraded — it must not quietly
 * reorder here.
 */
export function missingCardsRarestFirst(
  missing: readonly { cardId: string; tierId: string }[],
  tiers: readonly TierConfig[],
): { cardId: string; tierId: string }[] {
  const rateOf = new Map(tiers.map((t) => [t.id, t.drawRate]));
  return [...missing].sort((a, b) => {
    const ra = rateOf.get(a.tierId) ?? Number.POSITIVE_INFINITY;
    const rb = rateOf.get(b.tierId) ?? Number.POSITIVE_INFINITY;
    if (ra !== rb) return ra - rb; // lower draw rate = rarer = first
    return a.cardId.localeCompare(b.cardId); // stable
  });
}

/**
 * Total shards to complete a set outright, in rarest-first order.
 * One action, one total — this is the figure the single complete-the-set
 * button prints.
 */
export function completionCost(
  missing: readonly { cardId: string; tierId: string }[],
  tiers: readonly TierConfig[],
): number {
  const priceOf = new Map(tiers.map((t) => [t.id, t.craftPrice]));
  return missing.reduce((sum, m) => sum + (priceOf.get(m.tierId) ?? 0), 0);
}

export interface Affordability {
  total: number;
  available: number;
  affordable: boolean;
  shortfall: number;
}

/** Whether the player can complete now, and by how much they fall short. */
export function affordability(total: number, available: number): Affordability {
  const shortfall = Math.max(0, total - available);
  return { total, available, affordable: shortfall === 0, shortfall };
}

/* ----------------------------------------------------------------------------
 * Pity
 * --------------------------------------------------------------------------*/

/**
 * Pity position after an open. The backstop is a hard floor: at
 * `backstopAt` consecutive non-rare opens the next open is guaranteed rare.
 * `backstopAt` is configuration.
 */
export function nextPityPosition(
  current: number,
  drewRare: boolean,
  backstopAt: number,
): number {
  if (drewRare) return 0;
  return Math.min(current + 1, backstopAt);
}

/** Opens remaining before the backstop fires. */
export function opensToBackstop(current: number, backstopAt: number): number {
  return Math.max(0, backstopAt - current);
}

/** True when the next open must yield a rare. */
export function backstopDue(current: number, backstopAt: number): boolean {
  return current >= backstopAt;
}

/* ----------------------------------------------------------------------------
 * Expected opens — the honest figure, with its quantile named
 * ----------------------------------------------------------------------------
 * A P90 is NOT a worst case and must never be labelled one. Callers render
 * the quantile alongside the number; the deterministic ceiling is the craft
 * cost plus the backstop, not this figure.
 * --------------------------------------------------------------------------*/

/**
 * Mean opens to collect `k` more distinct cards from a set, ignoring the craft
 * path — coupon-collector with per-card rates supplied by the caller.
 *
 * This is the DRAW-ONLY path. Under a shared pull pool across a catalogue the
 * per-set figure is slower than the independent-set model implies; the
 * catalogue-level convention is not decided here.
 */
export function meanOpensForRemaining(
  missingRates: readonly number[],
): number {
  let mean = 0;
  for (const p of missingRates) {
    if (p <= 0) return Number.POSITIVE_INFINITY;
    mean += 1 / p;
  }
  return mean;
}

/**
 * The guaranteed ceiling: complete by crafting instead of chasing.
 * This IS a ceiling and may be labelled as one — unlike a quantile.
 */
export function guaranteedOpensCeiling(
  totalShardCost: number,
  expectedShardsPerOpen: number,
): number {
  if (expectedShardsPerOpen <= 0) return Number.POSITIVE_INFINITY;
  return Math.ceil(totalShardCost / expectedShardsPerOpen);
}

/* ----------------------------------------------------------------------------
 * Allocation — earmark first, then the player's priority order
 * ----------------------------------------------------------------------------
 * Resolved BEFORE the draw. A set the player cannot still complete is skipped
 * so opens are never allocated into a finished collection.
 * --------------------------------------------------------------------------*/

export function resolveAllocationTarget(
  liveSetIds: readonly string[],
  priorityOrder: readonly string[],
  completeSetIds: readonly string[],
  earmarkSetId: string | null,
): string | null {
  const live = new Set(liveSetIds);
  const done = new Set(completeSetIds);
  const eligible = (id: string) => live.has(id) && !done.has(id);

  if (earmarkSetId && eligible(earmarkSetId)) return earmarkSetId;
  for (const id of priorityOrder) if (eligible(id)) return id;
  for (const id of liveSetIds) if (eligible(id)) return id;
  return null; // caller falls back to shards-only
}

/* ----------------------------------------------------------------------------
 * Accumulator
 * --------------------------------------------------------------------------*/

/**
 * Opens earned and the remainder, from accumulated qualifying progress.
 * `thresholdM` is the owner parameter, passed in. The remainder ROUNDS DOWN so
 * the screen never shows a threshold the engine has not reached.
 */
export function opensFromProgress(
  accumulated: number,
  thresholdM: number,
): { earnedOpens: number; remainder: number; progressToNext: number } {
  if (thresholdM <= 0) {
    return { earnedOpens: 0, remainder: 0, progressToNext: 0 };
  }
  const earnedOpens = Math.floor(accumulated / thresholdM);
  const remainder = accumulated - earnedOpens * thresholdM;
  return {
    earnedOpens,
    remainder,
    progressToNext: remainder / thresholdM,
  };
}

/* ----------------------------------------------------------------------------
 * Exchange impact — what a repeatable exchange actually costs
 * --------------------------------------------------------------------------*/

export interface ExchangeImpact {
  /** cards the player will no longer hold at all after the exchange */
  lost: string[];
  /** cards where a spare copy absorbs the cost — the holding shrinks, not ends */
  covered: string[];
  /** OTHER sets that lose distinct cards, and how many each loses */
  collateral: { setId: string; loses: number }[];
}

/**
 * Exchanging a set spends ONE COPY of each of its cards, so the set empties and
 * has to be collected again.
 *
 * The consequence that is not obvious, and that the player must be told BEFORE
 * they press anything: cards belong to several sets at once. Spending a card
 * for one set also removes it from every other set that contains it — unless a
 * duplicate absorbs the cost. Discovering that afterwards, on a surface that
 * pays real money, is a support ticket and a fair complaint.
 *
 * Pure and data-driven: it takes the holding and the set membership rather than
 * reaching for the fixtures, so the rule is testable and survives either pool model.
 */
export function exchangeImpact(
  setCardIds: readonly string[],
  heldCounts: ReadonlyMap<string, number>,
  otherSets: readonly { setId: string; cardIds: readonly string[] }[],
): ExchangeImpact {
  const lost: string[] = [];
  const covered: string[] = [];

  for (const cardId of setCardIds) {
    // A card held once is gone; held twice or more, a spare absorbs it.
    if ((heldCounts.get(cardId) ?? 0) > 1) covered.push(cardId);
    else lost.push(cardId);
  }

  const lostSet = new Set(lost);
  const collateral = otherSets
    .map((s) => ({
      setId: s.setId,
      // Only cards the player currently HOLDS can be lost from another set.
      loses: s.cardIds.filter((c) => lostSet.has(c) && (heldCounts.get(c) ?? 0) > 0)
        .length,
    }))
    .filter((s) => s.loses > 0);

  return { lost, covered, collateral };
}

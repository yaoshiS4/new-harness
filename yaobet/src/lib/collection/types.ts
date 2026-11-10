/* ============================================================================
 * Yaobet — COLLECTION feature domain types (PRD "BỘ SƯU TẬP").
 * ----------------------------------------------------------------------------
 * Scope note. These are the types the PORTS speak. They are
 * deliberately thin: the card-pool model is an OPEN RULING
 * (sets-own-cards vs sets-are-views) and the universe size `U` is open.
 * Nothing here may prejudge either. Where a shape depends on
 * those rulings it is marked and kept minimal rather than guessed.
 *
 * PARAMETERS, NEVER LITERALS. `M` (the qualifying amount that mints one open)
 * and `R` (the completion reward) are owner-set and appear nowhere in this
 * codebase as values. They travel as configuration.
 *
 * Reads use the house envelope from "@/lib/types" so the four data states
 * (live / loading / error / absent) are available to every surface for free.
 * ==========================================================================*/

import type { MoneyValue } from "@/lib/types";

/* ----------------------------------------------------------------------------
 * 1. ENTITLEMENT — the four-state open
 * ----------------------------------------------------------------------------
 * The lifecycle is fixed by the PRD and is NOT open: an open is minted
 * `pending` at placement, becomes `vested` at settlement, and is `opened`
 * once consumed. `unvested` is the deposit-minted state that the sequence
 * rule governs — money may SCHEDULE an open; only a settled wager may OPEN
 * one. An unvested entitlement is never auto-opened by any process;
 * its only terminal alternative to vesting is `lapsed`.
 * --------------------------------------------------------------------------*/

export type EntitlementState =
  | "pending"
  | "unvested"
  | "vested"
  | "opened"
  | "lapsed";

/** One minted open, traceable to the activity that produced it. */
export interface Entitlement {
  id: string;
  state: EntitlementState;
  /** the qualifying activity that minted it — the support trace's anchor */
  sourceActivityId: string;
  mintedAt: string; // ISO, server clock
  /** set when the entitlement leaves `pending`/`unvested` */
  vestedAt: string | null;
  /** plain-Vietnamese reason, shown verbatim to the player and to support */
  reason?: string;
}

/* ----------------------------------------------------------------------------
 * 2. THE ACCUMULATOR — the load-bearing shape (⚠)
 * ----------------------------------------------------------------------------
 * The trigger is an OPEN RULING. The seam therefore models the
 * ACCUMULATOR, not the qualifying event: "progress toward the next open".
 * Whatever the owner rules — turnover milestone, per-ticket, session,
 * activity-with-stake-as-accelerator — it feeds this same counter, and the UI
 * never learns which. Modelling a bet ticket here instead would leak the
 * unresolved trigger into every surface and is the one expensive mistake in
 * this module.
 * --------------------------------------------------------------------------*/

export interface AccumulatorPosition {
  /** opens already minted from accumulated qualifying progress */
  earnedOpens: number;
  /** progress toward the next open, as a fraction of `M` in [0, 1) */
  progressToNext: number;
  /**
   * Remainder expressed in the trigger's own unit, for display only.
   * Rounded DOWN so the screen never shows a threshold the engine has not
   * reached. `unitLabel` is configuration — never hard-coded copy.
   */
  remainder: { value: number; unitLabel: string } | null;
  /** true when the position was produced by a dev/simulated source */
  simulated: boolean;
}

/* ----------------------------------------------------------------------------
 * 3. CARDS, SETS, CATALOGUE — minimal, pending the pool-model ruling
 * ----------------------------------------------------------------------------
 * The pool-model ruling decides whether sets OWN cards or are VIEWS over one pool. Until it
 * lands, a card carries its identity and its art, and membership is expressed
 * as a list of set ids the card belongs to — which is representable under
 * BOTH rulings and commits to neither. The rate and craft price deliberately
 * live on the SET-scoped view, not on the card, because a shared card
 * carrying two published rates is precisely the defect that ruling exists
 * to prevent.
 * --------------------------------------------------------------------------*/

/** Content-layer identity. Art, names and marks are DATA, never code. */
export interface Card {
  id: string;
  /** display name — content, swappable with the theme */
  name: string;
  /** art slot — content, swappable with the theme */
  artSrc: string;
  /** rarity tier id, resolved against the set's published table */
  tierId: string;
  /** set ids this card belongs to (pool-model-neutral) */
  setIds: string[];
}

export interface CollectionSet {
  id: string;
  name: string;
  /** class id — every economic parameter derives from the class */
  classId: string;
  /** number of distinct cards required to complete */
  size: number;
  /** ISO; null = the standing, never-expiring collection */
  endsAt: string | null;
  /**
   * What completing this set pays — the parameter the PRD calls `R`.
   * DEMO VALUES ONLY. `R` is an owner parameter and has not been set; these
   * are placeholders so the surface can be built and compared. They rise with
   * set size on purpose: a small set paying more than a large one is the
   * cheapest thing in the catalogue to farm.
   */
  reward?: MoneyValue;
}

export interface Catalogue {
  sets: CollectionSet[];
  cards: Card[];
  /** the version the published rates were issued under — travels with accruals */
  rateTableVersion: string;
  effectiveAt: string; // ISO
}

/* ----------------------------------------------------------------------------
 * 4. PLAYER COLLECTION STATE
 * --------------------------------------------------------------------------*/

export interface HeldCard {
  cardId: string;
  /** total copies held; the first is the collected card, the rest are dupes */
  count: number;
  firstAcquiredAt: string; // ISO
}

export interface SetProgress {
  setId: string;
  /** distinct cards held of the set's `size` */
  held: number;
  size: number;
  complete: boolean;
  /**
   * How many times this set has been completed AND exchanged.
   *
   * A set is REPEATABLE: exchanging spends one copy of each of its cards, so
   * the set drops back to empty and has to be collected again. That is why this
   * is a count and not the old `claimedAt` boolean — "already claimed" is no
   * longer a terminal state, and nothing may treat it as one.
   */
  exchangeCount: number;
  lastExchangedAt: string | null;
}

export interface ShardPurse {
  /** pooled across ordinary collections */
  pooled: number;
  /** tag-locked inside a premium block, keyed by block id */
  locked: Record<string, number>;
}

export interface CollectionState {
  heldCards: HeldCard[];
  progress: SetProgress[];
  shards: ShardPurse;
  /** opens held, by state */
  entitlements: Entitlement[];
  /** consecutive opens since the last rare — the visible pity position */
  pityPosition: number;
  /** the player's set priority order, set once (not a per-pull picker) */
  priorityOrder: string[];
  /** the published earmark share for a premium block, if enrolled */
  earmarkSetId: string | null;
  /**
   * The player's own record, newest first — and it lives HERE, in persisted
   * state, rather than in adapter memory. It was adapter-private, so it reset
   * on every adapter construction: a player with a full collection opened the
   * history on another route and read "Chưa có hoạt động nào." The record that
   * support reads during a dispute cannot be the one thing that does not
   * survive a page navigation.
   */
  audit: AuditEntry[];
  /** monotonic, persisted — ids must not restart and collide across sessions */
  auditSeq: number;
}

/* ----------------------------------------------------------------------------
 * 5. THE OPEN RESULT
 * --------------------------------------------------------------------------*/

export interface OpenOutcome {
  entitlementId: string;
  cardId: string;
  /** which live set the open was allocated to (earmark, then priority order) */
  allocatedSetId: string;
  /** true when the card was already held → shards minted instead */
  duplicate: boolean;
  shardsMinted: number;
  /** pity counter AFTER this open */
  pityPosition: number;
  drawnAt: string; // ISO
}

/* ----------------------------------------------------------------------------
 * 6. SUPPRESSION, RISK, RG
 * ----------------------------------------------------------------------------
 * Kept as distinct verdicts on purpose: RG and Risk are split on GOVERNANCE
 * grounds, not technical ones. A player suppressed for zero weight is not
 * rendered the feature at all — no promo card, no badge, no empty catalogue.
 * --------------------------------------------------------------------------*/

export type SuppressionReason =
  | "zero-weight"
  | "rg-control"
  | "self-excluded"
  | "age-unassured"
  | "holdout"
  | "risk-hold";

export interface RenderVerdict {
  /** false → the feature does not exist for this player on any surface */
  render: boolean;
  reason: SuppressionReason | null;
  /** plain-Vietnamese support-facing sentence, identical to the rules page */
  supportReason?: string;
}

export interface RiskVerdict {
  allowed: boolean;
  /** cap that bound, if any — published as terms, never hidden */
  boundBy: "daily" | "season" | "cluster" | "bank" | null;
  supportReason?: string;
}

/* ----------------------------------------------------------------------------
 * 7. REWARD
 * ----------------------------------------------------------------------------
 * `R` is an owner parameter. The port returns what was credited, it does not
 * decide what R is. Cash-like rewards are spendable on arrival with zero
 * wagering requirement; the physical class is fulfilled by Collection Ops
 * under two-person authorisation and never at tier-1/tier-2.
 * --------------------------------------------------------------------------*/

export type RewardKind = "cash-like" | "physical";

export interface RewardGrant {
  setId: string;
  kind: RewardKind;
  /** present for cash-like grants; absent for physical (fulfilment is offline) */
  amount?: MoneyValue;
  /** the receipt the player is shown — a payout-proof moment */
  transactionId: string;
  grantedAt: string; // ISO
}

/* ----------------------------------------------------------------------------
 * 8. AUDIT
 * --------------------------------------------------------------------------*/

export interface AuditEntry {
  id: string;
  at: string; // ISO
  /** what happened, in a support-readable phrase */
  event: string;
  /** the entitlement, card or set the entry concerns */
  subjectId: string;
  /** plain-Vietnamese reason sentence, identical to the player-facing string */
  reason?: string;
}

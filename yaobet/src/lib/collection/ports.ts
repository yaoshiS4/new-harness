/* ============================================================================
 * Yaobet — COLLECTION ports.
 * ----------------------------------------------------------------------------
 * ELEVEN interface declarations, no implementations. This is the seam between
 * the collection feature and the platform. No component ever knows whether it
 * is talking to a fixture or a backend.
 *
 * Rules this file exists to enforce:
 *   1. Every READ returns the house `Envelope<T>` — so loading, error and
 *      absent states are available to every surface for free, not retrofitted.
 *   2. Every MUTATION carries an idempotency key FROM THE FIRST COMMIT. A
 *      double-submit must be rejectable before any caller exists.
 *   3. Qualifying activity is an ACCUMULATOR, never a bet ticket. The trigger
 *      is unruled; modelling the event here would leak that
 *      decision into every surface.
 *   4. RG is SPLIT from Risk on governance grounds. They are different owners
 *      answering different questions and must not share a verdict type.
 *   5. `M` and `R` never appear here as values. They are configuration.
 *
 * Implementations live in ./adapters and are NOT exported through the feature
 * barrel — feature code depends on these declarations only.
 * ==========================================================================*/

import type { Envelope } from "@/lib/types";
import type {
  AccumulatorPosition,
  AuditEntry,
  Catalogue,
  CollectionState,
  Entitlement,
  OpenOutcome,
  RenderVerdict,
  RewardGrant,
  RewardKind,
  RiskVerdict,
} from "./types";

/* ----------------------------------------------------------------------------
 * Mutation envelope — every write is idempotent from day one.
 * --------------------------------------------------------------------------*/

/** Caller-supplied key. The same key must never apply an effect twice. */
export type IdempotencyKey = string;

export type MutationResult<T> =
  | { status: "applied"; value: T }
  | { status: "duplicate"; value: T }
  | { status: "rejected"; reason: string; canRetry: boolean };

/* ----------------------------------------------------------------------------
 * 1 · Qualifying activity — THE ACCUMULATOR
 * --------------------------------------------------------------------------*/

export interface QualifyingActivityPort {
  /**
   * Progress toward the next open. Whatever the owner rules as the trigger
   * feeds this counter; the UI never learns which. Never expose a bet ticket,
   * a stake figure or a settlement event through this port.
   */
  getPosition(playerId: string): Promise<Envelope<AccumulatorPosition>>;
}

/* ----------------------------------------------------------------------------
 * 2 · Entitlement — minting, vesting, lapsing
 * --------------------------------------------------------------------------*/

export interface EntitlementPort {
  list(playerId: string): Promise<Envelope<Entitlement[]>>;
  /**
   * Consume one VESTED entitlement. Implementations MUST refuse any
   * entitlement that is not `vested` — an unvested entitlement is never
   * opened by any process, in any state, at any incident level.
   */
  consume(
    playerId: string,
    entitlementId: string,
    key: IdempotencyKey,
  ): Promise<MutationResult<Entitlement>>;
}

/* ----------------------------------------------------------------------------
 * 3 · Outcome — the draw
 * --------------------------------------------------------------------------*/

export interface OutcomePort {
  /**
   * Resolve one open. Allocation (earmark first, then the player's priority
   * order) is resolved BEFORE the draw, by the implementation.
   *
   * Kept behind a port so the demo's seeded client generator and a pilot's
   * server-authoritative draw share one call site. Production forbids a
   * client-side draw; the demo adapter is a DECLARED, time-boxed departure
   * and no pilot code may depend on it.
   */
  draw(
    playerId: string,
    entitlementId: string,
    key: IdempotencyKey,
  ): Promise<MutationResult<OpenOutcome>>;
}

/* ----------------------------------------------------------------------------
 * 4 · Wallet — the payout-proof moment
 * --------------------------------------------------------------------------*/

export interface WalletPort {
  /**
   * Credit a completion reward. Idempotent from the first commit: the same
   * key must return `duplicate` with the original grant, never credit twice.
   * The port does not decide what `R` is.
   */
  credit(
    playerId: string,
    setId: string,
    kind: RewardKind,
    key: IdempotencyKey,
  ): Promise<MutationResult<RewardGrant>>;
}

/* ----------------------------------------------------------------------------
 * 5 · Risk — caps, velocity, identity clusters
 * --------------------------------------------------------------------------*/

export interface RiskPort {
  /** Asked before an open is granted, never after it is revealed. */
  check(playerId: string): Promise<Envelope<RiskVerdict>>;
}

/* ----------------------------------------------------------------------------
 * 6 · RG — split from Risk on governance grounds
 * --------------------------------------------------------------------------*/

export interface RgPort {
  /**
   * Whether the feature renders for this player at all. A suppressed player
   * sees nothing — no promo card, no badge, no locked or teaser state.
   */
  renderVerdict(playerId: string): Promise<Envelope<RenderVerdict>>;
}

/* ----------------------------------------------------------------------------
 * 7 · Catalogue — content is DATA
 * --------------------------------------------------------------------------*/

export interface CataloguePort {
  /**
   * The live catalogue and the rate-table version it was issued under.
   * Card art, names and marks are content and must be swappable without a
   * rebuild.
   */
  getCatalogue(): Promise<Envelope<Catalogue>>;
}

/* ----------------------------------------------------------------------------
 * 8 · Collection state — the player's own holdings
 * --------------------------------------------------------------------------*/

export interface CollectionStatePort {
  get(playerId: string): Promise<Envelope<CollectionState>>;
  setPriorityOrder(
    playerId: string,
    setIds: string[],
    key: IdempotencyKey,
  ): Promise<MutationResult<CollectionState>>;
  /** Atomic, rarest-first completion. One action, one total — never a shop. */
  craftToComplete(
    playerId: string,
    setId: string,
    key: IdempotencyKey,
  ): Promise<MutationResult<CollectionState>>;
}

/* ----------------------------------------------------------------------------
 * 9 · Clock — one source, server-declared timezone
 * --------------------------------------------------------------------------*/

export interface ClockPort {
  /** ISO, server clock. No surface may call a date function directly. */
  now(): string;
  /** The published timezone. Never the device's local zone. */
  timezone(): string;
}

/* ----------------------------------------------------------------------------
 * 10 · Audit — the support trace
 * --------------------------------------------------------------------------*/

/** One page of the trace. Newest first. */
export interface AuditPage {
  entries: AuditEntry[];
  /** feed back as `cursor` for the next page; null = the end of the record */
  nextCursor: string | null;
}

/** Paging query. Both fields optional so a caller may ask for "the first page". */
export interface TraceQuery {
  /** rows to return; implementations clamp to a published maximum */
  limit?: number;
  /** opaque, taken from the previous page's `nextCursor` */
  cursor?: string;
}

export interface AuditPort {
  /**
   * Per-activity trace answering "why did I not get a card?" in plain
   * Vietnamese, in sentences identical to the published rules.
   *
   * BOUNDED, from the first commit. An unbounded trace only fails on the
   * heaviest accounts — the ones whose support tickets matter most — and it
   * fails there by rendering the entire record into one scroll. The page is
   * still an `Envelope`, so loading/error/absent are unchanged for callers.
   */
  trace(playerId: string, query?: TraceQuery): Promise<Envelope<AuditPage>>;
}

/* ----------------------------------------------------------------------------
 * 11 · Holdout — invisible, pre-registered
 * --------------------------------------------------------------------------*/

export interface HoldoutPort {
  /**
   * Whether this player is in the holdout arm. A held-out player is treated
   * identically to a suppressed one so exposure stays binary — and is never
   * told, because telling them destroys the measurement.
   */
  isHeldOut(playerId: string): Promise<Envelope<boolean>>;
}

/* ----------------------------------------------------------------------------
 * The port set — what a surface receives
 * --------------------------------------------------------------------------*/

export interface CollectionPorts {
  activity: QualifyingActivityPort;
  entitlement: EntitlementPort;
  outcome: OutcomePort;
  wallet: WalletPort;
  risk: RiskPort;
  rg: RgPort;
  catalogue: CataloguePort;
  state: CollectionStatePort;
  clock: ClockPort;
  audit: AuditPort;
  holdout: HoldoutPort;
}

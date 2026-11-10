/* ============================================================================
 * Yaobet — COLLECTION feature barrel.
 * ----------------------------------------------------------------------------
 * THE ONLY PATH FEATURE CODE IMPORTS FROM.
 *
 * What is exported: the port declarations, the domain types, and the pure
 * arithmetic. What is NOT exported: the adapters. A component that could
 * import a fixture could accidentally ship one, and could learn whether it is
 * talking to a fixture or a backend — which is the one thing this seam exists
 * to prevent.
 *
 * The adapters are wired once, at the composition root (`./provider`), and
 * reach components as the `CollectionPorts` declaration and nothing else.
 *
 * Enforced by lint: no file under components/ or app/ may import
 * `@/lib/collection/adapters/*` or `@/lib/mock` when it is collection code.
 * ==========================================================================*/

/* — the seam — */
export type {
  AuditPage,
  CollectionPorts,
  IdempotencyKey,
  MutationResult,
  TraceQuery,
  QualifyingActivityPort,
  EntitlementPort,
  OutcomePort,
  WalletPort,
  RiskPort,
  RgPort,
  CataloguePort,
  CollectionStatePort,
  ClockPort,
  AuditPort,
  HoldoutPort,
} from "./ports";

/* — the domain — */
export type {
  AccumulatorPosition,
  AuditEntry,
  Card,
  Catalogue,
  CollectionSet,
  CollectionState,
  Entitlement,
  EntitlementState,
  HeldCard,
  OpenOutcome,
  RenderVerdict,
  RewardGrant,
  RewardKind,
  RiskVerdict,
  SetProgress,
  ShardPurse,
  SuppressionReason,
} from "./types";

/* — the arithmetic (pure, React-free, verifiable in a node REPL) — */
export {
  affordability,
  backstopDue,
  completionCost,
  completionFraction,
  distinctHeld,
  guaranteedOpensCeiling,
  isComplete,
  meanOpensForRemaining,
  missingCardsRarestFirst,
  nextPityPosition,
  opensFromProgress,
  exchangeImpact,
  opensToBackstop,
  resolveAllocationTarget,
  shardsForDuplicate,
} from "./math";
export type { Affordability, ExchangeImpact, SetConfig, TierConfig } from "./math";

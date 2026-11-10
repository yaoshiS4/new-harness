/* ============================================================================
 * Yaobet — COLLECTION fixture adapters.
 * ----------------------------------------------------------------------------
 * Implementations of the eleven ports, backed by fixtures, latency and seeded
 * failure. Feature code NEVER imports this file — it imports the barrel and
 * receives the port declarations. Swapping these for HTTP adapters is a
 * one-file change with no call-site churn.
 *
 * TWO PORTS DELIBERATELY REFUSE.
 *   · Catalogue  — the content model is blocked on the open decisions
 *                  (sets-own-cards vs sets-are-views; universe size, rate
 *                  derivation). It returns `absent`: no real source. That is
 *                  the truthful envelope, and the surface omits rather than
 *                  renders a fabricated set.
 *   · Outcome    — the draw is four stories downstream of those same
 *                  three rulings. It rejects with the ruling named.
 *
 * Faking either would teach a false economy that gets quoted back later, and
 * would bury three open decisions behind a screen that looks finished.
 * ==========================================================================*/

import type { Envelope } from "@/lib/types";
import type {
  AuditPage,
  AuditPort,
  CataloguePort,
  ClockPort,
  CollectionStatePort,
  EntitlementPort,
  HoldoutPort,
  IdempotencyKey,
  MutationResult,
  OutcomePort,
  QualifyingActivityPort,
  RgPort,
  RiskPort,
  TraceQuery,
  WalletPort,
  CollectionPorts,
} from "../ports";
import type {
  AccumulatorPosition,
  Catalogue,
  CollectionState,
  Entitlement,
  OpenOutcome,
  RenderVerdict,
  RewardGrant,
  RewardKind,
  RiskVerdict,
  SetProgress,
} from "../types";
import {
  affordability,
  completionCost,
  distinctHeld,
  isComplete,
  missingCardsRarestFirst,
  nextPityPosition,
  opensFromProgress,
  resolveAllocationTarget,
} from "../math";
import {
  cardById,
  cardsInSet,
  DEMO_CARDS,
  DEMO_PITY_BACKSTOP,
  DEMO_SETS,
  DEMO_TIERS,
  drawTable,
  tierOf,
} from "../fixtures/epl";
import { OffsetClock } from "./clock";
import { CollectionStore, capAudit } from "./store";
import { createRng, FixtureRuntime, type FixtureConfig } from "./runtime";

/**
 * Provisional pity backstop — demo value, not the shipped floor. Read from the
 * CONTENT layer, not typed here: the terms publish this same constant, and a
 * guarantee that is stated at one N and rolled at another is a false statement.
 */
const PITY_BACKSTOP = DEMO_PITY_BACKSTOP;

/** Trace paging. Bounded from the first commit — see `AuditPort.trace`. */
const TRACE_LIMIT_DEFAULT = 50;
const TRACE_LIMIT_MAX = 200;

/**
 * Recompute every set's progress from the player's distinct holdings.
 *
 * The EXCHANGE HISTORY is carried forward, never recomputed. It records what
 * happened to the player's money, not something derivable from their cards.
 * `held` and `complete` ARE recomputed every time, which is what lets a set
 * empty itself the moment its cards are spent.
 */
function recomputeProgress(heldCardIds: string[], prev: SetProgress[] = []) {
  return DEMO_SETS.map((s) => {
    const setCardIds = cardsInSet(s.id).map((c) => c.id);
    const held = distinctHeld(heldCardIds, setCardIds);
    const before = prev.find((p) => p.setId === s.id);
    return {
      setId: s.id,
      held,
      size: s.size,
      complete: isComplete(held, s.size),
      exchangeCount: before?.exchangeCount ?? 0,
      lastExchangedAt: before?.lastExchangedAt ?? null,
    };
  });
}

/* ----------------------------------------------------------------------------
 * Simulated session — what the dev controls drive
 * --------------------------------------------------------------------------*/

export interface SimulatedSession {
  /** accumulated qualifying progress, in the trigger's own unit */
  accumulated: number;
  /** the owner parameter `M`. Configuration — never a literal in feature code. */
  thresholdM: number;
  /** label for the trigger's unit; content, not copy baked into a component */
  unitLabel: string;
  /** forced states */
  forced: {
    riskBlock: boolean;
    rgSuppressed: boolean;
    zeroWeight: boolean;
    ageUnassured: boolean;
    holdout: boolean;
    walletFailure: boolean;
  };
}

export function defaultSession(): SimulatedSession {
  return {
    accumulated: 0,
    thresholdM: 1, // placeholder unit-scale ONLY; the real M is owner-set
    unitLabel: "đơn vị cược",
    forced: {
      riskBlock: false,
      rgSuppressed: false,
      zeroWeight: false,
      ageUnassured: false,
      holdout: false,
      walletFailure: false,
    },
  };
}

/* ----------------------------------------------------------------------------
 * The adapter set
 * --------------------------------------------------------------------------*/

export class FixtureCollectionAdapters {
  readonly runtime: FixtureRuntime;
  readonly clock: OffsetClock;
  readonly store: CollectionStore;
  session: SimulatedSession;

  private seq = 0;
  /** Draw randomness is seeded separately from failure injection, so a demo
   *  that reruns produces the same cards even if a read failed on the way. */
  private drawRng: () => number;

  constructor(accountId = "demo-a", config: Partial<FixtureConfig> = {}) {
    this.runtime = new FixtureRuntime(config);
    this.clock = new OffsetClock(this.runtime.getConfig().timezone);
    this.store = new CollectionStore(accountId);
    this.session = defaultSession();
    this.drawRng = createRng(this.runtime.getConfig().seed ^ 0x5eed);
  }

  private nextId(prefix: string): string {
    this.seq += 1;
    return `${prefix}-${this.seq}`;
  }

  /**
   * Appended to PERSISTED state, newest first. The sequence lives in the state
   * too, so ids stay unique across sessions — restarting it at 1 on every
   * adapter construction would hand two different events the same id, and the
   * trace cursor is an id.
   */
  private log(event: string, subjectId: string, reason?: string): void {
    this.store.update((prev) =>
      capAudit({
        ...prev,
        auditSeq: prev.auditSeq + 1,
        audit: [
          {
            id: `aud-${prev.auditSeq + 1}`,
            at: this.clock.now(),
            event,
            subjectId,
            reason,
          },
          ...prev.audit,
        ],
      }),
    );
  }

  /* --------------------------------------------------------------------------
   * 1 · Qualifying activity — the accumulator
   * ------------------------------------------------------------------------*/

  activity: QualifyingActivityPort = {
    getPosition: async (): Promise<Envelope<AccumulatorPosition>> =>
      this.runtime.read<AccumulatorPosition>(() => {
        const { accumulated, thresholdM, unitLabel } = this.session;
        const { earnedOpens, remainder, progressToNext } = opensFromProgress(
          accumulated,
          thresholdM,
        );
        return {
          earnedOpens,
          progressToNext,
          remainder: { value: Math.floor(remainder), unitLabel },
          simulated: true,
        };
      }, this.clock.now()),
  };

  /* --------------------------------------------------------------------------
   * 2 · Entitlement
   * ------------------------------------------------------------------------*/

  entitlement: EntitlementPort = {
    list: async (): Promise<Envelope<Entitlement[]>> =>
      this.runtime.read<Entitlement[]>(
        () => this.store.read().entitlements,
        this.clock.now(),
      ),

    consume: async (
      _playerId: string,
      entitlementId: string,
      key: IdempotencyKey,
    ): Promise<MutationResult<Entitlement>> => {
      const current = this.store
        .read()
        .entitlements.find((e) => e.id === entitlementId);

      if (!current) {
        return this.runtime.reject("Không tìm thấy lượt mở.");
      }

      // The invariant. An unvested entitlement is never opened, by any
      // process, in any state. Enforced at the seam so no caller can bypass it.
      if (current.state !== "vested") {
        this.log("consume.refused", entitlementId, unvestedReason(current.state));
        return this.runtime.reject(unvestedReason(current.state));
      }

      return this.runtime.mutate(key, () => {
        const next = this.store.update((prev) => ({
          ...prev,
          entitlements: prev.entitlements.map((e) =>
            e.id === entitlementId ? { ...e, state: "opened" as const } : e,
          ),
        }));
        this.log("consume.applied", entitlementId);
        return next.entitlements.find((e) => e.id === entitlementId)!;
      });
    },
  };

  /* --------------------------------------------------------------------------
   * 3 · Outcome — BLOCKED on the open content decisions
   * ------------------------------------------------------------------------*/

  outcome: OutcomePort = {
    draw: async (
      _playerId: string,
      entitlementId: string,
      key: IdempotencyKey,
    ): Promise<MutationResult<OpenOutcome>> => {
      const before = this.store.read();
      const ent = before.entitlements.find((e) => e.id === entitlementId);

      if (!ent) return this.runtime.reject("Không tìm thấy lượt mở.");
      if (ent.state !== "vested") {
        this.log("draw.refused", entitlementId, unvestedReason(ent.state));
        return this.runtime.reject(unvestedReason(ent.state));
      }

      return this.runtime.mutate(key, () => {
        // Allocation is resolved BEFORE the draw — earmark, then priority.
        const complete = before.progress.filter((p) => p.complete).map((p) => p.setId);
        const target =
          resolveAllocationTarget(
            DEMO_SETS.map((s) => s.id),
            before.priorityOrder,
            complete,
            before.earmarkSetId,
          ) ?? DEMO_SETS[0].id;

        // Seeded draw against the published table, restricted to the target set.
        const pool = drawTable().filter((t) =>
          cardById(t.cardId)?.setIds.includes(target),
        );
        const total = pool.reduce((s, t) => s + t.weight, 0);
        let roll = this.drawRng() * total;
        let picked = pool[pool.length - 1].cardId;
        for (const t of pool) {
          roll -= t.weight;
          if (roll <= 0) {
            picked = t.cardId;
            break;
          }
        }

        const already = before.heldCards.find((h) => h.cardId === picked);
        const duplicate = Boolean(already);
        const tier = tierOf(picked);
        const shards = duplicate ? tier.shardYield : 0;
        const drewRare = tier.id === "rare";

        const next = this.store.update((prev) => {
          const heldCards = duplicate
            ? prev.heldCards.map((h) =>
                h.cardId === picked ? { ...h, count: h.count + 1 } : h,
              )
            : [
                ...prev.heldCards,
                { cardId: picked, count: 1, firstAcquiredAt: this.clock.now() },
              ];

          return {
            ...prev,
            heldCards,
            shards: { ...prev.shards, pooled: prev.shards.pooled + shards },
            entitlements: prev.entitlements.map((e) =>
              e.id === entitlementId ? { ...e, state: "opened" as const } : e,
            ),
            pityPosition: nextPityPosition(prev.pityPosition, drewRare, PITY_BACKSTOP),
            progress: recomputeProgress(heldCards.map((h) => h.cardId), prev.progress),
          };
        });

        // The reason string is the PLAYER-FACING sentence, verbatim. It used to
        // read `+N mảnh` — a credit the player cannot spend anywhere, which
        // would keep leaking the word into the history long after the stage
        // stopped saying it. Shards still accrue in state; nothing is lost.
        this.log(
          duplicate ? "draw.duplicate" : "draw.new",
          picked,
          duplicate ? "Bạn đã có thẻ này." : undefined,
        );

        const outcome: OpenOutcome = {
          entitlementId,
          cardId: picked,
          allocatedSetId: target,
          duplicate,
          shardsMinted: shards,
          pityPosition: next.pityPosition,
          drawnAt: this.clock.now(),
        };
        return outcome;
      });
    },
  };

  /* --------------------------------------------------------------------------
   * 4 · Wallet
   * ------------------------------------------------------------------------*/

  wallet: WalletPort = {
    credit: async (
      _playerId: string,
      setId: string,
      kind: RewardKind,
      key: IdempotencyKey,
    ): Promise<MutationResult<RewardGrant>> => {
      if (this.session.forced.walletFailure) {
        return this.runtime.reject("Ví tạm thời không khả dụng.", true);
      }
      return this.runtime.mutate(key, () => {
        const grantedAt = this.clock.now();
        const grant: RewardGrant = {
          setId,
          kind,
          // No amount: `R` is an owner parameter and is not set in code.
          transactionId: this.nextId("txn"),
          grantedAt,
        };
        /* THE SET IS SPENT, NOT STAMPED.
           Exchanging consumes one copy of each of the set's cards, so the set
           drops back to empty and has to be collected again. A player holding a
           spare keeps it — which is the first thing in this feature that gives
           a duplicate a purpose. */
        const setCardIds = cardsInSet(setId).map((c) => c.id);
        this.store.update((prev) => {
          const heldCards = prev.heldCards
            .map((h) =>
              setCardIds.includes(h.cardId) ? { ...h, count: h.count - 1 } : h,
            )
            // A card at zero copies is not held. It leaves the inventory rather
            // than lingering as `×0`, which is not a state this product has.
            .filter((h) => h.count > 0);

          const spentProgress = prev.progress.map((p) =>
            p.setId === setId
              ? {
                  ...p,
                  exchangeCount: p.exchangeCount + 1,
                  lastExchangedAt: grantedAt,
                }
              : p,
          );

          return {
            ...prev,
            heldCards,
            progress: recomputeProgress(
              heldCards.map((h) => h.cardId),
              spentProgress,
            ),
          };
        });
        this.log("reward.exchanged", setId);
        return grant;
      });
    },
  };

  /* --------------------------------------------------------------------------
   * 5 · Risk
   * ------------------------------------------------------------------------*/

  risk: RiskPort = {
    check: async (): Promise<Envelope<RiskVerdict>> =>
      this.runtime.read<RiskVerdict>(() => {
        if (this.session.forced.riskBlock) {
          return {
            allowed: false,
            boundBy: "daily",
            supportReason: "Đã đạt giới hạn lượt mở trong ngày.",
          };
        }
        return { allowed: true, boundBy: null };
      }, this.clock.now()),
  };

  /* --------------------------------------------------------------------------
   * 6 · RG — split from Risk on governance grounds
   * ------------------------------------------------------------------------*/

  rg: RgPort = {
    renderVerdict: async (): Promise<Envelope<RenderVerdict>> =>
      this.runtime.read<RenderVerdict>(() => {
        const f = this.session.forced;
        if (f.zeroWeight) {
          return {
            render: false,
            reason: "zero-weight",
            supportReason:
              "Các trò chơi bạn đang chơi không tính vào chương trình này.",
          };
        }
        if (f.rgSuppressed) return { render: false, reason: "rg-control" };
        if (f.ageUnassured) return { render: false, reason: "age-unassured" };
        if (f.holdout) return { render: false, reason: "holdout" };
        return { render: true, reason: null };
      }, this.clock.now()),
  };

  /* --------------------------------------------------------------------------
   * 7 · Catalogue — BLOCKED on the content model (the content spine)
   * ------------------------------------------------------------------------*/

  catalogue: CataloguePort = {
    // DEMO content. The rate-table version is stamped `provisional` so no
    // surface can quote these numbers as published rates — they are not.
    getCatalogue: async (): Promise<Envelope<Catalogue>> =>
      this.runtime.read<Catalogue>(
        () => ({
          sets: DEMO_SETS,
          cards: DEMO_CARDS,
          rateTableVersion: "provisional-demo (BR-03/04/05 chưa chốt)",
          effectiveAt: this.clock.now(),
        }),
        this.clock.now(),
      ),
  };

  /* --------------------------------------------------------------------------
   * 8 · Collection state
   * ------------------------------------------------------------------------*/

  state: CollectionStatePort = {
    get: async (): Promise<Envelope<CollectionState>> =>
      this.runtime.read<CollectionState>(
        () => this.store.read(),
        this.clock.now(),
      ),

    setPriorityOrder: async (
      _playerId: string,
      setIds: string[],
      key: IdempotencyKey,
    ): Promise<MutationResult<CollectionState>> =>
      this.runtime.mutate(key, () => {
        this.log("priority.set", setIds.join(","));
        return this.store.update((prev) => ({ ...prev, priorityOrder: setIds }));
      }),

    craftToComplete: async (
      _playerId: string,
      setId: string,
      key: IdempotencyKey,
    ): Promise<MutationResult<CollectionState>> => {
      const before = this.store.read();
      const held = new Set(before.heldCards.map((h) => h.cardId));
      const missing = cardsInSet(setId)
        .filter((c) => !held.has(c.id))
        .map((c) => ({ cardId: c.id, tierId: c.tierId }));

      if (missing.length === 0) {
        return this.runtime.reject("Bộ này đã đủ thẻ.");
      }

      // Rarest-first, always. Spending cheapest-first silently reproduces the
      // no-craft distribution and destroys the guarantee (the spend-order guard).
      const ordered = missingCardsRarestFirst(missing, DEMO_TIERS);
      const cost = completionCost(ordered, DEMO_TIERS);
      const purse = affordability(cost, before.shards.pooled);

      if (!purse.affordable) {
        return this.runtime.reject(
          `Cần thêm ${purse.shortfall} mảnh để hoàn thành bộ này.`,
        );
      }

      return this.runtime.mutate(key, () => {
        this.log("craft.complete", setId, `${cost} mảnh`);
        return this.store.update((prev) => {
          const heldCards = [
            ...prev.heldCards,
            ...ordered.map((m) => ({
              cardId: m.cardId,
              count: 1,
              firstAcquiredAt: this.clock.now(),
            })),
          ];
          return {
            ...prev,
            heldCards,
            shards: { ...prev.shards, pooled: prev.shards.pooled - cost },
            progress: recomputeProgress(heldCards.map((h) => h.cardId), prev.progress),
          };
        });
      });
    },
  };

  /* --------------------------------------------------------------------------
   * 9 · Clock
   * ------------------------------------------------------------------------*/

  get clockPort(): ClockPort {
    return this.clock;
  }

  /* --------------------------------------------------------------------------
   * 10 · Audit
   * ------------------------------------------------------------------------*/

  auditPort: AuditPort = {
    /**
     * One page, newest first. The cursor is the id of the first entry of the
     * NEXT page, so it stays valid while newer entries are unshifted onto the
     * front — a cursor that drifts with every draw would repeat rows to the
     * one player most likely to be reading the record during a dispute.
     */
    trace: async (
      _playerId: string,
      query?: TraceQuery,
    ): Promise<Envelope<AuditPage>> =>
      this.runtime.read<AuditPage>(() => {
        const audit = this.store.read().audit;
        const limit = Math.min(
          Math.max(1, Math.floor(query?.limit ?? TRACE_LIMIT_DEFAULT)),
          TRACE_LIMIT_MAX,
        );
        const start = query?.cursor
          ? audit.findIndex((e) => e.id === query.cursor)
          : 0;
        // An unknown cursor is "no real source", not a crash and not page one.
        if (start < 0) return null;
        const entries = audit.slice(start, start + limit);
        if (entries.length === 0) return null;
        const after = audit[start + limit];
        return { entries, nextCursor: after ? after.id : null };
      }, this.clock.now()),
  };

  /* --------------------------------------------------------------------------
   * 11 · Holdout
   * ------------------------------------------------------------------------*/

  holdout: HoldoutPort = {
    isHeldOut: async (): Promise<Envelope<boolean>> =>
      this.runtime.read<boolean>(
        () => this.session.forced.holdout,
        this.clock.now(),
      ),
  };

  /* --------------------------------------------------------------------------
   * Dev controls — fire simulated qualifying activity
   * ------------------------------------------------------------------------*/

  /** Append synthetic qualifying activity. Every surface labels it simulated. */
  fireActivity(amount: number): void {
    this.session.accumulated += amount;
    this.log("activity.simulated", `+${amount}`);
  }

  /**
   * DEV ONLY — grant every card in a set so the completed/claimable case is
   * reachable in one click instead of ~60 opens.
   *
   * It grants cards, it does NOT grant the reward: the set becomes complete and
   * the player still has to exchange it. Short-circuiting to "claimed" would
   * mock up a screen nobody can reach by playing, which is the failure mode a
   * demo is supposed to rule out rather than reproduce.
   */
  completeSet(setId: string): void {
    const ids = cardsInSet(setId).map((c) => c.id);
    this.store.update((prev) => {
      const heldCards = [...prev.heldCards];
      for (const cardId of ids) {
        const at = heldCards.findIndex((h) => h.cardId === cardId);
        if (at < 0) {
          heldCards.push({ cardId, count: 1, firstAcquiredAt: this.clock.now() });
        }
      }
      return {
        ...prev,
        heldCards,
        progress: recomputeProgress(heldCards.map((h) => h.cardId), prev.progress),
      };
    });
    this.log("collection.completed", setId, "Mô phỏng — hoàn thành bộ");
  }

  /** Mint the opens the accumulator has earned but not yet issued. */
  mintEarnedOpens(): number {
    const { earnedOpens } = opensFromProgress(
      this.session.accumulated,
      this.session.thresholdM,
    );
    const existing = this.store.read().entitlements.length;
    const toMint = Math.max(0, earnedOpens - existing);
    if (toMint === 0) return 0;

    this.store.update((prev) => ({
      ...prev,
      entitlements: [
        ...prev.entitlements,
        ...Array.from({ length: toMint }, () => {
          const id = this.nextId("ent");
          return {
            id,
            state: "vested" as const,
            sourceActivityId: "simulated",
            mintedAt: this.clock.now(),
            vestedAt: this.clock.now(),
          };
        }),
      ],
    }));
    this.log("entitlement.earned", `${toMint}`);
    return toMint;
  }

  /**
   * Seed the demo account ONCE, and only against an untouched store.
   *
   * Mounting a route is not a qualifying event. State is persisted per account
   * key and therefore shared across routes, so every composition root must go
   * through this — an unguarded `fireActivity(); mintEarnedOpens();` in a
   * second root turns a `/bo-suu-tap` → `/cua-toi` → back round trip into a
   * source of free opens. Returns whether it seeded, for the caller's logs.
   */
  ensureSeeded(opens: number): boolean {
    const s = this.store.read();
    const untouched =
      s.entitlements.length === 0 &&
      s.heldCards.length === 0 &&
      s.shards.pooled === 0;
    if (!untouched) return false;
    this.fireActivity(opens);
    this.mintEarnedOpens();
    return true;
  }

  /** Reset the demo account to the known seed. */
  resetDemo(): void {
    this.store.reset();
    this.runtime.resetLedger();
    this.session = defaultSession();
    this.clock.reset();
    // The trace resets with the store — `store.reset()` above returns the seed,
    // whose `audit` is empty and whose `auditSeq` is 0.
    this.seq = 0;
  }

  /** The port set a surface receives. */
  toPorts(): CollectionPorts {
    return {
      activity: this.activity,
      entitlement: this.entitlement,
      outcome: this.outcome,
      wallet: this.wallet,
      risk: this.risk,
      rg: this.rg,
      catalogue: this.catalogue,
      state: this.state,
      clock: this.clockPort,
      audit: this.auditPort,
      holdout: this.holdout,
    };
  }
}

/* ----------------------------------------------------------------------------
 * Reason strings — identical to the player-facing sentence.
 * --------------------------------------------------------------------------*/

function unvestedReason(state: string): string {
  switch (state) {
    case "unvested":
      return "Lượt mở này chưa hợp lệ: cần một cược đã kết toán mới được mở.";
    case "pending":
      return "Lượt mở đang chờ kết toán.";
    case "opened":
      return "Lượt mở này đã được sử dụng.";
    case "lapsed":
      return "Lượt mở đã hết hạn mà không được mở.";
    default:
      return "Lượt mở không ở trạng thái có thể mở.";
  }
}

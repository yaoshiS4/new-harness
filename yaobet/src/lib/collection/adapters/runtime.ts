/* ============================================================================
 * Yaobet — COLLECTION fixture runtime.
 * ----------------------------------------------------------------------------
 * The fixtures are SLOW and they FAIL, by default.
 *
 * The house fixture helper resolves synchronously at its default, so loading
 * and failure paths never render in development. For a read-only marketing
 * surface that is a convenience. For a MUTATING feature it is a defect
 * generator: we would ship an optimistic UI nobody has ever seen fail.
 *
 * So: every read and every write here resolves asynchronously after a
 * configurable non-zero delay, and fails at a configurable rate. Both are on
 * by default and both are visible in the harness before any caller exists.
 *
 * Determinism matters as much as failure. The failure roll is SEEDED — a demo
 * that fails randomly is a demo nobody trusts, and a test that fails randomly
 * gets deleted. Same seed, same sequence, for a second stakeholder and for CI.
 * ==========================================================================*/

import type { Envelope } from "@/lib/types";
import type { IdempotencyKey, MutationResult } from "../ports";

/* ----------------------------------------------------------------------------
 * Configuration
 * --------------------------------------------------------------------------*/

export interface FixtureConfig {
  /** milliseconds before a read or write resolves. Non-zero by default. */
  latencyMs: number;
  /** probability in [0,1] that a read returns an error envelope */
  readFailureRate: number;
  /** probability in [0,1] that a mutation is rejected */
  writeFailureRate: number;
  /** seed for the failure roll — same seed, same sequence */
  seed: number;
  /** server-declared validity window carried on every live envelope */
  freshnessMs: number;
  /** the published timezone — never the device's */
  timezone: string;
}

export const DEFAULT_FIXTURE_CONFIG: FixtureConfig = {
  latencyMs: 450,
  readFailureRate: 0.08,
  writeFailureRate: 0.06,
  seed: 20260813,
  freshnessMs: 30_000,
  timezone: "Asia/Ho_Chi_Minh",
};

/* ----------------------------------------------------------------------------
 * Seeded generator — mulberry32
 * --------------------------------------------------------------------------*/

export function createRng(seed: number): () => number {
  let a = seed >>> 0;
  return function next(): number {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* ----------------------------------------------------------------------------
 * The runtime
 * --------------------------------------------------------------------------*/

export class FixtureRuntime {
  private config: FixtureConfig;
  private rng: () => number;
  /** idempotency ledger — key → the result the FIRST commit produced */
  private applied = new Map<IdempotencyKey, unknown>();

  constructor(config: Partial<FixtureConfig> = {}) {
    this.config = { ...DEFAULT_FIXTURE_CONFIG, ...config };
    this.rng = createRng(this.config.seed);
  }

  getConfig(): FixtureConfig {
    return { ...this.config };
  }

  /** Dev control. Re-seeds so a reconfigured runtime is still deterministic. */
  configure(patch: Partial<FixtureConfig>): void {
    this.config = { ...this.config, ...patch };
    this.rng = createRng(this.config.seed);
  }

  /** Clears the idempotency ledger — demo reset only. */
  resetLedger(): void {
    this.applied.clear();
  }

  private delay(): Promise<void> {
    return new Promise((r) => setTimeout(r, this.config.latencyMs));
  }

  /* --------------------------------------------------------------------------
   * Reads — always one of the four envelope states
   * ------------------------------------------------------------------------*/

  /**
   * Wrap a fixture read. Returns a genuine `error` envelope at the configured
   * rate, and a genuine `absent` envelope when the producer yields null —
   * absent means "no real source", and the caller OMITS the band rather than
   * rendering a zero.
   */
  async read<T>(produce: () => T | null, nowIso: string): Promise<Envelope<T>> {
    await this.delay();
    if (this.rng() < this.config.readFailureRate) {
      return { status: "error", canRetry: true };
    }
    const value = produce();
    if (value === null || value === undefined) return { status: "absent" };
    return {
      status: "live",
      value,
      sourcedAt: nowIso,
      freshnessMs: this.config.freshnessMs,
    };
  }

  /* --------------------------------------------------------------------------
   * Mutations — idempotent from the first commit
   * ------------------------------------------------------------------------*/

  /**
   * Wrap a fixture mutation.
   *
   * The idempotency check happens BEFORE the failure roll and before the
   * effect: a replayed key returns `duplicate` carrying the original result
   * and never applies the effect twice. That ordering is the whole point — a
   * double-submit must be rejectable even when the network is misbehaving.
   */
  async mutate<T>(
    key: IdempotencyKey,
    apply: () => T,
  ): Promise<MutationResult<T>> {
    await this.delay();

    if (this.applied.has(key)) {
      return { status: "duplicate", value: this.applied.get(key) as T };
    }

    if (this.rng() < this.config.writeFailureRate) {
      return {
        status: "rejected",
        reason: "Kết nối gián đoạn, vui lòng thử lại.",
        canRetry: true,
      };
    }

    const value = apply();
    this.applied.set(key, value);
    return { status: "applied", value };
  }

  /** Reject a mutation for a domain reason — not a transport failure. */
  reject<T>(reason: string, canRetry = false): MutationResult<T> {
    return { status: "rejected", reason, canRetry };
  }
}

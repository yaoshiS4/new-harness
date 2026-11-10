/* ============================================================================
 * Yaobet — mock accessor helpers
 * ----------------------------------------------------------------------------
 * `getX()` async fns mimic server fetches so pages call them like a real data
 * layer. The real-API migration replaces the function BODIES, not the call
 * sites. `DEMO_EMPTY` forces honest empty/absent states across the app (0.4
 * Done-When) so QA can exercise the truthful-only fallbacks.
 * ==========================================================================*/

import type { LiveMoney } from "../types";

/** Flip to force honest empty states app-wide. */
export const DEMO_EMPTY = false as const;

/** Simulate a server fetch latency without blocking the build/test path. */
export function simulateFetch<T>(value: T, ms = 0): Promise<T> {
  if (ms <= 0) return Promise.resolve(value);
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

/** Build a LiveMoney with a server "now" timestamp (the dynamic-data seam). */
export function liveMoney(amount: number, sourcedAt: string = nowIso()): LiveMoney {
  return { amount, currency: "VND", live: true, sourcedAt };
}

/** A stable-ish ISO "server clock" anchor for fixtures. Real API supplies its own. */
export function nowIso(): string {
  return new Date().toISOString();
}

/** ISO N minutes from now (for truthful deadlines). */
export function isoIn(minutes: number): string {
  return new Date(Date.now() + minutes * 60_000).toISOString();
}

/** ISO N minutes ago (for past timestamps in history fixtures). */
export function isoAgo(minutes: number): string {
  return new Date(Date.now() - minutes * 60_000).toISOString();
}

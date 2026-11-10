/* ============================================================================
 * Yaobet — COLLECTION clock adapter.
 * ----------------------------------------------------------------------------
 * ONE clock. Every dated surface in the feature reads this; no surface calls a
 * date function directly. The published timezone is configuration, never the
 * device's local zone — a player in Bangkok and a player in Hanoi must see the
 * same season deadline.
 *
 * The offset exists so a season close can be demonstrated without waiting for
 * one. It is a demo control and it moves ALL dated surfaces at once, because
 * the defect class this prevents is two surfaces disagreeing about what time
 * it is — which always arrives at season close, at 23:00, on the night nobody
 * can fix it.
 * ==========================================================================*/

import type { ClockPort } from "../ports";

export class OffsetClock implements ClockPort {
  private offsetMs = 0;
  private readonly tz: string;

  constructor(timezone: string) {
    this.tz = timezone;
  }

  now(): string {
    return new Date(Date.now() + this.offsetMs).toISOString();
  }

  timezone(): string {
    return this.tz;
  }

  /* --------------------------------------------------------------------------
   * Demo controls
   * ------------------------------------------------------------------------*/

  /** Move the clock. Negative rewinds. All dated surfaces agree instantly. */
  shift(ms: number): void {
    this.offsetMs += ms;
  }

  /** Jump to a specific instant — used to sit just before a season boundary. */
  setTo(iso: string): void {
    this.offsetMs = new Date(iso).getTime() - Date.now();
  }

  reset(): void {
    this.offsetMs = 0;
  }

  getOffsetMs(): number {
    return this.offsetMs;
  }
}

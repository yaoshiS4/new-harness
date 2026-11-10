/* ============================================================================
 * Yaobet — lib/format
 * ----------------------------------------------------------------------------
 * The SINGLE implementation of: VND formatting (1.234.567 ₫), the lucky-6/8 +
 * digit-4-taboo rules, odds and tabular-numeral display.
 *
 * Lucky-digit discipline applies to
 * MARKETING numerals ONLY (suggested deposit chips, decorative counters). A
 * ledger / odds / OTP / payout / balance value is NEVER massaged. The two
 * functions are deliberately separated so a caller cannot accidentally launder
 * a real figure through the lucky path.
 * ==========================================================================*/

import type { MoneyValue, LiveMoney, AnyMoney } from "./types";
import { vi } from "./i18n";

/** Group digits VN-style: 1234567 → "1.234.567". */
function groupVnd(amount: number): string {
  const sign = amount < 0 ? "-" : "";
  const whole = Math.abs(Math.trunc(amount));
  const grouped = whole
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return `${sign}${grouped}`;
}

/** Format a TRUTHFUL VND figure: "1.234.567 ₫". Never lucky-massaged. */
export function formatVnd(value: AnyMoney | number): string {
  const amount = typeof value === "number" ? value : value.amount;
  return `${groupVnd(amount)} ₫`;
}

/** Signed VND for ledger rows: "+1.234.567 ₫" / "-50.000 ₫". */
export function formatSignedVnd(value: AnyMoney | number): string {
  const amount = typeof value === "number" ? value : value.amount;
  const sign = amount > 0 ? "+" : "";
  return `${sign}${formatVnd(amount)}`;
}

/** Decimal odds, tabular, 2dp: 1.85 → "1.85". Truthful — never massaged. */
export function formatOdds(odds: number): string {
  return odds.toFixed(2);
}

/** Plain grouped count (points, participant counts): 12345 → "12.345". */
export function formatCount(n: number): string {
  return groupVnd(n);
}

/**
 * Whole-percent for a PUBLISHED CONTRIBUTION RATE (game-contribution table).
 * A rate is a LEDGER value — routed OUTSIDE the lucky-digit path below: a `0`
 * is never suppressed and a `4` is never massaged (100/20/15/0 → "100%"/"20%"/
 * "15%"/"0%"). VN decimal comma is used ONLY when a `dp` is requested.
 */
export function formatPercent(value: number, dp = 0): string {
  const fixed = value.toFixed(dp);
  return `${dp > 0 ? fixed.replace(".", ",") : fixed}%`;
}

/* ----------------------------------------------------------------------------
 * LUCKY DISCIPLINE — MARKETING NUMERALS ONLY.
 * digit-4 taboo (避4) + 6/8 favoured (喜6喜8). Use for suggested-amount chips,
 * decorative counters — NEVER a real ledger/odds/OTP/payout/balance value.
 * --------------------------------------------------------------------------*/

/** True if the integer part contains the taboo digit 4 (for payout-display lint). */
export function hasDigitFour(amount: number): boolean {
  return /4/.test(Math.abs(Math.trunc(amount)).toString());
}

/**
 * Curated lucky deposit-suggestion presets (marketing). Favours 6/8, avoids 4.
 * These are SUGGESTIONS shown as chips; the user's actual entered amount is
 * formatted via formatVnd and never altered.
 */
export const LUCKY_DEPOSIT_PRESETS: readonly number[] = [
  100_000, 188_000, 288_000, 588_000, 688_000, 888_000, 1_688_000, 6_888_000,
] as const;

/** Format a marketing preset for a chip label: 688000 → "688K", 6888000 → "6.888K". */
export function formatPresetChip(amount: number): string {
  return `${groupVnd(Math.round(amount / 1000))}K`;
}

/** Helper: is a marketing numeral "lucky-safe" (no digit-4)? */
export function isLuckySafe(amount: number): boolean {
  return !hasDigitFour(amount);
}

/* ----------------------------------------------------------------------------
 * FRESHNESS — the stale-stop seam. A live value past its
 * server-declared freshness window must be marked stale, not shown as live.
 * --------------------------------------------------------------------------*/

/** True iff a LiveMoney/Live value is past its freshness window relative to now. */
export function isStale(sourcedAt: string, freshnessMs: number, now: number = Date.now()): boolean {
  const sourced = new Date(sourcedAt).getTime();
  return now - sourced > freshnessMs;
}

/* ----------------------------------------------------------------------------
 * RELATIVE TIME — shared plain-VN humanizer (notification bell + message
 * center). The source `at` is the server clock; this is a DISPLAY-only
 * humanization against the client clock, never a stored value. Units come from
 * the vi.notifications catalog (Vừa xong / N phút trước / N giờ trước / N ngày
 * trước) so the bell and the inbox read identically.
 * --------------------------------------------------------------------------*/

/** Plain-VN relative time from an ISO instant against the client clock. */
export function relativeTime(iso: string, now: number = Date.now()): string {
  const diffMin = Math.max(0, Math.round((now - new Date(iso).getTime()) / 60_000));
  if (diffMin < 1) return vi.notifications.justNow;
  if (diffMin < 60) return `${diffMin} ${vi.notifications.minutesAgo}`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr} ${vi.notifications.hoursAgo}`;
  const diffDay = Math.round(diffHr / 24);
  return `${diffDay} ${vi.notifications.daysAgo}`;
}

/* The absolute `notificationTime()` formatter ("14:05 31/08") that used to sit
 * here belonged to the deleted /thong-bao feed row. The header bell — now the
 * only notification surface — shows the RELATIVE time the
 * owner approved ("18 phút trước") from relativeTime() above, so the absolute
 * formatter had no caller left and is deleted with its surface. */

/** Re-export the money type guard at the format boundary for convenience. */
export type { MoneyValue, LiveMoney, AnyMoney };

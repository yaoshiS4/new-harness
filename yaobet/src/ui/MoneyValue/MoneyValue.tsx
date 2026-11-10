/* ============================================================================
 * MoneyValue / DeltaAmount — the money role. NOT a --money token:
 * a `.money` utility composed from the type + win/loss tokens.
 *
 *  • MoneyValue — every figure that aligns/moves: VND grouping `1.234.567 ₫`,
 *    tabular-nums (no reflow on tick). Truthfulness is a property of the VALUE'S
 *    TYPE, not a prop: a plain `MoneyValue` renders static; a `LiveMoney` self-
 *    sets data-truthful (the Odometer/tween path reads that). NO hand-passed
 *    `truthful` boolean. Live values past freshness render "tạm dừng".
 *  • DeltaAmount — a signed win/loss figure on the luminance-matched pair,
 *    EQUAL salience (loss is never dimmer; red is loss/error only). digit-4
 *    discipline lives in lib/format and applies to marketing numerals only —
 *    a real ledger figure is never massaged here.
 *
 * digit-4 NOTE: this primitive renders REAL ledger/odds/balance figures, so it
 * NEVER routes through the lucky path. Marketing chips use lib/format presets.
 * ==========================================================================*/

import { formatVnd, formatSignedVnd, formatCount, formatOdds, isStale } from "@/lib/format";
import { isLiveMoney, type AnyMoney } from "@/lib/types";

export type MoneyKind = "money" | "balance" | "odds" | "count" | "countdown";
export type MoneySize = "num" | "num-lg";

export interface MoneyValueProps {
  value: AnyMoney;
  kind?: MoneyKind;
  size?: MoneySize;
  /** server-declared freshness window for a LiveMoney (stale-stop) */
  freshnessMs?: number;
  className?: string;
}

/** Render a money/aligning figure. Static for MoneyValue, tween-enabled (via
 *  data-truthful, read downstream by Odometer) for a server-issued LiveMoney. */
export function MoneyValue({
  value,
  kind = "money",
  size = "num",
  freshnessMs,
  className,
}: MoneyValueProps) {
  const live = isLiveMoney(value);
  const stale =
    live && freshnessMs != null && isStale(value.sourcedAt, freshnessMs);

  if (stale) {
    return (
      <span
        className={["ui-money", `ui-money-${size}`, "ui-money-stale", className]
          .filter(Boolean)
          .join(" ")}
        data-stale="true"
        title="Giá trị tạm dừng cập nhật"
      >
        tạm dừng
      </span>
    );
  }

  const text =
    kind === "odds"
      ? formatOdds(value.amount)
      : kind === "count"
        ? formatCount(value.amount)
        : formatVnd(value.amount);

  return (
    <span
      className={["ui-money", `ui-money-${size}`, className].filter(Boolean).join(" ")}
      // truthfulness is the TYPE's property — only a LiveMoney sets this.
      data-truthful={live ? "true" : undefined}
      data-kind={kind}
    >
      {text}
    </span>
  );
}

export type DeltaTone = "win" | "loss" | "auto";

export interface DeltaAmountProps {
  /** static, truthful ledger figure — signed amount drives win/loss color */
  value: AnyMoney;
  /** force a tone, or "auto" (default) = sign of the amount */
  tone?: DeltaTone;
  size?: MoneySize;
  className?: string;
}

/** A signed win/loss figure — equal salience, luminance-matched pair. */
export function DeltaAmount({
  value,
  tone = "auto",
  size = "num",
  className,
}: DeltaAmountProps) {
  const resolved: "win" | "loss" =
    tone === "auto" ? (value.amount >= 0 ? "win" : "loss") : tone;
  return (
    <span
      className={["ui-money", `ui-money-${size}`, `ui-money-${resolved}`, className]
        .filter(Boolean)
        .join(" ")}
      data-outcome={resolved}
    >
      {formatSignedVnd(value.amount)}
    </span>
  );
}

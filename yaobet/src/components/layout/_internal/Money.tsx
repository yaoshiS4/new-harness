/* ============================================================================
 * Money (shell-local) — tabular VND figure for the header balance chip / rail
 * / right-rail. A server-issued `LiveMoney` self-sets
 * data-truthful; a plain `MoneyValue` renders static. There is NO hand-passed
 * `truthful` boolean — truthfulness is a property of the value's TYPE.
 *
 * This is a thin shell-scoped renderer (not the full ui/Money primitive): it
 * does not tween — it shows the truthful resting figure, which is the correct
 * value under reduced-motion and is honest at all times. It reads --font-num /
 * --t-num and the equal-salience --win/--loss pair via the shell stylesheet.
 * ==========================================================================*/

import type { AnyMoney } from "@/lib/types";
import { isLiveMoney } from "@/lib/types";
import { formatVnd, formatSignedVnd } from "@/lib/format";

export interface MoneyProps {
  value: AnyMoney;
  /** num = inline (--t-num); num-lg = hero (--t-num-lg) */
  size?: "num" | "num-lg";
  /** show +/- sign and win/loss colour (ledger rows) */
  signed?: boolean;
  className?: string;
}

export function Money({ value, size = "num", signed = false, className }: MoneyProps) {
  const live = isLiveMoney(value);
  const text = signed ? formatSignedVnd(value) : formatVnd(value);
  const tone = signed ? (value.amount >= 0 ? "win" : "loss") : "neutral";
  return (
    <span
      className={["shell-money", `shell-money-${size}`, `shell-money-${tone}`, className]
        .filter(Boolean)
        .join(" ")}
      data-truthful={live ? "" : undefined}
    >
      {text}
    </span>
  );
}

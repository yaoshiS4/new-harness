/* ============================================================================
 * RateCell — the ONE renderer for every rate value (prototype §3.1 +
 * §3.6). It is the single place the two hard rules live:
 *   1. "Never decorate a zero." A `0%` renders in the SAME neutral treatment as
 *      100% / 20% / 15% — no chip, fill, icon, muted colour, opacity or strike.
 *      It reads as a BARE "0%" (owner override dropped the old "— Không tính"
 *      suffix): identical --text-hi + tabular numeral treatment to 100%.
 *      A column rendered uniformly reads as a MEASUREMENT; a decorated cell
 *      reads as a JUDGEMENT.
 *   2. A per-tier cell carries ALL tier values in ONE <td>, ascending, as
 *      coalesced ordinal groups (equal adjacent tiers become one `(Hạng a–b)`
 *      group). Middot `·` separated (never a range dash / slash). The ordinal
 *      words are the ONLY coloured element (--caution) — never the numeral.
 *      <768 the groups stack and the middot is hidden; ≥768 one line with the
 *      middot. An srOnly span enumerates every leg; the visible `·` is
 *      aria-hidden. NO gold / --brand-accent on any rate value.
 * ==========================================================================*/

import { Fragment } from "react";
import type { CategoryRate, TierGroup } from "@/lib/mock";
import { resolveTierRates, coalesceAdjacentEqual } from "@/lib/mock";
import { formatPercent } from "@/lib/format";
import { t, vi } from "@/lib/i18n";

/** "(Hạng 3)" for a single tier, "(Hạng 3–5)" for a span. Parens included so
 *  the whole label is one text node (no hydration comment splits the string). */
function tierLabel(g: TierGroup): string {
  return g.from === g.to
    ? `(${t(vi.contribution.tierOneLabel, { n: g.from })})`
    : `(${t(vi.contribution.tierRangeLabel, { a: g.from, b: g.to })})`;
}

/** Spoken enumeration of every group: "15 phần trăm ở hạng 1 và hạng 2; …". */
function tierSr(groups: TierGroup[]): string {
  return groups
    .map((g) =>
      g.from === g.to
        ? t(vi.contribution.srTierOne, { p: g.p, n: g.from })
        : t(vi.contribution.srTierRange, { p: g.p, a: g.from, b: g.to }),
    )
    .join("; ");
}

export function RateCell({ rate }: { rate: CategoryRate }) {
  if (rate.kind === "flat") {
    // 0% renders as a bare "0%" — the SAME neutral --text-hi tabular numeral as
    // 100% / 20% / 15% (no suffix, no chip, no muted colour). A zero is a value,
    // not a state. `flat 100` → "100%".
    return <span className="text-text-hi">{formatPercent(rate.p)}</span>;
  }

  const groups = coalesceAdjacentEqual(resolveTierRates(rate));
  return (
    <span className="text-text-hi">
      {groups.map((g, i) => (
        <Fragment key={`${g.from}-${g.to}-${g.p}`}>
          {i > 0 && (
            <span className="hidden min-[768px]:inline" aria-hidden="true">
              {" · "}
            </span>
          )}
          <span className="block min-[768px]:inline">
            <span className="text-text-hi">{formatPercent(g.p)}</span>{" "}
            <span className="text-caution">{tierLabel(g)}</span>
          </span>
        </Fragment>
      ))}
      <span className="absolute w-[1px] h-[1px] p-[0] m-[-1px] overflow-hidden [clip:rect(0,0,0,0)] whitespace-nowrap [border:0]">{tierSr(groups)}</span>
    </span>
  );
}

/* ============================================================================
 * VipRules — upgrade + rebate rules copy. Static,
 * truthful explanatory cards: how a tier is reached (real turnover, no dressed
 * numbers), how %-of-play cashback works (equal win/loss salience), and the RG
 * line (18+, set limits, support). A Server-Component-safe presentational
 * component — no client state, no fabricated figures.
 * ==========================================================================*/

import { Card, Icon } from "@/ui";
import { vipCopy } from "./copy";

export function VipRules() {
  return (
    <ol className="list-none m-[0] p-[0] flex flex-col gap-space-3 [counter-reset:rule] min-[768px]:grid min-[768px]:grid-cols-[1fr_1fr]">
      {vipCopy.rules.map((rule, i) => (
        <li key={rule.title} className="flex">
          <Card variant="default" className="flex items-start gap-space-3 p-space-4 w-full">
            <span className="flex-[0_0_auto] w-[28px] h-[28px] rounded-pill grid place-items-center text-t-sm font-weight-bold text-brand-accent-fg [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)] font-brand-font-num" aria-hidden>
              {i + 1}
            </span>
            <div className="flex flex-col gap-space-1 min-w-[0]">
              <h3 className="text-t-h3 font-weight-semi text-text-hi">{rule.title}</h3>
              <p className="text-t-sm leading-lh-body text-text-mid">{rule.body}</p>
            </div>
            <Icon name="info" size={18} className="flex-[0_0_auto] ml-auto text-text-dim" aria-hidden />
          </Card>
        </li>
      ))}
    </ol>
  );
}

/* ============================================================================
 * Luxury VIP — VipFaq. Single-open accordion (openFaq internal, -1=none);
 * chevron rotate + max-height transition; open row gets a faint gold bg.
 * ==========================================================================*/
"use client";

import { useState } from "react";
import type { FaqItem, Lang } from "@/lib/vip";

export function VipFaq({ items, lang }: { items: FaqItem[]; lang: Lang }) {
  const [openFaq, setOpenFaq] = useState<number>(-1);

  return (
    <div className="flex flex-col gap-space-3 max-w-[760px] my-[0] mx-auto">
      {items.map((item, i) => {
        const open = openFaq === i;
        const panelId = `vip-faq-panel-${i}`;
        const buttonId = `vip-faq-button-${i}`;
        return (
          <div
            key={item.q.vi}
            className={
              open
                ? "vip-faq-item vip-faq-item-open relative border rounded-vip-radius-table overflow-hidden [transition:background_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard)] [background:var(--vip-gold-tint)] border-[color-mix(in_srgb,var(--vip-gold-mid)_34%,transparent)] hover:border-[color-mix(in_srgb,var(--vip-gold-mid)_24%,transparent)]"
                : "vip-faq-item relative border rounded-vip-radius-table overflow-hidden [transition:background_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard)] border-vip-hairline [background:var(--vip-panel-bg)] hover:border-[color-mix(in_srgb,var(--vip-gold-mid)_24%,transparent)]"
            }
          >
            <button
              type="button"
              id={buttonId}
              className={
                open
                  ? "group w-full flex items-center justify-between gap-space-3 min-h-tap-min py-space-4 px-space-5 [border:0] [background:transparent] font-brand-font-body text-t-body font-weight-semi leading-[1.4] text-left cursor-pointer [transition:color_var(--dur-fast)_var(--ease-standard)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[-2px] max-900:py-space-3 max-900:px-space-4 max-900:text-t-sm text-vip-gold-mid"
                  : "group w-full flex items-center justify-between gap-space-3 min-h-tap-min py-space-4 px-space-5 [border:0] [background:transparent] font-brand-font-body text-t-body font-weight-semi leading-[1.4] text-left cursor-pointer [transition:color_var(--dur-fast)_var(--ease-standard)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[-2px] max-900:py-space-3 max-900:px-space-4 max-900:text-t-sm text-vip-text-primary hover:text-vip-gold-end"
              }
              aria-expanded={open}
              aria-controls={panelId}
              onClick={() => setOpenFaq(open ? -1 : i)}
            >
              <span>{item.q[lang]}</span>
              <span
                aria-hidden="true"
                className={
                  open
                    ? "flex-[0_0_auto] inline-flex items-center justify-center w-[26px] h-[26px] rounded-pill border text-vip-gold-mid text-t-h3 leading-[1] [transition:transform_var(--dur-slow)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),background_var(--dur-fast)_var(--ease-standard)] [transform:rotate(180deg)] border-[color-mix(in_srgb,var(--vip-gold-mid)_55%,transparent)] [background:var(--vip-gold-tint)] [.group:hover_&]:[transform:rotate(180deg)_scale(1.1)] motion-reduce:[transform:rotate(180deg)] motion-reduce:[.group:hover_&]:[transform:rotate(180deg)]"
                    : "flex-[0_0_auto] inline-flex items-center justify-center w-[26px] h-[26px] rounded-pill border text-vip-gold-mid text-t-h3 leading-[1] [transition:transform_var(--dur-slow)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),background_var(--dur-fast)_var(--ease-standard)] border-[color-mix(in_srgb,var(--vip-gold-mid)_30%,transparent)] [.group:hover_&]:[transform:scale(1.1)] motion-reduce:[.group:hover_&]:[transform:none]"
                }
              >
                ⌄
              </span>
            </button>
            <div
              id={panelId}
              role="region"
              aria-labelledby={buttonId}
              className={
                open
                  ? "overflow-hidden [transition:max-height_var(--dur-slow)_var(--ease-standard)] text-vip-text-secondary max-h-[520px]"
                  : "overflow-hidden [transition:max-height_var(--dur-slow)_var(--ease-standard)] text-vip-text-secondary max-h-[0]"
              }
            >
              <div className="pt-[0] px-space-5 pb-space-5 text-t-sm leading-[1.65] text-vip-text-secondary max-900:px-space-4 max-900:pb-space-4">{item.a[lang]}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

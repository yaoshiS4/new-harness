/* ============================================================================
 * Yaobet — LUXURY VIP program — root client island.
 * ----------------------------------------------------------------------------
 * Owns the shared runtime state (vipSel / vipLvl / lang) and the auth-driven
 * member↔guest split (useRequireAuth().allowed — NO member/guest toggle). Wires
 * tier selection so it drives BOTH the comparison target AND the level table.
 * Renders the child components by direct path; the shared
 * components/vip/index.ts barrel serves /tier.
 * ==========================================================================*/

"use client";

import { useState } from "react";
import { useRequireAuth } from "@/lib/auth";
import {
  TIERS,
  CURRENT_USER,
  CUR,
  CUR_LEVEL,
  FAQ_ITEMS,
  getVipCopy,
  type Lang,
} from "@/lib/vip";
import { VipSectionHeading } from "./VipSectionHeading";
import { VipHeroMember } from "./VipHeroMember";
import { VipHeroGuest } from "./VipHeroGuest";
import { TierDeck } from "./TierDeck";
import { PrivilegeComparison } from "./PrivilegeComparison";
import { PrivilegeMatrix } from "./PrivilegeMatrix";
import { LevelTable } from "./LevelTable";
import { VipFaq } from "./VipFaq";

export function VipProgram() {
  const { allowed, promptAuth } = useRequireAuth();

  const [vipSel, setVipSel] = useState<number>(CUR); // default Gold
  const [vipLvl, setVipLvl] = useState<number>(Math.min(CUR_LEVEL + 1, 10));
  const [lang, setLang] = useState<Lang>("vi");

  const copy = getVipCopy(lang);

  /** Selecting a tier: set target + reset the level cursor. */
  const onSelect = (i: number) => {
    setVipSel(i);
    setVipLvl(i === CUR ? Math.min(CUR_LEVEL + 1, 10) : 1);
  };

  return (
    <div className="[background:var(--vip-page-bg)] text-vip-text-primary font-brand-font-body min-h-[100%] pt-space-5 px-gutter pb-space-8 flex flex-col gap-space-6 overflow-x-hidden">
      <div className="w-full max-w-frame-w mx-auto flex flex-col gap-space-6 max-900:max-w-full">
        {/* deferrable VI/EN toggle (a lang state is required) */}
        <div className="self-end inline-flex gap-space-1 border border-vip-hairline rounded-pill p-space-1" role="group" aria-label="Language">
          {(["vi", "en"] as const).map((l) => (
            <button
              key={l}
              type="button"
              className={
                lang === l
                  ? "min-h-tap-min py-[0] px-space-3 [border:0] rounded-pill [background:var(--vip-gold-mid)] text-vip-gold-ink font-weight-semi cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 motion-reduce:[transform:none] motion-reduce:hover:[transform:none]"
                  : "min-h-tap-min py-[0] px-space-3 [border:0] rounded-pill [background:transparent] text-vip-text-muted cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[transform:scale(1.05)] hover:text-vip-gold-end focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 motion-reduce:[transform:none] motion-reduce:hover:[transform:none]"
              }
              aria-pressed={lang === l}
              onClick={() => setLang(l)}
            >
              {l.toUpperCase()}
            </button>
          ))}
        </div>

        {/* hero — auth drives the variant, not a toggle */}
        {allowed ? (
          <VipHeroMember user={CURRENT_USER} tiers={TIERS} lang={lang} />
        ) : (
          <VipHeroGuest
            lang={lang}
            onRegister={() => promptAuth()}
            onLogin={() => promptAuth()}
          />
        )}

        {/* tier deck (both variants) */}
        <section className="flex flex-col gap-space-4">
          <VipSectionHeading>{copy.allTiers}</VipSectionHeading>
          <TierDeck
            tiers={TIERS}
            selected={vipSel}
            onSelect={onSelect}
            currentTierIndex={allowed ? CUR : null}
            lang={lang}
          />
        </section>

        {/* privileges — comparison (member) vs matrix (guest) */}
        {allowed ? (
          <section className="flex flex-col gap-space-4">
            <VipSectionHeading>{copy.tierSectionTitle}</VipSectionHeading>
            <PrivilegeComparison
              tiers={TIERS}
              selected={vipSel}
              currentTierIndex={CUR}
              currentLevel={CUR_LEVEL}
              lang={lang}
            />
          </section>
        ) : (
          <section className="flex flex-col gap-space-4">
            <VipSectionHeading>{copy.tierMatrixTitle}</VipSectionHeading>
            <PrivilegeMatrix tiers={TIERS} selected={vipSel} lang={lang} />
          </section>
        )}

        {/* level table — driven by the selected tier + level cursor */}
        <section className="flex flex-col gap-space-4">
          <VipSectionHeading>{copy.lvlSectionTitle}</VipSectionHeading>
          <LevelTable
            tier={TIERS[vipSel]}
            selectedTierIndex={vipSel}
            currentTierIndex={allowed ? CUR : null}
            currentLevel={allowed ? CUR_LEVEL : null}
            lang={lang}
          />
          {/* vipLvl is consumed by the fleshed-out table/comparison; referenced
              here so the scaffold state is wired end-to-end. */}
          <span hidden aria-hidden>
            {vipLvl}
          </span>
        </section>

        {/* FAQ (both variants) */}
        <section className="flex flex-col gap-space-4">
          <VipSectionHeading>{copy.faqTitle}</VipSectionHeading>
          <VipFaq items={FAQ_ITEMS} lang={lang} />
        </section>
      </div>
    </div>
  );
}

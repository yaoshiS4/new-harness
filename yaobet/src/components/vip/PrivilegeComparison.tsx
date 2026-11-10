/* ============================================================================
 * Luxury VIP — PrivilegeComparison (member). Two benefit cards:
 * current tier → cmpT. cmpT = (selected===currentTierIndex && cur<4)
 * ? cur+1 : selected  → the right card is ALWAYS an upgrade on own tier
 * Privileges are per-tier & cumulative (rowIndex < tier.perks);
 * newly-gained rows on the target card get a gold "MỚI/NEW" badge, and an
 * unlock-wager footer note shows when the target sits above the current tier.
 * ==========================================================================*/
"use client";

import { getVipCopy, PRIVILEGES, type Lang, type VipTierDef } from "@/lib/vip";

export function PrivilegeComparison({
  tiers,
  selected,
  currentTierIndex,
  currentLevel,
  lang,
}: {
  tiers: VipTierDef[];
  selected: number;
  currentTierIndex: number;
  currentLevel: number;
  lang: Lang;
}) {
  const copy = getVipCopy(lang);
  void currentLevel; // per-tier privileges are level-independent

  const cmpT =
    selected === currentTierIndex && currentTierIndex < tiers.length - 1
      ? currentTierIndex + 1
      : selected;

  const left = tiers[currentTierIndex];
  const right = tiers[cmpT];
  const targetAboveCurrent = cmpT > currentTierIndex;

  const renderRows = (tier: VipTierDef, comparedTo?: VipTierDef) =>
    PRIVILEGES.map((key, idx) => {
      const unlocked = idx < tier.perks;
      const isNew = comparedTo ? idx >= comparedTo.perks && unlocked : false;
      return (
        <li
          key={key}
          className={
            isNew
              ? "flex items-center gap-space-2 py-space-2 px-[0] text-t-sm text-vip-gold-mid font-weight-semi"
              : unlocked
                ? "flex items-center gap-space-2 py-space-2 px-[0] text-t-sm text-vip-text-secondary"
                : "flex items-center gap-space-2 py-space-2 px-[0] text-t-sm text-vip-text-muted"
          }
        >
          <span
            className={
              unlocked
                ? "inline-grid place-items-center w-[20px] h-[20px] flex-none rounded-pill text-t-micro text-vip-positive [background:color-mix(in_srgb,var(--vip-positive)_16%,transparent)]"
                : "inline-grid place-items-center w-[20px] h-[20px] flex-none rounded-pill text-t-micro text-vip-text-muted"
            }
            aria-hidden
          >
            {unlocked ? "✓" : "🔒"}
          </span>
          <span className="min-w-[0]">{copy[key]}</span>
          {isNew && <span className="ml-auto py-[2px] px-space-2 rounded-pill [background:var(--vip-gold-mid)] text-vip-gold-ink text-t-micro font-weight-bold tracking-[0.06em]">{copy.newTag}</span>}
        </li>
      );
    });

  return (
    <div className="flex items-stretch gap-space-4 flex-wrap">
      <article className="flex-[1_1_260px] flex flex-col p-card-pad-sm rounded-card [background:var(--vip-panel-bg)] border border-vip-hairline">
        <header className="flex items-center gap-space-2 mb-space-3 pb-space-3 border-b border-b-vip-hairline">
          <span className="w-[20px] h-[20px] flex-none rounded-vip-radius-gem [border:1px_solid_color-mix(in_srgb,var(--vip-page-bg)_40%,transparent)] [transform:rotate(45deg)]" style={{ background: left.acc }} aria-hidden />
          <h3 className="vip-type-h4 tracking-[0.03em] uppercase m-[0]" style={{ color: left.acc }}>
            {copy[left.nameKey]}
          </h3>
        </header>
        <ul className="list-none m-[0] p-[0] flex flex-col gap-space-1">{renderRows(left)}</ul>
      </article>

      <div className="self-center text-vip-gold-mid text-t-display leading-[1] max-900:[transform:rotate(90deg)] max-900:self-center" aria-hidden>
        →
      </div>

      <article className="flex-[1_1_260px] flex flex-col p-card-pad-sm rounded-card [background:var(--vip-panel-bg)] border border-[color-mix(in_srgb,var(--vip-gold-mid)_45%,transparent)]">
        <header className="flex items-center gap-space-2 mb-space-3 pb-space-3 border-b border-b-vip-hairline">
          <span className="w-[20px] h-[20px] flex-none rounded-vip-radius-gem [border:1px_solid_color-mix(in_srgb,var(--vip-page-bg)_40%,transparent)] [transform:rotate(45deg)]" style={{ background: right.acc }} aria-hidden />
          <h3 className="vip-type-h4 tracking-[0.03em] uppercase m-[0]" style={{ color: right.acc }}>
            {copy[right.nameKey]}
          </h3>
        </header>
        <ul className="list-none m-[0] p-[0] flex flex-col gap-space-1">{renderRows(right, left)}</ul>
        {targetAboveCurrent && (
          <footer className="flex items-center gap-space-2 mt-space-3 pt-space-3 border-t border-t-vip-hairline text-vip-text-muted text-t-sm">
            <span className="text-vip-text-muted" aria-hidden>
              🔒
            </span>
            {copy.needWager} {right.unlock}
          </footer>
        )}
      </article>
    </div>
  );
}

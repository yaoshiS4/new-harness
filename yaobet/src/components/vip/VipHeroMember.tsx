/* ============================================================================
 * Luxury VIP — VipHeroMember. Gold-tinted hero panel with radial glow:
 *   • LEFT  — SVG level ring ("CẤP {level}") + name (Cinzel) + tier pill w/ crown
 *   • RIGHT — points (gold Cinzel), no sub-metrics
 *   • ROW 2 — "Tiến độ cược lên hạng sau" + {pct}% (gold), gold progress bar
 *             with a knob, a next-tier chevron chip pinned at the end, and the
 *             "{pointsToNextTier} điểm để lên {nextTier}" caption.
 * ==========================================================================*/
import { getVipCopy, type CurrentUser, type Lang, type VipTierDef } from "@/lib/vip";
import { LevelRing } from "./LevelRing";

export function VipHeroMember({
  user,
  tiers,
  lang,
}: {
  user: CurrentUser;
  tiers: VipTierDef[];
  lang: Lang;
}) {
  const copy = getVipCopy(lang);
  const tier = tiers[user.currentTierIndex];
  const nextTier = tiers[user.nextTierIndex];
  const tierName = copy[tier.nameKey];
  const nextName = nextTier ? copy[nextTier.nameKey] : "";

  const pct = Math.max(0, Math.min(100, user.wagerProgressPctToNextTier));

  return (
    <section className="vip-hero-member-bg relative overflow-hidden flex flex-col gap-space-5 p-card-pad rounded-card [border:1px_solid_color-mix(in_srgb,var(--vip-gold-mid)_22%,var(--vip-hairline))]">
      <div className="flex flex-wrap items-center gap-space-5">
        <div className="flex items-center gap-space-4">
          <LevelRing
            level={user.currentLevel}
            percent={pct}
            levelWord={copy.levelWord}
          />
          <div className="flex flex-col gap-space-2">
            <h1 className="vip-type-h1 text-vip-text-primary m-[0]">{user.name}</h1>
            {/* SOLID tier accent — tier.grad is a 3-stop metallic gradient and
                the flat system bans gradients on chips/buttons/cards. tier.acc
                is the same tier's flat accent; --vip-gold-ink stays legible on
                every one of the five accents. */}
            <span
              className="inline-flex items-center gap-space-1 self-start py-space-1 px-space-3 rounded-pill text-vip-gold-ink font-weight-bold text-t-sm tracking-[0.04em] uppercase"
              style={{ background: tier.acc }}
            >
              <span className="text-t-body leading-[1]" aria-hidden>
                ♛
              </span>
              {tierName}
            </span>
          </div>
        </div>

        <div className="ml-auto text-right max-900:ml-[0] max-900:text-left max-900:w-full">
          <div className="text-vip-text-muted text-t-sm uppercase tracking-[0.1em]">{copy.statPoints}</div>
          <div className="vip-type-num-lg text-vip-gold-mid">
            {user.points.toLocaleString("en-US")}
          </div>
        </div>
      </div>

      {nextTier && (
        <div className="flex flex-col gap-space-3">
          <div className="flex items-baseline justify-between gap-space-3">
            <span className="text-vip-text-secondary text-t-sm">{copy.progressLabel}</span>
            <span className="vip-type-num-md text-vip-gold-mid">{pct}%</span>
          </div>

          <div className="flex items-center gap-space-3 max-900:flex-wrap">
            <div
              className="relative flex-[1_1_auto] h-[10px] rounded-pill [background:color-mix(in_srgb,var(--vip-gold-start)_12%,var(--vip-inner-bg))] border border-vip-hairline"
              role="progressbar"
              aria-valuenow={pct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={copy.progressLabel}
            >
              <div className="absolute [inset:0_auto_0_0] rounded-pill [background:var(--vip-gold-mid)] [transition:width_var(--dur-slow)_var(--ease-entrance)]" style={{ width: `${pct}%` }} />
              <span className="absolute top-[50%] w-[18px] h-[18px] rounded-pill [background:var(--vip-gold-end)] [border:2px_solid_var(--vip-gold-ink)] [transform:translate(-50%,-50%)] [transition:left_var(--dur-slow)_var(--ease-entrance)]" style={{ left: `${pct}%` }} />
            </div>

            <span
              className="inline-flex items-center gap-space-1 flex-none py-space-1 px-space-3 rounded-pill border border-vip-hairline [background:color-mix(in_srgb,var(--vip-panel-alt)_70%,transparent)] text-t-sm font-weight-semi uppercase tracking-[0.04em] whitespace-nowrap max-900:order-[-1] max-900:self-end"
              style={{
                borderColor: `color-mix(in srgb, ${nextTier.acc} 55%, transparent)`,
                color: nextTier.acc,
              }}
            >
              {nextName}
              <span className="text-t-body leading-[1]" aria-hidden>
                ›
              </span>
            </span>
          </div>

          <div className="text-vip-text-muted text-t-sm">
            {user.pointsToNextTier.toLocaleString("en-US")}{" "}
            {copy.pointsToNextSuffix} {nextName}
          </div>
        </div>
      )}
    </section>
  );
}

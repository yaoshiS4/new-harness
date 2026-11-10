/* ============================================================================
 * Luxury VIP — VipHeroGuest. Badge + H1 + sub + two CTAs. NO stat
 * numbers. onRegister/onLogin surface the auth modal (wired by the parent).
 * ==========================================================================*/
import { getVipCopy, type Lang } from "@/lib/vip";

export function VipHeroGuest({
  lang,
  onRegister,
  onLogin,
}: {
  lang: Lang;
  onRegister: () => void;
  onLogin: () => void;
}) {
  const copy = getVipCopy(lang);

  return (
    <section className="vip-hero-guest-bg relative isolate overflow-hidden flex flex-col items-center text-center gap-space-3 py-[calc(var(--card-pad)*1.75)] px-card-pad rounded-card [border:1px_solid_color-mix(in_srgb,var(--vip-gold-mid)_34%,transparent)] max-900:py-[calc(var(--card-pad)*1.25)] max-900:px-card-pad-sm">
      <span className="inline-flex items-center gap-space-1 py-space-1 px-space-3 rounded-pill [border:1px_solid_color-mix(in_srgb,var(--vip-gold-mid)_40%,transparent)] [background:color-mix(in_srgb,var(--vip-gold-mid)_8%,transparent)] text-vip-gold-end text-t-micro font-weight-semi tracking-[0.16em] uppercase">
        <span className="w-[12px] h-[12px] rounded-vip-radius-gem [background:var(--vip-gold-mid)] [transform:rotate(45deg)]" aria-hidden />
        {copy.guestBadge}
      </span>
      <h1 className="vip-type-h1 tracking-[0.01em] text-vip-text-primary max-w-[18ch] m-[0]">{copy.guestH1}</h1>
      <p className="text-vip-text-secondary text-t-body leading-[1.6] max-w-[56ch] m-[0]">{copy.guestSub}</p>
      <div className="flex gap-space-3 flex-wrap justify-center mt-space-2">
        <button type="button" className="inline-flex items-center justify-center min-h-tap-min py-[0] px-[calc(var(--space-4)*1.5)] rounded-vip-radius-control font-weight-semi tracking-[0.02em] cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[transform:scale(1.05)] [border:0] [background:var(--vip-gold-mid)] text-vip-gold-ink hover:[background:var(--vip-gold-end)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 max-900:flex-[1_1_auto] motion-reduce:[transform:none] motion-reduce:hover:[transform:none]" onClick={onRegister}>
          {copy.ctaRegister}
        </button>
        <button type="button" className="inline-flex items-center justify-center min-h-tap-min py-[0] px-[calc(var(--space-4)*1.5)] rounded-vip-radius-control font-weight-semi tracking-[0.02em] cursor-pointer [transition:transform_var(--dur-fast)_var(--ease-standard),background_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard),color_var(--dur-fast)_var(--ease-standard)] hover:[transform:scale(1.05)] [background:color-mix(in_srgb,var(--vip-gold-mid)_4%,transparent)] border border-[color-mix(in_srgb,var(--vip-gold-mid)_45%,transparent)] text-vip-gold-end hover:[background:color-mix(in_srgb,var(--vip-gold-mid)_12%,transparent)] hover:border-vip-gold-mid focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 max-900:flex-[1_1_auto] motion-reduce:[transform:none] motion-reduce:hover:[transform:none]" onClick={onLogin}>
          {copy.ctaLogin}
        </button>
      </div>
    </section>
  );
}

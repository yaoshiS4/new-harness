/* ============================================================================
 * StepExplainer — 4-step "how it works" grid.
 * Static, truthful copy only (no fabricated bonus %). .step_box:
 * a 2-col grid (centered, fit-content) of image-over-caption cards; single
 * column @375. Server-rendered. Shared by /dai-ly AND /gioi-thieu.
 *
 * On /gioi-thieu this grid IS the honest no-friends onboarding empty state, so
 * an optional `intro` prop (default OFF → /dai-ly unaffected) renders a lead-in
 * headline above it. We own no banner PNGs, so each card is ICON-LED (our own
 * Icon over a token tile) — commissioning real Vietnamese banners is a later
 * asset task; the icon tile is the honest placeholder for that art.
 * ==========================================================================*/

import { Icon, type IconName } from "@/ui";
import { vi } from "@/lib/i18n";

const t = vi.referral;

interface Step {
  icon: IconName;
  body: string;
}

/* The refer-page flow: send → register → play → receive commission. */
const STEPS: Step[] = [
  { icon: "copy", body: t.step1 },
  { icon: "user", body: t.step2 },
  { icon: "referral", body: t.step3 },
  { icon: "cashback", body: t.step4 },
];

export interface StepExplainerProps {
  /** render the lead-in onboarding headline above the grid. Default OFF so
   *  /dai-ly keeps just the "Cách hoạt động" title. */
  intro?: boolean;
}

export function StepExplainer({ intro = false }: StepExplainerProps) {
  return (
    <section className="flex flex-col gap-space-4 items-center" aria-label={t.stepsHeading}>
      {intro ? (
        <p className="text-t-body text-text-mid text-center leading-lh-body max-w-[48ch] [margin:0_auto]">{t.stepsIntro}</p>
      ) : (
        <h2 className="promo-type-h4 text-text-hi self-start">{t.stepsHeading}</h2>
      )}
      <ol className="grid grid-cols-[1fr] gap-space-5 w-full max-w-[320px] [margin:0_auto] list-none p-[0] min-[640px]:grid-cols-[repeat(2,1fr)] min-[640px]:w-fit min-[640px]:max-w-none">
        {STEPS.map((s, i) => (
          <li key={s.body} className="flex flex-col items-center gap-space-2 min-[640px]:w-[214px]">
            {/* colorful gradient banner (.step_img is an illustration; we own
             *  no art, so each step gets a distinct brand-palette gradient +
             *  icon + faded number — a premium, original stand-in). */}
            <span
              className={[
                "relative overflow-hidden flex items-center justify-center w-full aspect-[16/9] rounded-md",
                [
                  "[background:var(--brand-accent)] text-brand-on-accent",
                  "[background:var(--info)] text-canvas",
                  "[background:var(--win)] text-canvas",
                  "[background:var(--loss)] text-canvas",
                ][i],
              ].join(" ")}
              aria-hidden="true"
            >
              <Icon name={s.icon} size={34} className="relative z-[1]" />
              <span className="absolute right-[10px] bottom-[-2px] font-brand-font-num text-[46px] font-weight-bold leading-[1] [color:inherit] opacity-[0.22]">{i + 1}</span>
            </span>
            <span className="text-t-sm text-text-mid leading-[1.5] text-center">
              <span className="text-text font-weight-semi">{i + 1}.</span> {s.body}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}

/* Luxury VIP — small-caps section heading in the h3 type role. */
import type { ReactNode } from "react";

export function VipSectionHeading({ children }: { children: ReactNode }) {
  return (
    <h2 className="vip-type-h3 [font-variant-caps:small-caps] tracking-[0.06em] text-vip-gold-mid m-[0]">
      {children}
    </h2>
  );
}

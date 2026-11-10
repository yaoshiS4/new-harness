/* ============================================================================
 * VipSection — a thin titled-section wrapper used by the VIP + ladder pages to
 * keep consistent vertical rhythm and headings. Presentational, SC-safe.
 * ==========================================================================*/

import type { ReactNode } from "react";
import { Icon, type IconName } from "@/ui";

export interface VipSectionProps {
  title: string;
  icon?: IconName;
  /** optional right-aligned link/action node */
  action?: ReactNode;
  children: ReactNode;
}

export function VipSection({ title, icon, action, children }: VipSectionProps) {
  return (
    <section className="flex flex-col gap-space-4" aria-label={title}>
      <div className="flex items-center justify-between gap-space-3">
        <h2 className="inline-flex items-center gap-space-2 text-t-h2 font-weight-bold text-text-hi">
          {icon && <Icon name={icon} size={20} className="text-brand-accent-fg" />}
          {title}
        </h2>
        {action}
      </div>
      {children}
    </section>
  );
}

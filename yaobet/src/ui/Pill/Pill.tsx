/* ============================================================================
 * Pill — selectable filter chip (Chip). Used in promo/category
 * tab+filter strips and lucky deposit-amount chips. Active = gold; ≥--tap-min
 * tappable. Renders as <button> (toggle) by default.
 * ==========================================================================*/

import type { ReactNode } from "react";
import { Icon, type IconName } from "../Icon/Icon";

export interface PillProps {
  children: ReactNode;
  active?: boolean;
  disabled?: boolean;
  icon?: IconName;
  onClick?: () => void;
  className?: string;
  /** semantic role for filter groups */
  "aria-pressed"?: boolean;
}

export function Pill({
  children,
  active = false,
  disabled = false,
  icon,
  onClick,
  className,
  ...rest
}: PillProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      aria-pressed={rest["aria-pressed"] ?? active}
      className={["ui-pill", active ? "ui-pill-active" : "", className]
        .filter(Boolean)
        .join(" ")}
      onClick={onClick}
    >
      {icon && <Icon name={icon} className="ui-pill-icon" />}
      {children}
    </button>
  );
}

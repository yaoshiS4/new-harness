/* ============================================================================
 * Button — every actionable button. Variants gold / primary (the gold
 * primary with the sheen) / ghost (the quiet ivory action) / danger (the
 * register CTA, reading --brand-cta-accent) / destructive (the --error
 * outline). ≥--tap-min (44px) enforced; bottom-bar callers pass
 * size="bar" for ≥48px. Loading is single-flight: blocks re-submit + shows a
 * spinner. Reads --brand-* / semantic vars only.
 * ==========================================================================*/

import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Icon, type IconName } from "../Icon/Icon";

export type ButtonVariant =
  | "gold"
  | "primary"
  | "ghost"
  | "danger"
  | "destructive";
export type ButtonSize = "sm" | "md" | "lg" | "bar";

export interface ButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children"> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  /** leading icon name from the Icon sprite */
  icon?: IconName;
  loading?: boolean;
  fullWidth?: boolean;
  children?: ReactNode;
}

export function Button({
  variant = "primary",
  size = "md",
  icon,
  loading = false,
  fullWidth = false,
  disabled,
  type = "button",
  className,
  children,
  onClick,
  ...rest
}: ButtonProps) {
  const blocked = disabled || loading;
  return (
    <button
      type={type}
      disabled={blocked}
      aria-busy={loading || undefined}
      data-loading={loading || undefined}
      className={[
        "ui-btn",
        `ui-btn-${variant}`,
        `ui-btn-${size}`,
        fullWidth ? "ui-btn-full" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      // single-flight: a loading button never re-fires its handler
      onClick={loading ? undefined : onClick}
      {...rest}
    >
      {loading && <span className="ui-btn-spinner" aria-hidden="true" />}
      {!loading && icon && <Icon name={icon} className="ui-btn-icon" />}
      {children != null && <span className="ui-btn-label">{children}</span>}
    </button>
  );
}

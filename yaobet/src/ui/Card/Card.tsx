/* ============================================================================
 * Card — the ONE card chassis every surface inherits (the
 * .common_box analog): --radius-card box, solid --card-bg fill, a decorative
 * --border hairline and the level 1 --lift shadow (none when nested in another
 * card, a modal or a sheet). No glow, no gradient. Lit/active = a solid 8%
 * accent film + solid accent border. Interactive cards hover →
 * uniform scale(1.02) + border colour shift on pointer (icons inside ride at
 * 1.10), press scale(.98) on touch; reduced-motion → colour shift only.
 * Renders as <a> when `href` is set, else <div> (or <button> when interactive
 * + onClick).
 * ==========================================================================*/

import Link from "next/link";
import type { ReactNode } from "react";

export type CardVariant = "default" | "rail" | "promo" | "product" | "vip" | "tile";

export interface CardProps {
  variant?: CardVariant;
  interactive?: boolean;
  href?: string;
  /** lit/active state — inner gold glow */
  active?: boolean;
  className?: string;
  children?: ReactNode;
  onClick?: () => void;
  "aria-label"?: string;
}

export function Card({
  variant = "default",
  interactive = false,
  href,
  active = false,
  className,
  children,
  onClick,
  ...rest
}: CardProps) {
  const cls = [
    "ui-card",
    `ui-card-${variant}`,
    interactive ? "ui-card-interactive" : "",
    active ? "ui-card-active" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  if (href) {
    return (
      <Link href={href} className={cls} onClick={onClick} {...rest}>
        {children}
      </Link>
    );
  }
  if (interactive && onClick) {
    return (
      <button type="button" className={cls} onClick={onClick} {...rest}>
        {children}
      </button>
    );
  }
  return (
    <div className={cls} {...rest}>
      {children}
    </div>
  );
}

/* ============================================================================
 * EmptyState — honest "chưa có dữ liệu / không có kết quả".
 * NEVER filler, never fabricated activity. Backs the cashback/records/messages/
 * referral honest-empty Done-Whens. `filtered` variant adds a reset action for
 * a filtered-empty list (e.g. records with an active filter).
 * ==========================================================================*/

import type { ReactNode } from "react";
import { Icon, type IconName } from "../Icon/Icon";
import { Button } from "../Button/Button";

export interface EmptyStateProps {
  /** default = no data yet; filtered = filter matched nothing (offers reset) */
  variant?: "default" | "filtered";
  icon?: IconName;
  title?: string;
  message?: ReactNode;
  /** reset action — shown by default in the filtered variant */
  onReset?: () => void;
  resetLabel?: string;
  className?: string;
}

export function EmptyState({
  variant = "default",
  icon = "empty",
  title,
  message,
  onReset,
  resetLabel = "Đặt lại bộ lọc",
  className,
}: EmptyStateProps) {
  const defaultTitle =
    variant === "filtered" ? "Không có kết quả" : "Chưa có dữ liệu";
  return (
    <div className={["ui-empty", className].filter(Boolean).join(" ")} role="status">
      <Icon name={icon} size={40} className="ui-empty-icon" />
      <p className="ui-empty-title">{title ?? defaultTitle}</p>
      {message && <p className="ui-empty-message">{message}</p>}
      {onReset && (
        <Button variant="ghost" size="sm" onClick={onReset} className="ui-empty-action">
          {resetLabel}
        </Button>
      )}
    </div>
  );
}

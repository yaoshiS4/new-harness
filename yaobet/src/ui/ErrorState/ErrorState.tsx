/* ============================================================================
 * ErrorState — fetch-failure surface. Message + retry,
 * network-aware. This is the HONEST fallback when a dynamic fetch fails:
 * it NEVER shows a fabricated/stale number as live — it shows an honest
 * error and a retry that re-issues the server fetch.
 * ==========================================================================*/

"use client";

import { useEffect, useState, type ReactNode } from "react";
import { Icon } from "../Icon/Icon";
import { Button } from "../Button/Button";

export interface ErrorStateProps {
  title?: string;
  message?: ReactNode;
  /** re-issues the server fetch; component shows a retrying state while awaited */
  onRetry?: () => void | Promise<void>;
  retryLabel?: string;
  className?: string;
}

export function ErrorState({
  title = "Không tải được dữ liệu",
  message,
  onRetry,
  retryLabel = "Thử lại",
  className,
}: ErrorStateProps) {
  const [online, setOnline] = useState(true);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    const update = () => setOnline(navigator.onLine);
    update();
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);

  const handleRetry = async () => {
    if (!onRetry) return;
    setRetrying(true);
    try {
      await onRetry();
    } finally {
      setRetrying(false);
    }
  };

  const resolvedMessage =
    message ?? (online ? "Đã xảy ra lỗi. Vui lòng thử lại." : "Mất kết nối mạng. Kiểm tra kết nối rồi thử lại.");

  return (
    <div className={["ui-error", className].filter(Boolean).join(" ")} role="alert">
      <Icon name="warning" size={40} className="ui-error-icon" />
      <p className="ui-error-title">{title}</p>
      <p className="ui-error-message">{resolvedMessage}</p>
      {onRetry && (
        <Button
          variant="ghost"
          size="sm"
          icon="retry"
          loading={retrying}
          onClick={handleRetry}
          className="ui-error-action"
        >
          {retryLabel}
        </Button>
      )}
    </div>
  );
}

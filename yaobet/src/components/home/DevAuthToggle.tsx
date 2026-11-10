/* ============================================================================
 * DevAuthToggle — a DEV-ONLY mock-auth state switcher. Lets QA flip guest →
 * level-0 → tiered to exercise every auth-aware home surface without a
 * backend. Collapsed by default, pinned top-left, and kept clear of the sticky
 * header / TopBar so it never overlaps real chrome. Not a product surface — it
 * renders only in development.
 *
 * Uses the mock session's `cycleDevState` (guest → level-0 → tiered → guest).
 * The unstyled `cycle` and `stateLabel` classes are hooks for the screenshot
 * capture script.
 * ==========================================================================*/

"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth/session";

const STATE_LABEL: Record<string, string> = {
  guest: "Khách",
  "level-0": "Cấp 0",
  tiered: "Hội viên",
};

export function DevAuthToggle() {
  const { authState, cycleDevState } = useAuth();
  const [open, setOpen] = useState(false);

  // dev-only: never ship to production chrome (hooks run unconditionally above).
  if (process.env.NODE_ENV === "production") return null;

  if (!open) {
    return (
      <button
        type="button"
        className="home-dev-auth-toggle-fab"
        onClick={() => setOpen(true)}
        aria-label="Mở bảng chuyển trạng thái đăng nhập (dev)"
        title="Dev: auth state"
      >
        DEV
      </button>
    );
  }

  return (
    <div className="home-dev-auth-toggle-panel" role="group" aria-label="Trạng thái đăng nhập (dev)">
      <div className="home-dev-auth-toggle-row">
        <span className="home-dev-auth-toggle-tag">DEV · AUTH</span>
        <button
          type="button"
          className="home-dev-auth-toggle-close"
          onClick={() => setOpen(false)}
          aria-label="Đóng"
        >
          ×
        </button>
      </div>
      <button type="button" className="home-dev-auth-toggle-cycle cycle" onClick={cycleDevState}>
        <span className="home-dev-auth-toggle-state-label stateLabel">{STATE_LABEL[authState] ?? authState}</span>
        <span className="home-dev-auth-toggle-hint">chạm để đổi</span>
      </button>
    </div>
  );
}

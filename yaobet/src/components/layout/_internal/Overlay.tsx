/* ============================================================================
 * Overlay (shell-local) — the lazy-mounted scrim + panel base the layout/auth
 * overlays compose (AuthModal, CategorySheet) until the shared ui/Sheet +
 * ui/Dialog land. ONE behaviour, two presentations:
 *   - presentation="sheet"  → bottom-pinned sheet (mobile; swipe-down + Esc +
 *                             scrim dismiss; safe-area-inset-bottom honoured)
 *   - presentation="dialog" → centred dialog (desktop)
 *   - presentation="auto"   → sheet <640 / dialog ≥640, chosen by
 *                             CSS so it is correct without JS measurement.
 *
 * NOT in the DOM until `open` (lazy-mounted — never a modal farm). SOLID scrim,
 * NEVER backdrop-filter:blur (lint). Reduced-motion → instant mount (motion.css
 * zeroes --dur-* + the stylesheet disables the slide). Focus-trapped with Esc and
 * return-focus via useFocusTrap; `returnFocus={false}` lets the FTD seam hand
 * focus to the next sheet instead.
 * ==========================================================================*/

"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { useFocusTrap } from "./useFocusTrap";

export interface OverlayProps {
  open: boolean;
  onClose: () => void;
  presentation?: "auto" | "sheet" | "dialog";
  /** swipe-down dismiss for the sheet presentation (mobile). */
  swipeDismiss?: boolean;
  /** return focus to the trigger on close. false during an FTD handoff. */
  returnFocus?: boolean;
  labelledBy?: string;
  describedBy?: string;
  className?: string;
  /** desktop/dialog max-width override (e.g. the 2-zone AuthModal needs 720px).
   *  Applied inline so it deterministically beats the stylesheet's default; the
   *  mobile sheet stays full-bleed via the @media reset in the stylesheet. */
  desktopMaxWidth?: number;
  children: ReactNode;
}

export function Overlay({
  open,
  onClose,
  presentation = "auto",
  swipeDismiss = true,
  returnFocus = true,
  labelledBy,
  describedBy,
  className,
  desktopMaxWidth,
  children,
}: OverlayProps) {
  const panelRef = useFocusTrap<HTMLDivElement>({ open, onClose, returnFocus });
  const startY = useRef<number | null>(null);
  const dragY = useRef(0);

  // lock body scroll while open (prevents the page behind from scrolling)
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  if (!open) return null; // lazy: NOT in DOM until triggered

  function onTouchStart(e: React.TouchEvent) {
    if (!swipeDismiss) return;
    startY.current = e.touches[0].clientY;
    dragY.current = 0;
  }
  function onTouchMove(e: React.TouchEvent) {
    if (startY.current == null) return;
    const dy = e.touches[0].clientY - startY.current;
    dragY.current = Math.max(0, dy);
    if (dragY.current > 0) {
      e.currentTarget.setAttribute("style", `transform:translateY(${dragY.current}px)`);
    }
  }
  function onTouchEnd(e: React.TouchEvent) {
    if (startY.current == null) return;
    e.currentTarget.removeAttribute("style");
    if (dragY.current > 96) onClose();
    startY.current = null;
    dragY.current = 0;
  }

  return (
    <div
      className="shell-overlay-scrim"
      // scrim click closes; clicks inside the panel don't bubble here
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        aria-describedby={describedBy}
        className={["shell-overlay-panel", `shell-overlay-${presentation}`, className]
          .filter(Boolean)
          .join(" ")}
        style={
          desktopMaxWidth
            ? ({ "--overlay-desktop-max": `${desktopMaxWidth}px` } as React.CSSProperties)
            : undefined
        }
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        {presentation !== "dialog" && (
          <span className="shell-overlay-grab" aria-hidden="true" />
        )}
        {children}
      </div>
    </div>
  );
}

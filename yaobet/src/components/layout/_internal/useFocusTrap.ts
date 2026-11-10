/* ============================================================================
 * useFocusTrap — focus-trap + Esc + return-focus for overlays (focus-return
 * contract). Shell-local helper for the layout/auth overlays
 * (Overlay, AuthModal, CategorySheet) until the shared ui/Sheet|Dialog land.
 *
 * - On open: records the trigger (activeElement), moves focus to the first
 *   focusable inside the container (or an explicit initialFocus ref).
 * - While open: Tab/Shift+Tab cycle inside; Esc invokes onClose.
 * - On close: returns focus to the recorded trigger UNLESS a handoff is
 *   requested (the FTD seam transfers focus into the next sheet instead).
 * ==========================================================================*/

"use client";

import { useCallback, useEffect, useRef, type RefObject } from "react";

const FOCUSABLE =
  'a[href],button:not([disabled]),textarea:not([disabled]),input:not([disabled]),select:not([disabled]),[tabindex]:not([tabindex="-1"])';

export interface FocusTrapOptions {
  open: boolean;
  onClose: () => void;
  /** when false, Esc/scrim still call onClose but focus is NOT auto-returned
   *  (the FTD handoff transfers focus into the next sheet itself). */
  returnFocus?: boolean;
  /** optional element to focus first instead of the first focusable. */
  initialFocus?: RefObject<HTMLElement | null>;
}

export function useFocusTrap<T extends HTMLElement>({
  open,
  onClose,
  returnFocus = true,
  initialFocus,
}: FocusTrapOptions): RefObject<T | null> {
  const containerRef = useRef<T | null>(null);
  const triggerRef = useRef<HTMLElement | null>(null);

  const focusables = useCallback((): HTMLElement[] => {
    const root = containerRef.current;
    if (!root) return [];
    return Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
      (el) => el.offsetParent !== null || el === document.activeElement,
    );
  }, []);

  useEffect(() => {
    if (!open) return;
    // record the trigger so focus can return on close.
    triggerRef.current = document.activeElement as HTMLElement | null;
    const target = initialFocus?.current ?? focusables()[0] ?? containerRef.current;
    target?.focus();

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.stopPropagation();
        onClose();
        return;
      }
      if (e.key !== "Tab") return;
      const items = focusables();
      if (items.length === 0) {
        e.preventDefault();
        return;
      }
      const first = items[0];
      const last = items[items.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (e.shiftKey && active === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && active === last) {
        e.preventDefault();
        first.focus();
      }
    }

    document.addEventListener("keydown", onKeyDown, true);
    return () => {
      document.removeEventListener("keydown", onKeyDown, true);
      if (returnFocus) triggerRef.current?.focus?.();
    };
    // initialFocus/focusables are stable refs/callbacks
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, onClose, returnFocus]);

  return containerRef;
}

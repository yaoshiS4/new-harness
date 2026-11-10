/* ============================================================================
 * Dropdown / Popover — the focus-trapped overlay anchored to a trigger.
 * The base for Select/DatePicker and the Wallet/Member/Category panels.
 * Opened by tap/click/focus — NEVER hover-only (matches CategoryRail). Esc
 * closes + returns focus to trigger; outside-click closes; `aria-expanded` on
 * the trigger. Panel reads --surface-3 / --z-dropdown / --radius-md.
 *
 * Self-contained: render a trigger node via `renderTrigger`, the panel via
 * `children`. The component owns open-state wiring + the a11y contract so
 * Select/DatePicker/WalletDropdown compose it without re-implementing it.
 * ==========================================================================*/

"use client";

import {
  cloneElement,
  isValidElement,
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type ReactElement,
  type ReactNode,
} from "react";

const FOCUSABLE =
  'a[href],button:not([disabled]),textarea,input,select,[tabindex]:not([tabindex="-1"])';

export type DropdownPlacement = "bottom-start" | "bottom-end";

export interface DropdownProps {
  /** the trigger element; the component injects ref + aria-expanded + onClick */
  trigger: ReactElement<Record<string, unknown>>;
  children: ReactNode;
  placement?: DropdownPlacement;
  /** controlled open (optional); omit for self-managed */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  className?: string;
  /** accessible label for the panel region */
  label?: string;
}

export function Dropdown({
  trigger,
  children,
  placement = "bottom-start",
  open: controlledOpen,
  onOpenChange,
  className,
  label,
}: DropdownProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = controlledOpen ?? internalOpen;
  const panelId = useId();
  const wrapRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const triggerWrapRef = useRef<HTMLDivElement>(null);

  const setOpen = useCallback(
    (next: boolean) => {
      if (controlledOpen == null) setInternalOpen(next);
      onOpenChange?.(next);
    },
    [controlledOpen, onOpenChange],
  );

  // focus into panel on open
  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => {
      const first = panelRef.current?.querySelector<HTMLElement>(FOCUSABLE);
      (first ?? panelRef.current)?.focus();
    }, 0);
    return () => clearTimeout(t);
  }, [open]);

  // Esc + focus-trap + outside-click
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        (triggerWrapRef.current?.querySelector<HTMLElement>(FOCUSABLE))?.focus();
        return;
      }
      if (e.key !== "Tab") return;
      const nodes = panelRef.current?.querySelectorAll<HTMLElement>(FOCUSABLE);
      if (!nodes || nodes.length === 0) return;
      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };
    const onDown = (e: MouseEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("keydown", onKey, true);
    document.addEventListener("mousedown", onDown, true);
    return () => {
      document.removeEventListener("keydown", onKey, true);
      document.removeEventListener("mousedown", onDown, true);
    };
  }, [open, setOpen]);

  // inject trigger props (tap/click/focus open — never hover-only)
  const triggerProps = (isValidElement(trigger) ? trigger.props : {}) as {
    onClick?: (e: React.MouseEvent) => void;
  };
  const triggerNode = isValidElement(trigger)
    ? cloneElement(trigger, {
        "aria-expanded": open,
        "aria-haspopup": "true",
        "aria-controls": open ? panelId : undefined,
        onClick: (e: React.MouseEvent) => {
          triggerProps.onClick?.(e);
          setOpen(!open);
        },
      })
    : trigger;

  return (
    <div className={["ui-dropdown", className].filter(Boolean).join(" ")} ref={wrapRef}>
      <div ref={triggerWrapRef} className="ui-dropdown-trigger-wrap">
        {triggerNode}
      </div>
      {open && (
        <div
          ref={panelRef}
          id={panelId}
          role="menu"
          aria-label={label}
          tabIndex={-1}
          className={["ui-dropdown-panel", `ui-dropdown-${placement}`].join(" ")}
        >
          {children}
        </div>
      )}
    </div>
  );
}

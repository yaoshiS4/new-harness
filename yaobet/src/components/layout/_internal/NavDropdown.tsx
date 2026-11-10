/* ============================================================================
 * NavDropdown (shell-local) — the desktop category-nav trigger + panel.
 * Opens on tap/click/focus AND on hover with a 120ms hover-intent
 * delay — NEVER hover-only (keyboard + touch reach it). `aria-expanded` on the
 * trigger; Esc + outside-click + blur-out close. Panel uses --z-dropdown and an
 * opaque --surface fill (no transparent sticky chrome).
 * ==========================================================================*/

"use client";

import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { Icon, type IconName } from "@/ui/Icon/Icon";

const HOVER_INTENT_MS = 120;

export interface NavDropdownProps {
  label: string;
  active?: boolean;
  /** leading per-vertical glyph (iconographic nav). Decorative. */
  icon?: IconName;
  /** when omitted the trigger is a plain link with no panel (caret hidden). */
  panel?: ReactNode;
  href?: string;
}

export function NavDropdown({ label, active, icon, panel, href }: NavDropdownProps) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const panelId = useId();
  const hasPanel = panel != null;

  useEffect(() => {
    if (!open) return;
    function onDocDown(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function clearTimer() {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
  }
  function hoverOpen() {
    if (!hasPanel) return;
    clearTimer();
    timer.current = setTimeout(() => setOpen(true), HOVER_INTENT_MS);
  }
  function hoverClose() {
    clearTimer();
    timer.current = setTimeout(() => setOpen(false), HOVER_INTENT_MS);
  }

  const Trigger = href ? "a" : "button";

  return (
    <div
      ref={wrapRef}
      className="shell-nav-dropdown-wrap"
      onMouseEnter={hoverOpen}
      onMouseLeave={hoverClose}
      onBlur={(e) => {
        if (!wrapRef.current?.contains(e.relatedTarget as Node)) setOpen(false);
      }}
    >
      <Trigger
        type={href ? undefined : "button"}
        href={href}
        className={["shell-nav-dropdown-trigger", active ? "shell-nav-dropdown-active" : ""]
          .filter(Boolean)
          .join(" ")}
        aria-expanded={hasPanel ? open : undefined}
        aria-controls={hasPanel ? panelId : undefined}
        onClick={() => {
          if (hasPanel) setOpen((o) => !o);
        }}
        onFocus={() => {
          if (hasPanel) setOpen(true);
        }}
      >
        {icon && <Icon name={icon} size={20} className="shell-nav-dropdown-icon" />}
        <span>{label}</span>
        {hasPanel && (
          <Icon name="chevronDown" size={16} className="shell-nav-dropdown-caret" />
        )}
      </Trigger>

      {hasPanel && open && (
        <div id={panelId} className="shell-nav-dropdown-panel" role="region" aria-label={label}>
          {panel}
        </div>
      )}
    </div>
  );
}

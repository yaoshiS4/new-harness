/* ============================================================================
 * Scroller — the ONE horizontal-scroll primitive. Every @375
 * strip and wide matrix composes it (no per-component scroll hacks): 16px peek
 * (--gutter), CSS scroll-snap, momentum without scroll-hijack, edge fades.
 * `freezeFirstColumn` pins column 1 while the rest scrolls — for the privilege
 * / club comparison matrices' frozen-first-column @375.
 *
 * The page body never scrolls horizontally (globals.css overflow-x:hidden);
 * wide content scrolls inside THIS, in its own overflow-x container.
 * ==========================================================================*/

"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

export interface ScrollerProps {
  children: ReactNode;
  /** enable scroll-snap on children (default true) */
  snap?: boolean;
  /** show 16px peek of the next item (default true) */
  peek?: boolean;
  /** pin the first column (matrix mode) */
  freezeFirstColumn?: boolean;
  /** aria role/label for the scroll region */
  label?: string;
  className?: string;
}

export function Scroller({
  children,
  snap = true,
  peek = true,
  freezeFirstColumn = false,
  label,
  className,
}: ScrollerProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [edge, setEdge] = useState<{ start: boolean; end: boolean }>({
    start: true,
    end: false,
  });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const update = () => {
      const atStart = el.scrollLeft <= 1;
      const atEnd = el.scrollLeft + el.clientWidth >= el.scrollWidth - 1;
      setEdge({ start: atStart, end: atEnd });
    };
    update();
    el.addEventListener("scroll", update, { passive: true });
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => {
      el.removeEventListener("scroll", update);
      ro.disconnect();
    };
  }, []);

  return (
    <div
      className={[
        "ui-scroller",
        edge.start ? "" : "ui-scroller-fade-start",
        edge.end ? "" : "ui-scroller-fade-end",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <div
        ref={ref}
        className={[
          "ui-scroller-rail",
          snap ? "ui-scroller-snap" : "",
          peek ? "ui-scroller-peek" : "",
          freezeFirstColumn ? "ui-scroller-freeze" : "",
        ]
          .filter(Boolean)
          .join(" ")}
        role="group"
        aria-label={label}
        tabIndex={0}
      >
        {children}
      </div>
    </div>
  );
}

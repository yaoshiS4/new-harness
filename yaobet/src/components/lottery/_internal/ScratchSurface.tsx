/* ============================================================================
 * ScratchSurface — a REAL scratch-off coating over one section of the card.
 *
 * ONE CANVAS PER SECTION, never one per cell. That is the whole point: a single
 * drag has to sweep continuously across several values. A per-cell control that
 * flips on click is the thing this replaces.
 *
 * HOW IT ERASES
 *   The real values live in the DOM UNDERNEATH (`children`). A <canvas> sits on
 *   top, painted by coverArt with the medallion coating. Scratching draws with
 *   globalCompositeOperation = "destination-out", which removes coating pixels
 *   instead of adding paint. Strokes run along the INTERPOLATED PATH between
 *   successive pointer samples (plus getCoalescedEvents where the browser
 *   offers it), with round caps and joins — so a fast flick leaves a continuous
 *   stroke and never a dotted line.
 *
 *   Pointer Events + setPointerCapture: one code path for mouse, touch and
 *   stylus, and the drag survives leaving the canvas. `touch-action: none` in
 *   the module stops the gesture from scrolling the page on mobile.
 *
 * HOW IT KNOWS WHEN TO STOP
 *   getImageData is expensive, so progress is NOT measured per frame. Every
 *   SAMPLE_MS at most, one read is taken and walked on a stride-SAMPLE_STEP
 *   grid (a few thousand samples, not a few hundred thousand pixels). At
 *   CLEAR_THRESHOLD the remainder fades out on its own and the section settles:
 *   nobody has to scrub the corners.
 *
 * ACCESSIBILITY
 *   The canvas is decoration — aria-hidden, never focusable, never the only way
 *   to reach a value. The parent owns `revealed`, exposes the DOM underneath to
 *   assistive tech when it flips, and offers "Mở tất cả" as the keyboard and
 *   screen-reader path. Under prefers-reduced-motion the coating is removed
 *   INSTANTLY — the scratch gesture is user-driven and stays, but nothing
 *   animates on its own.
 *
 * DPR
 *   The backing store is scaled by devicePixelRatio and the transform is reset
 *   on every resize, so the coating stays crisp and the erased stroke lands
 *   exactly under the pointer.
 * ==========================================================================*/

"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  paintCover,
  readCoverPalette,
  type CoinSpot,
  type CoverPalette,
  type CoverVariant,
} from "./coverArt";

/** Brush diameter in CSS px, per section. Wide enough that one sweep clears a
 *  row; narrow enough that the coating comes off as a stroke, not a wipe. */
const BRUSH: Record<CoverVariant, number> = { band: 34, field: 42 };
/** Alpha-sampling throttle (ms). getImageData never runs on the hot path. */
const SAMPLE_MS = 120;
/** Downsample stride, in DEVICE px, for the coverage walk. */
const SAMPLE_STEP = 6;
/** A sampled pixel counts as cleared below this alpha. */
const ALPHA_CLEAR = 24;
/** Erased fraction at which the rest fades on its own. */
const CLEAR_THRESHOLD = 0.58;
/** Fade of the remaining coating (ms). Mirrors --dur-slow; JS-side only. */
const CLEAR_MS = 320;
/** Backing-store cap: beyond 3x the extra pixels only cost memory. */
const MAX_DPR = 3;

interface Point {
  x: number;
  y: number;
}

export interface ScratchSurfaceProps {
  variant: CoverVariant;
  /** owned by the card: true once this section has settled (scratch or "Mở tất cả") */
  revealed: boolean;
  /** fired once, when the erased fraction crosses the threshold */
  onReveal: () => void;
  /** OS reduced-motion — removes the fade, keeps the (user-driven) gesture */
  reduced: boolean;
  /** the well chrome; the host also carries position + radius from the module */
  className?: string;
  /** the real values — always in the DOM, never painted into the canvas */
  children: ReactNode;
}

/** Coin centres are MEASURED from the live `[data-token]` elements rather than
 *  recomputed from a grid formula, so the coating always lands on the values
 *  underneath whatever the breakpoint does to the layout. */
function readSpots(host: HTMLElement): CoinSpot[] {
  const box = host.getBoundingClientRect();
  const out: CoinSpot[] = [];
  for (const el of Array.from(host.querySelectorAll<HTMLElement>("[data-token]"))) {
    const r = el.getBoundingClientRect();
    if (r.width < 6 || r.height < 6) continue;
    out.push({
      x: r.left - box.left + r.width / 2,
      y: r.top - box.top + r.height / 2,
      r: Math.min(r.width, r.height) / 2,
    });
  }
  return out;
}

export function ScratchSurface({
  variant,
  revealed,
  onReveal,
  reduced,
  className,
  children,
}: ScratchSurfaceProps) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  /** the palette read, cached for the life of the surface (never per frame) */
  const paletteRef = useRef<CoverPalette | null>(null);
  const sizeRef = useRef({ w: 0, h: 0, dpr: 0 });
  const lastRef = useRef<Point | null>(null);
  const drawingRef = useRef(false);
  const sampledAtRef = useRef(0);
  /** latched the moment the threshold is crossed, so it can only fire once */
  const doneRef = useRef(false);
  const timerRef = useRef<number | null>(null);
  /** onReveal is called from a timeout — read it through a ref, not a closure */
  const revealRef = useRef(onReveal);

  /** true only while the remainder is fading; drives the CSS opacity hand-off */
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    revealRef.current = onReveal;
  });

  /* ---- paint + keep the backing store in step with the CSS box ---------- */
  useEffect(() => {
    if (revealed) return;
    const host = hostRef.current;
    const canvas = canvasRef.current;
    if (!host || !canvas) return;

    // willReadFrequently: the coating is painted once and its alpha is read
    // many times, which is exactly the case this hint exists for.
    const ctx = canvas.getContext("2d", { willReadFrequently: true });
    if (!ctx) return;
    ctxRef.current = ctx;
    paletteRef.current ??= readCoverPalette(host);

    const paint = () => {
      const box = host.getBoundingClientRect();
      const w = Math.round(box.width);
      const h = Math.round(box.height);
      if (w < 8 || h < 8) return;
      const dpr = Math.min(window.devicePixelRatio || 1, MAX_DPR);
      const size = sizeRef.current;
      if (size.w === w && size.h === h && size.dpr === dpr) return; // no-op resize
      sizeRef.current = { w, h, dpr };

      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      // reset the transform on every resize — setting width/height clears it,
      // and a stale scale is what makes the stroke drift off the pointer.
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.globalCompositeOperation = "source-over";
      paintCover(ctx, w, h, readSpots(host), paletteRef.current!, variant);
    };

    paint();
    const ro = new ResizeObserver(paint);
    ro.observe(host);
    return () => ro.disconnect();
  }, [revealed, variant]);

  /* ---- one-shot timers must not outlive the surface -------------------- */
  useEffect(
    () => () => {
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
    },
    [],
  );

  function settle() {
    if (doneRef.current) return;
    doneRef.current = true;
    drawingRef.current = false;
    if (reduced) {
      revealRef.current(); // instant: no fade, no stagger
      return;
    }
    setClearing(true);
    timerRef.current = window.setTimeout(() => {
      timerRef.current = null;
      revealRef.current();
    }, CLEAR_MS);
  }

  /** Walk a stride grid of the alpha channel. Throttled — never per frame. */
  function sample(force: boolean) {
    const now = performance.now();
    if (!force && now - sampledAtRef.current < SAMPLE_MS) return;
    sampledAtRef.current = now;

    const ctx = ctxRef.current;
    const canvas = canvasRef.current;
    if (!ctx || !canvas) return;
    const cw = canvas.width;
    const ch = canvas.height;
    if (cw < 1 || ch < 1) return;

    const { data } = ctx.getImageData(0, 0, cw, ch);
    let total = 0;
    let clear = 0;
    for (let y = 0; y < ch; y += SAMPLE_STEP) {
      const row = y * cw;
      for (let x = 0; x < cw; x += SAMPLE_STEP) {
        total++;
        if (data[(row + x) * 4 + 3] < ALPHA_CLEAR) clear++;
      }
    }
    if (total > 0 && clear / total >= CLEAR_THRESHOLD) settle();
  }

  function localPoint(canvas: HTMLCanvasElement, clientX: number, clientY: number): Point {
    const box = canvas.getBoundingClientRect();
    return { x: clientX - box.left, y: clientY - box.top };
  }

  function onPointerDown(e: React.PointerEvent<HTMLCanvasElement>) {
    if (doneRef.current) return;
    const canvas = e.currentTarget;
    const ctx = ctxRef.current;
    if (!ctx) return;
    // capture so the stroke survives the pointer leaving the canvas
    canvas.setPointerCapture(e.pointerId);
    drawingRef.current = true;

    const p = localPoint(canvas, e.clientX, e.clientY);
    lastRef.current = p;
    ctx.globalCompositeOperation = "destination-out";
    ctx.beginPath();
    ctx.arc(p.x, p.y, BRUSH[variant] / 2, 0, Math.PI * 2);
    ctx.fill();
  }

  function onPointerMove(e: React.PointerEvent<HTMLCanvasElement>) {
    if (!drawingRef.current || doneRef.current) return;
    const ctx = ctxRef.current;
    const last = lastRef.current;
    if (!ctx || !last) return;

    const canvas = e.currentTarget;
    const box = canvas.getBoundingClientRect();
    const native = e.nativeEvent;
    // every intermediate sample the browser buffered between frames — a fast
    // drag then erases the path it actually took, not a straight chord
    const batch =
      typeof native.getCoalescedEvents === "function"
        ? native.getCoalescedEvents()
        : [native];

    ctx.globalCompositeOperation = "destination-out";
    ctx.lineWidth = BRUSH[variant];
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.beginPath();
    ctx.moveTo(last.x, last.y);
    let nx = last.x;
    let ny = last.y;
    for (const pe of batch) {
      nx = pe.clientX - box.left;
      ny = pe.clientY - box.top;
      ctx.lineTo(nx, ny);
    }
    ctx.stroke();
    lastRef.current = { x: nx, y: ny };

    sample(false);
  }

  function onPointerEnd() {
    if (!drawingRef.current) return;
    drawingRef.current = false;
    lastRef.current = null;
    sample(true); // one guaranteed read on release, so a last sweep counts
  }

  return (
    <div
      ref={hostRef}
      className={["relative", className].filter(Boolean).join(" ")}
      data-revealed={revealed || undefined}
    >
      {children}
      {!revealed && (
        <canvas
          ref={canvasRef}
          className="lottery-scratch-surface-cover absolute inset-[0] block w-full h-full rounded-[inherit] touch-none select-none cursor-grab active:cursor-grabbing"
          data-clearing={clearing || undefined}
          /* decoration only: every value it hides is in the DOM above */
          aria-hidden="true"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerEnd}
          onPointerCancel={onPointerEnd}
          onLostPointerCapture={onPointerEnd}
        />
      )}
    </div>
  );
}

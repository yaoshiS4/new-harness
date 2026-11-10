/* ============================================================================
 * coverArt — the scratch COATING, painted into a <canvas> with 2D gradients.
 *
 * NO IMAGE FILES, NO DEPENDENCIES. Every pixel of the cover is drawn here, so
 * the coating re-skins with the brand instead of shipping a baked PNG of one
 * palette that a [data-brand] switch would silently contradict.
 *
 * WHERE THE COLOURS COME FROM
 *   readCoverPalette() reads the SAME custom properties the stylesheets read —
 *   --brand-accent / --brand-accent-2 / --canvas / --text-hi — off the live
 *   element via getComputedStyle. Nothing here hardcodes a brand hex except the
 *   FALLBACK, which only ever applies if a token is missing entirely. Custom
 *   properties compute with var() already substituted, so --brand-accent comes
 *   back as the resolved literal and not as "var(--gold-500)".
 *
 *   The read is one getComputedStyle call per surface MOUNT. The caller caches
 *   it in a ref; it must never run per frame (it forces style resolution).
 *
 * WHAT IT LOOKS LIKE
 *   A struck-metal medallion per value — radial body, darker rim with knurling,
 *   an inner bevel ring, a five-point star, and a specular highlight offset to
 *   the upper-left — sitting on a brushed foil field. The field matters: with
 *   it, erasing reads as coating coming AWAY; without it, erasing reads as
 *   holes appearing.
 *
 * TWO CHROMES. `variant` separates the small precious band (winning numbers)
 * from the main field (the 4x3 grid) — denser knurl, brighter ground and a
 * double rim on the band — so the two sections can never be confused.
 * ==========================================================================*/

/** sRGB triple, 0–255. Alpha is applied at use-site, never carried here. */
export type Rgb = readonly [number, number, number];

export interface CoverPalette {
  /** --brand-accent — the gold the coin body is struck from */
  accent: Rgb;
  /** --brand-accent-2 — the pressed/darker step, used for rim + shade */
  accent2: Rgb;
  /** --canvas — the deep ground everything is shaded toward */
  ink: Rgb;
  /** --text-hi — champagne, the specular/sheen colour */
  light: Rgb;
}

export interface CoinSpot {
  /** centre, in CSS px relative to the canvas box */
  x: number;
  y: number;
  /** coin radius, in CSS px */
  r: number;
}

export type CoverVariant = "band" | "field";

/** Only reached if a token is absent from the cascade entirely. */
const FALLBACK: CoverPalette = {
  accent: [212, 175, 55],
  accent2: [180, 149, 47],
  ink: [10, 10, 10],
  light: [242, 240, 228],
};

const TAU = Math.PI * 2;

/* ----------------------------------------------------------------------------
 * COLOUR — parse the token, then mix in JS.
 * `color-mix()` is not reliably accepted by canvas fillStyle, so the blending
 * the stylesheets do with color-mix() is done here numerically instead.
 * --------------------------------------------------------------------------*/

function clamp255(n: number): number {
  return n < 0 ? 0 : n > 255 ? 255 : Math.round(n);
}

/** Accepts `#abc`, `#aabbcc(aa)`, `rgb(…)`, `rgba(…)`. Anything else → fallback. */
function parseColor(raw: string, fallback: Rgb): Rgb {
  const s = raw.trim();
  if (!s) return fallback;

  if (s.charCodeAt(0) === 35 /* # */) {
    const hex = s.slice(1);
    const short = hex.length === 3 || hex.length === 4;
    const long = hex.length === 6 || hex.length === 8;
    if (!short && !long) return fallback;
    const cut = (i: number) =>
      short ? hex[i] + hex[i] : hex.slice(i * 2, i * 2 + 2);
    const rgb = [0, 1, 2].map((i) => parseInt(cut(i), 16));
    return rgb.some(Number.isNaN) ? fallback : [rgb[0], rgb[1], rgb[2]];
  }

  // rgb()/rgba(), comma or space separated
  const nums = s.match(/-?\d*\.?\d+/g);
  if (nums && nums.length >= 3) {
    return [clamp255(+nums[0]), clamp255(+nums[1]), clamp255(+nums[2])];
  }
  return fallback;
}

/** Linear blend, t=0 → a, t=1 → b. */
function mix(a: Rgb, b: Rgb, t: number): Rgb {
  return [
    clamp255(a[0] + (b[0] - a[0]) * t),
    clamp255(a[1] + (b[1] - a[1]) * t),
    clamp255(a[2] + (b[2] - a[2]) * t),
  ];
}

function css(c: Rgb): string {
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

function rgba(c: Rgb, alpha: number): string {
  return `rgba(${c[0]}, ${c[1]}, ${c[2]}, ${alpha})`;
}

/**
 * One getComputedStyle read of the four tokens the coating is struck from.
 * Call ONCE per surface (on mount) and cache the result — never per frame.
 */
export function readCoverPalette(el: Element): CoverPalette {
  const cs = getComputedStyle(el);
  const read = (name: string, fb: Rgb): Rgb =>
    parseColor(cs.getPropertyValue(name), fb);
  return {
    accent: read("--brand-accent", FALLBACK.accent),
    accent2: read("--brand-accent-2", FALLBACK.accent2),
    ink: read("--canvas", FALLBACK.ink),
    light: read("--text-hi", FALLBACK.light),
  };
}

/* ----------------------------------------------------------------------------
 * SHAPES
 * --------------------------------------------------------------------------*/

function roundRectPath(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
): void {
  const rad = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rad, y);
  ctx.lineTo(x + w - rad, y);
  ctx.arcTo(x + w, y, x + w, y + rad, rad);
  ctx.lineTo(x + w, y + h - rad);
  ctx.arcTo(x + w, y + h, x + w - rad, y + h, rad);
  ctx.lineTo(x + rad, y + h);
  ctx.arcTo(x, y + h, x, y + h - rad, rad);
  ctx.lineTo(x, y + rad);
  ctx.arcTo(x, y, x + rad, y, rad);
  ctx.closePath();
}

function starPath(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  outer: number,
  inner: number,
  points: number,
): void {
  ctx.beginPath();
  for (let i = 0; i < points * 2; i++) {
    const rad = i % 2 === 0 ? outer : inner;
    const a = -Math.PI / 2 + (i * Math.PI) / points;
    const px = cx + Math.cos(a) * rad;
    const py = cy + Math.sin(a) * rad;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }
  ctx.closePath();
}

/** One struck coin: rim → knurl → bevelled body → inner ring → star → specular. */
function paintCoin(
  ctx: CanvasRenderingContext2D,
  spot: CoinSpot,
  pal: CoverPalette,
  variant: CoverVariant,
): void {
  const { x, y, r } = spot;
  if (r < 4) return;

  /* rim — a directional gradient so the coin has a lit side and a shaded one */
  const rim = ctx.createLinearGradient(x - r, y - r, x + r, y + r);
  rim.addColorStop(0, css(mix(pal.accent, pal.light, 0.5)));
  rim.addColorStop(0.45, css(pal.accent));
  rim.addColorStop(1, css(mix(pal.accent2, pal.ink, 0.4)));
  ctx.beginPath();
  ctx.arc(x, y, r, 0, TAU);
  ctx.fillStyle = rim;
  ctx.fill();

  /* knurling — short radial ticks around the rim; the band mills finer */
  const ticks = variant === "band" ? 44 : 30;
  ctx.strokeStyle = rgba(pal.ink, 0.26);
  ctx.lineWidth = Math.max(1, r * 0.05);
  for (let i = 0; i < ticks; i++) {
    const a = (i / ticks) * TAU;
    const c = Math.cos(a);
    const s = Math.sin(a);
    ctx.beginPath();
    ctx.moveTo(x + c * r * 0.985, y + s * r * 0.985);
    ctx.lineTo(x + c * r * 0.885, y + s * r * 0.885);
    ctx.stroke();
  }

  /* the band gets a second rule inside the rim — the "more precious" chrome */
  if (variant === "band") {
    ctx.beginPath();
    ctx.arc(x, y, r * 0.9, 0, TAU);
    ctx.lineWidth = Math.max(1, r * 0.035);
    ctx.strokeStyle = rgba(pal.light, 0.34);
    ctx.stroke();
  }

  /* body — radial gradient with its light centre pushed to the upper-left, so
   * the coin reads as struck metal rather than as a flat disc */
  const body = ctx.createRadialGradient(
    x - r * 0.34,
    y - r * 0.4,
    r * 0.05,
    x,
    y,
    r * 0.9,
  );
  body.addColorStop(0, css(mix(pal.accent, pal.light, 0.66)));
  body.addColorStop(0.4, css(pal.accent));
  body.addColorStop(0.8, css(pal.accent2));
  body.addColorStop(1, css(mix(pal.accent2, pal.ink, 0.45)));
  ctx.beginPath();
  ctx.arc(x, y, r * 0.84, 0, TAU);
  ctx.fillStyle = body;
  ctx.fill();

  /* inner bevel: a full shade ring, then a lit arc across its top-left */
  ctx.lineWidth = Math.max(1, r * 0.05);
  ctx.beginPath();
  ctx.arc(x, y, r * 0.7, 0, TAU);
  ctx.strokeStyle = rgba(pal.ink, 0.24);
  ctx.stroke();
  ctx.beginPath();
  ctx.arc(x, y, r * 0.7, Math.PI * 1.02, Math.PI * 1.9);
  ctx.strokeStyle = rgba(pal.light, 0.32);
  ctx.stroke();

  /* the motif */
  starPath(ctx, x, y, r * 0.44, r * 0.185, 5);
  const star = ctx.createLinearGradient(x, y - r * 0.46, x, y + r * 0.46);
  star.addColorStop(0, css(mix(pal.accent, pal.light, 0.78)));
  star.addColorStop(1, css(mix(pal.accent2, pal.ink, 0.24)));
  ctx.fillStyle = star;
  ctx.fill();
  ctx.lineWidth = Math.max(1, r * 0.03);
  ctx.strokeStyle = rgba(pal.ink, 0.3);
  ctx.stroke();

  /* specular — offset toward the top-left, clipped to the coin body */
  const spec = ctx.createRadialGradient(
    x - r * 0.4,
    y - r * 0.44,
    0,
    x - r * 0.4,
    y - r * 0.44,
    r * 0.62,
  );
  spec.addColorStop(0, rgba(pal.light, 0.5));
  spec.addColorStop(1, rgba(pal.light, 0));
  ctx.beginPath();
  ctx.arc(x, y, r * 0.84, 0, TAU);
  ctx.fillStyle = spec;
  ctx.fill();
}

/**
 * Paint the whole coating: brushed foil ground, sheen, a dashed inner rule as
 * the "this comes off" affordance, then one medallion per value.
 *
 * `w`/`h` are CSS px — the caller has already scaled the backing store by dpr
 * and set the transform, so everything below is authored in CSS pixels.
 */
export function paintCover(
  ctx: CanvasRenderingContext2D,
  w: number,
  h: number,
  spots: readonly CoinSpot[],
  pal: CoverPalette,
  variant: CoverVariant,
): void {
  ctx.save();
  ctx.globalCompositeOperation = "source-over";
  ctx.clearRect(0, 0, w, h);

  /* ground — a dark alloy of the accent, never flat black, so the coating
   * still reads as metal where no coin sits */
  const deep = variant === "band" ? 0.66 : 0.76;
  const ground = ctx.createLinearGradient(0, 0, w, h);
  ground.addColorStop(0, css(mix(pal.accent, pal.ink, deep - 0.08)));
  ground.addColorStop(0.5, css(mix(pal.accent, pal.ink, deep)));
  ground.addColorStop(1, css(mix(pal.accent2, pal.ink, deep + 0.06)));
  ctx.fillStyle = ground;
  ctx.fillRect(0, 0, w, h);

  /* brushed foil: paired light/dark diagonals. One-time cost at paint, and it
   * is what makes an erased patch look like coating lifting off. */
  ctx.save();
  ctx.beginPath();
  ctx.rect(0, 0, w, h);
  ctx.clip();
  ctx.lineWidth = 1;
  const step = variant === "band" ? 7 : 9;
  for (let pass = 0; pass < 2; pass++) {
    ctx.strokeStyle = pass === 0 ? rgba(pal.light, 0.05) : rgba(pal.ink, 0.11);
    const off = pass === 0 ? 0 : step / 2;
    for (let x = -h; x < w + h; x += step) {
      ctx.beginPath();
      ctx.moveTo(x + off, 0);
      ctx.lineTo(x + off + h, h);
      ctx.stroke();
    }
  }
  ctx.restore();

  /* sheen from the upper-left, matching the coins' light direction */
  const sheen = ctx.createRadialGradient(
    w * 0.18,
    -h * 0.15,
    0,
    w * 0.18,
    -h * 0.15,
    Math.max(w, h) * 1.05,
  );
  sheen.addColorStop(0, rgba(pal.light, 0.16));
  sheen.addColorStop(1, rgba(pal.light, 0));
  ctx.fillStyle = sheen;
  ctx.fillRect(0, 0, w, h);

  /* the affordance: a dashed rule just inside the edge */
  ctx.setLineDash([5, 6]);
  ctx.lineWidth = 1;
  ctx.strokeStyle = rgba(pal.light, 0.2);
  roundRectPath(ctx, 4.5, 4.5, w - 9, h - 9, variant === "band" ? 10 : 8);
  ctx.stroke();
  ctx.setLineDash([]);

  for (const spot of spots) paintCoin(ctx, spot, pal, variant);

  ctx.restore();
}

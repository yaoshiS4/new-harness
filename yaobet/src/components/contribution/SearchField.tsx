/* ============================================================================
 * SearchField — the ONE text input in the feature.
 * Hand-rolled (apps/web/src/ui/ has NO input primitive; nothing is added
 * to ui/ this round). It owns three things and nothing else:
 *
 *   1. FOLDING, and the order is the whole point:
 *        (1) lowercase → (2) đ→d / Đ→d  BEFORE  NFD → (3) NFD + strip
 *        U+0300–U+036F → (4) strip punctuation + collapse whitespace → (5) tokens.
 *      `đ` (U+0111) is NOT decomposed by NFD, so the naïve "NFD then strip marks"
 *      recipe never folds `Đá gà` to `da ga`. We fold it explicitly, first. The
 *      SAME fold is exported so the resolver applies it to provider names too.
 *
 *   2. The IME COMPOSITION GUARD: while `isComposing` is true NO query fires and
 *      NO debounce clock runs; the 250ms clock starts on `compositionend`
 *      (Telex types `nổ hũ` as noo→noor→nổ→nổ h→…; firing mid-composition flashes
 *      not-found at a user who is typing correctly). Minimum 2 chars.
 *
 *   3. A controlled value + a clearable ✕ (44×44) + a visually-hidden <label>.
 *      The field sits on --surface-3, so the placeholder reads
 *      --fg-muted-raised; the ✕ takes the shared inset focus ring.
 *
 * OFFLINE / JS-OFF: `offline` (JS-on, no network) disables the field and swaps
 * the hint to `searchOffline`. With JS disabled the SSR field is enhanced by a
 * <noscript> style that dims it and shows the offline hint (zero flash for the
 * JS-on happy path).
 * ==========================================================================*/

"use client";

import { useEffect, useRef } from "react";
import { Icon } from "@/ui/Icon/Icon";
import { vi } from "@/lib/i18n";

/** Fold a string to the search index form. đ→d BEFORE NFD (the trap most builds
 *  miss). Exported so the resolver folds provider names with the exact same rule. */
export function foldQuery(input: string): string {
  return input
    .toLowerCase() // (1)
    .replace(/đ/g, "d") // (2) Đ already lowercased to đ above — fold before NFD
    .normalize("NFD") // (3)
    .replace(/[̀-ͯ]/g, "") // strip the tone marks (combining diacritics)
    .replace(/[^a-z0-9\s]/g, " ") // (4) punctuation → space
    .replace(/\s+/g, " ")
    .trim(); // (5) split on whitespace happens at the call site
}

const DEBOUNCE_MS = 250;
const MIN_CHARS = 2;

export function SearchField({
  value,
  onChange,
  onCommit,
  offline = false,
}: {
  /** the raw, controlled value (drives the visible input + the clear ✕) */
  value: string;
  /** immediate raw-value update (controlled input) */
  onChange: (raw: string) => void;
  /** the FOLDED, debounced query — "" when below the 2-char minimum */
  onCommit: (folded: string) => void;
  /** JS-on-but-no-network: disable the field + swap the hint */
  offline?: boolean;
}) {
  const composingRef = useRef(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimer = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  };

  // handlers are recreated each render, so this closure always captures the
  // latest onCommit at call time — no ref needed.
  const scheduleCommit = (raw: string) => {
    clearTimer();
    timerRef.current = setTimeout(() => {
      const folded = foldQuery(raw);
      onCommit(folded.length >= MIN_CHARS ? folded : "");
    }, DEBOUNCE_MS);
  };

  // clean up a pending clock on unmount
  useEffect(() => clearTimer, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    onChange(raw);
    // no query fires and NO debounce clock runs while composing
    if (composingRef.current) return;
    scheduleCommit(raw);
  };

  const handleCompositionStart = () => {
    composingRef.current = true;
    clearTimer(); // stop any in-flight clock the moment composition begins
  };

  const handleCompositionEnd = (e: React.CompositionEvent<HTMLInputElement>) => {
    composingRef.current = false;
    scheduleCommit(e.currentTarget.value); // the clock starts on compositionend
  };

  const clear = () => {
    clearTimer();
    onChange("");
    onCommit("");
  };

  const showClear = value.length > 0 && !offline;

  // <noscript> enhancement — JS-off: dim the field + show the offline hint. The
  // selectors are the stable data-* hooks on this field's input and hints, so
  // these global rules match this field only. Zero flash for the JS-on path
  // (which never renders noscript content).
  const noscriptCss =
    `[data-search-input]{opacity:.5;pointer-events:none;}` +
    `[data-hint="live"]{display:none;}` +
    `[data-hint="offline"]{display:block;}`;

  return (
    <div className="flex flex-col gap-space-2 min-w-[0] w-full">
      {/* visually-hidden label (a11y) */}
      <label className="absolute w-[1px] h-[1px] p-[0] m-[-1px] overflow-hidden [clip:rect(0,0,0,0)] whitespace-nowrap [border:0]" htmlFor="contribution-search">
        {vi.contribution.searchLabel}
      </label>

      <div className="relative flex items-center h-tap-bar p-[1px] [background:var(--surface-3)] [border:1px_solid_var(--border)] rounded-md [transition:border-color_var(--dur-fast)_var(--ease-standard)] focus-within:[border-width:2px] focus-within:border-focus-ring focus-within:p-[0] motion-reduce:[transition:none]">
        <span className="inline-flex items-center justify-center px-space-3 text-text-mid text-t-body flex-[0_0_auto]" aria-hidden="true">
          <Icon name="search" />
        </span>
        <input
          id="contribution-search"
          type="text"
          inputMode="search"
          autoComplete="off"
          data-search-input
          className="flex-[1_1_auto] min-w-[0] h-full ps-[0] pe-space-3 [border:0] [background:transparent] text-text-hi font-brand-font-body text-t-body leading-lh-body placeholder:text-fg-muted-raised placeholder:opacity-100 disabled:cursor-not-allowed"
          placeholder={vi.contribution.searchPlaceholder}
          value={value}
          disabled={offline}
          onChange={handleChange}
          onCompositionStart={handleCompositionStart}
          onCompositionEnd={handleCompositionEnd}
        />
        {showClear && (
          <button
            type="button"
            className="flex-[0_0_auto] inline-flex items-center justify-center w-tap-min h-tap-min me-space-1 [background:transparent] [border:0] rounded-md text-text-mid cursor-pointer [transition:color_var(--dur-fast)_var(--ease-standard),transform_var(--dur-fast)_var(--ease-standard)] hover:text-text-hi hover:[transform:scale(1.05)] focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[-2px] motion-reduce:[transition:none] motion-reduce:hover:[transform:none]"
            aria-label={vi.contribution.searchClear}
            onClick={clear}
          >
            <Icon name="close" />
          </button>
        )}
      </div>

      {/* live hint (JS on): swaps to the offline copy when the field is disabled */}
      <p data-hint="live" className="text-text-mid text-t-sm leading-lh-tight">
        {offline ? vi.contribution.searchOffline : vi.contribution.searchHint}
      </p>
      {/* static offline hint — hidden unless the noscript style reveals it */}
      <p data-hint="offline" className="text-text-mid text-t-sm leading-lh-tight hidden">{vi.contribution.searchOffline}</p>

      <noscript>
        <style>{noscriptCss}</style>
      </noscript>
    </div>
  );
}

/* ============================================================================
 * RateFilters — the header IA for the conventional table (owner override,
 * decisions/2026-08-10). Category is NO LONGER a primary nav band; it is one of
 * three secondary filters under a PRIMARY, full-width search. This component owns
 * NO business logic — the island owns state; it renders controls + forwards.
 *
 *   1. PRIMARY — SearchField, full-width, on top (folds + debounces +
 *      IME-guards a query upward).
 *   2. SECONDARY — a filter bar with THREE filters that COMBINE (AND) with search
 *      and each other:
 *        · category  — a ui/Dropdown (Tất cả + the 8 categories in lobby order).
 *        · provider  — a ui/Dropdown (options DERIVED from the catalogue).
 *        · rate-%    — a segmented ui/Pill group (Tất cả · 100% · Một phần ·
 *          Không tính) in a role="group"; the active pill carries aria-pressed
 *          (Pill sets it from `active`). It filters rows by their category's rate
 *          bucket — the isolate-0% ("Không tính") bucket is an accepted tradeoff.
 * ==========================================================================*/

"use client";

import { useState } from "react";
import { Pill } from "@/ui/Pill/Pill";
import { Dropdown } from "@/ui/Dropdown/Dropdown";
import { Icon } from "@/ui/Icon/Icon";
import type { RateBucket } from "@/lib/mock";
import { vi } from "@/lib/i18n";
import { SearchField } from "./SearchField";

/** the rate-bucket filter value: a real bucket or the "all" pass-through */
export type BucketValue = RateBucket | "all";

interface Option {
  value: string;
  label: string;
}

/** One dropdown filter (category / provider) — a labelled trigger + a radio
 *  menu. Self-contained open-state; ui/Dropdown owns the a11y (focus-trap, Esc,
 *  outside-click, aria-expanded). The current label wraps inside the 44px
 *  trigger instead of clipping. */
function SelectFilter({
  small,
  panelLabel,
  value,
  options,
  onPick,
}: {
  /** the muted label baked into the trigger */
  small: string;
  /** accessible label for the popover panel */
  panelLabel: string;
  value: string;
  options: Option[];
  onPick: (value: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const current =
    options.find((o) => o.value === value)?.label ?? options[0]?.label ?? "";

  return (
    <div className="min-w-[0] min-[768px]:flex-[1_1_auto]">
      <Dropdown
        open={open}
        onOpenChange={setOpen}
        label={panelLabel}
        placement="bottom-start"
        trigger={
          <button type="button" className="group flex items-center gap-space-2 w-full min-h-tap-min py-space-2 px-space-3 [background:var(--surface)] [border:1px_solid_var(--border)] rounded-md text-text-hi font-brand-font-body text-t-sm cursor-pointer [transition:background-color_var(--dur-fast)_var(--ease-standard),border-color_var(--dur-fast)_var(--ease-standard)] hover:[background:var(--surface-hover)] hover:border-brand-accent-hairline focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 motion-reduce:[transition:none]">
            <span className="text-text-mid group-hover:text-fg-muted-raised flex-[0_0_auto]">{small}</span>
            <span className="flex-[1_1_auto] min-w-[0] text-left wrap-anywhere font-weight-semi">{current}</span>
            <Icon name="chevronDown" aria-hidden className="flex-[0_0_auto] text-text-mid text-t-body" />
          </button>
        }
      >
        <ul className="flex flex-col gap-space-1 list-none m-[0] p-[0]">
          {options.map((opt) => {
            const selected = opt.value === value;
            return (
              <li key={opt.value}>
                <button
                  type="button"
                  role="menuitemradio"
                  aria-checked={selected}
                  className={`flex items-center justify-between gap-space-3 w-full min-h-tap-min py-[0] px-space-3 [background:transparent] [border:0] rounded-sm font-brand-font-body text-t-sm text-left cursor-pointer hover:[background:var(--surface-hover)] hover:text-text-hi focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-2 ${selected ? "text-text-hi font-weight-semi" : "text-text"}`}
                  onClick={() => {
                    onPick(opt.value);
                    setOpen(false);
                  }}
                >
                  <span>{opt.label}</span>
                  {selected && <Icon name="check" aria-hidden />}
                </button>
              </li>
            );
          })}
        </ul>
      </Dropdown>
    </div>
  );
}

export function RateFilters({
  categories,
  providers,
  categoryId,
  provider,
  bucket,
  rawQuery,
  offline,
  onQueryChange,
  onCommit,
  onCategory,
  onProvider,
  onBucket,
}: {
  /** the 8 categories in LOBBY order — {id, name} */
  categories: { id: string; name: string }[];
  /** provider names derived from the catalogue */
  providers: string[];
  categoryId: string;
  provider: string;
  bucket: BucketValue;
  rawQuery: string;
  offline: boolean;
  onQueryChange: (raw: string) => void;
  onCommit: (folded: string) => void;
  onCategory: (id: string) => void;
  onProvider: (name: string) => void;
  onBucket: (b: BucketValue) => void;
}) {
  const categoryOptions: Option[] = [
    { value: "all", label: vi.contribution.filterAll },
    ...categories.map((c) => ({ value: c.id, label: c.name })),
  ];
  const providerOptions: Option[] = [
    { value: "all", label: vi.contribution.providerAll },
    ...providers.map((p) => ({ value: p, label: p })),
  ];
  const buckets: { value: BucketValue; label: string }[] = [
    { value: "all", label: vi.contribution.bucketAll },
    { value: "full", label: vi.contribution.bucketFull },
    { value: "partial", label: vi.contribution.bucketPartial },
    { value: "none", label: vi.contribution.bucketNone },
  ];

  return (
    <div className="flex flex-col gap-space-3 min-w-[0]">
      {/* PRIMARY — full-width search */}
      <div className="w-full min-w-[0]">
        <SearchField
          value={rawQuery}
          onChange={onQueryChange}
          onCommit={onCommit}
          offline={offline}
        />
      </div>

      {/* SECONDARY — the three filters (stack <768, row/wrap ≥768) */}
      <div className="flex flex-col gap-space-3 min-w-[0] min-[768px]:flex-row min-[768px]:flex-wrap min-[768px]:items-center min-[768px]:gap-y-space-3 min-[768px]:gap-x-space-4">
        <SelectFilter
          small={vi.contribution.categoryFilterLabel}
          panelLabel={vi.contribution.filterCategoryLabel}
          value={categoryId}
          options={categoryOptions}
          onPick={onCategory}
        />
        <SelectFilter
          small={vi.contribution.providerLabel}
          panelLabel={vi.contribution.providerLabel}
          value={provider}
          options={providerOptions}
          onPick={onProvider}
        />

        {/* rate-% quick filter — a segmented Pill group; active = aria-pressed */}
        <div
          className="flex flex-wrap gap-space-2 min-w-[0] min-[768px]:flex-[1_1_100%]"
          role="group"
          aria-label={vi.contribution.bucketGroupLabel}
        >
          {buckets.map((b) => (
            <Pill
              key={b.value}
              active={bucket === b.value}
              onClick={() => onBucket(b.value)}
            >
              {b.label}
            </Pill>
          ))}
        </div>
      </div>
    </div>
  );
}

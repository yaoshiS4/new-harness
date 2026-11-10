/* ============================================================================
 * RestrictedFilters — the header IA for the bonus-restricted list
 * (/game-han-che). A PRIMARY full-width search on top; a SECONDARY bar with TWO
 * dropdown filters (category · provider) that COMBINE (AND) with search. There
 * is NO rate-% pill group here — this page has no rate.
 *
 * It owns NO business logic — the island owns state; this renders controls +
 * forwards. The SearchField (and its diacritic fold) is reused verbatim from the
 * contribution feature; the dropdown pattern mirrors RateFilters' SelectFilter.
 * ==========================================================================*/

"use client";

import { useState } from "react";
import { Dropdown } from "@/ui/Dropdown/Dropdown";
import { Icon } from "@/ui/Icon/Icon";
import { vi } from "@/lib/i18n";
import { SearchField } from "@/components/contribution";

interface Option {
  value: string;
  label: string;
}

/** One dropdown filter (category / provider) — a labelled trigger + a radio
 *  menu. Self-contained open-state; ui/Dropdown owns the a11y (focus-trap, Esc,
 *  outside-click, aria-expanded). Mirrors RateFilters' SelectFilter. The
 *  current label wraps inside the 44px trigger instead of clipping. */
function SelectFilter({
  small,
  panelLabel,
  value,
  options,
  onPick,
}: {
  small: string;
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

export function RestrictedFilters({
  categories,
  providers,
  categoryId,
  provider,
  rawQuery,
  offline,
  onQueryChange,
  onCommit,
  onCategory,
  onProvider,
}: {
  /** categories present among restricted games, in taxonomy order — {id, name} */
  categories: { id: string; name: string }[];
  /** provider names derived from the restricted games */
  providers: string[];
  categoryId: string;
  provider: string;
  rawQuery: string;
  offline: boolean;
  onQueryChange: (raw: string) => void;
  onCommit: (folded: string) => void;
  onCategory: (id: string) => void;
  onProvider: (name: string) => void;
}) {
  const categoryOptions: Option[] = [
    { value: "all", label: vi.contribution.filterAll },
    ...categories.map((c) => ({ value: c.id, label: c.name })),
  ];
  const providerOptions: Option[] = [
    { value: "all", label: vi.contribution.providerAll },
    ...providers.map((p) => ({ value: p, label: p })),
  ];

  return (
    <div className="flex flex-col gap-space-3 min-w-[0]">
      {/* PRIMARY — full-width search (reused verbatim, folds + debounces) */}
      <div className="w-full min-w-[0]">
        <SearchField
          value={rawQuery}
          onChange={onQueryChange}
          onCommit={onCommit}
          offline={offline}
        />
      </div>

      {/* SECONDARY — the two filters (stack <768, row/wrap ≥768). No rate pills. */}
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
      </div>
    </div>
  );
}

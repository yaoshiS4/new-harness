/* ============================================================================
 * FilterNotice — one inline strip, two variants (owner conventional-table
 * override). It NEVER takes over the page — the table frame below it stays
 * mounted (ui/ErrorState is a block surface and is deliberately NOT used here).
 * Variants:
 *   · "empty" — the active filter combo (no search) matched nothing; a neutral
 *     info strip with a "clear filters" reset. Never reads "excluded / banned".
 *   · "error" — the client search index failed to build; --caution (amber
 *     "attention", NOT a loss / not red) with a retry.
 * The icon is an aria-hidden <Icon> sibling, never a glyph baked into a string.
 * Carries no percentage, no banned string.
 * ==========================================================================*/

import { Icon } from "@/ui/Icon/Icon";
import { Button } from "@/ui/Button/Button";

export type FilterNoticeVariant = "empty" | "error";

export function FilterNotice({
  variant,
  message,
  action,
}: {
  variant: FilterNoticeVariant;
  message: string;
  /** optional reset / retry — a 44px ghost button */
  action?: { label: string; onClick: () => void };
}) {
  const isError = variant === "error";
  return (
    <div className="flex items-start gap-space-3 [background:var(--surface-2)] [border:1px_solid_var(--border)] rounded-md py-space-3 px-space-4">
      <span className={`flex-[0_0_auto] inline-flex text-t-body leading-[1] mt-space-1 ${isError ? "text-caution" : "text-text-mid"}`} aria-hidden="true">
        <Icon name={isError ? "warning" : "info"} />
      </span>
      <div className="flex flex-col gap-space-2 min-w-[0]">
        <p className="text-text text-t-sm leading-lh-body">{message}</p>
        {action && (
          <div className="flex">
            <Button variant="ghost" size="sm" onClick={action.onClick}>
              {action.label}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

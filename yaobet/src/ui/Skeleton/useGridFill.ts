/* ============================================================================
 * useGridFill — measures a CSS grid's RESOLVED column count (from the computed
 * grid-template-columns track list) and returns how many filler cells are
 * needed to complete the last partial row. Breakpoint-agnostic: it reads the
 * real resolved track count, so a 3-up @375 / 4-up @768 / 6-up @992 / 8-up @1424
 * ladder each pad to their own full row. Re-measures on resize via ResizeObserver.
 *
 * Used to pad game grids so they NEVER show ragged trailing empty space
 * — the caller renders `fillerCount` quiet pad-tiles after the real
 * tiles. Feature/spanning tiles are accounted for by passing `occupiedCells`
 * (the total grid track-cells the real items consume, spans included).
 * ==========================================================================*/

"use client";

import { useEffect, useState, type RefObject } from "react";

/**
 * useGridCols — the RESOLVED column count of a CSS grid (from computed
 * grid-template-columns), re-measured on resize. 0 before first layout.
 * Use this when occupancy depends on the live breakpoint (e.g. a 2×2 feature
 * tile that only takes 4 cells once the grid is ≥4-up).
 */
export function useGridCols(ref: RefObject<HTMLElement | null>): number {
  const [cols, setCols] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const measure = () => {
      const tracks = getComputedStyle(el).gridTemplateColumns;
      // "none" before layout, else a space-separated list of resolved px tracks
      const n = tracks && tracks !== "none" ? tracks.split(" ").length : 0;
      setCols(n);
    };

    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [ref]);

  return cols;
}

/**
 * useGridFill — how many filler cells to append so the grid (a) completes its
 * last partial row AND (b) never leaves a large dead void below a short tab:
 * the filled total is padded up to at least `minRows` full rows. A provider
 * with only a handful of games therefore reads as a full, intentional lobby
 * block instead of one filler row floating over empty space.
 * @param ref           the grid element
 * @param occupiedCells total track-cells the real items occupy (spans counted)
 * @param minRows       minimum number of full rows the grid should fill (default 2)
 * @returns number of filler cells to append (0 before first layout)
 */
export function useGridFill(
  ref: RefObject<HTMLElement | null>,
  occupiedCells: number,
  minRows = 2,
): number {
  const cols = useGridCols(ref);
  return computeGridFill(cols, occupiedCells, minRows);
}

/**
 * computeGridFill — pure cell-fill math, shared by callers that resolve `cols`
 * themselves (e.g. a grid with row-spanning feature tiles). Rounds the occupied
 * cell count UP to a full row, then up to at least `minRows` full rows, and
 * returns the filler count needed to reach that target.
 */
export function computeGridFill(
  cols: number,
  occupiedCells: number,
  minRows = 2,
): number {
  if (cols <= 0 || occupiedCells <= 0) return 0;
  const usedRows = Math.ceil(occupiedCells / cols);
  const targetRows = Math.max(usedRows, minRows);
  return targetRows * cols - occupiedCells;
}

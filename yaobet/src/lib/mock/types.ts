/* ============================================================================
 * Yaobet — mock/types re-export
 * ----------------------------------------------------------------------------
 * One spec places domain types at lib/mock/types.ts; another places
 * them at lib/types.ts. The canonical source is "@/lib/types". This file
 * re-exports it so BOTH import paths resolve and downstream agents can use
 * either. Do not duplicate type definitions here.
 * ==========================================================================*/

export * from "../types";

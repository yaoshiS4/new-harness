/* ============================================================================
 * Yaobet — points-store escalation math (PRD §4.3)
 * ----------------------------------------------------------------------------
 * Pure, React-free helpers that resolve the restart-cooldown claim mechanic
 * for a Product. NOTHING here is stored — every value is derived from the
 * server clock + the owner config, mirroring the PRD's "no stored never-claimed
 * state; decide by runtime gates" (§5).
 *
 * One economic truth (PRD §1): the item/face is paid IN FULL on every claim;
 * only the POINT cost rises on an early (cooldown-running) claim. These helpers
 * therefore only ever compute POINT costs and the branch — never a reduced face.
 * ==========================================================================*/

import type { Product } from "../types";

/**
 * RG threshold for unlimited packages: once a running,
 * uncapped ladder climbs PAST this step, the strong "no floor" disclosure with
 * cumulative cycle points is mandatory. Matches the PRD illustration where the
 * strong disclosure fires at step 5 (past the step-4 warning boundary).
 */
export const RG_UNLIMITED_WARN_STEP = 4;

/**
 * points_k = ceil( basePoints × (1/q)^(k-1) ), pinned at `maxSteps` when set.
 * Step 1 = full rate = basePoints. PRD §4.3 · golden vectors (§4.4):
 * base=1000 q=0.70 → 1000 · 1429 · 2041 · 2916 · 4165 · 5950.
 */
export function pointsAtStep(
  base: number,
  q: number,
  step: number,
  maxSteps: number | null,
): number {
  const effectiveStep = maxSteps != null ? Math.min(step, maxSteps) : step;
  const k = Math.max(1, effectiveStep);
  const cost = base * Math.pow(1 / q, k - 1);
  return Math.ceil(cost);
}

/**
 * Rate as a percentage of full value for the "{pct}% (bước {k})" disclosure:
 * rate_k = r0 × q^(k-1) → pct = q^(k-1) × 100. Step 1 = 100%.
 */
export function ratePct(q: number, step: number): number {
  const k = Math.max(1, step);
  return Math.pow(q, k - 1) * 100;
}

/**
 * Is a cooldown running against `nowMs`? Strict `now < cooldownEndsAt`
 * (the boundary `now == expiry` counts as NOT running → BASE/reset).
 * `cooldownEndsAt == null` → not running (first-ever / clean).
 */
export function isCooldownRunning(p: Product, nowMs: number): boolean {
  if (p.cooldownEndsAt == null) return false;
  return nowMs < new Date(p.cooldownEndsAt).getTime();
}

/** The claim branch resolved from the server clock (PRD §5 Gate 2). */
export type ClaimBranch = "base" | "escalate" | "at_floor" | "unlimited_deep";

/**
 * Resolve which claim branch the NEXT claim lands on:
 *  - `base`            — cooldown not running (null OR now >= expiry) → step 1, basePoints.
 *  - `escalate`        — running, and (unlimited OR currentStep+1 ≤ maxSteps).
 *  - `at_floor`        — running, maxSteps set, currentStep+1 > maxSteps → pinned.
 *  - `unlimited_deep`  — unlimited, running, and step > RG_UNLIMITED_WARN_STEP.
 */
export function resolveBranch(p: Product, nowMs: number): ClaimBranch {
  if (!isCooldownRunning(p, nowMs)) return "base";

  const nextStep = p.currentStep + 1;

  if (p.maxSteps == null) {
    return nextStep > RG_UNLIMITED_WARN_STEP ? "unlimited_deep" : "escalate";
  }

  return nextStep > p.maxSteps ? "at_floor" : "escalate";
}

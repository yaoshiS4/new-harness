/* ============================================================================
 * Yaobet MOCK — points store × restart-cooldown
 * ----------------------------------------------------------------------------
 * ALL DATA HERE IS MOCK — clearly fabricated fixtures, placeholder image, no
 * real figures. Each Product carries the full restart-cooldown shape (types.ts
 * §1.1). Per-state DEMO_* fixtures make every plan §3 state reviewable in
 * isolation; flip DEMO_STATE / DEMO_ERROR to exercise a single branch.
 *
 * Points → ITEM analog of the PRD's points → CASH mechanic: the item/face is
 * paid IN FULL every claim; only the POINT cost escalates on an early claim.
 * ==========================================================================*/

import type { MoneyValue, Product } from "../types";
import { DEMO_EMPTY, isoIn, simulateFetch } from "./helpers";

const PROD = "/assets/store/reward-coins.jpg"; // MOCK reward thumbnail

/** MOCK money helper — clearly fabricated VND face figures. */
const vnd = (amount: number): MoneyValue => ({ amount, currency: "VND" });

/* ----------------------------------------------------------------------------
 * DEMO toggles — flip to review a single state without wiring a real backend.
 * DEMO_STATE null → the normal PRODUCTS catalog. Otherwise the matching
 * single-state fixture below is served alone.
 * --------------------------------------------------------------------------*/
export type DemoState =
  | "full-rate"
  | "early"
  | "at-floor"
  | "unlimited-deep"
  | "insufficient"
  | "rolling-unmet"
  | "sold-out";

/** Flip to a DemoState to preview that card state alone; null = full catalog. */
export const DEMO_STATE: DemoState | null = null;
/** Flip true to exercise the grid fetch-error (ErrorState onRetry) path. */
export const DEMO_ERROR = false as const;
/** Flip true to exercise the program-budget breaker: paused dialog + a
 *  disabled-everywhere card face (plan §3 row 13 · PRD §7.1a row 1). */
export const DEMO_PAUSED = false as const;

/** Shared MOCK defaults so each fixture only overrides the field under test. */
function mockProduct(over: Partial<Product> & Pick<Product, "id" | "name">): Product {
  return {
    imageSrc: PROD,
    category: "voucher", // default family; physical goods override to 'product'
    rollingRequired: 3, // "3 vòng cược" — withdrawal condition (info only)
    stockTotal: 200,
    stockRemaining: 88,
    redeemedCount: 0, // GLOBAL social-proof tally (across all users)
    faceValue: vnd(1_000_000),
    basePoints: 1_000, // 1 điểm = 1.000₫ (r0)
    repeatFraction: 0.7,
    cooldownMinutes: 4_320, // 3 days
    maxSteps: 4,
    currentStep: 1,
    cooldownEndsAt: null, // not running → full rate by default
    userRedeemedCount: 0,
    cyclePointsBurned: 0,
    ...over,
  };
}

/* ----------------------------------------------------------------------------
 * Normal catalog (all fields; clearly MOCK). Rate 1 điểm = 1.000₫ so
 * basePoints = faceValue / 1000. Vouchers (category 'voucher') carry a rolling
 * multiplier; physical goods (category 'product') set rollingRequired 0 so the
 * "Rút sau …" line and the dialog "Điều kiện rút" row never render.
 * --------------------------------------------------------------------------*/
const PRODUCTS: Product[] = [
  // 1 — normal, affordable.
  mockProduct({
    id: "s-voucher-200",
    name: "Voucher 200K",
    category: "voucher",
    faceValue: vnd(200_000),
    basePoints: 200,
    rollingRequired: 5,
    stockRemaining: 286,
    redeemedCount: 74,
  }),
  // 2 — normal, affordable.
  mockProduct({
    id: "s-voucher-300",
    name: "Voucher 300K",
    category: "voucher",
    faceValue: vnd(300_000),
    basePoints: 300,
    rollingRequired: 3,
    stockRemaining: 210,
    redeemedCount: 129,
  }),
  // 3 — SOLD OUT (stockRemaining 0).
  mockProduct({
    id: "s-voucher-500",
    name: "Voucher 500K",
    category: "voucher",
    faceValue: vnd(500_000),
    basePoints: 500,
    rollingRequired: 3,
    stockRemaining: 0,
    redeemedCount: 500,
  }),
  // 4 — normal, affordable.
  mockProduct({
    id: "s-voucher-1m",
    name: "Voucher 1 triệu",
    category: "voucher",
    faceValue: vnd(1_000_000),
    basePoints: 1_000,
    rollingRequired: 3,
    stockRemaining: 168,
    redeemedCount: 168,
  }),
  // 5 — running cooldown (chip 00:13:15) + affordable → EARLY dialog case.
  mockProduct({
    id: "s-voucher-2m",
    name: "Voucher 2 triệu",
    category: "voucher",
    faceValue: vnd(2_000_000),
    basePoints: 2_000,
    rollingRequired: 8,
    stockRemaining: 66,
    redeemedCount: 312,
    repeatFraction: 0.7,
    maxSteps: 4,
    currentStep: 1, // next claim escalates to step 2 → 2858 điểm
    cooldownEndsAt: isoIn(13.25), // ~00:13:15
  }),
  // 5b — LIMIT REACHED (at_floor): redeemed to the cap, must wait out the cooldown.
  mockProduct({
    id: "s-voucher-100",
    name: "Voucher 100K",
    category: "voucher",
    faceValue: vnd(100_000),
    basePoints: 100,
    rollingRequired: 5,
    stockRemaining: 140,
    redeemedCount: 921,
    repeatFraction: 0.7,
    maxSteps: 4,
    currentStep: 4, // at the cap → next early claim is at_floor → "Quay lại sau" lock
    cooldownEndsAt: isoIn(720), // 12h — stable so the limit state stays reviewable
  }),
  // 6 — physical product, INSUFFICIENT (14000 > 3250).
  mockProduct({
    id: "s-ps5",
    name: "PlayStation 5 Slim",
    category: "product",
    faceValue: vnd(14_000_000),
    basePoints: 14_000,
    rollingRequired: 0,
    stockRemaining: 40,
    redeemedCount: 12,
  }),
  // 7 — physical product, INSUFFICIENT.
  mockProduct({
    id: "s-iphone",
    name: "iPhone 15 Pro Max",
    category: "product",
    faceValue: vnd(30_000_000),
    basePoints: 30_000,
    rollingRequired: 0,
    stockRemaining: 22,
    redeemedCount: 8,
  }),
  // 8 — physical product, INSUFFICIENT.
  mockProduct({
    id: "s-airpods",
    name: "AirPods Pro 2",
    category: "product",
    faceValue: vnd(5_500_000),
    basePoints: 5_500,
    rollingRequired: 0,
    stockRemaining: 74,
    redeemedCount: 51,
  }),
  // 9 — physical product, running cooldown (chip 01:59:01) AND INSUFFICIENT.
  mockProduct({
    id: "s-watch",
    name: "Apple Watch Series 9",
    category: "product",
    faceValue: vnd(9_000_000),
    basePoints: 9_000,
    rollingRequired: 0,
    stockRemaining: 36,
    redeemedCount: 19,
    repeatFraction: 0.7,
    maxSteps: 4,
    currentStep: 1,
    cooldownEndsAt: isoIn(119), // ~01:59:01
  }),
  // 10 — physical product, SOLD OUT.
  mockProduct({
    id: "s-steamdeck",
    name: "Steam Deck OLED",
    category: "product",
    faceValue: vnd(13_000_000),
    basePoints: 13_000,
    rollingRequired: 0,
    stockRemaining: 0,
    redeemedCount: 60,
  }),
];

/* ----------------------------------------------------------------------------
 * Per-state DEMO fixtures (plan §3 state matrix). Each overrides ONE dimension.
 * --------------------------------------------------------------------------*/
const DEMO_FULL_RATE = mockProduct({
  id: "demo-base",
  name: "[DEMO] Full rate",
  cooldownEndsAt: null, // not running → BASE
  currentStep: 1,
});

const DEMO_EARLY = mockProduct({
  id: "demo-early",
  name: "[DEMO] Đổi sớm",
  cooldownEndsAt: isoIn(120), // running
  currentStep: 1, // next claim escalates to step 2
});

const DEMO_AT_FLOOR = mockProduct({
  id: "demo-atfloor",
  name: "[DEMO] Mức thấp nhất",
  maxSteps: 4,
  currentStep: 4, // next claim pins at cap
  cooldownEndsAt: isoIn(200),
});

const DEMO_UNLIMITED_DEEP = mockProduct({
  id: "demo-unlimited",
  name: "[DEMO] Không giới hạn",
  maxSteps: null, // unlimited
  currentStep: 5, // past RG_UNLIMITED_WARN_STEP → strong disclosure
  cyclePointsBurned: 9_589,
  cooldownEndsAt: isoIn(400),
});

const DEMO_INSUFFICIENT = mockProduct({
  id: "demo-broke",
  name: "[DEMO] Chưa đủ điểm",
  basePoints: 900_000, // huge cost vs the mock balance below
  cooldownEndsAt: isoIn(150), // running → escalated cost, unaffordable
  currentStep: 2,
});

const DEMO_ROLLING_UNMET = mockProduct({
  id: "demo-rolling",
  name: "[DEMO] Chưa đủ vòng cược",
  rollingRequired: 12,
});

const DEMO_SOLD_OUT = mockProduct({
  id: "demo-soldout",
  name: "[DEMO] Hết hàng",
  stockRemaining: 0,
  redeemedCount: 420,
});

const DEMO_FIXTURES: Record<DemoState, Product> = {
  "full-rate": DEMO_FULL_RATE,
  early: DEMO_EARLY,
  "at-floor": DEMO_AT_FLOOR,
  "unlimited-deep": DEMO_UNLIMITED_DEEP,
  insufficient: DEMO_INSUFFICIENT,
  "rolling-unmet": DEMO_ROLLING_UNMET,
  "sold-out": DEMO_SOLD_OUT,
};

/* ----------------------------------------------------------------------------
 * Accessors — real-API migration replaces only these BODIES.
 * --------------------------------------------------------------------------*/
export async function getProducts(): Promise<Product[]> {
  if (DEMO_ERROR) throw new Error("MOCK: DEMO_ERROR — simulated catalog fetch failure");
  if (DEMO_EMPTY) return simulateFetch([]);
  if (DEMO_STATE) return simulateFetch([DEMO_FIXTURES[DEMO_STATE]]);
  return simulateFetch(PRODUCTS);
}

export async function getPointsBalance(): Promise<number> {
  return simulateFetch(DEMO_EMPTY ? 0 : 3_250);
}

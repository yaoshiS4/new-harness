/* Yaobet mock — Hoàn trả (the CORE 1% surface). RG.
 * %-of-play truthful; claimable vs accrued distinct; honest empty when none. */

import type { Cashback, RebateEntry } from "../types";
import { DEMO_EMPTY, simulateFetch } from "./helpers";

const ENTRIES: RebateEntry[] = [
  { id: "r1", productName: "Casino", turnoverBasis: { amount: 38_600_000, currency: "VND" }, rate: 0.6, accrued: { amount: 231_600, currency: "VND" } },
  { id: "r2", productName: "Nổ hũ", turnoverBasis: { amount: 16_800_000, currency: "VND" }, rate: 0.8, accrued: { amount: 134_400, currency: "VND" } },
  { id: "r3", productName: "Thể thao", turnoverBasis: { amount: 8_000_000, currency: "VND" }, rate: 0.5, accrued: { amount: 40_000, currency: "VND" } },
];

export async function getCashback(): Promise<Cashback> {
  if (DEMO_EMPTY) {
    return simulateFetch<Cashback>({
      accrued: { amount: 0, currency: "VND" },
      claimable: { amount: 0, currency: "VND" },
      period: "Tuần này",
      status: "empty",
      entries: [],
    });
  }
  return simulateFetch<Cashback>({
    accrued: { amount: 406_000, currency: "VND" },
    claimable: { amount: 366_000, currency: "VND" },
    period: "Tuần này",
    status: "claimable",
    entries: ENTRIES,
  });
}

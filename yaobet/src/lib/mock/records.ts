/* Yaobet mock — records / Lịch sử. Equal win/loss salience. */

import type { Transaction } from "../types";
import { DEMO_EMPTY, isoAgo, simulateFetch } from "./helpers";

const RECORDS: Transaction[] = [
  { id: "tx1", type: "deposit", amount: { amount: 6_886_000, currency: "VND" }, at: isoAgo(30), note: "Nạp qua ngân hàng" },
  { id: "tx2", type: "win", amount: { amount: 880_000, currency: "VND" }, at: isoAgo(95) },
  { id: "tx3", type: "loss", amount: { amount: -560_000, currency: "VND" }, at: isoAgo(110) },
  { id: "tx4", type: "cashback", amount: { amount: 366_000, currency: "VND" }, at: isoAgo(1500), note: "Hoàn trả tuần" },
  { id: "tx5", type: "withdraw", amount: { amount: -2_000_000, currency: "VND" }, at: isoAgo(2880) },
  { id: "tx6", type: "transfer", amount: { amount: -500_000, currency: "VND" }, at: isoAgo(3000), note: "Chuyển sang Thể thao" },
];

export async function getRecords(): Promise<Transaction[]> {
  return simulateFetch(DEMO_EMPTY ? [] : RECORDS);
}

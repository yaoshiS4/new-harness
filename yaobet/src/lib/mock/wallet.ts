/* Yaobet mock — wallet + per-product balances. No crypto. */

import type { Envelope, LiveMoney, Wallet } from "../types";
import { DEMO_EMPTY, liveMoney, nowIso, simulateFetch } from "./helpers";

export async function getWallet(): Promise<Wallet> {
  return simulateFetch<Wallet>({
    balance: liveMoney(DEMO_EMPTY ? 0 : 6_886_000),
    products: DEMO_EMPTY
      ? []
      : [
          { productId: "casino", productName: "Casino", balance: { amount: 2_886_000, currency: "VND" } },
          { productId: "sports", productName: "Thể thao", balance: { amount: 1_680_000, currency: "VND" } },
          { productId: "slots", productName: "Nổ hũ", balance: { amount: 2_320_000, currency: "VND" } },
        ],
  });
}

/** Balance for the TopBar chip / WalletBalanceHeader — Live envelope, stale-aware. */
export async function getBalance(): Promise<Envelope<LiveMoney>> {
  if (DEMO_EMPTY) return simulateFetch({ status: "absent" });
  return simulateFetch<Envelope<LiveMoney>>({
    status: "live",
    value: liveMoney(6_886_000),
    sourcedAt: nowIso(),
    freshnessMs: 20_000,
  });
}

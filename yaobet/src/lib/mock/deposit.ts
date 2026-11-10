/* Yaobet mock — deposit rails + FTD offer. RG. */

import type { DepositOffer } from "../types";
import { DEMO_EMPTY, simulateFetch } from "./helpers";

/** First-deposit offer — live, server-sourced T&C; NO hardcoded %. */
export async function getDepositOffer(): Promise<DepositOffer | null> {
  if (DEMO_EMPTY) return simulateFetch(null);
  return simulateFetch<DepositOffer>({
    title: "Ưu đãi lần nạp đầu",
    body: "Nạp lần đầu để nhận ưu đãi chào mừng. Xem điều khoản chi tiết trước khi tham gia.",
    minToQualify: { amount: 100_000, currency: "VND" },
  });
}

/** Bank transfer memo a user copies (tap-to-copy) for the bank rail. */
export async function getBankTransferMemo(): Promise<{ account: string; bank: string; memo: string }> {
  return simulateFetch({
    account: "060 1234 56789",
    bank: "Vietcombank — CT YAOBET",
    memo: "YB668812",
  });
}

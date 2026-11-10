/* Yaobet mock — profile / security index + verification fields + linked
 * bank cards & crypto addresses + member account summary. Truthful-only: every value is either a real fixture or honestly
 * absent under DEMO_EMPTY. Sensitive values arrive already masked. */

import type {
  AccountSummary,
  BankCard,
  CryptoAddress,
  SecurityFactor,
  SecurityIndex,
  VerificationItem,
} from "../types";
import { DEMO_EMPTY, simulateFetch } from "./helpers";

const FACTORS: SecurityFactor[] = [
  { id: "name", label: "Tên thật, giới tính, ngày sinh", status: "verified" },
  { id: "phone", label: "Số điện thoại", status: "verified" },
  { id: "email", label: "Email", status: "pending" },
  { id: "2fa", label: "Xác thực 2 bước", status: "unset" },
  { id: "fundpw", label: "Mật khẩu rút tiền", status: "unset" },
];

export async function getSecurityIndex(): Promise<SecurityIndex> {
  const factors = DEMO_EMPTY
    ? FACTORS.map((f) => ({ ...f, status: "unset" as const }))
    : FACTORS;
  const verified = factors.filter((f) => f.status === "verified").length;
  return simulateFetch<SecurityIndex>({ factors, score: verified * 20 });
}

/** Row-level verification fields shown under the "Thông tin xác minh" tab. */
const VERIFICATION: VerificationItem[] = [
  { id: "realName", value: "Nguyễn Văn An", status: "verified" },
  { id: "phone", value: "•••• •••• 866", status: "verified" },
  { id: "email", value: "a••••n@gmail.com", status: "pending" },
  { id: "fundPassword", value: null, status: "unset" },
  { id: "dynamicCode", value: null, status: "unset" },
];

export async function getVerification(): Promise<VerificationItem[]> {
  if (DEMO_EMPTY) {
    return simulateFetch(
      VERIFICATION.map((v) => ({ ...v, value: null, status: "unset" as const })),
    );
  }
  return simulateFetch(VERIFICATION);
}

/** Member account summary (points + accrued rebate) for the left rail. */
export async function getAccountSummary(): Promise<AccountSummary> {
  return simulateFetch<AccountSummary>({
    points: DEMO_EMPTY ? 0 : 86_880,
    rebate: { amount: DEMO_EMPTY ? 0 : 168_000, currency: "VND" },
  });
}

/** Linked bank cards (liên kết thẻ ngân hàng). Masked at source. */
const BANK_CARDS: BankCard[] = [
  {
    id: "bc_1",
    bankName: "Vietcombank",
    holderName: "NGUYEN VAN AN",
    maskedNumber: "•••• •••• 8866",
    isDefault: true,
  },
  {
    id: "bc_2",
    bankName: "Techcombank",
    holderName: "NGUYEN VAN AN",
    maskedNumber: "•••• •••• 6886",
    isDefault: false,
  },
];

export async function getBankCards(): Promise<BankCard[]> {
  return simulateFetch(DEMO_EMPTY ? [] : BANK_CARDS);
}

/** Linked crypto withdrawal addresses (địa chỉ ví). Masked at source. */
const CRYPTO_ADDRESSES: CryptoAddress[] = [
  {
    id: "ca_1",
    asset: "USDT",
    network: "TRC20",
    maskedAddress: "TQ8r…9fAe",
    isDefault: true,
  },
  {
    id: "ca_2",
    asset: "USDT",
    network: "BEP20",
    maskedAddress: "0x6f…8d2C",
    isDefault: false,
  },
];

export async function getCryptoAddresses(): Promise<CryptoAddress[]> {
  return simulateFetch(DEMO_EMPTY ? [] : CRYPTO_ADDRESSES);
}

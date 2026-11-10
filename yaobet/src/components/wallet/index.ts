/* ============================================================================
 * Yaobet — wallet feature components barrel (§wallet / §deposit).
 * The /vi-tien surface is a TABBED wallet — balance header + a
 * card-style tab strip switching FOUR single-purpose panels (one feature/view):
 * Nạp tiền (deposit, VN rails) · Rút tiền (withdraw) · Lịch sử (history, equal
 * win/loss salience) · Chuyển quỹ (product fund transfer).
 * ==========================================================================*/

export { WalletTabs } from "./WalletTabs";
export type { WalletTabsProps } from "./WalletTabs";

export { WalletBalanceHeader } from "./WalletBalanceHeader";
export type { WalletBalanceHeaderProps } from "./WalletBalanceHeader";

export { DepositPanel } from "./DepositPanel";
export type { DepositPanelProps } from "./DepositPanel";

export { WithdrawPanel } from "./WithdrawPanel";
export type { WithdrawPanelProps } from "./WithdrawPanel";

export { FundTransferPanel } from "./FundTransferPanel";
export type { FundTransferPanelProps } from "./FundTransferPanel";

export { WalletHistory } from "./WalletHistory";
export type { WalletHistoryProps } from "./WalletHistory";

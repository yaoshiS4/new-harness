/* Yaobet — auth barrel. Downstream agents import from "@/lib/auth". */
export { MockAuthProvider, useAuth } from "./session";
export { AuthModalProvider, useAuthModal } from "./modal";
export type { AuthModalMode } from "./modal";
export { useRequireAuth, isGuest, isLevelZero, isTiered } from "./guard";
export type { RequireAuthResult } from "./guard";
export { SESSIONS, LEVEL_0_USER, TIERED_USER } from "./fixtures";

/* ============================================================================
 * Yaobet — mock session fixtures
 * Three view-states the source exhibits: logged-out / level-0 / tiered.
 * ==========================================================================*/

import type { Session, User } from "../types";

export const LEVEL_0_USER: User = {
  id: "u_new",
  displayName: "Thành viên mới",
  memberId: "YB-668812",
  vipLevel: 0,
  vipTierName: "Tân thủ",
  verified: false,
  unreadMessages: 1,
};

export const TIERED_USER: User = {
  id: "u_vip",
  displayName: "Nguyễn Văn An",
  memberId: "YB-880066",
  vipLevel: 3,
  vipTierName: "Bạch Kim",
  verified: true,
  unreadMessages: 2,
};

export const SESSIONS: Record<Session["state"], Session> = {
  guest: { state: "guest", user: null },
  "level-0": { state: "level-0", user: LEVEL_0_USER },
  tiered: { state: "tiered", user: TIERED_USER },
};

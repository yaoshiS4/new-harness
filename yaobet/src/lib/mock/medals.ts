/* Yaobet mock — medals / honor wall. RG-reframed:
 * neutral activity metrics only, NO loss-as-status; families trimmed to 1–2. */

import type { Medal } from "../types";
import { DEMO_EMPTY, simulateFetch } from "./helpers";

const ART = "/assets/placeholders/medal.svg";

const MEDALS: Medal[] = [
  { id: "md1", family: "Hoạt động", name: "Đăng nhập đều đặn", metricLabel: "Số ngày đăng nhập", artSrc: ART, earned: true },
  { id: "md2", family: "Hoạt động", name: "Khám phá trò chơi", metricLabel: "Số trò chơi đã thử", artSrc: ART, earned: true },
  { id: "md3", family: "Cộng đồng", name: "Người giới thiệu", metricLabel: "Số bạn đã mời", artSrc: ART, earned: false },
];

export async function getMedals(): Promise<Medal[]> {
  return simulateFetch(DEMO_EMPTY ? [] : MEDALS);
}

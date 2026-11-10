/* Yaobet mock — messages / Tin nhắn. */

import type { Message } from "../types";
import { DEMO_EMPTY, isoAgo, simulateFetch } from "./helpers";

const MESSAGES: Message[] = [
  { id: "m1", subject: "Chào mừng đến với Yaobet", body: "Cảm ơn bạn đã tham gia. Hoàn tất xác minh để mở khóa rút tiền.", read: false, at: isoAgo(60) },
  { id: "m2", subject: "Hoàn trả tuần đã sẵn sàng", body: "Hoàn trả tuần này của bạn đã có thể nhận tại mục Hoàn trả.", read: false, at: isoAgo(720) },
  { id: "m3", subject: "Cập nhật điều khoản dịch vụ", body: "Chúng tôi đã cập nhật điều khoản. Vui lòng xem chi tiết.", read: true, at: isoAgo(4320) },
];

export async function getMessages(): Promise<Message[]> {
  return simulateFetch(DEMO_EMPTY ? [] : MESSAGES);
}

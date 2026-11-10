/* ============================================================================
 * StoreTerms — the "Điều khoản & điều kiện" accordion on the points store.
 * A small client island: a titled panel (section-sign sigil + subtitle + last-updated) over
 * a list of expand/collapse Q&A items, closed with a short program note. Content
 * is fixed Vietnamese copy (owner-approved); tokens only, matches the gold-on-dark
 * store surface. One item open at a time.
 * ==========================================================================*/

"use client";

import { useState } from "react";
import { Icon } from "@/ui";

/** Owner-approved T&C copy (Vietnamese). Order matches the store screenshot. */
const ITEMS: { q: string; a: string }[] = [
  {
    q: "Làm sao để có điểm thưởng?",
    a: "Bạn nhận điểm thưởng từ các hoạt động trên Yaobet như thăng cấp, thưởng tuần và thưởng tháng. Điểm sẽ được cộng tự động vào tài khoản để bạn đổi quà.",
  },
  {
    q: "Đổi quà như thế nào?",
    a: "Chọn phần quà bạn muốn và nhấn Xác nhận đổi, quà sẽ được ghi nhận ngay. Lưu ý: điểm đã đổi sẽ không được hoàn lại, bạn hãy kiểm tra kỹ trước khi xác nhận nhé.",
  },
  {
    q: "Thời gian chờ là gì?",
    a: "Mỗi vật phẩm đều có một khoảng thời gian chờ nhất định tùy theo giá trị. Sau khi bạn đổi, thời gian chờ sẽ bắt đầu tính. Chỉ cần đợi hết khoảng thời gian này, số điểm cần để đổi sẽ trở về mức thấp nhất.",
  },
  {
    q: "Đổi sớm là gì?",
    a: "Khi vật phẩm đang trong thời gian chờ, bạn vẫn có thể bỏ qua bằng cách đổi sớm. Tuy nhiên, đổi sớm sẽ cần mức quy đổi cao hơn bình thường, và càng đổi sớm liên tiếp, mức quy đổi sẽ càng tăng. Số điểm cụ thể luôn hiển thị trên nút đổi để bạn cân nhắc trước khi quyết định.",
  },
  {
    q: "Tại sao lại hết lượt đổi?",
    a: "Mỗi vật phẩm có số lần quy đổi nhất định cho mỗi tài khoản. Khi đã đổi hết số lần tối đa, bạn chỉ cần đợi thời gian chờ trở về 0 là có thể đổi tiếp.",
  },
];

export function StoreTerms() {
  const [open, setOpen] = useState<number | null>(null);

  return (
    <section className="mt-space-6 p-space-5 rounded-card [background:var(--surface-2)] [border:1px_solid_var(--border)]" aria-label="Điều khoản & điều kiện">
      <header className="grid grid-cols-[auto_1fr_auto] max-639:grid-cols-[auto_1fr] items-center gap-x-space-3 gap-y-space-2 mb-space-4">
        <span className="flex-none inline-flex items-center justify-center w-[44px] h-[44px] rounded-md [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)] text-brand-accent-fg text-t-h2 font-weight-bold leading-[1]" aria-hidden="true">
          §
        </span>
        <div className="flex flex-col gap-[2px] min-w-[0] mr-auto">
          <h2 className="m-[0] store-type-h4 text-text-hi">Điều khoản &amp; điều kiện</h2>
          <p className="m-[0] text-t-sm text-text-mid leading-lh-tight">
            Quy định về việc tích lũy và sử dụng điểm thưởng
          </p>
        </div>
        <span className="max-639:col-start-2 justify-self-start flex-none py-[4px] px-space-3 rounded-pill [border:1px_solid_var(--border)] [background:var(--surface-3)] text-fg-muted-raised text-t-micro whitespace-nowrap">Cập nhật lần cuối · —</span>
      </header>

      <ul className="flex flex-col gap-space-2 list-none m-[0] p-[0]">
        {ITEMS.map((item, i) => {
          const isOpen = open === i;
          const panelId = `terms-panel-${i}`;
          return (
            <li key={item.q} className="store-terms-item" data-open={isOpen}>
              <button
                type="button"
                className="store-terms-trigger group flex items-center gap-space-3 w-full p-space-4 [background:none] [border:0] cursor-pointer text-left text-text-hi"
                aria-expanded={isOpen}
                aria-controls={panelId}
                onClick={() => setOpen(isOpen ? null : i)}
              >
                <span className="flex-none inline-flex items-center justify-center w-[34px] h-[34px] rounded-md [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)] text-brand-accent-fg text-t-sm font-weight-bold tabular-nums" aria-hidden="true">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="flex-[1_1_auto] min-w-[0] text-t-body font-weight-semi text-text-hi leading-lh-tight [.group:hover_&]:text-text-hi">{item.q}</span>
                <Icon
                  name="chevronDown"
                  size={18}
                  className="store-terms-chevron"
                  aria-hidden="true"
                />
              </button>
              {isOpen && (
                <p id={panelId} className="m-[0] pt-[0] pr-space-4 pb-space-4 pl-[calc(var(--space-4)+34px+var(--space-3))] text-t-sm leading-lh-body text-fg-muted-raised">
                  {item.a}
                </p>
              )}
            </li>
          );
        })}
      </ul>

      <p className="flex items-start gap-space-2 [margin:var(--space-4)_0_0] py-space-3 px-space-4 rounded-md [background:var(--surface-3)] text-t-sm leading-lh-body text-fg-muted-raised">
        <Icon name="info" size={16} className="flex-none mt-[2px] text-fg-muted-raised" aria-hidden="true" />
        <span>
          Chương trình có thể thay đổi hoặc kết thúc mà không cần báo trước; quyết
          định cuối cùng thuộc về ban quản trị. Nếu cần hỗ trợ, vui lòng liên hệ bộ
          phận chăm sóc khách hàng.
        </span>
      </p>
    </section>
  );
}

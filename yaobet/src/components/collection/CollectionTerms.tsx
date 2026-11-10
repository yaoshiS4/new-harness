/* ============================================================================
 * Yaobet — BỘ SƯU TẬP · the terms.
 * ----------------------------------------------------------------------------
 * A PLAIN DOCUMENT, and prop-free on purpose. It is mounted inside the house
 * `Overlay` from the collection surface, and can be mounted on any page or at
 * a canonical URL without changing a line — so it never owns the sheet's
 * chrome (title bar, close button, scroll cap). That belongs to whoever opens
 * it. It also carries no callback and no set, which is what lets the pack
 * stage ask for it with a zero-argument callback.
 *
 * Two things restored here that the code already computed and never published:
 *   · the RATE MODEL, derived rather than typed. Note what this file does NOT
 *     say: a per-card percentage. The engine allocates each open to a set and
 *     rolls inside it, so a whole-pool figure is the chance of no open anyone
 *     receives. What survives renormalisation is the RATIO between the tiers —
 *     both are divided by the same total — so the ratio is published here and
 *     the exact per-set percentage is published on the card itself
 *     (`CardDetail` / `ratesBySet`). An earlier draft hand-typed a rate next to
 *     a pool and advertised 11.5% on a card whose real chance was 7.03%; a
 *     whole-pool rate over a set-scoped roll is the same error one level up.
 *   · the GUARANTEE, at the same N the engine rolls (`DEMO_PITY_BACKSTOP`).
 *     Stated as a rule, here. NOT as a live counter on the pack stage — "2
 *     lượt nữa là chắc chắn" over a CTA is a spend meter.
 *
 * `M` (the qualifying amount) and `R` (the reward) stay parameters. No amount
 * is stated as final anywhere in this file.
 * ==========================================================================*/

"use client";

import Link from "next/link";
import { DEMO_PITY_BACKSTOP, DEMO_TIERS } from "@/lib/collection/fixtures/epl";

/** Published per-card rates, read from the derived table. Never authored. */
const RARE = DEMO_TIERS.find((t) => t.id === "rare")!;
const COMMON = DEMO_TIERS.find((t) => t.id === "common")!;

export function CollectionTerms() {
  return (
    <div className="grid gap-space-2 [&_h3]:[margin:var(--space-3)_0_0] [&_h3]:text-t-sm [&_h3]:font-weight-semi [&_h3]:text-text-hi [&_h3:first-child]:mt-[0] [&_ul]:m-[0] [&_ul]:pl-[1.15em] [&_ul]:grid [&_ul]:gap-[8px] [&_li]:text-t-sm [&_li]:text-text [&_li]:leading-lh-body [&_strong]:text-text-hi [&_strong]:font-weight-semi [&_strong]:tabular-nums">
      <h3>Cách nhận lượt mở</h3>
      <ul>
        <li>Mỗi cược thể thao đã <strong>kết toán</strong> và hợp lệ sẽ cộng vào một bộ đếm chung.</li>
        <li>Mỗi khi bộ đếm đạt mức quy định, bạn nhận <strong>một lượt mở</strong>. Đơn vị tính là số tiền cược, không phải số phiếu cược — chia nhỏ cược không làm tăng số lượt.</li>
        <li>Cược bị <strong>hủy, hoàn hoặc hòa</strong> sẽ thu hồi lượt mở tạm ghi.</li>
        <li>Chỉ nạp tiền mà không đặt cược thì <strong>không</strong> nhận được lượt mở.</li>
        <li>Cược bằng số dư khuyến mãi không được tính.</li>
      </ul>

      <h3>Mở thẻ</h3>
      <ul>
        <li>Mỗi lượt mở luôn cho <strong>đúng một thẻ</strong>. Không có trường hợp mở ra mà không nhận được gì.</li>
        {/* the shard clause published a term the product cannot honour:
            there is no way to spend a mảnh and no balance shown anywhere. What
            a duplicate actually does is stated instead. */}
        <li>Thẻ đã có sẽ <strong>không được tính thêm</strong> vào bộ. Bạn vẫn giữ toàn bộ số thẻ đã nhận.</li>
        <li>Một thẻ có thể thuộc <strong>nhiều bộ</strong> cùng lúc.</li>
        <li>Việc bạn chọn túi nào <strong>không</strong> ảnh hưởng đến thẻ nhận được — kết quả đã được xác định trước.</li>
      </ul>

      <h3>Tỷ lệ công bố</h3>
      <ul>
        {/* SET-SCOPED, deliberately. The engine allocates each open to a set
            and rolls inside it, so a whole-pool percentage is the probability
            of no open anyone actually receives. What IS stable across every set
            is the ratio between the tiers, because renormalising divides both
            by the same total — so that is what gets published here, and the
            exact per-set number lives on the card itself. */}
        <li>
          Mỗi lượt mở được tính cho <strong>một bộ</strong>, và thẻ được quay trong
          phạm vi bộ đó. Vì vậy tỷ lệ của một thẻ <strong>phụ thuộc vào bộ</strong> đang
          được mở — xem tỷ lệ chính xác ngay trên từng thẻ.
        </li>
        <li>
          Trong mọi bộ, thẻ thường có khả năng ra <strong>cao gấp khoảng{" "}
          {(COMMON.drawRate / RARE.drawRate).toFixed(1)} lần</strong> thẻ hiếm.
        </li>
        <li>Tổng tỷ lệ của tất cả thẻ trong <strong>cùng một bộ</strong> luôn bằng <strong>100%</strong>. Tỷ lệ hiển thị chính là tỷ lệ hệ thống quay.</li>
        <li>
          Bảo chứng thẻ hiếm: sau <strong>{DEMO_PITY_BACKSTOP} lượt mở</strong> liên tiếp không ra
          thẻ hiếm, lượt kế tiếp <strong>chắc chắn</strong> ra thẻ hiếm.
        </li>
        <li>Tỷ lệ và nội dung bộ không thay đổi khi mùa đang diễn ra.</li>
      </ul>

      <h3>Đổi thưởng</h3>
      <ul>
        <li>Bạn cần sở hữu <strong>toàn bộ thẻ</strong> trong một bộ mới đổi được thưởng của bộ đó.</li>
        {/* Sets are REPEATABLE and the exchange is DESTRUCTIVE. Both clauses
            here previously said the opposite — that cards were never consumed
            and that a set paid once per season. Publishing a term the product
            contradicts is worse than publishing nothing. */}
        <li>
          Đổi thưởng sẽ <strong>dùng hết một thẻ mỗi loại</strong> trong bộ. Bộ trở về{" "}
          <strong>0</strong> và bạn sưu tầm lại từ đầu.
        </li>
        <li>
          Một thẻ thuộc <strong>nhiều bộ</strong>, nên dùng thẻ cho bộ này cũng làm
          <strong> giảm tiến độ các bộ khác</strong> — trừ khi bạn có thẻ dự phòng.
          Màn hình xác nhận luôn hiển thị đầy đủ trước khi bạn đồng ý.
        </li>
        <li>
          <strong>Thẻ trùng là thẻ dự phòng.</strong> Giữ thẻ trùng để không mất tiến
          độ ở các bộ khác khi đổi thưởng.
        </li>
        <li>Mỗi bộ có thể đổi thưởng <strong>nhiều lần</strong>, mỗi lần cần sưu tầm lại đủ bộ.</li>
        <li>Thưởng được cộng vào <strong>ví chính</strong>, dùng được ngay, <strong>không kèm điều kiện cược</strong>, và có mã giao dịch để đối chiếu.</li>
      </ul>

      <h3>Những điều không áp dụng</h3>
      <ul>
        <li>Không bán lượt mở dưới bất kỳ hình thức nào.</li>
        <li>Không trao đổi, tặng hoặc chuyển thẻ giữa các tài khoản.</li>
        <li>Không thay đổi tỷ lệ hoặc nội dung bộ khi mùa đang diễn ra.</li>
      </ul>

      <p className="[margin:var(--space-3)_0_0] pt-space-2 [border-top:1px_dashed_var(--border)] text-t-micro text-text-dim leading-lh-body">
        Đây là bản demo. Tỷ lệ, phần thưởng và mức nhận lượt là số liệu tạm tính,
        chưa phải điều khoản công bố chính thức.
      </p>

      {/* History is NOT in this panel. It is unbounded, it is what support
          reads, and it needs a URL — "gửi cho tôi đường dẫn lịch sử" is a real
          support sentence and a modal has no link. */}
      <p className="sticky bottom-[0] [margin:var(--space-2)_0_0] [padding:var(--space-2)_0_0] [border-top:1px_solid_var(--border)] [background:var(--surface)]">
        <Link className="inline-flex items-center min-h-tap-min text-t-sm font-weight-semi text-text-hi no-underline hover:underline focus-visible:[outline:2px_solid_var(--focus-ring)] focus-visible:outline-offset-[2px]" href="/bo-suu-tap/cua-toi?tab=lich-su">
          Xem lịch sử →
        </Link>
      </p>
    </div>
  );
}

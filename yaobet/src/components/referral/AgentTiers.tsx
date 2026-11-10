/* ============================================================================
 * AgentTiers — affiliate tier ladder. The Đại lý
 * dashboard's tier overview. Tier NAMES + qualitative criteria are program
 * structure (not live numbers); commission rates are intentionally described as
 * "theo điều khoản chương trình" rather than fabricated %, so no false payout
 * figure is shown. The member's CURRENT tier is highlighted.
 * Server-rendered; the current-tier highlight comes from a passed level.
 * ==========================================================================*/

import { Card, Badge, Icon } from "@/ui";

export interface AgentTiersProps {
  /** the member's current affiliate level (0 = not yet an agent) */
  currentLevel: number;
}

interface AgentTier {
  level: number;
  name: string;
  criteria: string;
}

// Program structure — names + criteria only. NO fabricated commission %.
const TIERS: AgentTier[] = [
  { level: 1, name: "Đại lý Đồng", criteria: "Bắt đầu khi có thành viên giới thiệu hoạt động." },
  { level: 2, name: "Đại lý Bạc", criteria: "Đạt mốc thành viên hoạt động theo điều khoản." },
  { level: 3, name: "Đại lý Vàng", criteria: "Mở rộng mạng lưới giới thiệu ổn định." },
  { level: 5, name: "Đại lý Bạch kim", criteria: "Mạng lưới giới thiệu quy mô lớn, hoa hồng cao nhất." },
];

export function AgentTiers({ currentLevel }: AgentTiersProps) {
  return (
    <section className="flex flex-col gap-space-4" aria-label="Cấp đại lý">
      <h2 className="promo-type-h4 text-text-hi">Cấp đại lý</h2>
      <ul className="flex flex-col gap-space-3 list-none m-[0] p-[0]">
        {TIERS.map((t) => {
          const isCurrent = t.level === currentLevel;
          return (
            <li key={t.level}>
              <Card
                variant="vip"
                active={isCurrent}
                className="flex items-start gap-space-3 p-space-4"
              >
                <span className="inline-flex items-center justify-center w-[44px] h-[44px] flex-[0_0_auto] rounded-md [background:var(--surface-3)] [border:1px_solid_var(--brand-accent-hairline)] text-brand-accent-fg" aria-hidden="true">
                  <Icon name="trophy" size={22} />
                </span>
                <div className="flex flex-col gap-space-1 min-w-[0]">
                  <div className="flex items-center gap-space-2 flex-wrap">
                    <span className="text-t-body text-text-hi font-weight-bold">{t.name}</span>
                    {isCurrent && <Badge tone="gold">Cấp hiện tại</Badge>}
                  </div>
                  <span className="text-t-sm text-text-mid leading-lh-body">{t.criteria}</span>
                  <span className="text-t-micro text-text-mid">
                    Hoa hồng theo điều khoản chương trình
                  </span>
                </div>
              </Card>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

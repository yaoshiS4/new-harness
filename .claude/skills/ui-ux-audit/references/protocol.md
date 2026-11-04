# Full protocol: ui-ux-audit

Loaded on demand; see SKILL.md for triggers and core rules.

## 1. Audit Execution Protocol (4-Stage Workflow)

```text
╭────────────────────────────────────╮     ╭────────────────────────────────────╮
│ 1. Cognitive & Architecture Audit  │ ──▶ │ 2. Visual Symmetry & Breathability │
╰────────────────────────────────────╯     ╰────────────────────────────────────╯
                                                              │
                                                              ▼
╭────────────────────────────────────╮     ╭────────────────────────────────────╮
│ 4. Anti-Slop Sweep & Scoring       │ ◀── │ 3. Tokens, Typography & Motion     │
╰────────────────────────────────────╯     ╰────────────────────────────────────╯
```

1. **Stage 1 (Forensic Inspection)**: Examine component topology, cognitive layers (< 3s glance, < 30s action, on-demand deep-dive), duplicate props, and ghost fallback data.
2. **Stage 2 (Layout & Ergonomics)**: Verify 1:1 dual calendar symmetry, 50/50 polarity grids, card padding (≥ 16dp), grid gap (≥ 12dp), and touch boundaries (≥ 44 × 44dp iOS/Web, ≥ 48 × 48dp Android).
3. **Stage 3 (Tokens, Typography & Motion)**: Audit 60-30-10 palette, Single-Channel compound labels, Vietnamese diacritics (lineHeight ≥ 1.45× body, ≥ 1.25× display), 2:1 golden metric ratio, and synchronized motion tokens (`motion.spring.snappy` with `useNativeDriver: true`).
4. **Stage 4 (Anti-Slop Sweep & Verdict)**: Purge rogue star glyphs (`★`) from sub-lists, sanitize AI parenthetical explanations, eliminate icon-noun redundancies, and emit structured verdict.

---


---
## 2. The 12 Master Audit Dimensions & Verification Checklist

### Dimension 1: Kiến Trúc Thông Tin & Nhận Thức (Cognitive Architecture & Zero-Echo) [Bastien & Scapin: Workload Concision · NN/g: Heuristic #8 Minimalist Design]
- [ ] **[Tier 3: Visual Review] 3-Layer Cognitive Hierarchy**:
  - **Layer 1: Glance & Hook (< 3s)**: Hero card, high-impact numbers, 1 compound status badge. Max 3 main cards. CẤM inlined 12 double-hours or 30+ activity matrix here.
  - **Layer 2: Action & Triage (< 30s)**: Quick actionable tools (Top 3 Golden Hours, Do/Avoid highlights, directional hints). Strictly adheres to the **5-Item Threshold (Law 35)**: max 3-5 items on screen with explicit CTA triggers to Bottom Drawers.
  - **Layer 3: Deep-Dive (On-Demand)**: 12 Thời Thần timeline, 30+ Dụng Sự lookup, Bát Tự **BẮT BUỘC nằm ở Sub-Pages/Tabs hoặc Modals/Drawers**. CẤM inlined monolithic datasets on primary screens.
- [ ] **[Tier 2: Unit Test] Law of Zero-Echo & Tautological Copy Pruning**:
  - CẤM Card Echo: Không lặp lại cùng 1 thông tin thành 4 props/labels khác nhau trong cùng 1 thẻ.
  - CẤM lặp tiêu đề H2 ở câu đầu tiên của đoạn văn bản; CẤM nhãn kép cho Toggle Switch ("Status: BẬT").
- [ ] **[Tier 3: Visual Review] Triệt Tiêu Trùng Lặp Thông Tin (Information Deduplication)**:
  - Loại bỏ hoàn toàn sự trùng lặp giữa các header, card và sub-footer (ví dụ: đã có `THÁNG 7 ÂM` ở Hero thì Sub-footer chỉ hiển thị `Tháng Đủ (30 ngày)` / `Tháng Thiếu (29 ngày)`).
- [ ] **[Tier 2: Unit Test] Cấm Ghost Data Fallbacks**:
  - Tuyệt đối không gán cứng mảng dữ liệu mẫu giả lập khi ngày trống dữ liệu. Bắt buộc hiển thị Empty State điềm tĩnh (*"Ngày bình hòa, không có việc đại cát hay đại kỵ đặc thù"*).

---

### Dimension 2: Cân Bằng Đối Xứng Thị Giác & Độ Thở (Visual Symmetry & Breathability) [Gestalt Symmetry · IBM Carbon: Expressive/Productive Rhythm · Bastien & Scapin: Visual Grouping]
- [ ] **[Tier 2: Unit Test] Dual Calendar 1:1 Stacking Symmetry**:
  - Bảng so sánh Dương Lịch & Âm Lịch bắt buộc có cấu trúc 3 tầng đối xứng 1:1: `[Top Header Label -> Center Hero Numeral -> Bottom Subtitle Label]`.
  - Chữ số ngày Dương và Âm phải căn chỉnh thẳng hàng ngang tuyệt đối (`alignItems: 'baseline'`).
- [ ] **[Tier 3: Visual Review] Polarity Grid Symmetry (50/50)**:
  - Các thẻ so sánh 2 cực (Việc Nên Làm ↔ Việc Nên Tránh) phải cân bằng đối xứng về layout, dot indicators, font sizes, và lề ngăn cách.
- [ ] **[Tier 1: AST/Lint] Card Margins & Padding Floor**:
  - Card margin ngang ≥ 16dp, padding trong ≥ 16dp, khoảng cách grid gap ≥ 12dp.
- [ ] **[Tier 2: Unit Test] Mobile Density Ceiling**:
  - Trên màn hình di động (≤ 412dp), lưới hiển thị telemetry tối đa **2 cột**.
- [ ] **[Tier 2: Unit Test] Border-Free Tonal Elevation & Cấm Box-in-a-Box**:
  - Thẻ tiêu chuẩn khai báo `bordered={false}`, phân tầng bằng màu nền và khoảng cách. CẤM lồng hộp trong hộp (Box-in-a-Box); phân cách các mục con bằng đường chỉ mỏng hairlines (`rgba(255, 255, 255, 0.08)`).
- [ ] **[Tier 3: Visual Review] Calendar Row Breathing Room**:
  - Khoảng cách giữa hàng ngày cuối và dải đáy lịch tháng ≥ 6-8dp; khoảng cách giữa indicator dots và số ngày hàng dưới ≥ 6dp.

---

### Dimension 3: Màu Sắc, Tokens & Trạng Thái Đơn Kênh (Color Science & Single-Signal) [SLDS/DTCG 3-Tier Tokens · Bastien & Scapin: Significance of Codes · WCAG AA/AAA]
- [ ] **[Tier 3: Visual Review] 60-30-10 Chromatic Hierarchy & Typographic Calm**:
  - **60%**: Nền đen nhung Midnight (`#0B0E14` / `#10131A` / `#1D2026`).
  - **30%**: Màu chữ dịu mắt (`#E1E2EB` / `#D0C5AF`). CẤM in đậm tràn lan hoặc dùng màu sắc lòe loẹt khắp màn hình.
  - **10%**: Điểm nhấn kim loại quý (Vàng Hoàng Gia `#DFC15D`, Ngọc Bích `#2DD4BF`, Chu Sa `#FFB4AB`, Thanh Thiên `#38BDF8`).
- [ ] **[Tier 1: AST/Lint] 100% DTCG Token Compliance**:
  - Zero hardcoded hex values; 100% sử dụng token ngữ nghĩa (`colors.canvas.*`, `colors.text.*`, `colors.accent.*`).
- [ ] **[Tier 2: Unit Test] Single-Channel Status (Cấm Quad-Indicator Slop)**:
  - CẤM biểu diễn 1 trạng thái qua 4-5 kênh thị giác trùng lặp (nền màu + chấm màu + pill badge + nhãn % + text lặp lại + ngôi sao `★`).
  - Hợp nhất thành 1 nhãn typographic compound duy nhất (`★ Giờ Vàng · 70%` hoặc `Hoàng Đạo · 60%`).
- [ ] **[Tier 2: Unit Test] Pill Budget ≤ 2 Per Card**:
  - Mỗi thẻ chỉ được phép có tối đa **2 badge/pill có khung viền**.
- [ ] **[Tier 2: Unit Test] Deterministic Polarity Deduplication (Law 9)**:
  - Việc Nên Làm và Việc Nên Tránh phải được lọc triệt để loại trừ lẫn nhau: `sanitizedGood = rawGood.filter(x => !rawBad.includes(x))`.
  - Chuỗi toàn cục hung/cát quy về đúng 1 nhãn duy nhất (`"Mọi việc đều xấu"` / `"Mọi việc đều tốt"`).

---

### Dimension 4: Typography, Số Liệu Định Lượng & Tiếng Việt (Typography & Diacritics) [Bastien & Scapin: Legibility · Laws 13 & 19 · WCAG 2.2 Text Spacing]
- [ ] **[Tier 2: Unit Test] Vietnamese Diacritics Floor (Law 19)**:
  - Body/caption reading text: `lineHeight ≥ 1.45×` font-size (ví dụ: `fontSize: 14` → `lineHeight ≥ 21`, `fontSize: 16` → `lineHeight ≥ 24`).
  - Display/hero text: `lineHeight ≥ 1.25×` font-size.
  - Uppercase data/mono labels: `lineHeight ≥ 1.20×` font-size.
- [ ] **[Tier 1: AST/Lint] Zero Fixed Height On Text Containers**:
  - CẤM gán cứng `height: <px>` trên container chứa text động. Bắt buộc dùng `minHeight` và `paddingVertical`.
  - Mọi danh sách chips, badges, tags bắt buộc khai báo `flexDirection: 'row'`, `flexWrap: 'wrap'`, `gap: 8`.
- [ ] **[Tier 3: Visual Review] Golden Metric Ratio (2:1)**:
  - Mọi chỉ số định lượng (điểm `%`, độ số `128°`, nhiệt độ `28°C`) phải render số lớn gấp đôi (≈ 2×) đơn vị đi kèm và căn chỉnh chân dòng (`alignItems: 'baseline'`).
- [ ] **[Tier 2: Unit Test] Action-Oriented Scholar Microcopy**:
  - CẤM nút "Xem thêm", "Chi tiết", "Click đây", "Hoàn tất tra cứu".
  - Bắt buộc mở đầu bằng động từ hành động học thuật: **`"12 Thời Thần ›"`**, **`"Sổ tay Dụng Sự ›"`**, **`"Đánh Giá Khởi Sự"`**, **`"Tìm ngày ›"`**, **`"Đóng tra cứu"`**.

---

### Dimension 5: Tiết Kiệm Icon & Thanh Lọc Ký Tự (Icon Frugality & Anti-Glyph Slop) [NN/g: Icon Usability · Law 17: Zero Emoji & Zero Icon-Noun Redundancy]
- [ ] **[Tier 1: AST/Lint] Icon Budget**:
  - Tối đa **1 functional icon** cho mỗi interactive element (CTA/Button).
  - **0 icons** trên các thẻ hiển thị thông số/telemetry tĩnh khi typography đã có nhãn rõ ràng.
- [ ] **[Tier 2: Unit Test] Zero Emoji UI**:
  - CẤM 100% Emoji làm icon giao diện chức năng. Bắt buộc dùng Vector SVG có khung chuẩn 16dp-20dp.
- [ ] **[Tier 3: Visual Review] Zero Icon-Noun Redundancy**:
  - Không đặt icon mô tả trực diện danh từ bên cạnh (không đặt ✉️ cạnh "Email", 📅 cạnh "Ngày", 📍 cạnh "Địa điểm").
- [ ] **[Tier 2: Unit Test] Anti-Glyph Slop Sweep**:
  - Xóa bỏ toàn bộ ký tự `★` rải rác trong các danh sách con (*Tương Tác Bản Mệnh, Sổ Tay Dụng Sự*). Chỉ sử dụng bullet chuẩn `•` có điểm màu Hán phong.
  - Ký tự `★` chỉ xuất hiện trên duy nhất 1 huy hiệu Cát/Hung cấp cao nhất ở Hero Card.

---

### Dimension 6: Động Lực Học, Đồng Bộ Tokens & Hiệu Năng Khung Hình (Motion & Performance) [Doherty Threshold · M3 Shared-Axis Motion · Law 20: Asymmetric Motion]
- [ ] **[Tier 1: AST/Lint] Token-Synchronized Durations & Easings**:
  - Các thành phần chuyển động đồng thời theo thời gian cố định (ví dụ: Accordion mở lịch tháng và mũi tên xoay) **bắt buộc dùng chung duration (260ms)** và `Easing.bezier(0.25, 0.1, 0.25, 1)`.
- [ ] **[Tier 1: AST/Lint] Native Driver Invariant**:
  - 100% chuyển động transform/opacity phải khai báo `useNativeDriver: true`.
- [ ] **[Tier 2: Unit Test] Fluid Tab Glide**:
  - Sub-Nav Segmented chỉ dùng 1 đường gạch chân trượt duy nhất (`motion.tabGlide`, `mass: 0.8, stiffness: 280, damping: 24`). CẤM vừa sáng nền vừa bật gạch chân cùng lúc. Luôn đối chiếu giá trị lò xo với `src/theme/motion.ts` (SOT).
- [ ] **[Tier 2: Unit Test] PanResponder Snap-Back Physics**:
  - Mọi thao tác vuốt thả (Pager tuần, Pager tháng) dùng chung token lò xo `motion.spring.snappy` (`mass: 0.8, stiffness: 180, damping: 12`).
- [ ] **[Tier 3: Visual Review] 60fps / 120fps Frame Budget & Layout Stability (CLS = 0)**:
  - Zero dropped frames khi cuộn, vuốt pager hoặc mở đóng accordion; không giật nảy layout.

---

### Dimension 7: Quét Sạch AI Slop & Anti-Patterns (AI Slop Ban-List) [NN/g Heuristic #8 · Bastien & Scapin: Workload Brevity]
- [ ] **[Tier 2: Unit Test] Cấm Dấu Ngoặc Đơn Giải Thích Ngữ Nghĩa (AI Parenthetical Tells)**:
  - CẤM đặt ngoặc giải thích kiểu `"Tra Cứu Khởi Sự (Dụng Sự)"` → Đổi thành `"Đánh Giá Khởi Sự"`.
- [ ] **[Tier 2: Unit Test] Cấm Số Thứ Tự Trang Trí (Eyebrow Numbers)**:
  - CẤM chèn "01 / 02 / 03" vào tiêu đề nếu nội dung không phải là một chuỗi tuần tự có chủ đích.
- [ ] **[Tier 2: Unit Test] Cấm Nhãn Kép Cho Công Tắc**:
  - CẤM ghi "Trạng thái: BẬT" cạnh Toggle Switch.
- [ ] **[Tier 2: Unit Test] Cấm Badges Tự Hiển Nhiên**:
  - Không gắn badge "Cài đặt" lên dòng cài đặt. Badges chỉ dùng cho trạng thái động (`Mới`, `Lỗi`, `Hoàng Đạo`).
- [ ] **[Tier 3: Visual Review] Cấm Div-Based Fake Screenshots**:
  - Không dùng các hình chữ nhật giả lập giao diện; dùng component thật hoặc vector tinh gọn.

---

### Dimension 8: Công Thái Học Chạm, Drawer & Trạng Thái Tương Tác (Ergonomics & 8-States) [Apple HIG Touch Targets · Google M3 8-States · WCAG 2.2 Criterion 2.5.8]
- [ ] **[Tier 1: AST/Lint] Touch Target Floor**:
  - Vùng chạm ≥ 44 × 44dp (iOS/Web), ≥ 48 × 48dp (Android Material 3). Mọi nút nhỏ/link text bắt buộc khai báo `hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}` và `minHeight: 44`.
- [ ] **[Tier 1: AST/Lint] Khoảng Cách Nút Liền Kề**:
  - Khoảng cách giữa 2 điểm chạm liền kề ≥ 8dp.
- [ ] **[Tier 2: Unit Test] Đồng Bộ Drawers & Modal Sheets**:
  - Mọi Bottom-Sheet Drawer dùng chung nền `colors.canvas.midnight` hoặc `colors.canvas.surface`, viền `colors.border.gold` (`rgba(223, 193, 93, 0.25)`).
  - Safe Area Padding: `paddingBottom: Platform.OS === "ios" ? 34 : 20`.
- [ ] **[Tier 2: Unit Test] Đầy Đủ 8 Trạng Thái Tương Tác (8-States Coverage)**:
  - Đã định nghĩa và kiểm thử đủ 8 trạng thái: `default`, `hover/press`, `focus-visible`, `active`, `disabled`, `loading (skeleton)`, `empty (calm academic copy)`, `error (with remedy CTA)`.

---

### Dimension 9: Cấu Trúc Mã Nguồn & Giới Hạn Kích Thước File (Codebase Topology Budget) [Bastien & Scapin: Consistency · Law 16: 6-Tier JSX Taxonomy]
- [ ] **[Tier 1: AST/Lint] File Size Budget**:
  - File màn hình (`*Screen.tsx`) ≤ 200 dòng; Card/Tab (`*Card.tsx`, `*Tab.tsx`) ≤ 250 dòng.
- [ ] **[Tier 3: Visual Review] 6-Tier JSX Taxonomy**:
  - File component bắt buộc tuân theo 6 khối chuẩn: Docstring → Grouped Imports → Props Interface → Main Component → Sub-renderers → Token StyleSheet.
- [ ] **[Tier 1: AST/Lint] Zero Dead Code**:
  - Không còn file rác, mock data hay export component mồ côi trong các file barrel (`index.ts`).

---

### Dimension 10: Điều Hướng Liền Mạch, Tầm Chạm & Tránh Điểm Chết (Userflow Continuity, Reachability & Atomic Annoyances - Laws 31–34) [NN/g Heuristic #3 User Control · Fitts's Law 2.0 · Bastien & Scapin: Explicit Control]
- [ ] **[Tier 3: Visual Review] Triệt Tiêu Điểm Chết Luồng & Điều Hướng Liền Mạch (Connected Navigation & Non-Trapping Flow - Law 31)**:
  - Mọi modal, sheet drawer, và màn hình kết quả tính toán/chiêm đoán bắt buộc có lối thoát trực quan (nút quay lại `‹` góc trên cùng, nhãn nguồn rõ ràng như `‹ Thiền Viện`, hỗ trợ drag-to-dismiss). Tuyệt đối CẤM để user rơi vào ngõ cụt thao tác hoặc bị mắc kẹt trên trang kết quả mà không có đường trở về màn hình khởi tạo ban đầu.
- [ ] **[Tier 2: Unit Test] Tầm Chạm Hành Động Trên Đường Gấp Màn Hình (Above-the-Fold Action Reachability & Anti-Fold Fall - Law 32)**:
  - Nút hành động chính (Gieo lại / Tính toán lại) và công cụ chuyển đổi phương thức BẮT BUỘC nằm trong vùng nạp nhận thức đầu tiên trên đường gấp màn hình ($\le 240\text{dp}$ từ đỉnh component hoặc neo cố định vùng ngón cái đáy). TUYỆT ĐỐI CẤM đẩy các nút hành động chính xuống đáy sau các thẻ nội dung đồ sộ ($\ge 300\text{dp}$) khiến người dùng phải cuộn tìm kiếm.
- [ ] **[Tier 2: Unit Test] Tinh Giản Icon Nút Tùy Chọn Thay Vì Chữ Rườm Rà (Compact Icon Triggers Over Text Bloat - Law 33)**:
  - Nút tùy chọn phương thức/nghi thức hoặc cài đặt phụ cạnh nút CTA chính BẮT BUỘC dùng nút icon chuẩn hình tròn/pill bo tròn ($\ge 44\times 44\text{dp}$ diện tích chạm với vector/phosphor icon), TUYỆT ĐỐI CẤM dùng nút chữ rườm rà kèm mũi tên xổ xuống (`▾`).
- [ ] **[Tier 2: Unit Test] Cân Bằng Đối Xứng Trục Ngang (Bilateral Visual Symmetry & Balanced Flanks - Law 34)**:
  - Thanh công cụ hành động, header đầu trang và hàng nút điều khiển bắt buộc cân bằng đối xứng hoàn hảo qua trục dọc trung tâm (ví dụ: hai nút icon tròn 44×44dp ở hai cánh kẹp nút CTA chính ở giữa; hoặc căn giữa tuyệt đối tiêu đề kẹp giữa nút Back và Badge trạng thái có cùng trọng lượng thị giác).
- [ ] **[Tier 2: Unit Test] Độ Thở Hàng Nút Bấm & Khoảng Cách Biên (Button Breathability & Spacing Floor)**:
  - Hàng chứa nhiều nút bấm bắt buộc duy trì khoảng cách `gap >= 12dp` (chuẩn mực `spacing.md` 16dp). CẤM các cụm nút bấm dính chùm chỉ có 8dp gap gây nhầm lẫn khi chạm ngón tay. Diện tích chạm tối thiểu $\ge 44\text{dp}$ (iOS) / $\ge 48\text{dp}$ (Android).
- [ ] **[Tier 2: Unit Test] Tuân Thủ Tuyệt Đối Design Tokens Cho Tab Đa Tầng (Multi-Level Navigation Token Contract)**:
  - Tab tầng 1 bắt buộc dùng `tab-level-1-underline` (gạch chân trượt 2.5px, container trong suốt không nền, không viền). Tab tầng 2 chuyển phân hệ/pha quẻ bắt buộc dùng `tab-level-2-pill` (`PillTab` bo tròn `radii.full`, container trong suốt không nền, không viền/outline, chỉ pill active nhận nền vàng ấm `rgba(223, 193, 93, 0.18)`). TUYỆT ĐỐI CẤM tự chế các thanh stepper dạng hộp, mũi tên thủ công gây vỡ nhịp điệu thiết kế.
- [ ] **[Tier 2: Unit Test] Cấm Modal Inception (Chồng Lớp Modal)**:
  - CẤM mở modal toàn màn hình đè lên modal toàn màn hình khác. Thay bằng step transitions trong 1 drawer duy nhất hoặc accordion expand tại chỗ.
- [ ] **[Tier 2: Unit Test] Bảo Toàn Công Sức Người Dùng (State Continuity & Zero-Wipe)**:
  - Khi validation lỗi hoặc chuyển tab, TUYỆT ĐỐI KHÔNG xóa trắng form đã nhập hoặc reset ngày đã chọn (`selectedDate`).
- [ ] **[Tier 3: Visual Review] Không Che Khuất Form Nhập (Virtual Keyboard Avoidance)**:
  - Trường nhập liệu đang focus không bao giờ bị bàn phím ảo che khuất (`KeyboardAvoidingView` chuẩn xác, auto-scroll to active input).
- [ ] **[Tier 2: Unit Test] Ngắt Dòng Chuỗi Kép Theo Divider (Clean Compound String Wrapping - Law 24)**:
  - Khi chuỗi ghép chứa divider (`·`, `*`, `/`, `-`, `&`, `(...)`) dài quá 1 dòng, BẮT BUỘC chủ động ngắt dòng ngay tại divider (`\n` hoặc bố cục 2 dòng riêng). CẤM auto-wrap ngắt cụt lủn ở giữa từ ngữ của vế thứ hai.
- [ ] **[Tier 2: Unit Test] Loại Bỏ Phụ Đề Thừa Dưới Tiêu Đề Section (Zero Redundant Section Subtitles - Law 12)**:
  - CẤM thêm các đoạn subtitle/subtext giải thích thừa thãi, chung chung dưới tiêu đề section. Tiêu đề mục phải cô đọng, uy nghi với Eyebrow + Title alone.
- [ ] **[Tier 2: Unit Test] Ngưỡng 5 Phần Tử & Tách Tải Sổ Tay Đầy Đủ Sang Bottom Drawer Card (The 5-Item Threshold & Canonical Drawer Offloading - Law 35)**:
  - Mọi tập dữ liệu kinh điển hoặc lặp lại $> 5$ phần tử (12 Thời Thần, 28 Tú, 12 Trực, 30+ Dụng Sự, 8 Cung Bát Trạch, 6 Hào Biến Hóa) TUYỆT ĐỐI CẤM hiển thị dàn trải nguyên khối trên canvas Layer 1/2.
  - Bắt buộc tinh tuyển $\le 3-5$ phần tử hành động nhanh cho Layer 2; tách tải toàn bộ sổ tay dữ liệu sang Bottom Drawer Card (`sheetDetents.medium: 0.52` / `sheetDetents.large: 0.90`) hoặc Sub-Page tab riêng.
- [ ] **[Tier 3: Visual Review] Đồng Bộ Phản Hồi Chạm & Haptics (Touch Feedback Consistency)**:
  - Mọi interactive control có visual feedback (`activeOpacity`, haptic) rõ ràng; các thẻ hiển thị tĩnh tuyệt đối không phát ra hiệu ứng click giả.
- [ ] **[Tier 3: Visual Review] Triệt Tiêu Giật Nảy Giao Diện (CLS = 0 & Zero Visual Jitter)**:
  - Không có hiện tượng giật nảy khi load dữ liệu hoặc hình ảnh; pre-reserve kích thước và skeleton tĩnh tại.

---

### Dimension 11: Công Thái Học Vùng Chạm Ngón Cái & Minh Bạch Thuật Toán (Thumb-Zone Ergonomics & Explainability) [Fitts's Law · Uber Base Thumb Ergonomics · Google PAIR Calibrated Confidence]
- [ ] **[Tier 1: AST/Lint] Thumb-Zone Reachability (Law 25)**:
  - Primary interactive controls, date pickers, và main CTA đặt ở vùng 40% đáy màn hình (Natural Reach Zone). Đỉnh màn hình chỉ dành cho passive telemetry và visual hook.
- [ ] **[Tier 2: Unit Test] Triệt Tiêu Fake Decimal Precision & Calibrated Confidence (Law 26)**:
  - CẤM hiển thị điểm cát hung dạng số thập phân giả tạo (regex `/\d+\.\d+%/`). Bắt buộc làm tròn đến bội số của 5% hoặc 10% (hoặc nhãn định tính). Mọi điểm số thuật số phải có anchor giải trình nguyên nhân ("Vì sao có kết quả này?").
- [ ] **[Tier 2: Unit Test] Dynamic Type Reflow & Tỷ Lệ Co Giãn (Law 27)**:
  - Không vỡ layout khi font scale tăng đến 200%. Dynamic text containers bắt buộc dùng `minHeight` và `flexWrap: 'wrap'` phòng thủ.

---

### Dimension 12: Apple HIG Deference, Phản Hồi Xúc Giác Đa Tầng & Vùng An Toàn Đáy (Apple HIG Ergonomics) [Apple HIG: Deference, Depth, Haptics, Safe Area Buffer, Non-Destructive Undo]
- [ ] **[Tier 1: AST/Lint] Home Indicator Exclusion Zone**:
  - Mọi docked bottom action bar, floating sheet drawer bắt buộc khai báo `paddingBottom: insets.bottom + 12` (tối thiểu ≥ 34pt iOS / ≥ 20dp Android gesture bar). CẤM đặt nút tương tác dính sát mép đáy màn hình.
- [ ] **[Tier 2: Unit Test] Apple HIG Deference & Minimal Chrome**:
  - UI chrome (bars, tabs, borders) phải lùi lại để nhường spotlight cho nội dung nông lịch/thiên văn. CẤM các khung viền dày, bóng đổ thô đặc (`elevation > 8` không kiểm soát).
- [ ] **[Tier 2: Unit Test] 3-Tier Sensory Tactile Hierarchy**:
  - Phản hồi rung haptic tuân thủ đúng 3 tầng: `selection` (wheel/tab), `impact` (gieo quẻ/lật bài/snap detent), `notification` (thành công/cảnh báo hung). CẤM rung bừa bãi phá vỡ sự trang nghiêm, tĩnh tại.
- [ ] **[Tier 3: Visual Review] Sheet Detents & Non-Destructive Undo**:
  - Modal drawers hỗ trợ detents mượt mà. Reversible actions cung cấp thanh Undo Toast (≥ 5s) thay vì hộp thoại hỏi dồn dập.

---

## 3. Output Format & Scoring Verdict

Khi thực hiện audit UI/UX cho bất kỳ component hoặc trang nào, xuất báo cáo theo mẫu chuẩn:

```yaml
ui_ux_audit_verdict:
  target: "<ComponentOrScreenPath>"
  status: PASS | CONDITIONAL | FAIL
  score: <0-100> # Pass threshold >= 94
  dimensions:
    cognitive_architecture: PASS | FAIL
    visual_symmetry: PASS | FAIL
    color_tokens: PASS | FAIL
    typography_diacritics: PASS | FAIL
    icon_frugality: PASS | FAIL
    motion_sync: PASS | FAIL
    ai_slop_sweep: PASS | FAIL
    touch_ergonomics: PASS | FAIL
    file_topology: PASS | FAIL
    userflow_continuity_and_atomic_annoyances: PASS | FAIL
    thumb_zone_and_explainability: PASS | FAIL
    apple_hig_deference_and_haptics: PASS | FAIL
  critical_violations: []
  recommended_patches: []
```

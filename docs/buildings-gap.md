# BUILDINGS-GAP — đối chiếu dữ liệu tòa với nội dung đã publish trên site

> Phase 1 của kế hoạch mở rộng SEO trang tòa. Đối chiếu `data/buildings.json`
> (sinh bởi `scripts/trich-xuat-toa.py` từ `data.json`) với những gì các
> trang tĩnh trên site **đã viết bằng lời** về số lượng/tên tòa, và với
> `SEO-CONTENT-PLAN.md`. Chỉ liệt kê khoảng trống — **không tự bổ sung, không
> tự đoán tên tòa còn thiếu**, theo đúng ràng buộc #8 của `SEOEXPANSIONPLAN.md`.

---

## 1. Đối chiếu từng phân khu (tòa được nhắc trong nội dung vs tòa có trong `data.json`)

| Phân khu | Trang nhắc | Tòa nhắc trong nội dung (nguyên văn) | Tòa có trong `data.json` (mọi trạng thái) | Khớp? |
|---|---|---|---|---|
| Sapphire | `sapphire/index.html` dòng 877-878 | "Sapphire 1 (S1.01–S1.06, không có S1.04), Sapphire 2 (S2.01, S2.02, S2.03, S2.05), Sapphire 3 (S3.01–S3.03) và Sapphire 4" (S4 không liệt kê chi tiết ở câu này) | S101,S102,S103,S105,S106,S201,S202,S203,S205,S301,S302,S303,S401,S402,S403 (15 tòa) | ✅ Khớp hoàn toàn với phần đã liệt kê chi tiết (S1: 01,02,03,05,06 — đúng 5, thiếu 04 đúng như văn bản nói; S2: 01,02,03,05 — đúng 4, thiếu 04; S3: 01,02,03 — đúng 3). Trang không liệt kê chi tiết S4 nên không đối chiếu được câu này, nhưng `data.json` có sẵn S401/S402/S403. |
| Masteri | `masteri/index.html` dòng 601-602 và FAQ | "bốn tòa West A, West B, West C và West D" | MASA, MASB, MASC, MASD (4 tòa) | ⚠️ **Số lượng khớp (4 tòa)** nhưng **tên không khớp trực tiếp**: `data.json` dùng mã `MasA/MasB/MasC/MasD`, trang lại gọi bằng tên `West A/B/C/D`. Rất có khả năng đây là cùng một tòa (A=West A, B=West B...) nhưng **không có field nào trong `data.json` xác nhận trực tiếp** — quan hệ này chỉ là suy đoán theo thứ tự chữ cái, phải xếp vào diện "chưa xác minh", KHÔNG tự ghi `ten_hien_thi` là "West A" trong `data/buildings.json`. |
| Sakura | `sakura/index.html` dòng 397-398 | "bốn tòa SA1, SA2, SA3 và SA5" | SA1, SA2, SA3, SA5 (4 tòa) | ✅ Khớp hoàn toàn. |
| Miami | `miami/index.html` | Không tìm thấy câu liệt kê tên tòa cụ thể (chỉ có "tòa v...", "tòa m..." — cần xem lại nếu cần trích, không phải danh sách tên tòa) | GS1, GS2, GS3, GS5, GS6 (5 tòa) | ⚪ Không có gì để đối chiếu — trang Miami hiện không liệt kê tên tòa bằng lời như 4 phân khu kia. |
| Imperia | `imperia/index.html` dòng 301-304 | "năm tòa I1 đến I5" | I1, I2, I3, I4, I5 (5 tòa) | ✅ Khớp hoàn toàn. |
| Canopy | `canopy/index.html` dòng 265 | "ba tòa TC1, TC2, TC3" | TC1, TC2, TC3 (3 tòa) | ✅ Khớp hoàn toàn. |
| Tonkin | `tonkin/index.html` dòng 157 | "hai tòa TK1 và TK2" | TK1, TK2 (2 tòa) | ✅ Khớp hoàn toàn. |
| Lumiere | `lumiere/index.html` | Không tìm thấy câu liệt kê tên tòa cụ thể | A2, A3 (2 tòa) | ⚪ Không có gì để đối chiếu. |

**Không có tòa nào được nhắc trong nội dung mà hoàn toàn vắng mặt trong
`data.json`** (khác với ví dụ giả định ban đầu trong `SEOEXPANSIONPLAN.md`
dòng 122 — West A-D **có** dữ liệu, chỉ là tên gọi không khớp chữ, xem mục 2).

## 2. Việc CẦN xác nhận thủ công (không tự suy diễn)

1. **Tên hiển thị của 4 tòa Masteri**: `data.json` ghi `MasA/MasB/MasC/MasD`,
   nội dung trang `masteri/index.html` gọi 4 tòa này là `West A/B/C/D`. Nếu
   đúng là cùng một tòa theo đúng thứ tự (MasA=West A, MasB=West B,
   MasC=West C, MasD=West D), Phase 2 nên dùng tên "West A" (khớp thương
   hiệu chủ đầu tư Masterise Homes đặt) thay vì "MasA" khi hiển thị `<h1>`/
   `<title>` trang tòa Masteri, thay vì mã nội bộ. **Cần chị Thủy/đội vận
   hành xác nhận đúng cặp tương ứng trước khi Phase 2 chốt `ten_hien_thi`**.
   `data/buildings.json` hiện để `ma_toa` = mã chuẩn hoá thô (`MasA` v.v.),
   không tự đổi thành "West A".

2. **Chênh lệch số căn Masteri**: tổng 4 tòa MasA+MasB+MasC+MasD trong
   `data/buildings.json` tại thời điểm trích xuất là **46 căn**
   (9+19+8+10), trong khi `masteri/index.html` (sinh gần nhất cùng ngày
   24/08/2026) hiển thị **44 căn**. Chênh lệch 2 căn nhiều khả năng do
   `data.json` được Apps Script ghi đè ~30 phút/lần và hai lần trích xuất
   không cùng thời điểm — **không phải lỗi cần sửa**, chỉ ghi nhận để không
   ai hiểu nhầm là mất căn. Không cần hành động ở Phase 1.

3. **Miami và Lumiere chưa có câu liệt kê tên tòa bằng lời** trên trang phân
   khu tương ứng — không phải lỗi (chưa từng hứa liệt kê), nhưng có nghĩa là
   khi Phase 3 làm khối "Các tòa thuộc {Phân khu}" cho 2 phân khu này, đó sẽ
   là lần đầu tiên site nói rõ tên các tòa GS1/GS2/GS3/GS5/GS6 và A2/A3 bằng
   chữ — nên biên tập cẩn thận vì không có tiền lệ để đối chiếu.

4. **`GS2` — ví dụ URL trong chính `SEOEXPANSIONPLAN.md` dòng 142** hiện chỉ
   có **2 căn đang hiển thị**, dưới ngưỡng 3 căn. Nếu dùng đúng dữ liệu hôm
   nay, `/gs2-vinhomes-smart-city/` **sẽ không được sinh** ở đợt đầu Phase 2
   (nằm trong nhóm "dưới ngưỡng" của `data/buildings.json`). Nêu rõ để không
   ai ngạc nhiên khi thấy ví dụ trong tài liệu gốc không xuất hiện trong đợt
   publish đầu tiên — GS2 có thể đạt ngưỡng ở lần trích xuất sau nếu chủ nhà
   thêm căn.

## 3. Đối chiếu với `SEO-CONTENT-PLAN.md` (đợt audit SEO trước)

Grep toàn bộ `SEO-CONTENT-PLAN.md`: tài liệu đó **không nhắc tới bất kỳ mã
tòa cụ thể nào** (không có `S4.01`, `GS2`, `TC1`...) — toàn bộ đề xuất ở đó
dừng ở cấp **phân khu** (mục 2.1: 5 phân khu còn thiếu pillar) và **loại
căn × phân khu** (mục 3.1 "Cluster 3", ngưỡng ≥10 căn, ví dụ `/sapphire/2pn/`).
Không có xung đột trực tiếp về tên/mã tòa giữa hai kế hoạch. Chi tiết ma
trận chồng chéo file/trang giữa hai kế hoạch xem báo cáo Phase 1
(`docs/phase1-bao-cao.md` mục B5).

## 4. Việc KHÔNG làm ở Phase 1 (nhắc lại)

- Không tự đặt `ten_hien_thi` = "West A/B/C/D" cho 4 tòa Masteri khi chưa có
  xác nhận (mục 2.1).
- Không tự loại GS2 hay bất kỳ tòa nào khỏi `data/buildings.json` — file vẫn
  liệt kê đủ 40 tòa, chỉ đánh dấu `dat_nguong_sinh_trang: false` cho 7 tòa
  dưới ngưỡng, để Phase 2 tự quyết dựa trên dữ liệu tại thời điểm publish.
- Không sửa nội dung bất kỳ trang phân khu nào ở Phase 1 (việc đó thuộc
  Phase 3).

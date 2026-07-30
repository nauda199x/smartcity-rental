# SEO-AUDIT — đợt cập nhật tháng 7/2026

Báo cáo kiểm tra theo yêu cầu **Task A3** của SPEC. Toàn bộ 38 trang HTML có sẵn
trong repo đã được rà từng hạng mục; trang mới `bang-gia-thue-vinhomes-smart-city.html`
(Task B) nâng tổng số lên 39 trang.

Nguyên tắc áp dụng: **chỉ sửa hạng mục còn thiếu hoặc còn sai, không ghi đè phần đã đúng.**

---

## 1. Tổng quan trước / sau

| Hạng mục | Trước | Sau |
|---|---|---|
| Trang có đúng 1 canonical, non-www, https | 37/38 | **39/39** |
| Trang có đúng 1 thẻ `<h1>` | 38/38 (đã đúng sẵn) | **39/39** |
| Cấu trúc heading không nhảy cấp | 37/38 | **39/39** |
| Title ≤ 60 ký tự | 14/38 | **39/39** |
| Title không trùng nhau | 38/38 (đã đúng sẵn) | **39/39** |
| Meta description trong khoảng 140–160 ký tự | 17/38 | **39/39** |
| JSON-LD parse được | 38/38 (đã đúng sẵn) | **39/39** |
| Schema `Article` đủ 5 field bắt buộc | 2/8 | **8/8** |
| `.gitignore` chặn file rác | không có file | **đã thêm** |

---

## 2. A1 — Dọn dẹp thư mục rác

| Hạng mục | Kết quả |
|---|---|
| `mnt/user-data/outputs/` | **Đã đúng sẵn — bỏ qua.** Đường dẫn này chỉ còn dấu vết trong lịch sử của nhánh cũ đã đóng (2 file), không còn trong cây làm việc của `main`. Không có gì để xóa. |
| `.DS_Store`, `outputs/`, `temp/`, file `.zip` còn sót | **Đã đúng sẵn — bỏ qua.** Quét toàn bộ repo (kể cả file chưa được git theo dõi): không tìm thấy file nào. |
| `.gitignore` | **ĐÃ SỬA — tạo mới.** Chặn `.DS_Store`, `Thumbs.db`, `mnt/`, `outputs/`, `temp/`, `tmp/`, `*.zip`, `node_modules/`. |
| `robots.txt` | **Đã đúng sẵn — bỏ qua.** Chỉ có `Allow: /` và dòng Sitemap, không có dòng nào trỏ tới đường dẫn rác. |

---

## 3. A2 — Canonical, heading, Article schema, 404

| File | Đã sửa | Đã đúng sẵn (bỏ qua) |
|---|---|---|
| `404.html` | Thêm thẻ `<link rel="canonical">` còn thiếu (trang duy nhất chưa có) | Có `<h1>`, có `noindex, follow`, có link về trang chủ + đủ 3 nhóm danh mục (loại căn / phân khu / khoảng giá) |
| `index.html` | Đổi `<h4>` trang trí trong hộp thoại "Đã nhận được yêu cầu" thành `<div class="tieu-de">` + CSS — gỡ bước nhảy H2 → H4 (trang duy nhất bị nhảy cấp) | Canonical, 1 thẻ `<h1>`, schema `RealEstateAgent` (đã kiểm lại sau khi sửa: vẫn hợp lệ, 11 thuộc tính, `FAQPage` cùng khối vẫn parse được) |
| `bang-gia-thue-smart-city-thang-7-2026.html` | Thêm field `image` vào `Article` | `headline`, `datePublished`, `dateModified`, `author`, `publisher`, canonical, heading |
| `gia-thue-studio-smart-city.html` | Thêm field `image` vào `Article` | 4 field còn lại của `Article`, canonical, heading |
| `kinh-nghiem-thue-chung-cu-smart-city.html` | Thêm field `image` vào `Article` | 4 field còn lại của `Article`, canonical, heading |
| `luu-y-do-xe-thu-cung-phi-dich-vu-smart-city.html` | Thêm field `image` vào `Article` | 4 field còn lại của `Article`, canonical, heading |
| `phi-dich-vu-vinhomes-smart-city.html` | Thêm field `image` vào `Article` | 4 field còn lại của `Article`, canonical, heading |
| `tien-ich-vinhomes-smart-city.html` | Thêm field `image` vào `Article` | 4 field còn lại của `Article`, canonical, heading |
| `cho-thue-can-ho-masteri-west-heights-smart-city.html` | — | **`Article` đã đủ cả 5 field từ trước, không sửa** |
| `so-sanh-gia-thue-cac-phan-khu-smart-city.html` | — | **`Article` đã đủ cả 5 field từ trước, không sửa** |
| 25 trang danh mục (`studio/`, `1pn/`, `sapphire/`, …) | — | Canonical, `<h1>` duy nhất, heading không nhảy cấp, `BreadcrumbList` + `ItemList` + `FAQPage` đều hợp lệ |
| `chinh-sach-quyen-rieng-tu.html`, `gui-thue/index.html`, `cam-nang-thue-nha.html` | — | Canonical, heading đều đã đúng |

**Ghi chú về ảnh trong schema:** mọi URL đưa vào field `image` đã được kiểm tra là
file có thật trong repo, không dùng đường dẫn phỏng đoán.

**Ghi chú về canonical của `404.html`:** trang này đã có `noindex` nên Google sẽ bỏ qua
canonical. Thẻ được thêm vào để đạt yêu cầu "mọi trang HTML có đúng 1 canonical" của SPEC;
không gây tác dụng phụ nhưng cũng không mang lại lợi ích SEO thực tế.

---

## 4. A2 — Title (24 trang đã sửa)

Tất cả đã rút xuống ≤ 60 ký tự, vẫn giữ từ khóa chính + "Smart City", 39/39 trang không trùng title.
Các con số (số căn, giá từ) là số đã có sẵn trong title cũ, **không tự sinh số mới**.

| File | Trước (ký tự) | Sau (ký tự) |
|---|---|---|
| `index.html` | Thuê chung cư Smart City — Cho thuê căn hộ Vinhomes Smart City T07/2026 (71) | Thuê chung cư Smart City – Cho thuê căn hộ Vinhomes T07/2026 (60) |
| `1pn/index.html` | 71 | 55 |
| `2pn/index.html` | 71 | 55 |
| `3pn/index.html` | 72 | 56 |
| `1pn-plus/index.html` | 66 | 53 |
| `2pn-plus/index.html` | 68 | 55 |
| `studio/index.html` | 66 | 55 |
| `2pn-full-do/index.html` | 61 | 55 |
| `3pn-full-do/index.html` | 61 | 55 |
| `sapphire/index.html` | 62 | 55 |
| `masteri/index.html` | 67 | 60 |
| `miami/index.html` | 63 | 56 |
| `sakura/index.html` | 62 | 55 |
| `imperia/index.html` | 61 | 54 |
| `lumiere/index.html` | 64 | 57 |
| `canopy/index.html` | 68 | 56 |
| `tonkin/index.html` | 64 | 57 |
| `gui-thue/index.html` | 72 | 59 |
| `cam-nang-thue-nha.html` | 62 | 52 (đồng thời escape `&` thành `&amp;` cho hợp lệ HTML) |
| `kinh-nghiem-thue-chung-cu-smart-city.html` | 67 | 58 |
| `luu-y-do-xe-thu-cung-phi-dich-vu-smart-city.html` | 68 | 52 |
| `so-sanh-gia-thue-cac-phan-khu-smart-city.html` | 76 | 58 |
| `tien-ich-vinhomes-smart-city.html` | 67 | 54 |
| `gia-thue-studio-smart-city.html` | 61 | 51 |

**Đã đúng sẵn — bỏ qua (14 trang):** `404.html`, `chinh-sach-quyen-rieng-tu.html`,
`phi-dich-vu-vinhomes-smart-city.html`, `bang-gia-thue-smart-city-thang-7-2026.html`,
`cho-thue-can-ho-masteri-west-heights-smart-city.html`, `1pn-plus-duoi-10-trieu/`,
`1pn-plus-full-do/`, `2pn-10-12-trieu/`, `2pn-duoi-10-trieu/`, `2pn-plus-12-15-trieu/`,
`3pn-12-15-trieu/`, `studio-7-10-trieu/`, `studio-duoi-7-trieu/`, `studio-full-do/`.

---

## 5. A2 — Meta description (21 trang đã sửa)

Tất cả đã vào khoảng 140–160 ký tự. Với các trang mô tả quá ngắn, phần bổ sung là nội dung
định tính có thật (ảnh thật từng căn, đặt lịch xem nhà) — **không thêm con số nào không có
trong dữ liệu**. Với các trang quá dài, chỉ cắt bớt, giữ nguyên các số liệu cũ.

| File | Trước | Sau |
|---|---|---|
| `studio/index.html` | 139 | 156 |
| `studio-duoi-7-trieu/index.html` | 121 | 148 |
| `studio-7-10-trieu/index.html` | 119 | 153 |
| `studio-full-do/index.html` | 137 | 155 |
| `1pn/index.html` | 132 | 150 |
| `1pn-plus-duoi-10-trieu/index.html` | 119 | 147 |
| `1pn-plus-full-do/index.html` | 130 | 145 |
| `2pn-duoi-10-trieu/index.html` | 127 | 144 |
| `2pn-10-12-trieu/index.html` | 115 | 149 |
| `2pn-full-do/index.html` | 128 | 143 |
| `2pn-plus-12-15-trieu/index.html` | 127 | 141 |
| `3pn-12-15-trieu/index.html` | 115 | 149 |
| `3pn-full-do/index.html` | 129 | 144 |
| `tonkin/index.html` | 163 | 140 |
| `bang-gia-thue-smart-city-thang-7-2026.html` | 163 | 147 |
| `chinh-sach-quyen-rieng-tu.html` | 136 | 153 |
| `gia-thue-studio-smart-city.html` | 129 | 152 |
| `kinh-nghiem-thue-chung-cu-smart-city.html` | 165 | 144 |
| `luu-y-do-xe-thu-cung-phi-dich-vu-smart-city.html` | 162 | 143 |
| `so-sanh-gia-thue-cac-phan-khu-smart-city.html` | 189 | 147 |
| `tien-ich-vinhomes-smart-city.html` | 189 | 143 |

**Đã đúng sẵn — bỏ qua (17 trang):** `index.html` (159), `404.html` (152), `gui-thue/` (142),
`cam-nang-thue-nha.html` (154), `phi-dich-vu-vinhomes-smart-city.html` (147),
`cho-thue-can-ho-masteri-west-heights-smart-city.html` (148), `1pn-plus/` (146), `2pn/` (142),
`2pn-plus/` (144), `3pn/` (143), `sapphire/` (147), `masteri/` (147), `miami/` (145),
`sakura/` (142), `imperia/` (152), `lumiere/` (157), `canopy/` (146).

---

## 6. Task B — trang mới và các file liên quan

| File | Thay đổi |
|---|---|
| `bang-gia-thue-vinhomes-smart-city.html` | Tạo mới. Bảng giá tính 100% từ `data.json` phía client, không có số giá hard-code nào trong file. |
| `sitemap.xml` | Thêm 1 URL: `changefreq: weekly`, `priority: 0.9`. XML đã kiểm tra hợp lệ. |
| `index.html` | Thêm link trong khối mục lục "Cẩm nang thuê nhà" ở trang chủ |
| `sapphire/index.html` | Thêm link vào khối danh mục liên quan (`.lq`) — phân khu nhiều căn nhất |
| `masteri/index.html` | Thêm link vào khối `.lq` — phân khu nhiều căn thứ 2 |
| `miami/index.html` | Thêm link vào khối `.lq` — phân khu nhiều căn thứ 3 |

Đã kiểm tra thực tế bằng Chromium (1280px, 390px, 320px): bảng dựng đúng, cuộn ngang được
trong khung riêng, trang không tràn ngang ở cả 3 độ rộng, không có lỗi JavaScript,
21/21 link nội bộ trong trang mới đều trỏ tới file có thật.

---

## 7. Những điểm ghi nhận nhưng KHÔNG sửa

Các điểm dưới đây nằm ngoài phạm vi Task A và B, ghi lại để chủ repo quyết định:

1. **`chinh-sach-quyen-rieng-tu.html` chưa có trong `sitemap.xml`.** Trang tồn tại và index
   được nhưng không được khai báo. SPEC không yêu cầu nên không tự thêm.
2. **Đầu trang của các bài viết cũ bị vỡ trên điện thoại.** Trên màn hình ≤ 390px, tên
   thương hiệu ở thanh header bị 2 nút Hotline/Zalo chèn hết chỗ nên gãy thành 5 dòng, mỗi
   dòng một chữ, và đè lên nút Hotline. Lỗi này có ở `bang-gia-thue-smart-city-thang-7-2026.html`
   và các bài dùng chung mẫu CSS đó. **Trang mới của Task B đã xử lý** (dùng nhãn ngắn
   "Smart City" trên mobile, ẩn hẳn nhãn dưới 360px), nhưng các trang cũ **chưa sửa** vì
   ngoài phạm vi SPEC — nên xử lý trong một đợt riêng.
3. **Số căn và giá trong title/description các trang danh mục là số cứng.** Ví dụ
   "45 căn, từ 6 triệu" — `dong-bo-can.js` cập nhật được số căn trong nội dung trang nhưng
   không cập nhật thẻ `<title>` và `<meta description>`, nên các số này sẽ lệch dần theo
   thời gian. Đợt này giữ nguyên đúng số cũ (không tự đổi số), nhưng đây là món nợ kỹ thuật
   nên xử lý.
4. **`data.json` không có field timestamp.** Chi tiết cách xử lý ở phần dưới.

---

## 8. Cách kiểm tra lại

Các con số trong báo cáo này lấy từ script kiểm tra chạy trên toàn bộ file HTML của repo,
đo: số thẻ canonical + tiền tố URL, số thẻ `<h1>`, chuỗi cấp heading (bỏ qua nội dung trong
`<script>`/`<style>`), độ dài title sau khi giải mã HTML entity, độ dài meta description,
và parse từng khối JSON-LD. Chạy lại trước khi merge để xác nhận không có trang nào tụt lại.

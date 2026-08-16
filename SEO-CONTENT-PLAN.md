# SEO-CONTENT-PLAN — timthuesmartcity.com

Phase 2. Dựa trên `SEO-CONTENT-AUDIT.md`. Không đề xuất đổi URL/slug/canonical/
H1/title của bất kỳ trang nào đang index. Mọi hàng "URL đề xuất" là **URL mới**,
cộng thêm vào kiến trúc hiện có, không thay thế.

Phân loại:
- **P0** — rủi ro thấp, tác động cao, không tạo URL mới, không cần nội dung
  biên tập mới (chỉ dùng lại nội dung đã hiển thị sẵn). Triển khai ngay ở
  Phase 3.
- **P1** — tác động cao, cần nội dung biên tập thật (không tự bịa số liệu),
  hoặc tạo URL mới nhưng rủi ro thấp vì đúng mẫu đã có. Cần thêm input thủ
  công/xác nhận trước khi viết.
- **P2** — tác động vừa/thấp hơn, hoặc phụ thuộc dữ liệu chưa đủ ổn định
  (cluster 3 dưới ngưỡng), để sau.

---

## 1. P0 — triển khai trong đợt này

| Việc | URL bị ảnh hưởng | Thay đổi | Nguồn dữ liệu | Rủi ro |
|---|---|---|---|---|
| Thêm `FAQPage` JSON-LD | 25 trang danh mục (`/studio/`, `/1pn/`, …, `/s4-01-vinhomes-smart-city/`) | Thêm 1 phần tử `FAQPage` vào khối `@graph` đã có (`BreadcrumbList`+`ItemList`), sinh từ đúng 5 câu `<details><summary>` đang hiển thị trên trang | HTML hiện có của chính trang đó (không bịa câu hỏi mới) | Không đổi URL/canonical/H1/title/nội dung hiển thị. Chỉ thêm markup ẩn khớp nội dung đã có → đúng tinh thần Phần G |

Không có mục P0 nào khác đạt tiêu chí "không cần nội dung biên tập mới" —
mọi cơ hội content-depth khác (pillar, cẩm nang, combo) đều cần viết nội
dung thật, nên xếp P1/P2 theo đúng yêu cầu SPEC "không code toàn bộ ngay,
chỉ làm P0 rủi ro thấp trước".

---

## 2. P1 — cần nội dung biên tập, làm sau khi có xác nhận

### 2.1 Pillar phân khu còn thiếu (Cluster 2)

Mẫu đã có 3/8 phân khu (Imperia, Masteri, Lumière — file `cho-thue-can-ho-*.html`
/ `thue-can-ho-lumiere-evergreen.html`). Đề xuất làm nốt 5 phân khu còn lại,
ưu tiên theo số căn hiện có (phân khu nhiều căn = search volume/giá trị
thương mại cao hơn):

| Phân khu | URL đề xuất | Số căn hiện tại | Ưu tiên |
|---|---|---|---|
| Sapphire | `cho-thue-can-ho-sapphire-smart-city.html` | 66 | 1 — nhiều căn nhất, chưa có pillar |
| Sakura | `cho-thue-can-ho-sakura-smart-city.html` | 27 | 2 |
| Miami | `cho-thue-can-ho-the-miami-smart-city.html` | 27 | 2 |
| Canopy | `cho-thue-can-ho-canopy-residences-smart-city.html` | 22 | 3 |
| Tonkin | `cho-thue-can-ho-the-tonkin-smart-city.html` | 8 | 4 — ít căn nhất, làm sau cùng |

Mỗi bài theo đúng khung nội dung 3 bài đã có (vị trí, đặc điểm, tiện ích,
chất lượng căn hộ, khoảng giá, loại căn phổ biến, ưu điểm, hạn chế, đối
tượng phù hợp, FAQ, quỹ căn hiện tại) — **không copy-paste đổi tên phân khu**,
vì mỗi phân khu có đặc điểm thật khác nhau (năm bàn giao, vị trí trong khu,
loại hình tòa) cần biên tập viên xác nhận, không tự suy diễn.

Internal link 2 chiều bắt buộc: pillar mới ↔ trang danh mục cùng phân khu
(`/sapphire/` …) ↔ trang chủ ↔ bài so sánh phân khu.

### 2.2 Bài cẩm nang còn thiếu (Content Hub)

Giữ nguyên `cam-nang-thue-nha.html` làm mục lục (đã index tốt, không đổi
URL). Bổ sung các bài SPEC liệt kê mà hiện chưa có bài riêng:

| Chủ đề | URL đề xuất | Search intent | Nguồn dữ liệu |
|---|---|---|---|
| Giá thuê 1PN Smart City | `gia-thue-1pn-smart-city.html` | Thông tin + thương mại | `data.json` lọc `loai=1 Ngủ +` (mẫu y hệt `gia-thue-studio-smart-city.html`) |
| Giá thuê 2PN Smart City | `gia-thue-2pn-smart-city.html` | Thông tin + thương mại | `data.json` lọc `loai=2 Ngủ` |
| Giá thuê 3PN Smart City | `gia-thue-3pn-smart-city.html` | Thông tin + thương mại | `data.json` lọc `loai=3 Ngủ` |
| Tiền cọc thuê nhà Smart City thường bao nhiêu? | `tien-coc-thue-nha-smart-city.html` | Informational, chưa có bài riêng (mới có 1 câu FAQ rải rác) | Cần biên tập xác nhận thông lệ thật (đã có nhắc "cọc 1 tháng" trong FAQ các trang — cần gộp + mở rộng, không bịa số mới) |
| Checklist nhận bàn giao căn thuê | `checklist-nhan-ban-giao-can-thue-smart-city.html` | Informational, quy trình | Cần biên tập mới hoàn toàn |
| Điều khoản cần chú ý trong hợp đồng thuê | `dieu-khoan-hop-dong-thue-nha-smart-city.html` | Informational | Cần biên tập mới hoàn toàn |
| Thuê trực tiếp chủ nhà vs qua môi giới | `thue-truc-tiep-vs-qua-moi-gioi-smart-city.html` | Informational, cân nhắc | Cần biên tập mới hoàn toàn |
| Đi lại từ Smart City vào trung tâm & VinBus | `di-lai-vinbus-smart-city.html` | Informational | Một phần đã có trong `tien-ich-vinhomes-smart-city.html` — tách thành bài chuyên sâu hoặc giữ gộp (cần quyết định, không tách nếu nội dung gốc chưa đủ dày) |

### 2.3 Bài so sánh (Comparison)

| Cặp so sánh | URL đề xuất | Ghi chú |
|---|---|---|
| Masteri vs Sapphire | `so-sanh-masteri-vs-sapphire-smart-city.html` | 2 phân khu nhiều căn nhất — ưu tiên 1 |
| Lumière vs Masteri | `so-sanh-lumiere-vs-masteri-smart-city.html` | Cả 2 đã có pillar riêng, dễ tổng hợp số liệu |
| Canopy vs Masteri | `so-sanh-canopy-vs-masteri-smart-city.html` | |
| Studio vs 1PN | `so-sanh-studio-vs-1pn-smart-city.html` | Cả 2 loại đã có trang danh mục đầy đủ số liệu |
| 1PN+ vs 2PN | `so-sanh-1pn-plus-vs-2pn-smart-city.html` | |
| Full nội thất vs nội thất cơ bản | `so-sanh-noi-that-day-du-vs-co-ban-smart-city.html` | Phụ thuộc mục 2.4 (cluster 5) làm trước |

Lưu ý: `so-sanh-gia-thue-cac-phan-khu-smart-city.html` (đã có, tổng hợp tất
cả phân khu) **không bị thay thế** bởi các bài so sánh cặp — hai loại nội
dung phục vụ search intent khác nhau (tổng quan vs quyết định giữa 2 lựa
chọn cụ thể), giữ cả hai.

### 2.4 Cluster 5 — nội thất (mở rộng)

Dữ liệu đủ ở cấp toàn site (mục 6.2 audit): 30 căn "Đồ Cơ bản", 48 căn
"Nhà Nguyên Bản". Đề xuất 2 trang hub mới, theo đúng mẫu 4 trang `*-full-do/`
đã có (dựng bằng `dong-bo-can.js`/script, không phải bài viết tay):

| URL đề xuất | Bộ lọc | Số căn hiện tại |
|---|---|---|
| `/noi-that-co-ban/` | `{"noiThat": "Đồ Cơ bản"}` | 30 |
| `/khong-do/` | `{"noiThat": "Nhà Nguyên Bản"}` | 48 |

Đây là 2 trang danh mục kỹ thuật giống 25 trang hiện có — tạo theo đúng quy
trình đã ghi trong `README.md` mục "Thêm một trang danh mục mới" (khai
`#bo-loc-trang`, không cần đăng ký thêm nơi khác). **Không tách theo từng
loại căn** (vd "studio đồ cơ bản") vì audit đã chỉ ra dưới ngưỡng dữ liệu ổn
định — để P2.

---

## 3. P2 — Cluster 3 (loại × phân khu) và các hạng mục phụ thuộc dữ liệu

### 3.1 Ngưỡng dữ liệu tối thiểu đề xuất

**≥ 10 căn đang hiển thị tại thời điểm tạo trang**, kiểm tra lại tự động
mỗi lần `dung-lai-trang-danh-muc.py` chạy (giống cơ chế 25 trang hiện có).
Lý do chọn 10:
- Dưới 10 căn, trang gần như chắc chắn sẽ có lúc rơi về dưới 5 căn (data
  đổi theo giờ) — trải nghiệm người dùng lẫn tín hiệu content-depth cho
  Google đều yếu vào những lúc đó.
- Trên 10 căn vẫn đủ để bảng giá theo tòa/nội thất trong bài có ý nghĩa
  thống kê tối thiểu (không phải 2-3 dòng).

Theo dữ liệu hiện tại (mục 6.1 audit), **9 tổ hợp đạt ngưỡng**:

| Tổ hợp | Số căn | URL đề xuất |
|---|---|---|
| Sapphire × 2 Ngủ | 17 | `/sapphire/2pn/` |
| Sapphire × 2 Ngủ + | 15 | `/sapphire/2pn-plus/` |
| Masteri × 1 Ngủ + | 14 | `/masteri/1pn-plus/` |
| Masteri × Studio | 13 | `/masteri/studio/` |
| Miami × 2 Ngủ | 13 | `/miami/2pn/` |
| Sapphire × 1 Ngủ + | 13 | `/sapphire/1pn-plus/` |
| Sapphire × Studio | 11 | `/sapphire/studio/` |
| Lumiere × 2 Ngủ | 11 | `/lumiere/2pn/` |
| Sapphire × 3 Ngủ | 10 | `/sapphire/3pn/` |

38 tổ hợp còn lại **không tạo URL indexable**. Theo đúng yêu cầu Phần A/D
của SPEC, xử lý bằng một trong hai cách (quyết định kỹ thuật cụ thể để lúc
triển khai, không quyết ở audit vì ảnh hưởng cấu trúc site):
- Không tạo file/route cho tổ hợp dưới ngưỡng (đơn giản nhất, đúng tinh
  thần "không tạo URL rác" — khuyến nghị chọn cách này), **hoặc**
- Nếu vì lý do UX cần có trang, thêm `noindex` + canonical trỏ về trang cha
  gần nhất (trang phân khu hoặc trang loại căn, tuỳ trang nào có nhiều nội
  dung hơn).

### 3.2 Rủi ro biến động

9 tổ hợp trên có thể tụt dưới 10 căn theo thời gian (data đổi theo Apps
Script). Cần logic tự động: nếu một tổ hợp đã lên trang mà tụt dưới ngưỡng
(vd còn 5 căn), **không tự xoá trang** (phá SEO đã tích luỹ) mà giữ trang,
hiển thị đúng số căn thật + có thể thêm câu gợi ý xem trang cha rộng hơn.
Chỉ NGỪNG tạo trang mới cho tổ hợp chưa từng lên, không hồi tố trang đã có.

### 3.3 Internal linking cho Cluster 3 (khi triển khai)

```
Trang chủ
  → /masteri/                      (phân khu)
      → /masteri/studio/           (loại × phân khu, P2)
          → bảng giá Masteri (P1, mục 2.2 nếu làm riêng)
          → pillar Masteri (đã có: cho-thue-can-ho-masteri-west-heights...)
      ← /studio/                   (loại căn, link chiều ngược)
```

Mỗi trang combo P2 phải link ngược về CẢ HAI trang cha (loại căn + phân
khu) — không chỉ một chiều — đúng yêu cầu Phần F.

---

## 4. Sitemap — quy tắc cập nhật

- P0 (FAQPage schema): **không đổi sitemap** — không có URL mới.
- P1 (pillar/cẩm nang/so sánh/cluster 5 mới): thêm vào `sitemap.xml` ngay
  khi trang được publish, `changefreq` theo đúng quy ước đã có (`monthly`
  cho pillar phân khu, `daily` cho trang danh mục dựng từ data, `daily`
  cho bài giá/so sánh có bảng động).
- P2 (combo dưới ngưỡng): **không đưa vào sitemap** dù có tạo trang
  `noindex` hay không — đúng Phần H.
- Không bao giờ thêm URL có query string hay trang search-result.

## 5. Schema — quy tắc áp dụng cho P1/P2

- Pillar phân khu mới: `Article` (đủ 5 field, theo mẫu 3 pillar đã có) +
  `BreadcrumbList` + `FAQPage` (nếu bài có khối FAQ thật).
- Trang cẩm nang mới: `Article` + `BreadcrumbList`.
- Trang combo Cluster 3 (nếu qua ngưỡng): `BreadcrumbList` + `ItemList` +
  `FAQPage`, đúng mẫu 25 trang danh mục hiện có — tái dùng
  `dung-lai-trang-danh-muc.py`/`sinh-trang-toa.py`, không viết logic mới.
- Không thêm `Review`/`AggregateRating` ở bất kỳ đâu — site không có cơ chế
  thu thập đánh giá thật.

## 6. Việc KHÔNG làm trong bất kỳ phase nào (nhắc lại nguyên tắc bắt buộc)

- Không đổi URL/slug của 44 trang hiện có.
- Không đổi canonical, H1, title của trang đang index.
- Không xoá `bang-gia-thue-smart-city-thang-7-2026.html` (trang chuyển
  hướng giả) dù không còn giá trị SEO riêng — xoá sẽ làm mất tín hiệu
  chuyển hướng cho các link cũ đã chia sẻ ra ngoài.
- Không đổi cấu trúc điều hướng chính (`header nav`, footer phân khu).
- Không tạo redirect hàng loạt.
- Không tạo trang combo Cluster 3 dưới ngưỡng 10 căn.

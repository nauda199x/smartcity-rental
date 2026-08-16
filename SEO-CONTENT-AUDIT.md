# SEO-CONTENT-AUDIT — timthuesmartcity.com

Audit Phase 1 theo yêu cầu "Nâng cấp SEO Content Architecture". Đọc toàn bộ
repo (44 file HTML, `data.json`, `dong-bo-can.js`, 10 script trong `scripts/`,
2 GitHub Actions workflow) trước khi đề xuất bất kỳ thay đổi nào. Không file
nào bị sửa trong Phase 1.

Ngày audit: 16/08/2026. Baseline dùng để so sánh trước/sau nằm ở
`scripts/kiem-tra-seo-snapshot.py` (đã chạy, lưu tại
`/tmp/.../scratchpad/BEFORE-snapshot.json`) và `scripts/kiem-tra-lien-ket.py`.

---

## 1. Hiện trạng kiến trúc — tóm tắt cho người chưa đọc code

Đây **không phải** một site tổng hợp bất động sản. Đây là site HTML tĩnh,
không framework, không build step, chạy trên GitHub Pages, chuyên biệt 100%
cho thị trường cho thuê **một khu đô thị duy nhất** (Vinhomes Smart City).
Điều này tự nó đã là một tín hiệu topical authority tốt — không cần "giả vờ"
chuyên sâu, kiến trúc site sẵn đã đúng hướng.

Luồng dữ liệu (xem thêm `README.md`):

```
Google Sheets (chủ nhà nhập căn)
  → Apps Script đẩy data.json vào repo (~30 phút/lần)
  → 3 lần/ngày, GitHub Actions chạy:
      sinh-trang-toa.py         → dựng lại trang tòa S4.01
      dung-lai-trang-danh-muc.py → dựng lại LƯỚI CĂN TĨNH của 25 trang danh mục
      cap-nhat-so-can.mjs       → ghi số căn/giá vào <title>/meta description
      cap-nhat-sitemap.mjs      → cập nhật <lastmod>
  → dong-bo-can.js (chạy trong trình duyệt) dựng lại lưới cho người dùng thật,
    dùng ĐÚNG logic lọc/sắp xếp mà bản Python đã dựng tĩnh
```

**Phát hiện quan trọng nhất của audit này:** phần lớn "rủi ro indexability"
mà SPEC lo ngại (Phần C — Googlebot chỉ thấy "Đang tải dữ liệu...") **đã được
xử lý từ trước**, không phải việc cần làm lại. Chi tiết ở mục 4.

---

## 2. URL Inventory đầy đủ

### 2.1 Trang chủ (1)

| URL | Title | Canonical | H1 | Robots | Schema |
|---|---|---|---|---|---|
| `/` | Cho thuê căn hộ chung cư Vinhomes Smart City tháng 08/2026 (60 ký tự) | đúng, non-www, https | 1 | index | `RealEstateAgent` + `FAQPage` (3 khối JSON-LD) |

### 2.2 Trang danh mục — 25 trang, tự dựng từ `data.json`

Toàn bộ có: canonical đúng, đúng 1 H1, `BreadcrumbList` + `ItemList` hợp lệ,
lưới căn TĨNH (không phụ thuộc JS), khối biên tập (`section.bai`), FAQ dạng
`<details>`, khối "Danh mục liên quan" + "Đọc thêm trước khi thuê" (internal
link), bảng giá theo phân khu/loại căn tính động từ đúng tập căn đang hiển thị.

**Cluster loại căn (6):** `/studio/` (46 căn) · `/1pn/` (9 căn) ·
`/1pn-plus/` (41 căn) · `/2pn/` (73 căn) · `/2pn-plus/` (43 căn) · `/3pn/` (28 căn)

**Cluster phân khu (8):** `/sapphire/` (66 căn) · `/sakura/` (27 căn) ·
`/masteri/` (45 căn) · `/miami/` (27 căn) · `/imperia/` (18 căn) ·
`/lumiere/` (25 căn) · `/canopy/` (22 căn) · `/tonkin/` (8 căn)

**Cluster giá (7):** `/studio-duoi-7-trieu/` · `/studio-7-10-trieu/` ·
`/1pn-plus-duoi-10-trieu/` · `/2pn-duoi-10-trieu/` · `/2pn-10-12-trieu/` ·
`/2pn-plus-12-15-trieu/` · `/3pn-12-15-trieu/`

**Cluster nội thất (4):** `/studio-full-do/` · `/1pn-plus-full-do/` ·
`/2pn-full-do/` · `/3pn-full-do/`

**Trang tòa (1, cơ chế riêng):** `/s4-01-vinhomes-smart-city/`

### 2.3 Bài cẩm nang / pillar page — 13 trang (file phẳng, không nằm dưới `/cam-nang/`)

| File | Chủ đề | Schema Article đủ 5 field |
|---|---|---|
| `cam-nang-thue-nha.html` | Hub cẩm nang (mục lục) | có |
| `bang-gia-thue-vinhomes-smart-city.html` | Bảng giá toàn site, tính động | có |
| `gia-thue-studio-smart-city.html` | Giá thuê Studio | có |
| `kinh-nghiem-thue-chung-cu-smart-city.html` | Kinh nghiệm thuê | có |
| `thu-tuc-thue-nha-vinhomes-smart-city.html` | Thủ tục thuê | có |
| `phi-dich-vu-vinhomes-smart-city.html` | Phí dịch vụ | có |
| `luu-y-do-xe-thu-cung-phi-dich-vu-smart-city.html` | Đỗ xe/thú cưng/phí | có |
| `tien-ich-vinhomes-smart-city.html` | Tiện ích khu đô thị | có |
| `so-sanh-gia-thue-cac-phan-khu-smart-city.html` | So sánh giá phân khu | có |
| `thue-can-ho-gan-vinschool-smart-city.html` | Gần Vinschool (đối tượng gia đình) | có |
| `cho-thue-can-ho-imperia-smart-city.html` | Pillar phân khu Imperia | có |
| `cho-thue-can-ho-masteri-west-heights-smart-city.html` | Pillar phân khu Masteri | có |
| `thue-can-ho-lumiere-evergreen.html` | Pillar phân khu Lumière | có |

### 2.4 Trang khác (2 indexable, 3 noindex)

| URL | Robots | Ghi chú |
|---|---|---|
| `/gui-thue/` | index | Landlord gửi căn — không phải nội dung SEO thuê, không đụng |
| `chinh-sach-quyen-rieng-tu.html` | **noindex, follow** | Đúng, không cần trong sitemap |
| `404.html` | **noindex, follow** | Đúng |
| `bang-gia-thue-smart-city-thang-7-2026.html` | **noindex, follow** + canonical trỏ URL mới + meta refresh | Trang chuyển hướng "giả 301" — GitHub Pages không hỗ trợ 301 thật, đây là giải pháp khả thi nhất, **giữ nguyên, không xóa** |

### 2.5 Sitemap

41 URL trong `sitemap.xml`, khớp đúng tập trang nên index (1 home + 25 danh
mục + 13 guide + `/gui-thue/`, trừ đúng 3 trang noindex ở trên). Không có
URL filter/query-param/thin page nào trong sitemap. `sitemap-images.xml`
144KB, khai ảnh riêng cho các trang có ảnh thật. `robots.txt` chỉ có
`Allow: /` + 2 dòng Sitemap — sạch, không chặn nhầm.

**Kiểm tra kỹ thuật (chạy trên toàn bộ 44 file):**
- Canonical: 44/44 file có đúng 1 thẻ, non-www, https, đúng domain.
- H1: 44/44 file có đúng 1 thẻ.
- Title: 39/39 trang public trong khoảng ≤ 60 ký tự (không trùng nhau).
- Meta description: 39/39 trang trong khoảng 138–162 ký tự.
- hreflang: không có (site đơn ngữ — không phải lỗi, không cần thêm).
- Internal link: `kiem-tra-lien-ket.py` PASS toàn bộ ngưỡng đặt sẵn cho các
  bài cẩm nang, không có link nội bộ trỏ tới trang không tồn tại.

**Kết luận mục 2:** phần kỹ thuật on-page (title/meta/canonical/H1/schema
hợp lệ/robots/sitemap sạch) đã ở trạng thái tốt nhờ một đợt audit trước đó
(`SEO-AUDIT.md`, tháng 7/2026). Đây **không phải** ưu tiên của đợt này.

---

## 3. Content Depth — đánh giá theo đúng khung SPEC yêu cầu

Đối chiếu nội dung thật của `/studio/`, `/sapphire/`, `/masteri/` (đại diện
2 cluster lớn nhất) với danh sách SPEC yêu cầu cho mỗi trang loại căn/phân khu:

| Yêu cầu SPEC | Có sẵn? | Ghi chú |
|---|---|---|
| Khoảng giá thuê | ✅ | `.sl` (4 ô thống kê) + bảng giá theo phân khu/loại |
| Diện tích phổ biến | ✅ | Trong `.sl` và đoạn mô tả |
| Phù hợp với ai | ✅ | H2 riêng "…hợp với ai?" |
| Ưu/nhược điểm | ⚠️ một phần | Có đoạn "Vài điều nên biết…" nói thẳng nhược điểm (VD: Studio — thiếu hầm xe, hàng quán tạm), nhưng không tách rõ thành 2 cột ưu/nhược |
| Nội thất | ✅ | Badge nội thất trên từng thẻ căn + nhắc trong đoạn mô tả |
| Phân khu có nhiều căn | ✅ | Bảng giá theo phân khu, sắp theo số căn giảm dần |
| Kinh nghiệm chọn | ✅ | Đoạn "Vài điều nên biết trước khi thuê" |
| FAQ riêng | ⚠️ | Có khối FAQ (5 câu `<details>`) trên mọi trang, **nhưng đối chiếu lại `studio/`, `2pn-10-12-trieu/`, `canopy/`: cả 5 câu hỏi và câu trả lời trùng 100% từng chữ trên toàn bộ 25 trang** — là boilerplate dùng chung, không phải nội dung riêng theo trang |
| Danh sách căn đang có | ✅ | Lưới căn tĩnh, đúng dữ liệu, ảnh thật khi có |

**Kết luận: Cluster 1 (loại căn) và phần lớn Cluster 2 (phân khu) đã đạt gần
hết yêu cầu content depth của SPEC.** Đây là phát hiện quan trọng thứ hai —
site không "mỏng", một đợt code trước (không rõ tác giả) đã làm đúng hướng.

### 3.1 Khoảng trống thật (không phải "chưa làm gì" mà là "làm chưa đều")

1. **FAQ của 25 trang danh mục là boilerplate dùng chung 100%, không riêng
   theo trang.** Cả 5 câu hỏi lẫn 5 câu trả lời trùng khớp từng chữ giữa
   `/studio/`, `/2pn-10-12-trieu/`, `/canopy/` (đã đối chiếu trực tiếp). Nội
   dung vẫn đúng/hữu ích (cọc, phí dịch vụ, thú cưng, mùa thấp điểm, xem nhà
   trực tiếp) và không sai sự thật, nhưng không tận dụng được đặc thù riêng
   của từng trang (VD trang phân khu có thể hỏi về năm bàn giao, trang loại
   căn có thể hỏi về diện tích/số người ở phù hợp). Xếp P1: viết lại FAQ theo
   cụm (loại căn / phân khu / khoảng giá / nội thất có thể dùng bộ câu hỏi
   khác nhau theo cụm, thay vì 1 bộ chung cho cả 25 trang).
2. **Bất đối xứng phân khu — 3/8 có pillar riêng, 5/8 thì không.**
   Sapphire, Sakura, Miami, Canopy, Tonkin chỉ có trang danh mục (ngắn hơn,
   thiên về listing) mà không có bài pillar sâu như Imperia/Masteri/Lumière
   (`cho-thue-can-ho-*.html`, `thue-can-ho-lumiere-evergreen.html`). Sapphire
   là phân khu **nhiều căn nhất** (66 căn) nhưng lại chưa có pillar riêng —
   đây là khoảng trống content depth lớn nhất của toàn site.
2. **Ưu/nhược điểm chưa tách khối rõ ràng**, đang lồng trong văn xuôi. Dễ bổ
   sung mà không đổi cấu trúc trang (chỉ thêm 1 khối trong `section.bai`
   đã có sẵn).
3. **Cluster 5 (nội thất) chỉ có 1/3 nhánh.** Có `*-full-do/` cho 4 loại
   căn. Không có landing page cho "nội thất cơ bản" hay "không đồ/nguyên
   bản" — dù dữ liệu thật có đủ: 30 căn "Đồ Cơ bản", 48 căn "Nhà Nguyên Bản"
   toàn site (xem mục 6.2).
4. **Cluster 3 (loại × phân khu) chưa tồn tại** — đúng như SPEC dự đoán, xem
   phân tích ngưỡng dữ liệu ở mục 6.1.
5. **Content Hub `/cam-nang/` chưa tồn tại như một thư mục URL riêng.**
   Hiện tại là 1 file phẳng `cam-nang-thue-nha.html` đóng vai trò mục lục,
   trỏ tới 9 bài cẩm nang cũng nằm phẳng ở gốc domain. Về nội dung, khá nhiều
   chủ đề SPEC liệt kê **đã có bài** (giá theo loại căn — studio; phí dịch
   vụ; điện nước/gửi xe — gộp trong 1 bài; thủ tục thuê; kinh nghiệm thuê;
   tiện ích; trường học; so sánh phân khu). Khoảng trống thật:
   - Giá thuê riêng cho 1PN/2PN/3PN (hiện chỉ Studio có bài riêng, các loại
     khác dồn vào bảng giá tổng `bang-gia-thue-vinhomes-smart-city.html`).
   - Tiền cọc / điều khoản hợp đồng / checklist bàn giao — mới có rải rác
     trong FAQ, chưa có bài riêng.
   - Thuê trực tiếp chủ nhà vs qua môi giới — chưa có.
   - So sánh cặp phân khu cụ thể (Masteri vs Sapphire…) — mới có 1 bài so
     sánh tổng hợp tất cả phân khu, chưa có bài 1-đối-1.
   - So sánh loại căn (Studio vs 1PN, 1PN+ vs 2PN, full đồ vs cơ bản) — chưa có.
   - Đi lại/VinBus — mới nhắc trong `tien-ich...html`, chưa có bài riêng.
6. **Không có nội dung nhồi từ khóa vô nghĩa.** Kiểm tra ngẫu nhiên 6 trang:
   không thấy mẫu câu kiểu "Bạn đang tìm căn hộ Smart City?..." mà SPEC cảnh
   báo. Văn phong nhất quán, có chi tiết thật (vd: "cả khu chỉ có một tầng
   hầm", "chạy sang khu Geleximco ngay cạnh") — đúng tinh thần Phần I.

---

## 4. Rendering & Indexability (Phần C của SPEC)

**Đây là phần SPEC coi là quan trọng nhất, và đây là tin tốt nhất của audit
này: đã được giải quyết, không phải xây từ đầu.**

`dung-lai-trang-danh-muc.py` (chạy 3 lần/ngày qua GitHub Actions, xem
mục 1) dựng lại **file HTML tĩnh trên đĩa** — không phải chỉ dựng trong
trình duyệt — cho cả 25 trang danh mục, đọc trực tiếp từ `data.json`. Đã
kiểm tra thực tế `curl`-tương đương (đọc thẳng file nguồn, không chạy JS):
Googlebot tải HTML thô của `/studio/` sẽ thấy ngay, không cần đợi JS:

- Tiêu đề + đoạn mô tả riêng của Studio ("Studio Vinhomes Smart City hợp
  với ai?")
- Số căn hiện có (46), giá thấp nhất (5,5 triệu), diện tích (25–35m²), số
  phân khu (8) — 4 số này **không hard-code**, tính lại mỗi lần script chạy
- Bảng giá theo phân khu, tính từ đúng tập căn trong lưới
- 46/46 thẻ căn thật: mã căn, tòa, diện tích, giá, tình trạng, nội thất,
  ảnh thật (hoặc khối "chưa có ảnh, nhắn Zalo" nếu thiếu — không giả ảnh)
- 5 câu FAQ
- Internal link sang danh mục liên quan + bài cẩm nang

`dong-bo-can.js` sau đó dựng lại **đúng cùng nội dung đó** trong trình
duyệt cho người dùng thật (không phải Googlebot mới thấy một bản, người
dùng thấy một bản khác) — hai bản dùng chung logic lọc/sắp xếp, đã được
đối chiếu từng dòng khi viết `dung-lai-trang-danh-muc.py` (xem docstring
script, phần "PHẦN 1").

### 4.1 Vẫn còn 2 khoảng hở nhỏ (không phải rủi ro, là cơ hội tối ưu thêm)

1. **`<title>` và `<meta description>` không tự cập nhật theo thời gian
   thực** — chỉ đúng tại thời điểm `cap-nhat-so-can.mjs` chạy (3 lần/ngày,
   01h/09h/17h UTC). Giữa hai lần chạy, số căn trong `<title>` có thể lệch
   vài đơn vị so với lưới thật bên dưới. Đây là độ trễ chấp nhận được (đã
   được README ghi nhận là hạn chế đã biết của GitHub Pages, không có server
   để làm real-time), **không phải lỗi cần sửa gấp**.
2. **`data.json` không có field timestamp cập nhật** (SEO-AUDIT.md mục 7.4
   đã ghi nhận từ trước) — ngày "Cập nhật DD/MM/YYYY" hiển thị trên trang
   lấy từ ngày commit git của `data.json`, không phải field trong chính
   data. Hoạt động đúng nhưng hơi gián tiếp.

### 4.2 Trang KHÔNG có cơ chế dựng tĩnh này

`index.html` (trang chủ) — lưới căn ở trang chủ vẫn dựa vào
`dong-bo-can.js` chạy trong trình duyệt để hiển thị lưới đầy đủ (có bộ lọc
tương tác). Đây là hành vi hợp lý cho trang chủ (là công cụ tìm kiếm/lọc,
không phải landing page 1 chủ đề), nhưng có nghĩa Googlebot đọc HTML thô của
`/` sẽ **không** thấy lưới căn đầy đủ — chỉp thấy phần nội dung tĩnh (H1,
đoạn mở đầu, schema `RealEstateAgent`/`FAQPage`, mục lục cẩm nang, footer
link phân khu). Không phải vấn đề cấp thiết vì trang chủ không cạnh tranh
từ khóa dài như `/studio/`, nhưng ghi nhận để không ai nhầm là "toàn site
đã SSR".

---

## 5. Schema hiện tại

| Loại schema | Dùng ở đâu | Đúng với nội dung hiển thị? |
|---|---|---|
| `RealEstateAgent` | `index.html` | Có — khớp thông tin liên hệ thật, `sameAs` khớp đúng mạng xã hội thật ở footer (đã có comment cảnh báo giữ đồng bộ) |
| `BreadcrumbList` | 25 trang danh mục + tất cả bài guide | Có |
| `ItemList` | 25 trang danh mục | Có — số lượng và tên khớp đúng lưới căn tĩnh |
| `Article` | 13 bài cẩm nang, đủ 5 field bắt buộc (headline/datePublished/dateModified/author/publisher) | Có |
| `FAQPage` | `index.html`, `cam-nang-thue-nha.html`, `bang-gia-thue-vinhomes-smart-city.html`, 3 bài pillar phân khu, `thu-tuc-thue-nha...html`, `thue-can-ho-gan-vinschool...html` (theo snapshot: 8 file) | Có |
| **`FAQPage` — THIẾU** | **25 trang danh mục** | **Có nội dung FAQ hiển thị thật (`<details><summary>`, 5 câu/trang) nhưng KHÔNG có schema tương ứng.** Đây là khoảng trống schema rõ ràng nhất tìm được — đúng tinh thần Phần G ("chỉ triển khai schema phù hợp nội dung thực sự xuất hiện"): nội dung đã có sẵn, chỉ thiếu đánh dấu. |

Không tìm thấy review/rating giả, không có schema mô tả nội dung không hiển
thị trên trang.

**Lưu ý khi thêm `FAQPage` cho 25 trang (mục 3.1.1):** vì 5 câu hỏi/trả lời
là boilerplate giống nhau trên toàn bộ 25 trang, schema `FAQPage` sinh ra
cũng sẽ giống nhau về nội dung giữa các trang — đây là hệ quả trung thực
của việc "chỉ đánh dấu đúng nội dung đã hiển thị", không phải lỗi của việc
thêm schema. Google không cấm FAQPage giống nhau giữa các trang miễn khớp
nội dung thật hiển thị trên đúng trang đó; rich-result FAQ trên kết quả tìm
kiếm cũng đã bị Google giới hạn phần lớn cho site chính phủ/y tế từ 2023 nên
lợi ích chính của việc thêm ở đây là dữ liệu có cấu trúc chuẩn cho AI
Overview/trợ lý tìm kiếm đọc hiểu trang, không phải rich snippet cổ điển.
Giá trị lâu dài hơn vẫn là việc viết FAQ riêng theo từng trang (P1, mục 3.1
điểm 1).

---

## 6. Dữ liệu định lượng phục vụ Phase 2 (Architecture)

Tính trực tiếp từ 238 căn đang "Hiển thị trên Web" = Có trong `data.json`
(dùng lại đúng logic lọc của `dong-bo-can.js`/`sinh-trang-toa.py`, không tự
suy diễn).

### 6.1 Ma trận Loại căn × Phân khu (cho Cluster 3)

Chỉ liệt kê tổ hợp có ≥ 8 căn (48 tổ hợp lý thuyết, phần lớn dưới 5 căn):

| Phân khu × Loại | Số căn |
|---|---|
| Sapphire × 2 Ngủ | 17 |
| Sapphire × 2 Ngủ + | 15 |
| Masteri × 1 Ngủ + | 14 |
| Masteri × Studio | 13 |
| Miami × 2 Ngủ | 13 |
| Sapphire × 1 Ngủ + | 13 |
| Sapphire × Studio | 11 |
| Lumiere × 2 Ngủ | 11 |
| Sapphire × 3 Ngủ | 10 |
| Sakura × 2 Ngủ | 9 |
| Masteri × 2 Ngủ + | 9 |
| Sakura × Studio | 8 |
| Canopy × 2 Ngủ | 8 |

38/48 tổ hợp còn lại có dưới 8 căn, phần lớn dưới 4 — đúng như SPEC cảnh
báo, **tuyệt đại đa số tổ hợp loại×phân khu KHÔNG đủ dữ liệu để làm landing
page riêng.** Đề xuất ngưỡng cụ thể ở `SEO-CONTENT-PLAN.md`.

### 6.2 Nội thất (cho Cluster 5)

| Nội thất | Số căn (toàn site) |
|---|---|
| Full nội thất | 160 |
| Nhà Nguyên Bản (= không đồ) | 48 |
| Đồ Cơ bản | 30 |

Đủ dữ liệu để làm 2 trang hub theo nội thất ở cấp toàn site ("nội thất cơ
bản", "không đồ/nguyên bản"), nhưng **không đủ để tách riêng theo từng loại
căn** (vd: "2PN đồ cơ bản" có thể chỉ còn dưới 10 căn) — cần tính lại tại
thời điểm triển khai.

### 6.3 Loại căn (cho Cluster 1, đối chiếu số trên trang thật)

| Loại | Số căn |
|---|---|
| 2 Ngủ | 73 |
| Studio | 44 |
| 2 Ngủ + | 43 |
| 1 Ngủ + | 41 |
| 3 Ngủ | 28 |
| 1 Ngủ | 9 |

`/1pn/` (1 Ngủ, không "+") chỉ có 9 căn — mỏng nhất trong cluster 1 nhưng
**đã tồn tại và đã index**, nên theo nguyên tắc "không xóa trang SEO hiện
tại", giữ nguyên, không gộp/xóa dù mỏng.

---

## 7. Rủi ro nếu làm sai (để Phase 2/3 tránh)

1. **5 phân khu chưa có pillar (Sapphire, Sakura, Miami, Canopy, Tonkin) —
   nếu viết pillar mới, PHẢI đặt URL khác với trang danh mục hiện có**
   (vd. theo mẫu 3 pillar đã có: `cho-thue-can-ho-sapphire-smart-city.html`),
   tuyệt đối không đổi URL/H1/canonical của `/sapphire/` đang index.
2. **Cluster 3 (loại×phân khu) là rủi ro cao nhất nếu làm ẩu** — SPEC đã
   cảnh báo đúng: 38/48 tổ hợp quá mỏng. Nếu tạo URL indexable cho các tổ
   hợp đó sẽ tạo hàng chục trang gần như trùng nội dung (thin/duplicate),
   ngược hoàn toàn mục tiêu topical authority. Bắt buộc phải có ngưỡng dữ
   liệu tối thiểu + noindex/không tạo URL cho phần dưới ngưỡng (Phần A yêu
   cầu rõ).
3. **Trang danh mục dựng lại 3 lần/ngày qua script** — bất kỳ thay đổi thủ
   công nào vào 5 khối mà `dung-lai-trang-danh-muc.py` quản lý (`section.luoi`,
   `h2.tieu-de-luoi`, `p.tt` đầu tiên, `div.sl`, `table.bang`) sẽ **bị ghi
   đè ở lần chạy tiếp theo** nếu không sửa cùng lúc trong chính script đó.
   Muốn thêm nội dung mới (vd khối ưu/nhược điểm) phải thêm NGOÀI 5 khối này
   hoặc dạy script mới cách bảo toàn khối đó.
4. **`assets/v3.css` dùng chung toàn site** — README đã cảnh báo, CSS
   desktop mới phải nằm trong `@media (min-width:1024px)`. Bất kỳ thay đổi
   CSS nào cho trang mới đều có khả năng ảnh hưởng toàn bộ 44 trang khác.
5. **Không đổi khối JSON-LD/GA4 trong `dong-bo-can.js`** — README ghi rõ
   đây là hai khối tuyệt đối không đụng.
6. **`data.json` chỉ đọc, không bao giờ ghi** — Apps Script ghi đè ~30
   phút/lần, mọi sửa tay sẽ mất ở lần đẩy kế tiếp.

---

## 8. Cơ hội ưu tiên cao / rủi ro thấp (tóm tắt, chi tiết ở Phase 2)

Xếp theo tỷ lệ impact/risk, không xếp theo độ khó:

1. **Thêm `FAQPage` schema cho 25 trang danh mục** — nội dung đã hiển thị
   sẵn, chỉ thiếu markup. Rủi ro gần như 0 (không đổi URL/title/H1/canonical,
   không đổi nội dung hiển thị). *(P0 — sẽ triển khai ở Phase 3.)*
2. **Viết pillar riêng cho Sapphire** (phân khu nhiều căn nhất, đang thiếu
   pillar) — cần nội dung biên tập thật, không tự sinh số liệu bịa. *(P1.)*
3. **Bài cẩm nang: tiền cọc, checklist bàn giao, điều khoản hợp đồng, thuê
   trực tiếp vs môi giới** — chưa có bài riêng dù có tín hiệu search intent
   rõ (SPEC liệt kê đích danh). *(P1.)*
4. **Combo Cluster 3 cho 9 tổ hợp đủ ngưỡng** (mục 6.1) — cần template +
   quy tắc noindex cho phần còn lại. *(P1/P2 tuỳ ngưỡng chọn.)*
5. **Cluster 5 mở rộng** ("đồ cơ bản", "không đồ" cấp toàn site) — đủ dữ
   liệu, đơn giản hơn Cluster 3. *(P1.)*

Không đề xuất mục nào yêu cầu đổi URL/slug/canonical/H1 của trang đang index
— đúng nguyên tắc bắt buộc của SPEC.

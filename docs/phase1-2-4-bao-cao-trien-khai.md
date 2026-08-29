# BÁO CÁO TRIỂN KHAI — PHASE 1, 2, 4
Ngày: 29/08/2026 · Nhánh: `claude/code-task-phase-0-r3nd4t`
Phase 3 **chưa áp**, chờ duyệt — xem `docs/phase3-de-xuat-gop-schema-trang-chu.md`.

---

## 🔙 KỊCH BẢN ROLLBACK

**Commit an toàn (trước mọi thay đổi của việc này): `5900bad`**

```bash
git revert --no-commit 5900bad..HEAD && git commit -m "Rollback khối NAP và trang Giới thiệu & Liên hệ"
```
Hoặc deploy lại nguyên trạng: `git checkout 5900bad -- .`

Các commit của việc này, theo thứ tự:

| Commit | Nội dung | Ảnh hưởng production |
|---|---|---|
| `04e5bcf` | Phase 0 — báo cáo khảo sát | không, chỉ thêm `docs/` |
| `29cc083` | Phase 1 — nâng cấp trang Giới thiệu & Liên hệ, sitemap | có |
| *(Phase 3)* | đề xuất gộp schema | không, chỉ thêm `docs/` |
| `e62dd09` | Phase 2 — khối NAP vào footer toàn site | có |

---

## PHASE 1 — TRANG GIỚI THIỆU & LIÊN HỆ

Giữ nguyên URL `gioi-thieu-lien-he.html`. **Không tạo `/gioi-thieu/`, không tạo `/lien-he/`, không cần 301.**

| Việc | Trạng thái |
|---|---|
| Sửa tên đơn vị → `Cho thuê chung cư Smart City` | ✅ ở NAP, `<title>`, `og:site_name`, header, schema. `TimThueSmartCity.com` chỉ còn dùng khi câu văn nói về **website** |
| Giữ mục "Tuyên bố độc lập" | ✅ nguyên văn, vẫn ở cuối trang |
| Giữ mục "Nguyên tắc về phí dịch vụ" | ✅ nguyên văn |
| Đổ nội dung từ 2 file nháp theo thứ tự đã duyệt | ✅ |
| Thêm vào `sitemap.xml` | ✅ `monthly`, `priority 0.6`, XML hợp lệ |
| Link từ footer toàn site | ✅ 43 trang (sẽ lên ~105 sau lần chạy CI kế tiếp) |
| `<title>` mới | ✅ `Giới thiệu & Liên hệ – Cho thuê chung cư Smart City \| 0977 923 284` |
| JSON-LD | ✅ `AboutPage` + `ContactPage`, `BreadcrumbList`, `FAQPage`. Trỏ tới `#organization` bằng `@id`, **không định nghĩa lại thực thể** |
| GA4 | ✅ giữ nguyên |
| `hreflang` | ✅ không thêm, đúng như đã duyệt ở câu 4 |

### Khối đã XOÁ HẲN vì thiếu dữ liệu (không để placeholder lên production)

| Khối | Chặn bởi |
|---|---|
| ~~Mục "Người phụ trách"~~ | ✅ **đã chèn lại** — A1/A2 gỡ chặn 29/08/2026 |
| ~~Dòng "Giờ làm việc"~~ | ✅ **đã chèn lại** — A3 gỡ chặn, 07:00–22:00 |
| Dòng "Email" trong bảng liên hệ | B1 |
| Mức cọc ở bước 4 quy trình | B6 |
| Nguyên tắc thứ 4 "Giá hiển thị là giá chủ nhà đưa ra" | B5 (phần giải thích bị chặn) |
| FAQ "Phí môi giới tính thế nào" | B5 |
| FAQ "Có hỗ trợ khách nước ngoài không" | chưa xác nhận nhân sự; và câu "website hỗ trợ EN/KO" **chỉ đúng với trang chủ** |
| FAQ "Bao lâu thì vào ở được" | chưa xác nhận |
| Mục "Hướng dẫn đường đi" (4 mục) | B8 |
| Ô số liệu: số căn trống + số năm kinh nghiệm | B7 lấy động được; **anh Đức không cung cấp số năm** nên vẫn bỏ cả cụm — nội dung dùng chữ "nhiều năm", không có con số |

Vị trí từng khối bị bỏ đều có chú thích trong mã nguồn, có dữ liệu là thêm lại được ngay.

---

## PHASE 2 — KHỐI NAP TOÀN SITE

### Nguồn duy nhất
`scripts/khoi-nap.tpl` — dùng chung cho cả 2 script sinh trang và script chèn. Không có bản thứ hai để lệch nhau.

### Nội dung khối NAP
```
Cho thuê chung cư Smart City
Vinhomes Smart City, phường Tây Mỗ, thành phố Hà Nội
Hotline & Zalo: 0977 923 284 · Nhắn Zalo
Thông tin minh bạch: … không đại diện cho Vinhomes/Vingroup.
Giới thiệu & Liên hệ · Cẩm nang thuê nhà · Chủ nhà gửi căn · Chính sách quyền riêng tư
```
Dòng "Giờ làm việc: 07:00 – 22:00, tất cả các ngày trong tuần" đã có (A3 gỡ chặn 29/08/2026), thêm ở đúng một chỗ là `khoi-nap.tpl` rồi đồng bộ ra 45 trang bằng một lệnh.

### Độ phủ

| Nhóm | Số trang | Trạng thái |
|---|---|---|
| Trang tĩnh | **45 / 46** | ✅ đã có NAP trong HTML nguồn |
| Trang chuyển hướng `bang-gia-thue-smart-city-thang-7-2026.html` | 1 | ⏭ bỏ qua **có chủ đích** — `noindex` + `meta refresh` 0 giây, không có footer |
| Trang sinh tự động | 62 | ⏳ template đã sửa; có NAP ở **lần chạy CI kế tiếp** (workflow chạy 01/09/17 giờ UTC) |

### ⚠️ Vì sao KHÔNG dựng lại 62 trang sinh tự động ngay

Đã thử: chạy `sinh-trang-toa.py` một mình **gỡ mất toàn bộ link sang trang chi tiết căn** trong lưới thẻ — vì `noi-lien-ket-chi-tiet.py` mới là bước nối các link đó vào, và nó chạy sau trong pipeline. Chạy đủ pipeline thì lại kéo theo dữ liệu mới (13 trang căn mới, giá đổi, ngày đổi) — vừa lệch phạm vi việc này, vừa chắc chắn đụng độ với commit mà CI tự đẩy 3 lần/ngày.

→ Đúng nguyên tắc repo đã ghi: *"sửa script, đừng sửa file"*. Template đã sửa và **đã kiểm chứng sinh ra đúng khối NAP**; CI dựng lại là xong, không cần thao tác tay.

### Việc kèm theo: gỡ dòng nhận diện cũ trùng lặp

Footer cũ có dòng `Cho thuê chung cư Smart City — môi giới cá nhân… Hotline & Zalo: 0977923284`.
Để cả dòng đó lẫn khối NAP thì **mỗi trang có hai cách viết số điện thoại** (`0977923284` và `0977 923 284`) và hai câu tuyên bố độc lập — đúng kiểu lệch NAP mà việc này sinh ra để dẹp. Nên dòng cũ được **thay bằng** khối NAP (89 trang), 404.html xử lý biến thể `<span>` riêng.

Không mất thông tin nào: khối NAP nói đủ tên đơn vị, tuyên bố độc lập và số điện thoại, cộng thêm địa chỉ và link Giới thiệu & Liên hệ.

### Nghiệm thu Phase 2 (View Source, không phải DevTools)
Khối NAP nằm trong HTML thô, có thể kiểm bằng `curl` hoặc Ctrl+U. Đã đối chiếu bằng máy: bỏ hết thẻ `script` khỏi trang rồi khối NAP vẫn còn nguyên.

---

## PHASE 4

| | Việc | Trạng thái |
|---|---|---|
| A | Thay iframe bản đồ | ⏳ **chờ anh Đức gửi mã nhúng chính thức**. Trang đang dùng mã dạng tìm kiếm — chạy được, trỏ đúng khu đô thị, **chưa trỏ đúng ghim hồ sơ**. Đã ghi chú ngay tại vị trí cần thay, giữ `loading="lazy"` |
| B | Cập nhật `sitemap.xml` | ✅ xong ở Phase 1 |

`scripts/cap-nhat-sitemap.mjs` chỉ sửa `<lastmod>` và gỡ URL `noindex`, **không dựng lại sitemap**, nên URL vừa thêm sẽ được giữ và tự cập nhật ngày.

---

## BẢNG NGHIỆM THU 12 MỤC

| # | Hạng mục | Kết quả |
|---|---|---|
| 1 | Không còn placeholder | ✅ grep `CẦN BỔ SUNG` và `[SỐ]` → **0 kết quả** |
| 2 | Schema hợp lệ | ✅ 186 khối JSON-LD toàn site parse sạch, 0 lỗi · ⏳ Rich Results Test cần chạy trên URL thật sau deploy |
| 3 | JSON-LD trang chủ | ⏳ **Phase 3 chưa áp** — `index.html` chưa sửa dòng schema nào, `FAQPage` còn nguyên. Bảng đề xuất đã cập nhật theo A1/A3 |
| 4 | NAP nhất quán | ✅ trên website chỉ còn **một** cách viết duy nhất · 🔴 **cần anh sửa hồ sơ Google** (xem dưới) |
| 5 | Bản đồ | ⏳ chờ iframe chính thức |
| 6 | GA4 | ✅ 107 trang có tag, không đổi · ⏳ Realtime kiểm sau deploy |
| 7 | Đa ngôn ngữ | ✅ trang thuần tiếng Việt như 107 trang còn lại, đúng như đã duyệt |
| 8 | URL cũ vẫn 200 | ✅ không xoá, không đổi tên URL nào; `kiem-tra-lien-ket.py` báo **không có link gãy** |
| 9 | Công cụ tìm căn ở trang chủ | ✅ `index.html` **chỉ thêm 33 dòng trong footer, xoá 0 dòng** — không chạm bộ lọc |
| 10 | Không mồ côi | ✅ **43 link nội bộ** trỏ tới trang Giới thiệu & Liên hệ (trước: 1). Sẽ lên ~105 sau lần chạy CI |
| 11 | Sitemap | ✅ có URL mới, XML hợp lệ, 44 URL |
| 12 | Tốc độ | ⏳ kiểm sau deploy. Không thêm request nào: +33 dòng HTML/trang, +38 dòng vào `v3.css` sẵn có, không thêm file CSS/JS |

`kiem-tra-lien-ket.py`: **PASS**, 5 cảnh báo (không làm fail). Hai cảnh báo mới xuất hiện là do trung vị nhóm `bai-viet` tăng từ 6 lên 12 khi trang Giới thiệu & Liên hệ nhảy lên 43 link vào — **không trang nào bị mất link**.

---

## 🔴 CÒN CHẶN — CẦN ANH ĐỨC

### Trên hồ sơ Google Business Profile (ngoài code)
1. Sửa địa chỉ thành `Vinhomes Smart City, phường Tây Mỗ, thành phố Hà Nội`
   *(đang là `vinhome Smart City, Tây Mỗ, Hà Nội 100000` — sai chính tả "vinhome")*
2. Chốt giờ làm việc — hồ sơ đang "Mở cả ngày", website **hiện chưa ghi giờ nào**

### ✅ Dữ liệu chặn deploy — ĐÃ GỠ HẾT (29/08/2026)
| # | Đã nhận | Đã dùng ở đâu |
|---|---|---|
| **A1** | Trần Trung Đức · Người trực tiếp vận hành và dẫn xem căn | Mục "Người trực tiếp vận hành", dòng "Người phụ trách" trong bảng liên hệ, `Person.name` trong JSON-LD |
| **A2** | Sống ngay trong khu đô thị, dẫn xem căn linh hoạt · "nhiều năm", **không có con số** | 3 đoạn trong mục "Người trực tiếp vận hành" |
| **A3** | 07:00 – 22:00, tất cả các ngày | Khối NAP (45 trang), bảng liên hệ, `openingHoursSpecification` |

### Duyệt Phase 3
Bảng so sánh trước–sau ở `docs/phase3-de-xuat-gop-schema-trang-chu.md`. Cần 2 câu trả lời: duyệt bảng chưa, và `postalCode` gỡ hay giữ.

### Nên có (không chặn)
Email · URL hồ sơ Google Maps (`hasMap`) · iframe bản đồ chính thức · chính sách phí môi giới · mức cọc · hướng dẫn đường đi.

---

## SAU KHI DEPLOY
Google Search Console → **URL Inspection** → `https://timthuesmartcity.com/gioi-thieu-lien-he.html` → **Request Indexing**.
Trang này chưa từng nằm trong sitemap nên nhiều khả năng chưa được index lần nào.

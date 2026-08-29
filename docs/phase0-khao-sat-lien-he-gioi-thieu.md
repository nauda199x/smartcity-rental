# PHASE 0 — BÁO CÁO KHẢO SÁT
**Phiếu giao việc:** Trang Liên hệ, Giới thiệu & khối NAP toàn site
**Ngày khảo sát:** 29/08/2026 · **Trạng thái:** chỉ đọc, chưa sửa file production nào

---

## 1. Trang chủ có JSON-LD chưa?

**CÓ — 3 khối, dạng object đơn rời nhau, KHÔNG dùng `@graph`, KHÔNG có `@id`.**

| Dòng trong `index.html` | `@type` | Nội dung chính |
|---|---|---|
| 57 | `FAQPage` | 6 cặp hỏi–đáp về giá, vị trí, loại căn, nội thất, cách liên hệ, tần suất cập nhật |
| 114 | `WebSite` | `name` "Cho thuê chung cư Smart City", `alternateName` "Tìm Thuê Smart City" |
| 124 | `RealEstateAgent` | Đã có `telephone` `+84977923284`, `logo`, `image`, `priceRange`, `areaServed`, `address`, và **`sameAs` với 4 URL mạng xã hội thật** |

Toàn site: 102 `BreadcrumbList`, 32 `FAQPage`, 60 `RealEstateListing`/`Apartment`/`Offer`, 27 `Organization`, 13 `Article`.

### ⚠️ Xung đột cần anh Đức quyết trước Phase 3

Trang chủ **đã có sẵn** `RealEstateAgent`, và nội dung khác với khối trong `footer-nap-snippet.html`:

| Trường | Trang chủ hiện tại | Snippet đề xuất |
|---|---|---|
| `priceRange` | `5.500.000₫ - 16.000.000₫` | `6.000.000₫ - 30.000.000₫` |
| `address` | có `streetAddress: "Vinhomes Smart City"`, `postalCode: "100000"` | bỏ `streetAddress`, chỉ `addressLocality: "Phường Tây Mỗ"` |
| `areaServed` | `"Vinhomes Smart City, phường Tây Mỗ, Hà Nội"` | `"Vinhomes Smart City, Tây Mỗ, Nam Từ Liêm, Hà Nội"` |
| `sameAs` | **4 URL thật đang chạy** | 4 chỗ `[CẦN BỔ SUNG]` |
| `@id` | không có | `#organization` |

Ràng buộc số 5 nói "chỉ bổ sung, không thay thế". Nhưng để hai `RealEstateAgent` cùng tồn tại trên một trang với dữ liệu lệch nhau sẽ **hại nhiều hơn lợi** — Google không biết tin cái nào.
→ Đề xuất: **gộp** thành một `@graph` duy nhất, giữ toàn bộ giá trị thật đang có, chỉ thêm `@id`, `employee`/`Person`, `openingHoursSpecification`, `hasMap`. Không tự ý làm, chờ anh duyệt.

---

## 2. GA4 nằm ở đâu? Mã đo là gì?

- **Mã đo:** `G-VF9KHC5TWD` (duy nhất, không có mã thứ hai)
- **Cách đặt:** **inline trong `<head>` từng file**, không có partial. Đặt ở vị trí đầu `<head>`.
- **Độ phủ:** 107 / 108 file HTML.
- **❗ Thiếu GA4:** `bang-gia-thue-smart-city-thang-7-2026.html` — trang này không đo được, ngoài phạm vi phiếu nhưng báo để anh biết.

Có 2 định dạng snippet (cùng mã, khác cách xuống dòng):
- Trang viết tay: khối 8 dòng có comment `<!-- Google Analytics 4 -->`
- Trang sinh tự động: khối 3 dòng nén (xem `s4-01-vinhomes-smart-city/index.html:25`)

→ Hai trang mới chỉ cần dán y hệt khối 8 dòng. Không có vướng mắc.

---

## 3. Cơ chế đa ngôn ngữ VI/EN/KO?

**Đây là điểm phiếu giao việc đang hiểu khác thực tế — cần anh đọc kỹ mục này.**

- File: `assets/ngon-ngu.js` (667 dòng) + `assets/ngon-ngu.css`
- **Chỉ nạp ở duy nhất `index.html`.** 107 trang còn lại không có bộ đổi ngôn ngữ.
- Cơ chế: **dịch chữ hiển thị bằng JS**, đọc từ điển `["EN","KO"]`, lưu lựa chọn vào `localStorage["smartcity_lang"]`, đặt `document.documentElement.lang`. Có đọc `?lang=` nếu có sẵn trên URL nhưng **không sinh ra URL riêng**.
- **KHÔNG có thư mục `/en/` `/ko/`. KHÔNG có thẻ `hreflang` nào trên toàn bộ 108 file.** (đã grep, 0 kết quả)

Phần đầu `ngon-ngu.js` ghi rõ đây là **quyết định cố ý**, nguyên văn:

> *"ĐÂY LÀ TÍNH NĂNG TRẢI NGHIỆM NGƯỜI DÙNG, KHÔNG PHẢI TÍNH NĂNG SEO. Chỉ một địa chỉ duy nhất "/" — không sinh /en/ /ko/, không đụng sitemap, không thêm hreflang."*
> *"KHÔNG tự đoán ngôn ngữ theo trình duyệt... Googlebot thu thập trang với Accept-Language: en-US; tự đổi theo trình duyệt là Google sẽ index bản tiếng Anh thay cho bản tiếng Việt."*

### ⚠️ Hệ quả với Phase 1

Phiếu yêu cầu *"`hreflang` VI/EN/KO đúng cơ chế đã xác định ở Phase 0"*. Cơ chế đã xác định là: **site không dùng hreflang, và đó là chủ ý.**
Thêm `hreflang` vào 2 trang mới sẽ khai báo những URL không tồn tại → lỗi trong Search Console.

→ **Đề xuất:** hai trang mới làm **thuần tiếng Việt, không `hreflang`**, giống hệt 107 trang còn lại. Nghiệm thu mục 7 ("chuyển VI/EN/KO trên 2 trang mới") xin sửa lại thành "không có bộ đổi ngôn ngữ, đúng như mọi trang không phải trang chủ". Chờ anh xác nhận.

---

## 4. Header/footer là partial dùng chung hay copy từng file?

**COPY THỦ CÔNG TỪNG FILE — không có hệ partial.** Và còn phức tạp hơn thế, có 3 lớp:

### Lớp 1 — HTML tĩnh: hai bộ giao diện khác nhau

| Kiểu | Số file | Header | Footer | Wrapper |
|---|---|---|---|---|
| A | 88 | `<header class="top">` | `<footer class="chan">` | `.khung` |
| B | 17–19 | `<header class="topbar">` | `<footer class="site-footer">` | `.shell` |
| Lẻ | 2 | — | `<footer>` trần / inline style | — |

Nội dung footer hai kiểu **khác nhau về chữ**, không chỉ khác class.

### Lớp 2 — 63 trang là FILE SINH TỰ ĐỘNG, sửa tay sẽ mất

| Script | Số trang |
|---|---|
| `scripts/sinh-trang-can.py` (template footer tại dòng 347) | 61 |
| `scripts/sinh-trang-toa.py` | 2 |
| `scripts/dung-lai-trang-danh-muc.py` | 1 |
| `scripts/dung-lai-trang-chu.py` | 1 |

Đầu các file này ghi: *"Trang này do scripts/sinh-trang-toa.py sinh lại từ data.json mỗi lần chạy. **Sửa tay ở đây sẽ mất trong lần chạy sau** - sửa script, đừng sửa file."*
Workflow `cap-nhat-so-can.yml` chạy **3 lần/ngày** (01:00, 09:00, 17:00 UTC) và tự commit → NAP dán tay vào 63 file này sẽ **biến mất trong vòng 8 tiếng**.

### Lớp 3 — ✅ ĐÃ CÓ SẴN cơ chế "footer dùng chung", bằng JS

`assets/app-shell.js` được nạp ở **cả 108 file**, và hàm `boSungDanhTinhWebsite()` (dòng 200–216) **đã chèn sẵn một khối vào `document.querySelector("footer")` trên mọi trang** — kèm link `/gioi-thieu-lien-he.html`.

Chính file này ghi rõ lý do chọn JS:
> *"VÌ SAO DỰNG BẰNG JS THAY VÌ DÁN HTML VÀO 39 TRANG: Sửa một file là cả site đổi theo, không phải mở lại 39 file mỗi lần..."*

### 3 hướng cho Phase 2 — cần anh chọn

| | Cách làm | Ưu | Nhược |
|---|---|---|---|
| **1** | Chèn NAP vào `app-shell.js` (nối tiếp cách đang dùng) | Sửa **1 file**, phủ 108 trang ngay, không sợ bị sinh đè | NAP do JS tạo → công cụ crawl bỏ `<script>` sẽ **không thấy**. *Đây đúng là lý do phiếu kết luận "footer không có tên đơn vị"* |
| **2** | Sửa template trong 2 script sinh trang + sửa tay 45 trang viết tay | NAP nằm trong HTML tĩnh, mọi crawler đều đọc được | Đụng 47 điểm, phải chạy lại script sinh trang, rủi ro cao hơn |
| **3** | **Kết hợp:** sửa template script (63 trang) + sửa tay 45 trang, `app-shell.js` chỉ làm lưới an toàn | Tĩnh 100%, phủ đủ | Nhiều việc nhất |

→ **Đề xuất hướng 3**, vì mục đích của NAP là để **Google đọc được**, mà lớp JS hiện tại chính là thứ đã khiến việc kiểm chứng từ bên ngoài kết luận "site không có thông tin doanh nghiệp". Chờ anh quyết.

---

## 5. Có build script không? Deploy bằng gì?

- **Không có build system.** Không `package.json`, không bundler, không static site generator.
- HTML tĩnh viết tay + **bộ script sinh trang** (14 file Python, 2 file Node) trong `scripts/`, chạy thủ công hoặc qua Actions.
- **2 GitHub Actions:**
  - `cap-nhat-so-can.yml` — 3 lần/ngày, chạy 4 script sinh trang + cập nhật số căn + `cap-nhat-sitemap.mjs`, rồi **tự commit thẳng vào nhánh mặc định**.
  - `tai-anh-can-ho.yml` — tải & thay ảnh căn hộ.
- **Deploy:** GitHub Pages phục vụ trực tiếp từ nhánh (có `CNAME` = `timthuesmartcity.com` ở gốc, không có workflow build/deploy Pages). **Merge vào `main` là lên production ngay**, không có bước staging.
- ⚠️ `sitemap.xml` do `scripts/cap-nhat-sitemap.mjs` cập nhật tự động → Phase 4B phải **thêm 2 URL vào script đó**, không phải sửa tay `sitemap.xml` (sẽ bị ghi đè).

---

# 🔴 PHÁT HIỆN NGOÀI 5 CÂU HỎI — ẢNH HƯỞNG TRỰC TIẾP TỚI PHẠM VI VIỆC

## A. Website ĐÃ CÓ trang Giới thiệu & Liên hệ

File `gioi-thieu-lien-he.html` ở thư mục gốc — **đang chạy trên production**, 7.756 byte, có đủ:
`<title>`, `<meta description>`, `<link rel="canonical">`, GA4, header/footer kiểu B, và các mục: *TimThueSmartCity.com là gì · Đơn vị vận hành · Phạm vi dịch vụ · Nguyên tắc về phí dịch vụ · Tuyên bố độc lập với Vinhomes/Vingroup · Liên hệ (hotline + Zalo)*.

Trang này được link từ **mọi trang** qua `app-shell.js`, cộng 1 link tĩnh trong `chinh-sach-quyen-rieng-tu.html`.

**Nhưng:**
- ❌ **Không có trong `sitemap.xml`** → Google gần như chắc chắn chưa index
- ❌ **Không có JSON-LD nào**
- ❌ Link duy nhất trỏ tới nó trên hầu hết trang là **do JS sinh ra** → crawler không thấy
- ❌ Không có tên người phụ trách, không có giờ làm việc, không có địa chỉ

→ Đây giải thích vì sao kiểm chứng từ bên ngoài kết luận "không có trang Giới thiệu/Liên hệ": **trang có tồn tại, nhưng vô hình với Google.**

### ⚠️ Cần anh quyết trước Phase 1

Tạo thêm `/lien-he/` và `/gioi-thieu/` sẽ thành **3 trang cùng chủ đề** tự cạnh tranh nhau. Ba hướng:

| | Cách | Ghi chú |
|---|---|---|
| **1** | Tạo 2 trang mới, `gioi-thieu-lien-he.html` đặt `canonical` trỏ về `/gioi-thieu/` | Giữ URL cũ trả 200 (ràng buộc 3), gom tín hiệu về trang mới |
| **2** | Chỉ nâng cấp `gioi-thieu-lien-he.html` tại chỗ + thêm vào sitemap | Ít việc nhất, nhưng gộp 2 chủ đề vào 1 URL, yếu hơn về SEO |
| **3** | Tạo 2 trang mới, để nguyên trang cũ | ❌ Không nên — trùng lặp nội dung |

→ **Đề xuất hướng 1.**

## B. NAP đang lệch giữa 3 nguồn — chưa chốt được chuỗi chuẩn

| Nguồn | Địa chỉ |
|---|---|
| `footer-nap-snippet.html` | `Vinhomes Smart City, P. Tây Mỗ, **Q. Nam Từ Liêm**, Hà Nội` |
| `index.html` JSON-LD | `Vinhomes Smart City, **phường Tây Mỗ, Hà Nội**` (không có cấp quận) |
| Hồ sơ Google (theo phiếu) | Chỉ hiện `Hà Nội` — dạng khu vực phục vụ |

Bản thân site đã bỏ cấp quận (khớp với việc Hà Nội bỏ cấp quận/huyện từ 2025). Nghiệm thu mục 4 đòi "giống hệt từng ký tự" → **chưa có chuỗi chuẩn để đối chiếu.** Không tự chọn, xin anh chốt.

## C. Dữ liệu B2 (sameAs) — repo ĐÃ CÓ, không cần anh cung cấp

4 URL này đã nằm trong `index.html` JSON-LD **và** trong footer của 107 trang, kèm comment yêu cầu hai nơi phải trùng khớp:

```
https://www.facebook.com/people/T%C3%ACm-thu%C3%AA-Smart-City/61591756688919/
https://www.tiktok.com/@timthuesmartcity
https://www.instagram.com/timthuesmartcity_com/
https://www.youtube.com/@Timthuesmartcity
```

→ Đây là dữ liệu thật đang chạy trên site, không phải bịa. Đề xuất **dùng lại nguyên văn** cho `sameAs` của 2 trang mới. Chờ anh gật.

## D. Nhánh Git lệch với phiếu

Phiếu ghi nhánh `seo/contact-about-pages`. Phiên làm việc này được giao nhánh **`claude/code-task-phase-0-r3nd4t`** và không được phép đẩy sang nhánh khác. Em đang làm trên nhánh được giao. Nếu anh muốn đúng tên trong phiếu, anh xác nhận để em đổi.

---

# 📋 DỮ LIỆU CÒN THIẾU — CHỜ ANH ĐỨC CUNG CẤP

Em **không điền bất kỳ mục nào** dưới đây (ràng buộc số 7).

## Bắt buộc — thiếu thì không deploy được

| # | Cần gì | Xuất hiện ở |
|---|---|---|
| **A1** | **Họ và tên người phụ trách** | `gioi-thieu/index.html:137`, JSON-LD `Person.name` ở 3 chỗ |
| **A2** | **Số năm kinh nghiệm** + 2–3 câu mô tả thực tế (đã hỗ trợ bao nhiêu khách, am hiểu phân khu nào nhất) | `gioi-thieu/index.html:93, 140` |
| **A3** | **Chốt giờ làm việc.** Hồ sơ Google đang để *"Mở cả ngày"*, 3 file nháp đang ghi *08:00–20:00*. Phải sửa một trong hai | `footer-nap-snippet.html:87–89`, `lien-he`, `gioi-thieu` |

## Nên có — không chặn deploy, thiếu thì em **xoá hẳn khối đó**, không để `[CẦN BỔ SUNG]` lên production

| # | Cần gì | Trạng thái |
|---|---|---|
| B1 | Email liên hệ | ❌ chưa có ở đâu trong repo |
| B2 | URL Facebook/TikTok/YouTube/Instagram | ✅ **repo đã có** — xem mục C, chỉ cần anh gật |
| B3 | URL hồ sơ Google Maps (cho `hasMap`) | ❌ chưa có |
| B4 | Ảnh đại diện | ⚠️ repo có `og-smartcity.jpg` + `favicon-512.png` đang dùng làm `image`/`logo`. Nếu anh muốn ảnh chân dung thật thì cần gửi file |
| B5 | Chính sách phí môi giới — ai trả, mức bao nhiêu | ❌ trang hiện tại cố tình nói tránh: *"sẽ được trao đổi rõ ràng... không đưa ra cam kết về mức phí"*. Cần anh quyết có công bố con số không |
| B6 | Mức đặt cọc và điều kiện | ❌ chưa có |
| B7 | Số căn đang trống | ✅ **lấy động được** — `scripts/cap-nhat-so-can.mjs` đã làm việc này cho trang chủ, em nối vào, không nhập tay |
| B8 | Hướng dẫn đường đi (4 mục: từ trung tâm HN, từ ĐL Thăng Long, xe buýt, chỗ để xe) | ❌ chưa có |
| — | **iframe bản đồ chính thức** (Phase 4A) | ❌ chờ anh lấy từ Google Maps → Chia sẻ → Nhúng bản đồ |

---

# ❓ 5 CÂU CHỜ ANH DUYỆT TRƯỚC KHI SANG PHASE 1

1. **Xử lý `gioi-thieu-lien-he.html` đang tồn tại thế nào?** (đề xuất: tạo 2 trang mới + canonical trang cũ về `/gioi-thieu/`)
2. **Phase 2 đi hướng nào?** (đề xuất: hướng 3 — sửa template script + 45 trang tĩnh, JS làm lưới an toàn)
3. **Phase 3 gộp `RealEstateAgent` cũ và mới thành một `@graph`, giữ nguyên giá trị thật đang chạy** — anh đồng ý không?
4. **Bỏ yêu cầu `hreflang`** cho 2 trang mới, làm thuần tiếng Việt như 107 trang còn lại — anh đồng ý không?
5. **Chuỗi địa chỉ chuẩn** để 3 nơi khớp từng ký tự là chuỗi nào? Và **giờ làm việc (A3)** chốt theo Google hay theo file nháp?

Cùng với đó là **A1, A2** — hai mục này thiếu thì trang Giới thiệu không có giá trị.

**Em dừng ở đây, chưa sửa file production nào. Chờ anh duyệt.**

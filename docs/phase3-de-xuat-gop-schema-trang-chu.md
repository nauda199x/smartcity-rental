# PHASE 3 — ĐỀ XUẤT GỘP SCHEMA TRANG CHỦ
🛑 **CHƯA ÁP DỤNG.** File này chỉ để anh Đức duyệt. `index.html` chưa bị sửa dòng nào.

Ngày lập: 29/08/2026 · Cập nhật sau phiếu bổ sung A1/A2/A3 · Áp cho: `index.html`

---

## Hiện trạng

Trang chủ có **3 khối JSON-LD rời nhau**, object đơn, không `@graph`, không `@id`:

| Dòng | Khối | Xử lý đề xuất |
|---|---|---|
| 57 | `FAQPage` (6 câu hỏi) | **KHÔNG ĐỘNG** — giữ nguyên khối riêng, không đưa vào `@graph` |
| 114 | `WebSite` | Gộp vào `@graph`, thêm `@id` |
| 124 | `RealEstateAgent` | Gộp vào `@graph`, thêm `@id` + các trường còn thiếu |

Nguyên tắc áp dụng theo duyệt: **giá trị thật đang chạy là gốc, chỉ thêm trường còn thiếu.**

---

## BẢNG SO SÁNH TỪNG TRƯỜNG — `RealEstateAgent`

| Trường | TRƯỚC (đang chạy) | SAU (đề xuất) | Loại |
|---|---|---|---|
| `@id` | *(không có)* | `https://timthuesmartcity.com/#organization` | ➕ THÊM |
| `@type` | `RealEstateAgent` | *không đổi* | = giữ |
| `name` | `Cho thuê chung cư Smart City` | *không đổi* | = giữ ✅ **đã khớp hồ sơ Google, không cần dùng tới ngoại lệ ghi đè ở quy tắc 3** |
| `alternateName` | *(không có)* | `Tìm Thuê Smart City` | ➕ THÊM — lấy từ `WebSite.alternateName` đang chạy, **giữ nguyên cách viết hoa cũ**, không dùng `Tìm thuê Smart City` của file nháp |
| `url` | `https://timthuesmartcity.com/` | *không đổi* | = giữ |
| `telephone` | `+84977923284` | *không đổi* | = giữ |
| `logo` | `.../favicon-512.png` | *không đổi* | = giữ |
| `image` | `.../og-smartcity.jpg` | *không đổi* | = giữ — mục B4 coi như đã có, trừ khi anh muốn ảnh chân dung |
| `priceRange` | `5.500.000₫ - 16.000.000₫` | *không đổi* | = giữ ⚠️ **KHÔNG lấy `6.000.000₫ - 30.000.000₫` của file nháp** |
| `sameAs` | 4 URL thật (FB, TikTok, IG, YouTube) | *không đổi* | = giữ ⚠️ **KHÔNG ghi đè bằng 4 placeholder của file nháp** |
| `description` | *(không có)* | `Chuyên cho thuê căn hộ tại Vinhomes Smart City, phường Tây Mỗ, thành phố Hà Nội. Quỹ căn cập nhật hằng ngày, ảnh thật, phủ 8 phân khu.` | ➕ THÊM |
| `currenciesAccepted` | *(không có)* | `VND` | ➕ THÊM |
| `areaServed.name` | `Vinhomes Smart City, phường Tây Mỗ, Hà Nội` | `Vinhomes Smart City, phường Tây Mỗ, thành phố Hà Nội` | ✏️ **SỬA** — chuẩn hoá theo chuỗi đã chốt ở câu 5. Chỉ thêm hai chữ "thành phố" |
| `address.streetAddress` | `Vinhomes Smart City` | *(gỡ bỏ)* | ➖ **GỠ** — theo câu 5: hồ sơ là dạng khu vực phục vụ, không dùng `streetAddress` |
| `address.addressLocality` | `Tây Mỗ` | `Phường Tây Mỗ` | ✏️ SỬA — theo khối JSON-LD anh đã chốt ở câu 5 |
| `address.addressRegion` | `Hà Nội` | *không đổi* | = giữ |
| `address.postalCode` | `100000` | *(gỡ bỏ)* | ➖ **GỠ** — ❓ **XIN ANH XÁC NHẬN RIÊNG MỤC NÀY** (xem cảnh báo bên dưới) |
| `address.addressCountry` | `VN` | *không đổi* | = giữ |
| `openingHoursSpecification` | *(không có)* | `07:00` – `22:00`, cả 7 ngày | ➕ **THÊM** — đã gỡ chặn A3. ⚠️ **KHÔNG dùng `08:00`/`20:00` của file nháp**, giá trị đó đã hết hiệu lực |
| `employee` → node `Person` | *(không có)* | `{ "@id": ".../#agent" }` + node `Person` tên **Trần Trung Đức** | ➕ **THÊM** — đã gỡ chặn A1 |
| `hasMap` | *(không có)* | ⏸ **CHƯA THÊM** | 🔒 chặn bởi **B3** |
| `email` | *(không có)* | ⏸ **CHƯA THÊM** | 🔒 chặn bởi **B1** |

### ❓ Một mục cần anh quyết riêng: `postalCode`

Khối JSON-LD anh chốt ở câu 5 không có `postalCode`, nên theo đúng chữ thì phải gỡ.
Nhưng hồ sơ Google hiện **đang hiển thị `100000`** (`vinhome Smart City, Tây Mỗ, Hà Nội 100000`).

Gỡ đi thì website và hồ sơ lệch nhau một trường. Hai lựa chọn:
- **(a) Gỡ** — đúng nguyên tắc "dạng khu vực phục vụ, không khai địa chỉ chi tiết". Khi anh sửa hồ sơ Google theo chuỗi chuẩn thì bỏ luôn mã bưu chính cho khớp.
- **(b) Giữ `100000`** — khớp đúng hồ sơ hiện tại, và mã bưu chính không phải địa chỉ đường phố nên không mâu thuẫn với dạng khu vực phục vụ.

*Em nghiêng về (b): giữ được một trường thật đang khớp cả hai nơi, và cũng đúng quy tắc số 1 "giá trị thật đang chạy là gốc". Nhưng đây là ghi đè giá trị đang chạy nên em không tự quyết.*
**Bảng và mã dưới đây đang thể hiện phương án (a) — đúng theo câu 5 anh đã chốt.**

---

## BẢNG SO SÁNH TỪNG TRƯỜNG — `WebSite`

| Trường | TRƯỚC | SAU | Loại |
|---|---|---|---|
| `@id` | *(không có)* | `https://timthuesmartcity.com/#website` | ➕ THÊM |
| `name` | `Cho thuê chung cư Smart City` | *không đổi* | = giữ |
| `alternateName` | `Tìm Thuê Smart City` | *không đổi* | = giữ |
| `url` | `https://timthuesmartcity.com/` | *không đổi* | = giữ |
| `inLanguage` | *(không có)* | `vi-VN` | ➕ THÊM |
| `publisher` | *(không có)* | `{ "@id": ".../#organization" }` | ➕ THÊM |

## `FAQPage` — KHÔNG ĐỘNG

Giữ nguyên khối riêng ở dòng 57, không đưa vào `@graph`, không sửa một ký tự.
Như vậy nghiệm thu mục 3 ("schema cũ còn nguyên") kiểm chứng được bằng `git diff`.

---

## ✅ TỔNG KẾT THAY ĐỔI

- **Không mất trường nào** đang có giá trị thật, trừ 2 trường địa chỉ gỡ theo đúng câu 5 (`streetAddress`, `postalCode`).
- **Không có giá trị nào của file nháp ghi đè giá trị thật.** `priceRange` và `sameAs` giữ nguyên bản đang chạy.
- **2 trường bị hoãn** vì thiếu dữ liệu thật: `hasMap` (B3), `email` (B1).
- **Đã gỡ chặn** sau phiếu bổ sung: `openingHoursSpecification` (A3 → 07:00–22:00) và node `Person` (A1 → Trần Trung Đức).

> Node `Person` và `openingHoursSpecification` hiện **đã có trên `gioi-thieu-lien-he.html`** dưới dạng mô tả bổ sung cùng `@id`. Khi áp Phase 3, trang chủ mang bản định nghĩa đầy đủ; hai nơi cùng `@id` và cùng giá trị nên bộ đọc JSON-LD gộp lại, không xung đột.

---

## MÃ SẼ THAY VÀO — thay cho HAI khối ở dòng 114 và 124

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "RealEstateAgent",
      "@id": "https://timthuesmartcity.com/#organization",
      "name": "Cho thuê chung cư Smart City",
      "alternateName": "Tìm Thuê Smart City",
      "url": "https://timthuesmartcity.com/",
      "telephone": "+84977923284",
      "logo": "https://timthuesmartcity.com/favicon-512.png",
      "image": "https://timthuesmartcity.com/og-smartcity.jpg",
      "description": "Chuyên cho thuê căn hộ tại Vinhomes Smart City, phường Tây Mỗ, thành phố Hà Nội. Quỹ căn cập nhật hằng ngày, ảnh thật, phủ 8 phân khu.",
      "priceRange": "5.500.000₫ - 16.000.000₫",
      "currenciesAccepted": "VND",
      "sameAs": [
        "https://www.facebook.com/people/T%C3%ACm-thu%C3%AA-Smart-City/61591756688919/",
        "https://www.tiktok.com/@timthuesmartcity",
        "https://www.instagram.com/timthuesmartcity_com/",
        "https://www.youtube.com/@Timthuesmartcity"
      ],
      "areaServed": {
        "@type": "Place",
        "name": "Vinhomes Smart City, phường Tây Mỗ, thành phố Hà Nội"
      },
      "address": {
        "@type": "PostalAddress",
        "addressLocality": "Phường Tây Mỗ",
        "addressRegion": "Hà Nội",
        "addressCountry": "VN"
      },
      "openingHoursSpecification": [{
        "@type": "OpeningHoursSpecification",
        "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        "opens": "07:00",
        "closes": "22:00"
      }],
      "employee": { "@id": "https://timthuesmartcity.com/#agent" }
    },
    {
      "@type": "Person",
      "@id": "https://timthuesmartcity.com/#agent",
      "name": "Trần Trung Đức",
      "jobTitle": "Người trực tiếp vận hành và dẫn xem căn",
      "telephone": "+84977923284",
      "worksFor": { "@id": "https://timthuesmartcity.com/#organization" },
      "knowsAbout": [
        "Cho thuê căn hộ Vinhomes Smart City",
        "Thị trường thuê nhà Tây Mỗ, Hà Nội"
      ]
    },
    {
      "@type": "WebSite",
      "@id": "https://timthuesmartcity.com/#website",
      "url": "https://timthuesmartcity.com/",
      "name": "Cho thuê chung cư Smart City",
      "alternateName": "Tìm Thuê Smart City",
      "inLanguage": "vi-VN",
      "publisher": { "@id": "https://timthuesmartcity.com/#organization" }
    }
  ]
}
</script>
```

## Sẽ thêm ngay khi có dữ liệu

```json
"email": "…",     // B1
"hasMap": "…"     // B3 — URL hồ sơ Google Maps
```

---

## 🛑 CHỜ DUYỆT

Anh trả lời gọn 2 ý là em áp ngay:
1. Duyệt bảng trên chưa?
2. `postalCode` — chọn **(a) gỡ** hay **(b) giữ `100000`**?

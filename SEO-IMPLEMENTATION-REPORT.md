# SEO-IMPLEMENTATION-REPORT — timthuesmartcity.com

Phase 5. Ghi lại đúng những gì đã đổi trong đợt này. Xem `SEO-CONTENT-AUDIT.md`
(Phase 1) và `SEO-CONTENT-PLAN.md` (Phase 2) để biết toàn bộ phát hiện và kế
hoạch — báo cáo này chỉ nói về phần **đã triển khai** (P0).

## 1. Việc đã làm

**Duy nhất một thay đổi:** thêm schema `FAQPage` vào 25 trang danh mục
(cluster loại căn, phân khu, giá, nội thất, và trang tòa S4.01 nếu có FAQ —
thực tế S4.01 không có khối FAQ hiển thị nên không bị đụng tới).

### File đã thêm mới

| File | Nội dung |
|---|---|
| `SEO-CONTENT-AUDIT.md` | Audit Phase 1 — URL inventory, content depth, rendering/indexability, schema, dữ liệu định lượng, rủi ro |
| `SEO-CONTENT-PLAN.md` | Kiến trúc đề xuất Phase 2 — P0/P1/P2, ngưỡng dữ liệu Cluster 3, danh sách URL đề xuất |
| `scripts/them-schema-faq.py` | Script sinh `FAQPage` từ khối FAQ hiển thị sẵn, idempotent, có cờ `--thu` |

### File đã sửa (25 file, mỗi file đúng 1 dòng)

`1pn/`, `1pn-plus/`, `1pn-plus-duoi-10-trieu/`, `1pn-plus-full-do/`, `2pn/`,
`2pn-plus/`, `2pn-duoi-10-trieu/`, `2pn-10-12-trieu/`, `2pn-full-do/`,
`2pn-plus-12-15-trieu/`, `3pn/`, `3pn-12-15-trieu/`, `3pn-full-do/`,
`studio/`, `studio-duoi-7-trieu/`, `studio-7-10-trieu/`, `studio-full-do/`,
`sapphire/`, `sakura/`, `masteri/`, `miami/`, `imperia/`, `lumiere/`,
`canopy/`, `tonkin/` — tất cả `index.html`.

Mỗi file: **duy nhất dòng chứa `<script type="application/ld+json">` thay
đổi** — chèn thêm 1 phần tử `{"@type":"FAQPage","mainEntity":[...]}` vào
mảng `@graph` đã có sẵn (`BreadcrumbList` + `ItemList`). 5 câu hỏi/trả lời
lấy nguyên văn từ khối `<details><summary>` đang hiển thị trên chính trang
đó (đã bỏ thẻ HTML, giữ nguyên chữ) — không tạo câu hỏi mới, không đổi câu
trả lời.

**Không đổi:** URL, canonical, `<title>`, meta description, `<h1>`, nội
dung hiển thị, `sitemap.xml`, `robots.txt`, `data.json`, `dong-bo-can.js`,
`assets/v3.css`, cấu trúc điều hướng.

## 2. Lý do

`SEO-CONTENT-AUDIT.md` mục 5 phát hiện: 25 trang danh mục có khối FAQ hiển
thị thật (visible, không ẩn) nhưng thiếu schema `FAQPage` tương ứng, trong
khi 8 trang khác của site (trang chủ, các bài cẩm nang) đã có đúng schema
này từ trước. Đây là khoảng schema rõ nhất, đúng tinh thần Phần G của SPEC
("chỉ triển khai schema phù hợp với nội dung thực sự xuất hiện trên trang")
và là việc duy nhất trong toàn bộ danh sách cơ hội (audit mục 8) **không
cần viết nội dung biên tập mới** — điều kiện bắt buộc để xếp P0 theo đúng
yêu cầu "chỉ làm rủi ro thấp trước, không code toàn bộ ngay".

Lưu ý trung thực (đã ghi trong audit): 5 câu hỏi/trả lời giống nhau trên cả
25 trang (boilerplate có sẵn từ trước, không phải do đợt này tạo ra), nên
`FAQPage` sinh ra cũng giống nhau về nội dung giữa các trang — đây là hệ quả
đúng của nguyên tắc "chỉ đánh dấu đúng nội dung đã hiển thị", không phải lỗi
kỹ thuật. Việc viết FAQ riêng theo từng trang được xếp P1 trong kế hoạch.

## 3. Cách sinh ra

`scripts/them-schema-faq.py` (script mới, theo đúng quy ước đặt tên/cấu
trúc của các script khác trong `scripts/`):

1. Quét toàn repo tìm trang có `id="bo-loc-trang"` — đúng cách
   `dung-lai-trang-danh-muc.py` đang dùng, không viết cứng danh sách trang.
2. Đọc khối `<h2>Câu hỏi thường gặp</h2>...<details>...</details>` đã có
   sẵn trong HTML, bỏ thẻ, giải mã HTML entity.
3. Parse JSON-LD hiện có, chèn/cập nhật phần tử `FAQPage` trong `@graph`,
   ghi lại bằng đúng định dạng compact (không thêm khoảng trắng) khớp style
   hiện tại của file.
4. Chỉ ghi file nếu nội dung thực sự đổi (idempotent — chạy lại lần 2 trên
   cùng input cho 0 thay đổi, đã kiểm chứng).
5. Hỗ trợ `--thu` (xem trước, không ghi) theo đúng quy ước các script khác.

## 4. Regression check (Phase 4)

So sánh BEFORE (trước khi chạy script) / AFTER (sau khi chạy) bằng đúng 2
công cụ audit có sẵn trong repo:

**`scripts/kiem-tra-seo-snapshot.py --so-sanh`** (title, meta description,
canonical, toàn bộ H1/H2/H3 theo thứ tự, JSON-LD, GA4, alt ảnh của 44 trang):

- **Khác biệt duy nhất: đúng 25 trang danh mục, đúng ở JSON-LD, đúng như dự
  kiến** ("JSON-LD khác nhau (1 → 1 khối)" — vẫn 1 script tag/trang, chỉ
  nội dung bên trong lớn hơn).
- **19 trang còn lại: 0 khác biệt.**
- **Toàn bộ 44 trang: title, meta description, canonical, H1/H2/H3, GA4, alt
  ảnh — giống hệt trước và sau, không một ký tự nào đổi.**

**`scripts/kiem-tra-lien-ket.py`** (đếm link vào/ra theo ngưỡng, phát hiện
link nội bộ hỏng): output **giống hệt byte-for-byte** trước/sau —
`=== KẾT QUẢ: PASS`.

**Kiểm tra thêm đã chạy:**
- `json.loads()` toàn bộ khối JSON-LD của 27 file `*/index.html` — parse
  được 100%, không lỗi cú pháp.
- `git diff --stat` xác nhận đúng 25 file đổi, mỗi file đúng 1 dòng — không
  file nào khác trong repo bị chạm (đặc biệt: `sitemap.xml`, `robots.txt`,
  `data.json`, `dong-bo-can.js`, `assets/` — 0 thay đổi).
- Chạy lại script lần 2 (`--thu`): 25/25 trang báo "đã có sẵn" — xác nhận
  idempotent, an toàn nếu vô tình chạy trùng trong workflow.

**Không phát hiện:** canonical sai, noindex ngoài ý muốn, duplicate
title/H1 hàng loạt mới sinh ra, link nội bộ hỏng, lỗi sitemap, redirect
chain, orphan page. Không có thay đổi nào ảnh hưởng CSS/layout nên không có
rủi ro Core Web Vitals (không đụng file `assets/v3.css`, không thêm
DOM hiển thị — `FAQPage` là JSON-LD, không render ra màn hình).

## 5. Rủi ro còn lại / việc cần làm thủ công

1. **Chưa wire vào GitHub Actions.** `scripts/them-schema-faq.py` hiện chạy
   tay. Nếu sau này có người sửa tay nội dung FAQ hiển thị trên 1 trang danh
   mục mà không chạy lại script, `FAQPage` sẽ lệch với nội dung hiển thị.
   Đề xuất: thêm 1 bước gọi script này (idempotent, đã kiểm chứng an toàn)
   vào `cap-nhat-so-can.yml`, ngay sau bước `dung-lai-trang-danh-muc.py` —
   nhưng **không tự làm trong đợt này** vì đây là thay đổi vào file workflow
   (`.github/workflows/`), ngoài phạm vi "không tạo URL/logic mới ngoài P0
   đã duyệt", cần người chủ repo xác nhận trước.
2. **FAQ vẫn là boilerplate chung 25 trang** (ghi nhận ở audit, xếp P1) —
   thêm schema không tự làm nội dung phong phú hơn, chỉ đánh dấu đúng những
   gì đang có. Giá trị thật (rich result, AI Overview) sẽ tăng khi nội dung
   FAQ được viết riêng theo từng trang.
3. **Google Rich Results Test nên chạy tay trước khi coi là "xong hẳn".**
   Đã validate JSON parse được và đúng cấu trúc `Question`/`acceptedAnswer`/
   `Answer` theo schema.org, nhưng khuyến nghị dán 1-2 trang (vd `/studio/`)
   vào https://search.google.com/test/rich-results sau khi merge để xác
   nhận Google đọc được, trước khi coi việc này là hoàn tất 100%.
4. **Toàn bộ Phase A (nội dung mới: pillar phân khu, bài cẩm nang, so
   sánh, Cluster 3/5)** trong `SEO-CONTENT-PLAN.md` **chưa triển khai** —
   đúng theo yêu cầu SPEC "không code toàn bộ ngay, chỉ P0 trước". Cần trao
   đổi với chủ site để xác nhận thứ tự ưu tiên P1 trước khi viết, vì các
   mục đó cần nội dung biên tập thật (không được tự bịa số liệu/tiện ích
   theo Phần I của SPEC).

## 6. Expected SEO impact

- **Ngắn hạn:** không thay đổi thứ hạng (không đổi nội dung hiển thị/URL).
  Structured data bổ sung giúp Google/AI Overview hiểu rõ hơn nội dung FAQ
  đã có trên 25 trang landing page thương mại quan trọng nhất site (đang
  giữ `priority: 0.9` trong sitemap).
- **Trung hạn:** khi kết hợp với P1 (viết FAQ riêng theo trang), giá trị
  tăng thêm vì mỗi `FAQPage` sẽ phản ánh đúng câu hỏi đặc thù của từng
  cluster thay vì bộ câu hỏi chung.
- **Rủi ro tồn dư:** gần như bằng 0 với đúng phạm vi đã triển khai — đã
  regression-test đầy đủ theo yêu cầu Phần J của SPEC, không phát hiện tác
  dụng phụ nào.

# AUDIT-REPO — Giai đoạn 0: khảo sát repo

> Đầu ra bắt buộc của Phase 0 theo `SEOEXPANSIONPLAN.md`. Chỉ đọc, không sửa
> code ở giai đoạn này. Ngày khảo sát: 24/08/2026.
> Commit an toàn để rollback nếu cần: `6bcf6cf040f1245e85433cd1e4f0a10690ab0830`
> (nhánh làm việc: `claude/new-session-uiz59k` — nhánh do hệ thống chỉ định
> cho phiên này, thay cho `seo/building-pages-expansion` nêu trong tài liệu
> gốc; xem mục 8).

---

## 1. Cấu trúc thư mục (rút gọn, bỏ `anh-can-ho/*.webp` và `images/*`)

```
/
├── .github/workflows/
│   ├── cap-nhat-so-can.yml      # chạy 3 lần/ngày: sinh trang tòa, trang căn,
│   │                             # cập nhật thẻ SEO + sitemap, commit thẳng vào nhánh
│   └── tai-anh-can-ho.yml       # chạy tay: tải ảnh Drive -> webp, sitemap-images.xml
├── data.json                    # NGUỒN DỮ LIỆU DUY NHẤT — 1000 dòng, do Apps Script ghi đè
├── dong-bo-can.js               # đọc data.json trong trình duyệt, dựng lưới căn + JSON-LD + GA4
├── index.html                   # trang chủ — công cụ tìm căn (KHÔNG ĐỤNG)
├── sitemap.xml, sitemap-can-ho.xml, sitemap-images.xml, robots.txt
├── assets/{v3.css, app-shell.js, gallery.js, ngon-ngu.js, ngon-ngu.css}
├── scripts/                     # 12 script Python/Node, xem mục 3 và 6
├── {studio,1pn,1pn-plus,2pn,2pn-plus,3pn}/                    # 6 trang loại căn gốc
├── {studio,1pn-plus,2pn}-{duoi-...,...-trieu}/, *-full-do/    # 12 trang danh mục con (giá/nội thất)
├── {sapphire,masteri,miami,sakura,imperia,lumiere,canopy,tonkin}/  # 8 trang phân khu
├── s4-01-vinhomes-smart-city/   # 1 trang cấp TÒA — DUY NHẤT, template mẫu cho Phase 2
├── can-ho/                      # 27 trang riêng từng căn hộ + danh-sach-trang.json (sổ đăng ký slug)
├── gui-thue/                    # trang chủ nhà gửi căn
├── *.html (17 file)             # bài cẩm nang, pillar phân khu, trang thủ tục... (nội dung tĩnh viết tay)
├── SEO-AUDIT.md, SEO-CONTENT-AUDIT.md, SEO-CONTENT-PLAN.md,
│   SEO-IMPLEMENTATION-REPORT.md, AUDIT-BRAND-NAME.md   # audit SEO đợt trước (xem mục 8)
├── README.md                    # tài liệu kiến trúc do repo tự viết — RẤT ĐÁNG TIN, xem mục 3
├── llms.txt, BingSiteAuth.xml, CNAME
└── docs/audit-repo.md           # file này
```

27 trang danh mục tĩnh (6 loại căn + 12 giá/nội thất + 8 phân khu + 1 tòa =
27) đều cùng một khuôn: `<script type="application/json" id="bo-loc-trang">`
khai bộ lọc, `dong-bo-can.js` đọc và dựng lưới căn lúc chạy trong trình
duyệt. Trang tòa S4.01 khác hẳn: **không** dùng `dong-bo-can.js`, toàn bộ
listing nằm sẵn trong HTML do `sinh-trang-toa.py` sinh ra (xem mục 3).

## 2. Schema dữ liệu quỹ căn — `data.json`

**Nguồn:** Google Sheets → Apps Script đẩy thẳng vào `data.json` ở gốc repo,
~30 phút/lần, commit trực tiếp vào `main`/nhánh hiện tại (12 commit tự động
riêng trong ngày 24/08/2026, message `"Tự động cập nhật dữ liệu căn hộ - ..."`).
File JSON dạng mảng phẳng, 1000 dòng (bao gồm cả căn không hiển thị).

| Field | Kiểu | Ví dụ giá trị thật |
|---|---|---|
| `Mã nội bộ` | number hoặc string | `2`, `"CT.2N2.364"`, `"CC3"` |
| `Tòa` | string, **không chuẩn hoá** | `"SA3"`, `"S401"`, `"MasA"`, `"A2"`, `"GS5"` |
| `Loại` | string | `"Studio"`, `"1 Ngủ +"`, `"2 Ngủ"`, `"3 Ngủ"` |
| `Diện tích` | number (m²) | `32` |
| `Nội thất` | string | `"Full nội thất"`, `"Đồ Cơ bản"`, `"Nhà Nguyên Bản"` |
| `Giá thuê` | number (VNĐ/tháng) | `6800000` |
| `Ngày vào ở` | string `dd/mm/yyyy` hoặc chữ | `"01/08/2026"`, `"Luôn"` |
| `Ảnh đại diện` | URL Google Drive (`?id=...`) | `"https://drive.google.com/thumbnail?id=..."` |
| `Danh sách ảnh` | nhiều URL Drive, nối bằng `\n` | — |
| `Video` | string, thường rỗng | — |
| `Ngày thêm vào hệ thống` | string, thường rỗng | — |
| `Hiển thị trên Web` | string boolean-like | `"Có"` / `"Không"` / `"TRUE"` |

**Không có field phân khu.** Phân khu được **suy luận** từ tiền tố mã tòa,
qua hàm `phan_khu_tu_toa()` trong `scripts/sinh-danh-sach-anh.py` (dùng lại
ở `sinh-trang-toa.py` qua `importlib`, tránh hai bản ánh xạ lệch nhau):

```
MAS*/WEST* -> Masteri   SA*  -> Sakura     GS* -> Miami
TC*        -> Canopy    TK*  -> Tonkin     I\d -> Imperia
A\d        -> Lumiere   V\d  -> Victoria   S\d -> Sapphire   G\d -> Sola Park
```

Đã chạy thử ánh xạ này trên toàn bộ `data.json` (chỉ căn `Hiển thị trên Web`
= có): **40 tòa có ít nhất 1 căn trống, không có mã tòa nào rơi ra ngoài
bảng** (0 unmapped). Đây là tín hiệu tốt cho Phase 1 — không cần bảng "chưa
nhận diện được" lớn.

## 3. Cơ chế sinh trang — **KẾT LUẬN QUAN TRỌNG NHẤT**

Repo dùng **cả ba cơ chế**, tuỳ loại trang:

1. **27 trang danh mục cũ** (`/studio/`, `/sapphire/`, 12 trang giá/nội
   thất...): HTML tĩnh viết/sinh sẵn, nhưng **listing căn render bằng JS
   phía client** — `dong-bo-can.js` đọc `data.json` lúc chạy trong trình
   duyệt rồi dựng `<section class="luoi">`. Thẻ SEO (`<title>`, meta
   description, số liệu trong JSON-LD `ItemList`) được **Node script**
   (`cap-nhat-so-can.mjs`, `dung-lai-trang-danh-muc.py`) ghi thẳng vào file
   HTML qua GitHub Actions vì JS chạy trong trình duyệt không kịp cho
   Googlebot thấy số mới nhất.

2. **Trang cấp tòa** (`s4-01-vinhomes-smart-city/`, đúng 1 trang hiện có):
   **build script Python** (`scripts/sinh-trang-toa.py`) sinh **toàn bộ**
   file `index.html` từ `data.json` mỗi lần chạy — kể cả danh sách thẻ căn
   nằm thẳng trong HTML, KHÔNG qua `dong-bo-can.js`. Đây chính xác là loại
   trang mà `SEOEXPANSIONPLAN.md` Phase 2 muốn nhân bản. **Script này đã tồn
   tại và đã bao gồm gần như toàn bộ yêu cầu của Phase 2** (xem mục 7).

3. **27 trang riêng từng căn hộ** (`can-ho/<slug>/index.html`): build script
   Python khác (`scripts/sinh-trang-can.py`), cùng kiểu với (2), có sổ đăng
   ký slug vĩnh viễn `can-ho/danh-sach-trang.json` để URL không bao giờ đổi
   dù căn hết hạn hiển thị.

**Không có bước build tổng ở tầng deploy.** Site là GitHub Pages phục vụ
thẳng file tĩnh trong repo (xác nhận qua file `CNAME` ở gốc, domain
`timthuesmartcity.com`, không có workflow deploy riêng — 2 workflow hiện có
đều là "sinh & commit file tĩnh", không phải "build rồi deploy"). Đẩy commit
lên nhánh mặc định thì GitHub Pages tự phục vụ ngay.

## 4. GA4, JSON-LD, canonical, đa ngôn ngữ

- **GA4**: `G-VF9KHC5TWD`, snippet giống hệt nhau (`gtag.js` async + inline
  config) được nhúng cứng trong `<head>` của **mọi** trang tĩnh, kể cả trang
  do script sinh (`sinh-trang-toa.py` có sẵn đúng snippet này ở dòng
  400-402). Trang chủ còn có thêm khối GA4 trong `dong-bo-can.js` cho các
  sự kiện tương tác — README liệt kê khối này vào danh sách "không được
  sửa".
- **JSON-LD**: dùng `@graph` gộp nhiều `@type` trong một `<script
  type="application/ld+json">`: `BreadcrumbList` + `ItemList` (listing căn)
  + `FAQPage` (nếu trang có khối FAQ hiển thị thật — bổ sung ở đợt audit
  trước, xem mục 8). Trang S4.01 hiện **chỉ có `BreadcrumbList`**, chưa có
  `ItemList`/`FAQPage` — vì trang này sinh trước và tách biệt khỏi luồng 25
  trang danh mục kia. Phase 2 cần quyết định có bổ sung `ItemList` cho
  listing 6 căn của S4.01/các tòa mới hay không (nhất quán với 27 trang kia)
  — đây là điểm cần làm rõ ở Phase 1/2, không tự quyết ở đây.
- **Canonical**: mọi trang tĩnh tự khai `self-canonical`. Trang chủ
  `index.html` canonical **luôn trỏ về `/`** bất kể query string
  (`?loai=studio&gia=...`) — đã xác nhận đúng như tài liệu mô tả, rủi ro
  trùng lặp do bộ lọc **đã được xử lý từ trước**, không phải việc mới.
- **Đa ngôn ngữ VI/EN/KO — KHÁC với giả định trong `SEOEXPANSIONPLAN.md`**:
  `assets/ngon-ngu.js` (667 dòng) là cơ chế **dịch hiển thị bằng JS, chỉ áp
  dụng cho `index.html`** (dropdown chọn VI/EN/한, nhớ lựa chọn bằng
  `localStorage` + `?lang=`). File tự ghi rõ trong comment đầu:
  *"ĐÂY LÀ TÍNH NĂNG TRẢI NGHIỆM NGƯỜI DÙNG, KHÔNG PHẢI TÍNH NĂNG SEO"* —
  không sinh `/en/`, `/ko/`, **không thêm `hreflang`**, không đổi
  `<title>`/meta/canonical/JSON-LD, không tự đoán ngôn ngữ theo trình
  duyệt (luôn mặc định VI để Googlebot thấy đúng bản tiếng Việt).
  Grep toàn repo xác nhận **0 chỗ dùng `hreflang`** và **không có thư mục
  `/en/` hay `/ko/`**. 27 trang phân khu/loại căn/tòa hiện tại **không có**
  bộ chuyển ngôn ngữ này — nó chỉ gắn ở trang chủ.
  → **Hệ quả cho Phase 2**: không cần sinh `hreflang` cho trang tòa mới
  (site hiện không dùng cơ chế đó ở bất kỳ đâu); nếu muốn trang tòa có cùng
  bộ chuyển ngôn ngữ với trang chủ thì đó là việc UX riêng, ngoài phạm vi
  "tương thích cơ chế hiện tại" mà tài liệu gốc giả định — cần hỏi lại khi
  tới Phase 2 nếu muốn mở rộng.

  **✅ ĐÃ DUYỆT (phản hồi Phase 0, 24/08/2026)**: không dùng `hreflang` cho
  trang tòa. Lý do được xác nhận: `hreflang` chỉ có ý nghĩa khi mỗi ngôn ngữ
  có một URL riêng để trỏ chéo sang nhau; ở đây bản dịch VI/EN/KO là dịch
  bằng JS ngay trên cùng một URL (`ngon-ngu.js`), không có URL riêng cho
  từng ngôn ngữ, nên không có gì để `hreflang` trỏ tới — thêm thẻ này vào
  sẽ là khai báo sai, không phải khai báo thiếu. Kết luận này áp dụng cho
  toàn bộ 33 trang tòa ở Phase 2, không cần hỏi lại.

## 5. Sitemap

- **`sitemap.xml`**: viết/cập nhật một phần bằng tay, một phần bằng
  `scripts/cap-nhat-sitemap.mjs` (chỉ đổi `<lastmod>` theo ngày commit git
  thật của từng file — có bảo vệ chống shallow-clone). **43 `<url>`**, không
  phải 51 như tài liệu gốc ước tính — chênh lệch không lớn, không ảnh hưởng
  kết luận (trang tòa vẫn chỉ có 1/43).
- **`sitemap-can-ho.xml`**: **61 `<url>`**, sinh bởi `scripts/sinh-trang-can.py`
  cho 27 trang căn hộ (+trang mục lục `/can-ho/`). **Tồn tại thật, không phải
  404** — khác cảnh báo "chưa xác minh" trong tài liệu gốc.
- **`sitemap-images.xml`**: **76 `<url>`** (thực ra >200 khối `<image:image>`
  lồng trong đó), sinh bởi `scripts/tai-anh-can-ho.py`. **Tồn tại thật,
  không phải 404.**
- Cả ba đều được khai đúng trong `robots.txt`. **Kết luận Phase 0, mục
  7 của tài liệu gốc: cả hai nghi vấn 404 đều SAI — không cần sửa
  `robots.txt` hay tạo file mới ở bước này.**

## 6. Pipeline deploy & CI hiện có

| Workflow | Lịch | Việc làm | Có commit trực tiếp vào nhánh không |
|---|---|---|---|
| `cap-nhat-so-can.yml` | `0 1,9,17 * * *` (3 lần/ngày, giờ VN 08:00/16:00/00:00) | `sinh-trang-toa.py` → `dung-lai-trang-danh-muc.py` → `dung-lai-trang-chu.py` → `sinh-trang-can.py` → `cap-nhat-so-can.mjs` → `cap-nhat-sitemap.mjs` → commit + push (rebase, retry 4 lần) | Có — push thẳng `HEAD:$NHANH`, không qua PR |
| `tai-anh-can-ho.yml` | chỉ chạy tay | `sinh-danh-sach-anh.py` → `tai-anh-can-ho.py` → `thay-anh-trong-html.py` → commit | Có |

⚠️ **Rủi ro cần lưu ý cho các giai đoạn sau**: `cap-nhat-so-can.yml` chạy
theo lịch trên **nhánh mà nó được kích hoạt** — nếu nhánh làm việc SEO này
tồn tại đủ lâu và workflow được phép chạy trên nhánh đó, nó có thể tự động
ghi đè `s4-01-vinhomes-smart-city/` (và mọi trang tòa mới ta thêm vào biến
`CAC_TOA`) *trước khi* PR được duyệt. Không phải lỗi cần sửa ngay, nhưng
Phase 1/2 nên kiểm tra workflow chỉ chạy trên nhánh mặc định (mục
`on.schedule` không giới hạn nhánh theo YAML chuẩn của GitHub — cron chỉ
chạy trên nhánh mặc định của repo theo hành vi mặc định của GitHub Actions,
nên rủi ro thực tế thấp, nhưng `workflow_dispatch` thì ai cũng chạy được
trên bất kỳ nhánh nào).

## 7. Trang mẫu `s4-01-vinhomes-smart-city/` — soi kỹ

Sinh bởi `scripts/sinh-trang-toa.py`, cấu hình tòa khai trong dict `CAC_TOA`
(hiện chỉ có 1 dòng cho S4.01). Đối chiếu với checklist "Cấu trúc bắt buộc"
ở Phase 2 của `SEOEXPANSIONPLAN.md`:

| Yêu cầu Phase 2 | Trạng thái trong `sinh-trang-toa.py` |
|---|---|
| `<title>` động, mẫu "Cho thuê căn hộ tòa {MÃ} ... – {N} căn" | ✅ đã đúng mẫu |
| `<meta description>` động, số căn+giá+ngày | ✅ |
| canonical self | ✅ |
| hreflang | Site không dùng hreflang ở đâu cả (mục 4) — N/A |
| `<h1>` chứa mã tòa | ✅ |
| breadcrumb hiển thị | ✅ `Trang chủ › {Phân khu} › Tòa {Mã}` |
| khối số liệu thật (số căn, breakdown, giá, %full nội thất, ngày) | ✅ đầy đủ |
| danh sách căn thật (ảnh, mã, diện tích, giá, Zalo) | ✅ dùng đúng class `.the`/`.luoi` của `assets/v3.css`, không thêm CSS |
| khối liên kết nội bộ | ⚠️ **một phần**: có link ngược phân khu + link loại căn có thật trong tòa; **CHƯA có** link ngang tới 3–5 tòa khác cùng phân khu (yêu cầu Phase 3-B) |
| JSON-LD: giữ schema hiện có + `BreadcrumbList` | ⚠️ mới chỉ có `BreadcrumbList`, chưa có `ItemList` như 25 trang danh mục kia (xem mục 4) |
| GA4 | ✅ |
| ngưỡng chống thin content (≥3 căn) | ✅ đã có `NGUONG_TOI_THIEU = 3`, đúng số Phase 2 yêu cầu |
| xử lý tòa hết căn (không xoá, không noindex) | ✅ script đã có logic: dưới ngưỡng thì **giữ nguyên file cũ**, không ghi đè, không xoá — khớp yêu cầu "hiển thị thông báo hết căn + link tòa khác" **về phần không xoá**, nhưng **chưa render** khối thông báo "Tòa X hiện chưa có căn trống, xem tòa khác..." — hiện tại chỉ là im lặng giữ nguyên nội dung cũ |
| chống trùng lặp nội dung (≥40% chữ từ dữ liệu thật) | ✅ đoạn "Tòa {X} đang có gì" hoàn toàn lắp ráp từ số liệu tính toán (câu liệt kê loại căn, khoảng giá, khoảng diện tích, tỷ lệ nội thất) — không có đoạn văn mẫu cố định nào dài |

**Kết luận mục 7**: kiến trúc kỹ thuật cho Phase 2 **đã có sẵn ~85%**. Việc
còn lại chủ yếu là (a) mở rộng `CAC_TOA` từ 1 dòng lên N dòng theo danh sách
tòa đạt ngưỡng (Phase 1), (b) thêm khối "link ngang 3-5 tòa cùng phân khu"
và khối "hết căn thì gợi ý tòa khác" vào `dung_trang()`, (c) quyết định có
thêm `ItemList` hay không, (d) cập nhật `sitemap.xml` cho các tòa mới —
**không phải viết lại từ đầu**.

Chạy thử `data.json` hiện tại qua đúng logic chuẩn hoá mã tòa +
`phan_khu_tu_toa()`: **33 tòa đạt ngưỡng ≥3 căn** trong tổng 40 tòa có căn
hiển thị (7 tòa còn lại 1–2 căn, đúng diện "không sinh trang riêng" của
Phase 2). Toàn bộ 33 tòa đều map được về 1 trong 8 phân khu đã có trang —
không phát sinh phân khu lạ. Danh sách đầy đủ (mã tòa chuẩn hoá, số căn,
phân khu) đã tính sẵn, sẽ đưa chính thức vào `data/buildings.json` ở Phase 1.

## 8. Trạng thái Git / nhánh & audit SEO trước đó

- Nhánh hệ thống chỉ định cho phiên này: **`claude/new-session-uiz59k`**
  (đã tồn tại từ trước, đang là nhánh hiện tại, working tree sạch). Tài liệu
  gốc yêu cầu nhánh `seo/building-pages-expansion` — **không tạo nhánh đó**
  vì hướng dẫn hệ thống của phiên làm việc này chỉ định rõ nhánh phải dùng
  là `claude/new-session-uiz59k` và không được lệch. Nêu ở đây để người
  review biết và xác nhận có chấp nhận không trước khi sang Phase 1.
- Repo đã có **một đợt audit/triển khai SEO trước đó** (không liên quan
  trang tòa): `SEO-AUDIT.md`, `SEO-CONTENT-AUDIT.md` (Phase 1 cũ),
  `SEO-CONTENT-PLAN.md` (Phase 2 cũ — pillar phân khu còn thiếu, cẩm nang,
  bài so sánh, cluster "loại×phân khu" ngưỡng ≥10 căn, cluster nội thất),
  `SEO-IMPLEMENTATION-REPORT.md` (đã triển khai P0: thêm `FAQPage` cho 25
  trang danh mục). **Không trùng phạm vi** với `SEOEXPANSIONPLAN.md` (tài
  liệu này tập trung riêng cấp **tòa**, chưa từng được đề cập trong
  `SEO-CONTENT-PLAN.md`) — hai kế hoạch bổ sung cho nhau, không xung đột.
  Cần lưu ý khi Phase 5 (nội dung phân khu) tới: `SEO-CONTENT-PLAN.md` mục
  2.1 đã có sẵn danh sách 5 phân khu cần viết pillar mới, tránh làm trùng.

## 9. Danh sách rủi ro phát hiện được

1. **Xung đột ghi file với workflow tự động** (mục 6): `cap-nhat-so-can.yml`
   chạy 3 lần/ngày và tự commit đè lên đúng những file Phase 2 sẽ sửa
   (`CAC_TOA` trong `sinh-trang-toa.py` sẽ sinh ra các trang tòa mới, và nếu
   nhánh SEO tồn tại song song lâu, cần rebase thường xuyên trước khi
   merge). Không nghiêm trọng nếu merge nhanh, nhưng phải tính đến.
2. **`ItemList` thiếu ở trang tòa** (mục 4, 7): 25 trang danh mục khác đều
   có `ItemList` trong JSON-LD, trang tòa S4.01 thì không — cần quyết định ở
   Phase 1/2 để nhất quán, tránh vừa làm 33 trang mới vừa lệch chuẩn.
3. **Giả định hreflang/đa ngôn ngữ trong tài liệu gốc không khớp thực tế**
   (mục 4): đã làm rõ, không phải rủi ro chặn nhưng cần tài liệu gốc/người
   duyệt xác nhận lại yêu cầu "tương thích cơ chế hiện tại" nghĩa là gì cho
   trang tòa (khuyến nghị: không cần hreflang, có thể để trang tòa dùng
   được nút chuyển ngôn ngữ như trang chủ sau, không bắt buộc ở Phase 2).
4. **Trang tòa hết căn hiện chưa có UI báo "hết căn"** (mục 7) — script chỉ
   lặng lẽ giữ file cũ. Đúng yêu cầu "không xoá/không noindex" nhưng **chưa
   đạt** yêu cầu UX "hiển thị thông báo + link tòa khác" của Phase 2. Cần
   thêm khi mở rộng script.
5. **`can-ho/danh-sach-trang.json` chỉ có 27/1000 dòng** (cơ chế riêng biệt
   cho trang từng căn, ngưỡng ≥8 ảnh + mã `^CT\.`) — không liên quan trực
   tiếp Phase 2 nhưng cùng dùng `data.json`, cần tránh nhầm lẫn hai cơ chế
   sinh trang khi mở rộng `sinh-trang-toa.py`.
6. **Dữ liệu "Tòa" trong `data.json` không chuẩn hoá** (ví dụ `MasA` vs
   `MASA`) — `chuan_ma_toa()` đã xử lý tốt (test thực tế 0 tòa unmapped),
   nhưng Phase 1 vẫn cần xuất bảng ánh xạ biến thể để người review xác nhận
   theo đúng yêu cầu tài liệu gốc, đặc biệt với các mã 1 chữ cái dễ nhầm
   (`I` Imperia vs `A` Lumiere vs `S` Sapphire — thứ tự xét trong code đã
   đúng, tiền tố dài đứng trước tiền tố ngắn).
7. **Không có file `data/buildings.json` hay `docs/buildings-gap.md`** —
   bình thường, đây là sản phẩm của Phase 1, chưa làm ở Phase 0.

---

### 🛑 Checkpoint

Đã dừng đúng theo yêu cầu Phase 0. Chờ duyệt các điểm mục 8 (nhánh làm
việc) và mục 9.2–9.3 (ItemList, hreflang) trước khi sang Phase 1.

**✅ PHASE 0 ĐÃ DUYỆT (24/08/2026)** — xác nhận cả 4 điểm: (1) không dùng
hreflang cho trang tòa, xem mục 4; (2) giữ nhánh `claude/new-session-uiz59k`,
mọi thay đổi qua PR, không push thẳng `main`; (3) sẽ bổ sung `ItemList`
JSON-LD + UI "tòa hết căn" ở Phase 2; (4) mở rộng
`scripts/sinh-trang-toa.py` thay vì viết script mới. Xem tiếp
`docs/phase1-bao-cao.md` cho Phase 1.

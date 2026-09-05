# timthuesmartcity.com

Trang cho thuê căn hộ Vinhomes Smart City. Toàn bộ là HTML tĩnh chạy trên GitHub Pages — không framework, không bundler, không build step. Danh sách căn nằm trong `data.json`, được các script trong `scripts/` và `dong-bo-can.js` đọc để dựng lưới căn cùng thẻ SEO cho 25 trang danh mục.

## Luồng dữ liệu

```
Google Sheets            Apps Script              data.json              GitHub Pages
(chủ nhà nhập căn)  ──▶  (đẩy ~30 phút/lần)  ──▶  (ở gốc repo)  ──▶  (trình duyệt khách)
                                                        │
                                                        ├──▶ dong-bo-can.js  — dựng lại lưới căn lúc chạy
                                                        └──▶ scripts/*       — sửa thẻ SEO tĩnh qua Actions
```

Google Sheets là nguồn duy nhất. Apps Script ghi đè `data.json` khoảng 30 phút một lần và commit thẳng vào `main`. Trong trình duyệt, `dong-bo-can.js` đọc lại `data.json` để dựng lưới căn, nên nội dung trong `<body>` luôn khớp Sheet. Riêng `<title>`, `og:title` và `meta description` thì trình duyệt sửa không kịp cho Googlebot, nên phải do GitHub Actions ghi thẳng vào file HTML.

## Script trong `scripts/`

| Script | Việc nó làm |
|---|---|
| `cap-nhat-so-can.mjs` | Đếm căn theo bộ lọc của từng trang rồi ghi số căn, giá sàn và ngày cập nhật vào `<title>` / `og:title` / `meta description`. |
| `cap-nhat-sitemap.mjs` | Cập nhật `<lastmod>` trong `sitemap.xml` theo ngày commit thật của `data.json` (trang động) hoặc của chính file đó (trang tĩnh). |
| `sinh-trang-toa.py` | Dựng lại trang danh mục theo tòa (`s4-01-vinhomes-smart-city/`) từ `data.json` mỗi lần chạy nên không bao giờ lệch dữ liệu. |
| `sinh-trang-can.py` | Sinh trang riêng cho từng căn. Căn thiếu Tòa hoặc Diện tích **không** được cấp URL (tránh slug rác `--0m2`); trang căn đã có khách mang `robots: noindex,follow` và không vào sitemap. |
| `sinh-danh-sach-anh.py` | Dựng `scripts/danh-sach-anh.json` từ `data.json`, liệt kê căn đang hiển thị và có ảnh đại diện. |
| `tai-anh-can-ho.py` | Tải ảnh đại diện từ Google Drive về `anh-can-ho/` dưới dạng WebP, ghi `anh-map.json` và `sitemap-images.xml`. |
| `thay-anh-trong-html.py` | Đọc `anh-map.json` rồi đổi `src` của các thẻ `<img>` tĩnh từ URL Drive sang đường dẫn ảnh trong repo. |
| `ap-giao-dien-v3.py` | Áp giao diện v3 lên HTML tĩnh: thay khối `<style>` nội tuyến bằng link `/assets/v3.css`, chuyển nhãn nội thất thành huy hiệu trên ảnh. |
| `kiem-tra-seo-snapshot.py` | Chụp lại title, meta, heading, JSON-LD, GA4, alt ảnh của mọi trang để so sánh trước và sau khi đổi giao diện. |
| `kiem-tra-lien-ket.py` | Đếm số link vào/ra của từng trang theo ngưỡng đặt sẵn và báo mọi link nội bộ trỏ tới trang không tồn tại. |

Mọi script có ghi file đều nhận cờ `--thu` để xem trước mà không sửa gì, trừ `tai-anh-can-ho.py`. Hai script `kiem-tra-*` chỉ đọc và in kết quả.

## Workflow trong `.github/workflows/`

| Workflow | Lịch chạy | Việc nó làm |
|---|---|---|
| `cap-nhat-so-can.yml` | `0 19 * * *` — mỗi ngày một lần, 02:00 giờ Việt Nam | Chạy `sinh-trang-toa.py`, `cap-nhat-so-can.mjs`, `cap-nhat-sitemap.mjs` rồi commit HTML và `sitemap.xml`. |
| `tai-anh-can-ho.yml` | Không có lịch — chỉ chạy tay từ tab Actions | Chạy `sinh-danh-sach-anh.py`, `tai-anh-can-ho.py`, `thay-anh-trong-html.py` rồi commit ảnh và `sitemap-images.xml`. |

Workflow ảnh phải chạy trên Actions vì môi trường phát triển bị chặn `drive.google.com`.

## Video trang chi tiết

`scripts/dong-bo-video.py` lấy danh sách video công khai từ bảng hàng, đối chiếu
với căn đang hiển thị trong `data.json`, rồi tạo MP4 H.264/AAC có `faststart`
trong `video-can-ho/`. Script chỉ chuyển đổi video mới; không ghi `data.json`.
Workflow `dong-bo-video.yml` cập nhật manifest và yêu cầu GitHub Pages build sau
khi push để video mới xuất hiện trên website.

Player dùng chung cho mobile/desktop, ưu tiên MP4 cùng domain. Video chưa xử lý
dùng một Drive preview riêng; không chạy thêm player ẩn hoặc tự đổi nguồn khi
tải chậm. Giới hạn mỗi MP4 30 MiB, toàn kho 450 MiB; video không xử lý được vẫn
có đường dẫn gốc. Nút chọn video hỗ trợ căn có nhiều clip.

Căn mới chỉ có video không cần sửa mã nguồn hoặc chạy lệnh riêng: sau khi căn
được bật hiển thị trong bảng hàng (đủ mã căn, tòa và diện tích để cấp URL),
workflow tự nhận video sau lượt đồng bộ dữ liệu và kiểm tra bổ sung mỗi 30 phút.
Mỗi MP4 có ảnh bìa WebP lấy từ một khung hình thật; trang chủ, danh mục và trang
chi tiết dùng ảnh này khi căn không có ảnh. Ảnh bìa video không được tính thành
ảnh chụp trong album. Cùng lượt chạy tự sinh/cập nhật URL và đưa lên Pages.
Video Drive phải được chia sẻ công khai như nguồn video hiện có.

Kiểm tra vòng đời player: cài `jsdom` trong thư mục tạm, đặt
`CT_VIDEO_TEST_JSDOM` trỏ tới package đó rồi chạy
`node --test scripts/kiem-tra-video.cjs`.

## Header và cache — file `_headers`

`_headers` khai báo 5 security header còn thiếu (audit 02/09/2026 chấm
securityheaders.com điểm D) và cache 1 năm cho ảnh/asset. **GitHub Pages không
đọc file này** — nó nằm sẵn để lần chuyển sang Cloudflare Pages hoặc Netlify là
có header ngay, URL không đổi. Đang ở GitHub Pages thì phải đặt Cloudflare ở
trước và chép đúng các giá trị đó vào Transform Rules.

CSP đang để `Content-Security-Policy-Report-Only`. Chạy một tuần, xem console
không còn cảnh báo thì mới đổi tên thành `Content-Security-Policy`.

## Không được sửa

| File / khối | Lý do |
|---|---|
| `data.json` | Apps Script ghi đè khoảng 30 phút một lần. Mọi sửa tay đều bị mất ở lần đẩy kế tiếp. Sai dữ liệu thì sửa trong Google Sheet. |
| `assets/v3.css` | Một file dùng chung cho toàn site. CSS desktop mới chỉ được đặt trong khối `@media (min-width:1024px)`. |
| Khối schema JSON-LD trong `dong-bo-can.js` | Google đã index theo cấu trúc này; đổi là mất rich result. |
| Khối GA4 trong `dong-bo-can.js` | Đụng vào là đứt số liệu, không có cách dựng lại phần đã hụt. |

## Thêm một trang danh mục mới

Trang danh mục là HTML tĩnh tự khai điều kiện lọc của mình; `dong-bo-can.js` đọc khai báo đó rồi dựng lưới căn. Không cần đăng ký trang ở đâu khác.

1. Tạo thư mục mới kèm `index.html`, chép từ một trang danh mục đang có (ví dụ `2pn-full-do/`).
2. Sửa `<title>`, `meta description`, `canonical`, `<h1>` và khối JSON-LD cho khớp nội dung trang mới.
3. Khai bộ lọc ngay trước thẻ `<script src="/dong-bo-can.js" defer>`:

```html
<script type="application/json" id="bo-loc-trang">{"loai": "2 Ngủ +", "giaTren": 12000000, "giaMax": 15000000}</script>
```

Các khoá dùng được:

| Khoá | Ý nghĩa | Ví dụ |
|---|---|---|
| `loai` | Loại căn, khớp đúng cột "Loại" trong Sheet | `"Studio"`, `"1 Ngủ +"`, `"3 Ngủ"` |
| `phanKhu` | Tên phân khu, suy ra từ mã tòa | `"Sapphire"`, `"Masteri"` |
| `noiThat` | Khớp đúng cột "Nội thất" | `"Full nội thất"` |
| `giaTren` | Chỉ lấy căn có giá **lớn hơn** mức này | `10000000` |
| `giaMax` | Chỉ lấy căn có giá **nhỏ hơn hoặc bằng** mức này | `12000000` |

Bỏ trống khoá nào thì khoá đó không lọc. Nhiều khoá đi cùng nhau là điều kiện **và**.

4. Thêm URL mới vào `sitemap.xml`.
5. Chạy `node scripts/cap-nhat-so-can.mjs --thu` để kiểm tra trang mới được nhận diện và số căn đếm ra đúng, rồi bỏ `--thu` để ghi thật.

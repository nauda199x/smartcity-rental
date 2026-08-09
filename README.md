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

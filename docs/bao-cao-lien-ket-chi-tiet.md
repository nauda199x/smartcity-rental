# BÁO CÁO — nối 26 trang danh mục vào 60 trang chi tiết

> Thực hiện theo `LIEN-KET-TRANG-CHI-TIET.md`. TASK 1–3 (P0) đã xong và kiểm
> thử tại chỗ. TASK 4 (P1) **chưa làm** — tài liệu gốc yêu cầu làm sau khi
> TASK 1–3 đã lên live và xác minh xong, xem mục "Việc chưa làm" cuối báo cáo.

---

## 1. Bốn con số — trước và sau

Đo lại tại thời điểm chạy (25/08/2026), bằng đúng cách đếm nêu ở mục 1 của
tài liệu gốc (`article.the` trên 26 trang danh mục).

| Chỉ số | Trước (BƯỚC 0) | Sau khi chạy `noi-lien-ket-chi-tiet.py` |
|---|---|---|
| Tổng thẻ căn tĩnh (`article.the`) | 765 | 765 (không đổi số thẻ, chỉ đổi nội dung `h3.ten`) |
| Thẻ có `data-ma-noi-bo` khớp trang chi tiết | 193 | 193 |
| Liên kết `href="/can-ho/..."` trên 26 trang | 0 | **193** |
| Trang chi tiết được trỏ tới (≥1 liên kết) | 60/60 (chỉ tính hiện diện trên trang, chưa có link) | **60/60 có link thật** |

Con số đo lại khớp chính xác con số 25/08/2026 nêu trong tài liệu gốc — không
có lệch dữ liệu giữa thời điểm viết yêu cầu và thời điểm chạy.

## 2. Script sinh `section.luoi` — khoảng trống trong README.md

**`scripts/dung-lai-trang-danh-muc.py`** dựng lại 6 khối của 25 trang danh
mục (`bo-loc-trang`) từ `data.json`, trong đó có toàn bộ `article.the` trong
`section.luoi`. Script này dùng lại `dung_the_can()` của `sinh-trang-toa.py`
qua `importlib` để markup không lệch giữa hai nơi.

Riêng trang tòa `s4-01-vinhomes-smart-city/` (không có `bo-loc-trang`) do
chính **`scripts/sinh-trang-toa.py`** sinh trực tiếp — trang này không nạp
`dong-bo-can.js`, hoàn toàn tĩnh.

Cả hai script được gọi trong `.github/workflows/cap-nhat-so-can.yml`
("Sinh trang theo tòa" rồi "Dựng lại thân trang danh mục"), chạy 3 lần/ngày
(`0 1,9,17 * * *`). **`README.md` mục "Script trong scripts/" không liệt kê
`dung-lai-trang-danh-muc.py`** — đây là khoảng trống tài liệu cần bổ sung
(nằm ngoài phạm vi sửa `README.md` của task này, chỉ ghi nhận lại).

## 3. Trang chi tiết không nhận được liên kết nào

Không có. Cả 60/60 trang chi tiết trong `can-ho/danh-sach-trang.json` đều
nhận được ít nhất một liên kết sau khi chạy script (xác nhận bằng đếm slug
duy nhất trong đầu ra `noi-lien-ket-chi-tiet.py`: "Trang chi tiết được trỏ
tới: 60/60").

## 4. Kết quả từng tiêu chí nghiệm thu

**HTML tĩnh**

1. ✅ Số liên kết mới = 193 = đúng số thẻ khớp bảng tra tại thời điểm chạy.
2. ✅ Toàn bộ 60 slug trong bảng tra đều có thư mục `can-ho/{slug}/index.html`
   thật trong repo (kiểm bằng `os.path.isdir`, 0 slug thiếu thư mục).
3. ✅ `python3 scripts/kiem-tra-lien-ket.py` → `PASS`, 0 link gãy, 0 orphan.
   Số cảnh báo (WARN, không fail) còn **giảm** từ 8 xuống 5 sau khi chạy —
   ba trang chi tiết trước đó có inbound thấp bất thường
   (`cho-thue-can-ho-studio-tonkin-25m2-ct-stu-715`,
   `cho-thue-can-ho-2-ngu-canopy-75m2-ct-2n-270`,
   `cho-thue-can-ho-2-ngu-canopy-61m2-ct-2n2-209`) nay đã hết cảnh báo nhờ
   liên kết mới. Không có cảnh báo mới nào sinh ra.
4. ✅ Chạy script lần hai: `Liên kết đã chèn: 0`, `Bỏ qua (đã có): 193`,
   `Đã ghi 0 trang`. `git diff --stat` không đổi so với lần chạy đầu.
5. ✅ `git diff --stat` sau TASK 1–3 chỉ chạm: 25 file `*/index.html` trong
   thư mục danh mục + `s4-01-vinhomes-smart-city/index.html` (do script mới),
   `dong-bo-can.js` (TASK 1), `.github/workflows/cap-nhat-so-can.yml`
   (TASK 3), và file mới `scripts/noi-lien-ket-chi-tiet.py`. Không đụng
   `data.json`, `assets/v3.css`, `index.html` gốc.

**Sau khi JS chạy** (kiểm bằng Chromium headless, phục vụ repo qua
`python -m http.server`, trang `/2pn/`)

6. ✅ Số `a[href^="/can-ho/"]` trong DOM sau khi lưới dựng xong = 15, đúng
   bằng số liên kết trong HTML tĩnh của `2pn/index.html` (đếm bằng grep =
   15). Số thẻ tổng trong DOM (89) cao hơn số thẻ tĩnh (86) — chênh lệch này
   là hành vi có chủ ý sẵn có của `dong-bo-can.js` (luôn đồng bộ lại với
   `data.json` mới nhất lúc chạy), không phải do thay đổi của task này.
7. ✅ Bấm tiêu đề thẻ có liên kết → điều hướng sang đúng
   `/can-ho/{slug}/`, không mở album ảnh (xác nhận `ev.target.closest("a")`
   ở trình xử lý click vẫn chặn đúng như trước — TASK 1.3 không cần sửa gì
   ở đó, đã kiểm chứng chứ không chỉ tin vào mô tả).
8. ✅ Bấm ảnh của cùng thẻ đó → mở album ảnh (overlay `.dbc-nen` hiện ra),
   URL không đổi.
9. ✅ Nút "Nhắn Zalo" giữ nguyên `href="https://zalo.me/0977923284"`, không
   bị thẻ `<a>` mới can thiệp.
10. ✅ Đổi tên tạm `can-ho/danh-sach-trang.json` để giả lập 404, tải lại
    `/2pn/`: lưới vẫn dựng đủ 89 thẻ, chỉ mất liên kết (0 thẻ `a[href^="/can-ho/"]`
    trong DOM). Không có lỗi JS (không có `pageerror`/exception nào từ
    `dong-bo-can.js`; log console chỉ có thông báo tải tài nguyên 404, đúng
    là hệ quả của việc tự giả lập lỗi, không phải exception trong code).
    File được phục hồi ngay sau kiểm thử, xác nhận `git status` sạch.

**Không hồi quy**

11. ✅ `python3 scripts/kiem-tra-seo-snapshot.py` chụp trước (qua `git stash`)
    và sau: **"KHÔNG CÓ KHÁC BIỆT"** — title, meta description, h1/h2/h3,
    JSON-LD, GA4, alt ảnh giữ nguyên 100% trên cả 108 trang. Khác biệt duy
    nhất trong `git diff` là các thẻ `<a>` mới quanh `h3.ten`.

## 5. Việc chưa làm — TASK 4 (P1)

Tài liệu gốc yêu cầu làm TASK 4 (bổ sung `ItemList` cho `sinh-trang-toa.py`)
**"sau khi TASK 1–3 đã lên live và xác minh xong"**. Vì TASK 1–3 trong phiên
làm việc này mới chỉ kiểm thử tại chỗ (local), chưa qua workflow thật trên
`main` và chưa được xác nhận trên site live, TASK 4 **chưa được thực hiện**
theo đúng trình tự tài liệu yêu cầu — tránh tự ý mở rộng phạm vi khi điều
kiện tiên quyết (lên live + xác minh) chưa hội đủ. Sẽ làm ở đợt kế tiếp sau
khi TASK 1–3 được xác nhận ổn định trên production.

## 6. File thay đổi

- `dong-bo-can.js` — TASK 1: nạp bảng tra `ma -> slug`, bọc `h3.ten` bằng `<a>`.
- `scripts/noi-lien-ket-chi-tiet.py` (mới) — TASK 2: chèn liên kết vào HTML tĩnh.
- `.github/workflows/cap-nhat-so-can.yml` — TASK 3: gắn script vào chuỗi chạy hằng ngày.
- 26 file `*/index.html` (25 trang danh mục + trang tòa S4.01) — kết quả chạy TASK 2.
- `docs/bao-cao-lien-ket-chi-tiet.md` (file này).

# NHIỆM VỤ: Di dời 197 ảnh đại diện từ Google Drive về repo (định dạng WebP)

## 1. Bối cảnh và mục tiêu

Toàn bộ ảnh căn hộ của `timthuesmartcity.com` đang host trên Google Drive. Google Drive chặn
crawler nên **không một ảnh nào được Google Images index** — mất hoàn toàn một kênh traffic.

Nhiệm vụ này di dời **197 ảnh đại diện của các căn đang hiển thị trên web** về repo, chuyển sang
WebP, đặt tên file mô tả tiếng Việt, và trỏ frontend sang ảnh mới.

Phạm vi lần này **chỉ gồm ảnh đại diện (ảnh bìa thẻ căn hộ)**. Ảnh trong album chi tiết
(`Danh sách ảnh`) và ảnh của các căn đã ẩn **không xử lý trong PR này**.

**Branch:** `claude/di-doi-anh-dai-dien`

---

## 2. Dữ liệu đầu vào

File `danh-sach-anh.json` (kèm theo trong thư mục này) chứa 197 bản ghi. Mỗi bản ghi:

```json
{
  "ma": "CT.Stu.545",
  "toa": "MasA",
  "phan_khu": "Masteri",
  "loai": "Studio",
  "dien_tich": 33,
  "drive_id": "178XfMYrwLGXdzEvUC8NEGVvVTc-yA1_C",
  "url_goc": "https://drive.google.com/thumbnail?id=178XfMYrwLGXdzEvUC8NEGVvVTc-yA1_C&sz=w1000",
  "ten_file": "cho-thue-can-ho-studio-masteri-33m2-ct-stu-545.webp"
}
```

Danh sách này đã được xác minh: 197 bản ghi, không trùng mã nội bộ, không trùng tên file,
không thiếu `drive_id`.

---

## 3. Các bước thực hiện

### Bước 1 — Tải và chuyển đổi ảnh

- Tạo thư mục `anh-can-ho/` ở gốc repo.
- Với mỗi bản ghi trong `danh-sach-anh.json`:
  - Tải ảnh từ `url_goc` (dạng `https://drive.google.com/thumbnail?id=<ID>&sz=w1000`).
  - Nếu URL đó trả về lỗi, thử lại với `https://drive.google.com/uc?export=download&id=<ID>`.
  - Chuyển sang **WebP**, chiều rộng tối đa **800px** (giữ nguyên tỉ lệ, không cắt xén),
    chất lượng **82**, dùng Pillow.
  - Lưu vào `anh-can-ho/<ten_file>`.
- Chèn độ trễ khoảng 0.3–0.5 giây giữa các lượt tải để tránh bị Drive chặn.
- **Ghi log rõ ràng**: bao nhiêu ảnh tải thành công, bao nhiêu lỗi, mã nội bộ nào lỗi.

**Rủi ro cần lường trước:** nếu môi trường không truy cập được `drive.google.com`,
hoặc quá nửa số ảnh tải lỗi, **dừng lại và báo cáo — không mở PR với dữ liệu thiếu.**

### Bước 2 — Sinh file ánh xạ

Tạo `anh-can-ho/anh-map.json`, chỉ chứa các ảnh **đã tải thành công**:

```json
{
  "178XfMYrwLGXdzEvUC8NEGVvVTc-yA1_C": "/anh-can-ho/cho-thue-can-ho-studio-masteri-33m2-ct-stu-545.webp"
}
```

Khóa là `drive_id`, giá trị là đường dẫn tuyệt đối tính từ gốc site.

### Bước 3 — Sửa `dong-bo-can.js` (file ở gốc repo)

Đây là phần cốt lõi. Ba thay đổi:

**3a.** Nạp `anh-map.json` một lần khi script khởi động, lưu vào biến trong module.
Nếu nạp lỗi thì để map rỗng — site vẫn phải chạy bình thường với ảnh Drive.

**3b.** Sửa hàm `driveUrlToViewUrl` (khoảng dòng 75): sau khi trích được ID từ URL,
tra ID đó trong map. Nếu có thì trả về đường dẫn ảnh repo; nếu không thì giữ nguyên
hành vi cũ (trả URL thumbnail Drive).

**3c.** Sửa hàm `anhBia` (khoảng dòng 172): hiện hàm này trả về URL thô từ `data.json`,
**không đi qua** `driveUrlToViewUrl`, nên ảnh bìa sẽ không được áp dụng map.
Cho giá trị trả về đi qua `driveUrlToViewUrl` trước khi trả.

Giữ nguyên toàn bộ phần còn lại của hàm, kể cả `onerror` của thẻ `<img>` (khoảng dòng 448).

### Bước 4 — Bổ sung sitemap ảnh

- Nếu repo đã có sitemap ảnh: bổ sung các URL ảnh mới vào.
- Nếu chưa có: tạo `sitemap-images.xml` theo chuẩn Google Image Sitemap, liệt kê 197 ảnh mới,
  và khai báo file này trong `robots.txt`.
- Kiểm tra `sitemap.xml` hiện có — nếu là sitemap index thì thêm tham chiếu tới sitemap ảnh.

---

## 4. Ràng buộc bắt buộc

- **KHÔNG chỉnh sửa `data.json`** dưới bất kỳ hình thức nào. File này do Apps Script quản lý.
- **KHÔNG chỉnh sửa `/assets/v3.css`.**
- **KHÔNG đụng vào khối GA4 `ganDoLuongChuyenDoi`** hay bất kỳ mã đo lường nào.
- **KHÔNG sửa schema JSON-LD** ở các trang HTML trong PR này.
- **KHÔNG tự merge PR.** Mở PR về `main` và dừng lại.
- Chỉ làm đúng nhiệm vụ trong tài liệu này, không gộp việc khác.

---

## 5. Kiểm tra trước khi mở PR

- [ ] Số file trong `anh-can-ho/` khớp số dòng trong `anh-map.json`
- [ ] Không có file nào 0 byte; mở thử vài file xác nhận ảnh hiển thị đúng, không méo tỉ lệ
- [ ] Tổng dung lượng thư mục `anh-can-ho/` báo cáo cụ thể (dự kiến 20–30MB)
- [ ] `dong-bo-can.js` chạy được khi `anh-map.json` bị lỗi/không tồn tại (fallback về Drive)
- [ ] `git status` xác nhận `data.json` **không** nằm trong danh sách thay đổi
- [ ] Tên file không chứa dấu cách, dấu tiếng Việt, hay hậu tố kiểu `(1)`, `(8)`

## 6. Nội dung mô tả PR

Ghi rõ: số ảnh tải thành công / thất bại, danh sách mã nội bộ lỗi (nếu có),
tổng dung lượng thêm vào repo, và các file đã sửa.

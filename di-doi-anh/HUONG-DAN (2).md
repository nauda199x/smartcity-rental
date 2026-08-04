# NHIỆM VỤ: Dựng GitHub Actions tự động di dời ảnh đại diện từ Google Drive về repo (WebP)

## 1. Bối cảnh

Ảnh căn hộ của `timthuesmartcity.com` đang host trên Google Drive. Drive chặn crawler nên
**không ảnh nào được Google Images index** — mất hoàn toàn một kênh traffic.

Lần thử trước đã thất bại vì môi trường Claude Code bị chính sách egress chặn `drive.google.com`
(gateway trả 403 cho CONNECT). Lần này **việc tải ảnh được chuyển sang GitHub Actions runner**,
nơi không bị chặn.

Vì workflow đằng nào cũng phải quét toàn bộ dữ liệu, script được viết ở dạng **tổng quát và
chạy lặp lại được** — không phải script chạy một lần. Lần chạy đầu sẽ xử lý 197 ảnh hiện có;
các lần sau chỉ xử lý phần chênh lệch.

**Branch:** `claude/actions-di-doi-anh` (nếu môi trường tự thêm hậu tố ngẫu nhiên thì giữ nguyên,
không sao)

---

## 2. Sản phẩm cần tạo

| File | Vai trò |
|---|---|
| `.github/workflows/dong-bo-anh.yml` | Workflow chạy bằng `workflow_dispatch` (bấm nút thủ công) |
| `scripts/dong_bo_anh.py` | Script Python làm toàn bộ việc tải, chuyển đổi, dọn dẹp |
| `anh-can-ho/` | Thư mục chứa ảnh WebP (do script sinh ra khi chạy) |
| `anh-can-ho/anh-map.json` | Ánh xạ `drive_id` → đường dẫn ảnh trong repo |
| `sitemap-images.xml` | Sitemap ảnh (do script sinh ra) |

Ngoài ra sửa `dong-bo-can.js` và `robots.txt` — chi tiết ở §5.

---

## 3. Logic của `scripts/dong_bo_anh.py`

### 3.1 Đọc dữ liệu

Đọc `data.json` ở gốc repo (**chỉ đọc, tuyệt đối không ghi**). Lọc các căn thỏa mãn **cả hai**:

- Trường `Hiển thị trên Web` sau khi `.strip().upper()` thuộc tập `('TRUE','1','CÓ','CO','X','YES')`
- Trường `Ảnh đại diện` không rỗng

### 3.2 Quy tắc đặt tên file — phải tuân thủ chính xác

Tên file: `cho-thue-can-ho-{loai}-{phan_khu}-{dien_tich}m2-{ma}.webp`

trong đó mỗi thành phần được slug hóa bằng hàm sau (thứ tự các bước quan trọng):

```python
def slug(s):
    s = str(s).replace('đ', 'd').replace('Đ', 'D')
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')
```

- `dien_tich` làm tròn về số nguyên rồi ghép hậu tố `m2`. Nếu rỗng thì bỏ qua thành phần này.
- `phan_khu` suy ra từ trường `Tòa`, **dùng đúng logic của hàm `tenPhanKhu` đã có sẵn trong
  `dong-bo-can.js`** (bỏ khoảng trắng và `._-`, viết hoa, rồi so tiền tố theo thứ tự):
  `MAS`/`WEST`→Masteri, `SA`→Sakura, `GS`→Miami, `TC`→Canopy, `TK`→Tonkin,
  `I` + chữ số→Imperia, `S`→Sapphire, `A`→Lumiere, `G`→Sola Park.
  **Thứ tự so sánh phải giữ nguyên** — tiền tố dài đứng trước, nếu đảo thứ tự sẽ sai
  (ví dụ `GS1` phải ra Miami chứ không phải Sola Park).

Ví dụ đúng: `cho-thue-can-ho-studio-masteri-33m2-ct-stu-545.webp`

### 3.3 Trích `drive_id`

Từ URL trong `Ảnh đại diện`, lấy ID theo một trong hai mẫu:
`/file/d/([^/]+)` hoặc `[?&]id=([^&]+)`. Bản ghi không trích được ID thì bỏ qua và ghi log.

### 3.4 Tải và chuyển đổi

Với mỗi căn hợp lệ:

- **Bỏ qua nếu `drive_id` đã có trong `anh-map.json` và file tương ứng đã tồn tại** —
  đây là điểm giúp các lần chạy sau nhanh và chỉ xử lý ảnh mới.
- Tải từ `https://drive.google.com/thumbnail?id={drive_id}&sz=w1000`.
  Nếu lỗi, thử `https://drive.google.com/uc?export=download&id={drive_id}`.
- Cho phép redirect (Drive hay chuyển hướng sang `drive.usercontent.google.com` hoặc
  `lh3.googleusercontent.com`).
- Kiểm tra nội dung tải về **đúng là ảnh** (Pillow mở được). Drive đôi khi trả về trang HTML
  cảnh báo virus thay vì file — trường hợp này tính là lỗi, không lưu.
- Chuyển sang WebP: chiều rộng tối đa **800px**, giữ nguyên tỉ lệ, không cắt xén,
  chất lượng **82**. Ảnh gốc nhỏ hơn 800px thì giữ nguyên kích thước.
- Lưu vào `anh-can-ho/<ten_file>`.
- Nghỉ **0.4 giây** giữa các lượt tải.
- Thử lại tối đa **2 lần** cho lỗi mạng tạm thời. **Không thử lại với lỗi 403** —
  403 là chặn theo chính sách, retry vô nghĩa.

### 3.5 Dọn ảnh không còn dùng

Sau khi xử lý xong, đối chiếu file thực tế trong `anh-can-ho/` với danh sách căn đang hiển thị:

- File không thuộc căn nào đang hiển thị (căn đã cho thuê, đã ẩn) → là ảnh cần dọn.
- **Mặc định CHỈ liệt kê ra log, KHÔNG xóa.** Chỉ xóa thật khi workflow được chạy với
  tham số đầu vào `don_dep = true`.
- Lý do: lần chạy đầu tiên phải quan sát danh sách trước khi cho phép xóa tự động.

### 3.6 Ghi kết quả

- Ghi lại `anh-can-ho/anh-map.json`: khóa là `drive_id`, giá trị là đường dẫn tuyệt đối
  tính từ gốc site, dạng `/anh-can-ho/<ten_file>`. **Chỉ ghi các ảnh có file thực tế tồn tại.**
- Sinh `sitemap-images.xml` theo chuẩn Google Image Sitemap, liệt kê toàn bộ ảnh trong map.
- In báo cáo tổng kết: số ảnh mới tải, số bỏ qua (đã có), số lỗi kèm mã nội bộ,
  số ảnh thuộc diện dọn dẹp, tổng dung lượng thư mục.

---

## 4. Workflow `.github/workflows/dong-bo-anh.yml`

- Kích hoạt: **chỉ `workflow_dispatch`** (chạy bằng tay). **Chưa đặt lịch `schedule`** —
  sẽ bật sau khi chạy thật vài lần thấy ổn định.
- Tham số đầu vào (`inputs`): `don_dep` kiểu boolean, **mặc định `false`**.
- `permissions: contents: write` để runner commit được.
- Các bước: checkout → cài Python 3.11 → `pip install pillow requests` → chạy script →
  commit và push nếu có thay đổi.
- Commit message: `Đồng bộ ảnh đại diện sang WebP - <ngày giờ>`
- Nếu không có thay đổi nào thì **không tạo commit rỗng**.
- Đặt `timeout-minutes: 30`.

**Quan trọng:** workflow này commit thẳng vào branch mà nó chạy. Trong PR chỉ nộp *file workflow
và script*, **không chạy nó**. Anh sẽ tự bấm chạy sau khi merge.

---

## 5. Sửa frontend

### 5a. `dong-bo-can.js` (file ở gốc repo) — ba thay đổi

1. Nạp `/anh-can-ho/anh-map.json` một lần khi script khởi động, lưu vào biến trong module.
   **Nếu nạp lỗi hoặc file chưa tồn tại thì để map rỗng** — site phải chạy bình thường với
   ảnh Drive như hiện nay. Đây là yêu cầu bắt buộc, không được để site phụ thuộc vào file này.
2. Trong hàm `driveUrlToViewUrl` (khoảng dòng 75): sau khi trích được ID từ URL, tra ID trong map.
   Có thì trả đường dẫn ảnh repo; không có thì giữ nguyên hành vi cũ (trả URL thumbnail Drive).
3. Trong hàm `anhBia` (khoảng dòng 172): hiện hàm trả URL thô từ `data.json`, **không đi qua**
   `driveUrlToViewUrl` nên map sẽ không áp dụng được cho ảnh bìa. Cho giá trị trả về đi qua
   `driveUrlToViewUrl` trước khi trả.

Giữ nguyên mọi phần khác, kể cả `onerror` của thẻ `<img>` (khoảng dòng 448).

### 5b. `robots.txt`

Thêm dòng khai báo `Sitemap:` trỏ tới `sitemap-images.xml`. Giữ nguyên dòng khai báo
`sitemap.xml` hiện có.

---

## 6. Ràng buộc bắt buộc

- **KHÔNG chỉnh sửa `data.json`** dưới bất kỳ hình thức nào — script chỉ được đọc.
- **KHÔNG chỉnh sửa `/assets/v3.css`.**
- **KHÔNG đụng khối GA4 `ganDoLuongChuyenDoi`** hay bất kỳ mã đo lường nào.
- **KHÔNG sửa schema JSON-LD** trong các trang HTML ở PR này.
- **KHÔNG hardcode token** — dùng `GITHUB_TOKEN` sẵn có của Actions.
- **KHÔNG tự merge PR.**
- **KHÔNG chạy workflow trong PR này** — chỉ nộp code.

---

## 7. Kiểm tra trước khi mở PR

- [ ] Chạy thử phần logic **không cần mạng**: cho script chạy ở chế độ chỉ đọc `data.json`
      và in ra danh sách tên file dự kiến. Xác nhận ra **đúng 197 bản ghi**, không trùng tên file.
- [ ] Đối chiếu vài tên file với `di-doi-anh/danh-sach-anh.json` (file tham chiếu đã có sẵn
      trong repo) — phải khớp chính xác từng ký tự. Nếu lệch, logic slug hoặc `tenPhanKhu` sai.
- [ ] `dong-bo-can.js` vẫn chạy đúng khi `anh-map.json` không tồn tại (ảnh Drive hiển thị bình thường)
- [ ] YAML workflow hợp lệ về cú pháp
- [ ] `git status` xác nhận `data.json` **không** nằm trong danh sách thay đổi

## 8. Nội dung mô tả PR

Nêu rõ: các file đã tạo/sửa, kết quả bước kiểm tra 197 bản ghi, và hướng dẫn ngắn cho người
merge biết cần vào tab Actions bấm chạy workflow sau khi merge.

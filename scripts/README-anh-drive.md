# Đồng bộ ảnh thư mục Drive

`data.json` vẫn do Apps Script quản lý. `quet-thu-muc-anh.py` đọc các cột công khai B/I/J/K/L của tab Cong ty trong Sheet web, đối chiếu mã căn đang hiển thị và quét lại từng thư mục Drive công khai. Không đọc cột chủ nhà hoặc ghi chú nội bộ.

Kết quả lưu ở `anh-can-ho/nguon-anh.json`. Trang chủ, danh mục, trang chi tiết và danh sách tải WebP dùng cùng snapshot này. Khi các cột ảnh trong data.json mới hơn snapshot, hệ thống ưu tiên dữ liệu Sheet cho đến lượt quét tiếp theo. Video và ảnh bìa trích từ video được giữ riêng; video không được tính thành ảnh trong album.

Workflow ảnh chạy sau đồng bộ SEO và theo lịch phút 07/37 mỗi giờ. Thay đổi tên/link thư mục không còn là điều kiện để phát hiện ảnh mới. Thêm/xóa ảnh cập nhật album; file bị thay nội dung nhưng giữ ID được nhận biết qua modified time và kích thước, tạo URL WebP có phiên bản mới. Lịch 03:20 giờ Việt Nam vẫn làm mới sâu như trước. GitHub có thể chạy lịch trễ.

Nguồn HTML công khai của Drive không phải API ổn định. Parser từ chối dữ liệu thiếu, phân trang (100 mục trở lên), thư mục con hoặc cấu trúc lạ. Lỗi riêng lẻ giữ snapshot gần nhất; lỗi diện rộng dừng xuất bản. Các trường hợp này hiện trong warning/error của GitHub Actions, không xóa ảnh đang chạy. Muốn hỗ trợ thư mục con/nhiều hơn 99 mục cần bổ sung cơ chế liệt kê đầy đủ trước.

Kiểm tra hồi quy:

```sh
python3 -m unittest discover -s scripts -p test_quet_anh.py
```

Không sửa tay `data.json` hoặc `nguon-anh.json`. Chạy workflow ảnh để quét, tải, dựng lại HTML và yêu cầu GitHub Pages build trong cùng lượt.

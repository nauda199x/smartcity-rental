# Đồng bộ ảnh thư mục Drive

`quet-thu-muc-anh.py` không ghi vào `data.json`. Nguồn An Việt đọc mã căn và thư mục ảnh ở cột C/J của 7 tab CTV; nguồn Thu Thảo đọc `Thư mục ảnh CTV` đã đồng bộ từ cột I vào `data.json`. Đối chiếu mã nội bộ theo namespace CT.* / TT.* và chỉ quét các căn đang hiển thị. Không đọc cột chủ nhà hoặc ghi chú nội bộ.

Ảnh Thu Thảo dùng cùng pipeline snapshot → WebP → album/trang chi tiết. Khóa snapshot bao gồm thư mục CTV, vì vậy khi Sheet đổi/xóa thư mục sẽ không áp ảnh cũ cho căn. Thư mục trùng chỉ quét một lần; tải tối đa 4 ảnh đồng thời, mỗi luồng có HTTP session riêng và vẫn giữ cache/retry.

Kết quả lưu ở `anh-can-ho/nguon-anh.json`. Trang chủ, danh mục, trang chi tiết và danh sách tải WebP dùng cùng snapshot này. Khi các cột ảnh trong data.json mới hơn snapshot, hệ thống ưu tiên dữ liệu Sheet cho đến lượt quét tiếp theo. Video và ảnh bìa trích từ video được giữ riêng; video không được tính thành ảnh trong album.

Workflow công bố nhanh ảnh chạy sau mỗi lượt đồng bộ Sheet CTV thành công, không cần đợi tải toàn bộ WebP hoặc lượt SEO. Lịch phút 07/37 vẫn là lớp quét dự phòng. Thay đổi tên/link thư mục không còn là điều kiện để phát hiện ảnh mới. Thêm/xóa ảnh cập nhật album; file bị thay nội dung nhưng giữ ID được nhận biết qua modified time và kích thước, tạo URL WebP có phiên bản mới. Lịch 03:20 giờ Việt Nam vẫn làm mới sâu như trước. GitHub có thể chạy lịch trễ.

Nguồn HTML công khai của Drive không phải API ổn định. Parser xác minh metadata trước khi nhận thư mục rỗng (Drive dùng `null` cho danh sách rỗng). Thư mục con được quét đầy đủ, tối đa 3 cấp sâu và 32 thư mục cho một album; ảnh trùng ID chỉ xuất hiện một lần, video không tính vào album. Dữ liệu thiếu, phân trang (100 mục trở lên), cây quá lớn/lặp hoặc một thư mục con lỗi đều giữ snapshot gần nhất, không xuất album một phần. Lỗi diện rộng dừng xuất bản. Sheet ảnh An Việt lỗi không chặn Thu Thảo: dùng lại thư mục An Việt đã xác minh chỉ khi khóa nguồn vẫn khớp. Giới hạn đọc An Việt cho phép đến 1.500 dòng để không dừng quét ảnh khi quỹ căn vượt 500 dòng. Không thay đổi quyền Drive hay GitHub Pages.

Kiểm tra hồi quy:

```sh
python3 -m unittest discover -s scripts -p test_quet_anh.py
```

Không sửa tay `data.json` hoặc `nguon-anh.json`. Chạy workflow ảnh để quét, tải, dựng lại HTML và yêu cầu GitHub Pages build trong cùng lượt.

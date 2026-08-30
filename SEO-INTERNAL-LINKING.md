# SEO Internal Linking Architecture

Kiến trúc nội bộ của timthuesmartcity.com sau bước 6.

## Cây chủ đề

1. **Hub gốc** — `/`
2. **Hub giao dịch chính**
   - Loại căn: Studio, 1PN, 1PN+, 2PN, 2PN+, 3PN
   - Phân khu: Sapphire, Masteri, Miami, Sakura, Imperia, Lumiere, Canopy, Tonkin
   - Hub URL căn: `/can-ho/`
3. **Long-tail hiện có**
   - Theo khoảng giá
   - Theo full nội thất
4. **Trang căn chi tiết**
   - Parent phân khu
   - Parent loại căn
   - Long-tail phù hợp giá/nội thất
   - Trang tòa nếu có
   - Bảng giá / phí / kinh nghiệm
5. **Cẩm nang hỗ trợ**
   - Bảng giá
   - So sánh phân khu
   - Kinh nghiệm thuê
   - Phí dịch vụ

## Quy tắc link

- Link quan trọng phải nằm trong HTML tĩnh, không phụ thuộc JS.
- Một block điều hướng theo chủ đề tối đa khoảng 3 nhóm.
- Không biến block SEO thành tag cloud toàn site.
- Anchor mô tả đúng trang đích; tránh lặp một anchor keyword ở hàng chục vị trí vô nghĩa.
- Trang long-tail luôn có đường về parent loại căn.
- Trang phân khu ưu tiên link sang các loại căn thực sự có inventory.
- Trang loại căn ưu tiên link sang các phân khu đang có nhiều inventory cho chính loại đó.
- Trang chi tiết ưu tiên parent + intent gần (giá/nội thất) + cẩm nang.
- URL căn đã thuê vẫn 200 và tiếp tục truyền đường link sang cụm active.
- Không link internal tới query parameter để làm SEO; query chỉ phục vụ UX.

## Tự động hóa

`scripts/cap-nhat-lien-ket-noi-bo.py`
- đọc `data.json`;
- tìm các trang có `#bo-loc-trang`;
- tính top phân khu / top loại căn theo inventory thật;
- thay block cũ bằng block `SEO-LINKS` tĩnh;
- chạy sau khi lưới và URL detail được sinh.

`scripts/sinh-trang-can.py`
- tự nối trang chi tiết vào parent + long-tail phù hợp;
- `/can-ho/` có hub link lên top loại căn / phân khu.

`scripts/sinh-trang-toa.py`
- trang tòa nối lên phân khu, loại căn đang có và nhóm cẩm nang.

## Không làm ở bước 6

Không tạo trang **Phân khu × Loại căn** mới. Đây là bước 7 để tránh tạo hàng loạt URL mỏng trước khi có template/content đúng.

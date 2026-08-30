# Smart City Design System

> Áp dụng cho timthuesmartcity.com. Nguồn CSS chính: `assets/v3.css`, khối **SMART CITY DESIGN SYSTEM V11**.

## 1. Nguyên tắc

- Một ngôn ngữ thị giác xuyên suốt: sạch, tin cậy, thiên về marketplace bất động sản.
- Không tạo màu/radius/shadow mới trong từng trang nếu token hiện có đáp ứng được.
- Mobile ưu tiên thao tác ngón cái; desktop ưu tiên quét thông tin nhanh.
- Không đổi URL, canonical, schema hoặc cấu trúc dữ liệu chỉ để phục vụ giao diện.
- Component mới phải dùng lại token và breakpoint hiện có.

## 2. Token màu

- Brand 950/900: tiêu đề, vùng nhận diện, trạng thái active mạnh.
- Brand 700: CTA chính, giá, liên kết quan trọng.
- Brand 600 / Accent: focus, hover, trạng thái tương tác.
- Text / Text 2 / Text 3: nội dung chính / phụ / metadata.
- Surface / Surface 2 / Surface 3: card / nền phụ / nền muted.
- Line / Line Strong: viền thường / viền hover.
- Success / Warning / Danger: trạng thái căn và thông báo.

Không viết thêm mã hex vào component nếu có thể dùng `--ds-*`.

## 3. Radius

- `--ds-r-xs: 8px`: badge nhỏ.
- `--ds-r-sm: 10px`: button, input.
- `--ds-r-md: 14px`: stat, bảng, card nhỏ.
- `--ds-r-lg: 18px`: section/card lớn.
- `--ds-r-xl: 22px`: article/form chính.
- `--ds-r-pill`: chip, language switch, badge tròn.

## 4. Shadow

- XS: card tĩnh / surface.
- SM: card nội dung và listing.
- MD: sticky card / hover.
- LG: dropdown / overlay nổi.

Không dùng shadow lớn cho mọi card. Viền + shadow nhẹ là mặc định.

## 5. Typography

- Heading: Plus Jakarta Sans, 700–800.
- Body: Be Vietnam Pro, 400–600.
- H1 dùng `clamp()`, line-height ~1.16.
- Body line-height ~1.65; bài dài ~1.8.
- Metadata không nhỏ hơn khoảng 11–12px trên mobile.

## 6. Component chuẩn

### Header
- Brand + navigation + hành động.
- Desktop menu theo intent thuê.
- Tablet giữ menu.
- Mobile dùng bottom navigation + bottom sheet.

### Button
- Primary: brand 700, chữ trắng.
- Secondary: nền trắng, viền line strong, chữ brand.
- Zalo: màu Zalo riêng.
- Touch target mobile tối thiểu ~44px.

### Surface/Card
- Surface trắng, viền `--ds-line`, radius MD/LG.
- Hover chỉ nâng nhẹ; không phóng/nhảy quá mạnh.

### Listing card
- Desktop 2 card/hàng, card ngang.
- Tablet 1 card ngang/hàng.
- Mobile card dọc + swipe ảnh.
- Giá là hierarchy số 1; loại căn/diện tích số 2; vị trí số 3.

### Content article
- `.pillar` là reading surface duy nhất.
- `.sec` bên trong bài là heading, không phải card.
- `.toc` là surface phụ muted.
- `.note` dùng nền xanh rất nhạt + viền trái.

### Table
- Header nền muted.
- Row divider mảnh.
- Table rộng dùng `.bang-cuon` để cuộn ngang mobile.

### Form
- Input cao tối thiểu 46px.
- Focus ring brand.
- Fieldset chia nhóm bằng divider.
- Form chính dùng radius XL.

### Footer
- Nền off-white, NAP rõ ràng.
- Link quan trọng dùng brand 700.

## 7. Breakpoint

- Mobile: `<= 640px`
- Tablet/intermediate: `641–1080px`
- Desktop marketplace: `>= 1081px`

Không tạo breakpoint mới nếu không có lý do kỹ thuật rõ ràng.

## 8. Quy tắc cho lần sửa tiếp theo

Trước khi thêm CSS mới:

1. Kiểm tra component đã tồn tại chưa.
2. Dùng token `--ds-*`.
3. Không ghi đè mobile nếu yêu cầu chỉ liên quan desktop.
4. Không thay layout bằng JS nếu CSS giải quyết được.
5. Các trang sinh tự động phải sửa generator, không sửa output riêng lẻ.
6. Mọi thay đổi shared CSS phải kiểm tra ít nhất: trang chủ, trang danh mục, cẩm nang, ký gửi và trang chi tiết.

# Audit brand name — `nauda199x/smartcity-rental`

Báo cáo thuần audit. **Không sửa file HTML nào** — mọi con số dưới đây đếm
trực tiếp từ repo tại thời điểm audit (nhánh `claude/new-session-89nn24`,
44 trang HTML, 51 khối JSON-LD). Lệnh đếm dùng `grep -c`/`grep -l` và một
script Python walk toàn bộ JSON-LD (đệ quy, kể cả trường lồng trong
`@graph`, `author`, `publisher`, `isPartOf`, `creator`...); mọi số liệu đều
tái tạo được bằng các lệnh liệt kê trong từng mục.

---

## 1. Kiểm kê toàn bộ trường JSON-LD chứa tên thương hiệu

Quét đệ quy 51 khối JSON-LD, lọc mọi trường `name` / `alternateName` /
`legalName` khớp mẫu chứa "Smart City" hoặc "thuê", sau đó loại các trường
là **tiêu đề nội dung trang** (`ItemList.name`, `BreadcrumbList...name`,
`FAQPage.mainEntity.Question.name`, `CollectionPage.about.name`...) — các
trường này phản ánh H1/tiêu đề bài viết cụ thể từng trang, không phải danh
tính thương hiệu, và nằm trong vùng cấm sửa (H1, FAQ). Bảng dưới đây chỉ còn
lại các trường **danh tính site/tổ chức**:

| Trường | Giá trị | Số file | File |
|---|---|---|---|
| `WebSite.name` | `Thuê Chung Cư Smart City` | 1 | `index.html` |
| `WebSite.alternateName` | `Tìm Thuê Smart City` | 1 | `index.html` |
| `RealEstateAgent.name` | `Cho thuê chung cư Smart City` | 1 | `index.html` |
| `CollectionPage.isPartOf.WebSite.name` | `Cho thuê chung cư Smart City` | 1 | `cam-nang-thue-nha.html` |
| `Article.author.Organization.name` | `Cho thuê chung cư Smart City` | 11 | 11 bài viết (danh sách mục 1b) |
| `Article.publisher.Organization.name` | `Cho thuê chung cư Smart City` | 11 | trùng 11 file trên (mỗi file có cả `author` và `publisher`) |
| `ImageObject.creator.Organization.name` | `timthuesmartcity.com` | 1 | `bang-gia-thue-vinhomes-smart-city.html` |
| `og:site_name` (meta, không phải JSON-LD nhưng cùng vai trò khai danh tính site) | `Thuê Chung Cư Smart City` | 28 | danh sách mục 1c |

**Phát hiện quan trọng không có trong đề bài gốc:** `isPartOf.WebSite.name`
trên `cam-nang-thue-nha.html` mang giá trị `Cho thuê chung cư Smart City`,
khác với `WebSite.name` chính khai trên `index.html`
(`Thuê Chung Cư Smart City`). Đây là **cùng một thực thể WebSite** nhưng bị
khai hai giá trị `name` khác nhau ở hai trang — một mâu thuẫn dữ liệu có
thật, độc lập với việc nên chọn tên nào.

Cũng phát hiện `ImageObject.creator.Organization.name` dùng giá trị thứ tư —
`timthuesmartcity.com` (chính là domain) — khác cả ba biến thể tên trong đề
bài. Trường này ít ảnh hưởng (chỉ gắn với 1 ảnh) nên không đưa vào bảng đếm
chính, nhưng đáng chú ý vì nó **tự nhiên đã dùng domain làm tên**, cùng
hướng với `Tìm Thuê Smart City`.

### 1a. Ba biến thể theo đề bài — xác nhận lại bằng đếm trực tiếp

| Biến thể | Số lần (đã verify) | Số file (đã verify) |
|---|---|---|
| `Cho thuê chung cư Smart City` | 122 | 43 |
| `Thuê Chung Cư Smart City` | 29 | 28 |
| `Tìm Thuê Smart City` | 1 | 1 |

Khớp 100% với số liệu đề bài cung cấp.

Phân loại 122 lần xuất hiện của `Cho thuê chung cư Smart City` theo vị trí
(đếm bằng script phân loại từng dòng khớp):

| Vị trí | Số lần |
|---|---|
| Footer (bản quyền / mô tả) | 44 |
| Header (liên kết logo/brand) | 29 (một phần bị gộp vào "khác" do khác biến thể markup giữa `index.html` và các trang còn lại — tổng header+"khác" thực chất đều là brand-link, xem ghi chú) |
| JSON-LD (`RealEstateAgent.name` + `author.name` + `publisher.name` + `isPartOf.WebSite.name`) | 24 |
| Nội dung thân trang khác (đoạn mô tả, brand-link ở trang danh mục dùng `class="hieu"`) | 22 |
| Meta description | 2 |
| Title tag | 1 |

Tổng 44+29+24+22+2+1 = 122, khớp số đếm gốc.

### 1b. 11 file có `author.name` / `publisher.name`

Đây đúng là 11/14 trang nhóm "bài viết" (nhóm `bai-viet` trong
`kiem-tra-lien-ket.py`), tức các bài kiểu `Article`:

```
cho-thue-can-ho-imperia-smart-city.html
cho-thue-can-ho-masteri-west-heights-smart-city.html
gia-thue-studio-smart-city.html
kinh-nghiem-thue-chung-cu-smart-city.html
luu-y-do-xe-thu-cung-phi-dich-vu-smart-city.html
phi-dich-vu-vinhomes-smart-city.html
so-sanh-gia-thue-cac-phan-khu-smart-city.html
thu-tuc-thue-nha-vinhomes-smart-city.html
thue-can-ho-gan-vinschool-smart-city.html
thue-can-ho-lumiere-evergreen.html
tien-ich-vinhomes-smart-city.html
```

3 trang còn lại trong nhóm `bai-viet` (`bang-gia-thue-smart-city-thang-7-2026.html`
— trang redirect stub, `cam-nang-thue-nha.html` — dùng `CollectionPage` +
`isPartOf.WebSite.name` thay vì `author`/`publisher`, và
`bang-gia-thue-vinhomes-smart-city.html` — dùng `ImageObject`) không thuộc
`@type: Article` nên không có cặp `author`/`publisher`.

### 1c. 28 file có `og:site_name`

```
index.html, 1pn/index.html, 1pn-plus/index.html, 1pn-plus-duoi-10-trieu/index.html,
1pn-plus-full-do/index.html, 2pn/index.html, 2pn-10-12-trieu/index.html,
2pn-duoi-10-trieu/index.html, 2pn-full-do/index.html, 2pn-plus/index.html,
2pn-plus-12-15-trieu/index.html, 3pn/index.html, 3pn-12-15-trieu/index.html,
3pn-full-do/index.html, canopy/index.html, imperia/index.html, lumiere/index.html,
masteri/index.html, miami/index.html, s4-01-vinhomes-smart-city/index.html,
sakura/index.html, sapphire/index.html, studio/index.html, studio-7-10-trieu/index.html,
studio-duoi-7-trieu/index.html, studio-full-do/index.html, tonkin/index.html,
thue-can-ho-lumiere-evergreen.html
```

Ghi nhận thêm một **bất nhất nội bộ có sẵn, không liên quan tên nào đúng**:
`og:site_name` phủ toàn bộ trang danh mục (loại căn, giá-nội thất, phân khu,
trang tòa) và trang chủ, nhưng chỉ phủ **1/14** trang bài viết
(`thue-can-ho-lumiere-evergreen.html`) — 13 bài viết còn lại (kể cả 11 bài
có `author`/`publisher` ở trên) **không có `og:site_name`**. Đây là lỗ hổng
kỹ thuật độc lập, TASK 2 chỉ ghi nhận, không sửa.

---

## 2. Tên hiển thị thực tế theo nhóm trang (header/footer/title)

Kiểm tra trực tiếp theo 6 nhóm vai trò dùng trong `kiem-tra-lien-ket.py`
(`trang-chu`, `danh-muc-loai-can`, `danh-muc-gia-noi-that`,
`danh-muc-phan-khu`, `trang-toa`, `bai-viet`, `phu-tro`):

| Nhóm | Header/logo hiển thị | Footer hiển thị | `<title>` có brand suffix? |
|---|---|---|---|
| Trang chủ (`index.html`) | `Cho thuê chung cư Smart City` | `Cho thuê chung cư Smart City` | Mở đầu bằng `Thuê chung cư Smart City –` (biến thể thứ 4, xem mục 2a) |
| Danh mục loại căn / giá-nội thất / phân khu / trang tòa | `Cho thuê chung cư Smart City` (thẻ `<a class="hieu">`) | `Cho thuê chung cư Smart City` | Không — title chỉ chứa từ khóa loại căn/khu, không có brand suffix |
| Bài viết (`bai-viet`) | `Cho thuê chung cư Smart City` | `Cho thuê chung cư Smart City` | 1/14 có brand suffix (`chinh-sach-quyen-rieng-tu.html` không thuộc nhóm này — xem dưới); còn lại không |
| Phụ trợ (`chinh-sach-quyen-rieng-tu.html`, `gui-thue/index.html`) | `Cho thuê chung cư Smart City` | `Cho thuê chung cư Smart City` | `chinh-sach-quyen-rieng-tu.html` có suffix `\| Cho thuê chung cư Smart City`; `gui-thue` không |
| `404.html` | `Thuê chung cư Smart City` (biến thể thứ 4, không có "Cho") | `Cho thuê chung cư Smart City` | Có, dùng biến thể thứ 4 |
| `bang-gia-thue-smart-city-thang-7-2026.html` (stub redirect, miễn orphan) | Không có header/footer chuẩn — trang chỉ có nút chuyển hướng | — | Không |

**Kết luận mục 2: không có nhóm nào lệch nhau.** 43/44 trang (trừ trang
stub redirect, vốn không có layout chuẩn) hiển thị **thống nhất tuyệt đối**
`Cho thuê chung cư Smart City` ở cả header lẫn footer, không phân biệt
nhóm trang. Đây là tên hiển thị trên UI mạnh và nhất quán nhất trong ba biến
thể — ngược lại với giả định trước đây rằng `Thuê Chung Cư Smart City` là
"tên chính".

### 2a. Biến thể thứ 4 phát hiện thêm: `Thuê chung cư Smart City` (không có "Cho")

Xuất hiện ở `<title>`/H2 của `index.html` và `<title>`/span của `404.html`.
Trong `index.html` có comment sẵn trong code (dòng 605) giải thích đây là
**từ khóa SEO cố ý nhắm tới** ("từ khóa 'thuê chung cư Smart City', vốn là
từ khóa giá trị nhất"), không phải một biến thể tên thương hiệu — nó là
cụm từ khóa tìm kiếm, khác phạm trù với brand identity. Ghi nhận để đầy đủ,
nhưng **không tính là ứng viên tên chính** vì mục đích khai báo khác hẳn
(target từ khóa SEO on-page, nằm trong `<title>`/H2 — vùng cấm sửa của cả
hai task), và không nằm trong ba biến thể đề bài yêu cầu đối chiếu.

---

## 3. Đối chiếu với danh tính social/domain

| Kênh | Định danh thực tế trong repo (`sameAs`, `index.html` dòng 134-139 và
footer dòng 675-682) |
|---|---|
| Domain | `timthuesmartcity.com` |
| Facebook | `facebook.com/people/Tìm-thuê-Smart-City/...` (encode: `T%C3%ACm-thu%C3%AA-Smart-City`) |
| TikTok | `@timthuesmartcity` |
| Instagram | `@timthuesmartcity_com` |
| YouTube | `@Timthuesmartcity` |

Đối chiếu từng biến thể với 5 định danh trên:

| Biến thể | Khớp domain | Khớp Facebook | Khớp TikTok | Khớp Instagram | Khớp YouTube | Tổng khớp |
|---|---|---|---|---|---|---|
| `Tìm Thuê Smart City` | ✅ | ✅ | ✅ | ✅ | ✅ | **5/5** |
| `Thuê Chung Cư Smart City` | ❌ | ❌ | ❌ | ❌ | ❌ | **0/5** |
| `Cho thuê chung cư Smart City` | ❌ | ❌ | ❌ | ❌ | ❌ | **0/5** |

`Tìm Thuê Smart City` là biến thể **duy nhất** khớp toàn bộ 5 định danh bên
ngoài (domain + 4 kênh social) đã được chính repo công khai trong
`sameAs` và ở dải nút mạng xã hội trên footer. Không có sự mơ hồ trong phép
đối chiếu này — đây là dữ liệu cấu trúc, đếm được, không suy đoán.

### Trả lời câu hỏi mục 3 của đề bài

**Tên chính nên là `Tìm Thuê Smart City`, không phải `Thuê Chung Cư Smart City`.**

Lý do dựa trên dữ liệu đếm được (không ước đoán):

1. `Thuê Chung Cư Smart City` tuy phủ 28 file qua `og:site_name` + 1 qua
   `WebSite.name`, nhưng **khớp 0/5** định danh bên ngoài mà chính repo đã
   công khai (domain, Facebook, TikTok, Instagram, YouTube). Một tên chính
   không khớp domain lẫn bất kỳ kênh social nào là rủi ro cho entity SEO:
   Google đối chiếu `sameAs` với `name`/`alternateName` để xác nhận một
   thực thể duy nhất; lệch tên ở đây làm suy yếu tín hiệu đó — đúng như
   comment sẵn trong `index.html` (dòng 671-674) đã cảnh báo cho social
   links, logic tương tự áp dụng cho tên site.
2. `Tìm Thuê Smart City` khớp **5/5**: domain, cả 4 social. Đây là danh
   tính mà các nền tảng bên ngoài (Facebook, TikTok, Instagram, YouTube,
   registrar domain) đã "bỏ phiếu" đồng nhất — dữ liệu độc lập với nội bộ
   repo, đáng tin hơn giả định nội bộ trước đây.
3. `Cho thuê chung cư Smart City` — biến thể phổ biến nhất về mặt hiển thị
   UI (122 lần / 43 file, xem mục 2) — cũng khớp 0/5, giống
   `Thuê Chung Cư Smart City`. Nó có sức nặng vì là tên **người dùng thấy**,
   không phải vì khớp định danh ngoài.

**Giới hạn của kết luận này:** đây là kết luận về **nhất quán thực thể cho
schema/entity SEO** (dựa trên đối chiếu domain + sameAs, dữ liệu đếm được
100%), không phải kết luận về **mức độ nhận diện tìm kiếm hiện tại của
người dùng** giữa các biến thể — câu hỏi đó cần dữ liệu Google Search
Console (query thương hiệu, số impression/click cho từng biến thể tên), mà
**repo này không có** (đã kiểm tra, không tìm thấy file GSC/query nào).
Nếu cần quyết định có nên đổi cả tên hiển thị UI (`Cho thuê chung cư Smart
City`, đang phủ 43/44 trang) hay không, bắt buộc phải bổ sung số liệu GSC
branded-query trước — mục 4 dưới đây vì vậy **không đề xuất đổi tên hiển
thị UI**, chỉ đề xuất đổi tầng JSON-LD/meta.

---

## 4. Đề xuất cấu hình cuối cùng

> Đề xuất dưới đây **không được áp dụng trong task này** (ngoài phạm vi,
> xem hướng dẫn — "Đổi brand name... KHÔNG làm" bất kể kết luận). Ghi lại
> để chủ repo quyết định và giao cho một task riêng nếu đồng ý.

- **`name` chính** (dùng cho mọi trường `name` trong JSON-LD ở tầng
  site/tổ chức — `WebSite.name`, `RealEstateAgent.name`,
  `isPartOf.WebSite.name`, `author.name`, `publisher.name`):
  **`Tìm Thuê Smart City`**. Lý do: khớp 5/5 định danh ngoài (mục 3),
  là cách duy nhất để `sameAs` thực sự xác nhận đúng một thực thể.

- **`alternateName`**: giữ **`Thuê Chung Cư Smart City`** làm alternate
  duy nhất (bỏ trống hoặc chỉ 1 giá trị, không dùng 2, để tránh loãng tín
  hiệu entity). Lý do giữ nó làm alternate thay vì xoá hẳn: nó đã được
  Google index qua `og:site_name` trên 28 trang suốt một thời gian —
  giữ làm alternate giúp giữ cầu nối nhận diện trong lúc chuyển đổi, đúng
  vai trò của trường `alternateName` trong schema.org. Không đề xuất thêm
  `Cho thuê chung cư Smart City` làm alternateName thứ hai vì
  schema.org khuyến nghị `alternateName` gọn (thường 1 giá trị) và giá trị
  này đã có vai trò riêng làm tên hiển thị UI (xem mục dưới) — không cần
  lặp lại ở tầng structured data.

- **Tên hiển thị header/footer (`Cho thuê chung cư Smart City`)**:
  **giữ nguyên, không đổi.** Lý do:
  1. Nằm ngoài phạm vi được phép sửa của cả hai task (mục "Ngoài phạm vi").
  2. Đã phủ 43/44 trang tuyệt đối nhất quán (mục 2) — đổi sẽ là thay đổi
     lớn, rủi ro cao, trong khi mục tiêu entity SEO (mục 3) có thể đạt
     được chỉ bằng cách sửa tầng JSON-LD/`og:site_name`, không cần đụng
     UI. Structured data và nội dung hiển thị không bắt buộc phải giống
     hệt nhau — `alternateName` chính là cơ chế schema.org dành cho
     trường hợp này.
  3. Quyết định đổi tên hiển thị UI cần dữ liệu GSC (mục 3, phần giới hạn)
     mà hiện chưa có.

---

## 5. Ước lượng khối lượng nếu áp dụng đề xuất mục 4

Chỉ tính phần **JSON-LD + `og:site_name`** (không đụng header/footer UI,
theo khuyến nghị mục 4):

| Trường cần đổi | Số vị trí | Số file |
|---|---|---|
| `WebSite.name` (`index.html`) | 1 | 1 |
| `RealEstateAgent.name` (`index.html`) | 1 | (cùng file trên) |
| `isPartOf.WebSite.name` (`cam-nang-thue-nha.html`) | 1 | 1 |
| `Article.author.Organization.name` | 11 | 11 |
| `Article.publisher.Organization.name` | 11 | (cùng 11 file trên) |
| `og:site_name` | 28 | 28 |
| **Tổng** | **53 vị trí** | **39 file duy nhất** (28 file có `og:site_name` ∪ 11 file `author`/`publisher` ∪ `cam-nang-thue-nha.html`, trừ 1 file trùng — `thue-can-ho-lumiere-evergreen.html` — có cả `og:site_name` lẫn `author`/`publisher`) |

`WebSite.alternateName` không cần đổi giá trị (đã đúng `Tìm Thuê Smart
City`), chỉ cần xác nhận giữ nguyên.

**Đề xuất tách PR** (khớp cách chia nhỏ, thận trọng mà repo đang áp dụng —
nhiều script nhỏ, từng PR một mục đích):

1. **PR 1 — lõi thực thể trang chủ** (`index.html`, 1 file, 3 vị trí):
   `WebSite.name` → `Tìm Thuê Smart City`; `RealEstateAgent.name` →
   `Tìm Thuê Smart City`; xác nhận `alternateName` giữ
   `Thuê Chung Cư Smart City`. File duy nhất, rủi ro thấp nhất, dễ review.
2. **PR 2 — `og:site_name` trên 27 file còn lại** (28 trừ `index.html` đã
   ở PR 1): đổi đồng loạt sang `Tìm Thuê Smart City`. Thay đổi cùng dạng,
   máy móc, dễ diff-review theo batch.
3. **PR 3 — `author`/`publisher`/`isPartOf` trên 12 file bài viết**
   (11 file `Article` + `cam-nang-thue-nha.html`): 23 vị trí. Gộp chung vì
   cùng nhóm vai trò trang (`bai-viet`), cùng lý do sửa.

Không PR nào đụng tới `title`, `meta description`, `H1`, FAQ, internal
link, hay `data.json` — đúng ràng buộc cứng của cả hai task.

---

## Xác nhận cho acceptance criteria TASK 2

- Toàn bộ số liệu trong báo cáo này đếm trực tiếp từ repo bằng `grep`/script
  Python tại thời điểm audit — không có số liệu ước đoán.
- Không tìm thấy dữ liệu GSC (Google Search Console) trong repo; phần giới
  hạn kết luận ở mục 3 đã nêu rõ cần bổ sung gì nếu muốn quyết định thêm về
  tên hiển thị UI.
- `git status` sau khi hoàn thành TASK 2: sạch, ngoại trừ chính file báo cáo
  này (`AUDIT-BRAND-NAME.md`, file mới) và thay đổi của TASK 1
  (`scripts/kiem-tra-lien-ket.py`). Không file HTML nào bị sửa.

# PHASE 2 — BÁO CÁO: mở rộng `sinh-trang-toa.py` + 3 trang mẫu chờ duyệt

> Trả lời đầy đủ các mục A–G theo yêu cầu duyệt Phase 1. **Chưa publish gì
> cả** theo đúng yêu cầu mục F: 3 trang mẫu đã sinh thật (để xem trực tiếp)
> nhưng `sitemap.xml` không bị đụng, và 20/24 tòa còn lại (đủ điều kiện theo
> dữ liệu hôm nay) **chưa được ghi ra** — chỉ dùng để đo rủi ro rồi xoá lại
> (mục F cuối báo cáo giải thích quy trình đo này).

---

## A — Quyết định về pilot (không chờ 4-6 tuần)

Ghi nhận đầy đủ để truy vết sau này:

- **Chủ ý gốc** (docstring `sinh-trang-toa.py` trước khi sửa, viết lúc tạo
  trang S4.01): thử 1 trang, đo Google Search Console 4-6 tuần rồi mới nhân
  rộng.
- **Quyết định của anh/chị (24/08/2026, ghi lại nguyên văn lý do)**: KHÔNG
  chờ. Mở rộng đủ số tòa đạt ngưỡng ngay. Lý do: cỡ mẫu n=1 trong 4-6 tuần
  không tách được chất lượng template khỏi nhiễu ngẫu nhiên — lượng thông
  tin thu được gần như bằng 0 so với chi phí 6 tuần chờ.
- **Cơ chế kiểm soát rủi ro thay thế đã dùng thay cho việc chờ**: duyệt
  template thủ công trên 3 trang mẫu trước khi sinh hàng loạt (mục F) +
  Google Search Console đo cả lô sau 3 tuần (mục G). Phase 2 này áp dụng
  đúng cơ chế thay thế đó — và trong lúc kiểm tra template, đã phát hiện
  thật một lỗi (mục F.3, trùng lặp nội dung) mà nếu chờ 4-6 tuần với n=1
  cũng không thể phát hiện được (S4.01 một mình không tạo ra cặp nào để so
  sánh). Đây là bằng chứng cụ thể cho lý do đã nêu: kiểm tra chéo giữa nhiều
  trang có giá trị hơn hẳn quan sát một trang đơn lẻ theo thời gian.

## B — Hai lỗ hổng kỹ thuật (đã xử lý trong code)

### B1 — Ngưỡng dao động: luật publish lần đầu tách khỏi luật duy trì

Kiến trúc mới trong `scripts/sinh-trang-toa.py` (thay hẳn dict `CAC_TOA`
viết tay cũ):

- **`data/published-buildings.json`** — nguồn sự thật duy nhất cho "tòa nào
  đã từng có trang". Mỗi lần chạy: đọc file này trước, không suy luận "đã
  publish hay chưa" bằng cách xem thư mục HTML có tồn tại không (tránh mất
  trạng thái nếu file bị xoá ngoài ý muốn).
- **Luật publish lần đầu**: một tòa CHỈ được thêm vào file trạng thái (và có
  trang lần đầu) khi đang có ≥3 căn hiển thị VÀ phân khu nằm trong
  `PHAN_KHU_DA_DUYET`.
- **Luật duy trì**: một khi đã có trong `published-buildings.json`, tòa đó
  **luôn được xử lý ở mọi lần chạy sau**, bất kể số căn hiện tại là bao
  nhiêu (kể cả 0) — không có nhánh code nào xoá entry khỏi file này.
- **Nhánh hết căn**: khi một tòa đã publish tụt về 0 căn hiển thị, trang
  chuyển sang hiển thị "Tòa X hiện chưa có căn trống" + khối "Các tòa khác
  thuộc {phân khu}" (không noindex, không xoá file, không có `ItemList` vì
  không có gì để liệt kê). **Đã kiểm thử thật** bằng một tòa giả lập 0 căn —
  xem kết quả ở mục F.4.

Đã seed sẵn `data/published-buildings.json` với `S4.01` (`ngay_publish_lan_dau:
2026-08-23`, lấy từ `git log` thật của trang đó) — nếu không seed, lần chạy
đầu tiên của script mới sẽ coi S4.01 là "publish lần đầu" và ghi lại ngày
publish sai.

### B2 — Sitemap tự sinh, không thêm tay

`cap_nhat_sitemap_toa()` trong `sinh-trang-toa.py`:

- Ghi lastmod = **ngày sinh thật của lần chạy** (không phải ngày cố định).
- Chỉ thay đúng nội dung giữa 2 mốc `<!-- TOA:START -->` / `<!-- TOA:END
  -->` bằng regex có neo cả hai đầu — không đụng bất kỳ dòng nào khác trong
  43 URL hiện có của `sitemap.xml`.
- **Nếu 2 mốc đó chưa tồn tại trong `sitemap.xml`**: in cảnh báo và **bỏ
  qua hoàn toàn**, không tự chèn liều. Đã kiểm thử thật — chạy script với
  `sitemap.xml` ở trạng thái hiện tại (chưa có mốc) ra đúng cảnh báo này,
  file `sitemap.xml` không đổi một byte nào (xem `git status` cuối báo cáo).

→ **Việc còn lại, làm MỘT LẦN, thủ công, có review** (không phải "thêm tay
33 dòng" như đề xuất cũ đã bị bác — đây chỉ là thêm **2 dòng mốc rỗng**,
sau đó script tự lo phần còn lại vĩnh viễn): chèn `<!-- TOA:START
(sinh tự động bởi scripts/sinh-trang-toa.py, không sửa tay) -->` và
`<!-- TOA:END -->` (liền nhau, chưa có `<url>` nào ở giữa) vào vị trí phù
hợp trong `sitemap.xml`. Đề xuất làm việc này ở đầu Phase 4 (dọn sitemap),
cùng lúc với review toàn bộ thay đổi sitemap khác — **chưa làm ở Phase 2**
theo đúng yêu cầu mục F "CHƯA đụng sitemap".

## C — Mapping tòa: bảng xác nhận (chờ trả lời, KHÔNG duyệt gộp)

### C1 — Miami và Lumiere (7 tòa, TẠM DỪNG)

| Mã tòa | Phân khu suy luận | Căn cứ suy luận | Số căn hiện tại | Mã căn ví dụ |
|---|---|---|---|---|
| GS1 | Miami | Tiền tố `GS` → Miami trong `phan_khu_tu_toa()` (`sinh-danh-sach-anh.py`) | 8 | `CT.2N2.259`, `CT.3N.124`, `CT.2N2.341` |
| GS2 | Miami | (như trên) | 2 — dưới ngưỡng, không publish dù được duyệt | `CT.2N+.240`, `CT.2N+.279` |
| GS3 | Miami | (như trên) | 2 — dưới ngưỡng | `CT.2N+.229`, `CT.2N1.204` |
| GS5 | Miami | (như trên) | 9 | `CT.3N.52`, `CT.3N.129`, `CT.2N2.326` |
| GS6 | Miami | (như trên) | 7 | `CT.2N2.317`, `CT.2N2.319`, `CT.3N.122` |
| A2 | Lumiere | Tiền tố `A` + 1 chữ số → Lumiere trong `phan_khu_tu_toa()` | 29 | `CT.2N2.351`, `CT.3N.145`, `CT.1N.150` |
| A3 | Lumiere | (như trên) | 9 | `CT.1N.127`, `CT.1N.111`, `CT.2N2.243` |

**Vì sao TẠM DỪNG dù cùng một hàm suy luận đã đúng ở 6 phân khu khác**: hai
trang `miami/index.html` và `lumiere/index.html` hiện **không có câu văn
nào tự liệt kê tên các tòa thuộc phân khu** (đã grep toàn bộ 2 file, không
tìm thấy — khác 6 phân khu kia đều có câu kiểu "gồm bốn tòa X, Y, Z..."), nên
không có bằng chứng độc lập để đối chiếu với suy luận từ tiền tố mã. Không
phải nghi ngờ hàm sai — chỉ là chưa có gì để xác nhận, đúng nguyên tắc
"không đoán rồi ghi như dữ kiện" của tài liệu gốc.

**Câu hỏi cần anh/chị xác nhận**: 7 tòa trên có đúng thuộc Miami/Lumiere như
suy luận không? Nếu đúng, trả lời "duyệt Miami+Lumiere" là đủ để Phase 2
thêm 2 dòng vào `PHAN_KHU_DA_DUYET` (không cần sửa gì khác — kiến trúc mới
không cần liệt kê từng tòa).

### C2 — Masteri: "West A/B/C/D" trong nội dung vs "MasA-D" trong dữ liệu

| Mã tòa (data.json) | Số căn | Mã căn ví dụ | Tên nhắc trong `masteri/index.html` (nếu đúng thứ tự chữ cái) |
|---|---|---|---|
| MasA | 9 | (xem `docs/buildings-gap.md`) | "West A" |
| MasB | 19 | | "West B" |
| MasC | 8 | | "West C" |
| MasD | 10 | | "West D" |

**Bằng chứng đã có**: `masteri/index.html` viết "Masteri West Heights do
Masterise Homes phát triển, gồm bốn tòa West A, West B, West C và West D"
(dòng 601-602 và khối FAQ). Số lượng khớp tuyệt đối (4 = 4). **Bằng chứng
CÒN THIẾU**: không có field nào trong `data.json` hay bất kỳ đâu trong repo
nối trực tiếp `MasA` với `West A` theo đúng thứ tự — đây là suy đoán theo
vần chữ cái (A↔A, B↔B...), hợp lý nhưng chưa xác nhận.

**Ảnh hưởng nếu đoán sai thứ tự**: `<title>`, `<h1>`, breadcrumb của 4 trang
tòa Masteri sẽ mang tên sai ngay từ khi Google index lần đầu — sửa sau khi
đã có index tốn kém hơn nhiều so với chờ xác nhận trước.

**Quyết định đã áp dụng cho Phase 2 (để không phải làm lại)**: `PHAN_KHU_DA_DUYET`
**chưa có "Masteri"**. Mapping phân khu của 4 tòa này (MasA-D → Masteri) về
bản chất đã khớp số lượng như 6 phân khu kia, nhưng cả gói (mapping + tên
hiển thị) đang được giữ lại làm MỘT quyết định duy nhất — tránh trường hợp
publish trước bằng tên "MasA" rồi phải đổi thành "West A" sau, tương đương
đổi `<title>` của trang đã index (điều `SEOEXPANSIONPLAN.md` ràng buộc #4
cấm — dù đây là trang mới chưa publish nên về kỹ thuật không vi phạm, nhưng
tinh thần tránh đổi tên sau khi lên là như nhau). Chỉ cần 1 câu trả lời của
anh/chị ("West A = MasA, đúng thứ tự" hoặc "giữ nguyên MasA, không đổi
tên") là đủ để mở khoá.

## D — Tòa dưới ngưỡng (liệt kê text ở trang phân khu)

**Chưa thực hiện ở Phase 2 này.** Đây là việc sửa 5 file `index.html` phân
khu (Sapphire, Sakura, Imperia, Canopy, Tonkin) — đúng luật D yêu cầu, đã
thiết kế sẵn cách làm (mục E dưới), nhưng cố tình **không chạy** trong vòng
duyệt template này để giữ đúng phạm vi mục F ("3 trang mẫu... CHƯA publish"
— sửa thêm 5 file khác trước khi template được duyệt sẽ lặp lại đúng rủi ro
"nhân bản một lỗi ra nhiều trang" mà mục F muốn tránh, chỉ là nhân ra trang
phân khu thay vì trang tòa). Sẽ làm ngay sau khi mục F được duyệt.

5 tòa dưới ngưỡng thuộc phạm vi 5 phân khu đã duyệt (không tính GS2/GS3 vì
Miami đang tạm dừng — mục C1): **I4 (2 căn), I2 (2 căn)** → khối "Các tòa
thuộc Imperia"; **S1.06 (2 căn), S2.03 (2 căn), S2.05 (2 căn)** → khối "Các
tòa thuộc Sapphire". Sakura, Canopy, Tonkin không có tòa nào dưới ngưỡng.

## E — Ranh giới sở hữu với `SEO-CONTENT-PLAN.md` (đã thiết kế, chưa áp dụng)

Quy ước marker cho khối "Các tòa thuộc {Phân khu}" khi triển khai (Phase kế
tiếp, sau khi F được duyệt):

```html
<!-- BUILDING-LINKS:START (sinh tự động, không sửa tay — xem scripts/sinh-trang-toa.py) -->
<h2>Các tòa thuộc Sapphire</h2>
<div class="lq">
  <a href="/s1-01-vinhomes-smart-city/">Tòa S1.01 – 10 căn trống, từ 6,5 triệu</a>
  ...
  <span class="toa-chua-du-can">Tòa S1.06 – 2 căn trống</span>
</div>
<!-- BUILDING-LINKS:END -->
```

Script sinh khối mới sẽ tìm đúng cặp marker này trong mỗi file phân khu
(giống hệt cơ chế `TOA:START/END` đã dùng cho sitemap ở mục B2) và chỉ ghi
đè phần ở giữa — không đụng phần còn lại của trang, kể cả khi
`SEO-CONTENT-PLAN.md` sau này chèn thêm nội dung pillar/cẩm nang ở chỗ
khác trong cùng file. Sở hữu rõ ràng theo đúng yêu cầu:

| Khối | Sở hữu |
|---|---|
| `<!-- BUILDING-LINKS:START/END -->`, breadcrumb, `BreadcrumbList` JSON-LD | Kế hoạch trang tòa (tài liệu này) |
| Nội dung mô tả, cẩm nang, bài so sánh | `SEO-CONTENT-PLAN.md` |

Về `sinh-trang-toa.py` và Cluster 3: đã thêm ghi chú thẳng vào docstring
script (đoạn "GHI CHÚ VỀ CLUSTER 3") — có thể tái dùng nếu Cluster 3 triển
khai, nhưng Phase 2 không refactor cho mục đích đó.

## F — Duyệt template: 3 trang mẫu

### F.1 — Đã sinh (file thật, xem trực tiếp trong repo)

| Trang | Phân khu | Hồ sơ | Số căn | Loại căn |
|---|---|---|---|---|
| `/s1-01-vinhomes-smart-city/` | Sapphire | Nhiều căn | 10 | Studio, 1N+, 2N, 2N+ |
| `/sa2-vinhomes-smart-city/` | Sakura | Chỉ 1-2 loại căn | 4 | Studio, 3N |
| `/tk2-vinhomes-smart-city/` | Tonkin | Sát ngưỡng | 4 | Studio, 2N, 2N+ |

(Không có tòa nào trong 5 phân khu đã duyệt đúng 3 căn ngoài Sapphire —
S1.05/S4.03 là 2 tòa duy nhất ở đúng ngưỡng 3, cả hai đều Sapphire, trùng
phân khu với mẫu 1 — nên chọn TK2 (4 căn, phân khu khác) làm mẫu "sát
ngưỡng" để đủ 3 phân khu khác nhau như yêu cầu.)

`/s4-01-vinhomes-smart-city/` (trang sống) cũng được chạy lại qua script
mới — diff với bản trước khi sửa **chỉ có 3 khác biệt**: thêm `ItemList`
vào JSON-LD, thêm khối "Các tòa khác thuộc Sapphire", và một dấu cách thừa
quanh dấu gạch ngang trong `.tt` được chuẩn hoá lại cho khớp mô tả — không
đổi `<title>`, canonical, breadcrumb, thẻ căn, hay bất kỳ số liệu nào.

### F.2 — Bảng tự kiểm

| Hạng mục | S1.01 | SA2 | TK2 | Cách kiểm |
|---|---|---|---|---|
| Canonical self, đúng URL | ✅ | ✅ | ✅ | `grep rel="canonical"`, đúng 1 dòng/trang, trỏ về chính URL |
| GA4 (`G-VF9KHC5TWD`) | ✅ | ✅ | ✅ | `grep`, đúng 2 lần (script + config)/trang |
| `ItemList` JSON-LD | ✅ | ✅ | ✅ | `numberOfItems` khớp đúng số thẻ căn hiển thị |
| `BreadcrumbList` JSON-LD | ✅ | ✅ | ✅ | 3 cấp: Trang chủ › Phân khu › Tòa, đúng URL từng cấp |
| Liên kết nội bộ | ✅ | ✅ | ✅ | Mỗi trang có: link về phân khu, link loại căn có thật, link "Các tòa khác cùng phân khu" (S1.01: 5 link, SA2: 3 link, TK2: 1 link — đúng số tòa cùng phân khu đang đạt ngưỡng, xem mục F.4) |
| Hiển thị mobile | ✅ | ✅ | ✅ | Chụp màn hình thật ở viewport 390×844 (iPhone 12/13) bằng Chromium qua Playwright, phục vụ qua local server — không đoán, đã xem trực tiếp. Layout dùng đúng `assets/v3.css` sẵn có, không thêm CSS |
| Trùng lặp nội dung < 60% | ⚠️ **1/3 cặp còn vượt nhẹ** | | | Xem F.3 |

### F.3 — Kiểm tra trùng lặp nội dung (phát hiện quan trọng nhất của Phase 2)

**Vòng đo đầu tiên** (dùng nguyên bản template đã sinh trước khi sửa gì),
so `<main>` của 3 trang mẫu:

| Cặp | Trùng lặp |
|---|---|
| S1.01 vs SA2 | 55,2% |
| S1.01 vs TK2 | 40,9% |
| SA2 vs TK2 | **76,9%** ❌ vượt 60% |

Đào sâu: 76,9% chủ yếu đến từ MỘT câu văn cố định 100% giống hệt trên mọi
trang tòa (kể cả bản S4.01 gốc) — "Danh sách được dựng lại từ dữ liệu căn
của bên em mỗi ngày, nên căn nào đã có khách thuê sẽ tự biến mất khỏi trang
thay vì nằm lại làm mất công anh/chị hỏi." — không chứa dữ liệu, thuần giải
thích, nặng ký hơn hẳn ở những trang ít căn (SA2, TK2 chỉ 4 căn nên đoạn
văn xuôi chiếm tỷ trọng cao trong tổng nội dung).

**Đã sửa**: bỏ hẳn câu đó, gộp phần "cập nhật {ngày}" còn giữ vào cuối đoạn
2. Đo lại: SA2 vs TK2 còn 74,7% — giảm nhưng chưa đủ.

**Đo thêm ở quy mô lớn hơn để biết mức độ nghiêm trọng thật** (không chỉ
tin vào 3 mẫu): sinh thử **cả 24 tòa** đủ điều kiện (chỉ để đo, không giữ
lại — xem cách dọn ở cuối mục này), so trùng lặp từng cặp trong 276 cặp có
thể có:

| Phạm vi so sánh | Số cặp vượt 60% | Tỷ lệ |
|---|---|---|
| Toàn bộ `<main>` (kể cả lưới thẻ căn + bảng giá) | 99/276 | 35,9% |
| Chỉ 2 đoạn văn xuôi tự do (`section.bai`, phần duy nhất không phải heading/CTA/bảng cố định) | 268/276 | **97,1%** |

Kết luận: đoạn văn xuôi — phần lẽ ra phải là "nội dung riêng" của từng
trang — thực chất vẫn là một khung câu cố định, chỉ đổi số/tên. Đây đúng là
loại lỗi mục F được lập ra để bắt trước khi nhân ra 33 lần.

**Đã sửa tiếp**: thêm 3 biến thể cho câu 1 và 2 biến thể cho câu 2 (giữ
nguyên số liệu thật, chỉ đổi cách diễn đạt), chọn theo tổng mã ký tự của mã
tòa — **cố định (deterministic), không phải ngẫu nhiên**, để chạy lại nhiều
lần vẫn ra đúng một bản cho cùng một tòa (đúng yêu cầu gốc của script).

**Đo lại sau khi thêm biến thể câu** (lại trên cả 24 tòa):

| Phạm vi so sánh | Trước | Sau | Cải thiện |
|---|---|---|---|
| Toàn bộ `<main>` | 99/276 (35,9%) | 82/276 (29,7%) | −17 cặp |
| Chỉ văn xuôi tự do | 268/276 (97,1%) | 68/276 (24,6%) | −200 cặp |

Trên riêng 3 trang mẫu: SA2 vs TK2 từ 76,9% → **63,8%** — cải thiện rõ
nhưng **vẫn vượt 60%**.

**Đánh giá trung thực, không né tránh**: việc xoay vòng câu chữ đã giảm
đáng kể trùng lặp cơ học (đặc biệt ở phần văn xuôi: giảm 75%) nhưng KHÔNG
giải quyết triệt để, vì nguyên nhân gốc là cấu trúc dữ liệu, không phải
cách viết câu — tòa càng ít căn (ngưỡng 3-4) thì phần "nội dung riêng" thật
sự (lưới thẻ căn, bảng giá) càng mỏng, khiến phần khung câu cố định (dù đã
có nhiều biến thể) chiếm tỷ trọng tương đối càng cao. Thêm biến thể câu nữa
sẽ giảm tiếp con số đo được, nhưng đến một lúc nào đó bắt đầu giống
"spinning" nội dung (nhiều cách viết cho cùng một ý, không thêm giá trị
thật) — chính là kiểu nội dung mà hệ thống phát hiện trùng lặp của Google
được thiết kế để nhận ra, nên không đề xuất tiếp tục theo hướng này.

**3 lựa chọn cho anh/chị quyết định trước khi publish 24 tòa** (không tự
chọn thay):

1. **Chấp nhận rủi ro còn lại**: các cặp vượt 60% đều là những tòa RẤT ít
   căn (3-4), nơi thẻ căn thật (ảnh, giá, mã căn) mới là tín hiệu SEO chính
   theo đúng tinh thần `SEOEXPANSIONPLAN.md` ("khối số liệu thật — lợi thế
   cạnh tranh lớn nhất"), còn phép đo ký tự thô không phân biệt được "hai
   tòa nhỏ giống nhau về cấu trúc câu" với "nội dung rác/spam thật" như
   thuật toán Google dùng (DOM-aware, không chỉ đếm ký tự trùng). Publish
   đủ 24, theo dõi Search Console mục G.
2. **Nâng ngưỡng publish** từ 3 lên cao hơn (vd 5) để giảm số tòa "mỏng",
   chấp nhận publish ít trang hơn ở đợt đầu.
3. **Giữ ngưỡng 3, nhưng bớt phần văn xuôi cố định hơn nữa** cho tòa dưới
   một mốc căn nào đó (vd ≤4 căn thì bỏ hẳn đoạn văn xuôi, chỉ giữ số liệu +
   thẻ căn + bảng giá) — giảm tối đa phần "khung câu" ở đúng nhóm rủi ro
   cao nhất mà không cần bịa thêm cách diễn đạt.

Cá nhân tôi nghiêng về lựa chọn 3 (ít thay đổi kiến trúc nhất, xử lý đúng
gốc rủi ro), nhưng đây là quyết định về mức độ chấp nhận rủi ro SEO nên để
anh/chị chọn.

**Dọn dẹp sau khi đo**: 24 trang sinh ra để đo đã bị xoá ngay sau khi lấy
số liệu, **trừ 3 trang mẫu đã duyệt và S4.01** — `data/published-buildings.json`
đã được khôi phục về đúng 4 dòng tương ứng. `git status` cuối phiên xác
nhận không còn thư mục thừa nào.

### F.4 — Kiểm thử nhánh "hết căn"

Không có tòa nào trong dữ liệu thật hiện về 0 căn để thử tự nhiên, nên đã
tạo một tòa giả lập (`S999`, xoá ngay sau khi xem kết quả, không commit) để
xác nhận nhánh này chạy đúng: hiển thị "Tòa X hiện chưa có căn trống", 0
`ItemList` (không có gì để liệt kê), vẫn có breadcrumb + khối "Các tòa khác
thuộc {phân khu}" với 5 link tới tòa khác — đúng thiết kế mục B1.

## G — Sau khi publish (ghi để nhớ)

Sau khi 24 (hoặc số lượng đã chốt theo lựa chọn ở mục F.3) trang được
publish: **mở Google Search Console sau 3 tuần**, xem tỷ lệ index thật của
cả lô (Pages report, so URL đã nộp sitemap vs URL "Indexed"). Đây là phép
đo có ý nghĩa thống kê duy nhất khả thi — so với thử nghiệm n=1 kéo dài 4-6
tuần đã bị thay thế ở mục A. Không đo được bằng bất kỳ công cụ nào có sẵn
trong phiên làm việc này.

---

### 🛑 Checkpoint

Dừng lại chờ duyệt: (1) template 3 trang mẫu (mục F.2), (2) một trong 3 lựa
chọn xử lý trùng lặp nội dung (mục F.3 — **cần trả lời trước khi publish
hàng loạt**), (3) xác nhận mapping Miami/Lumiere (mục C1), (4) xác nhận tên
hiển thị Masteri (mục C2). Sau khi có đủ 4 câu trả lời mới sang: (a) publish
đủ số tòa đã chốt, (b) thêm mốc `TOA:START/END` vào `sitemap.xml`, (c) làm
khối "Các tòa thuộc {Phân khu}" cho 5 (hoặc 7) trang phân khu theo mục D/E.

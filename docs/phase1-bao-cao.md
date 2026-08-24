# PHASE 1 — BÁO CÁO: trích xuất & chuẩn hoá danh sách tòa

> Trả lời đầy đủ 5 việc bổ sung (B1–B5) theo yêu cầu duyệt Phase 0. Sản phẩm
> dữ liệu: `data/buildings.json`, `docs/buildings-mapping.md`,
> `docs/buildings-gap.md`, script `scripts/trich-xuat-toa.py`. File này là
> phần diễn giải/phân tích đi kèm — không lặp lại dữ liệu thô.

---

## B1 — Nguồn của mapping tòa → phân khu

**Kết luận ngắn: `data.json` không có cột phân khu. 100% (40/40) tòa trong
`data/buildings.json` mang `"mapping": "inferred"`. Không có tòa nào là
`"from-data"`, vì trường dữ liệu đó không tồn tại trong schema — không phải
vì suy luận thất bại ở một vài tòa.**

Đây là điều chỉnh so với giả định ban đầu trong `SEOEXPANSIONPLAN.md`
(dòng 93: *"Chỉ map khi dữ liệu gốc có thông tin phân khu... nếu phải suy
luận từ tiền tố mã tòa, đánh dấu inferred"*) — tài liệu gốc để ngỏ khả năng
có cả hai loại, nhưng khảo sát Phase 0 đã xác nhận field `Tòa` là cột DUY
NHẤT liên quan tới vị trí trong `data.json` (12 field, xem `docs/audit-repo.md`
mục 2). Không có field nào tên `Phân khu`/`Zone`/`Cluster`. Vì vậy **toàn bộ
40 tòa cần người review xác nhận thủ công**, không phải một danh sách con.

**Vì sao mức độ tin cậy vẫn cao dù 100% là "inferred":**

1. Hàm suy luận `phan_khu_tu_toa()` không phải viết mới cho việc này — nó là
   hàm đã chạy trong production từ trước (dùng để tổ chức `anh-can-ho/` theo
   tên file, và được `sinh-trang-toa.py` tái sử dụng cho chính trang S4.01
   đang live). Nếu sai, ảnh 400+ file trong `anh-can-ho/` và trang S4.01 đã
   sai từ trước, không phải rủi ro mới do Phase 1 tạo ra.
2. Đối chiếu chéo với nội dung ĐÃ PUBLISH (không phải suy luận của tôi): 6/8
   trang phân khu hiện có tự mô tả bằng lời tên các tòa thuộc phân khu đó
   (`sapphire/index.html`, `masteri/index.html`, `sakura/index.html`,
   `imperia/index.html`, `canopy/index.html`, `tonkin/index.html`) — toàn bộ
   đều khớp 100% với danh sách tòa mà `phan_khu_tu_toa()` gán cho phân khu
   đó (bảng chi tiết ở `docs/buildings-gap.md` mục 1). Đây là bằng chứng độc
   lập, không dùng lại chính logic đang được kiểm tra.
3. **Riêng 2/8 phân khu (Miami, Lumiere) không có câu văn liệt kê tên tòa để
   đối chiếu** — với 5 tòa Miami (GS1/GS2/GS3/GS5/GS6) và 2 tòa Lumiere
   (A2/A3), việc suy luận phân khu **chưa có bằng chứng độc lập xác nhận**,
   dù cùng dùng một hàm đã đúng ở 6 phân khu kia. Đề nghị người review xác
   nhận riêng 7 tòa này trước khi Phase 2 publish.

**Danh sách đầy đủ 40 tòa cần xác nhận** nằm trong `data/buildings.json`
(field `mapping` của mọi phần tử đều là `"inferred"`) — không tách file
riêng vì tách ra sẽ là bản sao thứ hai của cùng dữ liệu, dễ lệch.

## B2 — Đủ mẫu số

Tính từ `data.json` hiện tại (chạy `scripts/trich-xuat-toa.py --thu`,
24/08/2026), lọc theo `Hiển thị trên Web`:

| Nhóm | Số tòa | Ghi chú |
|---|---|---|
| Tổng số mã tòa xuất hiện trong `data.json` (**mọi trạng thái hiển thị**, kể cả căn đã cho thuê/ẩn) | **40** | Không có tòa nào chỉ tồn tại dưới dạng căn ẩn — xem dòng dưới |
| Trong đó: có ≥1 căn **đang hiển thị** (0 căn hiển thị) | **0** | Không có tòa "0 căn" — mọi tòa từng xuất hiện trong Sheet hiện đều có ít nhất 1 căn đang cho thuê |
| — Đạt ngưỡng **≥3 căn** (Phase 2 sẽ sinh trang) | **33** | 82,5% số tòa |
| — Dưới ngưỡng, **1–2 căn** (không sinh trang riêng) | **7** | I4(2), S106(2), GS3(2), S203(2), GS2(2), S205(2), I2(2) — tất cả đúng 2 căn, không có tòa nào 1 căn |

**Độ phủ**: 33/40 = 82,5% số tòa có dữ liệu sẽ có trang riêng ngay ở Phase 2.
7 tòa còn lại (17,5%) chỉ cách ngưỡng 1 căn — nhiều khả năng sẽ tự đạt ngưỡng
ở các lần trích xuất sau nếu chủ nhà thêm căn, không cần hành động gì thêm
(đúng cơ chế "không hồi tố, chỉ ngừng tạo mới cho tổ hợp chưa từng lên" mà
`SEO-CONTENT-PLAN.md` mục 3.2 đã áp dụng cho Cluster 3 — nên giữ nhất quán).

Không có canonical nào gộp từ nhiều biến thể raw khác nhau (0/40) — xem
`docs/buildings-mapping.md`.

## B3 — `docs/buildings-gap.md`

Đã tạo, xem file riêng. Tóm tắt 2 phát hiện chính cần xác nhận thủ công:
tên gọi "West A/B/C/D" (nội dung `masteri/index.html`) chưa được xác nhận là
tương ứng 1-1 với mã `MasA/MasB/MasC/MasD` trong `data.json`; và `GS2` (ví
dụ URL trong chính `SEOEXPANSIONPLAN.md`) hiện dưới ngưỡng, sẽ không có
trang ở đợt publish đầu Phase 2 trừ khi dữ liệu thay đổi trước đó.

## B4 — Cơ chế cập nhật lại (ưu tiên cao nhất)

### Câu 1: `sinh-trang-toa.py` chạy thủ công hay tự động?

**Tự động.** Được gọi vô điều kiện ở bước "Sinh trang theo tòa" trong
`.github/workflows/cap-nhat-so-can.yml`, chạy theo `cron: "0 1,9,17 * * *"`
— 3 lần/ngày, giờ Việt Nam 08:00/16:00/00:00 — đúng lịch mà 25 trang danh
mục khác cũng dùng. Không cần chạy tay.

### Câu 2: vì sao tới nay chỉ có 1 trang tòa?

**Không phải do thiếu tự động hoá — đây là quyết định có chủ đích, ghi rõ
trong chính docstring của script** (`scripts/sinh-trang-toa.py` dòng 6-7):

> *"Đây là thử nghiệm MỘT trang duy nhất: đo Search Console 4-6 tuần rồi
> mới tính chuyện sinh hàng loạt."*

Và dòng 45-46 (comment ngay trên biến `CAC_TOA`):

> *"Hiện CHỈ có S4.01 - đây là thử nghiệm một trang, chưa mở rộng."*

**Đối chiếu ngày tạo qua git log**: cả `scripts/sinh-trang-toa.py` và
`s4-01-vinhomes-smart-city/index.html` được thêm vào repo ngày
**23/08/2026** — tức **mới chạy được khoảng 1 ngày** tính đến hôm nay
(24/08/2026), không phải 4-6 tuần như mốc đo lường mà chính script đề ra.

⚠️ **Cần anh/chị lưu ý trước khi sang Phase 2**: `SEOEXPANSIONPLAN.md` yêu
cầu mở rộng ngay từ 1 lên 33 trang, tức là **sớm hơn nhiều** so với mốc "đo
Search Console 4-6 tuần" mà chính người viết script S4.01 đặt ra ban đầu.
Đây không phải rủi ro kỹ thuật (hạ tầng đã sẵn sàng, xem câu 3) mà là câu
hỏi về **chiến lược đo lường**: mở rộng ngay sẽ mất khả năng so sánh "1
trang tòa có tăng traffic không" trước khi nhân rộng. Tôi vẫn sẽ làm theo
đúng chỉ đạo mở rộng ở Phase 2 vì đó là yêu cầu tường minh của anh/chị hôm
nay (ghi đè quyết định 1-ngày-tuổi trong code) — chỉ nêu ra để có ghi nhận
rõ ràng, không tự ý bỏ qua.

### Câu 3: đề xuất cơ chế để trang tòa tự sinh lại mỗi khi quỹ căn đổi

**Hạ tầng cần thiết đã tồn tại đầy đủ, không cần thêm workflow mới:**

1. Đã kiểm chứng bằng lệnh thật (`git add --dry-run -- '*.html'` trên một
   file thử trong thư mục con mới) rằng pathspec `'*.html'` trong bước
   commit của `cap-nhat-so-can.yml` (dòng `git add -- '*.html' sitemap.xml
   s4-01-vinhomes-smart-city can-ho sitemap-can-ho.xml`) **bắt được file
   HTML ở MỌI thư mục con, kể cả thư mục hoàn toàn mới/chưa từng commit**.
   → Khi Phase 2 mở rộng `CAC_TOA` từ 1 lên 33 dòng, 33 thư mục
   `{slug}-vinhomes-smart-city/index.html` mới sinh ra sẽ **tự động được
   `git add`, commit và push** ở lần chạy cron kế tiếp, không cần sửa dòng
   `git add` này. (Tên `s4-01-vinhomes-smart-city` trong lệnh đó hoá ra là
   thừa/dự phòng — `'*.html'` một mình đã đủ bao phủ.)
2. Vòng lặp `for toa, cau_hinh in CAC_TOA.items()` trong `main()` của
   `sinh-trang-toa.py` không có giới hạn số dòng — mở rộng dict lên 33 phần
   tử chạy đúng như 1 phần tử, không cần đổi logic.
3. **Một việc thật sự cần làm thủ công, đúng một lần**: `sitemap.xml` không
   tự thêm URL mới. `scripts/cap-nhat-sitemap.mjs` (chạy cùng workflow) CHỈ
   cập nhật `<lastmod>` của các `<url>` **đã có sẵn** trong file, không tạo
   khối `<url>` mới cho URL chưa từng khai báo (đọc kỹ `RE_KHOI_URL`/logic
   `main()` của script — nó lặp trên các khối `<url>` hiện có, không chèn
   thêm). → Phase 2/4 phải tự tay thêm 33 dòng `<url>` mới vào `sitemap.xml`
   khi publish (một lần, làm cùng lúc với tạo trang) — **sau đó** thì
   `cap-nhat-sitemap.mjs` sẽ tự giữ `<lastmod>` của 33 URL đó luôn mới, y
   hệt cách nó đang làm với S4.01.
4. **Khuyến nghị KHÔNG thêm trigger `push` theo `data.json`** để chạy
   real-time: Apps Script tự commit `data.json` ~30 phút/lần (~48
   lần/ngày). Một workflow chạy real-time theo mỗi lần push sẽ tốn 48 lần
   CI/ngày thay vì 3 lần, trong khi tần suất "cập nhật nhiều lần mỗi ngày"
   mà site quảng cáo (xem `llms.txt`) đã được đáp ứng đủ ở lịch 3 lần/ngày
   hiện có — đúng tần suất mà 25 trang danh mục khác đang chạy. Giữ nguyên
   lịch cron là đủ, không cần thay đổi hạ tầng CI.
5. Rủi ro "cron chạy trên nhánh làm việc" nêu ở `docs/audit-repo.md` mục 6
   thực ra **thấp hơn đã ghi**: theo hành vi chuẩn của GitHub Actions,
   `schedule` (cron) **chỉ chạy trên nhánh mặc định của repo**, không chạy
   trên nhánh PR — chỉ `workflow_dispatch` (chạy tay) mới có thể nhắm vào
   nhánh khác, và đó là hành động con người phải chủ động chọn nhánh. Không
   cần thêm rào chắn kỹ thuật ở Phase 1/2.

**Kết luận B4**: không có "cơ chế cập nhật lại" nào cần xây mới. Rủi ro "33
trang ghi cập nhật 24/08/2026 rồi đứng yên" mà anh/chị lo ngại **sẽ không
xảy ra về mặt kỹ thuật** — miễn là (a) 33 dòng cấu hình được thêm vào
`CAC_TOA` ở Phase 2, và (b) 33 dòng `<url>` được thêm tay vào `sitemap.xml`
đúng một lần lúc publish. Sau đó cơ chế 3 lần/ngày đã có sẵn tự lo phần còn
lại, giống hệt S4.01.

## B5 — Ma trận chồng chéo với `SEO-CONTENT-PLAN.md`

| Hạng mục | `SEOEXPANSIONPLAN.md` (trang tòa) | `SEO-CONTENT-PLAN.md` (đợt trước) | File/trang dùng chung | Mức rủi ro ghi đè |
|---|---|---|---|---|
| 8 trang phân khu (`sapphire/index.html`...) | Phase 3: thêm khối "Các tòa thuộc {Phân khu}" + link nội bộ tới trang tòa, đặt **phía trên** `section.luoi`. Phase 5: viết lại đoạn mô tả chung chung bằng nội dung thật. | Mục 2.1 (P1): viết 5 bài **pillar mới, file riêng** (vd `cho-thue-can-ho-sapphire-smart-city.html`) cho 5/8 phân khu, yêu cầu "internal link 2 chiều bắt buộc: pillar mới ↔ trang danh mục cùng phân khu". Mục 3.1 (P2, Cluster 3, **chưa duyệt**): tạo `/sapphire/2pn/`... cũng cần link ra từ `sapphire/index.html`. | **Cùng 8 file `index.html`** | **CAO.** Cả 3 việc (khối tòa mới, link ra pillar mới, link ra Cluster 3 nếu triển khai) đều ghi vào cùng khu vực nội dung của cùng 8 file. Không phải xung đột Git tự động (khác dòng thời điểm) mà là rủi ro **hai đợt làm việc cách nhau vài tuần cùng sửa một trang** — người làm sau dễ không biết khối trước đã thêm gì nếu không đọc lại file. Khuyến nghị Phase 3 khi viết phải đọc lại toàn bộ file hiện tại (không giả định cấu trúc cũ) và đặt khối mới ở vị trí có thể mở rộng thêm (không hard-code "đây là khối liên kết duy nhất"). |
| `scripts/dung-lai-trang-danh-muc.py` (chạy tự động 3 lần/ngày, ghi đè 6 khối cố định của 25 trang danh mục — trong đó có 8 trang phân khu) | Không trực tiếp nhắc tới, nhưng Phase 3 THÊM một khối HTML mới vào chính 8 file mà script này đang tự động ghi đè một phần. | Không nhắc tới trong `SEO-CONTENT-PLAN.md`. | 8 trang phân khu | **TRUNG BÌNH.** Đã đọc source: script chỉ ghi đè `section.luoi`, `h2.tieu-de-luoi`, `p.tt` (khối đầu), `div.sl`, `table.bang`, `span[data-so]` — và **tự khai rõ "không đụng khối `.lq`"**. Miễn khối "Các tòa thuộc {Phân khu}" mới của Phase 3 nằm ngoài 6 vùng này (đúng yêu cầu gốc "đặt phía trên `section.luoi`" đã thoả), script tự động sẽ không xoá nó. **Vẫn cần kiểm tra thực tế sau khi code Phase 3 xong** bằng cách chạy thử `dung-lai-trang-danh-muc.py --thu` và diff, không chỉ tin vào đọc code. |
| `scripts/sinh-trang-toa.py` | Phase 2: mở rộng trực tiếp (thêm `CAC_TOA`, `ItemList`, UI hết-căn, link ngang 3-5 tòa). | Mục 5 (P1/P2) nói rõ: nếu Cluster 3 (loại×phân khu) qua ngưỡng, sẽ **"tái dùng `dung-lai-trang-danh-muc.py`/`sinh-trang-toa.py`, không viết logic mới."** | `scripts/sinh-trang-toa.py` | **TRUNG BÌNH-CAO (thiết kế, chưa phải xung đột file).** `SEO-CONTENT-PLAN.md` đã dự tính từ trước sẽ tái sử dụng chính file mà Phase 2 của kế hoạch này sắp sửa đổi cấu trúc lớn. Cluster 3 chưa triển khai (P2, "để sau") nên chưa có xung đột thật, nhưng Phase 2 nên viết `sinh-trang-toa.py` theo hướng **dễ tái sử dụng cho tổ hợp loại×phân khu sau này** (tách hàm dựng thẻ căn / thống kê / khung HTML thành các hàm độc lập, không gộp cứng vào một hàm `dung_trang()` chỉ nhận tham số theo tòa) — không bắt buộc làm ngay, chỉ là định hướng nên tránh khoá cứng. |
| `sitemap.xml` | Phase 4: thêm 33 URL trang tòa mới (thủ công một lần, xem B4 câu 3). | Mục 4: nếu triển khai P1 (pillar/cẩm nang/so sánh/cluster 5), cũng thêm URL mới vào cùng file. | `sitemap.xml` | **THẤP.** Cùng file nhưng thêm dòng mới ở vị trí khác nhau — xung đột chỉ xảy ra nếu 2 PR chỉnh sitemap không rebase trước khi merge, Git xử lý được phần lớn trường hợp tự động. |
| 25 trang danh mục — `FAQPage` JSON-LD (đã triển khai, xem `SEO-IMPLEMENTATION-REPORT.md`) | Không động vào — trang tòa dùng luồng JSON-LD riêng (`BreadcrumbList`, sắp thêm `ItemList`). | Đã xong (lịch sử, P0 của đợt trước). | 25 file `index.html` cùng nhóm | **THẤP.** Việc đã merge trước, không hoạt động song song với Phase 2/3. |
| `README.md` (mục "Thêm một trang danh mục mới") | Phase 2 nên bổ sung mục hướng dẫn riêng cho quy trình trang tòa (khác hẳn quy trình 25 trang: không dùng `dong-bo-can.js`/`bo-loc-trang`, dùng `CAC_TOA` + build script). | Không động. | `README.md` | **THẤP.** Chỉ một bên sửa, nhưng nên làm ở Phase 2 để tránh người sau lẫn lộn 2 quy trình sinh trang khác nhau trong cùng repo. |

**Tổng kết B5**: điểm va chạm thật sự đáng lo là **8 file trang phân khu**
(bị 2 kế hoạch cùng nhắm tới cho mục đích internal-linking) và **định hướng
thiết kế của `sinh-trang-toa.py`** (đã được đợt audit trước "đặt cọc" sẽ
tái dùng cho Cluster 3). Không có xung đột nào cần giải quyết ngay ở Phase 1
— ghi nhận để Phase 3 code cẩn thận, không giả định mình là người đầu tiên
và cuối cùng chạm vào các file đó.

---

## Sản phẩm Phase 1 (tổng hợp)

| File | Nội dung |
|---|---|
| `scripts/trich-xuat-toa.py` | Script trích xuất, dùng lại logic từ `sinh-trang-toa.py`/`sinh-danh-sach-anh.py` qua importlib, có cờ `--thu` |
| `data/buildings.json` | 40 tòa, đủ field theo mẫu `SEOEXPANSIONPLAN.md` (+ `ma_toa_du_lieu`, `dat_nguong_sinh_trang` bổ sung để Phase 2 lọc) |
| `docs/buildings-mapping.md` | Bảng biến thể raw → canonical (rỗng về mặt xung đột: 0/40 tòa có >1 biến thể) |
| `docs/buildings-gap.md` | Đối chiếu tòa trong dữ liệu vs tòa nhắc trong nội dung đã publish + `SEO-CONTENT-PLAN.md` |
| `docs/audit-repo.md` (cập nhật) | Ghi nhận xác nhận hreflang (A1) và duyệt Phase 0 |
| `docs/phase1-bao-cao.md` | File này |

---

### 🛑 Checkpoint

Dừng sau Phase 1 theo đúng yêu cầu. Chờ duyệt B1–B5 (đặc biệt lưu ý phần
"⚠️" ở B4 câu 2 — mốc đo lường 4-6 tuần của thử nghiệm S4.01 chưa đạt) trước
khi sang Phase 2. Phase 2 sẽ chuẩn bị 3 trang mẫu (3 phân khu khác nhau,
theo yêu cầu mục D) để duyệt template trước khi sinh đủ 33 trang.

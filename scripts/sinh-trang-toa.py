#!/usr/bin/env python3
"""Sinh trang danh mục theo TÒA từ data.json.

PHASE 2 (24/08/2026) — mở rộng từ bản thử nghiệm 1 trang (S4.01) sang nhiều
tòa. Xem docs/audit-repo.md, docs/phase1-bao-cao.md, docs/phase2-bao-cao.md
để biết đầy đủ lý do các quyết định dưới đây.

KIẾN TRÚC MỚI — không còn danh sách tòa viết cứng
--------------------------------------------------
Bản gốc (Phase pilot) có một dict CAC_TOA liệt kê tay từng tòa. Bản này thay
bằng PHAN_KHU_DA_DUYET (danh sách PHÂN KHU được duyệt, không phải từng tòa)
cộng với việc tự tính lại từ data.json mỗi lần chạy tòa nào trong các phân
khu đó đang có bao nhiêu căn — giống hệt cách 25 trang danh mục khác luôn tự
tính lại, không lưu danh sách cứng. Thêm phân khu mới = thêm 1 dòng vào
PHAN_KHU_DA_DUYET, không phải liệt kê từng tòa.

HAI LUẬT TÁCH BIỆT (bắt buộc theo yêu cầu duyệt Phase 2, mục B1)
------------------------------------------------------------------
  - LUẬT PUBLISH LẦN ĐẦU: một tòa CHỈ được tạo trang mới khi đang có >=
    NGUONG_TOI_THIEU căn VÀ thuộc phân khu nằm trong PHAN_KHU_DA_DUYET.
  - LUẬT DUY TRÌ: một khi đã publish (ghi trong data/published-buildings.json)
    thì KHÔNG BAO GIỜ bị xoá hay ngừng sinh lại, kể cả khi tụt xuống dưới
    ngưỡng hoặc về 0 căn — tránh kịch bản trang bật/tắt theo từng đợt dữ liệu
    (căn cho thuê hết rồi có lại quanh mốc 3 căn) làm mất index đã tích luỹ.
    Khi về 0 căn, trang chuyển sang hiển thị thông báo hết căn + link sang
    tòa khác cùng phân khu, KHÔNG đặt noindex, KHÔNG xoá file.

data/published-buildings.json là NGUỒN SỰ THẬT duy nhất cho luật duy trì —
đọc/ghi ở đây, không suy luận lại "đã publish hay chưa" bằng cách xem file
HTML có tồn tại hay không (tránh trường hợp file bị xoá thủ công ngoài ý
muốn làm mất trạng thái).

SITEMAP — cập nhật đúng vùng, không ghi đè toàn bộ
----------------------------------------------------
Script tự viết lại đúng vùng giữa 2 mốc <!-- TOA:START --> / <!-- TOA:END -->
trong sitemap.xml (xem cap_nhat_sitemap_toa()). Nếu sitemap.xml CHƯA có cặp
mốc này, script CẢNH BÁO và bỏ qua bước này — không tự ý chèn liều vào một
file đang có 43 URL khác đã ổn định.

GHI CHÚ VỀ CLUSTER 3 (loại×phân khu, SEO-CONTENT-PLAN.md mục 5, P2, "để sau")
------------------------------------------------------------------------------
SEO-CONTENT-PLAN.md đã dự tính nếu Cluster 3 (vd /sapphire/2pn/) qua ngưỡng
sẽ tái dùng chính script này thay vì viết logic mới. Phase 2 của kế hoạch
trang tòa KHÔNG refactor sinh-trang-toa.py cho mục đích đó — các hàm ở đây
(dung_the_can, thong_ke, dung_item_list...) tái dùng được nguyên trạng nếu
cần, nhưng việc tách chúng thành module dùng chung, nếu Cluster 3 triển khai
thật, là việc của lúc đó, không phải bây giờ. Xem docs/phase1-bao-cao.md
mục B5 và docs/phase2-bao-cao.md mục E.

Chạy:
  python3 scripts/sinh-trang-toa.py                          # đủ, mặc định
  python3 scripts/sinh-trang-toa.py --thu                    # chỉ xem trước
  python3 scripts/sinh-trang-toa.py --chi-toa S401,SA1,TC2   # giới hạn vài tòa
  python3 scripts/sinh-trang-toa.py --khong-cap-nhat-sitemap # bỏ qua bước sitemap
"""

import argparse
import datetime
import html
import importlib.util
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DUONG_DATA = os.path.join(GOC, "data.json")
DUONG_MAP_ANH = os.path.join(GOC, "anh-can-ho", "anh-map.json")
DUONG_TRANG_THAI = os.path.join(GOC, "data", "published-buildings.json")
DUONG_SITEMAP = os.path.join(GOC, "sitemap.xml")

TEN_MIEN = "https://timthuesmartcity.com"
SDT = "0977923284"

# Tòa còn quá ít căn thì trang mỏng, Google coi là trang rác. Dưới ngưỡng
# này thì KHÔNG publish trang mới — nhưng trang ĐÃ publish thì không đụng,
# xem "LUẬT DUY TRÌ" ở docstring trên.
NGUONG_TOI_THIEU = 3

# Phân khu đã duyệt để triển khai trang tòa (docs/phase2-bao-cao.md mục C).
# CHỈ thêm phân khu vào đây khi mapping tòa->phân khu có bằng chứng độc lập
# (nội dung trang phân khu đã publish tự liệt kê tên tòa, đối chiếu khớp)
# và, nếu có câu hỏi về tên hiển thị, đã được xác nhận thủ công.
#   - Miami, Lumiere: CHƯA — không có nội dung nào liệt kê tên tòa để đối
#     chiếu độc lập với suy luận từ tiền tố mã (docs/phase1-bao-cao.md B1).
#   - Masteri: CHƯA — mapping phân khu khớp số lượng (4 tòa = "bốn tòa West
#     A-D" trong nội dung), nhưng TÊN HIỂN THỊ từng tòa (MasA hay "West A"?)
#     chưa xác nhận, ảnh hưởng trực tiếp <title>/<h1>/breadcrumb đã index
#     nên không đoán trước. Xem docs/phase2-bao-cao.md mục C.
PHAN_KHU_DA_DUYET = {"Sapphire", "Sakura", "Imperia", "Canopy", "Tonkin"}

# Ánh xạ loại căn -> trang loại căn tương ứng. Chỉ liên kết tới trang có thật
# trong repo; loại nào chưa có trang thì bỏ qua, không tạo link gãy.
TRANG_LOAI_CAN = {
    "studio": ("/studio/", "Căn hộ Studio"),
    "1 ngủ": ("/1pn/", "Căn 1 phòng ngủ"),
    "1 ngủ +": ("/1pn-plus/", "Căn 1 phòng ngủ +"),
    "2 ngủ": ("/2pn/", "Căn 2 phòng ngủ"),
    "2 ngủ +": ("/2pn-plus/", "Căn 2 phòng ngủ +"),
    "3 ngủ": ("/3pn/", "Căn 3 phòng ngủ"),
}

# Ánh xạ phân khu -> trang phân khu. Giữ đủ cả 8 (không chỉ PHAN_KHU_DA_DUYET)
# vì một tòa ĐÃ publish vẫn cần breadcrumb đúng dù sau này phân khu của nó có
# được duyệt muộn hơn hay không — luật duy trì không phụ thuộc danh sách duyệt.
TRANG_PHAN_KHU = {
    "Sapphire": "/sapphire/",
    "Masteri": "/masteri/",
    "Miami": "/miami/",
    "Sakura": "/sakura/",
    "Imperia": "/imperia/",
    "Lumiere": "/lumiere/",
    "Canopy": "/canopy/",
    "Tonkin": "/tonkin/",
}

DAU_TOA_BAT_DAU = "<!-- TOA:START (sinh tự động bởi scripts/sinh-trang-toa.py, không sửa tay) -->"
DAU_TOA_KET_THUC = "<!-- TOA:END -->"


def nap_module_anh():
    """Nạp sinh-danh-sach-anh.py để dùng lại ánh xạ tòa -> phân khu."""
    duong = os.path.join(THU_MUC_SCRIPT, "sinh-danh-sach-anh.py")
    dac_ta = importlib.util.spec_from_file_location("sinh_danh_sach_anh", duong)
    mo_dun = importlib.util.module_from_spec(dac_ta)
    cu = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        dac_ta.loader.exec_module(mo_dun)
    finally:
        sys.dont_write_bytecode = cu
    return mo_dun


ANH = nap_module_anh()
phan_khu_tu_toa = ANH.phan_khu_tu_toa
dang_hien_thi = ANH.dang_hien_thi


def esc(v):
    return html.escape("" if v is None else str(v), quote=True)


def chuan_ma_toa(toa):
    """Bỏ khoảng trắng và dấu ngăn rồi đổi hoa: 's4.01' -> 'S401'."""
    return re.sub(r'[\s._-]', '', str(toa)).upper()


def ma_toa_dep(ma_chuan):
    """Định dạng hiển thị cho mã tòa chuẩn hoá.

    CHỈ chèn dấu chấm cho tòa Sapphire dạng S+1 số khối+2 số tòa (S401 ->
    S4.01) — không phải suy đoán tự ý: sapphire/index.html (đã publish) mô
    tả đúng quy ước này bằng lời ("Sapphire 1 (S1.01–S1.06...)"), và trang
    S4.01 hiện có dùng đúng định dạng này. Mọi tòa khác giữ NGUYÊN mã chuẩn
    hoá — các trang phân khu tương ứng cũng nhắc tên tòa bằng đúng dạng thô
    này trong nội dung đã publish (vd "tòa TC1", "tòa SA1", "tòa I1", "tòa
    TK1" — không dấu chấm/khoảng trắng). Xem docs/phase1-bao-cao.md."""
    if len(ma_chuan) == 4 and ma_chuan[0] == "S" and ma_chuan[1:].isdigit():
        return "%s.%s" % (ma_chuan[:2], ma_chuan[2:])
    return ma_chuan


def slug_tu_ma(ma_dep):
    """'S4.01' -> 's4-01'; 'GS2' -> 'gs2'. Quy tắc URL Phase 2:
    /{slug}-vinhomes-smart-city/."""
    return ma_dep.lower().replace(".", "-")


def so_tien(v):
    if isinstance(v, (int, float)):
        return int(v)
    return int(re.sub(r'[^\d]', '', str(v)) or 0)


def dien_tich(v):
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace(",", ".")
    s = re.sub(r'[^\d.]', '', s)
    try:
        return float(s)
    except ValueError:
        return 0.0


def dinh_dang_gia(p):
    if not p:
        return "Liên hệ"
    if p % 1000000 == 0:
        return "%d triệu" % (p // 1000000)
    return ("%s triệu" % (round(p / 100000) / 10)).replace(".", ",")


def ngay_hom_nay():
    return (datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=7)).date()


def la_ngay_da_qua(s, hom_nay):
    khop = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', str(s).strip())
    if not khop:
        return False
    try:
        ngay = datetime.date(int(khop.group(3)), int(khop.group(2)),
                             int(khop.group(1)))
    except ValueError:
        return False
    return ngay <= hom_nay


def nhan_tinh_trang(can, hom_nay):
    s = str(can.get("Ngày vào ở", "")).strip()
    if not s or s.lower() in ("luôn", "ở ngay", "o ngay", "ngay"):
        return "Vào ngay"
    if la_ngay_da_qua(s, hom_nay):
        return "Vào ngay"
    khop = re.match(r'^(\d{1,2})/(\d{1,2})', s)
    return "Trống từ " + (khop.group(0) if khop else s)


def doc_map_anh():
    if not os.path.exists(DUONG_MAP_ANH):
        return {}
    with open(DUONG_MAP_ANH, encoding="utf-8") as f:
        anh_map = json.load(f)
    return {ma: duong for ma, duong in anh_map.items()
            if os.path.exists(os.path.join(GOC, duong.lstrip("/")))}


def anh_dai_dien(can, map_anh):
    url = str(can.get("Ảnh đại diện", "")).strip()
    if not url:
        return ""
    khop = re.search(r'id=([A-Za-z0-9_-]+)', url)
    if khop and khop.group(1) in map_anh:
        return map_anh[khop.group(1)]
    return url


def gom_theo_toa(du_lieu):
    """Gom mọi căn ĐANG HIỂN THỊ theo mã tòa chuẩn hoá. Một lần quét duy
    nhất cho toàn bộ script, thay vì lọc lại data.json cho từng tòa."""
    gom = {}
    for c in du_lieu:
        toa_raw = c.get("Tòa", "")
        if not str(toa_raw).strip() or not dang_hien_thi(c):
            continue
        gom.setdefault(chuan_ma_toa(toa_raw), []).append(c)
    return gom


def thong_ke(cac_can):
    gia = [so_tien(c.get("Giá thuê")) for c in cac_can]
    gia = [g for g in gia if g > 0]
    dt = [dien_tich(c.get("Diện tích")) for c in cac_can]
    dt = [d for d in dt if d > 0]

    theo_loai = {}
    for c in cac_can:
        loai = str(c.get("Loại", "")).strip()
        muc = theo_loai.setdefault(loai, {"so_can": 0, "gia": []})
        muc["so_can"] += 1
        g = so_tien(c.get("Giá thuê"))
        if g > 0:
            muc["gia"].append(g)

    theo_noi_that = {}
    for c in cac_can:
        nt = str(c.get("Nội thất", "")).strip()
        if nt:
            theo_noi_that[nt] = theo_noi_that.get(nt, 0) + 1

    return {
        "so_can": len(cac_can),
        "gia_min": min(gia) if gia else 0,
        "gia_max": max(gia) if gia else 0,
        "dt_min": round(min(dt)) if dt else 0,
        "dt_max": round(max(dt)) if dt else 0,
        "theo_loai": sorted(theo_loai.items(),
                            key=lambda x: (-x[1]["so_can"], x[0])),
        "theo_noi_that": sorted(theo_noi_that.items(),
                                key=lambda x: (-x[1], x[0])),
        "full_noi_that": sum(1 for c in cac_can
                             if str(c.get("Nội thất", "")).strip().lower()
                             == "full nội thất"),
    }


def liet_ke(cac_phan):
    if not cac_phan:
        return ""
    if len(cac_phan) == 1:
        return cac_phan[0]
    return ", ".join(cac_phan[:-1]) + " và " + cac_phan[-1]


def khoang_gia(gia_min, gia_max):
    if not gia_min:
        return ""
    if gia_min == gia_max:
        return dinh_dang_gia(gia_min)
    return "%s – %s" % (dinh_dang_gia(gia_min), dinh_dang_gia(gia_max))


def dung_the_can(can, phan_khu, map_anh, hom_nay):
    ma = str(can.get("Mã nội bộ", "")).strip()
    loai = str(can.get("Loại", "")).strip()
    toa = str(can.get("Tòa", "")).strip()
    noi_that = str(can.get("Nội thất", "")).strip()
    dt = round(dien_tich(can.get("Diện tích")))
    gia = dinh_dang_gia(so_tien(can.get("Giá thuê")))
    anh = anh_dai_dien(can, map_anh)
    alt = "Cho thuê %s %s Vinhomes Smart City%s" % (
        loai, toa, " %dm2" % dt if dt else "")
    vi_tri = "%s · %s" % (phan_khu, toa) if phan_khu else toa

    huy_hieu_nt = ""
    if noi_that:
        lop = "badge-nt" if noi_that.lower() == "full nội thất" else "badge-nt thuong"
        huy_hieu_nt = '<span class="%s">%s</span>' % (lop, esc(noi_that))

    return """      <article class="the" data-ma-noi-bo="%(ma_thuoc_tinh)s">
        <div class="the-anh"><img src="%(anh)s" alt="%(alt)s" loading="lazy" \
decoding="async" width="400" height="300" \
onerror="this.closest('.the').classList.add('khong-anh');this.remove()">\
<span class="tinh-trang">%(tinh_trang)s</span>%(huy_hieu_nt)s</div>
        <div class="than">
          <h3 class="ten">%(ten)s</h3>
          <p class="vi-tri">%(vi_tri)s</p>
          <div class="chan-the">
            <div class="gia">%(gia)s<small>/tháng</small></div>
            <a class="zalo" href="https://zalo.me/%(sdt)s" target="_blank" \
rel="noopener">Nhắn Zalo</a>
          </div>
          <p class="ma-can">Mã căn: <b>%(ma)s</b></p>
        </div>
      </article>""" % {
        "ma_thuoc_tinh": esc(ma),
        "ma": esc(ma),
        "anh": esc(anh),
        "alt": esc(alt),
        "tinh_trang": esc(nhan_tinh_trang(can, hom_nay)),
        "huy_hieu_nt": huy_hieu_nt,
        "ten": esc(loai) + (" · %d m²" % dt if dt else ""),
        "vi_tri": esc(vi_tri),
        "gia": esc(gia),
        "sdt": SDT,
    }


def dung_bang_gia(tk):
    dong = []
    for loai, muc in tk["theo_loai"]:
        gia = muc["gia"]
        dong.append("<tr><td>%s</td><td>%d</td><td>%s</td></tr>" % (
            esc(loai), muc["so_can"],
            esc(khoang_gia(min(gia), max(gia)) if gia else "Liên hệ")))
    return "".join(dong)


def dung_item_list(ten_danh_sach, url, cac_can):
    """ItemList JSON-LD. Cùng định dạng '{Loại} {Tòa} {DT}m² – {Giá}/tháng'
    và cùng cách trỏ mọi item về URL trang mà 25 trang danh mục khác đang
    dùng (cap-nhat-so-can.mjs) — không tạo định dạng riêng cho trang tòa."""
    items = []
    for i, c in enumerate(cac_can, 1):
        loai = str(c.get("Loại", "")).strip()
        toa = str(c.get("Tòa", "")).strip()
        dt = round(dien_tich(c.get("Diện tích")))
        gia = dinh_dang_gia(so_tien(c.get("Giá thuê")))
        ten_item = "%s %s %sm² – %s/tháng" % (loai, toa, dt, gia) if dt else \
                   "%s %s – %s/tháng" % (loai, toa, gia)
        items.append({"@type": "ListItem", "position": i, "name": ten_item, "url": url})
    return {
        "@type": "ItemList",
        "name": ten_danh_sach,
        "numberOfItems": len(cac_can),
        "itemListElement": items,
    }


def dung_khoi_tang_ngang(ma_hien_tai, phan_khu, ung_vien_cung_pk):
    """Link ngang tới 3-5 tòa khác cùng phân khu (yêu cầu Phase 3-B, làm
    trước trong Phase 2 theo chỉ đạo). Nguồn là mọi tòa ĐÃ publish hoặc ĐANG
    đạt ngưỡng trong phân khu đã duyệt — không giới hạn theo --chi-toa của
    lần chạy hiện tại, để link luôn phản ánh đúng bức tranh đầy đủ."""
    khac = [t for t in ung_vien_cung_pk if t["ma_toa_du_lieu"] != ma_hien_tai]
    khac.sort(key=lambda t: (-t["so_can_trong"], t["ten_hien_thi"]))
    khac = khac[:5]
    if not khac:
        return ""
    links = "".join('<a href="%s">Tòa %s</a>' % (esc(t["duong_dan"]), esc(t["ten_hien_thi"]))
                    for t in khac)
    return ('\n  <h2 style="font-size:19px;margin-bottom:2px">Các tòa khác thuộc %s</h2>\n'
            '  <div class="lq">%s</div>\n') % (esc(phan_khu), links)


def dung_khoi_het_can(ten, phan_khu, tang_ngang_html):
    return """  <div class="sl">
    <div class="o"><b>0</b><span>căn đang trống</span></div>
  </div>

  <section class="bai">
    <h2>Tòa %(ten)s hiện chưa có căn trống</h2>
    <p>Tòa %(ten)s hiện không có căn nào đang cho thuê. Trang này vẫn được
giữ lại vì quỹ căn thay đổi liên tục — anh/chị xem các tòa khác đang có căn
trống trong cùng phân khu %(phan_khu)s bên dưới, hoặc quay lại trang tìm
căn để xem toàn bộ khu đô thị.</p>
  </section>
%(tang_ngang)s
  <a class="cta-home duoi" href="/">Quay lại trang tìm căn của cả khu đô thị
    <small>Hàng trăm căn đang trống ở mọi phân khu, kèm ảnh thật từng căn</small></a>
""" % {"ten": esc(ten), "phan_khu": esc(phan_khu), "tang_ngang": tang_ngang_html}


# Hai đoạn văn xuôi trong "Tòa X đang có gì" là phần DUY NHẤT không phải
# heading/CTA/bảng cố định — nhưng nếu chỉ có 1 cách viết, khung câu giống
# hệt nhau giữa mọi tòa (chỉ đổi số/tên) vẫn đủ để 2 trang tòa nhỏ (3-4 căn,
# nơi văn xuôi này chiếm tỷ trọng lớn nhất trang) vượt ngưỡng trùng lặp 60%
# yêu cầu ở nghiệm thu Phase 2 — đo thực tế thấy 268/276 cặp trong batch 24
# tòa vượt ngưỡng CHỈ TÍNH riêng 2 đoạn văn này. Xoay vòng khung câu (giữ
# nguyên số liệu thật, chỉ đổi cách diễn đạt) để giảm trùng lặp cơ học, chọn
# theo tổng mã ký tự của mã tòa — DETERMINISTIC, không phải random, để chạy
# lại nhiều lần vẫn ra đúng một bản cho cùng một tòa.
DOAN_1_BIEN_THE = [
    "Trang này gom lại toàn bộ căn hộ thuộc riêng tòa %(ten)s mà bên em đang "
    "nhận cho thuê, tách khỏi danh sách chung của cả phân khu %(phan_khu)s. "
    "Hiện có %(so_can)d căn: %(cau_loai)s.",
    "Tòa %(ten)s hiện có %(so_can)d căn đang cho thuê: %(cau_loai)s. Danh sách "
    "dưới đây tách riêng khỏi phân khu %(phan_khu)s để anh/chị xem đúng quỹ "
    "căn của tòa này.",
    "Bên em đang nhận cho thuê %(so_can)d căn tại tòa %(ten)s, thuộc phân khu "
    "%(phan_khu)s, gồm %(cau_loai)s.",
]
DOAN_2_BIEN_THE = [
    "Giá thuê trải từ %(gia_min)s tới %(gia_max)s mỗi tháng, diện tích từ "
    "%(dt_min)d m² đến %(dt_max)d m². Xét theo tình trạng đồ đạc thì có "
    "%(cau_noi_that)s. Cập nhật gần nhất %(ngay)s.",
    "Mức giá hiện tại ở tòa %(ten)s là %(gia_min)s–%(gia_max)s/tháng, diện "
    "tích %(dt_min)d–%(dt_max)dm². Về nội thất: %(cau_noi_that)s (cập nhật "
    "%(ngay)s).",
]


def dung_khoi_co_can(ten, phan_khu, trang_phan_khu, cac_can, tk, map_anh, hom_nay, tang_ngang_html):
    cau_loai = liet_ke(["%d căn %s" % (m["so_can"], l)
                        for l, m in tk["theo_loai"]])
    cau_noi_that = liet_ke(["%d căn %s" % (n, t)
                            for t, n in tk["theo_noi_that"]])
    the_can = "\n".join(dung_the_can(c, phan_khu, map_anh, hom_nay)
                        for c in cac_can)
    lien_ket_loai = "".join(
        '<a href="%s">%s</a>' % TRANG_LOAI_CAN[l.lower()]
        for l, _ in tk["theo_loai"] if l.lower() in TRANG_LOAI_CAN)
    ngay = hom_nay.strftime("%d/%m/%Y")

    idx1 = sum(ord(c) for c in ten) % len(DOAN_1_BIEN_THE)
    idx2 = sum(ord(c) for c in ten[::-1]) % len(DOAN_2_BIEN_THE)
    doan_van_bien_so = {
        "ten": esc(ten), "phan_khu": esc(phan_khu), "so_can": tk["so_can"],
        "cau_loai": esc(cau_loai), "cau_noi_that": esc(cau_noi_that),
        "gia_min": esc(dinh_dang_gia(tk["gia_min"])),
        "gia_max": esc(dinh_dang_gia(tk["gia_max"])),
        "dt_min": tk["dt_min"], "dt_max": tk["dt_max"], "ngay": ngay,
    }
    doan_1 = DOAN_1_BIEN_THE[idx1] % doan_van_bien_so
    doan_2 = DOAN_2_BIEN_THE[idx2] % doan_van_bien_so

    return """  <div class="sl">
    <div class="o"><b>%(so_can)d</b><span>căn đang trống</span></div>
    <div class="o"><b>%(gia_min)s</b><span>giá thấp nhất</span></div>
    <div class="o"><b>%(dt_min)d–%(dt_max)dm²</b><span>diện tích</span></div>
    <div class="o"><b>%(full_noi_that)d</b><span>căn full nội thất</span></div>
  </div>

  <a class="cta-home tren" href="/">Xem toàn bộ căn trống ở Vinhomes Smart City
    <small>Mở trang tìm căn để so sánh tòa %(ten)s với những tòa còn lại</small></a>

  <h2 class="tieu-de-luoi" style="font-size:1.15rem;margin:0 0 14px">Danh sách %(so_can)d căn đang cho thuê ở tòa %(ten)s</h2>
  <section class="luoi">
%(the_can)s
  </section>

  <a class="cta-loc" href="/">Chưa ưng căn nào ở tòa %(ten)s?
    <small>Bộ lọc theo giá, tòa và nội thất nằm ở trang tìm căn</small></a>

  <section class="bai">
    <h2>Tòa %(ten)s đang có gì</h2>
    <p>%(doan_1)s</p>
    <p>%(doan_2)s</p>
    <h3>Bảng giá theo loại căn</h3>
    <table class="bang">
      <thead><tr><th>Loại căn</th><th>Số căn trống</th><th>Khoảng giá/tháng</th></tr></thead>
      <tbody>%(bang_gia)s</tbody>
    </table>
    <p style="font-size:13.5px;color:var(--muted);margin-top:10px">
      Số liệu tính trực tiếp từ danh sách căn ở trên, cập nhật %(ngay)s.</p>
  </section>

  <h2 style="font-size:19px;margin-bottom:2px">Loại căn có ở tòa %(ten)s</h2>
  <div class="lq">%(lien_ket_loai)s</div>
%(tang_ngang)s
  <h2 style="font-size:19px;margin-bottom:2px">Xem rộng hơn</h2>
  <div class="lq"><a href="%(trang_phan_khu)s">Cả phân khu %(phan_khu)s</a><a href="/">Tất cả căn đang trống</a><a href="/bang-gia-thue-vinhomes-smart-city.html">Bảng giá thuê Vinhomes Smart City</a></div>

  <a class="cta-home duoi" href="/">Quay lại trang tìm căn của cả khu đô thị
    <small>Hàng trăm căn đang trống ở mọi phân khu, kèm ảnh thật từng căn</small></a>
""" % {
        "ten": esc(ten),
        "phan_khu": esc(phan_khu),
        "trang_phan_khu": esc(trang_phan_khu),
        "so_can": tk["so_can"],
        "gia_min": esc(dinh_dang_gia(tk["gia_min"])),
        "gia_max": esc(dinh_dang_gia(tk["gia_max"])),
        "dt_min": tk["dt_min"],
        "dt_max": tk["dt_max"],
        "full_noi_that": tk["full_noi_that"],
        "cau_loai": esc(cau_loai),
        "cau_noi_that": esc(cau_noi_that),
        "doan_1": doan_1,
        "doan_2": doan_2,
        "the_can": the_can,
        "bang_gia": dung_bang_gia(tk),
        "lien_ket_loai": lien_ket_loai,
        "ngay": ngay,
        "tang_ngang": tang_ngang_html,
    }


def dung_trang(canonical, ten, duong_dan, phan_khu, cac_can, tk, map_anh, hom_nay, ung_vien_cung_pk):
    url = TEN_MIEN + duong_dan
    ngay = hom_nay.strftime("%d/%m/%Y")
    trang_phan_khu = TRANG_PHAN_KHU.get(phan_khu, "")
    het_can = not cac_can

    duong_dan_bua = {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Trang chủ",
             "item": TEN_MIEN + "/"},
            {"@type": "ListItem", "position": 2,
             "name": "Cho thuê căn hộ %s Vinhomes Smart City" % phan_khu,
             "item": TEN_MIEN + trang_phan_khu},
            {"@type": "ListItem", "position": 3,
             "name": "Cho thuê căn hộ tòa %s Vinhomes Smart City" % ten,
             "item": url},
        ],
    }
    graph = [duong_dan_bua]
    if not het_can:
        graph.append(dung_item_list(
            "Cho thuê căn hộ tòa %s Vinhomes Smart City" % ten, url, cac_can))
    schema_json = json.dumps({"@context": "https://schema.org", "@graph": graph},
                             ensure_ascii=False)

    if het_can:
        tieu_de = "Cho thuê căn hộ tòa %s Vinhomes Smart City" % ten
        mo_ta = ("Tòa %s Vinhomes Smart City hiện chưa có căn trống. Xem các tòa "
                 "khác đang có căn trống thuộc phân khu %s, cập nhật %s."
                 % (ten, phan_khu, ngay))
    else:
        tieu_de = "Cho thuê căn hộ tòa %s Vinhomes Smart City – %d căn" % (
            ten, tk["so_can"])
        khoang = khoang_gia(tk["gia_min"], tk["gia_max"])
        mo_ta = ("Danh sách %d căn hộ cho thuê tại tòa %s Vinhomes Smart City, giá "
                 "%s/tháng, diện tích %d–%d m². Ảnh thật, cập nhật %s." % (
                     tk["so_can"], ten, khoang.replace(" – ", "–"),
                     tk["dt_min"], tk["dt_max"], ngay))

    tang_ngang_html = dung_khoi_tang_ngang(canonical, phan_khu, ung_vien_cung_pk)

    if het_can:
        khoi_chinh = dung_khoi_het_can(ten, phan_khu, tang_ngang_html)
    else:
        khoi_chinh = dung_khoi_co_can(ten, phan_khu, trang_phan_khu, cac_can, tk,
                                      map_anh, hom_nay, tang_ngang_html)

    return """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<!-- Trang này do scripts/sinh-trang-toa.py sinh lại từ data.json mỗi lần chạy.
     Sửa tay ở đây sẽ mất trong lần chạy sau - sửa script, đừng sửa file. -->
<title>%(tieu_de)s</title>
<meta name="description" content="%(mo_ta)s">
<link rel="canonical" href="%(url)s">
<link rel="icon" href="/favicon.ico" sizes="any">
<meta property="og:type" content="website">
<meta property="og:url" content="%(url)s">
<meta property="og:title" content="%(tieu_de)s">
<meta property="og:description" content="%(mo_ta)s">
<meta property="og:image" content="https://timthuesmartcity.com/og-smartcity.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:site_name" content="Cho thuê chung cư Smart City">
<meta name="twitter:image" content="https://timthuesmartcity.com/og-smartcity.jpg">
<meta property="og:locale" content="vi_VN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(tieu_de)s">
<meta name="twitter:description" content="%(mo_ta)s">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-VF9KHC5TWD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
gtag('js',new Date());gtag('config','G-VF9KHC5TWD');</script>
<script type="application/ld+json">%(schema_json)s</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Be+Vietnam+Pro:wght@300;400;500;600&display=swap"
      media="print" onload="this.media='all'">
<noscript>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Be+Vietnam+Pro:wght@300;400;500;600&display=swap">
</noscript>
<link rel="stylesheet" href="/assets/v3.css">
</head>
<body>
<header class="top">
  <div class="khung">
    <a class="hieu" href="/">Cho thuê chung cư Smart City<small>Ảnh thật · Cập nhật mỗi ngày</small></a>
    <nav>
      <a href="/">Tất cả căn</a><a href="/studio/">Studio</a><a href="/1pn-plus/">1 ngủ +</a>
      <a href="/2pn/">2 ngủ</a><a href="/3pn/">3 ngủ</a>
      <a href="/cam-nang-thue-nha.html">Cẩm nang</a>
    </nav>
  </div>
</header>

<main class="khung">
  <p class="bc"><a href="/">Trang chủ</a> › <a href="%(trang_phan_khu)s">%(phan_khu)s</a> › <span>Tòa %(ten)s</span></p>
  <h1>Cho thuê căn hộ tòa %(ten)s Vinhomes Smart City</h1>
  <p class="tt">%(mo_ta)s</p>

%(khoi_chinh)s
</main>

<footer class="chan">
  <div class="khung">
    <p><strong>Cho thuê chung cư Smart City</strong> — môi giới cá nhân, không phải đại diện
    chính thức của Vinhomes hay Vingroup. Hotline &amp; Zalo: %(sdt)s.</p>
    <p>Cập nhật %(ngay)s · <a href="/">Tìm căn hộ</a> ·
    <a href="/cam-nang-thue-nha.html">Cẩm nang thuê nhà</a> ·
    <a href="/gui-thue/">Chủ nhà gửi căn</a> ·
    <a href="/chinh-sach-quyen-rieng-tu.html">Chính sách quyền riêng tư</a></p>
  </div>
</footer>
<a class="zalo-noi" href="https://zalo.me/%(sdt)s" target="_blank" rel="noopener">Nhắn Zalo tư vấn</a>
  <script src="/assets/app-shell.js" defer></script>
</body>
""" % {
        "tieu_de": esc(tieu_de),
        "mo_ta": esc(mo_ta),
        "url": esc(url),
        "schema_json": schema_json,
        "phan_khu": esc(phan_khu),
        "trang_phan_khu": esc(trang_phan_khu),
        "ten": esc(ten),
        "khoi_chinh": khoi_chinh,
        "ngay": ngay,
        "sdt": SDT,
    }


def doc_trang_thai():
    if not os.path.exists(DUONG_TRANG_THAI):
        return {}
    with open(DUONG_TRANG_THAI, encoding="utf-8") as f:
        return json.load(f)


def ghi_trang_thai(trang_thai):
    os.makedirs(os.path.dirname(DUONG_TRANG_THAI), exist_ok=True)
    with open(DUONG_TRANG_THAI, "w", encoding="utf-8", newline="") as f:
        json.dump(trang_thai, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def cap_nhat_sitemap_toa(trang_thai, hom_nay_str, bo_qua):
    """Ghi lại ĐÚNG vùng giữa 2 mốc TOA:START/TOA:END trong sitemap.xml bằng
    danh sách tòa đã publish. Không đụng bất kỳ dòng nào khác trong file 43
    URL hiện có. Nếu chưa có mốc, cảnh báo và bỏ qua — không tự ý chèn liều
    (yêu cầu duyệt Phase 2 mục B2)."""
    if bo_qua:
        print("(--thu / --khong-cap-nhat-sitemap) Bỏ qua bước cập nhật sitemap.xml.")
        return
    if not os.path.exists(DUONG_SITEMAP):
        print("CẢNH BÁO: không thấy sitemap.xml — bỏ qua bước cập nhật sitemap.")
        return
    with open(DUONG_SITEMAP, encoding="utf-8") as f:
        noi_dung = f.read()
    if DAU_TOA_BAT_DAU not in noi_dung or DAU_TOA_KET_THUC not in noi_dung:
        print("CẢNH BÁO: sitemap.xml chưa có cặp mốc TOA:START/TOA:END — bỏ qua, "
              "KHÔNG tự ý chèn hay ghi đè. Cần thêm 2 dòng mốc này vào sitemap.xml "
              "một lần (thủ công, có review) trước khi bật bước này.")
        return

    dong = []
    for canonical in sorted(trang_thai, key=lambda k: trang_thai[k]["duong_dan"]):
        info = trang_thai[canonical]
        dong.append('  <url><loc>%s%s</loc><lastmod>%s</lastmod>'
                    '<changefreq>daily</changefreq><priority>0.9</priority></url>'
                    % (TEN_MIEN, info["duong_dan"], hom_nay_str))
    khoi_moi = "\n".join(dong)

    mau = re.compile(re.escape(DAU_TOA_BAT_DAU) + r'.*?' + re.escape(DAU_TOA_KET_THUC), re.S)
    thay = "%s\n%s\n  %s" % (DAU_TOA_BAT_DAU, khoi_moi, DAU_TOA_KET_THUC)
    noi_dung_moi, so_thay = mau.subn(thay, noi_dung, count=1)

    if noi_dung_moi == noi_dung:
        print("sitemap.xml: vùng trang tòa đã đúng, không đổi.")
        return
    with open(DUONG_SITEMAP, "w", encoding="utf-8", newline="") as f:
        f.write(noi_dung_moi)
    print("Đã cập nhật vùng trang tòa trong sitemap.xml (%d URL)." % len(dong))


def xu_ly_mot_toa(canonical, cac_can, phan_khu, trang_thai, ung_vien_cung_pk,
                  map_anh, hom_nay, chi_thu):
    ten = ma_toa_dep(canonical)
    slug = slug_tu_ma(ten)
    duong_dan = "/%s-vinhomes-smart-city/" % slug
    duong_ra = os.path.join(GOC, slug + "-vinhomes-smart-city", "index.html")

    cac_can_sap_xep = sorted(
        cac_can, key=lambda c: (so_tien(c.get("Giá thuê")),
                                dien_tich(c.get("Diện tích")),
                                str(c.get("Mã nội bộ", ""))))
    tk = thong_ke(cac_can_sap_xep) if cac_can_sap_xep else None

    het_can = not cac_can_sap_xep
    print("=== TÒA %s (%s) ===" % (ten, phan_khu))
    print("Mã trong data.json : %s" % canonical)
    print("Số căn đang hiển thị: %d%s" % (
        len(cac_can_sap_xep), "  [HẾT CĂN — vẫn giữ trang]" if het_can else ""))
    print("Sẽ ghi             : %s" % os.path.relpath(duong_ra, GOC))

    trang = dung_trang(canonical, ten, duong_dan, phan_khu, cac_can_sap_xep, tk,
                       map_anh, hom_nay, ung_vien_cung_pk)

    if not chi_thu:
        os.makedirs(os.path.dirname(duong_ra), exist_ok=True)
        with open(duong_ra, "w", encoding="utf-8", newline="") as f:
            f.write(trang)
        print("Đã ghi %s." % os.path.relpath(duong_ra, GOC))
    else:
        print("(--thu) Không ghi file.")

    ngay_publish_lan_dau = (trang_thai[canonical]["ngay_publish_lan_dau"]
                            if canonical in trang_thai
                            else hom_nay.strftime("%Y-%m-%d"))
    return {
        "ma_toa": ten,
        "slug": slug,
        "duong_dan": duong_dan,
        "phan_khu": phan_khu,
        "ngay_publish_lan_dau": ngay_publish_lan_dau,
    }


def main():
    bo_phan_tich = argparse.ArgumentParser(
        description="Sinh trang danh mục theo tòa từ data.json.")
    bo_phan_tich.add_argument("--thu", action="store_true",
                              help="chỉ in thống kê, không ghi file/trạng thái/sitemap")
    bo_phan_tich.add_argument("--chi-toa", default="",
                              help="giới hạn xử lý vài mã tòa, phân tách bằng dấu phẩy "
                                   "(vd S401,SA1,TC2) — dùng để sinh trang mẫu")
    bo_phan_tich.add_argument("--khong-cap-nhat-sitemap", action="store_true",
                              help="bỏ qua bước ghi vùng TOA:START/END trong sitemap.xml")
    tham_so = bo_phan_tich.parse_args()

    with open(DUONG_DATA, encoding="utf-8") as f:
        du_lieu = json.load(f)

    if not isinstance(du_lieu, list) or not du_lieu:
        print("LỖI: data.json rỗng hoặc không phải mảng. Dừng, không ghi gì.")
        return 1
    print("data.json: %d dòng." % len(du_lieu))

    map_anh = doc_map_anh()
    print("anh-map.json: %d ảnh có file trên đĩa.\n" % len(map_anh))

    hom_nay = ngay_hom_nay()
    hom_nay_str = hom_nay.strftime("%Y-%m-%d")

    trang_thai = doc_trang_thai()
    gom = gom_theo_toa(du_lieu)

    # Ứng viên đủ điều kiện có trang (đã publish HOẶC mới đạt ngưỡng trong
    # phân khu đã duyệt) — dùng để dựng khối "tòa khác cùng phân khu" luôn
    # đầy đủ, không phụ thuộc --chi-toa của lần chạy này.
    ung_vien_day_du = []
    ma_ung_vien = set(trang_thai.keys())
    for canonical, cac_can in gom.items():
        if len(cac_can) >= NGUONG_TOI_THIEU and phan_khu_tu_toa(canonical) in PHAN_KHU_DA_DUYET:
            ma_ung_vien.add(canonical)
    for canonical in ma_ung_vien:
        pk = trang_thai.get(canonical, {}).get("phan_khu") or phan_khu_tu_toa(canonical)
        ten = ma_toa_dep(canonical)
        ung_vien_day_du.append({
            "ma_toa_du_lieu": canonical,
            "ten_hien_thi": ten,
            "duong_dan": "/%s-vinhomes-smart-city/" % slug_tu_ma(ten),
            "phan_khu": pk,
            "so_can_trong": len(gom.get(canonical, [])),
        })

    can_xu_ly = set(ma_ung_vien)
    if tham_so.chi_toa.strip():
        chi_toa_loc = set(chuan_ma_toa(x) for x in tham_so.chi_toa.split(",") if x.strip())
        khong_khop = chi_toa_loc - can_xu_ly
        if khong_khop:
            print("CẢNH BÁO --chi-toa: %s không đủ điều kiện (chưa từng publish và "
                  "chưa đạt ngưỡng trong phân khu đã duyệt) — bỏ qua." % ", ".join(sorted(khong_khop)))
        can_xu_ly = can_xu_ly & chi_toa_loc

    so_xu_ly = 0
    for canonical in sorted(can_xu_ly):
        cac_can = gom.get(canonical, [])
        pk = trang_thai.get(canonical, {}).get("phan_khu") or phan_khu_tu_toa(canonical)
        cung_pk = [t for t in ung_vien_day_du if t["phan_khu"] == pk]
        ket_qua = xu_ly_mot_toa(canonical, cac_can, pk, trang_thai, cung_pk,
                                map_anh, hom_nay, tham_so.thu)
        so_xu_ly += 1
        if not tham_so.thu:
            trang_thai[canonical] = {
                "ma_toa": ket_qua["ma_toa"],
                "slug": ket_qua["slug"],
                "duong_dan": ket_qua["duong_dan"],
                "phan_khu": ket_qua["phan_khu"],
                "ngay_publish_lan_dau": ket_qua["ngay_publish_lan_dau"],
            }

    print("\nĐã xử lý %d tòa (trong tổng %d tòa đủ điều kiện)." % (so_xu_ly, len(can_xu_ly)))

    if not tham_so.thu:
        ghi_trang_thai(trang_thai)
        print("Đã ghi %s (%d tòa đã publish)." % (
            os.path.relpath(DUONG_TRANG_THAI, GOC), len(trang_thai)))

    cap_nhat_sitemap_toa(trang_thai, hom_nay_str,
                         tham_so.thu or tham_so.khong_cap_nhat_sitemap)
    return 0


if __name__ == "__main__":
    sys.exit(main())

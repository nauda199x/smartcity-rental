#!/usr/bin/env python3
"""Sinh trang danh mục theo TÒA từ data.json.

Site đang có trang theo phân khu (/sapphire/) và theo loại căn (/2pn/) nhưng
chưa có trang nào theo tòa, trong khi nhóm truy vấn "thuê căn hộ tòa S4.01"
có lượng tìm khá và gần như không ai làm. Đây là thử nghiệm MỘT trang duy
nhất: đo Search Console 4-6 tuần rồi mới tính chuyện sinh hàng loạt.

Khác 27 trang danh mục cũ (HTML tĩnh viết tay, lệch dần với data.json), trang
này được dựng lại từ đầu mỗi lần chạy nên không bao giờ lệch. Toàn bộ con số
trên trang - số căn, khoảng giá, khoảng diện tích, số căn full nội thất - đều
tính lại lúc chạy, không có chỗ nào viết cứng.

Listing nằm sẵn trong mã nguồn HTML, KHÔNG render bằng JavaScript. Đó là toàn
bộ lý do trang này tồn tại: Googlebot đọc được ngay danh sách căn.

Trang chỉ chứa thông tin suy ra được từ data.json. Không có số tầng, năm bàn
giao, hướng ban công hay mô tả cảm tính - những thứ đó không nằm trong dữ
liệu nên không được viết ra.

Chạy nhiều lần cho kết quả giống hệt nhau (trừ ngày cập nhật khi qua ngày mới).

Chạy:  python3 scripts/sinh-trang-toa.py [--thu]
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

TEN_MIEN = "https://timthuesmartcity.com"
SDT = "0977923284"

# ---------------------------------------------------------------------------
# KHỐI NAP DÙNG CHUNG (thêm 29/08/2026)
# Nguồn duy nhất: scripts/khoi-nap.tpl. Đọc từ file thay vì chép nội dung vào
# đây, vì NAP lệch một ký tự giữa các trang là mất sạch tác dụng của việc này —
# có hai bản trong hai script là sớm muộn cũng lệch.
# Chèn SAU khi đã format %(...)s để nội dung NAP không phải lo escape dấu %.
# ---------------------------------------------------------------------------
MOC_NAP = "<!--KHOI-NAP-->"
_khoi_nap_da_doc = None


def doc_khoi_nap():
    global _khoi_nap_da_doc
    if _khoi_nap_da_doc is None:
        duong = os.path.join(GOC, "scripts", "khoi-nap.tpl")
        with open(duong, encoding="utf-8") as f:
            _khoi_nap_da_doc = f.read().rstrip("\n")
    return _khoi_nap_da_doc


# ---------------------------------------------------------------------------
# Tòa cần sinh trang. Thêm tòa mới = thêm một dòng ở đây, không phải sửa code.
# Hiện CHỈ có S4.01 - đây là thử nghiệm một trang, chưa mở rộng.
# ---------------------------------------------------------------------------
CAC_TOA = {
    "S4.01": {
        "ma_toa_data": "S401",       # giá trị trong cột "Tòa" của data.json
        "duong_dan": "/s4-01-vinhomes-smart-city/",
        "ten_hien_thi": "S4.01",
    },
}

# Tòa còn quá ít căn thì trang mỏng, Google coi là trang rác và có thể kéo tụt
# cả site. Dưới ngưỡng này thì không sinh, giữ nguyên trang cũ nếu đã có.
NGUONG_TOI_THIEU = 3

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

# Ánh xạ phân khu -> trang phân khu. Victoria và Sola Park chưa có trang nên
# không nằm trong bảng này.
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


def nap_module_anh():
    """Nạp sinh-danh-sach-anh.py để dùng lại ánh xạ tòa -> phân khu.

    Tên file có dấu gạch ngang nên không import thẳng được, phải đi đường
    importlib. Viết lại ánh xạ đó ở đây thì sớm muộn hai bản cũng lệch nhau -
    SA5 rơi nhầm vào Sapphire là đúng cái bẫy mà file kia đã xử lý."""
    duong = os.path.join(THU_MUC_SCRIPT, "sinh-danh-sach-anh.py")
    dac_ta = importlib.util.spec_from_file_location("sinh_danh_sach_anh", duong)
    mo_dun = importlib.util.module_from_spec(dac_ta)
    # Không để Python đẻ ra scripts/__pycache__/ chỉ vì một lần import - repo
    # này là nội dung website, không phải thư mục mã nguồn có sẵn .gitignore
    # cho rác build.
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
    """Thoát ký tự đặc biệt cho cả nội dung thẻ lẫn giá trị thuộc tính."""
    return html.escape("" if v is None else str(v), quote=True)


def chuan_ma_toa(toa):
    """Bỏ khoảng trắng và dấu ngăn rồi đổi hoa: 's4.01' -> 'S401'.

    Cột Tòa nhập tay trên Sheet nên cùng một tòa có thể là S401, S4.01,
    S4-01 hay 's4 01'."""
    return re.sub(r'[\s._-]', '', str(toa)).upper()


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
    """Port nguyên cách viết giá của dong-bo-can.js: 15 triệu, 8,5 triệu."""
    if not p:
        return "Liên hệ"
    if p % 1000000 == 0:
        return "%d triệu" % (p // 1000000)
    return ("%s triệu" % (round(p / 100000) / 10)).replace(".", ",")


def ngay_hom_nay():
    """Hôm nay theo giờ Việt Nam. Workflow chạy trên runner giờ UTC, không quy
    đổi thì đêm cuối tháng sẽ ghi lùi một ngày."""
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
    """Chữ trên huy hiệu tình trạng, lấy từ cột Ngày vào ở.

    Không dùng nhãn "Mới" của dong-bo-can.js: nhãn đó tính theo mốc 72 tiếng
    nên nội dung file sẽ đổi giữa hai lần chạy trong cùng một ngày."""
    s = str(can.get("Ngày vào ở", "")).strip()
    if not s or s.lower() in ("luôn", "ở ngay", "o ngay", "ngay"):
        return "Vào ngay"
    if la_ngay_da_qua(s, hom_nay):
        return "Vào ngay"
    khop = re.match(r'^(\d{1,2})/(\d{1,2})', s)
    return "Trống từ " + (khop.group(0) if khop else s)


def doc_map_anh():
    """Bảng tra Drive ID -> đường dẫn WebP trong repo.

    Chỉ nhận dòng có file thật trên đĩa. Trỏ sang đường dẫn không tồn tại thì
    trang vỡ ảnh, tệ hơn hẳn việc để nguyên URL Drive - đúng cách mà
    thay-anh-trong-html.py đang làm."""
    if not os.path.exists(DUONG_MAP_ANH):
        return {}
    with open(DUONG_MAP_ANH, encoding="utf-8") as f:
        anh_map = json.load(f)
    return {ma: duong for ma, duong in anh_map.items()
            if os.path.exists(os.path.join(GOC, duong.lstrip("/")))}


def anh_dai_dien(can, map_anh):
    """Ảnh bìa của căn: ưu tiên WebP trong repo, không có thì giữ URL Drive."""
    url = str(can.get("Ảnh đại diện", "")).strip()
    if not url:
        return ""
    khop = re.search(r'id=([A-Za-z0-9_-]+)', url)
    if khop and khop.group(1) in map_anh:
        return map_anh[khop.group(1)]
    return url


def loc_can_cua_toa(du_lieu, ma_toa_data):
    """Căn đang hiển thị trên web và thuộc đúng tòa cần sinh."""
    muc_tieu = chuan_ma_toa(ma_toa_data)
    return [c for c in du_lieu
            if dang_hien_thi(c) and chuan_ma_toa(c.get("Tòa", "")) == muc_tieu]


def thong_ke(cac_can):
    """Toàn bộ con số xuất hiện trên trang, tính lại từ danh sách căn thật."""
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
        # Nhiều căn nhất đứng trước; cùng số căn thì xếp theo tên cho ổn định
        # giữa các lần chạy.
        "theo_loai": sorted(theo_loai.items(),
                            key=lambda x: (-x[1]["so_can"], x[0])),
        "theo_noi_that": sorted(theo_noi_that.items(),
                                key=lambda x: (-x[1], x[0])),
        "full_noi_that": sum(1 for c in cac_can
                             if str(c.get("Nội thất", "")).strip().lower()
                             == "full nội thất"),
    }


def liet_ke(cac_phan):
    """Nối danh sách theo kiểu tiếng Việt: 'a, b và c'."""
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
    """Một thẻ căn. Cấu trúc thẻ và class lấy nguyên từ sapphire/index.html để
    dùng chung assets/v3.css, không thêm CSS mới."""
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
    """Bảng giá theo loại căn, số liệu tính từ chính danh sách căn ở trên."""
    dong = []
    for loai, muc in tk["theo_loai"]:
        gia = muc["gia"]
        dong.append("<tr><td>%s</td><td>%d</td><td>%s</td></tr>" % (
            esc(loai), muc["so_can"],
            esc(khoang_gia(min(gia), max(gia)) if gia else "Liên hệ")))
    return "".join(dong)


def dung_trang(toa, cau_hinh, cac_can, tk, map_anh, hom_nay):
    ten = cau_hinh["ten_hien_thi"]
    duong_dan = cau_hinh["duong_dan"]
    url = TEN_MIEN + duong_dan
    ngay = hom_nay.strftime("%d/%m/%Y")
    phan_khu = phan_khu_tu_toa(cau_hinh["ma_toa_data"])
    trang_phan_khu = TRANG_PHAN_KHU.get(phan_khu, "")

    tieu_de = "Cho thuê căn hộ tòa %s Vinhomes Smart City – %d căn" % (
        ten, tk["so_can"])
    khoang = khoang_gia(tk["gia_min"], tk["gia_max"])
    mo_ta = ("Danh sách %d căn hộ cho thuê tại tòa %s Vinhomes Smart City, giá "
             "%s/tháng, diện tích %d–%d m². Ảnh thật, cập nhật %s." % (
                 tk["so_can"], ten, khoang.replace(" – ", "–"),
                 tk["dt_min"], tk["dt_max"], ngay))

    # Câu liệt kê loại căn: "2 căn 1 Ngủ +, 3 căn 2 Ngủ +..." - đọc thẳng từ
    # dữ liệu, không diễn giải thêm.
    cau_loai = liet_ke(["%d căn %s" % (m["so_can"], l)
                        for l, m in tk["theo_loai"]])
    cau_noi_that = liet_ke(["%d căn %s" % (n, t)
                            for t, n in tk["theo_noi_that"]])

    the_can = "\n".join(dung_the_can(c, phan_khu, map_anh, hom_nay)
                        for c in cac_can)

    # Liên kết tới đúng những trang loại căn có mặt trong tòa này.
    lien_ket_loai = "".join(
        '<a href="%s">%s</a>' % TRANG_LOAI_CAN[l.lower()]
        for l, _ in tk["theo_loai"] if l.lower() in TRANG_LOAI_CAN)

    duong_dan_bua = json.dumps({
        "@context": "https://schema.org",
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
    }, ensure_ascii=False)

    return ("""<!doctype html>
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
<script type="application/ld+json">%(duong_dan_bua)s</script>
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
  <p class="tt">Danh sách %(so_can)d căn hộ cho thuê tại tòa %(ten)s Vinhomes Smart City, giá %(khoang_gia)s/tháng, diện tích %(dt_min)d–%(dt_max)d m². Ảnh thật, cập nhật %(ngay)s.</p>

  <div class="sl">
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
    <p>Trang này gom lại toàn bộ căn hộ thuộc riêng tòa %(ten)s mà bên em đang
nhận cho thuê, tách khỏi danh sách chung của cả phân khu %(phan_khu)s. Hiện có
%(so_can)d căn: %(cau_loai)s.</p>
    <p>Giá thuê trải từ %(gia_min)s tới %(gia_max)s mỗi tháng, diện tích từ
%(dt_min)d m² đến %(dt_max)d m². Xét theo tình trạng đồ đạc thì có %(cau_noi_that)s.</p>
    <p>Danh sách được dựng lại từ dữ liệu căn của bên em mỗi ngày, nên căn nào
đã có khách thuê sẽ tự biến mất khỏi trang thay vì nằm lại làm mất công anh/chị
hỏi. Lần cập nhật gần nhất là %(ngay)s.</p>
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

  <h2 style="font-size:19px;margin-bottom:2px">Xem rộng hơn</h2>
  <div class="lq"><a href="%(trang_phan_khu)s">Cả phân khu %(phan_khu)s</a><a href="/">Tất cả căn đang trống</a><a href="/bang-gia-thue-vinhomes-smart-city.html">Bảng giá thuê Vinhomes Smart City</a></div>

  <a class="cta-home duoi" href="/">Quay lại trang tìm căn của cả khu đô thị
    <small>Hàng trăm căn đang trống ở mọi phân khu, kèm ảnh thật từng căn</small></a>

</main>

<footer class="chan">
<!--KHOI-NAP-->
  <div class="khung">
    <!-- Dòng "môi giới cá nhân … Hotline &amp; Zalo: 0977923284" cũ đã gỡ ngày
         29/08/2026: khối NAP ngay phía trên đã nói đủ tên đơn vị, tuyên bố độc
         lập và số điện thoại — mà nói bằng ĐÚNG một cách viết số duy nhất
         "0977 923 284". Để cả hai thì mỗi trang có hai cách viết số điện thoại
         khác nhau, đúng kiểu lệch NAP mà việc này sinh ra để dẹp. -->
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
        "duong_dan_bua": duong_dan_bua,
        "ten": esc(ten),
        "phan_khu": esc(phan_khu),
        "trang_phan_khu": esc(trang_phan_khu),
        "so_can": tk["so_can"],
        "khoang_gia": esc(khoang),
        "gia_min": esc(dinh_dang_gia(tk["gia_min"])),
        "gia_max": esc(dinh_dang_gia(tk["gia_max"])),
        "dt_min": tk["dt_min"],
        "dt_max": tk["dt_max"],
        "full_noi_that": tk["full_noi_that"],
        "cau_loai": esc(cau_loai),
        "cau_noi_that": esc(cau_noi_that),
        "the_can": the_can,
        "bang_gia": dung_bang_gia(tk),
        "lien_ket_loai": lien_ket_loai,
        "ngay": ngay,
        "sdt": SDT,
    }).replace(MOC_NAP, doc_khoi_nap())


def xu_ly_mot_toa(toa, cau_hinh, du_lieu, map_anh, hom_nay, chi_thu):
    """Sinh trang cho một tòa. Trả về True nếu mọi thứ bình thường."""
    cac_can = loc_can_cua_toa(du_lieu, cau_hinh["ma_toa_data"])
    duong_ra = os.path.join(
        GOC, cau_hinh["duong_dan"].strip("/"), "index.html")

    print("=== TÒA %s ===" % toa)
    print("Mã trong data.json : %s" % cau_hinh["ma_toa_data"])
    print("Số căn đang hiển thị: %d" % len(cac_can))

    if len(cac_can) < NGUONG_TOI_THIEU:
        # Không phải lỗi - tòa hết căn là chuyện bình thường. Chỉ là không có
        # gì để đăng, nên giữ nguyên trang cũ (nếu có) và đi tiếp.
        print("CẢNH BÁO: dưới ngưỡng %d căn — KHÔNG sinh, KHÔNG ghi đè %s."
              % (NGUONG_TOI_THIEU, os.path.relpath(duong_ra, GOC)))
        return True

    cac_can.sort(key=lambda c: (so_tien(c.get("Giá thuê")),
                                dien_tich(c.get("Diện tích")),
                                str(c.get("Mã nội bộ", ""))))

    tk = thong_ke(cac_can)
    print("Loại căn           : %s" % ", ".join(
        "%s (%d)" % (l, m["so_can"]) for l, m in tk["theo_loai"]))
    print("Khoảng giá         : %s/tháng" % khoang_gia(tk["gia_min"], tk["gia_max"]))
    print("Khoảng diện tích   : %d–%d m²" % (tk["dt_min"], tk["dt_max"]))
    print("Nội thất           : %s" % ", ".join(
        "%s (%d)" % (t, n) for t, n in tk["theo_noi_that"]))
    print("Có ảnh đại diện    : %d/%d" % (
        sum(1 for c in cac_can if anh_dai_dien(c, map_anh)), len(cac_can)))
    print("Sẽ ghi             : %s" % os.path.relpath(duong_ra, GOC))

    trang = dung_trang(toa, cau_hinh, cac_can, tk, map_anh, hom_nay)

    if chi_thu:
        print("(--thu) Không ghi file.")
        return True

    os.makedirs(os.path.dirname(duong_ra), exist_ok=True)
    # newline="" để nội dung ghi ra đúng từng ký tự, không bị đổi kiểu xuống dòng.
    with open(duong_ra, "w", encoding="utf-8", newline="") as f:
        f.write(trang)
    print("Đã ghi %s (%d thẻ căn)." % (os.path.relpath(duong_ra, GOC), tk["so_can"]))
    return True


def main():
    bo_phan_tich = argparse.ArgumentParser(
        description="Sinh trang danh mục theo tòa từ data.json.")
    bo_phan_tich.add_argument("--thu", action="store_true",
                              help="chỉ in thống kê và đường dẫn sẽ ghi, không tạo file")
    tham_so = bo_phan_tich.parse_args()

    with open(DUONG_DATA, encoding="utf-8") as f:
        du_lieu = json.load(f)

    # data.json rỗng gần như luôn là lỗi đẩy dữ liệu chứ không phải hết căn.
    # Dừng hẳn còn hơn ghi đè trang bằng một danh sách trắng.
    if not isinstance(du_lieu, list) or not du_lieu:
        print("LỖI: data.json rỗng hoặc không phải mảng. Dừng, không ghi gì.")
        return 1
    print("data.json: %d dòng." % len(du_lieu))

    map_anh = doc_map_anh()
    print("anh-map.json: %d ảnh có file trên đĩa.\n" % len(map_anh))

    hom_nay = ngay_hom_nay()
    for toa, cau_hinh in CAC_TOA.items():
        if not xu_ly_mot_toa(toa, cau_hinh, du_lieu, map_anh, hom_nay,
                             tham_so.thu):
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

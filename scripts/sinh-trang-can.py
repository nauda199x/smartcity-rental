#!/usr/bin/env python3
"""Sinh trang tĩnh riêng cho từng căn hộ đủ điều kiện, mỗi căn một URL vĩnh viễn.

Phạm vi hiện tại: mọi căn đang "Hiển thị trên Web" = có và "Mã nội bộ"
khớp ^CT\\. đều có một URL chi tiết riêng, KHÔNG phụ thuộc số lượng ảnh.
(mã dạng số hoặc CC3 không đảm bảo duy nhất trên toàn sheet nên chưa sinh URL).
Trần cứng TOI_DA vẫn giữ để một lần data.json lỗi không sinh hàng loạt trang rác.

URL không bao giờ bị xoá: khi một căn hết hạn hiển thị, trang vẫn trả 200,
đổi sang bản "đã có khách" và trỏ khách sang các căn còn trống tương tự.
Toàn bộ slug từng sinh nằm trong can-ho/danh-sach-trang.json — mất file đó
là mất lịch sử URL.

Chỉ dùng dữ liệu có thật trong data.json. Không suy diễn số tầng, hướng ban
công hay mô tả cảm tính.

Ngày hiển thị trên trang chi tiết là ngày căn lần đầu xuất hiện
trên website. Mốc này được lưu bền trong danh-sach-trang.json nên
không bị thay đổi khi workflow chạy lại để cập nhật giá, ảnh hay nội thất.

Chạy:  python3 scripts/sinh-trang-can.py [--thu]
"""

import argparse
import datetime
import html
import importlib.util
import json
import os
import re
import shutil
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DUONG_DATA = os.path.join(GOC, "data.json")
DUONG_MAP_ANH = os.path.join(GOC, "anh-can-ho", "anh-map.json")
THU_MUC_CAN_HO = os.path.join(GOC, "can-ho")
DUONG_SO_DANG_KY = os.path.join(THU_MUC_CAN_HO, "danh-sach-trang.json")
DUONG_SITEMAP = os.path.join(GOC, "sitemap-can-ho.xml")

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

ANH_MAC_DINH = "https://timthuesmartcity.com/og-smartcity.jpg"

# data.json lỗi (Apps Script đẩy nhầm file rỗng) làm mất sạch danh sách. Dưới
# ngưỡng này thì dừng, không ghi đè, không xoá gì. Giống NGUONG_TOI_THIEU
# trong sinh-danh-sach-anh.py.
NGUONG_TOI_THIEU = 150

# Trần cứng số căn đủ điều kiện được sinh trang trong MỘT lần chạy. Tổng quỹ
# hiện nhỏ hơn nhiều mốc này; vượt trần gần như chắc chắn là data.json đang lỗi
# hoặc cột "Hiển thị trên Web" bị đẩy sai hàng loạt.
TOI_DA = 400

# Từ ngưỡng này (tỷ lệ trên TOI_DA) trở lên script vẫn sinh trang bình
# thường (exit 0) nhưng in thêm một dòng CẢNH BÁO, để thấy trước lúc còn dư
# dả thay vì đợi tới lần chạy vượt hẳn TOI_DA rồi mới biết.
NGUONG_CANH_BAO = 0.8

# Ánh xạ loại căn -> trang loại căn tương ứng. Chép từ TRANG_LOAI_CAN trong
# sinh-trang-toa.py — file đó không phải module để import (chạy code ở mức
# top-level khi nạp), nên giữ một bản riêng ở đây như chính file đó đang làm.
TRANG_LOAI_CAN = {
    "studio": ("/studio/", "Căn hộ Studio"),
    "1 ngủ": ("/1pn/", "Căn 1 phòng ngủ"),
    "1 ngủ +": ("/1pn-plus/", "Căn 1 phòng ngủ +"),
    "2 ngủ": ("/2pn/", "Căn 2 phòng ngủ"),
    "2 ngủ +": ("/2pn-plus/", "Căn 2 phòng ngủ +"),
    "3 ngủ": ("/3pn/", "Căn 3 phòng ngủ"),
}

# Ánh xạ phân khu -> trang phân khu. Victoria và Sola Park chưa có trang.
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

# Ánh xạ tòa (mã đã chuẩn hoá) -> trang tòa đang được generator duy trì.
# Phải khớp với CAC_TOA trong sinh-trang-toa.py để breadcrumb của trang căn
# trỏ xuống đúng landing tòa thay vì chỉ dừng ở phân khu.
TRANG_TOA = {
    "A2": ("/a2-lumiere-evergreen/", "A2 Lumière"),
    "MASB": ("/west-b-masteri-smart-city/", "West B Masteri"),
    "A3": ("/a3-lumiere-evergreen/", "A3 Lumière"),
    "MASD": ("/west-d-masteri-smart-city/", "West D Masteri"),
    "GS5": ("/gs5-the-miami-smart-city/", "GS5 The Miami"),
    "MASA": ("/west-a-masteri-smart-city/", "West A Masteri"),
    "SA3": ("/sa3-the-sakura-smart-city/", "SA3 The Sakura"),
    "SA1": ("/sa1-the-sakura-smart-city/", "SA1 The Sakura"),
    "S101": ("/s1-01-vinhomes-smart-city/", "S1.01"),
    "S202": ("/s2-02-vinhomes-smart-city/", "S2.02"),
    "GS6": ("/gs6-the-miami-smart-city/", "GS6 The Miami"),
    "TC1": ("/tc1-canopy-smart-city/", "TC1 The Canopy"),
    "I1": ("/i1-imperia-smart-city/", "I1 Imperia"),
    "S401": ("/s4-01-vinhomes-smart-city/", "S4.01"),
    "S303": ("/s3-03-vinhomes-smart-city/", "S3.03"),
}


def nap_module_anh():
    """Nạp sinh-danh-sach-anh.py để dùng lại slug() và phan_khu_tu_toa().

    Đi đường importlib giống hệt cách sinh-trang-toa.py làm ở nap_module_anh():
    tên file có dấu gạch ngang nên không import thẳng được, và viết lại logic
    ở đây sớm muộn sẽ lệch với bản gốc — URL trang và tên file ảnh sẽ không
    còn khớp nhau nữa."""
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
slug = ANH.slug
phan_khu_tu_toa = ANH.phan_khu_tu_toa


def esc(v):
    return html.escape("" if v is None else str(v), quote=True)


def chuan_ma_toa(toa):
    return re.sub(r'[\s._-]', '', str(toa)).upper()


def so_tien(v):
    if isinstance(v, (int, float)):
        return int(v)
    return int(re.sub(r'[^\d]', '', str(v)) or 0)


def dien_tich_so(v):
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
    """Hôm nay theo giờ Việt Nam — runner GitHub Actions chạy giờ UTC."""
    return (datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=7)).date()


def ngay_da_qua(s, hom_nay):
    khop = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', str(s).strip())
    if not khop:
        return False
    try:
        ngay = datetime.date(int(khop.group(3)), int(khop.group(2)), int(khop.group(1)))
    except ValueError:
        return False
    return ngay <= hom_nay


def ngay_vao_o_hien_thi(can, hom_nay):
    s = str(can.get("Ngày vào ở", "")).strip()
    if not s or s.lower() in ("luôn", "ở ngay", "o ngay", "ngay"):
        return "Vào ngay"
    if ngay_da_qua(s, hom_nay):
        return "Vào ngay"
    return s


def ngay_iso(s):
    chuoi = str(s).strip()
    khop_iso = re.match(r'^(\d{4})-(\d{2})-(\d{2})', chuoi)
    if khop_iso:
        try:
            return datetime.date(int(khop_iso.group(1)), int(khop_iso.group(2)),
                                 int(khop_iso.group(3))).isoformat()
        except ValueError:
            return None

    khop = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', chuoi)
    if not khop:
        return None
    d, m, y = int(khop.group(1)), int(khop.group(2)), int(khop.group(3))
    try:
        return datetime.date(y, m, d).isoformat()
    except ValueError:
        return None


def ngay_hien_thi(s):
    """Chuẩn hoá ISO hoặc dd/mm/yyyy về dd/mm/yyyy để hiển thị."""
    iso = ngay_iso(s)
    if not iso:
        return ""
    return datetime.date.fromisoformat(iso).strftime("%d/%m/%Y")


def dang_hien_thi(can):
    """Đúng điều kiện 1 của tài liệu: chỉ nhận giá trị 'có', không nới lỏng
    thêm cách viết khác — khớp với lệnh đối chiếu #13 trong tài liệu."""
    return str(can.get("Hiển thị trên Web", "")).strip().lower() == "có"


def ma_hop_le(can):
    """Mã nội bộ chỉ cần không rỗng.

    Quỹ cũ còn một số mã legacy dạng số/CC*, nhưng vẫn là mã duy nhất và ổn
    định. Khóa cứng CT.* làm các căn đó không bao giờ có URL chi tiết."""
    return bool(str(can.get("Mã nội bộ", "")).strip())


def danh_sach_anh(can):
    """Ảnh đại diện đứng đầu, sau đó tới Danh sách ảnh; loại trùng URL.

    Trang chi tiết phải tồn tại kể cả căn mới chỉ có 0–1 ảnh. Ảnh là nội dung
    bổ sung, KHÔNG còn là điều kiện để một căn được cấp URL."""
    ra = []
    da_co = set()
    nguon = [str(can.get("Ảnh đại diện", "") or "").strip()]
    nguon.extend(x.strip() for x in str(can.get("Danh sách ảnh", "") or "").split("\n"))
    for url in nguon:
        if not url or url in da_co:
            continue
        da_co.add(url)
        ra.append(url)
    return ra


# Slug rác: thiếu tòa làm slug dính hai dấu gạch liền nhau, thiếu diện tích
# làm slug ghi "0m2". Cả hai đều đã từng lọt ra URL công khai (24 trang, phát
# hiện trong audit 02/09/2026) với title "Căn hộ 1 Ngủ + 0m²" và breadcrumb
# "Trang chủ › ›". Regex này là chốt chặn cuối, dùng cho cả slug mới sinh lẫn
# slug cũ còn nằm trong sổ đăng ký.
RE_SLUG_RAC = re.compile(r"--|-0m2-|-0m2$")


def slug_rac(s):
    return bool(RE_SLUG_RAC.search(s))


def du_du_lieu_cap_url(can):
    """Bản ghi phải đủ tòa và diện tích thì mới được cấp URL.

    Đây KHÔNG phải điều kiện thương mại (giá, ảnh vẫn có thể trống) mà là điều
    kiện tối thiểu để slug, title, breadcrumb và schema không sinh ra chuỗi vô
    nghĩa. Căn thiếu hai trường này vẫn nằm trên lưới danh mục, chỉ là không có
    trang chi tiết riêng — sửa trong Google Sheet là lần chạy sau tự có URL."""
    return (bool(str(can.get("Tòa", "")).strip())
            and dien_tich_so(can.get("Diện tích")) > 0)


def du_dieu_kien(can):
    """Mọi căn đang public có Mã nội bộ và đủ tòa/diện tích đều phải có URL
    chi tiết riêng."""
    return dang_hien_thi(can) and ma_hop_le(can) and du_du_lieu_cap_url(can)


def doc_map_anh():
    """Bảng tra Drive ID -> đường dẫn WebP trong repo, chỉ nhận file có thật."""
    if not os.path.exists(DUONG_MAP_ANH):
        return {}
    with open(DUONG_MAP_ANH, encoding="utf-8") as f:
        anh_map = json.load(f)
    return {ma: duong for ma, duong in anh_map.items()
            if os.path.exists(os.path.join(GOC, duong.lstrip("/")))}


def drive_id(url):
    khop = re.search(r'id=([A-Za-z0-9_-]+)', str(url))
    return khop.group(1) if khop else None


def anh_tu_url(url, map_anh):
    """Ảnh thật trong repo nếu có trong anh-map.json, không có thì giữ URL Drive."""
    did = drive_id(url)
    if did and did in map_anh:
        return TEN_MIEN + map_anh[did]
    return str(url).strip()


def og_image_cho_can(anh_list, map_anh):
    """og:image không bao giờ trỏ Drive — ảnh bìa WebP nếu có, không thì ảnh mặc định."""
    for url in anh_list:
        did = drive_id(url)
        if did and did in map_anh:
            return TEN_MIEN + map_anh[did]
    return ANH_MAC_DINH


def tinh_slug(can):
    loai = can.get("Loại", "")
    toa = can.get("Tòa", "")
    ma = can.get("Mã nội bộ", "")
    phan_khu = phan_khu_tu_toa(toa)
    dt = round(dien_tich_so(can.get("Diện tích")))
    return "cho-thue-can-ho-%s-%s-%dm2-%s" % (
        slug(loai), slug(phan_khu), dt, slug(ma))


def doc_so_dang_ky():
    if not os.path.exists(DUONG_SO_DANG_KY):
        return {}
    with open(DUONG_SO_DANG_KY, encoding="utf-8") as f:
        return json.load(f)


def ghi_so_dang_ky(so_dang_ky):
    os.makedirs(THU_MUC_CAN_HO, exist_ok=True)
    with open(DUONG_SO_DANG_KY, "w", encoding="utf-8", newline="") as f:
        json.dump(so_dang_ky, f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


def can_tuong_tu(slug_hien_tai, toa, phan_khu, loai, active, gioi_han=6):
    """6 căn cùng tòa; không đủ thì lấy tiếp cùng phân khu + cùng loại.

    `active` là dict slug -> {toa, phan_khu, loai, ...} của các căn ĐANG có
    trang thật (không gợi ý sang căn cũng đã có khách)."""
    ma_toa = chuan_ma_toa(toa)
    cung_toa = [s for s, c in active.items()
                if s != slug_hien_tai and chuan_ma_toa(c["toa"]) == ma_toa]
    con_thieu = gioi_han - len(cung_toa)
    cung_pk_loai = []
    if con_thieu > 0:
        cung_pk_loai = [s for s, c in active.items()
                        if s != slug_hien_tai and s not in cung_toa
                        and c["phan_khu"] == phan_khu and c["loai"] == loai]
    return (cung_toa + cung_pk_loai)[:gioi_han]


def dung_the_tuong_tu(s, c):
    dt = round(dien_tich_so(c["dien_tich"]))
    gia = dinh_dang_gia(so_tien(c.get("gia", 0)))
    return ('<a class="the-nho" href="/can-ho/%s/"><b>%s</b><span>%s · %d m² · %s'
            '</span></a>') % (esc(s), esc(c["loai"]), esc(c["toa"]), dt, esc(gia))


# ---------------------------------------------------------------------------
# Khung HTML dùng chung (header/nav/footer) — chép nguyên từ
# s4-01-vinhomes-smart-city/index.html để dùng chung assets/v3.css.
# ---------------------------------------------------------------------------

DAU_TRANG = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<!-- Trang này do scripts/sinh-trang-can.py sinh lại từ data.json mỗi lần
     chạy. Sửa tay ở đây sẽ mất trong lần chạy sau - sửa script, đừng sửa file. -->
<title>%(tieu_de)s</title>
<meta name="description" content="%(mo_ta)s">
<meta name="robots" content="%(robots)s">
<link rel="canonical" href="%(url)s">
<link rel="icon" href="/favicon.ico" sizes="any">
<meta property="og:type" content="website">
<meta property="og:url" content="%(url)s">
<meta property="og:title" content="%(tieu_de)s">
<meta property="og:description" content="%(mo_ta)s">
<meta property="og:image" content="%(og_image)s">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:site_name" content="Tìm Thuê Smart City">
<meta name="twitter:image" content="%(og_image)s">
<meta property="og:locale" content="vi_VN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(tieu_de)s">
<meta name="twitter:description" content="%(mo_ta)s">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-VF9KHC5TWD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
gtag('js',new Date());gtag('config','G-VF9KHC5TWD');</script>
<script type="application/ld+json">%(bua)s</script>
<script type="application/ld+json">%(listing)s</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Be+Vietnam+Pro:wght@300;400;500;600&display=swap"
      media="print" onload="this.media='all'">
<noscript>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Be+Vietnam+Pro:wght@300;400;500;600&display=swap">
</noscript>
<link rel="stylesheet" href="/assets/v3.css?v=20260830-6">
<link rel="stylesheet" href="/assets/ngon-ngu.css?v=20260831-2">
</head>
<body>
<header class="top">
  <div class="khung">
    <a class="hieu" href="/">Cho thuê chung cư Smart City<small>Ảnh thật · Cập nhật mỗi ngày</small></a>
    <nav>
      <a href="/">Tất cả căn</a><a href="/studio/">Studio</a><a href="/1pn-plus/">1 ngủ +</a>
      <a href="/2pn/">2 ngủ</a><a href="/3pn/">3 ngủ</a>
      <a href="/can-ho-vao-o-ngay-vinhomes-smart-city.html">Vào ở ngay</a>
      <a href="/cam-nang-thue-nha.html">Cẩm nang</a>
    </nav>
    <div class="doi-tieng" role="group" aria-label="Language / 언어">
      <button type="button" data-lang="vi" aria-pressed="true">VI</button>
      <button type="button" data-lang="en" aria-pressed="false">EN</button>
      <button type="button" data-lang="ko" aria-pressed="false">한</button>
    </div>
  </div>
</header>

<main class="khung">
  <p class="bc"><a href="/">Trang chủ</a> › <a href="%(trang_phan_khu)s">%(phan_khu)s</a> › <span>%(bc_hien_tai)s</span></p>
"""

CHAN_TRANG = """</main>

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
  <script src="/assets/ngon-ngu.js?v=20260831-2" defer></script>
  <script id="ct-gallery-js" src="/assets/gallery.js?v=20260830-6" defer></script>
  <script id="ct-detail-js" src="/assets/can-ho-detail.js?v=20260831-2" defer></script>
  <script src="/assets/app-shell.js?v=20260901-1" defer></script>
  <script id="ct-detail-i18n-js" src="/assets/can-ho-detail-i18n.js?v=20260831-1" defer></script>
</body>
</html>
"""


def dung_footer(ngay_str):
    return (CHAN_TRANG % {"sdt": SDT, "ngay": ngay_str}).replace(
        MOC_NAP, doc_khoi_nap())


def longtail_cho_can(loai, gia, noi_that):
    """Các trang nhu cầu sâu đã tồn tại phù hợp với chính căn đang xem."""
    l = str(loai).strip().lower()
    nt = str(noi_that).strip().lower()
    o = []

    if l == "studio":
        if gia > 0 and gia <= 7000000:
            o.append(("/studio-duoi-7-trieu/", "Studio dưới 7 triệu"))
        elif gia > 7000000 and gia <= 10000000:
            o.append(("/studio-7-10-trieu/", "Studio 7–10 triệu"))
        if nt == "full nội thất":
            o.append(("/studio-full-do/", "Studio full nội thất"))

    elif l == "1 ngủ +":
        if gia > 0 and gia <= 10000000:
            o.append(("/1pn-plus-duoi-10-trieu/", "1 phòng ngủ + dưới 10 triệu"))
        if nt == "full nội thất":
            o.append(("/1pn-plus-full-do/", "1 phòng ngủ + full nội thất"))

    elif l == "2 ngủ":
        if gia > 0 and gia <= 10000000:
            o.append(("/2pn-duoi-10-trieu/", "2 phòng ngủ dưới 10 triệu"))
        elif gia > 10000000 and gia <= 12000000:
            o.append(("/2pn-10-12-trieu/", "2 phòng ngủ 10–12 triệu"))
        if nt == "full nội thất":
            o.append(("/2pn-full-do/", "2 phòng ngủ full nội thất"))

    elif l == "2 ngủ +" and gia > 12000000 and gia <= 15000000:
        o.append(("/2pn-plus-12-15-trieu/", "2 phòng ngủ + 12–15 triệu"))

    elif l == "3 ngủ":
        if gia > 12000000 and gia <= 15000000:
            o.append(("/3pn-12-15-trieu/", "3 phòng ngủ 12–15 triệu"))
        if nt == "full nội thất":
            o.append(("/3pn-full-do/", "3 phòng ngủ full nội thất"))

    # Giữ thứ tự nhưng không lặp href.
    ra, da_co = [], set()
    for href, ten in o:
        if href not in da_co:
            da_co.add(href)
            ra.append((href, ten))
    return ra


def lien_ket_noi_bo(phan_khu, loai, ma_toa, gia=0, noi_that=""):
    """Đi từ căn chi tiết lên parent, sang intent gần và sang cẩm nang."""
    o = []

    tp = TRANG_PHAN_KHU.get(phan_khu)
    if tp:
        o.append('<a href="%s">Căn hộ %s đang cho thuê</a>' % (
            esc(tp), esc(phan_khu)))

    tl = TRANG_LOAI_CAN.get(str(loai).strip().lower())
    if tl:
        o.append('<a href="%s">%s</a>' % (esc(tl[0]), esc(tl[1])))

    for href, ten in longtail_cho_can(loai, gia, noi_that):
        o.append('<a href="%s">%s</a>' % (esc(href), esc(ten)))

    tt = TRANG_TOA.get(chuan_ma_toa(ma_toa))
    if tt:
        o.append('<a href="%s">Tòa %s</a>' % (esc(tt[0]), esc(tt[1])))

    o.append('<a href="/bang-gia-thue-vinhomes-smart-city.html">Bảng giá thuê Smart City</a>')
    o.append('<a href="/phi-dich-vu-vinhomes-smart-city.html">Phí dịch vụ & gửi xe</a>')
    o.append('<a href="/kinh-nghiem-thue-chung-cu-smart-city.html">Kinh nghiệm thuê nhà</a>')
    o.append('<a href="/can-ho/">Danh sách trang căn chi tiết</a>')
    return "".join(o)


def dung_trang_can(can, s, active, hom_nay):
    """Trang căn ĐANG hiển thị — nội dung đầy đủ từ data.json."""
    ma = str(can.get("Mã nội bộ", "")).strip()
    loai = str(can.get("Loại", "")).strip()
    toa = str(can.get("Tòa", "")).strip()
    noi_that = str(can.get("Nội thất", "")).strip()
    dt = round(dien_tich_so(can.get("Diện tích")))
    gia_so = so_tien(can.get("Giá thuê"))
    gia = dinh_dang_gia(gia_so)
    phan_khu = phan_khu_tu_toa(toa)
    map_anh = active["_map_anh"]
    anh_urls = danh_sach_anh(can)
    ngay_vao_o = str(can.get("Ngày vào ở", "")).strip()
    ngay_str = hom_nay.strftime("%d/%m/%Y")
    ngay_xuat_hien_str = ngay_hien_thi(
        active["ban_do"][s].get("ngay_xuat_hien")) or ngay_str
    url = "%s/can-ho/%s/" % (TEN_MIEN, s)

    tieu_de = "Cho thuê căn hộ %s %s Vinhomes Smart City %dm² – %s/tháng" % (
        loai, toa, dt, gia)
    mo_ta = ("Cho thuê căn hộ %s tòa %s phân khu %s Vinhomes Smart City, diện tích "
              "%dm², %s, giá %s/tháng. %s. Cập nhật %s." % (
                  loai, toa, phan_khu or toa, dt,
                  noi_that.lower() if noi_that else "nội thất theo mô tả",
                  gia,
                  "Vào ở " + ngay_vao_o_hien_thi(can, hom_nay).lower()
                  if ngay_vao_o_hien_thi(can, hom_nay) != "Vào ngay"
                  else "Vào ở ngay",
                  ngay_xuat_hien_str))

    the_can_ten = "Căn hộ %s %s %dm²" % (loai, toa, dt)

    bua = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": TEN_MIEN + "/"},
            {"@type": "ListItem", "position": 2,
             "name": "Cho thuê căn hộ %s Vinhomes Smart City" % (phan_khu or toa),
             "item": TEN_MIEN + TRANG_PHAN_KHU.get(phan_khu, "/")},
            {"@type": "ListItem", "position": 3, "name": the_can_ten, "item": url},
        ],
    }, ensure_ascii=False)

    offers = {
        "@type": "Offer",
        "price": gia_so,
        "priceCurrency": "VND",
        "availability": "https://schema.org/InStock",
    }
    iso = ngay_iso(ngay_vao_o)
    if iso:
        offers["availabilityStarts"] = iso

    listing = json.dumps({
        "@context": "https://schema.org",
        "@type": "RealEstateListing",
        "name": the_can_ten,
        "url": url,
        "about": {
            "@type": "Apartment",
            "name": "%s %s" % (loai, toa),
            "floorSize": {"@type": "QuantitativeValue", "value": dt, "unitCode": "MTK"},
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "Vinhomes Smart City",
                "addressLocality": "Tây Mỗ",
                "addressRegion": "Hà Nội",
                "addressCountry": "VN",
            },
        },
        "offers": offers,
    }, ensure_ascii=False)

    og_image = og_image_cho_can(anh_urls, map_anh)

    dau = DAU_TRANG % {
        "tieu_de": esc(tieu_de),
        "mo_ta": esc(mo_ta),
        "url": esc(url),
        "og_image": esc(og_image),
        "robots": "index,follow",
        "bua": bua,
        "listing": listing,
        "phan_khu": esc(phan_khu or toa),
        "trang_phan_khu": esc(TRANG_PHAN_KHU.get(phan_khu, "/")),
        "bc_hien_tai": esc(the_can_ten),
    }

    anh_html = []
    for i, u in enumerate(anh_urls):
        src = anh_tu_url(u, map_anh)
        alt = "Ảnh %d căn hộ %s %s Vinhomes Smart City %dm²" % (i + 1, loai, toa, dt)
        tai = 'eager' if i == 0 else 'lazy'
        anh_html.append(
            '<img src="%s" alt="%s" loading="%s" decoding="async" width="800" height="600">'
            % (esc(src), esc(alt), tai))
    if anh_html:
        gallery = '  <section class="gallery">\n    %s\n  </section>\n' % "\n    ".join(anh_html)
    else:
        gallery = ('  <section class="gallery ct-gallery-empty-source">\n'
                   '    <div class="ct-no-photo"><b>Căn này đang cập nhật ảnh</b>'
                   '<span>Nhắn Zalo để nhận ảnh và video thực tế.</span></div>\n'
                   '  </section>\n')

    bang = ("<table class=\"bang\"><tbody>"
            "<tr><td>Mã căn</td><td>%s</td></tr>"
            "<tr><td>Loại</td><td>%s</td></tr>"
            "<tr><td>Diện tích</td><td>%d m²</td></tr>"
            "<tr><td>Tòa</td><td>%s</td></tr>"
            "<tr><td>Phân khu</td><td>%s</td></tr>"
            "<tr><td>Nội thất</td><td>%s</td></tr>"
            "<tr><td>Giá thuê</td><td>%s/tháng</td></tr>"
            "<tr><td>Ngày vào ở</td><td>%s</td></tr>"
            "<tr><td>Ngày cập nhật</td><td>%s</td></tr>"
            "</tbody></table>") % (
        esc(ma), esc(loai), dt, esc(toa), esc(phan_khu or toa), esc(noi_that or "Liên hệ"),
        esc(gia), esc(ngay_vao_o_hien_thi(can, hom_nay)), ngay_xuat_hien_str)

    lien_ket = lien_ket_noi_bo(phan_khu, loai, toa, gia_so, noi_that)

    tuong_tu = can_tuong_tu(s, toa, phan_khu, loai, active["ban_do"])
    tuong_tu_html = ""
    if tuong_tu:
        the_list = "".join(dung_the_tuong_tu(x, active["ban_do"][x]) for x in tuong_tu)
        tuong_tu_html = (
            '  <h2 style="font-size:19px;margin-bottom:2px">Căn tương tự</h2>\n'
            '  <div class="lq">%s</div>\n' % the_list)

    than = """  <h1>Cho thuê căn hộ %(loai)s %(dt)dm² tòa %(toa)s – Vinhomes Smart City</h1>
  <p class="tt">Căn hộ %(loai)s diện tích %(dt)dm² tại tòa %(toa)s, phân khu %(phan_khu)s,
Vinhomes Smart City. %(noi_that_cau)s Giá thuê %(gia)s/tháng. Cập nhật %(ngay)s.</p>

%(gallery)s
  <div class="sl">
    <div class="o"><b>%(dt)dm²</b><span>diện tích</span></div>
    <div class="o"><b>%(gia)s</b><span>giá thuê/tháng</span></div>
    <div class="o"><b>%(noi_that)s</b><span>nội thất</span></div>
    <div class="o"><b>%(vao_o)s</b><span>tình trạng</span></div>
  </div>

  %(bang)s

  <p style="margin:18px 0">
    <a class="cta-loc" href="https://zalo.me/%(sdt)s" target="_blank" rel="noopener">Nhắn Zalo hỏi căn %(ma)s</a>
    <a class="cta-home tren" href="tel:%(sdt)s">Gọi %(sdt)s</a>
  </p>

  <h2 style="font-size:19px;margin-bottom:2px">Xem thêm theo nhu cầu</h2>
  <div class="lq">%(lien_ket)s</div>

%(tuong_tu)s
""" % {
        "loai": esc(loai), "dt": dt, "toa": esc(toa), "phan_khu": esc(phan_khu or toa),
        "noi_that_cau": ("Căn %s." % noi_that.lower()) if noi_that else "",
        "gia": esc(gia), "ngay": ngay_xuat_hien_str, "gallery": gallery,
        "noi_that": esc(noi_that or "Liên hệ"),
        "vao_o": esc(ngay_vao_o_hien_thi(can, hom_nay)),
        "bang": bang, "sdt": SDT, "ma": esc(ma), "lien_ket": lien_ket,
        "tuong_tu": tuong_tu_html,
    }

    return dau + than + dung_footer(ngay_str)


def dung_trang_da_thue(s, ho_so, active, hom_nay):
    """Trang căn đã hết hạn hiển thị — 200, không noindex, không offers, gợi ý
    căn tương tự còn trống. Chỉ dùng dữ liệu đóng băng trong sổ đăng ký."""
    ma = ho_so["ma"]
    loai = ho_so["loai"]
    toa = ho_so["toa"]
    phan_khu = ho_so["phan_khu"]
    dt = round(dien_tich_so(ho_so["dien_tich"]))
    ngay_str = hom_nay.strftime("%d/%m/%Y")
    url = "%s/can-ho/%s/" % (TEN_MIEN, s)

    tieu_de = "Căn hộ %s %s %dm² đã có khách – Vinhomes Smart City" % (loai, toa, dt)
    mo_ta = ("Căn hộ %s tòa %s %dm² tại Vinhomes Smart City hiện đã có khách thuê. "
              "Xem các căn còn trống tương tự cùng tòa, cùng phân khu %s. Cập nhật %s."
              % (loai, toa, dt, phan_khu or toa, ngay_str))
    the_can_ten = "Căn hộ %s %s %dm² (đã có khách)" % (loai, toa, dt)

    bua = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": TEN_MIEN + "/"},
            {"@type": "ListItem", "position": 2,
             "name": "Cho thuê căn hộ %s Vinhomes Smart City" % (phan_khu or toa),
             "item": TEN_MIEN + TRANG_PHAN_KHU.get(phan_khu, "/")},
            {"@type": "ListItem", "position": 3, "name": the_can_ten, "item": url},
        ],
    }, ensure_ascii=False)

    listing = json.dumps({
        "@context": "https://schema.org",
        "@type": "RealEstateListing",
        "name": the_can_ten,
        "url": url,
        "about": {
            "@type": "Apartment",
            "name": "%s %s" % (loai, toa),
            "floorSize": {"@type": "QuantitativeValue", "value": dt, "unitCode": "MTK"},
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "Vinhomes Smart City",
                "addressLocality": "Tây Mỗ",
                "addressRegion": "Hà Nội",
                "addressCountry": "VN",
            },
        },
    }, ensure_ascii=False)

    dau = DAU_TRANG % {
        "tieu_de": esc(tieu_de),
        "mo_ta": esc(mo_ta),
        "url": esc(url),
        "og_image": ANH_MAC_DINH,
        # Tin đã có khách là ngõ cụt với người tìm nhà: giữ trang (200) để
        # backlink và khách cũ không gãy, nhưng gỡ khỏi index để Google dồn
        # crawl budget cho căn còn trống, và để SERP không còn title "đã có
        # khách". follow giữ nguyên nên link sang 6 căn tương tự vẫn truyền.
        "robots": "noindex,follow",
        "bua": bua,
        "listing": listing,
        "phan_khu": esc(phan_khu or toa),
        "trang_phan_khu": esc(TRANG_PHAN_KHU.get(phan_khu, "/")),
        "bc_hien_tai": esc(the_can_ten),
    }

    bang = ("<table class=\"bang\"><tbody>"
            "<tr><td>Mã căn</td><td>%s</td></tr>"
            "<tr><td>Loại</td><td>%s</td></tr>"
            "<tr><td>Diện tích</td><td>%d m²</td></tr>"
            "<tr><td>Tòa</td><td>%s</td></tr>"
            "<tr><td>Phân khu</td><td>%s</td></tr>"
            "</tbody></table>") % (esc(ma), esc(loai), dt, esc(toa), esc(phan_khu or toa))

    lien_ket = lien_ket_noi_bo(phan_khu, loai, toa, 0, "")

    tuong_tu = can_tuong_tu(s, toa, phan_khu, loai, active["ban_do"])
    tuong_tu_html = "<p>Hiện chưa có căn trống tương tự, mời xem <a href=\"/can-ho/\">toàn bộ căn hộ đang cho thuê</a>.</p>"
    if tuong_tu:
        the_list = "".join(dung_the_tuong_tu(x, active["ban_do"][x]) for x in tuong_tu)
        tuong_tu_html = '<div class="lq">%s</div>' % the_list

    than = """  <h1>%(tieu_de)s</h1>
  <section class="bai">
    <p><strong>Căn này đã có khách thuê.</strong> Dưới đây là các căn còn trống tương tự.</p>
  </section>

  %(bang)s

  <h2 style="font-size:19px;margin-bottom:2px">Căn còn trống tương tự</h2>
  %(tuong_tu)s

  <h2 style="font-size:19px;margin-bottom:2px">Xem thêm theo nhu cầu</h2>
  <div class="lq">%(lien_ket)s</div>
""" % {
        "tieu_de": esc(the_can_ten), "bang": bang,
        "tuong_tu": tuong_tu_html, "lien_ket": lien_ket,
    }

    return dau + than + dung_footer(ngay_str)


def dung_hub_internal_links(active):
    """Đường tắt từ /can-ho/ lên các cụm cha có nhiều căn nhất."""
    dem_pk = {}
    dem_loai = {}
    for c in active["ban_do"].values():
        pk = c.get("phan_khu") or ""
        loai = str(c.get("loai", "")).strip().lower()
        if pk in TRANG_PHAN_KHU:
            dem_pk[pk] = dem_pk.get(pk, 0) + 1
        if loai in TRANG_LOAI_CAN:
            dem_loai[loai] = dem_loai.get(loai, 0) + 1

    top_pk = sorted(dem_pk, key=lambda x: (-dem_pk[x], x))[:4]
    top_loai = sorted(dem_loai, key=lambda x: (-dem_loai[x], x))[:4]

    loai_html = "".join(
        '<a href="%s"><strong>%s</strong><span>%d căn đang có URL chi tiết.</span></a>'
        % (esc(TRANG_LOAI_CAN[l][0]), esc(TRANG_LOAI_CAN[l][1]), dem_loai[l])
        for l in top_loai)

    pk_html = "".join(
        '<a href="%s"><strong>%s</strong><span>%d căn đang có URL chi tiết.</span></a>'
        % (esc(TRANG_PHAN_KHU[pk]), esc(pk), dem_pk[pk])
        for pk in top_pk)

    guide_html = (
        '<a href="/bang-gia-thue-vinhomes-smart-city.html"><strong>Bảng giá thuê</strong>'
        '<span>So sánh giá theo loại căn và phân khu.</span></a>'
        '<a href="/so-sanh-gia-thue-cac-phan-khu-smart-city.html"><strong>So sánh phân khu</strong>'
        '<span>Đối chiếu mặt bằng giá giữa các khu.</span></a>'
        '<a href="/cam-nang-thue-nha.html"><strong>Cẩm nang thuê nhà</strong>'
        '<span>Quy trình, chi phí và lưu ý trước khi thuê.</span></a>'
    )

    return (
        '<div class="can-ho-hub-nav"><section class="seo-graph" '
        'aria-label="Điều hướng theo cụm căn hộ">'
        '<div class="seo-graph-head"><span>Đi theo cụm</span>'
        '<h2>Tìm nhanh trước khi mở từng căn</h2>'
        '<p>Đi từ danh sách URL căn hộ lên loại căn, phân khu hoặc cẩm nang phù hợp.</p></div>'
        '<div class="seo-graph-grid">'
        '<div class="seo-graph-group"><h3>Loại căn nhiều lựa chọn</h3>'
        '<div class="seo-graph-links">%s</div></div>'
        '<div class="seo-graph-group"><h3>Phân khu nhiều lựa chọn</h3>'
        '<div class="seo-graph-links">%s</div></div>'
        '<div class="seo-graph-group"><h3>Thông tin trước khi thuê</h3>'
        '<div class="seo-graph-links">%s</div></div>'
        '</div></section></div>'
    ) % (loai_html, pk_html, guide_html)


def dung_trang_hub(active, occupied_list, hom_nay):
    ngay_str = hom_nay.strftime("%d/%m/%Y")
    url = TEN_MIEN + "/can-ho/"
    so_active = len(active["ban_do"])
    so_tong = so_active + len(occupied_list)

    tieu_de = "Danh sách căn hộ cho thuê Vinhomes Smart City có ảnh chi tiết"
    mo_ta = ("Danh sách %d căn hộ cho thuê tại Vinhomes Smart City có trang riêng kèm ảnh "
              "thật, thông số đầy đủ. Cập nhật %s." % (so_active, ngay_str))

    bua = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": TEN_MIEN + "/"},
            {"@type": "ListItem", "position": 2, "name": "Danh sách căn hộ", "item": url},
        ],
    }, ensure_ascii=False)

    theo_phan_khu = {}
    for s, c in active["ban_do"].items():
        theo_phan_khu.setdefault(c["phan_khu"] or c["toa"], []).append(s)
    for pk in theo_phan_khu:
        theo_phan_khu[pk].sort()

    item_list = []
    vi_tri = 1
    khoi_html = []
    for pk in sorted(theo_phan_khu):
        muc = []
        for s in theo_phan_khu[pk]:
            c = active["ban_do"][s]
            dt = round(dien_tich_so(c["dien_tich"]))
            gia = dinh_dang_gia(so_tien(c.get("gia", 0)))
            href = "%s/can-ho/%s/" % (TEN_MIEN, s)
            item_list.append({"@type": "ListItem", "position": vi_tri, "url": href})
            vi_tri += 1
            muc.append('<li><a href="/can-ho/%s/">%s %s · %d m² · %s/tháng</a></li>' % (
                esc(s), esc(c["loai"]), esc(c["toa"]), dt, esc(gia)))
        khoi_html.append('<h2 style="font-size:19px">%s</h2>\n  <ul class="ds-can-ho">\n    %s\n  </ul>' % (
            esc(pk), "\n    ".join(muc)))

    if occupied_list:
        muc = []
        for s, ho_so in occupied_list:
            dt = round(dien_tich_so(ho_so["dien_tich"]))
            href = "%s/can-ho/%s/" % (TEN_MIEN, s)
            item_list.append({"@type": "ListItem", "position": vi_tri, "url": href})
            vi_tri += 1
            muc.append('<li><a href="/can-ho/%s/">%s %s · %d m² (đã có khách)</a></li>' % (
                esc(s), esc(ho_so["loai"]), esc(ho_so["toa"]), dt))
        khoi_html.append(
            '<h2 style="font-size:19px">Đã có khách</h2>\n  <ul class="ds-can-ho">\n    %s\n  </ul>'
            % "\n    ".join(muc))

    danh_sach = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "numberOfItems": so_tong,
        "itemListElement": item_list,
    }, ensure_ascii=False)

    return """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<!-- Trang này do scripts/sinh-trang-can.py sinh lại từ data.json mỗi lần
     chạy. Sửa tay ở đây sẽ mất trong lần chạy sau - sửa script, đừng sửa file. -->
<title>%(tieu_de)s</title>
<meta name="description" content="%(mo_ta)s">
<link rel="canonical" href="%(url)s">
<link rel="icon" href="/favicon.ico" sizes="any">
<meta property="og:type" content="website">
<meta property="og:url" content="%(url)s">
<meta property="og:title" content="%(tieu_de)s">
<meta property="og:description" content="%(mo_ta)s">
<meta property="og:image" content="%(og_image)s">
<meta property="og:site_name" content="Tìm Thuê Smart City">
<meta property="og:locale" content="vi_VN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(tieu_de)s">
<meta name="twitter:description" content="%(mo_ta)s">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-VF9KHC5TWD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}
gtag('js',new Date());gtag('config','G-VF9KHC5TWD');</script>
<script type="application/ld+json">%(bua)s</script>
<script type="application/ld+json">%(danh_sach)s</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Be+Vietnam+Pro:wght@300;400;500;600&display=swap"
      media="print" onload="this.media='all'">
<noscript>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Be+Vietnam+Pro:wght@300;400;500;600&display=swap">
</noscript>
<link rel="stylesheet" href="/assets/v3.css?v=20260830-6">
</head>
<body>
<header class="top">
  <div class="khung">
    <a class="hieu" href="/">Cho thuê chung cư Smart City<small>Ảnh thật · Cập nhật mỗi ngày</small></a>
    <nav>
      <a href="/">Tất cả căn</a><a href="/studio/">Studio</a><a href="/1pn-plus/">1 ngủ +</a>
      <a href="/2pn/">2 ngủ</a><a href="/3pn/">3 ngủ</a>
      <a href="/can-ho-vao-o-ngay-vinhomes-smart-city.html">Vào ở ngay</a>
      <a href="/cam-nang-thue-nha.html">Cẩm nang</a>
    </nav>
  </div>
</header>

<main class="khung">
  <p class="bc"><a href="/">Trang chủ</a> › <span>Danh sách căn hộ</span></p>
  <h1>Danh sách căn hộ cho thuê Vinhomes Smart City có ảnh chi tiết</h1>
  <p class="tt">%(mo_ta)s</p>

  <div class="sl">
    <div class="o"><b>%(so_active)d</b><span>căn đang trống</span></div>
    <div class="o"><b>%(so_tong)d</b><span>trang căn hộ</span></div>
  </div>

  %(hub_nav)s

  %(khoi)s

</main>

%(chan)s""" % {
        "tieu_de": esc(tieu_de), "mo_ta": esc(mo_ta), "url": esc(url),
        "og_image": ANH_MAC_DINH, "bua": bua, "danh_sach": danh_sach,
        "so_active": so_active, "so_tong": so_tong,
        "hub_nav": dung_hub_internal_links(active),
        "khoi": "\n\n  ".join(khoi_html),
        "chan": dung_footer(ngay_str).replace("</main>\n\n", "", 1),
    }


def dung_sitemap(active, hom_nay):
    ngay = hom_nay.isoformat()
    dong = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
            '  <url><loc>%s/can-ho/</loc><lastmod>%s</lastmod>'
            '<changefreq>daily</changefreq><priority>0.8</priority></url>' % (TEN_MIEN, ngay)]
    for s in sorted(active["ban_do"]):
        dong.append(
            '  <url><loc>%s/can-ho/%s/</loc><lastmod>%s</lastmod>'
            '<changefreq>weekly</changefreq><priority>0.6</priority></url>'
            % (TEN_MIEN, s, ngay))
    dong.append('</urlset>')
    return "\n".join(dong) + "\n"


def main():
    bo_phan_tich = argparse.ArgumentParser(
        description="Sinh trang tĩnh riêng cho từng căn hộ đủ điều kiện.")
    bo_phan_tich.add_argument("--thu", action="store_true",
                              help="chỉ in thống kê, không ghi file")
    tham_so = bo_phan_tich.parse_args()

    with open(DUONG_DATA, encoding="utf-8") as f:
        du_lieu = json.load(f)

    if not isinstance(du_lieu, list) or len(du_lieu) < NGUONG_TOI_THIEU:
        print("DỪNG AN TOÀN (mã 2): data.json có %d bản ghi, dưới ngưỡng %d "
              "— nhiều khả năng đang lỗi. Không sinh, không ghi đè, không xoá "
              "gì. Các bước còn lại của workflow vẫn chạy bình thường. Kiểm "
              "tra lại data.json rồi chạy lại."
              % (len(du_lieu) if isinstance(du_lieu, list) else 0, NGUONG_TOI_THIEU))
        return 2

    qualifying = [c for c in du_lieu if du_dieu_kien(c)]
    thieu_ma = [c for c in du_lieu if dang_hien_thi(c) and not ma_hop_le(c)]
    print("data.json               : %d bản ghi" % len(du_lieu))
    print("Đủ điều kiện sinh trang  : %d" % len(qualifying))
    thieu_du_lieu = [c for c in du_lieu
                     if dang_hien_thi(c) and ma_hop_le(c) and not du_du_lieu_cap_url(c)]
    if thieu_ma:
        print("CẢNH BÁO: %d căn public đang thiếu Mã nội bộ — không thể cấp URL ổn định; giữ căn trên danh sách nhưng không tự bịa URL." % len(thieu_ma))
    if thieu_du_lieu:
        print("CẢNH BÁO: %d căn public thiếu Tòa hoặc Diện tích — không sinh trang chi tiết "
              "(slug sẽ thành dạng '--0m2'). Điền vào Google Sheet để lần chạy sau có URL:"
              % len(thieu_du_lieu))
        for c in thieu_du_lieu[:10]:
            print("    mã %s · tòa %r · diện tích %r"
                  % (str(c.get("Mã nội bộ", "")).strip(),
                     str(c.get("Tòa", "")).strip(), c.get("Diện tích")))
        if len(thieu_du_lieu) > 10:
            print("    … và %d căn nữa." % (len(thieu_du_lieu) - 10))

    if len(qualifying) > TOI_DA:
        print("\nDỪNG AN TOÀN (mã 2): %d căn đủ điều kiện, vượt trần %d.\n"
              "Không sinh, không ghi đè, không xoá gì. Các bước còn lại của\n"
              "workflow vẫn chạy bình thường. Kiểm tra data.json rồi nâng trần\n"
              "nếu con số này là thật."
              % (len(qualifying), TOI_DA))
        return 2

    if len(qualifying) >= TOI_DA * NGUONG_CANH_BAO:
        print("\nCẢNH BÁO: %d/%d căn đủ điều kiện (%d%% trần). Cân nhắc nâng TOI_DA."
              % (len(qualifying), TOI_DA, round(100 * len(qualifying) / TOI_DA)))

    # Chốt chặn cuối: kể cả khi tòa và diện tích đã có, một mã tòa chưa nằm
    # trong bảng ánh xạ phân khu vẫn cho slug dạng "...-ngu--<dt>m2-...".
    # Lọc theo chính chuỗi slug là cách duy nhất bắt được mọi nguyên nhân.
    slug_hong = [c for c in qualifying if slug_rac(tinh_slug(c))]
    if slug_hong:
        print("CẢNH BÁO: %d căn cho slug không hợp lệ — bỏ qua, không sinh trang:"
              % len(slug_hong))
        for c in slug_hong[:10]:
            print("    mã %s · tòa %r -> %s"
                  % (str(c.get("Mã nội bộ", "")).strip(),
                     str(c.get("Tòa", "")).strip(), tinh_slug(c)))
        qualifying = [c for c in qualifying if not slug_rac(tinh_slug(c))]

    qualifying.sort(key=tinh_slug)

    ban_do_active = {}
    trung_slug = {}
    for c in qualifying:
        s = tinh_slug(c)
        if s in trung_slug:
            print("\nDỪNG: hai căn cho cùng slug %s (%s và %s)." % (
                s, trung_slug[s], c.get("Mã nội bộ")))
            return 1
        trung_slug[s] = c.get("Mã nội bộ")
        ban_do_active[s] = {
            "ma": str(c.get("Mã nội bộ", "")).strip(),
            "toa": str(c.get("Tòa", "")).strip(),
            "phan_khu": phan_khu_tu_toa(c.get("Tòa", "")),
            "loai": str(c.get("Loại", "")).strip(),
            "dien_tich": c.get("Diện tích"),
            "gia": so_tien(c.get("Giá thuê")),
        }

    so_dang_ky = doc_so_dang_ky()
    hom_nay = ngay_hom_nay()

    # Dọn slug rác đã lỡ sinh trước khi có du_du_lieu_cap_url. Giữ chúng trong
    # sổ đăng ký thì mỗi lần chạy lại dựng lại đúng 24 trang "0m² đã có khách",
    # vì nhánh occupied lấy dữ liệu từ sổ chứ không từ data.json. Xoá khỏi sổ
    # VÀ xoá thư mục để Google nhận 404 và loại chúng khỏi index.
    slug_can_don = sorted(s for s in so_dang_ky if slug_rac(s))
    if slug_can_don:
        print("Dọn %d URL rác (slug thiếu tòa/diện tích):" % len(slug_can_don))
        for s in slug_can_don[:5]:
            print("    /can-ho/%s/" % s)
        if len(slug_can_don) > 5:
            print("    … và %d URL nữa." % (len(slug_can_don) - 5))
        for s_rac in slug_can_don:
            so_dang_ky.pop(s_rac, None)

    # Mã căn là khoá ổn định. Nếu tòa/loại/diện tích được sửa
    # làm slug thay đổi, vẫn phải giữ ngày xuất hiện của căn cũ.
    ngay_xuat_hien_theo_ma = {}
    for ho_so in so_dang_ky.values():
        ma = str(ho_so.get("ma", "")).strip()
        ngay = ngay_iso(ho_so.get("ngay_xuat_hien", ""))
        if ma and ngay:
            ngay_xuat_hien_theo_ma.setdefault(ma, ngay)

    for s in ban_do_active:
        rec = ban_do_active[s]
        ho_so_cu = so_dang_ky.get(s, {})
        ngay_xuat_hien = (
            ngay_iso(ho_so_cu.get("ngay_xuat_hien", ""))
            or ngay_xuat_hien_theo_ma.get(rec["ma"])
            or hom_nay.isoformat()
        )
        rec["ngay_xuat_hien"] = ngay_xuat_hien
        ngay_xuat_hien_theo_ma.setdefault(rec["ma"], ngay_xuat_hien)
        so_dang_ky[s] = {
            "ma": rec["ma"], "toa": rec["toa"], "phan_khu": rec["phan_khu"],
            "loai": rec["loai"], "dien_tich": rec["dien_tich"],
            "ngay_xuat_hien": ngay_xuat_hien,
        }

    occupied_slugs = sorted(set(so_dang_ky) - set(ban_do_active))
    occupied_list = [(s, so_dang_ky[s]) for s in occupied_slugs]

    map_anh = doc_map_anh()
    active = {"ban_do": ban_do_active, "_map_anh": map_anh}
    print("Đang có trang (đã thuê) : %d" % len(occupied_list))
    print("Tổng trang căn (sổ đăng ký) sau lần chạy này: %d" % len(so_dang_ky))

    if tham_so.thu:
        print("\n(--thu) Không ghi file. Sẽ ghi %d trang căn (%d hoạt động + %d đã thuê), "
              "1 trang hub, sitemap-can-ho.xml (%d URL) và danh-sach-trang.json (%d mục)."
              % (len(so_dang_ky), len(ban_do_active), len(occupied_list),
                 len(ban_do_active) + 1, len(so_dang_ky)))
        return 0

    os.makedirs(THU_MUC_CAN_HO, exist_ok=True)

    for s_rac in slug_can_don:
        thu_muc_rac = os.path.join(THU_MUC_CAN_HO, s_rac)
        if os.path.isdir(thu_muc_rac):
            shutil.rmtree(thu_muc_rac)

    for c in qualifying:
        s = tinh_slug(c)
        trang = dung_trang_can(c, s, active, hom_nay)
        thu_muc = os.path.join(THU_MUC_CAN_HO, s)
        os.makedirs(thu_muc, exist_ok=True)
        with open(os.path.join(thu_muc, "index.html"), "w", encoding="utf-8", newline="") as f:
            f.write(trang)

    for s, ho_so in occupied_list:
        trang = dung_trang_da_thue(s, ho_so, active, hom_nay)
        thu_muc = os.path.join(THU_MUC_CAN_HO, s)
        os.makedirs(thu_muc, exist_ok=True)
        with open(os.path.join(thu_muc, "index.html"), "w", encoding="utf-8", newline="") as f:
            f.write(trang)

    with open(os.path.join(THU_MUC_CAN_HO, "index.html"), "w", encoding="utf-8", newline="") as f:
        f.write(dung_trang_hub(active, occupied_list, hom_nay))

    with open(DUONG_SITEMAP, "w", encoding="utf-8", newline="") as f:
        f.write(dung_sitemap(active, hom_nay))

    ghi_so_dang_ky(so_dang_ky)

    print("\nĐã ghi %d trang căn hoạt động, %d trang đã thuê, 1 trang hub, "
          "sitemap-can-ho.xml và danh-sach-trang.json." % (
              len(ban_do_active), len(occupied_list)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

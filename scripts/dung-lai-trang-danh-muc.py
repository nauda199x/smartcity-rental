#!/usr/bin/env python3
"""Dựng lại thân động của 25 trang danh mục từ data.json.

VÌ SAO CẦN SCRIPT NÀY
---------------------
25 trang danh mục có thân tĩnh dựng MỘT LẦN rồi để đó, trong khi
scripts/cap-nhat-so-can.mjs cập nhật <title>, meta description và khối
ItemList từ data.json 3 lần/ngày. Hai nửa của cùng một trang vì thế trôi xa
nhau: đo lúc 11/08/2026 có 359/794 thẻ căn (45%) mang mã nội bộ không còn
trong tập căn đang hiển thị, và 23/25 trang lệch số căn giữa <title>,
<h2 class="tieu-de-luoi"> và số thẻ article.the thật.

dong-bo-can.js có dựng lại lưới trong trình duyệt nên khách thật không thấy
lỗi này. Nhưng Google index đợt đầu đọc HTML thô trước, render sau và thường
trễ — nên phần Googlebot đọc được ngay lại là phần sai. Trang
/s4-01-vinhomes-smart-city/ do scripts/sinh-trang-toa.py dựng lại 3 lần/ngày
có 0/10 căn cũ, chứng minh cách làm đúng đã có sẵn trong repo.

Script này áp đúng cách làm đó cho 25 trang danh mục còn lại.

PHẠM VI — NĂM KHỐI ĐƯỢC GHI ĐÈ
------------------------------
    section.luoi          toàn bộ article.the
    h2.tieu-de-luoi       "Danh sách {N} căn đang cho thuê"
    p.tt (khối đầu tiên)  số căn, khoảng diện tích, ngày cập nhật
    div.sl                bốn ô thống kê
    table.bang            bảng giá theo phân khu / theo loại căn + ngày ở
                          dòng chú thích ngay dưới bảng

Bốn khối đầu là phạm vi giao việc. Khối thứ năm là phần PHẢI thêm sau khi đo:
bảng giá tự nhận "Số liệu tính trực tiếp từ danh sách căn đang trống ở trên,
cập nhật 24/07/2026." nhưng lại đóng băng từ 24/07 — 25/25 trang đang như vậy.
Dựng lại lưới mà để nguyên bảng thì bảng nói khác hẳn danh sách nó vừa viện
dẫn, và chuỗi ngày 24/07/2026 vẫn còn nguyên trên cả 25 trang (nghiệm thu B-3
đòi 0). Chi tiết cách dựng xem RE_BANG bên dưới.

Không đụng khối .lq ("Đọc thêm trước khi thuê"), không đụng JSON-LD (đó là
việc của cap-nhat-so-can.mjs), không đụng data.json.

NGUYÊN TẮC
----------
  - Toàn bộ hàm dựng thẻ căn DÙNG LẠI scripts/sinh-trang-toa.py qua importlib,
    không chép lại. Nhờ vậy sinh-trang-toa.py không phải sửa một dòng nào và
    trang S4.01 — đang là phép thử có mốc đo tháng 9 — không thể bị ảnh hưởng.
  - Logic lọc và thứ tự sắp xếp chép nguyên ngữ nghĩa từ dong-bo-can.js. Đã
    đối chiếu: scripts/cap-nhat-so-can.mjs (hàm dsCanLenLuoi) đang chạy đúng
    cùng logic đó. Ba bản phải luôn giống nhau, lệch một chỗ là title hứa
    khác lưới căn.
  - Chạy hai lần trên cùng data.json phải ra file giống hệt từng byte. Repo
    đã có ~48 commit rỗng/ngày từ Apps Script, không thêm nguồn rác thứ hai.
  - Không tự tạo khối chưa tồn tại. Thiếu .sl hoặc .tt thì bỏ qua khối đó và
    ghi cảnh báo.
  - data.json rỗng, hoặc lọc ra 0 căn trong khi trang đang có thẻ -> giữ
    nguyên trang, ghi cảnh báo, thoát mã 0. Chép đúng lớp bảo vệ của
    dong-bo-can.js (hàm chay: "dsCan.length === 0 && soCu > 0 -> return").

Chạy:  python3 scripts/dung-lai-trang-danh-muc.py [--thu]
"""

import argparse
import importlib.util
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DUONG_DATA = os.path.join(GOC, "data.json")

BO_QUA_THU_MUC = {".git", ".github", "node_modules", "images", "scripts",
                  "anh-can-ho"}


def nap_sinh_trang_toa():
    """Nạp sinh-trang-toa.py để dùng lại nguyên bộ hàm dựng thẻ căn.

    Tên file có dấu gạch ngang nên không import thẳng được, phải đi đường
    importlib — đúng thủ pháp mà chính sinh-trang-toa.py đang dùng để nạp
    sinh-danh-sach-anh.py.

    Chép lại dung_the_can() sang đây thì sớm muộn hai bản cũng lệch nhau, và
    lệch ở đúng chỗ đau nhất: markup thẻ căn phải trùng khít với v3.css và với
    thẻ mà dong-bo-can.js dựng trong trình duyệt."""
    duong = os.path.join(THU_MUC_SCRIPT, "sinh-trang-toa.py")
    dac_ta = importlib.util.spec_from_file_location("sinh_trang_toa", duong)
    mo_dun = importlib.util.module_from_spec(dac_ta)
    # Không để Python đẻ ra scripts/__pycache__/ chỉ vì một lần import.
    cu = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        dac_ta.loader.exec_module(mo_dun)
    finally:
        sys.dont_write_bytecode = cu
    return mo_dun


STT = nap_sinh_trang_toa()

# Dùng lại nguyên văn, không định nghĩa lại (bảng ở HUONG-DAN mục B.1).
dung_the_can = STT.dung_the_can          # dòng 271 — dựng article.the
anh_dai_dien = STT.anh_dai_dien          # dòng 196 — chọn ảnh qua anh-map.json
doc_map_anh = STT.doc_map_anh            # dòng 182 — nạp bản đồ ảnh
so_tien = STT.so_tien                    # dòng 123 — chuẩn hoá tiền
dien_tich = STT.dien_tich                # dòng 129 — chuẩn hoá diện tích
dinh_dang_gia = STT.dinh_dang_gia        # dòng 141 — "8,5 triệu"
ngay_hom_nay = STT.ngay_hom_nay          # hôm nay theo giờ Việt Nam
phan_khu_tu_toa = STT.phan_khu_tu_toa    # ánh xạ mã tòa -> phân khu
khoang_gia = STT.khoang_gia              # "8 triệu – 12,5 triệu"
esc = STT.esc                            # dòng 110 — escape HTML


# ===========================================================================
# PHẦN 1 — Lọc và sắp xếp. Chép nguyên ngữ nghĩa từ dong-bo-can.js.
# ===========================================================================

def chuan(v):
    """dong-bo-can.js dòng 41: String(v == null ? "" : v).trim()"""
    return str("" if v is None else v).strip()


def khoa(v):
    """dong-bo-can.js dòng 42: chuan(v).toLowerCase()

    CHÚ Ý: khoa() KHÔNG bỏ dấu và KHÔNG gộp khoảng trắng — nó chỉ trim rồi
    thường hoá. Đã kiểm lại tận nơi trong dong-bo-can.js trước khi viết hàm
    này. Thêm bước bỏ dấu ở đây sẽ làm bản Python lọc rộng hơn bản chạy trong
    trình duyệt, và số căn trong HTML lại lệch với lưới khách nhìn thấy —
    đúng lỗi mà script này sinh ra để sửa."""
    return chuan(v).lower()


def la_can_hop_le(r):
    """dong-bo-can.js dòng 48. Đo trên data.json ngày 11/08/2026: cột
    "Hiển thị trên Web" có các giá trị 'Có' (243), 'Có ' (24, thừa dấu cách),
    'có' (1), 'Không' (465), '' (115), 'không' (2) — trim + thường hoá là đủ
    nhận đúng 268 căn bật hiển thị."""
    v = khoa(r.get("Hiển thị trên Web")
             or r.get("Hiển thị trên web")
             or r.get("Hiển thị"))
    return v in ("có", "co", "yes", "true")


def khop_bo_loc(r, bl):
    """dong-bo-can.js dòng 551 (hàm khopBoLoc), giữ nguyên từng điều kiện.

    Chú ý hai mốc giá KHÔNG đối xứng, đây là chủ ý của bản gốc:
      giaTren -> giữ khi gia > giaTren   (lớn hơn tuyệt đối)
      giaMax  -> giữ khi 0 < gia <= giaMax
    Đổi một trong hai thành >= hay < là số căn của /2pn-10-12-trieu/ và
    /studio-7-10-trieu/ lệch ngay."""
    if bl.get("loai") and khoa(r.get("Loại")) != khoa(bl["loai"]):
        return False
    if bl.get("phanKhu") and khoa(phan_khu_tu_toa(r.get("Tòa", ""))) != khoa(bl["phanKhu"]):
        return False
    if bl.get("noiThat") and khoa(r.get("Nội thất")) != khoa(bl["noiThat"]):
        return False
    g = so_tien(r.get("Giá thuê"))
    if bl.get("giaTren") and not g > bl["giaTren"]:
        return False
    if bl.get("giaMax") and not (g > 0 and g <= bl["giaMax"]):
        return False
    return True


def can_len_luoi(r, bl):
    """Đúng ba điều kiện của dong-bo-can.js dòng 581."""
    return la_can_hop_le(r) and chuan(r.get("Mã nội bộ")) and khop_bo_loc(r, bl)


def anh_bia(can, map_anh):
    """Ảnh bìa theo đúng hàm anhBia của dong-bo-can.js (dòng 208): ưu tiên
    "Ảnh đại diện", rỗng thì lấy ảnh đầu trong "Danh sách ảnh".

    sinh-trang-toa.py chỉ đọc "Ảnh đại diện" nên phải bọc thêm nhánh dự phòng
    ở đây; phần đổi URL Drive -> đường dẫn WebP trong repo vẫn để nguyên
    anh_dai_dien() lo. Đo trên data.json ngày 11/08/2026: 0/265 căn rơi vào
    nhánh dự phòng này, nhưng thiếu nó thì một căn chỉ có "Danh sách ảnh" sẽ
    bị xếp vào nhóm "có ảnh" mà thẻ lại không có ảnh nào."""
    url = chuan(can.get("Ảnh đại diện"))
    if not url:
        url = chuan(chuan(can.get("Danh sách ảnh")).split("\n")[0])
    if not url:
        return ""
    return anh_dai_dien({"Ảnh đại diện": url}, map_anh)


def ds_can_len_luoi(du_lieu, bl, map_anh):
    """Đúng tập căn VÀ đúng thứ tự mà dong-bo-can.js dựng (dòng 589):
        1. lọc bằng can_len_luoi;
        2. sắp theo giá tăng dần;
        3. căn có ảnh bìa đứng trước, căn chưa có ảnh dồn xuống cuối, mỗi
           nhóm giữ nguyên thứ tự tương đối theo giá.

    sorted() của Python là sort ổn định nên hai căn cùng giá luôn giữ thứ tự
    xuất hiện trong data.json — chạy lại script cho ra đúng kết quả cũ, không
    sinh diff giả (nghiệm thu B-5)."""
    ds = [r for r in du_lieu if can_len_luoi(r, bl)]
    ds.sort(key=lambda r: so_tien(r.get("Giá thuê")))
    co_anh = [r for r in ds if anh_bia(r, map_anh)]
    khong_anh = [r for r in ds if not anh_bia(r, map_anh)]
    return co_anh + khong_anh


def thong_ke_trang(cac_can):
    """Bốn con số của khối .sl, tính đúng như dong-bo-can.js dòng 604-618."""
    gia_min = 0
    dt_min = 0
    dt_max = 0
    phan_khu = set()
    for c in cac_can:
        g = so_tien(c.get("Giá thuê"))
        if g > 0 and (gia_min == 0 or g < gia_min):
            gia_min = g
        dt = dien_tich(c.get("Diện tích"))
        if dt > 0:
            if dt_min == 0 or dt < dt_min:
                dt_min = dt
            if dt > dt_max:
                dt_max = dt
        t = phan_khu_tu_toa(c.get("Tòa", ""))
        if t:
            phan_khu.add(t)

    if dt_min > 0:
        chuoi_dt = ("%dm²" % round(dt_min) if dt_min == dt_max
                    else "%d–%dm²" % (round(dt_min), round(dt_max)))
    else:
        chuoi_dt = ""

    return {
        "so_can": len(cac_can),
        "gia_min": gia_min,
        "chuoi_dt": chuoi_dt,
        "so_phan_khu": len(phan_khu),
    }


# ===========================================================================
# PHẦN 2 — Dựng thẻ căn
# ===========================================================================

# Thẻ căn không có ảnh: dong-bo-can.js đặt class "the khong-anh" và bỏ hẳn thẻ
# <img>, còn dung_the_can() của sinh-trang-toa.py luôn ghi class "the" kèm một
# <img src=""> — vì trang S4.01 đo được 10/10 căn đều có ảnh nên nhánh đó chưa
# bao giờ chạy tới ở bên kia.
#
# 25 trang danh mục thì có thật: bản tĩnh hiện tại đang chứa những thẻ
# <article class="the khong-anh"> không hề có <img>, đúng dạng dong-bo-can.js
# dựng. Vì vậy phải vá lại output cho đúng dạng đó.
#
# Vá bằng hai phép thay chuỗi có neo rõ ràng, KHÔNG sửa sinh-trang-toa.py:
# nghiệm thu B-6 đòi output của script kia không đổi một byte, mà trang S4.01
# đang là phép thử có mốc đo tháng 9.
RE_IMG_RONG = re.compile(r'<img src=""[^>]*>')


def dung_the(can, map_anh, hom_nay):
    """Một thẻ căn của trang danh mục.

    phan_khu suy từ chính mã tòa của căn (không phải từ bộ lọc của trang):
    trang /2pn/ gộp căn của nhiều phân khu nên mỗi thẻ phải tự ghi phân khu
    của nó — đúng như dong-bo-can.js làm ở dòng 458."""
    toa = chuan(can.get("Tòa"))
    anh = anh_bia(can, map_anh)

    # Ảnh lấy được từ nhánh dự phòng "Danh sách ảnh" thì phải nhét ngược vào
    # bản sao của bản ghi, vì dung_the_can() chỉ đọc "Ảnh đại diện".
    ban_ghi = can
    if anh and not chuan(can.get("Ảnh đại diện")):
        ban_ghi = dict(can)
        ban_ghi["Ảnh đại diện"] = anh

    the = dung_the_can(ban_ghi, phan_khu_tu_toa(toa), map_anh, hom_nay)

    if anh:
        return the

    # Không có ảnh -> đưa về đúng dạng dong-bo-can.js dựng.
    the_moi = the.replace('<article class="the"',
                          '<article class="the khong-anh"', 1)
    the_moi, so_lan = RE_IMG_RONG.subn("", the_moi, count=1)
    if the_moi == the or so_lan != 1:
        # Markup của sinh-trang-toa.py đã đổi -> dừng hẳn còn hơn ghi ra thẻ
        # hỏng trên 25 trang.
        raise RuntimeError(
            "Không vá được thẻ căn không ảnh (%s): markup của "
            "sinh-trang-toa.py đã đổi, phải rà lại dung_the()."
            % chuan(can.get("Mã nội bộ")))
    return the_moi


# ===========================================================================
# PHẦN 3 — Ghi đè bốn khối trong HTML
# ===========================================================================

RE_BO_LOC = re.compile(
    r'<script type="application/json" id="bo-loc-trang">(.*?)</script>', re.S)

# Neo phần đóng vào "\n + thụt lề + </thẻ>" để bắt đúng thẻ đóng ngoài cùng,
# không dừng ở </div> của một ô con.
RE_LUOI = re.compile(r'(<section class="luoi"[^>]*>)(.*?)(\n[ \t]*</section>)', re.S)
RE_H2 = re.compile(r'(<h2 class="tieu-de-luoi"[^>]*>)(.*?)(</h2>)', re.S)
RE_TT = re.compile(r'(<p class="tt"[^>]*>)(.*?)(</p>)', re.S)
RE_SL = re.compile(r'(<div class="sl"[^>]*>)(.*?)(\n[ \t]*</div>)', re.S)
RE_O = re.compile(r'(<div class="o"><b>)(.*?)(</b><span>)(.*?)(</span></div>)')

# Câu "Đang hiện 60 trong tổng số 68 căn" chỉ đúng khi thân trang còn bị chặn
# ở 60 thẻ. Script này bỏ chặn đó (dong-bo-can.js không có chặn nào, giữ lại
# sẽ tái tạo đúng lỗi lệch số đang cần sửa) nên câu đó thành sai — gỡ luôn.
# Đo ngày 11/08/2026: chỉ 2/25 trang có câu này (/sapphire/ và /2pn/), đúng
# hai trang đang bị chặn ở 60 thẻ.
RE_DANG_HIEN = re.compile(
    r'[ \t]*<p class="tt">Đang hiện\s+\d+\s+trong tổng số\s+\d+\s+căn\.'
    r'.*?</p>\n', re.S)

# --- Bảng giá dưới phần nội dung ------------------------------------------
# Mỗi trang có ĐÚNG MỘT <table class="bang">, gom theo một trong hai chiều:
#   17/25 trang (trang loại căn, trang khoảng giá): "Phân khu | Số căn trống |
#          Khoảng giá/tháng"
#    8/25 trang (trang phân khu):                   "Loại căn | Số căn trống |
#          Khoảng giá/tháng"
# Chiều gom được ĐỌC TỪ CHÍNH Ô <th> ĐẦU TIÊN của bảng, không viết cứng theo
# đường dẫn: thêm trang danh mục mới là script tự nhận đúng chiều.
#
# Thứ tự dòng: nhiều căn nhất đứng trước, cùng số căn thì xếp theo tên. Đây là
# quy tắc sinh-trang-toa.py đang dùng cho thống kê theo loại (khoá sắp xếp
# (-so_can, ten)) — bảng tĩnh cũ xếp ngẫu nhiên ở các dòng cùng số căn, không
# tái lập được, nên phải chọn một quy tắc xác định để chạy hai lần ra một kết
# quả (nghiệm thu B-5).
#
# Khoảng giá dùng lại khoang_gia() của sinh-trang-toa.py, nên nhóm chỉ có một
# mức giá ghi gọn "9 triệu" thay vì "9 triệu – 9 triệu" như bản tĩnh cũ.
RE_BANG = re.compile(
    r'(<table class="bang">\s*<thead><tr><th>)([^<]*)(</th>.*?<tbody>)(.*?)(</tbody>)',
    re.S)

# Dòng chú thích ngay dưới bảng, chứa chuỗi ngày đóng băng 24/07/2026.
RE_CHU_THICH_NGAY = re.compile(
    r'(Số liệu tính trực tiếp từ danh sách căn đang trống ở trên,\s*'
    r'[Cc]ập nhật)\s*\d{1,2}/\d{1,2}/\d{4}')

# Ngày ở chân trang. Đo ngày 11/08/2026: 26/42 file HTML có dòng này — 25
# trang danh mục đóng băng ở 24/07/2026, và /s4-01-vinhomes-smart-city/ ghi
# 11/08/2026 vì sinh-trang-toa.py (dòng 483) dựng lại nó mỗi lần chạy. Nói
# cách khác trang duy nhất được sinh tự động là trang duy nhất có ngày đúng;
# 25 trang còn lại chỉ đang thiếu chính cơ chế đó. Neo vào cả dấu "·" đứng sau
# để không đụng nhầm chữ "Cập nhật" ở chỗ khác trong trang.
RE_CHAN_NGAY = re.compile(r'(<p>[Cc]ập nhật\s+)\d{1,2}/\d{1,2}/\d{4}(\s*·)')

RE_TT_SO_CAN = re.compile(r'Danh sách\s+\d+\s+căn')
RE_TT_DIEN_TICH = re.compile(
    r'diện tích\s*[\d.,]+\s*[–-]\s*[\d.,]+\s*m²', re.I)
# Giữ nguyên kiểu viết hoa/thường của chữ "cập nhật": 11/25 trang viết hoa
# ("… diện tích 42–49m². Cập nhật 24/07/2026."), viết thường hoá nó sẽ thành
# lỗi chính tả ngay sau dấu chấm.
#
# dong-bo-can.js dòng 631-632 định làm đúng như vậy — nó có hẳn hai lệnh
# replace, một cho "cập nhật" một cho "Cập nhật" — nhưng lệnh đầu mang cờ /i
# nên đã nuốt luôn cả trường hợp viết hoa và lệnh thứ hai không bao giờ chạy.
# Ở đây bám theo Ý ĐỊNH đó chứ không bám theo lỗi: nhóm ([Cc]) được trả lại
# nguyên vẹn. cap-nhat-so-can.mjs (hằng RE_DESC_NGAY) cũng đang giữ nguyên
# kiểu viết đúng cách này cho meta description.
RE_TT_NGAY = re.compile(r'([Cc]ập nhật)\s*\d{1,2}/\d{1,2}/\d{4}')


def doc_bo_loc(html):
    khop = RE_BO_LOC.search(html)
    if not khop:
        return None
    try:
        return json.loads(khop.group(1))
    except ValueError:
        return None


def dem_the(html):
    khop = RE_LUOI.search(html)
    if not khop:
        return 0
    return len(re.findall(r'<article class="the[" ]', khop.group(2)))


def ghi_de_luoi(html, cac_the, ten, canh_bao):
    khop = RE_LUOI.search(html)
    if not khop:
        canh_bao.append("%s: không tìm thấy section.luoi — BỎ QUA lưới căn." % ten)
        return html, False
    moi = "\n" + "\n".join(cac_the)
    if moi == khop.group(2):
        return html, False
    return (html[:khop.start()] + khop.group(1) + moi + khop.group(3)
            + html[khop.end():]), True


def ghi_de_h2(html, so_can, ten, canh_bao):
    khop = RE_H2.search(html)
    if not khop:
        canh_bao.append("%s: không tìm thấy h2.tieu-de-luoi — BỎ QUA tiêu đề lưới." % ten)
        return html, False
    moi = "Danh sách %d căn đang cho thuê" % so_can
    if moi == khop.group(2):
        return html, False
    return (html[:khop.start()] + khop.group(1) + moi + khop.group(3)
            + html[khop.end():]), True


def ghi_de_tt(html, tk, ngay, ten, canh_bao):
    """Chỉ thay ba cụm số trong đoạn mô tả, giữ nguyên phần chữ riêng của
    từng trang (dong-bo-can.js dòng 626-634)."""
    khop = RE_TT.search(html)
    if not khop:
        canh_bao.append("%s: không tìm thấy p.tt — BỎ QUA đoạn mô tả." % ten)
        return html, False
    doan = khop.group(2)
    moi = RE_TT_SO_CAN.sub("Danh sách %d căn" % tk["so_can"], doan, count=1)
    if tk["chuoi_dt"]:
        moi = RE_TT_DIEN_TICH.sub("diện tích " + tk["chuoi_dt"], moi, count=1)
    moi = RE_TT_NGAY.sub(lambda m: "%s %s" % (m.group(1), ngay), moi, count=1)
    if moi == doan:
        return html, False
    return (html[:khop.start()] + khop.group(1) + moi + khop.group(3)
            + html[khop.end():]), True


def ghi_de_sl(html, tk, ten, canh_bao):
    """Bốn ô thống kê. Ô nào không tính được thì giữ nguyên giá trị cũ, đúng
    như dong-bo-can.js (capNhatO chỉ được gọi khi giá trị > 0)."""
    khop = RE_SL.search(html)
    if not khop:
        canh_bao.append("%s: không tìm thấy div.sl — BỎ QUA khối thống kê." % ten)
        return html, False

    gia_tri = {"căn đang trống": str(tk["so_can"])}
    if tk["gia_min"] > 0:
        gia_tri["giá thấp nhất"] = dinh_dang_gia(tk["gia_min"])
    if tk["chuoi_dt"]:
        gia_tri["diện tích"] = tk["chuoi_dt"]
    if tk["so_phan_khu"] > 0:
        gia_tri["phân khu"] = str(tk["so_phan_khu"])

    thay = []

    def mot_o(m):
        nhan = m.group(4)
        for khoa_nhan, gt in gia_tri.items():
            if khoa_nhan in nhan:
                if m.group(2) != gt:
                    thay.append(nhan)
                return m.group(1) + gt + m.group(3) + nhan + m.group(5)
        return m.group(0)

    than_moi = RE_O.sub(mot_o, khop.group(2))
    if not thay:
        return html, False
    return (html[:khop.start()] + khop.group(1) + than_moi + khop.group(3)
            + html[khop.end():]), True


def ghi_de_bang(html, cac_can, ten, canh_bao):
    """Dựng lại bảng giá từ đúng tập căn đang hiển thị trên lưới."""
    khop = RE_BANG.search(html)
    if not khop:
        canh_bao.append("%s: không tìm thấy table.bang — BỎ QUA bảng giá." % ten)
        return html, False

    cot = khoa(khop.group(2))
    if cot.startswith("phân khu"):
        lay_nhom = lambda c: phan_khu_tu_toa(c.get("Tòa", ""))
    elif cot.startswith("loại"):
        lay_nhom = lambda c: chuan(c.get("Loại"))
    else:
        canh_bao.append(
            "%s: cột đầu của table.bang là %r — không phải 'Phân khu' hay "
            "'Loại căn', BỎ QUA bảng giá." % (ten, khop.group(2)))
        return html, False

    nhom = {}
    thieu = 0
    for c in cac_can:
        ten_nhom = lay_nhom(c)
        if not ten_nhom:
            # Căn không suy ra được nhóm (mã tòa lạ, hoặc cột Loại bỏ trống)
            # thì không dựng nổi một dòng có nghĩa — bỏ khỏi bảng và đếm lại
            # để báo, chứ không tạo dòng tên rỗng.
            thieu += 1
            continue
        muc = nhom.setdefault(ten_nhom, [])
        g = so_tien(c.get("Giá thuê"))
        muc.append(g)
    if thieu:
        canh_bao.append(
            "%s: %d căn không suy ra được %s — không đưa vào bảng giá."
            % (ten, thieu, khop.group(2)))

    dong = []
    for ten_nhom, cac_gia in sorted(nhom.items(),
                                    key=lambda x: (-len(x[1]), x[0])):
        gia = [g for g in cac_gia if g > 0]
        dong.append("<tr><td>%s</td><td>%d</td><td>%s</td></tr>" % (
            esc(ten_nhom), len(cac_gia),
            esc(khoang_gia(min(gia), max(gia)) if gia else "Liên hệ")))

    than_moi = "".join(dong)
    if than_moi == khop.group(4):
        return html, False
    return (html[:khop.start()] + khop.group(1) + khop.group(2)
            + khop.group(3) + than_moi + khop.group(5)
            + html[khop.end():]), True


def xu_ly_mot_trang(duong, du_lieu, map_anh, hom_nay, ngay_chu, chi_thu,
                    canh_bao):
    """Trả về một dòng cho bảng nghiệm thu, hoặc None nếu trang bị bỏ qua."""
    ten = os.path.relpath(duong, GOC)
    with open(duong, encoding="utf-8") as f:
        html = f.read()

    bl = doc_bo_loc(html)
    if bl is None:
        canh_bao.append("%s: #bo-loc-trang không parse được — BỎ QUA cả trang." % ten)
        return None

    cac_can = ds_can_len_luoi(du_lieu, bl, map_anh)
    the_truoc = dem_the(html)

    # Lớp bảo vệ của dong-bo-can.js (dòng 587): lọc ra 0 căn mà trang đang có
    # thẻ thì gần như chắc chắn là lỗi dữ liệu, không phải hết căn thật.
    if not cac_can and the_truoc > 0:
        canh_bao.append(
            "%s: lọc ra 0 căn trong khi trang đang có %d thẻ — GIỮ NGUYÊN "
            "trang, không ghi đè." % (ten, the_truoc))
        return {"ten": ten, "so_can": 0, "gia": "—",
                "truoc": the_truoc, "sau": the_truoc, "bo_qua": True}

    tk = thong_ke_trang(cac_can)
    goc = html

    html = RE_DANG_HIEN.sub("", html, count=1)
    html = RE_CHU_THICH_NGAY.sub(
        lambda m: "%s %s" % (m.group(1), ngay_chu), html, count=1)
    html = RE_CHAN_NGAY.sub(
        lambda m: "%s%s%s" % (m.group(1), ngay_chu, m.group(2)), html, count=1)
    html, _ = ghi_de_tt(html, tk, ngay_chu, ten, canh_bao)
    html, _ = ghi_de_sl(html, tk, ten, canh_bao)
    html, _ = ghi_de_h2(html, tk["so_can"], ten, canh_bao)
    html, _ = ghi_de_bang(html, cac_can, ten, canh_bao)
    html, _ = ghi_de_luoi(
        html, [dung_the(c, map_anh, hom_nay) for c in cac_can], ten, canh_bao)

    if html != goc and not chi_thu:
        # newline="" để nội dung ghi ra đúng từng ký tự, không bị đổi kiểu
        # xuống dòng (giống sinh-trang-toa.py).
        with open(duong, "w", encoding="utf-8", newline="") as f:
            f.write(html)

    return {
        "ten": ten,
        "so_can": tk["so_can"],
        "gia": dinh_dang_gia(tk["gia_min"]) if tk["gia_min"] else "—",
        "truoc": the_truoc,
        "sau": dem_the(html),
        "bo_qua": False,
    }


def tim_trang_danh_muc():
    """Quét repo tìm file HTML có khai #bo-loc-trang. Không viết cứng danh
    sách — thêm trang danh mục mới là script tự nhận."""
    ra = []
    for thu_muc, cac_thu_muc, cac_file in os.walk(GOC):
        cac_thu_muc[:] = [d for d in cac_thu_muc
                          if d not in BO_QUA_THU_MUC and not d.startswith(".")]
        for ten in cac_file:
            if not ten.endswith(".html"):
                continue
            duong = os.path.join(thu_muc, ten)
            with open(duong, encoding="utf-8") as f:
                if 'id="bo-loc-trang"' in f.read():
                    ra.append(duong)
    return sorted(ra)


def main():
    bo_phan_tich = argparse.ArgumentParser(
        description="Dựng lại thân động của các trang danh mục từ data.json.")
    bo_phan_tich.add_argument("--thu", action="store_true",
                              help="chỉ in bảng nghiệm thu, không ghi file")
    tham_so = bo_phan_tich.parse_args()

    with open(DUONG_DATA, encoding="utf-8") as f:
        du_lieu = json.load(f)

    # data.json rỗng gần như luôn là lỗi đẩy dữ liệu chứ không phải hết căn.
    # Thoát mã 0 để không đánh đỏ cả workflow vì một lần Apps Script lỗi.
    if not isinstance(du_lieu, list) or not du_lieu:
        print("CẢNH BÁO: data.json rỗng hoặc không phải mảng — "
              "GIỮ NGUYÊN mọi trang, không ghi gì.")
        return 0
    print("data.json: %d dòng." % len(du_lieu))

    map_anh = doc_map_anh()
    print("anh-map.json: %d ảnh có file trên đĩa." % len(map_anh))

    hom_nay = ngay_hom_nay()
    ngay_chu = hom_nay.strftime("%d/%m/%Y")
    cac_trang = tim_trang_danh_muc()
    print("Quét thấy %d trang danh mục.\n" % len(cac_trang))

    canh_bao = []
    bang = []
    for duong in cac_trang:
        dong = xu_ly_mot_trang(duong, du_lieu, map_anh, hom_nay, ngay_chu,
                               tham_so.thu, canh_bao)
        if dong:
            bang.append(dong)

    rong = max([len(d["ten"]) for d in bang] + [5])
    print("%-*s | %6s | %13s | %9s | %8s" % (
        rong, "trang", "số căn", "giá thấp nhất", "thẻ trước", "thẻ sau"))
    print("-" * (rong + 50))
    for d in bang:
        print("%-*s | %6d | %13s | %9d | %8d%s" % (
            rong, d["ten"], d["so_can"], d["gia"], d["truoc"], d["sau"],
            "   (bỏ qua)" if d["bo_qua"] else ""))

    tong = sum(d["sau"] for d in bang if not d["bo_qua"])
    print("\nTổng %d thẻ căn trên %d trang.%s" % (
        tong, len(bang), "  (--thu: chưa ghi file nào)" if tham_so.thu else ""))

    if canh_bao:
        print("\n%d cảnh báo:" % len(canh_bao))
        for c in canh_bao:
            print("  - " + c)
    else:
        print("\nKhông có cảnh báo nào.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

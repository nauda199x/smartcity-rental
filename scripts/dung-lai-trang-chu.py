#!/usr/bin/env python3
"""Dựng lại khối tĩnh 16 căn trên trang chủ (index.html) từ data.json.

VÌ SAO CẦN SCRIPT NÀY
---------------------
Toàn bộ danh sách căn hộ trên trang chủ được vẽ bằng JavaScript
(renderCards() đọc data.json qua fetch). HTML thô trả về cho crawler không
chạy JS — trong đó có toàn bộ crawler của các công cụ AI (GPTBot, ClaudeBot,
PerplexityBot) — chỉ thấy khối "Đang tải dữ liệu...". Script này chèn sẵn 16
căn thật vào giữa hai mốc HTML-DANG-KHOI-TAO-BAT-DAU/KET-THUC trong
#listingGrid, đồng thời điền số thật vào ba ô thống kê (#totalCount,
#readyCount, #phanKhuCount) và dòng #resultCount.

renderCards()/render() trong index.html vẫn gán lại grid.innerHTML và nội
dung ba ô thống kê ngay khi data.json tải xong ở trình duyệt — khối tĩnh chỉ
tồn tại trong HTML thô, người dùng thật không nhìn thấy nó. Script này
KHÔNG đụng tới bất kỳ JavaScript nào trong index.html.

TÁI DÙNG — KHÔNG VIẾT LẠI LOGIC
--------------------------------
Toàn bộ hàm dựng thẻ căn, lọc căn hợp lệ, khoi_khong_anh() (ruột thẻ chưa có
ảnh) và định dạng số liệu ĐỀU nạp lại từ scripts/dung-lai-trang-danh-muc.py
qua importlib (chính script đó cũng nạp lại scripts/sinh-trang-toa.py theo
đúng cách này) — không chép, không viết bản thứ hai. Cụ thể:
    dung_the()        — dựng nguyên article.the, tự gọi khoi_khong_anh()
                         bên trong khi căn không có ảnh, không cần gọi tay.
    la_can_hop_le()    — "Hiển thị trên Web" == có/yes/true.
    thong_ke_trang()   — đếm so_can và so_phan_khu cho một danh sách căn.
    anh_bia(), doc_map_anh(), ngay_hom_nay(), so_tien(), dinh_dang_gia()...

QUYẾT ĐỊNH NGOÀI SPEC (ghi trong PR)
-------------------------------------
readyCount (B-5) cần "đúng logic đang có trong index.html" cho việc một căn
đã ở được ngay hay chưa — đó là hàm JS sanSangONgay(), không gọi được từ
Python. Bản mirror gần nhất đã có sẵn trong repo là nhan_tinh_trang() của
sinh-trang-toa.py (nạp lại qua DLTDM.STT): cùng đọc cột "Ngày vào ở", cùng
coi trống/"luôn"/"ở ngay" và ngày đã qua là sẵn sàng ngay — đúng ba nhánh của
sanSangONgay(). Hàm này đã là nguồn duy nhất dùng để in nhãn "Vào ngay" trên
mọi thẻ căn tĩnh khác trong repo (sinh-trang-toa.py, dung-lai-trang-danh-muc.py
qua dung_the()), nên dùng lại ở đây thay vì chép luật ra một lần nữa.

Chạy:  python3 scripts/dung-lai-trang-chu.py [--thu]
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
DUONG_INDEX = os.path.join(GOC, "index.html")
DUONG_BANG_GIA = os.path.join(GOC, "bang-gia-thue-vinhomes-smart-city.html")

SO_CARD = 16                # khớp SO_CARD_DESKTOP trong index.html
TRAN_TOA_BAT_DAU = 3         # tối đa mỗi tòa lúc đầu, để trải trên nhiều phân khu
TRAN_TOA_NOI_RONG = 5        # nới trần nếu vòng đầu chưa đủ 16


def nap_dung_lai_trang_danh_muc():
    """Nạp scripts/dung-lai-trang-danh-muc.py để dùng lại nguyên bộ hàm dựng
    thẻ căn và lọc dữ liệu — cùng thủ pháp importlib mà chính file đó dùng để
    nạp sinh-trang-toa.py (tên file có dấu gạch ngang, không import thẳng
    được)."""
    duong = os.path.join(THU_MUC_SCRIPT, "dung-lai-trang-danh-muc.py")
    dac_ta = importlib.util.spec_from_file_location(
        "dung_lai_trang_danh_muc", duong)
    mo_dun = importlib.util.module_from_spec(dac_ta)
    cu = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        dac_ta.loader.exec_module(mo_dun)
    finally:
        sys.dont_write_bytecode = cu
    return mo_dun


DLTDM = nap_dung_lai_trang_danh_muc()

# Dùng lại nguyên văn, không định nghĩa lại.
chuan = DLTDM.chuan
la_can_hop_le = DLTDM.la_can_hop_le
anh_bia = DLTDM.anh_bia
dung_the = DLTDM.dung_the                # dựng article.the, tự lo cả ca không ảnh
thong_ke_trang = DLTDM.thong_ke_trang
doc_map_anh = DLTDM.doc_map_anh
ngay_hom_nay = DLTDM.ngay_hom_nay
so_tien = DLTDM.so_tien
chuan_ma_toa = DLTDM.STT.chuan_ma_toa    # sinh-trang-toa.py, nạp lại qua STT
nhan_tinh_trang = DLTDM.STT.nhan_tinh_trang
phan_khu_tu_toa = DLTDM.phan_khu_tu_toa
dinh_dang_gia = DLTDM.dinh_dang_gia

# Thứ tự cố định để bảng thị trường không nhảy vị trí giữa các lần cập nhật.
THI_TRUONG_LOAI = [
    ("studio", "Studio", "/studio/"),
    ("1 ngủ", "1 phòng ngủ", "/1pn/"),
    ("1 ngủ +", "1 phòng ngủ +", "/1pn-plus/"),
    ("2 ngủ", "2 phòng ngủ", "/2pn/"),
    ("2 ngủ +", "2 phòng ngủ +", "/2pn-plus/"),
    ("3 ngủ", "3 phòng ngủ", "/3pn/"),
]
THI_TRUONG_KHU = [
    ("Sapphire", "Sapphire", "/sapphire/"),
    ("Masteri", "Masteri West Heights", "/masteri/"),
    ("Lumiere", "Lumière Evergreen", "/lumiere/"),
    ("Miami", "The Miami", "/miami/"),
    ("Sakura", "The Sakura", "/sakura/"),
    ("Imperia", "Imperia Smart City", "/imperia/"),
    ("Canopy", "The Canopy", "/canopy/"),
    ("Tonkin", "The Tonkin", "/tonkin/"),
]


# ===========================================================================
# Chọn 16 căn (HUONG-DAN mục B-2)
# ===========================================================================

def chon_theo_tran(ung_vien, tran, con_thieu, da_chon_ma):
    """Duyệt ung_vien (đã sắp giá tăng dần), nhận vào tối đa `tran` căn mỗi
    tòa, dừng khi đủ `con_thieu` căn hoặc hết ung_vien."""
    ket_qua = []
    dem_toa = {}
    for r in ung_vien:
        ma = chuan(r.get("Mã nội bộ"))
        if not ma or ma in da_chon_ma:
            continue
        toa = chuan_ma_toa(r.get("Tòa", ""))
        if dem_toa.get(toa, 0) >= tran:
            continue
        ket_qua.append(r)
        dem_toa[toa] = dem_toa.get(toa, 0) + 1
        da_chon_ma.add(ma)
        if len(ket_qua) >= con_thieu:
            break
    return ket_qua


def chon_16_can(cac_can_hien_thi):
    """Trả về (danh sách tối đa SO_CARD căn, có đủ SO_CARD hay không)."""
    co_anh = [r for r in cac_can_hien_thi if anh_bia(r, {})]
    khong_anh = [r for r in cac_can_hien_thi if not anh_bia(r, {})]
    co_anh.sort(key=lambda r: so_tien(r.get("Giá thuê")))
    khong_anh.sort(key=lambda r: so_tien(r.get("Giá thuê")))

    da_chon_ma = set()
    ket_qua = chon_theo_tran(co_anh, TRAN_TOA_BAT_DAU, SO_CARD, da_chon_ma)

    if len(ket_qua) < SO_CARD:
        # Nới trần rồi quét lại TOÀN BỘ nhóm có ảnh từ đầu (không chỉ phần
        # còn lại) — đúng "quét lại" mà HUONG-DAN mục B-2 bước 5 mô tả.
        da_chon_ma = set()
        ket_qua = chon_theo_tran(co_anh, TRAN_TOA_NOI_RONG, SO_CARD, da_chon_ma)

    if len(ket_qua) < SO_CARD:
        # Vẫn chưa đủ: lấy tiếp căn không có ảnh, giữ nguyên trần đã nới.
        con_thieu = SO_CARD - len(ket_qua)
        them = chon_theo_tran(khong_anh, TRAN_TOA_NOI_RONG, con_thieu, da_chon_ma)
        ket_qua = ket_qua + them

    return ket_qua[:SO_CARD], len(ket_qua) >= SO_CARD


# ===========================================================================
# Ghi đè vào index.html
# ===========================================================================

RE_KHOI_TINH = re.compile(
    r'(<!-- KHOI-TINH-BAT-DAU.*?-->)(.*?)(<!-- KHOI-TINH-KET-THUC -->)',
    re.S)
RE_TOTAL = re.compile(r'(<strong id="totalCount">)([^<]*)(</strong>)')
RE_READY = re.compile(r'(<strong id="readyCount">)([^<]*)(</strong>)')
RE_ZONE = re.compile(r'(<strong id="phanKhuCount">)([^<]*)(</strong>)')
RE_RESULT = re.compile(
    r'(<div class="result-count" id="resultCount" data-i18n="l\.loading">)'
    r'(.*?)(</div>)', re.S)
RE_THI_TRUONG_LOAI = re.compile(
    r'(<!-- THI-TRUONG-LOAI:BAT-DAU -->)(.*?)(<!-- THI-TRUONG-LOAI:KET-THUC -->)',
    re.S)
RE_THI_TRUONG_KHU = re.compile(
    r'(<!-- THI-TRUONG-KHU:BAT-DAU -->)(.*?)(<!-- THI-TRUONG-KHU:KET-THUC -->)',
    re.S)

# Các mốc tĩnh trên trang bảng giá. JS vẫn cập nhật lại khi khách mở trang,
# còn các mốc này giúp crawler không chạy JavaScript vẫn nhìn thấy số thật.
RE_BANG_GIA_LOAI = re.compile(
    r'(<!-- BANG-GIA-TOM-TAT-LOAI:BAT-DAU -->)(.*?)(<!-- BANG-GIA-TOM-TAT-LOAI:KET-THUC -->)',
    re.S)
RE_BANG_GIA_KHU = re.compile(
    r'(<!-- BANG-GIA-TOM-TAT-KHU:BAT-DAU -->)(.*?)(<!-- BANG-GIA-TOM-TAT-KHU:KET-THUC -->)',
    re.S)
RE_BANG_GIA_CHI_TIET = re.compile(
    r'(<!-- BANG-GIA-CHI-TIET:BAT-DAU -->)(.*?)(<!-- BANG-GIA-CHI-TIET:KET-THUC -->)',
    re.S)
RE_BANG_GIA_TOTAL = re.compile(r'(<b id="bangGiaTotal">)([^<]*)(</b>)')
RE_BANG_GIA_ZONE_COUNT = re.compile(r'(<b id="bangGiaZoneCount">)([^<]*)(</b>)')
RE_BANG_GIA_TYPE_COUNT = re.compile(r'(<b id="bangGiaTypeCount">)([^<]*)(</b>)')


def ghi_de_khoi_tinh(html, cac_the):
    khop = RE_KHOI_TINH.search(html)
    if not khop:
        return html, False
    moi = "\n      " + "\n".join(cac_the) + "\n      "
    if moi == khop.group(2):
        return html, False
    return (html[:khop.start()] + khop.group(1) + moi + khop.group(3)
            + html[khop.end():]), True


def ghi_de_o(html, mau, gia_tri):
    khop = mau.search(html)
    if not khop:
        return html, False
    if khop.group(2) == gia_tri:
        return html, False
    return (html[:khop.start()] + khop.group(1) + gia_tri + khop.group(3)
            + html[khop.end():]), True


def ghi_de_dong_thi_truong(html, mau, cac_dong):
    """Ghi phần giữa hai marker, giữ nguyên marker để lần sau cập nhật idempotent."""
    khop = mau.search(html)
    if not khop:
        return html, False
    moi = "\n                " + "\n                ".join(cac_dong) + "\n                "
    if moi == khop.group(2):
        return html, False
    return (html[:khop.start()] + khop.group(1) + moi + khop.group(3)
            + html[khop.end():]), True


def gia_trieu_ngan(v):
    """8_500_000 -> '8,5', dùng lại formatter chung để không lệch quy tắc."""
    return dinh_dang_gia(v).replace(" triệu", "").strip()


def dong_thi_truong(cac_can):
    """Trả hai danh sách <tr>: theo loại căn và theo phân khu."""
    theo_loai = {}
    theo_khu = {}
    for r in cac_can:
        gia = so_tien(r.get("Giá thuê"))
        if gia <= 0:
            continue
        loai = chuan(r.get("Loại")).lower()
        khu = phan_khu_tu_toa(r.get("Tòa", ""))
        if loai:
            theo_loai.setdefault(loai, []).append(gia)
        if khu:
            theo_khu.setdefault(khu, []).append(gia)

    def dung_dong(label, href, ds_gia):
        if not ds_gia:
            return ""
        lo = min(ds_gia)
        hi = max(ds_gia)
        khoang = "%s–%s triệu/tháng" % (gia_trieu_ngan(lo), gia_trieu_ngan(hi))
        return ('<tr><th scope="row"><a href="%s">%s</a></th>'
                '<td><strong>%d</strong> căn</td><td>%s</td></tr>') % (
                    href, label, len(ds_gia), khoang)

    dong_loai = [
        dung_dong(label, href, theo_loai.get(key, []))
        for key, label, href in THI_TRUONG_LOAI
    ]
    dong_khu = [
        dung_dong(label, href, theo_khu.get(key, []))
        for key, label, href in THI_TRUONG_KHU
    ]
    return [x for x in dong_loai if x], [x for x in dong_khu if x]


def trung_vi_gia(ds_gia):
    """Trung vị của một danh sách giá; đầu vào không cần sắp xếp trước."""
    ds = sorted(ds_gia)
    n = len(ds)
    if not n:
        return 0
    giua = n // 2
    return ds[giua] if n % 2 else (ds[giua - 1] + ds[giua]) / 2


def o_chi_tiet_bang_gia(ds_gia):
    """HTML một ô Phân khu × Loại căn. Dưới 3 mẫu thì không suy đoán giá."""
    if len(ds_gia) < 3:
        return '<span class="bang-gia-thieu">Chưa đủ dữ liệu</span>'
    ds = sorted(ds_gia)
    return (
        '<span class="bang-gia-khoang">%s–%s tr</span>'
        '<small>Trung vị %s · n=%d</small>'
    ) % (
        gia_trieu_ngan(ds[0]),
        gia_trieu_ngan(ds[-1]),
        gia_trieu_ngan(trung_vi_gia(ds)),
        len(ds),
    )


def dong_chi_tiet_bang_gia(cac_can):
    """Dựng các hàng của ma trận 8 phân khu × 6 loại căn trên trang bảng giá."""
    theo = {}
    tong_khu = {}
    for r in cac_can:
        gia = so_tien(r.get("Giá thuê"))
        if gia <= 0:
            continue
        loai = chuan(r.get("Loại")).lower()
        khu = phan_khu_tu_toa(r.get("Tòa", ""))
        if not loai or not khu:
            continue
        theo.setdefault((khu, loai), []).append(gia)
        tong_khu[khu] = tong_khu.get(khu, 0) + 1

    cac_dong = []
    for khu_key, khu_label, khu_href in THI_TRUONG_KHU:
        if not tong_khu.get(khu_key):
            continue
        o = []
        for loai_key, _, _ in THI_TRUONG_LOAI:
            o.append("<td>%s</td>" % o_chi_tiet_bang_gia(
                theo.get((khu_key, loai_key), [])))
        cac_dong.append(
            '<tr><th scope="row"><a href="%s">%s</a><small>%d căn</small></th>%s</tr>'
            % (khu_href, khu_label, tong_khu[khu_key], "".join(o))
        )
    return cac_dong


def main():
    bo_phan_tich = argparse.ArgumentParser(
        description="Dựng lại khối tĩnh 16 căn trên trang chủ từ data.json.")
    bo_phan_tich.add_argument("--thu", action="store_true",
                              help="chỉ in bảng nghiệm thu, không ghi file")
    tham_so = bo_phan_tich.parse_args()

    with open(DUONG_DATA, encoding="utf-8") as f:
        du_lieu = json.load(f)

    if not isinstance(du_lieu, list) or not du_lieu:
        print("CẢNH BÁO: data.json rỗng hoặc không phải mảng — "
              "GIỮ NGUYÊN trang chủ, không ghi gì.")
        return 0
    print("data.json: %d dòng." % len(du_lieu))

    if not os.path.exists(DUONG_INDEX):
        print("CẢNH BÁO: không tìm thấy %s — thoát." % DUONG_INDEX)
        return 0
    with open(DUONG_INDEX, encoding="utf-8") as f:
        html = f.read()

    if not RE_KHOI_TINH.search(html):
        print("CẢNH BÁO: không tìm thấy mốc KHOI-TINH-BAT-DAU/KHOI-TINH-KET-THUC "
              "trong index.html — GIỮ NGUYÊN trang, không ghi gì.")
        return 0

    map_anh = doc_map_anh()
    print("anh-map.json: %d ảnh có file trên đĩa." % len(map_anh))
    hom_nay = ngay_hom_nay()

    # Tập căn đang hiển thị + có tòa/loại/giá — đúng ba điều kiện mà
    # publicApartments của index.html dùng (item.show && item.tower &&
    # item.type && item.price), để #totalCount/#phanKhuCount/#resultCount in
    # ra HTML thô khớp con số mà JS sẽ tính lại khi tải xong.
    cac_can_cong_khai = [
        r for r in du_lieu
        if la_can_hop_le(r) and chuan(r.get("Tòa")) and chuan(r.get("Loại"))
        and so_tien(r.get("Giá thuê")) > 0
    ]
    tk = thong_ke_trang(cac_can_cong_khai)
    so_can_ready = sum(
        1 for r in cac_can_cong_khai
        if nhan_tinh_trang(r, hom_nay) == "Vào ngay")

    print("Căn đang hiển thị (đủ tòa/loại/giá): %d" % tk["so_can"])
    print("Ở ngay: %d" % so_can_ready)
    print("Phân khu đang có căn: %d" % tk["so_phan_khu"])

    cac_can_16, du = chon_16_can(cac_can_cong_khai)
    if not du:
        print("CẢNH BÁO: chỉ chọn được %d/%d căn cho khối tĩnh trang chủ."
              % (len(cac_can_16), SO_CARD))
    print("Đã chọn %d căn cho khối tĩnh, trải trên %d tòa." % (
        len(cac_can_16),
        len(set(chuan_ma_toa(c.get("Tòa", "")) for c in cac_can_16))))

    cac_the = [dung_the(c, map_anh, hom_nay) for c in cac_can_16]
    dong_loai, dong_khu = dong_thi_truong(cac_can_cong_khai)
    print("Bảng thị trường: %d loại căn, %d phân khu." % (
        len(dong_loai), len(dong_khu)))

    goc = html
    html, _ = ghi_de_khoi_tinh(html, cac_the)
    html, _ = ghi_de_dong_thi_truong(html, RE_THI_TRUONG_LOAI, dong_loai)
    html, _ = ghi_de_dong_thi_truong(html, RE_THI_TRUONG_KHU, dong_khu)
    html, _ = ghi_de_o(html, RE_TOTAL, str(tk["so_can"]))
    html, _ = ghi_de_o(html, RE_READY, str(so_can_ready))
    html, _ = ghi_de_o(html, RE_ZONE, str(tk["so_phan_khu"]))
    html, _ = ghi_de_o(
        html, RE_RESULT,
        "<strong>%d</strong> căn hộ đang trống phù hợp" % tk["so_can"])

    if html != goc and not tham_so.thu:
        with open(DUONG_INDEX, "w", encoding="utf-8", newline="") as f:
            f.write(html)
        print("Đã ghi index.html.")
    elif tham_so.thu:
        print("(--thu) Không ghi index.html.")
    else:
        print("index.html không có gì thay đổi.")

    # Trang bảng giá dùng cùng dữ liệu với khối thị trường trên trang chủ,
    # nhưng có thêm ma trận Phân khu × Loại căn. Dựng sẵn HTML thô để crawler
    # đọc được ngay; JavaScript của trang vẫn đọc data.json lại khi người dùng mở.
    if os.path.exists(DUONG_BANG_GIA):
        with open(DUONG_BANG_GIA, encoding="utf-8") as f:
            html_bg = f.read()
        goc_bg = html_bg
        dong_chi_tiet = dong_chi_tiet_bang_gia(cac_can_cong_khai)

        html_bg, _ = ghi_de_dong_thi_truong(
            html_bg, RE_BANG_GIA_LOAI, dong_loai)
        html_bg, _ = ghi_de_dong_thi_truong(
            html_bg, RE_BANG_GIA_KHU, dong_khu)
        html_bg, _ = ghi_de_dong_thi_truong(
            html_bg, RE_BANG_GIA_CHI_TIET, dong_chi_tiet)
        html_bg, _ = ghi_de_o(
            html_bg, RE_BANG_GIA_TOTAL, str(tk["so_can"]))
        html_bg, _ = ghi_de_o(
            html_bg, RE_BANG_GIA_ZONE_COUNT, str(len(dong_khu)))
        html_bg, _ = ghi_de_o(
            html_bg, RE_BANG_GIA_TYPE_COUNT, str(len(dong_loai)))

        if html_bg != goc_bg and not tham_so.thu:
            with open(DUONG_BANG_GIA, "w", encoding="utf-8", newline="") as f:
                f.write(html_bg)
            print("Đã ghi bang-gia-thue-vinhomes-smart-city.html.")
        elif tham_so.thu:
            print("(--thu) Không ghi trang bảng giá.")
        else:
            print("Trang bảng giá không có gì thay đổi.")
    else:
        print("CẢNH BÁO: không tìm thấy trang bảng giá — bỏ qua.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

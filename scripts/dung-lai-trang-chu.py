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
    co_anh = [r for r in cac_can_hien_thi if chuan(r.get("Ảnh đại diện"))]
    khong_anh = [r for r in cac_can_hien_thi if not chuan(r.get("Ảnh đại diện"))]
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

    goc = html
    html, _ = ghi_de_khoi_tinh(html, cac_the)
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
        print("(--thu) Không ghi file.")
    else:
        print("Không có gì thay đổi.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

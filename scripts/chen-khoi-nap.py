#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""chen-khoi-nap.py — Chèn khối NAP vào footer của các TRANG TĨNH.

VÌ SAO CÓ SCRIPT NÀY
--------------------
Repo không có footer partial: header/footer được chép tay vào từng file, theo
hai bộ giao diện khác nhau (.chan/.khung và .site-footer/.shell). 63 trang do
sinh-trang-can.py / sinh-trang-toa.py sinh lại ba lần mỗi ngày — hai script đó
đã tự chèn NAP từ template, KHÔNG đụng tới ở đây. Còn lại là các trang tĩnh
viết tay; sửa tay từng file là gần như chắc chắn sót, mà sót một trang thì mất
tính nhất quán — vốn là toàn bộ giá trị của việc này.

NGUỒN DUY NHẤT của khối NAP: scripts/khoi-nap.tpl (dùng chung với 2 script sinh
trang). Không chép nội dung NAP vào script này.

CÁCH CHÈN
---------
1. Trang nào còn dòng nhận diện cũ ("… môi giới cá nhân … Hotline & Zalo:
   0977923284") thì THAY dòng đó bằng khối NAP. Giữ cả hai sẽ có hai cách viết
   số điện thoại trên cùng một trang — đúng kiểu lệch NAP cần dẹp.
2. Không có dòng đó thì chèn khối NAP ngay sau thẻ <footer …> mở.

AN TOÀN
-------
- Idempotent: trang đã có data-site-identity="true" thì bỏ qua.
- Chỉ đụng danh sách trang tĩnh tính được ở dưới, không đụng trang sinh tự động.
- In rõ trang đã sửa, trang bỏ qua và trang KHÔNG tìm thấy mốc neo.
- --thu để xem trước, không ghi file nào.
"""

import argparse
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUONG_NAP = os.path.join(GOC, "scripts", "khoi-nap.tpl")

# Nhận diện trang sinh tự động bằng ĐÚNG câu cảnh báo mà hai script sinh trang
# ghi vào đầu mỗi file chúng tạo ra.
#
# KHÔNG dò theo tên script ("sinh-trang-toa.py"): index.html có một dòng chú
# thích NHẮC TỚI tên script đó khi nói về các trang theo tòa, nên dò kiểu ấy sẽ
# loại nhầm chính trang chủ — trang cần khối NAP nhất.
DAU_HIEU_SINH_TU_DONG = ("Sửa tay ở đây sẽ mất trong lần chạy sau",)

MOC_DA_CO = 'data-site-identity="true"'

# Trang cố tình KHÔNG chèn NAP. Bỏ qua có chủ đích thì không tính là lỗi, nhưng
# một trang lạ không có footer thì vẫn phải báo đỏ — nên liệt kê tường minh.
BO_QUA_CO_CHU_DICH = {
    # Trang chuyển hướng: noindex + meta refresh 0 giây, không có footer.
    # Chèn NAP vào đây không ai đọc được, Google cũng không đọc vì noindex.
    "bang-gia-thue-smart-city-thang-7-2026.html":
        "trang chuyển hướng noindex, không có footer",
}

# Dòng nhận diện cũ trong footer kiểu .chan — khớp cả bản xuống dòng khác nhau.
RE_DONG_CU = re.compile(
    r'[ \t]*<p><strong>Cho thuê chung cư Smart City</strong>[^<]*môi giới cá nhân.*?</p>\n',
    re.S)

# Biến thể ở 404.html: hotline và câu miễn trừ tách thành hai <span> rời. Cùng
# lý do như trên — số điện thoại ở đây viết liền "0977923284", khối NAP viết
# "0977 923 284", để cả hai là một trang có hai cách viết NAP.
RE_SPAN_CU = re.compile(
    r'[ \t]*<span class="hotline">.*?</span>\n'
    r'[ \t]*<span class="mien-tru">.*?</span>\n',
    re.S)

RE_MO_FOOTER = re.compile(r'<footer\b[^>]*>')

# Khối NAP đã chèn từ lần chạy trước. Bắt được cả bản cũ (chưa có mốc bao ngoài)
# lẫn bản mới, để mỗi lần khoi-nap.tpl đổi là chạy lại một phát đồng bộ hết —
# script này vừa là chèn lần đầu, vừa là đồng bộ về sau.
# Trong .site-nap chỉ có các thẻ <p>, không có <div> lồng, nên </div> đầu tiên
# sau thẻ mở chính là thẻ đóng của khối.
RE_KHOI_DA_CO = re.compile(
    r'[ \t]*<!-- ══ KHỐI NAP.*?<div class="shell site-nap".*?</div>\n'
    r'(?:[ \t]*<!-- KHOI-NAP:KET-THUC -->\n)?',
    re.S)


def doc_khoi_nap():
    with open(DUONG_NAP, encoding="utf-8") as f:
        return f.read().rstrip("\n")


def la_trang_sinh_tu_dong(noi_dung):
    return any(d in noi_dung for d in DAU_HIEU_SINH_TU_DONG)


def liet_ke_trang_tinh():
    """Mọi .html trong repo trừ trang sinh tự động và trừ thư mục .git."""
    ra = []
    for thu_muc, cac_tm_con, cac_file in os.walk(GOC):
        cac_tm_con[:] = [t for t in cac_tm_con if t not in (".git", "node_modules")]
        for ten in cac_file:
            if not ten.endswith(".html"):
                continue
            duong = os.path.join(thu_muc, ten)
            with open(duong, encoding="utf-8") as f:
                noi_dung = f.read()
            if la_trang_sinh_tu_dong(noi_dung):
                continue
            ra.append((os.path.relpath(duong, GOC), noi_dung))
    return sorted(ra)


def chen(noi_dung, khoi_nap):
    """Trả về (nội dung mới, cách chèn) hoặc (None, lý do) nếu không chèn được."""
    if MOC_DA_CO in noi_dung:
        moi, so_lan = RE_KHOI_DA_CO.subn(lambda _: khoi_nap + "\n", noi_dung, count=1)
        if not so_lan:
            return None, "co-moc-nhung-khong-doc-duoc-khoi"
        if moi == noi_dung:
            return None, "khong-doi"
        return moi, "dong-bo-lai"

    moi, so_lan = RE_DONG_CU.subn(khoi_nap + "\n", noi_dung, count=1)
    if so_lan:
        return moi, "thay-dong-cu"

    moi, so_lan = RE_SPAN_CU.subn("", noi_dung, count=1)
    if so_lan:
        noi_dung = moi

    m = RE_MO_FOOTER.search(noi_dung)
    if not m:
        return None, "khong-co-footer"
    vi_tri = m.end()
    return noi_dung[:vi_tri] + "\n" + khoi_nap + noi_dung[vi_tri:], "chen-dau-footer"


def main():
    bo = argparse.ArgumentParser(description=__doc__)
    bo.add_argument("--thu", "--dry-run", action="store_true",
                    help="Chỉ xem trước, không ghi file nào")
    tham_so = bo.parse_args()

    khoi_nap = doc_khoi_nap()
    trang_tinh = liet_ke_trang_tinh()

    da_sua, bo_qua, khong_moc = [], [], []
    co_chu_dich = []
    for duong, noi_dung in trang_tinh:
        if duong in BO_QUA_CO_CHU_DICH:
            co_chu_dich.append((duong, BO_QUA_CO_CHU_DICH[duong]))
            continue
        moi, cach = chen(noi_dung, khoi_nap)
        if moi is None:
            (bo_qua if cach == "khong-doi" else khong_moc).append((duong, cach))
            continue
        da_sua.append((duong, cach))
        if not tham_so.thu:
            with open(os.path.join(GOC, duong), "w", encoding="utf-8") as f:
                f.write(moi)

    print("Trang tĩnh quét được : %d" % len(trang_tinh))
    print("Đã chèn NAP          : %d" % len(da_sua))
    print("Đã đúng, không đổi   : %d" % len(bo_qua))
    print("Bỏ qua có chủ đích   : %d" % len(co_chu_dich))
    print("KHÔNG tìm thấy mốc   : %d" % len(khong_moc))

    if da_sua:
        print("\n--- ĐÃ CHÈN ---")
        for duong, cach in da_sua:
            print("  [%s] %s" % (cach, duong))
    if bo_qua:
        print("\n--- ĐÃ ĐÚNG, KHÔNG ĐỔI ---")
        for duong, _ in bo_qua:
            print("  %s" % duong)
    if co_chu_dich:
        print("\n--- BỎ QUA CÓ CHỦ ĐÍCH ---")
        for duong, ly_do in co_chu_dich:
            print("  %s — %s" % (duong, ly_do))
    if khong_moc:
        print("\n--- KHÔNG TÌM THẤY MỐC NEO — xử lý riêng ---")
        for duong, cach in khong_moc:
            print("  [%s] %s" % (cach, duong))

    if tham_so.thu:
        print("\n(--thu) Không ghi file nào.")
    return 1 if khong_moc else 0


if __name__ == "__main__":
    sys.exit(main())

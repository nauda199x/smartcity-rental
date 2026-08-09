#!/usr/bin/env python3
"""Thay URL Google Drive trong thẻ <img> bằng đường dẫn WebP nằm trong repo.

tai-anh-can-ho.py đã tải ảnh về anh-can-ho/ và ghi anh-map.json, nhưng HTML
tĩnh vẫn trỏ thẳng sang drive.google.com — nơi Googlebot bị chặn nên không ảnh
nào được index. Script này là mắt xích cuối: đọc anh-map.json rồi sửa src của
các thẻ <img> sang đường dẫn nội bộ.

Chỉ thay khi ID vừa có trong map vừa có file WebP thật trên đĩa. ID nào chưa
tải được ảnh thì giữ nguyên URL Drive để trang không vỡ ảnh — chạy lại workflow
tai-anh-can-ho là lần sau sẽ thay được.

Chạy lần hai trên repo đã sửa phải cho 0 thay đổi.

Chạy:  python3 scripts/thay-anh-trong-html.py [--thu]
"""

import argparse
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_ANH = os.path.join(GOC, "anh-can-ho")
DUONG_MAP = os.path.join(THU_MUC_ANH, "anh-map.json")

# Thư mục không chứa HTML của trang, hoặc chứa bản nháp/thư viện không được
# đụng tới. 404.html do GitHub Pages phục vụ riêng, không có thẻ ảnh căn hộ.
THU_MUC_BO_QUA = {".git", "anh-can-ho", "_design:", "assets", "images",
                  "scripts", ".github"}
FILE_BO_QUA = {"404.html"}

# Bắt src của thẻ <img>. Dấu & trong HTML tĩnh phần lớn là thực thể &amp;,
# nhưng vẫn có chỗ viết & thuần nên phải nhận cả hai.
MAU_SRC = re.compile(
    r'(src\s*=\s*")'
    r'https://drive\.google\.com/thumbnail\?id=([A-Za-z0-9_-]+)(?:&amp;|&)sz=w1000'
    r'(")'
)
MAU_IMG = re.compile(r'<img\b[^>]*>', re.IGNORECASE)


def cac_file_html():
    """Duyệt repo, trả về đường dẫn tương đối của mọi file HTML trong phạm vi."""
    ket_qua = []
    for thu_muc, cac_con, cac_file in os.walk(GOC):
        # Cắt nhánh ngay tại đây để không phải duyệt vào trong cho tốn thời gian.
        cac_con[:] = [c for c in cac_con
                      if os.path.relpath(os.path.join(thu_muc, c), GOC)
                      not in THU_MUC_BO_QUA]
        for ten in cac_file:
            if ten.endswith(".html") and ten not in FILE_BO_QUA:
                ket_qua.append(
                    os.path.relpath(os.path.join(thu_muc, ten), GOC))
    return sorted(ket_qua)


def thay_trong_html(noi_dung, co_the_thay, bo_qua):
    """Thay src Drive trong từng thẻ <img>. Trả về (nội dung mới, số lượt thay).

    Chỉ đụng phần văn bản nằm trong thẻ <img>, nên URL Drive ở <a href>,
    <video src>, thuộc tính data-*, khối <script> hay bình luận HTML đều không
    bị ảnh hưởng."""
    dem = [0]

    def thay_mot_img(khop_img):
        the = khop_img.group(0)

        def thay_mot_src(khop):
            ma_drive = khop.group(2)
            duong_dan = co_the_thay.get(ma_drive)
            if not duong_dan:
                bo_qua.append(ma_drive)
                return khop.group(0)
            dem[0] += 1
            return khop.group(1) + duong_dan + khop.group(3)

        return MAU_SRC.sub(thay_mot_src, the)

    return MAU_IMG.sub(thay_mot_img, noi_dung), dem[0]


def main():
    bo_phan_tich = argparse.ArgumentParser()
    bo_phan_tich.add_argument("--thu", action="store_true",
                              help="chỉ in kết quả dự kiến, không ghi file")
    tham_so = bo_phan_tich.parse_args()

    if not os.path.exists(DUONG_MAP):
        print("Không tìm thấy %s — chạy tai-anh-can-ho.py trước." % DUONG_MAP)
        return 1

    with open(DUONG_MAP, encoding="utf-8") as f:
        anh_map = json.load(f)

    # Map có thể còn dòng của ảnh đã bị xoá khỏi đĩa. Thay bằng đường dẫn không
    # tồn tại thì trang vỡ ảnh, tệ hơn cả để nguyên URL Drive.
    co_the_thay = {}
    thieu_file = 0
    for ma_drive, duong_dan in anh_map.items():
        if os.path.exists(os.path.join(GOC, duong_dan.lstrip("/"))):
            co_the_thay[ma_drive] = duong_dan
        else:
            thieu_file += 1

    print("anh-map.json: %d ảnh, %d ảnh có file trên đĩa%s\n"
          % (len(anh_map), len(co_the_thay),
             ", %d dòng thiếu file" % thieu_file if thieu_file else ""))

    tong_thay = tong_bo_qua = 0
    bo_qua_tat_ca = []
    print("%-46s %8s %8s" % ("File", "Đã thay", "Bỏ qua"))
    print("-" * 64)
    for duong_dan in cac_file_html():
        with open(os.path.join(GOC, duong_dan), encoding="utf-8") as f:
            noi_dung = f.read()

        bo_qua = []
        moi, so_thay = thay_trong_html(noi_dung, co_the_thay, bo_qua)
        if not so_thay and not bo_qua:
            continue

        print("%-46s %8d %8d" % (duong_dan, so_thay, len(bo_qua)))
        tong_thay += so_thay
        tong_bo_qua += len(bo_qua)
        bo_qua_tat_ca.extend(bo_qua)

        if so_thay and not tham_so.thu:
            # newline="" để không đụng vào ký tự xuống dòng sẵn có của file.
            with open(os.path.join(GOC, duong_dan), "w",
                      encoding="utf-8", newline="") as f:
                f.write(moi)

    print("-" * 64)
    print("%-46s %8d %8d" % ("TỔNG", tong_thay, tong_bo_qua))

    if bo_qua_tat_ca:
        rieng = sorted(set(bo_qua_tat_ca))
        print("\n%d lượt bỏ qua, thuộc %d Drive ID chưa có ảnh trong repo."
              % (tong_bo_qua, len(rieng)))
        print("Chạy workflow tai-anh-can-ho để tải về, sau đó chạy lại script này.")
        for ma_drive in rieng[:20]:
            print("  - %s" % ma_drive)
        if len(rieng) > 20:
            print("  ... còn %d ID nữa" % (len(rieng) - 20))

    if tham_so.thu:
        print("\n(--thu) Không ghi file nào.")
    elif tong_thay:
        print("\nĐã sửa xong. Chạy lại script này phải cho 0 lượt thay.")
    else:
        print("\nKhông có gì để thay.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

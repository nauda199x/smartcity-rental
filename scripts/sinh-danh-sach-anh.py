#!/usr/bin/env python3
"""Sinh scripts/danh-sach-anh.json từ data.json ở gốc repo.

Trước đây danh-sach-anh.json là file tĩnh, không script nào sinh ra nên mỗi lần
data.json có căn mới là danh sách lại lỗi thời, kéo theo tai-anh-can-ho.py bỏ
sót ảnh. Script này dựng lại danh sách đó từ nguồn duy nhất là data.json.

Chỉ lấy căn đang hiển thị trên web và có ảnh đại diện. Tên file WebP được sinh
theo đúng công thức cũ để 197 ảnh đã tải về giữ nguyên tên, không phải tải lại.

Script KHÔNG đụng vào data.json, chỉ đọc.

Chạy:  python3 scripts/sinh-danh-sach-anh.py [--thu]
"""

import argparse
import json
import os
import re
import sys
import unicodedata

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUONG_DATA = os.path.join(GOC, "data.json")
DUONG_RA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "danh-sach-anh.json")

# Giá trị được coi là "đang hiển thị" ở cột Hiển thị trên Web. Dữ liệu do người
# nhập tay trên Sheet nên phải chấp nhận nhiều cách viết.
GIA_TRI_HIEN_THI = ("TRUE", "1", "CÓ", "CO", "X", "YES")

# data.json lỗi (Apps Script đẩy nhầm file rỗng chẳng hạn) sẽ làm danh sách mất
# sạch và workflow xoá hết ảnh. Dưới ngưỡng này thì dừng, không ghi đè.
NGUONG_TOI_THIEU = 150


def slug(s):
    """Bỏ dấu tiếng Việt, hạ chữ thường, nối bằng dấu gạch ngang.

    Đ/đ phải đổi tay vì NFD không tách được dấu gạch ngang của chữ Đ."""
    s = str(s).replace('Đ', 'D').replace('đ', 'd')
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')


def phan_khu_tu_toa(toa):
    """Suy ra phân khu từ mã tòa. Không nhận diện được thì trả về chuỗi rỗng.

    Thứ tự xét quan trọng: tiền tố dài phải đứng trước tiền tố ngắn, nếu không
    SA5 (Sakura) sẽ rơi nhầm vào nhánh ^S\\d của Sapphire."""
    t = re.sub(r'[\s._-]', '', str(toa)).upper()
    if t.startswith("MAS") or t.startswith("WEST"):
        return "Masteri"
    if t.startswith("SA"):
        return "Sakura"
    if t.startswith("GS"):
        return "Miami"
    if t.startswith("TC"):
        return "Canopy"
    if t.startswith("TK"):
        return "Tonkin"
    if re.match(r'^I\d', t):
        return "Imperia"
    if re.match(r'^A\d', t):
        return "Lumiere"
    if re.match(r'^V\d', t):
        return "Victoria"
    if re.match(r'^S\d', t):
        return "Sapphire"
    if re.match(r'^G\d', t):
        return "Sola Park"
    return ""


def dang_hien_thi(can):
    return str(can.get("Hiển thị trên Web", "")).strip().upper() in GIA_TRI_HIEN_THI


def dung_ban_ghi(can, canh_bao):
    """Dựng một mục cho danh-sach-anh.json, hoặc None nếu bản ghi không dùng được."""
    ma = can.get("Mã nội bộ", "")
    url_goc = str(can.get("Ảnh đại diện", "")).strip()

    khop = re.search(r'id=([A-Za-z0-9_-]+)', url_goc)
    if not khop:
        canh_bao.append("%s: không tách được Drive ID từ %r" % (ma, url_goc))
        return None

    toa = can.get("Tòa", "")
    phan_khu = phan_khu_tu_toa(toa)
    if not phan_khu:
        canh_bao.append("%s: không nhận diện được tòa %r" % (ma, toa))
        return None

    loai = can.get("Loại", "")
    dien_tich = can.get("Diện tích", "")
    try:
        dien_tich_lam_tron = round(float(dien_tich))
    except (TypeError, ValueError):
        canh_bao.append("%s: diện tích không phải số (%r)" % (ma, dien_tich))
        return None

    # Công thức tên file phải giữ nguyên: ảnh đã tải về nằm trong anh-can-ho/
    # theo đúng tên này, đổi một ký tự là 197 ảnh cũ thành mồ côi.
    ten_file = 'cho-thue-can-ho-%s-%s-%dm2-%s.webp' % (
        slug(loai), slug(phan_khu), dien_tich_lam_tron, slug(ma))

    return {
        "ma": ma,
        "toa": toa,
        "phan_khu": phan_khu,
        "loai": loai,
        "dien_tich": dien_tich,
        "drive_id": khop.group(1),
        "url_goc": url_goc,
        "ten_file": ten_file,
    }


def main():
    bo_phan_tich = argparse.ArgumentParser()
    bo_phan_tich.add_argument("--thu", action="store_true",
                              help="chỉ in thống kê, không ghi file")
    tham_so = bo_phan_tich.parse_args()

    with open(DUONG_DATA, encoding="utf-8") as f:
        du_lieu = json.load(f)

    co_anh = [c for c in du_lieu
              if dang_hien_thi(c) and str(c.get("Ảnh đại diện", "")).strip()]

    canh_bao = []
    ban_ghi = [bg for c in co_anh if (bg := dung_ban_ghi(c, canh_bao))]
    ban_ghi.sort(key=lambda x: x["ten_file"])

    # Hai căn cùng loại, cùng phân khu, cùng diện tích và trùng mã sẽ đè ảnh của
    # nhau. Không đoán bừa căn nào đúng — dừng để người xem lại data.json.
    theo_ten = {}
    trung = []
    for bg in ban_ghi:
        if bg["ten_file"] in theo_ten:
            trung.append((theo_ten[bg["ten_file"]], bg))
        else:
            theo_ten[bg["ten_file"]] = bg

    print("=== THỐNG KÊ ===")
    print("Tổng bản ghi trong data.json : %d" % len(du_lieu))
    print("Đang hiển thị + có ảnh       : %d" % len(co_anh))
    print("Bản ghi hợp lệ               : %d" % len(ban_ghi))
    print("Tên file trùng               : %d" % len(trung))
    print("Tòa không nhận diện được     : %d"
          % sum(1 for c in canh_bao if "không nhận diện được tòa" in c))

    if canh_bao:
        print("\nCảnh báo (%d):" % len(canh_bao))
        for dong in canh_bao[:20]:
            print("  - %s" % dong)
        if len(canh_bao) > 20:
            print("  ... còn %d cảnh báo nữa" % (len(canh_bao) - 20))

    if trung:
        print("\nDỪNG: có tên file trùng, không ghi %s." % DUONG_RA)
        for cu, moi in trung:
            print("  - %s  <-  %s và %s" % (moi["ten_file"], cu["ma"], moi["ma"]))
        return 1

    if len(ban_ghi) < NGUONG_TOI_THIEU:
        print("\nDỪNG: chỉ có %d bản ghi hợp lệ, dưới ngưỡng %d — data.json "
              "nhiều khả năng đang lỗi. Không ghi đè danh sách cũ."
              % (len(ban_ghi), NGUONG_TOI_THIEU))
        return 1

    if tham_so.thu:
        print("\n(--thu) Không ghi file. Danh sách sẽ có %d mục." % len(ban_ghi))
        return 0

    with open(DUONG_RA, "w", encoding="utf-8") as f:
        json.dump(ban_ghi, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("\nĐã ghi scripts/danh-sach-anh.json (%d mục)." % len(ban_ghi))
    return 0


if __name__ == "__main__":
    sys.exit(main())

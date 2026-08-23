#!/usr/bin/env python3
"""Sinh scripts/danh-sach-anh.json từ data.json ở gốc repo.

Trước đây danh-sach-anh.json là file tĩnh, không script nào sinh ra nên mỗi lần
data.json có căn mới là danh sách lại lỗi thời, kéo theo tai-anh-can-ho.py bỏ
sót ảnh. Script này dựng lại danh sách đó từ nguồn duy nhất là data.json.

Có hai loại bản ghi:
  - "bia"     — ảnh đại diện của mọi căn đang hiển thị trên web và có ảnh đại
                diện. Tên file WebP theo đúng công thức cũ để ảnh đã tải về
                giữ nguyên tên, không phải tải lại (loai_anh="bia").
  - "gallery" — mọi ảnh trong cột "Danh sách ảnh", nhưng CHỈ với căn đủ điều
                kiện có trang riêng (giống hệt du_dieu_kien() trong
                sinh-trang-can.py, nạp qua importlib — không chép luật).
                Trỏ về đúng trang căn qua khoá "trang".

Script KHÔNG đụng vào data.json, chỉ đọc.

Chạy:  python3 scripts/sinh-danh-sach-anh.py [--thu]
"""

import argparse
import importlib.util
import json
import os
import re
import sys
import unicodedata

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DUONG_DATA = os.path.join(GOC, "data.json")
DUONG_RA = os.path.join(THU_MUC_SCRIPT, "danh-sach-anh.json")
DUONG_MAP_ANH = os.path.join(GOC, "anh-can-ho", "anh-map.json")

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


def drive_id_tu_url(url):
    khop = re.search(r'id=([A-Za-z0-9_-]+)', str(url))
    return khop.group(1) if khop else None


def dung_ban_ghi(can, canh_bao):
    """Dựng một mục ảnh bìa cho danh-sach-anh.json, hoặc None nếu bản ghi
    không dùng được."""
    ma = can.get("Mã nội bộ", "")
    url_goc = str(can.get("Ảnh đại diện", "")).strip()

    drive_id = drive_id_tu_url(url_goc)
    if not drive_id:
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
    # theo đúng tên này, đổi một ký tự là hàng trăm ảnh cũ thành mồ côi.
    ten_file = 'cho-thue-can-ho-%s-%s-%dm2-%s.webp' % (
        slug(loai), slug(phan_khu), dien_tich_lam_tron, slug(ma))

    return {
        "ma": ma,
        "toa": toa,
        "phan_khu": phan_khu,
        "loai": loai,
        "dien_tich": dien_tich,
        "drive_id": drive_id,
        "url_goc": url_goc,
        "ten_file": ten_file,
        "loai_anh": "bia",
    }


def nap_module_trang():
    """Nạp sinh-trang-can.py để dùng lại du_dieu_kien() và tinh_slug() — điều
    kiện và slug của ảnh gallery phải khớp tuyệt đối với điều kiện và URL của
    trang căn, viết lại ở đây sớm muộn sẽ lệch nhau.

    Gọi HÀM NÀY chỉ lúc cần (trong main()), không gọi ở mức module: file kia
    tự nạp lại chính file này qua importlib ở mức module của nó, gọi ở đây tại
    thời điểm nạp module sẽ đệ quy vô hạn."""
    duong = os.path.join(THU_MUC_SCRIPT, "sinh-trang-can.py")
    dac_ta = importlib.util.spec_from_file_location("sinh_trang_can", duong)
    mo_dun = importlib.util.module_from_spec(dac_ta)
    cu = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        dac_ta.loader.exec_module(mo_dun)
    finally:
        sys.dont_write_bytecode = cu
    return mo_dun


def doc_map_anh():
    """Bảng tra drive_id -> tên file WebP đã có trên đĩa (chỉ đọc).

    Nguồn sự thật duy nhất để chống đổi tên ảnh gallery khi chủ nhà đảo thứ
    tự ảnh trong Sheet: ảnh đã tải rồi thì giữ nguyên tên, không tính lại
    theo vị trí mới."""
    if not os.path.exists(DUONG_MAP_ANH):
        return {}
    with open(DUONG_MAP_ANH, encoding="utf-8") as f:
        anh_map = json.load(f)
    return {drive_id: os.path.basename(duong) for drive_id, duong in anh_map.items()}


def dung_ban_ghi_gallery(can, s, anh_map_ten_file, theo_drive_id, canh_bao):
    """Dựng các bản ghi ảnh gallery của một căn đã có trang riêng.

    `theo_drive_id` là bảng tra TOÀN CỤC (mọi bản ghi đã dựng, cả bìa lẫn
    gallery) dùng để khử trùng lặp: một drive_id chỉ xuất hiện một lần trong
    danh-sach-anh.json. Ảnh bìa thường trùng ảnh gallery số 1 — gặp trường hợp
    đó thì giữ bản ghi bìa (tên file bìa đã được các script khác dùng), chỉ bổ
    sung khoá "trang"."""
    ma = str(can.get("Mã nội bộ", "")).strip()
    toa = can.get("Tòa", "")
    phan_khu = phan_khu_tu_toa(toa)
    loai = can.get("Loại", "")
    dien_tich = can.get("Diện tích", "")
    trang = "/can-ho/%s/" % s

    # N của ảnh mới phải nối tiếp N lớn nhất đã dùng cho chính căn này trên
    # đĩa — không bắt đầu lại từ 1 mỗi lần, nếu không sẽ ghi đè tên đã có.
    mau_hau_to = re.compile(r'^%s-a(\d+)\.webp$' % re.escape(s))
    da_dung = [int(m.group(1)) for ten in anh_map_ten_file.values()
              if (m := mau_hau_to.match(ten))]
    n_ke_tiep = (max(da_dung) + 1) if da_dung else 1

    ket_qua = []
    for url in str(can.get("Danh sách ảnh", "") or "").split("\n"):
        url = url.strip()
        if not url:
            continue
        drive_id = drive_id_tu_url(url)
        if not drive_id:
            canh_bao.append("%s: không tách được Drive ID từ ảnh gallery %r" % (ma, url))
            continue

        if drive_id in theo_drive_id:
            hien_co = theo_drive_id[drive_id]
            if hien_co.get("loai_anh") == "bia" and not hien_co.get("trang"):
                hien_co["trang"] = trang
            continue

        ten_co_san = anh_map_ten_file.get(drive_id)
        if ten_co_san:
            ten_file = ten_co_san
        else:
            ten_file = "%s-a%d.webp" % (s, n_ke_tiep)
            n_ke_tiep += 1

        bg = {
            "ma": ma, "toa": toa, "phan_khu": phan_khu, "loai": loai,
            "dien_tich": dien_tich, "drive_id": drive_id, "url_goc": url,
            "ten_file": ten_file, "loai_anh": "gallery", "trang": trang,
        }
        theo_drive_id[drive_id] = bg
        ket_qua.append(bg)
    return ket_qua


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

    print("=== THỐNG KÊ ẢNH BÌA ===")
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

    # --- Ảnh gallery: chỉ với căn đủ điều kiện có trang riêng ------------
    trang_mod = nap_module_trang()
    anh_map_ten_file = doc_map_anh()
    theo_drive_id = {bg["drive_id"]: bg for bg in ban_ghi}

    gallery_units = [c for c in du_lieu if trang_mod.du_dieu_kien(c)]
    gallery_units.sort(key=trang_mod.tinh_slug)

    canh_bao_gallery = []
    ban_ghi_gallery = []
    for c in gallery_units:
        s = trang_mod.tinh_slug(c)
        ban_ghi_gallery.extend(
            dung_ban_ghi_gallery(c, s, anh_map_ten_file, theo_drive_id, canh_bao_gallery))

    print("\n=== THỐNG KÊ ẢNH GALLERY ===")
    print("Căn đủ điều kiện có trang     : %d" % len(gallery_units))
    print("Bản ghi gallery mới           : %d" % len(ban_ghi_gallery))
    if canh_bao_gallery:
        print("\nCảnh báo gallery (%d):" % len(canh_bao_gallery))
        for dong in canh_bao_gallery[:20]:
            print("  - %s" % dong)
        if len(canh_bao_gallery) > 20:
            print("  ... còn %d cảnh báo nữa" % (len(canh_bao_gallery) - 20))

    toan_bo = ban_ghi + ban_ghi_gallery
    toan_bo.sort(key=lambda x: x["ten_file"])

    if tham_so.thu:
        print("\n(--thu) Không ghi file. Danh sách sẽ có %d mục (%d bìa + %d gallery)."
              % (len(toan_bo), len(ban_ghi), len(ban_ghi_gallery)))
        return 0

    with open(DUONG_RA, "w", encoding="utf-8") as f:
        json.dump(toan_bo, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print("\nĐã ghi scripts/danh-sach-anh.json (%d mục: %d bìa + %d gallery)."
          % (len(toan_bo), len(ban_ghi), len(ban_ghi_gallery)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

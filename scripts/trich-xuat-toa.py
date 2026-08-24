#!/usr/bin/env python3
"""Trích xuất danh sách TÒA từ data.json cho Phase 1 của kế hoạch mở rộng SEO
trang tòa (xem docs/audit-repo.md và SEOEXPANSIONPLAN.md).

Script này CHỈ ĐỌC data.json và scripts/sinh-trang-toa.py /
scripts/sinh-danh-sach-anh.py (qua importlib, không chép lại logic chuẩn hoá
mã tòa / suy luận phân khu / tính thống kê — dùng đúng một nguồn như
sinh-trang-toa.py đang làm). Không sinh trang HTML, không sửa data.json.

Ghi ra hai file:
  - data/buildings.json     — TOÀN BỘ tòa có ít nhất 1 căn đang hiển thị
                               (không chỉ 33 tòa đạt ngưỡng), kèm cờ
                               "dat_nguong_sinh_trang" để Phase 2 tự lọc.
  - docs/buildings-mapping.md — bảng biến thể raw -> canonical (yêu cầu Phase 1
                               mục "ghi lại bảng ánh xạ để người review kiểm tra").

QUAN TRỌNG — về field "mapping":
  data.json KHÔNG có cột phân khu. Toàn bộ giá trị "phan_khu" trong file ra
  đều được suy luận từ tiền tố mã tòa qua phan_khu_tu_toa() (importlib từ
  sinh-danh-sach-anh.py). Vì vậy mapping của MỌI tòa đều ghi "inferred" —
  không có trường hợp nào là "from-data" vì trường dữ liệu đó không tồn tại.
  Đây là phát hiện của Phase 0 audit-repo.md mục 2, script này chỉ hiện thực
  hoá đúng phát hiện đó, không tự ý đổi.

Chạy:  python3 scripts/trich-xuat-toa.py [--thu]
"""

import argparse
import datetime
import importlib.util
import json
import os
import statistics
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THU_MUC_SCRIPT = os.path.dirname(os.path.abspath(__file__))
DUONG_DATA = os.path.join(GOC, "data.json")
DUONG_RA_JSON = os.path.join(GOC, "data", "buildings.json")
DUONG_RA_MAPPING = os.path.join(GOC, "docs", "buildings-mapping.md")

NGUONG_TOI_THIEU = 3  # phải khớp NGUONG_TOI_THIEU trong sinh-trang-toa.py

# Ánh xạ "Loại" (giá trị thật trong data.json) -> khoá breakdown trong file ra.
# Giữ đúng 6 khoá SEOEXPANSIONPLAN.md yêu cầu ở Phase 1.
LOAI_SANG_KHOA = {
    "Studio": "studio",
    "1 Ngủ": "1pn",
    "1 Ngủ +": "1pn_plus",
    "2 Ngủ": "2pn",
    "2 Ngủ +": "2pn_plus",
    "3 Ngủ": "3pn",
}


def nap_module(ten_file, ten_module):
    duong = os.path.join(THU_MUC_SCRIPT, ten_file)
    dac_ta = importlib.util.spec_from_file_location(ten_module, duong)
    mo_dun = importlib.util.module_from_spec(dac_ta)
    cu = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        dac_ta.loader.exec_module(mo_dun)
    finally:
        sys.dont_write_bytecode = cu
    return mo_dun


# Dùng lại nguyên hàm chuẩn hoá mã tòa / lọc hiển thị / suy luận phân khu /
# đổi tiền / đổi diện tích từ hai script đã có, không viết lại.
TOA = nap_module("sinh-trang-toa.py", "sinh_trang_toa")
chuan_ma_toa = TOA.chuan_ma_toa
so_tien = TOA.so_tien
dien_tich = TOA.dien_tich
dang_hien_thi = TOA.dang_hien_thi
phan_khu_tu_toa = TOA.phan_khu_tu_toa
ngay_hom_nay = TOA.ngay_hom_nay


def slug_tu_ma(ma_pretty):
    """'S4.01' -> 's4-01'; 'GS2' -> 'gs2'. Không đổi gì khác ngoài hạ chữ
    thường và đổi dấu chấm thành gạch ngang — đúng quy tắc URL Phase 2:
    /{slug}-vinhomes-smart-city/."""
    return ma_pretty.lower().replace(".", "-")


def ma_toa_dep(ma_chuan):
    """Định dạng hiển thị cho mã tòa chuẩn hoá.

    CHỈ áp dụng quy tắc chèn dấu chấm cho tòa Sapphire dạng S+1 số khối+2 số
    tòa (vd S401 -> S4.01) — đây KHÔNG phải suy đoán tự ý: chính trang
    sapphire/index.html (dòng ~877-878, đã publish) mô tả quy ước này bằng
    lời ("Sapphire 1 (S1.01–S1.06...)"), và trang S4.01 hiện có đã dùng đúng
    định dạng này. Với mọi tòa khác (Masteri, Sakura, Miami, Canopy, Tonkin,
    Imperia, Lumiere), giữ NGUYÊN mã chuẩn hoá không chèn thêm ký tự nào —
    đối chiếu Phase 0 cho thấy các trang phân khu tương ứng cũng nhắc tên
    tòa bằng đúng dạng thô này trong nội dung đã publish (vd "tòa TC1",
    "tòa SA1", "tòa I1", "tòa TK1" — không có dấu chấm/khoảng trắng)."""
    if len(ma_chuan) == 4 and ma_chuan[0] == "S" and ma_chuan[1:].isdigit():
        return "%s.%s" % (ma_chuan[:2], ma_chuan[2:])
    return ma_chuan


def thong_ke_day_du(cac_can):
    gia = [so_tien(c.get("Giá thuê")) for c in cac_can]
    gia = [g for g in gia if g > 0]
    dt = [dien_tich(c.get("Diện tích")) for c in cac_can]
    dt = [d for d in dt if d > 0]

    breakdown = {khoa: 0 for khoa in LOAI_SANG_KHOA.values()}
    khong_khop_loai = {}
    for c in cac_can:
        loai = str(c.get("Loại", "")).strip()
        khoa = LOAI_SANG_KHOA.get(loai)
        if khoa:
            breakdown[khoa] += 1
        elif loai:
            khong_khop_loai[loai] = khong_khop_loai.get(loai, 0) + 1

    full = sum(1 for c in cac_can
               if str(c.get("Nội thất", "")).strip().lower() == "full nội thất")

    return {
        "so_can_trong": len(cac_can),
        "breakdown": breakdown,
        "gia": {
            "min": min(gia) if gia else 0,
            "median": int(statistics.median(gia)) if gia else 0,
            "max": max(gia) if gia else 0,
        },
        "dien_tich": {
            "min": round(min(dt)) if dt else 0,
            "max": round(max(dt)) if dt else 0,
        },
        "noi_that": {
            "full": full,
            "co_ban": len(cac_can) - full,
        },
        "_loai_khong_khop": khong_khop_loai,  # chỉ để cảnh báo, không ghi ra file cuối
    }


def main():
    bo_phan_tich = argparse.ArgumentParser(
        description="Trích xuất danh sách tòa từ data.json (Phase 1).")
    bo_phan_tich.add_argument("--thu", action="store_true",
                              help="chỉ in kết quả, không ghi file")
    tham_so = bo_phan_tich.parse_args()

    with open(DUONG_DATA, encoding="utf-8") as f:
        du_lieu = json.load(f)

    if not isinstance(du_lieu, list) or not du_lieu:
        print("LỖI: data.json rỗng hoặc không phải mảng. Dừng, không ghi gì.")
        return 1

    hom_nay = ngay_hom_nay().strftime("%Y-%m-%d")

    # Gom theo mã tòa chuẩn hoá, đồng thời giữ lại MỌI biến thể raw gặp được
    # (kể cả ở căn không hiển thị) để dựng bảng ánh xạ cho người review.
    theo_toa = {}          # canonical -> list các dòng ĐANG HIỂN THỊ
    bien_the_raw = {}      # canonical -> set(chuỗi raw gặp trong TOÀN BỘ data.json)
    tong_dong_moi_trang_thai = {}  # canonical -> tổng số dòng (mọi trạng thái hiển thị)

    for c in du_lieu:
        toa_raw = c.get("Tòa", "")
        if not str(toa_raw).strip():
            continue
        canonical = chuan_ma_toa(toa_raw)
        bien_the_raw.setdefault(canonical, set()).add(str(toa_raw))
        tong_dong_moi_trang_thai[canonical] = tong_dong_moi_trang_thai.get(canonical, 0) + 1
        if dang_hien_thi(c):
            theo_toa.setdefault(canonical, []).append(c)

    ket_qua = []
    canh_bao_loai_la = {}
    for canonical in sorted(theo_toa):
        cac_can = theo_toa[canonical]
        tk = thong_ke_day_du(cac_can)
        if tk.pop("_loai_khong_khop"):
            canh_bao_loai_la[canonical] = tk

        phan_khu = phan_khu_tu_toa(canonical)
        ma_dep = ma_toa_dep(canonical)

        ket_qua.append({
            "ma_toa": ma_dep,
            "ma_toa_du_lieu": canonical,
            "slug": slug_tu_ma(ma_dep),
            "phan_khu": phan_khu if phan_khu else None,
            "mapping": "inferred",  # xem docstring — data.json không có cột phân khu
            "dat_nguong_sinh_trang": tk["so_can_trong"] >= NGUONG_TOI_THIEU,
            **tk,
            "cap_nhat": hom_nay,
        })

    dat_nguong = [b for b in ket_qua if b["dat_nguong_sinh_trang"]]
    duoi_nguong = [b for b in ket_qua if not b["dat_nguong_sinh_trang"]]
    khong_map_duoc = [b for b in ket_qua if b["phan_khu"] is None]

    print("Tổng số tòa có >=1 căn đang hiển thị: %d" % len(ket_qua))
    print("  - Đạt ngưỡng >=%d căn (sẽ sinh trang ở Phase 2): %d"
          % (NGUONG_TOI_THIEU, len(dat_nguong)))
    print("  - Dưới ngưỡng (1-2 căn, KHÔNG sinh trang riêng): %d" % len(duoi_nguong))
    print("  - Không suy luận được phân khu (cần người review xác nhận thủ công): %d"
          % len(khong_map_duoc))
    if khong_map_duoc:
        for b in khong_map_duoc:
            print("      %s" % b["ma_toa_du_lieu"])
    if canh_bao_loai_la:
        print("\nCẢNH BÁO: có căn với giá trị 'Loại' không khớp 6 khoá chuẩn:")
        for canonical, loai_la in canh_bao_loai_la.items():
            print("  %s: %s" % (canonical, loai_la))

    if tham_so.thu:
        print("\n(--thu) Không ghi file.")
        return 0

    os.makedirs(os.path.dirname(DUONG_RA_JSON), exist_ok=True)
    with open(DUONG_RA_JSON, "w", encoding="utf-8", newline="") as f:
        json.dump(ket_qua, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("\nĐã ghi %s (%d tòa)." % (os.path.relpath(DUONG_RA_JSON, GOC), len(ket_qua)))

    # Bảng ánh xạ biến thể — yêu cầu bắt buộc của Phase 1, kể cả khi rỗng.
    dong_bang = []
    co_bien_the = False
    for canonical in sorted(bien_the_raw):
        raws = sorted(bien_the_raw[canonical])
        if len(raws) > 1:
            co_bien_the = True
        dong_bang.append("| `%s` | %s | %d |" % (
            canonical, ", ".join("`%s`" % r for r in raws),
            tong_dong_moi_trang_thai[canonical]))

    with open(DUONG_RA_MAPPING, "w", encoding="utf-8", newline="") as f:
        f.write("# Bảng ánh xạ biến thể mã tòa -> canonical\n\n")
        f.write("Sinh bởi `scripts/trich-xuat-toa.py` từ toàn bộ `data.json` "
                "(mọi trạng thái hiển thị), ngày %s.\n\n" % hom_nay)
        if co_bien_the:
            f.write("Có tòa với nhiều cách viết khác nhau trong Sheet — xem "
                    "các dòng có hơn 1 giá trị ở cột \"Biến thể raw\".\n\n")
        else:
            f.write("**Không có canonical nào gộp từ nhiều biến thể raw khác "
                    "nhau** — cột \"Tòa\" trong data.json hiện tại đã nhất "
                    "quán 1-1 với mã chuẩn hoá (khả năng do Sheet dùng "
                    "dropdown/validation ở nguồn). Bảng dưới đây vẫn liệt kê "
                    "đủ để đối chiếu, theo đúng yêu cầu Phase 1.\n\n")
        f.write("| Mã canonical | Biến thể raw gặp trong data.json | Tổng số dòng (mọi trạng thái) |\n")
        f.write("|---|---|---|\n")
        f.write("\n".join(dong_bang))
        f.write("\n")
    print("Đã ghi %s." % os.path.relpath(DUONG_RA_MAPPING, GOC))
    return 0


if __name__ == "__main__":
    sys.exit(main())

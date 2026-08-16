#!/usr/bin/env python3
"""Nghiệm thu chung — đồng bộ số căn và khoảng giá trên 25 trang danh mục,
sau khi đã chạy scripts/dung-lai-trang-danh-muc.py rồi scripts/cap-nhat-so-can.mjs.

Với mỗi trang, "sự thật" (N_that, gia_that) đọc trực tiếp từ chính
section.luoi — đúng những article[data-ma-noi-bo] và div.gia đang hiển thị
trên lưới, không tính lại qua data.json/bộ lọc. Sáu điều kiện:

  C-1  a.cta-loc khớp N_that                                     (25/25)
  C-2  mọi span[data-so="can"] khớp N_that                        (25/25)
  C-3  span[data-so="gia-min"] / "gia-max" khớp gia_that     (25/25, trang có span)
  C-4  khoảng giá trong meta description khớp gia_that      (25/25, trang có mẫu)
  C-5  số căn trong <title> = numberOfItems = h2.tieu-de-luoi = N_that (25/25)
  C-6  chạy pipeline (hai script trên) thêm một lần nữa -> không sinh thêm
       thay đổi nào (bắt buộc, tự chạy trong chính script này)

Chạy:  python3 scripts/kiem-tra-dong-bo-so.py [--bo-qua-c6]
Thoát mã 1 nếu bất kỳ điều kiện nào (áp dụng được) chưa đạt ở bất kỳ trang nào.
In bảng từng trang; dán nguyên output vào phần mô tả PR.
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BO_QUA_THU_MUC = {".git", ".github", "node_modules", "images", "scripts",
                  "anh-can-ho"}

RE_LUOI = re.compile(r'<section class="luoi"[^>]*>(.*?)\n[ \t]*</section>', re.S)
RE_ARTICLE = re.compile(
    r'<article class="the[^"]*"\s+data-ma-noi-bo="([^"]*)">(.*?)</article>', re.S)
RE_GIA = re.compile(r'<div class="gia">([^<]*)<small>')
RE_CTA_LOC = re.compile(r'<a class="cta-loc"[^>]*>.*?</a>', re.S)
RE_CTA_LOC_SO = re.compile(r'Lọc chi tiết\D*?(\d+)')
RE_SPAN_CAN = re.compile(r'<span data-so="can">([^<]*)</span>')
RE_SPAN_GIA_MIN = re.compile(r'<span data-so="gia-min">([^<]*)</span>')
RE_SPAN_GIA_MAX = re.compile(r'<span data-so="gia-max">([^<]*)</span>')
RE_TITLE = re.compile(r'<title[^>]*>(.*?)</title>', re.S)
RE_TITLE_SO_CAN = re.compile(r'(\d+)\s*căn')
RE_H2_SO_CAN = re.compile(r'<h2 class="tieu-de-luoi"[^>]*>Danh sách\s+(\d+)\s+căn')
RE_NUMBER_OF_ITEMS = re.compile(r'"numberOfItems":(\d+)')
RE_META_DESC = re.compile(r'<meta name="description"[^>]*\bcontent="([^"]*)"')
RE_KHOANG_GIA = re.compile(r'([\d,]+)\s*triệu–([\d,]+)\s*triệu')

HAU_TO_TRIEU = " triệu"


def tim_trang_danh_muc():
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


def gia_tu_van_ban(text):
    """'8,5 triệu' -> (8.5, '8,5'); 'Liên hệ' hoặc rỗng -> None."""
    text = text.strip()
    if not text.endswith(HAU_TO_TRIEU):
        return None
    chuoi_so = text[:-len(HAU_TO_TRIEU)]
    try:
        gia_tri = float(chuoi_so.replace(",", "."))
    except ValueError:
        return None
    return gia_tri, chuoi_so


def phan_tich_su_that(html):
    """Đọc N_that và gia_that trực tiếp từ section.luoi."""
    m_luoi = RE_LUOI.search(html)
    than_luoi = m_luoi.group(1) if m_luoi else ""

    n_that = 0
    cac_gia = []
    for m in RE_ARTICLE.finditer(than_luoi):
        n_that += 1
        m_gia = RE_GIA.search(m.group(2))
        if not m_gia:
            continue
        kq = gia_tu_van_ban(m_gia.group(1))
        if kq is not None:
            cac_gia.append(kq)

    gia_min_chu = gia_max_chu = None
    if cac_gia:
        gia_min_chu = min(cac_gia, key=lambda x: x[0])[1]
        gia_max_chu = max(cac_gia, key=lambda x: x[0])[1]

    return n_that, gia_min_chu, gia_max_chu


def kiem_c1(html, n_that):
    khop = RE_CTA_LOC.search(html)
    if not khop:
        return "TRƯỢT", "không tìm thấy a.cta-loc"
    m = RE_CTA_LOC_SO.search(khop.group(0))
    if not m:
        return "TRƯỢT", "không đọc được số trong a.cta-loc"
    if m.group(1) != str(n_that):
        return "TRƯỢT", "a.cta-loc=%s, N_that=%d" % (m.group(1), n_that)
    return "OK", ""


def kiem_c2(html, n_that):
    cac = RE_SPAN_CAN.findall(html)
    if not cac:
        return "TRƯỢT", "không có span[data-so=\"can\"] nào"
    lech = [v for v in cac if v != str(n_that)]
    if lech:
        return "TRƯỢT", "span[can] có giá trị lệch: %s (N_that=%d)" % (set(lech), n_that)
    return "OK", ""


def kiem_c3(html, gia_min_chu, gia_max_chu):
    m_min = RE_SPAN_GIA_MIN.search(html)
    m_max = RE_SPAN_GIA_MAX.search(html)
    if not m_min or not m_max:
        return "N/A", "trang không có span gia-min/gia-max"
    if gia_min_chu is None:
        return "TRƯỢT", "có span nhưng không có căn nào giá > 0 trong lưới"
    if m_min.group(1) != gia_min_chu or m_max.group(1) != gia_max_chu:
        return "TRƯỢT", "span=%s–%s, gia_that=%s–%s" % (
            m_min.group(1), m_max.group(1), gia_min_chu, gia_max_chu)
    return "OK", ""


def kiem_c4(html, gia_min_chu, gia_max_chu):
    m_desc = RE_META_DESC.search(html)
    if not m_desc:
        return "N/A", "không có thẻ meta description"
    cac_khop = RE_KHOANG_GIA.findall(m_desc.group(1))
    if len(cac_khop) != 1:
        return "N/A", "description không có đúng 1 mẫu \"N triệu–M triệu\""
    if gia_min_chu is None:
        return "TRƯỢT", "description có mẫu nhưng không có căn nào giá > 0 trong lưới"
    got_min, got_max = cac_khop[0]
    if got_min != gia_min_chu or got_max != gia_max_chu:
        return "TRƯỢT", "description=%s–%s, gia_that=%s–%s" % (
            got_min, got_max, gia_min_chu, gia_max_chu)
    return "OK", ""


def kiem_c5(html, n_that):
    m_title = RE_TITLE.search(html)
    m_h2 = RE_H2_SO_CAN.search(html)
    m_ld = RE_NUMBER_OF_ITEMS.search(html)
    if not (m_title and m_h2 and m_ld):
        return "TRƯỢT", "thiếu <title>, h2.tieu-de-luoi hoặc numberOfItems"
    m_title_so = RE_TITLE_SO_CAN.search(m_title.group(1))
    if not m_title_so:
        return "TRƯỢT", "<title> không có mẫu \"N căn\""
    gia_tri = {
        "<title>": m_title_so.group(1),
        "numberOfItems": m_ld.group(1),
        "h2.tieu-de-luoi": m_h2.group(1),
        "N_that": str(n_that),
    }
    if len(set(gia_tri.values())) != 1:
        return "TRƯỢT", ", ".join("%s=%s" % kv for kv in gia_tri.items())
    return "OK", ""


def chay_pipeline():
    ket_qua = subprocess.run(
        [sys.executable, os.path.join(GOC, "scripts", "dung-lai-trang-danh-muc.py")],
        cwd=GOC, capture_output=True, text=True)
    if ket_qua.returncode != 0:
        raise RuntimeError("dung-lai-trang-danh-muc.py thoát mã %d:\n%s"
                           % (ket_qua.returncode, ket_qua.stderr))
    ket_qua = subprocess.run(
        ["node", os.path.join(GOC, "scripts", "cap-nhat-so-can.mjs")],
        cwd=GOC, capture_output=True, text=True)
    if ket_qua.returncode != 0:
        raise RuntimeError("cap-nhat-so-can.mjs thoát mã %d:\n%s"
                           % (ket_qua.returncode, ket_qua.stderr))


def bam_cac_trang(cac_trang):
    bam = {}
    for duong in cac_trang:
        with open(duong, "rb") as f:
            bam[duong] = hashlib.sha256(f.read()).hexdigest()
    return bam


def kiem_c6(cac_trang):
    """Chạy lại nguyên pipeline (đã coi là chạy 'lần 1' trước khi gọi script
    này) thêm một lần nữa ('lần 2') — 25 file phải giống hệt byte."""
    truoc = bam_cac_trang(cac_trang)
    try:
        chay_pipeline()
    except RuntimeError as loi:
        return "TRƯỢT", str(loi)
    sau = bam_cac_trang(cac_trang)
    lech = [os.path.relpath(d, GOC) for d in cac_trang if truoc[d] != sau[d]]
    if lech:
        return "TRƯỢT", "chạy thêm một lần vẫn còn đổi: %s" % ", ".join(lech)
    return "OK", ""


def main():
    bo_phan_tich = argparse.ArgumentParser(
        description="Nghiệm thu chung: đồng bộ số căn/khoảng giá 25 trang danh mục.")
    bo_phan_tich.add_argument("--bo-qua-c6", action="store_true",
                              help="không tự chạy lại pipeline để kiểm C-6 "
                                   "(chỉ dùng khi đã kiểm C-6 riêng)")
    tham_so = bo_phan_tich.parse_args()

    cac_trang = tim_trang_danh_muc()
    if not cac_trang:
        print("LỖI: không quét thấy trang danh mục nào (#bo-loc-trang).")
        return 1

    hang = []
    for duong in cac_trang:
        ten = os.path.relpath(duong, GOC)
        with open(duong, encoding="utf-8") as f:
            html = f.read()

        n_that, gia_min_chu, gia_max_chu = phan_tich_su_that(html)

        c1 = kiem_c1(html, n_that)
        c2 = kiem_c2(html, n_that)
        c3 = kiem_c3(html, gia_min_chu, gia_max_chu)
        c4 = kiem_c4(html, gia_min_chu, gia_max_chu)
        c5 = kiem_c5(html, n_that)

        hang.append((ten, n_that, c1, c2, c3, c4, c5))

    rong = max(len(h[0]) for h in hang)
    dau = "%-*s | N_that | C-1   | C-2   | C-3   | C-4   | C-5" % (rong, "trang")
    print(dau)
    print("-" * (len(dau) + 5))
    for ten, n_that, c1, c2, c3, c4, c5 in hang:
        print("%-*s | %6d | %-5s | %-5s | %-5s | %-5s | %-5s" % (
            rong, ten, n_that, c1[0], c2[0], c3[0], c4[0], c5[0]))

    ghi_chu = []
    for ten, n_that, c1, c2, c3, c4, c5 in hang:
        for ma, (kq, ly_do) in [("C-1", c1), ("C-2", c2), ("C-3", c3),
                                ("C-4", c4), ("C-5", c5)]:
            if kq == "TRƯỢT":
                ghi_chu.append("  %s %s: %s" % (ten, ma, ly_do))
    if ghi_chu:
        print("\nChi tiết TRƯỢT:")
        for g in ghi_chu:
            print(g)

    def dem(idx, ky_hieu):
        ap_dung = [h[idx] for h in hang if h[idx][0] != "N/A"]
        dat = [h for h in ap_dung if h[0] == "OK"]
        return "%s: %d/%d (trong %d trang áp dụng được)" % (
            ky_hieu, len(dat), len(ap_dung), len(ap_dung))

    print()
    print(dem(2, "C-1"))
    print(dem(3, "C-2"))
    print(dem(4, "C-3"))
    print(dem(5, "C-4"))
    print(dem(6, "C-5"))

    dat_c1_c5 = all(h[i][0] in ("OK", "N/A") for h in hang for i in (2, 3, 4, 5, 6))

    if tham_so.bo_qua_c6:
        c6 = ("N/A", "--bo-qua-c6")
    else:
        print("\nĐang chạy lại pipeline (dung-lai-trang-danh-muc.py rồi "
              "cap-nhat-so-can.mjs) để kiểm C-6...")
        c6 = kiem_c6(cac_trang)
    print("C-6: %s%s" % (c6[0], (" — " + c6[1]) if c6[1] else ""))

    tat_ca_dat = dat_c1_c5 and c6[0] in ("OK", "N/A")

    if not tat_ca_dat:
        print("\nKẾT QUẢ: TRƯỢT.")
        return 1
    print("\nKẾT QUẢ: ĐẠT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

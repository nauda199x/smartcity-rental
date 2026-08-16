#!/usr/bin/env python3
"""Nghiệm thu VIỆC A — chèn span mốc data-so vào a.cta-loc và section.bai.

Ba điều kiện, đo trên đúng 25 trang danh mục (file */index.html có khai
#bo-loc-trang):

  A-1  Gỡ toàn bộ thẻ HTML khỏi bản TRƯỚC và bản SAU khi chèn span, chuẩn hoá
       khoảng trắng — hai chuỗi phải giống hệt từng ký tự. Việc A chỉ được
       thêm <span>/</span>, không được đổi một ký tự nội dung nào.
  A-2  Mỗi trang có đúng một span[data-so="can"] nằm bên trong a.cta-loc.
  A-3  Mọi span[data-so] chỉ chứa chữ số, dấu phẩy hoặc dấu chấm — không có
       thẻ con.

Bản TRƯỚC lấy qua git (không cần giữ file .orig riêng):
  - Nếu working tree đang có thay đổi chưa commit ở các trang danh mục ->
    bản TRƯỚC = phiên bản đang có trong git HEAD, bản SAU = file trên đĩa.
  - Nếu working tree sạch (đã commit) -> bản TRƯỚC = HEAD^, bản SAU = HEAD.
  Có thể ép bằng --base <ref> nếu cần so với một mốc khác.

Chạy:  python3 scripts/kiem-tra-span-moc.py [--base <git-ref>]
Thoát mã 1 nếu bất kỳ trang nào trượt bất kỳ điều kiện nào.
"""

import argparse
import os
import re
import subprocess
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BO_QUA_THU_MUC = {".git", ".github", "node_modules", "images", "scripts",
                  "anh-can-ho"}

KHOA_HOP_LE = {"can", "gia-min", "gia-max", "dt-min", "dt-max"}

RE_TAG = re.compile(r'<[^>]*>')
RE_WS = re.compile(r'\s+')
RE_CTA_LOC = re.compile(r'<a class="cta-loc"[^>]*>.*?</a>', re.S)
RE_SPAN_MO = re.compile(r'<span data-so="([^"]*)">')


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


def strip_va_chuan_hoa(html):
    return RE_WS.sub(" ", RE_TAG.sub("", html)).strip()


def git_show(ref, duong_tuyet_doi):
    duong_tuong_doi = os.path.relpath(duong_tuyet_doi, GOC)
    ket_qua = subprocess.run(
        ["git", "show", "%s:%s" % (ref, duong_tuong_doi)],
        cwd=GOC, capture_output=True, text=True)
    if ket_qua.returncode != 0:
        return None
    return ket_qua.stdout


def co_thay_doi_chua_commit(cac_trang):
    duong_tuong_doi = [os.path.relpath(d, GOC) for d in cac_trang]
    ket_qua = subprocess.run(
        ["git", "status", "--porcelain", "--"] + duong_tuong_doi,
        cwd=GOC, capture_output=True, text=True)
    return bool(ket_qua.stdout.strip())


def kiem_tra_a1(truoc, sau):
    return strip_va_chuan_hoa(truoc) == strip_va_chuan_hoa(sau)


def kiem_tra_a2(sau):
    """Đúng một span[data-so="can"] bên trong a.cta-loc."""
    khop = RE_CTA_LOC.search(sau)
    if not khop:
        return False, "không tìm thấy a.cta-loc"
    so_can = len(re.findall(r'<span data-so="can">', khop.group(0)))
    if so_can != 1:
        return False, "a.cta-loc có %d span[data-so=\"can\"] (cần đúng 1)" % so_can
    return True, ""


def kiem_tra_a3(sau):
    """Mọi span[data-so] chỉ chứa chữ số/phẩy/chấm, không thẻ con, khoá hợp lệ."""
    loi = []
    for m in RE_SPAN_MO.finditer(sau):
        khoa = m.group(1)
        if khoa not in KHOA_HOP_LE:
            loi.append("khoá lạ %r" % khoa)
            continue
        con = sau[m.end():]
        dong = re.match(r'([^<]*)</span>', con)
        if not dong:
            loi.append("span[data-so=%r] không đóng sạch (có thẻ con?)" % khoa)
            continue
        noi_dung = dong.group(1)
        if not noi_dung or not re.fullmatch(r'[\d,.]+', noi_dung):
            loi.append("span[data-so=%r] chứa %r (phải chỉ gồm chữ số/phẩy/chấm)"
                       % (khoa, noi_dung))
    if loi:
        return False, "; ".join(loi)
    return True, ""


def main():
    bo_phan_tich = argparse.ArgumentParser(
        description="Nghiệm thu Việc A: span mốc data-so.")
    bo_phan_tich.add_argument("--base", default=None,
                              help="git ref của bản TRƯỚC khi chèn span "
                                   "(mặc định tự nhận theo trạng thái working tree)")
    tham_so = bo_phan_tich.parse_args()

    cac_trang = tim_trang_danh_muc()
    if not cac_trang:
        print("LỖI: không quét thấy trang danh mục nào (#bo-loc-trang).")
        return 1

    if tham_so.base:
        base = tham_so.base
    elif co_thay_doi_chua_commit(cac_trang):
        base = "HEAD"
    else:
        base = "HEAD^"

    print("So bản TRƯỚC (git %s) với bản SAU (working tree).\n" % base)

    hang = []
    tat_ca_dat = True
    for duong in cac_trang:
        ten = os.path.relpath(duong, GOC)
        truoc = git_show(base, duong)
        with open(duong, encoding="utf-8") as f:
            sau = f.read()

        if truoc is None:
            hang.append((ten, "LỖI", "-", "-", "không đọc được bản TRƯỚC ở %s" % base))
            tat_ca_dat = False
            continue

        a1 = kiem_tra_a1(truoc, sau)
        a2, loi_a2 = kiem_tra_a2(sau)
        a3, loi_a3 = kiem_tra_a3(sau)

        dat = a1 and a2 and a3
        tat_ca_dat = tat_ca_dat and dat
        ghi_chu = "; ".join(x for x in [
            "" if a1 else "A-1 lệch nội dung",
            "" if a2 else "A-2 " + loi_a2,
            "" if a3 else "A-3 " + loi_a3,
        ] if x)
        hang.append((ten, "OK" if a1 else "TRƯỢT", "OK" if a2 else "TRƯỢT",
                    "OK" if a3 else "TRƯỢT", ghi_chu))

    rong = max(len(h[0]) for h in hang)
    print("%-*s | %-6s | %-6s | %-6s | %s" % (rong, "trang", "A-1", "A-2", "A-3", "ghi chú"))
    print("-" * (rong + 60))
    for ten, a1, a2, a3, ghi_chu in hang:
        print("%-*s | %-6s | %-6s | %-6s | %s" % (rong, ten, a1, a2, a3, ghi_chu))

    so_dat = sum(1 for h in hang if h[1] == "OK" and h[2] == "OK" and h[3] == "OK")
    print("\n%d/%d trang đạt cả ba điều kiện." % (so_dat, len(hang)))

    if not tat_ca_dat:
        print("\nKẾT QUẢ: TRƯỢT.")
        return 1
    print("\nKẾT QUẢ: ĐẠT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

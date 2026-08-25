#!/usr/bin/env python3
"""Nối 26 trang danh mục vào 60 trang chi tiết căn hộ trong can-ho/.

VÌ SAO CẦN SCRIPT NÀY
---------------------
can-ho/ có 60 trang chi tiết tĩnh, đầy đủ schema RealEstateListing/Apartment/
Offer/BreadcrumbList, canonical đúng — tài sản SEO đuôi dài tốt nhất của site.
Nhưng chúng chỉ nhận liên kết từ đúng một trang (can-ho/index.html). Đo trên
26 trang danh mục (25 trang loại/giá/nội thất/phân khu + trang tòa
s4-01-vinhomes-smart-city/): 193/765 thẻ article.the mang data-ma-noi-bo khớp
một trang chi tiết đang tồn tại, nhưng không có lấy một href="/can-ho/..."
nào — 193 cơ hội liên kết nội bộ bị bỏ trống.

Khóa nối đã có sẵn, không cần tạo mới: mỗi thẻ căn mang
data-ma-noi-bo="CT.2N1.200", và can-ho/danh-sach-trang.json là từ điển
slug -> {ma, ...} với "ma" đúng định dạng đó. Trang chi tiết nằm ở
/can-ho/{slug}/.

Script này chỉ bọc tiêu đề thẻ (h3.ten) sẵn có trong một thẻ <a>, không đụng
gì khác — không đổi văn bản, không cần CSS mới, không tạo liên kết tới trang
không tồn tại.

Bản HTML tĩnh này phải khớp TỪNG KÝ TỰ với markup mà dong-bo-can.js dựng lại
trong trình duyệt (hàm dungThe, khối h3.ten) — sai lệch một ký tự là trang
nhảy layout ngay khi JS chạy xong.

Chạy:  python3 scripts/noi-lien-ket-chi-tiet.py [--thu]
"""

import argparse
import html
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUONG_DANH_SACH_TRANG = os.path.join(GOC, "can-ho", "danh-sach-trang.json")

BO_QUA_THU_MUC = {".git", ".github", "node_modules", "images", "scripts",
                  "anh-can-ho"}

# Neo vào data-ma-noi-bo để bắt đúng từng thẻ căn, không neo vào khoảng
# trắng. Không tham lam (.*?) để không nuốt qua thẻ article kế tiếp.
RE_THE = re.compile(
    r'<article class="the[^"]*"[^>]*\bdata-ma-noi-bo="([^"]*)"[^>]*>.*?</article>',
    re.S)

# Neo vào chính thẻ h3.ten bên trong khối article vừa khớp ở trên.
RE_TEN = re.compile(r'(<h3 class="ten">)(.*?)(</h3>)', re.S)


def esc(v):
    """Thoát ký tự đặc biệt cho giá trị thuộc tính, cùng cách sinh-trang-toa.py
    và dong-bo-can.js đang dùng."""
    return html.escape("" if v is None else str(v), quote=True)


def doc_bang_tra():
    """can-ho/danh-sach-trang.json: slug -> {ma, ...} — đảo thành ma -> slug."""
    with open(DUONG_DANH_SACH_TRANG, encoding="utf-8") as f:
        ds = json.load(f)
    bang = {}
    for slug, thong_tin in ds.items():
        ma = str((thong_tin or {}).get("ma", "")).strip()
        if ma:
            bang[ma] = slug
    return bang, len(ds)


def tim_trang_can_xu_ly():
    """Quét repo tìm mọi */index.html có chứa section.luoi. Không viết cứng
    danh sách — trang tòa sinh thêm sau tự động được phủ."""
    ra = []
    for thu_muc, cac_thu_muc, cac_file in os.walk(GOC):
        cac_thu_muc[:] = [d for d in cac_thu_muc
                          if d not in BO_QUA_THU_MUC and not d.startswith(".")]
        for ten in cac_file:
            if ten != "index.html":
                continue
            duong = os.path.join(thu_muc, ten)
            with open(duong, encoding="utf-8") as f:
                if 'class="luoi"' in f.read():
                    ra.append(duong)
    return sorted(ra)


def xu_ly_mot_trang(duong, bang_tra, thong_ke):
    """Bọc <a> quanh h3.ten của mọi thẻ khớp bảng tra. Trả về (html_moi, co_doi)."""
    with open(duong, encoding="utf-8") as f:
        goc = f.read()

    def mot_the(m):
        ma = m.group(1)
        khoi = m.group(0)
        thong_ke["the_quet"] += 1

        slug = bang_tra.get(ma)
        if not slug:
            return khoi
        thong_ke["the_khop"] += 1
        # Dù liên kết vừa chèn hay đã có sẵn, thẻ này đang trỏ tới slug —
        # tính vào độ phủ trang chi tiết cả hai trường hợp.
        thong_ke["slug_duoc_tro"].add(slug)

        def mot_ten(m2):
            mo, noi_dung, dong = m2.group(1), m2.group(2), m2.group(3)
            if "<a" in noi_dung:
                thong_ke["bo_qua_da_co"] += 1
                return m2.group(0)
            thong_ke["lien_ket_chen"] += 1
            return (mo + '<a href="/can-ho/%s/">' % esc(slug)
                    + noi_dung + "</a>" + dong)

        khoi_moi, so_lan = RE_TEN.subn(mot_ten, khoi, count=1)
        return khoi_moi

    moi = RE_THE.sub(mot_the, goc)
    return moi, moi != goc


def main():
    bo_phan_tich = argparse.ArgumentParser(
        description="Nối 26 trang danh mục vào các trang chi tiết căn hộ trong can-ho/.")
    bo_phan_tich.add_argument("--thu", action="store_true",
                              help="chỉ in bảng nghiệm thu, không ghi file")
    tham_so = bo_phan_tich.parse_args()

    bang_tra, tong_slug = doc_bang_tra()
    print("can-ho/danh-sach-trang.json: %d mục, %d mã hợp lệ." % (
        tong_slug, len(bang_tra)))

    cac_trang = tim_trang_can_xu_ly()

    thong_ke = {
        "the_quet": 0,
        "the_khop": 0,
        "lien_ket_chen": 0,
        "bo_qua_da_co": 0,
        "slug_duoc_tro": set(),
    }

    da_doi = 0
    for duong in cac_trang:
        moi, co_doi = xu_ly_mot_trang(duong, bang_tra, thong_ke)
        if co_doi:
            da_doi += 1
            if not tham_so.thu:
                with open(duong, "w", encoding="utf-8", newline="") as f:
                    f.write(moi)

    print()
    print("Trang xử lý:        %d" % len(cac_trang))
    print("Thẻ quét:          %d" % thong_ke["the_quet"])
    print("Thẻ khớp trang CT: %d" % thong_ke["the_khop"])
    print("Liên kết đã chèn:  %d" % thong_ke["lien_ket_chen"])
    print("Bỏ qua (đã có):    %d" % thong_ke["bo_qua_da_co"])
    print("Trang chi tiết được trỏ tới: %d/%d" % (
        len(thong_ke["slug_duoc_tro"]), len(bang_tra)))

    if tham_so.thu:
        print("\n(--thu: chưa ghi file nào, %d trang có thay đổi nếu chạy thật)"
              % da_doi)
    else:
        print("\nĐã ghi %d trang." % da_doi)

    return 0


if __name__ == "__main__":
    sys.exit(main())

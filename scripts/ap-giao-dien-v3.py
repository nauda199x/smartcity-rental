#!/usr/bin/env python3
"""
ap-giao-dien-v3.py — Áp bộ giao diện v3 lên các file HTML tĩnh.

Làm đúng hai việc, không đụng gì khác:
  1. Thay khối <style> nội tuyến bằng link tới /assets/v3.css + font Google.
  2. Trên thẻ căn hộ tĩnh: chuyển <p class="nhan-nt">…</p> từ trong .than
     lên thành huy hiệu nằm trên ảnh (.badge-nt), đúng bản thiết kế v3.
     Chữ bên trong giữ NGUYÊN VĂN, chỉ đổi chỗ đứng và class.

Không sửa: title, meta, heading, JSON-LD, canonical, alt, đường dẫn.

    python3 scripts/ap-giao-dien-v3.py --thu     # xem trước, không ghi
    python3 scripts/ap-giao-dien-v3.py
"""
import re
import sys
import os

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHI_THU = "--thu" in sys.argv

LINK_CSS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Be+Vietnam+Pro:wght@300;400;500;600&display=swap"
      media="print" onload="this.media='all'">
<noscript>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Be+Vietnam+Pro:wght@300;400;500;600&display=swap">
</noscript>
<link rel="stylesheet" href="/assets/v3.css">"""

# Ảnh + huy hiệu tình trạng nằm trong .the-anh; nhãn nội thất nằm dưới, trong .than.
# Bắt cả cụm để chuyển nhãn lên trên mà không đụng vào phần nào khác.
MAU_THE = re.compile(
    r'(<div class="the-anh">.*?)(</div>)'          # 1 = ruột .the-anh, 2 = thẻ đóng
    r'(\s*<div class="than">\s*'
    r'<h3 class="ten">.*?</h3>\s*'
    r'<p class="vi-tri">.*?</p>\s*)'               # 3 = đầu .than, giữ nguyên
    r'<p class="nhan-nt">(.*?)</p>\s*',            # 4 = chữ nhãn nội thất
    re.S,
)


def chuyen_nhan_noi_that(html):
    """Đưa nhãn nội thất lên ảnh. Trả về (html_moi, so_the_da_sua)."""
    dem = [0]

    def thay(m):
        dem[0] += 1
        chu = m.group(4)
        la_full = chu.strip().lower() == "full nội thất"
        lop = "badge-nt" if la_full else "badge-nt thuong"
        return (
            m.group(1)
            + f'<span class="{lop}">{chu}</span>'
            + m.group(2)
            + m.group(3)
        )

    return MAU_THE.sub(thay, html), dem[0]


def thay_style(html):
    """Đổi khối <style> nội tuyến thành link tới file CSS dùng chung."""
    i = html.find("<style>")
    if i == -1:
        return html, False
    j = html.find("</style>", i)
    if j == -1:
        return html, False
    # Giữ đúng thụt lề của dòng chứa <style> cho gọn diff
    dau_dong = html.rfind("\n", 0, i) + 1
    thut = html[dau_dong:i]
    link = ("\n" + thut).join(LINK_CSS.split("\n"))
    return html[:i] + link + html[j + len("</style>"):], True


def xu_ly(duong_dan, doi_the=True):
    html = open(duong_dan, encoding="utf-8").read()
    goc = html
    html, da_thay_style = thay_style(html)
    so_the = 0
    if doi_the:
        html, so_the = chuyen_nhan_noi_that(html)
    if html == goc:
        return None
    if not CHI_THU:
        open(duong_dan, "w", encoding="utf-8").write(html)
    return da_thay_style, so_the


if __name__ == "__main__":
    danh_sach = []
    for thu_muc, con, files in os.walk(GOC):
        con[:] = [d for d in con if d not in
                  {".git", ".github", "node_modules", "images", "scripts", "_design:", "assets"}]
        for ten in sorted(files):
            if ten.endswith(".html"):
                danh_sach.append(os.path.join(thu_muc, ten))

    tong_the = 0
    for duong_dan in sorted(danh_sach):
        ten = os.path.relpath(duong_dan, GOC)
        kq = xu_ly(duong_dan)
        if kq is None:
            print(f"  – {ten}: không có gì để sửa")
            continue
        da_style, so_the = kq
        tong_the += so_the
        print(f"  ✓ {ten}: style={'đã thay' if da_style else 'không có'}, thẻ căn sửa={so_the}")
    print(f"\nTổng số thẻ căn đã chuyển nhãn nội thất: {tong_the}")
    if CHI_THU:
        print("(chạy thử — chưa ghi file nào)")

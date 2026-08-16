#!/usr/bin/env python3
"""Thêm khối FAQPage vào JSON-LD của các trang danh mục đã có FAQ hiển thị.

VÌ SAO CẦN SCRIPT NÀY
---------------------
SEO-CONTENT-AUDIT.md mục 5: 25 trang danh mục (studio/, 1pn/, sapphire/, …)
đều có sẵn khối "Câu hỏi thường gặp" hiển thị thật bằng <details><summary>,
nhưng JSON-LD của các trang này chỉ có BreadcrumbList + ItemList, thiếu hẳn
FAQPage — trong khi 8 trang khác trong site (index.html, các bài cẩm nang…)
đã có FAQPage đúng chuẩn từ trước. Đây là khoảng schema thiếu rõ nhất, đúng
tinh thần "chỉ thêm schema khớp nội dung đã hiển thị" (không tạo nội dung
mới, không tạo review/rating giả).

PHẠM VI
-------
Chỉ đọc khối <h2>Câu hỏi thường gặp</h2>...<details>...</details> đã có sẵn
trong HTML, dựng lại thành đúng cấu trúc FAQPage rồi chèn vào phần tử
"@graph" đã có của JSON-LD. Không đụng URL, canonical, H1, title, meta
description, hay bất kỳ nội dung hiển thị nào. Không đụng 5 khối mà
dung-lai-trang-danh-muc.py quản lý (lưới căn, tiêu đề lưới, đoạn mô tả, khối
thống kê, bảng giá).

Trang không có khối FAQ hiển thị (vd s4-01-vinhomes-smart-city/, dựng theo
cơ chế riêng của sinh-trang-toa.py) thì bỏ qua, không tạo FAQPage rỗng.

Chạy hai lần trên cùng nội dung phải ra file giống hệt (idempotent): nếu
FAQPage đã đúng nội dung rồi thì không ghi lại file.

Chạy:  python3 scripts/them-schema-faq.py [--thu]
"""

import argparse
import html
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BO_QUA_THU_MUC = {".git", ".github", "node_modules", "images", "scripts",
                  "anh-can-ho"}

RE_FAQ_SECTION = re.compile(
    r'<h2>Câu hỏi thường gặp</h2>(.*?)</section>', re.S)
RE_DETAILS = re.compile(
    r'<details><summary>(.*?)</summary><p>(.*?)</p></details>', re.S)
RE_JSONLD = re.compile(
    r'(<script type="application/ld\+json">)(\{.*?\})(</script>)', re.S)
RE_TAG = re.compile(r'<[^>]+>')


def van_ban_thuan(doan_html):
    """Bỏ thẻ HTML, giải mã entity — dùng cho "name"/"text" trong JSON-LD.

    FAQ hiện tại chỉ có <a> lồng bên trong (link sang bài phí dịch vụ); bỏ
    thẻ <a> vẫn giữ nguyên chữ hiển thị, chỉ mất đường link — chấp nhận được
    vì JSON-LD Question/Answer là văn bản thuần, không phải HTML có link."""
    khong_the = RE_TAG.sub("", doan_html)
    return html.unescape(khong_the).strip()


def tim_trang_danh_muc():
    """Quét repo tìm file HTML có khai #bo-loc-trang, giống hệt cách
    dung-lai-trang-danh-muc.py làm — không viết cứng danh sách."""
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


def doc_faq(html_noi_dung):
    """Trả về list [{"@type":"Question", ...}, ...] hoặc [] nếu không có
    khối FAQ hiển thị trên trang."""
    khop_khoi = RE_FAQ_SECTION.search(html_noi_dung)
    if not khop_khoi:
        return []
    cac_cau = RE_DETAILS.findall(khop_khoi.group(1))
    return [
        {
            "@type": "Question",
            "name": van_ban_thuan(q),
            "acceptedAnswer": {
                "@type": "Answer",
                "text": van_ban_thuan(a),
            },
        }
        for q, a in cac_cau
    ]


def ghi_de_faqpage(html_noi_dung, cau_hoi, ten, canh_bao):
    """Chèn/cập nhật phần tử FAQPage trong @graph. Trả về (html_moi, đổi?)."""
    khop = RE_JSONLD.search(html_noi_dung)
    if not khop:
        canh_bao.append("%s: không tìm thấy khối JSON-LD — BỎ QUA." % ten)
        return html_noi_dung, False

    try:
        du_lieu = json.loads(khop.group(2))
    except ValueError:
        canh_bao.append("%s: JSON-LD không parse được — BỎ QUA." % ten)
        return html_noi_dung, False

    if "@graph" not in du_lieu or not isinstance(du_lieu["@graph"], list):
        canh_bao.append("%s: JSON-LD không có @graph dạng mảng — BỎ QUA." % ten)
        return html_noi_dung, False

    faq_moi = {"@type": "FAQPage", "mainEntity": cau_hoi}

    da_co = None
    for i, phan_tu in enumerate(du_lieu["@graph"]):
        if isinstance(phan_tu, dict) and phan_tu.get("@type") == "FAQPage":
            da_co = i
            break

    if da_co is not None:
        if du_lieu["@graph"][da_co] == faq_moi:
            return html_noi_dung, False
        du_lieu["@graph"][da_co] = faq_moi
    else:
        du_lieu["@graph"].append(faq_moi)

    chuoi_moi = json.dumps(du_lieu, ensure_ascii=False, separators=(",", ":"))
    if chuoi_moi == khop.group(2):
        return html_noi_dung, False

    return (html_noi_dung[:khop.start()] + khop.group(1) + chuoi_moi
            + khop.group(3) + html_noi_dung[khop.end():]), True


def xu_ly_mot_trang(duong, chi_thu, canh_bao):
    ten = os.path.relpath(duong, GOC)
    with open(duong, encoding="utf-8") as f:
        noi_dung = f.read()

    cau_hoi = doc_faq(noi_dung)
    if not cau_hoi:
        return {"ten": ten, "so_cau": 0, "trang_thai": "khong-co-faq"}

    noi_dung_moi, doi = ghi_de_faqpage(noi_dung, cau_hoi, ten, canh_bao)
    if doi and not chi_thu:
        with open(duong, "w", encoding="utf-8", newline="") as f:
            f.write(noi_dung_moi)

    return {
        "ten": ten,
        "so_cau": len(cau_hoi),
        "trang_thai": "da-them" if doi else "da-co-san",
    }


def main():
    bo_phan_tich = argparse.ArgumentParser(
        description="Thêm schema FAQPage vào các trang danh mục đã có FAQ hiển thị.")
    bo_phan_tich.add_argument("--thu", action="store_true",
                              help="chỉ in bảng nghiệm thu, không ghi file")
    tham_so = bo_phan_tich.parse_args()

    cac_trang = tim_trang_danh_muc()
    print("Quét thấy %d trang danh mục.\n" % len(cac_trang))

    canh_bao = []
    bang = []
    for duong in cac_trang:
        bang.append(xu_ly_mot_trang(duong, tham_so.thu, canh_bao))

    rong = max([len(d["ten"]) for d in bang] + [5])
    print("%-*s | %6s | %s" % (rong, "trang", "số câu", "trạng thái"))
    print("-" * (rong + 40))
    for d in bang:
        print("%-*s | %6d | %s" % (rong, d["ten"], d["so_cau"], d["trang_thai"]))

    da_them = sum(1 for d in bang if d["trang_thai"] == "da-them")
    khong_co = sum(1 for d in bang if d["trang_thai"] == "khong-co-faq")
    print("\n%d trang được thêm FAQPage, %d trang không có khối FAQ hiển thị (bỏ qua).%s"
          % (da_them, khong_co, "  (--thu: chưa ghi file nào)" if tham_so.thu else ""))

    if canh_bao:
        print("\n%d cảnh báo:" % len(canh_bao))
        for c in canh_bao:
            print("  - " + c)
    else:
        print("\nKhông có cảnh báo nào.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

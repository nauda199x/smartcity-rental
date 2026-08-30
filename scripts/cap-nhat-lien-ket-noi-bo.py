#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cập nhật internal-link tĩnh cho các trang danh mục có #bo-loc-trang.

Kiến trúc:
  Trang chủ -> Loại căn / Phân khu -> Long-tail -> Căn chi tiết -> Cẩm nang.
Không tạo URL mới. Khối link được ghi trực tiếp vào HTML để crawler đọc được
mà không cần JavaScript. Chạy lặp lại cho kết quả ổn định.
"""
import argparse
import collections
import html
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DUONG_DATA = os.path.join(GOC, "data.json")
MOC_DAU = "<!-- SEO-LINKS:BAT-DAU -->"
MOC_CUOI = "<!-- SEO-LINKS:KET-THUC -->"

RE_BO_LOC = re.compile(
    r'<script type="application/json" id="bo-loc-trang">(.*?)</script>', re.S)
RE_KHOI = re.compile(
    r'<!-- SEO-LINKS:BAT-DAU -->.*?<!-- SEO-LINKS:KET-THUC -->', re.S)
RE_CU = re.compile(
    r'\s*<h2[^>]*>\s*Danh mục liên quan\s*</h2>\s*'
    r'<div class="lq">.*?</div>\s*'
    r'<h2[^>]*>\s*Đọc thêm trước khi thuê\s*</h2>\s*'
    r'<div class="lq">.*?</div>\s*', re.S | re.I)

LOAI = {
    "studio": ("studio", "Studio", "/studio/"),
    "1 ngủ": ("1pn", "1 phòng ngủ", "/1pn/"),
    "1 ngủ +": ("1pn-plus", "1 phòng ngủ +", "/1pn-plus/"),
    "2 ngủ": ("2pn", "2 phòng ngủ", "/2pn/"),
    "2 ngủ +": ("2pn-plus", "2 phòng ngủ +", "/2pn-plus/"),
    "3 ngủ": ("3pn", "3 phòng ngủ", "/3pn/"),
}
LOAI_THU_TU = ["studio", "1 ngủ", "1 ngủ +", "2 ngủ", "2 ngủ +", "3 ngủ"]

PHAN_KHU = {
    "Sapphire": ("/sapphire/", "Sapphire"),
    "Masteri": ("/masteri/", "Masteri West Heights"),
    "Miami": ("/miami/", "The Miami"),
    "Sakura": ("/sakura/", "The Sakura"),
    "Imperia": ("/imperia/", "Imperia Smart City"),
    "Lumiere": ("/lumiere/", "Lumière Evergreen"),
    "Canopy": ("/canopy/", "The Canopy"),
    "Tonkin": ("/tonkin/", "The Tonkin"),
}
PHAN_KHU_THU_TU = list(PHAN_KHU)

BAI_PHAN_KHU = {
    "Masteri": ("/cho-thue-can-ho-masteri-west-heights-smart-city.html",
                "Tổng quan thuê Masteri West Heights"),
    "Imperia": ("/cho-thue-can-ho-imperia-smart-city.html",
                "Tổng quan thuê Imperia Smart City"),
    "Lumiere": ("/thue-can-ho-lumiere-evergreen.html",
                "Tổng quan thuê Lumière Evergreen"),
}

LONGTAIL = {
    "studio-duoi-7-trieu": ("studio", "Studio dưới 7 triệu"),
    "studio-7-10-trieu": ("studio", "Studio 7–10 triệu"),
    "studio-full-do": ("studio", "Studio full nội thất"),
    "1pn-plus-duoi-10-trieu": ("1pn-plus", "1 phòng ngủ + dưới 10 triệu"),
    "1pn-plus-full-do": ("1pn-plus", "1 phòng ngủ + full nội thất"),
    "2pn-duoi-10-trieu": ("2pn", "2 phòng ngủ dưới 10 triệu"),
    "2pn-10-12-trieu": ("2pn", "2 phòng ngủ 10–12 triệu"),
    "2pn-full-do": ("2pn", "2 phòng ngủ full nội thất"),
    "2pn-plus-12-15-trieu": ("2pn-plus", "2 phòng ngủ + 12–15 triệu"),
    "3pn-12-15-trieu": ("3pn", "3 phòng ngủ 12–15 triệu"),
    "3pn-full-do": ("3pn", "3 phòng ngủ full nội thất"),
}
LONGTAIL_THEO_LOAI = collections.defaultdict(list)
for _slug, (_parent, _label) in LONGTAIL.items():
    LONGTAIL_THEO_LOAI[_parent].append((_slug, _label))

GUIDE_LINKS = [
    ("/bang-gia-thue-vinhomes-smart-city.html",
     "Bảng giá thuê Smart City",
     "So sánh mặt bằng giá theo loại căn và phân khu."),
    ("/so-sanh-gia-thue-cac-phan-khu-smart-city.html",
     "So sánh giá các phân khu",
     "Xem chênh lệch giá thuê giữa các khu."),
    ("/kinh-nghiem-thue-chung-cu-smart-city.html",
     "Kinh nghiệm thuê nhà",
     "Checklist xem nhà, cọc và hợp đồng."),
]

def esc(v):
    return html.escape("" if v is None else str(v), quote=True)

def chuan(v):
    return str("" if v is None else v).strip()

def khoa(v):
    return chuan(v).lower()

def so_tien(v):
    if isinstance(v, (int, float)):
        return int(v)
    return int(re.sub(r"[^\d]", "", str(v)) or 0)

def phan_khu_tu_toa(toa):
    t = re.sub(r"[\s._-]", "", chuan(toa)).upper()
    if not t:
        return ""
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
    if re.match(r"^I\d", t):
        return "Imperia"
    if re.match(r"^A\d", t):
        return "Lumiere"
    if re.match(r"^S\d", t):
        return "Sapphire"
    return ""

def la_public(r):
    v = khoa(r.get("Hiển thị trên Web") or r.get("Hiển thị trên web")
             or r.get("Hiển thị"))
    return v in ("có", "co", "yes", "true")

def khop(r, bo_loc):
    if not la_public(r):
        return False
    if bo_loc.get("loai") and khoa(r.get("Loại")) != khoa(bo_loc["loai"]):
        return False
    if bo_loc.get("phanKhu") and khoa(phan_khu_tu_toa(r.get("Tòa"))) != khoa(bo_loc["phanKhu"]):
        return False
    if bo_loc.get("noiThat") and khoa(r.get("Nội thất")) != khoa(bo_loc["noiThat"]):
        return False
    g = so_tien(r.get("Giá thuê"))
    if bo_loc.get("giaTren") and not g > int(bo_loc["giaTren"]):
        return False
    if bo_loc.get("giaMax") and not (g > 0 and g <= int(bo_loc["giaMax"])):
        return False
    return True

def tim_trang_danh_muc():
    ra = []
    bo_qua = {".git", ".github", "node_modules", "can-ho",
              "scripts", "images", "anh-can-ho"}
    for root, dirs, files in os.walk(GOC):
        dirs[:] = [d for d in dirs if d not in bo_qua]
        if "index.html" not in files:
            continue
        path = os.path.join(root, "index.html")
        with open(path, encoding="utf-8", errors="replace") as f:
            raw = f.read()
        m = RE_BO_LOC.search(raw)
        if not m:
            continue
        try:
            bo_loc = json.loads(m.group(1))
        except json.JSONDecodeError:
            print("CẢNH BÁO JSON bộ lọc:", os.path.relpath(path, GOC))
            continue
        slug = os.path.relpath(root, GOC).replace(os.sep, "/")
        ra.append((slug, path, raw, bo_loc))
    return sorted(ra)

def dem_theo_phan_khu(data, bo_loc):
    dem = collections.Counter()
    for r in data:
        if khop(r, bo_loc):
            pk = phan_khu_tu_toa(r.get("Tòa"))
            if pk in PHAN_KHU:
                dem[pk] += 1
    return dem

def dem_theo_loai(data, bo_loc):
    dem = collections.Counter()
    for r in data:
        if khop(r, bo_loc):
            l = khoa(r.get("Loại"))
            if l in LOAI:
                dem[l] += 1
    return dem

def top_keys(counter, thu_tu, n=4):
    thu = {k: i for i, k in enumerate(thu_tu)}
    ds = [k for k, c in counter.items() if c > 0]
    ds.sort(key=lambda k: (-counter[k], thu.get(k, 999), k))
    return ds[:n]

def link_card(href, title, desc=""):
    them = '<span>%s</span>' % esc(desc) if desc else ""
    return '<a href="%s"><strong>%s</strong>%s</a>' % (
        esc(href), esc(title), them)

def group(title, links):
    if not links:
        return ""
    return ('<div class="seo-graph-group"><h3>%s</h3>'
            '<div class="seo-graph-links">%s</div></div>') % (
                esc(title), "".join(links))

def tim_loai_theo_slug(slug):
    for key, info in LOAI.items():
        if info[0] == slug:
            return key, info
    return None

def dung_khoi(slug, bo_loc, data):
    loai_key = khoa(bo_loc.get("loai"))
    pk = chuan(bo_loc.get("phanKhu"))
    co_loc_sau = bool(bo_loc.get("giaMax") or bo_loc.get("giaTren")
                      or bo_loc.get("noiThat"))
    is_zone = bool(pk in PHAN_KHU and not loai_key and not co_loc_sau)
    is_type = bool(loai_key in LOAI and not pk and not co_loc_sau)
    is_long = slug in LONGTAIL or (loai_key in LOAI and not is_type)

    groups = []
    title = "Khám phá căn hộ liên quan"
    intro = ("Đi tiếp theo loại căn, phân khu và nhu cầu thuê mà không phải "
             "quay lại tìm từ đầu.")

    if is_zone:
        title = "Khám phá thêm tại %s" % PHAN_KHU[pk][1]
        dem_loai = dem_theo_loai(data, bo_loc)
        top_loai = top_keys(dem_loai, LOAI_THU_TU, 4)
        groups.append(group("Loại căn đang có", [
            link_card(LOAI[t][2], "Căn %s" % LOAI[t][1],
                      "%d căn loại này đang có tại %s." % (
                          dem_loai[t], PHAN_KHU[pk][1]))
            for t in top_loai
        ]))
        links = [
            link_card("/", "Toàn bộ căn đang trống",
                      "So sánh với các phân khu khác."),
            link_card("/can-ho/", "Trang chi tiết từng căn",
                      "Mở các URL căn hộ có ảnh và thông số riêng."),
        ]
        if pk in BAI_PHAN_KHU:
            href, label = BAI_PHAN_KHU[pk]
            links.append(link_card(href, label,
                                   "Đọc thông tin sâu về phân khu."))
        groups.append(group("Đi lên trong cụm", links))

    elif is_type:
        type_slug, type_label, _ = LOAI[loai_key]
        title = "Tìm %s theo nhu cầu" % type_label
        links = [
            link_card("/%s/" % s, label,
                      "Lọc sâu theo giá hoặc tình trạng nội thất.")
            for s, label in LONGTAIL_THEO_LOAI.get(type_slug, [])
        ]
        if not links:
            for t in LOAI_THU_TU:
                if t != loai_key:
                    links.append(link_card(
                        LOAI[t][2], "Căn %s" % LOAI[t][1],
                        "Xem thêm loại căn khác."))
                if len(links) >= 3:
                    break
        groups.append(group("Lọc sâu theo nhu cầu", links[:4]))

        dem_pk = dem_theo_phan_khu(data, bo_loc)
        top_pk = top_keys(dem_pk, PHAN_KHU_THU_TU, 4)
        groups.append(group("Phân khu có nhiều lựa chọn", [
            link_card(PHAN_KHU[z][0], PHAN_KHU[z][1],
                      "%d căn %s đang xuất hiện trong quỹ." % (
                          dem_pk[z], type_label))
            for z in top_pk
        ]))

    elif is_long:
        parent_slug = LONGTAIL.get(slug, ("", ""))[0]
        if not parent_slug and loai_key in LOAI:
            parent_slug = LOAI[loai_key][0]
        pinfo = tim_loai_theo_slug(parent_slug)
        if pinfo:
            _, (_, plabel, phref) = pinfo
            title = "Mở rộng tìm kiếm %s" % plabel
            links = [
                link_card(phref, "Tất cả căn %s" % plabel,
                          "Quay về trang loại căn cha.")
            ]
            for s, label in LONGTAIL_THEO_LOAI.get(parent_slug, []):
                if s != slug:
                    links.append(link_card(
                        "/%s/" % s, label,
                        "Nhu cầu gần với trang đang xem."))
            groups.append(group("Cùng loại căn", links[:4]))

        dem_pk = dem_theo_phan_khu(data, bo_loc)
        top_pk = top_keys(dem_pk, PHAN_KHU_THU_TU, 4)
        groups.append(group("Phân khu đang có lựa chọn", [
            link_card(PHAN_KHU[z][0], PHAN_KHU[z][1],
                      "%d căn khớp bộ lọc hiện tại." % dem_pk[z])
            for z in top_pk
        ]))

    groups.append(group("Thông tin trước khi thuê", [
        link_card(h, t, d) for h, t, d in GUIDE_LINKS
    ]))

    return (
        '%s\n<section class="seo-graph" aria-label="Liên kết nội bộ theo chủ đề">'
        '<div class="seo-graph-head"><span>Khám phá tiếp</span>'
        '<h2>%s</h2><p>%s</p></div>'
        '<div class="seo-graph-grid">%s</div></section>\n%s'
    ) % (MOC_DAU, esc(title), esc(intro), "".join(groups), MOC_CUOI)

def chen(raw, khoi):
    if RE_KHOI.search(raw):
        return RE_KHOI.sub(khoi, raw, count=1)

    raw, _ = RE_CU.subn("\n", raw, count=1)

    marker = '<a class="cta-home duoi"'
    i = raw.find(marker)
    if i >= 0:
        return raw[:i] + khoi + "\n\n  " + raw[i:]

    i = raw.rfind("</main>")
    if i >= 0:
        return raw[:i] + "\n  " + khoi + "\n\n" + raw[i:]
    return raw

def main():
    ap = argparse.ArgumentParser(
        description="Dựng internal links tĩnh cho các trang danh mục.")
    ap.add_argument("--thu", action="store_true",
                    help="chỉ in thống kê, không ghi file")
    args = ap.parse_args()

    with open(DUONG_DATA, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        print("LỖI: data.json rỗng hoặc không phải mảng.")
        return 1

    pages = tim_trang_danh_muc()
    print("Trang danh mục tìm thấy:", len(pages))
    changed = 0
    for slug, path, raw, bo_loc in pages:
        moi = chen(raw, dung_khoi(slug, bo_loc, data))
        rel = os.path.relpath(path, GOC)
        if moi == raw:
            print("= ", rel)
            continue
        changed += 1
        print("* ", rel)
        if not args.thu:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(moi)

    print("Thay đổi:", changed, "/", len(pages))
    if args.thu:
        print("(--thu) Không ghi file.")
    return 0

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sinh trang SEO giao nhau Phân khu × Loại căn từ data.json.

Chỉ mở index khi tổ hợp có >= NGUONG_INDEX căn đang public. URL đã từng sinh
không bị xóa: khi quỹ tụt dưới ngưỡng, trang vẫn trả 200 nhưng chuyển
noindex,follow và rời sitemap để tránh 404/thin content.

Chạy: python3 scripts/sinh-trang-giao-thoa.py [--thu]
"""

import argparse
import collections
import importlib.util
import json
import os
import re
import sys

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(GOC, "data.json")
REGISTRY = os.path.join(GOC, "seo-phan-khu-loai-can.json")
SITEMAP = os.path.join(GOC, "sitemap-phan-khu-loai-can.xml")
DETAIL_MAP = os.path.join(GOC, "can-ho", "danh-sach-trang.json")
TEN_MIEN = "https://timthuesmartcity.com"
NGUONG_INDEX = 4
NGUONG_DATA = 100
NGUONG_PUBLIC = 50
CSS_VERSION = "20260830-7"

ZONES = {
    "Sapphire": {"slug": "sapphire", "label": "Sapphire", "parent": "/sapphire/"},
    "Masteri": {"slug": "masteri", "label": "Masteri West Heights", "parent": "/masteri/"},
    "Miami": {"slug": "miami", "label": "The Miami", "parent": "/miami/"},
    "Sakura": {"slug": "sakura", "label": "The Sakura", "parent": "/sakura/"},
    "Imperia": {"slug": "imperia", "label": "Imperia Smart City", "parent": "/imperia/"},
    "Lumiere": {"slug": "lumiere", "label": "Lumière Evergreen", "parent": "/lumiere/"},
    "Canopy": {"slug": "canopy", "label": "The Canopy", "parent": "/canopy/"},
    "Tonkin": {"slug": "tonkin", "label": "The Tonkin", "parent": "/tonkin/"},
}
TYPES = {
    "Studio": {"slug": "studio", "label": "Studio", "short": "Studio", "parent": "/studio/"},
    "1 Ngủ": {"slug": "1pn", "label": "1 phòng ngủ", "short": "1PN", "parent": "/1pn/"},
    "1 Ngủ +": {"slug": "1pn-plus", "label": "1 phòng ngủ +", "short": "1PN+", "parent": "/1pn-plus/"},
    "2 Ngủ": {"slug": "2pn", "label": "2 phòng ngủ", "short": "2PN", "parent": "/2pn/"},
    "2 Ngủ +": {"slug": "2pn-plus", "label": "2 phòng ngủ +", "short": "2PN+", "parent": "/2pn-plus/"},
    "3 Ngủ": {"slug": "3pn", "label": "3 phòng ngủ", "short": "3PN", "parent": "/3pn/"},
}

def nap_module(ten, file_name):
    path = os.path.join(SCRIPTS, file_name)
    spec = importlib.util.spec_from_file_location(ten, path)
    mod = importlib.util.module_from_spec(spec)
    cu = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = cu
    return mod

DM = nap_module("dung_lai_danh_muc", "dung-lai-trang-danh-muc.py")
STT = DM.STT
esc = STT.esc
so_tien = STT.so_tien
dien_tich = STT.dien_tich
dinh_dang_gia = STT.dinh_dang_gia
khoang_gia = STT.khoang_gia
phan_khu_tu_toa = STT.phan_khu_tu_toa
ngay_hom_nay = STT.ngay_hom_nay
doc_map_anh = STT.doc_map_anh
doc_khoi_nap = STT.doc_khoi_nap

def public_row(r):
    return DM.la_can_hop_le(r) and bool(DM.chuan(r.get("Mã nội bộ")))

def slug_combo(pk, loai):
    return "cho-thue-%s-%s-smart-city" % (TYPES[loai]["slug"], ZONES[pk]["slug"])

def doc_json(path, fallback):
    if not os.path.exists(path):
        return fallback
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback

def detail_reverse():
    raw = doc_json(DETAIL_MAP, {})
    ra = {}
    for slug, rec in raw.items():
        ma = str((rec or {}).get("ma", "")).strip()
        if ma:
            ra[ma] = slug
    return ra

def stats(ds):
    gia = [so_tien(r.get("Giá thuê")) for r in ds if so_tien(r.get("Giá thuê")) > 0]
    dt = [dien_tich(r.get("Diện tích")) for r in ds if dien_tich(r.get("Diện tích")) > 0]
    towers = collections.Counter(str(r.get("Tòa", "")).strip() for r in ds if str(r.get("Tòa", "")).strip())
    interiors = collections.Counter(str(r.get("Nội thất", "")).strip() for r in ds if str(r.get("Nội thất", "")).strip())
    return {
        "n": len(ds),
        "gia_min": min(gia) if gia else 0,
        "gia_max": max(gia) if gia else 0,
        "dt_min": round(min(dt)) if dt else 0,
        "dt_max": round(max(dt)) if dt else 0,
        "towers": towers,
        "interiors": interiors,
    }

def item_list(ds, detail_map):
    items = []
    for i, r in enumerate(ds, 1):
        ma = str(r.get("Mã nội bộ", "")).strip()
        slug = detail_map.get(ma)
        if not slug:
            continue
        dt = round(dien_tich(r.get("Diện tích")))
        g = dinh_dang_gia(so_tien(r.get("Giá thuê")))
        items.append({
            "@type": "ListItem",
            "position": i,
            "name": "%s %s %sm² – %s/tháng" % (
                str(r.get("Loại", "")).strip(), str(r.get("Tòa", "")).strip(), dt, g),
            "url": TEN_MIEN + "/can-ho/" + slug + "/",
        })
    return items

def tower_text(towers):
    if not towers:
        return "chưa ghi nhận tòa trong dữ liệu"
    parts = ["%s (%d căn)" % (t, n) for t, n in towers.most_common()]
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " và " + parts[-1]

def interior_text(interiors):
    if not interiors:
        return "tình trạng nội thất đang được cập nhật"
    parts = ["%s: %d căn" % (t, n) for t, n in interiors.most_common()]
    return "; ".join(parts)

def render_page(pk, loai, ds, indexable, detail_map, ngay):
    z = ZONES[pk]
    t = TYPES[loai]
    st = stats(ds)
    slug = slug_combo(pk, loai)
    url = TEN_MIEN + "/" + slug + "/"
    gia_txt = khoang_gia(st["gia_min"], st["gia_max"]) if st["gia_min"] else "Liên hệ"
    dt_txt = ("%d–%d m²" % (st["dt_min"], st["dt_max"])) if st["dt_min"] and st["dt_min"] != st["dt_max"] else ("%d m²" % st["dt_min"] if st["dt_min"] else "Đang cập nhật")
    title = "Cho thuê %s %s Smart City – %d căn" % (t["short"], z["label"], st["n"])
    if st["gia_min"] and st["gia_max"]:
        gia_desc = ("%s–%s" % (dinh_dang_gia(st["gia_min"]), dinh_dang_gia(st["gia_max"]))
                    if st["gia_min"] != st["gia_max"] else dinh_dang_gia(st["gia_min"]))
    else:
        gia_desc = "Liên hệ"
    desc = ("Danh sách %d căn %s cho thuê tại %s, Vinhomes Smart City, giá %s/tháng, "
            "diện tích %s. Ảnh và thông số từng căn, cập nhật %s."
            % (st["n"], t["label"], z["label"], gia_desc, dt_txt, ngay.strftime("%d/%m/%Y")))
    robots = "index,follow" if indexable else "noindex,follow"
    notice = ""
    if not indexable:
        notice = ('<section class="bai combo-thin-note"><p><strong>Quỹ căn hiện đang ít.</strong> '
                  'Trang được giữ lại để không làm đứt URL cũ; mời xem trang phân khu hoặc loại căn để có thêm lựa chọn.</p></section>')

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": TEN_MIEN + "/"},
            {"@type": "ListItem", "position": 2, "name": z["label"], "item": TEN_MIEN + z["parent"]},
            {"@type": "ListItem", "position": 3, "name": "Cho thuê %s %s" % (t["label"], z["label"]), "item": url},
        ],
    }
    listing = {
        "@type": "ItemList",
        "name": "Căn %s cho thuê tại %s" % (t["label"], z["label"]),
        "numberOfItems": st["n"],
        "itemListElement": item_list(ds, detail_map),
    }
    graph = {"@context": "https://schema.org", "@graph": [breadcrumb, listing]}
    cards = "\n".join(DM.dung_the(r, MAP_ANH, HOM_NAY) for r in ds)
    # Bảng một dòng cố định theo loại căn để dung-lai-trang-danh-muc.py tiếp tục cập nhật an toàn.
    table = ('<table class="bang"><thead><tr><th>Loại căn</th><th>Số căn trống</th><th>Khoảng giá/tháng</th></tr></thead>'
             '<tbody><tr><td>%s</td><td>%d</td><td>%s</td></tr></tbody></table>'
             % (esc(loai), st["n"], esc(gia_txt)))

    html = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<!-- Trang sinh tự động bởi scripts/sinh-trang-giao-thoa.py -->
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<meta name="robots" content="%(robots)s">
<link rel="canonical" href="%(url)s">
<link rel="icon" href="/favicon.ico" sizes="any">
<meta property="og:type" content="website">
<meta property="og:url" content="%(url)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:image" content="https://timthuesmartcity.com/og-smartcity.jpg">
<meta property="og:site_name" content="Tìm Thuê Smart City">
<meta property="og:locale" content="vi_VN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title)s">
<meta name="twitter:description" content="%(desc)s">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-VF9KHC5TWD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-VF9KHC5TWD');</script>
<script type="application/ld+json">%(graph)s</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Be+Vietnam+Pro:wght@300;400;500;600&display=swap" media="print" onload="this.media='all'">
<noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Be+Vietnam+Pro:wght@300;400;500;600&display=swap"></noscript>
<link rel="stylesheet" href="/assets/v3.css?v=%(css_version)s">
</head>
<body>
<header class="top"><div class="khung">
<a class="hieu" href="/">Cho thuê chung cư Smart City<small>Ảnh thật · Cập nhật mỗi ngày</small></a>
<nav><a href="/">Tất cả căn</a><a href="/studio/">Studio</a><a href="/1pn-plus/">1 ngủ +</a><a href="/2pn/">2 ngủ</a><a href="/3pn/">3 ngủ</a><a href="/cam-nang-thue-nha.html">Cẩm nang</a></nav>
</div></header>

<main class="khung">
<p class="bc"><a href="/">Trang chủ</a> › <a href="%(zone_parent)s">%(zone)s</a> › <span>%(type_label)s</span></p>
<h1>Cho thuê căn hộ %(type_label)s %(zone)s Smart City</h1>
<p class="tt">Danh sách %(n)d căn %(type_label)s tại %(zone)s, giá %(gia)s/tháng, diện tích %(dt)s. Ảnh thật và thông số từng căn, cập nhật %(ngay)s.</p>

<div class="sl">
  <div class="o"><b>%(n)d</b><span>căn đang trống</span></div>
  <div class="o"><b>%(gia_min)s</b><span>giá thấp nhất</span></div>
  <div class="o"><b>%(dt)s</b><span>diện tích</span></div>
  <div class="o"><b>%(tower_count)d</b><span>tòa đang có</span></div>
</div>

%(notice)s

<h2 class="tieu-de-luoi">Danh sách %(n)d căn đang cho thuê</h2>
<section class="luoi">
%(cards)s
</section>

<a class="cta-loc" href="/?pk=%(zone_slug)s&loai=%(type_slug)s">Mở bộ lọc toàn quỹ căn
  <small>So sánh thêm giá, nội thất và các lựa chọn khác trong Smart City</small></a>

<section class="bai">
  <h2>Giá thuê %(type_label)s tại %(zone)s hiện nay</h2>
  <p>Dữ liệu đang hiển thị có <strong><span data-so="can">%(n)d</span> căn</strong>, giá từ <strong><span data-so="gia-min">%(gia_min_num)s</span> triệu–<span data-so="gia-max">%(gia_max_num)s</span> triệu/tháng</strong> và diện tích <span data-so="dt-min">%(dt_min)d</span>–<span data-so="dt-max">%(dt_max)d</span>m². Đây là số liệu lấy trực tiếp từ quỹ căn public trên website tại thời điểm %(ngay)s.</p>
  <p>Các tòa đang có căn: %(tower_text)s. Tình trạng nội thất trong quỹ hiện tại: %(interior_text)s.</p>
  <h3>Cách mở rộng tìm kiếm</h3>
  <p>Nếu chưa thấy căn phù hợp, anh/chị có thể xem toàn bộ <a href="%(zone_parent)s">căn đang cho thuê tại %(zone)s</a> hoặc mở trang <a href="%(type_parent)s">%(type_label)s toàn Vinhomes Smart City</a> để so sánh thêm các phân khu khác.</p>
  <h3>Bảng giá quỹ căn đang trống</h3>
  %(table)s
  <p style="font-size:13px;color:var(--gray-lt)">Số liệu được dựng lại từ data.json; căn tắt “Hiển thị trên Web” sẽ rời danh sách ở lần đồng bộ tiếp theo.</p>
</section>

<a class="cta-home duoi" href="%(zone_parent)s">Xem toàn bộ căn tại %(zone)s
  <small>Không giới hạn riêng %(type_label)s</small></a>
</main>

<footer class="chan">
%(nap)s
<div class="khung"><p>Cập nhật %(ngay)s · <a href="/">Tìm căn hộ</a> · <a href="/bang-gia-thue-vinhomes-smart-city.html">Bảng giá thuê</a> · <a href="/cam-nang-thue-nha.html">Cẩm nang thuê nhà</a> · <a href="/gui-thue/">Chủ nhà gửi căn</a></p></div>
</footer>
<a class="zalo-noi" href="https://zalo.me/%(sdt)s" target="_blank" rel="noopener">Nhắn Zalo tư vấn</a>
<script type="application/json" id="bo-loc-trang">%(filter_json)s</script>
<script src="/dong-bo-can.js?v=20260830-7" defer></script>
<script src="/assets/app-shell.js?v=20260830-7" defer></script>
</body>
</html>
""" % {
        "title": esc(title), "desc": esc(desc), "robots": robots, "url": esc(url),
        "graph": json.dumps(graph, ensure_ascii=False).replace("</", "<\\/"),
        "css_version": CSS_VERSION,
        "zone_parent": esc(z["parent"]), "zone": esc(z["label"]), "zone_slug": esc(z["slug"]),
        "type_label": esc(t["label"]), "type_parent": esc(t["parent"]), "type_slug": esc(t["slug"]),
        "n": st["n"], "gia": esc(gia_txt), "gia_min": esc(dinh_dang_gia(st["gia_min"]) if st["gia_min"] else "Liên hệ"),
        "gia_min_num": esc(dinh_dang_gia(st["gia_min"]).replace(" triệu", "") if st["gia_min"] else "0"),
        "gia_max_num": esc(dinh_dang_gia(st["gia_max"]).replace(" triệu", "") if st["gia_max"] else "0"),
        "dt_min": st["dt_min"], "dt_max": st["dt_max"],
        "dt": esc(dt_txt), "tower_count": len(st["towers"]), "notice": notice,
        "cards": cards, "ngay": ngay.strftime("%d/%m/%Y"),
        "tower_text": esc(tower_text(st["towers"])), "interior_text": esc(interior_text(st["interiors"])),
        "table": table, "nap": doc_khoi_nap(), "sdt": STT.SDT,
        "filter_json": json.dumps({"phanKhu": pk, "loai": loai}, ensure_ascii=False).replace("</", "<\\/"),
    }
    return html

def sitemap_xml(indexable_slugs, ngay):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for slug in sorted(indexable_slugs):
        lines.append('  <url><loc>%s/%s/</loc><lastmod>%s</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>'
                     % (TEN_MIEN, slug, ngay.isoformat()))
    lines.append('</urlset>')
    return "\n".join(lines) + "\n"

def main():
    global MAP_ANH, HOM_NAY
    ap = argparse.ArgumentParser()
    ap.add_argument("--thu", action="store_true", help="chỉ xem trước")
    args = ap.parse_args()

    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or len(data) < NGUONG_DATA:
        print("DỪNG AN TOÀN: data.json quá nhỏ; không ghi gì.")
        return 2

    public = [r for r in data if public_row(r)]
    if len(public) < NGUONG_PUBLIC:
        print("DỪNG AN TOÀN: chỉ %d căn public; không ghi gì." % len(public))
        return 2

    MAP_ANH = doc_map_anh()
    HOM_NAY = ngay_hom_nay()
    detail_map = detail_reverse()

    registry = doc_json(REGISTRY, {})
    if not isinstance(registry, dict):
        registry = {}

    counts = collections.Counter()
    for r in public:
        pk = phan_khu_tu_toa(r.get("Tòa", ""))
        loai = str(r.get("Loại", "")).strip()
        if pk in ZONES and loai in TYPES:
            counts[(pk, loai)] += 1

    # Tổ hợp đủ ngưỡng mới được cấp URL lần đầu.
    for (pk, loai), n in counts.items():
        if n < NGUONG_INDEX:
            continue
        slug = slug_combo(pk, loai)
        if slug not in registry:
            registry[slug] = {
                "phanKhu": pk, "loai": loai,
                "created": HOM_NAY.isoformat(),
            }

    indexable = []
    changed = 0
    for slug in sorted(registry):
        rec = registry[slug]
        pk = rec.get("phanKhu")
        loai = rec.get("loai")
        if pk not in ZONES or loai not in TYPES:
            print("BỎ QUA registry lỗi:", slug)
            continue
        bl = {"phanKhu": pk, "loai": loai}
        ds = DM.ds_can_len_luoi(data, bl, MAP_ANH)
        ok = len(ds) >= NGUONG_INDEX
        rec["count"] = len(ds)
        rec["indexable"] = ok
        rec["updated"] = HOM_NAY.isoformat()
        if ok:
            indexable.append(slug)
        print("%-48s %3d căn  %s" % (slug, len(ds), "INDEX" if ok else "NOINDEX"))
        if args.thu:
            continue
        folder = os.path.join(GOC, slug)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, "index.html")
        html = render_page(pk, loai, ds, ok, detail_map, HOM_NAY)
        old = ""
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                old = f.read()
        if old != html:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(html)
            changed += 1

    if not args.thu:
        with open(REGISTRY, "w", encoding="utf-8", newline="") as f:
            json.dump(registry, f, ensure_ascii=False, indent=2, sort_keys=True)
            f.write("\n")
        with open(SITEMAP, "w", encoding="utf-8", newline="") as f:
            f.write(sitemap_xml(indexable, HOM_NAY))

    print("\nRegistry: %d URL · indexable: %d · HTML thay đổi: %d%s" % (
        len(registry), len(indexable), changed,
        " (--thu, không ghi)" if args.thu else ""))
    return 0

if __name__ == "__main__":
    sys.exit(main())
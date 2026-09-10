#!/usr/bin/env python3
"""Mở rộng cụm landing SEO theo tòa mà không phá URL đã có.

Nguyên tắc:
- 15 URL tòa cũ trong sinh-trang-toa.py luôn được giữ nguyên slug.
- Tòa mới chỉ được cấp URL khi có >= 3 căn đang hiển thị, tránh index trang mỏng.
- URL đã từng được cấp được giữ ổn định về sau. Nếu còn 1-2 căn vẫn cập nhật
  trang bằng dữ liệu thật; nếu về 0 căn thì chuyển sang trang 200 + noindex,follow
  thay vì giữ số liệu cũ hoặc tạo 404.
- Sinh sitemap-toa.xml riêng và seo-toa.json làm sổ đăng ký URL tòa.

Chạy: python3 scripts/mo-rong-trang-toa.py [--thu]
"""

import argparse
import html
import importlib.util
import json
import os
import re
import sys
import unicodedata

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(GOC, "data.json")
REGISTRY = os.path.join(GOC, "seo-toa.json")
SITEMAP = os.path.join(GOC, "sitemap-toa.xml")
DOMAIN = "https://timthuesmartcity.com"
MIN_NEW = 3


def nap_module():
    if SCRIPTS not in sys.path:
        sys.path.insert(0, SCRIPTS)
    path = os.path.join(SCRIPTS, "sinh-trang-toa.py")
    spec = importlib.util.spec_from_file_location("sinh_trang_toa_core", path)
    mod = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = old
    return mod


CORE = nap_module()


def esc(v):
    return html.escape("" if v is None else str(v), quote=True)


def slugify(v):
    s = unicodedata.normalize("NFD", str(v))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.lower().replace("đ", "d")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def doc_registry():
    if not os.path.exists(REGISTRY):
        return {"version": 2, "towers": {}}
    try:
        obj = json.load(open(REGISTRY, encoding="utf-8"))
        if not isinstance(obj, dict):
            raise ValueError("registry không phải object")
        if not isinstance(obj.get("towers"), dict):
            obj["towers"] = {}
        obj["version"] = 2
        return obj
    except Exception as e:
        print("CẢNH BÁO: không đọc được seo-toa.json (%s), dựng registry mới." % e)
        return {"version": 2, "towers": {}}


def hien_thi_va_slug(ma_goc, phan_khu):
    n = CORE.chuan_ma_toa(ma_goc)
    if phan_khu == "Masteri" and re.fullmatch(r"MAS[A-Z]", n):
        letter = n[-1]
        return "West %s Masteri" % letter, "/west-%s-masteri-smart-city/" % letter.lower()
    if phan_khu == "Lumiere" and re.fullmatch(r"A\d+", n):
        return "%s Lumière" % n, "/%s-lumiere-evergreen/" % n.lower()
    if phan_khu == "Miami" and re.fullmatch(r"GS\d+", n):
        return "%s The Miami" % n, "/%s-the-miami-smart-city/" % n.lower()
    if phan_khu == "Sakura" and re.fullmatch(r"SA\d+", n):
        return "%s The Sakura" % n, "/%s-the-sakura-smart-city/" % n.lower()
    if phan_khu == "Canopy" and re.fullmatch(r"TC\d+", n):
        return "%s The Canopy" % n, "/%s-canopy-smart-city/" % n.lower()
    if phan_khu == "Imperia" and re.fullmatch(r"I\d+", n):
        return "%s Imperia" % n, "/%s-imperia-smart-city/" % n.lower()
    if phan_khu == "Sapphire":
        m = re.fullmatch(r"S(\d)(\d{2})", n)
        if m:
            display = "S%s.%s" % (m.group(1), m.group(2))
            return display, "/s%s-%s-vinhomes-smart-city/" % (m.group(1), m.group(2))
    display = "%s %s" % (str(ma_goc).strip(), phan_khu)
    return display.strip(), "/%s-smart-city/" % slugify(display)


def gom_theo_toa(data):
    groups = {}
    raw = {}
    for c in data:
        if not CORE.dang_hien_thi(c):
            continue
        ma = str(c.get("Tòa", "")).strip()
        if not ma:
            continue
        norm = CORE.chuan_ma_toa(ma)
        if not norm:
            continue
        groups.setdefault(norm, []).append(c)
        raw.setdefault(norm, ma)
    return groups, raw


def config_cu_theo_norm():
    out = {}
    for _, cfg in CORE.CAC_TOA.items():
        n = CORE.chuan_ma_toa(cfg["ma_toa_data"])
        out[n] = dict(cfg)
    return out


def dinh_dang_registry_entry(norm, cfg, phan_khu, cac_can, today, first_seen):
    tk = CORE.thong_ke(cac_can) if cac_can else {
        "so_can": 0, "gia_min": 0, "gia_max": 0, "dt_min": 0, "dt_max": 0,
        "theo_loai": [], "theo_noi_that": [], "full_noi_that": 0,
    }
    return {
        "code": norm,
        "data_code": cfg["ma_toa_data"],
        "name": cfg["ten_hien_thi"],
        "path": cfg["duong_dan"],
        "district": phan_khu,
        "count": len(cac_can),
        "price_min": tk["gia_min"],
        "price_max": tk["gia_max"],
        "area_min": tk["dt_min"],
        "area_max": tk["dt_max"],
        "types": [
            {"name": loai, "count": muc["so_can"],
             "price_min": min(muc["gia"]) if muc["gia"] else 0,
             "price_max": max(muc["gia"]) if muc["gia"] else 0}
            for loai, muc in tk["theo_loai"]
        ],
        "first_seen": first_seen or today.isoformat(),
        "last_seen": today.isoformat() if cac_can else None,
        "indexable": bool(cac_can),
    }


def placeholder_het_can(entry, today):
    name = entry["name"]
    path = entry["path"]
    pk = entry.get("district") or "Vinhomes Smart City"
    parent = CORE.TRANG_PHAN_KHU.get(pk, "/")
    url = DOMAIN + path
    title = "Tòa %s hiện chưa có căn trống | Vinhomes Smart City" % name
    desc = ("Tòa %s hiện chưa có căn cho thuê đang xác nhận. Xem quỹ căn còn trống "
            "tại %s và các tòa lân cận trong Vinhomes Smart City." % (name, pk))
    breadcrumb = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": DOMAIN + "/"},
            {"@type": "ListItem", "position": 2, "name": "Cho thuê căn hộ %s" % pk,
             "item": DOMAIN + parent},
            {"@type": "ListItem", "position": 3, "name": "Tòa %s" % name, "item": url},
        ],
    }, ensure_ascii=False)
    return """<!doctype html>
<html lang="vi"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<meta name="robots" content="noindex,follow,max-image-preview:large">
<link rel="canonical" href="%(url)s">
<meta property="og:type" content="website"><meta property="og:url" content="%(url)s">
<meta property="og:title" content="%(title)s"><meta property="og:description" content="%(desc)s">
<meta property="og:image" content="%(domain)s/og-smartcity.jpg"><meta property="og:site_name" content="Tìm Thuê Smart City">
<script type="application/ld+json">%(breadcrumb)s</script>
<link rel="stylesheet" href="/assets/v3.css?v=20260830-6">
</head><body>
<header class="top"><div class="khung"><a class="hieu" href="/">Cho thuê chung cư Smart City<small>Ảnh thật · Cập nhật mỗi ngày</small></a></div></header>
<main class="khung">
<p class="bc"><a href="/">Trang chủ</a> › <a href="%(parent)s">%(pk)s</a> › <span>Tòa %(name)s</span></p>
<h1>Tòa %(name)s hiện chưa có căn trống</h1>
<section class="bai"><p>Dữ liệu quỹ căn vừa được đối chiếu ngày %(date)s. Hiện chưa có căn tại tòa %(name)s đủ điều kiện hiển thị.</p>
<p>URL này được giữ lại để không làm gãy liên kết cũ. Khi có căn mới, trang sẽ tự chuyển lại trạng thái có thể lập chỉ mục và hiển thị quỹ căn mới nhất.</p></section>
<div class="lq"><a href="%(parent)s">Xem căn tại %(pk)s</a><a href="/can-ho/">Xem toàn bộ căn đang trống</a><a href="/bang-gia-thue-vinhomes-smart-city.html">Bảng giá thuê Smart City</a></div>
</main>
<script src="/assets/app-shell.js?v=20260901-1" defer></script>
</body></html>""" % {
        "title": esc(title), "desc": esc(desc), "url": esc(url), "domain": DOMAIN,
        "breadcrumb": breadcrumb, "parent": esc(parent), "pk": esc(pk),
        "name": esc(name), "date": today.strftime("%d/%m/%Y"),
    }


def ghi_file(path, content, dry):
    rel = os.path.relpath(path, GOC)
    if dry:
        print("(--thu) sẽ ghi %s" % rel)
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(content)


def tao_sitemap(entries, today):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for e in sorted(entries, key=lambda x: x["path"]):
        if not e.get("indexable") or e.get("count", 0) < 1:
            continue
        lines.append('  <url><loc>%s%s</loc><lastmod>%s</lastmod><changefreq>daily</changefreq><priority>0.85</priority></url>'
                     % (DOMAIN, e["path"], today.isoformat()))
    lines.append('</urlset>')
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thu", action="store_true", help="chỉ xem trước")
    args = ap.parse_args()
    data = json.load(open(DATA, encoding="utf-8"))
    if not isinstance(data, list) or len(data) < 20:
        print("DỪNG AN TOÀN: data.json bất thường (%s bản ghi)." % (len(data) if isinstance(data, list) else "không phải mảng"))
        return 2
    today = CORE.ngay_hom_nay()
    groups, raw_codes = gom_theo_toa(data)
    old = doc_registry()
    old_towers = old.get("towers", {})
    configs = config_cu_theo_norm()
    for norm, e in old_towers.items():
        if norm in configs:
            continue
        if e.get("path") and e.get("name"):
            configs[norm] = {"ma_toa_data": e.get("data_code") or norm, "duong_dan": e["path"], "ten_hien_thi": e["name"]}
    for norm, cans in groups.items():
        if norm in configs or len(cans) < MIN_NEW:
            continue
        raw = raw_codes[norm]
        pk = CORE.phan_khu_tu_toa(raw)
        if pk not in CORE.TRANG_PHAN_KHU:
            print("Bỏ qua tòa mới %s: chưa có landing phân khu %r." % (raw, pk))
            continue
        display, path = hien_thi_va_slug(raw, pk)
        if any(c.get("duong_dan") == path for c in configs.values()):
            print("CẢNH BÁO slug trùng %s — bỏ qua %s." % (path, raw))
            continue
        configs[norm] = {"ma_toa_data": raw, "duong_dan": path, "ten_hien_thi": display}
        print("MỞ URL TÒA MỚI: %s -> %s (%d căn)" % (display, path, len(cans)))
    map_anh = CORE.doc_map_anh()
    registry = {"version": 2, "towers": {}}
    entries = []
    for norm in sorted(configs):
        cfg = configs[norm]
        cans = list(groups.get(norm, []))
        pk = CORE.phan_khu_tu_toa(cfg["ma_toa_data"])
        old_e = old_towers.get(norm, {})
        entry = dinh_dang_registry_entry(norm, cfg, pk, cans, today, old_e.get("first_seen"))
        registry["towers"][norm] = entry
        entries.append(entry)
        out = os.path.join(GOC, cfg["duong_dan"].strip("/"), "index.html")
        if cans:
            cans.sort(key=lambda c: (CORE.so_tien(c.get("Giá thuê")), CORE.dien_tich(c.get("Diện tích")), str(c.get("Mã nội bộ", ""))))
            tk = CORE.thong_ke(cans)
            page = CORE.dung_trang(cfg["ten_hien_thi"], cfg, cans, tk, map_anh, today)
            ghi_file(out, page, args.thu)
            print("OK %-28s %2d căn -> %s" % (cfg["ten_hien_thi"], len(cans), cfg["duong_dan"]))
        else:
            entry["indexable"] = False
            ghi_file(out, placeholder_het_can(entry, today), args.thu)
            print("NOINDEX %-23s  0 căn -> giữ URL 200" % cfg["ten_hien_thi"])
    reg_text = json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    sitemap_text = tao_sitemap(entries, today)
    if args.thu:
        print("(--thu) sẽ ghi seo-toa.json và sitemap-toa.xml")
    else:
        with open(REGISTRY, "w", encoding="utf-8", newline="") as f:
            f.write(reg_text)
        with open(SITEMAP, "w", encoding="utf-8", newline="") as f:
            f.write(sitemap_text)
    active = sum(1 for e in entries if e["indexable"])
    print("Tổng registry: %d tòa · indexable: %d · URL mới cần >= %d căn." % (len(entries), active, MIN_NEW))
    return 0


if __name__ == "__main__":
    sys.exit(main())

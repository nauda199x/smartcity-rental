#!/usr/bin/env python3
import json
import os
import re
import shutil
import sys
import unicodedata
from html import escape
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data-lumi.json"
BASE = ROOT / "lumi-hanoi" / "can-ho"
REGISTRY = BASE / "danh-sach-trang.json"
SITEMAP = ROOT / "sitemap-lumi.xml"
DOMAIN = "https://timthuesmartcity.com"
ZALO = "0977923284"
FALLBACK_OG = "https://www.capitaland.com/vn/en/stay/residential-development-listing/lumi-hanoi/_jcr_content/root/container/container/entitydetails.coreimg.jpeg/content/dam/capitaland-media-library/residential/Vietnam/Hanoi/lumi-hanoi/Lumi%20Hanoi_Overall%20Facade%20%28D%29_Final.jpg"


def txt(v):
    return str(v or "").strip()


def key(v):
    return txt(v).lower()


def slug(v):
    s = unicodedata.normalize("NFD", txt(v))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def number(v):
    if isinstance(v, (int, float)):
        return float(v)
    s = txt(v).replace(",", ".")
    s = re.sub(r"[^\d.]", "", s)
    try:
        return float(s)
    except ValueError:
        return 0.0


def money(v):
    if isinstance(v, (int, float)):
        return int(v)
    s = re.sub(r"[^\d]", "", txt(v))
    return int(s or 0)


def price(v):
    p = money(v)
    if not p:
        return "Liên hệ"
    m = p / 1_000_000
    if m.is_integer():
        return "%d triệu" % int(m)
    return ("%.1f triệu" % m).replace(".", ",")


def active(row):
    return key(row.get("Hiển thị trên Web")) == "có"


def images(row):
    values = [txt(row.get("Ảnh đại diện"))]
    values += [x.strip() for x in txt(row.get("Danh sách ảnh")).splitlines()]
    out = []
    for u in values:
        if u and u not in out:
            out.append(u)
    return out


def available(row):
    s = txt(row.get("Ngày vào ở"))
    if not s or key(s) in ("vào luôn", "vào ngay", "ở ngay", "ngay"):
        return "Vào ngay"
    if "chưa xác nhận" in key(s):
        return "Liên hệ ngày vào"
    return s


def iso_date(s):
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", txt(s))
    if not m:
        return ""
    return "%s-%02d-%02d" % (m.group(3), int(m.group(2)), int(m.group(1)))


def proposed_slug(row):
    return "cho-thue-can-ho-%s-%s-%dm2-%s" % (
        slug(row.get("Loại")), slug(row.get("Tòa")),
        round(number(row.get("Diện tích"))), slug(row.get("Mã căn"))
    )


def read_registry():
    if not REGISTRY.exists():
        return {}
    try:
        value = json.loads(REGISTRY.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def json_safe(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def h(v):
    return escape(txt(v), quote=True)


def detail_html(row, page_slug, similar, slug_by_id):
    is_active = active(row)
    typ = txt(row.get("Loại")) or "Căn hộ"
    tower = txt(row.get("Tòa"))
    code = txt(row.get("Mã căn"))
    area = number(row.get("Diện tích"))
    area_text = ("%g" % area).replace(".", ",")
    p = money(row.get("Giá thuê"))
    interior = txt(row.get("Nội thất")) or "Đang cập nhật"
    direction = txt(row.get("Hướng ban công")) or "Đang cập nhật"
    move = available(row)
    updated = txt(row.get("Ngày cập nhật")) or txt(row.get("Ngày thêm vào hệ thống"))
    imgs = images(row)
    url = DOMAIN + "/lumi-hanoi/can-ho/" + page_slug + "/"

    if is_active:
        title = "Cho thuê căn hộ %s %s Lumi Hanoi %sm² – %s/tháng" % (typ, tower, area_text, price(p))
        description = ("Cho thuê căn hộ %s tòa %s Lumi Hanoi, diện tích %sm², %s, giá %s/tháng. %s%s." %
                       (typ, tower, area_text, interior.lower(), price(p), move,
                        (". Cập nhật " + updated) if updated else ""))
    else:
        title = "Căn hộ %s %s %sm² hiện không còn trong quỹ – Lumi Hanoi" % (typ, tower, area_text)
        description = ("Căn hộ %s tòa %s Lumi Hanoi hiện không còn trong quỹ công khai. "
                       "Xem các căn Lumi Hanoi còn trống tương tự." % (typ, tower))

    og = imgs[0] if imgs else FALLBACK_OG
    breadcrumb = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Trang chủ", "item": DOMAIN + "/"},
            {"@type": "ListItem", "position": 2, "name": "Cho thuê căn hộ Lumi Hanoi",
             "item": DOMAIN + "/lumi-hanoi/"},
            {"@type": "ListItem", "position": 3, "name": "%s %s %sm²" % (typ, tower, area_text),
             "item": url},
        ],
    }
    listing = {
        "@context": "https://schema.org", "@type": "RealEstateListing",
        "name": "%s %s %sm² Lumi Hanoi" % (typ, tower, area_text),
        "url": url, "identifier": code,
        "about": {
            "@type": "Apartment", "name": "%s %s" % (typ, tower),
            "floorSize": {"@type": "QuantitativeValue", "value": area, "unitCode": "MTK"},
            "address": {"@type": "PostalAddress", "streetAddress": "Lumi Hanoi",
                        "addressRegion": "Hà Nội", "addressCountry": "VN"},
        },
    }
    if is_active and p > 0:
        listing["offers"] = {"@type": "Offer", "price": p, "priceCurrency": "VND",
                             "availability": "https://schema.org/InStock"}
        iso = iso_date(row.get("Ngày vào ở"))
        if iso:
            listing["offers"]["availabilityStarts"] = iso

    if imgs:
        gallery = '<section class="gallery">\n'
        for i, u in enumerate(imgs):
            gallery += ('    <img src="%s" alt="Ảnh %d căn hộ %s %s Lumi Hanoi %sm²" '
                        'loading="%s" decoding="async" width="800" height="600">\n' %
                        (h(u), i + 1, h(typ), h(tower), h(area_text), "eager" if i == 0 else "lazy"))
        gallery += "  </section>"
    else:
        gallery = ('<section class="gallery ct-gallery-empty-source">\n'
                   '    <div class="ct-no-photo"><b>Căn này đang cập nhật ảnh</b>'
                   '<span>Nhắn Zalo để nhận ảnh và video thực tế.</span></div>\n'
                   '  </section>')

    if is_active:
        body_top = (
            '<h1>Cho thuê căn hộ %s %sm² tòa %s – Lumi Hanoi</h1>\n'
            '  <p class="tt">Căn hộ %s diện tích %sm² tại tòa %s, Lumi Hanoi. %s. '
            'Giá thuê %s/tháng. %s%s.</p>\n'
            '  <p class="ct-identity-note">Mã căn %s: %s; %s m²; tòa %s; %s; '
            'giá %s/tháng; %s.</p>' %
            (h(typ), h(area_text), h(tower), h(typ), h(area_text), h(tower), h(interior),
             h(price(p)), h(move), (". Cập nhật " + h(updated)) if updated else "",
             h(code), h(typ), h(area_text), h(tower), h(interior), h(price(p)), h(move.lower()))
        )
    else:
        body_top = (
            '<h1>Căn hộ %s %s %sm² hiện không còn trong quỹ</h1>\n'
            '  <section class="bai"><p><strong>Căn này hiện đã tắt khỏi bảng hàng công khai.</strong> '
            'Xem các căn Lumi Hanoi còn trống tương tự bên dưới.</p></section>' %
            (h(typ), h(tower), h(area_text))
        )

    similar_html = ""
    for x in similar:
        target = slug_by_id.get(txt(x.get("Mã nội bộ")))
        if not target:
            continue
        x_area = ("%g" % number(x.get("Diện tích"))).replace(".", ",")
        similar_html += (
            '<a class="the-nho" href="/lumi-hanoi/can-ho/%s/"><b>%s</b>'
            '<span>%s · %s m² · %s</span></a>' %
            (h(target), h(x.get("Loại")), h(x.get("Tòa")), h(x_area), h(price(x.get("Giá thuê"))))
        )
    if not similar_html:
        similar_html = '<a href="/lumi-hanoi/">Xem các căn Lumi Hanoi còn trống</a>'

    robots = "index, follow, max-image-preview:large" if is_active else "noindex,follow"
    return """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(description)s">
<meta name="robots" content="%(robots)s">
<link rel="canonical" href="%(url)s">
<link rel="icon" href="/favicon.ico" sizes="any">
<meta property="og:type" content="website">
<meta property="og:url" content="%(url)s">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(description)s">
<meta property="og:image" content="%(og)s">
<meta property="og:site_name" content="Tìm Thuê Smart City">
<meta property="og:locale" content="vi_VN">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="%(title)s">
<meta name="twitter:description" content="%(description)s">
<meta name="twitter:image" content="%(og)s">
<script async src="https://www.googletagmanager.com/gtag/js?id=G-VF9KHC5TWD"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-VF9KHC5TWD');</script>
<script type="application/ld+json">%(breadcrumb)s</script>
<script type="application/ld+json">%(listing)s</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800&family=Be+Vietnam+Pro:wght@300;400;500;600&display=swap">
<link rel="stylesheet" href="/assets/v3.css?v=20260830-14">
<link rel="stylesheet" href="/assets/ngon-ngu.css?v=20260914-compact">
<link rel="stylesheet" href="/assets/project-switch.css?v=20261003-1">
</head>
<body>
<header class="top">
  <div class="khung">
    <a class="hieu" href="/lumi-hanoi/">Cho thuê căn hộ Lumi Hanoi<small>Ảnh thật · Quỹ căn cập nhật thường xuyên</small></a>
    <nav>
      <a href="/lumi-hanoi/">Tất cả căn</a>
      <a href="/lumi-hanoi/?type=1-ngu">1PN</a>
      <a href="/lumi-hanoi/?type=2-ngu">2PN</a>
      <a href="/lumi-hanoi/?type=3-ngu">3PN</a>
      <a href="/">Smart City</a>
      <a href="/cam-nang-thue-nha.html">Cẩm nang</a>
    </nav>
    <div class="doi-tieng" role="group" aria-label="Language / 언어 / 语言">
      <button type="button" data-lang="vi" aria-pressed="true">VI</button>
      <button type="button" data-lang="en" aria-pressed="false">EN</button>
      <button type="button" data-lang="ko" aria-pressed="false">한</button>
      <button type="button" data-lang="zh" aria-pressed="false" aria-label="简体中文" title="简体中文">中</button>
    </div>
  </div>
</header>

<main class="khung">
  <p class="bc"><a href="/">Trang chủ</a> › <a href="/lumi-hanoi/">Lumi Hanoi</a> › <span>%(type)s %(tower)s %(area)sm²</span></p>
  %(body_top)s

  %(gallery)s

  <div class="sl">
    <div class="o"><b>%(area)sm²</b><span>diện tích</span></div>
    <div class="o"><b>%(price)s</b><span>giá thuê/tháng</span></div>
    <div class="o"><b>%(interior)s</b><span>nội thất</span></div>
    <div class="o"><b>%(move)s</b><span>tình trạng</span></div>
  </div>

  <table class="bang"><tbody>
    <tr><td>Mã căn</td><td>%(code)s</td></tr>
    <tr><td>Loại</td><td>%(type)s</td></tr>
    <tr><td>Diện tích</td><td>%(area)s m²</td></tr>
    <tr><td>Tòa</td><td>%(tower)s</td></tr>
    <tr><td>Hướng ban công</td><td>%(direction)s</td></tr>
    <tr><td>Nội thất</td><td>%(interior)s</td></tr>
    <tr><td>Giá thuê</td><td>%(price)s/tháng</td></tr>
    <tr><td>Ngày vào ở</td><td>%(move)s</td></tr>
    <tr><td>Ngày cập nhật</td><td>%(updated)s</td></tr>
  </tbody></table>

  <p style="margin:18px 0">
    <a class="cta-loc" href="https://zalo.me/%(zalo)s" target="_blank" rel="noopener">Nhắn Zalo hỏi căn %(code)s</a>
    <a class="cta-home tren" href="tel:%(zalo)s">Gọi %(zalo)s</a>
  </p>

  <h2 style="font-size:19px;margin-bottom:2px">Xem thêm theo nhu cầu</h2>
  <div class="lq">
    <a href="/lumi-hanoi/">Toàn bộ căn Lumi Hanoi</a>
    <a href="/lumi-hanoi/?tower=%(tower_key)s">Căn tòa %(tower)s</a>
    <a href="/lumi-hanoi/?type=%(type_slug)s">Căn %(type)s</a>
    <a href="/">Xem quỹ căn Vinhomes Smart City</a>
  </div>

  <h2 style="font-size:19px;margin-bottom:2px">Căn tương tự</h2>
  <div class="lq">%(similar)s</div>
</main>

<footer class="chan">
  <div class="khung">
    <p>Tìm Thuê Smart City · Quỹ căn Smart City &amp; Lumi Hanoi · Hotline &amp; Zalo:
    <a href="tel:+84977923284">0977 923 284</a> · <a href="/lumi-hanoi/">Quay lại bảng hàng Lumi Hanoi</a></p>
  </div>
</footer>
<a class="zalo-noi" href="https://zalo.me/%(zalo)s" target="_blank" rel="noopener">Nhắn Zalo tư vấn</a>
<script src="/assets/ngon-ngu.js?v=20261004-lumi-1" defer></script>
<script id="ct-gallery-js" src="/assets/gallery.js?v=20260830-6" defer></script>
<script id="ct-detail-js" src="/assets/can-ho-detail.js?v=20261004-lumi-2" defer></script>
<script src="/assets/app-shell.js?v=20260901-1" defer></script>
<script id="ct-detail-i18n-js" src="/assets/can-ho-detail-i18n.js?v=20261004-lumi-1" defer></script>
</body>
</html>
""" % {
        "title": h(title), "description": h(description), "robots": robots, "url": url, "og": h(og),
        "breadcrumb": json_safe(breadcrumb), "listing": json_safe(listing), "type": h(typ),
        "tower": h(tower), "area": h(area_text), "body_top": body_top, "gallery": gallery,
        "price": h(price(p)), "interior": h(interior), "move": h(move), "code": h(code),
        "direction": h(direction), "updated": h(updated or "Đang cập nhật"), "zalo": ZALO,
        "tower_key": h(key(tower)), "type_slug": h(slug(typ)), "similar": similar_html,
    }


def list_index(rows, slug_by_id):
    cards = []
    for r in rows:
        if not active(r):
            continue
        s = slug_by_id.get(txt(r.get("Mã nội bộ")))
        if not s:
            continue
        ar = ("%g" % number(r.get("Diện tích"))).replace(".", ",")
        cards.append(
            '<a class="the-nho" href="/lumi-hanoi/can-ho/%s/"><b>%s · %s</b>'
            '<span>%s m² · %s · %s</span></a>' %
            (h(s), h(r.get("Loại")), h(r.get("Tòa")), h(ar),
             h(price(r.get("Giá thuê"))), h(r.get("Mã căn")))
        )
    return """<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Danh sách căn hộ Lumi Hanoi đang cho thuê</title>
<meta name="robots" content="noindex,follow,max-image-preview:large">
<link rel="canonical" href="%(domain)s/lumi-hanoi/">
<link rel="stylesheet" href="/assets/v3.css?v=20260830-14"></head><body>
<header class="top"><div class="khung"><a class="hieu" href="/lumi-hanoi/">Cho thuê căn hộ Lumi Hanoi<small>Quỹ căn cập nhật thường xuyên</small></a></div></header>
<main class="khung"><p class="bc"><a href="/">Trang chủ</a> › <a href="/lumi-hanoi/">Lumi Hanoi</a> › Danh sách căn</p>
<h1>Danh sách căn hộ Lumi Hanoi đang cho thuê</h1>
<p class="tt">Mở từng căn để xem giá, diện tích, nội thất, ngày vào ở và hình ảnh thực tế.</p>
<div class="lq">%(cards)s</div></main></body></html>""" % {"domain": DOMAIN, "cards": "".join(cards)}


def main():
    rows = json.loads(DATA.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or len(rows) < 10:
        raise ValueError("data-lumi.json rỗng/bất thường")

    BASE.mkdir(parents=True, exist_ok=True)
    old = read_registry()
    old_by_id = {txt(v.get("id")): s for s, v in old.items() if isinstance(v, dict) and v.get("id")}
    used = {}
    registry = {}
    slug_by_id = {}

    for r in rows:
        ident = txt(r.get("Mã nội bộ"))
        if not ident or not txt(r.get("Mã căn")) or not txt(r.get("Tòa")) or number(r.get("Diện tích")) <= 0:
            continue
        candidate = old_by_id.get(ident) or proposed_slug(r)
        base = candidate
        n = 2
        while candidate in used and used[candidate] != ident:
            candidate = "%s-%d" % (base, n)
            n += 1
        used[candidate] = ident
        slug_by_id[ident] = candidate
        registry[candidate] = {
            "id": ident, "ma": txt(r.get("Mã căn")), "loai": txt(r.get("Loại")),
            "toa": txt(r.get("Tòa")), "dien_tich": number(r.get("Diện tích")),
            "active": active(r),
        }

    # Dọn toàn bộ URL legacy từng chứa mã căn thật. Chỉ giữ thư mục tương ứng
    # với registry public hiện tại (mã dạng thue1N.<STT>, thue2N.<STT>...).
    for child in BASE.iterdir():
        if child.is_dir() and child.name not in registry:
            shutil.rmtree(child)

    for r in rows:
        ident = txt(r.get("Mã nội bộ"))
        page_slug = slug_by_id.get(ident)
        if not page_slug:
            continue
        candidates = [x for x in rows if active(x) and txt(x.get("Mã nội bộ")) != ident]
        candidates.sort(key=lambda x: (
            0 if key(x.get("Tòa")) == key(r.get("Tòa")) else 1,
            0 if key(x.get("Loại")) == key(r.get("Loại")) else 1,
            abs(money(x.get("Giá thuê")) - money(r.get("Giá thuê"))),
        ))
        page_dir = BASE / page_slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(
            detail_html(r, page_slug, candidates[:6], slug_by_id), encoding="utf-8"
        )

    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (BASE / "index.html").write_text(list_index(rows, slug_by_id), encoding="utf-8")

    urls = [
        (DOMAIN + "/lumi-hanoi/", "", "0.9"),
    ]
    for r in rows:
        if not active(r):
            continue
        page_slug = slug_by_id.get(txt(r.get("Mã nội bộ")))
        if not page_slug:
            continue
        lastmod = iso_date(txt(r.get("Ngày cập nhật")) or txt(r.get("Ngày thêm vào hệ thống")))
        urls.append((DOMAIN + "/lumi-hanoi/can-ho/" + page_slug + "/", lastmod, "0.6"))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod, priority in urls:
        part = "  <url><loc>%s</loc>" % xml_escape(loc)
        if lastmod:
            part += "<lastmod>%s</lastmod>" % lastmod
        part += "<priority>%s</priority></url>" % priority
        lines.append(part)
    lines += ["</urlset>", ""]
    SITEMAP.write_text("\n".join(lines), encoding="utf-8")
    print("Đã sinh %d trang căn Lumi; sitemap có %d URL." % (len(registry), len(urls)))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("::error::%s" % error, file=sys.stderr)
        sys.exit(1)

#!/usr/bin/env python3
"""P0-P4 post-processor + audit cho timthuesmartcity.com.

P0: canonical/query guard + robots nhất quán, không chặn query bằng robots.txt.
P1/P2: củng cố landing tòa bằng entity schema và dữ liệu quỹ căn; chỉ chèn ảnh
       mặt bằng khi tìm thấy asset local khớp chính xác.
P3: liên kết ngang giữa các tòa cùng phân khu + cụm cha/con.
P4: title tòa ổn định, schema ItemList lấy từ link thật, audit sitemap/canonical.

Script idempotent: chạy lặp không nhân đôi marker.
"""

import argparse
import hashlib
import html
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(GOC, "seo-toa.json")
SITEMAP_TOWER = os.path.join(GOC, "sitemap-toa.xml")
REPORT = os.path.join(GOC, "bao-cao-seo-p0-p4.json")
DATA = os.path.join(GOC, "data.json")
DOMAIN = "https://timthuesmartcity.com"
QUERY_START = "<!-- SEO-QUERY-GUARD:START -->"
QUERY_END = "<!-- SEO-QUERY-GUARD:END -->"
HEAD_START = "<!-- SEO-TOWER-ENTITY:START -->"
HEAD_END = "<!-- SEO-TOWER-ENTITY:END -->"
BODY_START = "<!-- SEO-TOWER-CONTEXT:START -->"
BODY_END = "<!-- SEO-TOWER-CONTEXT:END -->"
SKIP_DIRS = {".git", ".github", "node_modules", "scripts", "images", "anh-can-ho", "assets"}

QUERY_BLOCK = r'''<!-- SEO-QUERY-GUARD:START -->
<script id="seo-query-guard">
(function(){
  if (!window.location.search) return;
  var robots=document.querySelector('meta[name="robots"]');
  if(!robots){robots=document.createElement('meta');robots.name='robots';document.head.appendChild(robots);}
  robots.content='noindex,follow,max-image-preview:large';
  var canonical=document.querySelector('link[rel="canonical"]');
  if(canonical){try{var u=new URL(canonical.href,location.origin);u.search='';u.hash='';canonical.href=u.href;}catch(e){}}
})();
</script>
<!-- SEO-QUERY-GUARD:END -->'''


def esc(v):
    return html.escape("" if v is None else str(v), quote=True)


def slugify(v):
    s = unicodedata.normalize("NFD", str(v))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.lower().replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def replace_marker(text, start, end, block):
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if pat.search(text):
        return pat.sub(block, text, count=1)
    return text


def ensure_query_guard(text):
    text = replace_marker(text, QUERY_START, QUERY_END, QUERY_BLOCK)
    if QUERY_START in text:
        return text
    return text.replace("</head>", QUERY_BLOCK + "\n</head>", 1) if "</head>" in text else text


def ensure_robots(text):
    if re.search(r'<meta\s+[^>]*name=["\']robots["\']', text, re.I):
        return text
    tag = '<meta name="robots" content="index,follow,max-image-preview:large">\n'
    m = re.search(r'<link\s+[^>]*rel=["\']canonical["\'][^>]*>\s*', text, re.I)
    if m:
        return text[:m.end()] + tag + text[m.end():]
    return text.replace("</head>", tag + "</head>", 1)


def canonical(text):
    m = re.search(r'<link\s+[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', text, re.I)
    if not m:
        m = re.search(r'<link\s+[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', text, re.I)
    return m.group(1).strip() if m else ""


def title_of(text):
    m = re.search(r'<title>(.*?)</title>', text, re.I | re.S)
    return re.sub(r"\s+", " ", html.unescape(m.group(1))).strip() if m else ""


def h1_of(text):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.I | re.S)
    return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ""


def noindex(text):
    m = re.search(r'<meta\s+[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']+)', text, re.I)
    if not m:
        m = re.search(r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']robots["\']', text, re.I)
    return bool(m and "noindex" in m.group(1).lower())


def stable_tower_title(entry):
    name = entry["name"]
    if "Masteri" in name or "Lumière" in name or "Lumiere" in name:
        return "Cho Thuê Căn Hộ %s Smart City | Giá Tốt" % name
    return "Cho Thuê Căn Hộ %s Vinhomes Smart City | Giá Tốt" % name


def set_title_family(text, new_title):
    text = re.sub(r'<title>.*?</title>', '<title>%s</title>' % esc(new_title), text, count=1, flags=re.I | re.S)
    text = re.sub(r'(<meta\s+property=["\']og:title["\']\s+content=["\'])[^"\']*(["\'])', r'\g<1>%s\2' % esc(new_title), text, count=1, flags=re.I)
    text = re.sub(r'(<meta\s+name=["\']twitter:title["\']\s+content=["\'])[^"\']*(["\'])', r'\g<1>%s\2' % esc(new_title), text, count=1, flags=re.I)
    return text


def detail_urls(text):
    seen = []
    for m in re.finditer(r'href=["\'](/can-ho/[^"\']+/)["\']', text, re.I):
        href = m.group(1)
        if href == "/can-ho/" or href in seen:
            continue
        seen.append(href)
    return seen


def jsonld_block(entry, urls):
    page_url = DOMAIN + entry["path"]
    items = [{"@type": "ListItem", "position": i + 1, "url": DOMAIN + u} for i, u in enumerate(urls)]
    obj = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "@id": page_url + "#collectionpage", "url": page_url,
        "name": stable_tower_title(entry),
        "dateModified": entry.get("last_seen") or entry.get("first_seen"),
        "isPartOf": {"@type": "WebSite", "@id": DOMAIN + "/#website", "url": DOMAIN + "/", "name": "Tìm Thuê Smart City"},
        "about": {"@type": "Place", "name": "%s, Vinhomes Smart City" % entry["name"]},
        "mainEntity": {"@type": "ItemList", "numberOfItems": entry.get("count", 0), "itemListElement": items},
    }
    return HEAD_START + "\n<script type=\"application/ld+json\">" + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>\n" + HEAD_END


def money(v):
    try:
        v = int(v)
    except Exception:
        return "Liên hệ"
    if v <= 0:
        return "Liên hệ"
    return ("%g triệu" % (v / 1_000_000)).replace(".", ",")


def floorplan_asset(entry):
    tokens = {slugify(entry.get("data_code", "")), slugify(entry.get("name", ""))}
    tokens |= set(slugify(entry.get("name", "")).split("-"))
    tokens = {t for t in tokens if len(t) >= 2 and t not in {"the", "smart", "city", "vinhomes", "west"}}
    candidates = []
    image_root = os.path.join(GOC, "images")
    if not os.path.isdir(image_root):
        return ""
    for root, dirs, files in os.walk(image_root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            low = slugify(f)
            if "mat-bang" not in low and "layout" not in low:
                continue
            if any(t in low for t in tokens):
                candidates.append("/" + os.path.relpath(os.path.join(root, f), GOC).replace(os.sep, "/"))
    return sorted(candidates)[0] if candidates else ""


def parent_path(pk):
    mp = {"Sapphire": "/sapphire/", "Masteri": "/masteri/", "Miami": "/miami/", "Sakura": "/sakura/", "Imperia": "/imperia/", "Lumiere": "/lumiere/", "Canopy": "/canopy/", "Tonkin": "/tonkin/"}
    return mp.get(pk, "/")


def context_block(entry, siblings):
    types = entry.get("types") or []
    dominant = types[0]["name"] if types else "các loại căn đang có"
    price = money(entry.get("price_min"))
    if entry.get("price_max") and entry.get("price_max") != entry.get("price_min"):
        price += " – " + money(entry.get("price_max"))
    area = ""
    if entry.get("area_min") and entry.get("area_max"):
        area = "%s–%s m²" % (entry["area_min"], entry["area_max"])
    links = "".join('<a href="%s"><strong>%s</strong><span>%d căn đang hiển thị</span></a>' % (esc(s["path"]), esc(s["name"]), s.get("count", 0)) for s in siblings[:5])
    if not links:
        links = '<a href="%s"><strong>Xem toàn phân khu %s</strong><span>So sánh quỹ căn theo tòa và loại căn.</span></a>' % (esc(parent_path(entry.get("district"))), esc(entry.get("district") or "Smart City"))
    fp = floorplan_asset(entry)
    floor = ""
    if fp:
        floor = ('<div class="seo-graph-group"><h3>Mặt bằng / layout có sẵn</h3><img src="%s" alt="Mặt bằng tòa %s Vinhomes Smart City" loading="lazy" decoding="async" style="width:100%%;height:auto;border-radius:14px"></div>') % (esc(fp), esc(entry["name"]))
    summary = ("Tại thời điểm dữ liệu gần nhất, tòa <strong>%s</strong> có <strong>%d căn</strong> đang hiển thị. Khoảng giá hiện tại là <strong>%s/tháng</strong>%s; nhóm căn xuất hiện nhiều nhất là <strong>%s</strong>. Các con số này lấy trực tiếp từ cùng snapshot dữ liệu dùng để dựng danh sách căn, không viết cứng.") % (esc(entry["name"]), entry.get("count", 0), esc(price), (", diện tích %s" % esc(area)) if area else "", esc(dominant))
    return (BODY_START + '\n<section class="seo-graph" aria-label="Dữ liệu SEO theo tòa"><div class="seo-graph-head"><span>Dữ liệu theo tòa</span><h2>So sánh %s trong %s</h2><p>%s</p></div><div class="seo-graph-grid"><div class="seo-graph-group"><h3>Tòa cùng phân khu</h3><div class="seo-graph-links">%s</div></div><div class="seo-graph-group"><h3>Đi tiếp theo nhu cầu</h3><div class="seo-graph-links"><a href="%s"><strong>Toàn bộ %s</strong><span>Xem quỹ căn của cả phân khu.</span></a><a href="/can-ho/"><strong>Danh sách căn có URL chi tiết</strong><span>Mở từng căn đang còn trống.</span></a><a href="/bang-gia-thue-vinhomes-smart-city.html"><strong>Bảng giá thuê</strong><span>So sánh mặt bằng giá toàn Smart City.</span></a></div></div>%s</div></section>\n' + BODY_END) % (esc(entry["name"]), esc(entry.get("district") or "Vinhomes Smart City"), summary, links, esc(parent_path(entry.get("district"))), esc(entry.get("district") or "phân khu"), floor)


def enrich_tower(text, entry, siblings):
    text = ensure_query_guard(ensure_robots(text))
    text = set_title_family(text, stable_tower_title(entry))
    head = jsonld_block(entry, detail_urls(text))
    text = replace_marker(text, HEAD_START, HEAD_END, head)
    if HEAD_START not in text:
        text = text.replace("</head>", head + "\n</head>", 1)
    body = context_block(entry, siblings)
    text = replace_marker(text, BODY_START, BODY_END, body)
    if BODY_START not in text:
        text = text.replace("</main>", body + "\n</main>", 1)
    return text


def iter_html():
    for root, dirs, files in os.walk(GOC):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if f.endswith(".html"):
                yield os.path.join(root, f)


def sitemap_urls(path):
    if not os.path.exists(path):
        return []
    return re.findall(r'<loc>(.*?)</loc>', open(path, encoding="utf-8").read(), re.I | re.S)


def local_path_from_url(url):
    if not url.startswith(DOMAIN):
        return None
    p = url[len(DOMAIN):].split("?", 1)[0].split("#", 1)[0]
    if p == "/":
        return os.path.join(GOC, "index.html")
    if p.endswith("/"):
        return os.path.join(GOC, p.strip("/"), "index.html")
    return os.path.join(GOC, p.lstrip("/"))


def audit(registry):
    critical, warnings = [], []
    title_counts, canonical_counts = Counter(), Counter()
    query_guard = indexable = total = 0
    for path in iter_html():
        total += 1
        text = open(path, encoding="utf-8").read()
        rel = os.path.relpath(path, GOC).replace(os.sep, "/")
        t, c, h = title_of(text), canonical(text), h1_of(text)
        if t: title_counts[t] += 1
        if c: canonical_counts[c] += 1
        if QUERY_START in text: query_guard += 1
        if not noindex(text):
            indexable += 1
            if not t or not c or not h: warnings.append({"page": rel, "issue": "indexable page thiếu title/canonical/H1"})
            if c and ("?" in c or "#" in c): warnings.append({"page": rel, "issue": "canonical chứa query/hash"})
    for t, n in title_counts.items():
        if n > 1: warnings.append({"issue": "duplicate title", "value": t, "count": n})
    for c, n in canonical_counts.items():
        if n > 1: warnings.append({"issue": "duplicate canonical", "value": c, "count": n})
    active_paths = {e["path"] for e in registry.values() if e.get("indexable") and e.get("count", 0) > 0}
    by_path = {e["path"]: e for e in registry.values()}
    sm_paths = {u[len(DOMAIN):] for u in sitemap_urls(SITEMAP_TOWER) if u.startswith(DOMAIN)}
    if active_paths != sm_paths:
        critical.append({"issue": "sitemap-toa không khớp registry", "missing": sorted(active_paths - sm_paths), "extra": sorted(sm_paths - active_paths)})
    for p in sorted(active_paths):
        e = by_path[p]
        f = os.path.join(GOC, p.strip("/"), "index.html")
        if not os.path.exists(f):
            critical.append({"issue": "tower page missing", "path": p}); continue
        text = open(f, encoding="utf-8").read()
        expected = DOMAIN + p
        if canonical(text) != expected: critical.append({"issue": "tower canonical mismatch", "path": p, "canonical": canonical(text), "expected": expected})
        if noindex(text): critical.append({"issue": "indexable tower bị noindex", "path": p})
        if HEAD_START not in text: critical.append({"issue": "tower thiếu CollectionPage schema", "path": p})
        if title_of(text) != stable_tower_title(e): critical.append({"issue": "tower title chưa ổn định", "path": p})
    for sm_name in ("sitemap.xml", "sitemap-can-ho.xml", "sitemap-phan-khu-loai-can.xml", "sitemap-ngan-sach-loai-can.xml", "sitemap-toa.xml"):
        for u in sitemap_urls(os.path.join(GOC, sm_name)):
            lp = local_path_from_url(u)
            if lp and os.path.exists(lp) and noindex(open(lp, encoding="utf-8").read()):
                critical.append({"issue": "noindex URL nằm trong sitemap", "sitemap": sm_name, "url": u})
    data_hash = hashlib.sha256(open(DATA, "rb").read()).hexdigest()[:16] if os.path.exists(DATA) else ""
    return {"version": 1, "data_fingerprint": data_hash, "html_pages": total, "indexable_pages": indexable, "query_guard_pages": query_guard, "tower_registry": len(registry), "tower_indexable": len(active_paths), "critical_count": len(critical), "warning_count": len(warnings), "critical": critical, "warnings": warnings[:200]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thu", action="store_true")
    ap.add_argument("--kiem-tra", action="store_true")
    args = ap.parse_args()
    if not os.path.exists(REGISTRY):
        print("LỖI: chưa có seo-toa.json. Chạy mo-rong-trang-toa.py trước."); return 2
    registry = json.load(open(REGISTRY, encoding="utf-8")).get("towers", {})
    if not args.kiem_tra:
        changed = 0
        for path in list(iter_html()):
            old = open(path, encoding="utf-8").read()
            new = ensure_query_guard(ensure_robots(old))
            if new != old:
                changed += 1
                if not args.thu:
                    with open(path, "w", encoding="utf-8", newline="") as f: f.write(new)
        print("P0: %d HTML cần/được cập nhật robots + query guard." % changed)
        by_pk = defaultdict(list)
        for e in registry.values():
            if e.get("indexable") and e.get("count", 0) > 0: by_pk[e.get("district")].append(e)
        for pk in by_pk: by_pk[pk].sort(key=lambda e: (-e.get("count", 0), e["name"]))
        enriched = 0
        for e in registry.values():
            if not e.get("indexable") or e.get("count", 0) < 1: continue
            path = os.path.join(GOC, e["path"].strip("/"), "index.html")
            if not os.path.exists(path): continue
            old = open(path, encoding="utf-8").read()
            siblings = [x for x in by_pk.get(e.get("district"), []) if x["path"] != e["path"]]
            new = enrich_tower(old, e, siblings)
            if new != old:
                enriched += 1
                if not args.thu:
                    with open(path, "w", encoding="utf-8", newline="") as f: f.write(new)
        print("P1-P4: %d landing tòa cần/được enrich." % enriched)
    report = audit(registry)
    print("Audit: %d HTML · %d indexable · %d tower indexable · %d critical · %d warning" % (report["html_pages"], report["indexable_pages"], report["tower_indexable"], report["critical_count"], report["warning_count"]))
    for e in report["critical"][:20]: print("CRITICAL:", e)
    if not args.thu:
        with open(REPORT, "w", encoding="utf-8", newline="") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True); f.write("\n")
    return 1 if report["critical_count"] else 0


if __name__ == "__main__":
    sys.exit(main())

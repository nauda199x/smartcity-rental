#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P7 — ưu tiên crawl/index bằng kiến trúc link thật, không dùng sitemap <priority>.

Mục tiêu:
- Giữ một nhóm URL thương mại cốt lõi (Tier 1) luôn indexable, self-canonical,
  có trong sitemap và nhận link từ các hub mạnh.
- Chọn các landing tòa có quỹ căn lớn nhất làm Tier 2.
- Chọn các căn active xuất hiện gần đây làm Tier 3 để ưu tiên kiểm tra/submit thủ công.
- Không tạo URL mới và không gọi Google Indexing API.

Output `seo-index-priority.json` là deterministic: nếu dữ liệu/graph không đổi thì file
không đổi, tránh tạo commit giả và lastmod giả.
"""

import argparse
import html
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://timthuesmartcity.com"
OUTPUT = os.path.join(ROOT, "seo-index-priority.json")
TOWER_REGISTRY = os.path.join(ROOT, "seo-toa.json")
LISTING_REGISTRY = os.path.join(ROOT, "can-ho", "danh-sach-trang.json")
APARTMENT_SITEMAP = os.path.join(ROOT, "sitemap-can-ho.xml")

START = "<!-- P7-CRAWL-PRIORITY:START -->"
END = "<!-- P7-CRAWL-PRIORITY:END -->"

# URL kiếm khách trực tiếp. Không thêm URL mới chỉ để SEO.
CORE = [
    ("/", "Trang thuê Smart City", "landing chính cho cụm từ khóa thuê Smart City"),
    ("/can-ho/", "Căn hộ đang cho thuê", "hub URL chi tiết căn active"),
    ("/studio/", "Thuê Studio", "intent theo loại căn"),
    ("/1pn/", "Thuê 1PN", "intent theo loại căn"),
    ("/1pn-plus/", "Thuê 1PN+", "intent theo loại căn"),
    ("/2pn/", "Thuê 2PN", "intent theo loại căn"),
    ("/2pn-plus/", "Thuê 2PN+", "intent theo loại căn"),
    ("/3pn/", "Thuê 3PN", "intent theo loại căn"),
    ("/bang-gia-thue-vinhomes-smart-city.html", "Bảng giá thuê", "intent giá thuê có dữ liệu thực tế"),
]

DISTRICT_HUBS = {
    "Sapphire": ("/sapphire/", "Sapphire"),
    "Masteri": ("/masteri/", "Masteri West Heights"),
    "Miami": ("/miami/", "The Miami"),
    "Sakura": ("/sakura/", "The Sakura"),
    "Imperia": ("/imperia/", "Imperia Smart City"),
    "Lumiere": ("/lumiere/", "Lumière Evergreen"),
    "Canopy": ("/canopy/", "The Canopy"),
    "Tonkin": ("/tonkin/", "Tonkin"),
}

# Hai nguồn có lượng inbound rất mạnh, dùng để truyền đường crawl trực tiếp tới money pages.
SOURCE_HUBS = [
    "cam-nang-thue-nha.html",
    "kinh-nghiem-thue-chung-cu-smart-city.html",
]


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value.strip())


def read(rel):
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def url_to_rel(url):
    p = urlparse(url).path
    if p == "/":
        return "index.html"
    p = p.lstrip("/")
    if p.endswith("/"):
        return p + "index.html"
    return p


def canonical_of(raw):
    if not raw:
        return ""
    m = re.search(r'<link\b(?=[^>]*\brel=["\']canonical["\'])(?=[^>]*\bhref=["\']([^"\']+)["\'])[^>]*>', raw, re.I)
    if not m:
        # Cho phép thứ tự href trước rel.
        m = re.search(r'<link\b(?=[^>]*\bhref=["\']([^"\']+)["\'])(?=[^>]*\brel=["\']canonical["\'])[^>]*>', raw, re.I)
    return m.group(1).strip() if m else ""


def robots_of(raw):
    if not raw:
        return ""
    m = re.search(r'<meta\b(?=[^>]*\bname=["\']robots["\'])(?=[^>]*\bcontent=["\']([^"\']*)["\'])[^>]*>', raw, re.I)
    if not m:
        m = re.search(r'<meta\b(?=[^>]*\bcontent=["\']([^"\']*)["\'])(?=[^>]*\bname=["\']robots["\'])[^>]*>', raw, re.I)
    return m.group(1).lower() if m else ""


def expected_canonical(url):
    return BASE + ("/" if url == "/" else url)


def all_html():
    skip = {".git", ".github", "node_modules"}
    docs = {}
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip]
        for name in files:
            if name.lower().endswith(".html"):
                path = os.path.join(root, name)
                rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
                try:
                    raw = open(path, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                docs[rel] = raw
    return docs


def normalize_internal(href, source_rel):
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
        return ""
    source_url = BASE + "/" if source_rel == "index.html" else BASE + "/" + source_rel
    u = urlparse(urljoin(source_url, href))
    if u.scheme not in ("http", "https") or u.netloc.lower() not in ("timthuesmartcity.com", "www.timthuesmartcity.com"):
        return ""
    path = re.sub(r"/{2,}", "/", u.path or "/")
    if path != "/" and not path.endswith("/") and not path.lower().endswith(".html"):
        # Các asset không được tính như page link.
        if "." in path.rsplit("/", 1)[-1]:
            return ""
    return path


def inbound_counts(docs):
    inbound = Counter()
    sources = defaultdict(set)
    for rel, raw in docs.items():
        if "noindex" in robots_of(raw):
            continue
        parser = LinkParser()
        try:
            parser.feed(raw)
        except Exception:
            continue
        seen = set()
        for href in parser.hrefs:
            path = normalize_internal(href, rel)
            if not path or path in seen:
                continue
            seen.add(path)
            inbound[path] += 1
            sources[path].add(rel)
    return inbound, sources


def sitemap_urls():
    urls = set()
    for name in os.listdir(ROOT):
        if not (name.startswith("sitemap") and name.endswith(".xml")):
            continue
        try:
            raw = open(os.path.join(ROOT, name), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for loc in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", raw, re.I):
            u = urlparse(loc.strip())
            if u.netloc.lower() in ("timthuesmartcity.com", "www.timthuesmartcity.com"):
                urls.add(u.path or "/")
    return urls


def district_priority():
    totals = Counter()
    if os.path.isfile(TOWER_REGISTRY):
        try:
            raw = json.load(open(TOWER_REGISTRY, encoding="utf-8"))
            for rec in (raw.get("towers") or {}).values():
                district = str(rec.get("district") or "")
                if district in DISTRICT_HUBS and rec.get("indexable"):
                    totals[district] += int(rec.get("count") or 0)
        except Exception:
            pass
    ranked = sorted(DISTRICT_HUBS, key=lambda x: (-totals.get(x, 0), x))
    return ranked, totals


def top_towers(limit=12):
    rows = []
    if not os.path.isfile(TOWER_REGISTRY):
        return rows
    try:
        raw = json.load(open(TOWER_REGISTRY, encoding="utf-8"))
    except Exception:
        return rows
    for rec in (raw.get("towers") or {}).values():
        if not rec.get("indexable") or int(rec.get("count") or 0) <= 0:
            continue
        href = str(rec.get("path") or "")
        if not href:
            continue
        rows.append({
            "url": href,
            "label": str(rec.get("name") or href),
            "district": str(rec.get("district") or ""),
            "inventory": int(rec.get("count") or 0),
        })
    rows.sort(key=lambda r: (-r["inventory"], r["url"]))
    return rows[:limit]


def newest_active(limit=20):
    active = set()
    if os.path.isfile(APARTMENT_SITEMAP):
        raw = open(APARTMENT_SITEMAP, encoding="utf-8", errors="replace").read()
        for loc in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", raw, re.I):
            p = urlparse(loc.strip()).path
            if p.startswith("/can-ho/") and p != "/can-ho/":
                active.add(p.rstrip("/").split("/")[-1])
    if not os.path.isfile(LISTING_REGISTRY):
        return []
    try:
        reg = json.load(open(LISTING_REGISTRY, encoding="utf-8"))
    except Exception:
        return []
    rows = []
    for slug, rec in reg.items():
        if slug not in active:
            continue
        date = str(rec.get("ngay_xuat_hien") or "")
        rows.append({
            "url": "/can-ho/%s/" % slug,
            "first_seen": date,
            "code": str(rec.get("ma") or ""),
            "tower": str(rec.get("toa") or ""),
            "type": str(rec.get("loai") or ""),
            "district": str(rec.get("phan_khu") or ""),
        })
    rows.sort(key=lambda r: (r["first_seen"], r["url"]), reverse=True)
    return rows[:limit]


def esc(v):
    return html.escape(str(v), quote=True)


def priority_block(top_districts):
    type_links = [
        ("/studio/", "Studio"), ("/1pn/", "1PN"), ("/1pn-plus/", "1PN+"),
        ("/2pn/", "2PN"), ("/2pn-plus/", "2PN+"), ("/3pn/", "3PN"),
    ]
    district_links = [DISTRICT_HUBS[d] for d in top_districts[:6]]
    def cards(rows, prefix=""):
        return "".join('<a href="%s"><strong>%s%s</strong></a>' % (esc(h), esc(prefix), esc(label)) for h, label in rows)
    return (
        START + '\n<section class="seo-graph p7-crawl-priority" aria-label="Tìm thuê Smart City theo nhu cầu">'
        '<div class="seo-graph-head"><span>Tìm thuê nhanh</span>'
        '<h2>Trang thuê Smart City được ưu tiên</h2>'
        '<p>Đi thẳng tới các nhóm căn và phân khu đang có quỹ thuê thực tế.</p></div>'
        '<div class="seo-graph-grid">'
        '<div class="seo-graph-group"><h3>Theo loại căn</h3><div class="seo-graph-links">%s</div></div>'
        '<div class="seo-graph-group"><h3>Theo phân khu</h3><div class="seo-graph-links">%s</div></div>'
        '<div class="seo-graph-group"><h3>Dữ liệu thuê</h3><div class="seo-graph-links">'
        '<a href="/can-ho/"><strong>Căn hộ đang trống</strong></a>'
        '<a href="/bang-gia-thue-vinhomes-smart-city.html"><strong>Bảng giá thuê thực tế</strong></a>'
        '</div></div></div></section>\n' + END
    ) % (cards(type_links), cards(district_links))


def replace_block(raw, block):
    pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if pat.search(raw):
        return pat.sub(block, raw, count=1)
    if "</main>" in raw:
        return raw.replace("</main>", block + "\n</main>", 1)
    if "</body>" in raw:
        return raw.replace("</body>", block + "\n</body>", 1)
    return raw


def write_hubs(block, dry=False):
    changed = 0
    for rel in SOURCE_HUBS:
        raw = read(rel)
        if not raw or "noindex" in robots_of(raw):
            continue
        new = replace_block(raw, block)
        if new == raw:
            continue
        changed += 1
        if not dry:
            with open(os.path.join(ROOT, rel), "w", encoding="utf-8", newline="") as f:
                f.write(new)
        print(("(--thu) sẽ ưu tiên " if dry else "P7 ưu tiên ") + rel)
    return changed


def build_report(docs, inbound, sitemaps, ranked_districts, totals):
    tier1 = []
    # Core + 6 phân khu có quỹ lớn nhất. Các phân khu còn lại vẫn được P6 liên kết bình thường.
    targets = list(CORE)
    for district in ranked_districts[:6]:
        href, label = DISTRICT_HUBS[district]
        targets.append((href, "Thuê " + label, "phân khu có quỹ căn active lớn"))

    failures = []
    for url, label, reason in targets:
        rel = url_to_rel(url)
        raw = docs.get(rel)
        expected = expected_canonical(url)
        exists = raw is not None
        indexable = bool(raw is not None and "noindex" not in robots_of(raw))
        canonical = canonical_of(raw) if raw else ""
        self_canonical = canonical.rstrip("/") == expected.rstrip("/")
        in_sitemap = url in sitemaps or (url == "/" and "/" in sitemaps)
        item = {
            "url": url,
            "label": label,
            "reason": reason,
            "inbound_pages": int(inbound.get(url, 0)),
            "exists": exists,
            "indexable": indexable,
            "self_canonical": self_canonical,
            "in_sitemap": in_sitemap,
        }
        tier1.append(item)
        if not (exists and indexable and self_canonical and in_sitemap):
            failures.append(item)

    tier2 = top_towers(12)
    for item in tier2:
        item["inbound_pages"] = int(inbound.get(item["url"], 0))

    tier3 = newest_active(20)
    for item in tier3:
        item["inbound_pages"] = int(inbound.get(item["url"], 0))

    report = {
        "policy": {
            "tier_1": "Money pages: phải tồn tại, indexable, self-canonical và có trong sitemap; nhận link từ hub mạnh.",
            "tier_2": "Landing tòa có quỹ căn lớn: ưu tiên crawl sau money pages.",
            "tier_3": "20 căn active xuất hiện gần đây nhất: hàng đợi ưu tiên kiểm tra URL Inspection khi cần.",
            "note": "Không dùng sitemap priority/changefreq và không dùng Google Indexing API cho URL bất động sản thông thường."
        },
        "tier_1": tier1,
        "tier_2": tier2,
        "tier_3": tier3,
        "district_inventory": {d: int(totals.get(d, 0)) for d in ranked_districts},
        "summary": {
            "tier_1_count": len(tier1),
            "tier_2_count": len(tier2),
            "tier_3_count": len(tier3),
            "critical": len(failures),
        }
    }
    return report, failures


def main():
    ap = argparse.ArgumentParser(description="P7 crawl/index priority cho timthuesmartcity.com")
    ap.add_argument("--kiem-tra", action="store_true", help="chỉ audit, không sửa HTML/output")
    ap.add_argument("--thu", action="store_true", help="dry-run HTML nhưng vẫn không ghi output")
    args = ap.parse_args()

    ranked, totals = district_priority()
    if not args.kiem_tra:
        changed = write_hubs(priority_block(ranked), dry=args.thu)
        print("P7 hub boost: %d file %s." % (changed, "cần đổi" if args.thu else "đã đổi"))

    docs = all_html()
    inbound, _ = inbound_counts(docs)
    sitemaps = sitemap_urls()
    report, failures = build_report(docs, inbound, sitemaps, ranked, totals)

    if not (args.kiem_tra or args.thu):
        new = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
        old = ""
        if os.path.isfile(OUTPUT):
            old = open(OUTPUT, encoding="utf-8", errors="replace").read()
        if new != old:
            with open(OUTPUT, "w", encoding="utf-8", newline="") as f:
                f.write(new)
            print("Đã cập nhật seo-index-priority.json")
        else:
            print("seo-index-priority.json không đổi")

    t1 = report["tier_1"]
    min_inbound = min((x["inbound_pages"] for x in t1), default=0)
    print("P7 priority: Tier1=%d · Tier2=%d · newest=%d · min inbound Tier1=%d · critical=%d" % (
        len(t1), len(report["tier_2"]), len(report["tier_3"]), min_inbound, len(failures)
    ))
    if failures:
        for x in failures:
            print("CRITICAL %s exists=%s indexable=%s selfCanonical=%s sitemap=%s" % (
                x["url"], x["exists"], x["indexable"], x["self_canonical"], x["in_sitemap"]
            ))
        return 1
    print("PASS — toàn bộ URL Tier 1 đủ điều kiện crawl/index kỹ thuật.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

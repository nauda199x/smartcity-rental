#!/usr/bin/env python3
"""P3/P4: loại orphan ở các landing programmatic indexable.

Tự phát hiện hai nhóm URL có ý định tìm kiếm rõ:
- loại căn × ngân sách (vd. /2pn-tren-15-trieu/)
- loại căn × phân khu (vd. /cho-thue-1pn-plus-imperia-smart-city/)

Mỗi child indexable được nối từ hub cha tương ứng. Không link trang noindex.
Marker giúp chạy lặp an toàn và không nhân đôi liên kết.
"""

import argparse
import html
import os
import re
import sys
from collections import defaultdict

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START = "<!-- SEO-PROGRAMMATIC-HUB:START -->"
END = "<!-- SEO-PROGRAMMATIC-HUB:END -->"

TYPE_HUBS = {
    "studio": "studio/index.html",
    "1pn": "1pn/index.html",
    "1pn-plus": "1pn-plus/index.html",
    "2pn": "2pn/index.html",
    "2pn-plus": "2pn-plus/index.html",
    "3pn": "3pn/index.html",
}
DISTRICT_HUBS = {
    "sapphire": "sapphire/index.html",
    "masteri": "masteri/index.html",
    "miami": "miami/index.html",
    "sakura": "sakura/index.html",
    "imperia": "imperia/index.html",
    "lumiere": "lumiere/index.html",
    "canopy": "canopy/index.html",
    "tonkin": "tonkin/index.html",
}
LABEL_TYPE = {
    "studio": "Studio", "1pn": "1 phòng ngủ", "1pn-plus": "1 phòng ngủ+",
    "2pn": "2 phòng ngủ", "2pn-plus": "2 phòng ngủ+", "3pn": "3 phòng ngủ",
}
LABEL_DISTRICT = {
    "sapphire": "Sapphire", "masteri": "Masteri", "miami": "Miami",
    "sakura": "Sakura", "imperia": "Imperia", "lumiere": "Lumière",
    "canopy": "Canopy", "tonkin": "Tonkin",
}


def esc(v):
    return html.escape(str(v), quote=True)


def is_indexable(path):
    if not os.path.exists(path):
        return False
    text = open(path, encoding="utf-8").read()
    m = re.search(r'<meta\s+[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']+)', text, re.I)
    if not m:
        m = re.search(r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*name=["\']robots["\']', text, re.I)
    return not (m and "noindex" in m.group(1).lower())


def title_of(path):
    text = open(path, encoding="utf-8").read()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.I | re.S)
    if not m:
        m = re.search(r'<title>(.*?)</title>', text, re.I | re.S)
    if not m:
        return os.path.basename(os.path.dirname(path))
    value = re.sub(r'<[^>]+>', '', m.group(1))
    return re.sub(r'\s+', ' ', html.unescape(value)).strip()


def discover():
    children = {}
    for name in os.listdir(GOC):
        p = os.path.join(GOC, name, "index.html")
        if not os.path.isdir(os.path.join(GOC, name)) or not is_indexable(p):
            continue
        # Intersection: loại căn × phân khu. Match longest type first.
        m = re.fullmatch(r'cho-thue-(1pn-plus|2pn-plus|studio|1pn|2pn|3pn)-(sapphire|masteri|miami|sakura|imperia|lumiere|canopy|tonkin)-smart-city', name)
        if m:
            typ, district = m.groups()
            children["/" + name + "/"] = {
                "kind": "intersection", "type": typ, "district": district,
                "title": title_of(p),
            }
            continue
        # Budget / furnishing pages underneath a unit-type hub.
        m = re.fullmatch(r'(1pn-plus|2pn-plus|studio|1pn|2pn|3pn)-(.+)', name)
        if m and m.group(1) in TYPE_HUBS:
            typ, suffix = m.groups()
            if any(k in suffix for k in ("trieu", "duoi", "tren", "full-do")):
                children["/" + name + "/"] = {
                    "kind": "type-child", "type": typ, "title": title_of(p),
                }
    return children


def collect_by_parent(children):
    by_parent = defaultdict(list)
    for href, info in children.items():
        by_parent[TYPE_HUBS[info["type"]]].append((href, info))
        if info["kind"] == "intersection":
            by_parent[DISTRICT_HUBS[info["district"]]].append((href, info))
    for parent in by_parent:
        by_parent[parent].sort(key=lambda x: (x[1]["kind"], x[0]))
    return by_parent


def block_for(parent, items):
    links = []
    for href, info in items:
        if info["kind"] == "intersection":
            note = "%s tại %s" % (LABEL_TYPE[info["type"]], LABEL_DISTRICT[info["district"]])
        else:
            note = "Lọc sâu theo giá / nội thất cho %s" % LABEL_TYPE[info["type"]]
        links.append('<a href="%s"><strong>%s</strong><span>%s</span></a>' % (
            esc(href), esc(info["title"]), esc(note)))
    return (
        START + '\n<section class="seo-graph" aria-label="Lọc sâu theo nhu cầu">'
        '<div class="seo-graph-head"><span>Landing chuyên sâu</span>'
        '<h2>Tìm nhanh theo nhu cầu cụ thể</h2>'
        '<p>Các trang dưới đây chỉ xuất hiện khi URL đang indexable và có nội dung riêng, giúp Google và người dùng đi từ hub lớn tới đúng nhu cầu.</p></div>'
        '<div class="seo-graph-links">%s</div></section>\n' + END
    ) % "".join(links)


def replace_or_insert(text, block):
    pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if pat.search(text):
        return pat.sub(block, text, count=1)
    if "</main>" in text:
        return text.replace("</main>", block + "\n</main>", 1)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thu", action="store_true")
    args = ap.parse_args()
    children = discover()
    by_parent = collect_by_parent(children)
    changed = 0
    linked = set()
    for rel, items in sorted(by_parent.items()):
        path = os.path.join(GOC, rel)
        if not os.path.exists(path):
            continue
        old = open(path, encoding="utf-8").read()
        new = replace_or_insert(old, block_for(rel, items))
        if new != old:
            changed += 1
            if not args.thu:
                with open(path, "w", encoding="utf-8", newline="") as f:
                    f.write(new)
        linked.update(href for href, _ in items)
    missing = sorted(set(children) - linked)
    print("P3/P4 programmatic hub: %d child indexable · %d parent hub · %d file đổi · %d child chưa nối." % (
        len(children), len(by_parent), changed, len(missing)))
    for href in missing[:30]:
        print("CẢNH BÁO chưa có parent:", href)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())

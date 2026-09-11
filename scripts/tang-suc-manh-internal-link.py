#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P6: tăng sức mạnh internal-link cho các cụm thật sự yếu, không tạo URL mới.

Năm lớp liên kết ổn định:
1) Hub cẩm nang/giá/so sánh -> các bài nghiên cứu chuyên sâu đang có ít nguồn.
2) Ba hub thuê mạnh -> toàn bộ landing ngân sách/nội thất indexable theo loại căn.
3) Landing tòa <-> các intent page cùng phân khu.
4) Landing giao thoa phân khu×loại -> sibling intent + tòa cùng phân khu.
5) Hỗ trợ cụm tòa nhỏ chưa đủ nguồn crawl từ một hub loại căn liên quan.

Mỗi lớp có marker riêng để nhiều block P6 cùng tồn tại trên một trang. Script tự
migrate marker P6 cũ dùng chung một lần, chạy lặp idempotent. Không đổi URL,
title, canonical, robots hay schema.
"""

import argparse
import html
import json
import os
import re
import sys
from collections import defaultdict

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGACY_START = "<!-- P6-LINK-BOOST:START -->"
LEGACY_END = "<!-- P6-LINK-BOOST:END -->"

ARTICLE_HUBS = [
    "cam-nang-thue-nha.html",
    "bang-gia-thue-vinhomes-smart-city.html",
    "kinh-nghiem-thue-chung-cu-smart-city.html",
    "so-sanh-gia-thue-cac-phan-khu-smart-city.html",
    "tien-ich-vinhomes-smart-city.html",
]
ARTICLE_LINKS = [
    ("/lich-su-gia-thue-vinhomes-smart-city.html", "Lịch sử giá thuê Smart City"),
    ("/cho-thue-can-ho-imperia-smart-city.html", "Thuê căn hộ Imperia Smart City"),
    ("/masteri-vs-lumiere-thue-can-ho-smart-city.html", "Masteri hay Lumière khi thuê?"),
    ("/nen-thue-phan-khu-nao-vinhomes-smart-city.html", "Nên thuê phân khu nào?"),
    ("/ngan-sach-10-trieu-thue-can-ho-smart-city.html", "Ngân sách 10 triệu thuê căn nào?"),
    ("/ngan-sach-12-trieu-thue-can-ho-smart-city.html", "Ngân sách 12 triệu thuê căn nào?"),
    ("/thue-can-ho-gan-vinschool-smart-city.html", "Thuê căn gần Vinschool"),
]

DISTRICT_HUB = {
    "Sapphire": "/sapphire/",
    "Masteri": "/masteri/",
    "Miami": "/miami/",
    "Sakura": "/sakura/",
    "Imperia": "/imperia/",
    "Lumiere": "/lumiere/",
    "Canopy": "/canopy/",
    "Tonkin": "/tonkin/",
}

TYPE_LABEL = {
    "studio": "Studio",
    "1pn": "1PN",
    "1pn-plus": "1PN+",
    "2pn": "2PN",
    "2pn-plus": "2PN+",
    "3pn": "3PN",
}


def esc(v):
    return html.escape(str(v), quote=True)


def read(rel):
    path = os.path.join(GOC, rel)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def is_indexable(raw):
    if raw is None:
        return False
    m = re.search(
        r'<meta\b(?=[^>]*\bname=["\']robots["\'])(?=[^>]*\bcontent=["\']([^"\']*)["\'])[^>]*>',
        raw, re.I,
    )
    return not (m and "noindex" in m.group(1).lower())


def markers(key):
    safe = re.sub(r"[^A-Z0-9_-]", "-", key.upper())
    return (
        "<!-- P6-LINK-BOOST:%s:START -->" % safe,
        "<!-- P6-LINK-BOOST:%s:END -->" % safe,
    )


def wrap_block(key, body):
    start, end = markers(key)
    return start + "\n" + body + "\n" + end


def replace_block(raw, key, new_block):
    """Thay đúng block P6 theo key; migrate marker legacy mà không đè block khác."""
    legacy = re.compile(re.escape(LEGACY_START) + r".*?" + re.escape(LEGACY_END), re.S)
    raw = legacy.sub("", raw)

    start, end = markers(key)
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if pat.search(raw):
        return pat.sub(new_block, raw, count=1)
    if "</main>" in raw:
        return raw.replace("</main>", new_block + "\n</main>", 1)
    if "</body>" in raw:
        return raw.replace("</body>", new_block + "\n</body>", 1)
    return raw


def link_card(href, label, desc=""):
    span = "<span>%s</span>" % esc(desc) if desc else ""
    return '<a href="%s"><strong>%s</strong>%s</a>' % (esc(href), esc(label), span)


def block(key, title, intro, groups):
    cols = []
    for heading, links in groups:
        if not links:
            continue
        cols.append(
            '<div class="seo-graph-group"><h3>%s</h3><div class="seo-graph-links">%s</div></div>'
            % (esc(heading), "".join(links))
        )
    if not cols:
        return ""
    body = (
        '<section class="seo-graph p6-link-boost" aria-label="Liên kết nội bộ chuyên sâu">'
        '<div class="seo-graph-head"><span>Khám phá chuyên sâu</span><h2>%s</h2><p>%s</p></div>'
        '<div class="seo-graph-grid">%s</div></section>'
    ) % (esc(title), esc(intro), "".join(cols))
    return wrap_block(key, body)


def write(rel, key, b, dry):
    raw = read(rel)
    if raw is None or not b:
        return 0
    new = replace_block(raw, key, b)
    if new == raw:
        return 0
    if not dry:
        with open(os.path.join(GOC, rel), "w", encoding="utf-8", newline="") as f:
            f.write(new)
    print(("(--thu) sẽ boost " if dry else "Boost ") + rel + " [" + key + "]")
    return 1


def budget_pages():
    groups = defaultdict(list)
    pat = re.compile(r'^(studio|1pn-plus|1pn|2pn-plus|2pn|3pn)-(.+)$')
    for name in sorted(os.listdir(GOC)):
        path = os.path.join(GOC, name, "index.html")
        if not os.path.isfile(path):
            continue
        m = pat.match(name)
        if not m or not ("trieu" in name or name.endswith("full-do")):
            continue
        raw = read(name + "/index.html")
        if not is_indexable(raw):
            continue
        typ = m.group(1)
        tail = m.group(2)
        label = TYPE_LABEL.get(typ, typ.upper()) + " " + tail
        label = label.replace("duoi-", "dưới ").replace("tren-", "trên ")
        label = label.replace("full-do", "full nội thất").replace("-trieu", " triệu")
        label = label.replace("10-12", "10–12").replace("12-15", "12–15").replace("7-10", "7–10")
        groups[typ].append(("/" + name + "/", label))
    return groups


def article_block():
    links = []
    for href, label in ARTICLE_LINKS:
        rel = href.lstrip("/")
        if is_indexable(read(rel)):
            links.append(link_card(href, label, "Phân tích chuyên sâu phục vụ quyết định thuê."))
    return block(
        "ARTICLE",
        "Nghiên cứu thêm trước khi thuê",
        "Các bài dưới đây bổ sung dữ liệu giá, so sánh phân khu và tình huống thuê thực tế.",
        [("Bài chuyên sâu", links)],
    )


def budget_block(groups):
    cols = []
    for typ in ("studio", "1pn", "1pn-plus", "2pn", "2pn-plus", "3pn"):
        rows = groups.get(typ, [])
        if not rows:
            continue
        cols.append((TYPE_LABEL[typ], [
            link_card(href, label, "Mở landing lọc sâu đang indexable.")
            for href, label in rows
        ]))
    return block(
        "BUDGET",
        "Tìm căn theo ngân sách và nội thất",
        "Đi trực tiếp tới các landing lọc sâu có quỹ căn thật thay vì tìm lại từ đầu.",
        cols,
    )


def load_towers():
    path = os.path.join(GOC, "seo-toa.json")
    groups = defaultdict(list)
    if not os.path.isfile(path):
        return groups
    raw = json.load(open(path, encoding="utf-8"))
    for e in (raw.get("towers") or {}).values():
        if not e.get("indexable") or int(e.get("count") or 0) <= 0:
            continue
        district = e.get("district")
        if district not in DISTRICT_HUB:
            continue
        groups[district].append(e)
    for district in groups:
        groups[district].sort(key=lambda e: (-int(e.get("count") or 0), str(e.get("name") or "")))
    return groups


def tower_links(towers, current_path=""):
    out = []
    for e in towers:
        href = str(e.get("path") or "")
        if not href or href == current_path:
            continue
        out.append(link_card(
            href,
            "Tòa %s" % (e.get("name") or ""),
            "%d căn đang hiển thị." % int(e.get("count") or 0),
        ))
    return out


def page_h1(rel):
    raw = read(rel) or ""
    m = re.search(r'<h1[^>]*>(.*?)</h1>', raw, re.I | re.S)
    if not m:
        return rel.split("/", 1)[0].replace("-", " ").title()
    value = re.sub(r'<[^>]+>', ' ', m.group(1))
    value = html.unescape(re.sub(r'\s+', ' ', value)).strip()
    return value or rel.split("/", 1)[0].replace("-", " ").title()


def combo_links(combo_rels, current_rel="", limit=4):
    links = []
    for rel in combo_rels:
        if rel == current_rel or not is_indexable(read(rel)):
            continue
        href = "/" + rel[:-len("index.html")]
        links.append(link_card(
            href,
            page_h1(rel),
            "Loại căn đang có quỹ thuê trong cùng phân khu.",
        ))
    return links[:limit]


def tower_block(district, towers, combo_rels, current_path=""):
    parent = link_card(
        DISTRICT_HUB[district],
        "Tất cả căn tại %s" % district,
        "Quay về hub phân khu để so sánh toàn bộ quỹ căn.",
    )
    groups = [
        ("Hub phân khu", [parent]),
        ("Các tòa cùng phân khu", tower_links(towers, current_path)),
    ]
    intents = combo_links(combo_rels, limit=4)
    if intents:
        groups.append(("Loại căn tại phân khu", intents))
    return block(
        "TOWER",
        "Xem thêm theo tòa tại %s" % district,
        "Các tòa và loại căn cùng phân khu được nối trực tiếp để Googlebot và người thuê đi qua cụm này dễ hơn.",
        groups,
    )


def combo_pages_by_district():
    path = os.path.join(GOC, "seo-phan-khu-loai-can.json")
    out = defaultdict(list)
    if not os.path.isfile(path):
        return out
    raw = json.load(open(path, encoding="utf-8"))
    for slug, rec in (raw or {}).items():
        if not isinstance(rec, dict) or not rec.get("indexable"):
            continue
        district = str(rec.get("phanKhu") or "").strip()
        rel = slug.strip("/") + "/index.html"
        if district in DISTRICT_HUB and os.path.isfile(os.path.join(GOC, rel)):
            out[district].append(rel)
    for district in out:
        out[district].sort()
    return out


def combo_block(district, towers, combo_rels, current_rel):
    parent = link_card(
        DISTRICT_HUB[district],
        "Tất cả căn tại %s" % district,
        "Quay về hub phân khu để so sánh toàn bộ quỹ căn.",
    )
    siblings = combo_links(combo_rels, current_rel, 4)
    groups = [("Hub phân khu", [parent])]
    if siblings:
        groups.append(("Loại căn khác cùng phân khu", siblings))
    groups.append(("Các tòa cùng phân khu", tower_links(towers)))
    return block(
        "TOWER",
        "Khám phá thêm tại %s" % district,
        "Liên kết giữa loại căn và các tòa trong cùng phân khu giúp người thuê đi tiếp đúng nhu cầu và tạo đường crawl tự nhiên.",
        groups,
    )


def small_cluster_support_block(district, towers):
    return block(
        "SMALL-%s" % district.upper(),
        "Xem căn theo tòa tại %s" % district,
        "Các tòa đang có quỹ căn được nối từ trang loại căn liên quan để tăng đường crawl tự nhiên.",
        [("Tòa đang có căn", tower_links(towers))],
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thu", action="store_true")
    args = ap.parse_args()
    changed = 0

    # 1) Bài nghiên cứu: thêm nguồn link từ 5 hub mạnh, có ngữ cảnh rõ ràng.
    ab = article_block()
    for rel in ARTICLE_HUBS:
        if is_indexable(read(rel)):
            changed += write(rel, "ARTICLE", ab, args.thu)

    # 2) Landing ngân sách: ba hub mạnh nối tới toàn bộ landing indexable.
    bgroups = budget_pages()
    bb = budget_block(bgroups)
    for rel in (
        "bang-gia-thue-vinhomes-smart-city.html",
        "cam-nang-thue-nha.html",
        "kinh-nghiem-thue-chung-cu-smart-city.html",
    ):
        if is_indexable(read(rel)):
            changed += write(rel, "BUDGET", bb, args.thu)

    # 3-4) Cụm tòa và landing phân khu×loại: link hai chiều trong đúng semantic cluster.
    towers = load_towers()
    combos = combo_pages_by_district()
    for district, rows in towers.items():
        combo_rels = combos.get(district, [])
        for e in rows:
            href = str(e.get("path") or "")
            rel = href.strip("/") + "/index.html"
            if is_indexable(read(rel)):
                changed += write(rel, "TOWER", tower_block(district, rows, combo_rels, href), args.thu)
        for rel in combo_rels:
            if is_indexable(read(rel)):
                changed += write(rel, "TOWER", combo_block(district, rows, combo_rels, rel), args.thu)

    # 5) Tonkin chỉ có hai tower; giữ thêm một nguồn từ hub Studio để tower không mỏng.
    tonkin = towers.get("Tonkin", [])
    if tonkin and is_indexable(read("studio/index.html")):
        sb = small_cluster_support_block("Tonkin", tonkin)
        changed += write("studio/index.html", "SMALL-TONKIN", sb, args.thu)

    print("P6 internal-link boost: %d file/block %s · %d landing ngân sách · %d phân khu tòa." % (
        changed,
        "cần đổi" if args.thu else "đã đổi",
        sum(len(v) for v in bgroups.values()),
        len(towers),
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
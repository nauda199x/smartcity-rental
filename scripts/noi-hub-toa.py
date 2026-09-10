#!/usr/bin/env python3
"""Nối landing tòa vào các hub phân khu để mọi URL tòa có inbound crawl thật.

Đây là lớp P3 chạy sau khi seo-toa.json được dựng. Script chỉ thêm liên kết
nội bộ, không tạo URL mới, không đổi canonical/title. Marker giúp chạy lặp an toàn.
"""

import argparse
import html
import json
import os
import re
import sys
from collections import defaultdict

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(GOC, "seo-toa.json")
START = "<!-- SEO-TOWER-HUB:START -->"
END = "<!-- SEO-TOWER-HUB:END -->"

TARGETS = {
    "Sapphire": "sapphire/index.html",
    "Masteri": "masteri/index.html",
    "Miami": "miami/index.html",
    "Sakura": "sakura/index.html",
    "Imperia": "imperia/index.html",
    "Lumiere": "lumiere/index.html",
    "Canopy": "canopy/index.html",
    "Tonkin": "tonkin/index.html",
}


def esc(v):
    return html.escape("" if v is None else str(v), quote=True)


def replace_marker(text, block):
    pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if pat.search(text):
        return pat.sub(block, text, count=1)
    if "</main>" in text:
        return text.replace("</main>", block + "\n</main>", 1)
    return text


def guide_links():
    return (
        '<a href="/gia-thue-studio-smart-city.html"><strong>Giá thuê Studio Smart City</strong>'
        '<span>Theo dõi mặt bằng giá Studio từ dữ liệu đang có.</span></a>'
        '<a href="/tien-ich-vinhomes-smart-city.html"><strong>Tiện ích Vinhomes Smart City</strong>'
        '<span>Xem tiện ích và các điểm cần biết trước khi chọn tòa.</span></a>'
        '<a href="/luu-y-do-xe-thu-cung-phi-dich-vu-smart-city.html"><strong>Phí, gửi xe & thú cưng</strong>'
        '<span>Kiểm tra chi phí và quy định trước khi đặt cọc.</span></a>'
    )


def district_block(pk, towers):
    links = "".join(
        '<a href="%s"><strong>Tòa %s</strong><span>%d căn đang hiển thị · xem giá và căn trống</span></a>'
        % (esc(e["path"]), esc(e["name"]), int(e.get("count", 0)))
        for e in towers
    )
    return (
        START + '\n<section class="seo-graph" aria-label="Các tòa đang cho thuê tại %s">'
        '<div class="seo-graph-head"><span>Theo từng tòa</span>'
        '<h2>Các tòa đang có căn cho thuê tại %s</h2>'
        '<p>Danh sách dưới đây lấy từ cùng quỹ căn đang hiển thị. Chọn tòa để xem giá, diện tích và từng căn thực tế.</p></div>'
        '<div class="seo-graph-grid">'
        '<div class="seo-graph-group"><h3>Landing theo tòa</h3><div class="seo-graph-links">%s</div></div>'
        '<div class="seo-graph-group"><h3>Thông tin trước khi thuê</h3><div class="seo-graph-links">%s</div></div>'
        '</div></section>\n' + END
    ) % (esc(pk), esc(pk), links, guide_links())


def global_block(groups):
    cols = []
    for pk in sorted(groups):
        links = "".join(
            '<a href="%s"><strong>%s</strong><span>%d căn</span></a>'
            % (esc(e["path"]), esc(e["name"]), int(e.get("count", 0)))
            for e in groups[pk]
        )
        cols.append('<div class="seo-graph-group"><h3>%s</h3><div class="seo-graph-links">%s</div></div>' % (esc(pk), links))
    return (
        START + '\n<section class="seo-graph" aria-label="Tìm căn theo tòa">'
        '<div class="seo-graph-head"><span>Crawl hub theo tòa</span>'
        '<h2>Tìm căn hộ theo từng tòa Vinhomes Smart City</h2>'
        '<p>Mỗi link mở landing của một tòa đang có ít nhất một căn trong quỹ dữ liệu hiện tại.</p></div>'
        '<div class="seo-graph-grid">%s</div></section>\n' + END
    ) % "".join(cols)


def write_if_changed(rel, block, dry):
    path = os.path.join(GOC, rel)
    if not os.path.exists(path):
        print("CẢNH BÁO: thiếu hub %s" % rel)
        return 0
    old = open(path, encoding="utf-8").read()
    new = replace_marker(old, block)
    if new == old:
        return 0
    if not dry:
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(new)
    print("%s %s" % ("(--thu) sẽ nối" if dry else "Đã nối", rel))
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thu", action="store_true")
    args = ap.parse_args()
    if not os.path.exists(REGISTRY):
        print("LỖI: chưa có seo-toa.json")
        return 2
    towers = json.load(open(REGISTRY, encoding="utf-8")).get("towers", {})
    groups = defaultdict(list)
    for e in towers.values():
        if e.get("indexable") and int(e.get("count", 0)) > 0 and e.get("district") in TARGETS:
            groups[e["district"]].append(e)
    for pk in groups:
        groups[pk].sort(key=lambda e: (-int(e.get("count", 0)), e.get("name", "")))
    changed = 0
    for pk, rel in TARGETS.items():
        if groups.get(pk):
            changed += write_if_changed(rel, district_block(pk, groups[pk]), args.thu)
    # /can-ho/ là hub rất mạnh và đã được crawl thường xuyên; nối toàn bộ tòa
    # ở đây giúp tower URL mới không phụ thuộc duy nhất vào sibling links.
    if groups:
        changed += write_if_changed("can-ho/index.html", global_block(groups), args.thu)
    print("P3 tower hub: %d file cần/được cập nhật · %d phân khu · %d tòa active." % (
        changed, len(groups), sum(len(v) for v in groups.values())))
    return 0


if __name__ == "__main__":
    sys.exit(main())

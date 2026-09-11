#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P8: tăng độ rõ search-intent cho landing chính timthuesmartcity.com.

Mục tiêu:
- Không sinh URL mới, không đổi canonical.
- Giữ title ngắn, ổn định theo tháng; bổ sung cụm "căn hộ" ở H1/description.
- Dùng dữ liệu quỹ căn thật để tạo đoạn giới thiệu giao dịch hữu ích trên trang chủ.
- Thêm CollectionPage schema phản ánh đúng vai trò landing tập hợp căn cho thuê.
- Chạy lại được sau mỗi lần data.json thay đổi, idempotent.

Chạy:
  python3 scripts/toi-uu-landing-chinh.py
  python3 scripts/toi-uu-landing-chinh.py --kiem-tra
  python3 scripts/toi-uu-landing-chinh.py --thu
"""

import argparse
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(GOC, "index.html")
DATA = os.path.join(GOC, "data.json")
DOMAIN = "https://timthuesmartcity.com"

HEAD_START = "<!-- P8-MAIN-COLLECTION:START -->"
HEAD_END = "<!-- P8-MAIN-COLLECTION:END -->"
BODY_START = "<!-- P8-MAIN-INTENT:START -->"
BODY_END = "<!-- P8-MAIN-INTENT:END -->"


def nap_danh_muc():
    path = os.path.join(SCRIPT_DIR, "dung-lai-trang-danh-muc.py")
    spec = importlib.util.spec_from_file_location("p8_danh_muc", path)
    mod = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = old
    return mod


DL = nap_danh_muc()
la_can_hop_le = DL.la_can_hop_le
so_tien = DL.so_tien
phan_khu_tu_toa = DL.phan_khu_tu_toa


def esc(v):
    return html.escape(str(v), quote=True)


def thang_hien_tai():
    now = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    return "T%02d/%d" % (now.month, now.year)


def gia_trieu(v):
    if not v:
        return ""
    x = v / 1_000_000
    s = ("%.1f" % x).rstrip("0").rstrip(".").replace(".", ",")
    return s


def data_modified():
    try:
        p = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", "data.json"],
            cwd=GOC, capture_output=True, text=True, check=False,
        )
        out = (p.stdout or "").strip()
        return out or None
    except Exception:
        return None


def doc_data():
    raw = json.load(open(DATA, encoding="utf-8"))
    rows = raw if isinstance(raw, list) else raw.get("data", raw.get("rows", []))
    return [r for r in rows if isinstance(r, dict) and la_can_hop_le(r)]


def thong_ke(rows):
    prices = [so_tien(r.get("Giá thuê")) for r in rows]
    prices = [p for p in prices if p and p > 0]
    zones = set()
    for r in rows:
        try:
            z = phan_khu_tu_toa(r.get("Tòa", ""))
        except Exception:
            z = ""
        if z:
            zones.add(str(z).strip())
    return {
        "total": len(rows),
        "min_price": min(prices) if prices else 0,
        "max_price": max(prices) if prices else 0,
        "zones": len(zones),
    }


def title_text():
    return "Cho Thuê Chung Cư Vinhomes Smart City %s | Giá Tốt" % thang_hien_tai()


def h1_text():
    return "Cho Thuê Căn Hộ Chung Cư Vinhomes Smart City"


def description_text(stats):
    price = ""
    if stats["min_price"] and stats["max_price"]:
        price = ", giá %s–%s triệu/tháng" % (
            gia_trieu(stats["min_price"]), gia_trieu(stats["max_price"])
        )
    return (
        "Cho thuê căn hộ Vinhomes Smart City Tây Mỗ %s: %d căn Studio–3PN%s. "
        "Quỹ căn thực tế, ảnh và tình trạng trống cập nhật liên tục."
        % (thang_hien_tai(), stats["total"], price)
    )


def replace_marker(raw, start, end, block):
    pat = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if pat.search(raw):
        return pat.sub(block, raw, count=1)
    return raw


def set_meta(raw, key, value, attr="name"):
    pat = re.compile(
        r'(<meta\s+[^>]*%s=["\']%s["\'][^>]*content=["\'])[^"\']*(["\'])'
        % (re.escape(attr), re.escape(key)), re.I,
    )
    if pat.search(raw):
        return pat.sub(lambda m: m.group(1) + value + m.group(2), raw, count=1)
    pat2 = re.compile(
        r'(<meta\s+[^>]*content=["\'])[^"\']*(["\'][^>]*%s=["\']%s["\'][^>]*>)'
        % (re.escape(attr), re.escape(key)), re.I,
    )
    return pat2.sub(lambda m: m.group(1) + value + m.group(2), raw, count=1)


def schema_block(stats, desc):
    obj = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "@id": DOMAIN + "/#rental-collection",
        "url": DOMAIN + "/",
        "name": title_text(),
        "description": desc,
        "inLanguage": "vi-VN",
        "isPartOf": {"@id": DOMAIN + "/#website"},
        "about": {
            "@type": "Place",
            "name": "Vinhomes Smart City",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Tây Mỗ",
                "addressRegion": "Hà Nội",
                "addressCountry": "VN",
            },
        },
        "mainEntity": {
            "@type": "ItemList",
            "name": "Căn hộ Vinhomes Smart City đang cho thuê",
            "numberOfItems": stats["total"],
        },
    }
    modified = data_modified()
    if modified:
        obj["dateModified"] = modified
    return (
        HEAD_START + "\n"
        '<script type="application/ld+json" id="p8-main-collection-data">'
        + json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        + "</script>\n" + HEAD_END
    )


def body_block(stats):
    minp = gia_trieu(stats["min_price"])
    maxp = gia_trieu(stats["max_price"])
    price_text = ("%s–%s triệu/tháng" % (minp, maxp)) if minp and maxp else "xem theo từng căn"
    zone_text = "%d phân khu" % stats["zones"] if stats["zones"] else "nhiều phân khu"
    return BODY_START + "\n" + (
        '<section class="seo-graph p8-main-intent" aria-labelledby="p8-main-title">'
        '<div class="seo-graph-head">'
        '<span>Quỹ căn cho thuê %s</span>'
        '<h2 id="p8-main-title">Cho thuê căn hộ Vinhomes Smart City Tây Mỗ – quỹ căn thực tế</h2>'
        '<p>Hiện website đang hiển thị <strong>%d căn hộ cho thuê</strong> tại <strong>%s</strong>, '
        'mức giá trong quỹ hiện tại khoảng <strong>%s</strong>. Dữ liệu được đồng bộ thường xuyên từ bảng hàng thực tế; '
        'mỗi căn đang hoạt động có thông tin giá, tòa, loại căn, nội thất và tình trạng vào ở để người thuê so sánh trước khi đi xem.</p>'
        '</div>'
        '<div class="seo-graph-grid">'
        '<div class="seo-graph-group"><h3>Xem quỹ căn đang thuê được</h3><div class="seo-graph-links">'
        '<a href="/can-ho/"><strong>Danh sách căn hộ đang cho thuê</strong><span>Mở từng căn có URL chi tiết, giá và tình trạng trống.</span></a>'
        '<a href="/can-ho-vao-o-ngay-vinhomes-smart-city.html"><strong>Căn có thể vào ở ngay</strong><span>Ưu tiên những căn đang sẵn sàng nhận nhà.</span></a>'
        '<a href="/bang-gia-thue-vinhomes-smart-city.html"><strong>Bảng giá thuê Smart City</strong><span>So sánh giá theo loại căn và phân khu từ quỹ đang có.</span></a>'
        '</div></div>'
        '<div class="seo-graph-group"><h3>Kiểm tra trước khi thuê</h3><div class="seo-graph-links">'
        '<a href="/thu-tuc-thue-nha-vinhomes-smart-city.html"><strong>Thủ tục thuê và hợp đồng</strong><span>Các bước từ chọn căn, đặt cọc đến bàn giao.</span></a>'
        '<a href="/phi-dich-vu-vinhomes-smart-city.html"><strong>Phí dịch vụ khi ở Smart City</strong><span>Đọc trước các khoản chi ngoài tiền thuê.</span></a>'
        '<a href="/dang-ky-tam-tru-thue-nha-vinhomes-smart-city.html"><strong>Đăng ký tạm trú</strong><span>Thông tin cần biết sau khi nhận căn.</span></a>'
        '</div></div>'
        '</div></section>'
    ) % (esc(thang_hien_tai()), stats["total"], esc(zone_text), esc(price_text)) + "\n" + BODY_END


def apply(raw, stats):
    title = title_text()
    desc = description_text(stats)

    raw = re.sub(r'<title>.*?</title>', '<title>%s</title>' % esc(title), raw, count=1, flags=re.I | re.S)
    raw = set_meta(raw, "description", esc(desc), "name")
    raw = set_meta(raw, "og:title", esc(title), "property")
    raw = set_meta(raw, "og:description", esc(desc), "property")
    raw = set_meta(raw, "twitter:title", esc(title), "name")
    raw = set_meta(raw, "twitter:description", esc(desc), "name")
    raw = re.sub(
        r'(<h1\b[^>]*data-i18n=["\']hero\.h1["\'][^>]*>).*?(</h1>)',
        lambda m: m.group(1) + esc(h1_text()) + m.group(2),
        raw, count=1, flags=re.I | re.S,
    )

    head = schema_block(stats, desc)
    old = raw
    raw = replace_marker(raw, HEAD_START, HEAD_END, head)
    if raw == old and HEAD_START not in raw:
        raw = raw.replace("</head>", head + "\n</head>", 1)

    body = body_block(stats)
    old = raw
    raw = replace_marker(raw, BODY_START, BODY_END, body)
    if raw == old and BODY_START not in raw:
        anchor = "    <!-- DỮ LIỆU THỊ TRƯỜNG"
        if anchor in raw:
            raw = raw.replace(anchor, "    " + body + "\n\n" + anchor, 1)
        else:
            raw = raw.replace("</main>", body + "\n</main>", 1)

    # Đồng bộ schema WebPage ảnh ưu tiên nếu block đó đang tồn tại.
    pat = re.compile(r'(<script[^>]+id=["\']google-image-preview-data["\'][^>]*>)(.*?)(</script>)', re.I | re.S)
    m = pat.search(raw)
    if m:
        try:
            obj = json.loads(m.group(2))
            obj["name"] = title
            if isinstance(obj.get("primaryImageOfPage"), dict):
                obj["primaryImageOfPage"]["caption"] = title
            payload = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
            raw = raw[:m.start()] + m.group(1) + payload + m.group(3) + raw[m.end():]
        except Exception:
            pass
    return raw


def canonical(raw):
    m = re.search(r'<link\s+[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', raw, re.I)
    if not m:
        m = re.search(r'<link\s+[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']canonical["\']', raw, re.I)
    return m.group(1).strip() if m else ""


def noindex(raw):
    m = re.search(r'<meta\s+[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']+)', raw, re.I)
    return bool(m and "noindex" in m.group(1).lower())


def audit(raw, stats):
    problems = []
    title = re.search(r'<title>(.*?)</title>', raw, re.I | re.S)
    h1 = re.search(r'<h1\b[^>]*>(.*?)</h1>', raw, re.I | re.S)
    if not title or html.unescape(re.sub(r"\s+", " ", title.group(1))).strip() != title_text():
        problems.append("title landing chính chưa đúng P8")
    if not h1 or h1_text().lower() not in re.sub(r'<[^>]+>', '', html.unescape(h1.group(1))).lower():
        problems.append("H1 thiếu intent căn hộ/chung cư")
    if canonical(raw) != DOMAIN + "/":
        problems.append("canonical trang chủ không self-canonical")
    if noindex(raw):
        problems.append("trang chủ bị noindex")
    if raw.count(HEAD_START) != 1 or raw.count(BODY_START) != 1:
        problems.append("marker P8 thiếu hoặc bị nhân đôi")
    if "p8-main-collection-data" not in raw or '"@type":"CollectionPage"' not in raw:
        problems.append("thiếu CollectionPage schema P8")
    if stats["total"] <= 0:
        problems.append("không đọc được quỹ căn active")
    if ("%d căn hộ cho thuê" % stats["total"]) not in raw:
        problems.append("khối P8 chưa đồng bộ tổng quỹ căn")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kiem-tra", action="store_true")
    ap.add_argument("--thu", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(INDEX) or not os.path.isfile(DATA):
        print("LỖI: thiếu index.html hoặc data.json")
        return 2

    rows = doc_data()
    stats = thong_ke(rows)
    raw = open(INDEX, encoding="utf-8").read()

    if not args.kiem_tra:
        new = apply(raw, stats)
        changed = new != raw
        if changed and not args.thu:
            with open(INDEX, "w", encoding="utf-8", newline="") as f:
                f.write(new)
            raw = new
        elif changed:
            raw = new
        print("P8 landing chính: %s index.html · %d căn · %d phân khu · giá %s–%s triệu/tháng" % (
            "sẽ cập nhật" if args.thu and changed else ("đã cập nhật" if changed else "không đổi"),
            stats["total"], stats["zones"], gia_trieu(stats["min_price"]), gia_trieu(stats["max_price"]),
        ))

    problems = audit(raw, stats)
    print("P8 audit: %d critical" % len(problems))
    for p in problems:
        print("CRITICAL:", p)
    if not problems:
        print("PASS — landing chính giữ self-canonical và đã rõ search intent cho thuê Smart City.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

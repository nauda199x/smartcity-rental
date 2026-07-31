#!/usr/bin/env python3
"""
kiem-tra-seo-snapshot.py — Chụp "ảnh chụp" các yếu tố SEO của mọi trang HTML
để so sánh TRƯỚC và SAU khi đổi giao diện.

Ghi ra JSON gồm: title, meta description, canonical, toàn bộ H1/H2/H3 theo
đúng thứ tự, các khối JSON-LD (đã chuẩn hoá), sự hiện diện mã GA4, alt ảnh.

    python3 scripts/kiem-tra-seo-snapshot.py truoc.json      # chụp
    python3 scripts/kiem-tra-seo-snapshot.py --so-sanh a.json b.json
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

GA4 = "G-VF9KHC5TWD"
BO_QUA = {".git", ".github", "node_modules", "images", "scripts", "_design:"}


class BocTrang(HTMLParser):
    """Đọc HTML thô, nhặt ra đúng những thứ cần theo dõi."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self.description = None
        self.canonical = None
        self.headings = []          # [(cap, chu)]
        self.jsonld = []
        self.alts = []
        self._trong = None          # thẻ đang mở mà ta cần gom chữ
        self._dem = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title" and self.title is None:
            self._trong, self._dem = "title", []
        elif tag == "meta":
            if a.get("name", "").lower() == "description" and self.description is None:
                self.description = a.get("content", "")
        elif tag == "link":
            if "canonical" in a.get("rel", "").lower() and self.canonical is None:
                self.canonical = a.get("href", "")
        elif tag in ("h1", "h2", "h3"):
            self._trong, self._dem = tag, []
        elif tag == "script" and a.get("type", "") == "application/ld+json":
            self._trong, self._dem = "ld", []
        elif tag == "img":
            self.alts.append(a.get("alt"))

    def handle_endtag(self, tag):
        if self._trong is None:
            return
        if tag == "title" and self._trong == "title":
            self.title = "".join(self._dem).strip()
        elif tag in ("h1", "h2", "h3") and self._trong == tag:
            chu = re.sub(r"\s+", " ", "".join(self._dem)).strip()
            self.headings.append([tag, chu])
        elif tag == "script" and self._trong == "ld":
            self.jsonld.append("".join(self._dem))
        else:
            return
        self._trong, self._dem = None, []

    def handle_data(self, data):
        if self._trong is not None:
            self._dem.append(data)


def chuan_hoa_ld(chuoi):
    """Parse JSON-LD rồi dump lại có sắp xếp — so sánh nội dung, bỏ qua định dạng."""
    try:
        return json.dumps(json.loads(chuoi), sort_keys=True, ensure_ascii=False)
    except Exception as loi:
        return "LOI-CU-PHAP: " + str(loi)


def quet(goc):
    ket_qua = {}
    for thu_muc, cac_thu_muc_con, cac_file in os.walk(goc):
        cac_thu_muc_con[:] = [d for d in cac_thu_muc_con if d not in BO_QUA]
        for ten in sorted(cac_file):
            if not ten.endswith(".html"):
                continue
            duong_dan = os.path.join(thu_muc, ten)
            khoa = os.path.relpath(duong_dan, goc)
            noi_dung = open(duong_dan, encoding="utf-8").read()
            p = BocTrang()
            p.feed(noi_dung)
            ket_qua[khoa] = {
                "title": p.title,
                "description": p.description,
                "canonical": p.canonical,
                "headings": p.headings,
                "jsonld": sorted(chuan_hoa_ld(x) for x in p.jsonld),
                "so_jsonld": len(p.jsonld),
                "ga4": GA4 in noi_dung,
                "alts": p.alts,
            }
    return ket_qua


def so_sanh(a, b):
    """In ra mọi khác biệt. Trả về số lỗi."""
    loi = 0
    chi_a = set(a) - set(b)
    chi_b = set(b) - set(a)
    if chi_a:
        print(f"  ✗ FILE BỊ MẤT ({len(chi_a)}): {sorted(chi_a)}")
        loi += len(chi_a)
    if chi_b:
        print(f"  ✗ FILE MỚI THÊM ({len(chi_b)}): {sorted(chi_b)}")
        loi += len(chi_b)

    for ten in sorted(set(a) & set(b)):
        x, y = a[ten], b[ten]
        for truong in ("title", "description", "canonical"):
            if x[truong] != y[truong]:
                print(f"  ✗ {ten} · {truong}")
                print(f"      trước: {x[truong]!r}")
                print(f"      sau  : {y[truong]!r}")
                loi += 1
        if x["headings"] != y["headings"]:
            print(f"  ✗ {ten} · heading khác nhau")
            cu = [f"{c}:{t}" for c, t in x["headings"]]
            moi = [f"{c}:{t}" for c, t in y["headings"]]
            for i in range(max(len(cu), len(moi))):
                v1 = cu[i] if i < len(cu) else "(không có)"
                v2 = moi[i] if i < len(moi) else "(không có)"
                if v1 != v2:
                    print(f"      [{i}] trước: {v1}")
                    print(f"      [{i}] sau  : {v2}")
            loi += 1
        if x["jsonld"] != y["jsonld"]:
            print(f"  ✗ {ten} · JSON-LD khác nhau ({x['so_jsonld']} → {y['so_jsonld']} khối)")
            loi += 1
        if x["ga4"] != y["ga4"]:
            print(f"  ✗ {ten} · GA4 {x['ga4']} → {y['ga4']}")
            loi += 1
        if x["alts"] != y["alts"]:
            print(f"  ✗ {ten} · thuộc tính alt khác nhau")
            print(f"      trước: {x['alts']}")
            print(f"      sau  : {y['alts']}")
            loi += 1
    return loi


if __name__ == "__main__":
    goc = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if sys.argv[1:2] == ["--so-sanh"]:
        truoc = json.load(open(sys.argv[2], encoding="utf-8"))
        sau = json.load(open(sys.argv[3], encoding="utf-8"))
        print(f"So sánh {sys.argv[2]} → {sys.argv[3]}")
        n = so_sanh(truoc, sau)
        print(f"\n{'✓ KHÔNG CÓ KHÁC BIỆT' if n == 0 else f'✗ {n} KHÁC BIỆT'}")
        sys.exit(1 if n else 0)

    dich = sys.argv[1] if sys.argv[1:] else "snapshot.json"
    d = quet(goc)
    json.dump(d, open(dich, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Đã chụp {len(d)} trang → {dich}")
    print(f"  heading: {sum(len(v['headings']) for v in d.values())}")
    print(f"  JSON-LD: {sum(v['so_jsonld'] for v in d.values())}")
    print(f"  GA4    : {sum(1 for v in d.values() if v['ga4'])}/{len(d)} trang")
    print(f"  ảnh alt: {sum(len(v['alts']) for v in d.values())}")

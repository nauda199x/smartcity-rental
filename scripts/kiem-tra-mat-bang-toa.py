#!/usr/bin/env python3
"""P2 safety gate: chỉ giữ ảnh mặt bằng khi filename khớp đúng tòa.

`seo-p0-p4.py` chỉ thử chèn asset local. Gate này chạy ngay sau đó và loại block
mặt bằng nếu tên file chỉ khớp chung chung theo phân khu (vd. chỉ có "lumiere")
mà không có mã tòa cụ thể. Nhờ vậy không bao giờ gắn nhầm mặt bằng cho A2/A3,
GS1/GS2... chỉ để "có ảnh".
"""

import argparse
import json
import os
import re
import sys
import unicodedata

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(GOC, "seo-toa.json")
BODY_START = "<!-- SEO-TOWER-CONTEXT:START -->"
BODY_END = "<!-- SEO-TOWER-CONTEXT:END -->"
FLOOR_RE = re.compile(
    r'<div class="seo-graph-group"><h3>Mặt bằng / layout có sẵn</h3>'
    r'<img src="([^"]+)"[^>]*></div>', re.I | re.S)


def slugify(v):
    s = unicodedata.normalize("NFD", str(v or ""))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.lower().replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def specific_tokens(entry):
    raw = slugify(entry.get("data_code") or entry.get("code"))
    code = slugify(entry.get("code"))
    name = slugify(entry.get("name"))
    out = {x for x in (raw, code) if len(x) >= 2}

    # Các tên thương mại có code quá ngắn cần thêm tổ hợp đặc hiệu.
    m = re.search(r'west-([a-d])', name)
    if m:
        out.update({"west-" + m.group(1), "masteri-" + m.group(1)})
    m = re.match(r'(a\d+)-lumi', name)
    if m:
        out.add(m.group(1))
    m = re.match(r'(gs\d+)-', name)
    if m:
        out.add(m.group(1))
    m = re.match(r'(sa\d+)-', name)
    if m:
        out.add(m.group(1))
    m = re.match(r'(tc\d+)-', name)
    if m:
        out.add(m.group(1))
    m = re.match(r'(tk\d+)-', name)
    if m:
        out.add(m.group(1))
    m = re.match(r'(i\d+)-', name)
    if m:
        out.add(m.group(1))
    # S1.01 có thể xuất hiện trong filename dưới dạng s1-01 hoặc s101.
    for token in list(out):
        compact = token.replace("-", "")
        if len(compact) >= 3:
            out.add(compact)
    return sorted(out, key=len, reverse=True)


def filename_matches(src, entry):
    base = slugify(os.path.basename(src))
    compact = base.replace("-", "")
    for token in specific_tokens(entry):
        if "-" in token and token in base:
            return True
        tcompact = token.replace("-", "")
        if len(tcompact) >= 3 and tcompact in compact:
            return True
        # code 2 ký tự như A2/I1: chỉ chấp nhận segment độc lập.
        if len(token) == 2 and re.search(r'(^|-)%s(-|$)' % re.escape(token), base):
            return True
    return False


def process(path, entry, dry):
    if not os.path.exists(path):
        return 0, 0
    old = open(path, encoding="utf-8").read()
    start = old.find(BODY_START)
    end = old.find(BODY_END, start + len(BODY_START)) if start >= 0 else -1
    if start < 0 or end < 0:
        return 0, 0
    segment = old[start:end]
    matches = list(FLOOR_RE.finditer(segment))
    if not matches:
        return 0, 0
    removed = 0
    new_segment = segment
    for m in reversed(matches):
        src = m.group(1)
        if filename_matches(src, entry):
            continue
        new_segment = new_segment[:m.start()] + new_segment[m.end():]
        removed += 1
        print("LOẠI ảnh mặt bằng chưa đủ đặc hiệu: %s <- %s" % (entry.get("name"), src))
    if removed:
        new = old[:start] + new_segment + old[end:]
        if not dry:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new)
        return 1, removed
    return 0, 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--thu", action="store_true")
    args = ap.parse_args()
    if not os.path.exists(REGISTRY):
        print("LỖI: thiếu seo-toa.json")
        return 2
    towers = json.load(open(REGISTRY, encoding="utf-8")).get("towers", {})
    files = removed = 0
    for entry in towers.values():
        if not entry.get("indexable"):
            continue
        path = os.path.join(GOC, entry["path"].strip("/"), "index.html")
        f, r = process(path, entry, args.thu)
        files += f
        removed += r
    print("P2 floorplan safety: loại %d block không khớp tòa trên %d file." % (removed, files))
    return 0


if __name__ == "__main__":
    sys.exit(main())

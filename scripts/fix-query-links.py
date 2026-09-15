#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0 SEO: giữ URL filter cho UX nhưng không phát tín hiệu crawl nội bộ.

Quét toàn bộ HTML và thêm rel="nofollow" vào mọi <a> nội bộ có query string.
Không đổi href, nên các link kiểu ?loai=, ?pk=, ?gia=, ?q=, ?form= vẫn hoạt
động y nguyên cho khách/Zalo/Facebook. Script idempotent: chạy nhiều lần không
nhân bản nofollow.

Lý do không dùng robots.txt Disallow: Google phải crawl URL query thì mới đọc
được meta noindex/query guard trên trang đích.
"""

from pathlib import Path
from urllib.parse import urlsplit
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
HOSTS = {"timthuesmartcity.com", "www.timthuesmartcity.com"}
SKIP_DIRS = {".git", ".github", "node_modules"}

RE_A = re.compile(r"<a\b[^>]*>", re.I | re.S)
RE_HREF = re.compile(r"\bhref\s*=\s*([\"'])(.*?)\1", re.I | re.S)
RE_REL = re.compile(r"\brel\s*=\s*([\"'])(.*?)\1", re.I | re.S)


def la_query_noi_bo(href: str) -> bool:
    raw = (href or "").strip()
    if not raw or raw.startswith("#"):
        return False
    low = raw.lower()
    if low.startswith(("mailto:", "tel:", "javascript:", "data:", "blob:", "sms:", "zalomsg:")):
        return False

    parsed = urlsplit(raw if not raw.startswith("//") else "https:" + raw)
    if parsed.scheme in ("http", "https") or parsed.netloc:
        if (parsed.hostname or "").lower() not in HOSTS:
            return False
    return bool(parsed.query)


def them_nofollow(tag: str) -> tuple[str, bool]:
    hm = RE_HREF.search(tag)
    if not hm or not la_query_noi_bo(hm.group(2)):
        return tag, False

    rm = RE_REL.search(tag)
    if rm:
        rels = rm.group(2).split()
        if any(x.lower() == "nofollow" for x in rels):
            return tag, False
        moi = (rm.group(2).rstrip() + " nofollow").strip()
        tag2 = tag[:rm.start(2)] + moi + tag[rm.end(2):]
        return tag2, True

    # Chèn trước dấu > cuối cùng, giữ nguyên toàn bộ class/data/href và markup.
    pos = tag.rfind(">")
    if pos < 0:
        return tag, False
    return tag[:pos] + ' rel="nofollow"' + tag[pos:], True


def xu_ly_file(path: Path) -> int:
    raw = path.read_text(encoding="utf-8", errors="replace")
    dem = 0

    def repl(match):
        nonlocal dem
        tag2, doi = them_nofollow(match.group(0))
        if doi:
            dem += 1
        return tag2

    moi = RE_A.sub(repl, raw)
    if dem and moi != raw:
        path.write_text(moi, encoding="utf-8")
    return dem


def main():
    tong_link = 0
    tong_file = 0
    for path in ROOT.rglob("*.html"):
        rel_parts = path.relative_to(ROOT).parts
        if any(p in SKIP_DIRS for p in rel_parts):
            continue
        n = xu_ly_file(path)
        if n:
            tong_file += 1
            tong_link += n
            print(f"FIX {path.relative_to(ROOT).as_posix()}: {n} link")

    print(f"P0 query links: đã chuẩn hóa {tong_link} link trong {tong_file} file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
